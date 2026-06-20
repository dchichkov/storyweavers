#!/usr/bin/env python3
"""
storyworlds/worlds/rusty_sign_attic_ladder_twist_moral_value_5.py
=================================================================

Standalone storyworld for a TinyStories-style seed:

    Words: rusty sign
    Setting: attic ladder
    Features: Twist, Moral Value
    Style: Space Adventure

Internal source tale:
    Mira turns an attic ladder into the boarding ramp for a pretend starship.
    A rusty sign beside the ladder looks like a secret space clue, so she
    almost rushes upward. The twist is that the sign is not a treasure hint at
    all. It is an old safety warning, and the repair tool she needs is hidden
    behind it. When Mira slows down, listens, and fixes the real problem before
    climbing, the mission succeeds because careful courage is stronger than
    hurried pretending.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class LaunchPlace:
    key: str
    house_name: str
    attic_name: str
    mission_goal: str
    opening_image: str
    ending_image: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RustySign:
    key: str
    family: str
    paint_words: str
    misread_text: str
    true_meaning: str
    hidden_gear: str
    reveal_image: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class LadderHazard:
    key: str
    family: str
    need: str
    label: str
    danger_line: str
    repair_goal: str
    base_danger: float
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepairGear:
    key: str
    need: str
    label: str
    action_line: str
    proof_line: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MoralValue:
    key: str
    virtue: str
    pause_line: str
    helper_line: str
    lesson_line: str
    closing_line: str
    tags: tuple[str, ...] = ()


@dataclass
class StoryParams:
    place: str
    sign: str
    hazard: str
    gear: str
    value: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "sister"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "father", "uncle", "brother"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "it", "object": "it", "possessive": "its"}
        return table[case]


@dataclass
class World:
    params: StoryParams
    place: LaunchPlace
    sign: RustySign
    hazard: LadderHazard
    gear: RepairGear
    value: MoralValue
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    history: list[dict[str, str]] = field(default_factory=list)
    facts: dict[str, str | bool | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, key: str, **details: str | int | float | bool) -> None:
        row = {"event": key}
        row.update({name: str(value) for name, value in details.items()})
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in paragraph if part) for paragraph in self.paragraphs if paragraph)

    def trace(self) -> str:
        lines = [
            "--- world ---",
            f"place={self.place.key}",
            f"sign={self.sign.key}",
            f"hazard={self.hazard.key}",
            f"gear={self.gear.key}",
            f"value={self.value.key}",
        ]
        seen: set[int] = set()
        for ent in self.entities.values():
            if id(ent) in seen:
                continue
            seen.add(id(ent))
            lines.append(
                f"{ent.id}: kind={ent.kind} type={ent.type} location={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)} attrs={ent.attrs}"
            )
        lines.append(f"facts={json.dumps(self.facts, ensure_ascii=False, sort_keys=True)}")
        lines.append("history:")
        for row in self.history:
            lines.append(f"  - {row}")
        return "\n".join(lines)


PLACES: dict[str, LaunchPlace] = {
    "comet_bay": LaunchPlace(
        key="comet_bay",
        house_name="the Fern family attic hall",
        attic_name="the comet bay under the rafters",
        mission_goal="a milk-crate cockpit with paper planets clipped around a fan",
        opening_image="The attic ladder dropped from the ceiling like a silver boarding ramp to a little starship.",
        ending_image="At the top, the comet bay glowed with paper planets while the ladder stood still and strong below.",
        tags=("attic", "ladder", "space"),
    ),
    "orbit_loft": LaunchPlace(
        key="orbit_loft",
        house_name="the Juniper house landing",
        attic_name="the orbit loft above the hall",
        mission_goal="a round window, a toy telescope, and a blanket spread like a captain's map",
        opening_image="Above the hallway, the attic ladder looked like a launch spine reaching into orbit.",
        ending_image="Moonlight touched the orbit loft, and the safe ladder waited like a docked rocket rail.",
        tags=("attic", "window", "orbit"),
    ),
    "nebula_nest": LaunchPlace(
        key="nebula_nest",
        house_name="the Clover house stairwell",
        attic_name="the nebula nest beside the roof beam",
        mission_goal="a star chart pinned near a flashlight that pretended to be mission control",
        opening_image="The attic ladder pointed into the dim ceiling like a quiet path toward a private nebula.",
        ending_image="The nebula nest shone softly overhead while the mended ladder rested as calm as a ship at port.",
        tags=("attic", "stars", "beam"),
    ),
}


SIGNS: dict[str, RustySign] = {
    "pin_code": RustySign(
        key="pin_code",
        family="pin",
        paint_words="CHECK PIN BEFORE BLASTOFF",
        misread_text="a secret launch code that sounded as if the ladder hid a captain's door",
        true_meaning="the fourth rung pin had slipped and needed attention before anyone climbed higher",
        hidden_gear="a bright spare cotter pin taped behind the sign",
        reveal_image="When the sign tipped open, the spare pin flashed like a silver comet.",
        tags=("pin", "warning"),
    ),
    "hook_order": RustySign(
        key="hook_order",
        family="hook",
        paint_words="LOCK HATCH FOR ORBIT",
        misread_text="an old command from a ship captain guarding the attic prize",
        true_meaning="the attic hatch hook had to be fastened or the panel might swing and bump a climber",
        hidden_gear="a blue loop cord and a brass hook tucked behind the sign",
        reveal_image="Behind the rusty sign waited a blue cord loop like a sleepy rocket tail.",
        tags=("hook", "warning"),
    ),
    "rail_order": RustySign(
        key="rail_order",
        family="rail",
        paint_words="GLOVE UP AT STARBOARD RAIL",
        misread_text="a clue about astronaut gloves hidden near a secret control panel",
        true_meaning="the right rail had a rough edge that needed smoothing before a small hand slid along it",
        hidden_gear="a strip of sanding cloth and silver tape hidden behind the sign",
        reveal_image="The back of the sign held sanding cloth and silver tape like patient tools from a ship locker.",
        tags=("rail", "warning"),
    ),
}


HAZARDS: dict[str, LadderHazard] = {
    "loose_rung_pin": LadderHazard(
        key="loose_rung_pin",
        family="pin",
        need="pin",
        label="a loose rung pin",
        danger_line="One metal pin had backed out so far that the rung could wobble under a small shoe.",
        repair_goal="the rung clicked back into line and stopped wiggling",
        base_danger=0.88,
        tags=("rung", "metal"),
    ),
    "swinging_hatch_hook": LadderHazard(
        key="swinging_hatch_hook",
        family="hook",
        need="hook",
        label="a swinging attic hatch",
        danger_line="The hatch panel above the ladder could flap and bump a climber if no hook held it open.",
        repair_goal="the hatch stayed open without drifting back",
        base_danger=0.82,
        tags=("hatch", "panel"),
    ),
    "rough_side_rail": LadderHazard(
        key="rough_side_rail",
        family="rail",
        need="rail",
        label="a rough side rail",
        danger_line="A rough splintered patch on the right rail could scrape a hand during the climb.",
        repair_goal="the rail felt smooth and kind to the touch",
        base_danger=0.74,
        tags=("rail", "wood"),
    ),
}


GEARS: dict[str, RepairGear] = {
    "spare_pin": RepairGear(
        key="spare_pin",
        need="pin",
        label="the spare cotter pin",
        action_line="Mira pressed the bright pin through the rung bracket and folded its ends flat.",
        proof_line="The rung stopped wobbling and answered with one neat click.",
        tags=("pin", "repair"),
    ),
    "hook_loop": RepairGear(
        key="hook_loop",
        need="hook",
        label="the brass hook and blue loop cord",
        action_line="Mira slipped the loop over the hatch ring and set the brass hook where it could hold fast.",
        proof_line="The hatch stayed wide and still instead of drifting back.",
        tags=("hook", "repair"),
    ),
    "sanding_strip": RepairGear(
        key="sanding_strip",
        need="rail",
        label="the sanding cloth and silver tape",
        action_line="Mira rubbed the rail smooth with the cloth and wrapped the last rough spot with silver tape.",
        proof_line="The rail felt smooth under her palm, almost cool like a ship handle.",
        tags=("rail", "repair"),
    ),
}


VALUES: dict[str, MoralValue] = {
    "careful_courage": MoralValue(
        key="careful_courage",
        virtue="careful courage",
        pause_line="Mira took a brave breath and decided that real captains check danger before they pretend to zoom away.",
        helper_line="Pip's quiet beep reminded her that courage is strongest when it looks closely first.",
        lesson_line="She learned that careful courage is not slower bravery. It is bravery that brings everyone home safe.",
        closing_line="Because she was careful first, the launch felt bigger and brighter at the end.",
        tags=("courage", "safety"),
    ),
    "patient_listening": MoralValue(
        key="patient_listening",
        virtue="patient listening",
        pause_line="Mira held still long enough to listen, and the attic suddenly felt less like a puzzle and more like a place that could answer back.",
        helper_line="Pip chirped once, and Mira listened to the sign, the ladder, and the little warning hidden inside the moment.",
        lesson_line="She learned that patient listening can turn a confusing clue into a clear path. The answer had been there all along.",
        closing_line="When she climbed at last, she knew the mission had started with listening, not with rushing.",
        tags=("listening", "patience"),
    ),
    "shared_responsibility": MoralValue(
        key="shared_responsibility",
        virtue="shared responsibility",
        pause_line="Mira remembered that a pretend ship is still shared space, so keeping it safe was part of being captain.",
        helper_line="She thanked Pip for the warning beep and treated the fix like work the whole crew deserved.",
        lesson_line="She learned that shared responsibility makes even a one-room mission feel real. Caring for the ladder was caring for the crew.",
        closing_line="The attic felt more like a true ship after she fixed what everyone depended on.",
        tags=("teamwork", "care"),
    ),
}


HERO_NAME = "Mira"
HELPER_NAME = "Pip"


def valid_combo(place: str, sign: str, hazard: str, gear: str, value: str) -> bool:
    if place not in PLACES or sign not in SIGNS or hazard not in HAZARDS or gear not in GEARS or value not in VALUES:
        return False
    sign_spec = SIGNS[sign]
    hazard_spec = HAZARDS[hazard]
    gear_spec = GEARS[gear]
    return sign_spec.family == hazard_spec.family and hazard_spec.need == gear_spec.need


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for place in sorted(PLACES):
        for sign in sorted(SIGNS):
            for hazard in sorted(HAZARDS):
                for gear in sorted(GEARS):
                    for value in sorted(VALUES):
                        if valid_combo(place, sign, hazard, gear, value):
                            rows.append((place, sign, hazard, gear, value))
    return rows


def explain_rejection(place: str, sign: str, hazard: str, gear: str, value: str) -> str:
    unknown: list[str] = []
    if place not in PLACES:
        unknown.append(f"unknown place {place!r}")
    if sign not in SIGNS:
        unknown.append(f"unknown sign {sign!r}")
    if hazard not in HAZARDS:
        unknown.append(f"unknown hazard {hazard!r}")
    if gear not in GEARS:
        unknown.append(f"unknown gear {gear!r}")
    if value not in VALUES:
        unknown.append(f"unknown value {value!r}")
    if unknown:
        return "; ".join(unknown)

    sign_spec = SIGNS[sign]
    hazard_spec = HAZARDS[hazard]
    gear_spec = GEARS[gear]
    if sign_spec.family != hazard_spec.family:
        return (
            f"Invalid story: sign {sign!r} warns about {sign_spec.family}, "
            f"but hazard {hazard!r} belongs to {hazard_spec.family}."
        )
    if hazard_spec.need != gear_spec.need:
        return (
            f"Invalid story: hazard {hazard!r} needs {hazard_spec.need}, "
            f"but gear {gear!r} repairs {gear_spec.need}."
        )
    return "Invalid story options."


def _build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.sign, params.hazard, params.gear, params.value):
        raise StoryError(explain_rejection(params.place, params.sign, params.hazard, params.gear, params.value))

    world = World(
        params=params,
        place=PLACES[params.place],
        sign=SIGNS[params.sign],
        hazard=HAZARDS[params.hazard],
        gear=GEARS[params.gear],
        value=VALUES[params.value],
    )

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="girl",
            label=HERO_NAME,
            location="hall",
            role="hero",
            traits=["imaginative", "brave"],
        )
    )
    hero.meters["feet_on_rungs"] = 0.0
    hero.meters["goal_height_m"] = 2.4
    hero.memes["wonder"] = 1.2
    hero.memes["haste"] = 0.9
    hero.memes["patience"] = 0.2
    hero.memes["care"] = 0.3

    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="robot",
            label=HELPER_NAME,
            location="hall",
            role="helper",
            traits=["watchful", "loyal"],
        )
    )
    helper.meters["beep_strength"] = 0.6
    helper.memes["care"] = 1.0
    helper.memes["trust"] = 0.8

    ladder = world.add(
        Entity(
            id="ladder",
            kind="object",
            type="ladder",
            label="the attic ladder",
            location="hall",
            role="ladder",
            traits=["folding", "tall"],
        )
    )
    ladder.meters["height_m"] = 2.4
    ladder.meters["danger"] = world.hazard.base_danger
    ladder.meters["ready"] = 0.0
    ladder.meters["stability"] = max(0.0, 1.0 - world.hazard.base_danger)

    sign = world.add(
        Entity(
            id="sign",
            kind="object",
            type="sign",
            label="the rusty sign",
            location="ladder_side",
            role="sign",
            traits=["rusty", "old"],
            attrs={"paint_words": world.sign.paint_words},
        )
    )
    sign.meters["rust"] = 0.9
    sign.meters["clarity"] = 0.5
    sign.memes["warning"] = 1.0

    gear = world.add(
        Entity(
            id="gear",
            kind="object",
            type="gear",
            label=world.gear.label,
            location="behind_sign",
            role="gear",
        )
    )
    gear.meters["usefulness"] = 1.0

    attic = world.add(
        Entity(
            id="attic",
            kind="place",
            type="attic",
            label=world.place.attic_name,
            location="ceiling",
            role="destination",
        )
    )
    attic.meters["wonder"] = 1.0

    world.facts.update(
        {
            "hero_name": hero.label,
            "helper_name": helper.label,
            "goal": world.place.mission_goal,
            "hazard_label": world.hazard.label,
            "hazard_need": world.hazard.need,
            "paint_words": world.sign.paint_words,
            "misread": world.sign.misread_text,
            "true_meaning": world.sign.true_meaning,
            "hidden_gear": world.sign.hidden_gear,
            "twist_revealed": False,
            "hazard_fixed": False,
            "launched_safely": False,
            "moral": world.value.virtue,
        }
    )
    return world


def _introduce(world: World) -> None:
    hero = world.get("hero")
    world.say(world.place.opening_image)
    world.say(
        f"{hero.label} called the top of it {world.place.attic_name}, because {world.place.mission_goal} waited there."
    )
    world.say(
        f"She lifted one foot toward the attic ladder and whispered that this would be the cleanest launch in {world.place.house_name}."
    )
    world.event("premise", place=world.place.key, goal=world.place.mission_goal)


def _misread_sign(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    sign = world.get("sign")
    hero.memes["wonder"] += 0.3
    hero.memes["haste"] += 0.4
    world.para()
    world.say(
        f"Beside the first rung hung {sign.label}, its old paint saying '{world.sign.paint_words}'."
    )
    world.say(
        f"To {hero.label}, the message looked like {world.sign.misread_text}, so she almost scampered up before {helper.label} could roll under the ladder."
    )
    if hero.memes["haste"] > hero.memes["patience"]:
        world.say(
            f"{helper.label} gave a worried beep, and {hero.label} froze with her toes just brushing the lowest rung."
        )
        hero.meters["feet_on_rungs"] = 0.1
        world.facts["almost_rushed"] = True
    world.event("misread_sign", paint=world.sign.paint_words, misread=world.sign.misread_text)


def _reveal_twist(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    ladder = world.get("ladder")
    world.para()
    world.say(world.value.pause_line)
    world.say(world.value.helper_line)
    world.say(
        f"She traced the arrow on the rusty sign with one finger and finally saw the truth: it was not a treasure clue at all."
    )
    world.say(
        f"It meant that {world.sign.true_meaning}. {world.hazard.danger_line}"
    )
    world.say(world.sign.reveal_image)
    world.say(
        f"There was {world.sign.hidden_gear}, which matched the warning exactly."
    )
    hero.memes["haste"] = max(0.0, hero.memes["haste"] - 0.8)
    hero.memes["patience"] += 0.9
    hero.memes["care"] += 0.7
    helper.memes["trust"] += 0.1
    world.facts["twist_revealed"] = True
    world.event("twist", truth=world.sign.true_meaning, hidden_gear=world.sign.hidden_gear)
    if ladder.meters["danger"] >= 0.8:
        world.facts["risk_level"] = "high"
    elif ladder.meters["danger"] >= 0.5:
        world.facts["risk_level"] = "medium"
    else:
        world.facts["risk_level"] = "low"


def _repair(world: World) -> None:
    hero = world.get("hero")
    ladder = world.get("ladder")
    world.para()
    world.say(
        f"{hero.label} climbed back down to the floor, took {world.gear.label}, and treated the ladder like real equipment instead of scenery."
    )
    world.say(world.gear.action_line)
    world.say(world.gear.proof_line)
    world.say(
        f"Soon {world.hazard.repair_goal}, and the attic ladder felt ready for small astronaut feet."
    )
    ladder.meters["danger"] = 0.0
    ladder.meters["ready"] = 1.0
    ladder.meters["stability"] = 1.0
    hero.memes["courage"] += 0.8
    hero.memes["care"] += 0.4
    world.facts["hazard_fixed"] = True
    world.event("repair", gear=world.gear.key, hazard=world.hazard.key)


def _launch(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    ladder = world.get("ladder")
    world.para()
    if ladder.meters["ready"] < 1.0:
        raise StoryError("Story generation bug: launch attempted before ladder was ready.")
    hero.meters["feet_on_rungs"] = ladder.meters["height_m"]
    hero.location = "attic"
    helper.location = "attic"
    world.say(
        f"Then {hero.label} and {helper.label} climbed together, one careful rung at a time, until the mission deck opened above them."
    )
    world.say(world.value.lesson_line)
    world.say(world.value.closing_line)
    world.say(world.place.ending_image)
    world.facts["launched_safely"] = True
    world.event("launch", destination=world.place.attic_name, safe=True)


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    _introduce(world)
    _misread_sign(world)
    _reveal_twist(world)
    _repair(world)
    _launch(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Write a child-friendly Space Adventure in an attic where a rusty sign beside an attic ladder "
            f"turns out to be a safety warning instead of a clue."
        ),
        (
            f"Tell a story about {world.facts['hero_name']} trying to reach {world.place.attic_name}, "
            f"finding {world.facts['hidden_gear']}, and learning {world.value.virtue}."
        ),
        (
            f"Create a complete beginning-middle-ending story with a twist: the words '{world.sign.paint_words}' "
            f"look magical at first, but they really protect a child on an attic ladder."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = str(world.facts["hero_name"])
    return [
        QAItem(
            question="Why did Mira stop before racing up the attic ladder?",
            answer=(
                f"{hero} stopped because the rusty sign was warning her about {world.hazard.label}, not inviting her to a secret prize. "
                f"When she understood the real danger, she knew rushing would make the pretend mission unsafe."
            ),
        ),
        QAItem(
            question="What was the twist about the rusty sign?",
            answer=(
                f"The twist was that the rusty sign was not a space clue at all. "
                f"It was an old safety warning, and the repair item hidden behind it helped {hero} fix the ladder."
            ),
        ),
        QAItem(
            question="How did Mira make the mission safe enough to continue?",
            answer=(
                f"{hero} used {world.gear.label} to fix {world.hazard.label}. "
                f"After that, the attic ladder became steady enough for her and Pip to climb one careful rung at a time."
            ),
        ),
        QAItem(
            question="What moral did Mira learn by the end of the story?",
            answer=(
                f"{hero} learned {world.value.virtue}. "
                f"The mission only felt like a true launch after she slowed down, listened, and cared for the ladder first."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a warning sign matter even during pretend play?",
            answer=(
                "A warning sign can point to a real physical problem even when the game is imaginary. "
                "In this attic mission, the sign kept the child from treating danger like decoration."
            ),
        ),
        QAItem(
            question="What kind of problem did the attic ladder have in this world?",
            answer=(
                f"The attic ladder had {world.hazard.label}. "
                f"That problem mattered because climbing higher without fixing it could have made the launch shaky or painful."
            ),
        ),
        QAItem(
            question="How did the story show that bravery and safety can belong together?",
            answer=(
                f"The story showed it by letting {world.facts['hero_name']} stay brave enough to keep the mission going while still repairing the danger first. "
                f"Her courage became more real after it protected the crew instead of rushing past the warning."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
place(P) :- launch_place(P).
sign(S) :- rusty_sign(S).
hazard(H) :- ladder_hazard(H).
gear(G) :- repair_gear(G).
value(V) :- moral_value(V).

valid(P,S,H,G,V) :-
    place(P),
    sign(S),
    hazard(H),
    gear(G),
    value(V),
    sign_family(S,F),
    hazard_family(H,F),
    hazard_need(H,N),
    gear_need(G,N).

ok :- chosen(P,S,H,G,V), valid(P,S,H,G,V).

#show valid/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for place in PLACES.values():
        rows.append(fact("launch_place", place.key))
    for sign in SIGNS.values():
        rows.append(fact("rusty_sign", sign.key))
        rows.append(fact("sign_family", sign.key, sign.family))
    for hazard in HAZARDS.values():
        rows.append(fact("ladder_hazard", hazard.key))
        rows.append(fact("hazard_family", hazard.key, hazard.family))
        rows.append(fact("hazard_need", hazard.key, hazard.need))
    for gear in GEARS.values():
        rows.append(fact("repair_gear", gear.key))
        rows.append(fact("gear_need", gear.key, gear.need))
    for value in VALUES.values():
        rows.append(fact("moral_value", value.key))
    if params is not None:
        rows.append(fact("chosen", params.place, params.sign, params.hazard, params.gear, params.value))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(tuple(str(x) for x in atom) for atom in atoms(model, "valid"))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        raise StoryError(
            f"ASP/Python mismatch. only_python={sorted(py - asp)} only_asp={sorted(asp - py)}"
        )

    for index, combo in enumerate(sorted(py), start=1):
        params = StoryParams(*combo, seed=index)
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid combo {combo!r}.")
        sample = generate(params)
        if "rusty sign" not in sample.story or "attic ladder" not in sample.story:
            raise StoryError(f"Generated story missed seed words for combo {combo!r}.")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"Generated sample omitted prompts or QA for combo {combo!r}.")
        if not sample.world:
            raise StoryError(f"Generated sample lost world state for combo {combo!r}.")
        if not sample.world.facts.get("twist_revealed"):
            raise StoryError(f"Generated sample never revealed the twist for combo {combo!r}.")
        if not sample.world.facts.get("hazard_fixed"):
            raise StoryError(f"Generated sample never fixed the ladder for combo {combo!r}.")
        if not sample.world.facts.get("launched_safely"):
            raise StoryError(f"Generated sample never completed a safe launch for combo {combo!r}.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated sample leaked template braces for combo {combo!r}.")

    invalid = StoryParams(
        place="comet_bay",
        sign="pin_code",
        hazard="rough_side_rail",
        gear="spare_pin",
        value="careful_courage",
        seed=999,
    )
    if valid_combo(invalid.place, invalid.sign, invalid.hazard, invalid.gear, invalid.value):
        raise StoryError("Internal verify bug: invalid combo unexpectedly passed Python gate.")
    if asp_accepts(invalid):
        raise StoryError("ASP accepted an invalid combo with mismatched sign and hazard families.")

    return (
        f"OK: Python and ASP agree on {len(py)} valid attic-ladder space-adventure stories, "
        "and each generated story reaches the twist, repair, and moral ending."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Storyworld: rusty-sign attic-ladder Space Adventure with a twist and moral value."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--sign", choices=sorted(SIGNS))
    parser.add_argument("--hazard", choices=sorted(HAZARDS))
    parser.add_argument("--gear", choices=sorted(GEARS))
    parser.add_argument("--value", choices=sorted(VALUES))
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sign is None or combo[1] == args.sign)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.gear is None or combo[3] == args.gear)
        and (args.value is None or combo[4] == args.value)
    ]
    if not choices:
        place_key = args.place or sorted(PLACES)[0]
        sign_key = args.sign or sorted(SIGNS)[0]
        hazard_key = args.hazard or sorted(HAZARDS)[0]
        gear_key = args.gear or sorted(GEARS)[0]
        value_key = args.value or sorted(VALUES)[0]
        raise StoryError(explain_rejection(place_key, sign_key, hazard_key, gear_key, value_key))
    combo = rng.choice(sorted(choices))
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(*combo, seed=seed)


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if args.qa:
        print("\nPROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nSTORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
    if args.trace and sample.world is not None:
        print("\nTRACE")
        print(sample.world.trace())


def _samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        base_seed = args.seed if args.seed is not None else 1000
        return [
            generate(StoryParams(*combo, seed=base_seed + idx))
            for idx, combo in enumerate(valid_combos(), start=1)
        ]

    target = max(1, args.n)
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    i = 0
    while len(samples) < target and attempts < target * 50:
        seed = base_seed + i
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed), index=i + 1)
        sample = generate(params)
        attempts += 1
        i += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique attic-ladder space-adventure samples.")
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = _samples_from_args(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for idx, sample in enumerate(samples, start=1):
            label = None
            if args.all:
                params = sample.params
                label = f"### {params.place} / {params.sign} / {params.hazard} / {params.gear} / {params.value}"
            elif len(samples) > 1:
                label = f"### variant {idx}"
            emit(sample, args, label)
            if idx != len(samples):
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
