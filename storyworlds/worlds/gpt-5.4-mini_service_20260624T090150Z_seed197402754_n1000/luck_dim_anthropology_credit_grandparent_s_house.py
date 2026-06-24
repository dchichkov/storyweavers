#!/usr/bin/env python3
"""
A small storyworld: at a grandparent's house, a child follows a dim little clue,
remembers an old flashback, and learns what real credit means.

The style is intended to feel like a gentle ghost story: quiet rooms, soft
sounds, one small mystery, and an ending that proves the feeling changed.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    gp: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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


@dataclass
class Setting:
    place: str = "grandparent's house"
    rooms: list[str] = field(default_factory=lambda: ["front room", "hall", "attic"])
    tone: str = "quiet"
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
class Clue:
    id: str
    label: str
    phrase: str
    glow: str
    history: str
    kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    flashback_used: bool = False

    w: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.flashback_used = self.flashback_used
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "grandparents_house": Setting(place="grandparent's house"),
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Owen", "Luna", "Theo"]
GRANDPARENT_NAMES = ["Grandma", "Grandpa"]

CLUES = {
    "coin": Clue(
        id="coin",
        label="old coin",
        phrase="a dime-dark coin with a soft shine",
        glow="dim",
        history="from long ago",
        kind="coin",
        tags={"luck-dim", "credit"},
    ),
    "birdcard": Clue(
        id="birdcard",
        label="library card",
        phrase="a creased card with a bird stamp",
        glow="dim",
        history="from a little museum trip",
        kind="card",
        tags={"anthropology", "credit"},
    ),
    "shell": Clue(
        id="shell",
        label="shell charm",
        phrase="a shell charm tied with a string",
        glow="dim",
        history="from the seaside",
        kind="shell",
        tags={"luck-dim", "anthropology"},
    ),
}

GENRES = ["luck-dim", "anthropology", "credit"]

CURATED = [
    ("grandparents_house", "coin", "Maya", "Grandma"),
    ("grandparents_house", "birdcard", "Leo", "Grandpa"),
    ("grandparents_house", "shell", "Nina", "Grandma"),
]


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    grandparent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story style tale at a grandparent's house."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--grandparent", choices=GRANDPARENT_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "grandparents_house"
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    gp = getattr(args, "grandparent", None) or rng.choice(GRANDPARENT_NAMES)
    return StoryParams(place=place, clue=clue, name=name, grandparent=gp)


def _flashback(world: World, child: Entity, clue: Clue) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    world.say(
        f"For a blink, {child.id} remembered another night, when the same little "
        f"{clue.label} had been held up to the lamp and looked almost alive."
    )
    world.say(
        f"In that old flashback, {child.id} had heard {child.pronoun('possessive')} "
        f"{world.facts['grandparent'].label} say that some things keep a story in them."
    )


def _do_night(world: World, child: Entity, gp: Entity, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    child.memes["unease"] += 1
    world.say(
        f"That evening, {child.id} stayed at {world.setting.place} while the house "
        f"grew quiet and the hall clock made a tiny click in the dark."
    )
    world.say(
        f"On the shelf, {clue.phrase} gave off a {clue.glow} shine, and {child.id} "
        f"kept looking at it as if it were calling from another room."
    )
    _flashback(world, child, clue)
    if clue.kind == "coin":
        child.memes["luck"] += 1
        world.facts["luck_dim"] = True
        world.say(
            f"{child.id} thought the coin looked like luck, but it was a dim sort of luck: "
            f"small, quiet, and easy to miss unless someone cared to notice."
        )
    elif clue.kind == "birdcard":
        child.memes["history"] += 1
        world.facts["anthropology"] = True
        world.say(
            f"{child.id} wondered why a card could feel so old. {gp.id} explained that "
            f"anthropology is the study of people, their things, and the traces they leave behind."
        )
    else:
        child.memes["wonder"] += 1
        world.facts["anthropology"] = True
        world.say(
            f"The shell charm felt like a tiny museum piece, and {child.id} guessed it had "
            f"crossed many hands before it reached this shelf."
        )


def _ask_credit(world: World, child: Entity, gp: Entity, clue: Clue) -> None:
    child.memes["worry"] += 1
    world.say(
        f"At last, {child.id} picked up the clue and asked, \"Who should get credit for it?\""
    )
    world.say(
        f"{gp.id} smiled in the lamplight and said that credit means naming the person who found "
        f"something, made something, or helped keep it safe."
    )
    world.say(
        f"{gp.id} added that real credit is not a spooky prize; it is a fair way to remember who did what."
    )
    world.facts["credit"] = True


def _resolve(world: World, child: Entity, gp: Entity, clue: Clue) -> None:
    child.memes["unease"] = 0.0
    child.memes["pride"] += 1
    world.say(
        f"{child.id} then put the {clue.label} back where it belonged and gave {gp.id} the credit "
        f"for telling the story behind it."
    )
    world.say(
        f"The house felt warmer after that. The little {clue.label} still looked dim, but it no longer looked lonely."
    )


def generate_story(world: World, child: Entity, gp: Entity, clue: Clue) -> None:
    world.say(
        f"{child.id} was visiting {world.setting.place} with {gp.id}, where the rooms were quiet "
        f"and every shadow seemed to listen."
    )
    world.say(
        f"{child.id} found {clue.phrase} on a shelf and leaned close, because the shine was so {clue.glow} "
        f"that it felt like a secret."
    )
    _do_night(world, child, gp, clue)
    world.para()
    _ask_credit(world, child, gp, clue)
    world.para()
    _resolve(world, child, gp, clue)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle ghost story set at a grandparent's house where a child finds a dim clue and learns about credit.",
        f"Tell a spooky-but-kind story about {f['child'].id} and {f['grandparent'].id} at {world.setting.place}.",
        "Write a child-friendly story that includes a flashback, anthropology, and the idea of giving credit fairly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    gp = _safe_fact(world, world.facts, "grandparent")
    clue = _safe_fact(world, world.facts, "clue")
    return [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place at {world.setting.place}, where {c.id} is visiting {gp.id}.",
        ),
        QAItem(
            question=f"What did {c.id} find on the shelf?",
            answer=f"{c.id} found {clue.phrase} on the shelf, and it looked very {clue.glow}.",
        ),
        QAItem(
            question=f"What did the flashback help {c.id} remember?",
            answer=f"The flashback helped {c.id} remember that the little {clue.label} had a history and a story attached to it.",
        ),
        QAItem(
            question=f"What does credit mean in the story?",
            answer=f"Credit means naming the person who found something, made something, or helped keep it safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is anthropology?",
            answer="Anthropology is the study of people, their lives, their things, and the traces they leave behind.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, like a soft little light in a quiet room.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered piece of the past that briefly returns to the present story.",
        ),
        QAItem(
            question="What does it mean to give credit?",
            answer="To give credit means to fairly say who did the work, found the thing, or helped make it happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
clue_kind(coin, luck_dim).
clue_kind(birdcard, anthropology).
clue_kind(birdcard, credit).
clue_kind(shell, luck_dim).
clue_kind(shell, anthropology).
clue_kind(coin, credit).

interesting(C) :- clue_kind(C, luck_dim).
interesting(C) :- clue_kind(C, anthropology).
interesting(C) :- clue_kind(C, credit).

valid_story(Place, Clue) :- setting(Place), clue(Clue), interesting(Clue), place_ok(Place).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "grandparents_house"), asp.fact("place_ok", "grandparents_house")]
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {("grandparents_house", cid) for cid in CLUES if _safe_lookup(CLUES, cid).tags & {"luck-dim", "anthropology", "credit"}}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) != "grandparents_house":
        pass
    place = "grandparents_house"
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    gp = getattr(args, "grandparent", None) or rng.choice(GRANDPARENT_NAMES)
    return StoryParams(place=place, clue=clue, name=name, grandparent=gp)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Maya", "Nina", "Luna"} else "boy"))
    gp = world.add(Entity(id=params.grandparent, kind="character", type="grandmother" if params.grandparent == "Grandma" else "grandfather"))
    clue = _safe_lookup(CLUES, params.clue)
    world.facts.update(child=child, grandparent=gp, clue=clue)
    generate_story(world, child, gp, clue)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} valid story seeds:")
        for place, clue in combos:
            print(f"  {place} {clue}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, clue, name, gp in CURATED:
            samples.append(generate(StoryParams(place=place, clue=clue, name=name, grandparent=gp, seed=base_seed)))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_combo(args, random.Random(seed))
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
            header = f"### {p.name} at {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
