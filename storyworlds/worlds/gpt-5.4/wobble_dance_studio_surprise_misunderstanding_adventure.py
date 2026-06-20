#!/usr/bin/env python3
"""
wobble_dance_studio_surprise_misunderstanding_adventure.py
==========================================================

A small dance-studio adventure storyworld built from a fixed source tale:

    A child rehearses an adventure dance trail in a dance studio. A friend
    quietly moves a prop or finish mark to prepare a surprise, but the child
    overhears only half the plan and mistakes kindness for betrayal. After a
    wobbling search through mirrors, ribbons, or drum pads, the child discovers
    the truth and finishes the routine with more trust than fear.
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

SOURCE_TALE = (
    "At Bright Steps Dance Studio, a child practices a dance trail that feels "
    "like an adventure map. A helper hides part of the setup for a surprise, "
    "but the child hears only a secretive whisper and forms a misunderstanding. "
    "The child follows a clue, steadies a wobble, learns the truth, and ends "
    "the routine feeling brave and loved."
)

STUDIO_NAME = "Bright Steps Dance Studio"


@dataclass(frozen=True)
class Trail:
    key: str
    phrase: str
    intro_detail: str
    obstacle: str
    search_path: str
    finish_spot: str
    reveal_spot: str
    adventure_name: str
    allowed_misunderstandings: tuple[str, ...]
    supported_surprises: tuple[str, ...]
    wobble_load: float


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
    doubt_boost: float


@dataclass(frozen=True)
class Surprise:
    key: str
    phrase: str
    setup_template: str
    reveal_line_template: str
    ending_template: str
    warm_afterglow: str
    wonder_boost: float


@dataclass
class StoryParams:
    trail: str
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
    trail: Trail
    misunderstanding: Misunderstanding
    surprise: Surprise
    source_tale: str
    entities: dict[str, Entity] = field(default_factory=dict)
    beats: list[Beat] = field(default_factory=list)
    clue_found: str = ""
    misunderstanding_seen: bool = False
    surprise_ready: bool = False
    resolved: bool = False
    story: str = ""
    final_image: str = ""
    setup_phrase: str = ""
    reveal_line: str = ""
    suspicion_text: str = ""
    truth_text: str = ""
    tension_feeling: str = ""

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
        lines.append(f"  trail={self.trail.key}")
        lines.append(f"  misunderstanding={self.misunderstanding.key}")
        lines.append(f"  surprise={self.surprise.key}")
        lines.append(f"  misunderstanding_seen={self.misunderstanding_seen}")
        lines.append(f"  surprise_ready={self.surprise_ready}")
        lines.append(f"  resolved={self.resolved}")
        lines.append(f"  clue_found={self.clue_found or 'none'}")
        for key, ent in self.entities.items():
            meters = ", ".join(f"{name}={value:.2f}" for name, value in sorted(ent.meters.items())) or "none"
            memes = ", ".join(f"{name}={value:.2f}" for name, value in sorted(ent.memes.items())) or "none"
            inventory = ", ".join(ent.inventory) if ent.inventory else "none"
            lines.append(f"  {key}: {ent.name} ({ent.kind}) @ {ent.location}")
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


TRAILS: dict[str, Trail] = {
    "mirror_cove": Trail(
        key="mirror_cove",
        phrase="Mirror Cove trail",
        intro_detail="silver tape stars curling between tall mirrors and the quiet barre",
        obstacle="the moonbeam balance strip",
        search_path="the mirror wall, the piano nook, and the velvet practice curtain",
        finish_spot="the crescent finish star by the front mirrors",
        reveal_spot="the darkened side mirrors",
        adventure_name="mirror-cave crossing",
        allowed_misunderstandings=("missing_scarf", "quiet_music"),
        supported_surprises=("lantern_reveal", "family_watch"),
        wobble_load=0.24,
    ),
    "ribbon_bridge": Trail(
        key="ribbon_bridge",
        phrase="Ribbon Bridge trail",
        intro_detail="blue cloud mats, hanging ribbons, and a speaker shelf like a dock",
        obstacle="the bridge bench over the cloud mats",
        search_path="the ribbon arch, the speaker wall, and the curtain lane",
        finish_spot="the gold finish star beside the speaker wall",
        reveal_spot="the soft blue curtain",
        adventure_name="ribbon-bridge crossing",
        allowed_misunderstandings=("quiet_music", "covered_star"),
        supported_surprises=("banner_drop", "family_watch"),
        wobble_load=0.28,
    ),
    "drum_island": Trail(
        key="drum_island",
        phrase="Drum Island trail",
        intro_detail="foam drums set like tiny islands around the back practice ring",
        obstacle="the round stepping drums",
        search_path="the prop trunk, the drum ring, and the captain's circle by the wall",
        finish_spot="the captain's circle at the back wall",
        reveal_spot="the captain's circle",
        adventure_name="island-hop expedition",
        allowed_misunderstandings=("covered_star", "missing_scarf"),
        supported_surprises=("badge_ceremony", "banner_drop", "lantern_reveal"),
        wobble_load=0.33,
    ),
}

MISUNDERSTANDINGS: dict[str, Misunderstanding] = {
    "missing_scarf": Misunderstanding(
        key="missing_scarf",
        prop_phrase="the silver comet scarf",
        overheard_line="Keep it hidden until the last count.",
        suspicion_template="{friend} was taking {hero}'s silver comet scarf away and planning to lead the ending instead.",
        truth_template="{friend} had only borrowed the silver comet scarf so {teacher} could smooth its wrinkles and make it shine for the reveal.",
        clue_text="A silver thread glimmered beside the practice piano.",
        clue_phrase="a silver thread glimmering beside the practice piano",
        search_goal="the piano nook",
        allowed_surprises=("lantern_reveal", "family_watch"),
        doubt_boost=0.34,
    ),
    "quiet_music": Misunderstanding(
        key="quiet_music",
        prop_phrase="the music box remote",
        overheard_line="Do not start the song until he gets here.",
        suspicion_template="{teacher} was giving the final song to someone else, so {hero} would lose the ending of the routine.",
        truth_template="{teacher} had lowered the music only so the hidden guests could take their places before the reveal.",
        clue_text="Fresh toe marks pointed toward the curtain lane.",
        clue_phrase="fresh toe marks pointing toward the curtain lane",
        search_goal="the curtain lane",
        allowed_surprises=("banner_drop", "family_watch"),
        doubt_boost=0.30,
    ),
    "covered_star": Misunderstanding(
        key="covered_star",
        prop_phrase="the gold finish star",
        overheard_line="Move the star before she sees it.",
        suspicion_template="{friend} and {teacher} were erasing the finish of the routine and taking away {hero}'s best landing spot.",
        truth_template="{friend} had moved the gold finish star only so the surprise setup could fit in the final circle.",
        clue_text="A curl of gold tape peeked out from under the prop trunk.",
        clue_phrase="a curl of gold tape peeking out from under the prop trunk",
        search_goal="the back prop corner",
        allowed_surprises=("banner_drop", "badge_ceremony"),
        doubt_boost=0.36,
    ),
}

SURPRISES: dict[str, Surprise] = {
    "lantern_reveal": Surprise(
        key="lantern_reveal",
        phrase="a lantern path surprise",
        setup_template="paper lanterns shaped like little moons all along the trail",
        reveal_line_template="They had lit a lantern path so {hero} could dance through a tiny moon adventure.",
        ending_template="{hero} finished with a bright moon-sail turn under the lantern glow.",
        warm_afterglow="The studio looked less like a practice room and more like a brave little night sea.",
        wonder_boost=0.40,
    ),
    "family_watch": Surprise(
        key="family_watch",
        phrase="a hidden family audience",
        setup_template="a row of folding chairs and waiting smiles tucked behind the curtain",
        reveal_line_template="They had invited {hero}'s family to watch the full trail as a secret cheer squad.",
        ending_template="{hero} bowed so proudly that even the mirrors seemed ready to clap.",
        warm_afterglow="The room felt warmer the moment the curtain opened and the smiles came out.",
        wonder_boost=0.38,
    ),
    "banner_drop": Surprise(
        key="banner_drop",
        phrase="a comet banner reveal",
        setup_template="a comet banner with {hero}'s name hanging over the finish spot",
        reveal_line_template="They had hidden a comet banner above the ending so {hero} would feel like the captain of the whole adventure.",
        ending_template="{hero} landed beneath the banner with both feet steady and chin high.",
        warm_afterglow="For one shining moment, the finish mark felt like the deck of a storybook ship.",
        wonder_boost=0.36,
    ),
    "badge_ceremony": Surprise(
        key="badge_ceremony",
        phrase="a Trail Captain badge ceremony",
        setup_template="a tiny badge stand waiting beside the captain's circle",
        reveal_line_template="They had prepared a Trail Captain badge because {hero} had kept trying even on hard practice days.",
        ending_template="{hero} landed in the captain's circle while the new badge gleamed near the heart.",
        warm_afterglow="The little badge looked small, but it carried the weight of every brave try.",
        wonder_boost=0.42,
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Ava", "Nora", "Lila", "Mina", "Suri"),
    "boy": ("Leo", "Eli", "Milo", "Rory", "Tomas"),
}

FRIEND_NAMES: tuple[str, ...] = ("June", "Pip", "Sana", "Theo", "Mika", "Nell")
TEACHERS: tuple[str, ...] = ("Ms. Sol", "Mr. Vale", "Coach Lark")


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combos() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for trail in TRAILS.values():
        for misunderstanding in MISUNDERSTANDINGS.values():
            if misunderstanding.key not in trail.allowed_misunderstandings:
                continue
            for surprise in SURPRISES.values():
                if surprise.key not in trail.supported_surprises:
                    continue
                if surprise.key not in misunderstanding.allowed_surprises:
                    continue
                rows.append((trail.key, misunderstanding.key, surprise.key))
    return sorted(rows)


def describe_rejection(trail_key: str, misunderstanding_key: str, surprise_key: str) -> str:
    if trail_key not in TRAILS:
        raise StoryError(f"Unknown trail '{trail_key}'. Choose from {', '.join(sorted(TRAILS))}.")
    if misunderstanding_key not in MISUNDERSTANDINGS:
        raise StoryError(
            f"Unknown misunderstanding '{misunderstanding_key}'. Choose from {', '.join(sorted(MISUNDERSTANDINGS))}."
        )
    if surprise_key not in SURPRISES:
        raise StoryError(f"Unknown surprise '{surprise_key}'. Choose from {', '.join(sorted(SURPRISES))}.")

    trail = TRAILS[trail_key]
    misunderstanding = MISUNDERSTANDINGS[misunderstanding_key]
    surprise = SURPRISES[surprise_key]
    if misunderstanding.key not in trail.allowed_misunderstandings:
        return (
            f"{trail.phrase} does not fit the {misunderstanding.key} misunderstanding. "
            f"That trail supports {', '.join(trail.allowed_misunderstandings)}."
        )
    if surprise.key not in trail.supported_surprises:
        return (
            f"{trail.phrase} cannot stage {surprise.phrase}. "
            f"That trail supports {', '.join(trail.supported_surprises)}."
        )
    if surprise.key not in misunderstanding.allowed_surprises:
        return (
            f"The {misunderstanding.key} misunderstanding does not lead cleanly to {surprise.phrase}. "
            f"It supports {', '.join(misunderstanding.allowed_surprises)}."
        )
    return "That dance-studio adventure combination is not reasonable."


def build_world(params: StoryParams) -> World:
    if (params.trail, params.misunderstanding, params.surprise) not in valid_combos():
        raise StoryError(describe_rejection(params.trail, params.misunderstanding, params.surprise))

    trail = TRAILS[params.trail]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    surprise = SURPRISES[params.surprise]

    world = World(
        params=params,
        trail=trail,
        misunderstanding=misunderstanding,
        surprise=surprise,
        source_tale=SOURCE_TALE,
    )

    hero = Entity(
        name=params.hero,
        kind="child dancer",
        location="cubby row",
        meters={"balance": 0.58, "stamina": 0.72, "wobble": 0.26},
        memes={"courage": 0.61, "trust": 0.74, "worry": 0.18, "wonder": 0.47, "surprise": 0.0},
        inventory=[],
        notes={"goal": trail.finish_spot},
    )
    friend = Entity(
        name=params.friend,
        kind="helper friend",
        location="prop shelf",
        meters={"quiet_steps": 0.66, "timing": 0.63},
        memes={"care": 0.82, "secrecy": 0.42, "patience": 0.59},
        inventory=[],
    )
    teacher = Entity(
        name=params.teacher,
        kind="dance teacher",
        location="music stand",
        meters={"timing": 0.90, "voice": 0.68},
        memes={"guidance": 0.94, "care": 0.88, "surprise": 0.32},
        inventory=[],
    )
    prop = Entity(
        name=misunderstanding.prop_phrase,
        kind="studio prop",
        location="hero cubby",
        meters={"shine": 0.42, "steadiness": 0.50},
        memes={"importance": 0.66},
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

    hero.location = world.trail.phrase
    hero.inventory = [prop.name]
    world.setup_phrase = world.surprise.setup_template.format(hero=hero.name)
    world.reveal_line = world.surprise.reveal_line_template.format(hero=hero.name)
    world.suspicion_text = world.misunderstanding.suspicion_template.format(
        hero=hero.name, friend=friend.name, teacher=teacher.name
    )
    world.truth_text = world.misunderstanding.truth_template.format(
        hero=hero.name, friend=friend.name, teacher=teacher.name
    )

    _record(
        world,
        "beginning",
        world.trail.phrase,
        f"{hero.name} arrived to rehearse the {world.trail.phrase} at {STUDIO_NAME}.",
        "A fresh practice day had started.",
        f"{hero.name} focused on reaching {world.trail.finish_spot}.",
    )

    friend.location = world.misunderstanding.search_goal
    teacher.location = "music stand"
    prop.location = world.misunderstanding.search_goal
    hero.inventory.clear()
    friend.inventory = [prop.name]
    world.misunderstanding_seen = True
    hero.memes["worry"] += world.misunderstanding.doubt_boost
    hero.memes["trust"] -= 0.24
    hero.memes["wonder"] -= 0.10
    friend.memes["secrecy"] += 0.18
    world.tension_feeling = "tight and stormy" if hero.memes["worry"] > 0.45 else "small and shaky"
    _record(
        world,
        "misunderstanding",
        world.misunderstanding.search_goal,
        f"{hero.name} saw {friend.name} slip away with {prop.name} after hearing, '{world.misunderstanding.overheard_line}'",
        "The teacher and friend were hiding the surprise setup.",
        world.suspicion_text,
    )

    world.clue_found = world.misunderstanding.clue_text
    hero.location = world.trail.search_path
    hero.meters["wobble"] += world.trail.wobble_load
    hero.meters["balance"] -= 0.08
    hero.meters["stamina"] -= 0.07
    hero.memes["courage"] += 0.12
    _record(
        world,
        "search",
        world.trail.search_path,
        f"{hero.name} followed the clue of {world.misunderstanding.clue_phrase} through {world.trail.search_path}.",
        "The misunderstanding made the studio feel like a real adventure trail.",
        f"A careful wobble on {world.trail.obstacle} reminded {hero.name} to breathe and keep going.",
    )

    hero.location = world.trail.reveal_spot
    friend.location = world.trail.reveal_spot
    teacher.location = world.trail.reveal_spot
    prop.location = hero.name
    friend.inventory.clear()
    hero.inventory = [prop.name]
    world.surprise_ready = True
    world.resolved = True
    hero.memes["trust"] += 0.41
    hero.memes["wonder"] += world.surprise.wonder_boost
    hero.memes["surprise"] += 0.78
    hero.memes["worry"] = max(0.06, hero.memes["worry"] - 0.40)
    hero.meters["balance"] += 0.20
    hero.meters["wobble"] = max(0.18, hero.meters["wobble"] - 0.10)
    teacher.memes["surprise"] += 0.30
    _record(
        world,
        "reveal",
        world.trail.reveal_spot,
        f"{hero.name} found {friend.name} and {teacher.name} finishing {world.setup_phrase}.",
        world.truth_text,
        world.reveal_line,
    )

    hero.location = world.trail.finish_spot
    teacher.location = world.trail.finish_spot
    friend.location = world.trail.finish_spot
    hero.meters["stamina"] += 0.05
    hero.memes["courage"] += 0.18
    hero.memes["wonder"] += 0.08
    world.final_image = world.surprise.ending_template.format(hero=hero.name)
    _record(
        world,
        "ending",
        world.trail.finish_spot,
        f"{hero.name} danced across {world.trail.adventure_name} and reached {world.trail.finish_spot}.",
        "The truth replaced fear with trust.",
        world.final_image,
    )


def _wobble_phrase(world: World) -> str:
    wobble = world.hero().meters["wobble"]
    if wobble >= 0.50:
        return "a big wobble"
    if wobble >= 0.35:
        return "a careful wobble"
    return "a tiny wobble"


def _mood_phrase(world: World) -> str:
    trust = world.hero().memes["trust"]
    worry = world.hero().memes["worry"]
    if trust > 0.80 and worry < 0.20:
        return "steady-hearted"
    if worry > trust:
        return "stormy inside"
    return "careful but hopeful"


def render_story(world: World) -> str:
    hero = world.hero()
    friend = world.friend()
    teacher = world.teacher()
    prop = world.prop()
    subj, poss, _obj = _pronouns(world.params.gender)
    wobble = _wobble_phrase(world)

    beginning = (
        f"At {STUDIO_NAME}, {hero.name} was ready to rehearse the {world.trail.phrase}. "
        f"The dance studio had {world.trail.intro_detail}, and the whole room felt like {world.trail.adventure_name}. "
        f"{hero.name} especially loved the part with {world.trail.obstacle}, where even {wobble} could become part of the dance if {subj} kept breathing."
    )

    middle = (
        f"Then {hero.name} noticed that {prop.name} was gone. {hero.name} saw {friend.name} hurry toward {world.misunderstanding.search_goal} "
        f"and heard {teacher.name} whisper, \"{world.misunderstanding.overheard_line}\" "
        f"For one hot moment, {hero.name} thought {world.suspicion_text} "
        f"The misunderstanding made {poss} chest feel {world.tension_feeling}, but {subj} still followed the clue of "
        f"{world.misunderstanding.clue_phrase} through {world.trail.search_path}."
    )

    ending = (
        f"Near {world.trail.reveal_spot}, {hero.name} found {friend.name} and {teacher.name} finishing {world.setup_phrase}. "
        f"{world.truth_text} It was a surprise for {hero.name}. {world.reveal_line} "
        f"When the music finally swelled, {hero.name} crossed {world.trail.obstacle} and landed on {world.trail.finish_spot}. "
        f"{world.final_image} "
        f"{world.surprise.warm_afterglow}"
    )

    return "\n\n".join([beginning, middle, ending])


def build_prompts(world: World) -> list[str]:
    hero = world.hero().name
    return [
        "Write a child-facing Adventure story that includes the word 'wobble.'",
        f"Set the story in a dance studio and center it on {hero} rehearsing the {world.trail.phrase}.",
        f"Include a misunderstanding about {world.misunderstanding.prop_phrase} that leads to {world.surprise.phrase}.",
    ]


def build_story_qa(world: World) -> list[QAItem]:
    hero = world.hero().name
    friend = world.friend().name
    teacher = world.teacher().name
    return [
        QAItem(
            question=f"Why did {hero} start searching through the studio?",
            answer=(
                f"{hero} thought {world.suspicion_text} "
                f"That misunderstanding made the practice trail feel like a real problem that had to be solved before the dance could end well."
            ),
        ),
        QAItem(
            question=f"What clue showed {hero} where to look next?",
            answer=(
                f"{world.clue_found} "
                f"It pointed {hero} toward {world.misunderstanding.search_goal}, which is where the surprise work was happening."
            ),
        ),
        QAItem(
            question="How did the wobble matter during the adventure?",
            answer=(
                f"{hero} felt { _wobble_phrase(world) } on {world.trail.obstacle}, so {hero} had to slow down and breathe. "
                f"That small steadying moment helped courage win over panic."
            ),
        ),
        QAItem(
            question=f"What was really happening behind {world.trail.reveal_spot}?",
            answer=(
                f"{friend} and {teacher} were finishing {world.setup_phrase}. "
                f"They were preparing {world.surprise.phrase} for {hero}, not taking the routine away."
            ),
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=(
                f"{world.truth_text} "
                f"Once {hero} heard the whole plan, trust came back and the room stopped feeling sneaky."
            ),
        ),
        QAItem(
            question=f"What changed for {hero} by the end of the story?",
            answer=(
                f"{hero} finished the rehearsal feeling braver and more sure of the people in the room. "
                f"The ending image proves that the wobble became part of a successful dance instead of a sign of failure."
            ),
        ),
    ]


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why might a dance teacher keep a surprise quiet during rehearsal?",
            answer=(
                "A surprise needs a little secrecy so the final reveal can feel bright and special. "
                "In this studio, the quiet planning let the ending land all at once instead of being spoiled early."
            ),
        ),
        QAItem(
            question="What can a wobble teach a dancer on a practice trail?",
            answer=(
                "A wobble can warn a dancer to slow down, breathe, and place each foot with care. "
                "That turns a shaky moment into a useful piece of practice instead of a defeat."
            ),
        ),
        QAItem(
            question="Why are misunderstandings easy to make in a busy dance studio?",
            answer=(
                "People move props, whisper cues, and cross the room quickly during rehearsal. "
                "If someone hears only half a plan, it is easy to build the wrong story in their head."
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
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("--- story qa ---")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    lines.append("--- world qa ---")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    parser = argparse.ArgumentParser(description="Dance studio misunderstanding-surprise adventure world.")
    parser.add_argument("--trail", choices=sorted(TRAILS))
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
        if (args.trail is None or combo[0] == args.trail)
        and (args.misunderstanding is None or combo[1] == args.misunderstanding)
        and (args.surprise is None or combo[2] == args.surprise)
    ]
    if not combos:
        raise StoryError(
            describe_rejection(
                args.trail or "mirror_cove",
                args.misunderstanding or "missing_scarf",
                args.surprise or "lantern_reveal",
            )
        )

    trail, misunderstanding, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    teacher = args.teacher or rng.choice(TEACHERS)
    if friend == hero:
        raise StoryError("Friend and hero must be different people in this storyworld.")
    return StoryParams(
        trail=trail,
        misunderstanding=misunderstanding,
        surprise=surprise,
        hero=hero,
        gender=gender,
        friend=friend,
        teacher=teacher,
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
combo(T,M,S) :-
  trail(T), misunderstanding(M), surprise(S),
  trail_allows_misunderstanding(T,M),
  trail_supports_surprise(T,S),
  misunderstanding_supports_surprise(M,S).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for trail in TRAILS.values():
        rows.append(asp.fact("trail", trail.key))
        for misunderstanding in trail.allowed_misunderstandings:
            rows.append(asp.fact("trail_allows_misunderstanding", trail.key, misunderstanding))
        for surprise in trail.supported_surprises:
            rows.append(asp.fact("trail_supports_surprise", trail.key, surprise))
    for misunderstanding in MISUNDERSTANDINGS.values():
        rows.append(asp.fact("misunderstanding", misunderstanding.key))
        for surprise in misunderstanding.allowed_surprises:
            rows.append(asp.fact("misunderstanding_supports_surprise", misunderstanding.key, surprise))
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
            trail=combo[0],
            misunderstanding=combo[1],
            surprise=combo[2],
            hero="Ava",
            gender="girl",
            friend="June",
            teacher="Ms. Sol",
            seed=700 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        if "wobble" not in story:
            problems.append(f"{combo}: story is missing the seed word 'wobble'")
        if "dance studio" not in story:
            problems.append(f"{combo}: story does not name the dance studio setting")
        if "surprise" not in story:
            problems.append(f"{combo}: story never names the surprise")
        if "misunderstanding" not in story:
            problems.append(f"{combo}: story never names the misunderstanding")
        if story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, middle, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if sample.world is None or not sample.world.resolved:
            problems.append(f"{combo}: world never reaches a resolved state")
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
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 41
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            trail=combo[0],
            misunderstanding=combo[1],
            surprise=combo[2],
            hero=args.hero or "Ava",
            gender=args.gender or "girl",
            friend=args.friend or "June",
            teacher=args.teacher or "Ms. Sol",
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
                header = (
                    f"### trail={p.trail} misunderstanding={p.misunderstanding} "
                    f"surprise={p.surprise}"
                )
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
