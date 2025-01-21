# example_workflow.py
from auto_steps import step

@step(auto_implement=True, description="Add two numbers and return a dict with the sum.")
def add_numbers(a: int, b: int) -> dict:
    """
    The user wants a function that calculates a+b 
    and returns something like {'sum': a+b}.
    But currently, it's a stub. The framework should auto-implement it.
    """
    pass


@step(auto_implement=True, description="Multiply two numbers, returning {'product': a*b}.")
def multiply_numbers(a: int, b: int) -> dict:
    """
    Another stub step. 
    The framework should generate code returning {'product': a*b}.
    """
    pass
def do_some_workflow():
    print("=== Running example workflow ===")
    s1 = add_numbers(3, 5)
    print("[Workflow] add_numbers(3,5) returned:", s1)

    s2 = multiply_numbers(4, 6)
    print("[Workflow] multiply_numbers(4,6) returned:", s2)

    print("=== Example workflow complete ===")

if __name__ == "__main__":
    do_some_workflow()
