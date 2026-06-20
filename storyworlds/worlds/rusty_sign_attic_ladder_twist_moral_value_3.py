#!/usr/bin/env python3
"""
storyworlds/worlds/rusty_sign_attic_ladder_twist_moral_value_3.py
=================================================================

Standalone storyworld for a TinyStories-style seed:

    Words: rusty sign
    Setting: attic ladder
    Features: Twist, Moral Value
    Style: Space Adventure

Internal source tale:
    Two children treat an attic ladder like the launch tower to a tiny space
    station under the roof. A rusty sign beside the ladder looks like a secret
    mission clue, so the eager hero nearly rushes past it. The twist is that
    the sign is not guarding treasure at all: it is an old safety warning left
    by a caring grown-up, pointing to a real physical problem on the ladder.
    Once the children slow down, decode the sign, and repair the hazard, they
    reach the attic safely and leave the path better for the next explorer.
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
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass(frozen=True)
class LaunchAttic:
    key: str
    house_name: str
    ladder_label: str
    attic_label: str
    window_label: str
    mission_goal: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class RustySign:
    key: str
    family: str
    paint_words: str
    misread_text: str
    true_purpose: str
    behind_sign: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Hazard:
    key: str
    family: str
    need: str
    sound_text: str
    discovery_text: str
    risk_text: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Fix:
    key: str
    need: str
    tool_text: str
    action_text: str
    proof_text: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ValueLesson:
    key: str
    virtue: str
    guidance_line: str
    choice_text: str
    community_action: str
    closing_moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "father"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class StoryParams:
    place: str
    sign: str
    hazard: str
    fix: str
    value: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: LaunchAttic, value: ValueLesson) -> None:
        self.place = place
        self.value = value
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}
        self.history: list[dict[str, str]] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
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
        return "\n\n".join(" ".join(parts) for parts in self.paragraphs if parts)

    def log(self, event: str, **details: str) -> None:
        item = {"event": event}
        item.update({k: str(v) for k, v in details.items()})
        self.history.append(item)

    def trace(self) -> str:
        lines = ["--- world ---", f"place={self.place.key}", f"value={self.value.key}"]
        seen: set[int] = set()
        for ent in self.entities.values():
            if id(ent) in seen:
                continue
            seen.add(id(ent))
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            lines.append(
                f"{ent.id}: kind={ent.kind} type={ent.type} meters={meters} memes={memes}"
            )
        lines.append("history:")
        for item in self.history:
            lines.append(f"  - {item}")
        return "\n".join(lines)


PLACES: dict[str, LaunchAttic] = {
    "comet_crate": LaunchAttic(
        key="comet_crate",
        house_name="the Maple Lane house",
        ladder_label="the attic ladder",
        attic_label="the comet attic deck",
        window_label="the round roof window",
        mission_goal="a cardboard star map taped beside an old silver fan",
        ending_image="fresh tape bright across the rail while moonlight pooled over the top rung",
        tags={"attic", "ladder", "space"},
    ),
    "orbital_quilt": LaunchAttic(
        key="orbital_quilt",
        house_name="the Bluebird cottage",
        ladder_label="the attic ladder",
        attic_label="the orbital quilt loft",
        window_label="the little skylight",
        mission_goal="a milk-crate control panel with paper planets hanging above it",
        ending_image="the safe rungs shining under the skylight like a small launch bridge",
        tags={"attic", "ladder", "quilt"},
    ),
    "meteor_nook": LaunchAttic(
        key="meteor_nook",
        house_name="the Juniper house",
        ladder_label="the attic ladder",
        attic_label="the meteor nook under the rafters",
        window_label="the narrow roof pane",
        mission_goal="a tin telescope pointing past a line of glow-star stickers",
        ending_image="the clear ladder rising to the nook like a calm rocket gantry",
        tags={"attic", "ladder", "telescope"},
    ),
}


SIGNS: dict[str, RustySign] = {
    "bolt_step": RustySign(
        key="bolt_step",
        family="rung",
        paint_words="TURN BOLT BEFORE STEP",
        misread_text="a captain's code that might open a hidden rocket lock",
        true_purpose="a careful reminder to tighten the loose rung before anyone climbed higher",
        behind_sign="a little tin clipped behind the sign held the right brass bolt and washer",
        tags={"sign", "bolt", "rung"},
    ),
    "latch_hatch": RustySign(
        key="latch_hatch",
        family="hatch",
        paint_words="LATCH HATCH BEFORE COUNTDOWN",
        misread_text="an air-lock order from some forgotten attic spaceship crew",
        true_purpose="a plain warning that the attic hatch could swing shut unless its hook was fastened",
        behind_sign="a small hook key on blue string",
        tags={"sign", "hatch", "hook"},
    ),
    "glove_rail": RustySign(
        key="glove_rail",
        family="rail",
        paint_words="GLOVES FOR STARBOARD RAIL",
        misread_text="a message about astronaut gloves waiting near secret controls",
        true_purpose="an old note telling climbers that the right rail still held sharp splinters",
        behind_sign="a strip of sanding cloth and a roll of smooth tape",
        tags={"sign", "rail", "splinter"},
    ),
}


HAZARDS: dict[str, Hazard] = {
    "wobble_rung": Hazard(
        key="wobble_rung",
        family="rung",
        need="tighten_bolt",
        sound_text="the fourth rung gave a hollow clink and tipped under Mira's slipper",
        discovery_text="the rung's brass bolt had slid halfway out, leaving the step loose in its socket",
        risk_text="One quick jump could have rolled a foot sideways and sent a climber bumping down the ladder.",
        tags={"ladder", "rung", "bolt"},
    ),
    "swing_hatch": Hazard(
        key="swing_hatch",
        family="hatch",
        need="secure_hook",
        sound_text="the attic hatch drifted and banged once above their heads like a metal moon door",
        discovery_text="the old hatch hook was unfastened, so the door could swing back into whoever reached the top",
        risk_text="A sudden door swing could have startled a child and knocked balance away on the narrow top steps.",
        tags={"ladder", "hatch", "door"},
    ),
    "splinter_rail": Hazard(
        key="splinter_rail",
        family="rail",
        need="sand_and_tape",
        sound_text="Mira's sleeve caught on the side rail with a dry scratch",
        discovery_text="the right rail had a spray of lifted splinters where old paint had peeled back",
        risk_text="A snagged sleeve could make a climber yank backward and miss the next rung.",
        tags={"ladder", "rail", "splinter"},
    ),
}


FIXES: dict[str, Fix] = {
    "tighten_bolt": Fix(
        key="tighten_bolt",
        need="tighten_bolt",
        tool_text="a moon-sticker wrench",
        action_text="Aunt Nova held the ladder steady while Mira passed the wrench up and Bo slid the brass bolt back through the rung.",
        proof_text="When Aunt Nova tested the step twice, it stayed level and quiet.",
        tags={"repair", "rung", "wrench"},
    ),
    "secure_hook": Fix(
        key="secure_hook",
        need="secure_hook",
        tool_text="the blue-string hook key",
        action_text="Mira climbed only halfway, passed the hook key up to Aunt Nova, and watched her fasten the hatch before anyone went higher.",
        proof_text="After that, the hatch rested open instead of swinging like a surprise door.",
        tags={"repair", "hatch", "hook"},
    ),
    "sand_and_tape": Fix(
        key="sand_and_tape",
        need="sand_and_tape",
        tool_text="sanding cloth and smooth silver tape",
        action_text="Bo rubbed the splinters down while Mira pressed smooth silver tape along the rail and Aunt Nova checked each edge with her palm.",
        proof_text="The rail turned gentle again, with nothing left to catch a sleeve or scrape a hand.",
        tags={"repair", "rail", "tape"},
    ),
}


VALUES: dict[str, ValueLesson] = {
    "patience": ValueLesson(
        key="patience",
        virtue="patience",
        guidance_line='Aunt Nova said, "Good captains do not race past a warning. They let the truth catch up first."',
        choice_text="Mira breathed slowly, let Aunt Nova test the fix twice, and waited for the safe word before taking another step.",
        community_action="Then she traced the faded letters with bright chalk so the warning could be read before the next mission too.",
        closing_moral="From then on, Mira remembered that patience can feel slower than a countdown, but it carries you farther than a rush.",
        tags={"value", "patience"},
    ),
    "responsibility": ValueLesson(
        key="responsibility",
        virtue="responsibility",
        guidance_line='Aunt Nova said, "A real captain leaves the ship safer than she found it."',
        choice_text="Mira stayed beside the ladder, named each risky spot out loud, and checked the path again after the repair instead of assuming it was fine.",
        community_action="Then she tied a clean paper label under the old sign so younger climbers would know exactly what to watch for.",
        closing_moral="From then on, Mira remembered that responsibility means caring about the next person's steps, not only your own adventure.",
        tags={"value", "responsibility"},
    ),
    "teamwork": ValueLesson(
        key="teamwork",
        virtue="teamwork",
        guidance_line='Aunt Nova said, "Even a rocket crew needs more than one pair of careful hands."',
        choice_text="Mira held the flashlight steady for Bo and Aunt Nova, and she listened when Bo noticed the last rough edge that she had missed.",
        community_action="Then the three of them cheered together and checked the ladder as one crew before returning to the mission.",
        closing_moral="From then on, Mira remembered that teamwork turns a scary problem into a shared solution.",
        tags={"value", "teamwork"},
    ),
}


KNOWLEDGE = {
    "attic": [
        (
            "What is an attic ladder?",
            "An attic ladder is a narrow ladder that leads up to a roof space or loft. Because it is steep and small, people have to climb it carefully.",
        )
    ],
    "rust": [
        (
            "Why can a rusty sign still matter?",
            "Rust can make a sign look old, but the message may still be important. Wise readers pay attention to the warning, not just the worn paint.",
        )
    ],
    "warning": [
        (
            "Why should children read warning signs slowly?",
            "Warnings often point to a real physical problem such as a loose step or sharp edge. Reading slowly helps a child understand the danger before acting.",
        )
    ],
    "rung": [
        (
            "Why is a loose rung dangerous?",
            "A loose rung can tilt under a foot without much notice. That sudden movement can make a climber lose balance.",
        )
    ],
    "hatch": [
        (
            "Why is a swinging hatch a problem near a ladder?",
            "A swinging hatch can surprise someone at the top of the ladder. Surprises are risky when there is very little space to steady your body.",
        )
    ],
    "rail": [
        (
            "Why are splinters on a rail unsafe?",
            "Splinters can scratch skin or catch on a sleeve. A sudden snag can pull a climber off balance.",
        )
    ],
    "patience": [
        (
            "How can patience keep someone safe?",
            "Patience makes room for checking and testing before action. That extra moment can stop a preventable accident.",
        )
    ],
    "responsibility": [
        (
            "What does responsibility look like in a shared place?",
            "Responsibility means noticing dangers and helping fix or mark them for others. It treats safety as something the whole group deserves.",
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help during repairs?",
            "One person can hold light, another can pass tools, and another can test the result. Shared jobs make careful work easier and safer.",
        )
    ],
    "space": [
        (
            "Why might a child call an attic a spaceship in a story?",
            "Children often use imagination to turn ordinary places into adventure settings. That play can be exciting as long as real-world safety still guides choices.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "attic",
    "rust",
    "warning",
    "rung",
    "hatch",
    "rail",
    "patience",
    "responsibility",
    "teamwork",
    "space",
]


def sign_matches_hazard(sign: RustySign, hazard: Hazard) -> bool:
    return sign.family == hazard.family


def fix_matches_hazard(hazard: Hazard, fix: Fix) -> bool:
    return hazard.need == fix.need


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_key in sorted(PLACES):
        for sign_key, sign in SIGNS.items():
            for hazard_key, hazard in HAZARDS.items():
                for fix_key, fix in FIXES.items():
                    for value_key in sorted(VALUES):
                        if sign_matches_hazard(sign, hazard) and fix_matches_hazard(hazard, fix):
                            combos.append((place_key, sign_key, hazard_key, fix_key, value_key))
    return sorted(combos)


def explain_rejection(place_key: str, sign_key: str, hazard_key: str, fix_key: str, value_key: str) -> str:
    if place_key not in PLACES:
        return f"Unknown place key: {place_key!r}."
    if sign_key not in SIGNS:
        return f"Unknown sign key: {sign_key!r}."
    if hazard_key not in HAZARDS:
        return f"Unknown hazard key: {hazard_key!r}."
    if fix_key not in FIXES:
        return f"Unknown fix key: {fix_key!r}."
    if value_key not in VALUES:
        return f"Unknown value key: {value_key!r}."
    sign = SIGNS[sign_key]
    hazard = HAZARDS[hazard_key]
    fix = FIXES[fix_key]
    reasons: list[str] = []
    if not sign_matches_hazard(sign, hazard):
        reasons.append(
            f"{sign.key} warns about {sign.family}, but {hazard.key} is a {hazard.family} problem."
        )
    if not fix_matches_hazard(hazard, fix):
        reasons.append(
            f"{fix.key} does not solve the need {hazard.need} created by {hazard.key}."
        )
    if not reasons:
        reasons.append(
            "The requested combination does not produce one coherent attic-ladder safety story."
        )
    reasons.append(f"Value {value_key} is allowed, but the sign, hazard, and fix still have to describe the same physical trouble.")
    return "Invalid story choices: " + " ".join(reasons)


def _r_decoded_sign_changes_hero(world: World) -> list[str]:
    hero = world.get("hero")
    sign = world.get("sign")
    if sign.meters["decoded"] < THRESHOLD or hero.memes["impatience"] < THRESHOLD:
        return []
    sig = ("decoded_sign", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["impatience"] = max(0.0, hero.memes["impatience"] - 0.7)
    hero.memes["care"] += 1.0
    hero.memes["respect"] += 1.0
    world.facts["twist_landed"] = True
    world.log("decoded_sign_changes_hero", hero=hero.id)
    return []


def _r_repair_secures_ladder(world: World) -> list[str]:
    ladder = world.get("ladder")
    hazard = world.get("hazard")
    attic = world.get("attic")
    if hazard.meters["solved"] < THRESHOLD or ladder.meters["tested"] < THRESHOLD:
        return []
    sig = ("ladder_safe", ladder.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ladder.meters["safe"] += 1.0
    attic.meters["reachable"] += 1.0
    world.facts["path_safe"] = True
    world.log("repair_secures_ladder", ladder=ladder.id)
    return []


def _r_value_completes_mission(world: World) -> list[str]:
    hero = world.get("hero")
    ladder = world.get("ladder")
    sign = world.get("sign")
    if ladder.meters["safe"] < THRESHOLD or sign.meters["clarified"] < THRESHOLD:
        return []
    if hero.memes["care"] < THRESHOLD or hero.memes["crew_spirit"] < THRESHOLD:
        return []
    sig = ("value_complete", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["moral_value_shown"] = True
    world.facts["resolved"] = True
    world.log("value_completes_mission", hero=hero.id, value=world.value.key)
    return []


CAUSAL_RULES = [
    _r_decoded_sign_changes_hero,
    _r_repair_secures_ladder,
    _r_value_completes_mission,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True


def introduce(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    elder = world.get("elder")
    attic = world.get("attic")
    hero.memes["wonder"] += 1.0
    hero.memes["crew_spirit"] += 0.5
    friend.memes["crew_spirit"] += 0.5
    attic.meters["mission_ready"] += 1.0
    world.say(
        f"Mira and Bo called {world.place.ladder_label} the launch tower to {world.place.attic_label} in {world.place.house_name}."
    )
    world.say(
        f"Above them, beside {world.place.window_label}, waited {world.place.mission_goal}, and Aunt Nova let them play captain there as long as they climbed carefully."
    )
    world.say(world.value.guidance_line)
    world.log("introduce", hero=hero.id, friend=friend.id, elder=elder.id, place=world.place.key)


def discover_sign(world: World, sign: RustySign) -> None:
    hero = world.get("hero")
    sign_ent = world.get("sign")
    ladder = world.get("ladder")
    hero.memes["impatience"] += 1.0
    hero.memes["wonder"] += 0.5
    sign_ent.meters["visible"] += 1.0
    ladder.meters["questioned"] += 1.0
    world.say(
        f"Halfway up, Mira spotted a rusty sign wired to the side of the attic ladder. Under the orange flakes, the old paint still said, \"{sign.paint_words}.\""
    )
    world.say(
        f"To Mira, it sounded like {sign.misread_text}, and her heart beat faster as if the mission had suddenly become real."
    )
    world.log("discover_sign", sign=sign.key)


def risky_misread(world: World, hazard: Hazard) -> None:
    hero = world.get("hero")
    hazard_ent = world.get("hazard")
    ladder = world.get("ladder")
    hero.memes["fear"] += 0.5
    hero.memes["impatience"] += 0.5
    hazard_ent.meters["active"] += 1.0
    ladder.meters["unsafe"] += 1.0
    world.say(
        f"Mira reached for the next step as if she could unlock the whole attic with one brave move, but {hazard.sound_text}."
    )
    world.say(
        f"Bo grabbed the rail and whispered, \"That does not sound like a game.\" {hazard.risk_text}"
    )
    world.log("risky_misread", hazard=hazard.key)


def reveal_twist(world: World, sign: RustySign, hazard: Hazard) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    sign_ent = world.get("sign")
    hazard_ent = world.get("hazard")
    hero.memes["curiosity"] += 1.0
    friend.memes["care"] += 0.5
    sign_ent.meters["decoded"] += 1.0
    sign_ent.meters["clarified"] += 1.0
    hazard_ent.meters["found"] += 1.0
    world.say(
        f"Aunt Nova shone her flashlight across the letters and smiled a little. The twist was simple: the sign was not a secret mission clue at all."
    )
    world.say(
        f"It was {sign.true_purpose}. Behind it, they found {sign.behind_sign}, and the light also showed {hazard.discovery_text}."
    )
    world.facts["twist_text"] = sign.true_purpose
    world.facts["hazard_text"] = hazard.discovery_text
    world.log("reveal_twist", sign=sign.key, hazard=hazard.key)
    propagate(world)


def repair_scene(world: World, fix: Fix) -> None:
    hero = world.get("hero")
    ladder = world.get("ladder")
    hazard = world.get("hazard")
    hero.memes["crew_spirit"] += 0.5
    hero.memes["care"] += 0.5
    ladder.meters["tested"] += 1.0
    hazard.meters["solved"] += 1.0
    world.say(
        f"They treated the repair like the most important part of the mission. Using {fix.tool_text}, {fix.action_text}"
    )
    world.say(fix.proof_text)
    world.facts["repair_action"] = fix.action_text
    world.facts["repair_tool"] = fix.tool_text
    world.log("repair", fix=fix.key)
    propagate(world)


def value_turn(world: World) -> None:
    hero = world.get("hero")
    sign_ent = world.get("sign")
    hero.memes["care"] += 0.5
    hero.memes["crew_spirit"] += 0.5
    sign_ent.meters["clarified"] += 0.5
    world.say(world.value.choice_text)
    world.say(world.value.community_action)
    world.log("value_turn", value=world.value.key)
    propagate(world)


def closing(world: World) -> None:
    attic = world.get("attic")
    if attic.meters["reachable"] < THRESHOLD or not world.facts.get("resolved"):
        raise StoryError("Story did not resolve into a safe, value-driven ending.")
    world.say(
        f"Only then did Mira and Bo climb the rest of the attic ladder. At the top, {world.place.mission_goal} waited in a wash of starlike dust, and the whole attic felt more like a space station because it was safe."
    )
    world.say(
        f"Before their pretend countdown, Mira looked back at {world.place.ending_image}. {world.value.closing_moral}"
    )
    world.log("closing", resolved="yes")


def tell(place: LaunchAttic, sign: RustySign, hazard: Hazard, fix: Fix, value: ValueLesson) -> World:
    world = World(place, value)
    hero = world.add(Entity("Mira", kind="character", type="girl", label="Mira", role="hero", traits=["imaginative"]))
    friend = world.add(Entity("Bo", kind="character", type="boy", label="Bo", role="friend", traits=["steady"]))
    elder = world.add(Entity("Aunt Nova", kind="character", type="woman", label="Aunt Nova", role="elder", traits=["careful"]))
    world.add(Entity("ladder", kind="thing", type="ladder", label=place.ladder_label))
    world.add(Entity("attic", kind="thing", type="attic", label=place.attic_label))
    world.add(Entity("sign", kind="thing", type="sign", label="rusty sign"))
    world.add(Entity("hazard", kind="thing", type="hazard", label=hazard.key))

    introduce(world)
    world.para()
    discover_sign(world, sign)
    risky_misread(world, hazard)
    reveal_twist(world, sign, hazard)
    world.para()
    repair_scene(world, fix)
    value_turn(world)
    closing(world)

    world.facts.update(
        place=place,
        sign=sign,
        hazard=hazard,
        fix=fix,
        value=value,
        hero=hero,
        friend=friend,
        elder=elder,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    sign: RustySign = world.facts["sign"]  # type: ignore[assignment]
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    value: ValueLesson = world.facts["value"]  # type: ignore[assignment]
    return [
        'Write a child-facing Space Adventure story that includes the words "rusty sign" and takes place on an attic ladder.',
        f"Give the story a twist where the sign saying {sign.paint_words!r} looks exciting at first but is really about the danger that {hazard.discovery_text}.",
        f"End with a clear moral value about {value.virtue} shown through a repaired ladder and a safer shared space.",
    ]


def story_questions(world: World) -> list[QAItem]:
    sign: RustySign = world.facts["sign"]  # type: ignore[assignment]
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    fix: Fix = world.facts["fix"]  # type: ignore[assignment]
    value: ValueLesson = world.facts["value"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where did the story happen?",
            f"The story happened around {world.place.ladder_label} leading up to {world.place.attic_label} in {world.place.house_name}. The ladder mattered because it was both the children's pretend launch tower and the place where the real danger waited.",
        ),
        QAItem(
            "What did Mira think the rusty sign meant at first?",
            f"At first, Mira thought the rusty sign sounded like {sign.misread_text}. Her imagination turned an old house warning into part of a space mission.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that the sign was really {sign.true_purpose}. What looked like treasure language was actually a caring message meant to protect climbers.",
        ),
        QAItem(
            "What danger was actually on the ladder?",
            f"The real danger was that {hazard.discovery_text}. {hazard.risk_text}",
        ),
        QAItem(
            "How did they make the ladder safe again?",
            f"Using {fix.tool_text}, {fix.action_text} {fix.proof_text}",
        ),
        QAItem(
            "What moral value did Mira learn?",
            f"Mira learned about {value.virtue}. She showed it by changing her behavior after the twist instead of hurrying back into the game.",
        ),
    ]


def world_knowledge_questions(world: World) -> list[QAItem]:
    sign: RustySign = world.facts["sign"]  # type: ignore[assignment]
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    value: ValueLesson = world.facts["value"]  # type: ignore[assignment]
    tags = {"attic", "rust", "warning", "space", value.key}
    tags |= set(sign.tags)
    tags |= set(hazard.tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(q, a))
    return out


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.sign not in SIGNS or params.hazard not in HAZARDS:
        raise StoryError("Unknown place, sign, or hazard key.")
    if params.fix not in FIXES or params.value not in VALUES:
        raise StoryError("Unknown fix or value key.")
    place = PLACES[params.place]
    sign = SIGNS[params.sign]
    hazard = HAZARDS[params.hazard]
    fix = FIXES[params.fix]
    value = VALUES[params.value]
    if not sign_matches_hazard(sign, hazard) or not fix_matches_hazard(hazard, fix):
        raise StoryError(explain_rejection(params.place, params.sign, params.hazard, params.fix, params.value))

    world = tell(place, sign, hazard, fix, value)
    if not world.facts.get("path_safe") or not world.facts.get("moral_value_shown"):
        raise StoryError("World failed to reach a safe, value-complete ending.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge_questions(world),
        world=world,
    )


ASP_RULES = r"""
place(P) :- launch_attic(P).
sign(S) :- rusty_sign(S).
hazard(H) :- ladder_hazard(H).
fix(F) :- repair_fix(F).
value(V) :- moral_value(V).

