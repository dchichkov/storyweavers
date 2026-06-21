#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/barge_lesson_learned_heartwarming.py
=====================================================================

A standalone story world for a small, heartwarming lesson-learned tale:
a child tries to use a river barge as a shortcut, something goes wrong in a
gentle, non-dangerous way, a calm adult helps, and the child learns a better
way to handle the same problem next time.

Seed request
------------
Words: barge
Features: Lesson Learned
Style: Heartwarming

Domain summary
--------------
This world simulates a tiny riverside day with:
- a barge carrying a load,
- a child who wants to move something quickly,
- a concern about balance, timing, or dropping a fragile item,
- a grown-up who predicts the trouble before it happens,
- a brief mishap that is fixed with patience and teamwork,
- an ending that shows the lesson has stuck.

The prose is state-driven: emotional meters and physical meters accumulate, and
the ending reflects what changed in the world model.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
- uses a Python reasonableness gate and an inline ASP twin
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
class Item:
    id: str
    label: str
    fragile: bool = False
    heavy: bool = False
    floats: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Place:
    id: str
    label: str
    near_water: bool = False
    narrow: bool = False
    sheltered: bool = False

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
class Activity:
    id: str
    verb: str
    goal: str
    risk: str
    mess: str
    keyword: str
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
class Helper:
    id: str
    label: str
    tool: str
    method: str
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
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_item(self, iid: str) -> Item:
        return self.items[iid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.items = copy.deepcopy(self.items)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
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
    child = world.entities.get("child")
    item = world.items.get("parcel")
    if not child or not item:
        return out
    if child.meters["rush"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["wobble"] += 1
    child.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    item = world.items.get("parcel")
    if not item or item.meters["wobble"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["spilled"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("spill", _r_spill)]


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


def reasonableness_gate(place: Place, activity: Activity, item: Item) -> bool:
    return place.near_water and activity.id == "barge" and (item.fragile or item.heavy)


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.id in {"rope", "crate"}]


def best_helper() -> Helper:
    return max(HELPERS.values(), key=lambda h: 1 if h.id in {"rope", "crate"} else 0)


def predict_turn(world: World, activity: Activity, item_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get_entity("child"), activity, item_id, narrate=False)
    it = sim.get_item(item_id)
    return {"wobble": it.meters["wobble"], "spilled": it.meters["spilled"]}


def _do_activity(world: World, child: Entity, activity: Activity, item_id: str, narrate: bool = True) -> None:
    child.meters["rush"] += 1
    child.memes["hope"] += 1
    world.say(f"{child.id} wanted to {activity.verb} with the {item_id} on the barge.")
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, adult: Entity, place: Place, activity: Activity) -> None:
    child.memes["joy"] += 1
    adult.memes["care"] += 1
    world.say(
        f"On a bright morning by the river, {child.id} and {adult.id} went to {place.label}. "
        f"The water moved slowly, and a barge drifted by with a careful little clatter."
    )
    world.say(
        f"{child.id} loved to watch the barge and {activity.verb}, because it felt like helping a floating home."
    )


def want_help(world: World, child: Entity, activity: Activity, item: Item) -> None:
    world.say(
        f"{child.id} saw the {item.label} and thought, \"If I take it across on the barge, "
        f"I can finish the job faster.\""
    )
    child.memes["impatience"] += 1


def warn(world: World, adult: Entity, child: Entity, activity: Activity, item: Item) -> None:
    pred = predict_turn(world, activity, "parcel")
    if pred["wobble"] < THRESHOLD:
        return
    world.facts["predicted_wobble"] = pred["wobble"]
    world.say(
        f"{adult.id} noticed the wind tugging at the deck and said, "
        f"\"That might make the {item.label} tip and spill.\""
    )
    adult.memes["wisdom"] += 1
    child.memes["attention"] += 1


def insist(world: World, child: Entity, activity: Activity) -> None:
    child.memes["stubborn"] += 1
    world.say(f"{child.id} still tried to hurry, stepping a little too fast.")
    world.facts["choice"] = "hurry"


def accident(world: World, item: Item, activity: Activity) -> None:
    _do_activity(world, world.get_entity("child"), activity, "parcel")
    if item.meters["wobble"] >= THRESHOLD:
        item.meters["spilled"] += 1
        world.say(
            f"The barge rocked once, and the {item.label} slid sideways. A few shiny pieces slipped loose."
        )


def fix(world: World, adult: Entity, child: Entity, helper: Helper, item: Item) -> None:
    item.meters["spilled"] = 0.0
    item.meters["secured"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    adult.memes["pride"] += 1
    world.say(
        f"{adult.id} knelt down, tied the {item.label} with the {helper.tool}, and showed {child.id} how to hold it steady."
    )
    world.say(
        f"Together they used {helper.method}, and the parcel stayed snug while the barge glided on."
    )


def lesson(world: World, adult: Entity, child: Entity, activity: Activity, item: Item) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say("For a moment, they both listened to the river.")
    world.say(
        f"Then {adult.id} smiled and said, \"Quick is nice, but careful keeps things safe.\""
    )
    world.say(
        f"{child.id} nodded, hugged the {item.label}, and promised to remember that next time."
    )


def ending(world: World, child: Entity, adult: Entity, place: Place, item: Item) -> None:
    world.say(
        f"By the end of the day, the {item.label} was secure, the barge kept floating gently, "
        f"and {child.id} had learned that a steady way could still be a happy way."
    )
    world.say(
        f"{child.id} waved at the river and smiled at {adult.id}, feeling older in a kind way."
    )


def tell(place: Place, activity: Activity, item: Item, helper: Helper,
         child_name: str = "Milo", child_gender: str = "boy",
         adult_name: str = "Mama", adult_gender: str = "mother") -> World:
    world = World()
    child = world.add_entity(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add_entity(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    parcel = world.add_item(Item(id="parcel", label=item.label, fragile=item.fragile, heavy=item.heavy, floats=item.floats))

    setup(world, child, adult, place, activity)
    world.para()
    want_help(world, child, activity, parcel)
    warn(world, adult, child, activity, parcel)
    insist(world, child, activity)
    accident(world, parcel, activity)
    world.para()
    fix(world, adult, child, helper, parcel)
    lesson(world, adult, child, activity, parcel)
    world.para()
    ending(world, child, adult, place, parcel)

    world.facts.update(
        child=child, adult=adult, place=place, activity=activity, item=item,
        helper=helper, outcome="learned", predicted_wobble=world.facts.get("predicted_wobble", 0),
    )
    return world


PLACES = {
    "riverside": Place("riverside", "the riverside dock", near_water=True, narrow=True),
    "harbor": Place("harbor", "the small harbor", near_water=True, narrow=False),
    "canal": Place("canal", "the quiet canal path", near_water=True, narrow=True, sheltered=True),
}

ACTIVITIES = {
    "barge": Activity("barge", "ride the barge with", "helping on the barge",
                      "rush across the deck", "rushed", "barge",
                      tags={"barge", "water", "river"}),
}

ITEMS = {
    "parcel": Item("parcel", "a parcel of muffins", fragile=True, heavy=False, floats=False),
    "crate": Item("crate", "a crate of jars", fragile=True, heavy=True, floats=False),
    "basket": Item("basket", "a basket of apples", fragile=False, heavy=True, floats=False),
}

HELPERS = {
    "rope": Helper("rope", "rope", "rope", "loop the rope around the parcel",
                   "They used rope to keep the parcel from sliding.", tags={"rope", "barge"}),
    "crate": Helper("crate", "wooden crate", "wooden crate", "nestle the parcel into a crate",
                    "They used a wooden crate to keep everything steady.", tags={"crate", "barge"}),
    "cloth": Helper("cloth", "cloth", "cloth", "wrap the parcel in cloth",
                    "They wrapped it in cloth, but it was not quite enough.", tags={"cloth"}),
}

GIRL_NAMES = ["Maya", "Lina", "Ruby", "Ivy", "Nora", "Ella"]
BOY_NAMES = ["Milo", "Eli", "Theo", "Finn", "Noah", "Ari"]
TRAITS = ["careful", "curious", "gentle", "thoughtful", "bright", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, act in ACTIVITIES.items():
            for iid, item in ITEMS.items():
                if reasonableness_gate(place, act, item):
                    combos.append((pid, aid, iid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    helper: str
    name: str
    gender: str
    adult: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a warm story for a preschooler that includes the word "barge" and ends with a learned lesson.',
        f"Tell a heartwarming river story where {f['child'].id} wants to use the barge to carry {f['item'].label}, "
        f"but learns to secure it more carefully.",
        f"Write a gentle story about a child, a barge, and a wiser choice that protects something fragile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    item = f["item"]
    helper = f["helper"]
    act = f["activity"]
    lines = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {adult.id} at the riverside. They were working beside a barge and trying to carry {item.label} safely."
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {act.verb} with the barge and hurry across the deck. That seemed faster, but it also made the parcel more likely to wobble."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"{adult.id} helped by using {helper.tool} and showing {child.id} how to steady the parcel. The careful method stopped the slipping and made the trip safer."
        ),
        QAItem(
            question="What did the child learn?",
            answer=f"{child.id} learned that moving fast is not always best. A steady, careful way can be kinder to people and safer for fragile things."
        ),
    ]
    return lines


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["helper"].tags)
    out: list[QAItem] = []
    if "barge" in tags:
        out.append(QAItem("What is a barge?", "A barge is a flat boat that carries things on rivers or canals. It moves slowly and is often used to move heavy loads." ))
    if "water" in tags:
        out.append(QAItem("Why do people stay careful near water?", "Water can make things slippery, and a bump or a rush can cause something to fall in. Careful hands help keep everyone and everything safe."))
    if "rope" in tags:
        out.append(QAItem("What does rope help with?", "Rope can tie things together and keep them from sliding or drifting away. It is useful when you want to hold something steady." ))
    if "crate" in tags:
        out.append(QAItem("What is a crate for?", "A crate can hold things so they do not roll around or get damaged. It helps keep items in one safe place."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for i in world.items.values():
        meters = {k: v for k, v in i.meters.items() if v}
        bits = [f"label={i.label}"]
        if meters:
            bits.append(f"meters={dict(meters)}")
        lines.append(f"  {i.id:8} (item   ) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("riverside", "barge", "parcel", "rope", "Milo", "boy", "mother", "careful"),
    StoryParams("harbor", "barge", "crate", "crate", "Maya", "girl", "father", "gentle"),
    StoryParams("canal", "barge", "parcel", "rope", "Theo", "boy", "mother", "thoughtful"),
]


def explain_rejection(place: Place, activity: Activity, item: Item) -> str:
    return "(No story: the chosen river setting and cargo do not make a believable barge lesson.)"


def sensible_choices() -> list[Helper]:
    return [h for h in HELPERS.values() if h.id in {"rope", "crate"}]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.activity and args.item:
        place, act, item = PLACES[args.place], ACTIVITIES[args.activity], ITEMS[args.item]
        if not reasonableness_gate(place, act, item):
            raise StoryError(explain_rejection(place, act, item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, item = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(h.id for h in sensible_choices()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, activity, item, helper, name, gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], ITEMS[params.item],
                 HELPERS[params.helper], params.name, params.gender, params.adult)
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


ASP_RULES = r"""
valid(P,A,I) :- place(P), activity(A), item(I), near_water(P), barge(A), risky(I).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.near_water:
            lines.append(asp.fact("near_water", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.fragile or i.heavy:
            lines.append(asp.fact("risky", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming barge lesson story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
