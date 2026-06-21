#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py
===========================================================================

A standalone storyworld for a small animal tale about teamwork on a cottage
stoop. Tiny animal friends find a baby animal stuck below or beside a stoop at
dusk, choose a sensible climbing plan, and keep trying together until the baby
gets home.

Seed constraints rebuilt as world state
---------------------------------------
- Includes the words "flare" and "stoop".
- Uses Repetition: the team repeats the same teamwork chant across attempts.
- Uses Teamwork: different helpers brace, push, and guide together.
- Style: Animal Story.

Run it
------
    python storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py
    python storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py --stoop mossy_stone --plan vine_ladder
    python storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py --stoop tall_porch --plan leaf_ramp
    python storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/flare_stoop_repetition_teamwork_animal_story.py --verify
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
from typing import Optional

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
    gender: str = "neutral"
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.gender == "female":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.gender == "male":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Stoop:
    id: str
    label: str
    place: str
    height: int
    surface: str
    has_railing: bool
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    build_text: str
    use_text: str
    max_height: int
    needs_railing: bool
    surfaces: set[str] = field(default_factory=set)
    power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    courage: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Stranded:
    id: str
    species: str
    label: str
    home: str
    call: str
    gait: str
    fear: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Team:
    id: str
    leader_name: str
    leader_species: str
    leader_gender: str
    helper1_name: str
    helper1_species: str
    helper1_gender: str
    helper2_name: str
    helper2_species: str
    helper2_gender: str
    chant: str
    roles: tuple[str, str, str]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    stoop: str
    stranded: str
    plan: str
    light: str
    team: str
    seed: Optional[int] = None


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


STOOPS = {
    "low_wood": Stoop(
        id="low_wood",
        label="the low wooden stoop",
        place="by the little cottage",
        height=1,
        surface="dry",
        has_railing=False,
        image="The stoop was only a little higher than the marigolds, with warm boards and a sleepy flowerpot beside it.",
        tags={"stoop", "cottage"},
    ),
    "mossy_stone": Stoop(
        id="mossy_stone",
        label="the mossy stone stoop",
        place="by the rain barrel",
        height=2,
        surface="slippery",
        has_railing=True,
        image="Green moss feathered the edge of the stoop, and the evening dew made the stone shine.",
        tags={"stoop", "moss"},
    ),
    "tall_porch": Stoop(
        id="tall_porch",
        label="the tall porch stoop",
        place="under the honeysuckle",
        height=3,
        surface="dry",
        has_railing=True,
        image="It was a tall stoop with a white railing, high enough to make even brave paws pause.",
        tags={"stoop", "porch"},
    ),
}

PLANS = {
    "leaf_ramp": Plan(
        id="leaf_ramp",
        label="a bent leaf ramp",
        build_text="tucked a big dock leaf against the step to make a small ramp",
        use_text="The little ramp held still while the team pressed it tight.",
        max_height=1,
        needs_railing=False,
        surfaces={"dry"},
        power=2,
        tags={"ramp"},
    ),
    "pebble_steps": Plan(
        id="pebble_steps",
        label="a line of pebble steps",
        build_text="rolled smooth pebbles into a neat little stair",
        use_text="The tiny stair gave the baby one safe place for each careful foot.",
        max_height=2,
        needs_railing=False,
        surfaces={"dry", "slippery"},
        power=2,
        tags={"steps"},
    ),
    "vine_ladder": Plan(
        id="vine_ladder",
        label="a vine ladder",
        build_text="looped a soft vine around the railing and knotted it into a tiny ladder",
        use_text="The vine ladder swayed, but three friends held it steady from below.",
        max_height=3,
        needs_railing=True,
        surfaces={"dry", "slippery"},
        power=3,
        tags={"ladder"},
    ),
}

LIGHTS = {
    "firefly": Light(
        id="firefly",
        label="a firefly",
        phrase="A firefly drifted near and gave a green flare in the dusk.",
        courage=1,
        tags={"firefly", "light"},
    ),
    "glowworms": Light(
        id="glowworms",
        label="two glowworms",
        phrase="Two glowworms blinked together, and their gentle flare turned the path silver-green.",
        courage=1,
        tags={"glowworm", "light"},
    ),
    "lantern_moth": Light(
        id="lantern_moth",
        label="a lantern moth",
        phrase="A lantern moth fluttered low, and the gold flare of its wings made the shadows feel smaller.",
        courage=2,
        tags={"moth", "light"},
    ),
}

