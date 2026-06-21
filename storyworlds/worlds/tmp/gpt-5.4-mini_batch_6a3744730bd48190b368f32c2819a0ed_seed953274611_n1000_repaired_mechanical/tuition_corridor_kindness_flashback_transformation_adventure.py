#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tuition_corridor_kindness_flashback_transformation_adventure.py
===============================================================================================

A small standalone storyworld for a child-facing adventure tale about a corridor,
tuition, kindness, a remembered flashback, and a transformation that changes the
ending image.

The world is intentionally tiny:
- a child needs tuition money to keep an adventure club going,
- an argument or setback happens in a corridor,
- kindness triggers a flashback to a past favor,
- that memory leads to a transformation in attitude and action,
- the ending shows a concrete change in the world.

The prose engine is state-driven: meters and memes accumulate, rules fire, and
the final text reflects what actually happened in the simulated world.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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


@dataclass
class Place:
    id: str
    label: str
    corridor: bool = False
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
class TuitionNeed:
    id: str
    label: str
    amount: int
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
class HelpOffer:
    id: str
    label: str
    kindness: int
    text: str
    flashback_text: str
    transform_text: str
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
    need: str
    helper: str
    hero: str
    hero_gender: str
    helper_gender: str
    parent: str
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


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["memory"] += 1
    world.facts["flashback"] = True
    out.append("__flashback__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    hero = world.get("hero")
    if helper.memes["memory"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["resolve"] += 1
    hero.memes["hope"] += 1
    world.facts["transformed"] = True
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("flashback", _r_flashback), Rule("transformation", _r_transformation)]


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


def is_reasonable(place: Place, need: TuitionNeed, offer: HelpOffer) -> bool:
    return place.corridor and need.amount > 0 and offer.kindness >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for nid, need in NEEDS.items():
            for hid, offer in OFFERS.items():
                if is_reasonable(place, need, offer):
                    combos.append((pid, nid, hid))
    return combos


def build_story(world: World, place: Place, need: TuitionNeed, offer: HelpOffer) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    parent = world.get("parent")

    world.say(
        f"On a bright afternoon, {hero.id} hurried down the {place.label} with a small envelope "
        f"for tuition."
    )
    world.say(
        f"{hero.id} wanted to reach the office before the bell rang, because the tuition note "
        f"said the class trip depended on it."
    )
    world.para()
    world.say(
        f"At the end of the {place.label}, {helper.id} noticed the worried look on {hero.id}'s face "
        f"and stepped aside with a gentle smile."
    )
    hero.memes["worry"] += 1
    helper.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f'"You look stuck," {helper.id} said. "{offer.text}"'
    )
    world.facts["offer_text"] = offer.text
    world.facts["need_label"] = need.label
    propagate(world, narrate=False)
    if world.facts.get("flashback"):
        world.para()
        world.say(
            f"The kind words sparked a flashback in {helper.id}'s mind."
        )
        world.say(
            f"{helper.id} remembered a rainy day when {hero.id} had shared an umbrella and waited "
            f"patiently in the corridor until the teachers arrived."
        )
        world.say(
            f"That memory made {helper.id} stand taller, and {offer.flashback_text}"
        )
    if world.facts.get("transformed"):
        world.para()
        helper.memes["confidence"] += 1
        hero.memes["relief"] += 1
        world.say(
            f"The whole mood changed. {helper.id} no longer sounded unsure; {offer.transform_text}"
        )
        world.say(
            f"{parent.id} came over, saw the neat envelope, and thanked them both for being so kind."
        )
        world.say(
            f"Together they walked through the corridor to the office, and the tuition was paid in time."
        )
        world.say(
            f"By the end, the long corridor did not feel lonely at all. It felt like a safe path to a new adventure."
        )
    else:
        world.para()
        world.say(
            f"Nothing changed, and the envelope stayed in {hero.id}'s hand while the bell kept ringing."
        )
        world.say(
            f"The corridor felt longer and colder, and the tuition promise was left unfinished."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        place=place,
        need=need,
        offer=offer,
        success=bool(world.facts.get("transformed")),
    )


