#!/usr/bin/env python3
"""
storyworlds/worlds/silent_fox_cub_garden_gnome_hardware_store_2.py
==================================================================

Nursery-rhyme storyworld about a hidden rattle in a hardware store.

Internal source tale:
In Hushbell Hardware Store, a silent fox cub named Pip helps straighten the
garden aisle while Mosscap the garden gnome keeps watch from a painted shelf.
A secret clinking sound starts at closing time. Pip wrongly thinks Mosscap made
the trouble, but the gnome is only pointing toward the clue. Pip solves the
hardware-store problem with the right small tool, discovers the true cause, and
mends the hurt with a silent apology before the store goes still again.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


STORE_NAME = "Hushbell Hardware Store"
FOX_NAME = "Pip"
GNOME_NAME = "Mosscap"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    subject: str = "they"
    object: str = "them"
    possessive: str = "their"
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class Aisle:
    id: str
    phrase: str
    opening_detail: str
    display_phrase: str
    hide_phrase: str
    clue_surface: str
    final_image: str
    tags: frozenset[str]


@dataclass(frozen=True)
class Problem:
    id: str
    noise_phrase: str
    origin_phrase: str
    hidden_item: str
    wrong_guess_text: str
    clue_text: str
    reveal_text: str
    risk_text: str
    aisle_tag: str
    needs_peek: int = 0
    needs_trace: int = 0
    needs_lift: int = 0
    needs_high: int = 0
    needs_steady: int = 0
    needs_magnet: int = 0
    needs_hook: int = 0


@dataclass(frozen=True)
class Plan:
    id: str
    phrase: str
    tool_phrase: str
    rhyme: str
    method_text: str
    apology_gesture: str
    peek: int = 0
    trace: int = 0
    lift: int = 0
    high: int = 0
    steady: int = 0
    magnet: int = 0
    hook: int = 0
    light: int = 0


@dataclass(frozen=True)
class StoryParams:
    aisle: str
    problem: str
    plan: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams, aisle: Aisle, problem: Problem, plan: Plan) -> None:
        self.params = params
        self.aisle = aisle
        self.problem = problem
        self.plan = plan
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, object]] = []
        self.facts: dict[str, object] = {
            "style": "nursery_rhyme",
            "features": ["problem_solving", "suspense", "reconciliation"],
            "setting": "hardware store",
            "seed_words": ["silent fox cub", "garden gnome"],
        }
        self.fired: set[str] = set()

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

    def note(self, event: str, **fields: object) -> None:
        row = {"event": event}
        row.update(fields)
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: object


AISLES: dict[str, Aisle] = {
    "gnome_endcap": Aisle(
        "gnome_endcap",
        "the gnome-and-seed endcap of the hardware store",
        "terracotta saucers, painted seed drawers, and a bell-mouthed watering can",
        "the painted gnome shelf",
        "the lip beneath the painted gnome shelf",
        "a dust-soft strip by the seed drawers",
        "the seed drawers sat straight, and Mosscap smiled beside a neat ring of terracotta saucers",
        frozenset({"low_gap", "garden_display", "seed_drawers", "lamp"}),
    ),
    "bolt_bay": Aisle(
        "bolt_bay",
        "the brass-bolt bay of the hardware store",
        "little drawers of nuts and washers gleaming like pocket moons",
        "the narrow bolt bins",
        "the gap beneath the bolt bins",
        "a silver-speckled floor mat",
        "the bolt bins rested still, with every drawer shut and every bright bit back in its place",
        frozenset({"low_gap", "metal_bits", "aisle_room"}),
    ),
    "watering_row": Aisle(
        "watering_row",
        "the watering-can row of the hardware store",
        "cans with long noses and a ladder of hoses hanging high",
        "the tall watering-can hooks",
        "the shadow behind the stacked cans",
        "a pale fan of sawdust under the cans",
        "the cans hung quiet as pears, and a thin line of light lay peaceful on the floor",
        frozenset({"tall_hooks", "garden_display", "lamp"}),
    ),
    "twine_rack": Aisle(
        "twine_rack",
        "the twine-and-stakes row of the hardware store",
        "spools of jute, bundles of stakes, and a bell on the sample gate",
        "the bell-hung stake rail",
        "the slot under the twine rack",
        "a crinkly paper runner by the sample gate",
        "the gate bell stopped trembling, and the row of twine sat tidy as sleeping kittens",
        frozenset({"tall_hooks", "garden_display", "aisle_room"}),
    ),
}


PROBLEMS: dict[str, Problem] = {
    "washer_tin": Problem(
        "washer_tin",
        "a tinny clink-clink-clink",
        "the dark floor gap",
        "the little tin of brass washers",
        "Pip thought Mosscap's clay boot must have nudged the shelf.",
        "a short shining trail of brass dust",
        "Out slid the little tin of brass washers. Its paper seal had popped, and the tin had rolled itself into the gap.",
        "Each tiny clink made the low bins tremble as if one more nudge might spill a glittering rain.",
        "low_gap",
        needs_peek=1,
        needs_magnet=1,
    ),
    "twine_spool": Problem(
        "twine_spool",
        "a hushy zip-zip-clack",
        "the shadows beside the garden display",
        "the spool of green twine",
        "Pip thought Mosscap had tugged the display ribbon for fun.",
        "a green line of twine curling over the floor",
        "There lay the spool of green twine, unwinding itself around a scoop handle and tugging it tap-tap against the rack.",
        "With every little tug, a scoop knocked the rail, and the whole corner sounded busier than it was.",
        "garden_display",
        needs_trace=1,
        needs_lift=1,
    ),
    "brass_hook": Problem(
        "brass_hook",
        "a high tap-tap-ting",
        "the tall rack above their heads",
        "the loose brass hook",
        "Pip thought Mosscap had rattled the hanging cans.",
        "one can rocking while all the others stayed still",
        "Up on the rack, one loose brass hook was tapping a watering can whenever the ceiling fan breathed past.",
        "The bright tapping came from so high above that the mystery felt bigger with every ting.",
        "tall_hooks",
        needs_high=1,
        needs_steady=1,
    ),
    "seed_scoop": Problem(
        "seed_scoop",
        "a soft cluck-cluck-scrape",
        "the space behind the seed drawers",
        "the cedar seed scoop",
        "Pip thought Mosscap had nudged the drawers with his round red hat.",
        "a cedar shaving caught on the drawer lip",
        "Behind the drawer face, a cedar seed scoop had slipped sideways and was scraping each time the drawer settled.",
        "The scrape was quiet but creepy, because it came from where no paws could see.",
        "seed_drawers",
        needs_peek=1,
        needs_hook=1,
    ),
}


PLANS: dict[str, Plan] = {
    "magnet_line": Plan(
        "magnet_line",
        "loop a horseshoe magnet on a blue string",
        "a horseshoe magnet on blue string",
        "Ring it, swing it, slow and bright, draw the metal into light.",
        "Pip tied the string, lowered the magnet with careful paws, and let Mosscap point exactly where the line should dip.",
        "a neat blue bow beside the gnome's boots",
        peek=1,
        magnet=1,
    ),
    "mirror_broom": Plan(
        "mirror_broom",
        "tilt a pocket mirror and guide with the broom handle",
        "a pocket mirror and the broom handle",
        "Look and crook, low and slow, see the trouble, nudge it so.",
        "Pip angled the mirror to catch the hidden edge, then nudged with the broom handle while Mosscap pointed without blinking.",
        "one polished brass washer by Mosscap's hand, like a shiny sorry",
        peek=1,
        hook=1,
    ),
    "stool_cloth": Plan(
        "stool_cloth",
        "climb the two-step stool with a folded dust cloth",
        "the two-step stool and a folded dust cloth",
        "Step by step and steady paws, gentle fixes mend small flaws.",
        "Pip climbed the stool softly, wrapped the cloth around the wobbling piece, and held still until the tapping gave up.",
        "Mosscap's clean red cap back in its proper place",
        high=1,
        steady=1,
        light=1,
    ),
    "lantern_twine": Plan(
        "lantern_twine",
        "shine a camping lantern and follow the twine",
        "a camping lantern and patient paws",
        "Line by line and gleam by gleam, follow where the tangles dream.",
        "Pip held the lantern low while Mosscap pointed along the curling string, and together they followed the green line to the snag.",
        "a little twine heart looped near the gnome's sleeve",
        trace=1,
        lift=1,
        light=1,
    ),
}


def reasonableness_report(aisle: Aisle, problem: Problem, plan: Plan) -> tuple[bool, str]:
    if problem.aisle_tag not in aisle.tags:
        return False, "that aisle cannot plausibly hide this kind of hardware-store trouble"
    if problem.needs_peek > plan.peek:
        return False, "the plan cannot peek into the hiding place well enough"
    if problem.needs_trace > plan.trace:
        return False, "the plan cannot follow the clue trail to the real cause"
    if problem.needs_lift > plan.lift:
        return False, "the plan cannot lift the snagged item free"
    if problem.needs_high > plan.high:
        return False, "the plan cannot safely reach the rattling trouble"
    if problem.needs_steady > plan.steady:
        return False, "the plan is not steady enough for the suspenseful fix"
    if problem.needs_magnet > plan.magnet:
        return False, "the plan needs a magnet to draw the metal piece out"
    if problem.needs_hook > plan.hook:
        return False, "the plan needs a hooked nudge to pull the hidden piece free"
    return True, ""


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for aisle_id, aisle in AISLES.items():
        for problem_id, problem in PROBLEMS.items():
            for plan_id, plan in PLANS.items():
                ok, _ = reasonableness_report(aisle, problem, plan)
                if ok:
                    combos.append((aisle_id, problem_id, plan_id))
    return combos


def all_params() -> list[StoryParams]:
    return [StoryParams(aisle, problem, plan) for aisle, problem, plan in valid_combos()]


def explain_rejection(aisle_id: str, problem_id: str, plan_id: str) -> str:
    if aisle_id not in AISLES:
        return f"unknown aisle: {aisle_id}"
    if problem_id not in PROBLEMS:
        return f"unknown problem: {problem_id}"
    if plan_id not in PLANS:
        return f"unknown plan: {plan_id}"
    _, reason = reasonableness_report(AISLES[aisle_id], PROBLEMS[problem_id], PLANS[plan_id])
    return reason or "no valid combination matched the requested options"


def _r_suspense(world: World) -> list[str]:
    source = world.get("source")
    store = world.get("store")
    fox = world.get("fox")
    gnome = world.get("gnome")
    if source.meters["hidden"] < 1 or source.meters["noise"] < 1:
        return []
    if "suspense" in world.fired:
        return []
    world.fired.add("suspense")
    store.meters["suspense"] += 1.0
    fox.memes["worry"] += 1.0
    gnome.memes["alert"] += 1.0
    world.note("suspense", noise=world.problem.noise_phrase, origin=world.problem.origin_phrase)
    return [
        f"Then came {world.problem.noise_phrase} from {world.aisle.hide_phrase}.",
        f"{world.problem.risk_text} The hardware store felt hush-hush-hush, as if every screw and sprinkler wanted to listen."
    ]


def _r_blame_stings(world: World) -> list[str]:
    fox = world.get("fox")
    gnome = world.get("gnome")
    relation = world.get("relation")
    if fox.memes["suspicion"] < 1 or gnome.memes["alert"] < 1:
        return []
    if "blame_stings" in world.fired:
        return []
    world.fired.add("blame_stings")
    gnome.memes["hurt"] += 1.0
    relation.meters["strain"] += 1.0
    world.note("blame", by=fox.label, against=gnome.label)
    return [
        "Mosscap's little clay shoulders drooped under his red cap.",
        "The garden gnome had only been warning Pip, so the space between them felt suddenly small and sore."
    ]


def _r_reveal(world: World) -> list[str]:
    source = world.get("source")
    store = world.get("store")
    display = world.get("display")
    fox = world.get("fox")
    gnome = world.get("gnome")
    if not world.facts.get("plan_ready"):
        return []
    if "reveal" in world.fired:
        return []
    world.fired.add("reveal")
    source.meters["hidden"] = 0.0
    source.meters["found"] = 1.0
    store.meters["calm"] += 1.0
    display.meters["rattle"] = 0.0
    fox.memes["remorse"] += 1.0
    fox.memes["understanding"] += 1.0
    gnome.memes["relief"] += 1.0
    world.note("reveal", item=world.problem.hidden_item, plan=world.plan.id)
    return [
        world.problem.reveal_text,
        f"The troubling sound stopped at once, and {world.aisle.display_phrase} quit shivering."
    ]


def _r_reconcile(world: World) -> list[str]:
    fox = world.get("fox")
    gnome = world.get("gnome")
    relation = world.get("relation")
    if fox.memes["apology"] < 1 or world.get("source").meters["found"] < 1:
        return []
    if "reconcile" in world.fired:
        return []
    world.fired.add("reconcile")
    relation.meters["strain"] = 0.0
    relation.meters["friendship"] += 1.0
    fox.memes["relief"] += 1.0
    gnome.memes["forgiveness"] += 1.0
    world.note("reconcile", fox=fox.label, gnome=gnome.label)
    return [
        "Mosscap tipped his cap and tapped Pip's paw in forgiveness.",
        "The sore feeling melted away, and the two friends stood shoulder to shoulder again."
    ]


RULES = [
    Rule("suspense", _r_suspense),
    Rule("blame_stings", _r_blame_stings),
    Rule("reveal", _r_reveal),
    Rule("reconcile", _r_reconcile),
]


def propagate(world: World, *, narrate: bool = False) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            before = len(world.fired)
            lines = rule.apply(world)
            if len(world.fired) != before:
                changed = True
            if narrate:
                out.extend(lines)
    return out


def introduce(world: World) -> None:
    fox = world.get("fox")
    gnome = world.get("gnome")
    fox.memes["care"] += 1.0
    gnome.memes["watchfulness"] += 1.0
    world.say(
        f"In {STORE_NAME}, where little hammers hung in a row, a silent fox cub named {fox.label} swept soft-soft-soft below."
    )
    world.say(
        f"Near {world.aisle.phrase} stood {gnome.label}, a garden gnome in a pea-green coat, while {world.aisle.opening_detail} kept still around him."
    )
    world.say(
        f"Pip liked closing time best, because quiet shelves and tidy tools made the whole hardware store feel tucked in for the night."
    )
    world.note("premise", place=STORE_NAME, aisle=world.aisle.id)


def disturbance(world: World) -> None:
    source = world.get("source")
    display = world.get("display")
    source.meters["hidden"] = 1.0
    source.meters["noise"] = 1.0
    display.meters["rattle"] = 1.0
    world.say(
        f"But just as Pip lifted his broom, something rustled and waited near {world.problem.origin_phrase}."
    )
    for line in propagate(world, narrate=True):
        world.say(line)


def quick_blame(world: World) -> None:
    fox = world.get("fox")
    gnome = world.get("gnome")
    fox.memes["suspicion"] += 1.0
    world.say(
        f"{gnome.label} stretched both clay hands toward the shaking place, and {world.problem.wrong_guess_text}"
    )
    world.say(
        "Pip could not ask a sharp question out loud, so his flat ears and worried eyes asked it for him."
    )
    for line in propagate(world, narrate=True):
        world.say(line)


def noticing_turn(world: World) -> None:
    fox = world.get("fox")
    fox.memes["care"] += 1.0
    world.say(
        f"Then Pip noticed {world.problem.clue_text} on {world.aisle.clue_surface}."
    )
    world.say(
        f"He saw that {gnome_name()} was not bragging over a mess at all. The little gnome had been pointing straight at the clue."
    )
    world.note("turn", clue=world.problem.clue_text)


def solve_problem(world: World) -> None:
    fox = world.get("fox")
    gnome = world.get("gnome")
    fox.memes["problem_solving"] += 1.0
    gnome.memes["helpfulness"] += 1.0
    world.say(
        f"Being a silent fox cub, {fox.label} answered with paws instead of words. He chose to {world.plan.phrase}."
    )
    world.say(f'"{world.plan.rhyme}"')
    world.say(world.plan.method_text)
    world.facts["plan_ready"] = True
    world.facts["tool_phrase"] = world.plan.tool_phrase
    for line in propagate(world, narrate=True):
        world.say(line)
    world.say(
        f"Pip looked at {gnome.label} with wide, sorry eyes, because the true trouble had been {world.problem.hidden_item} all along."
    )
    world.note("solution", plan=world.plan.id, tool=world.plan.tool_phrase)


def reconcile(world: World) -> None:
    fox = world.get("fox")
    fox.memes["apology"] += 1.0
    world.say(
        f"He set {world.plan.apology_gesture}. That was Pip's silent way of saying sorry."
    )
    for line in propagate(world, narrate=True):
        world.say(line)
    world.note("apology", gesture=world.plan.apology_gesture)


def ending(world: World) -> None:
    fox = world.get("fox")
    gnome = world.get("gnome")
    world.say(
        f"Together Pip and {gnome.label} straightened the last small thing, and soon {world.aisle.final_image}."
    )
    world.say(
        f"The noise was gone, the worry was gone, and {STORE_NAME} felt cozy enough to hum. {fox.label} swept one final swish, and the gnome gave one final nod."
    )
    world.facts["resolved"] = world.get("source").meters["found"] >= 1.0
    world.facts["reconciled"] = world.get("relation").meters["strain"] == 0.0 and world.get("relation").meters["friendship"] >= 1.0
    world.facts["final_image"] = world.aisle.final_image
    world.note("ending", image=world.aisle.final_image)


def gnome_name() -> str:
    return GNOME_NAME


def build_world(params: StoryParams) -> World:
    if params.aisle not in AISLES or params.problem not in PROBLEMS or params.plan not in PLANS:
        raise StoryError("requested params are not in this storyworld registry")
    aisle = AISLES[params.aisle]
    problem = PROBLEMS[params.problem]
    plan = PLANS[params.plan]
    ok, reason = reasonableness_report(aisle, problem, plan)
    if not ok:
        raise StoryError(reason)

    world = World(params, aisle, problem, plan)
    world.add(Entity(
        "fox",
        kind="character",
        type="fox_cub",
        label=FOX_NAME,
        phrase="silent fox cub",
        subject="he",
        object="him",
        possessive="his",
        location="aisle",
    ))
    world.add(Entity(
        "gnome",
        kind="character",
        type="garden_gnome",
        label=GNOME_NAME,
        phrase="garden gnome",
        subject="he",
        object="him",
        possessive="his",
        location="aisle",
    ))
    world.add(Entity(
        "store",
        kind="place",
        type="hardware_store",
        label=STORE_NAME,
        phrase="hardware store",
        location="store",
    ))
    world.add(Entity(
        "display",
        kind="thing",
        type="display",
        label=aisle.display_phrase,
        phrase=aisle.display_phrase,
        location="aisle",
    ))
    world.add(Entity(
        "source",
        kind="thing",
        type="problem_source",
        label=problem.hidden_item,
        phrase=problem.hidden_item,
        location="aisle",
    ))
    world.add(Entity(
        "relation",
        kind="social",
        type="friendship",
        label="friendship",
        phrase="friendship",
        location="aisle",
        meters=defaultdict(float, {"friendship": 1.0}),
    ))

    introduce(world)
    disturbance(world)

    world.para()
    quick_blame(world)
    noticing_turn(world)

    world.para()
    solve_problem(world)
    reconcile(world)

    world.para()
    ending(world)
    return world


def prompts_for(world: World) -> list[str]:
    return [
        'Write a Nursery Rhyme style story set in a hardware store using the words "silent fox cub" and "garden gnome."',
        f"Build suspense around {world.aisle.phrase} by using a hidden sound that comes from {world.problem.origin_phrase}.",
        f"Resolve the trouble through problem solving with {world.plan.tool_phrase}, then end in reconciliation and one calm closing image.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    fox = world.get("fox").label
    gnome = world.get("gnome").label
    return [
        QAItem(
            question="What made the hardware store feel suspenseful?",
            answer=(
                f"The suspense started when {world.problem.noise_phrase} came from {world.aisle.hide_phrase} and no one could see the cause. "
                f"Because the sound was hidden, {fox} had to wait, wonder, and watch the shelves instead of fixing the problem at once."
            ),
        ),
        QAItem(
            question=f"Why did {fox} wrongly blame {gnome} at first?",
            answer=(
                f"{fox} saw {gnome} pointing toward the shaking shelf and guessed too quickly that the garden gnome had caused the mischief. "
                f"He had not noticed the clue yet, so the warning pose looked like guilt instead of help."
            ),
        ),
        QAItem(
            question=f"How did {fox} solve the hidden problem?",
            answer=(
                f"He used {world.plan.tool_phrase} and followed the clue until the true cause showed itself. "
                f"That careful little plan turned the mystery into something real and fixable instead of something scary."
            ),
        ),
        QAItem(
            question="How did the story reach reconciliation?",
            answer=(
                f"After the hidden cause was revealed, {fox} understood that {gnome} had been helping all along. "
                f"He made a clear silent apology, and {gnome} forgave him, so their friendship settled back into place with the shelf."
            ),
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hardware store?",
            answer=(
                "A hardware store is a shop that keeps tools, fasteners, garden supplies, and repair things. "
                "People go there when something needs fixing, hanging, tightening, or tidying."
            ),
        ),
        QAItem(
            question="Why can gestures help with problem solving?",
            answer=(
                "Gestures can point to a clue even when words are missing or too slow. "
                "They help people share attention, compare what they see, and choose a useful next step."
            ),
        ),
        QAItem(
            question="What does reconciliation mean after a misunderstanding?",
            answer=(
                "Reconciliation means the hurt between friends is honestly mended after someone was blamed unfairly. "
                "It needs understanding, a real apology, and a willing answer from the friend who was hurt."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    world.facts["story"] = story
    sample = StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )
    return sample


ASP_RULES = r"""
valid(A,P,L) :-
    aisle(A),
    problem(P),
    plan(L),
    requires_aisle(P,T),
    supports_aisle(A,T),
    needs_peek(P,NP), gives_peek(L,GP), GP >= NP,
    needs_trace(P,NT), gives_trace(L,GT), GT >= NT,
    needs_lift(P,NL), gives_lift(L,GL), GL >= NL,
    needs_high(P,NH), gives_high(L,GH), GH >= NH,
    needs_steady(P,NS), gives_steady(L,GS), GS >= NS,
    needs_magnet(P,NM), gives_magnet(L,GM), GM >= NM,
    needs_hook(P,NK), gives_hook(L,GK), GK >= NK.