STRANDED = {
    "duckling": Stranded(
        id="duckling",
        species="duckling",
        label="the duckling",
        home="a straw basket on the porch",
        call="Peep, peep!",
        gait="waddle",
        fear=2,
        tags={"duckling"},
    ),
    "hedgehog": Stranded(
        id="hedgehog",
        species="hedgehog",
        label="the hedgehog",
        home="a soft basket by the door",
        call="Huff, huff!",
        gait="tiptoe",
        fear=1,
        tags={"hedgehog"},
    ),
    "kitten": Stranded(
        id="kitten",
        species="kitten",
        label="the kitten",
        home="a blanket box just inside the door",
        call="Mew, mew!",
        gait="climb",
        fear=2,
        tags={"kitten"},
    ),
}

TEAMS = {
    "garden_friends": Team(
        id="garden_friends",
        leader_name="Pip",
        leader_species="mouse",
        leader_gender="male",
        helper1_name="Moss",
        helper1_species="frog",
        helper1_gender="male",
        helper2_name="Tansy",
        helper2_species="squirrel",
        helper2_gender="female",
        chant="Push, brace, climb!",
        roles=("called the count", "braced the bottom", "guided from the side"),
        tags={"mouse", "frog", "squirrel"},
    ),
    "burrow_friends": Team(
        id="burrow_friends",
        leader_name="Fern",
        leader_species="rabbit",
        leader_gender="female",
        helper1_name="Pebble",
        helper1_species="mole",
        helper1_gender="male",
        helper2_name="Wisp",
        helper2_species="finch",
        helper2_gender="female",
        chant="Lift, steady, climb!",
        roles=("kept everyone's courage up", "nudged from below", "showed the next safe place"),
        tags={"rabbit", "mole", "finch"},
    ),
    "pond_friends": Team(
        id="pond_friends",
        leader_name="Reed",
        leader_species="water vole",
        leader_gender="male",
        helper1_name="Skip",
        helper1_species="toad",
        helper1_gender="male",
        helper2_name="Mira",
        helper2_species="wren",
        helper2_gender="female",
        chant="Together now, together now!",
        roles=("counted each try", "held the plan still", "cheered from above"),
        tags={"vole", "toad", "wren"},
    ),
}

KNOWLEDGE = {
    "stoop": [
        (
            "What is a stoop?",
            "A stoop is a little set of steps or a small raised place by a door. Animals or people have to climb up it to reach the doorway.",
        )
    ],
    "firefly": [
        (
            "Why do fireflies glow?",
            "Fireflies make light with their bodies. The glow helps them signal in the dark.",
        )
    ],
    "glowworm": [
        (
            "What is a glowworm?",
            "A glowworm is a little creature that shines in the dark. Its soft light can help other animals see at night.",
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is an insect with soft wings. Many moths fly at dusk and at night.",
        )
    ],
    "ramp": [
        (
            "What does a ramp do?",
            "A ramp makes a climb gentler by giving a smooth path upward. It can help small feet go where a tall step is hard to reach.",
        )
    ],
    "steps": [
        (
            "Why are small steps easier than one big step?",
            "Small steps break a climb into little parts. That makes it easier to balance and keep going.",
        )
    ],
    "ladder": [
        (
            "What does a ladder help you do?",
            "A ladder gives you places to hold and places to put your feet. It helps you climb up safely.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when everyone helps in a shared job. One friend can push, another can steady, and another can cheer.",
        )
    ],
    "repeat": [
        (
            "Why can repeating a brave try help?",
            "Repeating a try gives you another chance to do one small part right. Sometimes the next try works because everyone has learned a little more.",
        )
    ],
}
KNOWLEDGE_ORDER = ["stoop", "firefly", "glowworm", "moth", "ramp", "steps", "ladder", "teamwork", "repeat"]


