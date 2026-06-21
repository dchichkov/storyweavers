#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/intermediate_communicate_esquire_rhyme_suspense_nursery_rhyme.py
================================================================================================

A small nursery-rhyme-style story world about a little creature who must
communicate a warning to Badger Esquire before a waddling danger reaches the lane.

The world is intentionally narrow: a child sees that a gate has swung open and
some small animals are drifting toward trouble. The child chooses a way to send
the warning. Some methods can carry far enough by themselves; some need an
intermediate helper to relay the message. The result is either an early rescue
or a last-moment rescue, but only reasoned, plausible combinations are allowed.

Run it
------
python storyworlds/worlds/gpt-5.4/intermediate_communicate_esquire_rhyme_suspense_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/intermediate_communicate_esquire_rhyme_suspense_nursery_rhyme.py --place pumpkin_patch --method bell --helper robin
python storyworlds/worlds/gpt-5.4/intermediate_communicate_esquire_rhyme_suspense_nursery_rhyme.py --method hum
python storyworlds/worlds/gpt-5.4/intermediate_communicate_esquire_rhyme_suspense_nursery_rhyme.py --all
python storyworlds/worlds/gpt-5.4/intermediate_communicate_esquire_rhyme_suspense_nursery_rhyme.py --verify
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose"}
        male = {"boy", "father", "badger", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        if self.label:
            return self.label
        return self.id


@dataclass
class Place:
    id: str
    label: str
    distance: int
    relay_spot: str
    has_perch: bool
    opening_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    group: str
    count_word: str
    motion: str
    danger_place: str
    rescue_text: str
    ending_image: str
    hurry: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    action_text: str
    sound_text: str
    reach: int
    note_kind: bool = False
    can_relay: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    boost: int
    can_carry_note: bool
    needs_perch: bool
    relay_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_risk_grows(world: World) -> list[str]:
    risk_ent = world.get("risk")
    if risk_ent.meters["wandering"] < THRESHOLD:
        return []
    sig = ("risk_grows",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    hero.memes["worry"] += 1
    world.get("yard").meters["danger"] += 1
    return ["__danger__"]


def _r_delivery(world: World) -> list[str]:
    msg = world.get("message")
    if msg.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    badger = world.get("esquire")
    badger.memes["alert"] += 1
    return ["__delivery__"]


CAUSAL_RULES = [
    Rule(name="risk_grows", tag="physical", apply=_r_risk_grows),
    Rule(name="delivery", tag="social", apply=_r_delivery),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "rose_path": Place(
        id="rose_path",
        label="the rose path",
        distance=1,
        relay_spot="a mossy post",
        has_perch=True,
        opening_line="On the rose path, the dew lay bright and the beans stood in a row.",
        tags={"garden"},
    ),
    "pumpkin_patch": Place(
        id="pumpkin_patch",
        label="the pumpkin patch",
        distance=2,
        relay_spot="an intermediate stump between the vines",
        has_perch=True,
        opening_line="In the pumpkin patch, round leaves curled low while the moon peeped over the wall.",
        tags={"garden", "intermediate"},
    ),
    "orchard_gate": Place(
        id="orchard_gate",
        label="the orchard gate",
        distance=3,
        relay_spot="a flat watering stone by the pears",
        has_perch=False,
        opening_line="By the orchard gate, the grass was silver and the apple boughs gave little shakes.",
        tags={"orchard"},
    ),
}

RISKS = {
    "goslings": Risk(
        id="goslings",
        group="goslings",
        count_word="three",
        motion="wibbled through the open gate",
        danger_place="the moonlit lane",
        rescue_text="swept up the goslings and nudged the gate shut with his heel",
        ending_image="The three goslings tucked back under the hedge, all warm and all in a row.",
        hurry=1,
        tags={"animals", "gate"},
    ),
    "ducklings": Risk(
        id="ducklings",
        group="ducklings",
        count_word="four",
        motion="pitter-pattered toward the open gate",
        danger_place="the dark lane",
        rescue_text="herded the ducklings into his broad coat and latched the gate at once",
        ending_image="The ducklings settled by the watering can, each small beak tucked low.",
        hurry=2,
        tags={"animals", "gate"},
    ),
    "chicks": Risk(
        id="chicks",
        group="chicks",
        count_word="five",
        motion="tip-tapped toward the open gate",
        danger_place="the cart track",
        rescue_text="gathered the chicks into his hat and closed the gate with a click",
        ending_image="The chicks peeped safely in the straw, like soft yellow dots in a row.",
        hurry=2,
        tags={"animals", "gate"},
    ),
}

METHODS = {
    "hum": Method(
        id="hum",
        label="hum",
        phrase="a little hum",
        action_text="Pip tried a little hum",
        sound_text='"Hum-hum, hurry, come and see!"',
        reach=0,
        note_kind=False,
        can_relay=False,
        tags={"sound"},
    ),
    "rhyme_call": Method(
        id="rhyme_call",
        label="rhyme call",
        phrase="a rhyme call",
        action_text="Pip cupped small paws and sang a rhyme",
        sound_text='"Badger Esquire, do come quick-quick! The gate is loose with a click-click-click!"',
        reach=2,
        note_kind=False,
        can_relay=True,
        tags={"rhyme", "voice"},
    ),
    "bell": Method(
        id="bell",
        label="bell",
        phrase="the brass bell",
        action_text="Pip tugged the brass bell string",
        sound_text='Ding-ding! "Badger Esquire, pray come near!"',
        reach=2,
        note_kind=False,
        can_relay=False,
        tags={"bell", "sound"},
    ),
    "note": Method(
        id="note",
        label="note",
        phrase="a folded note",
        action_text="Pip scratched a tiny folded note",
        sound_text='"Please come quick. The gate is wide."',
        reach=1,
        note_kind=True,
        can_relay=True,
        tags={"note", "communicate"},
    ),
}

HELPERS = {
    "none": HelperCfg(
        id="none",
        label="no helper",
        phrase="no helper at all",
        boost=0,
        can_carry_note=False,
        needs_perch=False,
        relay_text="",
        tags=set(),
    ),
    "robin": HelperCfg(
        id="robin",
        label="Robin",
        phrase="Robin with the red round breast",
        boost=1,
        can_carry_note=True,
        needs_perch=True,
        relay_text="Robin hopped to the intermediate perch, then flashed on in a red little blur.",
        tags={"bird", "intermediate"},
    ),
    "squirrel": HelperCfg(
        id="squirrel",
        label="Squirrel",
        phrase="Squirrel with the whiskery tail",
        boost=1,
        can_carry_note=False,
        needs_perch=False,
        relay_text="Squirrel sprang over the roots and rattled the warning farther along.",
        tags={"helper"},
    ),
    "wren": HelperCfg(
        id="wren",
        label="Wren",
        phrase="Wren from the bean pole",
        boost=2,
        can_carry_note=True,
        needs_perch=True,
        relay_text="Wren landed at the intermediate perch and trilled the message clear as glass.",
        tags={"bird", "intermediate"},
    ),
}


def message_power(place: Place, method: Method, helper: HelperCfg) -> int:
    power = method.reach
    if helper.id != "none":
        power += helper.boost
    return power


def helper_allowed(place: Place, method: Method, helper: HelperCfg) -> bool:
    if helper.id == "none":
        return True
    if not method.can_relay:
        return False
    if helper.needs_perch and not place.has_perch:
        return False
    if method.note_kind and not helper.can_carry_note:
        return False
    return True


def valid_combo(place: Place, risk: Risk, method: Method, helper: HelperCfg) -> bool:
    if not helper_allowed(place, method, helper):
        return False
    return message_power(place, method, helper) >= place.distance


def outcome_for(place: Place, risk: Risk, method: Method, helper: HelperCfg) -> str:
    if not valid_combo(place, risk, method, helper):
        raise StoryError(explain_rejection(place, risk, method, helper))
    margin = message_power(place, method, helper) - (place.distance + risk.hurry)
    return "early" if margin >= 0 else "close_call"


def predict_delivery(world: World, place: Place, risk: Risk, method: Method, helper: HelperCfg) -> dict:
    sim = world.copy()
    sim.get("message").meters["delivered"] = 1.0 if valid_combo(place, risk, method, helper) else 0.0
    propagate(sim, narrate=False)
    return {
        "delivered": sim.get("message").meters["delivered"] >= THRESHOLD,
        "alert": sim.get("esquire").memes["alert"] >= THRESHOLD,
        "power": message_power(place, method, helper),
        "outcome": outcome_for(place, risk, method, helper) if valid_combo(place, risk, method, helper) else "none",
    }


def introduce(world: World, hero: Entity, place: Place, risk: Risk) -> None:
    world.say(place.opening_line)
    world.say(
        f"Pip the {hero.type} kept watch by the latch, all tidy and trim, "
        f"while {risk.count_word} {risk.group} peeped in a row."
    )
    world.say(
        "Everything seemed proper and mild, the sort of small evening a song might know."
    )


def trouble(world: World, hero: Entity, risk: Risk) -> None:
    risk_ent = world.get("risk")
    risk_ent.meters["wandering"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then puff went the wind, and the garden gate swung. "
        f"The {risk.group} {risk.motion} toward {risk.danger_place}."
    )
    world.say(
        f"Pip's whiskers gave a twitch. To communicate the danger, {hero.pronoun()} had to be quick."
    )


def consider(world: World, hero: Entity, place: Place, method: Method, helper: HelperCfg, risk: Risk) -> None:
    pred = predict_delivery(world, place, risk, method, helper)
    world.facts["predicted_power"] = pred["power"]
    world.facts["predicted_outcome"] = pred["outcome"]
    if helper.id != "none" and place.has_perch:
        world.say(
            f"Between Pip and Badger Esquire stood {place.relay_spot}, a halfway place for a helper to go."
        )
    elif helper.id != "none":
        world.say(
            f"Pip glanced between the trees, but there was no true perch or halfway post to help a message flow."
        )
    if method.note_kind:
        world.say(
            f"{hero.pronoun().capitalize()} thought of {method.phrase}, neat as a seed, if only quick wings would carry it on."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} thought of {method.phrase}, hoping the sound would run before the waddlers were gone."
        )


def send_message(world: World, hero: Entity, method: Method, helper: HelperCfg) -> None:
    msg = world.get("message")
    world.say(f"{method.action_text}. {method.sound_text}")
    if helper.id != "none":
        world.say(f"{helper.phrase} came to help. {helper.relay_text}")
    msg.meters["delivered"] = 1.0
    propagate(world, narrate=False)
    hero.memes["hope"] += 1


def rescue(world: World, risk: Risk, outcome: str) -> None:
    esquire = world.get("esquire")
    hero = world.get("hero")
    risk_ent = world.get("risk")
    risk_ent.meters["safe"] += 1
    hero.memes["relief"] += 1
    if outcome == "early":
        world.say(
            f"Badger Esquire heard at once and came with coat tails flapping low. "
            f"He {risk.rescue_text} before even one small foot reached the road."
        )
        world.say(
            "What had been a hush of worry became a patter of thanks, soft and slow."
        )
    else:
        world.say(
            f"For one bright breath it seemed too late. A little beak reached the edge, and the night felt wide below."
        )
        world.say(
            f"Then Badger Esquire rushed in with a lantern bounce and {risk.rescue_text} at the very last blink."
        )
    esquire.memes["care"] += 1


def comfort(world: World, hero: Entity, method: Method, helper: HelperCfg, outcome: str) -> None:
    esquire = world.get("esquire")
    hero.memes["pride"] += 1
    world.say(
        f'Badger Esquire bowed to Pip and said, "Well done, small one. You knew how to communicate, and you did not freeze."'
    )
    if helper.id != "none":
        world.say(
            f'He thanked {helper.label} too, and called the helper "a clever intermediate friend."'
        )
    if outcome == "early":
        world.say(
            f"Pip felt the fright melt down to a glow. Even the {method.label} seemed to ring with cheer."
        )
    else:
        world.say(
            "Pip still trembled a little, but now it was the tremble that comes after danger goes."
        )


def ending(world: World, risk: Risk) -> None:
    world.say(risk.ending_image)
    world.say("So hush went the lane, and click went the gate, and the garden kept its sleepy glow.")


def tell(
    place: Place,
    risk: Risk,
    method: Method,
    helper: HelperCfg,
    hero_name: str = "Pip",
    hero_type: str = "mouse",
    friend_name: str = "Tansy",
    friend_type: str = "mouse",
) -> World:
    world = World(place=place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    esquire = world.add(Entity(id="esquire", kind="character", type="badger", label="Badger Esquire", role="adult"))
    yard = world.add(Entity(id="yard", kind="thing", type="yard", label=place.label))
    risk_ent = world.add(Entity(id="risk", kind="thing", type="animals", label=risk.group))
    world.add(Entity(id="message", kind="thing", type="message", label=method.label))

    introduce(world, hero, place, risk)
    world.para()
    trouble(world, hero, risk)
    consider(world, hero, place, method, helper, risk)
    world.say(f'{friend.label} squeaked, "Be quick, Pip, be quick!"')

    world.para()
    send_message(world, hero, method, helper)
    outcome = outcome_for(place, risk, method, helper)
    rescue(world, risk, outcome)

    world.para()
    comfort(world, hero, method, helper, outcome)
    ending(world, risk)

    world.facts.update(
        hero=hero,
        friend=friend,
        esquire=esquire,
        place=place,
        risk_cfg=risk,
        risk=risk_ent,
        method=method,
        helper=helper,
        outcome=outcome,
        delivered=world.get("message").meters["delivered"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    risk: str
    method: str
    helper: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="rose_path",
        risk="goslings",
        method="rhyme_call",
        helper="none",
        hero_name="Pip",
        hero_type="mouse",
        friend_name="Tansy",
        friend_type="mouse",
    ),
    StoryParams(
        place="pumpkin_patch",
        risk="ducklings",
        method="note",
        helper="wren",
        hero_name="Mim",
        hero_type="mouse",
        friend_name="Poppy",
        friend_type="vole",
    ),
    StoryParams(
        place="pumpkin_patch",
        risk="chicks",
        method="rhyme_call",
        helper="robin",
        hero_name="Nip",
        hero_type="mouse",
        friend_name="Bramble",
        friend_type="mouse",
    ),
    StoryParams(
        place="orchard_gate",
        risk="ducklings",
        method="note",
        helper="none",
        hero_name="Dot",
        hero_type="mouse",
        friend_name="Moss",
        friend_type="vole",
    ),
]

NAMES = ["Pip", "Mim", "Dot", "Nip", "Tib", "Pru"]
TYPES = ["mouse", "vole"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for risk_id, risk in RISKS.items():
            for method_id, method in METHODS.items():
                for helper_id, helper in HELPERS.items():
                    if valid_combo(place, risk, method, helper):
                        combos.append((place_id, risk_id, method_id, helper_id))
    return sorted(combos)


def explain_rejection(place: Place, risk: Risk, method: Method, helper: HelperCfg) -> str:
    if helper.id != "none" and not method.can_relay:
        return (
            f"(No story: {method.label} cannot be relayed by a helper, so the warning "
            f"would never travel from {place.label} to Badger Esquire.)"
        )
    if helper.id != "none" and helper.needs_perch and not place.has_perch:
        return (
            f"(No story: {helper.label} needs a halfway perch, but {place.label} has "
            f"no usable intermediate stop for the message.)"
        )
    if method.note_kind and helper.id != "none" and not helper.can_carry_note:
        return (
            f"(No story: {helper.label} cannot carry {method.phrase}, so Pip cannot "
            f"communicate the warning that way.)"
        )
    power = message_power(place, method, helper)
    return (
        f"(No story: the warning power is only {power}, but Badger Esquire is {place.distance} "
        f"steps away across {place.label}. The message would not reach him in time even before "
        f"the {risk.group} drifted toward danger.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    risk = f["risk_cfg"]
    method = f["method"]
    helper = f["helper"]
    outcome = f["outcome"]
    helper_part = (
        f" using {helper.label} as an intermediate helper"
        if helper.id != "none"
        else ""
    )
    ending = "with a fast rescue" if outcome == "early" else "with a last-second rescue"
    return [
        'Write a short Nursery Rhyme style story with suspense that includes the words "intermediate", "communicate", and "esquire".',
        f"Tell a rhyming story where {hero.label} must communicate a warning to Badger Esquire from {place.label}{helper_part}.",
        f"Write a child-facing suspense story about {risk.group} wandering toward danger and a {method.label} carrying the warning, ending {ending}.",
    ]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == friend.type:
        return f"two little {hero.type}s"
    return "two little friends"


KNOWLEDGE = {
    "bell": [(
        "What does a bell do?",
        "A bell makes a clear ringing sound that can carry across a yard or a path. People use bells to call attention."
    )],
    "note": [(
        "What is a note?",
        "A note is a short written message. You can use it to communicate something important quickly."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words sound alike at the end, like row and glow. Rhymes make stories and songs easy to remember."
    )],
    "suspense": [(
        "What is suspense in a story?",
        "Suspense is the feeling that something important might happen very soon. It makes you wonder what will happen next."
    )],
    "intermediate": [(
        "What does intermediate mean?",
        "Intermediate means in the middle or halfway between two places or steps. An intermediate stop can help something travel farther."
    )],
    "communicate": [(
        "What does communicate mean?",
        "Communicate means to send or share a message. You can communicate by speaking, ringing, writing, or signaling."
    )],
    "esquire": [(
        "Why is someone called Esquire in a story?",
        "Esquire can be a polite title for a grown-up or a person treated with respect. In a story, it can make the character sound formal and kind."
    )],
    "helper": [(
        "Why can a helper make a message stronger?",
        "A helper can carry or repeat the message farther along. That way, the warning reaches someone who is too far away to hear it at first."
    )],
    "gate": [(
        "Why can an open gate be a problem for small animals?",
        "An open gate can lead them out of a safe yard and toward a road or another risky place. Small animals may not know where it is safe to stop."
    )],
}
KNOWLEDGE_ORDER = ["intermediate", "communicate", "esquire", "rhyme", "suspense", "bell", "note", "helper", "gate"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    risk = f["risk_cfg"]
    method = f["method"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)}, especially {hero.label}, and about Badger Esquire who comes to help."
        ),
        (
            "What went wrong in the garden?",
            f"The wind pushed the gate open, and the {risk.group} started moving toward {risk.danger_place}. That is why the story suddenly feels urgent and full of suspense."
        ),
        (
            f"Why did {hero.label} need to communicate quickly?",
            f"{hero.label} saw the {risk.group} drifting toward danger and knew Badger Esquire was not close enough to see it. The warning had to travel fast before the small animals reached the open way."
        ),
    ]
    if helper.id != "none":
        qa.append((
            f"How did {helper.label} help?",
            f"{helper.label} acted as an intermediate helper and carried or relayed the warning farther along. That extra step gave the message enough reach to find Badger Esquire."
        ))
    else:
        qa.append((
            f"Did {hero.label} have a helper?",
            f"No. {hero.label} had to send the warning alone with {method.phrase}. That made the moment feel brave and a little tense."
        ))
    if outcome == "early":
        qa.append((
            "Did Badger Esquire arrive in time?",
            f"Yes. He heard the warning early and rescued the {risk.group} before they reached {risk.danger_place}. The quick message changed the ending from danger to calm."
        ))
    else:
        qa.append((
            "How did the rescue happen?",
            f"It was a close call. The {risk.group} came right to the edge of trouble before Badger Esquire rushed in and saved them at the last blink."
        ))
    qa.append((
        f"What message method did {hero.label} use?",
        f"{hero.label} used {method.phrase}. That method fit the moment because it could carry the warning across {place.label}."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"communicate", "esquire", "suspense", "gate"}
    method = f["method"]
    helper = f["helper"]
    if method.id == "bell":
        tags.add("bell")
    if method.id == "note":
        tags.add("note")
    if method.id == "rhyme_call":
        tags.add("rhyme")
    if helper.id != "none":
        tags.add("helper")
        if helper.needs_perch or "intermediate" in helper.tags or "intermediate" in f["place"].tags:
            tags.add("intermediate")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
allowed_helper(P, M, H) :- helper(H), method(M), place(P), H = none.
allowed_helper(P, M, H) :- helper(H), method(M), place(P), H != none,
                           can_relay(M), not needs_perch(H).
allowed_helper(P, M, H) :- helper(H), method(M), place(P), H != none,
                           can_relay(M), needs_perch(H), has_perch(P).
:- chosen_method(M), chosen_helper(H), note_kind(M), not can_carry_note(H), H != none.

power(P, M, H, R + B) :- place_distance(P, _), method_reach(M, R), helper_boost(H, B),
                         allowed_helper(P, M, H).

valid(P, Rk, M, H) :- place(P), risk(Rk), method(M), helper(H),
                      allowed_helper(P, M, H),
                      power(P, M, H, Pw), place_distance(P, D), Pw >= D.

outcome(early) :- chosen_place(P), chosen_risk(Rk), chosen_method(M), chosen_helper(H),
                  valid(P, Rk, M, H),
                  power(P, M, H, Pw), place_distance(P, D), hurry(Rk, Hr),
                  Pw >= D + Hr.
outcome(close_call) :- chosen_place(P), chosen_risk(Rk), chosen_method(M), chosen_helper(H),
                       valid(P, Rk, M, H),
                       power(P, M, H, Pw), place_distance(P, D), hurry(Rk, Hr),
                       Pw < D + Hr.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_distance", pid, place.distance))
        if place.has_perch:
            lines.append(asp.fact("has_perch", pid))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("hurry", rid, risk.hurry))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_reach", mid, method.reach))
        if method.note_kind:
            lines.append(asp.fact("note_kind", mid))
        if method.can_relay:
            lines.append(asp.fact("can_relay", mid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_boost", hid, helper.boost))
        if helper.needs_perch:
            lines.append(asp.fact("needs_perch", hid))
        if helper.can_carry_note:
            lines.append(asp.fact("can_carry_note", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_risk", params.risk),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        py_out = outcome_for(
            PLACES[params.place],
            RISKS[params.risk],
            METHODS[params.method],
            HELPERS[params.helper],
        )
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme suspense story world: a child must communicate a warning to Badger Esquire."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.risk and args.method and args.helper:
        place = PLACES[args.place]
        risk = RISKS[args.risk]
        method = METHODS[args.method]
        helper = HELPERS[args.helper]
        if not valid_combo(place, risk, method, helper):
            raise StoryError(explain_rejection(place, risk, method, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.risk is None or combo[1] == args.risk)
        and (args.method is None or combo[2] == args.method)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, risk_id, method_id, helper_id = rng.choice(combos)
    hero_name = rng.choice(NAMES)
    hero_type = rng.choice(TYPES)
    friend_pool = [n for n in NAMES if n != hero_name]
    friend_name = rng.choice(friend_pool)
    friend_type = rng.choice(TYPES)
    return StoryParams(
        place=place_id,
        risk=risk_id,
        method=method_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        risk = RISKS[params.risk]
        method = METHODS[params.method]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_combo(place, risk, method, helper):
        raise StoryError(explain_rejection(place, risk, method, helper))

    world = tell(
        place=place,
        risk=risk,
        method=method,
        helper=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, risk, method, helper) combos:\n")
        for place, risk, method, helper in combos:
            outcome = asp_outcome(
                StoryParams(
                    place=place,
                    risk=risk,
                    method=method,
                    helper=helper,
                    hero_name="Pip",
                    hero_type="mouse",
                    friend_name="Mim",
                    friend_type="vole",
                )
            )
            print(f"  {place:13} {risk:10} {method:10} {helper:8} [{outcome}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            out = outcome_for(PLACES[p.place], RISKS[p.risk], METHODS[p.method], HELPERS[p.helper])
            header = f"### {p.hero_name}: {p.method} at {p.place} with {p.helper} ({out})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
