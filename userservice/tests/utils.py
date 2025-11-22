import random
import string


def random_string(n: int = 32) -> str:
    """
    Generate a random string of a specified length using ASCII letters.

    This function generates a string composed of randomly chosen ASCII letters.
    The input parameter defines the length of the string.

    Args:
        n (int): The length of the random string to generate.

    Returns:
        str: A string containing `n` randomly chosen ASCII letters.
    """
    return "".join(random.choices(string.ascii_letters, k=n))


def random_email() -> str:
    """
    Generates and returns a random email address.

    The email address is constructed with a random string for the username
    and `example` for the domain name, followed by the `.com` TLD.

    Returns:
        str: A randomly generated email address.
    """
    return f"{random_string(8)}@example.com"