def valid_combo(stoop: Stoop, plan: Plan) -> bool:
    if plan.needs_railing and not stoop.has_railing:
        return False
    if stoop.height > plan.max_height:
        return False
    if stoop.surface not in plan.surfaces:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for stoop_id, stoop in STOOPS.items():
        for plan_id, plan in PLANS.items():
            if valid_combo(stoop, plan):
                out.append((stoop_id, plan_id))
    return sorted(out)


def attempt_count(stoop: Stoop, plan: Plan, stranded: Stranded, light: Light) -> int:
    tries = 1 + max(0, stoop.height - plan.power) + max(0, stranded.fear - light.courage)
    return max(1, min(3, tries))


def outcome_of(params: StoryParams) -> str:
    tries = attempt_count(STOOPS[params.stoop], PLANS[params.plan], STRANDED[params.stranded], LIGHTS[params.light])
    return {1: "quick", 2: "steady", 3: "hard"}[tries]


def explain_rejection(stoop: Stoop, plan: Plan) -> str:
    if plan.needs_railing and not stoop.has_railing:
        return (
            f"(No story: {plan.label} needs a railing to tie or hold it, but {stoop.label} has no railing. "
            f"Pick pebble_steps or leaf_ramp for that stoop.)"
        )
    if stoop.height > plan.max_height:
        return (
            f"(No story: {plan.label} is too short for {stoop.label}. "
            f"That stoop is simply too high for this plan.)"
        )
    if stoop.surface not in plan.surfaces:
        return (
            f"(No story: {plan.label} would slip on the {stoop.surface} surface of {stoop.label}. "
            f"The fix has to match the footing.)"
        )
    return "(No story: that stoop and plan do not make a sensible climb.)"


def predict_climb(stoop: Stoop, plan: Plan, stranded: Stranded, light: Light) -> dict:
    tries = attempt_count(stoop, plan, stranded, light)
    return {
        "tries": tries,
        "hard": tries >= 3,
        "surface": stoop.surface,
    }


def introduce(world: World, team: Team, stoop: Stoop) -> None:
    leader = world.get("leader")
    h1 = world.get("helper1")
    h2 = world.get("helper2")
    world.say(
        f"At dusk, {leader.id} the {leader.type}, {h1.id} the {h1.type}, and {h2.id} the {h2.type} were sharing crumbs {stoop.place}."
    )
    world.say(stoop.image)


def hear_trouble(world: World, stranded_cfg: Stranded, stoop: Stoop) -> None:
    baby = world.get("baby")
    baby.memes["fear"] += stranded_cfg.fear
    world.say(
        f"Then a small voice called, \"{stranded_cfg.call}\" {stranded_cfg.label.capitalize()} was stuck below {stoop.label} and could not get back to {stranded_cfg.home}."
    )


def notice_light(world: World, light: Light) -> None:
    world.get("light").meters["glow"] += light.courage
    world.say(light.phrase)
    world.say("The small light did not lift anyone by itself, but it made brave thoughts feel a little bigger.")


def make_plan(world: World, plan: Plan, team: Team) -> None:
    leader = world.get("leader")
    h1 = world.get("helper1")
    h2 = world.get("helper2")
    world.get("plan").meters["ready"] += 1
    world.say(
        f"\"We can do this together,\" said {leader.id}. {leader.id}, {h1.id}, and {h2.id} {plan.build_text}."
    )
    world.say(
        f"{leader.id} {team.roles[0]}, {h1.id} {team.roles[1]}, and {h2.id} {team.roles[2]}."
    )


def try_once(world: World, stoop: Stoop, plan: Plan, team: Team, attempt_no: int, total_attempts: int) -> None:
    baby = world.get("baby")
    leader = world.get("leader")
    h1 = world.get("helper1")
    h2 = world.get("helper2")
    baby.meters["attempts"] += 1
    world.get("team").meters["teamwork"] += 1
    world.say(f"\"{team.chant}\" they said together.")
    if attempt_no == 1:
        world.say(plan.use_text)
    if attempt_no < total_attempts:
        baby.meters["progress"] += 1
        baby.memes["hope"] += 1
        baby.memes["fear"] = max(0.0, baby.memes["fear"] - 1.0)
        wobble = {
            "slippery": f"{stranded_word(baby)} slipped on the damp edge and came back down with a tiny gasp.",
            "dry": f"{stranded_word(baby)} climbed partway, then stopped and tucked close when the step still looked high.",
        }[stoop.surface]
        world.say(wobble)
        world.say(
            f"{leader.id} touched the plan again, {h1.id} held steady, and {h2.id} said, \"Again. We are right here.\""
        )
    else:
        baby.meters["progress"] += 1
        baby.meters["home"] = 1
        baby.memes["fear"] = 0.0
        baby.memes["joy"] += 1
        leader.memes["joy"] += 1
        h1.memes["joy"] += 1
        h2.memes["joy"] += 1
        world.say(
            f"Once more they breathed together. {stranded_word(baby).capitalize()} {baby.attrs['gait_phrase']} up, up, and at last reached the top of the stoop."
        )


