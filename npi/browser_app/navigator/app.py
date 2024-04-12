import base64
import json
from textwrap import dedent
from typing import Union, List

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from npi.core import App, BrowserApp, npi_tool, ChatParameters
from .schema import *

__PROMPT__ = """
Imagine that you are imitating humans doing web navigation for a task step by step. I will provide you with the following context and you should call the best tool to fulfill the task.

## Provided Context

- A screenshot of the target page in the current viewport.
- An annotated screenshot where the interactive elements are surrounded with rectangular bounding boxes in different colors. At the top left of each bounding box is a small rectangle in the same color as the bounding box. This is the label and it contains a number indicating the ID of that box. The label number starts from 0.
- The title of the target page.
- The task I want to perform.
- Chat history containing previous tool calls (you should use them to avoid duplicates).
- An array of the interactive elements inside the current viewport.
- An array of newly added elements' ID since the last action. These elements reflect the impact of your last action.

## Element Object

The original HTML elements are described as the following JSON objects:

type Element = {
  id: string; // The ID of the element
  tag: string; // The tag of the element
  role: string | null; // The accessible role of the element
  accessibleName: string; // The accessible name of the element
  accessibleDescription: string; // The accessible description of the element
  attributes: Record<string, string>; // Some helpful attributes of the element
  options?: string[]; // Available options of an <select> element. This property is only provided when the element is a <select> element.
}

## Instructions

Below is the instructions for you to outline the next actions of current stage:
- Examine the screenshots and the provided elements, and then think about what the current page is.
- Pay more attention to elements that overlap on top of other elements (i.e., is visible in the screenshots) and consider performing actions on these visible elements first. Remember that you are only given the elements within the current viewport.
- Go through the `role`, `accessibleName`, and `accessibleDescription` properties to grab semantics of the elements.
- Pay attention to the newly added elements (e.g., dropdown list) since they may related to the next action.
- Analyze the previous tool calls and their intention through the chat history. Particularly, focus on the last tool call, which may be more related to what you should do now as the next step.
- Validate previous tool calls using the screenshots. You should try to re-run the tools that are not successfully executed.
- Think about whether it is necessary to scroll the page down to see more contents. Scrolling could be useful when you find that the required element is beyond current viewport.
- When working on an input of a combobox or a datepicker, it may be useful to perform a click first.
- Based on the observation, think about the tool you need to take next to complete the task.
- Decide one best tool for the next step. Remember that you can only call one tool at a time.

## Conventions

Here are some conventions to choose a suitable tool:
- If you need to click on an element, you should call the `click` tool.
- If you need to type something into an input box, you should set call the `fill` tool and specify the `value` in the arguments.
- If you need to press the enter key on an input or textarea to trigger a search or submit a form, you should call the `enter` tool.
- If you need to select a value from a dropdown list, you should call the `select` tool and specify the `value` in the arguments.
- If the page is scrollable and you need to scroll down to see the rest of the page, you call the `scroll` tool.
- If you are performing a critical action, such as submitting a form to place an order, clicking a "Send" button to send a message, or clicking a "Save" button to save the form, you should ask for user confirmation.
- If the task need other tools beyond this navigator, you should ask for human help. 
- If the whole task is done, you should not call any further tools.
"""

from npi.core.context import Thread, ThreadMessage


