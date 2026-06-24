#!/usr/bin/env python3
"""
storyworlds/worlds/knife_lesson_learned_flashback_mystery.py
============================================================

A small mystery storyworld about a knife, a worrying discovery, a flashback,
and a lesson learned. The domain stays child-facing and state-driven: a clue is
found, suspicion rises, a memory explains the clue, and the ending proves what
changed.

The source tale to imagine:
---
A child finds a knife on the kitchen table and thinks someone forgot it there.
They get worried because the knife looks sharp and the room feels mysterious.
Then they remember a flashback: earlier, a grown-up had used the knife to cut
string for a craft project and had put it down for a moment while making lunch.
The child calls the grown-up, learns the knife was never left out by mistake,
and hears the lesson that knives are for grown-ups and must be handled with care.
The story ends with the knife safely put away and the child feeling wiser.

World shape:
- A small mystery domain with one child, one grown-up, one knife, and one clue.
- Physical meters track "sharp", "found", "moved", and "stored" states.
- Emotional memes track "curious", "worried", "relieved", and "lesson".
- A flashback beat reveals why the knife was out.
- A lesson-learned beat resolves the mystery and changes the ending image.

This file follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    drawer: object | None = None
    knife: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
class Place:
    name: str = "the kitchen"
    clue_spot: str = "the kitchen table"
    world: object | None = None
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    c: object | None = None
    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


KNOWLEDGE = {
    "knife": [
        ("What is a knife?",
         "A knife is a sharp tool used by grown-ups to cut food and other things carefully."),
        ("Why should children be careful around knives?",
         "Knives are sharp, so children should let a grown-up handle them to avoid getting hurt."),
    ],
    "flashback": [
        ("What is a flashback in a story?",
         "A flashback is a scene that shows something that happened earlier, before the present part of the story."),
    ],
    "lesson": [
        ("What does it mean to learn a lesson?",
         "It means you understand something important and remember to do better next time."),
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is a story about something puzzling that needs to be explained."),
    ],
}
KNOWLEDGE_ORDER = ["mystery", "flashback", "knife", "lesson"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about a knife, a flashback, and a lesson learned.")
    ap.add_argument("--child-name", choices=["Maya", "Leo", "Nina", "Owen"])
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name", choices=["Mom", "Dad"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    child = getattr(args, "child_name", None) or rng.choice(["Maya", "Nina"] if gender == "girl" else ["Leo", "Owen"])
    parent_gender = getattr(args, "parent_gender", None) or rng.choice(["mother", "father"])
    parent = getattr(args, "parent_name", None) or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(child_name=child, child_gender=gender, parent_name=parent, parent_gender=parent_gender)


ASP_RULES = r"""
knife_seen :- found(knife).
curious_rises :- knife_seen.
flashback_seen :- flashback(reveal).
lesson_done :- flashback_seen, stored(knife).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("entity", "knife"),
        asp.fact("entity", "child"),
        asp.fact("entity", "parent"),
        asp.fact("setting", "kitchen"),
        asp.fact("flashback", "reveal"),
        asp.fact("story_kind", "mystery"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _make_world(params: StoryParams) -> World:
    world = World(Place())
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label=params.parent_name))
    knife = world.add(Entity(id="knife", kind="thing", type="knife", label="knife", phrase="a shiny kitchen knife"))
    drawer = world.add(Entity(id="drawer", kind="thing", type="drawer", label="drawer"))

    child.memes.update(curious=1.0)
    knife.meters.update(sharp=1.0, found=0.0, moved=0.0, stored=0.0)
    world.facts.update(child=child, parent=parent, knife=knife, drawer=drawer)
    return world


def _flashback(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    knife = world.get("knife")
    child.memes["worried"] += 1.0
    world.say(
        f"{child.label} paused beside {world.place.clue_spot} and saw {knife.label} lying there."
    )
    world.say(
        f"It looked mysterious, and {child.pronoun()} wondered why a sharp knife was out in the open."
    )
    world.para()
    world.say(
        f"Then a flashback came to mind: earlier, {parent.label} had used the knife to cut string for a craft, "
        f"then set it down for a moment while getting lunch ready."
    )
    world.say(
        f"That memory solved the puzzle. The knife had not been forgotten by a careless stranger; it had been used for a normal grown-up job."
    )


def _resolution(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    knife = world.get("knife")
    child.memes["relieved"] += 1.0
    child.memes["lesson"] += 1.0
    knife.meters["found"] = 1.0
    knife.meters["moved"] = 1.0
    knife.meters["stored"] = 1.0
    world.say(
        f"{child.label} called for {parent.label} right away instead of touching the knife."
    )
    world.say(
        f"{parent.label} smiled, took the knife, and put it safely in the drawer."
    )
    world.say(
        f'"Knives are for grown-ups," {parent.label} said. "{child.label}, you did the right thing by asking."'
    )
    world.say(
        f"{child.label} felt proud to have solved the mystery the safe way, and the kitchen was ordinary again."
    )


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    child = world.get("child")
    knife = world.get("knife")

    child.memes["curious"] += 1.0
    knife.meters["found"] = 1.0
    world.say(
        f"One quiet morning, {child.label} was in {world.place.name} when {child.pronoun()} noticed {knife.phrase} on {world.place.clue_spot}."
    )
    world.say(
        f"The sight made {child.label} curious and a little worried, because the knife was sharp and did not belong where anyone could reach it."
    )
    world.para()
    _flashback(world)
    world.para()
    _resolution(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, knife = f["child"], f["parent"], f["knife"]
    return [
        QAItem(
            question=f"What mystery did {child.label} notice in the kitchen?",
            answer=f"{child.label} noticed a shiny kitchen knife on the kitchen table and wondered why it was there.",
        ),
        QAItem(
            question="What memory explained the knife?",
            answer=f"A flashback showed that {parent.label} had used the knife earlier to cut string for a craft and had set it down while getting lunch ready.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer=f"{child.label} learned that knives are for grown-ups and that it is safest to call an adult instead of touching a sharp knife.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short mystery story for a young child that includes a knife, a flashback, and a lesson learned.',
        f"Tell a gentle kitchen mystery where {f['child'].label} finds a knife, remembers an earlier flashback, and learns to ask a grown-up for help.",
        "Write a child-facing story that explains a puzzling knife on a table and ends with the knife safely put away.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(child_name="Maya", child_gender="girl", parent_name="Mom", parent_gender="mother"),
    StoryParams(child_name="Leo", child_gender="boy", parent_name="Dad", parent_gender="father"),
]


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show knife_seen/0.\n#show flashback_seen/0.\n#show lesson_done/0.")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    if {"knife_seen", "flashback_seen", "lesson_done"}.issubset(atoms):
        print("OK: ASP twin contains the mystery, flashback, and lesson facts.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected facts.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show knife_seen/0.\n#show flashback_seen/0.\n#show lesson_done/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show knife_seen/0.\n#show flashback_seen/0.\n#show lesson_done/0."))
        print("Derived atoms:", ", ".join(sorted(sym.name for sym in model)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
