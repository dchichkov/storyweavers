#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dynamo_precipitate_prank_inner_monologue_teamwork_moral.py
=====================================================================================

A small superhero-flavored storyworld about a child hero team, a dynamo-powered
rescue gadget, an impulsive prank, and the choice to work together and tell the
truth.

The model prefers a few strong, sensible variants over a wide weak space:
- a prank must plausibly affect the chosen dynamo gadget
- a fix must actually fit the kind of trouble caused
- very low-sense fixes are refused even if they exist in the registry
- outcomes are state-driven: the prank is either averted by conscience and
  teammates, repaired through teamwork, or it ruins the drill and the team must
  learn from it

Run it
------
python storyworlds/worlds/gpt-5.4/dynamo_precipitate_prank_inner_monologue_teamwork_moral.py
python storyworlds/worlds/gpt-5.4/dynamo_precipitate_prank_inner_monologue_teamwork_moral.py --all
python storyworlds/worlds/gpt-5.4/dynamo_precipitate_prank_inner_monologue_teamwork_moral.py --qa --json
python storyworlds/worlds/gpt-5.4/dynamo_precipitate_prank_inner_monologue_teamwork_moral.py --verify
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

_THIS = os.path.abspath(__file__)
_WORLDS_DIR = os.path.dirname(_THIS)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(_WORLDS_DIR))
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
IMPULSE_BASE = 4


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    place: str
    opener: str
    crowd: str
    ending_image: str


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    dynamo_kind: str
    signal: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Prank:
    id: str
    label: str
    action: str
    effect: str
    severity: int
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    sense: int = 2
    power: int = 1
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Trait:
    id: str
    caution: int
    style: str
    tags: set[str] = field(default_factory=set)


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
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_problem_spreads(world: World) -> list[str]:
    gadget = world.entities.get("gadget")
    team = world.entities.get("team")
    if gadget is None or team is None:
        return []
    if gadget.meters["jammed"] < THRESHOLD and gadget.meters["tangled"] < THRESHOLD:
        return []
    sig = ("problem_spreads",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    team.meters["delay"] += 1
    for ent in world.entities.values():
        if ent.role == "hero":
            ent.memes["worry"] += 1
    return ["__problem__"]


CAUSAL_RULES = [Rule(name="problem_spreads", tag="physical", apply=_r_problem_spreads)]


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


MISSIONS = {
    "roof": Mission(
        id="roof",
        place="the school roof garden",
        opener="The city below looked tiny, and the clouds were stacking up like gray blocks.",
        crowd="the families waiting in the yard",
        ending_image="the little beacon shining over the tomato boxes and windy flags",
    ),
    "courtyard": Mission(
        id="courtyard",
        place="the library courtyard",
        opener="Paper star capes fluttered near the fountain, and everyone was waiting for the weather drill.",
        crowd="the neighbors gathered by the benches",
        ending_image="the bright warning lamp glowing beside the lion statue",
    ),
    "playground": Mission(
        id="playground",
        place="the big playground stage",
        opener="The swings creaked softly, and dark clouds rolled past the sun.",
        crowd="the children lined up near the slide",
        ending_image="the rescue light sparkling above the painted wooden city",
    ),
}

GADGETS = {
    "beacon_bike": Gadget(
        id="beacon_bike",
        label="beacon",
        phrase="a bright rooftop beacon powered by a bicycle dynamo",
        dynamo_kind="wheel",
        signal="flash a brave blue light",
        difficulty=2,
        tags={"dynamo", "light"},
    ),
    "siren_cart": Gadget(
        id="siren_cart",
        label="siren",
        phrase="a rolling siren cart with a wheel dynamo",
        dynamo_kind="wheel",
        signal="sing out a strong whooo-whooo",
        difficulty=2,
        tags={"dynamo", "sound"},
    ),
    "floodlamp_crank": Gadget(
        id="floodlamp_crank",
        label="floodlamp",
        phrase="a hand-cranked floodlamp with a little dynamo inside",
        dynamo_kind="hand",
        signal="pour a white stripe of light across the ground",
        difficulty=1,
        tags={"dynamo", "light"},
    ),
}

PRANKS = {
    "glitter_gears": Prank(
        id="glitter_gears",
        label="glitter in the gears",
        action="sprinkle glitter into the dynamo gears",
        effect="jam",
        severity=2,
        fits={"wheel", "hand"},
        tags={"prank", "jam"},
    ),
    "cape_knot": Prank(
        id="cape_knot",
        label="a cape knot on the wheel",
        action="tie a loose cape ribbon around the dynamo wheel",
        effect="tangle",
        severity=2,
        fits={"wheel"},
        tags={"prank", "tangle"},
    ),
    "sticky_tape": Prank(
        id="sticky_tape",
        label="sticky tape over the crank slot",
        action="press sticky tape over the crank slot",
        effect="jam",
        severity=1,
        fits={"hand"},
        tags={"prank", "jam"},
    ),
}

FIXES = {
    "clean_and_brush": Fix(
        id="clean_and_brush",
        label="clean and brush",
        handles={"jam"},
        sense=3,
        power=2,
        text="used a brush and a cloth to clean the little dynamo until it spun freely again",
        fail="brushed and wiped in a hurry, but sticky bits still caught inside",
        qa_text="cleaned the dynamo with a brush and cloth until it could spin again",
        tags={"repair", "brush"},
    ),
    "untie_and_align": Fix(
        id="untie_and_align",
        label="untie and align",
        handles={"tangle"},
        sense=3,
        power=2,
        text="worked together to untie the ribbon, straighten the wheel, and set the belt back in line",
        fail="pulled at the knot, but the wheel stayed crooked and would not turn right",
        qa_text="untied the knot, straightened the wheel, and lined the belt back up",
        tags={"repair", "knot"},
    ),
    "peel_and_polish": Fix(
        id="peel_and_polish",
        label="peel and polish",
        handles={"jam"},
        sense=2,
        power=1,
        text="peeled the tape away and polished the slot so the crank could slide back in",
        fail="peeled the tape fast, but gummy glue still blocked the crank",
        qa_text="peeled the tape away and cleaned the crank slot",
        tags={"repair", "tape"},
    ),
    "yank_hard": Fix(
        id="yank_hard",
        label="yank hard",
        handles={"jam", "tangle"},
        sense=1,
        power=1,
        text="yanked at the machine",
        fail="yanked at the machine until it rattled even worse",
        qa_text="pulled on the machine hard",
        tags={"bad_fix"},
    ),
}

TRAITS = {
    "kind": Trait(id="kind", caution=4, style="kind", tags={"moral"}),
    "steady": Trait(id="steady", caution=3, style="steady", tags={"moral"}),
    "showy": Trait(id="showy", caution=1, style="showy", tags={"impulse"}),
    "hasty": Trait(id="hasty", caution=0, style="hasty", tags={"impulse"}),
}

GIRL_NAMES = ["Maya", "Nova", "Lina", "Ava", "Ruby", "Skye"]
BOY_NAMES = ["Jett", "Leo", "Max", "Theo", "Kai", "Finn"]
SIDEKICK_NAMES = ["Pip", "June", "Ivy", "Ben", "Nora", "Tess"]


def prank_fits(gadget: Gadget, prank: Prank) -> bool:
    return gadget.dynamo_kind in prank.fits


def sensible_fixes_for(prank: Prank) -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN and prank.effect in f.handles]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for gadget_id, gadget in GADGETS.items():
            for prank_id, prank in PRANKS.items():
                if prank_fits(gadget, prank) and sensible_fixes_for(prank):
                    out.append((mission_id, gadget_id, prank_id))
    return out


