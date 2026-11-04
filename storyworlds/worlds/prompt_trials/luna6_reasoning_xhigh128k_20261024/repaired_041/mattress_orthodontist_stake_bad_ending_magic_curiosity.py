#!/usr/bin/env python3
"""
A small, heartwarming storyworld about a magical mattress at an orthodontist's
family camp-in. Curiosity helps the children notice what the mattress is doing,
and a wooden tent stake helps them choose a safe way to keep it from drifting.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while not os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
    parent = os.path.dirname(ROOT)
    if parent == ROOT:
        raise RuntimeError("Could not find storyworlds/results.py")
    ROOT = parent
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "the clinic's family camp-in"
FEATURES = ("bad_ending", "magic", "curiosity")

HERO_NAMES = ("Iris", "Luna", "Mina", "Tavi", "Nell", "Rafi")
FRIEND_NAMES = ("Theo", "Milo", "June", "Ari", "Kit", "Ollie")
ORTHODONTIST_NAMES = ("Asha", "Lin", "Vale", "Rao", "Kim", "Noor")


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("wear", "warmth", "height", "drift", "secure", "depth", "looseness", "open", "glow", "visible", "swing"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "trust", "joy", "courage", "comfort", "teamwork", "wonder", "care"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Iris"
    friend: str = "Theo"
    orthodontist: str = "Asha"
    case: int = 0
    telling_mode: int = 0
    curiosity_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    key: str
    hazard: str
    clue: str
    false_lead: str
    worry: str
    doctor_reply: str
    repair: str
    proof: str
    ending: str
    gate_open: bool = True
    includes: tuple[str, ...] = ("mattress", "orthodontist", "stake")
    features: tuple[str, ...] = FEATURES
    method: str = "shelter_stake"
    outcome: str = "heartwarming"
    avoids: tuple[str, ...] = ("bad_ending",)


CASES = [
    Case(
        key="loose_flap",
        hazard="A gust lifted the canvas flap, and the blue mattress floated toward the open garden gate.",
        clue="the silver moon patch turned toward {friend}, while the paper lantern's tassel streamed toward the gate",
        false_lead="The lantern's wild dance made the wind seem like the only answer.",
        worry="I'm afraid tomorrow's adjustment will hurt.",
        doctor_reply="I can explain each step, and we can pause whenever you need. If anything hurts, tell me so I can help.",
        repair="reset the leaning wooden stake in the garden bed and latched the gate",
        proof="the flap stayed tucked in even when the lantern swung",
        ending="The silver moon lay flat beside the appointment card, and the latched gate stayed still in the lantern glow.",
    ),
    Case(
        key="soft_soil",
        hazard="Rain had softened the soil around the wooden stake, and the mattress slid toward the open garden gate.",
        clue="the mattress turned toward {friend} each time the rain grew quiet, though the canvas still fluttered toward the gate",
        false_lead="Pattering drops on the shelter made a gust seem responsible for every movement.",
        worry="I won't know how to clean around all the wires.",
        doctor_reply="I'll show you one small brushing step at a time, and we can practice together.",
        repair="moved the shelter away from the dripping gutter, looped the flap around the stake, and latched the gate",
        proof="the canvas stayed dry and the mattress no longer edged toward the path",
        ending="A little moonlight rested on the dry blue mattress while the canvas held snug against its stake.",
    ),
    Case(
        key="swinging_gate",
        hazard="The garden gate latch clicked loose just as the mattress lifted and drifted toward the opening.",
        clue="the moon patch kept facing {friend}, even when the gate swung away in the breeze",
        false_lead="The creaking gate sounded so mysterious that it seemed to be pulling the mattress along.",
        worry="Everyone at school will notice my braces.",
        doctor_reply="A new change can take time to get used to. We can talk about what to say, and you can tell me what feels hard.",
        repair="set the wooden stake firmly beside the shelter and clicked the gate latch closed",
        proof="the gate stayed shut through another soft gust, and the mattress rested inside",
        ending="The moon patch shone beside the appointment card, and the quiet gate framed a safe little camp.",
    ),
    Case(
        key="tapping_branch",
        hazard="A low branch tapped the shelter and tugged its flap loose from the wooden stake.",
        clue="the mattress paused whenever {friend} spoke, then turned toward them when the branch went still",
        false_lead="The branch's shifting shadow made it look as if something outside were chasing the mattress.",
        worry="I miss biting crunchy apples.",
        doctor_reply="I'll show you how to cut apples safely and which hard foods are best to avoid while your braces are on.",
        repair="retied the flap to the wooden stake, moved the shelter beyond the branch's reach, and latched the gate",
        proof="the branch could no longer tug the canvas, and the mattress stayed on its blanket",
        ending="Under the lantern, a small apple slice sat by the appointment card and the moon patch rested quietly.",
    ),
    Case(
        key="snagged_cord",
        hazard="The lantern cord snagged the canvas loop and pulled the wooden stake sideways as the mattress began to drift.",
        clue="the silver moon glowed each time {friend} sighed, though the lantern cord only moved when the wind blew",
        false_lead="The swaying lantern made its cord look like the mattress's only guide.",
        worry="I'm worried my smile won't look like me.",
        doctor_reply="Braces are tools, not a new person. Your questions and comfort matter, and we can talk through both.",
        repair="unhooked the lantern cord, secured the canvas loop to the wooden stake, and latched the gate",
        proof="the lantern swung freely without catching the canvas, and the mattress stayed whole",
        ending="The appointment card glimmered beneath the moon patch, while the free lantern cord made a gentle circle of light.",
    ),
    Case(
        key="busy_path",
        hazard="Footsteps shook the little shelter, loosening its wooden stake while the garden gate stood open.",
        clue="the mattress drifted toward {friend} even when everyone else crossed the path in the opposite direction",
        false_lead="The busy camp-in path made it easy to blame every wobble on passing feet.",
        worry="I can't remember all the brushing rules.",
        doctor_reply="It is okay to need reminders. I can make a simple brushing plan with you at your visit.",
        repair="cleared the path, reset the wooden stake, and latched the garden gate",
        proof="the shelter stopped wobbling when families walked by, and the mattress remained inside",
        ending="The appointment card lay ready for morning beside a moon patch that no longer needed to chase anyone.",
    ),
    Case(
        key="gutter_drip",
        hazard="A gutter drip softened the earth beside the wooden stake, and the mattress edged toward the garden gate.",
        clue="the moon patch glowed when {friend} looked at the appointment card, then dimmed when they looked away",
        false_lead="The gutter's plinks sounded like a steady little drum urging the mattress onward.",
        worry="I worry my speech will sound funny with braces.",
        doctor_reply="Some mouths take time to adjust. We can check what feels different, and you can practice at your own pace.",
        repair="moved the shelter to a dry patch, set the wooden stake firmly, and latched the gate",
        proof="the ground beneath the stake stayed firm, and the mattress did not slide toward the path",
        ending="The appointment card rested in the moonlight while the dry shelter held fast beside the garden gate.",
    ),
    Case(
        key="windward_flap",
        hazard="A late gust pulled the canvas door free from its wooden stake, and the mattress rose toward the open gate.",
        clue="the mattress rose with {friend}'s quiet sigh and lowered a little whenever they smiled",
        false_lead="The flapping canvas made the wind seem to be carrying the mattress away.",
        worry="I'm scared to ask questions during my appointment.",
        doctor_reply="Questions belong in an appointment. You can bring them on a card or ask me to pause while you speak.",
        repair="tied the canvas door back to the wooden stake and latched the garden gate",
        proof="the door stayed in place through the next breeze, and the mattress settled safely inside",
        ending="The appointment card waited in the lantern glow while the blue mattress made a calm, moonlit bed.",
    ),
]


OPENINGS = [
    "At the clinic's family camp-in, orthodontist Dr. {orthodontist} welcomed {hero} and {friend} to the enclosed courtyard. Their families were nearby, and {friend} had a braces check the next morning.",
    "The clinic garden was full of little tents for its family camp-in. Orthodontist Dr. {orthodontist} checked the shelter where {hero} and {friend} planned to rest before the morning visit.",
    "Orthodontist Dr. {orthodontist} had organized a gentle camp-in in the clinic courtyard. {hero} brought a pillow for {friend}, whose braces appointment was just after sunrise.",
    "As evening settled over the courtyard, Dr. {orthodontist}, the neighborhood orthodontist, made sure {hero} and {friend} had a cozy shelter near their families.",
    "The clinic's annual camp-in was nearly ready. {hero} and {friend} helped orthodontist Dr. {orthodontist} prepare one last shelter for the night before {friend}'s checkup.",
    "At the family camp-in, {hero} and {friend} shared a little canvas shelter while orthodontist Dr. {orthodontist} made the rounds beneath the courtyard lights.",
]

CURIOSITY_QUESTIONS = [
    "If the lantern is streaming toward the gate, why is the mattress turning toward you?",
    "Could we watch it for one whole gust before we decide what to do?",
    "Does the moon patch glow because of the wind, or because you are worried?",
    "What if it isn't trying to leave? What might it be trying to reach?",
]

ENDING_STYLES = [
    "At bedtime, {friend} chose the mattress for a rest, and {hero} settled beside the lantern. {ending}",
    "No one hurried away. {friend} tucked the appointment card close, and the two friends watched the shelter hold steady. {ending}",
    "When the courtyard grew quiet, {friend} lay down by choice, with {hero} keeping company. {ending}",
    "Before sleep, {friend} asked one more question about the morning. Dr. {orthodontist} promised to make time for it. {ending}",
]

CURATED = [
    StoryParams(hero="Iris", friend="Theo", orthodontist="Asha", case=0, telling_mode=0, curiosity_style=0, ending_style=0),
    StoryParams(hero="Luna", friend="Milo", orthodontist="Lin", case=1, telling_mode=1, curiosity_style=1, ending_style=1),
    StoryParams(hero="Mina", friend="June", orthodontist="Vale", case=2, telling_mode=2, curiosity_style=2, ending_style=2),
    StoryParams(hero="Tavi", friend="Ari", orthodontist="Rao", case=3, telling_mode=3, curiosity_style=3, ending_style=3),
    StoryParams(hero="Nell", friend="Kit", orthodontist="Kim", case=4, telling_mode=4, curiosity_style=0, ending_style=1),
    StoryParams(hero="Rafi", friend="Ollie", orthodontist="Noor", case=5, telling_mode=5, curiosity_style=1, ending_style=2),
    StoryParams(hero="Iris", friend="June", orthodontist="Lin", case=6, telling_mode=2, curiosity_style=2, ending_style=3),
    StoryParams(hero="Luna", friend="Ari", orthodontist="Asha", case=7, telling_mode=4, curiosity_style=3, ending_style=0),
]


@dataclass
class World:
    hero: Entity
    friend: Entity
    orthodontist: Entity
    mattress: Entity
    shelter: Entity
    stake: Entity
    lantern: Entity
    gate: Entity
    appointment_card: Entity
    moon_patch: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _entity(eid: str, kind: str, type_: str, label: str, location: str = "") -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def _valid_person_name(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 32:
        return False
    if not any(char.isalpha() for char in value):
        return False
    return all(char.isalpha() or char in " -'’" for char in value)


def python_case_valid(case: Case) -> bool:
    return (
        set(case.includes) >= {"mattress", "orthodontist", "stake"}
        and set(case.features) >= set(FEATURES)
        and case.method == "shelter_stake"
        and case.outcome == "heartwarming"
        and "bad_ending" in case.avoids
        and bool(case.hazard)
        and bool(case.clue)
        and bool(case.repair)
    )


def reasonableness_gate(params: StoryParams) -> bool:
    for label, value in (
        ("hero", params.hero),
        ("friend", params.friend),
        ("orthodontist", params.orthodontist),
    ):
        if not _valid_person_name(value):
            raise StoryError(
                f"The {label} name must contain letters and may use spaces, hyphens, or apostrophes."
            )

    names = (params.hero.casefold(), params.friend.casefold(), params.orthodontist.casefold())
    if len(set(names)) != len(names):
        raise StoryError("The child, friend, and orthodontist must have different names.")

    if type(params.case) is not int or not 0 <= params.case < len(CASES):
        raise StoryError(f"Case must be an integer from 0 to {len(CASES) - 1}.")
    if type(params.telling_mode) is not int or not 0 <= params.telling_mode < len(OPENINGS):
        raise StoryError("The selected telling style is not available.")
    if type(params.curiosity_style) is not int or not 0 <= params.curiosity_style < len(CURIOSITY_QUESTIONS):
        raise StoryError("The selected curiosity style is not available.")
    if type(params.ending_style) is not int or not 0 <= params.ending_style < len(ENDING_STYLES):
        raise StoryError("The selected ending style is not available.")

    case = CASES[params.case]
    if not python_case_valid(case):
        raise StoryError("This story needs a mattress, an orthodontist, a stake, magic, curiosity, and a safe ending.")
    return True


def build_world(params: StoryParams) -> World:
    case = CASES[params.case]
    hero = _entity(params.hero, "character", "child", "curious camper", "courtyard")
    friend = _entity(params.friend, "character", "child", "nervous camper", "courtyard")
    orthodontist = _entity(params.orthodontist, "character", "orthodontist", "orthodontist", "courtyard")
    mattress = _entity("mattress", "object", "mattress", "blue mattress", "canvas shelter")
    shelter = _entity("shelter", "place", "tent", "canvas shelter", "courtyard")
    stake = _entity("stake", "object", "tent stake", "wooden tent stake", "garden bed")
    lantern = _entity("lantern", "object", "lantern", "paper lantern", "courtyard")
    gate = _entity("gate", "place", "gate", "garden gate", "courtyard")
    appointment_card = _entity("appointment_card", "object", "card", "appointment card", "friend's pocket")
    moon_patch = _entity("moon_patch", "object", "charm", "silver moon patch", "mattress corner")

    hero.memes["curiosity"] = 1.0
    hero.memes["wonder"] = 0.4
    friend.memes["worry"] = 2.5
    friend.memes["trust"] = 0.4
    orthodontist.memes["care"] = 1.0
    orthodontist.memes["trust"] = 0.8

    mattress.meters.update({"height": 0.7, "drift": 0.75, "wear": 0.0, "warmth": 0.4})
    shelter.meters.update({"open": 1.0, "secure": 0.1})
    stake.meters.update({"depth": 0.25, "looseness": 0.85})
    lantern.meters["swing"] = 0.8
    gate.meters["open"] = 1.0 if case.gate_open else 0.0
    appointment_card.meters["visible"] = 0.0
    moon_patch.meters["glow"] = 0.2

    world = World(
        hero=hero,
        friend=friend,
        orthodontist=orthodontist,
        mattress=mattress,
        shelter=shelter,
        stake=stake,
        lantern=lantern,
        gate=gate,
        appointment_card=appointment_card,
        moon_patch=moon_patch,
    )
    world.facts.update(
        theme=THEME,
        case=case,
        bad_ending_risk=0.8,
        resolved=False,
        magic_confirmed=False,
        bad_ending_avoided=False,
        initial_gate_open=case.gate_open,
    )
    return world


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = build_world(params)
    hero = world.hero
    friend = world.friend
    doctor = world.orthodontist
    mattress = world.mattress
    case = CASES[params.case]

    opening = OPENINGS[params.telling_mode].format(
        hero=hero.id,
        friend=friend.id,
        orthodontist=doctor.id,
    )
    world.say(opening)
    world.say(
        f"The blue mattress came from the clinic's quiet room. Its silver moon patch had been stitched "
        f"by Dr. {doctor.id}'s grandmother, who used to say that a soft place could make a worry easier to share."
    )

    world.para()
    world.say(case.hazard)
    world.say(f"One small detail stood out: {case.clue.format(friend=friend.id)}. {case.false_lead}")
    world.say(
        f"Curiosity kept {hero.id} from rushing after the floating bed. {hero.id} watched the canvas, "
        f"the lantern, and {friend.id}'s face instead."
    )

    world.para()
    world.say(
        f"{friend.id} picked up the loose wooden stake. 'Could I use this to hold the mattress down?' "
        f"{friend.id} asked."
    )
    world.say(
        f"'Not against the mattress,' Dr. {doctor.id} replied. 'That could tear its old cover—a bad ending "
        f"for our cozy camp-in. A stake belongs in the ground. Let's secure the shelter instead.'"
    )
    world.say(
        f"'{CURIOSITY_QUESTIONS[params.curiosity_style]}' {hero.id} asked. "
        f"{friend.id} looked at the silver patch. 'I thought it was the wind, but it keeps turning when I go quiet.'"
    )
    world.say(
        f"'My grandmother called that patch a listening charm,' Dr. {doctor.id} said. "
        f"'I thought she meant it as a story. Maybe its magic really does carry comfort toward a worry.'"
    )

    world.para()
    world.say(f"{friend.id} took a breath. '{case.worry}'")
    world.say(f"'Thank you for telling me,' Dr. {doctor.id} said. '{case.doctor_reply}'")
    world.say(
        f"The silver thread shimmered, and the mattress sank a little. Its gentle magic had been carrying "
        f"a soft place toward {friend.id}, not trying to run away."
    )
    mattress.meters["height"] = 0.3
    mattress.meters["drift"] = 0.3
    world.moon_patch.meters["glow"] = 0.9
    world.facts["magic_confirmed"] = True

    world.para()
    world.say(
        f"While the mattress hovered just above the blanket, Dr. {doctor.id} secured the shelter. "
        f"With {hero.id} and {friend.id} keeping the canvas clear, Dr. {doctor.id} {case.repair}."
    )
    world.say(f"They tested the shelter: {case.proof}.")
    world.say(
        f"The mattress floated down onto the dry blanket without a tear. {friend.id} took the appointment "
        f"card from a pocket and set it beside the bed."
    )
    world.say(
        f"'I'll bring my questions tomorrow,' {friend.id} said. 'And I will make time to answer,' "
        f"Dr. {doctor.id} promised."
    )

    world.para()
    ending = case.ending.format(friend=friend.id)
    world.say(
        ENDING_STYLES[params.ending_style].format(
            friend=friend.id,
            hero=hero.id,
            orthodontist=doctor.id,
            ending=ending,
        )
    )

    mattress.meters.update({"height": 0.0, "drift": 0.0, "wear": 0.0, "warmth": 1.0})
    world.shelter.meters.update({"open": 0.0, "secure": 1.0})
    world.stake.meters.update({"depth": 1.0, "looseness": 0.0})
    world.lantern.meters["swing"] = 0.2
    world.gate.meters["open"] = 0.0
    world.appointment_card.location = "beside the mattress"
    world.appointment_card.meters["visible"] = 1.0
    world.moon_patch.meters["glow"] = 0.65

    hero.memes["curiosity"] += 1.5
    hero.memes["courage"] += 0.8
    hero.memes["teamwork"] += 1.0
    hero.memes["joy"] += 0.7
    friend.memes["worry"] = 0.8
    friend.memes["comfort"] += 1.5
    friend.memes["trust"] += 1.0
    friend.memes["courage"] += 0.8
    friend.memes["teamwork"] += 1.0
    doctor.memes["care"] += 0.5
    doctor.memes["trust"] += 0.4
    doctor.memes["joy"] += 0.4

    world.facts.update(
        resolved=True,
        bad_ending_risk=0.0,
        bad_ending_avoided=True,
        hero=hero,
        friend=friend,
        orthodontist=doctor,
        case_key=case.key,
        hazard=case.hazard,
        clue=case.clue.format(friend=friend.id),
        false_lead=case.false_lead,
        worry=case.worry,
        doctor_reply=case.doctor_reply,
        repair=case.repair,
        proof=case.proof,
        ending=ending,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    doctor = world.facts["orthodontist"]

    return [
        QAItem(
            question="Why did the mattress begin to drift toward the garden gate?",
            answer=(
                f"The mattress was enchanted to move toward someone who needed comfort, and {friend.id} "
                f"was hiding a worry about braces. The loose shelter and open gate made its gentle drifting risky."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} realize the wind was not the whole explanation?",
            answer=(
                f"{hero.id} noticed that {world.facts['clue']}. That detail did not match the lantern and canvas "
                f"moving with the breeze."
            ),
        ),
        QAItem(
            question=f"What did {friend.id} tell Dr. {doctor.id}?",
            answer=(
                f"{friend.id} admitted, \"{world.facts['worry']}\" Dr. {doctor.id} listened and offered "
                f"{world.facts['doctor_reply']}"
            ),
        ),
        QAItem(
            question="How did the campers avoid the bad ending?",
            answer=(
                f"They did not press the wooden stake into the mattress, which could have torn its cover. "
                f"Instead, Dr. {doctor.id} {world.facts['repair']}."
            ),
        ),
        QAItem(
            question="What showed that the problem was truly solved?",
            answer=(
                f"{world.facts['proof']}. The mattress settled onto the blanket with its cover still whole, "
                f"and {friend.id} placed the appointment card beside it."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an orthodontist do?",
            answer=(
                "An orthodontist is a dental specialist who helps teeth and jaws grow into healthier positions, "
                "often using braces or other dental appliances."
            ),
        ),
        QAItem(
            question="What is a tent stake for?",
            answer=(
                "A tent stake is a peg pushed into the ground to help hold a tent or its canvas in place. "
                "It is not meant to be pushed into a mattress."
            ),
        ),
        QAItem(
            question="What is curiosity?",
            answer=(
                "Curiosity is the wish to notice, ask questions, and learn how something works."
            ),
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer=(
                "A bad ending is an outcome where trouble is not put right. In this story, the characters "
                "noticed that danger and chose a safer path instead."
            ),
        ),
        QAItem(
            question="What is a mattress?",
            answer=(
                "A mattress is a soft, padded surface made for resting or sleeping on."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a heartwarming magical story at {THEME}, where an old mattress drifts toward {world.facts['friend'].id}.",
        f"Let curiosity uncover why the mattress moves: {case.clue.format(friend=world.facts['friend'].id)}.",
        "Include an orthodontist, a wooden tent stake, a possible bad ending, kind dialogue, and a safe resolution.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    entities = (
        world.hero,
        world.friend,
        world.orthodontist,
        world.mattress,
        world.shelter,
        world.stake,
        world.lantern,
        world.gate,
        world.appointment_card,
        world.moon_patch,
    )
    for entity in entities:
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        bits = [f"location={entity.location!r}"]
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if entity.carried_by:
            bits.append(f"carried_by={entity.carried_by}")
        if entity.hidden_in:
            bits.append(f"hidden_in={entity.hidden_in}")
        lines.append(f"  {entity.id:18} ({entity.kind:10}) {' '.join(bits)}")
    lines.append(
        "  outcome: "
        f"resolved={world.facts.get('resolved')}, "
        f"bad_ending_avoided={world.facts.get('bad_ending_avoided')}, "
        f"bad_ending_risk={world.facts.get('bad_ending_risk')}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
% Each case must contain the three seed objects and use curiosity to discover
% the mattress's magic. The stake secures the shelter rather than the mattress.
% A bad ending is considered, but the safe route resolves the story warmly.
supported(C) :-
    case(C),
    includes(C, mattress),
    includes(C, orthodontist),
    includes(C, stake),
    feature(C, bad_ending),
    feature(C, magic),
    feature(C, curiosity),
    method(C, shelter_stake).

good_ending(C) :-
    supported(C),
    outcome(C, heartwarming),
    avoids(C, bad_ending).

valid_case(C) :- supported(C), good_ending(C).
selected_valid :- selected_case(C), valid_case(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import

    facts = [
        asp.fact("setting", "orthodontic_camp_in"),
        asp.fact("theme", "heartwarming"),
    ]
    for case in CASES:
        facts.append(asp.fact("case", case.key))
        facts.extend(asp.fact("includes", case.key, item) for item in case.includes)
        facts.extend(asp.fact("feature", case.key, item) for item in case.features)
        facts.append(asp.fact("method", case.key, case.method))
        facts.append(asp.fact("outcome", case.key, case.outcome))
        facts.extend(asp.fact("avoids", case.key, item) for item in case.avoids)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models(show: str):
    import storyworlds.asp as asp  # lazy import

    return asp.one_model(asp_program(show))


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp  # lazy import
    except ImportError as exc:
        print(f"VERIFY ERROR: ASP verification needs clingo: {exc}")
        return 2

    try:
        symbols = asp.one_model(asp_program("#show valid_case/1."))
    except Exception as exc:
        print(f"VERIFY ERROR: ASP could not solve the story rules: {exc}")
        return 2

    asp_cases = {
        str(arguments[0])
        for arguments in asp.atoms(symbols, "valid_case")
    }
    python_cases = {case.key for case in CASES if python_case_valid(case)}
    if asp_cases != python_cases:
        print(f"MISMATCH: Python cases {sorted(python_cases)} differ from ASP cases {sorted(asp_cases)}.")
        return 1

    failures: list[str] = []
    for index, case in enumerate(CASES):
        params = StoryParams(
            hero="Iris",
            friend="Theo",
            orthodontist="Asha",
            case=index,
            telling_mode=index % len(OPENINGS),
            curiosity_style=index % len(CURIOSITY_QUESTIONS),
            ending_style=index % len(ENDING_STYLES),
            seed=9000 + index,
        )
        try:
            python_ok = reasonableness_gate(params)
            selected_symbols = asp.one_model(
                asp_program(f"selected_case({case.key}).\n#show selected_valid/0.")
            )
            asp_ok = any(symbol.name == "selected_valid" for symbol in selected_symbols)
            sample = generate(params)
        except Exception as exc:
            failures.append(f"{case.key}: generation or solving raised {exc}")
            continue

        story_lower = sample.story.lower()
        required_text = ("mattress", "orthodontist", "stake", "magic", "curiosity", "bad ending")
        if not python_ok or python_ok != asp_ok:
            failures.append(f"{case.key}: Python and ASP disagree on the reasonableness gate")
        if any(word not in story_lower for word in required_text):
            failures.append(f"{case.key}: story omitted a required narrative feature")
        if "?" not in sample.story or "{" in sample.story or "}" in sample.story:
            failures.append(f"{case.key}: story dialogue or template rendering is incomplete")
        if not sample.world or not sample.world.facts.get("resolved"):
            failures.append(f"{case.key}: story did not reach a resolved world state")
        elif (
            sample.world.mattress.meters["height"] != 0.0
            or sample.world.mattress.meters["wear"] != 0.0
            or sample.world.stake.meters["looseness"] != 0.0
            or not sample.world.facts.get("bad_ending_avoided")
        ):
            failures.append(f"{case.key}: the physical resolution or safe ending is incomplete")
        if not sample.story_qa or not sample.world_qa or not sample.story.strip().endswith((".", "!", "?”", "’")):
            failures.append(f"{case.key}: story, ending, or QA coverage is incomplete")

    if failures:
        print("MISMATCH: storyworld verification found problems:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"OK: ASP/Python parity across {len(CASES)} cases; "
        f"{len(CASES)} generated stories passed the story checks."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming magical story at an orthodontist's family camp-in."
    )
    parser.add_argument("--name", default=None, help="Name of the curious child")
    parser.add_argument("--friend", default=None, help="Name of the child's friend")
    parser.add_argument(
        "--orthodontist",
        "--doctor",
        dest="orthodontist",
        default=None,
        help="Name of the orthodontist",
    )
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Generate the curated set of cases")
    parser.add_argument("--trace", action="store_true", help="Show the simulated world state")
    parser.add_argument("--qa", action="store_true", help="Show prompts and question-answer sets")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--asp", action="store_true", help="Show one ASP model")
    parser.add_argument("--verify", action="store_true", help="Check ASP/Python parity and generated stories")
    parser.add_argument("--show-asp", action="store_true", help="Print the inline ASP program")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.name if args.name is not None else rng.choice(HERO_NAMES)
    friend_pool = [name for name in FRIEND_NAMES if name.casefold() != hero.casefold()]
    friend = args.friend if args.friend is not None else rng.choice(friend_pool)
    doctor_pool = [
        name for name in ORTHODONTIST_NAMES
        if name.casefold() not in {hero.casefold(), friend.casefold()}
    ]
    orthodontist = (
        args.orthodontist
        if args.orthodontist is not None
        else rng.choice(doctor_pool)
    )

    offset = sample_seed - base_seed
    case_index = offset % len(CASES)
    style_block = offset // len(CASES)
    params = StoryParams(
        hero=hero,
        friend=friend,
        orthodontist=orthodontist,
        case=case_index,
        telling_mode=style_block % len(OPENINGS),
        curiosity_style=(style_block // len(OPENINGS)) % len(CURIOSITY_QUESTIONS),
        ending_style=(style_block // (len(OPENINGS) * len(CURIOSITY_QUESTIONS))) % len(ENDING_STYLES),
        seed=sample_seed,
    )
    reasonableness_gate(params)
    return params


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _all_params(args: argparse.Namespace, base_seed: int) -> list[StoryParams]:
    custom_names = any(
        value is not None
        for value in (args.name, args.friend, args.orthodontist)
    )
    if not custom_names:
        return [
            replace(params, seed=base_seed + index)
            for index, params in enumerate(CURATED)
        ]

    results: list[StoryParams] = []
    for index in range(len(CASES)):
        sample_seed = base_seed + index
        params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
        params.case = index
        reasonableness_gate(params)
        results.append(params)
    return results


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            model = asp_models("#show valid_case/1.")
        except Exception as exc:
            parser.error(f"Could not run ASP: {exc}")
        print("ASP model:", [str(atom) for atom in model])
        return

    try:
        if not args.all and args.n < 1:
            raise StoryError("The number of stories must be at least 1.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        if args.all:
            samples = [generate(params) for params in _all_params(args, base_seed)]
        else:
            samples: list[StorySample] = []
            seen: set[str] = set()
            index = 0
            limit = max(50, args.n * 50)
            while len(samples) < args.n and index < limit:
                sample_seed = base_seed + index
                params = resolve_params(
                    args,
                    random.Random(sample_seed),
                    sample_seed,
                    base_seed,
                )
                sample = generate(params)
                if sample.story not in seen:
                    seen.add(sample.story)
                    samples.append(sample)
                index += 1

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
