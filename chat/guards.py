import random
import string


def create_guard(length=80):
    guard = "".join(random.choices(string.ascii_letters, k=length))
    return guard