@dataclass
class StoryParams:
    mission: str
    gadget: str
    prank: str
    fix: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    mentor: str
    trait: str
    team_size: int = 3
    seed: Optional[int] = None


def conscience_score(trait_id: str, team_size: int) -> int:
    return TRAITS[trait_id].caution + team_size


def would_avert(trait_id: str, team_size: int) -> bool:
    return conscience_score(trait_id, team_size) > IMPULSE_BASE + 1


def repair_score(fix_id: str, team_size: int) -> int:
    return FIXES[fix_id].power + team_size


def trouble_score(gadget_id: str, prank_id: str) -> int:
    return GADGETS[gadget_id].difficulty + PRANKS[prank_id].severity


def is_repaired(fix_id: str, gadget_id: str, prank_id: str, team_size: int) -> bool:
    return repair_score(fix_id, team_size) >= trouble_score(gadget_id, prank_id)


def predict_prank(world: World) -> dict:
    sim = world.copy()
    gadget = sim.get("gadget")
    prank = sim.facts["prank_cfg"]
    if prank.effect == "jam":
        gadget.meters["jammed"] += 1
    elif prank.effect == "tangle":
        gadget.meters["tangled"] += 1
    propagate(sim, narrate=False)
    return {
        "delay": sim.get("team").meters["delay"],
        "broken": gadget.meters["jammed"] >= THRESHOLD or gadget.meters["tangled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, sidekick: Entity, mission: Mission, gadget: Gadget) -> None:
    world.say(
        f"{hero.id}, {sidekick.id}, and the rest of the Tiny Thunder Team met at {mission.place}. "
        f"They wore paper masks, brave capes, and serious faces. {mission.opener}"
    )
    world.say(
        f"At the center of their mission stood {gadget.phrase}. When someone pedaled or cranked the dynamo, "
        f"the gadget would {gadget.signal} for {mission.crowd}."
    )


def desire_attention(world: World, hero: Entity, prank: Prank) -> None:
    hero.memes["showoff"] += 1
    world.say(
        f"{hero.id} loved being the first hero anyone noticed. Looking at the machine, "
        f"{hero.pronoun()} had a naughty idea: maybe {hero.pronoun()} could {prank.action} as a little prank, "
        f"then fix it and still look clever."
    )


def inner_monologue(world: World, hero: Entity, prank: Prank) -> None:
    hero.memes["conscience"] += TRAITS[world.facts["trait_cfg"].id].caution
    world.say(
        f'Inside {hero.pronoun("possessive")} head, a quieter voice spoke. '
        f'"Do not be precipitate," {hero.id} thought. "A prank that feels tiny now could '
        f'precipitate a real problem when people need this dynamo to work."'
    )


def warning(world: World, sidekick: Entity, prank: Prank, gadget: Gadget) -> None:
    pred = predict_prank(world)
    world.facts["predicted_delay"] = pred["delay"]
    sidekick.memes["care"] += 1
    world.say(
        f'{sidekick.id} saw the look on {world.get("hero").id}\'s face and stepped closer. '
        f'"If you turn this into a prank, the {gadget.label} could stop right when the drill begins," '
        f'{sidekick.pronoun()} said. "People will trust our signal."'
    )


def back_down(world: World, hero: Entity, sidekick: Entity, mentor: Entity, gadget: Gadget) -> None:
    hero.memes["relief"] += 1
    sidekick.memes["trust"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id} let out a long breath and dropped {hero.pronoun('possessive')} hand. "
        f'"You are right," {hero.pronoun()} said. "A real hero does not break things just to get a laugh."'
    )
    world.say(
        f"Instead, {hero.id} and {sidekick.id} checked the cables together, and {mentor.label_word} smiled to see "
        f"the team choosing care over showing off."
    )
    gadget.meters["working"] += 1


def do_prank(world: World, hero: Entity, prank: Prank, gadget: Gadget) -> None:
    hero.memes["defiance"] += 1
    if prank.effect == "jam":
        gadget.meters["jammed"] += 1
    elif prank.effect == "tangle":
        gadget.meters["tangled"] += 1
    gadget.meters["working"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"But the silly idea won for one moment. {hero.id} moved fast and {prank.action}. "
        f"At once the machine gave a sour little clack instead of working."
    )


def alarm(world: World, sidekick: Entity, gadget: Gadget) -> None:
    world.say(
        f'"Oh no," said {sidekick.id}. "The {gadget.label} is stuck." The team looked from the dark machine '
        f"to the waiting sky and then back at one another."
    )


def teamwork_fix(world: World, hero: Entity, sidekick: Entity, mentor: Entity, fix: Fix, gadget: Gadget) -> None:
    hero.memes["shame"] += 1
    sidekick.memes["teamwork"] += 1
    mentor.memes["guidance"] += 1
    gadget.meters["working"] += 1
    gadget.meters["jammed"] = 0.0
    gadget.meters["tangled"] = 0.0
    world.say(
        f"{hero.id}'s cheeks grew hot. {hero.pronoun().capitalize()} told the truth before anyone had to guess. "
        f'"I did it. I wanted a prank, and I was wrong."'
    )
    world.say(
        f"No one wasted time on scolding first. {hero.id}, {sidekick.id}, and {mentor.label_word} {fix.text}. "
        f"Little by little, the machine woke up."
    )
    world.say(
        f"Soon the dynamo hummed, and the {gadget.label} began to {gadget.signal}. "
        f"The team had fixed the trouble by working together and being honest."
    )
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1


def failed_fix(world: World, hero: Entity, sidekick: Entity, mentor: Entity, fix: Fix, gadget: Gadget, mission: Mission) -> None:
    hero.memes["shame"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id} swallowed hard and admitted the truth. Then the team tried to help, but they were too late. "
        f"They {fix.fail}."
    )
    world.say(
        f"The weather drill had to be canceled, and {mission.crowd} had to go inside without seeing the signal at all. "
        f"The quiet felt much bigger than the joke had."
    )
    world.say(
        f"{mentor.label_word.capitalize()} put a hand on {hero.id}'s shoulder. "
        f'"Power is not for tricks," {mentor.pronoun()} said gently. "People count on us."'
    )
    gadget.meters["working"] = 0.0


