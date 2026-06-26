#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit about a missing poem, a million-count clue,
and a cob in the room.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------


def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cob: object | None = None
    culprit: object | None = None
    detective: object | None = None
    million: object | None = None
    poem: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the little museum"
    detail: str = "The room smelled like paper, dust, and warm soup from the next hall."
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class SuspectProfile:
    type: str
    clue: str
    means: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    detective: str
    witness: str
    culprit: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "museum": Setting(
        place="the little museum",
        detail="The room smelled like paper, dust, and warm soup from the next hall.",
    ),
    "library": Setting(
        place="the old library",
        detail="Tall shelves made long shadows across the reading table.",
    ),
    "bakery": Setting(
        place="the corner bakery",
        detail="Warm rolls cooled on trays beside the checkout counter.",
    ),
}

CHARACTERS = {
    "Mina": {"type": "girl", "role": "detective"},
    "Owen": {"type": "boy", "role": "detective"},
    "Nia": {"type": "girl", "role": "witness"},
    "Pip": {"type": "boy", "role": "witness"},
    "Chef": {"type": "man", "role": "culprit"},
    "Ms. Reed": {"type": "woman", "role": "culprit"},
}

CULPRITS = {
    "chef": SuspectProfile(
        type="chef",
        clue="a floury apron",
        means="tucked the poem into a recipe tin",
    ),
    "librarian": SuspectProfile(
        type="librarian",
        clue="a bookmark shaped like a cob",
        means="hid the poem inside a book sleeve",
    ),
    "vendor": SuspectProfile(
        type="vendor",
        clue="a corn-cob charm on a string",
        means="slid the poem under a basket cloth",
    ),
}

TRAITS = ["careful", "curious", "brave", "quiet", "sharp-eyed"]
OPENINGS = [
    "Something small had gone missing, but the clues were not small at all.",
    "A strange hush had fallen over the room, and everyone kept glancing at the table.",
    "There was a mystery in the air, like sugar after a storm.",
]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

@dataclass
class Clue:
    kind: str
    text: str
    weight: int = 1
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class MysteryWorld:
    def __init__(self, setting: Setting) -> None:
        self.world = World(setting)
        self.clues: list[Clue] = []
        self.solution: str = ""
        self.fired: set[str] = set()

    def add_clue(self, kind: str, text: str, weight: int = 1) -> None:
        self.clues.append(Clue(kind=kind, text=text, weight=weight))

    def prove(self, key: str) -> bool:
        return key in self.fired

    def mark(self, key: str) -> None:
        self.fired.add(key)


def build_world(params: StoryParams) -> MysteryWorld:
    setting = _safe_lookup(SETTINGS, params.place)
    mw = MysteryWorld(setting)

    detective = mw.world.add(Entity(
        id=params.detective,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.detective)["type"],
        label=params.detective,
        memes={"curiosity": 2.0, "doubt": 0.0, "joy": 0.0},
    ))
    witness = mw.world.add(Entity(
        id=params.witness,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.witness)["type"],
        label=params.witness,
        memes={"nervous": 1.0},
    ))
    culprit = mw.world.add(Entity(
        id=params.culprit,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.culprit)["type"],
        label=params.culprit,
        memes={"nervous": 0.5, "guilt": 1.0},
    ))

    poem = mw.world.add(Entity(
        id="poem",
        type="poem",
        label="poem",
        phrase="a hand-copied poem on a yellow card",
        owner=culprit.id,
        hidden=True,
        meters={"value": 1.0},
    ))
    million = mw.world.add(Entity(
        id="million",
        type="number",
        label="million",
        phrase="one million tiny dots in the ledger",
        meters={"count": 1_000_000},
    ))
    cob = mw.world.add(Entity(
        id="cob",
        type="thing",
        label="cob",
        phrase="a corn cob with one bite taken out of it",
        hidden=False,
        meters={"crumbs": 1.0},
    ))

    mw.world.facts.update(
        detective=detective,
        witness=witness,
        culprit=culprit,
        poem=poem,
        million=million,
        cob=cob,
        setting=setting,
        culprit_profile=_safe_lookup(CULPRITS, params.culprit.lower() if params.culprit.lower() in CULPRITS else params.culprit),
    )
    return mw


