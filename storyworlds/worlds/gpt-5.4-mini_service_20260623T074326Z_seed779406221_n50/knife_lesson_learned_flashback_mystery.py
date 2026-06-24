#!/usr/bin/env python3
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

TITLE_WORDS = ["mystery", "flashback", "lesson"]
SENSE_MIN = 2
THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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

@dataclass
class StoryParams:
    setting: str
    investigator: str
    friend: str
    adult: str
    object: str = "knife"
    clue: str = "missing jam"
    memory: str = "the kitchen"
    lesson: str = "knives belong with grown-ups"
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def flashback_hint(world: World, params: StoryParams) -> None:
    world.say(
        f"Earlier that day, {params.investigator} had seen {params.adult} in {params.setting} "
        f"using a knife to cut fruit for a snack. The memory came back in a quick flash, "
        f"but only the safe part."
    )
    world.get("investigator").memes["curiosity"] += 1


def clue_scene(world: World, params: StoryParams) -> None:
    world.say(
        f"In the quiet of {params.setting}, {params.investigator} and {params.friend} found a small mystery: "
        f"{params.clue} was gone, and a shiny {params.object} lay nearby."
    )
    world.say(
        f"{params.friend} frowned. \"Something does not fit,\" they whispered, and the room felt still."
    )


def warning(world: World, params: StoryParams) -> None:
    world.say(
        f"{params.friend} pointed to the {params.object}. \"That's not for kids,\" they said. "
        f"\"Let's ask {params.adult} instead.\""
    )
    world.get("friend").memes["caution"] += 1


def lesson_scene(world: World, params: StoryParams) -> None:
    world.say(
        f"{params.adult} came over right away and took the knife with a calm hand. "
        f"\"Lesson learned,\" {params.adult} said softly. \"Knives are tools, not toys.\""
    )
    world.say(
        f"Then {params.adult} showed them how to look for clues with their eyes, not their hands."
    )
    world.get("investigator").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    world.get("investigator").memes["lesson"] += 1
    world.get("friend").memes["lesson"] += 1


def solve_mystery(world: World, params: StoryParams) -> None:
    world.say(
        f"At last, the missing {params.clue} turned out to be in a bowl on the counter, "
        f"hidden behind a napkin. The knife had nothing to do with it."
    )
    world.say(
        f"{params.investigator} felt proud for solving the mystery the safe way, and the kitchen "
        f"looked ordinary again."
    )


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="investigator", kind="character", label=params.investigator, role="investigator"))
    world.add(Entity(id="friend", kind="character", label=params.friend, role="friend"))
    world.add(Entity(id="adult", kind="character", label=params.adult, role="adult"))
    world.add(Entity(id="knife", kind="thing", label="knife"))
    world.add(Entity(id="room", kind="place", label=params.setting))
    world.facts["setting"] = params.setting
    world.facts["object"] = params.object
    world.facts["clue"] = params.clue
    world.facts["memory"] = params.memory
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    clue_scene(world, params)
    world.para()
    flashback_hint(world, params)
    world.para()
    warning(world, params)
    world.para()
    lesson_scene(world, params)
    world.para()
    solve_mystery(world, params)
    world.facts["lesson_learned"] = True
    return world


SETTINGS = [
    "the sunny kitchen",
    "the old cabin",
    "the little classroom",
    "the hallway by the coat rack",
]

NAMES = ["Mia", "Noah", "Luna", "Eli", "Zoe", "Finn", "Ava", "Theo", "Nora", "Max"]
ADULTS = ["Mom", "Dad", "Aunt June", "Mr. Lee"]


def valid_settings() -> list[str]:
    return list(SETTINGS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with a knife, a flashback, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--investigator")
    ap.add_argument("--friend")
    ap.add_argument("--adult", choices=ADULTS)
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
    setting = getattr(args, "setting", None) or rng.choice(SETTINGS)
    investigator = getattr(args, "investigator", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != investigator])
    adult = getattr(args, "adult", None) or rng.choice(ADULTS)
    if investigator == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, investigator=investigator, friend=friend, adult=adult, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    prompts = [
        f"Write a short mystery story set in {params.setting} where {params.investigator} notices a knife and learns a safety lesson.",
        f"Tell a child-facing mystery with a flashback that shows why a knife belongs with {params.adult}.",
        f"Make the ending prove that {params.investigator} and {params.friend} solved the mystery and learned a lesson.",
    ]
    story_qa = [
        QAItem(
            question="What made the story feel like a mystery?",
            answer=f"The children noticed something odd in {params.setting}: the missing {params.clue} and the knife nearby made them wonder what happened.",
        ),
        QAItem(
            question="What was the flashback about?",
            answer=f"The flashback showed {params.adult} using a knife safely to cut fruit, which helped {params.investigator} remember that knives are tools.",
        ),
        QAItem(
            question="What lesson did the children learn?",
            answer=f"They learned that {params.object}s belong with grown-ups and are not toys, so they should ask {params.adult} for help.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a knife for?",
            answer="A knife is a tool used for cutting. Grown-ups should handle it carefully because it can hurt someone if it is used the wrong way.",
        ),
        QAItem(
            question="Why can a knife be dangerous?",
            answer="A knife has a sharp edge, so it can cut skin quickly. That is why children should not play with one.",
        ),
        QAItem(
            question="What should children do when they find something dangerous?",
            answer="They should stop, stay safe, and ask a grown-up for help right away.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id}: {e.kind} " + " ".join(bits))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(setting="the sunny kitchen", investigator="Mia", friend="Noah", adult="Mom"),
    StoryParams(setting="the old cabin", investigator="Luna", friend="Eli", adult="Dad"),
    StoryParams(setting="the little classroom", investigator="Zoe", friend="Finn", adult="Mr. Lee"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ADULTS:
        lines.append(asp.fact("adult", a))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
ok_story(S) :- setting(S), sense_min(M), M >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


def resolve_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if getattr(args, "all", None):
        return list(CURATED)
    return [resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i)) for i in range(getattr(args, "n", None))]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program(show="#show ok_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 20:
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(p)
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
