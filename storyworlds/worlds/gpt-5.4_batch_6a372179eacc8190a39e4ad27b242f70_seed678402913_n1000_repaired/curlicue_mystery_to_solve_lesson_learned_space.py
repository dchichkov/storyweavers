#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/curlicue_mystery_to_solve_lesson_learned_space.py
============================================================================

A standalone story world about a small space-age mystery: two young cadets spot
a strange curlicue clue, imagine something dramatic, then learn to slow down,
check the evidence, and fix the real problem the sensible way.

The world model stays intentionally small:
- a clue appears because of a physical cause
- the children react with wonder and worry
- a helper recommends the right investigation tool
- the tool reveals the cause and guides the fix
- the ending image proves the lesson: clues first, guesses second

Run it
------
    python storyworlds/worlds/gpt-5.4/curlicue_mystery_to_solve_lesson_learned_space.py
    python storyworlds/worlds/gpt-5.4/curlicue_mystery_to_solve_lesson_learned_space.py --clue frost --cause vent_leak
    python storyworlds/worlds/gpt-5.4/curlicue_mystery_to_solve_lesson_learned_space.py --tool star_net
    python storyworlds/worlds/gpt-5.4/curlicue_mystery_to_solve_lesson_learned_space.py --all --qa
    python storyworlds/worlds/gpt-5.4/curlicue_mystery_to_solve_lesson_learned_space.py --verify
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
    traits: list[str] = field(default_factory=list)
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
        return self.label or self.type


