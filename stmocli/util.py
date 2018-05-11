import re


def name_to_stub(name):
    """
    Makes a filename-safe stub from an arbitrary title.

    Ex.: "My Life (And Hard Times)" -> "my_life_and_hard_times"
    """
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