#show valid/3.
"""


def asp_facts() -> str:
    rows: list[str] = []
    for aisle_id, aisle in AISLES.items():
        rows.append(f"aisle({aisle_id}).")
        for tag in sorted(aisle.tags):
            rows.append(f"supports_aisle({aisle_id},{tag}).")
    for problem_id, problem in PROBLEMS.items():
        rows.append(f"problem({problem_id}).")
        rows.append(f"requires_aisle({problem_id},{problem.aisle_tag}).")
        rows.append(f"needs_peek({problem_id},{problem.needs_peek}).")
        rows.append(f"needs_trace({problem_id},{problem.needs_trace}).")
        rows.append(f"needs_lift({problem_id},{problem.needs_lift}).")
        rows.append(f"needs_high({problem_id},{problem.needs_high}).")
        rows.append(f"needs_steady({problem_id},{problem.needs_steady}).")
        rows.append(f"needs_magnet({problem_id},{problem.needs_magnet}).")
        rows.append(f"needs_hook({problem_id},{problem.needs_hook}).")
    for plan_id, plan in PLANS.items():
        rows.append(f"plan({plan_id}).")
        rows.append(f"gives_peek({plan_id},{plan.peek}).")
        rows.append(f"gives_trace({plan_id},{plan.trace}).")
        rows.append(f"gives_lift({plan_id},{plan.lift}).")
        rows.append(f"gives_high({plan_id},{plan.high}).")
        rows.append(f"gives_steady({plan_id},{plan.steady}).")
        rows.append(f"gives_magnet({plan_id},{plan.magnet}).")
        rows.append(f"gives_hook({plan_id},{plan.hook}).")
    return "\n".join(rows) + "\n"


def asp_program() -> str:
    return asp_facts() + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise StoryError("verify: sample world is missing")
    story_lower = sample.story.lower()
    if "hardware store" not in story_lower:
        raise StoryError("verify: story forgot the hardware store setting")
    if "silent fox cub" not in story_lower:
        raise StoryError("verify: story forgot the seed phrase 'silent fox cub'")
    if "garden gnome" not in story_lower:
        raise StoryError("verify: story forgot the seed phrase 'garden gnome'")
    if sample.story.count("\n\n") < 3:
        raise StoryError("verify: story should have at least four paragraphs")
    if not world.facts.get("resolved"):
        raise StoryError("verify: story did not resolve the hidden hardware trouble")
    if not world.facts.get("reconciled"):
        raise StoryError("verify: story did not reach reconciliation")
    if world.get("source").meters["found"] < 1.0:
        raise StoryError("verify: hidden cause was never found")
    if world.get("relation").meters["strain"] != 0.0:
        raise StoryError("verify: friendship strain remained at the end")
    if len(sample.prompts) != 3:
        raise StoryError("verify: expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise StoryError("verify: QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("verify: unresolved formatting leaked into story text")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise StoryError(f"verify: answer too short for question: {item.question}")


def verify() -> int:
    py = sorted(valid_combos())
    lp = sorted(asp_valid_combos())
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        print("MISMATCH between Python and ASP gates:")
        if only_py:
            print("  only in Python:", only_py)
        if only_lp:
            print("  only in ASP:", only_lp)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid hardware-store stories).")
    for params in all_params():
        verify_sample(generate(params))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate nursery-rhyme hardware-store stories about a silent fox cub and a garden gnome."
    )
    parser.add_argument("--aisle", choices=sorted(AISLES))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    out: list[StoryParams] = []
    for params in all_params():
        if args.aisle is not None and params.aisle != args.aisle:
            continue
        if args.problem is not None and params.problem != args.problem:
            continue
        if args.plan is not None and params.plan != args.plan:
            continue
        out.append(params)
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = all(getattr(args, field) is not None for field in ("aisle", "problem", "plan"))
    if explicit:
        chosen = StoryParams(args.aisle, args.problem, args.plan, args.seed)
        ok, reason = reasonableness_report(AISLES[chosen.aisle], PROBLEMS[chosen.problem], PLANS[chosen.plan])
        if not ok:
            raise StoryError(reason)
        return chosen

    matches = matching_params(args)
    if not matches:
        aisle_id = args.aisle or next(iter(AISLES))
        problem_id = args.problem or next(iter(PROBLEMS))
        plan_id = args.plan or next(iter(PLANS))
        raise StoryError(explain_rejection(aisle_id, problem_id, plan_id))
    chosen = rng.choice(matches)
    return StoryParams(chosen.aisle, chosen.problem, chosen.plan, args.seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    matches = matching_params(args)
    if not matches:
        aisle_id = args.aisle or next(iter(AISLES))
        problem_id = args.problem or next(iter(PROBLEMS))
        plan_id = args.plan or next(iter(PLANS))
        raise StoryError(explain_rejection(aisle_id, problem_id, plan_id))

    if args.all:
        samples: list[StorySample] = []
        for index, params in enumerate(matches):
            chosen = StoryParams(params.aisle, params.problem, params.plan, args.seed + index)
            samples.append(generate(chosen))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    for index in range(max(1, args.n)):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params = StoryParams(params.aisle, params.problem, params.plan, base_seed + index)
        samples.append(generate(params))
    return samples


def dump_trace(world: World) -> str:
    lines = ["TRACE", f"params: aisle={world.params.aisle} problem={world.params.problem} plan={world.params.plan}"]
    for event in world.history:
        detail = ", ".join(f"{k}={v}" for k, v in event.items() if k != "event")
        lines.append(f"- {event['event']}: {detail}")
    lines.append("ENTITIES")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
        if meters:
            lines.append(f"    meters={meters}")
        if memes:
            lines.append(f"    memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid hardware-store stories:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== silent_fox_cub_garden_gnome_hardware_store_2 "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
