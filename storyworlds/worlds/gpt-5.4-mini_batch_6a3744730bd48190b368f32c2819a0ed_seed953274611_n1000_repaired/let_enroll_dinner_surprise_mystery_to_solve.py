#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/let_enroll_dinner_surprise_mystery_to_solve.py
================================================================================

A small nursery-rhyme-flavored storyworld about a child, a dinner-time surprise,
and a mystery to solve. The world stays tiny and concrete: one child wants to
let someone join a dinner plan, a small misunderstanding grows into a mystery,
and a gentle surprise resolves it.

Seed words: let, enroll, dinner
Features: Surprise, Mystery to Solve
Style: Nursery Rhyme
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
    detail: str
    sound: str
    dinner_ready: bool = True
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
    reveal: str
    gift: str
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
class Mystery:
    id: str
    label: str
    clue: str
    answer: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_hunger(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.kind == "character" and e.meters["hungry"] >= THRESHOLD:
            sig = ("hungry", e.id)
            if sig not in world.fired:
                world.fired.add(sig)
                e.memes["wish"] += 1
                out.append("")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    if world.facts.get("surprise_seen") and not world.facts.get("surprise_narrated"):
        world.facts["surprise_narrated"] = True
        out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("surprise", _r_surprise)]


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


def inspect_place(place: Place) -> bool:
    return place.dinner_ready


def mystery_active(world: World) -> bool:
    return world.facts.get("mystery_unsolved", False)


def solve_mystery(world: World, child: Entity, helper: Entity, mystery: Mystery, surprise: Surprise) -> None:
    world.facts["mystery_unsolved"] = False
    world.facts["surprise_seen"] = True
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.id} looked low and high, and found the clue: {mystery.clue}."
    )
    world.say(
        f"It was no scary riddle at all; it was {surprise.reveal}, "
        f"and that was the sweet surprise."
    )
    world.say(
        f"{child.id} laughed, and the dinner got bright with {surprise.gift}."
    )


def set_up(world: World, child: Entity, helper: Entity, place: Place, mystery: Mystery) -> None:
    child.memes["curious"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Under the moon by {place.label}, {child.id} came to dinner with {helper.id}."
    )
    world.say(
        f"The table was set, the bowls were round, and the room went hush-hush, soft as sound."
    )
    world.say(
        f"But one small thing was missing there, and that made a mystery in the air."
    )
    world.say(
        f"{child.id} frowned and said, \"Let's let the little plan enroll, but first we must solve {mystery.label}.\""
    )


def hint(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{helper.id} saw a clue upon the chair: {mystery.clue} lay waiting there."
    )
    world.say(
        f"\"If we can find it,\" said {helper.id}, \"our dinner tale will turn to bread.\""
    )
    world.facts["mystery_unsolved"] = True


def no_mystery(world: World) -> None:
    world.facts["mystery_unsolved"] = False
    world.say("If all the clues were plain and true, the story would have nothing new.")


def ending(world: World, child: Entity, helper: Entity, place: Place, surprise: Surprise) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"So {child.id} and {helper.id} sat down near the glow, and dinner felt warm from high to low."
    )
    world.say(
        f"{place.label} was calm, the night was mild, and {surprise.gift} shone like a nursery child."
    )


def tell(place: Place, child_name: str, child_type: str, helper_name: str, helper_type: str,
         surprise: Surprise, mystery: Mystery) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    child.meters["hungry"] = 1
    helper.meters["hungry"] = 1

    set_up(world, child, helper, place, mystery)
    world.para()
    hint(world, child, helper, mystery)

    if mystery_active(world):
        solve_mystery(world, child, helper, mystery, surprise)
    else:
        no_mystery(world)

    world.para()
    ending(world, child, helper, place, surprise)
    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        surprise=surprise,
        mystery=mystery,
    )
    return world


PLACES = {
    "cottage": Place(
        id="cottage",
        label="the cozy cottage",
        detail="a tiny cottage with a glowing window",
        sound="a dinner song",
        dinner_ready=True,
        tags={"dinner", "cozy"},
    ),
    "garden": Place(
        id="garden",
        label="the little garden",
        detail="a little garden with a round stone table",
        sound="the crickets singing",
        dinner_ready=True,
        tags={"dinner", "garden"},
    ),
    "hall": Place(
        id="hall",
        label="the bright hall",
        detail="a bright hall with benches and a big blue cloth",
        sound="a little tune",
        dinner_ready=True,
        tags={"dinner", "hall"},
    ),
}

SURPRISES = {
    "pie": Surprise(
        id="pie",
        label="pie",
        reveal="a pie was hiding under the cloth",
        gift="a plum pie",
        tags={"surprise", "dinner"},
    ),
    "song": Surprise(
        id="song",
        label="song",
        reveal="a song was waiting in a basket",
        gift="a honey songbook",
        tags={"surprise", "music"},
    ),
    "candle": Surprise(
        id="candle",
        label="candle",
        reveal="a candle had been kept for the feast",
        gift="a golden candle",
        tags={"surprise", "light"},
    ),
}

MYSTERIES = {
    "missing_spoon": Mystery(
        id="missing_spoon",
        label="the missing spoon",
        clue="a silver spoon was hiding behind the bread",
        answer="the spoon was behind the bread",
        tags={"mystery", "spoon"},
    ),
    "small_noise": Mystery(
        id="small_noise",
        label="the small noise",
        clue="a soft bump came from the cupboard",
        answer="a small kitten was in the cupboard",
        tags={"mystery", "sound"},
    ),
    "blue_cloth": Mystery(
        id="blue_cloth",
        label="the blue cloth",
        clue="the blue cloth hid a round shape",
        answer="the surprise was under the blue cloth",
        tags={"mystery", "cloth"},
    ),
}

