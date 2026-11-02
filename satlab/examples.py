"""Invented input counts for learning. These are not student observations."""
from .model import Counts


def example_modules():
    return {
        "rw": [Counts(confident=19, guess2=4, guess3=2, guess4=1, wrong=1),
               Counts(confident=16, guess2=5, guess3=3, guess4=2, wrong=1)],
        "math": [Counts(confident=14, guess2=2, guess3=1, guess4=1, fill_right=2, fill_wrong=1, fill_uncertain=1),
                 Counts(confident=12, guess2=3, guess3=1, guess4=1, fill_right=2, fill_wrong=1, fill_uncertain=1, wrong=1)],
    }
