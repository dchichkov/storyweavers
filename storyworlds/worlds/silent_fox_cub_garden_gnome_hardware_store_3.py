#!/usr/bin/env python3
"""
storyworlds/worlds/silent_fox_cub_garden_gnome_hardware_store_3.py
==================================================================

Nursery-rhyme storyworld about a silent fox cub, a garden gnome, and a hidden
hardware-store rattle.

Internal source tale:
In Bramble Bin Hardware, a silent fox cub named Pip helps straighten the
garden aisle while Mosscap the garden gnome keeps watch from a painted shelf.
Near closing time, a strange little clatter starts. Pip wrongly blames Mosscap,
but the gnome is really pointing toward the clue. Pip uses the right tool for
the right shelf, finds the true cause, and mends the hurt with an apology
before the hardware store grows still again.
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


STORE_NAME = "Bramble Bin Hardware"
FOX_NAME = "Pip"
GNOME_NAME = "Mosscap"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    subject: str
    object: str
    possessive: str
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class Shelf:
    id: str
    phrase: str
    display_text: str
    clue_spot: str
    closing_image: str
    allowed_plans: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    id: str
    label: str
    shelf: str
    sound_text: str
    origin_phrase: str
    clue_text: str
    wrong_guess_text: str
    reveal_text: str
    risk_text: str
    carrier_text: str
    needs: tuple[str, ...]
    compatible_plans: tuple[str, ...]


@dataclass(frozen=True)
class Plan:
    id: str
    phrase: str
    tool_label: str
    method_text: str
    helper_text: str
    apology_text: str
    rhyme_line: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class StoryParams:
    shelf: str
    problem: str
    plan: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams, shelf: Shelf, problem: Problem, plan: Plan) -> None:
        self.params = params
        self.shelf = shelf
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
            "resolved": False,
            "reconciled": False,
        }

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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


SHELVES: dict[str, Shelf] = {
    "seed_endcap": Shelf(
        id="seed_endcap",
        phrase="the seed-drawer endcap",
        display_text="painted seed drawers, terracotta saucers, and a watering can with a moon-round belly",
        clue_spot="under the seed drawers",
        closing_image="the seed drawers sat straight beside a moon of terracotta saucers, and the little lamp made the brass bits gleam softly",
        allowed_plans=("magnet_string", "crook_hook"),
    ),
    "can_hook_row": Shelf(
        id="can_hook_row",
        phrase="the watering-can hook row",
        display_text="long-nosed cans, bright brass hooks, and a red stepstool tucked by the wall",
        clue_spot="high over the hanging cans",
        closing_image="the watering cans hung still as pears, and the red stepstool rested flat with its feet square on the floor",
        allowed_plans=("stepstool_turn",),
    ),
    "twine_nook": Shelf(
        id="twine_nook",
        phrase="the twine-and-stakes nook",
        display_text="round spools of jute, little bundles of stakes, and a sample gate with one silver bell",
        clue_spot="behind the twine rack",
        closing_image="the twine slept in tidy circles, and the silver gate bell stayed still as a bead of dew",
        allowed_plans=("crook_hook",),
    ),
}


PROBLEMS: dict[str, Problem] = {
    "washer_tin": Problem(
        id="washer_tin",
        label="a runaway tin of brass washers",
        shelf="seed_endcap",
        sound_text="clink-clink-clink",
        origin_phrase="the dark little gap under the seed drawers",
        clue_text="a bright dust of brass by the drawer toes",
        wrong_guess_text="Pip thought Mosscap's clay shoe must have bumped the shelf.",
        reveal_text="Out slid a runaway tin of brass washers. Its paper band had popped, and the round tin had rolled itself into the gap.",
        risk_text="Each tiny clink made the low drawers quiver, as if one more shiver might spill shiny rings across the floor.",
        carrier_text="the tin of brass washers tucked in the drawer gap",
        needs=("magnet",),
        compatible_plans=("magnet_string",),
    ),
    "seed_scoop": Problem(
        id="seed_scoop",
        label="a cedar seed scoop wedged askew",
        shelf="seed_endcap",
        sound_text="scritch-cluck-scritch",
        origin_phrase="the hush behind the drawer faces",
        clue_text="a cedar shaving caught on the lip of one drawer",
        wrong_guess_text="Pip thought Mosscap's red hat must have nudged the drawer front.",
        reveal_text="Behind the drawer face sat a cedar seed scoop wedged sideways, scraping each time the drawer settled back into place.",
        risk_text="The sound was small and spooky, and Pip feared the drawer might jam shut before morning.",
        carrier_text="the cedar scoop lodged behind the seed drawer",
        needs=("hook",),
        compatible_plans=("crook_hook",),
    ),
    "hook_tap": Problem(
        id="hook_tap",
        label="a loose hook tapping a watering can",
        shelf="can_hook_row",
        sound_text="tap-ting, tap-ting",
        origin_phrase="the bright space over the hanging cans",
        clue_text="one watering can swaying while all the others stayed still",
        wrong_guess_text="Pip thought the garden gnome had rattled the cans for a joke.",
        reveal_text="High above them, one loose brass hook kept kissing a watering can each time the ceiling fan gave a sleepy puff.",
        risk_text="The sharp little ting sounded taller each time, and Pip worried the can might tumble if nobody steadied it.",
        carrier_text="the loose brass hook above the watering cans",
        needs=("reach", "steady"),
        compatible_plans=("stepstool_turn",),
    ),
    "twine_spool": Problem(
        id="twine_spool",
        label="a snagged spool of green twine",
        shelf="twine_nook",
        sound_text="zip-clack, zip-clack",
        origin_phrase="the shadow by the sample gate",
        clue_text="a green thread creeping over the floorboards",
        wrong_guess_text="Pip thought Mosscap had tugged the sample gate ribbon for fun.",
        reveal_text="A spool of green twine had caught on a scoop handle and was tugging the gate bell each time it unwound another inch.",
        risk_text="Each little zip pulled the knot tighter, so the bell snapped back louder and louder in the nook.",
        carrier_text="the twine spool caught behind the sample gate",
        needs=("hook",),
        compatible_plans=("crook_hook",),
    ),
}


PLANS: dict[str, Plan] = {
    "magnet_string": Plan(
        id="magnet_string",
        phrase="trail a blue string with a horseshoe magnet",
        tool_label="a blue string with a horseshoe magnet",
        method_text="Pip lowered the magnet into the dark gap and listened for the shy little click when metal met metal. Then he drew the string back one slow inch at a time.",
        helper_text="Mosscap pointed his painted spade at the brightest brass dust, so Pip knew exactly where to aim.",
        apology_text="Pip pressed one paw to his chest, bowed low to Mosscap, and admitted that he had blamed the wrong friend.",
        rhyme_line='He hummed, "Blue string, true string, bring the bright thing home."',
        capabilities=("magnet",),
    ),
    "crook_hook": Plan(
        id="crook_hook",
        phrase="slide a bent plant hook behind the shelf",
        tool_label="a bent plant hook",
        method_text="Pip eased the hook through the shadow and felt gently for the hidden snag. When the hook caught, he drew the trouble out a careful inch at a time so nothing jumped or spilled.",
        helper_text="Mosscap tapped the right spot with the end of his painted shovel, turning his silence into a clear little signal.",
        apology_text="Pip brushed the dust from Mosscap's coat, whispered sorry, and thanked him for pointing instead of pouting.",
        rhyme_line='He hummed, "Hook low, hook slow, show what shadows know."',
        capabilities=("hook",),
    ),
    "stepstool_turn": Plan(
        id="stepstool_turn",
        phrase="climb a red stepstool and tighten the top hook",
        tool_label="a red stepstool and a tiny wrench",
        method_text="Pip climbed just high enough to steady the swaying can. Then he turned the small nut with the wrench until the tapping thinned, sighed, and stopped.",
        helper_text="Mosscap planted both clay boots on the stepstool footboard, keeping it firm while Pip reached up.",
        apology_text="Pip touched Mosscap's hand, owned his mistake, and thanked him for holding the stool steady when the aisle felt tall.",
        rhyme_line='He hummed, "Step high, step shy, make the sharp taps sigh."',
        capabilities=("reach", "steady"),
    ),
}


def reasonableness_report(shelf: Shelf, problem: Problem, plan: Plan) -> tuple[bool, str]:
    if problem.shelf != shelf.id:
        return False, f"{problem.label.capitalize()} belongs at {SHELVES[problem.shelf].phrase}, not at {shelf.phrase}."
    if plan.id not in shelf.allowed_plans:
        return False, f"{plan.tool_label.capitalize()} does not fit the space and setup at {shelf.phrase}."
    if plan.id not in problem.compatible_plans:
        return False, f"{plan.tool_label.capitalize()} does not solve the real cause behind {problem.label}."
    for need in problem.needs:
        if need not in plan.capabilities:
            return False, f"{plan.tool_label.capitalize()} is missing the physical step this problem needs: {need}."
    return True, ""


def valid_combo(shelf_id: str, problem_id: str, plan_id: str) -> bool:
    ok, _reason = reasonableness_report(SHELVES[shelf_id], PROBLEMS[problem_id], PLANS[plan_id])
    return ok


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for shelf_id in sorted(SHELVES):
        for problem_id in sorted(PROBLEMS):
            for plan_id in sorted(PLANS):
                if valid_combo(shelf_id, problem_id, plan_id):
                    combos.append((shelf_id, problem_id, plan_id))
    return combos


def all_params() -> list[StoryParams]:
    return [StoryParams(shelf=s, problem=p, plan=l) for s, p, l in valid_combos()]


def explain_rejection(shelf_id: str, problem_id: str, plan_id: str) -> str:
    ok, reason = reasonableness_report(SHELVES[shelf_id], PROBLEMS[problem_id], PLANS[plan_id])
    if ok:
        return "valid"
    return reason


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    matches: list[StoryParams] = []
    for params in all_params():
        if args.shelf is not None and params.shelf != args.shelf:
            continue
        if args.problem is not None and params.problem != args.problem:
            continue
        if args.plan is not None and params.plan != args.plan:
            continue
        matches.append(params)
    return matches


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.shelf, params.problem, params.plan):
        raise StoryError(explain_rejection(params.shelf, params.problem, params.plan))

    shelf = SHELVES[params.shelf]
    problem = PROBLEMS[params.problem]
    plan = PLANS[params.plan]
    world = World(params=params, shelf=shelf, problem=problem, plan=plan)

    fox = world.add(
        Entity(
            id="fox",
            kind="animal",
            type="fox_cub",
            label=f"{FOX_NAME} the silent fox cub",
            phrase="the silent fox cub",
            subject="he",
            object="him",
            possessive="his",
            location=shelf.phrase,
        )
    )
    gnome = world.add(
        Entity(
            id="gnome",
            kind="figure",
            type="garden_gnome",
            label=f"{GNOME_NAME} the garden gnome",
            phrase="the garden gnome",
            subject="he",
            object="him",
            possessive="his",
            location=shelf.phrase,
        )
    )
    world.add(
        Entity(
            id="shelf",
            kind="place",
            type="hardware_aisle",
            label=shelf.phrase,
            phrase=shelf.phrase,
            subject="it",
            object="it",
            possessive="its",
            location=STORE_NAME,
        )
    )
    source = world.add(
        Entity(
            id="source",
            kind="object",
            type="hidden_cause",
            label=problem.label,
            phrase=problem.label,
            subject="it",
            object="it",
            possessive="its",
            location=problem.origin_phrase,
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            kind="tool",
            type="hardware_tool",
            label=plan.tool_label,
            phrase=plan.tool_label,
            subject="it",
            object="it",
            possessive="its",
            location=shelf.phrase,
        )
    )
    relation = world.add(
        Entity(
            id="relation",
            kind="relation",
            type="friendship",
            label="the trust between Pip and Mosscap",
            phrase="their friendship",
            subject="it",
            object="it",
            possessive="its",
            location=shelf.phrase,
        )
    )

    fox.meters["steps"] = 1.0
    fox.memes["care"] = 0.8
    fox.memes["worry"] = 0.1
    gnome.meters["steady"] = 1.0
    gnome.memes["patience"] = 1.0
    source.meters["hidden"] = 1.0
    source.meters["sounding"] = 1.0
    source.meters["found"] = 0.0
    tool.meters["ready"] = 1.0
    relation.meters["strain"] = 0.0
    relation.memes["trust"] = 0.8

    world.facts["carrier"] = problem.carrier_text
    world.facts["wrong_guess"] = problem.wrong_guess_text
    world.facts["plan"] = plan.phrase
    world.facts["shelf"] = shelf.phrase
    world.facts["problem_label"] = problem.label
    return world


def simulate(world: World) -> World:
    fox = world.get("fox")
    gnome = world.get("gnome")
    source = world.get("source")
    relation = world.get("relation")

    world.say(
        f"In {STORE_NAME}, a silent fox cub named {FOX_NAME} padded through {world.shelf.phrase}, "
        f"where {world.shelf.display_text} glowed under the last warm lamp."
    )
    world.say(
        f"On a painted shelf sat {GNOME_NAME}, a garden gnome with a berry-red hat, "
        f"keeping his pebble-still watch over the neat little rows."
    )
    world.say(
        f"{FOX_NAME} liked closing time, when he could set each small thing square and make the hardware store feel tucked in for the night."
    )
    world.note("opening", shelf=world.shelf.id, display=world.shelf.display_text)
    world.para()

    fox.memes["worry"] += 0.6
    source.meters["wobble"] = 1.0
    relation.meters["strain"] = 0.5
    relation.memes["trust"] -= 0.3
    world.say(
        f"Then came {world.problem.sound_text} from {world.problem.origin_phrase}, and the whole nook seemed to hold its breath."
    )
    world.say(
        f"{FOX_NAME} froze so still that even his whiskers seemed to wait. {world.problem.risk_text}"
    )
    world.say(world.problem.wrong_guess_text)
    world.note(
        "suspense",
        sound=world.problem.sound_text,
        origin=world.problem.origin_phrase,
        wrong_guess="gnome",
        risk=world.problem.risk_text,
    )
    world.para()

    world.say(
        f"{GNOME_NAME} did not argue. He only lifted his painted hand toward {world.problem.clue_text}, as if his silence were an arrow."
    )
    world.say(world.plan.helper_text)
    world.say(
        f"{FOX_NAME} looked twice, and then twice again, until he saw {world.problem.clue_text} and knew the trouble was hiding in a real thing."
    )
    world.say(world.plan.rhyme_line)
    world.say(world.plan.method_text)
    source.meters["hidden"] = 0.0
    source.meters["found"] = 1.0
    source.meters["sounding"] = 0.0
    source.meters["wobble"] = 0.0
    fox.memes["worry"] -= 0.4
    fox.memes["care"] += 0.1
    world.say(world.problem.reveal_text)
    world.facts["resolved"] = True
    world.note(
        "solve",
        clue=world.problem.clue_text,
        plan=world.plan.id,
        tool=world.plan.tool_label,
        reveal=world.problem.label,
    )
    world.para()

    relation.meters["strain"] = 0.0
    relation.memes["trust"] = 1.0
    fox.memes["guilt"] = 0.2
    fox.memes["relief"] = 0.9
    world.say(
        f"At once {FOX_NAME} understood that {GNOME_NAME} had been helping, not teasing, and the tight little knot in his chest came loose."
    )
    world.say(world.plan.apology_text)
    world.say(
        f"Together they set the shelf to rights, and soon {world.shelf.closing_image}."
    )
    world.say(
        f"So the hardware store ended in a hush: no {world.problem.sound_text}, no sore feelings, only a mended friendship and a tidy row asleep till dawn."
    )
    world.facts["reconciled"] = True
    world.note(
        "reconcile",
        apology=world.plan.apology_text,
        final_image=world.shelf.closing_image,
        trust=relation.memes["trust"],
    )
    return world


def _prompts(world: World) -> list[str]:
    return [
        f"Write a Nursery Rhyme style story set in a hardware store and include the exact seed words silent fox cub and garden gnome.",
        f"Build suspense around {world.problem.label} at {world.shelf.phrase}, and let the danger stay physical: {world.problem.risk_text}",
        f"Resolve the trouble through problem solving with {world.plan.tool_label} and end on reconciliation plus this concrete image: {world.shelf.closing_image}.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What was really making the strange sound in the hardware store?",
            f"The strange sound came from {world.problem.carrier_text}. "
            f"That mattered because the suspense rode on a real hidden object, and the story could only settle once Pip found that object and stopped it.",
        ),
        QAItem(
            f"Why did {FOX_NAME} first blame {GNOME_NAME}?",
            f"{FOX_NAME} blamed {GNOME_NAME} because the noise began near the gnome's shelf and he had not yet seen the true clue. "
            f"When he finally noticed {world.problem.clue_text}, he understood that the gnome had been pointing toward the cause instead of making mischief.",
        ),
        QAItem(
            f"How did {FOX_NAME} solve the problem?",
            f"{FOX_NAME} chose to {world.plan.phrase}. "
            f"That worked because the plan matched the physical need of the problem, letting him reach or catch the hidden source without making the shelf less steady.",
        ),
        QAItem(
            "How did the ending prove that the friendship was repaired?",
            f"The friendship was repaired when Pip apologized after the true cause was found, so blame gave way to gratitude instead of hanging in the air. "
            f"The ending then showed the change in the room itself: {world.shelf.closing_image}.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why would the wrong solving plan fail?",
            f"The wrong plan would fail because each shelf problem needs a believable physical method, not just any tidy-sounding fix. "
            f"Here, {world.problem.label} needs {', '.join(world.problem.needs)}, so a plan without that ability would not reasonably uncover or stop the cause.",
        ),
        QAItem(
            "What object carries the suspense in this story?",
            f"The suspense is carried by a concrete object rather than by a floating mood alone. "
            f"Here that carrier is {world.problem.carrier_text}, which is why the clue, the method, and the ending image can all stay grounded.",
        ),
        QAItem(
            "How is reconciliation tied to the solved problem instead of added as a moral afterthought?",
            f"Reconciliation only happens after the hidden source is found and the friendship strain can honestly drop back to zero. "
            f"The apology is therefore caused by new knowledge, and the calm shelf at the end proves that both the problem and the hurt feeling were repaired.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
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
valid(S,P,L) :-
    shelf(S),
    problem(P),
    plan(L),
    problem_at(P,S),
    shelf_allows(S,L),
    problem_allows(P,L),
    not unmet_need(P,L).

unmet_need(P,L) :-
    plan(L),
    problem_needs(P,N),
    not plan_has(L,N).

ok :-
    chosen(S,P,L),
    valid(S,P,L).

#show valid/3.
#show ok/0.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for shelf_id, shelf in sorted(SHELVES.items()):
        rows.append(asp.fact("shelf", shelf_id))
        for plan_id in shelf.allowed_plans:
            rows.append(asp.fact("shelf_allows", shelf_id, plan_id))
    for problem_id, problem in sorted(PROBLEMS.items()):
        rows.append(asp.fact("problem", problem_id))
        rows.append(asp.fact("problem_at", problem_id, problem.shelf))
        for plan_id in problem.compatible_plans:
            rows.append(asp.fact("problem_allows", problem_id, plan_id))
        for need in problem.needs:
            rows.append(asp.fact("problem_needs", problem_id, need))
    for plan_id, plan in sorted(PLANS.items()):
        rows.append(asp.fact("plan", plan_id))
        for capability in plan.capabilities:
            rows.append(asp.fact("plan_has", plan_id, capability))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        import asp

        chosen = asp.fact("chosen", params.shelf, params.problem, params.plan) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    import asp

    combos: set[tuple[str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "valid"))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    import asp

    model = asp.one_model(asp_program(params))
    return bool(asp.atoms(model, "ok"))


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
        raise StoryError("verify: the hidden cause was never resolved")
    if not world.facts.get("reconciled"):
        raise StoryError("verify: the friendship never reconciled")
    if world.get("source").meters["found"] < 1.0:
        raise StoryError("verify: the story never found the physical source")
    if world.get("relation").meters["strain"] != 0.0:
        raise StoryError("verify: friendship strain remained at the end")
    if len(sample.prompts) != 3:
        raise StoryError("verify: expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise StoryError("verify: QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("verify: unresolved formatting leaked into story text")
    for item in sample.story_qa:
        if item.answer.count(".") < 2:
            raise StoryError(f"verify: story QA answer is too thin: {item.question}")
    for item in sample.world_qa:
        if item.answer.count(".") < 2:
            raise StoryError(f"verify: world QA answer is too thin: {item.question}")


def verify() -> int:
    py = set(valid_combos())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(py - lp)
        only_lp = sorted(lp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_lp}")

    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(shelf=combo[0], problem=combo[1], plan=combo[2], seed=index)
        if not asp_accepts(params):
            raise StoryError(f"verify: ASP rejected valid combo {combo!r}")
        verify_sample(generate(params))

    print(f"OK: {len(py)} valid combos; ASP parity holds; generated stories pass quality checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate nursery-rhyme hardware-store stories about a silent fox cub and a garden gnome."
    )
    parser.add_argument("--shelf", choices=sorted(SHELVES), default=None)
    parser.add_argument("--problem", choices=sorted(PROBLEMS), default=None)
    parser.add_argument("--plan", choices=sorted(PLANS), default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    if args.shelf is not None and args.problem is not None and args.plan is not None:
        params = StoryParams(shelf=args.shelf, problem=args.problem, plan=args.plan, seed=args.seed)
        if not valid_combo(params.shelf, params.problem, params.plan):
            raise StoryError(explain_rejection(params.shelf, params.problem, params.plan))
        return params

    matches = matching_params(args)
    if not matches:
        shelf_id = args.shelf or sorted(SHELVES)[0]
        problem_id = args.problem or sorted(PROBLEMS)[0]
        plan_id = args.plan or sorted(PLANS)[0]
        raise StoryError(explain_rejection(shelf_id, problem_id, plan_id))

    chooser = rng or random.Random(args.seed)
    chosen = chooser.choice(matches)
    return StoryParams(chosen.shelf, chosen.problem, chosen.plan, seed=args.seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    matches = matching_params(args)
    if not matches:
        shelf_id = args.shelf or sorted(SHELVES)[0]
        problem_id = args.problem or sorted(PROBLEMS)[0]
        plan_id = args.plan or sorted(PLANS)[0]
        raise StoryError(explain_rejection(shelf_id, problem_id, plan_id))

    if args.all:
        samples: list[StorySample] = []
        for index, params in enumerate(matches):
            chosen = StoryParams(params.shelf, params.problem, params.plan, seed=args.seed + index)
            samples.append(generate(chosen))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params = StoryParams(params.shelf, params.problem, params.plan, seed=base_seed + index)
        samples.append(generate(params))
    return samples


def dump_trace(world: World) -> str:
    lines = [
        "TRACE",
        f"params: shelf={world.params.shelf} problem={world.params.problem} plan={world.params.plan}",
    ]
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


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if args.qa:
        print()
        print(format_qa(sample))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return verify()
    if args.asp:
        combos = sorted(asp_valid_combos())
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

    for index, sample in enumerate(samples):
        header = None
        if len(samples) > 1:
            header = f"=== sample {index + 1} / {len(samples)} :: {sample.params.shelf}, {sample.params.problem}, {sample.params.plan} ==="
        emit(sample, args, header)
        if index + 1 < len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
