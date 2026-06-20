#!/usr/bin/env python3
"""
confuse_brickle_repetition_dialogue_bedtime_story.py
====================================================

A small StoryWorld for the seed:

    words: confuse, brickle
    features: Repetition, Dialogue
    style: Bedtime Story

Internal source tale:
    At bedtime, a child makes a tiny brickle object in a cozy bedroom corner.
    A repeated night clue makes the object seem wrong and starts to confuse the
    child. A calm helper answers with soft dialogue, matches the clue to the
    right bedtime routine, and repeats a gentle line three times. The world
    settles, the true cause becomes clear, and the ending image shows the room
    quiet enough for sleep.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class BedroomCorner:
    key: str
    phrase: str
    setting_phrase: str
    landmark: str
    support_keys: tuple[str, ...]
    hush_level: float
    end_view: str


@dataclass(frozen=True)
class BrickleBuild:
    key: str
    phrase: str
    need_key: str
    material: str
    cause: str
    repair: str
    proof_image: str
    lesson: str


@dataclass(frozen=True)
class BedtimeRoutine:
    key: str
    phrase: str
    helper_line: str
    refrain: str
    hero_action: str
    result_line: str
    tool: str
    solves: tuple[str, ...]


@dataclass
class StoryParams:
    corner: str
    build: str
    routine: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    corner: BedroomCorner
    build: BrickleBuild
    routine: BedtimeRoutine
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    opening_text: str = ""
    tension_text: str = ""
    turn_text: str = ""
    ending_text: str = ""
    story: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"corner={self.corner.key} build={self.build.key} routine={self.routine.key} "
            f"hero={self.params.hero} helper={helper_name(self.params.helper)}"
        )
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {name:<10} ({ent.kind:<12}) {detail}".rstrip())
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


CORNERS: dict[str, BedroomCorner] = {
    "window_nook": BedroomCorner(
        key="window_nook",
        phrase="the window nook beside the bed",
        setting_phrase="in the window nook beside the bed",
        landmark="a moon curtain and a row of cotton-cloud pillows",
        support_keys=("tap", "shadow"),
        hush_level=0.6,
        end_view="the moon curtain hung still above the cotton-cloud pillows",
    ),
    "lamp_table": BedroomCorner(
        key="lamp_table",
        phrase="the small lamp table near the blanket basket",
        setting_phrase="at the small lamp table near the blanket basket",
        landmark="a pearly lamp and a folded story quilt",
        support_keys=("shadow", "rustle"),
        hush_level=0.7,
        end_view="the pearly lamp glowed over a smooth folded quilt",
    ),
    "pillow_cove": BedroomCorner(
        key="pillow_cove",
        phrase="the pillow cove at the head of the bed",
        setting_phrase="in the pillow cove at the head of the bed",
        landmark="a crescent pillow and a tucked-in storybook",
        support_keys=("tap", "rustle"),
        hush_level=0.8,
        end_view="the crescent pillow held the little build steady by the headboard",
    ),
    "quilt_chair": BedroomCorner(
        key="quilt_chair",
        phrase="the quilt chair by the sleepy shelf",
        setting_phrase="by the quilt chair near the sleepy shelf",
        landmark="a rocking chair with a draped blue quilt",
        support_keys=("rustle", "shadow"),
        hush_level=0.75,
        end_view="the blue quilt lay flat on the chair and the sleepy shelf looked clear",
    ),
}

BUILDS: dict[str, BrickleBuild] = {
    "star_stack": BrickleBuild(
        key="star_stack",
        phrase="a brickle stack of wooden stars",
        need_key="tap",
        material="wood",
        cause="a loose moon bead on the curtain cord kept tapping the sill, and each tiny tap made the little stars tremble",
        repair="counted the taps, tied the bead still, and nudged the bottom star square again",
        proof_image="The wooden stars stood in one sleepy line beside the pillow.",
        lesson="Small repeated sounds feel less strange when someone listens for their source.",
    ),
    "paper_moon": BrickleBuild(
        key="paper_moon",
        phrase="a brickle paper moon arch",
        need_key="shadow",
        material="paper",
        cause="the night-light threw a curtain shadow over the arch, so its curve looked broken even though the paper was whole",
        repair="lifted the light, moved the curtain edge, and watched the moon shape turn round again",
        proof_image="The paper moon arch lay round and pale in the gentle lamp glow.",
        lesson="A shadow can confuse tired eyes, but light can explain what darkness bent.",
    ),
    "shell_bridge": BrickleBuild(
        key="shell_bridge",
        phrase="a brickle shell bridge",
        need_key="rustle",
        material="shell",
        cause="a half-open storybook kept rustling under the blanket breeze, brushing the shell bridge until one side leaned",
        repair="closed the storybook, tucked the blanket, and reset the shells with two careful fingers",
        proof_image="The shell bridge rested quiet over the folded blanket, with no lean left at all.",
        lesson="Gentle bedtime fixes start by quieting the thing that keeps nudging the world.",
    ),
}

ROUTINES: dict[str, BedtimeRoutine] = {
    "count_the_taps": BedtimeRoutine(
        key="count_the_taps",
        phrase="count the taps and steady the bead",
        helper_line="Let us count before we guess.",
        refrain="Tap, wait, listen.",
        hero_action="counted each tiny tap on calm fingers and reached for the curtain bead only after the third sound",
        result_line="When the bead stopped tapping, the little stars stopped trembling too.",
        tool="calm fingers",
        solves=("tap",),
    ),
    "look_for_shadow": BedtimeRoutine(
        key="look_for_shadow",
        phrase="lift the light and look for the shadow",
        helper_line="Let us move the light before we worry.",
        refrain="Glow high, shadow shy.",
        hero_action="raised the pearly lamp while the curtain edge slid aside and the dark shape lost its trick",
        result_line="When the shadow slipped away, the paper moon looked round again.",
        tool="the night-light",
        solves=("shadow",),
    ),
    "tuck_the_rustle": BedtimeRoutine(
        key="tuck_the_rustle",
        phrase="tuck the blanket and hush the rustle",
        helper_line="Let us quiet the rustle and then look again.",
        refrain="Hush, tuck, settle.",
        hero_action="closed the fluttering storybook, tucked the quilt under it, and touched the shells only when the air was still",
        result_line="When the rustle ended, the shell bridge stopped leaning and held its shape.",
        tool="a tucked quilt",
        solves=("rustle",),
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Ada", "Mina", "Lucy"),
    "boy": ("Eli", "Noah", "Sam"),
}

HELPERS: dict[str, str] = {
    "mama": "Mama",
    "papa": "Papa",
    "nana_rose": "Nana Rose",
    "aunt_jo": "Aunt Jo",
}


def helper_name(key: str) -> str:
    return HELPERS[key]


def valid_combo(corner: str, build: str, routine: str) -> bool:
    if corner not in CORNERS or build not in BUILDS or routine not in ROUTINES:
        return False
    need = BUILDS[build].need_key
    return need in CORNERS[corner].support_keys and need in ROUTINES[routine].solves


def explain_rejection(corner: str, build: str, routine: str) -> str:
    if corner not in CORNERS:
        return f"No story: unknown bedroom corner {corner!r}."
    if build not in BUILDS:
        return f"No story: unknown brickle bedtime build {build!r}."
    if routine not in ROUTINES:
        return f"No story: unknown bedtime routine {routine!r}."
    need = BUILDS[build].need_key
    if need not in CORNERS[corner].support_keys:
        return (
            f"No story: {CORNERS[corner].phrase} cannot ground {BUILDS[build].phrase}; "
            f"that build needs a {need} clue."
        )
    if need not in ROUTINES[routine].solves:
        return (
            f"No story: {ROUTINES[routine].phrase} does not fit {BUILDS[build].phrase}; "
            f"try a routine that can answer a {need} clue."
        )
    return "No story: the bedtime choices do not form a reasonable tale."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for corner in sorted(CORNERS):
        for build in sorted(BUILDS):
            for routine in sorted(ROUTINES):
                if valid_combo(corner, build, routine):
                    combos.append((corner, build, routine))
    return combos


def _pick_hero(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES[gender])


def build_world(params: StoryParams) -> World:
    corner = CORNERS[params.corner]
    build = BUILDS[params.build]
    routine = ROUTINES[params.routine]

    hero = Entity(name=params.hero, kind="child")
    helper = Entity(name=helper_name(params.helper), kind="helper")
    room = Entity(name="Room", kind="bedroom")
    bedtime_build = Entity(name=build.phrase, kind="fragile_build")

    world = World(
        params=params,
        corner=corner,
        build=build,
        routine=routine,
        entities={
            "Hero": hero,
            "Helper": helper,
            "Room": room,
            "Build": bedtime_build,
        },
    )

    hero.set_meter("sleepiness", 0.5)
    hero.set_meter("repeat_count", 0.0)
    hero.add_meme("wonder", 0.8)
    hero.add_meme("trust", 0.5)

    helper.add_meme("patience", 1.0)
    helper.add_meme("care", 1.0)

    room.set_meter("glow", 0.7)
    room.set_meter("noise", 0.2)
    room.add_meme("hush", corner.hush_level)
    room.set_tag("landmark", corner.landmark)

    bedtime_build.set_meter("wobble", 0.2)
    bedtime_build.set_meter("stability", 0.4)
    bedtime_build.add_meme("delicacy", 0.9)
    bedtime_build.set_tag("material", build.material)
    bedtime_build.set_tag("need", build.need_key)
    bedtime_build.set_tag("resolved", "no")

    return world


def _r_open_bedtime_scene(world: World) -> bool:
    hero = world.entities["Hero"]
    room = world.entities["Room"]
    bedtime_build = world.entities["Build"]

    hero.add_meme("calm", 0.3)
    room.add_meme("hush", 0.2)
    bedtime_build.add_meme("comfort", 0.5)

    world.opening_text = (
        f"At bedtime, {world.params.hero} sat {world.corner.setting_phrase} with {helper_name(world.params.helper)} "
        f"and finished {world.build.phrase}. Around them were {world.corner.landmark}, and the room felt soft enough to yawn in."
    )
    world.note(
        f"{world.params.hero} built {world.build.phrase} in {world.corner.phrase} while the room settled for sleep."
    )
    return True


def _r_repeat_the_confusing_clue(world: World) -> bool:
    hero = world.entities["Hero"]
    room = world.entities["Room"]
    bedtime_build = world.entities["Build"]

    hero.add_meme("confusion", 1.3)
    hero.add_meme("wonder", 0.2)
    hero.set_meter("repeat_count", 3.0)
    room.add_meme("hush", -0.2)
    room.set_meter("noise", 0.5)
    bedtime_build.add_meme("delicacy", 0.2)
    bedtime_build.set_meter("wobble", 0.8)
    bedtime_build.set_tag("cause", world.build.cause)

    if world.build.need_key == "tap":
        clue = "Tap, tap, tap came from the moon curtain."
        reaction = "\"Why is it shaking? Why is it shaking? Why is it shaking?\""
    elif world.build.need_key == "shadow":
        clue = "Across the wall, the same dark shape crossed the little arch three times."
        reaction = "\"Why does it bend? Why does it bend? Why does it bend?\""
    else:
        clue = "From the blanket basket came rustle, rustle, rustle, each brush leaning one side a little more."
        reaction = "\"Why does it lean? Why does it lean? Why does it lean?\""

    world.tension_text = (
        f"Then the room changed. {clue} The small change began to confuse {world.params.hero}, and {world.params.hero} whispered, {reaction}"
    )
    world.note(world.tension_text)
    return True


def _r_match_clue_to_routine(world: World) -> bool:
    hero = world.entities["Hero"]
    helper = world.entities["Helper"]
    room = world.entities["Room"]
    bedtime_build = world.entities["Build"]

    hero.add_meme("trust", 0.6)
    hero.add_meme("calm", 1.0)
    hero.add_meme("confusion", -0.9)
    hero.add_meme("confidence", 0.7)
    helper.add_meme("care", 0.2)
    room.set_meter("noise", 0.1)
    room.add_meme("hush", 0.5)
    bedtime_build.set_meter("stability", 1.0)
    bedtime_build.set_meter("wobble", 0.1)
    bedtime_build.set_tag("resolved", "almost")
    bedtime_build.set_tag("repair", world.build.repair)

    world.turn_text = (
        f"\"{world.routine.helper_line}\" {helper.name} said. "
        f"\"Little bedtime clues can confuse sleepy thoughts, but they can also explain themselves.\" "
        f"Together they said, \"{world.routine.refrain}\" once, then again, then once more. "
        f"After that, {world.params.hero} {world.routine.hero_action}. "
        f"That was the turn: {world.build.cause}, so {world.params.hero} {world.build.repair}. "
        f"{world.routine.result_line}"
    )
    world.note(world.turn_text)
    return True


def _r_close_with_sleep(world: World) -> bool:
    hero = world.entities["Hero"]
    helper = world.entities["Helper"]
    room = world.entities["Room"]
    bedtime_build = world.entities["Build"]

    hero.set_meter("sleepiness", 0.95)
    hero.add_meme("calm", 0.9)
    hero.add_meme("joy", 0.8)
    helper.add_meme("relief", 0.7)
    room.set_tag("settled", "yes")
    bedtime_build.set_tag("resolved", "yes")
    bedtime_build.set_tag("proof_image", world.build.proof_image)

    world.ending_text = (
        f"\"There now,\" {helper.name} said, \"the room makes sense again.\" "
        f"{world.build.proof_image} Nearby, {world.corner.end_view}. "
        f"{world.params.hero} slid under the blanket, and the bedroom no longer felt puzzling. {world.build.lesson}"
    )
    world.note(world.ending_text)
    return True


RULES: tuple[tuple[str, Callable[[World], bool]], ...] = (
    ("open_bedtime_scene", _r_open_bedtime_scene),
    ("repeat_the_confusing_clue", _r_repeat_the_confusing_clue),
    ("match_clue_to_routine", _r_match_clue_to_routine),
    ("close_with_sleep", _r_close_with_sleep),
)


def run_world(world: World) -> World:
    for name, rule in RULES:
        fired = rule(world)
        if fired:
            world.fired_rules.append(name)
    return world


def render_story(world: World) -> str:
    middle = (
        f"{world.tension_text} {helper_name(world.params.helper)} leaned close instead of hurrying the fix, "
        f"because bedtime was supposed to get softer, not louder."
    )
    ending = f"{world.turn_text} {world.ending_text}"
    return "\n\n".join((world.opening_text, middle, ending))


def prompts_for(world: World) -> list[str]:
    return [
        f"Write a bedtime story that includes the words confuse and brickle in a child-facing way.",
        f"Use repetition and dialogue while {world.params.hero} tries to understand {world.build.phrase} in {world.corner.phrase}.",
        f"Let {helper_name(world.params.helper)} guide the turn with the repeated line \"{world.routine.refrain}\" and end with {world.build.proof_image}",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What was the child making at bedtime?",
            answer=(
                f"{world.params.hero} was making {world.build.phrase} in {world.corner.phrase}. "
                f"That mattered because the build was delicate enough for a small repeated clue to change how it looked."
            ),
        ),
        QAItem(
            question="What started to confuse the child?",
            answer=(
                f"The confusing part was this: {world.build.cause}. "
                f"Because the clue repeated three times, {world.params.hero} first thought the little build itself might be going wrong."
            ),
        ),
        QAItem(
            question="Why did the helper choose that routine?",
            answer=(
                f"{helper_name(world.params.helper)} chose {world.routine.phrase} because the problem needed a {world.build.need_key} answer. "
                f"The routine matched the clue type instead of guessing wildly, which is why the room settled instead of growing busier."
            ),
        ),
        QAItem(
            question="What line was repeated in the turning point?",
            answer=(
                f"The repeated line was \"{world.routine.refrain}\" and they said it three times together. "
                f"That repetition slowed the scene down and helped {world.params.hero} move from confusion toward calm attention."
            ),
        ),
        QAItem(
            question="What final image proves the room changed by the end?",
            answer=(
                f"The proof image is this: {world.build.proof_image} "
                f"It proves change because the delicate object is steady, the true cause has been handled, and bedtime can continue peacefully."
            ),
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can repetition help in a bedtime problem instead of making it scarier?",
            answer=(
                "A repeated clue gives the child something stable to notice, count, or compare. "
                "Once a pattern becomes clear, a helper can match a calm action to it and turn the unknown into an explanation."
            ),
        ),
        QAItem(
            question="Why should a routine match the clue type in a delicate room scene?",
            answer=(
                "Different clues call for different actions, such as listening for taps, moving light for shadows, or stopping a rustle. "
                "Matching the routine to the clue keeps the story physical and prevents a fix that would ignore the real cause."
            ),
        ),
        QAItem(
            question="Why do fragile bedtime builds need a calmer room than sturdy toys do?",
            answer=(
                "Fragile builds react to small movements, sounds, and breezes that sturdier toys can ignore. "
                "That is why the world tracks both emotional calm and physical steadiness before the child can feel ready to sleep."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.corner, params.build, params.routine):
        raise StoryError(explain_rejection(params.corner, params.build, params.routine))
    world = run_world(build_world(params))
    story = render_story(world)
    world.story = story
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Prompts ==", *[f"{i}. {item}" for i, item in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a brickle bedtime confusion storyworld.")
    parser.add_argument("--corner", choices=sorted(CORNERS))
    parser.add_argument("--build", choices=sorted(BUILDS))
    parser.add_argument("--routine", choices=sorted(ROUTINES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.corner is None or combo[0] == args.corner)
        and (args.build is None or combo[1] == args.build)
        and (args.routine is None or combo[2] == args.routine)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.corner or "window_nook",
                args.build or "star_stack",
                args.routine or "count_the_taps",
            )
        )

    corner, build, routine = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(rng, gender)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        corner=corner,
        build=build,
        routine=routine,
        hero=hero,
        gender=gender,
        helper=helper,
    )


ASP_RULES = r"""
combo(C,B,R) :-
  corner(C), build(B), routine(R),
  corner_support(C,N), build_need(B,N), routine_solves(R,N).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for corner in CORNERS.values():
        rows.append(asp.fact("corner", corner.key))
        for support in corner.support_keys:
            rows.append(asp.fact("corner_support", corner.key, support))
    for build in BUILDS.values():
        rows.append(asp.fact("build", build.key))
        rows.append(asp.fact("build_need", build.key, build.need_key))
    for routine in ROUTINES.values():
        rows.append(asp.fact("routine", routine.key))
        for support in routine.solves:
            rows.append(asp.fact("routine_solves", routine.key, support))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            corner=combo[0],
            build=combo[1],
            routine=combo[2],
            hero="Ada",
            gender="girl",
            helper="mama",
            seed=2400 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        world = sample.world
        if "brickle" not in story:
            problems.append(f"{combo}: story is missing the seed word 'brickle'")
        if "confuse" not in story:
            problems.append(f"{combo}: story is missing the seed word 'confuse'")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if sample.story.count("\"") < 6:
            problems.append(f"{combo}: story is missing enough visible dialogue")
        if sample.story.lower().count(ROUTINES[combo[2]].refrain.lower()) < 1:
            problems.append(f"{combo}: repeated bedtime line is missing")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story-grounded QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world-knowledge QA set is too small")
        if any(item.answer.count(".") < 2 for item in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if world is None:
            problems.append(f"{combo}: sample is missing its world model")
            continue
        if world.entities["Hero"].meters.get("repeat_count") != 3.0:
            problems.append(f"{combo}: repetition count was not recorded in the hero state")
        if world.entities["Build"].meters.get("stability") != 1.0:
            problems.append(f"{combo}: build never reached a stable ending state")
        if world.entities["Build"].tags.get("resolved") != "yes":
            problems.append(f"{combo}: build was never marked resolved")
        if world.entities["Room"].tags.get("settled") != "yes":
            problems.append(f"{combo}: room did not reach a settled ending state")
    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, dialogue, repetition, QA, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique bedtime stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            corner=combo[0],
            build=combo[1],
            routine=combo[2],
            hero="Ada",
            gender="girl",
            helper="mama",
            seed=base_seed + i,
        )
        rows.append(generate(params))
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            samples = _sample_n(args)
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