CHILD_NAMES = ["Mia", "Nell", "Pip", "Toby", "Ruby", "Finn", "Lily", "Sam"]
HELPER_NAMES = ["Mum", "Nan", "Dad", "Aunt May", "Uncle Ben"]


@dataclass
class StoryParams:
    place: str
    surprise: str
    mystery: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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
    for p in PLACES:
        for s in SURPRISES:
            for m in MYSTERIES:
                combos.append((p, s, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld with dinner, surprise, and a mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
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
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.surprise and args.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.surprise is None or c[1] == args.surprise)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, surprise, mystery = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman", "man"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        surprise=surprise,
        mystery=mystery,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story that includes the words "let", "enroll", and "dinner" in a gentle scene at {f["place"].label}.',
        f"Tell a small story where {f['child'].id} and {f['helper'].id} solve {f['mystery'].label} at dinner, with a surprise at the end.",
        f'Write a rhyme-like bedtime story with a mystery to solve, a dinner table, and a sweet surprise hidden in plain sight.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    surprise = f["surprise"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id} and {helper.id}, who sat down for dinner and looked for a clue together. The little mystery gave the story its soft middle turn.",
        ),
        QAItem(
            question=f"What mystery did they solve?",
            answer=f"They solved {mystery.label}. They found {mystery.clue}, and that clue led them to the answer in a very gentle way.",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {surprise.reveal}. It changed the dinner from puzzling to merry, because the hiding place turned out to hold a happy gift.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dinner?",
            answer="Dinner is the evening meal people eat when the day is getting dark. Families often sit together for it and talk about their day.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not explained yet. People solve it by looking for clues and thinking carefully.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something hidden or unexpected. It often makes people smile when it is finally found.",
        ),
    ]


ASP_RULES = r"""
valid(P,S,M) :- place(P), surprise(S), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
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

    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH between clingo and valid_combos().")
            return 1
        sample = generate(
            StoryParams(
                place="cottage",
                surprise="pie",
                mystery="missing_spoon",
                child_name="Mia",
                child_type="girl",
                helper_name="Mum",
                helper_type="mother",
            )
        )
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: ASP parity and generate/emit smoke test passed.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"VERIFY FAILED: {exc}")
        return 1


CURATED = [
    StoryParams(
        place="cottage",
        surprise="pie",
        mystery="missing_spoon",
        child_name="Mia",
        child_type="girl",
        helper_name="Mum",
        helper_type="mother",
    ),
    StoryParams(
        place="garden",
        surprise="song",
        mystery="small_noise",
        child_name="Pip",
        child_type="boy",
        helper_name="Nan",
        helper_type="woman",
    ),
    StoryParams(
        place="hall",
        surprise="candle",
        mystery="blue_cloth",
        child_name="Ruby",
        child_type="girl",
        helper_name="Dad",
        helper_type="father",
    ),
]


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("surprise", SURPRISES), ("mystery", MYSTERIES)):
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)!r}")
    place = PLACES[params.place]
    surprise = SURPRISES[params.surprise]
    mystery = MYSTERIES[params.mystery]
    world = World(place=place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    world.facts["place"] = place
    world.facts["surprise"] = surprise
    world.facts["mystery"] = mystery
    world.facts["child"] = child
    world.facts["helper"] = helper

    set_up(world, child, helper, place, mystery)
    world.para()
    hint(world, child, helper, mystery)
    solve_mystery(world, child, helper, mystery, surprise)
    world.para()
    ending(world, child, helper, place, surprise)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def set_up(world: World, child: Entity, helper: Entity, place: Place, mystery: Mystery) -> None:
    world.say(
        f"At {place.label}, by the soft dinner light, {child.id} and {helper.id} were merry that night."
    )
    world.say(
        f"The spoons were bright, the napkins neat, and the room went hum with a tiny beat."
    )
    world.say(
        f"But one thing was missing, as clues can show, and that was {mystery.label} in a row."
    )
    world.say(
        f"{child.id} said, \"Let's let the plan enroll for dinner, but first we must solve the little puzzle below.\""
    )


def hint(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["curious"] += 1
    helper.memes["curious"] += 1
    world.say(
        f"{helper.id} bent down low and found a sign: {mystery.clue} was the next line."
    )
    world.say(
        f"So the mystery was not a fright, just a hidden thing to bring to light."
    )
    world.facts["mystery_unsolved"] = True


def solve_mystery(world: World, child: Entity, helper: Entity, mystery: Mystery, surprise: Surprise) -> None:
    world.facts["surprise_seen"] = True
    world.facts["mystery_unsolved"] = False
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.id} lifted the cloth and, lo and behold, there was the answer tucked in the fold."
    )
    world.say(
        f"It matched {mystery.answer}, and there beside it was {surprise.reveal}."
    )
    world.say(
        f"That made a sweet surprise, with a little hooray, and dinner turned bright in a nursery way."
    )


def ending(world: World, child: Entity, helper: Entity, place: Place, surprise: Surprise) -> None:
    child.memes["joy"] += 1
    world.say(
        f"So {child.id} sat happy, with cheeks all warm, while {place.label} stayed safe from storm."
    )
    world.say(
        f"The surprise gift shone, the mystery slept, and everyone smiled as the evening crept."
    )
    world.say(
        f"With dinner done, {child.id} laughed and said, \"We let the moon keep watch over our bed!\""
    )


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, s, m in combos:
            print(f"  {p:8} {s:10} {m}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
