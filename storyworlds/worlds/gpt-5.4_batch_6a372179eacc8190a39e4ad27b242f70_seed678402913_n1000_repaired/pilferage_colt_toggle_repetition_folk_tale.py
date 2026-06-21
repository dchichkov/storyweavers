#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py
=========================================================================

A small folk-tale storyworld about a child, a restless colt, and a sly creature
that keeps stealing a toggle from the colt's gate. The world uses repetition:
the same trouble comes three times, each visit changing the child's knowledge
and the plan, until the third turn resolves the danger.

Seed words carried into the domain:
- pilferage
- colt
- toggle

Run it
------
python storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py
python storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py --place orchard --thief magpie --fix bell_thread
python storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py --toggle iron_pin   # rejected
python storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/pilferage_colt_toggle_repetition_folk_tale.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    can_carry_small: bool = False
    notices_sound: bool = False
    gate_part: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "granny"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type not in female | male:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "granny": "granny", "grandfather": "grandfather"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    village_name: str
    yard_phrase: str
    path_phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ThiefCfg:
    id: str
    label: str
    phrase: str
    motion: str
    lure: str
    hiding_place: str
    can_carry_small: bool = True
    likes_shiny: bool = False
    likes_wood: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ToggleCfg:
    id: str
    label: str
    phrase: str
    material: str
    easy_to_pilfer: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    sense: int
    works_for: set[str]
    text: str
    discovery: str
    ending: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict] = []
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.history = copy.deepcopy(self.history)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_open_gate(world: World) -> list[str]:
    toggle = world.get("toggle")
    gate = world.get("gate")
    colt = world.get("colt")
    out: list[str] = []
    if toggle.meters["missing"] >= THRESHOLD and gate.meters["open"] < THRESHOLD:
        sig = ("open_gate",)
        if sig not in world.fired:
            world.fired.add(sig)
            gate.meters["open"] += 1
            colt.meters["risk"] += 1
            colt.memes["restless"] += 1
            out.append("__gate_open__")
    return out


def _r_colt_wander(world: World) -> list[str]:
    gate = world.get("gate")
    colt = world.get("colt")
    out: list[str] = []
    if gate.meters["open"] >= THRESHOLD and colt.meters["wandering"] < THRESHOLD:
        sig = ("colt_wander", len(world.history))
        if sig not in world.fired:
            world.fired.add(sig)
            colt.meters["wandering"] += 1
            out.append("__colt_wander__")
    return out


def _r_child_worry(world: World) -> list[str]:
    colt = world.get("colt")
    child = world.get("child")
    if colt.meters["risk"] >= THRESHOLD and child.memes["worry"] < colt.meters["risk"]:
        child.memes["worry"] = colt.meters["risk"]
        return ["__worry__"]
    return []