def closing_image(world: World, mission: Mission, gadget: Gadget, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"When the first drops tapped the railings, {gadget.label} was ready, and the team stood proud beneath "
            f"{mission.ending_image}. No prank had stolen their moment."
        )
    elif outcome == "repaired":
        world.say(
            f"A little later, with the clouds finally opening above them, the children watched {mission.ending_image}. "
            f"This time the brave light meant something true."
        )
    else:
        world.say(
            f"After the crowd had gone, the team rolled the quiet machine back under cover. "
            f"{hero_name_from_world(world)} looked at the still dynamo and knew laughter is small when trust is broken."
        )


def hero_name_from_world(world: World) -> str:
    hero = world.entities.get("hero")
    return hero.id if hero is not None else "The hero"


def tell(
    mission: Mission,
    gadget_cfg: Gadget,
    prank_cfg: Prank,
    fix_cfg: Fix,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    sidekick_name: str = "Pip",
    sidekick_gender: str = "boy",
    mentor_type: str = "mother",
    trait_id: str = "steady",
    team_size: int = 3,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    hero.attrs["name"] = hero_name
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_gender, label=sidekick_name, role="sidekick"))
    sidekick.attrs["name"] = sidekick_name
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label="the mentor", role="mentor"))
    team = world.add(Entity(id="team", kind="thing", type="team", label="team"))
    gadget = world.add(Entity(id="gadget", kind="thing", type="gadget", label=gadget_cfg.label, tags=set(gadget_cfg.tags)))
    world.facts.update(
        mission=mission,
        gadget_cfg=gadget_cfg,
        prank_cfg=prank_cfg,
        fix_cfg=fix_cfg,
        trait_cfg=TRAITS[trait_id],
        hero=hero,
        sidekick=sidekick,
        mentor=mentor,
        team_size=team_size,
    )

    introduce(world, Entity(id=hero_name, kind="character", type=hero_gender), Entity(id=sidekick_name, kind="character", type=sidekick_gender), mission, gadget_cfg)
    world.para()
    desire_attention(world, Entity(id=hero_name, kind="character", type=hero_gender), prank_cfg)
    inner_monologue(world, Entity(id=hero_name, kind="character", type=hero_gender), prank_cfg)
    warning(world, Entity(id=sidekick_name, kind="character", type=sidekick_gender), prank_cfg, gadget_cfg)

    averted = would_avert(trait_id, team_size)
    if averted:
        world.para()
        back_down(world, Entity(id=hero_name, kind="character", type=hero_gender), Entity(id=sidekick_name, kind="character", type=sidekick_gender), mentor, gadget)
        outcome = "averted"
    else:
        world.para()
        do_prank(world, Entity(id=hero_name, kind="character", type=hero_gender), prank_cfg, gadget)
        alarm(world, Entity(id=sidekick_name, kind="character", type=sidekick_gender), gadget_cfg)
        repaired = is_repaired(fix_cfg.id, gadget_cfg.id, prank_cfg.id, team_size)
        world.para()
        if repaired:
            teamwork_fix(world, Entity(id=hero_name, kind="character", type=hero_gender), Entity(id=sidekick_name, kind="character", type=sidekick_gender), mentor, fix_cfg, gadget_cfg)
            outcome = "repaired"
        else:
            failed_fix(world, Entity(id=hero_name, kind="character", type=hero_gender), Entity(id=sidekick_name, kind="character", type=sidekick_gender), mentor, fix_cfg, gadget_cfg, mission)
            outcome = "failed"

    world.para()
    closing_image(world, mission, gadget_cfg, outcome)
    world.facts.update(
        outcome=outcome,
        prank_happened=not averted,
        repaired=(outcome == "repaired"),
        averted=averted,
        truthful=(outcome in {"repaired", "failed"}),
    )
    return world


