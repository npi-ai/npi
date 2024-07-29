# TODO: recreate navigator using function callings

import json
import re
from textwrap import dedent
from typing import Union, List, Literal, Tuple

from playwright.async_api import Error

from typing_extensions import NotRequired, TypedDict

from npiai.llm import LLM
from npiai.utils import logger
from npiai.context import Context, Task
from npiai.core.browser import PlaywrightContext
from npiai.core.tool._browser import BrowserTool
from npiai.core.tool._agent import BrowserAgentTool

__PROMPT__ = """
Imagine that you are imitating humans doing web navigation for a task step by step. I will provide you with the following context and you should call the best tool to fulfill the task.

## Provided Context

- A screenshot of the target page in the current viewport.
- An annotated screenshot where the interactive elements are surrounded with rectangular bounding boxes in different colors. At the top left of each bounding box is a small rectangle in the same color as the bounding box. This is the label and it contains a number indicating the ID of that box. The label number starts from 0.
- The title of the target page.
- The task I want to perform.
- Up to 10 previous actions (you should use them to avoid duplicates). Especially, each action in the history will have an "element" field specifying the target element of the action.
- An array of the interactive elements inside the current viewport.
- An array of newly added elements' ID since the last action. These elements reflect the impact of your last action.

## Element Object

The original HTML elements are described as the following JSON objects:

type Element = {
  id: string; // The ID of the element
  tag: string; // The tag of the element
  role: string | null; // The WAI-ARIA accessible role of the element
  accessibleName: string; // The WAI-ARIA accessible name of the element
  accessibleDescription: string; // The WAI-ARIA accessible description of the element
  attributes: Record<string, string>; // Some helpful attributes of the element
  options?: string[]; // Available options of an <select> element. This property is only provided when the element is a <select> element.
}

## Instructions

Below is the instructions for you to outline the next actions of current stage:
- Examine the screenshots and the provided HTML, and then think about what the current page is.
- Validate previous actions using the screenshots. You should try to re-run the actions that are not successfully performed.
- Pay more attention to elements that overlap on top of other elements (i.e., is visible in the screenshots) and consider performing actions on these visible elements first. Remember that you are only given the elements within the current viewport.
- Go through the `role`, `accessibleName`, and `accessibleDescription` properties to grab semantic information of the elements.
- Pay attention to the newly added elements (e.g., dropdown list) since they may related to the next action.
- Analyze the previous actions and their intention. Particularly, focus on the last action, which may be more related to what you should do now as the next step.
- Think if you need to close the dialogs before interacting with the elements below it. This is necessary when the dialog overlaps with other elements.
- Think if it is necessary to scroll the page down to see more contents. Scrolling could be useful when you find that the required element is beyond current viewport.
- When working on an input of a combobox or a datepicker, it may be useful to perform a click action first.
- If the target element is overlapped by some dialogs, it may be useful to close these dialogs first.
- Briefly describe the current screenshots and the provided HTML in the "observation" field. If there are previous actions, you need to briefly describe the previous actions and the page changes.
- Based on the observation, think about what you need to do next to complete the instructions, and output your thoughts in the "thoughts" field.
- Decide the best action for the next step.

## Conventions

Here are some conventions to choose a suitable tool:
- If you need to click on an element, you should set the `action.type` field to "click";
- If you need to press the enter key on an input or textarea to trigger a search or submit a form, you should set the `action.type` to "enter".
- If you need to type or fill something into an input box, you should set the `action.type` to "fill" and specify the text in the `value` field.
- If you need to select a value for a <select> element, you should set the `action.type` to "select" and specify the value in the `value` field.
- If the page is scrollable and the task requires actions beyond the provided viewport, you can set the `action` to "scroll" to scroll down to reveal the rest of the page.
- If you think you have missed something and need to scroll back to the top of the page to start over, you can set the `action` to "back_to_top".
- If you are performing a critical action, such as submitting a form to place an order, clicking a "Send" button to send a message, or clicking a "Save" button to save the form, you should set the `action.type` to "confirmation" and ask for user confirmation.
- If you need more information from the user to fulfill the task, such as requesting the user's name and making a choice, you should set the `action.type` to "human-intervention" and wait for user response.
- If the whole task is done, you should set the `action.type` to "done" not call any further tools.

## Response Format

You must exactly follow the following response format and avoid adding any explanation or additional text in your response. Particularly, do not put any comments in the response.

{
  "observation": string,
  "thoughts": string,
  "action": {
      "description": string,
      "type": 'fill' | 'click' | 'enter' | 'select' | 'scroll' | 'back-to-top' | 'confirmation' | 'human-intervention' | 'done',
      "value"?: string, // input value for 'type' or 'select' actions, if applicable
      "id"?: string, // element ID, unnecessary for the 'scroll' action
    }
}

## Input Example

Task: Search for the answer to everything
Scrollable: yes
Previous Actions: [{...}]
Elements: [{...}]
Newly Added Elements' ID: ["0", "1", "2", ...]

## Response Example

{
  "observation": "This is the Google search page with a search box in the center",
  "thoughts": "I should type the query text in the search box",
  "action": {
    "description": "Type 'the answer to everything' into the search box",
    "type": "fill",
    "value": "the answer to everything",
    "id": "42"
  }
}
"""