CAUSAL_RULES = [
    Rule(name="open_gate", tag="physical", apply=_r_open_gate),
    Rule(name="colt_wander", tag="physical", apply=_r_colt_wander),
    Rule(name="child_worry", tag="emotional", apply=_r_child_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


PLACES = {
    "orchard": Place(
        id="orchard",
        village_name="Pear-Tree Hollow",
        yard_phrase="a low foal-pen beside the orchard wall",
        path_phrase="the path between the well and the pear trees",
        ending_image="the orchard leaves whispered over the quiet pen",
        tags={"village", "orchard"},
    ),
    "mill": Place(
        id="mill",
        village_name="Miller's Ford",
        yard_phrase="a foal-pen near the old mill pond",
        path_phrase="the path by the turning wheel",
        ending_image="the mill wheel hummed while the pen stood still",
        tags={"village", "mill"},
    ),
    "meadow": Place(
        id="meadow",
        village_name="Red Clover End",
        yard_phrase="a foal-pen at the edge of the meadow",
        path_phrase="the lane between the hedge and the grazing ground",
        ending_image="the meadow grass bent softly around the safe pen",
        tags={"village", "meadow"},
    ),
}

THIEVES = {
    "magpie": ThiefCfg(
        id="magpie",
        label="magpie",
        phrase="a black-and-white magpie with a needle-bright eye",
        motion="down from the branch with a skip and a peck",
        lure="shiny things",
        hiding_place="its nest in the high elm",
        can_carry_small=True,
        likes_shiny=True,
        tags={"bird", "pilferage", "magpie"},
    ),
    "monkey": ThiefCfg(
        id="monkey",
        label="monkey",
        phrase="a little monkey from the tinker fair",
        motion="over the fence with nimble fingers and a whisk of a tail",
        lure="anything small enough to snatch",
        hiding_place="the abandoned cart behind the shed",
        can_carry_small=True,
        likes_shiny=True,
        likes_wood=True,
        tags={"animal", "pilferage", "monkey"},
    ),
    "jackdaw": ThiefCfg(
        id="jackdaw",
        label="jackdaw",
        phrase="a gray-naped jackdaw with a clever head",
        motion="out of the sky in a neat black dip",
        lure="small gleaming scraps",
        hiding_place="a cracked chimney nook",
        can_carry_small=True,
        likes_shiny=True,
        tags={"bird", "pilferage", "jackdaw"},
    ),
}

TOGGLES = {
    "wooden_pin": ToggleCfg(
        id="wooden_pin",
        label="toggle",
        phrase="a smooth wooden toggle",
        material="wood",
        easy_to_pilfer=True,
        tags={"toggle", "wood"},
    ),
    "brass_pin": ToggleCfg(
        id="brass_pin",
        label="toggle",
        phrase="a little brass toggle",
        material="brass",
        easy_to_pilfer=True,
        tags={"toggle", "brass", "shiny"},
    ),
    "iron_pin": ToggleCfg(
        id="iron_pin",
        label="toggle",
        phrase="a thick iron toggle",
        material="iron",
        easy_to_pilfer=False,
        tags={"toggle", "iron"},
    ),
}

FIXES = {
    "bell_thread": FixCfg(
        id="bell_thread",
        label="bell and red thread",
        sense=3,
        works_for={"magpie", "jackdaw", "monkey"},
        text="looped a red thread through the toggle and tied it to a small bell above the latch",
        discovery="When the thief tugged, the bell rang clear as a spoon on a bowl",
        ending="After that, no thief could touch the latch without waking the yard",
        qa_text="hung a bell on the toggle with a red thread so the yard would hear any tug",
        tags={"bell", "thread", "sound"},
    ),
    "berry_paste": FixCfg(
        id="berry_paste",
        label="berry paste and flour",
        sense=2,
        works_for={"magpie", "jackdaw"},
        text="rubbed berry paste on the toggle and dusted it with flour",
        discovery="When the thief snatched it, bright berry stains and white flour marked the little culprit",
        ending="After being seen so plainly, the thief never dared a fourth try",
        qa_text="dabbed the toggle with berry paste and flour, so the thief would be marked and caught",
        tags={"berries", "flour", "trap"},
    ),
    "basket_cover": FixCfg(
        id="basket_cover",
        label="basket cover",
        sense=2,
        works_for={"monkey"},
        text="set a willow basket over the latch and fastened it with a cord too stiff for quick little fingers",
        discovery="The thief scrabbled at the basket and could not get at the toggle at all",
        ending="After that, the latch sat hidden like a seed in a shell",
        qa_text="covered the latch with a willow basket so the thief could not reach the toggle",
        tags={"basket", "cover"},
    ),
    "candle_watch": FixCfg(
        id="candle_watch",
        label="candle watch",
        sense=1,
        works_for={"magpie", "jackdaw", "monkey"},
        text="set a candle by the pen and hoped to stay awake",
        discovery="The candle guttered low, and a thief could still come in the dark",
        ending="It was a poor answer, more sleepy than wise",
        qa_text="left a candle by the pen and tried to watch",
        tags={"candle"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Tessa", "Lina", "Elsa", "Pia"]
BOY_NAMES = ["Ivo", "Marten", "Ned", "Tobin", "Jory", "Silas"]
COLT_NAMES = ["Bramble", "Thistle", "Hazel", "Pebble", "Clover", "Moss"]


@dataclass
class StoryParams:
    place: str
    thief: str
    toggle: str
    fix: str
    child_name: str
    child_gender: str
    elder_type: str
    colt_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="orchard",
        thief="magpie",
        toggle="brass_pin",
        fix="bell_thread",
        child_name="Anya",
        child_gender="girl",
        elder_type="granny",
        colt_name="Bramble",
        seed=1,
    ),
    StoryParams(
        place="mill",
        thief="monkey",
        toggle="wooden_pin",
        fix="basket_cover",
        child_name="Tobin",
        child_gender="boy",
        elder_type="grandfather",
        colt_name="Pebble",
        seed=2,
    ),
    StoryParams(
        place="meadow",
        thief="jackdaw",
        toggle="brass_pin",
        fix="berry_paste",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandfather",
        colt_name="Clover",
        seed=3,
    ),
]


def hazard_possible(thief: ThiefCfg, toggle: ToggleCfg) -> bool:
    return thief.can_carry_small and toggle.easy_to_pilfer


def sensible_fixes() -> list[FixCfg]:
    return [cfg for cfg in FIXES.values() if cfg.sense >= SENSE_MIN]


def fix_works(thief_id: str, fix_id: str) -> bool:
    cfg = FIXES[fix_id]
    return cfg.sense >= SENSE_MIN and thief_id in cfg.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for thief_id, thief in THIEVES.items():
            for toggle_id, toggle in TOGGLES.items():
                if not hazard_possible(thief, toggle):
                    continue
                for fix_id in FIXES:
                    if fix_works(thief_id, fix_id):
                        combos.append((place_id, thief_id, toggle_id, fix_id))
    return combos


def explain_toggle_rejection(thief: ThiefCfg, toggle: ToggleCfg) -> str:
    if not toggle.easy_to_pilfer:
        return (
            f"(No story: {toggle.phrase} is too heavy or stubborn for a sneaking {thief.label} "
            f"to carry off, so there is no believable pilferage and no repeating trouble.)"
        )
    return "(No story: this thief cannot plausibly steal that toggle.)"


def explain_fix_rejection(fix_id: str, thief_id: str) -> str:
    cfg = FIXES[fix_id]
    if cfg.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix_id}': it scores too low on common sense "
            f"(sense={cfg.sense} < {SENSE_MIN}). Try one of: "
            f"{', '.join(sorted(f.id for f in sensible_fixes()))}.)"
        )
    return f"(No story: {cfg.label} is not a good answer for a {THIEVES[thief_id].label}.)"


def predict_theft(world: World) -> dict:
    sim = world.copy()
    toggle = sim.get("toggle")
    toggle.meters["missing"] += 1
    propagate(sim, narrate=False)
    colt = sim.get("colt")
    gate = sim.get("gate")
    return {
        "gate_open": gate.meters["open"] >= THRESHOLD,
        "colt_risk": colt.meters["risk"],
        "colt_wandering": colt.meters["wandering"] >= THRESHOLD,
    }


def setup_story(world: World, place: Place, child: Entity, elder: Entity, colt: Entity, toggle: ToggleCfg, thief: ThiefCfg) -> None:
    world.say(
        f"In {place.village_name}, where folk listened to wind and hoofbeat as if both could speak, "
        f"there lived {child.id} with {child.pronoun('possessive')} {elder.label_word}."
    )
    world.say(
        f"Behind their cottage stood {place.yard_phrase}, and in it frisked {colt.id}, "
        f"a young colt with knees too springy for stillness."
    )
    world.say(
        f"The gate of the little pen was fastened by {toggle.phrase}. It was only a small thing, "
        f"yet it held the whole gate quiet."
    )
    world.say(
        f"Now near that yard there watched {thief.phrase}, a creature fond of {thief.lure}. "
        f"Old people in the village muttered that small troubles often begin with small hands."
    )


def first_warning(world: World, child: Entity, elder: Entity, thief: ThiefCfg, place: Place) -> None:
    pred = predict_theft(world)
    world.facts["predicted_gate_open"] = pred["gate_open"]
    world.facts["predicted_colt_risk"] = pred["colt_risk"]
    world.say(
        f'One dawn {child.id} found the latch loose and ran to {child.pronoun("possessive")} {elder.label_word}. '
        f'"This is no wind-work," {child.pronoun()} said. "{elder.label_word.capitalize()}, someone is after the toggle."'
    )
    world.say(
        f'{elder.label_word.capitalize()} bent over the gate and answered, "A gate is a small promise. '
        f'When the promise slips, the colt will wander to {place.path_phrase}."'
    )


def steal_once(world: World, round_no: int, child: Entity, elder: Entity, colt: Entity, thief: ThiefCfg, toggle: ToggleCfg, place: Place) -> None:
    gate = world.get("gate")
    toggle_ent = world.get("toggle")
    colt_ent = world.get("colt")
    toggle_ent.meters["missing"] = 1.0
    gate.meters["open"] = 0.0
    colt_ent.meters["wandering"] = 0.0
    colt_ent.meters["risk"] = 0.0
    propagate(world, narrate=False)
    colt_ent.memes["fear"] += 1
    child.memes["care"] += 1
    record = {
        "round": round_no,
        "toggle_missing": True,
        "gate_open": gate.meters["open"] >= THRESHOLD,
        "colt_wandering": colt_ent.meters["wandering"] >= THRESHOLD,
    }
    world.history.append(record)
    first = {1: "On the first morning", 2: "On the second morning", 3: "On the third morning"}[round_no]
    world.say(
        f"{first}, before the porridge pot had finished singing, the {thief.label} came {thief.motion}, "
        f"nipped at the fastening, and away went the little {toggle.material} toggle."
    )
    if gate.meters["open"] >= THRESHOLD:
        world.say(
            f"At once the gate sagged open. Out stepped {colt.id}, light as spilled milk, nosing toward {place.path_phrase}."
        )
    if round_no < 3:
        world.say(
            f"{child.id} hurried after the colt and led {colt.pronoun('object')} back with both hands on the warm halter. "
            f"{elder.label_word.capitalize()} set the gate right again before worse could happen."
        )
    else:
        world.say(
            f"{child.id} saw it happen with {child.pronoun('possessive')} own eyes and knew the trouble had a name at last: pilferage."
        )


def repeated_repair(world: World, round_no: int, child: Entity, elder: Entity, toggle: ToggleCfg) -> None:
    gate = world.get("gate")
    toggle_ent = world.get("toggle")
    toggle_ent.meters["missing"] = 0.0
    gate.meters["open"] = 0.0
    if round_no == 1:
        world.say(
            f'So {elder.label_word.capitalize()} carved another {toggle.label} from a twig and said, '
            f'"A lost peg may be found, and a stolen peg may be replaced."'
        )
    elif round_no == 2:
        world.say(
            f'Again they set a fresh {toggle.label} in the latch, and again {elder.label_word.capitalize()} said, '
            f'"A lost peg may be found, and a stolen peg may be replaced."'
        )
        world.say(
            f"But this time {child.id} answered, \"Yes, but if the thief comes a third time, we must learn more than how to carve.\""
        )


def plan_fix(world: World, child: Entity, elder: Entity, thief: ThiefCfg, fix: FixCfg) -> None:
    child.memes["cleverness"] += 1
    elder.memes["trust"] += 1
    world.say(
        f"Then {child.id} watched the yard, the latch, and the shadow of the thief's path, and a thought came bright and plain."
    )
    world.say(
        f'{child.pronoun().capitalize()} told {elder.label_word.capitalize()} the plan, and {elder.label_word} nodded. '
        f'Together they {fix.text}.'
    )
    world.say(
        f'"Let the thief teach us its own trick," said {elder.label_word}. "Small pilferage likes to think itself unseen."'
    )


def catch_thief(world: World, child: Entity, elder: Entity, colt: Entity, thief: ThiefCfg, fix: FixCfg) -> None:
    child.memes["relief"] += 1
    colt.memes["calm"] += 1
    world.say(fix.discovery)
    if fix.id == "basket_cover":
        world.say(
            f"{thief.phrase.capitalize()} chattered with vexation and fled back to {thief.hiding_place} with empty paws."
        )
    elif fix.id == "berry_paste":
        world.say(
            f"{child.id} followed the bright little marks to {thief.hiding_place}, where the thief sat looking guilty and purple-snouted."
        )
    else:
        world.say(
            f"{child.id} followed the sudden ringing and saw the thief plain as noon, startled beside the pen."
        )
    world.say(
        f"{child.id} took back the stolen toggle, fastened the gate, and stroked the colt's neck until the trembling left {colt.pronoun('object')}."
    )
    world.say(
        f"{fix.ending}. After that, {colt.id} slept behind a shut gate and woke to nibble clover instead of chasing danger."
    )


def closing_image(world: World, place: Place, child: Entity, elder: Entity, colt: Entity) -> None:
    world.say(
        f"That evening {child.id} sat beside {elder.label_word.capitalize()}, and {place.ending_image}. "
        f"{colt.id} blew a soft breath through the rails, and even the smallest latch looked worthy of care."
    )


def tell(place: Place, thief_cfg: ThiefCfg, toggle_cfg: ToggleCfg, fix_cfg: FixCfg, child_name: str, child_gender: str, elder_type: str, colt_name: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["patient", "watchful"],
        notices_sound=True,
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        role="elder",
        traits=["wise"],
        notices_sound=True,
    ))
    colt = world.add(Entity(
        id=colt_name,
        kind="thing",
        type="colt",
        label=colt_name,
        phrase=f"{colt_name}, the colt",
        role="colt",
        movable=True,
    ))
    gate = world.add(Entity(
        id="gate",
        kind="thing",
        type="gate",
        label="gate",
        phrase="the foal-pen gate",
        role="gate",
    ))
    toggle = world.add(Entity(
        id="toggle",
        kind="thing",
        type="toggle",
        label="toggle",
        phrase=toggle_cfg.phrase,
        role="toggle",
        gate_part=True,
        movable=True,
        tags=set(toggle_cfg.tags),
    ))
    thief = world.add(Entity(
        id="thief",
        kind="thing",
        type=thief_cfg.id,
        label=thief_cfg.label,
        phrase=thief_cfg.phrase,
        role="thief",
        can_carry_small=thief_cfg.can_carry_small,
        movable=True,
        tags=set(thief_cfg.tags),
    ))

    setup_story(world, place, child, elder, colt, toggle_cfg, thief_cfg)
    world.para()
    first_warning(world, child, elder, thief_cfg, place)

    for round_no in (1, 2):
        world.para()
        steal_once(world, round_no, child, elder, colt, thief_cfg, toggle_cfg, place)
        repeated_repair(world, round_no, child, elder, toggle_cfg)

    world.para()
    plan_fix(world, child, elder, thief_cfg, fix_cfg)

    world.para()
    steal_once(world, 3, child, elder, colt, thief_cfg, toggle_cfg, place)
    catch_thief(world, child, elder, colt, thief_cfg, fix_cfg)

    world.para()
    closing_image(world, place, child, elder, colt)

    world.facts.update(
        place=place,
        thief_cfg=thief_cfg,
        toggle_cfg=toggle_cfg,
        fix_cfg=fix_cfg,
        child=child,
        elder=elder,
        colt=colt,
        rounds=len(world.history),
        repeated_thefts=sum(1 for h in world.history if h["toggle_missing"]),
        gate_openings=sum(1 for h in world.history if h["gate_open"]),
        wanderings=sum(1 for h in world.history if h["colt_wandering"]),
        resolution="caught",
    )
    return world