valid(P,S,H,F,V) :-
    place(P), sign(S), hazard(H), fix(F), value(V),
    sign_family(S,X), hazard_family(H,X),
    hazard_need(H,N), fix_need(F,N).

#show valid/5.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for place in PLACES.values():
        rows.append(asp.fact("launch_attic", place.key))
    for sign in SIGNS.values():
        rows.append(asp.fact("rusty_sign", sign.key))
        rows.append(asp.fact("sign_family", sign.key, sign.family))
    for hazard in HAZARDS.values():
        rows.append(asp.fact("ladder_hazard", hazard.key))
        rows.append(asp.fact("hazard_family", hazard.key, hazard.family))
        rows.append(asp.fact("hazard_need", hazard.key, hazard.need))
    for fix in FIXES.values():
        rows.append(asp.fact("repair_fix", fix.key))
        rows.append(asp.fact("fix_need", fix.key, fix.need))
    for value in VALUES.values():
        rows.append(asp.fact("moral_value", value.key))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(tuple(str(x) for x in atom) for atom in asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    for idx, combo in enumerate(sorted(py), start=1):
        sample = generate(StoryParams(*combo, seed=idx))
        lowered = sample.story.lower()
        if "rusty sign" not in lowered:
            print("Generated story missed required seed words for combo:", combo)
            return 1
        if "attic ladder" not in lowered:
            print("Generated story missed attic ladder setting for combo:", combo)
            return 1
        if not any(word in lowered for word in ("captain", "launch", "space", "rocket")):
            print("Generated story drifted away from space-adventure tone for combo:", combo)
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("Generated story missed QA output for combo:", combo)
            return 1
        if not sample.world.facts.get("resolved") or not sample.world.facts.get("moral_value_shown"):
            print("Generated story failed to reach a resolved moral ending for combo:", combo)
            return 1
    print(f"OK: Python and ASP agree on {len(py)} valid attic-ladder space-adventure stories, and all generated stories pass basic checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Storyworld: rusty-sign attic-ladder space adventure with a twist and moral value."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--sign", choices=sorted(SIGNS))
    parser.add_argument("--hazard", choices=sorted(HAZARDS))
    parser.add_argument("--fix", choices=sorted(FIXES))
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
        and (args.fix is None or combo[3] == args.fix)
        and (args.value is None or combo[4] == args.value)
    ]
    if not choices:
        place_key = args.place or sorted(PLACES)[0]
        sign_key = args.sign or sorted(SIGNS)[0]
        hazard_key = args.hazard or sorted(HAZARDS)[0]
        fix_key = args.fix or sorted(FIXES)[0]
        value_key = args.value or sorted(VALUES)[0]
        raise StoryError(explain_rejection(place_key, sign_key, hazard_key, fix_key, value_key))
    place_key, sign_key, hazard_key, fix_key, value_key = rng.choice(sorted(choices))
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(place_key, sign_key, hazard_key, fix_key, value_key, seed=seed)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("STORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("WORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        base_seed = args.seed if args.seed is not None else 1000
        return [
            generate(StoryParams(*combo, seed=base_seed + idx))
            for idx, combo in enumerate(valid_combos(), start=1)
        ]

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    seen: set[str] = set()
    samples: list[StorySample] = []
    attempts = 0
    i = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed), index=i)
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique attic-ladder space-adventure stories with the requested constraints.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, start=1):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"=== place={p.place} sign={p.sign} hazard={p.hazard} "
                f"fix={p.fix} value={p.value} seed={p.seed} ==="
            )
        elif len(samples) > 1:
            header = (
                f"=== rusty_sign_attic_ladder_twist_moral_value_3 "
                f"#{idx} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