@dataclass
class Mission:
    id: str
    place: str
    sky: str
    job: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    site: str
    opening: str
    pattern: str
    signal: str
    danger_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    makes: set[str]
    risk: str
    reveal: str
    fix: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    detects: set[str]
    repairs: set[str]
    method: str
    lesson_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mission: str
    clue: str
    cause: str
    tool: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    helper_type: str
    trait: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue_from_cause(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    cause = world.get("cause")
    signal = clue.attrs.get("signal", "")
    if signal and signal in cause.attrs.get("makes", set()):
        sig = ("clue_from_cause", signal)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["present"] += 1
            world.get("station").meters["trouble"] += 1
            out.append("__clue__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["present"] < THRESHOLD:
        return out
    for kid_id in ("hero", "partner"):
        kid = world.get(kid_id)
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["wonder"] += 1
        kid.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_scan_reveals(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    clue = world.get("clue")
    cause = world.get("cause")
    signal = clue.attrs.get("signal", "")
    cause_id = cause.attrs.get("cause_id", "")
    if tool.meters["used"] < THRESHOLD:
        return out
    if signal in tool.attrs.get("detects", set()):
        sig = ("reveal", signal, cause_id)
        if sig not in world.fired:
            world.fired.add(sig)
            cause.meters["known"] += 1
            world.get("station").meters["understood"] += 1
            world.get("hero").memes["care"] += 1
            world.get("partner").memes["care"] += 1
            out.append("__reveal__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    cause = world.get("cause")
    cause_id = cause.attrs.get("cause_id", "")
    if cause.meters["known"] < THRESHOLD:
        return out
    if cause_id in tool.attrs.get("repairs", set()):
        sig = ("fix", cause_id)
        if sig not in world.fired:
            world.fired.add(sig)
            cause.meters["fixed"] += 1
            world.get("station").meters["trouble"] = 0.0
            world.get("station").meters["safe"] += 1
            world.get("hero").memes["relief"] += 1
            world.get("partner").memes["relief"] += 1
            out.append("__fix__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="clue_from_cause", tag="physical", apply=_r_clue_from_cause),
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="scan_reveals", tag="knowledge", apply=_r_scan_reveals),
    Rule(name="fix", tag="physical", apply=_r_fix),
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
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


MISSIONS = {
    "moon_lab": Mission(
        id="moon_lab",
        place="the moon-window hall of the little lab",
        sky="Outside, black space held the moon rocks still and silver.",
        job="checking the station before bedtime",
        ending="through the window, the quiet moon looked friendly again",
        tags={"moon", "station"},
    ),
    "ring_garden": Mission(
        id="ring_garden",
        place="the clear dome above the ring garden",
        sky="Beyond the glass, the stars curled around the planet's bright rings.",
        job="making sure the garden dome was ready for morning light",
        ending="the ringed planet shone softly above the sleeping plants",
        tags={"planet", "garden"},
    ),
    "comet_deck": Mission(
        id="comet_deck",
        place="the small lookout deck near the comet maps",
        sky="Far away, a pale comet trailed a white ribbon across the dark.",
        job="tidying the deck after map practice",
        ending="the comet glimmered like a slow white brushstroke in the sky",
        tags={"comet", "deck"},
    ),
}

CLUES = {
    "frost": Clue(
        id="frost",
        label="frost swirl",
        site="the window",
        opening="a pale curlicue of frost on the inside of the window",
        pattern="The line looped and twirled like a tiny silver snail trail.",
        signal="cold_leak",
        danger_hint="If cold air kept slipping in, the room could get too chilly for the plants and people.",
        tags={"frost", "cold"},
    ),
    "dust": Clue(
        id="dust",
        label="dust spiral",
        site="the air grate",
        opening="a gray curlicue of dust beside the air grate",
        pattern="It looked as if an invisible finger had drawn a spiral in the powder.",
        signal="air_whirl",
        danger_hint="If the air moved the wrong way, the room could not stay fresh and clean.",
        tags={"dust", "air"},
    ),
    "sparkles": Clue(
        id="sparkles",
        label="sparkle ribbon",
        site="the light panel",
        opening="a golden curlicue of sparkles across the light panel",
        pattern="The tiny dots curved in a bright ribbon instead of shining in a straight line.",
        signal="power_skip",
        danger_hint="If the power skipped too long, the lights could blink out during the night shift.",
        tags={"sparkle", "power"},
    ),
}

CAUSES = {
    "vent_leak": Cause(
        id="vent_leak",
        label="loose vent seal",
        phrase="a loose seal around the cold-air vent",
        makes={"cold_leak"},
        risk="cold air slipping where it did not belong",
        reveal="The cold scanner showed a thin blue thread sneaking from a vent seal.",
        fix="clicked the vent seal snug again",
        ending_image="No new frost curls grew on the glass.",
        tags={"vent", "cold"},
    ),
    "fan_fluff": Cause(
        id="fan_fluff",
        label="linty fan",
        phrase="a fan stuffed with soft gray fluff",
        makes={"air_whirl"},
        risk="air swirling the wrong way through the room",
        reveal="The airflow reader blinked over one fan packed with lint like dusty wool.",
        fix="lifted the panel and brushed the fan clean until it could spin freely",
        ending_image="The grate hummed in a smooth, even breath.",
        tags={"fan", "air"},
    ),
    "battery_jiggle": Cause(
        id="battery_jiggle",
        label="wobbly battery latch",
        phrase="a battery latch that had slipped sideways",
        makes={"power_skip"},
        risk="lights flickering when the station needed steady power",
        reveal="The power wand flashed red beside a battery latch that was not sitting flat.",
        fix="pressed the latch back into place until it gave a neat little click",
        ending_image="The light panel glowed in one calm golden sheet.",
        tags={"battery", "power"},
    ),
}

TOOLS = {
    "cold_scanner": Tool(
        id="cold_scanner",
        label="cold scanner",
        phrase="the cold scanner",
        detects={"cold_leak"},
        repairs={"vent_leak"},
        method="It painted chilly places blue, so hidden drafts could not keep pretending to be a mystery.",
        lesson_line="Good space explorers do not guess first. They read the signs and use the right tool.",
        tags={"scanner", "cold"},
    ),
    "airflow_reader": Tool(
        id="airflow_reader",
        label="airflow reader",
        phrase="the airflow reader",
        detects={"air_whirl"},
        repairs={"fan_fluff"},
        method="Its little ribbons showed which way the air was truly moving.",
        lesson_line="Good space explorers do not chase wild ideas. They follow the clue that the world is giving them.",
        tags={"reader", "air"},
    ),
    "power_wand": Tool(
        id="power_wand",
        label="power wand",
        phrase="the power wand",
        detects={"power_skip"},
        repairs={"battery_jiggle"},
        method="It blinked wherever power was hopping instead of flowing smoothly.",
        lesson_line="Good space explorers slow down when something seems strange. Careful checking beats fancy guessing.",
        tags={"wand", "power"},
    ),
    "star_net": Tool(
        id="star_net",
        label="star net",
        phrase="the star net",
        detects=set(),
        repairs=set(),
        method="It was wonderful for catching toy meteors, but terrible at solving station problems.",
        lesson_line="A tool should match the job.",
        tags={"toy"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Ava", "Nora", "Zoe", "Ivy", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Kai", "Milo", "Ben", "Eli", "Theo"]
TRAITS = ["careful", "curious", "bright", "thoughtful", "steady", "brave"]


def cause_matches_clue(clue: Clue, cause: Cause) -> bool:
    return clue.signal in cause.makes


def tool_fits(clue: Clue, cause: Cause, tool: Tool) -> bool:
    return clue.signal in tool.detects and cause.id in tool.repairs


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for clue_id, clue in CLUES.items():
            for cause_id, cause in CAUSES.items():
                if not cause_matches_clue(clue, cause):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_fits(clue, cause, tool):
                        combos.append((mission_id, clue_id, cause_id, tool_id))
    return combos


def explain_bad_cause(clue: Clue, cause: Cause) -> str:
    return (
        f"(No story: {clue.label} points to {clue.signal.replace('_', ' ')}, but "
        f"{cause.phrase} would not make that clue. Pick a cause that truly fits the evidence.)"
    )


def explain_bad_tool(clue: Clue, cause: Cause, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot read {clue.label} and cannot fix {cause.label}. "
        f"A mystery story should use a tool that matches both the clue and the repair.)"
    )


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("tool").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "understood": sim.get("cause").meters["known"] >= THRESHOLD,
        "fixed": sim.get("cause").meters["fixed"] >= THRESHOLD,
        "safe": sim.get("station").meters["safe"] >= THRESHOLD,
    }


def introduce(world: World, mission: Mission, hero: Entity, partner: Entity, helper: Entity) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{hero.id} and {partner.id} were junior space cadets {mission.job} in {mission.place}."
    )
    world.say(mission.sky)
    world.say(
        f"With them floated {helper.label}, a small helper robot with a soft lamp for a nose."
    )


def notice_clue(world: World, clue: Clue, hero: Entity, partner: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} stopped. On {clue.site} was {clue.opening}."
    )
    world.say(clue.pattern)
    world.say(
        f'"Do you see that?" {hero.id} whispered. "{partner.id}, it was not there before."'
    )


def imagine_big_guess(world: World, clue: Clue, hero: Entity, partner: Entity) -> None:
    hero.memes["dramatic_guess"] += 1
    partner.memes["worry"] += 1
    world.say(
        f'{hero.id} leaned close and said, "Maybe a tiny comet ghost drew it."'
    )
    world.say(
        f'{partner.id} looked at the strange curl and felt a flutter in {partner.pronoun("possessive")} tummy.'
    )
    world.say(clue.danger_hint)


def helper_advises(world: World, tool: Tool, helper: Entity) -> None:
    pred = predict_solution(world)
    world.facts["predicted_understood"] = pred["understood"]
    world.facts["predicted_fixed"] = pred["fixed"]
    helper.memes["calm"] += 1
    world.say(
        f'{helper.label} gave a gentle beep. "Mystery note: begin with evidence. Let us fetch {tool.phrase}," it said.'
    )
    world.say(tool.method)


def investigate(world: World, tool: Tool, hero: Entity, partner: Entity) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    hero.memes["care"] += 1
    partner.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} carried {tool.phrase}, and {partner.id} held the light steady."
    )


def reveal(world: World, cause: Cause, tool: Tool, hero: Entity, partner: Entity) -> None:
    world.say(cause.reveal)
    world.say(
        f'"So it was {cause.phrase}," {partner.id} said. "{hero.id}, it only looked spooky because we did not know the reason yet."'
    )
    world.say(
        f"{hero.id} nodded. The mystery felt smaller now that it had a true name."
    )


def repair(world: World, cause: Cause, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Working slowly with {helper.label} beside {hero.pronoun('object')}, {hero.id} {cause.fix}."
    )
    world.say(cause.ending_image)


def lesson(world: World, tool: Tool, hero: Entity, partner: Entity) -> None:
    hero.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    hero.memes["worry"] = 0.0
    partner.memes["worry"] = 0.0
    world.say(
        f'"I almost called it a comet ghost," {hero.id} admitted with a shy smile.'
    )
    world.say(
        f'"And then we checked the clue first," {partner.id} said.'
    )
    world.say(tool.lesson_line)


def ending(world: World, mission: Mission, hero: Entity, partner: Entity) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"When the work was done, {hero.id} traced a curlicue in the air with one finger, just for fun."
    )
    world.say(
        f'"Next time we see something strange," {partner.id} said, "we will be brave enough to look closely before we guess."'
    )
    world.say(
        f"Hand in hand, the two cadets watched the stars, and {mission.ending}."
    )


