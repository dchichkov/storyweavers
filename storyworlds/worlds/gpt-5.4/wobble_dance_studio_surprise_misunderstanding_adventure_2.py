#!/usr/bin/env python3
"""
wobble_dance_studio_surprise_misunderstanding_adventure_2.py
============================================================

A small storyworld about a child practicing an adventure dance inside a studio.
The fixed source tale behind the simulation is:

    A child comes to rehearsal at Lantern Leap Dance Studio, where the floor is
    laid out like a tiny quest. A friend and teacher quietly move one part of
    the ending to prepare a surprise. The child hears only part of the plan,
    builds a misunderstanding, and goes searching through ribbons, mirrors, or
    curtain caves. A wobble on the route becomes the turning point that slows
    the child down long enough to notice a clue. The truth is kind, the
    surprise opens, and the final pose proves that trust has returned.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
STORYWORLDS = Path(__file__).resolve().parents[2]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

STUDIO_NAME = "Lantern Leap Dance Studio"
SOURCE_TALE = (
    "A child rehearses an adventure routine in a dance studio that has been set "
    "up like a quest path. A helper and teacher hide one last detail for a "
    "surprise, but the child hears only a secret line and forms a "
    "misunderstanding. While searching for the truth, the child meets a wobble, "
    "finds a clue, and reaches the final spot with more trust than fear."
)


@dataclass(frozen=True)
class Route:
    key: str
    phrase: str
    room_detail: str
    wobble_spot: str
    search_span: str
    finish_spot: str
    reveal_spot: str
    adventure_name: str
    allowed_misunderstandings: tuple[str, ...]
    allowed_surprises: tuple[str, ...]
    wobble_boost: float


@dataclass(frozen=True)
class Misunderstanding:
    key: str
    prop_phrase: str
    overheard_line: str
    suspicion_template: str
    truth_template: str
    clue_text: str
    clue_phrase: str
    search_goal: str
    allowed_surprises: tuple[str, ...]
    worry_boost: float


@dataclass(frozen=True)
class Surprise:
    key: str
    phrase: str
    setup_template: str
    reveal_template: str
    ending_template: str
    afterglow: str
    wonder_boost: float


@dataclass
class StoryParams:
    route: str
    misunderstanding: str
    surprise: str
    hero: str
    gender: str
    friend: str
    teacher: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class Beat:
    stage: str
    location: str
    summary: str
    cause: str
    consequence: str


@dataclass
class World:
    params: StoryParams
    route: Route
    misunderstanding: Misunderstanding
    surprise: Surprise
    source_tale: str
    entities: dict[str, Entity] = field(default_factory=dict)
    beats: list[Beat] = field(default_factory=list)
    clue_found: str = ""
    misunderstanding_active: bool = False
    surprise_ready: bool = False
    resolved: bool = False
    story: str = ""
    setup_text: str = ""
    reveal_text: str = ""
    suspicion_text: str = ""
    truth_text: str = ""
    final_image: str = ""
    tension_phrase: str = ""

    def hero(self) -> Entity:
        return self.entities["hero"]

    def friend(self) -> Entity:
        return self.entities["friend"]

    def teacher(self) -> Entity:
        return self.entities["teacher"]

    def prop(self) -> Entity:
        return self.entities["prop"]

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  studio={STUDIO_NAME}")
        lines.append(f"  route={self.route.key}")
        lines.append(f"  misunderstanding={self.misunderstanding.key}")
        lines.append(f"  surprise={self.surprise.key}")
        lines.append(f"  misunderstanding_active={self.misunderstanding_active}")
        lines.append(f"  surprise_ready={self.surprise_ready}")
        lines.append(f"  resolved={self.resolved}")
        lines.append(f"  clue_found={self.clue_found or 'none'}")
        for slot, ent in self.entities.items():
            meters = ", ".join(f"{k}={v:.2f}" for k, v in sorted(ent.meters.items())) or "none"
            memes = ", ".join(f"{k}={v:.2f}" for k, v in sorted(ent.memes.items())) or "none"
            inventory = ", ".join(ent.inventory) if ent.inventory else "none"
            lines.append(f"  {slot}: {ent.name} ({ent.kind}) @ {ent.location}")
            lines.append(f"    meters=[{meters}]")
            lines.append(f"    memes=[{memes}]")
            lines.append(f"    inventory=[{inventory}]")
        if self.beats:
            lines.append("  beats:")
            for beat in self.beats:
                lines.append(
                    f"    - {beat.stage} @ {beat.location}: {beat.summary} "
                    f"(cause={beat.cause}; consequence={beat.consequence})"
                )
        return "\n".join(lines)


ROUTES: dict[str, Route] = {
    "map_lane": Route(
        key="map_lane",
        phrase="Map Lane routine",
        room_detail="gold arrows on the floor, a mirror wall shining like water, and a little barrel drum by the barre",
        wobble_spot="the narrow compass beam",
        search_span="the mirror wall, the piano corner, and the ribbon arch",
        finish_spot="the treasure star beside the front mirrors",
        reveal_spot="the ribbon arch",
        adventure_name="a treasure-map crossing",
        allowed_misunderstandings=("moved_star", "quiet_music"),
        allowed_surprises=("moon_banner", "family_lanterns"),
        wobble_boost=0.26,
    ),
    "cave_loop": Route(
        key="cave_loop",
        phrase="Cave Loop routine",
        room_detail="soft tunnel curtains, stepping circles like cave stones, and a prop trunk by the back wall",
        wobble_spot="the echo stepping stools",
        search_span="the curtain cave, the prop trunk, and the back mirror corner",
        finish_spot="the lantern circle near the back wall",
        reveal_spot="the curtain cave",
        adventure_name="a cave rescue trail",
        allowed_misunderstandings=("borrowed_flag", "moved_star"),
        allowed_surprises=("captain_badge", "moon_banner"),
        wobble_boost=0.31,
    ),
    "storm_bridge": Route(
        key="storm_bridge",
        phrase="Storm Bridge routine",
        room_detail="blue mats spread like waves, silver streamers fluttering from a fan, and a speaker shelf like a lookout deck",
        wobble_spot="the windy turn board",
        search_span="the speaker shelf, the streamer lane, and the soft blue curtain",
        finish_spot="the harbor mark by the speaker shelf",
        reveal_spot="the soft blue curtain",
        adventure_name="a storm-bridge expedition",
        allowed_misunderstandings=("quiet_music", "borrowed_flag"),
        allowed_surprises=("family_lanterns", "captain_badge"),
        wobble_boost=0.29,
    ),
}

MISUNDERSTANDINGS: dict[str, Misunderstanding] = {
    "moved_star": Misunderstanding(
        key="moved_star",
        prop_phrase="the treasure star",
        overheard_line="Move the star before she comes back.",
        suspicion_template="{hero} thought {friend} and {teacher} were taking away the best ending spot and giving the finish to someone else.",
        truth_template="{friend} had only shifted the treasure star so there would be room for the surprise ending behind it.",
        clue_text="A strip of gold tape curled out from under the prop trunk.",
        clue_phrase="a strip of gold tape curling out from under the prop trunk",
        search_goal="the back prop corner",
        allowed_surprises=("moon_banner", "captain_badge"),
        worry_boost=0.34,
    ),
    "quiet_music": Misunderstanding(
        key="quiet_music",
        prop_phrase="the music remote",
        overheard_line="Keep the song low until he reaches the curtain.",
        suspicion_template="{hero} thought the last brave part of the routine was being saved for somebody else, and that the music would stop before the finish.",
        truth_template="{teacher} had lowered the music only so hidden guests could get into place without spoiling the surprise.",
        clue_text="Fresh dance-shoe marks pointed toward the curtain.",
        clue_phrase="fresh dance-shoe marks pointing toward the curtain",
        search_goal="the curtain lane",
        allowed_surprises=("family_lanterns",),
        worry_boost=0.30,
    ),
    "borrowed_flag": Misunderstanding(
        key="borrowed_flag",
        prop_phrase="the red trail flag",
        overheard_line="Hide the flag until the last count.",
        suspicion_template="{hero} thought {friend} had borrowed the red trail flag so {hero} would have to finish the adventure empty-handed.",
        truth_template="{friend} had hidden the red trail flag only because it was part of the final surprise and needed to appear at the perfect moment.",
        clue_text="A red ribbon thread was caught on the curtain ring.",
        clue_phrase="a red ribbon thread caught on the curtain ring",
        search_goal="the curtain ring by the wall",
        allowed_surprises=("captain_badge", "family_lanterns"),
        worry_boost=0.32,
    ),
}

SURPRISES: dict[str, Surprise] = {
    "moon_banner": Surprise(
        key="moon_banner",
        phrase="a moon banner surprise",
        setup_template="a silver moon banner with {hero}'s name painted across it",
        reveal_template="They had hung a moon banner so {hero} could land the final pose like the explorer of the whole room.",
        ending_template="{hero} reached the finish and lifted both arms under the silver moon banner.",
        afterglow="The studio no longer felt secret and sharp. It felt wide, bright, and safe again.",
        wonder_boost=0.41,
    ),
    "family_lanterns": Surprise(
        key="family_lanterns",
        phrase="a lantern-family surprise",
        setup_template="tiny paper lanterns and a row of smiling family faces tucked behind the curtain",
        reveal_template="They had invited family to watch while the lanterns glowed, so {hero} could feel cheered all the way to the last pose.",
        ending_template="{hero} crossed the last step while warm lantern light blinked across the mirrors.",
        afterglow="Each lantern turned the dance studio into a little harbor where brave tries could come home.",
        wonder_boost=0.39,
    ),
    "captain_badge": Surprise(
        key="captain_badge",
        phrase="a Trail Captain badge surprise",
        setup_template="a velvet stand with a tiny Trail Captain badge beside the ending mark",
        reveal_template="They had prepared a Trail Captain badge because {hero} kept trying even after hard wobbles and messy practices.",
        ending_template="{hero} landed on the final mark while the Trail Captain badge gleamed beside one dancing shoe.",
        afterglow="The badge was tiny, but it made every careful practice step feel important.",
        wonder_boost=0.43,
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Ava", "Mina", "Lila", "Nora", "Suri"),
    "boy": ("Leo", "Milo", "Eli", "Rory", "Tomas"),
}

FRIEND_NAMES: tuple[str, ...] = ("June", "Pip", "Mika", "Nell", "Theo", "Sana")
TEACHER_NAMES: tuple[str, ...] = ("Ms. Rill", "Coach Ember", "Mr. Vale")


def _pronouns(gender: str) -> tuple[str, str]:
    if gender == "boy":
        return "he", "his"
    return "she", "her"


def valid_combos() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for route in ROUTES.values():
        for misunderstanding in MISUNDERSTANDINGS.values():
            if misunderstanding.key not in route.allowed_misunderstandings:
                continue
            for surprise in SURPRISES.values():
                if surprise.key not in route.allowed_surprises:
                    continue
                if surprise.key not in misunderstanding.allowed_surprises:
                    continue
                rows.append((route.key, misunderstanding.key, surprise.key))
    return sorted(rows)


def describe_rejection(route_key: str, misunderstanding_key: str, surprise_key: str) -> str:
    if route_key not in ROUTES:
        raise StoryError(f"Unknown route '{route_key}'. Choose from {', '.join(sorted(ROUTES))}.")
    if misunderstanding_key not in MISUNDERSTANDINGS:
        raise StoryError(
            f"Unknown misunderstanding '{misunderstanding_key}'. "
            f"Choose from {', '.join(sorted(MISUNDERSTANDINGS))}."
        )
    if surprise_key not in SURPRISES:
        raise StoryError(f"Unknown surprise '{surprise_key}'. Choose from {', '.join(sorted(SURPRISES))}.")

    route = ROUTES[route_key]
    misunderstanding = MISUNDERSTANDINGS[misunderstanding_key]
    surprise = SURPRISES[surprise_key]

    if misunderstanding.key not in route.allowed_misunderstandings:
        return (
            f"{route.phrase} does not fit the {misunderstanding.key} misunderstanding. "
            f"That route supports {', '.join(route.allowed_misunderstandings)}."
        )
    if surprise.key not in route.allowed_surprises:
        return (
            f"{route.phrase} cannot stage {surprise.phrase}. "
            f"That route supports {', '.join(route.allowed_surprises)}."
        )
    if surprise.key not in misunderstanding.allowed_surprises:
        return (
            f"The {misunderstanding.key} misunderstanding does not lead cleanly to {surprise.phrase}. "
            f"It supports {', '.join(misunderstanding.allowed_surprises)}."
        )
    return "That dance-studio adventure combination is not reasonable."


def build_world(params: StoryParams) -> World:
    if (params.route, params.misunderstanding, params.surprise) not in valid_combos():
        raise StoryError(describe_rejection(params.route, params.misunderstanding, params.surprise))
    if params.friend == params.hero:
        raise StoryError("Friend and hero must be different people in this storyworld.")

    route = ROUTES[params.route]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    surprise = SURPRISES[params.surprise]
    world = World(
        params=params,
        route=route,
        misunderstanding=misunderstanding,
        surprise=surprise,
        source_tale=SOURCE_TALE,
    )

    hero = Entity(
        name=params.hero,
        kind="child dancer",
        location="cubby row",
        meters={"balance": 0.60, "breath": 0.71, "wobble": 0.18},
        memes={"trust": 0.73, "worry": 0.19, "wonder": 0.52, "courage": 0.63, "surprise": 0.00},
        inventory=[misunderstanding.prop_phrase],
        notes={"goal": route.finish_spot},
    )
    friend = Entity(
        name=params.friend,
        kind="helper friend",
        location="prop shelf",
        meters={"quiet_steps": 0.68, "timing": 0.64},
        memes={"care": 0.84, "secrecy": 0.40, "patience": 0.58},
        inventory=[],
    )
    teacher = Entity(
        name=params.teacher,
        kind="dance teacher",
        location="music stand",
        meters={"timing": 0.92, "voice": 0.70},
        memes={"guidance": 0.95, "care": 0.91, "calm": 0.76},
        inventory=[],
    )
    prop = Entity(
        name=misunderstanding.prop_phrase,
        kind="dance prop",
        location="hero cubby",
        meters={"shine": 0.45, "steadiness": 0.55},
        memes={"importance": 0.71},
        inventory=[],
    )

    world.entities = {"hero": hero, "friend": friend, "teacher": teacher, "prop": prop}
    return world


def _record(world: World, stage: str, location: str, summary: str, cause: str, consequence: str) -> None:
    world.beats.append(Beat(stage=stage, location=location, summary=summary, cause=cause, consequence=consequence))


def _simulate(world: World) -> None:
    hero = world.hero()
    friend = world.friend()
    teacher = world.teacher()
    prop = world.prop()

    world.setup_text = world.surprise.setup_template.format(hero=hero.name)
    world.reveal_text = world.surprise.reveal_template.format(hero=hero.name)
    world.suspicion_text = world.misunderstanding.suspicion_template.format(
        hero=hero.name, friend=friend.name, teacher=teacher.name
    )
    world.truth_text = world.misunderstanding.truth_template.format(
        hero=hero.name, friend=friend.name, teacher=teacher.name
    )

    hero.location = world.route.phrase
    _record(
        world,
        "beginning",
        world.route.phrase,
        f"{hero.name} arrived to rehearse the {world.route.phrase} at {STUDIO_NAME}.",
        "Practice had just begun.",
        f"{hero.name} set out to reach {world.route.finish_spot}.",
    )

    hero.inventory.clear()
    friend.inventory = [prop.name]
    prop.location = world.misunderstanding.search_goal
    friend.location = world.misunderstanding.search_goal
    world.misunderstanding_active = True
    hero.memes["worry"] += world.misunderstanding.worry_boost
    hero.memes["trust"] -= 0.25
    hero.memes["wonder"] -= 0.08
    friend.memes["secrecy"] += 0.20
    if hero.memes["worry"] >= 0.45:
        world.tension_phrase = "tight and stormy"
    elif hero.memes["trust"] <= 0.55:
        world.tension_phrase = "small and shaky"
    else:
        world.tension_phrase = "careful but brave"
    _record(
        world,
        "misunderstanding",
        world.misunderstanding.search_goal,
        f"{hero.name} heard, '{world.misunderstanding.overheard_line}' and saw {friend.name} carry off {prop.name}.",
        "The teacher and friend were quietly setting up a surprise ending.",
        world.suspicion_text,
    )

    hero.location = world.route.search_span
    hero.meters["wobble"] += world.route.wobble_boost
    hero.meters["balance"] -= 0.09
    hero.meters["breath"] -= 0.07
    hero.memes["courage"] += 0.14
    world.clue_found = world.misunderstanding.clue_text
    _record(
        world,
        "search",
        world.route.search_span,
        f"{hero.name} searched through {world.route.search_span} after spotting {world.misunderstanding.clue_phrase}.",
        "The misunderstanding made the room feel like a real adventure.",
        f"A wobble at {world.route.wobble_spot} slowed {hero.name} down just enough to notice the clue clearly.",
    )

    hero.location = world.route.reveal_spot
    friend.location = world.route.reveal_spot
    teacher.location = world.route.reveal_spot
    hero.inventory = [prop.name]
    friend.inventory.clear()
    prop.location = hero.name
    world.surprise_ready = True
    world.resolved = True
    hero.memes["trust"] += 0.43
    hero.memes["wonder"] += world.surprise.wonder_boost
    hero.memes["surprise"] += 0.80
    hero.memes["worry"] = max(0.05, hero.memes["worry"] - 0.42)
    hero.meters["balance"] += 0.18
    hero.meters["wobble"] = max(0.16, hero.meters["wobble"] - 0.12)
    teacher.memes["calm"] += 0.05
    _record(
        world,
        "reveal",
        world.route.reveal_spot,
        f"{hero.name} found {friend.name} and {teacher.name} arranging {world.setup_text}.",
        world.truth_text,
        world.reveal_text,
    )

    hero.location = world.route.finish_spot
    friend.location = world.route.finish_spot
    teacher.location = world.route.finish_spot
    hero.meters["breath"] += 0.06
    hero.memes["courage"] += 0.17
    hero.memes["wonder"] += 0.07
    world.final_image = world.surprise.ending_template.format(hero=hero.name)
    _record(
        world,
        "ending",
        world.route.finish_spot,
        f"{hero.name} danced across {world.route.adventure_name} and reached {world.route.finish_spot}.",
        "The truth brought trust back into the room.",
        world.final_image,
    )


def _wobble_phrase(world: World) -> str:
    wobble = world.hero().meters["wobble"]
    if wobble >= 0.45:
        return "a strong wobble"
    if wobble >= 0.30:
        return "a careful wobble"
    return "a tiny wobble"


def render_story(world: World) -> str:
    hero = world.hero()
    friend = world.friend()
    teacher = world.teacher()
    prop = world.prop()
    subj, poss = _pronouns(world.params.gender)

    beginning = (
        f"At {STUDIO_NAME}, {hero.name} came in ready for the {world.route.phrase}. "
        f"The dance studio held {world.route.room_detail}, and the whole room looked like {world.route.adventure_name}. "
        f"{hero.name} loved the part with {world.route.wobble_spot}, because even a wobble could become part of the dance when {subj} kept breathing."
    )

    middle = (
        f"Then a misunderstanding began. {hero.name} heard {teacher.name} whisper, "
        f"\"{world.misunderstanding.overheard_line}\" and saw {friend.name} carrying {prop.name}. "
        f"{world.suspicion_text} {poss.capitalize()} heart felt {world.tension_phrase}, but {subj} still searched through "
        f"{world.route.search_span}. When {hero.name} felt {_wobble_phrase(world)} at {world.route.wobble_spot}, {subj} slowed down and finally noticed {world.misunderstanding.clue_phrase}."
    )

    ending = (
        f"Behind {world.route.reveal_spot}, {hero.name} found {friend.name} and {teacher.name} arranging {world.setup_text}. "
        f"{world.truth_text} It was a surprise for {hero.name}. {world.reveal_text} "
        f"When the music swelled again, {hero.name} crossed the last steps and reached {world.route.finish_spot}. "
        f"{world.final_image} {world.surprise.afterglow}"
    )

    return "\n\n".join([beginning, middle, ending])


def build_prompts(world: World) -> list[str]:
    hero = world.hero().name
    return [
        "Write a child-facing Adventure story that includes the word 'wobble.'",
        f"Set the story in a dance studio and make {hero} the child at the center of the action.",
        f"Build the plot around the {world.misunderstanding.key} misunderstanding and reveal {world.surprise.phrase} at the end.",
    ]


def build_story_qa(world: World) -> list[QAItem]:
    hero = world.hero().name
    friend = world.friend().name
    teacher = world.teacher().name
    return [
        QAItem(
            question=f"Why did {hero} think something was wrong in the studio?",
            answer=(
                f"{hero} heard only part of the plan and saw {friend} carrying {world.prop().name}, so the scene looked sneaky instead of kind. "
                f"That half-heard moment built the misunderstanding before anyone could explain the surprise."
            ),
        ),
        QAItem(
            question=f"What clue helped {hero} keep searching?",
            answer=(
                f"{world.clue_found} "
                f"The clue pointed toward {world.misunderstanding.search_goal}, which was close to where the secret setup was happening."
            ),
        ),
        QAItem(
            question="How did the wobble change the adventure?",
            answer=(
                f"The wobble at {world.route.wobble_spot} forced {hero} to slow down and breathe instead of rushing in a panic. "
                f"Because of that pause, {hero} noticed the clue and moved closer to the truth."
            ),
        ),
        QAItem(
            question=f"What was {friend} really doing with {world.prop().name}?",
            answer=(
                f"{world.truth_text} "
                f"The prop was part of the ending plan, so moving it was an act of care rather than a trick."
            ),
        ),
        QAItem(
            question=f"What surprise was waiting at {world.route.reveal_spot}?",
            answer=(
                f"{friend} and {teacher} were arranging {world.setup_text}. "
                f"That setup turned the ordinary rehearsal into a reward shaped for {hero}'s adventure dance."
            ),
        ),
        QAItem(
            question=f"What changed for {hero} by the final pose?",
            answer=(
                f"{hero} ended the story feeling more trusting, more surprised, and more brave than before. "
                f"The final image shows that the scary misunderstanding gave way to a strong finish inside the same room."
            ),
        ),
    ]


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a dance studio feel like an adventure to a child?",
            answer=(
                "A dance studio already has routes, marks, props, and hidden corners that can feel like parts of a quest. "
                "When adults frame practice as a trail, the child can move through the room as if each step solves a tiny challenge."
            ),
        ),
        QAItem(
            question="Why do misunderstandings happen easily during rehearsals?",
            answer=(
                "Rehearsals are busy, so people move props, whisper counts, and cross the room quickly. "
                "If a child hears only one line of a larger plan, the missing pieces can turn kindness into a wrong guess."
            ),
        ),
        QAItem(
            question="What can a wobble teach a dancer during practice?",
            answer=(
                "A wobble teaches a dancer to pause, breathe, and place the next step with care. "
                "That small reset can protect balance and also make the dancer notice what is happening nearby."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _simulate(world)
    world.story = render_story(world)
    return StorySample(
        params=params,
        story=world.story,
        prompts=build_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["--- prompts ---"]
    lines.extend(f"- {item}" for item in sample.prompts)
    lines.append("")
    lines.append("--- story qa ---")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
        lines.append("")
    lines.append("--- world qa ---")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dance studio adventure with wobble, surprise, and misunderstanding.")
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    parser.add_argument("--surprise", choices=sorted(SURPRISES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--friend")
    parser.add_argument("--teacher")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.misunderstanding is None or combo[1] == args.misunderstanding)
        and (args.surprise is None or combo[2] == args.surprise)
    ]
    if not combos:
        raise StoryError(
            describe_rejection(
                args.route or "map_lane",
                args.misunderstanding or "moved_star",
                args.surprise or "moon_banner",
            )
        )

    route, misunderstanding, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    teacher = args.teacher or rng.choice(TEACHER_NAMES)
    if friend == hero:
        raise StoryError("Friend and hero must be different people in this storyworld.")
    return StoryParams(
        route=route,
        misunderstanding=misunderstanding,
        surprise=surprise,
        hero=hero,
        gender=gender,
        friend=friend,
        teacher=teacher,
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
combo(R,M,S) :-
  route(R), misunderstanding(M), surprise(S),
  route_allows_misunderstanding(R,M),
  route_allows_surprise(R,S),
  misunderstanding_allows_surprise(M,S).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for route in ROUTES.values():
        rows.append(asp.fact("route", route.key))
        for misunderstanding in route.allowed_misunderstandings:
            rows.append(asp.fact("route_allows_misunderstanding", route.key, misunderstanding))
        for surprise in route.allowed_surprises:
            rows.append(asp.fact("route_allows_surprise", route.key, surprise))
    for misunderstanding in MISUNDERSTANDINGS.values():
        rows.append(asp.fact("misunderstanding", misunderstanding.key))
        for surprise in misunderstanding.allowed_surprises:
            rows.append(asp.fact("misunderstanding_allows_surprise", misunderstanding.key, surprise))
    for surprise in SURPRISES.values():
        rows.append(asp.fact("surprise", surprise.key))
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
            route=combo[0],
            misunderstanding=combo[1],
            surprise=combo[2],
            hero="Ava",
            gender="girl",
            friend="June",
            teacher="Ms. Rill",
            seed=700 + i,
        )
        sample = generate(params)
        text = sample.story.lower()
        if "wobble" not in text:
            problems.append(f"{combo}: story is missing the seed word 'wobble'")
        if "dance studio" not in text:
            problems.append(f"{combo}: story does not name the dance studio setting")
        if "surprise" not in text:
            problems.append(f"{combo}: story never names the surprise")
        if "misunderstanding" not in text:
            problems.append(f"{combo}: story never names the misunderstanding")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story does not have clear beginning, middle, and ending paragraphs")
        if not sample.world or not sample.world.resolved:
            problems.append(f"{combo}: world does not reach a resolved state")
        if len(sample.story_qa) < 6:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(item.answer.count(".") < 2 for item in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if "{" in sample.story or "}" in sample.story:
            problems.append(f"{combo}: unresolved template text leaked into the story")
    return problems


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    status = 0
    if python_set == asp_set:
        print(f"OK: ASP gate matches Python valid_combos() ({len(python_set)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if python_set - asp_set:
            print(f"  only python: {sorted(python_set - asp_set)}")
        if asp_set - python_set:
            print(f"  only asp: {sorted(asp_set - python_set)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for problem in problems:
            print(f"  {problem}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, QA, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed), index=attempts)
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique dance-studio stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else 41
    rows: list[StorySample] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            route=combo[0],
            misunderstanding=combo[1],
            surprise=combo[2],
            hero=args.hero or "Ava",
            gender=args.gender or "girl",
            friend=args.friend or "June",
            teacher=args.teacher or "Ms. Rill",
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
        samples = _sample_all(args) if args.all else _sample_n(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### route={p.route} misunderstanding={p.misunderstanding} surprise={p.surprise}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
