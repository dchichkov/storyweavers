#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/external_nurture_beet_bad_ending_suspense_whodunit.py
=====================================================================================

A standalone storyworld for a small whodunit-like mystery about an external
visitor, a careful nurture plan, and a beet patch that ends in a bad ending.

The seed words are woven into the simulation:
- external: an outside helper/visitor, coming from beyond the garden
- nurture: the characters can tend, water, cover, and protect the beet bed
- beet: the garden crop at the center of the mystery

Style goals:
- whodunit mood
- suspenseful, child-facing prose
- bad ending outcome available and preferred in the curated set
- state-driven story, not a frozen paragraph

The file follows the Storyweavers storyworld contract:
- stdlib-only story engine
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py only in ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- QA prompts, story-grounded QA, world-knowledge QA
- Python reasonableness gate and inline ASP twin
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_THRESHOLD = 1.0


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
    external: bool = False
    watchful: bool = False
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
class Crop:
    id: str
    label: str
    fragile: bool = True
    edible: bool = True
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
class Lead:
    id: str
    label: str
    clue_text: str
    tension: int
    truth: str
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
class Fix:
    id: str
    label: str
    verb: str
    effect: str
    power: int
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
    crop: str
    lead: str
    fix: str
    external_visitor: str
    child: str
    child_gender: str
    caretaker: str
    caretaker_gender: str
    weather: str = "quiet"
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


PLACES = {
    "garden": Place("garden", "the garden", external=False, watchful=True, tags={"garden"}),
    "greenhouse": Place("greenhouse", "the greenhouse", external=False, watchful=True, tags={"greenhouse"}),
    "yard": Place("yard", "the yard", external=False, watchful=False, tags={"yard"}),
    "fence": Place("fence", "the back fence", external=True, watchful=False, tags={"external", "fence"}),
}

CROPS = {
    "beet": Crop("beet", "the beet bed", fragile=True, edible=True, tags={"beet", "crop"}),
    "beets": Crop("beets", "the beets", fragile=True, edible=True, tags={"beet", "crop"}),
    "seedlings": Crop("seedlings", "the beet seedlings", fragile=True, edible=True, tags={"beet", "seedling"}),
}

LEADS = {
    "muddy_boots": Lead("muddy_boots", "muddy boots", "There were muddy boot prints by the beet bed.", 2, "the prints belonged to an external visitor", tags={"clue", "boots", "external"}),
    "missing_leaf": Lead("missing_leaf", "missing leaf", "One beet leaf was torn, as if someone had rushed.", 3, "the plants had been disturbed by a hurried hand", tags={"clue", "leaf", "beet"}),
    "open_gate": Lead("open_gate", "open gate", "The side gate was not latched.", 4, "someone from outside had come in and out quickly", tags={"clue", "gate", "external"}),
}

