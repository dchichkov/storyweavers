#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py
=============================================================================

A small storyworld about a child caring for a wee pomegranate plant.

The seed image is simple and heartwarming: a child holds a tiny pomegranate
sprout in a small palm, notices that it is not doing well, and with gentle help
chooses the right kind of care. The world model tracks physical plant needs and
emotional responses, then renders a complete story with a clear setup, turn,
and happy ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py --problem thirst
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py --fix bigger_pot
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/pomegranate_wee_palm_happy_ending_heartwarming.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels to
# the package dir (storyworlds/) before importing results.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "plant" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    light: str
    air: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    need_meter: str
    symptom: str
    clue: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    helps: str
    action: str
    qa_action: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    opening: str
    noticing: str
    ending: str


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_need_worry(world: World) -> list[str]:
    plant = world.get("plant")
    child = world.get("child")
    out: list[str] = []
    if plant.meters["need"] >= THRESHOLD and ("worry", plant.id) not in world.fired:
        world.fired.add(("worry", plant.id))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_help_revive(world: World) -> list[str]:
    plant = world.get("plant")
    child = world.get("child")
    helper = world.get("helper")
    out: list[str] = []
    if helper.meters["used"] < THRESHOLD:
        return out
    if plant.meters["need"] > 0 and ("relief", plant.id) not in world.fired:
        world.fired.add(("relief", plant.id))
        plant.meters["need"] = 0.0
        plant.meters["droop"] = 0.0
        plant.meters["health"] += 1
        plant.meters["new_leaf"] += 1
        child.memes["hope"] += 1
        child.memes["pride"] += 1
        out.append("__revive__")
    return out


CAUSAL_RULES = [
    Rule(name="need_worry", tag="emotion", apply=_r_need_worry),
    Rule(name="help_revive", tag="physical", apply=_r_help_revive),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint logic
# ---------------------------------------------------------------------------
def fix_matches(problem: Problem, fix: Fix) -> bool:
    return problem.need_meter == fix.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for problem_id, problem in PROBLEMS.items():
            for fix_id, fix in FIXES.items():
                for mood_id in MOODS:
                    if fix_matches(problem, fix):
                        combos.append((setting_id, problem_id, fix_id, mood_id))
    return combos


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {fix.id.replace('_', ' ')} does not solve {problem.id}. "
        f"The plant's real need is {problem.need_meter.replace('_', ' ')}, so the fix "
        f"must match that need.)"
    )


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_recovery(world: World, fix: Fix) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    helper = sim.get("helper")
    helper.attrs["fix_id"] = fix.id
    helper.meters["used"] += 1
    plant.meters[fix.helps] = max(0.0, plant.meters[fix.helps] - 1)
    if sum(plant.meters[k] for k in ("thirst", "crowded", "cold")) <= 0:
        plant.meters["need"] = 0.0
    propagate(sim, narrate=False)
    return {
        "recovered": plant.meters["new_leaf"] >= THRESHOLD,
        "health": plant.meters["health"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, elder: Entity, mood: Mood) -> None:
    plant = world.get("plant")
    world.say(
        f"{mood.opening} {child.id} stood beside {child.pronoun('possessive')} "
        f"{elder.label_word} in {world.setting.place}, holding a wee pomegranate "
        f"sprout in {child.pronoun('possessive')} palm."
    )
    world.say(
        f"The little plant was so small it seemed to fit there like a green secret, "
        f"with a thin stem and two brave leaves."
    )
    child.memes["tenderness"] += 1
    child.memes["hope"] += 1
    plant.memes["beloved"] += 1


def promise(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f'"I will take good care of it," {child.id} said. {elder.label_word.capitalize()} '
        f"smiled and touched the back of {child.pronoun('possessive')} hand."
    )
    world.say(
        f'"A little plant listens to gentle hands," {elder.label_word} said.'
    )


def trouble_appears(world: World, child: Entity, elder: Entity, problem: Problem, mood: Mood) -> None:
    plant = world.get("plant")
    plant.meters[problem.need_meter] += 1
    plant.meters["need"] += 1
    plant.meters["droop"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But after a little while, {mood.noticing}. The pomegranate sprout looked "
        f"{problem.symptom}."
    )
    world.say(
        f"{child.id} noticed {problem.clue} and felt a small pinch in "
        f"{child.pronoun('possessive')} chest."
    )


def wonder(world: World, child: Entity, elder: Entity, problem: Problem, fix: Fix) -> None:
    pred = predict_recovery(world, fix)
    world.facts["predicted_recovery"] = pred["recovered"]
    child.memes["curiosity"] += 1
    world.say(
        f'"What is it trying to tell us?" {child.id} whispered.'
    )
    world.say(
        f'{elder.label_word.capitalize()} bent close and looked carefully. '
        f'"{problem.lesson}," {elder.pronoun()} said.'
    )


def choose_fix(world: World, child: Entity, elder: Entity, fix: Fix) -> None:
    helper = world.get("helper")
    helper.attrs["fix_id"] = fix.id
    helper.meters["used"] += 1
    child.memes["care"] += 1
    world.say(
        f"Together they {fix.action}."
    )


def apply_fix(world: World, child: Entity, elder: Entity, problem: Problem, fix: Fix) -> None:
    plant = world.get("plant")
    plant.meters[fix.helps] = max(0.0, plant.meters[fix.helps] - 1)
    if sum(plant.meters[k] for k in ("thirst", "crowded", "cold")) <= 0:
        plant.meters["need"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{child.id} used both hands as if the sprout were something precious and sleepy."
    )
    if plant.meters["new_leaf"] >= THRESHOLD:
        world.say(
            f"By evening, the stem no longer sagged so sadly. One tiny new leaf "
            f"lifted itself as if it were waving hello."
        )


def ending(world: World, child: Entity, elder: Entity, mood: Mood, fix: Fix) -> None:
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f'{child.id} laughed softly. "{fix.gift}"'
    )
    world.say(
        f"{mood.ending} The wee pomegranate plant rested in its new place, and "
        f"{child.id} kept one warm palm near it, not to hold it now, but to promise "
        f"it another kind day tomorrow."
    )


