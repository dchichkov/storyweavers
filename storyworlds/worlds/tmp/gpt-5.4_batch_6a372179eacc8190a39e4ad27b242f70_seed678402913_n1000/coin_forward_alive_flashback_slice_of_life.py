#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py
=========================================================================

A small storyworld about finding a coin during an ordinary errand, remembering
an older lesson in a flashback, and helping someone else's day move forward.

The world stays close to slice-of-life: the stakes are small but real. A child
finds a coin, feels the pull to keep it, notices that another person needs that
very coin for an everyday task, remembers a caregiver's advice, and chooses a
reasonable way to help. The ending image shows the place feeling ordinary and
alive again.

Run it
------
    python storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py --place laundromat
    python storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py --method pin_note
    python storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/coin_forward_alive_flashback_slice_of_life.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "neighbor_woman", "cashier_woman"}
        male = {"boy", "father", "grandfather", "man", "neighbor_man", "driver_man", "baker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    ambient: str
    owner_phrase: str
    need: str
    urgency: int
    has_clerk: bool = False
    clerk_label: str = ""
    clerk_type: str = ""
    use_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    sense: int
    reach: int
    needs_clerk: bool
    text: str
    clerk_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    id: str
    elder_type: str
    elder_label: str
    setting: str
    advice: str
    touch: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place_cfg = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.place_cfg)
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


def _r_worry(world: World) -> list[str]:
    owner = world.entities.get("owner")
    coin = world.entities.get("coin")
    if owner is None or coin is None:
        return []
    if coin.attrs.get("holder") != "ground" or owner.meters["needs_coin"] < THRESHOLD:
        return []
    sig = ("worry", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    return ["__worry__"]


def _r_ready(world: World) -> list[str]:
    owner = world.entities.get("owner")
    coin = world.entities.get("coin")
    if owner is None or coin is None:
        return []
    if coin.attrs.get("holder") != owner.id:
        return []
    sig = ("ready", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.meters["task_ready"] += 1
    owner.memes["relief"] += 1
    child = world.entities.get("child")
    if child is not None:
        child.memes["pride"] += 1
        child.memes["temptation"] = 0.0
        child.memes["relief"] += 1
    place = world.entities.get("place")
    if place is not None:
        place.memes["warmth"] += 1
    return ["__ready__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="ready", tag="social", apply=_r_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combo(place: Place, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if method.needs_clerk and not place.has_clerk:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for method_id, method in METHODS.items():
            if valid_combo(place, method):
                out.append((place_id, method_id))
    return out


def reunion_possible(place: Place, method: Method, delay: int) -> bool:
    return method.reach >= place.urgency + delay


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    method = METHODS[params.method]
    return "reunited" if reunion_possible(place, method, params.delay) else "clerk_safe"


def explain_rejection(place: Place, method: Method) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try a more direct, honest way "
            f"to help, such as {better}.)"
        )
    if method.needs_clerk and not place.has_clerk:
        return (
            f"(No story: {place.label} has no clerk desk in this world, so the "
            f"method '{method.id}' cannot actually hand the coin to anyone.)"
        )
    return "(No story: this place and method do not fit together.)"


def predict_help(world: World, method: Method, delay: int) -> dict:
    sim = world.copy()
    place = sim.facts["place_cfg"]
    return {
        "reunion": reunion_possible(place, method, delay),
        "urgency": place.urgency + delay,
    }


def introduce(world: World, child: Entity, place: Place, caregiver: Entity) -> None:
    child.memes["calm"] += 1
    world.say(
        f"After school, {child.id} walked with {child.pronoun('possessive')} "
        f"{caregiver.label_word} to {place.label}."
    )
    world.say(
        f"{place.scene} {place.ambient} The whole place felt alive in the small, "
        f"busy way an ordinary afternoon can."
    )


def errand(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"{child.id} was only there for a simple errand, the kind that lets a day "
        f"move forward without anybody making a fuss."
    )


def find_coin(world: World, child: Entity) -> None:
    coin = world.get("coin")
    coin.attrs["holder"] = "ground"
    child.memes["temptation"] += 1
    world.say(
        f"Near the floor, right by {child.pronoun('possessive')} shoe, "
        f"{child.pronoun()} spotted a coin."
    )
    world.say(
        f"It was only one coin, but it shone enough to make {child.id} imagine "
        f"a little treat all the same."
    )
    propagate(world, narrate=False)


def owner_notice(world: World, owner: Entity, place: Place) -> None:
    owner.meters["needs_coin"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {owner.phrase} patted {owner.pronoun('possessive')} pocket and looked down in a hurry."
    )
    world.say(
        f'"Oh dear," {owner.pronoun()} said softly. "I had the coin I need for '
        f'{place.use_line}."'
    )


def hesitate(world: World, child: Entity, owner: Entity) -> None:
    child.memes["conflict"] += 1
    if owner.memes["worry"] >= THRESHOLD:
        child.memes["empathy"] += 1
    world.say(
        f"{child.id} curled {child.pronoun('possessive')} fingers around the coin "
        f"and stood still for a moment."
    )
    world.say(
        f"Keeping it would have been easy. But {owner.phrase}'s worried face made "
        f"the coin feel heavier than before."
    )


def flashback(world: World, child: Entity, memory: Memory) -> None:
    child.memes["honesty"] += 1
    world.say(
        f"Just then, {child.id} remembered another day -- {memory.setting}."
    )
    world.say(
        f"In that flashback, {memory.elder_label} had {memory.touch} and said, "
        f'"{memory.advice}"'
    )


def decide(world: World, child: Entity) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} took one step forward, then another. Once {child.pronoun()} "
        f"started moving, the choice felt simpler."
    )


