#!/usr/bin/env python3
"""
storyworlds/worlds/rusty_sign_attic_ladder_twist_moral_value_4.py
=================================================================

Standalone storyworld for a TinyStories-style seed:

    Words: rusty sign
    Setting: attic ladder
    Features: Twist, Moral Value
    Style: Space Adventure

Internal source tale:
    A child turns an attic ladder into a launch tower for a pretend space
    mission. A rusty sign beside the ladder looks like a secret astronaut
    puzzle, so the child almost rushes upward. The twist is that the sign is
    not a treasure clue at all. It is an old safety warning that points to a
    real problem on the ladder, and the useful repair item is hidden behind the
    sign. When the crew slows down, fixes the danger, and then climbs, the
    mission succeeds because careful courage beats hurried pretending.
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
    ladder_label: str
    attic_label: str
    goal: str
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
    hidden_item: str
    reveal_image: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class LadderHazard:
    key: str
    family: str
    need: str
    cue_text: str
    discovery_text: str
    risk_text: str
    repaired_image: str
    base_safety: float
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepairFix:
    key: str
    need: str
    tool_text: str
    action_text: str
    proof_text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MoralValue:
    key: str
    virtue: str
    decision_line: str
    helper_line: str
    sharing_line: str
    closing_line: str
    tags: tuple[str, ...] = ()


@dataclass
class StoryParams:
    place: str
    sign: str
    hazard: str
    fix: str
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
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class World:
    params: StoryParams
    place: LaunchPlace
    sign: RustySign
    hazard: LadderHazard
    fix: RepairFix
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, key: str, **details: str) -> None:
        item = {"event": key}
        item.update({name: str(value) for name, value in details.items()})
        self.history.append(item)

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in paragraph if part) for paragraph in self.paragraphs if paragraph)

    def trace(self) -> str:
        lines = [
            "--- world ---",
            f"place={self.place.key}",
            f"sign={self.sign.key}",
            f"hazard={self.hazard.key}",
            f"fix={self.fix.key}",
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
        for item in self.history:
            lines.append(f"  - {item}")
        return "\n".join(lines)


PLACES: dict[str, LaunchPlace] = {
    "comet_platform": LaunchPlace(
        key="comet_platform",
        house_name="the Marigold house",
        ladder_label="the attic ladder",
        attic_label="the comet platform under the rafters",
        goal="a cardboard star chart clipped beside a silver fan that served as mission control",
        opening_image="The attic ladder hung from the ceiling like a launch tower waiting for its crew.",
        ending_image="The safe rungs rose to the comet platform while a paper moon turned in the attic breeze.",
        tags=("attic", "space", "ladder"),
    ),
    "orbit_nook": LaunchPlace(
        key="orbit_nook",
        house_name="the Juniper cottage",
        ladder_label="the attic ladder",
        attic_label="the orbit nook above the hall",
        goal="a milk-crate cockpit with sticker planets taped around a round window",
        opening_image="Above the hallway, the attic ladder looked like a silver bridge to orbit.",
        ending_image="Moonlight washed the orbit nook, and the ladder stood firm like a little rocket gantry.",
        tags=("attic", "orbit", "window"),
    ),
    "nebula_deck": LaunchPlace(
        key="nebula_deck",
        house_name="the Clover home",
        ladder_label="the attic ladder",
        attic_label="the nebula deck near the roof beam",
        goal="a toy telescope aimed at glow-star stickers and a map of make-believe planets",
        opening_image="The attic ladder pointed into the dim ceiling like a path toward a private nebula.",
        ending_image="At the top, the telescope gleamed while the repaired ladder rested as calmly as a docked ship.",
        tags=("attic", "telescope", "stars"),
    ),
}


SIGNS: dict[str, RustySign] = {
    "pin_warning": RustySign(
        key="pin_warning",
        family="rung",
        paint_words="CHECK PIN BEFORE BLASTOFF",
        misread_text="a launch code that seemed to promise a secret astronaut door",
        true_meaning="the fourth rung had a slipping pin and needed care before anyone climbed higher",
        hidden_item="a bright cotter pin taped to the back of the sign",
        reveal_image="When the sign swung open, the spare pin flashed like a tiny silver comet.",
        tags=("rung", "pin", "warning"),
    ),
    "hatch_warning": RustySign(
        key="hatch_warning",
        family="hatch",
        paint_words="LOCK HATCH FOR ORBIT",
        misread_text="an order from an old spaceship captain guarding the attic prize",
        true_meaning="the attic hatch could flap shut unless its hook was fastened first",
        hidden_item="a blue cord loop and a small brass hook tucked behind the sign",
        reveal_image="Behind the rusty sign waited a neat loop of blue cord like a sleeping rocket tail.",
        tags=("hatch", "hook", "warning"),
    ),
    "rail_warning": RustySign(
        key="rail_warning",
        family="rail",
        paint_words="GLOVE UP FOR STARBOARD RAIL",
        misread_text="a clue about astronaut gloves hidden near a starboard control panel",
        true_meaning="the right rail still had rough splinters and needed smoothing before a small hand slid along it",
        hidden_item="a strip of sanding cloth and a roll of silver tape hidden behind the sign",
        reveal_image="The back of the sign held smooth silver tape and sanding cloth like careful supplies from a ship locker.",
        tags=("rail", "splinter", "warning"),
    ),
}


HAZARDS: dict[str, LadderHazard] = {
    "loose_rung": LadderHazard(
        key="loose_rung",
        family="rung",
        need="pin_fix",
        cue_text="The middle of the attic ladder gave a quick clink when {hero} planted one sneaker on it.",
        discovery_text="A metal pin had crept halfway out of the fourth rung, leaving the step shaky in its socket.",
        risk_text="One fast leap could have rolled a foot sideways and sent the captain thumping down the ladder.",
        repaired_image="After the new pin clicked into place, the rung held still and strong.",
        base_safety=0.42,
        tags=("rung", "pin", "ladder"),
    ),
    "swinging_hatch": LadderHazard(
        key="swinging_hatch",
        family="hatch",
        need="hook_fix",
        cue_text="The open hatch above the attic ladder bumped the frame with a hollow bop each time the ladder moved.",
        discovery_text="The old hook that should have held the hatch open was missing, so the wooden door kept drifting back.",
        risk_text="A closing hatch could have startled the crew and pinched fingers right at the top of the climb.",
        repaired_image="Once the cord and hook were set, the hatch stayed open like a friendly air-lock door.",
        base_safety=0.45,
        tags=("hatch", "hook", "attic"),
    ),
    "splinter_rail": LadderHazard(
        key="splinter_rail",
        family="rail",
        need="tape_fix",
        cue_text="{hero}'s hand brushed the rail, and the wood scratched with a dry little hiss.",
        discovery_text="The right rail had a torn patch where a splinter stuck out like a jagged tooth.",
        risk_text="A rushing hand could have been scraped open, and the sting might have made the climber slip.",
        repaired_image="After sanding and taping, the rail felt smooth enough for a steady climb.",
        base_safety=0.48,
        tags=("rail", "splinter", "hand"),
    ),
}


FIXES: dict[str, RepairFix] = {
    "new_pin": RepairFix(
        key="new_pin",
        need="pin_fix",
        tool_text="the spare cotter pin from behind the sign",
        action_text="{helper} held the rung steady while {hero} slid the new pin through the bracket and bent its ends flat.",
        proof_text="The rung answered with a firm click instead of a wobble.",
        tags=("pin", "repair"),
    ),
    "hook_loop": RepairFix(
        key="hook_loop",
        need="hook_fix",
        tool_text="the blue cord and brass hook hidden behind the sign",
        action_text="{hero} threaded the cord through the hook, and {helper} fastened it so the hatch could stay open.",
        proof_text="The hatch stopped drifting and waited quietly overhead.",
        tags=("hook", "repair"),
    ),
    "silver_tape": RepairFix(
        key="silver_tape",
        need="tape_fix",
        tool_text="the sanding cloth and silver tape tucked behind the sign",
        action_text="{hero} rubbed the splinter smooth, then {helper} wrapped the rail with silver tape until it felt gentle.",
        proof_text="The rail no longer scratched at small fingers.",
        tags=("tape", "repair"),
    ),
}


VALUES: dict[str, MoralValue] = {
    "careful_courage": MoralValue(
        key="careful_courage",
        virtue="careful courage",
        decision_line="{hero} wanted to race like a rocket, but real captains check danger before they blast off.",
        helper_line="{helper} said brave explorers use their eyes as much as their boots.",
        sharing_line="Before climbing, the crew read the sign aloud so the next explorer would know the truth too.",
        closing_line="{hero} learned that careful courage shines brighter than pretending not to notice a warning.",
        tags=("moral", "courage"),
    ),
    "patient_truth": MoralValue(
        key="patient_truth",
        virtue="patient truth",
        decision_line="Instead of keeping the clue as a secret game, {hero} stopped to find out what the sign truly meant.",
        helper_line="{helper} smiled and said the truth is often quieter than a grand guess, but far more useful.",
        sharing_line="After the repair, they told the whole family what the rusty sign had really been trying to say.",
        closing_line="{hero} learned that patient truth can save a mission before trouble begins.",
        tags=("moral", "truth"),
    ),
    "shared_responsibility": MoralValue(
        key="shared_responsibility",
        virtue="shared responsibility",
        decision_line="{hero} saw that a space crew is strongest when one person spots danger and another helps fix it.",
        helper_line="{helper} reminded {hero} that looking after a ladder also means looking after everyone who will climb it later.",
        sharing_line="Together they left the repair in place and hung the sign where every future captain could read it.",
        closing_line="{hero} learned that shared responsibility turns a risky climb into a safe adventure for the whole crew.",
        tags=("moral", "teamwork"),
    ),
}


HEROES = ("Nova", "Mira", "Jules", "Tobin", "Ivy", "Nico")
HELPERS = ("Aunt Sol", "Grandpa Reed", "Mama", "Cousin Bea")
MISSION_TITLES = ("captain", "pilot", "scout", "navigator")


def valid_combo(place_key: str, sign_key: str, hazard_key: str, fix_key: str, value_key: str) -> bool:
    if place_key not in PLACES or sign_key not in SIGNS or hazard_key not in HAZARDS or fix_key not in FIXES or value_key not in VALUES:
        return False
    sign = SIGNS[sign_key]
    hazard = HAZARDS[hazard_key]
    fix = FIXES[fix_key]
    return sign.family == hazard.family and hazard.need == fix.need


def explain_rejection(place_key: str, sign_key: str, hazard_key: str, fix_key: str, value_key: str) -> str:
    if place_key not in PLACES:
        return f"No story: unknown place {place_key!r}."
    if sign_key not in SIGNS:
        return f"No story: unknown rusty sign {sign_key!r}."
    if hazard_key not in HAZARDS:
        return f"No story: unknown ladder hazard {hazard_key!r}."
    if fix_key not in FIXES:
        return f"No story: unknown repair fix {fix_key!r}."
    if value_key not in VALUES:
        return f"No story: unknown moral value {value_key!r}."
    sign = SIGNS[sign_key]
    hazard = HAZARDS[hazard_key]
    fix = FIXES[fix_key]
    if sign.family != hazard.family:
        return (
            f"No story: sign {sign_key!r} points to a {sign.family} problem, "
            f"but hazard {hazard_key!r} is a {hazard.family} problem."
        )
    if hazard.need != fix.need:
        return (
            f"No story: hazard {hazard_key!r} needs {hazard.need!r}, "
            f"but fix {fix_key!r} provides {fix.need!r}."
        )
    return "No story: the selected options do not form a reasonable attic-ladder mission."


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_key in sorted(PLACES):
        for sign_key in sorted(SIGNS):
            for hazard_key in sorted(HAZARDS):
                for fix_key in sorted(FIXES):
                    for value_key in sorted(VALUES):
                        if valid_combo(place_key, sign_key, hazard_key, fix_key, value_key):
                            combos.append((place_key, sign_key, hazard_key, fix_key, value_key))
    return combos


def _pick_names(seed: int | None) -> tuple[str, str, str]:
    rng = random.Random(seed if seed is not None else 0)
    hero = rng.choice(HEROES)
    helper = rng.choice(HELPERS)
    title = rng.choice(MISSION_TITLES)
    return hero, helper, title


def _build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.sign, params.hazard, params.fix, params.value):
        raise StoryError(explain_rejection(params.place, params.sign, params.hazard, params.fix, params.value))

    world = World(
        params=params,
        place=PLACES[params.place],
        sign=SIGNS[params.sign],
        hazard=HAZARDS[params.hazard],
        fix=FIXES[params.fix],
        value=VALUES[params.value],
    )
    hero_name, helper_name, mission_title = _pick_names(params.seed)
    hero = world.add(
        Entity(
            id="hero",
            kind="person",
            type="child",
            label=hero_name,
            location="hallway",
            role="hero",
            traits=["imaginative", "eager", "kind"],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="person",
            type="adult",
            label=helper_name,
            location="hallway",
            role="helper",
            traits=["calm", "watchful", "helpful"],
        )
    )
    ladder = world.add(
        Entity(
            id="ladder",
            kind="object",
            type="ladder",
            label=world.place.ladder_label,
            location="hallway ceiling",
            role="ladder",
            attrs={"attic": world.place.attic_label},
        )
    )
    sign = world.add(
        Entity(
            id="sign",
            kind="object",
            type="sign",
            label="rusty sign",
            location="ladder frame",
            role="sign",
            attrs={"paint_words": world.sign.paint_words},
        )
    )
    ladder.meters["safety"] = world.hazard.base_safety
    ladder.meters["height"] = 2.4
    sign.meters["rust"] = 0.81
    hero.memes["wonder"] = 0.9
    hero.memes["care"] = 0.35
    hero.memes["haste"] = 0.8
    helper.memes["care"] = 0.95
    world.facts.update(
        {
            "hero": hero.label,
            "helper": helper.label,
            "mission_title": mission_title,
            "goal": world.place.goal,
            "sign_words": world.sign.paint_words,
            "twist": world.sign.true_meaning,
            "hidden_item": world.sign.hidden_item,
            "risk": world.hazard.risk_text,
            "virtue": world.value.virtue,
            "resolved": False,
            "twist_revealed": False,
            "moral_value_shown": False,
        }
    )
    world.event("setup", hero=hero.label, helper=helper.label, mission=mission_title, goal=world.place.goal)
    return world


def _play_story(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    ladder = world.entities["ladder"]
    sign = world.entities["sign"]
    cue_text = world.hazard.cue_text.format(hero=hero.label, helper=helper.label)
    decision_line = world.value.decision_line.format(hero=hero.label, helper=helper.label)
    helper_line = world.value.helper_line.format(hero=hero.label, helper=helper.label)
    fix_action = world.fix.action_text.format(hero=hero.label, helper=helper.label)
    closing_line = world.value.closing_line.format(hero=hero.label, helper=helper.label)

    world.say(
        f"In {world.place.house_name}, {hero.label} called {world.place.ladder_label} the launch tower to {world.place.attic_label}."
    )
    world.say(world.place.opening_image)
    world.say(
        f"At the top waited {world.place.goal}, so {hero.label} marched over as the day's {world.facts['mission_title']}."
    )
    world.event("mission_named", place=world.place.key, goal=str(world.facts["goal"]))
    world.para()

    world.say(
        f"Beside the first rung hung a rusty sign stamped with {world.sign.paint_words!r}."
    )
    world.say(
        f"To {hero.label}, it looked like {world.sign.misread_text}."
    )
    world.say(decision_line)
    hero.memes["wonder"] += 0.2
    hero.memes["haste"] += 0.15
    world.event("misread_sign", guess=world.sign.misread_text, words=world.sign.paint_words)

    world.say(cue_text)
    world.say(world.hazard.discovery_text)
    hero.memes["fear"] += 0.35
    hero.memes["care"] += 0.3
    world.event("hazard_found", cue=cue_text, problem=world.hazard.discovery_text)
    world.para()

    world.say(
        f"{helper.label} touched the rusty sign and read it slowly. The twist was simple and important: the sign was not a secret riddle at all."
    )
    world.say(
        f"It really meant that {world.sign.true_meaning}."
    )
    world.say(world.sign.reveal_image)
    world.say(
        f"Behind it they found {world.sign.hidden_item}, exactly what the crew needed."
    )
    sign.memes["warning"] = 1.0
    world.facts["twist_revealed"] = True
    world.event("twist_revealed", meaning=world.sign.true_meaning, hidden_item=world.sign.hidden_item)

    world.say(helper_line)
    world.say(world.hazard.risk_text)
    world.event("risk_named", risk=world.hazard.risk_text)
    world.para()

    world.say(f"Using {world.fix.tool_text}, they fixed the problem together.")
    world.say(fix_action)
    world.say(world.fix.proof_text)
    world.say(world.hazard.repaired_image)
    ladder.meters["safety"] = 0.97
    hero.memes["haste"] = 0.15
    hero.memes["care"] = 1.0
    hero.memes["responsibility"] = 0.9
    world.event("repair", tool=world.fix.tool_text, action=world.fix.action_text, proof=world.fix.proof_text)

    world.say(world.value.sharing_line)
    world.event("share_warning", action=world.value.sharing_line)
    world.para()

    hero.location = world.place.attic_label
    helper.location = world.place.attic_label
    world.say(
        f"Only then did {hero.label} climb the attic ladder, one steady step at a time, and reach {world.place.goal}."
    )
    world.say(
        f"The mission felt even more like a space adventure because the crew had made the launch tower safe before blastoff."
    )
    world.say(world.place.ending_image)
    world.say(closing_line)
    world.facts["resolved"] = True
    world.facts["moral_value_shown"] = True
    world.facts["final_image"] = world.place.ending_image
    world.event("resolution", ending=world.place.ending_image, moral=closing_line)


def _prompts(world: World) -> list[str]:
    hero = str(world.facts["hero"])
    return [
        (
            "Write a child-facing Space Adventure story in a real house where "
            f"{hero} treats an attic ladder like a launch tower and notices a rusty sign."
        ),
        (
            "Keep the twist grounded: the sign should look mysterious first, then prove to be a practical warning "
            f"about the {world.hazard.family} on the ladder."
        ),
        (
            "End with a clear moral value about "
            f"{world.value.virtue} and an image that shows the climb became safe."
        ),
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = str(world.facts["hero"])
    helper = str(world.facts["helper"])
    stop_reason = {
        "rung": f"the ladder gave a warning clink under {hero}'s foot",
        "hatch": "the hatch above the ladder kept bumping and drifting back",
        "rail": f"the rail scratched at {hero}'s hand instead of feeling smooth",
    }[world.hazard.family]
    return [
        QAItem(
            question="Why did the crew stop before climbing the attic ladder?",
            answer=(
                f"They stopped because {stop_reason}. "
                f"{world.hazard.discovery_text} {world.hazard.risk_text}"
            ),
        ),
        QAItem(
            question="What was the twist about the rusty sign?",
            answer=(
                f"At first {hero} thought the rusty sign was {world.sign.misread_text}. "
                f"The twist was that it was really warning the crew that {world.sign.true_meaning}."
            ),
        ),
        QAItem(
            question="How did they make the launch tower safe?",
            answer=(
                f"They found the needed repair item behind the sign and used {world.fix.tool_text}. "
                f"{world.fix.action_text.format(hero=hero, helper=helper)} {world.fix.proof_text}"
            ),
        ),
        QAItem(
            question="What moral did the mission teach?",
            answer=(
                f"The mission taught {world.value.virtue}. "
                f"{world.value.closing_line.format(hero=hero, helper=helper)}"
            ),
        ),
        QAItem(
            question=f"How did {helper} help {hero}?",
            answer=(
                f"{helper} helped by reading the sign carefully and treating it as a real warning instead of part of the game. "
                f"That gave {hero} time to fix the danger before climbing."
            ),
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a warning sign matter even during pretend space play?",
            answer=(
                "Pretend play does not erase a real ladder, hatch, or rail. "
                "A warning sign can point to a physical risk that needs care before the game continues."
            ),
        ),
        QAItem(
            question="What made this attic ladder safer by the end of the story?",
            answer=(
                f"The crew matched the real problem to the right repair and raised the ladder's safety from a shaky state to a steady one. "
                f"In this world, that meant fixing the {world.hazard.family} problem instead of hurrying past it."
            ),
        ),
        QAItem(
            question="Why is slowing down a brave choice here?",
            answer=(
                "Slowing down kept the captain from confusing excitement with skill. "
                f"It protected the mission and gave the crew a way to show {world.value.virtue} in action."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    _play_story(world)
    story = world.render()
    lowered = story.lower()
    if "rusty sign" not in lowered:
        raise StoryError("Generated story missed the required seed words 'rusty sign'.")
    if "attic ladder" not in lowered:
        raise StoryError("Generated story missed the required setting phrase 'attic ladder'.")
    if not any(word in lowered for word in ("space adventure", "launch", "rocket", "orbit", "captain")):
        raise StoryError("Generated story drifted away from the requested Space Adventure style.")
    if not world.facts.get("resolved") or not world.facts.get("moral_value_shown"):
        raise StoryError("World did not reach a resolved moral ending.")
    return StorySample(
        params=params,
        story=story,
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
place(P) :- launch_place(P).
sign(S) :- rusty_sign(S).
hazard(H) :- ladder_hazard(H).
fix(F) :- repair_fix(F).
value(V) :- moral_value(V).

valid(P,S,H,F,V) :-
    place(P),
    sign(S),
    hazard(H),
    fix(F),
    value(V),
    sign_family(S,X),
    hazard_family(H,X),
    hazard_need(H,N),
    fix_need(F,N).

ok :- chosen(P,S,H,F,V), valid(P,S,H,F,V).

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
    for fix in FIXES.values():
        rows.append(fact("repair_fix", fix.key))
        rows.append(fact("fix_need", fix.key, fix.need))
    for value in VALUES.values():
        rows.append(fact("moral_value", value.key))
    if params is not None:
        rows.append(fact("chosen", params.place, params.sign, params.hazard, params.fix, params.value))
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
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"Generated sample omitted prompts or QA for combo {combo!r}.")
        if not sample.world or not sample.world.facts.get("twist_revealed"):
            raise StoryError(f"Generated sample never reached the twist for combo {combo!r}.")

    invalid = StoryParams("comet_platform", "pin_warning", "splinter_rail", "silver_tape", "careful_courage", seed=999)
    if valid_combo(invalid.place, invalid.sign, invalid.hazard, invalid.fix, invalid.value):
        raise StoryError("Internal verify bug: invalid combo unexpectedly passed Python gate.")
    if asp_accepts(invalid):
        raise StoryError("ASP accepted an invalid combo that mismatched sign and hazard families.")

    return f"OK: Python and ASP agree on {len(py)} valid space-attic stories, and each generated story passes core checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Storyworld: rusty-sign attic-ladder Space Adventure with a twist and moral value."
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
    combo = rng.choice(sorted(choices))
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(*combo, seed=seed)


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
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
                label = f"### {params.place} / {params.sign} / {params.hazard} / {params.fix} / {params.value}"
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
