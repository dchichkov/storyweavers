#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/agent_inherit_monthly_dining_room_happy_ending.py
==================================================================================

A small standalone story world for a dining-room animal tale about an agent,
an inheritance, and a monthly plan that ends in reconciliation.

Seed prompt:
------------
Write a story that includes the following words and narrative instruments.
Words: agent, inherit, monthly
Setting: dining room
Features: Happy Ending, Sound Effects, Reconciliation
Style: Animal Story

World idea:
-----------
A family of animals is gathered in the dining room for a monthly check-in.
One young animal worries about inheriting a keepsake or responsibility from an
older relative, and another animal feels left out by the plan. The children/
animals speak up, an adult or elder clears up the misunderstanding, and the
group reconciles. Sound effects from the dining room and the happy ending are
part of the story, but the simulation drives the prose.

This world is intentionally small: it prefers a few plausible scenarios over a
wide weak menu. The story should feel authored, concrete, and child-facing.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
        return {"mother": "mom", "father": "dad", "grandmother": "grandma",
                "grandfather": "grandpa"}.get(self.type, self.type)



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
    surface: str
    echoes: list[str] = field(default_factory=list)

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
class Item:
    id: str
    label: str
    phrase: str
    plural: bool = False
    inherited: bool = False
    valuable: bool = False
    shared: bool = False
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
class EventCue:
    id: str
    sound: str
    text: str
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