def tell(
    mission: Mission,
    clue: Clue,
    cause: Cause,
    tool: Tool,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    partner_name: str = "Owen",
    partner_gender: str = "boy",
    helper_type: str = "robot",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        phrase=partner_name,
        role="partner",
        traits=["kind"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="Orbit",
        phrase="Orbit",
        role="helper",
        traits=["calm"],
    ))
    station = world.add(Entity(
        id="station",
        kind="thing",
        type="station",
        label="station",
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        attrs={"signal": clue.signal, "site": clue.site},
        tags=set(clue.tags),
    ))
    cause_ent = world.add(Entity(
        id="cause",
        kind="thing",
        type="cause",
        label=cause.label,
        attrs={"makes": set(cause.makes), "cause_id": cause.id},
        tags=set(cause.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        attrs={"detects": set(tool.detects), "repairs": set(tool.repairs)},
        tags=set(tool.tags),
    ))

    introduce(world, mission, hero, partner, helper)
    world.para()
    notice_clue(world, clue, hero, partner)
    imagine_big_guess(world, clue, hero, partner)
    helper_advises(world, tool, helper)
    world.para()
    investigate(world, tool, hero, partner)
    reveal(world, cause, tool, hero, partner)
    repair(world, cause, hero, helper)
    world.para()
    lesson(world, tool, hero, partner)
    ending(world, mission, hero, partner)

    world.facts.update(
        mission=mission,
        clue_cfg=clue,
        cause_cfg=cause,
        tool_cfg=tool,
        hero=hero,
        partner=partner,
        helper=helper,
        station=station,
        clue=clue_ent,
        cause=cause_ent,
        tool=tool_ent,
        solved=cause_ent.meters["fixed"] >= THRESHOLD,
        understood=cause_ent.meters["known"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    clue = f["clue_cfg"]
    mission = f["mission"]
    tool = f["tool_cfg"]
    return [
        'Write a short space-adventure story for a 3-to-5-year-old that includes the word "curlicue" and a small mystery to solve.',
        f"Tell a gentle space mystery where {hero.label} and {partner.label} find {clue.opening} in {mission.place}, fear something dramatic, then solve it with {tool.phrase}.",
        "Write a child-facing story with a lesson learned: when something strange appears, look for clues before making wild guesses.",
    ]


KNOWLEDGE = {
    "frost": [
        (
            "What is frost?",
            "Frost is a thin layer of tiny ice crystals. It can appear when something is very cold."
        )
    ],
    "air": [
        (
            "What does a vent do?",
            "A vent lets air move in or out of a room. Good air flow helps a place stay comfortable."
        )
    ],
    "dust": [
        (
            "Why is dust a problem in a fan?",
            "Dust can clog the moving parts and make the fan work badly. Then the air does not move the way it should."
        )
    ],
    "power": [
        (
            "Why do lights need steady power?",
            "Lights need power flowing smoothly to stay bright. If the power skips, the lights can blink or go dim."
        )
    ],
    "scanner": [
        (
            "What does a scanner do?",
            "A scanner helps you notice something your eyes might miss. It is a tool for checking clues carefully."
        )
    ],
    "tool": [
        (
            "Why should you use the right tool?",
            "The right tool matches the job you are doing. A wrong tool can waste time and leave the problem unfixed."
        )
    ],
    "lesson": [
        (
            "What is a good thing to do when something seems strange?",
            "Take a breath and look for clues first. Careful checking can turn a scary mystery into a problem you can understand."
        )
    ],
}
KNOWLEDGE_ORDER = ["frost", "air", "dust", "power", "scanner", "tool", "lesson"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    clue = f["clue_cfg"]
    cause = f["cause_cfg"]
    tool = f["tool_cfg"]
    mission = f["mission"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two junior space cadets, {hero.label} and {partner.label}, and their helper robot Orbit. They were checking the station together."
        ),
        (
            "What was the mystery?",
            f"They found {clue.opening}. It looked strange, so at first it felt like something spooky or surprising might have happened."
        ),
        (
            f"Why did the curlicue clue matter?",
            f"It mattered because it was a sign that something in the station was not working right. The clue pointed toward {cause.risk}, so the children needed to understand it instead of ignoring it."
        ),
        (
            f"How did they solve the mystery?",
            f"They used {tool.phrase} to check the clue instead of guessing. That helped them discover {cause.phrase} and fix the real problem."
        ),
        (
            "What lesson did they learn?",
            f"They learned to look closely at evidence before making a dramatic guess. Once they slowed down and checked the clue, the mystery became clear and fixable."
        ),
        (
            "How did the story end?",
            f"The station was safe again, and the scary feeling was gone. In the quiet ending, they watched the stars and felt proud that careful thinking had helped them."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue_cfg"]
    cause = f["cause_cfg"]
    tool = f["tool_cfg"]
    tags: set[str] = {"lesson", "tool"}
    if clue.id == "frost":
        tags |= {"frost", "scanner"}
    if clue.id == "dust" or cause.id == "fan_fluff":
        tags |= {"dust", "air"}
    if clue.id == "sparkles" or cause.id == "battery_jiggle":
        tags |= {"power"}
    if tool.id in {"cold_scanner", "airflow_reader", "power_wand"}:
        tags |= {"scanner"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {}
            for k, v in e.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                else:
                    shown[k] = v
            bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon_lab",
        clue="frost",
        cause="vent_leak",
        tool="cold_scanner",
        hero="Lina",
        hero_gender="girl",
        partner="Owen",
        partner_gender="boy",
        helper_type="robot",
        trait="careful",
    ),
    StoryParams(
        mission="ring_garden",
        clue="dust",
        cause="fan_fluff",
        tool="airflow_reader",
        hero="Mira",
        hero_gender="girl",
        partner="Finn",
        partner_gender="boy",
        helper_type="robot",
        trait="curious",
    ),
    StoryParams(
        mission="comet_deck",
        clue="sparkles",
        cause="battery_jiggle",
        tool="power_wand",
        hero="Theo",
        hero_gender="boy",
        partner="Nora",
        partner_gender="girl",
        helper_type="robot",
        trait="bright",
    ),
]


ASP_RULES = r"""
clue_matches(C, K) :- clue(C), cause(K), signal(C, S), makes(K, S).
tool_fits(T, C, K) :- tool(T), clue(C), cause(K),
                      signal(C, S), detects(T, S), repairs(T, K).
valid(M, C, K, T) :- mission(M), clue(C), cause(K), tool(T),
                     clue_matches(C, K), tool_fits(T, C, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("signal", clue_id, clue.signal))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for sig in sorted(cause.makes):
            lines.append(asp.fact("makes", cause_id, sig))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for sig in sorted(tool.detects):
            lines.append(asp.fact("detects", tool_id, sig))
        for rep in sorted(tool.repairs):
            lines.append(asp.fact("repairs", tool_id, rep))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_test_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "curlicue" not in sample.story:
        raise StoryError("Smoke test failed: generated story missing expected content.")
    emit(sample, trace=False, qa=False, header="")


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
        smoke_test_generation()
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    try:
        rng = random.Random(7)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 7
        sample = generate(params)
        if not sample.story:
            raise StoryError("Generated empty story.")
        print("OK: random generation passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small space mystery, a clue, and a careful lesson."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.cause:
        if not cause_matches_clue(CLUES[args.clue], CAUSES[args.cause]):
            raise StoryError(explain_bad_cause(CLUES[args.clue], CAUSES[args.cause]))
    if args.clue and args.cause and args.tool:
        if not tool_fits(CLUES[args.clue], CAUSES[args.cause], TOOLS[args.tool]):
            raise StoryError(explain_bad_tool(CLUES[args.clue], CAUSES[args.cause], TOOLS[args.tool]))
    if args.tool and not any(tool_id == args.tool for (_, _, _, tool_id) in valid_combos()):
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
        raise StoryError(explain_bad_tool(clue, cause, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.clue is None or combo[1] == args.clue)
        and (args.cause is None or combo[2] == args.cause)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, clue_id, cause_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or _pick_name(rng, hero_gender)
    partner_name = args.partner or _pick_name(rng, partner_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    return StoryParams(
        mission=mission_id,
        clue=clue_id,
        cause=cause_id,
        tool=tool_id,
        hero=hero_name,
        hero_gender=hero_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper_type="robot",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.cause not in CAUSES:
        raise StoryError(f"Unknown cause: {params.cause}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")

    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    tool = TOOLS[params.tool]
    if not cause_matches_clue(clue, cause):
        raise StoryError(explain_bad_cause(clue, cause))
    if not tool_fits(clue, cause, tool):
        raise StoryError(explain_bad_tool(clue, cause, tool))

    world = tell(
        mission=MISSIONS[params.mission],
        clue=clue,
        cause=cause,
        tool=tool,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, clue, cause, tool) combos:\n")
        for mission_id, clue_id, cause_id, tool_id in combos:
            print(f"  {mission_id:11} {clue_id:9} {cause_id:15} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.partner}: {p.clue} -> {p.cause} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