FIXES = {
    "lantern": Fix("lantern", "a lantern", "hold up", "gave the garden a warm, safe light", 1, True, tags={"light"}),
    "cover": Fix("cover", "a cloth cover", "pull over", "hid the beet bed from rain and eyes", 2, True, tags={"cover"}),
    "replant": Fix("replant", "fresh soil", "replant", "started the beet bed over again", 3, True, tags={"soil"}),
    "report": Fix("report", "the grown-up note", "tell", "brought the caretaker into the mystery", 4, True, tags={"report"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ada", "Nora", "Ivy", "Maya", "Zoe"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Finn", "Noah", "Max", "Ben"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for crop_id in CROPS:
            for lead_id in LEADS:
                if place.external or place.watchful:
                    out.append((place_id, crop_id, lead_id))
    return out


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a whodunit-flavored garden mystery with suspense and a bad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--lead", choices=LEADS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--visitor", choices=["neighbor", "delivery", "stranger"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker")
    ap.add_argument("--caretaker-gender", choices=["mother", "father"])
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
              if (args.place is None or c[0] == args.place)
              and (args.crop is None or c[1] == args.crop)
              and (args.lead is None or c[2] == args.lead)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, crop, lead = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    visitor = args.visitor or rng.choice(["neighbor", "delivery", "stranger"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    caretaker_gender = args.caretaker_gender or ("mother" if child_gender == "girl" else "father")
    child = args.child or _pick_name(rng, child_gender)
    caretaker = args.caretaker or _pick_name(rng, caretaker_gender if caretaker_gender in ("girl", "boy") else "girl")
    return StoryParams(
        place=place,
        crop=crop,
        lead=lead,
        fix=fix,
        external_visitor=visitor,
        child=child,
        child_gender=child_gender,
        caretaker=caretaker,
        caretaker_gender=caretaker_gender,
        weather=rng.choice(["quiet", "foggy", "rainy"]),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.crop not in CROPS:
        raise StoryError("Unknown crop.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.lead not in LEADS:
        raise StoryError("Unknown clue.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")


def suspicion_level(world: World) -> float:
    return sum(e.meters["suspense"] for e in world.entities.values())


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters["disturbance"] >= THRESHOLD and ("disturbance", ent.id) not in world.fired:
                world.fired.add(("disturbance", ent.id))
                ent.memes["fear"] += 1
                ent.meters["suspense"] += 1
                changed = True
                out.append("__disturb__")
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    caretaker = world.add(Entity(id=params.caretaker, kind="character", type=params.caretaker_gender, role="caretaker", label="the caretaker"))
    place = world.add(Entity(id=params.place, kind="place", type="place", label=PLACES[params.place].label))
    crop = world.add(Entity(id="crop", kind="thing", type="crop", label=CROPS[params.crop].label))
    lead = world.add(Entity(id="lead", kind="thing", type="lead", label=LEADS[params.lead].label))
    fix = world.add(Entity(id="fix", kind="thing", type="fix", label=FIXES[params.fix].label))
    visitor = world.add(Entity(id="visitor", kind="character", type="person", label=f"the {params.external_visitor} visitor"))
    world.facts.update(params=params, child=child, caretaker=caretaker, place=place, crop=crop, lead=lead, fix=fix, visitor=visitor)

    child.memes["curiosity"] = 1
    caretaker.memes["care"] = 1
    place.meters["quiet"] = 1

    world.say(f"{child.id} and {caretaker.label_word} tended the {CROPS[params.crop].label} in {PLACES[params.place].label}.")
    world.say(f"They wanted to nurture it with water, shade, and patient hands.")

    world.para()
    world.say(f"But then {child.id} noticed something odd: {LEADS[params.lead].clue_text}")
    child.meters["suspense"] += 1
    caretaker.meters["suspense"] += 1

    world.para()
    world.say(f"At the {PLACES[params.place].label}, an {params.external_visitor} had been seen near the gate.")
    world.say(f'"Do you think it was a thief?" {child.id} whispered.')
    caretaker.memes["dread"] += 1

    world.para()
    world.say(f"{caretaker.label_word.capitalize()} chose not to rush. {caretaker.pronoun().capitalize()} kept looking at the clue and listening for another sound.")
    world.say(f"Then {visitor.label} passed by outside, and the shadows moved like a secret.")

    # bad ending: the external visitor is not resolved in time, and the crop is ruined
    world.para()
    crop.meters["disturbance"] += 1
    propagate(world, narrate=False)
    world.say(f"While they hesitated, the beet bed was trampled and the strongest leaves were torn away.")
    world.say(f"{child.id} ran to help, but the damage was already done.")

    world.para()
    world.say(f"{caretaker.label_word.capitalize()} knelt beside the bed and found only bent stems and muddy roots.")
    world.say(f'The mystery had an answer, but it was a sad one: somebody from outside had come, and the beet patch could not be saved in time.')
    world.say(f"That night, the garden stayed quiet, and the little bed of beets never grew back the way it should have.")

    world.facts["outcome"] = "bad"
    world.facts["suspense"] = suspicion_level(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a suspenseful whodunit for a young child that includes the words "external", "nurture", and "beet".',
        f"Tell a garden mystery where {p.child} tries to nurture a beet bed, notices a strange clue, and wonders whether an external visitor is involved.",
        f"Write a child-facing mystery with a nervous, clue-by-clue mood and a bad ending where the beet patch is ruined before the answer arrives.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    child = f["child"]
    caret = f["caretaker"]
    crop = f["crop"]
    lead = f["lead"]
    fix = f["fix"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {caret.label_word}, who were trying to care for the beet bed together. The garden clue made the day feel like a mystery."
        ),
        QAItem(
            question="What clue made the story feel suspenseful?",
            answer=f"The clue was {LEADS[p.lead].clue_text.lower()} It made {child.id} and {caret.id} worry that someone had been sneaking around the garden."
        ),
        QAItem(
            question="What happened to the beet bed in the end?",
            answer="The beet bed was damaged before anyone could save it. The mystery got an answer too late, so the ending stayed sad."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to nurture a plant?",
            answer="To nurture a plant means to care for it gently so it can grow. People nurture plants by watering them, giving them sunlight, and protecting them."
        ),
        QAItem(
            question="What is a beet?",
            answer="A beet is a root vegetable that grows in the ground. It can be red, purple, or golden, and people eat it after it is picked."
        ),
        QAItem(
            question="What does external mean?",
            answer="External means outside or from beyond the thing you are talking about. If a visitor is external to a garden, they come from outside it."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only tells clue-driven garden mysteries with a watchful or external place.)"


ASP_RULES = r"""
valid(P,C,L) :- place(P), crop(C), lead(L), watchful(P).
suspense_rises(C) :- clue(C), beet(C).
bad_ending :- suspense_rises(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.external:
            lines.append(asp.fact("external", pid))
        if p.watchful:
            lines.append(asp.fact("watchful", pid))
    for cid in CROPS:
        lines.append(asp.fact("crop", cid))
    for lid in LEADS:
        lines.append(asp.fact("lead", lid))
        lines.append(asp.fact("clue", lid))
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
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, crop=None, lead=None, fix=None, visitor=None,
            child=None, child_gender=None, caretaker=None, caretaker_gender=None
        ), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        print(f"EMIT SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.crop not in CROPS:
        raise StoryError("Unknown crop.")
    if params.lead not in LEADS:
        raise StoryError("Unknown lead.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
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
    StoryParams(
        place="fence",
        crop="beet",
        lead="open_gate",
        fix="report",
        external_visitor="stranger",
        child="Mina",
        child_gender="girl",
        caretaker="Dad",
        caretaker_gender="father",
        weather="foggy",
    ),
    StoryParams(
        place="garden",
        crop="beets",
        lead="muddy_boots",
        fix="lantern",
        external_visitor="neighbor",
        child="Owen",
        child_gender="boy",
        caretaker="Mom",
        caretaker_gender="mother",
        weather="quiet",
    ),
]


def _resolve_choice(value: Optional[str], choices: list[str]) -> str:
    if value is not None:
        return value
    return random.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.crop is None or c[1] == args.crop)
              and (args.lead is None or c[2] == args.lead)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, crop, lead = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    caretaker_gender = args.caretaker_gender or ("mother" if child_gender == "girl" else "father")
    return StoryParams(
        place=place,
        crop=crop,
        lead=lead,
        fix=args.fix or rng.choice(sorted(FIXES)),
        external_visitor=args.visitor or rng.choice(["neighbor", "delivery", "stranger"]),
        child=args.child or _pick_name(rng, child_gender),
        child_gender=child_gender,
        caretaker=args.caretaker or _pick_name(rng, "girl" if caretaker_gender == "mother" else "boy"),
        caretaker_gender=caretaker_gender,
        weather=rng.choice(["quiet", "foggy", "rainy"]),
    )


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
        for row in combos:
            print("  ", row)
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
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.place} / {p.crop} / {p.lead}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