# ---------------------------------------------------------------------------
# Full screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    problem: Problem,
    fix: Fix,
    mood: Mood,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    ribbon: str = "",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={"ribbon": ribbon},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    plant = world.add(
        Entity(
            id="plant",
            kind="plant",
            type="pomegranate",
            label="pomegranate sprout",
            phrase="a wee pomegranate sprout",
            tags={"pomegranate", "plant"},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="thing",
            type="care_tool",
            label=fix.id.replace("_", " "),
            attrs={"fix_id": ""},
            tags=set(fix.tags),
        )
    )

    introduce(world, child, elder, mood)
    promise(world, child, elder)

    world.para()
    trouble_appears(world, child, elder, problem, mood)
    wonder(world, child, elder, problem, fix)

    world.para()
    choose_fix(world, child, elder, fix)
    apply_fix(world, child, elder, problem, fix)
    ending(world, child, elder, mood, fix)

    world.facts.update(
        child=child,
        elder=elder,
        plant=plant,
        helper=helper,
        setting=setting,
        problem=problem,
        fix=fix,
        mood=mood,
        recovered=plant.meters["new_leaf"] >= THRESHOLD,
        ribbon=ribbon,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen_window": Setting(
        id="kitchen_window",
        place="the sunny kitchen window",
        light="golden morning light",
        air="warm and still",
        tags={"window", "sun"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the brick courtyard",
        light="soft afternoon light",
        air="sweet warm air",
        tags={"yard", "sun"},
    ),
    "porch": Setting(
        id="porch",
        place="the shaded front porch",
        light="gentle silver light",
        air="quiet evening air",
        tags={"porch"},
    ),
}

PROBLEMS = {
    "thirst": Problem(
        id="thirst",
        need_meter="thirst",
        symptom="droopy and tired",
        clue="that the soil looked dry and pale",
        lesson="A thirsty plant cannot drink wishes; it needs water at its roots",
        tags={"water", "plant"},
    ),
    "crowded": Problem(
        id="crowded",
        need_meter="crowded",
        symptom="tight and pinched in its little cup",
        clue="that tiny roots were peeking from the hole underneath",
        lesson="When roots have no room, a brave little plant needs a bigger home",
        tags={"roots", "pot"},
    ),
    "cold": Problem(
        id="cold",
        need_meter="cold",
        symptom="small and shivery after the cool night",
        clue="that the leaves felt cool and the stem had tucked inward",
        lesson="A young plant grows best where light and warmth can reach it kindly",
        tags={"warmth", "sun"},
    ),
}

FIXES = {
    "water_can": Fix(
        id="water_can",
        helps="thirst",
        action="tipped a small blue watering can until the soil turned dark and rich",
        qa_action="gave the sprout a careful drink with a small watering can",
        gift="You were only thirsty, little one.",
        tags={"water"},
    ),
    "bigger_pot": Fix(
        id="bigger_pot",
        helps="crowded",
        action="moved the sprout into a round clay pot with fresh loose soil",
        qa_action="moved the sprout into a bigger clay pot with fresh soil",
        gift="Now your roots can stretch and rest.",
        tags={"pot", "roots"},
    ),
    "sunny_spot": Fix(
        id="sunny_spot",
        helps="cold",
        action="carried the sprout to the warmest sunny spot by the window and tucked the soil snug around it",
        qa_action="moved the sprout to a warmer sunny window",
        gift="There now, here is some gentle warmth.",
        tags={"sun", "warmth"},
    ),
}

