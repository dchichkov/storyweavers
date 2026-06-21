#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glee_defend_repetition_animal_story.py
======================================================================

A standalone story world for a tiny animal tale about glee, defend, and
repetition.

Premise
-------
A small animal friend keeps repeating a proud trick during a playtime outing.
Another animal worries that the repeated move will cause trouble, then defends
the little one when a bigger animal blames them unfairly. The repeated pattern
leads to a wobble, a rescue, and a warm ending where the animals repeat a safer
game instead.

The world is built to be:
- small and classical
- state-driven rather than paragraph-swapped
- child-facing and concrete
- compatible with the shared StorySample / QAItem result API
- checked by a Python reasonableness gate plus an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    surface: str
    sound: str
    movement: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Animal:
    id: str
    species: str
    label: str
    plural_label: str
    action: str
    repeated_action: str
    glee_line: str
    role: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Trouble:
    id: str
    label: str
    warning: str
    wobble: str
    risk: str
    cause: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Defense:
    id: str
    label: str
    action: str
    fix: str
    ending_image: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["repeating"] < THRESHOLD:
            continue
        sig = ("wobble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["wobbly"] += 1
        e.memes["alarm"] += 1
        out.append("__wobble__")
    return out


def _r_defend(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["defended"] < THRESHOLD:
            continue
        sig = ("defend", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["brave"] += 1
        out.append("__defend__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("wobble", "physical", _r_wobble),
    Rule("defend", "social", _r_defend),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(animal: Animal, trouble: Trouble, defense: Defense) -> bool:
    return trouble.id in animal.tags and defense.power >= 1 and defense.sense >= 2


def repeated_risk(setting: Setting, animal: Animal, trouble: Trouble) -> bool:
    return setting.id in trouble.tags and trouble.id in animal.tags


def trouble_severity(repeat_count: int) -> int:
    return 1 + max(0, repeat_count - 1)


def can_hold(defense: Defense, repeat_count: int) -> bool:
    return defense.power >= trouble_severity(repeat_count)


def tell_tale(world: World, setting: Setting, animal: Animal, buddy: Entity,
              trouble: Trouble, defense: Defense, repeat_count: int,
              smaller_name: str, bigger_name: str) -> World:
    small = world.add(Entity(id=smaller_name, kind="character", type="animal",
                             label=animal.label, traits=["small"], role="trickster"))
    big = world.add(Entity(id=bigger_name, kind="character", type="animal",
                           label=buddy.label, traits=["big"], role="defender"))
    adult = world.add(Entity(id="Ranger", kind="character", type="adult",
                             label="the ranger", role="adult"))

    small.memes["glee"] = 1
    small.meters["repeating"] = float(repeat_count)
    big.memes["watchful"] = 1

    world.say(
        f"At {setting.place}, {small.id} was a little {animal.label} with so much glee. "
        f"{animal.glee_line} {animal.glee_line}"
    )
    world.say(
        f"{small.id} liked to {animal.action} again and again. Again and again, "
        f"{small.id} went {animal.repeated_action}."
    )
    world.say(
        f"Nearby, {big.id} listened and frowned. \"Again and again is fun,\" "
        f"{big.id} said, \"but it can lead to {trouble.warning}.\""
    )

    if not repeated_risk(setting, animal, trouble):
        raise StoryError("This setting and trouble do not fit together.")

    world.para()
    small.meters["repeating"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{small.id} did it one more time. This time, {trouble.wobble}."
    )
    world.say(
        f"\"{small.id}!\" shouted {big.id}. \"{trouble.label}!\""
    )
    big.memes["defended"] += 1
    world.say(
        f"Then {big.id} stepped in front and said, \"It was only a game. "
        f"Do not blame {small.id}. {big.id} will defend {small.id}.\""
    )

    if can_hold(defense, repeat_count):
        world.para()
        world.say(
            f"{adult.id} came walking over, saw the wobble, and used {defense.action}. "
            f"{defense.fix}"
        )
        world.say(
            f"{small.id} stopped the repeating, took a deep breath, and smiled with relief."
        )
        world.say(
            f"Now the pair played a safer game: {defense.ending_image}"
        )
    else:
        world.para()
        world.say(
            f"{adult.id} came walking over, but the trouble was too big for {defense.label}. "
            f"{trouble.risk}"
        )
        world.say(
            f"{small.id} and {big.id} had to slow down and try a safer game instead."
        )
        world.say(
            f"Even then, {big.id} still stayed beside {small.id}, ready to defend."
        )

    world.facts.update(
        setting=setting,
        animal=animal,
        buddy=buddy,
        trouble=trouble,
        defense=defense,
        repeat_count=repeat_count,
        outcome="held" if can_hold(defense, repeat_count) else "too_big",
        defended=True,
        glee=small.memes["glee"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "soft grass", "gentle rustling",
                      "hopping paths", tags={"garden"}),
    "pond": Setting("pond", "the pond edge", "muddy shore", "small splashes",
                    "skipping stones", tags={"pond"}),
    "barnyard": Setting("barnyard", "the barnyard", "dusty boards", "happy clucks",
                        "trotting past straw", tags={"barnyard"}),
}

ANIMALS = {
    "rabbit": Animal("rabbit", "rabbit", "little rabbit", "little rabbits",
                     "hop over the stones", "hop over the stones again",
                     "The little rabbit laughed with glee.", "trickster",
                     tags={"garden", "pond"}),
    "duck": Animal("duck", "duck", "little duck", "little ducks",
                   "waddle through the puddles", "waddle through the puddles again",
                   "The little duck quacked with glee.", "trickster",
                   tags={"pond", "barnyard"}),
    "goat": Animal("goat", "goat", "little goat", "little goats",
                   "climb the low fence", "climb the low fence again",
                   "The little goat bounced with glee.", "trickster",
                   tags={"barnyard", "garden"}),
}

TROUBLES = {
    "mud": Trouble("mud", "mud", "muddy shoes", "the ground got slippery",
                   "slip in the mud", "repeated hopping on wet grass",
                   tags={"garden", "pond", "barnyard"}),
    "splash": Trouble("splash", "water splash", "a wet patch", "the path got slick",
                      "slip by the water", "repeated stomping at the edge",
                      tags={"pond"}),
    "straw": Trouble("straw", "straw pile", "scattered straw", "the floor got messy",
                     "snag in the straw", "repeated jumping near the pile",
                     tags={"barnyard"}),
}

DEFENSES = {
    "gather": Defense("gather", "a wide stick", "gather the little ones into a ring",
                      "The stick made a safe line, and the ring kept everyone calm.",
                      "a circle of pebbles around a little seedling", 2, 3),
    "block": Defense("block", "a fence board", "block the slippery spot",
                     "The board kept paws off the slick part of the ground.",
                     "a careful path around the muddy patch", 1, 2),
    "call": Defense("call", "a soft whistle", "call the animals to stop and listen",
                    "The whistle worked like a pause button for the whole yard.",
                    "a quiet game of follow-the-leader", 1, 2),
}

GREETINGS = [
    "glee", "glee", "glee",
]


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    trouble: str
    defense: str
    repeat_count: int
    smaller_name: str
    bigger_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, animal in ANIMALS.items():
            if sid not in animal.tags:
                continue
            for tid, trouble in TROUBLES.items():
                if not repeated_risk(setting, animal, trouble):
                    continue
                for did, defense in DEFENSES.items():
                    if reasonableness_gate(animal, trouble, defense):
                        combos.append((sid, aid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "glee" and the word "defend".',
        f"Tell a short story where a small {f['animal'].label} repeats a fun move again and again, and a bigger animal defends {f['animal'].id} when trouble starts.",
        f"Write a gentle repeating animal story with a clear beginning, a repeated action, a wobble, and a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    small: Entity = f["small"]
    big: Entity = f["big"]
    animal: Animal = f["animal"]
    trouble: Trouble = f["trouble"]
    defense: Defense = f["defense"]
    repeat_count = f["repeat_count"]
    return [
        ("Who is the story about?",
         f"It is about {small.id}, {big.id}, and the little {animal.label}. "
         f"They are the ones who keep the story moving from glee to trouble to help."),
        ("What did the little animal keep doing again and again?",
         f"{animal.glee_line} {small.id} kept going {animal.repeated_action} again and again. "
         f"The repeating is what built the trouble in the story."),
        ("Who defended the little animal?",
         f"{big.id} defended {small.id}. {big.id} stepped in front and spoke up so the little one would not be blamed."),
    ]
    if f["outcome"] == "held":
        return [
            *[
                ("What happened when the little animal repeated the move one more time?",
                 f"The repeating made {trouble.wobble}. That wobble showed that the game had become risky."),
                ("How did the ending change after the defense?",
                 f"{f['small'].id} used {defense.label} and stopped the repeating. "
                 f"The final picture was safer and calmer, with everyone playing a new game."),
            ],
            *story_qa(world)[0:3],
        ]
    return [
        ("What happened when the little animal repeated the move one more time?",
         f"The repeating made {trouble.wobble}, and the trouble was bigger than the first fix. "
         f"The animals had to stop and choose a safer way."),
        ("How did the story end?",
         f"They did not keep repeating the risky move. {big.id} stayed close and still defended {small.id}, and the group switched to a safer game."),
        *story_qa(world)[0:3],
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is glee?",
         "Glee is a bright, happy feeling. It can make an animal bounce, grin, or cheer."),
        ("What does it mean to defend someone?",
         "To defend someone means to protect them or speak up for them when they are in trouble."),
        ("Why can repeating something again and again matter?",
         "Repeating a move can make a story feel lively, but it can also build risk if the action gets wobblier each time."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "rabbit", "mud", "block", 2, "Mina", "Bram"),
    StoryParams("pond", "duck", "splash", "call", 3, "Pip", "Dot"),
    StoryParams("barnyard", "goat", "straw", "gather", 2, "Juno", "Rex"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not give a believable animal problem and defense.)"


def outcome_of(params: StoryParams) -> str:
    defense = DEFENSES[params.defense]
    return "held" if can_hold(defense, params.repeat_count) else "too_big"


ASP_RULES = r"""
risk(S, A, T) :- setting(S), animal(A), trouble(T), setting_tag(S, X), animal_tag(A, X), trouble_tag(T, X).
repeat_wobbles(A) :- repeating(A, N), N >= 2.
defended(A) :- defense(D), power(D, P), P >= 1.
held(D) :- power(D, P), repeat_count(R), P >= R.
valid(S, A, T) :- risk(S, A, T), defense_ok(A, T).
defense_ok(A, T) :- animal_tag(A, X), trouble_tag(T, X), trouble_tag(T, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("setting_tag", sid, tag))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact("animal_tag", aid, tag))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("trouble_tag", tid, tag))
    for did, d in DEFENSES.items():
        lines.append(asp.fact("defense", did))
        lines.append(asp.fact("power", did, d.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with glee, defend, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--defense", choices=DEFENSES)
    ap.add_argument("--repeat-count", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--small-name")
    ap.add_argument("--big-name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal is None or c[1] == args.animal)
              and (args.trouble is None or c[2] == args.trouble)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, animal, trouble = rng.choice(sorted(combos))
    defense = args.defense or rng.choice(sorted(DEFENSES))
    if defense not in DEFENSES:
        raise StoryError(explain_rejection())
    repeat_count = args.repeat_count or rng.choice([2, 3, 4])
    if args.small_name:
        small_name = args.small_name
    else:
        small_name = rng.choice(["Pip", "Mia", "Lulu", "Nori", "Tavi"])
    if args.big_name:
        big_name = args.big_name
    else:
        big_name = rng.choice([n for n in ["Bram", "Dot", "Milo", "Sage", "Roo"] if n != small_name])
    return StoryParams(setting, animal, trouble, defense, repeat_count, small_name, big_name)


def generate(params: StoryParams) -> StorySample:
    world = World()
    small = world.add(Entity(id=params.small_name, kind="character", type="animal", label=ANIMALS[params.animal].label))
    big = world.add(Entity(id=params.big_name, kind="character", type="animal", label="big friend", role="defender"))
    animal = ANIMALS[params.animal]
    trouble = TROUBLES[params.trouble]
    defense = DEFENSES[params.defense]
    setting = SETTINGS[params.setting]
    world = tell_tale(world, setting, animal, big, trouble, defense, params.repeat_count, params.small_name, params.big_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for sid, aid, tid in asp_valid_combos():
            print(f"  {sid:10} {aid:8} {tid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
