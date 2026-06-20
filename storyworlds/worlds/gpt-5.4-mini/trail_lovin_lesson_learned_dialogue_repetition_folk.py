#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trail_lovin_lesson_learned_dialogue_repetition_folk.py
======================================================================================

A small folk-tale storyworld about a child on a trail, a lovable companion, a
mistake made in the woods, and a lesson learned through repeated dialogue.

The seed words are "trail" and "lovin". The tale style is folk-like: concrete,
simple, repetitive, and moral at the end. The story is generated from a world
model with typed entities, physical meters, emotional memes, a reasonableness
gate, an inline ASP twin, and grounded QA.

Story shape:
- A child and a beloved helper walk a trail.
- They are tempted to ignore a warning and take a shorter path.
- A small problem grows: they get turned around or lose their way.
- A calm helper uses repeated talk and a trail token to guide them home.
- The tale ends with a lesson learned and a changed emotional state.

This script is standalone and uses only the standard library plus the shared
`storyworlds/results.py` containers.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Place:
    id: str
    label: str
    kind: str
    safe: bool = True
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
class PathChoice:
    id: str
    label: str
    short: bool
    safe: bool
    lesson: str
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
class GuideToken:
    id: str
    label: str
    phrase: str
    light: str
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
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("lost", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["worry"] += 1
        out.append("__lost__")
    return out


def _r_love_boost(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["trust"] >= THRESHOLD and child.memes["relief"] >= THRESHOLD:
        sig = ("love", child.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["love"] += 1
        out.append("__love__")
    return out


CAUSAL_RULES = [Rule("lost", "physical", _r_lost), Rule("love_boost", "social", _r_love_boost)]


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


def risk_on_trail(trail: Place, choice: PathChoice) -> bool:
    return trail.safe and not choice.safe is False


def sensible_remedy() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def choose_path(choice: PathChoice, delay: int) -> int:
    return 1 + delay + (1 if choice.short else 0)


def can_fix(remedy: Remedy, choice: PathChoice, delay: int) -> bool:
    return remedy.power >= choose_path(choice, delay)


def tell(world: World, child: Entity, companion: Entity, parent: Entity,
         place: Place, choice: PathChoice, token: GuideToken, remedy: Remedy,
         delay: int = 0) -> World:
    child.memes["trust"] = 2.0
    companion.memes["calm"] = 2.0
    world.facts["delay"] = delay

    world.say(
        f"On a bright day, {child.id} and {companion.id} went along the {place.label}. "
        f"The {place.label} was a kind trail, and the wind knew their names."
    )
    world.say(
        f'{child.id} said, "{companion.label}, {companion.label}, I am lovin this trail." '
        f'{companion.id} said, "{child.id}, the trail is long, but the trail is kind."'
    )
    world.say(
        f'They walked and talked and walked some more. "{choice.label}," said '
        f"{child.id}. \"Short way! Short way!\""
    )
    world.para()
    child.memes["desire"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'{companion.id} shook {companion.pronoun("possessive")} head. '
        f'"No, no," {companion.id} said. "Stay on the trail."'
    )
    world.say(
        f'"Stay on the trail," {companion.id} said again. "The trail is safe. '
        f"The trail is sure. The trail is kind."
    )
    if choice.short:
        world.say(
            f'But {child.id} rushed ahead anyway, because the short way looked faster '
            f"than the right way."
        )
        child.meters["lost"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"At once the trees looked the same, and the little path curled away. "
            f"{child.id} could not tell which turn was home."
        )
        world.say(
            f'{child.id} called, "{companion.id}! {companion.id}!" and then again, '
            f'"Where is the trail? Where is the trail?"'
        )
        world.say(
            f'{companion.id} answered, "{token.label}! {token.label}! Follow the light, '
            f'follow the light."'
        )
        if can_fix(remedy, choice, delay):
            world.para()
            child.meters["lost"] = 0
            child.memes["worry"] += 1
            child.memes["relief"] += 2
            world.say(
                f"{parent.label_word.capitalize()} came walking down the path with a "
                f"{token.phrase}. In a flash, {parent.pronoun()} {remedy.text}."
            )
            world.say(
                f'{parent.id} said, "{choice.lesson}" and then said it again, '
                f'"{choice.lesson}"'
            )
            world.say(
                f'{child.id} listened. {companion.id} listened. They all listened. '
                f"Then the trail opened wide, and the way home was found."
            )
            world.para()
            world.say(
                f"After that, {child.id} stayed on the trail, and {child.id} stayed on the trail, "
                f"and {child.id} stayed on the trail. That made the whole walk safe."
            )
            child.memes["lesson"] += 1
            child.memes["love"] += 1
        else:
            world.para()
            child.meters["lost"] = 1.0
            world.say(
                f"{parent.label_word.capitalize()} came, but {parent.pronoun()} {remedy.fail}."
            )
            world.say(
                f"The day grew long, the trail grew dim, and the little walkers had to keep "
                f"to the main road to get home."
            )
            world.say(
                f"They were safe, but the lesson was heavy: the short way is not always the kind way."
            )
            child.memes["lesson"] += 1
    else:
        world.say(
            f'{child.id} looked at {companion.id}, then looked at the trail, and said, '
            f'"No short way. Trail way."'
        )
        world.say(
            f'{companion.id} smiled. "{choice.lesson}"'
        )
        world.para()
        world.say(
            f"They stayed where the moss was soft and the birds could see them. "
            f"The trail led them home before the sun touched the hill."
        )
        child.memes["lesson"] += 1
        child.memes["relief"] += 1

    world.facts.update(
        child=child, companion=companion, parent=parent, place=place,
        choice=choice, token=token, remedy=remedy, outcome=("lost" if choice.short else "safe")
    )
    return world


PLACES = {
    "woods": Place("woods", "forest trail", "outdoor", True, {"trail"}),
    "hill": Place("hill", "hill trail", "outdoor", True, {"trail"}),
    "brook": Place("brook", "brook trail", "outdoor", True, {"trail"}),
}

CHOICES = {
    "shortcut": PathChoice("shortcut", "short path", True, True, "A short path is not always the safe path.", {"trail"}),
    "sidepath": PathChoice("sidepath", "side path", True, True, "A side path can wander away from the way home.", {"trail"}),
    "maintrail": PathChoice("maintrail", "main trail", False, True, "The main trail may be longer, but it is kinder and safer.", {"trail"}),
}

TOKENS = {
    "lantern": GuideToken("lantern", "lantern", "a little lantern", "glowed like a warm star", {"lantern"}),
    "bell": GuideToken("bell", "bell", "a small bell", "rang clear and bright", {"bell"}),
}

REMEDIES = {
    "lamp": Remedy("lamp", 3, 3, "held up the lantern and lit the whole path", "could not light the way in time", "held up the lantern and lit the whole path", {"lantern"}),
    "call": Remedy("call", 3, 2, "called again and again until the sound brought help", "called, but the answer never came close enough", "called again and again until the sound brought help", {"call"}),
    "song": Remedy("song", 2, 2, "sang the trail song three times and kept everyone calm", "sang, but the tune was too small for the dark", "sang the trail song three times and kept everyone calm", {"song"}),
}

CHILD_NAMES = ["Mina", "Toby", "June", "Eli", "Nell", "Pip", "Rose", "Marl"]
COMPANION_NAMES = ["Fox", "Moss", "Wren", "Hare", "Bee", "Robin"]
PARENT_NAMES = ["Mother", "Father", "Aunt", "Uncle"]


@dataclass
@dataclass
class StoryParams:
    place: str
    choice: str
    token: str
    remedy: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    parent: str
    delay: int = 0
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
    for pid in PLACES:
        for cid in CHOICES:
            for tid in TOKENS:
                if risk_on_trail(PLACES[pid], CHOICES[cid]):
                    combos.append((pid, cid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale trail storyworld with lesson learned and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    if args.choice and args.choice not in CHOICES:
        raise StoryError("(No story: unknown path choice.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.choice is None or c[1] == args.choice)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid trail story matches the given options.)")
    place, choice, token = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedy()))
    child_gender = rng.choice(["girl", "boy"])
    companion_gender = rng.choice(["girl", "boy"])
    child = rng.choice(CHILD_NAMES)
    companion = rng.choice([n for n in COMPANION_NAMES if n != child])
    parent = args.parent or rng.choice(PARENT_NAMES)
    delay = rng.randint(0, 1)
    return StoryParams(place, choice, token, remedy, child, child_gender, companion, companion_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        World(),
        world_add_entity(params.child, "character", params.child_gender, "child"),
        world_add_entity(params.companion, "character", params.companion_gender, "companion"),
        world_add_entity(params.parent, "character", "mother" if params.parent == "Mother" else "father", "parent"),
        PLACES[params.place], CHOICES[params.choice], TOKENS[params.token], REMEDIES[params.remedy], params.delay
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def world_add_entity(name: str, kind: str, gender: str, role: str) -> Entity:
    return Entity(id=name, kind=kind, type=gender, role=role)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, companion, place, choice = f["child"], f["companion"], f["place"], f["choice"]
    return [
        f'Write a folk tale for a small child where {child.id} walks the {place.label} and says "{choice.label}".',
        f'Write a story with repetition in which {child.id} and {companion.id} stay on a trail and learn a lesson about shortcuts.',
        f'Write a gentle story that includes the words "trail" and "lovin" and ends with a moral about the right path.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, companion, parent, place, choice, token = f["child"], f["companion"], f["parent"], f["place"], f["choice"], f["token"]
    qa = [
        ("Who is in the story?", f"The story is about {child.id}, {companion.id}, and {parent.label_word.lower()}, all walking the {place.label}."),
        ("What did they keep saying?", f"They kept saying to stay on the trail, and they repeated the warning so the lesson would stick. The repeated words helped turn the story into a folk tale lesson."),
        ("What did {0} call the trail?".format(child.id), f"{child.id} called it lovin, meaning the trail felt dear and good to follow."),
    ]
    if f["outcome"] == "lost":
        qa.append(("What happened when they chose the short path?", f"They got turned around and had to follow the {token.label} back. The short way made them lose the safe way for a while."))
        qa.append(("What lesson did they learn?", f"They learned that the short way is not always the kind way, and that the trail is safer when you stay with it."))
    else:
        qa.append(("How did the story end?", f"They stayed on the trail and made it home safely. The trail, the trail, the trail was the right way after all."))
        qa.append(("What lesson did they learn?", f"They learned to keep to the trail and trust the slower path when it is the safer one."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a trail?", "A trail is a path people walk in the woods, hills, or fields. Trails help travelers keep their way."),
        ("What does lovin mean in this story?", "It means something dear, fond, or loved. In the tale, it shows the child feels warmly about the trail."),
        ("Why do people repeat a lesson in a folk tale?", "Folk tales repeat words so the message sticks in the listener's mind. The repetition makes the lesson easy to remember."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(choice: PathChoice) -> str:
    return f"(No story: {choice.label} is not a story-changing turn for this trail tale.)"


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    return f"(Refusing remedy '{rid}': it is too weak for the trail problem (sense={r.sense}).)"


ASP_RULES = r"""
safe_combo(P, C, T) :- place(P), choice(C), token(T), trail_risk(P, C).
outcome(lost) :- chosen_choice(C), short(C), chosen_delay(D), D >= 0.
outcome(safe) :- chosen_choice(C), not short(C).
fixed(R) :- remedy(R), power(R, P), needed(N), P >= N.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if c.short:
            lines.append(asp.fact("short", cid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_combo/3."))
    return sorted(set(asp.atoms(model, "safe_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in trail gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, choice=None, token=None, remedy=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


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
        print(asp_program("", "#show safe_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("woods", "shortcut", "lantern", "lamp", "Mina", "girl", "Fox", "boy", "Mother", 0),
            StoryParams("hill", "sidepath", "bell", "song", "Toby", "boy", "Wren", "girl", "Father", 1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.choice and args.choice not in CHOICES:
        raise StoryError("(No story: unknown choice.)")
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError(explain_remedy(args.remedy))
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.choice is None or c[1] == args.choice)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, choice, token = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedy()))
    child = rng.choice(CHILD_NAMES)
    companion = rng.choice([n for n in COMPANION_NAMES if n != child])
    parent = args.parent or rng.choice(PARENT_NAMES)
    child_gender = rng.choice(["girl", "boy"])
    companion_gender = rng.choice(["girl", "boy"])
    return StoryParams(place, choice, token, remedy, child, child_gender, companion, companion_gender, parent, rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion"))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother" if params.parent == "Mother" else "father", role="parent"))
    world.facts["child"] = child
    world.facts["companion"] = companion
    world.facts["parent"] = parent
    world.facts["place"] = PLACES[params.place]
    world.facts["choice"] = CHOICES[params.choice]
    world.facts["token"] = TOKENS[params.token]
    world.facts["remedy"] = REMEDIES[params.remedy]
    world.facts["outcome"] = "lost" if CHOICES[params.choice].short else "safe"
    world = tell(world, child, companion, parent, PLACES[params.place], CHOICES[params.choice], TOKENS[params.token], REMEDIES[params.remedy], params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


if __name__ == "__main__":
    main()