MOODS = {
    "hushed": Mood(
        id="hushed",
        opening="On a quiet morning",
        noticing="the happy feeling went a little still",
        ending="The whole room felt softer for a moment",
    ),
    "glowing": Mood(
        id="glowing",
        opening="In the tender glow of afternoon",
        noticing="the brightness of the hour seemed to dim just a bit",
        ending="Even the light on the wall seemed to smile",
    ),
    "cozy": Mood(
        id="cozy",
        opening="On a cozy little day",
        noticing="the cozy day suddenly felt full of careful watching",
        ending="The house seemed to take one calm breath with them",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ella", "Maya", "Rosa", "Lucy"]
BOY_NAMES = ["Omar", "Leo", "Noah", "Eli", "Ben", "Theo", "Sam", "Milo"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    mood: str
    child_name: str
    child_gender: str
    elder_type: str
    ribbon: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pomegranate": [
        (
            "What is a pomegranate?",
            "A pomegranate is a round fruit with many juicy seeds inside. It grows on a small tree or shrub."
        )
    ],
    "water": [
        (
            "Why do plants need water?",
            "Plants need water to stay firm and alive. Their roots drink it from the soil."
        )
    ],
    "roots": [
        (
            "What do roots do for a plant?",
            "Roots hold a plant in place and take in water and food from the soil. Healthy roots need room to grow."
        )
    ],
    "pot": [
        (
            "Why might a plant need a bigger pot?",
            "A plant may need a bigger pot when its roots have filled the old one. More room helps it keep growing."
        )
    ],
    "sun": [
        (
            "Why do many plants like a sunny window?",
            "Light helps many plants grow. A sunny window can also feel warmer than a dark corner."
        )
    ],
    "warmth": [
        (
            "Can a little plant feel too cold?",
            "Yes. A very small plant can struggle in chilly places, especially at night. Warmth can help it perk up."
        )
    ],
}
KNOWLEDGE_ORDER = ["pomegranate", "water", "roots", "pot", "sun", "warmth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "pomegranate", "wee", and "palm".',
        f"Tell a gentle happy-ending story where a child named {child.id} holds a wee pomegranate sprout in one palm, notices it is {problem.symptom}, and helps it feel better.",
        f"Write a cozy story in which a little plant has one clear problem and the family solves it by {fix.id.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    problem = f["problem"]
    fix = f["fix"]
    setting = f["setting"]
    recovered = f["recovered"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child caring for a wee pomegranate sprout, and {child.pronoun('possessive')} {elder.label_word} who helps. They spend the story watching the little plant together."
        ),
        (
            "What was in the child's palm at the beginning?",
            f"A wee pomegranate sprout rested in {child.pronoun('possessive')} palm. It was tiny enough to feel precious and easy to protect."
        ),
        (
            "What problem did the plant have?",
            f"The sprout looked {problem.symptom}. {child.id} could tell something was wrong because {problem.clue}."
        ),
        (
            f"How did {child.id} help the plant?",
            f"{child.id} and {child.pronoun('possessive')} {elder.label_word} {fix.qa_action}. They chose that care because the plant's real problem was {problem.id}, not just that it looked sad."
        ),
    ]
    if recovered:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily in {setting.place}, with the pomegranate sprout looking better and lifting a tiny new leaf. The ending shows that careful help changed the plant's day."
            )
        )
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt relieved and proud. The child had been worried first, so the new leaf felt like a small answer back."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pomegranate"} | set(world.facts["problem"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fix_matches(P, F) :- problem(P), fix(F), need_of(P, N), helps(F, N).
valid(S, P, F, M) :- setting(S), problem(P), fix(F), mood(M), fix_matches(P, F).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("need_of", problem_id, problem.need_meter))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("helps", fix_id, fix.helps))
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    # Smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="kitchen_window",
        problem="thirst",
        fix="water_can",
        mood="glowing",
        child_name="Mina",
        child_gender="girl",
        elder_type="grandmother",
        ribbon="yellow ribbon",
    ),
    StoryParams(
        setting="courtyard",
        problem="crowded",
        fix="bigger_pot",
        mood="cozy",
        child_name="Leo",
        child_gender="boy",
        elder_type="grandfather",
        ribbon="",
    ),
    StoryParams(
        setting="porch",
        problem="cold",
        fix="sunny_spot",
        mood="hushed",
        child_name="Rosa",
        child_gender="girl",
        elder_type="mother",
        ribbon="red ribbon",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child helps a wee pomegranate plant."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not fix_matches(problem, fix):
            raise StoryError(explain_rejection(problem, fix))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.fix is None or c[2] == args.fix)
        and (args.mood is None or c[3] == args.mood)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, fix_id, mood_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    ribbon = rng.choice(["", "", "blue ribbon", "yellow ribbon", "red ribbon"])
    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        fix=fix_id,
        mood=mood_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        ribbon=ribbon,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")

    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not fix_matches(problem, fix):
        raise StoryError(explain_rejection(problem, fix))

    world = tell(
        SETTINGS[params.setting],
        problem,
        fix,
        MOODS[params.mood],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        ribbon=params.ribbon,
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
        print(f"{len(combos)} compatible (setting, problem, fix, mood) combos:\n")
        for setting_id, problem_id, fix_id, mood_id in combos:
            print(f"  {setting_id:15} {problem_id:10} {fix_id:12} {mood_id}")
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
            header = f"### {p.child_name}: {p.problem} -> {p.fix} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
