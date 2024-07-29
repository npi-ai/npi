from npiai import FunctionTool, function


class MyTool(FunctionTool):
    def __init__(self):
        super().__init__(
            name="Fibonacci",
            description="My first NPi tool",
        )

    @function
    def fibonacci(self, n: int) -> int:
        """
        Get the nth Fibonacci number.

        Args:
            n: The index of the Fibonacci number in the sequence.
        """
        if n == 0:
            return 0
        if n == 1:
            return 1
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)