def return_coin(world: World, child: Entity, owner: Entity, method: Method) -> None:
    coin = world.get("coin")
    coin.attrs["holder"] = owner.id
    if method.id == "ask_clerk":
        world.say(
            method.clerk_text.format(child=child.id, owner=owner.phrase)
        )
    else:
        world.say(
            method.text.format(child=child.id, owner=owner.phrase)
        )
    propagate(world, narrate=False)


def owner_uses_coin(world: World, owner: Entity, place: Place) -> None:
    owner.meters["used_coin"] += 1
    world.say(
        f"With a grateful smile, {owner.phrase} used the coin for {place.use_line}."
    )
    world.say(
        f"The little snag in the afternoon loosened at once, and the day moved forward again."
    )


def clerk_safe(world: World, child: Entity, place: Place, method: Method) -> None:
    child.memes["pride"] += 1
    child.memes["temptation"] = 0.0
    child.memes["relief"] += 1
    world.get("place").memes["warmth"] += 1
    clerk = world.entities.get("clerk")
    if clerk is not None:
        world.say(
            f"{clerk.label.capitalize()} tucked the coin into the little dish by the counter "
            f"so the missing person could ask for it."
        )
    world.say(
        f"{child.id} did not see the owner turn back in time, but at least the coin "
        f"was safe and waiting in the right place."
    )
    world.say(
        f"That was not a grand rescue. It was only the careful thing, and it was enough."
    )


def close_story(world: World, child: Entity, caregiver: Entity, place: Place, outcome: str) -> None:
    if outcome == "reunited":
        world.say(
            f"On the way home, {caregiver.label_word} squeezed {child.pronoun('possessive')} hand, "
            f"and {child.id} felt warm all the way to the bus stop."
        )
    else:
        world.say(
            f"When {child.id} turned back toward {caregiver.label_word}, "
            f"{child.pronoun()} felt lighter than before."
        )
    world.say(
        f"Behind them, {place.label} kept humming along, ordinary and alive."
    )