def celebrate(world: World, stoop: Stoop, stranded_cfg: Stranded) -> None:
    leader = world.get("leader")
    h1 = world.get("helper1")
    h2 = world.get("helper2")
    baby = world.get("baby")
    world.say(
        f"{stranded_cfg.label.capitalize()} gave the happiest little sound and hurried home to {stranded_cfg.home}."
    )
    world.say(
        f"The four small friends sat together on {stoop.label}, and the night garden seemed less tall now that they had climbed it together."
    )
    world.say(
        f"Above them, the light made one more soft flare, and {leader.id}, {h1.id}, and {h2.id} knew they would remember this brave evening every time they passed the stoop."
    )


def stranded_word(baby: Entity) -> str:
    return baby.label or baby.type


def tell(stoop: Stoop, stranded_cfg: Stranded, plan: Plan, light_cfg: Light, team_cfg: Team) -> World:
    world = World()
    leader = world.add(
        Entity(
            id=team_cfg.leader_name,
            kind="character",
            type=team_cfg.leader_species,
            label=f"{team_cfg.leader_name} the {team_cfg.leader_species}",
            role="leader",
            gender=team_cfg.leader_gender,
        )
    )
    helper1 = world.add(
        Entity(
            id=team_cfg.helper1_name,
            kind="character",
            type=team_cfg.helper1_species,
            label=f"{team_cfg.helper1_name} the {team_cfg.helper1_species}",
            role="helper1",
            gender=team_cfg.helper1_gender,
        )
    )
    helper2 = world.add(
        Entity(
            id=team_cfg.helper2_name,
            kind="character",
            type=team_cfg.helper2_species,
            label=f"{team_cfg.helper2_name} the {team_cfg.helper2_species}",
            role="helper2",
            gender=team_cfg.helper2_gender,
        )
    )
    baby = world.add(
        Entity(
            id=stranded_cfg.label.capitalize(),
            kind="character",
            type=stranded_cfg.species,
            label=stranded_cfg.label,
            role="baby",
            gender="neutral",
            attrs={"gait_phrase": f"{stranded_cfg.gait}ed carefully"},
        )
    )
    light = world.add(
        Entity(
            id=light_cfg.label,
            kind="thing",
            type="light",
            label=light_cfg.label,
            role="light",
        )
    )
    plan_ent = world.add(
        Entity(
            id=plan.id,
            kind="thing",
            type="plan",
            label=plan.label,
            role="plan",
        )
    )
    team = world.add(
        Entity(
            id="team",
            kind="thing",
            type="team",
            label="the team",
            role="team",
        )
    )

    introduce(world, team_cfg, stoop)
    hear_trouble(world, stranded_cfg, stoop)
    world.para()
    notice_light(world, light_cfg)
    make_plan(world, plan, team_cfg)

    pred = predict_climb(stoop, plan, stranded_cfg, light_cfg)
    world.facts["predicted_tries"] = pred["tries"]
    world.facts["predicted_hard"] = pred["hard"]
    world.facts["surface"] = pred["surface"]

    world.para()
    total_attempts = pred["tries"]
    for i in range(1, total_attempts + 1):
        try_once(world, stoop, plan, team_cfg, i, total_attempts)

    world.para()
    celebrate(world, stoop, stranded_cfg)

    world.facts.update(
        leader=leader,
        helper1=helper1,
        helper2=helper2,
        baby=baby,
        light=light,
        plan=plan_ent,
        stoop=stoop,
        stranded_cfg=stranded_cfg,
        plan_cfg=plan,
        light_cfg=light_cfg,
        team_cfg=team_cfg,
        outcome={1: "quick", 2: "steady", 3: "hard"}[total_attempts],
        attempts=total_attempts,
        reached_home=baby.meters["home"] >= THRESHOLD,
        chant=team_cfg.chant,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    stoop = world.facts["stoop"]
    stranded_cfg = world.facts["stranded_cfg"]
    plan = world.facts["plan_cfg"]
    team = world.facts["team_cfg"]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the words "flare" and "stoop" and shows teamwork.',
        f"Tell a gentle story where {team.leader_name} and two animal friends help {stranded_cfg.label} climb {stoop.label} using {plan.label}, trying together more than once if needed.",
        f'Write an animal tale with repetition, using the teamwork chant "{team.chant}", and end with a safe, cozy image on the stoop.',
    ]


