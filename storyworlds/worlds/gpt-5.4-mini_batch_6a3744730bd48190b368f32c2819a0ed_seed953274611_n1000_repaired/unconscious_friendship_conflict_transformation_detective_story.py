#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/unconscious_friendship_conflict_transformation_detective_story.py
==================================================================================================

A standalone storyworld for a TinyStories-style detective mystery about friendship,
conflict, and transformation.

Premise:
- Two young detectives work a small case in a library-adjacent neighborhood.
- They find a friend unconscious after a harmless-but-scary fainting spell.
- A friendship conflict starts when one detective suspects the other.
- The investigation reveals a simple cause, the friend wakes up, and the group
  transforms from worried and suspicious into careful and trusting.

The world is intentionally compact:
- typed entities with meters and memes
- state-driven narration
- a Python reasonableness gate
- an inline ASP twin for parity checks
- three Q&A sets grounded in the generated world state

The word "unconscious" is included in the story text and world facts.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    mood: str
    dark_spot: str
    afford_clue: str
    heat: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    found_where: str
    points_to: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Cause:
    id: str
    label: str
    symptom: str
    fix: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    place: str
    clue: str
    cause: str
    detective_a: str
    detective_a_gender: str
    detective_b: str
    detective_b_gender: str
    friend: str
    friend_gender: str
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
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_unconscious(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    if friend.meters["heat"] >= 1 and friend.meters["tired"] >= 1 and friend.meters["collapse"] < 1:
        world.fired.add(("collapse",))
        friend.meters["collapse"] += 1
        friend.meters["unconscious"] += 1
        out.append("__collapse__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("friend").meters["unconscious"] >= THRESHOLD:
        for eid in ("a", "b"):
            world.get(eid).memes["worry"] += 1
        if ("worry",) not in world.fired:
            world.fired.add(("worry",))
            out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("unconscious", _r_unconscious), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def hazard_reasonable(place: Place, clue: Clue, cause: Cause) -> bool:
    return place.id in {"library", "museum", "attic"} and clue.points_to == cause.id and cause.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for cause in CAUSES:
                if hazard_reasonable(p, c, cause):
                    combos.append((p.id, c.id, cause.id))
    return combos


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.cause not in CAUSES:
        raise StoryError("Unknown cause.")
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    if not hazard_reasonable(place, clue, cause):
        raise StoryError("That clue and cause do not fit a believable detective mystery.")

    world = World()
    a = world.add(Entity(id="a", kind="character", type=params.detective_a_gender, role="detective", label=params.detective_a, traits=["curious"]))
    b = world.add(Entity(id="b", kind="character", type=params.detective_b_gender, role="detective", label=params.detective_b, traits=["careful"]))
    f = world.add(Entity(id="friend", kind="character", type=params.friend_gender, role="friend", label=params.friend))
    room = world.add(Entity(id="room", type="place", label=place.label))
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["cause"] = cause

    a.memes["trust"] = 3
    b.memes["trust"] = 6
    a.memes["suspicion"] = 0
    b.memes["suspicion"] = 0

    world.say(
        f"On a quiet afternoon, {a.label} and {b.label} opened their little detective notebook in {place.label}. "
        f"{place.mood.capitalize()} air drifted through the room, and {place.afford_clue} made the place feel full of secrets."
    )
    world.say(
        f'"If we follow the clue, we can solve the mystery," {a.label} said. '
        f'"And if we are careful, we can help our friend too," {b.label} answered.'
    )

    world.para()
    world.say(
        f"They found {f.label} lying by {clue.found_where}, looking {cause.symptom}. "
        f'For a moment, the word "unconscious" felt huge and scary.'
    )
    f.meters["heat"] += float(place.heat)
    f.meters["tired"] += 1
    propagate(world, narrate=False)

    world.say(
        f"{a.label} spotted {clue.phrase} and frowned. "
        f'"That looks strange," {a.label} whispered. "Maybe {b.label} hid it."'
    )
    a.memes["suspicion"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"{b.label}'s face went tight. " f'"I did not," {b.pronoun()} said, and the two friends stopped feeling like a team.'
    )

    world.para()
    world.say(
        f"Then {b.label} noticed the real pattern: {clue.phrase} matched {cause.label}, and {cause.fix} was the sensible answer."
    )
    world.say(
        f"{b.label} ran for water and a cool cloth, while {a.label} opened the window and called for a grown-up."
    )
    f.meters["cool"] += 1
    f.meters["help"] += 1
    if f.meters["unconscious"] >= THRESHOLD:
        f.meters["unconscious"] = 0
        f.memes["relief"] += 1
        f.memes["comfort"] += 1
        world.say(
            f"Soon {f.label} stirred, blinked, and sat up. {f.label} was no longer unconscious."
        )

    world.para()
    a.memes["suspicion"] = 0
    a.memes["trust"] += 2
    b.memes["hurt"] = 0
    b.memes["trust"] += 2
    f.memes["relief"] += 1
    world.say(
        f"{a.label} looked at {b.label} and lowered {a.pronoun('possessive')} voice. "
        f'"I was wrong," {a.label} said. "You helped solve it."'
    )
    world.say(
        f"{b.label} smiled back, and the three of them transformed from worried strangers into careful friends again."
    )
    world.say(
        f"By the end, {room.label_word if hasattr(room, 'label_word') else 'the room'} felt ordinary again, but the notebook held a new lesson: stay calm, look closely, and trust a friend who helps."
    )

    world.facts.update(
        a=a, b=b, friend=f, room=room, outcome="recovered", transformed=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    clue: Clue = f["clue"]
    cause: Cause = f["cause"]
    return [
        f'Write a child-friendly detective story set in {place.label} that includes the word "unconscious".',
        f"Tell a mystery where two friends find a third friend unconscious, argue for a moment, and then solve the case with a clue about {clue.label}.",
        f"Write a story about friendship, conflict, and transformation where careful noticing reveals that {cause.label} explains the mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a: Entity = f["a"]
    b: Entity = f["b"]
    friend: Entity = f["friend"]
    place: Place = f["place"]
    clue: Clue = f["clue"]
    cause: Cause = f["cause"]
    qa = [
        ("Who are the main characters?",
         f"The main characters are {a.label} and {b.label}, two young detectives who work together in {place.label}."),
        ("What happened to their friend?",
         f"Their friend {friend.label} became unconscious, which made the mystery feel urgent and scary."),
        ("Why did {a} suspect {b}?".format(a=a.label, b=b.label),
         f"{a.label} saw {clue.phrase} and guessed too quickly. {a.label} thought the clue meant {b.label} had done something wrong, but that guess was not true."),
        ("How was the mystery solved?",
         f"{b.label} matched the clue to {cause.label} and found the real reason. Then {b.label} used {cause.fix} and the two friends called for help."),
        ("How did the friendship change?",
         f"At first, the friends were tense and suspicious. By the end, they were honest, calm, and more trusting than before."),
    ]
    if friend.meters.get("unconscious", 0) < THRESHOLD:
        qa.append(
            ("Was the friend still unconscious at the end?",
             f"No. {friend.label} woke up, blinked, and sat up after the grown-up help and the cool cloth.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cause: Cause = f["cause"]
    clue: Clue = f["clue"]
    tags = set(cause.tags) | set(clue.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {e.label} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "library": Place(id="library", label="the little library", mood="quiet shelves waited nearby", dark_spot="the back reading corner", afford_clue="a sliver of torn paper under the table", heat=1, tags={"library"}),
    "museum": Place(id="museum", label="the tiny museum room", mood="dusty light hung over the cases", dark_spot="the storage alcove", afford_clue="a shiny button on the floor", heat=1, tags={"museum"}),
    "attic": Place(id="attic", label="the old attic", mood="wooden beams creaked overhead", dark_spot="the box corner by the window", afford_clue="a dusty ribbon under the lamp", heat=2, tags={"attic"}),
}

CLUES = {
    "paper": Clue(id="paper", label="torn paper", phrase="a torn paper scrap", found_where="the floor", points_to="paper", tags={"paper"}),
    "button": Clue(id="button", label="button", phrase="a shiny button", found_where="the rug", points_to="button", tags={"button"}),
    "ribbon": Clue(id="ribbon", label="ribbon", phrase="a dusty ribbon", found_where="the lamp base", points_to="ribbon", tags={"ribbon"}),
}

CAUSES = {
    "paper": Cause(id="paper", label="a loose paper fan", symptom="pale and shaky", fix="a cool drink and rest", safe=True, tags={"paper"}),
    "button": Cause(id="button", label="a too-tight costume button", symptom="hot and dizzy", fix="cool air and water", safe=True, tags={"button"}),
    "ribbon": Cause(id="ribbon", label="a dusty ribbon near the heater", symptom="hot and sleepy", fix="fresh air and a chair", safe=True, tags={"ribbon"}),
}

GIRL_NAMES = ["Mina", "Tessa", "Lila", "Nina", "Iris"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Milo", "Theo"]
FRIENDS = ["Pip", "Sam", "Rowan", "Alex", "Cleo"]


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(place="library", clue="paper", cause="paper", detective_a="Mina", detective_a_gender="girl", detective_b="Owen", detective_b_gender="boy", friend="Pip", friend_gender="boy"),
    StoryParams(place="museum", clue="button", cause="button", detective_a="Tessa", detective_a_gender="girl", detective_b="Theo", detective_b_gender="boy", friend="Sam", friend_gender="boy"),
    StoryParams(place="attic", clue="ribbon", cause="ribbon", detective_a="Lila", detective_a_gender="girl", detective_b="Nina", detective_b_gender="girl", friend="Alex", friend_gender="boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("points_to", c.id, c.points_to))
    for c in CAUSES.values():
        lines.append(asp.fact("cause", c.id))
        if c.safe:
            lines.append(asp.fact("safe", c.id))
        lines.append(asp.fact("fix", c.id, c.fix))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,Ca) :- place(P), clue(C), cause(Ca), points_to(C, Ca), safe(Ca).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo parity.")
        print(" only in python:", sorted(py - cl))
        print(" only in asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld about friendship, conflict, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.cause is None or c[2] == args.cause)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, cause = rng.choice(sorted(combos))
    a_name = args.__dict__.get("detective_a") or rng.choice(GIRL_NAMES)
    b_name = args.__dict__.get("detective_b") or rng.choice(BOY_NAMES)
    friend = rng.choice(FRIENDS)
    genders = ["girl", "boy"]
    return StoryParams(
        place=place,
        clue=clue,
        cause=cause,
        detective_a=a_name,
        detective_a_gender=rng.choice(genders),
        detective_b=b_name,
        detective_b_gender=rng.choice(genders),
        friend=friend,
        friend_gender=rng.choice(genders),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        for p, c, ca in asp_valid_combos():
            print(p, c, ca)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
