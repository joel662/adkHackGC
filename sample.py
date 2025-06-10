# sample_module.py

def add(a, b):
    """Adds two numbers."""
    return a + b

def divide(a, b):
    """Divides a by b, raises error if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def greet(name):
    """Returns a greeting message."""
    return f"Hello, {name}!"