def tell(place: Place, need: TuitionNeed, offer: HelpOffer,
         hero_name: str = "Mina", hero_gender: str = "girl",
         helper_name: str = "Jasper", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    corridor = world.add(Entity(id="corridor", kind="place", type="place", label=place.label, tags=place.tags))
    envelope = world.add(Entity(id="tuition", kind="thing", type="thing", label=need.label, tags=need.tags))

    hero.meters["hurry"] += 1
    hero.meters["tuition"] += need.amount
    helper.memes["kindness"] += 1
    world.facts["corridor"] = corridor
    world.facts["envelope"] = envelope

    build_story(world, place, need, offer)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "tuition" and "corridor".',
        f"Tell a kind adventure where {f['hero'].id} is hurrying through a corridor with tuition to pay, and a friend helps.",
        f"Write a story with a flashback and a transformation, where kindness changes what happens in a corridor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    place = f["place"]
    need = f["need"]
    qa = [
        QAItem(
            question="What was the child trying to do?",
            answer=f"{hero.id} was trying to get the tuition paid on time. The child hurried through the corridor because the class trip depended on it."
        ),
        QAItem(
            question="What kind thing did the helper do?",
            answer=f"{helper.id} spoke gently and offered help instead of getting in the way. That kindness made it possible to remember a good moment and keep going."
        ),
    ]
    if f.get("flashback"):
        qa.append(
            QAItem(
                question="What did the helper remember in the flashback?",
                answer=f"{helper.id} remembered a time when {hero.id} had helped before in the same corridor. That memory made the helper want to return the kindness."
            )
        )
    if f.get("transformed"):
        qa.append(
            QAItem(
                question="How did the situation change by the end?",
                answer=f"The worried mood transformed into a helpful one, and the tuition was paid in time. The corridor became a path to success instead of a place of worry."
            )
        )
    qa.append(
        QAItem(
            question="Who noticed the child at the corridor?",
            answer=f"{helper.id} noticed {hero.id}, and then {parent.id} came to see the plan through. Their help kept the adventure moving."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tuition?",
            answer="Tuition is the money paid for lessons or school classes. It helps a child keep learning and joining activities."
        ),
        QAItem(
            question="What is a corridor?",
            answer="A corridor is a long hallway inside a building. People walk through it to reach other rooms."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring. A kind action can make another person's hard moment feel lighter."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened before. It can help explain why a character changes what they do."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change. In a story, it often means a feeling, choice, or situation becomes something new."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(place: Place, need: TuitionNeed, offer: HelpOffer) -> str:
    if not place.corridor:
        return "(No story: this tale needs a corridor, because the adventure turns on a hallway decision.)"
    if offer.kindness < 2:
        return "(No story: the kindness level is too low for a believable flashback and transformation.)"
    if need.amount <= 0:
        return "(No story: tuition needs a real amount at stake.)"
    return "(No story: this combination does not make a sensible corridor adventure.)"


PLACES = {
    "hallway": Place(id="hallway", label="corridor", corridor=True, tags={"corridor"}),
    "school_corridor": Place(id="school_corridor", label="school corridor", corridor=True, tags={"corridor", "school"}),
    "library_corridor": Place(id="library_corridor", label="library corridor", corridor=True, tags={"corridor", "library"}),
}

NEEDS = {
    "tuition_note": TuitionNeed(id="tuition_note", label="tuition note", amount=1, tags={"tuition"}),
    "tuition_coin": TuitionNeed(id="tuition_coin", label="tuition coin pouch", amount=2, tags={"tuition"}),
    "tuition_envelope": TuitionNeed(id="tuition_envelope", label="tuition envelope", amount=3, tags={"tuition"}),
}

OFFERS = {
    "kind_note": HelpOffer(
        id="kind_note",
        label="a kind note",
        kindness=2,
        text="I can walk with you to the office so you do not have to carry this alone.",
        flashback_text="he offered to carry the envelope while the memory warmed his face.",
        transform_text="he lifted the envelope with new confidence and guided the way."
    ),
    "share_map": HelpOffer(
        id="share_map",
        label="a shared map",
        kindness=3,
        text="Let's use my map of the building and find the office together.",
        flashback_text="the remembered favor turned the map into a promise kept.",
        transform_text="he unfolded the map like a captain and led them forward."
    ),
    "carry_together": HelpOffer(
        id="carry_together",
        label="a carrying hand",
        kindness=4,
        text="I'll carry one side of the envelope, and we'll bring the tuition together.",
        flashback_text="the memory of old kindness made the corridor feel brighter.",
        transform_text="he took the other side of the envelope, and the weight seemed to vanish."
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zuri", "Sana"]
BOY_NAMES = ["Jasper", "Eli", "Theo", "Noah", "Arlo", "Ben"]


CURATED = [
    StoryParams(place="school_corridor", need="tuition_envelope", helper="carry_together", hero="Mina", hero_gender="girl", helper_gender="boy", parent="mother"),
    StoryParams(place="library_corridor", need="tuition_note", helper="share_map", hero="Jasper", hero_gender="boy", helper_gender="girl", parent="father"),
    StoryParams(place="hallway", need="tuition_coin", helper="kind_note", hero="Nora", hero_gender="girl", helper_gender="boy", parent="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny corridor adventure with tuition, kindness, flashback, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--helper", choices=OFFERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and not PLACES[args.place].corridor:
        raise StoryError(explain_rejection(PLACES[args.place], NEEDS["tuition_note"], OFFERS["kind_note"]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.need is None or c[1] == args.need)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid corridor adventure matches the given options.)")
    place, need, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, need=need, helper=helper, hero=hero, hero_gender=hero_gender, helper_gender=helper_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.need not in NEEDS or params.helper not in OFFERS:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(PLACES[params.place], NEEDS[params.need], OFFERS[params.helper],
                 hero_name=params.hero, hero_gender=params.hero_gender,
                 helper_name=("Jasper" if params.helper_gender == "boy" else "Lila") if params.helper == "share_map" and params.helper_gender else ("Jasper" if params.helper_gender == "boy" else "Lila"),
                 helper_gender=params.helper_gender, parent_type=params.parent)
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.corridor:
            lines.append(asp.fact("corridor", pid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("amount", nid, n.amount))
    for hid, h in OFFERS.items():
        lines.append(asp.fact("offer", hid))
        lines.append(asp.fact("kindness", hid, h.kindness))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,N,H) :- place(P), corridor(P), need(N), amount(N,A), A > 0, offer(H), kindness(H,K), K >= 2.
"""


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
        print("MISMATCH: ASP gate differs from Python valid_combos().")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        rc = 1
    if rc == 0:
        print(f"OK: ASP parity matches and smoke test passed ({len(valid_combos())} combos).")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} in {p.place} ({p.need}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
