#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py
=========================================================================

A standalone story world for a child-sized superhero tale about a flashy goal,
a real cry for help, and the moral choice to answer first.

The core domain:
- a child hero is hurrying toward a public superhero moment
- a call for help crackles in from nearby
- the hero must choose between applause and kindness
- the right gear makes the rescue plausible
- the ending proves that helping matters more than being first on stage

The required seed word "reply" appears naturally in the rescue beat.

Run it
------
python storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py
python storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py --setting fair --trouble kitten --gear ladder
python storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py --trouble kitten --gear wagon
python storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/reply_moral_value_conflict_superhero_story.py --verify
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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    stage: str
    crowd_sound: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    caller_name: str
    caller_type: str
    subject_label: str
    subject_phrase: str
    location: str
    problem: str
    risk_line: str
    fix_need: str
    solved_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.get("trouble")
    if trouble.meters["unresolved"] < THRESHOLD:
        return out
    sig = ("danger", trouble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    caller = world.get("caller")
    hero.memes["worry"] += 1
    hero.memes["conflict"] += 1
    caller.memes["worry"] += 1
    trouble.meters["risk"] += 1
    out.append("__danger__")
    return out


def _r_helped(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.get("trouble")
    if trouble.meters["helped"] < THRESHOLD:
        return out
    sig = ("helped", trouble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    caller = world.get("caller")
    subject = world.get("subject")
    trouble.meters["unresolved"] = 0.0
    trouble.meters["risk"] = 0.0
    subject.memes["relief"] += 1
    caller.memes["relief"] += 1
    hero.memes["kindness"] += 1
    hero.memes["true_pride"] += 1
    hero.memes["conflict"] = 0.0
    out.append("__helped__")
    return out


CAUSAL_RULES = [
    Rule(name="danger", tag="social", apply=_r_danger),
    Rule(name="helped", tag="social", apply=_r_helped),
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


def gear_fits(trouble: Trouble, gear: Gear) -> bool:
    return trouble.fix_need in gear.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for trouble_id in sorted(setting.affords):
            trouble = TROUBLES[trouble_id]
            for gear_id, gear in GEARS.items():
                if gear_fits(trouble, gear):
                    combos.append((setting_id, trouble_id, gear_id))
    return combos


def predict_need(world: World) -> dict:
    sim = world.copy()
    trouble = sim.get("trouble")
    trouble.meters["unresolved"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("trouble").meters["risk"],
        "hero_worry": sim.get("hero").memes["worry"],
    }


def opening(world: World, hero: Entity, alter_ego: str, setting: Setting, prize: str) -> None:
    hero.memes["excitement"] += 1
    hero.memes["glory_wish"] += 1
    world.say(
        f"{hero.id} tied on {hero.attrs['cape_color']} cape and whispered, "
        f'"{alter_ego} is on patrol."'
    )
    world.say(
        f"All along {setting.place}, people were heading toward {setting.stage}. "
        f"{setting.crowd_sound}, and a shiny {prize} waited for the first young hero to arrive."
    )


def hurry(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} dashed down the sidewalk with knees pumping and cape snapping behind "
        f"{hero.pronoun('object')}. {hero.pronoun().capitalize()} could almost hear the crowd cheer."
    )


def call_for_help(world: World, caller: Entity, trouble: Trouble) -> None:
    radio = world.get("radio")
    trouble_ent = world.get("trouble")
    trouble_ent.meters["unresolved"] += 1
    caller.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {radio.label} on {hero_name(world)}'s wrist crackled. "
        f'"{hero_alias(world)}, do you copy?" came {caller.id}\'s voice. '
        f'"{trouble.problem} at {trouble.location}!"'
    )


def temptation(world: World, rival: Entity, hero: Entity, prize: str) -> None:
    hero.memes["conflict"] += 1
    world.say(
        f"{rival.id}, wearing a paper mask with bright lightning bolts, pointed toward the stage. "
        f'"Come on!" {rival.pronoun()} called. "If we run now, maybe you can still win the {prize}!"'
    )


def moral_pause(world: World, hero: Entity, trouble: Trouble) -> None:
    pred = predict_need(world)
    world.facts["predicted_risk"] = pred["risk"]
    hero.memes["thinking"] += 1
    world.say(
        f"{hero.id} slowed down. {hero.pronoun('possessive').capitalize()} boots wanted to race one way, "
        f"but {hero.pronoun('possessive')} heart tugged the other way."
    )
    world.say(
        f"{trouble.risk_line} Real heroes, {hero.id} thought, do not only chase claps. "
        f"They answer when someone needs them."
    )


def reply_and_turn(world: World, hero: Entity, caller: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["glory_wish"] = 0.0
    world.say(
        f'{hero.id} pressed the talk button and sent a quick reply: '
        f'"I am on my way. Hold tight!"'
    )
    world.say(
        f"Then {hero.pronoun()} spun away from the stage and ran toward the trouble instead."
    )


def use_gear(world: World, hero: Entity, trouble: Trouble, gear: Gear) -> None:
    gear_ent = world.get("gear")
    trouble_ent = world.get("trouble")
    gear_ent.meters["used"] += 1
    hero.meters["delay"] += 1
    world.say(gear.action_text.format(hero=hero.id, location=trouble.location, subject=trouble.subject_label))
    trouble_ent.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(trouble.solved_text)


def crowd_resolution(world: World, hero: Entity, caller: Entity, mayor: Entity, setting: Setting, prize: str, trouble: Trouble) -> None:
    world.say(
        f"By the time {hero.id} reached {setting.stage}, the cheering had already started. "
        f"{hero.pronoun().capitalize()} was late, and {hero.pronoun('possessive')} cape had one new wrinkle in it."
    )
    world.say(
        f"But {caller.id} hurried beside {hero.pronoun('object')} and told everyone what had happened at {trouble.location}."
    )
    world.say(
        f'{mayor.id} smiled and held up the {prize}. "This belongs to a hero who chose people before applause," '
        f'{mayor.pronoun()} said.'
    )
    world.say(
        f"{hero.id} took the {prize} with hot cheeks and a quiet smile. It felt lighter than a cheer and warmer than sunshine."
    )
    world.say(trouble.ending_image)


def hero_name(world: World) -> str:
    return world.get("hero").id


def hero_alias(world: World) -> str:
    return world.get("hero").attrs["alias"]


def tell(
    setting: Setting,
    trouble_cfg: Trouble,
    gear_cfg: Gear,
    hero_name_value: str = "Maya",
    hero_type: str = "girl",
    alias: str = "Comet Girl",
    rival_name: str = "Blaze",
    rival_type: str = "boy",
    cape_color: str = "red",
    parent_type: str = "mother",
    prize: str = "silver star badge",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name_value,
            kind="character",
            type=hero_type,
            role="hero",
            attrs={"alias": alias, "cape_color": cape_color},
        )
    )
    caller = world.add(
        Entity(
            id=trouble_cfg.caller_name,
            kind="character",
            type=trouble_cfg.caller_type,
            role="caller",
            label="the caller",
        )
    )
    subject = world.add(
        Entity(
            id="Subject",
            kind="thing",
            type="subject",
            label=trouble_cfg.subject_label,
            phrase=trouble_cfg.subject_phrase,
            tags=set(trouble_cfg.tags),
        )
    )
    rival = world.add(
        Entity(
            id=rival_name,
            kind="character",
            type=rival_type,
            role="rival",
        )
    )
    mayor = world.add(
        Entity(
            id="Mayor June",
            kind="character",
            type=parent_type,
            role="mayor",
            label="the mayor",
        )
    )
    world.add(
        Entity(
            id="radio",
            kind="thing",
            type="tool",
            label="the little hero radio",
        )
    )
    world.add(
        Entity(
            id="gear",
            kind="thing",
            type="gear",
            label=gear_cfg.label,
            phrase=gear_cfg.phrase,
            tags=set(gear_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="trouble",
            kind="thing",
            type="trouble",
            label=trouble_cfg.id,
            phrase=trouble_cfg.problem,
            tags=set(trouble_cfg.tags),
        )
    )

    opening(world, hero, alias, setting, prize)
    hurry(world, hero)

    world.para()
    call_for_help(world, caller, trouble_cfg)
    temptation(world, rival, hero, prize)
    moral_pause(world, hero, trouble_cfg)

    world.para()
    reply_and_turn(world, hero, caller)
    use_gear(world, hero, trouble_cfg, gear_cfg)

    world.para()
    crowd_resolution(world, hero, caller, mayor, setting, prize, trouble_cfg)

    world.facts.update(
        hero=hero,
        caller=caller,
        subject=subject,
        rival=rival,
        mayor=mayor,
        setting=setting,
        trouble_cfg=trouble_cfg,
        gear_cfg=gear_cfg,
        prize=prize,
        resolved=world.get("trouble").meters["helped"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "fair": Setting(
        id="fair",
        place="the town fair",
        stage="the Hero Parade stage",
        crowd_sound="Trumpets toot-tooted near the cake booth",
        affords={"kitten", "groceries"},
    ),
    "library": Setting(
        id="library",
        place="the library square",
        stage="the Reading Rocket stage",
        crowd_sound="Children in capes rustled their paper programs",
        affords={"books", "groceries"},
    ),
    "park": Setting(
        id="park",
        place="the sunny park",
        stage="the Sky Shield platform",
        crowd_sound="Balloons bobbed while drums thumped by the fountain",
        affords={"kitten", "books"},
    ),
}

TROUBLES = {
    "kitten": Trouble(
        id="kitten",
        caller_name="Pip",
        caller_type="boy",
        subject_label="a striped kitten",
        subject_phrase="a striped kitten with trembling paws",
        location="the bakery roof",
        problem="A striped kitten is stuck on the bakery roof",
        risk_line="From far away, the mew sounded small and scared.",
        fix_need="reach_high",
        solved_text="The kitten slid into hero arms, purring so hard that its whiskers shook.",
        ending_image="At the edge of the stage, the little kitten curled around the badge ribbon like a tiny striped moon.",
        tags={"kitten", "kindness"},
    ),
    "groceries": Trouble(
        id="groceries",
        caller_name="Nia",
        caller_type="girl",
        subject_label="Grandma Tessa's groceries",
        subject_phrase="Grandma Tessa's rolling oranges and soup cans",
        location="the busy crosswalk",
        problem="Grandma Tessa's groceries spilled all over the crosswalk",
        risk_line="Cars were waiting, and the oranges kept wobbling farther from the curb.",
        fix_need="carry_many",
        solved_text="Soon every orange, can, and loaf was back in the wagon, and Grandma Tessa could cross safely.",
        ending_image="On the stage steps, the silver badge shone beside one round orange that Grandma Tessa saved for the hero.",
        tags={"groceries", "helping"},
    ),
    "books": Trouble(
        id="books",
        caller_name="Owen",
        caller_type="boy",
        subject_label="the library books",
        subject_phrase="a stack of library books in a dark tent",
        location="the story tent",
        problem="The lights went out in the story tent and the library books are lost in the dark",
        risk_line="Inside the dark tent, little voices were beginning to wobble.",
        fix_need="light_dark",
        solved_text="A bright beam swept under the chairs, and soon the missing books were stacked safely back on the reading mat.",
        ending_image="When the hero reached the stage, the flashlight beam still glowed softly across a pile of safe, neat books.",
        tags={"books", "flashlight"},
    ),
}

GEARS = {
    "ladder": Gear(
        id="ladder",
        label="ladder",
        phrase="a folding rescue ladder",
        solves={"reach_high"},
        action_text="{hero} dragged the folding ladder to {location}, climbed carefully, and scooped up {subject} before it could slip again.",
        qa_text="used a ladder to reach the kitten safely",
        tags={"ladder"},
    ),
    "wagon": Gear(
        id="wagon",
        label="wagon",
        phrase="a bright red wagon",
        solves={"carry_many"},
        action_text="{hero} grabbed the red wagon, knelt at {location}, and loaded every rolling thing before anyone stepped on it.",
        qa_text="used a wagon to gather the groceries quickly",
        tags={"wagon"},
    ),
    "flashlight": Gear(
        id="flashlight",
        label="flashlight",
        phrase="a bright silver flashlight",
        solves={"light_dark"},
        action_text="{hero} clicked on the silver flashlight, ducked into {location}, and searched every shadowy corner.",
        qa_text="used a flashlight to search the dark tent",
        tags={"flashlight"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Zoe", "Ava", "Nora", "Ruby", "Ella", "Lucy"]
BOY_NAMES = ["Leo", "Max", "Finn", "Eli", "Theo", "Jack", "Noah", "Sam"]
ALIASES_GIRL = ["Comet Girl", "Star Spark", "Captain Kind", "Meteor Miss"]
ALIASES_BOY = ["Comet Boy", "Captain Kind", "Rocket Ray", "Star Shield"]
RIVAL_NAMES = ["Blaze", "Dash", "Bolt", "Skipper", "Jade"]
CAPE_COLORS = ["red", "blue", "gold", "purple"]

PRIZES = [
    "silver star badge",
    "golden cape pin",
    "bright helper medal",
]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    gear: str
    hero_name: str
    hero_type: str
    alias: str
    rival_name: str
    rival_type: str
    cape_color: str
    parent_type: str
    prize: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kitten": [
        (
            "Why should you move slowly with a scared kitten?",
            "A scared kitten can wiggle, scratch, or try to jump away. Moving slowly helps it feel safe and keeps it from falling.",
        )
    ],
    "groceries": [
        (
            "Why is a spilled grocery bag a problem in a crosswalk?",
            "Things on the ground can roll where people walk and where cars pass. Picking them up quickly helps everyone stay safe.",
        )
    ],
    "books": [
        (
            "Why do people use a flashlight in the dark?",
            "A flashlight helps you see when a place is dark. It lets you look carefully without bumping into things.",
        )
    ],
    "ladder": [
        (
            "What does a ladder help you do?",
            "A ladder helps you reach a place that is too high for your feet alone. You still have to climb carefully and hold on tight.",
        )
    ],
    "wagon": [
        (
            "What is a wagon useful for?",
            "A wagon helps carry many things at once, especially heavy or rolling things. It keeps them together so they do not scatter again.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a battery-powered light you carry in your hand. It shines into dark places so you can see clearly.",
        )
    ],
    "kindness": [
        (
            "What makes someone a real hero?",
            "A real hero helps people when they need help. Being kind and brave matters more than getting cheers first.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kindness", "kitten", "groceries", "books", "ladder", "wagon", "flashlight"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble_cfg"]
    prize = f["prize"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "reply" and teaches that kindness matters more than applause.',
        f"Tell a superhero story where {hero.id} is hurrying to win a {prize} but hears that {trouble.problem.lower()}, and chooses to help first.",
        f"Write a gentle conflict story in superhero style where a child hero sends a brave reply over a radio and solves a real problem before going to the stage.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    caller = f["caller"]
    rival = f["rival"]
    trouble = f["trouble_cfg"]
    gear = f["gear_cfg"]
    prize = f["prize"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child superhero called {hero.attrs['alias']}. {caller.id}, {rival.id}, and Mayor June also matter because they shape the hard choice.",
        ),
        (
            "What did the hero want at the beginning?",
            f"{hero.id} wanted to reach {setting.stage} quickly and maybe win the {prize}. That shiny prize is what made the later choice feel hard.",
        ),
        (
            "What was the problem?",
            f"{caller.id} called to say that {trouble.problem.lower()}. The trouble was happening at {trouble.location}, so someone needed help right away.",
        ),
        (
            "Why was there a conflict in the story?",
            f"There was a conflict because {rival.id} urged {hero.id} to keep running toward the prize. But {hero.id} could feel that helping first was the kinder and braver choice.",
        ),
        (
            "What was the hero's reply?",
            'The hero pressed the radio button and said, "I am on my way. Hold tight!" That reply showed the hero had already chosen people over applause.',
        ),
        (
            "How did the hero solve the problem?",
            f"{hero.id} {gear.qa_text}. Because the right gear matched the trouble, the help worked quickly and safely.",
        ),
        (
            "What did the hero learn?",
            f"{hero.id} learned that a real hero answers a need before chasing cheers. The badge mattered less than the safe, relieved ending {hero.pronoun()} helped create.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kindness"} | set(world.facts["trouble_cfg"].tags) | set(world.facts["gear_cfg"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="fair",
        trouble="kitten",
        gear="ladder",
        hero_name="Maya",
        hero_type="girl",
        alias="Comet Girl",
        rival_name="Blaze",
        rival_type="boy",
        cape_color="red",
        parent_type="mother",
        prize="silver star badge",
    ),
    StoryParams(
        setting="library",
        trouble="groceries",
        gear="wagon",
        hero_name="Leo",
        hero_type="boy",
        alias="Captain Kind",
        rival_name="Jade",
        rival_type="girl",
        cape_color="blue",
        parent_type="father",
        prize="bright helper medal",
    ),
    StoryParams(
        setting="park",
        trouble="books",
        gear="flashlight",
        hero_name="Ruby",
        hero_type="girl",
        alias="Star Spark",
        rival_name="Dash",
        rival_type="boy",
        cape_color="gold",
        parent_type="mother",
        prize="golden cape pin",
    ),
]


def explain_rejection(setting_id: str, trouble_id: str, gear_id: str) -> str:
    setting = SETTINGS.get(setting_id)
    trouble = TROUBLES.get(trouble_id)
    gear = GEARS.get(gear_id)
    if setting is None or trouble is None or gear is None:
        return "(No story: one of the requested options is unknown.)"
    if trouble_id not in setting.affords:
        return (
            f"(No story: {trouble.problem} does not fit {setting.place} in this world, "
            f"so the rescue would feel ungrounded there.)"
        )
    return (
        f"(No story: {gear.label} does not solve the {trouble.id} problem here. "
        f"Choose gear that matches the need: ladder for height, wagon for many rolling things, or flashlight for darkness.)"
    )


ASP_RULES = r"""
need(T, N) :- trouble(T), fix_need(T, N).
fits(T, G) :- need(T, N), solves(G, N).
valid(S, T, G) :- setting(S), trouble(T), gear(G), affords(S, T), fits(T, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for trouble_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, trouble_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("fix_need", trouble_id, trouble.fix_need))
    for gear_id, gear in GEARS.items():
        lines.append(asp.fact("gear", gear_id))
        for need in sorted(gear.solves):
            lines.append(asp.fact("solves", gear_id, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero child chooses helping over applause."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.trouble and args.gear:
        if (args.setting, args.trouble, args.gear) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.setting, args.trouble, args.gear))
    elif args.setting and args.trouble and args.trouble not in SETTINGS[args.setting].affords:
        raise StoryError(explain_rejection(args.setting, args.trouble, next(iter(GEARS))))
    elif args.trouble and args.gear and not gear_fits(TROUBLES[args.trouble], GEARS[args.gear]):
        any_setting = next(iter(SETTINGS))
        raise StoryError(explain_rejection(any_setting, args.trouble, args.gear))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, gear_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name_value = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    alias = rng.choice(ALIASES_GIRL if hero_type == "girl" else ALIASES_BOY)
    rival_type = "boy" if hero_type == "girl" else rng.choice(["girl", "boy"])
    rival_name = rng.choice([n for n in RIVAL_NAMES if n != hero_name_value])
    cape_color = rng.choice(CAPE_COLORS)
    parent_type = args.parent or rng.choice(["mother", "father"])
    prize = rng.choice(PRIZES)
    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        gear=gear_id,
        hero_name=hero_name_value,
        hero_type=hero_type,
        alias=alias,
        rival_name=rival_name,
        rival_type=rival_type,
        cape_color=cape_color,
        parent_type=parent_type,
        prize=prize,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if (params.setting, params.trouble, params.gear) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.setting, params.trouble, params.gear))

    world = tell(
        setting=SETTINGS[params.setting],
        trouble_cfg=TROUBLES[params.trouble],
        gear_cfg=GEARS[params.gear],
        hero_name_value=params.hero_name,
        hero_type=params.hero_type,
        alias=params.alias,
        rival_name=params.rival_name,
        rival_type=params.rival_type,
        cape_color=params.cape_color,
        parent_type=params.parent_type,
        prize=params.prize,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, gear) combos:\n")
        for setting_id, trouble_id, gear_id in combos:
            print(f"  {setting_id:8} {trouble_id:10} {gear_id}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.trouble} at {p.setting} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
