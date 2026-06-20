#!/usr/bin/env python3
"""
storyworlds/worlds/silent_fox_cub_garden_gnome_hardware_store.py
================================================================

Seed prompt used:
    Write a story that includes the following words and narrative instruments.
    Words: silent fox cub, garden gnome
    Setting: hardware store
    Features: Problem Solving, Suspense, Reconciliation
    Style: Nursery Rhyme

Internal source tale
--------------------
In Hushbell Hardware Store, a silent fox cub named Pip helps at closing time
with Mosscap, a garden gnome who watches the shelves. A small hidden sound
starts in one corner of the store. Mosscap points at the real clue, but Pip
mistakes the warning for mischief and feels cross with the gnome. Pip solves
the real physical problem with the right small tool, learns Mosscap was trying
to help all along, and makes a gentle silent apology. The ending image proves
both the hardware store and the friendship have settled again.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


HARDWARE_STORE_NAME = "Hushbell Hardware Store"


@dataclass(frozen=True)
class Nook:
    key: str
    phrase: str
    cozy_detail: str
    ending_image: str
    allowed_plans: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    key: str
    label: str
    origin_phrase: str
    noise_phrase: str
    clue_pose: str
    false_guess: str
    truth: str
    why_here: str
    final_fix: str
    final_image: str
    compatible_plans: tuple[str, ...]
    nooks: tuple[str, ...]
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Plan:
    key: str
    phrase: str
    action_text: str
    solve_reason: str
    apology_gesture: str
    tags: tuple[str, ...] = ()


@dataclass
class StoryParams:
    nook: str
    problem: str
    plan: str
    fox_name: str
    gnome_name: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    phrase: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"fox_cub", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    nook_cfg: Nook
    problem_cfg: Problem
    plan_cfg: Plan
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, event: str, **data: str) -> None:
        row = {"event": event}
        row.update({k: str(v) for k, v in data.items()})
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  nook={self.nook_cfg.key}")
        lines.append(f"  problem={self.problem_cfg.key}")
        lines.append(f"  plan={self.plan_cfg.key}")
        for ent in self.entities.values():
            lines.append(
                f"  {ent.name}<{ent.kind}> location={ent.location} "
                f"meters={ent.meters} memes={ent.memes}"
            )
        lines.append(f"  facts={self.facts}")
        lines.append(f"  fired={self.fired}")
        lines.append(f"  history={self.history}")
        return "\n".join(lines)


NOOKS: dict[str, Nook] = {
    "fastener_wall": Nook(
        key="fastener_wall",
        phrase="the fastener wall by the brass bins",
        cozy_detail="little drawers sat in rows like tidy teeth, and penny nails winked in the lampglow",
        ending_image="the brass bins shone in quiet rows, and one silver washer rested still as a moon in a tray",
        allowed_plans=("magnet_wand", "cardboard_ramp"),
    ),
    "watering_shelf": Nook(
        key="watering_shelf",
        phrase="the watering shelf near the copper nozzles",
        cozy_detail="rubber hoses slept in loops, and watering cans hung round as bells",
        ending_image="the copper nozzles kept their hush, and the blue tag lay soft against the shelf",
        allowed_plans=("felt_pad", "twine_loop"),
    ),
    "twine_corner": Nook(
        key="twine_corner",
        phrase="the twine corner beside the seed crates",
        cozy_detail="jute smelled warm as toast, and cedar boxes made the aisle feel snug",
        ending_image="the seed crate stood square and still, and the twine loops drooped like sleepy curls",
        allowed_plans=("wood_wedge", "shelf_brace"),
    ),
}


PROBLEMS: dict[str, Problem] = {
    "rolling_washer": Problem(
        key="rolling_washer",
        label="the runaway washer",
        origin_phrase="under the brass-bin rail",
        noise_phrase="clink... clink... clink from somewhere low and hidden",
        clue_pose="{gnome}'s painted boot pointed straight at the floor gap",
        false_guess="{fox} feared {gnome} had kicked a metal bit loose while showing off",
        truth="one silver washer had slipped from a torn paper sack and was rolling inside a tin scoop",
        why_here="the sack had split when the bin was filled, and each small wobble sent the washer on another round",
        final_fix="{fox} tucked the torn sack into a wooden tray and set the quiet washer back with its bright brothers.",
        final_image="Nothing chased the scoop anymore; the little metal moon lay still.",
        compatible_plans=("magnet_wand", "cardboard_ramp"),
        nooks=("fastener_wall",),
        tags=("metal", "washer", "magnet"),
    ),
    "tapping_tag": Problem(
        key="tapping_tag",
        label="the tapping tag",
        origin_phrase="beside the copper pipe on the shelf edge",
        noise_phrase="tap-tap-tap, like a spoon on a teacup in the dark",
        clue_pose="{gnome}'s hat tipped toward a blue sale tag swinging near the pipe",
        false_guess="{fox} wondered if {gnome} had flicked the tag just to startle the quiet aisle",
        truth="a blue price tag was knocking the copper pipe whenever the ceiling fan breathed across the shelf",
        why_here="the tag string had stretched long enough for the paper edge to reach the pipe",
        final_fix="{fox} shortened the string and settled the tag where the fan could only brush it, not bang it.",
        final_image="The pipe kept its copper hush, and the paper tag rested flat as a folded wing.",
        compatible_plans=("felt_pad", "twine_loop"),
        nooks=("watering_shelf",),
        tags=("paper", "tag", "pipe", "felt", "twine"),
    ),
    "leaning_crate": Problem(
        key="leaning_crate",
        label="the leaning crate",
        origin_phrase="behind the seed crate stack",
        noise_phrase="tok... tok... tok, as if a tiny drum were hidden in the boards",
        clue_pose="{gnome} leaned both painted hands toward the crate that wobbled on one corner",
        false_guess="{fox} worried the gnome had climbed the crate and started the knocking",
        truth="the lowest seed crate had one short foot, and its loose slat kept tapping the floor each time the stack rocked",
        why_here="a knot in the wood had worn the foot smaller, so the crate could never quite sit square",
        final_fix="{fox} steadied the stack and gave the crate a firm, kind footing again.",
        final_image="The crate stood plumb and proper, and the seed packets stopped shivering.",
        compatible_plans=("wood_wedge", "shelf_brace"),
        nooks=("twine_corner",),
        tags=("wood", "crate", "brace", "wedge"),
    ),
}


PLANS: dict[str, Plan] = {
    "magnet_wand": Plan(
        key="magnet_wand",
        phrase="sweep a magnet wand low",
        action_text="{fox} knelt and slid a little magnet wand under the rail, slow and low, slow and low.",
        solve_reason="A magnet is sensible for a lost metal part because it can pull the piece out without scattering the whole bin.",
        apology_gesture="He tapped a sorry rhythm on the wand handle and bowed it toward {gnome}.",
        tags=("magnet", "metal"),
    ),
    "cardboard_ramp": Plan(
        key="cardboard_ramp",
        phrase="make a tidy cardboard ramp",
        action_text="{fox} tucked a flat scrap of cardboard into the gap to make a tidy ramp, slow and low, slow and low.",
        solve_reason="A smooth ramp gives a rolling part one safe path out instead of letting it rattle deeper under the shelf.",
        apology_gesture="He drew a tiny heart on the cardboard flap and held it up to {gnome}.",
        tags=("cardboard", "rolling"),
    ),
    "felt_pad": Plan(
        key="felt_pad",
        phrase="press a round felt pad in place",
        action_text="{fox} pressed a round felt pad where paper met pipe, soft and slight, soft and slight.",
        solve_reason="Felt hushes tapping because it cushions two hard surfaces before they can knock again.",
        apology_gesture="He patted {gnome}'s hat straight and traced a small sorry circle in the dust.",
        tags=("felt", "quiet"),
    ),
    "twine_loop": Plan(
        key="twine_loop",
        phrase="tie a neat twine loop",
        action_text="{fox} tied a neat twine loop to hold the tag from swinging wide, neat and light, neat and light.",
        solve_reason="A short twine loop limits the tag's swing, so the fan can stir it without letting it strike the pipe.",
        apology_gesture="He looped a tiny twine bow around {gnome}'s wrist as a soft apology.",
        tags=("twine", "knot"),
    ),
    "wood_wedge": Plan(
        key="wood_wedge",
        phrase="tap a cedar wedge beneath the foot",
        action_text="{fox} tapped a cedar wedge beneath the short foot, firm and true, firm and true.",
        solve_reason="A wedge fills the missing height under a wobbly crate, so the stack stops rocking and knocking.",
        apology_gesture="He set {gnome} back on the shelf and touched his own paw to his heart.",
        tags=("wood", "wedge"),
    ),
    "shelf_brace": Plan(
        key="shelf_brace",
        phrase="tighten a slim shelf brace",
        action_text="{fox} tightened a slim shelf brace against the crate stack, snug and true, snug and true.",
        solve_reason="A brace keeps the stack from swaying, which stops the loose slat from hitting the floor.",
        apology_gesture="He wrote 'sorry, friend' on a scrap label and tucked it by {gnome}'s boots.",
        tags=("brace", "wood"),
    ),
}


FOX_NAMES = ("Pip", "Fern", "Nim", "Tavi")
GNOME_NAMES = ("Mosscap", "Pebblehat", "Thimblebeard", "Cloverchin")


def valid_combo(nook_key: str, problem_key: str, plan_key: str) -> bool:
    if nook_key not in NOOKS or problem_key not in PROBLEMS or plan_key not in PLANS:
        return False
    nook = NOOKS[nook_key]
    problem = PROBLEMS[problem_key]
    return (
        nook_key in problem.nooks
        and plan_key in nook.allowed_plans
        and plan_key in problem.compatible_plans
    )


def invalid_reason(nook_key: str, problem_key: str, plan_key: str) -> str:
    if nook_key not in NOOKS:
        return f"No story: unknown nook {nook_key!r}."
    if problem_key not in PROBLEMS:
        return f"No story: unknown problem {problem_key!r}."
    if plan_key not in PLANS:
        return f"No story: unknown plan {plan_key!r}."

    nook = NOOKS[nook_key]
    problem = PROBLEMS[problem_key]
    plan = PLANS[plan_key]

    if nook_key not in problem.nooks:
        return (
            f"No story: {problem.label} does not belong at {nook.phrase}. "
            f"It only fits: {', '.join(problem.nooks)}."
        )
    if plan_key not in nook.allowed_plans:
        return (
            f"No story: {nook.phrase} does not support the plan {plan_key!r}. "
            f"Try one of: {', '.join(nook.allowed_plans)}."
        )
    if plan_key not in problem.compatible_plans:
        return (
            f"No story: {plan.phrase} does not sensibly solve {problem.label}. "
            f"Use one of: {', '.join(problem.compatible_plans)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nook_key in sorted(NOOKS):
        for problem_key in sorted(PROBLEMS):
            for plan_key in sorted(PLANS):
                if valid_combo(nook_key, problem_key, plan_key):
                    combos.append((nook_key, problem_key, plan_key))
    return combos


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random(args.seed + index)
    fox_name = args.fox_name or rng.choice(FOX_NAMES)
    gnome_name = args.gnome_name or rng.choice(GNOME_NAMES)
    nook_key, problem_key, plan_key = combo
    return StoryParams(
        nook=nook_key,
        problem=problem_key,
        plan=plan_key,
        fox_name=fox_name,
        gnome_name=gnome_name,
        seed=args.seed + index,
    )


def build_world(params: StoryParams) -> World:
    nook_cfg = NOOKS[params.nook]
    problem_cfg = PROBLEMS[params.problem]
    plan_cfg = PLANS[params.plan]
    world = World(params=params, nook_cfg=nook_cfg, problem_cfg=problem_cfg, plan_cfg=plan_cfg)

    fox = world.add(
        Entity(
            name=params.fox_name,
            kind="fox_cub",
            phrase="silent fox cub",
            location="hardware_store",
            meters={"steps": 0.0, "distance_to_problem": 2.0},
            memes={"calm": 0.9, "curiosity": 1.0, "worry": 0.0, "guilt": 0.0, "trust": 1.0},
        )
    )
    gnome = world.add(
        Entity(
            name=params.gnome_name,
            kind="gnome",
            phrase="garden gnome",
            location=params.nook,
            meters={"balance": 1.0, "visibility": 1.0},
            memes={"pride": 0.8, "hurt": 0.0, "trust": 1.0, "forgiveness": 0.0},
        )
    )
    world.add(
        Entity(
            name=params.nook,
            kind="nook",
            phrase=nook_cfg.phrase,
            location="hardware_store",
            meters={"quiet": 1.0, "lamp_glow": 0.8},
            memes={"cozy": 1.0},
        )
    )
    world.add(
        Entity(
            name=params.problem,
            kind="problem",
            phrase=problem_cfg.label,
            location=params.nook,
            meters={"hidden": 1.0, "noise": 1.0, "fixed": 0.0},
            memes={"uncertainty": 1.0, "suspense": 0.0},
        )
    )

    world.facts.update(
        {
            "setting": "hardware_store",
            "style": "nursery_rhyme",
            "features": "problem_solving,suspense,reconciliation",
            "seed_words": "silent fox cub,garden gnome",
            "fox": fox.name,
            "gnome": gnome.name,
            "reconciled": False,
        }
    )
    world.note("setup", fox=fox.name, gnome=gnome.name, nook=params.nook, problem=params.problem, plan=params.plan)
    return world


def _fox(world: World) -> Entity:
    return world.get(world.params.fox_name)


def _gnome(world: World) -> Entity:
    return world.get(world.params.gnome_name)


def _nook(world: World) -> Entity:
    return world.get(world.params.nook)


def _problem(world: World) -> Entity:
    return world.get(world.params.problem)


def _render_named(world: World, text: str) -> str:
    return text.format(fox=world.params.fox_name, gnome=world.params.gnome_name)


def _lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def _opening(world: World) -> None:
    fox = _fox(world)
    gnome = _gnome(world)
    nook = world.nook_cfg
    world.say(
        f"In {HARDWARE_STORE_NAME}, where little hammers slept by the door, a silent fox cub named {fox.name} swept with a swish-swish-swish."
    )
    world.say(
        f"At {nook.phrase} stood {gnome.name}, a garden gnome in a pea-green coat, while {nook.cozy_detail}."
    )
    world.say(
        f"{fox.name} did not use words when work was small or big. He used bright eyes, careful paws, and a tail that curled like a comma."
    )
    world.note("opening", setting=HARDWARE_STORE_NAME, nook=nook.key)
    world.fired.append("opening")


def _raise_suspense(world: World) -> None:
    fox = _fox(world)
    gnome = _gnome(world)
    nook_ent = _nook(world)
    problem_ent = _problem(world)
    problem_cfg = world.problem_cfg

    fox.memes["worry"] += 1.0
    fox.memes["curiosity"] += 0.4
    gnome.memes["hurt"] += 0.8
    nook_ent.meters["quiet"] = 0.2
    problem_ent.meters["noise"] = 1.3
    problem_ent.memes["suspense"] = 1.2
    world.facts["misread_warning"] = True

    world.para()
    world.say(
        f"Then came {problem_cfg.noise_phrase} from {problem_cfg.origin_phrase}. The hardware store felt hush-hush-hush, as if every screw and spool were listening."
    )
    world.say(
        f"{_render_named(world, problem_cfg.clue_pose)}. But {_render_named(world, problem_cfg.false_guess)}."
    )
    world.say(
        f"{fox.name} set {gnome.name} on a lower crate and frowned. The gnome's painted smile stayed put, yet somehow it looked smaller than before."
    )
    world.note("suspense", sound=problem_cfg.noise_phrase, false_guess=problem_cfg.false_guess)
    world.fired.append("suspense")


def _apply_plan(world: World) -> None:
    fox = _fox(world)
    gnome = _gnome(world)
    nook_ent = _nook(world)
    problem_ent = _problem(world)
    plan_cfg = world.plan_cfg

    fox.memes["calm"] += 0.2
    fox.memes["worry"] = max(0.2, fox.memes["worry"] - 0.3)
    fox.meters["distance_to_problem"] = 0.4
    gnome.meters["visibility"] += 0.1
    nook_ent.meters["lamp_glow"] += 0.1
    world.fired.append(f"used_{plan_cfg.key}")

    world.para()
    world.say(
        f"{fox.name} took one slow breath and looked again. If a thing goes wrong, he thought, the paws must go slow and the eyes must go low."
    )
    world.say(_render_named(world, plan_cfg.action_text))
    world.say(
        f"{plan_cfg.solve_reason} {gnome.name} watched without blinking, still pointing toward the true trouble."
    )
    problem_ent.memes["uncertainty"] = 0.4
    world.note("plan", plan=plan_cfg.key, reason=plan_cfg.solve_reason)


def _reveal(world: World) -> None:
    fox = _fox(world)
    gnome = _gnome(world)
    problem_ent = _problem(world)
    problem_cfg = world.problem_cfg

    fox.memes["understanding"] = 1.0
    fox.memes["worry"] = max(0.0, fox.memes["worry"] - 0.6)
    fox.memes["guilt"] += 0.9
    gnome.memes["hurt"] = max(0.1, gnome.memes["hurt"] - 0.2)
    problem_ent.meters["hidden"] = 0.0
    problem_ent.meters["fixed"] = 0.6
    problem_ent.meters["noise"] = 0.3
    problem_ent.memes["uncertainty"] = 0.0

    if world.plan_cfg.key == "magnet_wand":
        lead = "With one tiny clink, the answer came skimming out."
    elif world.plan_cfg.key == "cardboard_ramp":
        lead = "At the end of the cardboard path, the answer rolled into sight."
    elif world.plan_cfg.key == "felt_pad":
        lead = "As soon as the soft felt kissed the hard pipe, the answer showed itself."
    elif world.plan_cfg.key == "twine_loop":
        lead = "When the swing grew short and gentle, the answer was easy to see."
    elif world.plan_cfg.key == "wood_wedge":
        lead = "When the wedge lifted the corner true, the answer stopped hiding."
    elif world.plan_cfg.key == "shelf_brace":
        lead = "Once the brace held the stack snug, the answer could not keep tapping."
    else:
        raise StoryError(f"No reveal text for plan {world.plan_cfg.key!r}.")

    world.say(
        f"{lead} The real trouble was {problem_cfg.truth}. It had happened because {problem_cfg.why_here}."
    )
    world.say(
        f"Then {fox.name} understood the gnome at once: {gnome.name} had not made the mischief at all. The little garden gnome had been warning him where to look."
    )
    world.note("reveal", truth=problem_cfg.truth, why=problem_cfg.why_here)
    world.fired.append("reveal")


def _reconcile(world: World) -> None:
    fox = _fox(world)
    gnome = _gnome(world)
    nook_ent = _nook(world)
    problem_ent = _problem(world)
    problem_cfg = world.problem_cfg
    plan_cfg = world.plan_cfg

    problem_ent.meters["fixed"] = 1.0
    problem_ent.meters["noise"] = 0.0
    gnome.memes["hurt"] = 0.0
    gnome.memes["forgiveness"] = 1.0
    gnome.memes["trust"] += 0.4
    fox.memes["guilt"] = max(0.0, fox.memes["guilt"] - 0.2)
    fox.memes["trust"] += 0.3
    nook_ent.meters["quiet"] = 1.1
    world.facts["reconciled"] = True

    world.para()
    world.say(
        f"{_render_named(world, plan_cfg.apology_gesture)} Being a silent fox cub, {fox.name} could not say the word aloud, but the sorry was plain all the same."
    )
    if gnome.memes["forgiveness"] >= 1.0:
        world.say(
            f"{gnome.name} answered with a nod so small it was almost a rhyme. The hurt eased away, and the friendship clicked back into place."
        )
    world.say(_render_named(world, problem_cfg.final_fix))
    world.say(
        f"{problem_cfg.final_image} By closing time, {world.nook_cfg.ending_image}, and {fox.name} set {gnome.name} high again where both could keep the peace."
    )
    world.note("reconcile", apology=plan_cfg.apology_gesture, final_fix=problem_cfg.final_fix)
    world.fired.append("reconcile")


def simulate(world: World) -> World:
    _opening(world)
    _raise_suspense(world)
    _apply_plan(world)
    _reveal(world)
    _reconcile(world)
    return world


def _prompts(world: World) -> list[str]:
    nook = world.nook_cfg
    problem = world.problem_cfg
    plan = world.plan_cfg
    return [
        'Write a Nursery Rhyme style story set in a hardware store using the words "silent fox cub" and "garden gnome."',
        f"Build suspense around a hidden sound at {nook.phrase}, then solve the physical problem of {problem.label}.",
        f"End with reconciliation by having the fox cub {plan.phrase}, learn the gnome was helping, and close on one calm store image.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    fox = _fox(world)
    gnome = _gnome(world)
    nook = world.nook_cfg
    problem = world.problem_cfg
    plan = world.plan_cfg
    return [
        QAItem(
            "What made the hardware store feel suspenseful?",
            f"The suspense began when a hidden sound came from {problem.origin_phrase} at {nook.phrase}. Because {fox.name} could hear the trouble before seeing it, the cozy hardware store suddenly felt secret and tight with waiting.",
        ),
        QAItem(
            f"Why did {fox.name} hurt {gnome.name}'s feelings at first?",
            f"{fox.name} mistook the gnome's warning pose for mischief and blamed {gnome.name} too quickly. That misunderstanding stung because the garden gnome was trying to point at the real clue, not cause the noise.",
        ),
        QAItem(
            f"How did {plan.phrase} solve the problem?",
            f"{fox.name} used the plan to deal with the real physical cause: {problem.truth}. That worked because {_lower_first(plan.solve_reason)}",
        ),
        QAItem(
            "How did the story reach reconciliation?",
            f"After the real cause was revealed, {fox.name} understood that {gnome.name} had been helping all along. The fox cub gave a clear silent apology, and the gnome forgave him, so their friendship settled as neatly as the repaired shelf.",
        ),
        QAItem(
            "What final image proves that both the problem and the quarrel are over?",
            f"The ending proves it with two calm pictures: {problem.final_image} {world.nook_cfg.ending_image.capitalize()}. Those still details show that the noise is gone and the friends are at peace again.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    problem = world.problem_cfg
    plan = world.plan_cfg
    tag_set = set(problem.tags) | set(plan.tags)
    items: list[QAItem] = [
        QAItem(
            "What is a hardware store?",
            "A hardware store is a shop that keeps tools, fasteners, wood pieces, and repair supplies. People go there when something needs fixing or fitting together.",
        ),
        QAItem(
            "Why is it wise to follow a clue before blaming a friend?",
            "A clue points toward what really happened, while a quick blame can hurt someone who was trying to help. Looking first and judging second makes both the repair and the friendship stronger.",
        ),
        QAItem(
            "Why does reconciliation matter after a misunderstanding?",
            "Reconciliation matters because solving the object problem is only half the work when feelings were hurt. A true ending also mends trust, so the people in the story can feel safe with each other again.",
        ),
    ]

    if "magnet" in tag_set:
        items.append(
            QAItem(
                "Why can a magnet help with a lost metal piece?",
                "A magnet can pull on some kinds of metal without a person having to reach into a narrow gap. That makes it useful for small metal parts that are hard to grab with fingers.",
            )
        )
    elif "felt" in tag_set:
        items.append(
            QAItem(
                "What does a felt pad do?",
                "A felt pad is a soft piece of material that cushions hard surfaces. It can quiet a tap or scrape by keeping the objects from knocking directly together.",
            )
        )
    elif "twine" in tag_set:
        items.append(
            QAItem(
                "Why does a shorter loop change how something swings?",
                "A shorter loop gives an object less room to travel. When it cannot swing as far, it is less likely to bump into something nearby.",
            )
        )
    elif "wedge" in tag_set:
        items.append(
            QAItem(
                "What is a wedge used for?",
                "A wedge is a small piece that fills a gap or lifts one side a little. It is useful when an object rocks because one foot is lower than the others.",
            )
        )
    elif "brace" in tag_set:
        items.append(
            QAItem(
                "What does a brace do in a stack or shelf?",
                "A brace adds support and keeps the structure from swaying sideways. When the sway stops, loose pieces are less likely to knock or wobble.",
            )
        )

    return items


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.nook, params.problem, params.plan):
        raise StoryError(invalid_reason(params.nook, params.problem, params.plan))

    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(N,P,L) :-
    nook(N),
    problem(P),
    plan(L),
    problem_at(P,N),
    nook_allows(N,L),
    problem_allows(P,L).

ok :- chosen(N,P,L), combo(N,P,L).

#show combo/3.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for nook_key, nook in sorted(NOOKS.items()):
        rows.append(fact("nook", nook_key))
        for plan_key in nook.allowed_plans:
            rows.append(fact("nook_allows", nook_key, plan_key))
    for problem_key, problem in sorted(PROBLEMS.items()):
        rows.append(fact("problem", problem_key))
        for nook_key in problem.nooks:
            rows.append(fact("problem_at", problem_key, nook_key))
        for plan_key in problem.compatible_plans:
            rows.append(fact("problem_allows", problem_key, plan_key))
    for plan_key in sorted(PLANS):
        rows.append(fact("plan", plan_key))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.nook, params.problem, params.plan) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def _asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ok"))


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for index, combo in enumerate(sorted(python_set), 1):
        params = StoryParams(
            nook=combo[0],
            problem=combo[1],
            plan=combo[2],
            fox_name=FOX_NAMES[0],
            gnome_name=GNOME_NAMES[0],
            seed=index,
        )
        if not _asp_accepts(params):
            raise StoryError(f"ASP failed to accept valid combo {combo!r}.")

        sample = generate(params)
        story_lower = sample.story.lower()
        if "hardware store" not in story_lower:
            raise StoryError(f"Generated story for {combo!r} forgot the hardware store setting.")
        if "silent fox cub" not in story_lower:
            raise StoryError(f"Generated story for {combo!r} forgot the seed words 'silent fox cub'.")
        if "garden gnome" not in story_lower:
            raise StoryError(f"Generated story for {combo!r} forgot the seed words 'garden gnome'.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated story for {combo!r} leaked a template field.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} is missing a full beginning, turn, or ending.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated story for {combo!r} has the wrong number of prompts.")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated story for {combo!r} has incomplete QA sets.")
        if not sample.world or not sample.world.facts.get("reconciled"):
            raise StoryError(f"Generated story for {combo!r} did not reach reconciliation.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer is too thin for {combo!r}: {qa.question!r}")
        for qa in sample.world_qa:
            if not qa.answer.endswith("."):
                raise StoryError(f"World QA answer is malformed for {combo!r}: {qa.question!r}")

    alt_params = StoryParams(
        nook="twine_corner",
        problem="leaning_crate",
        plan="shelf_brace",
        fox_name=FOX_NAMES[-1],
        gnome_name=GNOME_NAMES[-1],
        seed=999,
    )
    alt_sample = generate(alt_params)
    for other_fox in FOX_NAMES:
        if other_fox != alt_params.fox_name and other_fox in alt_sample.story:
            raise StoryError(f"Generated story leaked unexpected fox name {other_fox!r}.")
    for other_gnome in GNOME_NAMES:
        if other_gnome != alt_params.gnome_name and other_gnome in alt_sample.story:
            raise StoryError(f"Generated story leaked unexpected gnome name {other_gnome!r}.")

    return f"OK: {len(python_set)} valid combos; ASP parity holds; generated stories pass quality checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate nursery-rhyme hardware-store stories about a silent fox cub and a garden gnome.")
    parser.add_argument("--nook", choices=sorted(NOOKS), default=None)
    parser.add_argument("--problem", choices=sorted(PROBLEMS), default=None)
    parser.add_argument("--plan", choices=sorted(PLANS), default=None)
    parser.add_argument("--fox-name", default=None)
    parser.add_argument("--gnome-name", default=None)
    parser.add_argument("--seed", type=int, default=1)
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
    combos = valid_combos()
    filtered = [
        combo
        for combo in combos
        if (args.nook is None or combo[0] == args.nook)
        and (args.problem is None or combo[1] == args.problem)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if args.nook and args.problem and args.plan and not filtered:
        raise StoryError(invalid_reason(args.nook, args.problem, args.plan))
    if not filtered:
        if args.nook or args.problem or args.plan:
            raise StoryError("No story: no valid nook/problem/plan combination matches the requested filters.")
        filtered = combos

    combo = rng.choice(filtered)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for nook_key, problem_key, plan_key in sorted(asp_valid_combos()):
        print(f"{nook_key}\t{problem_key}\t{plan_key}")


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0

        samples: list[StorySample] = []
        if args.all:
            combos = valid_combos()
            for index, combo in enumerate(combos, 1):
                samples.append(generate(_params_from_combo(args, combo, index)))
        else:
            count = max(1, args.n)
            for index in range(count):
                rng = random.Random(args.seed + index)
                samples.append(generate(resolve_params(args, rng, index)))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples, 1):
            header = ""
            if args.all:
                p = sample.params
                header = f"### {p.nook} / {p.problem} / {p.plan}"
            elif len(samples) > 1:
                header = f"### variant {index}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index != len(samples):
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
