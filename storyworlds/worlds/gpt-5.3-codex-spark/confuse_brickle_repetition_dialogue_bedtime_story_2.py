#!/usr/bin/env python3
"""confuse_brickle_repetition_dialogue_bedtime_story_2.py
=======================================================

Internal source tale
-------------------
At bedtime in a small room, a child and a patient adult hear a repeated
"brickle, brickle, brickle" from somewhere near the bedtime crafts.
The repetition makes the child confuse what is happening, so they pause and
follow the clue carefully through dialogue. They identify the physical source and
solve it with a matched method, then the room settles into an image that proves the
change is real.

Seed words: confuse, brickle
Features: Repetition, Dialogue
Style: Bedtime Story
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class BedScene:
    key: str
    label: str
    opening: str
    ending_image: str
    allowed_methods: tuple[str, ...]


@dataclass(frozen=True)
class BrindleProblem:
    key: str
    label: str
    scene: str
    refrain: str
    note: str
    cause: str
    need: str
    fixed_image: str
    compatible_methods: tuple[str, ...]


@dataclass(frozen=True)
class HelperMethod:
    key: str
    label: str
    action_text: str
    reason: str
    solves: str
    helper_line: str


@dataclass(frozen=True)
class StoryParams:
    scene: str
    problem: str
    method: str
    hero: str
    hero_kind: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    phrase: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "grandfather", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryBeat:
    id: str
    text: str


@dataclass
class World:
    params: StoryParams
    scene_cfg: BedScene
    problem_cfg: BrindleProblem
    method_cfg: HelperMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str | int | float | bool] = field(default_factory=dict)
    beats: list[StoryBeat] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired_rules: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, beat: str, text: str) -> None:
        self.beats.append(StoryBeat(beat, text))

    def render(self) -> str:
        return "\n\n".join(" ".join(bits) for bits in self.paragraphs if bits)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"scene={self.scene_cfg.key} problem={self.problem_cfg.key} method={self.method_cfg.key}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name}<{ent.kind}> loc={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"facts={self.facts}")
        rows.append(f"beats={len(self.beats)}")
        for beat in self.beats:
            rows.append(f"  {beat.id}: {beat.text}")
        rows.append(f"fired_rules={self.fired_rules}")
        return "\n".join(rows)


SCENES: dict[str, BedScene] = {
    "window_hollow": BedScene(
        key="window_hollow",
        label="the moonlit window hollow",
        opening="a folded blanket sat on the window bench, and the quilt smelled like warm soap",
        ending_image="the moon curtain hung still, and the window hollow stayed quiet as a soft breath",
        allowed_methods=("tie_down_loop", "add_soft_tension"),
    ),
    "sleep_nest": BedScene(
        key="sleep_nest",
        label="the blanket nest beside the night lamp",
        opening="pillows curved around the bed, and the room had the kind of hush that belongs to bedtime",
        ending_image="the nest stayed rounded, the lamp glow even, and the room no longer shook in little bursts",
        allowed_methods=("unwind_tangle", "add_soft_tension"),
    ),
}

PROBLEMS: dict[str, BrindleProblem] = {
    "wandering_bell": BrindleProblem(
        key="wandering_bell",
        label="the wind bell on a curtain loop",
        scene="window_hollow",
        refrain='"brickle, brickle, brickle"',
        note="The sound repeated as a soft, quick tapping from one corner of the curtain.",
        cause="the bell tie had slipped out of the loop and drummed once each time the air moved it.",
        need="stabilize",
        fixed_image="the curtain loop sat tight, and the wind bell no longer knocked the same point every breath.",
        compatible_methods=("tie_down_loop", "add_soft_tension"),
    ),
    "breezy_sheet": BrindleProblem(
        key="breezy_sheet",
        scene="sleep_nest",
        label="the shell charm near the story shelf",
        refrain='"brickle, brickle, brickle"',
        note="The sound came from the same shell edge brushing the shelf every few seconds.",
        cause="the shell chain was caught in a small loop and kept tugging whenever the blanket moved.",
        need="untangle",
        fixed_image="the chain sat loose across the shelf, and the shell charm balanced on its stand without scraping.",
        compatible_methods=("unwind_tangle", "add_soft_tension"),
    ),
}

METHODS: dict[str, HelperMethod] = {
    "tie_down_loop": HelperMethod(
        key="tie_down_loop",
        label="tie down the loose loop",
        action_text=(
            "{helper} knelt close, held the loop with one hand, and showed {hero} where to make one slow loop and knot."
        ),
        reason=(
            "A stable tie stops the loop from drifting, so the tapping source loses the repeated jerk that caused the brickle sound."
        ),
        solves="stabilize",
        helper_line='"Let us hold the knot first, then count the taps," {helper} said softly.',
    ),
    "unwind_tangle": HelperMethod(
        key="unwind_tangle",
        label="unwind the shell knot",
        action_text=(
            "{helper} and {hero} gently unwound the loop, then set the chain so it rested in a wide circle."
        ),
        reason=(
            "Unwinding removes the extra overlap so the object no longer brushes the shelf and taps by itself."
        ),
        solves="untangle",
        helper_line='"Small sounds are clues, not ghosts," {helper} whispered. "We can fix this by untying the loop."',
    ),
    "add_soft_tension": HelperMethod(
        key="add_soft_tension",
        label="add a soft safety brace",
        action_text=(
            "{hero} held the soft strip while {helper} eased the object into place with two careful breaths."
        ),
        reason=(
            "Supporting the edge slows the quick motion that repeats the noise."
        ),
        solves="stabilize",
        helper_line='"Let us give it one softer path," {helper} said. "Not a sharp move—just a calm one."',
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Lena", "Mina", "Nora", "Ada"),
    "boy": ("Noah", "Ravi", "Leo", "Sam"),
}

HELPERS: tuple[str, ...] = (
    "Grandma June",
    "Mama Rowan",
    "Uncle Finn",
    "Nana Rose",
)


def _pick_hero(kind: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[kind])


def _pick_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)


def valid_combo(scene_key: str, problem_key: str, method_key: str) -> bool:
    if scene_key not in SCENES or problem_key not in PROBLEMS or method_key not in METHODS:
        return False
    scene = SCENES[scene_key]
    problem = PROBLEMS[problem_key]
    method = METHODS[method_key]
    return (
        problem.scene == scene.key
        and method_key in scene.allowed_methods
        and method_key in problem.compatible_methods
        and method.solves == problem.need
    )


def invalid_reason(scene_key: str, problem_key: str, method_key: str) -> str:
    if scene_key and scene_key not in SCENES:
        return f"No story: unknown scene {scene_key!r}."
    if problem_key and problem_key not in PROBLEMS:
        return f"No story: unknown problem {problem_key!r}."
    if method_key and method_key not in METHODS:
        return f"No story: unknown method {method_key!r}."

    if scene_key and problem_key and (scene_key != PROBLEMS[problem_key].scene):
        return (
            f"No story: {PROBLEMS[problem_key].label} belongs to {SCENES[PROBLEMS[problem_key].scene].label}, "
            f"not {SCENES[scene_key].label}."
        )
    if scene_key and method_key:
        scene = SCENES[scene_key]
        method = METHODS[method_key]
        if method_key not in scene.allowed_methods:
            return (
                f"No story: scene {scene.label} does not host method {method.label}. "
                f"Try one of: {', '.join(scene.allowed_methods)}."
            )
    if problem_key and method_key:
        problem = PROBLEMS[problem_key]
        method = METHODS[method_key]
        if method_key not in problem.compatible_methods:
            return (
                f"No story: method {method.label} is not a compatible repair for {problem.label}. "
                f"This problem needs a solution of type {problem.need}."
            )
    return "No story: incompatible scene/problem/method combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_key in sorted(SCENES):
        for problem_key in sorted(PROBLEMS):
            for method_key in sorted(METHODS):
                if valid_combo(scene_key, problem_key, method_key):
                    combos.append((scene_key, problem_key, method_key))
    return combos


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    matches: list[tuple[str, str, str]] = []
    for combo in combos:
        if args.scene is not None and combo[0] != args.scene:
            continue
        if args.problem is not None and combo[1] != args.problem:
            continue
        if args.method is not None and combo[2] != args.method:
            continue
        matches.append(combo)
    return matches


def reasonableness_gate(params: StoryParams) -> None:
    if not valid_combo(params.scene, params.problem, params.method):
        raise StoryError(invalid_reason(params.scene, params.problem, params.method))


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    scene = SCENES[params.scene]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]
    world = World(params=params, scene_cfg=scene, problem_cfg=problem, method_cfg=method)

    hero = world.add(Entity(name=params.hero, kind=params.hero_kind, phrase=params.hero, location=scene.key))
    helper = world.add(Entity(name=params.helper, kind="helper", phrase=params.helper, location=scene.key))
    room = world.add(
        Entity(
            name=f"room:{scene.key}",
            kind="place",
            phrase=f"bedtime room at {scene.label}",
            location=scene.key,
        )
    )
    source = world.add(
        Entity(
            name=problem.key,
            kind="object",
            phrase=problem.label,
            location=scene.key,
        )
    )
    method_ent = world.add(
        Entity(
            name=method.key,
            kind="method",
            phrase=method.label,
            location=scene.key,
        )
    )

    hero.meters["focus"] = 1.0
    hero.meters["repetitions"] = 0.0
    hero.memes["confidence"] = 0.2
    hero.memes["confusion"] = 0.0

    helper.memes["calm"] = 1.1
    helper.memes["care"] = 1.4

    room.meters["hush"] = 1.0
    room.meters["noise"] = 0.0

    source.meters["signal"] = 0.0
    source.meters["risk"] = 0.0
    source.meters["resolved"] = 0.0
    source.memes["need"] = 1.0

    method_ent.memes["ready"] = 1.0

    world.facts.update(
        {
            "scene": scene.key,
            "problem": problem.key,
            "method": method.key,
            "hero": hero.name,
            "helper": helper.name,
            "seed": params.seed if params.seed is not None else 0,
        }
    )
    return world


def _opening(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    scene = world.scene_cfg
    world.note("opening", "bedtime begins")
    world.say(
        f"At the end of a long day, {hero.name} and {helper.name} sat down at {scene.label}. "
        f"The room was warm with the lamp, and there were no hard sounds except the soft one from the blankets. {scene.opening}."
    )
    world.say(
        f"{hero.name} was finishing night-readiness, and {hero.pronoun('possessive')} small routine felt complete.",
    )
    world.fired_rules.append("opening")


def _repeat_and_confuse(world: World) -> None:
    hero = world.get(world.params.hero)
    problem = world.problem_cfg
    source = world.get(world.params.problem)
    room = world.get(f"room:{world.scene_cfg.key}")

    room.meters["hush"] = 0.7
    source.meters["signal"] = 1.0
    source.meters["risk"] = 0.8
    hero.meters["repetitions"] = 3
    hero.memes["confusion"] = 1.2
    hero.memes["alert"] = 0.6

    world.note("repetition", "sound repeats before action")
    world.para()
    world.say(
        f"Then the room gave the same line again and again: {problem.refrain}, {problem.refrain}, and then one more time." +
        " It sounded gentle but it began to confuse, because the pattern touched the same little object every time."
    )
    world.say(f'"This is enough to confuse me," said {hero.name}.')
    world.say(f'"Let us count before touching anything," {world.get(world.params.helper).name} said.')
    world.say(f"{hero.name} counted each tapping rhythm while {world.get(world.params.helper).name} held {hero.pronoun('object')} from rushing.")
    world.fired_rules.append("repetition")


def _turn(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    method = world.method_cfg
    problem = world.problem_cfg
    source = world.get(world.params.problem)

    source.memes["need"] = 1.0
    source.meters["signal"] = 0.7

    world.para()
    world.say(method.helper_line.format(helper=helper.name).replace("{helper}", helper.name))
    world.say(f'"Could one steady action calm that pattern?" {hero.name} asked.')
    world.say(f'"{method.label} is what we planned," {helper.name} replied.')
    world.say(method.action_text.format(hero=hero.name, helper=helper.name))
    world.say(f"Why this works: {method.reason}")
    world.say(f"They did this exactly because the cause was {problem.cause}")

    source.meters["signal"] = 0.4
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 0.8)
    hero.memes["confidence"] = 1.2
    hero.memes["trust"] = 1.2
    world.fired_rules.append("turn")


def _resolve(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    scene = world.scene_cfg
    problem = world.problem_cfg
    source = world.get(world.params.problem)

    source.meters["signal"] = 0.0
    source.meters["risk"] = 0.0
    source.meters["resolved"] = 1.0
    source.memes["need"] = 0.0
    hero.memes["confusion"] = 0.0
    hero.memes["calm"] = 1.5
    hero.meters["focus"] = 1.5

    world.note("resolved", "problem fixed")
    world.para()
    world.say(
        f'"Now we can hear the room again," {helper.name} said. '
        f'{hero.name} nodded, and the sound was no longer a question.'
    )
    ending_image = scene.ending_image[0].upper() + scene.ending_image[1:]
    world.say(f"{problem.fixed_image.rstrip('.').capitalize()}. {ending_image}.")
    world.say(
        "The final image proved the change: a tiny physical source had moved from shaking and tapping to still rest, "
        f"so bedtime could continue as a calm lesson."
    )
    world.fired_rules.append("resolved")


def simulate(world: World) -> World:
    _opening(world)
    _repeat_and_confuse(world)
    _turn(world)
    _resolve(world)
    return world


def prompts(world: World) -> list[str]:
    return [
        "Write a bedtime story where a repeated brickle sound leads to a gentle state-driven fix.",
        "Include the words confuse and brickle, with clear repetition of brickle at least three times.",
        "Use warm dialogue, then end with a concrete image in the scene proving the room is physically settled for sleep.",
    ]


def story_grounded_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    helper = world.params.helper
    problem = world.problem_cfg
    method = world.method_cfg
    room = world.get(f"room:{world.scene_cfg.key}")
    sound_source = world.get(world.params.problem)
    repetition_count = int(sound_source.meters["resolved"] == 0.0 and 3 or 0)
    _ = repetition_count

    return [
        QAItem(
            "What made the child feel confused?",
            f"The child felt confused because the tiny sound repeated the same way and stayed at the same source, so {hero} could not tell if it was a warning or a toy. "
            "That uncertainty rose with each tap and was tracked as repeated signals in the room state.",
        ),
        QAItem(
            "Where did the repeated brickle sound come from first?",
            f"The repeated line came from {problem.label}, tracked as a physical object in the world. "
            f"Its cause was {problem.cause.rstrip('.')}. That cause made the repeated taps continue through the first phase.",
        ),
        QAItem(
            "How did dialogue change the turn?",
            f"The helper spoke a plan before touching anything, and {hero} and the helper chose {method.label} together. "
            "That avoided a guess-and-push attempt and matched the world state to a safe method with a direct physical cause.",
        ),
        QAItem(
            "How did repetition help solve the puzzle?",
            f"Repetition gave a clear rhythm: the team counted the same phrase three times before acting. "
            "Each pass reduced uncertainty, and when their method was applied, the signal meter moved from active to quiet in the source object.",
        ),
        QAItem(
            "How do we know the ending is real, not just explained away?",
            f"The ending image says the room settled in {world.scene_cfg.label} with the object remaining steady, so the meter for risk is now low in the model. "
            f"{helper} and {hero} can then continue their bedtime routine because the physical source no longer moves and the story leaves a visible change.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    problem = world.problem_cfg
    method = world.method_cfg
    sound_source = world.get(world.params.problem)
    hero = world.get(world.params.hero)

    return [
        QAItem(
            "Why are only some methods allowed for each scene?",
            "Each scene constrains movement and handling. "
            "The contract requires compatibility rules because a method that is safe for one sound source can be unsafe or irrelevant in a different setting.",
        ),
        QAItem(
            "What did the world model mark as the risk at the start of the middle?",
            f"The model held risk for {sound_source.name} at 0.8, then reduced it to 0.0 after the chosen method matched the cause. "
            f"That transition is part of the physical state, not just dialogue wording.",
        ),
        QAItem(
            "How is the helper choice constrained by the problem type?",
            f"The selected method must satisfy the problem need ({problem.need}) and be scene-compatible. "
            f"For {problem.label}, that means {method.label} is valid because its solve tag is {method.solves}.",
        ),
        QAItem(
            "What state tells you the story is truly resolved?",
            "When the sound source's resolved meter reaches 1.0 and its signal drops to 0.0, the simulation marks the conflict as fixed. "
            "The final scene image references both the scene and that object staying still, which is the state-driven closure.",
        ),
        QAItem(
            "How does the repeated line connect to the final image?",
            "The repeated line is used to keep attention on one object and update confidence before action. "
            "After the fix, the line is no longer present and the final image of stillness confirms the earlier repetition worked as a diagnostic rhythm.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(S,P,M) :-
    scene(S), problem(P), method(M),
    problem_in_scene(P,S),
    scene_allows(S,M),
    problem_allows(P,M),
    method_solves(M,N),
    problem_need(P,N).

ok :- chosen(S,P,M), combo(S,P,M).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, scene in sorted(SCENES.items()):
        rows.append(fact("scene", key))
        for method in scene.allowed_methods:
            rows.append(fact("scene_allows", key, method))
    for key, problem in sorted(PROBLEMS.items()):
        rows.append(fact("problem", key))
        rows.append(fact("problem_in_scene", key, problem.scene))
        rows.append(fact("problem_need", key, problem.need))
        for method in problem.compatible_methods:
            rows.append(fact("problem_allows", key, method))
    for key, method in sorted(METHODS.items()):
        rows.append(fact("method", key))
        rows.append(fact("method_solves", key, method.solves))
    if params is not None:
        from storyworlds.asp import fact

        rows.append(fact("chosen", params.scene, params.problem, params.method))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


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
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for i, combo in enumerate(sorted(python_combos), 1):
        params = StoryParams(
            scene=combo[0],
            problem=combo[1],
            method=combo[2],
            hero=HERO_NAMES["girl"][0],
            hero_kind="girl",
            helper=HELPERS[0],
            seed=i,
        )
        if not _asp_accepts(params):
            raise StoryError(f"ASP rejected valid combo {combo!r}.")

        sample = generate(params)
        story = sample.story.lower()
        if "brickle" not in story:
            raise StoryError(f"Generated story for {combo!r} lost seed word brickle.")
        if "confuse" not in story:
            raise StoryError(f"Generated story for {combo!r} lost seed word confuse.")
        if sample.story.count('\"') < 4:
            raise StoryError(f"Generated story for {combo!r} is missing enough dialogue.")
        if story.count("brickle") < 3:
            raise StoryError(f"Generated story for {combo!r} does not show repeated brickle.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} missed complete progression.")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 5:
            raise StoryError(f"Generated story for {combo!r} has incomplete QA.")
        for qa in sample.story_qa + sample.world_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"QA answer too short for {combo!r}: {qa.question!r}")
        if sample.world is None:
            raise StoryError(f"Missing world model for {combo!r}")
        source = sample.world.get(sample.params.problem)
        if source.meters["resolved"] != 1.0:
            raise StoryError(f"Resolution state did not complete for {combo!r}.")

    return f"OK: ASP parity matches and generated stories meet quality checks over {len(python_combos)} combos."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a bedtime confusion-brickle story world.")
    parser.add_argument("--scene", choices=sorted(SCENES))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--hero-kind", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    matches = _matching_combos(args)
    if not matches:
        raise StoryError(invalid_reason(args.scene or "<scene>", args.problem or "<problem>", args.method or "<method>"))

    rng = random.Random(args.seed + index)
    scene_key, problem_key, method_key = rng.choice(matches)
    hero_kind = args.hero_kind or rng.choice(sorted(HERO_NAMES))
    return StoryParams(
        scene=scene_key,
        problem=problem_key,
        method=method_key,
        hero=args.hero or _pick_hero(hero_kind, rng),
        hero_kind=hero_kind,
        helper=args.helper or _pick_helper(rng),
        seed=args.seed + index,
    )


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story-grounded Q&A ==")
    for item in sample.story_qa:
        print(f"Q: {item.question}")
        print(f"A: {item.answer}")
    print("\n== (3) World-knowledge Q&A ==")
    for item in sample.world_qa:
        print(f"Q: {item.question}")
        print(f"A: {item.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp() -> None:
    for scene_key, problem_key, method_key in sorted(asp_valid_combos()):
        print(f"{scene_key}\t{problem_key}\t{method_key}")


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp()
            return 0

        samples: list[StorySample] = []
        if args.all:
            combos = _matching_combos(args)
            for index, combo in enumerate(combos, 1):
                samples.append(
                    generate(
                        StoryParams(
                            scene=combo[0],
                            problem=combo[1],
                            method=combo[2],
                            hero="Lena",
                            hero_kind="girl",
                            helper=HELPERS[0],
                            seed=args.seed + index,
                        )
                    )
                )
        else:
            count = max(1, args.n)
            for index in range(count):
                samples.append(generate(resolve_params(args, index)))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
            return 0

        for i, sample in enumerate(samples):
            label = None
            if args.all:
                p = sample.params
                label = f"### {p.scene} / {p.problem} / {p.method}"
            elif len(samples) > 1:
                label = f"### variant {i + 1}"
            emit(sample, args=args, label=label)
            if i < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