class Navigator(App):
    browser_app: BrowserApp
    _selector: str
    _current_task: Union[str, None] = None

    def __init__(self, browser_app: BrowserApp, selector: str = None, llm=None):
        super().__init__(
            name='navigator',
            description='Simulate keyboard/mouse interaction on a specific web page',
            system_role=__PROMPT__,
            llm=llm or OpenAI(),
            model='gpt-4-vision-preview'
        )

        self.browser_app = browser_app
        self._selector = selector
        self._previous_actions = []

    def _get_page_title(self):
        return self.browser_app.page.title()

    def _get_screenshot(self):
        screenshot = self.browser_app.page.screenshot()
        return 'data:image/png;base64,' + base64.b64encode(screenshot).decode()

    def _init_browser_utils(self):
        self.browser_app.page.evaluate(
            """() => {
                if (!window.npi) {
                    window.npi = new window.BrowserUtils();
                }
            }"""
        )

    def _is_scrollable(self):
        self._init_browser_utils()
        return self.browser_app.page.evaluate('() => npi.isScrollable()')

    def _get_interactive_elements(self, screenshot: str):
        self._init_browser_utils()

        return self.browser_app.page.evaluate(
            """async (screenshot) => {
                const { elementsAsJSON, addedIDs } = await npi.snapshot(screenshot);
                return [elementsAsJSON, addedIDs];
            }""",
            screenshot,
        )

    def _get_element_by_id(self, elem_id: str):
        self._init_browser_utils()

        handle = self.browser_app.page.evaluate_handle(
            'id => npi.getElement(id)',
            elem_id,
        )

        elem_handle = handle.as_element()

        if not elem_handle:
            raise Exception(f'Element not found (id: {elem_id})')

        return elem_handle

    def _init_observer(self):
        self._init_browser_utils()
        self.browser_app.page.evaluate('() => npi.initObserver()')

    def _wait_for_stable(self):
        self._init_browser_utils()
        self.browser_app.page.evaluate('() => npi.stable()')

    def _generate_user_prompt(self):
        raw_screenshot = self._get_screenshot()
        elements, added_ids = self._get_interactive_elements(raw_screenshot)

        user_prompt: str = dedent(
            f"""
            Page Title: {self._get_page_title()}
            Task: {self._current_task}
            Scrollable: {self._is_scrollable()}
            Elements: {json.dumps(elements)}
            Newly Added Elements' ID: {json.dumps(added_ids)}
            """
        )

        # print(user_prompt)

        annotated_screenshot = self._get_screenshot()

        return {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': user_prompt,
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': raw_screenshot,
                    },
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': annotated_screenshot,
                    },
                },
            ]
        }

    def chat(
        self,
        message: str | ChatParameters,
        thread: Thread = None,
    ) -> str:
        task: str = message.task if isinstance(
            message, ChatParameters
        ) else message

        self._current_task = task

        if thread is None:
            thread = Thread()

        msg = thread.fork(task)

        msg.append(
            {
                'role': 'system',
                'content': self.system_role,
            }
        )

        msg.append(self._generate_user_prompt())

        response = self._call_llm(msg)
        msg.set_result(response)

        self._current_task = None

        return response

    def process_history(self, context: ThreadMessage) -> List[ChatCompletionMessageParam]:
        # TODO: optimize chat history
        # temporary workaround: delete previous user message
        messages = []
        last_user_msg_added = False

        for msg in reversed(context.messages):
            if isinstance(msg, dict):
                role = msg.get('role', None)
            else:
                role = msg.role

            if role != 'user':
                messages.insert(0, msg)
            elif not last_user_msg_added:
                last_user_msg_added = True
                messages.insert(0, msg)

        return messages

    def on_round_end(self, context: ThreadMessage) -> None:
        # update page info
        context.append(self._generate_user_prompt())

    @npi_tool
    def click(self, params: ClickParameters):
        """Click an element on the page"""

        self._init_observer()

        try:
            element = self._get_element_by_id(params.id)
            element.click()
        except TimeoutError:
            self.browser_app.page.evaluate(
                '(id) => npi.click(id)',
                params.id,
            )

        self._wait_for_stable()

        return f'Successfully clicked element with id: {params.id}'

    @npi_tool
    def fill(self, params: FillParameters):
        """Fill in an input field on the page"""

        self._init_observer()

        try:
            element = self._get_element_by_id(params.id)
            element.fill(params.value)
        except TimeoutError:
            self.browser_app.page.evaluate(
                '([id, value]) => npi.fill(id, value)',
                [params.id, params.value],
            )

        self._wait_for_stable()

        return f'Successfully filled value {params.value} into element with id: {params.id}'

    @npi_tool
    def select(self, params: FillParameters):
        """Select an option for a <select> element"""

        self._init_observer()

        try:
            element = self._get_element_by_id(params.id)
            element.select_option(params.value)
        except TimeoutError:
            self.browser_app.page.evaluate(
                '([id, value]) => npi.select(id, value)',
                [params.id, params.value],
            )

        self._wait_for_stable()

        return f'Successfully selected value {params.value} for element with id: {params.id}'

    @npi_tool
    def enter(self, params: FillParameters):
        """Press Enter on an input field. This action usually submits a form."""

        self._init_observer()

        try:
            element = self._get_element_by_id(params.id)
            element.press('Enter')
        except TimeoutError:
            self.browser_app.page.evaluate(
                '(id) => npi.enter(id)',
                params.id,
            )

        self._wait_for_stable()

        return f'Successfully pressed Enter on element with id: {params.id}'

    @npi_tool
    def scroll(self):
        """Scroll the page down to reveal more contents"""

        self._init_observer()

        self.browser_app.page.evaluate('() => npi.scrollPageDown()')

        self._wait_for_stable()

        return f'Successfully scrolled down to reveal more contents'
