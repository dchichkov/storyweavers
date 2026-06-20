#!/usr/bin/env python3
"""
mature_nopsu_curiosity_repetition_bedtime_story.py
==================================================

A small bedtime storyworld about a child, a plush named Nopsu, and a repeated
night sound that invites safe curiosity.
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


@dataclass(frozen=True)
class SoundSource:
    key: str
    phrase: str
    repeated_sound: str
    need: str
    mood: str
    location_phrase: str
    truth_phrase: str
    settle_action: str
    ending_image: str


@dataclass(frozen=True)
class Investigation:
    key: str
    phrase: str
    solves: tuple[str, ...]
    tool_phrase: str
    safe_detail: str


@dataclass(frozen=True)
class Ritual:
    key: str
    phrase: str
    suited_moods: tuple[str, ...]
    repeated_line: str
    action_text: str
    ending_image: str


@dataclass
class StoryParams:
    source: str
    investigation: str
    ritual: str
    hero: str
    gender: str
    adult: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    state: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    source: SoundSource
    investigation: Investigation
    ritual: Ritual
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    repetition_count: int = 0
    resolved: bool = False
    discovery: str = ""
    final_image: str = ""
    lesson: str = ""
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            "  params="
            f"source={self.params.source}, investigation={self.params.investigation}, "
            f"ritual={self.params.ritual}, hero={self.params.hero}, adult={self.params.adult}"
        )
        lines.append(
            f"  source={self.source.key} need={self.source.need} mood={self.source.mood} "
            f"repeated_sound={self.source.repeated_sound!r}"
        )
        lines.append(f"  investigation={self.investigation.key} tool={self.investigation.tool_phrase}")
        lines.append(f"  ritual={self.ritual.key} line={self.ritual.repeated_line!r}")
        lines.append(f"  repetition_count={self.repetition_count}")
        lines.append(f"  resolved={self.resolved}")
        if self.discovery:
            lines.append(f"  discovery={self.discovery}")
        if self.final_image:
            lines.append(f"  final_image={self.final_image}")
        lines.append(f"  events={', '.join(self.events) if self.events else 'none'}")
        for key, ent in self.entities.items():
            meter_bits = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items())) or "none"
            meme_bits = ", ".join(f"{k}={v:.2f}" for k, v in sorted(ent.memes.items())) or "none"
            state_bits = ", ".join(f"{k}={v}" for k, v in sorted(ent.state.items())) or "none"
            lines.append(
                f"  {key}: {ent.name} ({ent.kind}) | meters[{meter_bits}] | "
                f"memes[{meme_bits}] | state[{state_bits}]"
            )
        return "\n".join(lines)


SOURCES: dict[str, SoundSource] = {
    "branch_tap": SoundSource(
        key="branch_tap",
        phrase="a branch tapping the bedroom window",
        repeated_sound="tap, tap, tap",
        need="window",
        mood="fluttery",
        location_phrase="the curtain by the window",
        truth_phrase="a thin willow branch outside was bowing in the wind and brushing the glass",
        settle_action="They watched one more soft sway, then pulled the curtain thicker so the taps turned into a hush.",
        ending_image="the curtain breathed gently while the branch moved outside where it belonged",
    ),
    "bead_roll": SoundSource(
        key="bead_roll",
        phrase="a bead rolling under the bed slats",
        repeated_sound="tik, tik, tik",
        need="floor",
        mood="restless",
        location_phrase="the floor beside the bed",
        truth_phrase="one round wooden bead had slipped from an old bracelet and nudged the floorboard whenever the blanket shifted",
        settle_action="They rescued the bead and tucked it into a shell dish on the shelf so it could not wander again.",
        ending_image="the little bead rested in its shell dish beside the lamp",
    ),
    "heater_click": SoundSource(
        key="heater_click",
        phrase="the radiator making bedtime clicks",
        repeated_sound="click, click, click",
        need="radiator",
        mood="curious",
        location_phrase="the warm corner by the radiator",
        truth_phrase="the radiator was settling as the room cooled, making tiny metal clicks before sleep",
        settle_action="They counted the last warm clicks together until the metal finished settling and the corner went still.",
        ending_image="the quiet radiator glowed beside the rug like a sleepy red pebble",
    ),
}


INVESTIGATIONS: dict[str, Investigation] = {
    "curtain_peek": Investigation(
        key="curtain_peek",
        phrase="counted the sound with Nopsu and peeked through a small curtain gap",
        solves=("window",),
        tool_phrase="a moonlit curtain gap",
        safe_detail="The grown-up stood beside the bed first, so curiosity stayed gentle and safe.",
    ),
    "lantern_kneel": Investigation(
        key="lantern_kneel",
        phrase="knelt with a tiny amber lantern and followed the sound along the floorboards",
        solves=("floor",),
        tool_phrase="a low amber lantern",
        safe_detail="The lantern stayed low, and the grown-up kept fingers clear of the bed frame.",
    ),
    "warm_listen": Investigation(
        key="warm_listen",
        phrase="sat by the radiator and listened between each fading click",
        solves=("radiator",),
        tool_phrase="quiet listening by the radiator",
        safe_detail="The grown-up touched the safe cool edge first and showed exactly where to sit.",
    ),
}


RITUALS: dict[str, Ritual] = {
    "three_breaths": Ritual(
        key="three_breaths",
        phrase="three slow breaths under the quilt",
        suited_moods=("fluttery", "curious"),
        repeated_line="In, out, soft and slow.",
        action_text="Together they whispered, \"In, out, soft and slow,\" three times until the room answered with quiet.",
        ending_image="the blanket rose and fell in three slow little hills",
    ),
    "moon_count": Ritual(
        key="moon_count",
        phrase="a count of four moonlit squares on the quilt",
        suited_moods=("fluttery", "restless"),
        repeated_line="One moon, two moons, three moons, four.",
        action_text="They counted the moonlit squares on the quilt again: \"One moon, two moons, three moons, four,\" until the counting felt heavier than the worry.",
        ending_image="four pale squares of moonlight rested on the quilt without moving",
    ),
    "pillow_pat": Ritual(
        key="pillow_pat",
        phrase="a gentle pillow pat and tuck",
        suited_moods=("restless", "curious"),
        repeated_line="Pat, smooth, tuck.",
        action_text="They smoothed the pillow together and repeated, \"Pat, smooth, tuck,\" until even Nopsu's ear lay flat.",
        ending_image="the pillow stayed smooth and Nopsu's folded ear slept on top of the blanket",
    ),
}


HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Rina", "Mila", "Tali", "Sora"),
    "boy": ("Oren", "Milo", "Nico", "Ari"),
}

ADULT_NAMES: tuple[str, ...] = ("Mama", "Papa", "Grandma")


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combo(source_key: str, investigation_key: str, ritual_key: str) -> bool:
    if source_key not in SOURCES or investigation_key not in INVESTIGATIONS or ritual_key not in RITUALS:
        return False
    source = SOURCES[source_key]
    investigation = INVESTIGATIONS[investigation_key]
    ritual = RITUALS[ritual_key]
    return source.need in investigation.solves and source.mood in ritual.suited_moods


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for source_key in sorted(SOURCES):
        for investigation_key in sorted(INVESTIGATIONS):
            for ritual_key in sorted(RITUALS):
                if valid_combo(source_key, investigation_key, ritual_key):
                    combos.append((source_key, investigation_key, ritual_key))
    return combos


def explain_rejection(source_key: str, investigation_key: str, ritual_key: str) -> str:
    if source_key not in SOURCES:
        return f"No story: unknown sound source {source_key!r}."
    if investigation_key not in INVESTIGATIONS:
        return f"No story: unknown investigation {investigation_key!r}."
    if ritual_key not in RITUALS:
        return f"No story: unknown ritual {ritual_key!r}."
    source = SOURCES[source_key]
    investigation = INVESTIGATIONS[investigation_key]
    ritual = RITUALS[ritual_key]
    if source.need not in investigation.solves:
        return (
            f"No story: {investigation.phrase} does not fit a sound coming from "
            f"{source.location_phrase}."
        )
    if source.mood not in ritual.suited_moods:
        return (
            f"No story: {ritual.phrase} does not match the {source.mood} feeling "
            f"left by {source.phrase}."
        )
    return "No story: this bedtime setup is not reasonable."


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.source, params.investigation, params.ritual):
        raise StoryError(explain_rejection(params.source, params.investigation, params.ritual))

    source = SOURCES[params.source]
    investigation = INVESTIGATIONS[params.investigation]
    ritual = RITUALS[params.ritual]
    subject, possessive, _obj = _pronouns(params.gender)

    hero = Entity(
        name=params.hero,
        kind="child",
        meters={
            "height_m": 1.08 if params.gender == "girl" else 1.11,
            "bed_distance_m": 0.0,
            "blanket_edge_m": 0.35,
        },
        memes={
            "curiosity": 0.62,
            "worry": 0.24,
            "calm": 0.38,
            "sleepiness": 0.48,
        },
        state={
            "position": "bed",
            "pronoun": subject,
            "possessive": possessive,
        },
    )
    nopsu = Entity(
        name="Nopsu",
        kind="plush companion",
        meters={
            "height_m": 0.26,
            "bed_distance_m": 0.0,
            "ear_span_m": 0.12,
        },
        memes={
            "comfort": 0.84,
            "curiosity": 0.22,
        },
        state={
            "position": "under chin",
            "texture": "soft",
        },
    )
    adult = Entity(
        name=params.adult,
        kind="grown-up helper",
        meters={
            "height_m": 1.68,
            "door_distance_m": 1.9,
        },
        memes={
            "calm": 0.91,
            "patience": 0.88,
        },
        state={
            "position": "hallway",
        },
    )
    source_entity = Entity(
        name=source.key,
        kind="bedroom source",
        meters={
            "distance_from_bed_m": 0.8 if source.need == "window" else 0.3 if source.need == "floor" else 1.1,
        },
        memes={
            "mystery": 0.41,
        },
        state={
            "location": source.location_phrase,
            "sound": source.repeated_sound,
        },
    )

    world = World(
        params=params,
        source=source,
        investigation=investigation,
        ritual=ritual,
        entities={
            "hero": hero,
            "nopsu": nopsu,
            "adult": adult,
            "source": source_entity,
        },
    )

    _hear_repeated_sound(world)
    _call_for_help(world)
    _investigate(world)
    _settle(world)
    return world


def _hear_repeated_sound(world: World) -> None:
    hero = world.entities["hero"]
    hero.memes["worry"] += 0.16
    hero.memes["curiosity"] += 0.21
    world.repetition_count = 3
    world.events.append(f"heard:{world.source.repeated_sound}")


def _call_for_help(world: World) -> None:
    hero = world.entities["hero"]
    adult = world.entities["adult"]
    hero.memes["calm"] += 0.12
    hero.state["position"] = "sitting up"
    adult.state["position"] = "bedside"
    world.events.append("asked-grown-up")


def _investigate(world: World) -> None:
    hero = world.entities["hero"]
    nopsu = world.entities["nopsu"]
    adult = world.entities["adult"]
    source = world.entities["source"]

    hero.state["position"] = world.source.need
    nopsu.state["position"] = "held close"
    adult.state["position"] = world.source.need
    source.memes["mystery"] = 0.0
    hero.memes["curiosity"] += 0.08
    hero.memes["worry"] = max(0.05, hero.memes["worry"] - 0.18)
    hero.memes["calm"] += 0.19
    world.discovery = world.source.truth_phrase
    world.resolved = True
    world.events.append(f"investigated:{world.investigation.key}")
    world.events.append(f"discovered:{world.source.key}")


def _settle(world: World) -> None:
    hero = world.entities["hero"]
    nopsu = world.entities["nopsu"]
    hero.state["position"] = "back in bed"
    nopsu.state["position"] = "on blanket"
    hero.memes["sleepiness"] += 0.28
    hero.memes["calm"] += 0.18
    world.final_image = f"{world.source.ending_image}, and {world.ritual.ending_image}"
    world.lesson = "The mature choice was to ask, check, and understand the sound instead of feeding it guesses."
    world.events.append(f"ritual:{world.ritual.key}")
    world.events.append("asleep-soon")


def _opening(world: World) -> str:
    hero = world.entities["hero"].name
    source = world.source
    return (
        f"At bedtime, {hero} lay under a round quilt with Nopsu tucked beneath {world.entities['hero'].state['possessive']} chin. "
        f"The room was almost still when {source.repeated_sound} came from {source.location_phrase}, then {source.repeated_sound} again."
    )


def _tension(world: World) -> str:
    hero = world.entities["hero"].name
    adult = world.entities["adult"].name
    return (
        f"{hero} did not want to guess in the dark, but the repeated sound made {world.entities['hero'].state['possessive']} heart feel busy. "
        f"So {hero} used a small, mature voice and called for {adult}, still holding Nopsu close."
    )


def _turn(world: World) -> str:
    hero = world.entities["hero"].name
    adult = world.entities["adult"].name
    return (
        f"Together they {world.investigation.phrase}. {world.investigation.safe_detail} "
        f"There they found the answer: {world.discovery}. "
        f"{world.source.settle_action}"
    )


def _resolution(world: World) -> str:
    hero = world.entities["hero"].name
    return (
        f"Back in bed, {hero} and {world.entities['adult'].name} finished with {world.ritual.phrase}. "
        f"{world.ritual.action_text} {world.lesson}"
    )


def _ending_image(world: World) -> str:
    hero = world.entities["hero"].name
    final_image = world.final_image
    if final_image:
        final_image = final_image[:1].upper() + final_image[1:]
    return f"Soon {hero}'s eyes grew heavy. {final_image}."


def render_story(world: World) -> str:
    return "\n\n".join([
        " ".join([_opening(world), _tension(world)]),
        _turn(world),
        " ".join([_resolution(world), _ending_image(world)]),
    ])


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = render_story(world)
    world.story = story
    hero = world.entities["hero"].name
    adult = world.entities["adult"].name

    prompts = [
        f"Write a Bedtime Story about {hero}, a plush named Nopsu, and the repeated sound {world.source.repeated_sound}.",
        "Let Curiosity move the middle of the story, but keep every step safe and grounded in the room.",
        f"End with a concrete bedtime image after {adult} helps explain the sound.",
    ]

    story_qa = [
        QAItem(
            "What kept repeating at the start of the story?",
            f"The repeated sound was {world.source.repeated_sound}, coming from {world.source.location_phrase}. It mattered because that steady repetition is what woke up {hero}'s curiosity and worry at bedtime.",
        ),
        QAItem(
            "Why did the child call for help instead of guessing alone?",
            f"{hero} wanted to know the truth without making the dark feel bigger than it was. The story marks that as the mature choice, because a grown-up could help check the room safely.",
        ),
        QAItem(
            "How did they investigate the sound?",
            f"They {world.investigation.phrase}. That method fit the sound because it led them straight to {world.source.location_phrase} and kept the investigation calm.",
        ),
        QAItem(
            "What was the real cause of the sound?",
            f"The real cause was that {world.discovery}. Once they understood that cause, the sound stopped feeling mysterious and started feeling ordinary.",
        ),
        QAItem(
            "How does the ending prove that the room changed?",
            f"The ending image shows this: {world.final_image}. That image matters because it replaces the repeating noise with a settled room and a sleepy child.",
        ),
    ]

    world_qa = [
        QAItem(
            "Why can repeated sounds feel larger at bedtime?",
            "Dark rooms remove some of the easy clues that explain a sound right away. A repeated noise can fill that gap with worry until someone checks where it is really coming from.",
        ),
        QAItem(
            "What is a safe way for a child to explore a bedtime mystery?",
            "A safe way is to ask a grown-up, stay inside the room, and use a simple method that matches the place the sound comes from. That keeps curiosity grounded in real objects instead of wild guesses.",
        ),
        QAItem(
            "How can repetition become calming instead of scary?",
            "Repetition feels scary when it is unexplained, but it can feel soothing once the cause is known. A repeated breath, count, or tuck can give the body a steady rhythm after the mystery is solved.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== (2) Story-grounded QA"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.extend(["", "== (3) World-knowledge QA"])
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
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bedtime repetition-curiosity storyworld with Nopsu.")
    parser.add_argument("--source", choices=sorted(SOURCES))
    parser.add_argument("--investigation", choices=sorted(INVESTIGATIONS))
    parser.add_argument("--ritual", choices=sorted(RITUALS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--adult")
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
        if (args.source is None or combo[0] == args.source)
        and (args.investigation is None or combo[1] == args.investigation)
        and (args.ritual is None or combo[2] == args.ritual)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.source or "branch_tap",
                args.investigation or "curtain_peek",
                args.ritual or "three_breaths",
            )
        )

    source_key, investigation_key, ritual_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(
        source=source_key,
        investigation=investigation_key,
        ritual=ritual_key,
        hero=hero,
        gender=gender,
        adult=adult,
        seed=(args.seed if args.seed is not None else 1000) + index,
    )


ASP_RULES = r"""
combo(S,I,R) :-
  source(S), investigation(I), ritual(R),
  source_need(S,N), solves(I,N),
  source_mood(S,M), ritual_mood(R,M).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for source in SOURCES.values():
        rows.append(asp.fact("source", source.key))
        rows.append(asp.fact("source_need", source.key, source.need))
        rows.append(asp.fact("source_mood", source.key, source.mood))
    for investigation in INVESTIGATIONS.values():
        rows.append(asp.fact("investigation", investigation.key))
        for need in investigation.solves:
            rows.append(asp.fact("solves", investigation.key, need))
    for ritual in RITUALS.values():
        rows.append(asp.fact("ritual", ritual.key))
        for mood in ritual.suited_moods:
            rows.append(asp.fact("ritual_mood", ritual.key, mood))
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
            source=combo[0],
            investigation=combo[1],
            ritual=combo[2],
            hero="Rina",
            gender="girl",
            adult="Mama",
            seed=700 + i,
        )
        sample = generate(params)
        story_lower = sample.story.lower()
        if "mature" not in story_lower:
            problems.append(f"{combo}: story is missing the seed word 'mature'")
        if "nopsu" not in story_lower:
            problems.append(f"{combo}: story is missing the seed word 'nopsu'")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, middle, or ending paragraph")
        if sample.world is None or not sample.world.resolved:
            problems.append(f"{combo}: world never reaches a resolved state")
        if sample.world is None or sample.world.repetition_count < 3:
            problems.append(f"{combo}: repetition never becomes an explicit world fact")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
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
        raise StoryError("Not enough unique bedtime stories for the current constraint set.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 29
    hero = args.hero or "Rina"
    gender = args.gender or "girl"
    adult = args.adult or "Mama"
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            source=combo[0],
            investigation=combo[1],
            ritual=combo[2],
            hero=hero,
            gender=gender,
            adult=adult,
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
                    f"### source={p.source} investigation={p.investigation} "
                    f"ritual={p.ritual} hero={p.hero}"
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