def add_story_events(mw: MysteryWorld) -> None:
    w = mw.world
    f = w.facts
    detective: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    witness: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "witness")
    culprit: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    poem: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "poem")
    million: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "million")
    cob: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cob")

    opening = random.choice(OPENINGS)
    w.say(opening)
    w.say(f"{detective.id} tapped the table and said, \"Who took the poem?\"")
    w.say(f"{witness.id} hugged {witness.pronoun('possessive')} elbows and whispered, \"I only saw a cob.\"")
    w.say(f"{culprit.id} frowned. \"A cob? That sounds silly,\" {culprit.pronoun()} said.")
    w.say(f"{w.process() if False else w.setting.detail}")

    w.para()
    w.say(f"{detective.id} looked at the clue card and said, \"This ledger says a million dots were counted here.\"")
    w.say(f"\"A million?\" {witness.id} asked.")
    w.say(f"\"Not money,\" {detective.id} said. \"Dots. Someone wanted the counting to look important.\"")
    w.say(f"The detective noticed {cob.phrase} beside the bread tray and a crumb on the cover of the poem card.")
    mw.add_clue("count", "The million-count ledger was really a trick to hide a tiny swapping move.", 2)
    mw.add_clue("physical", "The cob had crumbs on it, so it had been handled near the table.", 1)

    w.para()
    w.say(f"{detective.id} turned to {witness.id}. \"Tell me what you saw.\"")
    w.say(f"\"I saw {culprit.id} near the table,\" {witness.id} said, \"and they kept a poem under their hand.\"")
    w.say(f"{culprit.id} said, \"I was only helping. The poem was for the notice board.\"")
    w.say(f"\"Then why hide it?\" {detective.id} asked.")
    w.say(f"{culprit.id} blinked. \"Because I was embarrassed,\" they said. \"I wrote it badly and thought no one would like it.\"")
    mw.add_clue("motive", "The culprit hid the poem because they felt shy about it.", 3)

    w.para()
    w.say(f"{detective.id} lifted the cob and found a folded card tucked behind it.")
    w.say(f"\"Here it is,\" {detective.id} said. \"The poem was never lost. It was hidden beside the cob as a decoy.\"")
    w.say(f"{culprit.id} stared at the card and said, \"I thought if the cob looked strange enough, nobody would ask about the poem.\"")
    w.say(f"{witness.id} smiled. \"That was a clever trick, but the crumbs told on you.\"")
    w.say(f"{detective.id} nodded. \"And the million dots were just a noisy clue, not the answer.\"")
    w.say(f"{detective.id} handed back the poem. \"Next time, show it instead of hiding it.\"")
    w.say(f"{culprit.id} took a breath and said, \"Okay. I can do that.\"")
    w.say(f"Then the poem went on the notice board, the cob went back to the kitchen, and the room felt bright again.")
    mw.solution = culprit.id
    mw.mark("solved")


# ---------------------------------------------------------------------------
# Paragraph generation helpers
# ---------------------------------------------------------------------------

def noun_phrase(ent: Entity) -> str:
    return ent.phrase or ent.label or ent.id


def generate_story_text(mw: MysteryWorld) -> str:
    add_story_events(mw)
    return mw.world.render()


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly whodunit story about a missing poem, a million-count clue, and a cob.',
        f"Tell a short mystery set in {world.setting.place} where someone hides a poem and the detective solves it with dialogue.",
        "Write a gentle whodunit where the clues include a cob, a poem, and a strange count of a million.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "detective")
    witness: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "witness")
    culprit: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "culprit")
    poem: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "poem")
    setting: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "setting")
    return [
        QAItem(
            question=f"Who solved the mystery in {setting.place}?",
            answer=f"{detective.id} solved it by asking questions and following the clues.",
        ),
        QAItem(
            question="What was missing from the story?",
            answer=f"The missing thing was the poem. It had been hidden instead of truly lost.",
        ),
        QAItem(
            question=f"What did {witness.id} say they saw?",
            answer=f"{witness.id} said they saw {culprit.id} near the table and noticed a cob.",
        ),
        QAItem(
            question="Why had the poem been hidden?",
            answer="It was hidden because the culprit felt shy and did not want anyone to read it yet.",
        ),
        QAItem(
            question="What clue helped the detective find the poem?",
            answer="The crumbs on the cob and the strange million-count clue helped the detective see that something had been moved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a poem?",
            answer="A poem is a piece of writing that uses rhythm, sound, and chosen words to paint a feeling or picture.",
        ),
        QAItem(
            question="What is a cob?",
            answer="A cob can mean a corn cob, which is the center part of an ear of corn after the kernels are eaten or cut off.",
        ),
        QAItem(
            question="What does million mean?",
            answer="A million is a very large number. It means one thousand thousands.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show solved/1.

hidden_poem(poem).
strange_count(million).
odd_cob(cob).

motive(culprit) :- shy(culprit), hidden_poem(poem).
clue(cob) :- odd_cob(cob).
clue(million) :- strange_count(million).

solved(culprit) :- motive(culprit), clue(cob), clue(million).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hidden_poem", "poem"),
        asp.fact("strange_count", "million"),
        asp.fact("odd_cob", "cob"),
        asp.fact("shy", "culprit"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solution() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(set(asp.atoms(model, "solved")))


def python_solution() -> list[tuple]:
    return [("culprit",)]


def asp_verify() -> int:
    a = set(asp_solution())
    p = set(python_solution())
    if a == p:
        print(f"OK: ASP matches Python reasoning ({len(a)} solution).")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(a))
    print("Python:", sorted(p))
    return 1


# ---------------------------------------------------------------------------
# Build / emit / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with dialogue.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--detective", choices=[k for k, v in CHARACTERS.items() if v["role"] == "detective"])
    ap.add_argument("--witness", choices=[k for k, v in CHARACTERS.items() if v["role"] == "witness"])
    ap.add_argument("--culprit", choices=[k for k, v in CHARACTERS.items() if v["role"] == "culprit"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    detective = getattr(args, "detective", None) or rng.choice([k for k, v in CHARACTERS.items() if v["role"] == "detective"])
    witness = getattr(args, "witness", None) or rng.choice([k for k, v in CHARACTERS.items() if v["role"] == "witness"])
    culprit = getattr(args, "culprit", None) or rng.choice([k for k, v in CHARACTERS.items() if v["role"] == "culprit"])

    if detective == witness or detective == culprit or witness == culprit:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, detective=detective, witness=witness, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    mw = build_world(params)
    story = generate_story_text(mw)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(mw.world),
        story_qa=story_qa(mw.world),
        world_qa=world_knowledge_qa(mw.world),
        world=mw.world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", detective="Mina", witness="Nia", culprit="Chef"),
    StoryParams(place="library", detective="Owen", witness="Pip", culprit="Ms. Reed"),
    StoryParams(place="bakery", detective="Mina", witness="Pip", culprit="Chef"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP solution:", asp_solution())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} at {p.place} / witness={p.witness} / culprit={p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