def pair_label(world: World) -> str:
    leader = world.facts["leader"]
    helper1 = world.facts["helper1"]
    helper2 = world.facts["helper2"]
    return f"{leader.id} the {leader.type}, {helper1.id} the {helper1.type}, and {helper2.id} the {helper2.type}"


def story_qa(world: World) -> list[tuple[str, str]]:
    stoop = world.facts["stoop"]
    stranded_cfg = world.facts["stranded_cfg"]
    plan = world.facts["plan_cfg"]
    light_cfg = world.facts["light_cfg"]
    attempts = world.facts["attempts"]
    leader = world.facts["leader"]
    helper1 = world.facts["helper1"]
    helper2 = world.facts["helper2"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_label(world)} helping {stranded_cfg.label}. The whole story turns on the friends working as one team.",
        ),
        (
            f"Why was {stranded_cfg.label} upset?",
            f"{stranded_cfg.label.capitalize()} was stuck below {stoop.label} and could not get back to {stranded_cfg.home}. The step felt especially big in the evening, so the baby felt scared.",
        ),
        (
            "How did the friends work together?",
            f"They built {plan.label} and each friend had a job. {leader.id} led the count, {helper1.id} held things steady, and {helper2.id} guided and encouraged the climb.",
        ),
        (
            f"Why does the story mention a flare of light?",
            f"The {light_cfg.label} made a small flare in the dusk so the friends could see and feel braver. The light did not solve the climb alone, but it helped the team keep trying.",
        ),
    ]
    if attempts == 1:
        qa.append(
            (
                "Did the plan work right away?",
                f"Yes. The climb was quick because {plan.label} matched the stoop well and the team held it steady. The friends still worked together, but one brave try was enough.",
            )
        )
    else:
        qa.append(
            (
                "Why did they have to try again?",
                f"They had to try {attempts} times because the climb felt hard for such a small animal. Each try gave {stranded_cfg.label} a little more hope, and the repeated teamwork made the last try succeed.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with all the small friends safe together on the stoop after {stranded_cfg.label} reached home. The last image shows that what changed was not the size of the step, but the courage they found together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"stoop", "teamwork", "repeat"}
    tags |= set(world.facts["plan_cfg"].tags)
    tags |= set(world.facts["light_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:16} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: attempts={world.facts.get('attempts')} outcome={world.facts.get('outcome')}")
    return "\n".join(lines)


ASP_RULES = r"""
% sensible stoop-plan pairs
valid(S, P) :- stoop(S), plan(P), height(S, H), max_height(P, M), H <= M,
               surface(S, T), works_on(P, T), (not needs_railing(P); has_railing(S)).

% attempt count and ending mood
attempts(1) :- chosen_stoop(S), chosen_plan(P), chosen_stranded(B), chosen_light(L),
               height(S, H), max_height(P, M), H - M <= 0,
               fear(B, F), courage(L, C), F - C <= 0.
attempts(2) :- chosen_stoop(S), chosen_plan(P), chosen_stranded(B), chosen_light(L),
               not attempts(1),
               height(S, H), max_height(P, M), fear(B, F), courage(L, C),
               V = 1 + max(0, H - M) + max(0, F - C), V = 2.
attempts(3) :- chosen_stoop(S), chosen_plan(P), chosen_stranded(B), chosen_light(L),
               not attempts(1), not attempts(2),
               height(S, H), max_height(P, M), fear(B, F), courage(L, C),
               V = 1 + max(0, H - M) + max(0, F - C), V >= 3.

outcome(quick)  :- attempts(1).
outcome(steady) :- attempts(2).
outcome(hard)   :- attempts(3).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for stoop_id, stoop in STOOPS.items():
        lines.append(asp.fact("stoop", stoop_id))
        lines.append(asp.fact("height", stoop_id, stoop.height))
        lines.append(asp.fact("surface", stoop_id, stoop.surface))
        if stoop.has_railing:
            lines.append(asp.fact("has_railing", stoop_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("max_height", plan_id, plan.max_height))
        if plan.needs_railing:
            lines.append(asp.fact("needs_railing", plan_id))
        for surface in sorted(plan.surfaces):
            lines.append(asp.fact("works_on", plan_id, surface))
    for stranded_id, stranded in STRANDED.items():
        lines.append(asp.fact("stranded", stranded_id))
        lines.append(asp.fact("fear", stranded_id, stranded.fear))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("courage", light_id, light.courage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_stoop", params.stoop),
            asp.fact("chosen_plan", params.plan),
            asp.fact("chosen_stranded", params.stranded),
            asp.fact("chosen_light", params.light),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal teamwork storyworld: a baby animal, a stoop, a sensible climbing plan, and repeated brave tries."
    )
    ap.add_argument("--stoop", choices=STOOPS)
    ap.add_argument("--stranded", choices=STRANDED)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--team", choices=TEAMS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (stoop, plan) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stoop and args.plan:
        if not valid_combo(STOOPS[args.stoop], PLANS[args.plan]):
            raise StoryError(explain_rejection(STOOPS[args.stoop], PLANS[args.plan]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.stoop is None or combo[0] == args.stoop)
        and (args.plan is None or combo[1] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    stoop_id, plan_id = rng.choice(combos)
    stranded_id = args.stranded or rng.choice(sorted(STRANDED))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    team_id = args.team or rng.choice(sorted(TEAMS))
    return StoryParams(
        stoop=stoop_id,
        stranded=stranded_id,
        plan=plan_id,
        light=light_id,
        team=team_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.stoop not in STOOPS:
        raise StoryError(f"(Unknown stoop: {params.stoop})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.stranded not in STRANDED:
        raise StoryError(f"(Unknown stranded animal: {params.stranded})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.team not in TEAMS:
        raise StoryError(f"(Unknown team: {params.team})")

    stoop = STOOPS[params.stoop]
    plan = PLANS[params.plan]
    if not valid_combo(stoop, plan):
        raise StoryError(explain_rejection(stoop, plan))

    world = tell(stoop, STRANDED[params.stranded], plan, LIGHTS[params.light], TEAMS[params.team])
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


CURATED = [
    StoryParams(
        stoop="low_wood",
        stranded="hedgehog",
        plan="leaf_ramp",
        light="firefly",
        team="garden_friends",
    ),
    StoryParams(
        stoop="mossy_stone",
        stranded="duckling",
        plan="pebble_steps",
        light="glowworms",
        team="pond_friends",
    ),
    StoryParams(
        stoop="mossy_stone",
        stranded="kitten",
        plan="vine_ladder",
        light="lantern_moth",
        team="burrow_friends",
    ),
    StoryParams(
        stoop="tall_porch",
        stranded="duckling",
        plan="vine_ladder",
        light="lantern_moth",
        team="garden_friends",
    ),
]


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid stoop/plan pairs match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    mismatches = []
    for p in cases:
        try:
            py_out = outcome_of(p)
            asp_out = asp_outcome(p)
        except Exception as err:  # pragma: no cover - verify path only
            rc = 1
            print(f"VERIFY ERROR while comparing outcomes: {err}")
            return rc
        if py_out != asp_out:
            mismatches.append((p, py_out, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model on {len(mismatches)} scenarios.")
        for p, py_out, asp_out in mismatches[:5]:
            print(f"  {p} python={py_out} asp={asp_out}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (stoop, plan) pairs:\n")
        for stoop_id, plan_id in combos:
            print(f"  {stoop_id:12} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.team}: {p.stranded} at {p.stoop} with {p.plan} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
