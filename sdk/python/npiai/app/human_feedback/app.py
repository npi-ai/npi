from npiai.core import App, npi_tool


class HumanFeedback(App):
    def __init__(self):
        super().__init__(
            name='human_feedback',
            description='Ask human for confirmation or additional information',
        )

    @npi_tool
    async def ask_human(self, question: str) -> str:
        """
        Ask the user to provide additional information.
        You should call this method if some information is missing.

        Args:
            question: The question to ask.
        """
        return await self.hitl.input(self.name, question)

    @npi_tool
    async def confirm_action(self, action: str) -> str:
        """
        Ask the user to confirm your action.
        You should call this method if you are preforming some critical actions such as placing an order.

        Args:
            action: The action to confirm.
        """
        approved = await self.hitl.confirm(self.name, action)

        return 'Approved' if approved else 'Rejected'