def tell(
    *,
    place: Place,
    method: Method,
    memory: Memory,
    child_name: str,
    child_type: str,
    caregiver_type: str,
    owner_type: str,
    delay: int,
) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    caregiver = world.add(
        Entity(id="Caregiver", kind="character", type=caregiver_type, role="caregiver", label="the caregiver")
    )
    owner = world.add(
        Entity(id="Owner", kind="character", type=owner_type, role="owner", phrase=place.owner_phrase, label="the other grown-up")
    )
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.add(Entity(id="coin", kind="thing", type="coin", label="coin", phrase="a small coin"))
    if place.has_clerk:
        world.add(
            Entity(id="clerk", kind="character", type=place.clerk_type, role="clerk", label=place.clerk_label)
        )

    world.facts.update(
        place_cfg=place,
        method_cfg=method,
        memory_cfg=memory,
        child=child,
        caregiver=caregiver,
        owner=owner,
        delay=delay,
    )

    introduce(world, child, place, caregiver)
    errand(world, child, place)

    world.para()
    find_coin(world, child)
    owner_notice(world, owner, place)
    hesitate(world, child, owner)

    world.para()
    flashback(world, child, memory)
    pred = predict_help(world, method, delay)
    world.facts["predicted_urgency"] = pred["urgency"]
    decide(world, child)

    outcome = "reunited" if pred["reunion"] else "clerk_safe"
    world.para()
    return_coin(world, child, owner, method)
    if outcome == "reunited":
        owner_uses_coin(world, owner, place)
    else:
        clerk_safe(world, child, place, method)

    world.para()
    close_story(world, child, caregiver, place, outcome)

    world.facts.update(
        outcome=outcome,
        reunited=(outcome == "reunited"),
        safe=(outcome in {"reunited", "clerk_safe"}),
        place=place.id,
        method=method.id,
        memory=memory.id,
    )
    return world


@dataclass
class StoryParams:
    place: str
    method: str
    memory: str
    child_name: str
    child_type: str
    caregiver_type: str
    owner_type: str
    delay: int = 0
    seed: Optional[int] = None


PLACES = {
    "laundromat": Place(
        id="laundromat",
        label="the laundromat",
        scene="Rows of round washer doors blinked under the bright lights.",
        ambient="Warm air smelled faintly of soap, and dryers thumped against the walls.",
        owner_phrase="the woman with a basket of towels",
        need="washer",
        urgency=1,
        has_clerk=True,
        clerk_label="attendant",
        clerk_type="cashier_woman",
        use_line="starting the washing machine",
        tags={"laundromat", "coin_machine"},
    ),
    "bus_stop": Place(
        id="bus_stop",
        label="the bus stop kiosk",
        scene="The glass shelter held a row of tired shoes and shopping bags.",
        ambient="A bus hissed at the curb, and the timetable fluttered in the breeze.",
        owner_phrase="the man with a paper bag of pears",
        need="fare",
        urgency=2,
        has_clerk=False,
        clerk_label="",
        clerk_type="",
        use_line="paying the bus fare",
        tags={"bus", "coin"},
    ),
    "bakery": Place(
        id="bakery",
        label="the corner bakery",
        scene="Trays of buns shone behind the case, with sugar catching the light.",
        ambient="The air smelled like warm bread, and tongs clicked now and then.",
        owner_phrase="the baker's customer in a blue coat",
        need="exact_change",
        urgency=1,
        has_clerk=True,
        clerk_label="cashier",
        clerk_type="cashier_woman",
        use_line="paying the last bit of exact change for a loaf",
        tags={"bakery", "bread"},
    ),
}

METHODS = {
    "call_out": Method(
        id="call_out",
        sense=3,
        reach=3,
        needs_clerk=False,
        text='"Excuse me," {child} said, opening a small hand. "Is this your coin?"',
        clerk_text="",
        qa_text="called out right away and held up the coin",
        tags={"return_found_money", "speak_up"},
    ),
    "ask_clerk": Method(
        id="ask_clerk",
        sense=2,
        reach=1,
        needs_clerk=True,
        text="",
        clerk_text='{child} brought the coin to the clerk and said, "Someone here needs this. '
                   'Can you hold it where they can find it?"',
        qa_text="gave the coin to the clerk to keep in the right place",
        tags={"return_found_money", "clerk"},
    ),
    "pin_note": Method(
        id="pin_note",
        sense=1,
        reach=0,
        needs_clerk=False,
        text="",
        clerk_text="",
        qa_text="left the coin in an indirect way",
        tags={"indirect"},
    ),
}

