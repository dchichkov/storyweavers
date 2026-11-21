"""Typed feature structures; all surfaces are existing weighted grammar Nodes."""
from dataclasses import dataclass
from ..grammar import Node


@dataclass(frozen=True)
class Agreement:
    number: str = "singular"
    person: int = 3

    def __post_init__(self):
        if self.number not in {"singular", "plural"} or self.person not in {1, 2, 3}:
            raise ValueError("invalid agreement")

    @property
    def third_singular(self):
        return self.number == "singular" and self.person == 3


@dataclass(frozen=True)
class CN:
    singular: Node
    plural: Node
    mass: bool = False


@dataclass(frozen=True)
class NP:
    subject: Node
    object: Node
    possessive: Node
    agreement: Agreement = Agreement()


@dataclass(frozen=True)
class AP:
    node: Node


@dataclass(frozen=True)
class Adv:
    node: Node


@dataclass(frozen=True)
class Verb:
    base: str
    third: str
    past: str
    participle: str
    gerund: str
    valencies: tuple[str, ...]


@dataclass(frozen=True)
class VP:
    verb: Verb
    tail: Node
    label: str
    auxiliary: str = ""


@dataclass(frozen=True)
class Clause:
    subject: NP
    predicate: VP


@dataclass(frozen=True)
class Sentence:
    node: Node


def require(value, expected):
    if not isinstance(value, expected):
        raise TypeError(f"expected {expected.__name__}, got {type(value).__name__}")
    return value