KNOWLEDGE = {
    "dynamo": [
        (
            "What is a dynamo?",
            "A dynamo is a little machine that turns movement into electricity. When a wheel or crank spins it, it can help power a light or another gadget."
        )
    ],
    "prank": [
        (
            "What is a prank?",
            "A prank is a trick someone plays to get a laugh. A prank is not a good choice when it can scare people, break things, or make others lose trust."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another instead of trying to do everything alone. Good teamwork is calm, honest, and kind."
        )
    ],
    "honesty": [
        (
            "Why is it important to tell the truth after a mistake?",
            "Telling the truth helps people fix the real problem faster. It also shows you are ready to be responsible."
        )
    ],
    "weather": [
        (
            "Why do weather drills matter?",
            "Weather drills help people practice what to do when a storm comes. Practice makes it easier to stay calm and safe."
        )
    ],
    "repair": [
        (
            "Why should you repair a machine carefully?",
            "Machines work best when you fix the part that is really causing trouble. Pulling or guessing can make the problem worse."
        )
    ],
}
KNOWLEDGE_ORDER = ["dynamo", "prank", "teamwork", "honesty", "weather", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].attrs.get("name", "Nova")
    sidekick = f["sidekick"].attrs.get("name", "Pip")
    gadget = f["gadget_cfg"]
    prank = f["prank_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short superhero story for a 3-to-5-year-old that includes the words "dynamo", "precipitate", and "prank".',
            f"Tell a gentle superhero story where {hero} is tempted to play a prank on a {gadget.label}, but an inner monologue and a teammate's warning help {hero} choose the good path.",
            f"Write a story with teamwork and moral value where a child hero decides not to be precipitate and keeps the dynamo gadget safe."
        ]
    if outcome == "repaired":
        return [
            'Write a short superhero story for a 3-to-5-year-old that includes the words "dynamo", "precipitate", and "prank".',
            f"Tell a superhero story where {hero}'s prank breaks a dynamo machine, but {hero}, {sidekick}, and a grown-up fix it through teamwork and honesty.",
            f"Write a story with inner monologue and a moral lesson where a hasty choice causes trouble and then gets repaired the right way."
        ]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "dynamo", "precipitate", and "prank".',
        f"Tell a cautionary superhero story where {hero} ignores a warning, plays a prank on the {gadget.label}, and learns that trust matters more than showing off.",
        "Write a story with teamwork, inner monologue, and moral value where a bad choice ruins the plan and leaves a quiet lesson behind."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"].attrs.get("name", "Nova")
    sidekick = f["sidekick"].attrs.get("name", "Pip")
    mentor = f["mentor"]
    gadget = f["gadget_cfg"]
    prank = f["prank_cfg"]
    fix = f["fix_cfg"]
    mission = f["mission"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about the Tiny Thunder Team, especially {hero} and {sidekick}. They are trying to help with a weather drill like little superheroes."
        ),
        (
            "What was the team supposed to do?",
            f"They were supposed to use {gadget.phrase} so it could {gadget.signal}. The signal was for {mission.crowd}, so the machine needed to work at the right time."
        ),
        (
            f"What bad idea did {hero} have?",
            f"{hero} wanted to turn the machine into a prank by trying {prank.label}. It seemed funny for one second, but it could stop the team from helping people."
        ),
        (
            f"What did {hero} think inside {f['hero'].pronoun('possessive')} head?",
            f"{hero} told {f['hero'].pronoun('object')}self not to be precipitate. {hero} understood that a tiny prank could precipitate a bigger problem."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Why did {hero} stop before doing the prank?",
                f"{hero} listened to the inner warning and to {sidekick}. That helped {hero} choose care over showing off before anything broke."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the gadget ready and the team standing proud together. The ending shows that real hero work means protecting trust, not chasing a laugh."
            )
        )
    elif outcome == "repaired":
        qa.append(
            (
                f"How did the team solve the problem?",
                f"They solved it by telling the truth and then working together. They {fix.qa_text}, which let the dynamo work again."
            )
        )
        qa.append(
            (
                f"What moral did {hero} learn?",
                f"{hero} learned that power should help people, not feed a prank. Honesty and teamwork repaired more than the machine, because they also repaired trust."
            )
        )
    else:
        qa.append(
            (
                "What happened because of the prank?",
                f"The prank left the machine unable to help, so the weather drill had to stop. The joke felt small after everyone lost the signal they were waiting for."
            )
        )
        qa.append(
            (
                f"What lesson did {mentor.label_word} teach?",
                f"{mentor.label_word.capitalize()} taught that power is not for tricks. The quiet ending shows that trust matters more than attention."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"dynamo", "prank", "teamwork", "weather"}
    if f["outcome"] in {"repaired", "failed"}:
        tags |= {"honesty", "repair"}
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
        parts = [f"{ent.id:8} ({ent.type:8})"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            parts.append(f"attrs={ent.attrs}")
        lines.append("  " + " ".join(parts))
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(gadget: Gadget, prank: Prank) -> str:
    return (
        f"(No story: {prank.label} does not fit a {gadget.dynamo_kind} dynamo gadget like the {gadget.label}. "
        f"Pick a prank that could really affect that machine.)"
    )


def explain_fix_rejection(prank: Prank, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). A superhero team should try a calmer, smarter repair.)"
        )
    return (
        f"(No story: {fix.label} does not actually handle a {prank.effect} problem. "
        f"Pick a fix that matches what the prank damaged.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.trait, params.team_size):
        return "averted"
    return "repaired" if is_repaired(params.fix, params.gadget, params.prank, params.team_size) else "failed"


ASP_RULES = r"""
valid(M, G, P) :- mission(M), gadget(G), prank(P), prank_fits(G, P), prank_effect(P, E), sensible_fix_for(E).

sensible_fix_for(E) :- fix(F), handles(F, E), sense(F, S), sense_min(Min), S >= Min.

conscience_score(C + T) :- chosen_trait(Tr), caution(Tr, C), team_size(T).
averted :- conscience_score(S), impulse_base(B), S > B + 1.

trouble(D + Sv) :- chosen_gadget(G), difficulty(G, D), chosen_prank(P), severity(P, Sv).
repair_score(Pw + T) :- chosen_fix(F), power(F, Pw), team_size(T).
repaired :- not averted, repair_score(R), trouble(Tb), R >= Tb.

outcome(averted) :- averted.
outcome(repaired) :- not averted, repaired.
outcome(failed) :- not averted, not repaired.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for gid, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("difficulty", gid, gadget.difficulty))
        lines.append(asp.fact("dynamo_kind", gid, gadget.dynamo_kind))
    for pid, prank in PRANKS.items():
        lines.append(asp.fact("prank", pid))
        lines.append(asp.fact("prank_effect", pid, prank.effect))
        lines.append(asp.fact("severity", pid, prank.severity))
        for kind in sorted(prank.fits):
            lines.append(asp.fact("prank_fits", pid, kind))
    for gid, gadget in GADGETS.items():
        for kind in sorted({gadget.dynamo_kind}):
            lines.append(asp.fact("prank_fits", gid, kind, truth=""))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
        for eff in sorted(fix.handles):
            lines.append(asp.fact("handles", fid, eff))
    for tid, trait in TRAITS.items():
        lines.append(asp.fact("trait", tid))
        lines.append(asp.fact("caution", tid, trait.caution))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_base", IMPULSE_BASE))
    lines.append("prank_fits(G, P) :- dynamo_kind(G, K), prank_fits(P, K).")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_gadget", params.gadget),
            asp.fact("chosen_prank", params.prank),
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_trait", params.trait),
            asp.fact("team_size", params.team_size),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        mission="roof",
        gadget="beacon_bike",
        prank="cape_knot",
        fix="untie_and_align",
        hero_name="Nova",
        hero_gender="girl",
        sidekick_name="Pip",
        sidekick_gender="boy",
        mentor="mother",
        trait="kind",
        team_size=3,
    ),
    StoryParams(
        mission="courtyard",
        gadget="floodlamp_crank",
        prank="sticky_tape",
        fix="peel_and_polish",
        hero_name="Jett",
        hero_gender="boy",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        mentor="father",
        trait="showy",
        team_size=3,
    ),
    StoryParams(
        mission="playground",
        gadget="siren_cart",
        prank="glitter_gears",
        fix="clean_and_brush",
        hero_name="Maya",
        hero_gender="girl",
        sidekick_name="Ben",
        sidekick_gender="boy",
        mentor="mother",
        trait="hasty",
        team_size=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero team, a dynamo gadget, and a prank that tests honesty."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--prank", choices=PRANKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--team-size", type=int, choices=[2, 3, 4], dest="team_size")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (mission, gadget, prank) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def _pick_sidekick(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in SIDEKICK_NAMES if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gadget and args.prank:
        gadget = GADGETS[args.gadget]
        prank = PRANKS[args.prank]
        if not prank_fits(gadget, prank):
            raise StoryError(explain_rejection(gadget, prank))
    if args.fix and args.prank:
        prank = PRANKS[args.prank]
        fix = FIXES[args.fix]
        if prank.effect not in fix.handles or fix.sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(prank, fix))

    combos = [
        c
        for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.gadget is None or c[1] == args.gadget)
        and (args.prank is None or c[2] == args.prank)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, gadget_id, prank_id = rng.choice(sorted(combos))
    prank = PRANKS[prank_id]

    if args.fix:
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(f.id for f in sensible_fixes_for(prank)))

    hero_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    sidekick_name, sidekick_gender = _pick_sidekick(rng, avoid=hero_name)
    mentor = args.mentor or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(sorted(TRAITS))
    team_size = args.team_size if args.team_size is not None else rng.choice([2, 3, 4])

    return StoryParams(
        mission=mission_id,
        gadget=gadget_id,
        prank=prank_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        mentor=mentor,
        trait=trait,
        team_size=team_size,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.gadget not in GADGETS:
        raise StoryError(f"(Unknown gadget: {params.gadget})")
    if params.prank not in PRANKS:
        raise StoryError(f"(Unknown prank: {params.prank})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.mentor not in {"mother", "father"}:
        raise StoryError(f"(Unknown mentor type: {params.mentor})")

    gadget = GADGETS[params.gadget]
    prank = PRANKS[params.prank]
    fix = FIXES[params.fix]
    if not prank_fits(gadget, prank):
        raise StoryError(explain_rejection(gadget, prank))
    if prank.effect not in fix.handles or fix.sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(prank, fix))

    world = tell(
        mission=MISSIONS[params.mission],
        gadget_cfg=gadget,
        prank_cfg=prank,
        fix_cfg=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        mentor_type=params.mentor,
        trait_id=params.trait,
        team_size=params.team_size,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed unexpectedly for seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test generated empty story.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, gadget, prank) combos:\n")
        for mission_id, gadget_id, prank_id in combos:
            print(f"  {mission_id:10} {gadget_id:16} {prank_id}")
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
            header = f"### {p.hero_name} at {p.mission}: {p.prank} -> {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