def _r_spike_feelings(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["worry"] >= THRESHOLD and world.get("guest").memes["left_out"] >= THRESHOLD:
        sig = ("spike",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["tears"] += 1
            world.get("guest").memes["hurt"] += 1
            out.append("__tension__")
    return out


CAUSAL_RULES = [
    Rule("spike_feelings", "social", _r_spike_feelings),
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


def explain_rejection(choice: str) -> str:
    return f"(No story: {choice} would not fit this small dining-room inheritance tale.)"


def reasonableness_gate(kind: str, reconciliation: bool) -> bool:
    return kind in {"small_misunderstanding", "monthly_checkin"} and reconciliation


def tell(place: Place, item: Item, cue: EventCue, parent_type: str = "mother",
         elder_type: str = "grandmother", child_type: str = "cat",
         guest_type: str = "dog", agent_role: str = "family agent",
         monthly: bool = True, inherited: bool = True,
         misunderstanding: str = "inheritance note") -> World:
    world = World()
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="mediator"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder", role="source"))
    child = world.add(Entity(id="child", kind="character", type=child_type, label="the child", role="worrying one", attrs={"agent_role": agent_role}))
    guest = world.add(Entity(id="guest", kind="character", type=guest_type, label="the guest", role="left_out one"))
    table = world.add(Entity(id="table", type="thing", label="the dining table"))
    world.facts["place"] = place
    world.facts["item"] = item
    world.facts["cue"] = cue
    world.facts["parent"] = parent
    world.facts["elder"] = elder
    world.facts["child"] = child
    world.facts["guest"] = guest
    world.facts["table"] = table
    world.facts["monthly"] = monthly
    world.facts["inherited"] = inherited
    world.facts["misunderstanding"] = misunderstanding
    world.facts["agent_role"] = agent_role

    child.memes["worry"] = 1
    guest.memes["left_out"] = 1

    world.say(
        f"On a monthly evening in {place.label}, {child.id} and {guest.id} sat near "
        f"the big table while {parent.label_word} and {elder.id} gathered the family."
    )
    world.say(
        f"Tap-tap, went the spoon. Rustle-rustle, went the napkins. The room felt calm "
        f"and snug, like it was waiting to hear a story."
    )

    world.para()
    world.say(
        f"{elder.id} opened an envelope and smiled. Inside was a note about what {child.id} might "
        f"{'inherit' if inherited else 'share'} one day: {item.phrase}."
    )
    world.say(
        f'{child.id} blinked hard. "Am I an agent for the family now? Does that mean I have to do it alone?"'
    )
    child.memes["worry"] += 1
    guest.memes["left_out"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{guest.id} nudged a chair leg and muttered, " 
        f'"What about me? I thought the monthly meeting was for everyone."'
    )
    world.say(f"{cue.sound} went the teacup as it softly tapped the saucer.")
    world.say(
        f"{parent.label_word.capitalize()} listened carefully, then leaned forward. "
        f'"Let us slow down and talk," {parent.pronoun()} said.'
    )

    world.para()
    child.memes["fear"] += 1
    guest.memes["hurt"] += 1
    world.say(
        f"{parent.label_word.capitalize()} explained that the note did not mean anyone would be left out. "
        f"It was only a kind message about a keepsake, not a secret rule."
    )
    world.say(
        f"{parent.label_word.capitalize()} added that {child.id} was not being made into a lone agent; "
        f"everyone in the family could help decide together."
    )
    world.say(
        f"{guest.id}'s ears perked up. {child.id} let out a tiny sniffle and looked at the floor."
    )

    world.para()
    world.say(
        f"{elder.id} tucked the envelope back into {item.label} and pushed it toward the middle of the table. "
        f'"It belongs to the whole story," {elder.id} said kindly.'
    )
    world.say(
        f"{child.id} slid the note back. {guest.id} scooted closer. The chair legs made a soft "
        f"scrape-scrape on the floor, and nobody minded anymore."
    )
    world.say(
        f'{child.id} whispered, "I’m sorry." {guest.id} answered, "I’m sorry too."'
    )
    child.memes["worry"] = 0
    guest.memes["hurt"] = 0
    child.memes["relief"] += 1
    guest.memes["relief"] += 1
    parent.memes["relief"] += 1
    elder.memes["relief"] += 1

    world.para()
    world.say(
        f"{parent.label_word.capitalize()} smiled and brought out warm bread. Everyone shared pieces "
        f"right there at the dining table."
    )
    world.say(
        f"The monthly meeting ended with soft laughter, a settled heart, and a plan to keep the note "
        f"safe until the family decided together."
    )
    world.say(
        f"{child.id} was glad to be part of the family, and {guest.id} was glad to be included too."
    )

    world.facts.update(outcome="reconciled", sound=cue.sound, place=place.label, item=item, cue=cue,
                       parent=parent, elder=elder, child=child, guest=guest)
    return world


PLACES = {
    "dining_room": Place("dining_room", "the dining room", "the dining table", echoes=["tap", "scrape"]),
}

ITEMS = {
    "photo_album": Item("photo_album", "photo album", "a thick photo album", inherited=True, valuable=True,
                        shared=True, tags={"inherit", "monthly"}),
    "silver_spoon": Item("silver_spoon", "silver spoon", "a little silver spoon", inherited=True, valuable=True,
                         shared=False, tags={"inherit"}),
    "recipe_box": Item("recipe_box", "recipe box", "a hand-labeled recipe box", inherited=True, valuable=True,
                       shared=True, tags={"monthly"}),
}

CUES = {
    "tap": EventCue("tap", "tap-tap", "Tap-tap", tags={"sound"}),
    "rustle": EventCue("rustle", "rustle-rustle", "Rustle-rustle", tags={"sound"}),
    "scrape": EventCue("scrape", "scrape-scrape", "Scrape-scrape", tags={"sound"}),
}

NAMES = ["Milo", "Nina", "Pip", "Poppy", "Jasper", "Mabel", "Rosie", "Otis"]
ANIMAL_TYPES = ["cat", "dog", "rabbit", "fox", "bear", "mouse", "badger", "owl"]


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    cue: str
    child_name: str
    child_type: str
    guest_name: str
    guest_type: str
    parent: str
    elder: str
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
    for p in PLACES:
        for i in ITEMS:
            for c in CUES:
                combos.append((p, i, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guest = f["guest"]
    item = f["item"]
    return [
        f'Write an animal story set in {f["place"]} that includes the words "agent", "inherit", and "monthly".',
        f"Tell a gentle reconciliation story where {child.id} thinks a family note means something serious, but {guest.id} feels left out and the family clears it up.",
        f"Write a happy-ending story with a dining room, a soft sound effect, and a family inheritance that turns out to be shared kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guest = f["guest"]
    parent = f["parent"]
    elder = f["elder"]
    item = f["item"]
    cue = f["cue"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {guest.id}, and their family in the dining room. The elder brings up a monthly note, and the parent helps everyone understand it."
        ),
        QAItem(
            question=f"Why did {child.id} feel worried?",
            answer=f"{child.id} thought the note meant {child.id} had to act like an agent all alone and inherit something without help. After that, {child.id} got scared until the family explained it was just a shared keepsake story."
        ),
        QAItem(
            question=f"How did the family reconcile?",
            answer=f"{parent.id} slowed the room down, listened to both feelings, and explained the note kindly. Then {elder.id} moved the {item.label} to the middle so everyone could share the decision, and the two friends apologized to each other."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with warm bread, quiet laughter, and everyone feeling included again. The monthly gathering finished with a peaceful plan instead of an argument."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a monthly meeting?",
            answer="A monthly meeting happens once each month. Families sometimes use it to check in, share news, and make plans together."
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to stop being upset with each other and become friendly again. It usually happens after people talk and understand each other better."
        ),
        QAItem(
            question="What is an agent?",
            answer="An agent is someone who acts for another person or helps carry out a plan. In stories, the word can also mean a helper who does a job for a family or group."
        ),
        QAItem(
            question="What does inherit mean?",
            answer="To inherit means to receive something from a family member after a long time or when the family decides to pass it on. It can be a toy, a keepsake, or a special responsibility."
        ),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("dining_room", "photo_album", "tap", "Milo", "cat", "Pip", "dog", "mother", "grandmother"),
    StoryParams("dining_room", "recipe_box", "rustle", "Nina", "rabbit", "Otis", "fox", "father", "grandfather"),
    StoryParams("dining_room", "silver_spoon", "scrape", "Poppy", "mouse", "Jasper", "bear", "mother", "grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: dining-room animal tale with reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--name")
    ap.add_argument("--guest-name")
    ap.add_argument("--child-type", choices=ANIMAL_TYPES)
    ap.add_argument("--guest-type", choices=ANIMAL_TYPES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    combos = valid_combos()
    if args.place and args.place not in PLACES:
        raise StoryError(explain_rejection(args.place))
    if args.item and args.item not in ITEMS:
        raise StoryError(explain_rejection(args.item))
    if args.cue and args.cue not in CUES:
        raise StoryError(explain_rejection(args.cue))
    place, item, cue = rng.choice(combos)
    if args.place:
        place = args.place
    if args.item:
        item = args.item
    if args.cue:
        cue = args.cue
    child_name = args.name or rng.choice(NAMES)
    guest_name = args.guest_name or rng.choice([n for n in NAMES if n != child_name])
    child_type = args.child_type or rng.choice(ANIMAL_TYPES)
    guest_type = args.guest_type or rng.choice([t for t in ANIMAL_TYPES if t != child_type])
    parent = args.parent or rng.choice(["mother", "father"])
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(place, item, cue, child_name, child_type, guest_name, guest_type, parent, elder)


def tell_story(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    world = World()
    place = PLACES[params.place]
    item = ITEMS[params.item]
    cue = CUES[params.cue]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    guest = world.add(Entity(id=params.guest_name, kind="character", type=params.guest_type, role="guest"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", role="mediator"))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, label="the elder", role="source"))
    world.add(Entity(id="table", type="thing", label="the dining table"))
    child.memes["worry"] = 1
    guest.memes["left_out"] = 1
    world.facts.update(place=place.label, item=item, cue=cue, child=child, guest=guest, parent=parent, elder=elder)

    world.say(
        f"On a monthly evening in {place.label}, {child.id} and {guest.id} gathered in the dining room with {parent.label_word} and {elder.id}."
    )
    world.say(
        f"The table shone under the lamp, and {cue.sound} went the little dishes as the family settled in."
    )
    world.para()
    world.say(
        f"{elder.id} brought out a note about what {child.id} might inherit one day: {item.phrase}."
    )
    world.say(
        f"{child.id} leaned close. '{child.id} wondered if an agent had to do everything alone,' {child.id} whispered."
    )
    child.memes["worry"] += 1
    guest.memes["left_out"] += 1
    world.para()
    world.say(
        f"{guest.id} worried too, because the monthly talk sounded important and a little secret."
    )
    world.say(
        f'{cue.sound.capitalize()} went the teacup again. Then {parent.label_word.capitalize()} said, "Let us talk it through."'
    )
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} explained that nobody was being shut out."
    )
    world.say(
        f"The note only meant the family would keep {item.label} safe and decide together, kindly and slowly."
    )
    world.say(
        f"{elder.id} slid the {item.label} to the middle of the table, and {child.id} and {guest.id} sat a little closer."
    )
    world.para()
    child.memes["worry"] = 0
    guest.memes["left_out"] = 0
    child.memes["relief"] += 1
    guest.memes["relief"] += 1
    parent.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.say(
        f'{child.id} said, "I am sorry." {guest.id} nodded and said, "I am sorry too."'
    )
    world.say(
        f"Then the family shared warm bread, and the dining room filled with soft smiles instead of worry."
    )
    world.say(
        f"By the end of the monthly meeting, everyone felt included, and the little {child.type} was glad to inherit a family story, not a lonely job."
    )
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
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for c in CUES:
        lines.append(asp.fact("cue", c))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,C) :- place(P), item(I), cue(C).
happy_ending(valid).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        return 1 if not print(exc) else 1
    return rc


def format_header(sample: StorySample, idx: int, all_mode: bool) -> str:
    if all_mode:
        p = sample.params
        return f"### {p.child_name} & {p.guest_name}: monthly {p.item} in {p.place}"
    if idx >= 0:
        return f"### variant {idx + 1}"
    return ""


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, i, c in combos:
            print(f"  {p:12} {i:12} {c}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=format_header(sample, i, args.all))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
