#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py
==================================================================

A standalone story world for gentle, child-facing space adventures where two
young explorers meet one tricky obstacle, use the right automatic helper, and
solve the mission through friendship.

The tiny domain is deliberately narrow and constraint-checked:

* each mission has one setting, one obstacle, and one automatic helper
* only some helpers sensibly fit some obstacles
* the emotional turn comes from a friend helping at the exact hard moment
* the ending image shows that the friendship changed how the mission felt

Run it
------
    python storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py
    python storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py --setting moon_dome --obstacle dark_tunnel
    python storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py --helper automatic_lift_pad
    python storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/automatic_friendship_space_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives in storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up from here.
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    sky: str
    goal: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    kind: str
    warning: str
    danger: str
    team_act: str
    solved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    wake: str = ""
    action: str = ""
    qa_text: str = ""
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
        clone = World()
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


def _r_rush_risk(world: World) -> list[str]:
    out: list[str] = []
    lead = world.entities.get("lead")
    path = world.entities.get("path")
    if lead is None or path is None:
        return out
    if lead.memes["rushing"] < THRESHOLD or path.meters["blocked"] < THRESHOLD:
        return out
    sig = ("rush_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead.memes["fear"] += 1
    path.meters["risk"] += 1
    partner = world.entities.get("partner")
    if partner is not None:
        partner.memes["care"] += 1
    out.append("__risk__")
    return out


def _r_helper_opens(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    obstacle = world.entities.get("obstacle")
    path = world.entities.get("path")
    if helper is None or obstacle is None or path is None:
        return out
    if helper.meters["active"] < THRESHOLD or path.meters["open"] >= THRESHOLD:
        return out
    fixes = set(helper.attrs.get("fixes", set()))
    if obstacle.attrs.get("kind") not in fixes:
        return out
    sig = ("open", helper.id, obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["open"] += 1
    path.meters["blocked"] = 0.0
    out.append("__open__")
    return out


def _r_friendship_lifts(world: World) -> list[str]:
    out: list[str] = []
    lead = world.entities.get("lead")
    partner = world.entities.get("partner")
    path = world.entities.get("path")
    if lead is None or partner is None or path is None:
        return out
    if partner.memes["helping"] < THRESHOLD or path.meters["open"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead.memes["fear"] = 0.0
    lead.memes["confidence"] += 1
    partner.memes["confidence"] += 1
    lead.memes["friendship"] += 1
    partner.memes["friendship"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [
    Rule(name="rush_risk", tag="social", apply=_r_rush_risk),
    Rule(name="helper_opens", tag="physical", apply=_r_helper_opens),
    Rule(name="friendship_lifts", tag="emotional", apply=_r_friendship_lifts),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def helper_fits(obstacle: Obstacle, helper: Helper) -> bool:
    return obstacle.kind in helper.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for oid, obstacle in OBSTACLES.items():
            for hid, helper in HELPERS.items():
                if helper_fits(obstacle, helper):
                    combos.append((sid, oid, hid))
    return combos


def predict_risk(world: World) -> dict:
    sim = world.copy()
    lead = sim.get("lead")
    lead.memes["rushing"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("path").meters["risk"],
        "fear": lead.memes["fear"],
    }


def introduce(world: World, lead: Entity, partner: Entity, setting: Setting) -> None:
    lead.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{setting.opening} {lead.id} and {partner.id} were space friends on a mission in {setting.place}."
    )
    world.say(
        f"They wore shiny boots, counted stars in {setting.sky}, and promised to find {setting.goal} before snack time."
    )


def discover(world: World, lead: Entity, partner: Entity, obstacle: Obstacle, setting: Setting) -> None:
    path = world.get("path")
    path.meters["blocked"] += 1
    world.say(
        f"At the end of a silver path, they saw {setting.goal}. But {obstacle.warning}"
    )
    world.say(
        f'{lead.id} leaned forward at once. "We are almost there," {lead.pronoun()} said.'
    )
    world.say(
        f'{partner.id} looked carefully and whispered, "{obstacle.danger}"'
    )


def rush(world: World, lead: Entity, partner: Entity) -> None:
    lead.memes["rushing"] += 1
    propagate(world, narrate=False)
    if lead.memes["fear"] >= THRESHOLD:
        world.say(
            f"{lead.id} took one quick step by {lead.pronoun('object')}self, then stopped. The hard moment suddenly felt much bigger."
        )
        world.say(
            f"{partner.id} saw {lead.pronoun('possessive')} brave face wobble and hurried closer."
        )
    else:
        world.say(f"{lead.id} started forward, eager to finish first.")


def wake_helper(world: World, partner: Entity, helper: Entity, helper_cfg: Helper) -> None:
    helper.meters["active"] += 1
    partner.memes["helping"] += 1
    world.say(
        f'{partner.id} tapped the side of {helper_cfg.phrase}. "Wake up, little helper," {partner.pronoun()} said.'
    )
    world.say(helper_cfg.wake)
    propagate(world, narrate=False)


def teamwork(world: World, lead: Entity, partner: Entity, obstacle: Obstacle, helper_cfg: Helper) -> None:
    world.say(helper_cfg.action)
    world.say(
        f"Then {partner.id} {obstacle.team_act}, and {lead.id} stayed close instead of pretending not to need help."
    )
    propagate(world, narrate=False)
    world.say(obstacle.solved_text)
    world.say(
        f"By the time they reached {world.facts['setting'].goal}, the mission felt easier because they were doing it together."
    )


def celebrate(world: World, lead: Entity, partner: Entity, setting: Setting, helper_cfg: Helper) -> None:
    lead.memes["joy"] += 1
    partner.memes["joy"] += 1
    lead.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f'They found {setting.goal} at last, and it glowed softly beside them. "{helper_cfg.label.capitalize()} helped," {lead.id} said, "but friendship helped most."'
    )
    world.say(
        f"{partner.id} smiled and bumped helmets with {lead.id}. Behind them, {setting.ending_image}."
    )


def tell(
    setting: Setting,
    obstacle_cfg: Obstacle,
    helper_cfg: Helper,
    *,
    lead_name: str = "Nova",
    lead_type: str = "girl",
    partner_name: str = "Milo",
    partner_type: str = "boy",
    parent_type: str = "mother",
    pet_name: str = "",
) -> World:
    world = World()
    lead = world.add(Entity(id="lead", kind="character", type=lead_type, label=lead_name, role="lead"))
    partner = world.add(Entity(id="partner", kind="character", type=partner_type, label=partner_name, role="partner"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    helper = world.add(
        Entity(
            id="helper",
            kind="thing",
            type="robot",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            role="helper",
            attrs={"fixes": set(helper_cfg.fixes)},
            tags=set(helper_cfg.tags),
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle_cfg.label,
            role="obstacle",
            attrs={"kind": obstacle_cfg.kind},
            tags=set(obstacle_cfg.tags),
        )
    )
    path = world.add(Entity(id="path", kind="thing", type="path", label="the path", role="path"))

    lead.id = lead_name
    partner.id = partner_name
    parent.id = parent.title_word.capitalize()
    world.entities["lead"] = lead
    world.entities["partner"] = partner
    world.entities["parent"] = parent

    world.facts["setting"] = setting
    world.facts["obstacle_cfg"] = obstacle_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["pet_name"] = pet_name

    introduce(world, lead, partner, setting)
    world.para()
    discover(world, lead, partner, obstacle_cfg, setting)
    rush(world, lead, partner)
    world.para()
    wake_helper(world, partner, helper, helper_cfg)
    teamwork(world, lead, partner, obstacle_cfg, helper_cfg)
    world.para()
    celebrate(world, lead, partner, setting, helper_cfg)

    if pet_name:
        world.say(f"Even {pet_name} gave a happy little bounce in the cargo basket.")

    world.facts.update(
        lead=lead,
        partner=partner,
        parent=parent,
        helper=helper,
        obstacle=obstacle,
        path=path,
        solved=path.meters["open"] >= THRESHOLD,
        frightened=lead.memes["fear"] <= 0.0 and world.get("path").meters["risk"] >= THRESHOLD,
        risk_seen=world.get("path").meters["risk"] >= THRESHOLD,
        friendship_grew=lead.memes["friendship"] >= THRESHOLD and partner.memes["friendship"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_dome": Setting(
        id="moon_dome",
        place="the Moon Marble Dome",
        opening="One bright morning under a bubble roof,",
        sky="the black velvet sky",
        goal="the singing star shell",
        ending_image="the moon dust shone with tiny blue sparkles",
        tags={"moon", "space"},
    ),
    "comet_cave": Setting(
        id="comet_cave",
        place="the Comet Ice Cave",
        opening="Far from Earth, near a slow sleepy comet,",
        sky="the glittering tail outside the cave",
        goal="the rainbow ice badge",
        ending_image="the icy walls blinked back little rainbow dots",
        tags={"comet", "space"},
    ),
    "ring_garden": Setting(
        id="ring_garden",
        place="the Ring Garden Station",
        opening="On a spinning garden station above the clouds,",
        sky="the curved rings outside the window",
        goal="the golden seed pod",
        ending_image="the glass leaves hummed in the warm star light",
        tags={"station", "space"},
    ),
}

OBSTACLES = {
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="dark tunnel",
        kind="dark",
        warning="a tunnel ahead was so dark that even the floor line had disappeared.",
        danger="If we rush in, we might miss the path.",
        team_act="reached out a steady hand so nobody had to walk alone",
        solved_text="A clean line of light spread over the floor, and the dark tunnel turned from spooky to safe.",
        tags={"dark", "tunnel"},
    ),
    "high_ledge": Obstacle(
        id="high_ledge",
        label="high ledge",
        kind="high",
        warning="a high ledge rose above them, much too tall for one quick hop.",
        danger="If we jump alone, we could slip back down.",
        team_act="pushed gently from below while cheering the whole way up",
        solved_text="The climb became a smooth little ride, and soon the high ledge felt like a staircase instead of a wall.",
        tags={"ledge", "climb"},
    ),
    "jammed_hatch": Obstacle(
        id="jammed_hatch",
        label="jammed hatch",
        kind="jammed",
        warning="a round silver hatch had stuck shut with a grumpy clunk.",
        danger="If one of us pulls alone, it may not open at all.",
        team_act="pressed the second shining button at the same time",
        solved_text="The hatch gave a happy click, then swung open as neatly as a storybook door.",
        tags={"hatch", "door"},
    ),
}

HELPERS = {
    "automatic_lantern_rover": Helper(
        id="automatic_lantern_rover",
        label="automatic lantern rover",
        phrase="the automatic lantern rover",
        fixes={"dark"},
        wake="Its tiny wheels hummed, and a warm beam rolled out in front of it.",
        action="The automatic lantern rover zipped ahead and painted a bright trail along the tunnel floor.",
        qa_text="used the automatic lantern rover to light the way",
        tags={"automatic", "robot", "light"},
    ),
    "automatic_lift_pad": Helper(
        id="automatic_lift_pad",
        label="automatic lift pad",
        phrase="the automatic lift pad",
        fixes={"high"},
        wake="The pad unfolded with a soft whirr and blinked a green ready-light.",
        action="The automatic lift pad rose slowly with a gentle whoosh, steady as a floating step.",
        qa_text="used the automatic lift pad to rise to the ledge",
        tags={"automatic", "machine", "lift"},
    ),
    "automatic_repair_drone": Helper(
        id="automatic_repair_drone",
        label="automatic repair drone",
        phrase="the automatic repair drone",
        fixes={"jammed"},
        wake="A tiny silver arm popped out, and the drone chirped as if it already knew the job.",
        action="The automatic repair drone oiled the stiff hatch wheel and blinked for them to press the buttons together.",
        qa_text="used the automatic repair drone to loosen the hatch",
        tags={"automatic", "robot", "repair"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zuri", "Ayla", "Tess", "Ivy", "Kira"]
BOY_NAMES = ["Milo", "Leo", "Finn", "Orion", "Jules", "Nico", "Theo", "Kai"]
PETS = ["the tiny moon mouse", "the sleepy space puppy", "the round robot kitten", ""]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    helper: str
    lead_name: str
    lead_type: str
    partner_name: str
    partner_type: str
    parent_type: str
    pet_name: str = ""
    seed: Optional[int] = None


KNOWLEDGE = {
    "automatic": [
        (
            "What does automatic mean?",
            "Automatic means something can do part of its job by itself once it is turned on. A person still needs to use it safely and wisely.",
        )
    ],
    "robot": [
        (
            "What is a robot helper?",
            "A robot helper is a machine made to do certain jobs. It can follow simple steps, but people still choose what kind thing to do.",
        )
    ],
    "light": [
        (
            "Why does a dark tunnel feel safer with light?",
            "Light helps you see where the floor and walls are. When you can see clearly, it is easier to walk safely and stay calm.",
        )
    ],
    "lift": [
        (
            "What does a lift do?",
            "A lift moves someone up or down without a hard jump. It helps reach a high place in a steady way.",
        )
    ],
    "repair": [
        (
            "What does a repair drone do?",
            "A repair drone helps fix small machine problems, like a stiff wheel or a stuck latch. It works best when people use it carefully.",
        )
    ],
    "friendship": [
        (
            "How can friendship help on a hard day?",
            "A friend can stay close, share ideas, and help you feel brave. Problems often feel smaller when you solve them together.",
        )
    ],
    "space": [
        (
            "What is a space station?",
            "A space station is a place built for people to live or work high above Earth. Stories often imagine them as bright homes among the stars.",
        )
    ],
    "moon": [
        (
            "What is the moon?",
            "The moon is the big round world that circles Earth. It shines because sunlight reflects off its dusty ground.",
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a chunk of ice and dust that travels through space. When it gets warm, it can grow a glowing tail.",
        )
    ],
}

KNOWLEDGE_ORDER = ["automatic", "robot", "light", "lift", "repair", "friendship", "space", "moon", "comet"]


def pair_noun(lead: Entity, partner: Entity) -> str:
    if lead.type == "girl" and partner.type == "girl":
        return "two friends"
    if lead.type == "boy" and partner.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    setting = f["setting"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    return [
        f'Write a short story for a 3-to-5-year-old in a Space Adventure style that includes the word "automatic".',
        f"Tell a gentle space mission story where {lead.id} and {partner.id} meet a {obstacle.label}, use {helper.phrase}, and learn that friendship helps more than showing off.",
        f"Write a child-facing adventure set in {setting.place} where one friend feels unsure, the other friend helps, and the ending shows they reached {setting.goal} together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    setting = f["setting"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(lead, partner)}, {lead.id} and {partner.id}, on a mission in {setting.place}. They are space friends who work together.",
        ),
        (
            "What were they trying to find?",
            f"They were trying to find {setting.goal}. That goal is what led them all the way to the tricky obstacle.",
        ),
        (
            f"What problem stopped them?",
            f"A {obstacle.label} stopped them on the path. It made the mission feel hard because it was not safe or easy for one child to handle alone.",
        ),
    ]
    if f.get("risk_seen"):
        qa.append(
            (
                f"Why did {lead.id} stop after rushing forward?",
                f"{lead.id} stopped because the problem suddenly felt scary and risky up close. The hard part looked bigger when {lead.pronoun()} tried to face it alone.",
            )
        )
    qa.append(
        (
            f"How did {partner.id} help?",
            f"{partner.id} woke {helper.phrase} and stayed close to {lead.id}. Then {partner.pronoun()} helped with the mission itself, so the plan worked because of both the machine and the friendship.",
        )
    )
    qa.append(
        (
            f"How did they solve the problem?",
            f"They {helper.qa_text}. After that, they finished the last hard part together instead of one child pretending to be brave alone.",
        )
    )
    if f.get("friendship_grew"):
        qa.append(
            (
                "What changed by the end of the story?",
                f"At the end, the obstacle was open and the children felt braver together. The mission changed from a lonely hard moment into a happy shared adventure.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"friendship"} | set(f["helper_cfg"].tags) | set(f["setting"].tags)
    if f["obstacle_cfg"].kind == "dark":
        tags.add("light")
    if f["obstacle_cfg"].kind == "high":
        tags.add("lift")
    if f["obstacle_cfg"].kind == "jammed":
        tags.add("repair")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for key in ["lead", "partner", "helper", "obstacle", "path"]:
        ent = world.entities.get(key)
        if ent is None:
            continue
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_dome",
        obstacle="dark_tunnel",
        helper="automatic_lantern_rover",
        lead_name="Nova",
        lead_type="girl",
        partner_name="Milo",
        partner_type="boy",
        parent_type="mother",
        pet_name="the tiny moon mouse",
    ),
    StoryParams(
        setting="comet_cave",
        obstacle="high_ledge",
        helper="automatic_lift_pad",
        lead_name="Finn",
        lead_type="boy",
        partner_name="Luna",
        partner_type="girl",
        parent_type="father",
        pet_name="the sleepy space puppy",
    ),
    StoryParams(
        setting="ring_garden",
        obstacle="jammed_hatch",
        helper="automatic_repair_drone",
        lead_name="Mira",
        lead_type="girl",
        partner_name="Kai",
        partner_type="boy",
        parent_type="mother",
        pet_name="the round robot kitten",
    ),
    StoryParams(
        setting="moon_dome",
        obstacle="high_ledge",
        helper="automatic_lift_pad",
        lead_name="Theo",
        lead_type="boy",
        partner_name="Ayla",
        partner_type="girl",
        parent_type="father",
        pet_name="",
    ),
]


def explain_rejection(obstacle: Obstacle, helper: Helper) -> str:
    needed = obstacle.kind
    have = ", ".join(sorted(helper.fixes))
    return (
        f"(No story: {helper.label} cannot sensibly solve a {obstacle.label}. "
        f"It handles [{have}] obstacles, but this mission needs '{needed}'.)"
    )


ASP_RULES = r"""
fits(O, H) :- obstacle(O), helper(H), fixes(H, K), kind(O, K).
valid(S, O, H) :- setting(S), obstacle(O), helper(H), fits(O, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("kind", oid, obstacle.kind))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for kind in sorted(helper.fixes):
            lines.append(asp.fact("fixes", hid, kind))
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
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        if "automatic" not in sample.story.lower():
            raise StoryError("smoke test story is missing the word 'automatic'")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small space adventure where friendship and the right automatic helper solve one obstacle."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--lead-name")
    ap.add_argument("--partner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, obstacle, helper) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    kind = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if kind == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), kind


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if not helper_fits(obstacle, helper):
            raise StoryError(explain_rejection(obstacle, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, obstacle, helper = rng.choice(sorted(combos))
    lead_name, lead_type = pick_kid(rng)
    partner_name, partner_type = pick_kid(rng, avoid=lead_name)
    return StoryParams(
        setting=setting,
        obstacle=obstacle,
        helper=helper,
        lead_name=args.lead_name or lead_name,
        lead_type=lead_type,
        partner_name=args.partner_name or partner_name,
        partner_type=partner_type,
        parent_type=args.parent or rng.choice(["mother", "father"]),
        pet_name=rng.choice(PETS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if not helper_fits(obstacle, helper):
        raise StoryError(explain_rejection(obstacle, helper))

    world = tell(
        setting=setting,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        lead_name=params.lead_name,
        lead_type=params.lead_type,
        partner_name=params.partner_name,
        partner_type=params.partner_type,
        parent_type=params.parent_type,
        pet_name=params.pet_name,
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
        print(f"{len(combos)} compatible (setting, obstacle, helper) combos:\n")
        for setting, obstacle, helper in combos:
            print(f"  {setting:12} {obstacle:12} {helper}")
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
            header = f"### {p.lead_name} and {p.partner_name}: {p.obstacle} with {p.helper} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