class Action(TypedDict):
    description: str
    type: Literal[
        "type",
        "click",
        "enter",
        "select",
        "scroll",
        "back-to-top",
        "confirmation",
        "human-intervention",
        "not-found",
        "done",
    ]
    value: NotRequired[str]
    id: NotRequired[str]
    element: NotRequired[dict]  # element json used for recording


class Response(TypedDict):
    observation: str
    thoughts: str
    action: Action


def _parse_response(response: str) -> Union[Response, None]:
    try:
        match = re.match(r"```.*\n([\s\S]+)```", response)
        data = json.loads(match.group(1)) if match else json.loads(response)
        return data
    except json.JSONDecodeError:
        return None


class NavigatorAgent(BrowserAgentTool):
    name: str = "navigator"

    def __init__(
        self,
        llm: LLM,
        playwright: PlaywrightContext,
        max_steps: int = 42,
    ):
        self._browser_app = BrowserTool(
            name="navigator",
            description="Perform any task by simulating keyboard/mouse interaction on a specific web page. "
            "If the some action needs user confirmation, please specify them.",
            system_prompt=__PROMPT__,
            playwright=playwright,
        )

        super().__init__(
            tool=self._browser_app,
            llm=llm,
        )

        self.max_steps = max_steps

    # navigator uses shared playwright context, so we don't need to start it again here
    async def start(self):
        pass

    async def end(self):
        pass

    async def generate_user_prompt(self, task: str, history: List[Response]):
        await self._browser_app.clear_bboxes()
        raw_screenshot = await self._browser_app.get_screenshot()
        elements, added_ids = await self._browser_app.get_interactive_elements(
            raw_screenshot
        )

        user_prompt: str = dedent(
            f"""
            Page Title: {await self._browser_app.get_page_title()}
            Task: {task}
            Scrollable: {await self._browser_app.is_scrollable()}
            Previous Actions: {json.dumps(history[-10:])}
            Elements: {json.dumps(elements)}
            Newly Added Elements' ID: {json.dumps(added_ids)}
            """
        )

        # print(user_prompt)

        annotated_screenshot = await self._browser_app.get_screenshot()

        if not raw_screenshot or not annotated_screenshot:
            return {
                "role": "user",
                "content": user_prompt,
            }

        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": raw_screenshot,
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": annotated_screenshot,
                    },
                },
            ],
        }

    async def chat(self, ctx: Context, instruction: str) -> str:
        history: List[Response] = []

        step = 0

        while True:
            msg = ctx.fork(instruction)
            msg.append(
                {
                    "role": "system",
                    "content": self._browser_app.system_prompt,
                }
            )
            msg.append(await self.generate_user_prompt(instruction, history))

            response_str = await self._call_llm(ctx, msg)
            response = _parse_response(response_str)

            if not response:
                # try again if the response can't be parsed correctly
                continue

            result, elem_json = await self._run_action(response["action"], ctx)
            logger.info(result)

            if not result:
                # requires further intervention if the action is not executable
                return response_str

            # remove element id from history to reduce noise
            response["action"].pop("id", None)
            response["action"]["element"] = elem_json
            history.append(response)
            step += 1

            if step > self.max_steps:
                return f"Maximum number of steps reached. Last response was: {response_str}"

    async def _call_llm(self, ctx: Context, message: Task) -> str:
        """
        Call llm for one round with the given prompts

        Args:
            message: ThreadMessage context

        Returns:
            response message
        """
        response = await self.llm.completion(
            messages=message.conversations(),
            max_tokens=4096,
        )

        response_message = response.choices[0].message

        message.step(response_message)

        if not response_message.content:
            raise Exception(f"{self.name}: No response message")

        logger.debug(response_message.content + "\n")

        return response_message.content

    async def _run_action(
        self, action: Action, ctx: Context
    ) -> Tuple[Union[str, None], dict]:
        """
        Run the given action

        Args:
            action: Action to run

        Returns:
            [0]: response message if the action is executable, None otherwise
            [1]: element json
        """
        await self._browser_app.clear_bboxes()
        await self._browser_app.init_observer()

        elem = (
            await self._browser_app.get_element_by_marker_id(action["id"])
            if "id" in action
            else None
        )
        elem_json = await self._browser_app.element_to_json(elem) if elem else None

        call_msg = f'[{self.name}]: {action["type"]} - {action["description"]}'

        logger.info(call_msg)
        await ctx.send(call_msg)

        match action["type"]:
            case "click":
                result = await self._browser_app.click(elem)
            case "enter":
                result = await self._browser_app.enter(elem)
            case "fill":
                result = await self._browser_app.fill(elem, action["value"])
            case "select":
                result = await self._browser_app.select(elem, action["value"])
            case "scroll":
                result = await self._browser_app.scroll()
            case "back-to-top":
                result = await self._browser_app.back_to_top()
            case "confirmation":
                result = await self.hitl.confirm(ctx, self.name, action["description"])
            case "human-intervention":
                result = await self.hitl.input(ctx, self.name, action["description"])
            case "done":
                result = None
            case _:
                raise Exception(f"{self.name}: Unknown action: {action}")

        if elem:
            await elem.dispose()

        try:
            await self._browser_app.wait_for_stable()
        except Error:
            # FIXME: if the action triggers a navigator, we will receive an error showing "Page.evaluate:
            #  Execution context was destroyed, most likely because of a navigation"
            await self._browser_app.playwright.page.wait_for_timeout(3000)

        return result, elem_json