MEMORIES = {
    "grandma_apron": Memory(
        id="grandma_apron",
        elder_type="grandmother",
        elder_label="Grandma",
        setting="in Grandma's kitchen while steam curled up from noodle soup",
        advice="If a small thing is helping someone else hold their day together, be the kind hands that pass it back.",
        touch="tapped the table with a floury finger",
        tags={"honesty", "care"},
    ),
    "dad_steps": Memory(
        id="dad_steps",
        elder_type="father",
        elder_label="Dad",
        setting="by the apartment stairs after a grocery bag split open",
        advice="When a problem looks tiny, do not step around it. Help it move forward before it grows.",
        touch="set an apple back into the bag",
        tags={"honesty", "help"},
    ),
    "grandpa_bench": Memory(
        id="grandpa_bench",
        elder_type="grandfather",
        elder_label="Grandpa",
        setting="on a park bench where pigeons bobbed near their shoes",
        advice="You stay alive to other people's needs by noticing what would be easy to ignore.",
        touch="rested a warm hand on the bench between them",
        tags={"care", "notice"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ava", "Zoe"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Sam", "Noah", "Eli"]


def _random_child(rng: random.Random) -> tuple[str, str]:
    child_type = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    return rng.choice(pool), child_type


def _owner_type_for_place(place: str) -> str:
    return {
        "laundromat": "neighbor_woman",
        "bus_stop": "driver_man",
        "bakery": "neighbor_woman",
    }[place]


CURATED = [
    StoryParams(
        place="laundromat",
        method="call_out",
        memory="grandma_apron",
        child_name="Maya",
        child_type="girl",
        caregiver_type="mother",
        owner_type="neighbor_woman",
        delay=0,
    ),
    StoryParams(
        place="bakery",
        method="ask_clerk",
        memory="dad_steps",
        child_name="Theo",
        child_type="boy",
        caregiver_type="father",
        owner_type="neighbor_woman",
        delay=1,
    ),
    StoryParams(
        place="bus_stop",
        method="call_out",
        memory="grandpa_bench",
        child_name="Lina",
        child_type="girl",
        caregiver_type="grandmother",
        owner_type="driver_man",
        delay=0,
    ),
]


KNOWLEDGE = {
    "coin": [
        (
            "What is a coin?",
            "A coin is a small piece of metal money. People use coins to pay for small things like fares or snacks."
        )
    ],
    "laundromat": [
        (
            "What is a laundromat?",
            "A laundromat is a place with washing machines and dryers that people use to clean clothes."
        )
    ],
    "bus": [
        (
            "Why might someone need a coin at a bus stop?",
            "Sometimes a person needs exact money for a bus fare. One missing coin can keep them from getting on quickly."
        )
    ],
    "bakery": [
        (
            "What is a bakery?",
            "A bakery is a shop where bread, buns, and other baked food are made and sold warm and fresh."
        )
    ],
    "return_found_money": [
        (
            "What should you do if you find money on the floor?",
            "You should try to give it back to the person who lost it, or hand it to a trusted grown-up who can help. Keeping it is not the honest choice."
        )
    ],
    "clerk": [
        (
            "How can a clerk help with a lost item?",
            "A clerk can keep the item in the right place so the owner can ask for it. That helps a small problem get solved safely."
        )
    ],
    "honesty": [
        (
            "What does honesty mean?",
            "Honesty means doing the true and fair thing, even when it would be easy not to. It often means thinking about how your choice affects someone else."
        )
    ],
    "care": [
        (
            "What does it mean to notice another person's needs?",
            "It means paying attention to what they are feeling or missing. Small acts of care can make an ordinary day much easier."
        )
    ],
}
KNOWLEDGE_ORDER = ["coin", "laundromat", "bus", "bakery", "return_found_money", "clerk", "honesty", "care"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place_cfg"]
    child = world.facts["child"]
    memory = world.facts["memory_cfg"]
    outcome = world.facts["outcome"]
    closing = "returns the coin directly" if outcome == "reunited" else "tries to return the coin in a careful indirect way"
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "coin", "forward", and "alive". Include a brief flashback.',
        f"Tell a gentle everyday story where a {child.type} named {child.id} finds a coin at {place.label}, remembers {memory.elder_label}'s advice in a flashback, and {closing}.",
        f"Write a small, warm story about honesty during an ordinary errand, with a flashback turn and an ending where the place still feels alive."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    owner = world.facts["owner"]
    place = world.facts["place_cfg"]
    method = world.facts["method_cfg"]
    memory = world.facts["memory_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who found a coin during an errand with {child.pronoun('possessive')} {caregiver.label_word}. "
            f"The story also includes {owner.phrase}, who needed the coin for {place.use_line}."
        ),
        (
            f"Why did the coin matter to {owner.phrase}?",
            f"It mattered because {owner.pronoun()} needed it for {place.use_line}. "
            f"Without that small coin, a simple part of the afternoon could not move forward."
        ),
        (
            f"What did {child.id} remember in the flashback?",
            f"{child.id} remembered {memory.elder_label}'s advice from {memory.setting}. "
            f"The memory reminded {child.pronoun('object')} that small honest actions can help someone else's day."
        ),
    ]
    if outcome == "reunited":
        qa.append(
            (
                f"How did {child.id} help?",
                f"{child.id} {method.qa_text}. That worked because the owner was still close enough to hear and take the coin back right away."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the coin back in the right hands and the errand going on. "
                f"The ordinary place still felt warm and alive because one small choice helped."
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} still do the right thing even without finding the owner in time?",
                f"Yes. {child.id} {method.qa_text}, so the coin stayed safe in the place where the owner could ask for it. "
                f"The help was smaller than a direct reunion, but it was still honest and careful."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with the coin left safely for the missing person. "
                f"{child.id} could not fix everything at once, but still made the situation better."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place_cfg"]
    method = world.facts["method_cfg"]
    memory = world.facts["memory_cfg"]
    tags = {"coin"} | set(place.tags) | set(method.tags) | set(memory.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None)}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(P, M) :- place(P), method(M), sensible(M), not needs_clerk(M).
valid(P, M) :- place(P), method(M), sensible(M), needs_clerk(M), has_clerk(P).

reunited :- chosen_place(P), chosen_method(M), urgency(P, U), delay(D), reach(M, R), R >= U + D.
outcome(reunited) :- reunited.
outcome(clerk_safe) :- not reunited.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("urgency", place_id, place.urgency))
        if place.has_clerk:
            lines.append(asp.fact("has_clerk", place_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
        if method.needs_clerk:
            lines.append(asp.fact("needs_clerk", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    p_valid = set(valid_combos())
    a_valid = set(asp_valid_combos())
    if p_valid == a_valid:
        print(f"OK: gate matches valid_combos() ({len(p_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in clingo:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in python:", sorted(p_valid - a_valid))

    p_sens = {m.id for m in sensible_methods()}
    a_sens = set(asp_sensible())
    if p_sens == a_sens:
        print(f"OK: sensible methods match ({sorted(p_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(a_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a found coin, a flashback, and a small honest choice."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra moment before the child acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible place/method pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.method:
        if not valid_combo(PLACES[args.place], METHODS[args.method]):
            raise StoryError(explain_rejection(PLACES[args.place], METHODS[args.method]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        place_for_msg = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        raise StoryError(explain_rejection(place_for_msg, METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, method_id = rng.choice(sorted(combos))
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    child_name, child_type = (args.name, args.gender) if args.name and args.gender else _random_child(rng)
    if args.gender and not args.name:
        pool = GIRL_NAMES if args.gender == "girl" else BOY_NAMES
        child_name, child_type = rng.choice(pool), args.gender
    elif args.name and not args.gender:
        child_name = args.name
        child_type = rng.choice(["girl", "boy"])
    caregiver_type = args.caregiver or rng.choice(["mother", "father", "grandmother", "grandfather"])
    owner_type = _owner_type_for_place(place_id)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        place=place_id,
        method=method_id,
        memory=memory_id,
        child_name=child_name,
        child_type=child_type,
        caregiver_type=caregiver_type,
        owner_type=owner_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    if not valid_combo(PLACES[params.place], METHODS[params.method]):
        raise StoryError(explain_rejection(PLACES[params.place], METHODS[params.method]))

    world = tell(
        place=PLACES[params.place],
        method=METHODS[params.method],
        memory=MEMORIES[params.memory],
        child_name=params.child_name,
        child_type=params.child_type,
        caregiver_type=params.caregiver_type,
        owner_type=params.owner_type,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, method) pairs:\n")
        for place_id, method_id in combos:
            print(f"  {place_id:10} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place}, {p.method}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