KNOWLEDGE = {
    "pilferage": [
        (
            "What does pilferage mean?",
            "Pilferage means stealing little things a bit at a time. It is still stealing, even when the object is small."
        )
    ],
    "colt": [
        (
            "What is a colt?",
            "A colt is a young horse. Young horses are lively, so they can get into danger if a gate comes open."
        )
    ],
    "toggle": [
        (
            "What is a toggle?",
            "A toggle is a small peg or pin used to fasten something shut. Tiny parts can matter a lot when they hold a gate closed."
        )
    ],
    "bell": [
        (
            "Why can a bell help guard something?",
            "A bell makes a sound when someone touches or moves it. That sound warns people quickly, even if they are not looking."
        )
    ],
    "basket": [
        (
            "How can a cover protect a latch?",
            "A cover hides the part a thief wants and makes it harder to grab. If the thief cannot reach the latch, the gate stays shut."
        )
    ],
    "berries": [
        (
            "Why would berry juice and flour help catch a sneaky thief?",
            "Sticky color and white flour can leave marks on fur or feathers. Those marks show where the thief has been."
        )
    ],
    "folk": [
        (
            "Why do folk tales repeat things three times?",
            "Repetition helps listeners remember the pattern and feel the trouble growing. The third time often brings the turning point."
        )
    ],
}
KNOWLEDGE_ORDER = ["pilferage", "colt", "toggle", "bell", "basket", "berries", "folk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    thief = f["thief_cfg"]
    fix = f["fix_cfg"]
    colt = f["colt"]
    return [
        (
            f'Write a folk tale for a young child that includes the words "pilferage", '
            f'"colt", and "toggle", and uses a three-time repetition pattern.'
        ),
        (
            f"Tell a village tale in which {child.id} discovers that a {thief.label} keeps stealing "
            f"the gate toggle from a colt's pen, and the third visit reveals the answer."
        ),
        (
            f"Write a simple repetitive folk tale where a small theft happens again and again, "
            f"until a child uses {fix.label} to keep {colt.id} safe."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    colt = f["colt"]
    thief = f["thief_cfg"]
    toggle = f["toggle_cfg"]
    fix = f["fix_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and {colt.id} the colt. "
            f"It is also about a sly {thief.label} that kept after the gate."
        ),
        (
            "Why did the missing toggle matter so much?",
            f"The {toggle.label} was a small fastening, but it held the gate shut. "
            f"When it was gone, the gate opened and the colt could wander toward {place.path_phrase}."
        ),
        (
            "What happened again and again in the story?",
            f"Three times the thief came for the toggle, and each time the little theft put the colt in danger. "
            f"The repetition showed that the trouble was real and growing, not a one-time accident."
        ),
        (
            f"Why did {child.id} call it pilferage on the third morning?",
            f"{child.id} finally saw the thief steal the toggle with {child.pronoun('possessive')} own eyes. "
            f"That turned a puzzling loss into clear, repeated stealing."
        ),
        (
            f"How did {child.id} and {elder.label_word} stop the thief?",
            f"They {fix.qa_text}. "
            f"That worked because it matched the thief's way of sneaking at the latch."
        ),
        (
            f"How did the story end for {colt.id}?",
            f"The colt was safe behind a shut gate and did not wander again. "
            f"The ending image proves the yard had become calm instead of anxious."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pilferage", "colt", "toggle", "folk"}
    fix = f["fix_cfg"]
    if "bell" in fix.tags or "sound" in fix.tags:
        tags.add("bell")
    if "basket" in fix.tags or "cover" in fix.tags:
        tags.add("basket")
    if "berries" in fix.tags or "trap" in fix.tags:
        tags.add("berries")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from this story ==")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.can_carry_small:
            bits.append("can_carry_small=True")
        if ent.movable:
            bits.append("movable=True")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  history={world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(Tf, Tg) :- thief(Tf), toggle(Tg), can_carry_small(Tf), easy_to_pilfer(Tg).
sensible_fix(Fx) :- fix(Fx), sense(Fx, S), sense_min(M), S >= M.
works(Tf, Fx) :- good_for(Fx, Tf), sensible_fix(Fx).
valid(Pl, Tf, Tg, Fx) :- place(Pl), hazard(Tf, Tg), works(Tf, Fx).

#show valid/4.
#show sensible_fix/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for thief_id, thief in THIEVES.items():
        lines.append(asp.fact("thief", thief_id))
        if thief.can_carry_small:
            lines.append(asp.fact("can_carry_small", thief_id))
    for toggle_id, toggle in TOGGLES.items():
        lines.append(asp.fact("toggle", toggle_id))
        if toggle.easy_to_pilfer:
            lines.append(asp.fact("easy_to_pilfer", toggle_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for thief_id in sorted(fix.works_for):
            lines.append(asp.fact("good_for", fix_id, thief_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def generate_smoke() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "colt" not in sample.story.lower() or "toggle" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story is empty or missing core story words.")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP valid_combos parity ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set))
    py_fixes = {cfg.id for cfg in sensible_fixes()}
    asp_fixes = set(asp_sensible_fixes())
    if py_fixes == asp_fixes:
        print(f"OK: sensible fixes match ({sorted(py_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: asp={sorted(asp_fixes)} python={sorted(py_fixes)}")
    try:
        generate_smoke()
        print("OK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Folk-tale storyworld: a thief steals a colt-gate toggle three times until a child finds the right answer."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thief", choices=THIEVES)
    ap.add_argument("--toggle", choices=TOGGLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["granny", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--colt-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid ASP combos")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thief and args.toggle:
        thief = THIEVES[args.thief]
        toggle = TOGGLES[args.toggle]
        if not hazard_possible(thief, toggle):
            raise StoryError(explain_toggle_rejection(thief, toggle))
    if args.fix and args.thief:
        if not fix_works(args.thief, args.fix):
            raise StoryError(explain_fix_rejection(args.fix, args.thief))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix, args.thief or "magpie"))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.thief is None or combo[1] == args.thief)
        and (args.toggle is None or combo[2] == args.toggle)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, thief_id, toggle_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["granny", "grandfather"])
    colt_name = args.colt_name or rng.choice(COLT_NAMES)
    return StoryParams(
        place=place_id,
        thief=thief_id,
        toggle=toggle_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        colt_name=colt_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        thief = THIEVES[params.thief]
        toggle = TOGGLES[params.toggle]
        fix = FIXES[params.fix]
    except KeyError as exc:
        raise StoryError(f"Unknown parameter choice: {exc}") from exc
    if not hazard_possible(thief, toggle):
        raise StoryError(explain_toggle_rejection(thief, toggle))
    if not fix_works(params.thief, params.fix):
        raise StoryError(explain_fix_rejection(params.fix, params.thief))
    world = tell(
        place=place,
        thief_cfg=thief,
        toggle_cfg=toggle,
        fix_cfg=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        colt_name=params.colt_name,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        fixes = asp_sensible_fixes()
        print(f"sensible fixes: {', '.join(fixes)}\n")
        print(f"{len(combos)} valid (place, thief, toggle, fix) combos:\n")
        for place_id, thief_id, toggle_id, fix_id in combos:
            print(f"  {place_id:8} {thief_id:8} {toggle_id:10} {fix_id}")
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
            header = f"### {p.child_name} in {p.place}: {p.thief} and the {p.toggle} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
