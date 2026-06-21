#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tomb_moral_value_surprise_slice_of_life.py
===========================================================================

A small standalone storyworld for a slice-of-life story about a child, a tomb,
a surprise, and a moral choice.

Premise:
- A child visits a quiet tomb with family or a caretaker.
- A small surprise is discovered near the tomb.
- The child faces a moral choice: keep the surprise or do the right thing.
- A gentle resolution follows, proving the change in the world state.

The world keeps a simple simulation:
- people and objects have meters and memes
- actions change state
- prose is rendered from that state
- Q&A is grounded in the simulated world, not by parsing prose

This script is self-contained and uses only the standard library plus the shared
storyworld result containers. ASP support is optional and imported lazily.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    quiet: bool = True
    has_tomb: bool = True
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
class Surprise:
    id: str
    label: str
    kind: str
    value: str
    hidden: bool = True
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
class MoralChoice:
    id: str
    label: str
    sense: int
    outcome_text: str
    lesson_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["distress"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life tomb storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--choice", choices=sorted(CHOICES))
    ap.add_argument("--child", choices=sorted(CHILDREN))
    ap.add_argument("--adult", choices=sorted(ADULTS))
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


@dataclass
class StoryParams:
    place: str
    surprise: str
    choice: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for surprise_id in SURPRISES:
            for choice_id in CHOICES:
                if place.has_tomb and surprise_id in {"note", "flower", "coin"}:
                    combos.append((place_id, surprise_id, choice_id))
    return combos


def reasonable_choice(choice_id: str) -> bool:
    return CHOICES[choice_id].sense >= 2


def explain_rejection() -> str:
    return "(No story: the options do not create a believable moral surprise near a tomb.)"


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.choice and not reasonable_choice(args.choice):
        raise StoryError("(No story: that choice is not sensible for this world.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.surprise is None or c[1] == args.surprise)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError(explain_rejection())
    place, surprise, choice = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    adult_gender = rng.choice(["mother", "father"])
    child = args.child or _pick_name(rng, child_gender)
    adult = args.adult or _pick_name(rng, adult_gender)
    return StoryParams(place=place, surprise=surprise, choice=choice,
                       child=child, child_gender=child_gender,
                       adult=adult, adult_gender=adult_gender)


def story_setup(world: World, child: Entity, adult: Entity, place: Place, surprise: Surprise) -> None:
    child.memes["curiosity"] += 1
    adult.memes["calm"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} walked with {adult.id} to {place.label}. "
        f"Near the tomb, the air felt still and soft."
    )
    world.say(
        f"{child.id} noticed something small tucked beside the stone: {surprise.label}."
    )


def wonder(world: World, child: Entity, surprise: Surprise) -> None:
    child.memes["want"] += 1
    world.say(
        f"{child.id} leaned closer. It was a {surprise.kind}, and it felt like a little surprise left just for {child.pronoun('object')}."
    )


def moral_warning(world: World, adult: Entity, child: Entity, choice: MoralChoice) -> None:
    child.memes["pause"] += 1
    world.say(
        f"{adult.id} put a hand on {child.pronoun('possessive')} shoulder and said, "
        f"\"Let's do the honest thing.\" {choice.lesson_text}"
    )


def choose_right(world: World, child: Entity, adult: Entity, surprise: Surprise, choice: MoralChoice) -> None:
    child.memes["honesty"] += 1
    child.meters["good_deed"] += 1
    world.say(
        f"{child.id} nodded and chose to do the right thing. {choice.outcome_text}"
    )
    world.say(
        f"Together, they left the surprise where it belonged and made the tomb look neat again."
    )


def ending(world: World, child: Entity, adult: Entity, surprise: Surprise) -> None:
    child.memes["pride"] += 1
    adult.memes["pride"] += 1
    world.say(
        f"Before they went home, {adult.id} smiled at {child.id}. "
        f"{child.id} felt warm inside, because {surprise.label} had not become something selfish."
    )
    world.say(
        f"The tomb stayed quiet, the little surprise was handled kindly, and the day ended with a small, good feeling."
    )


def tell(place: Place, surprise: Surprise, choice: MoralChoice, child_name: str, child_gender: str,
         adult_name: str, adult_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    tomb = world.add(Entity(id="tomb", kind="thing", type="tomb", label="the tomb"))
    item = world.add(Entity(id="surprise", kind="thing", type=surprise.kind, label=surprise.label))
    world.facts["place"] = place
    world.facts["surprise_cfg"] = surprise
    world.facts["choice_cfg"] = choice
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["tomb"] = tomb
    world.facts["item"] = item

    story_setup(world, child, adult, place, surprise)
    world.para()
    wonder(world, child, surprise)
    moral_warning(world, adult, child, choice)
    choose_right(world, child, adult, surprise, choice)
    world.para()
    ending(world, child, adult, surprise)
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    surprise = f["surprise_cfg"]
    choice = f["choice_cfg"]
    child = f["child"]
    return [
        f"Write a slice-of-life story about {child.id} at {place.label} where a small {surprise.kind} is found near a tomb, and the child makes a moral choice.",
        f"Tell a gentle story with the word 'tomb' in which a child notices {surprise.label} and chooses honesty over keeping it.",
        f"Write a calm, child-friendly story that ends with {child.id} doing the right thing after a surprise near a tomb."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    place = f["place"]
    surprise = f["surprise_cfg"]
    choice = f["choice_cfg"]
    qa = [
        ("Where did the story happen?",
         f"It happened at {place.label}, beside a tomb. The quiet place made the small surprise feel easy to notice."),
        ("What did the child find?",
         f"{child.id} found {surprise.label}. It was a small {surprise.kind} near the tomb, which made the moment feel a little special."),
        ("What moral choice did the child make?",
         f"{child.id} chose to do the honest thing. {choice.lesson_text}"),
        ("How did the story end?",
         f"It ended calmly, with {child.id} and {adult.id} leaving the surprise in place and going home with a good feeling."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["surprise_cfg"].tags) | set(f["choice_cfg"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge ==")
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
    return "\n".join(lines)


PLACES = {
    "old_cemetery": Place(id="old_cemetery", label="the old cemetery", tags={"quiet", "tomb"}),
    "hill_garden": Place(id="hill_garden", label="the hill garden", tags={"tomb", "flowers"}),
    "church_yard": Place(id="church_yard", label="the church yard", tags={"tomb", "quiet"}),
}

SURPRISES = {
    "note": Surprise(id="note", label="a folded note", kind="note", value="message", tags={"note"}),
    "flower": Surprise(id="flower", label="a little paper flower", kind="flower", value="gift", tags={"flower"}),
    "coin": Surprise(id="coin", label="a shiny coin", kind="coin", value="coin", tags={"coin"}),
}

CHOICES = {
    "return_note": MoralChoice(
        id="return_note",
        label="return the note",
        sense=3,
        outcome_text="They took the note to the caretaker at once.",
        lesson_text="A found note should be returned, not kept.",
        tags={"honesty", "return"},
    ),
    "leave_be": MoralChoice(
        id="leave_be",
        label="leave it there",
        sense=3,
        outcome_text="They put it back exactly where they found it.",
        lesson_text="If something belongs there, it should stay there.",
        tags={"honesty", "respect"},
    ),
    "share_with_adult": MoralChoice(
        id="share_with_adult",
        label="show the adult",
        sense=3,
        outcome_text="They showed it to the adult and asked what to do.",
        lesson_text="The safest honest choice is to ask a grown-up when you are unsure.",
        tags={"honesty", "adult_help"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Aya", "Mia"]
BOY_NAMES = ["Eli", "Noah", "Tao", "Ben", "Owen"]
ADULTS = GIRL_NAMES + BOY_NAMES

KNOWLEDGE = {
    "quiet": [("Why are cemeteries usually quiet?",
               "Cemeteries are usually quiet because people go there to remember someone and keep the place peaceful.")],
    "tomb": [("What is a tomb?",
              "A tomb is a place where someone is buried or remembered. People treat it with care and respect.")],
    "flowers": [("Why do people leave flowers near graves?",
                  "People leave flowers to show love, memory, and respect for the person who died.")],
    "note": [("What is a note?",
              "A note is a short written message. It can be used to tell someone something small and important.")],
    "coin": [("What is a coin?",
              "A coin is a small round piece of money. People use coins to pay for things or save them.")],
    "honesty": [("What does honesty mean?",
                 "Honesty means telling the truth and doing the right thing even when nobody is watching.")],
    "return": [("What should you do if you find something that belongs to someone else?",
                "You should give it to a grown-up or try to return it so the right person can get it back.")],
    "adult_help": [("When should you ask a grown-up for help?",
                    "You should ask a grown-up when something feels unsure, private, or too important to handle alone.")],
}

KNOWLEDGE_ORDER = ["quiet", "tomb", "flowers", "note", "coin", "honesty", "return", "adult_help"]


CURATED = [
    StoryParams(place="old_cemetery", surprise="note", choice="return_note",
                child="Mina", child_gender="girl", adult="Eli", adult_gender="boy"),
    StoryParams(place="hill_garden", surprise="flower", choice="leave_be",
                child="Noah", child_gender="boy", adult="Lila", adult_gender="girl"),
    StoryParams(place="church_yard", surprise="coin", choice="share_with_adult",
                child="Aya", child_gender="girl", adult="Ben", adult_gender="boy"),
]


ASP_RULES = r"""
choice_good(C) :- choice(C), sense(C, S), S >= sense_min.
tomb_place(P) :- place(P), has_tomb(P).
surprising(P, S) :- tomb_place(P), surprise(S), moral_choice(_), choice_good(_).
valid(P, S, C) :- tomb_place(P), surprise(S), choice(C), choice_good(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("has_tomb", pid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "surprise", "choice", "child", "adult"):
        if not hasattr(params, key):
            raise StoryError(f"missing param: {key}")
    if params.place not in PLACES or params.surprise not in SURPRISES or params.choice not in CHOICES:
        raise StoryError("(Invalid params: unknown place, surprise, or choice.)")
    world = tell(
        PLACES[params.place],
        SURPRISES[params.surprise],
        CHOICES[params.choice],
        params.child,
        params.child_gender,
        params.adult,
        params.adult_gender,
    )
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.surprise is None or c[1] == args.surprise)
               and (args.choice is None or c[2] == args.choice)]
    if not choices:
        raise StoryError(explain_rejection())
    place, surprise, choice = rng.choice(sorted(choices))
    child_gender = rng.choice(["girl", "boy"])
    adult_gender = rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, child_gender)
    adult = args.adult or _pick_name(rng, adult_gender)
    return StoryParams(place=place, surprise=surprise, choice=choice,
                       child=child, child_gender=child_gender,
                       adult=adult, adult_gender=adult_gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
