#!/usr/bin/env python3
"""
storyworlds/worlds/station_garden_center_suspense_bedtime_story.py
=================================================================

Bedtime story world for a garden center suspense seed.

Internal source tale
--------------------
At bedtime, a child helps close a garden center and hears a tiny mysterious
sound at one station. The child does not rush or grab. Instead, the child uses
one gentle, place-appropriate way to investigate. The sound turns out to come
from an ordinary hidden cause, and the ending image proves the garden center is
quiet again.
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


GARDEN_CENTER_NAME = "Moonpetal Garden Center"


@dataclass(frozen=True)
class StationArea:
    key: str
    phrase: str
    cozy_detail: str
    chore: str
    ending_image: str
    allowed_responses: tuple[str, ...]


@dataclass(frozen=True)
class Mystery:
    key: str
    label: str
    origin_phrase: str
    noise_phrase: str
    truth: str
    why_here: str
    final_fix: str
    final_image: str
    compatible_responses: tuple[str, ...]
    stations: tuple[str, ...]


@dataclass(frozen=True)
class ResponsePlan:
    key: str
    phrase: str
    action_text: str
    safe_reason: str


@dataclass
class StoryParams:
    station: str
    mystery: str
    response: str
    hero: str
    gender: str
    helper: str
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
        if self.kind in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    station_cfg: StationArea
    mystery_cfg: Mystery
    response_cfg: ResponsePlan
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
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

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  station={self.station_cfg.key}")
        rows.append(f"  mystery={self.mystery_cfg.key}")
        rows.append(f"  response={self.response_cfg.key}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name}<{ent.kind}> location={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(f"  fired={self.fired}")
        return "\n".join(rows)


STATIONS: dict[str, StationArea] = {
    "watering_station": StationArea(
        key="watering_station",
        phrase="the watering station beside the fern wall",
        cozy_detail="silver cans shone under the glass roof, and the pebble trays still smelled cool and green",
        chore="counted the pebble trays before closing",
        ending_image="the fern leaves held beads of water like sleepy stars",
        allowed_responses=("listen_for_drips", "close_valve"),
    ),
    "potting_station": StationArea(
        key="potting_station",
        phrase="the potting station near the clay pots",
        cozy_detail="small scoops rested in warm soil, and empty terracotta pots stood in neat towers",
        chore="stacked seed packets and brushed the last soil from the table",
        ending_image="the clay pots stood in quiet rows, each one round as a tucked-in pillow",
        allowed_responses=("lantern_peek", "wait_and_watch", "steady_the_tray"),
    ),
    "seedling_station": StationArea(
        key="seedling_station",
        phrase="the seedling station under the warm lamps",
        cozy_detail="tiny sprouts leaned toward the last gold light as if they were listening for a lullaby",
        chore="checked the small seedling flats and straightened their labels",
        ending_image="the seedling trays glowed softly, as calm as babies sleeping under blankets",
        allowed_responses=("lantern_peek", "wait_and_watch", "steady_the_tray"),
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "hedgehog_crate": Mystery(
        key="hedgehog_crate",
        label="the leaf crate",
        origin_phrase="under the leaf crate",
        noise_phrase="a papery rustle, then silence, then another rustle",
        truth="a tiny hedgehog curled in the leaves, blinking up with a dark, shiny nose",
        why_here="the leaves were warm, still, and soft enough for a nervous little traveler",
        final_fix="The crate was rolled to a quiet corner, and a shallow saucer of water was left nearby.",
        final_image="The rustling turned into one sleepy snuffle inside the leaves.",
        compatible_responses=("lantern_peek", "wait_and_watch"),
        stations=("potting_station", "seedling_station"),
    ),
    "drip_hose": Mystery(
        key="drip_hose",
        label="the watering rail",
        origin_phrase="behind the watering rail",
        noise_phrase="a soft tap-tap, like pebbles clicking inside a teacup",
        truth="a loose hose coupler flicking the rail each time one last drop slipped through",
        why_here="the final watering had left a stubborn bead of water in the line",
        final_fix="The little brass valve was turned a careful quarter-step until the line settled.",
        final_image="The tap-tap disappeared, and only the pebble trays glittered in the still air.",
        compatible_responses=("listen_for_drips", "close_valve"),
        stations=("watering_station",),
    ),
    "tag_tray": Mystery(
        key="tag_tray",
        label="the basil tray",
        origin_phrase="beneath a basil tray",
        noise_phrase="a tiny tick-tick, as if a pencil were knocking in its sleep",
        truth="a wooden plant tag rocking against the tray rim after slipping loose",
        why_here="the evening fan had made the tray tremble just enough to wake the tag",
        final_fix="The tag was tucked back into the soil, and the tray was squared on the table again.",
        final_image="The basil leaves stopped shivering and gave off a sweet, sleepy smell.",
        compatible_responses=("lantern_peek", "steady_the_tray"),
        stations=("potting_station", "seedling_station"),
    ),
}

RESPONSES: dict[str, ResponsePlan] = {
    "lantern_peek": ResponsePlan(
        key="lantern_peek",
        phrase="lift a honey-colored lantern and peek gently",
        action_text=(
            "{helper} raised the little honey-colored lantern, and {hero} bent low without grabbing or stomping. "
            "The warm circle of light stayed small and calm."
        ),
        safe_reason="It uses slow light instead of quick hands, so hidden things are not startled.",
    ),
    "wait_and_watch": ResponsePlan(
        key="wait_and_watch",
        phrase="stand still and wait for the sound to speak again",
        action_text=(
            "{hero} folded both hands, took three slow breaths, and waited with {helper} beside the station table. "
            "Nothing was touched until the sound returned on its own."
        ),
        safe_reason="It lets the cause reveal itself instead of turning a small mystery into a bigger fright.",
    ),
    "listen_for_drips": ResponsePlan(
        key="listen_for_drips",
        phrase="kneel beside the rail and listen for the next drip",
        action_text=(
            "{hero} knelt beside the rail while {helper} counted softly. "
            "Together they listened for the exact place where the next drop would land."
        ),
        safe_reason="It follows the sound to its source before anyone twists or pulls the watering line.",
    ),
    "close_valve": ResponsePlan(
        key="close_valve",
        phrase="steady the hose and turn the brass valve a little",
        action_text=(
            "{helper} steadied the hose while {hero} turned the brass valve only a little, just as carefully as closing a music box. "
            "The motion was slow enough to stop the tapping without splashing anything."
        ),
        safe_reason="It matches a watering problem with a gentle watering fix, not a rushed guess.",
    ),
    "steady_the_tray": ResponsePlan(
        key="steady_the_tray",
        phrase="hold the tray still and tuck the loose piece back in place",
        action_text=(
            "{hero} held the tray still with two careful hands while {helper} checked the edge of the soil. "
            "They moved so softly that even the basil leaves barely trembled."
        ),
        safe_reason="It calms the shaking object first, which prevents more clattering.",
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Lila", "Tessa", "Nora"),
    "boy": ("Eli", "Theo", "Ravi", "Jonah"),
}

HELPERS = ("Auntie Rose", "Grandpa Sol", "Mama June", "Uncle Ben")


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[gender])


def _pick_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)


def valid_combo(station_key: str, mystery_key: str, response_key: str) -> bool:
    if station_key not in STATIONS or mystery_key not in MYSTERIES or response_key not in RESPONSES:
        return False
    station = STATIONS[station_key]
    mystery = MYSTERIES[mystery_key]
    return (
        station_key in mystery.stations
        and response_key in station.allowed_responses
        and response_key in mystery.compatible_responses
    )


def invalid_reason(station_key: str, mystery_key: str, response_key: str) -> str:
    if station_key not in STATIONS:
        return f"No story: unknown station {station_key!r}."
    if mystery_key not in MYSTERIES:
        return f"No story: unknown mystery {mystery_key!r}."
    if response_key not in RESPONSES:
        return f"No story: unknown response {response_key!r}."

    station = STATIONS[station_key]
    mystery = MYSTERIES[mystery_key]
    response = RESPONSES[response_key]

    if station_key not in mystery.stations:
        station_list = ", ".join(mystery.stations)
        return (
            f"No story: {mystery.label} does not belong at {station.phrase}. "
            f"It only fits: {station_list}."
        )
    if response_key not in station.allowed_responses:
        return (
            f"No story: {station.phrase} does not support the response {response_key!r}. "
            f"Try one of: {', '.join(station.allowed_responses)}."
        )
    if response_key not in mystery.compatible_responses:
        return (
            f"No story: {response.phrase} does not sensibly solve the sound from {mystery.origin_phrase}. "
            f"Use one of: {', '.join(mystery.compatible_responses)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for station_key in sorted(STATIONS):
        for mystery_key in sorted(MYSTERIES):
            for response_key in sorted(RESPONSES):
                if valid_combo(station_key, mystery_key, response_key):
                    combos.append((station_key, mystery_key, response_key))
    return combos


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random(args.seed + index)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(gender, rng)
    helper = args.helper or _pick_helper(rng)
    station_key, mystery_key, response_key = combo
    return StoryParams(
        station=station_key,
        mystery=mystery_key,
        response=response_key,
        hero=hero,
        gender=gender,
        helper=helper,
        seed=args.seed + index,
    )


def build_world(params: StoryParams) -> World:
    station_cfg = STATIONS[params.station]
    mystery_cfg = MYSTERIES[params.mystery]
    response_cfg = RESPONSES[params.response]
    world = World(
        params=params,
        station_cfg=station_cfg,
        mystery_cfg=mystery_cfg,
        response_cfg=response_cfg,
    )

    hero_kind = params.gender
    hero = world.add(
        Entity(
            name=params.hero,
            kind=hero_kind,
            phrase=f"little {hero_kind}",
            location="garden_center",
            meters={"steps": 0.0, "distance_to_sound": 2.0},
            memes={"calm": 0.8, "curiosity": 0.7, "worry": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="adult",
            phrase="trusted grown-up",
            location="garden_center",
            meters={"steadiness": 1.0},
            memes={"calm": 1.2, "care": 1.0},
        )
    )
    world.add(
        Entity(
            name=station_cfg.key,
            kind="station",
            phrase=station_cfg.phrase,
            location="garden_center",
            meters={"lamp_glow": 0.8, "quiet": 0.7},
            memes={"cozy": 1.0},
        )
    )
    world.add(
        Entity(
            name=mystery_cfg.key,
            kind="mystery",
            phrase=mystery_cfg.label,
            location=station_cfg.key,
            meters={"hidden": 1.0, "sound": 1.0, "resolved": 0.0},
            memes={"uncertainty": 1.0},
        )
    )

    world.facts.update(
        {
            "setting": "garden_center",
            "style": "bedtime_story",
            "feature": "suspense",
            "seed_word": "station",
            "hero": hero.name,
            "helper": helper.name,
            "station": station_cfg.key,
            "mystery": mystery_cfg.key,
            "response": response_cfg.key,
            "seed": str(params.seed),
        }
    )
    world.fired.append(f"opening_at_{station_cfg.key}")
    return world


def _hero(world: World) -> Entity:
    return world.get(world.params.hero)


def _helper(world: World) -> Entity:
    return world.get(world.params.helper)


def _mystery_ent(world: World) -> Entity:
    return world.get(world.mystery_cfg.key)


def _station_ent(world: World) -> Entity:
    return world.get(world.station_cfg.key)


def _introduce(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    station = world.station_cfg
    world.say(
        f"One evening, {hero.name} went with {helper.name} to {GARDEN_CENTER_NAME} for one last bedtime chore. "
        f"They were working at {station.phrase}, where {station.cozy_detail}."
    )
    world.say(
        f"{hero.name} liked how the whole garden center seemed to yawn at closing time. "
        f"It was the kind of place where even the watering cans looked ready for sleep."
    )


def _raise_suspense(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    mystery_cfg = world.mystery_cfg
    mystery_ent = _mystery_ent(world)
    station_ent = _station_ent(world)

    hero.memes["worry"] += 1.0
    hero.memes["curiosity"] += 0.4
    mystery_ent.meters["sound"] = 1.3
    station_ent.meters["quiet"] = 0.2
    world.fired.append(f"heard_{mystery_cfg.key}")

    world.para()
    world.say(
        f"Then a sound came from {mystery_cfg.origin_phrase}. "
        f"It was {mystery_cfg.noise_phrase}, and for a moment the whole station felt as if it were holding its breath."
    )
    world.say(
        f"{hero.name} stopped in the middle of the chore and edged closer to {helper.name}. "
        f"{helper.name} whispered that little sounds can feel large in the evening, so the best clue is a calm clue."
    )


def _apply_response(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    response = world.response_cfg
    station_ent = _station_ent(world)

    hero.memes["worry"] = max(0.2, hero.memes["worry"] - 0.3)
    hero.memes["curiosity"] += 0.5
    helper.memes["care"] += 0.2
    station_ent.meters["lamp_glow"] += 0.1
    world.fired.append(f"used_{response.key}")

    world.para()
    world.say(response.action_text.format(hero=hero.name, helper=helper.name))
    world.say(response.safe_reason)


def _reveal(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    mystery_cfg = world.mystery_cfg
    mystery_ent = _mystery_ent(world)
    response_key = world.response_cfg.key

    mystery_ent.meters["hidden"] = 0.0
    mystery_ent.meters["resolved"] = 0.6
    hero.memes["relief"] += 0.8
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.6)
    world.fired.append(f"revealed_{mystery_cfg.key}")

    if mystery_cfg.key == "hedgehog_crate":
        if response_key == "lantern_peek":
            world.say(
                f"In the lantern glow, {mystery_cfg.truth}. "
                f"It had hidden there because {mystery_cfg.why_here}."
            )
        else:
            world.say(
                f"After three quiet breaths, {mystery_cfg.truth}. "
                f"It had hidden there because {mystery_cfg.why_here}."
            )
        return

    if mystery_cfg.key == "drip_hose":
        if response_key == "listen_for_drips":
            world.say(
                f"On the next drop, they found the answer: {mystery_cfg.truth}. "
                f"The little noise existed because {mystery_cfg.why_here}."
            )
        else:
            world.say(
                f"As soon as the valve slowed the line, the answer showed itself: {mystery_cfg.truth}. "
                f"The little noise existed because {mystery_cfg.why_here}."
            )
        return

    if mystery_cfg.key == "tag_tray":
        if response_key == "steady_the_tray":
            world.say(
                f"Once the tray stopped wobbling, they saw the answer: {mystery_cfg.truth}. "
                f"The tiny ticking had started because {mystery_cfg.why_here}."
            )
        else:
            world.say(
                f"In the small lantern circle, they saw the answer: {mystery_cfg.truth}. "
                f"The tiny ticking had started because {mystery_cfg.why_here}."
            )
        return

    raise StoryError(f"No reveal logic for mystery {mystery_cfg.key!r}.")


def _resolve(world: World) -> None:
    hero = _hero(world)
    mystery_cfg = world.mystery_cfg
    mystery_ent = _mystery_ent(world)
    station = world.station_cfg
    station_ent = _station_ent(world)

    mystery_ent.meters["sound"] = 0.0
    mystery_ent.meters["resolved"] = 1.0
    station_ent.meters["quiet"] = 1.1
    hero.memes["calm"] += 0.8
    hero.memes["relief"] += 0.8
    world.fired.append(f"resolved_{mystery_cfg.key}")

    world.para()
    world.say(mystery_cfg.final_fix)
    world.say(mystery_cfg.final_image)
    world.say(
        f"When the last lamp clicked off, {station.ending_image}. "
        f"{hero.name} carried that calm picture home and tucked it into bedtime."
    )


def simulate(world: World) -> World:
    _introduce(world)
    _raise_suspense(world)
    _apply_response(world)
    _reveal(world)
    _resolve(world)
    return world


def _prompts(world: World) -> list[str]:
    station = world.station_cfg
    mystery = world.mystery_cfg
    response = world.response_cfg
    return [
        f"Write a bedtime story set in a garden center at {station.phrase}.",
        f"Include the word station and build gentle suspense around a sound from {mystery.origin_phrase}.",
        f"Resolve the mystery by having the child {response.phrase} and end on a sleepy closing image.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    helper = world.params.helper
    station = world.station_cfg
    mystery = world.mystery_cfg
    response = world.response_cfg
    return [
        QAItem(
            "What made the garden center feel suspenseful?",
            f"The suspense began when a sound came from {mystery.origin_phrase} at {station.phrase}. "
            f"Because {hero} could hear the noise before seeing its cause, the familiar garden center briefly felt secret and strange.",
        ),
        QAItem(
            f"How did {hero} investigate without making the mystery worse?",
            f"{hero} chose to {response.phrase} with {helper}. "
            f"That method matched the place and the problem, so the search stayed gentle instead of rushed.",
        ),
        QAItem(
            "What was really making the sound?",
            f"The sound was really caused by {mystery.truth}. "
            f"It was there because {mystery.why_here}, which turned the scary guess into an ordinary answer.",
        ),
        QAItem(
            "How did the ending prove the problem was over?",
            f"The ending showed calm because {mystery.final_image.lower()} "
            f"Then {station.ending_image}, so the whole station felt settled again.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    station = world.station_cfg
    mystery = world.mystery_cfg
    response = world.response_cfg
    return [
        QAItem(
            f"Why is {response.key} allowed at {station.key}?",
            f"It is allowed because {station.phrase} supports that kind of slow, careful investigation. "
            f"The response also fits the physical source of the sound coming from {mystery.origin_phrase}.",
        ),
        QAItem(
            "Why would a mismatched response be rejected in this world?",
            f"A mismatched response could ignore the actual object that is making the sound. "
            f"The gate rejects it so the story keeps a believable cause, method, and result.",
        ),
        QAItem(
            "What physical thing carries the suspense here?",
            f"The suspense rides on a real object in the garden center, not on a floating feeling by itself. "
            f"In this sample, the sound comes from {mystery.label}, which is why the reveal can be grounded and concrete.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.station, params.mystery, params.response):
        raise StoryError(invalid_reason(params.station, params.mystery, params.response))

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
combo(S,M,R) :-
    station(S),
    mystery(M),
    response(R),
    mystery_at(M,S),
    station_allows(S,R),
    mystery_allows(M,R).

ok :- chosen(S,M,R), combo(S,M,R).

#show combo/3.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for station_key, station in sorted(STATIONS.items()):
        rows.append(fact("station", station_key))
        for response_key in station.allowed_responses:
            rows.append(fact("station_allows", station_key, response_key))
    for mystery_key, mystery in sorted(MYSTERIES.items()):
        rows.append(fact("mystery", mystery_key))
        for station_key in mystery.stations:
            rows.append(fact("mystery_at", mystery_key, station_key))
        for response_key in mystery.compatible_responses:
            rows.append(fact("mystery_allows", mystery_key, response_key))
    for response_key in sorted(RESPONSES):
        rows.append(fact("response", response_key))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.station, params.mystery, params.response) + "\n"
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
            station=combo[0],
            mystery=combo[1],
            response=combo[2],
            hero=HERO_NAMES["girl"][0],
            gender="girl",
            helper=HELPERS[0],
            seed=index,
        )
        if not _asp_accepts(params):
            raise StoryError(f"ASP failed to accept valid combo {combo!r}.")

        sample = generate(params)
        if "garden center" not in sample.story.lower():
            raise StoryError(f"Generated story for {combo!r} forgot the garden center setting.")
        if "station" not in sample.story.lower():
            raise StoryError(f"Generated story for {combo!r} forgot the seed word 'station'.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated story for {combo!r} leaked a template field.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} is missing a full beginning, turn, or ending.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated story for {combo!r} has the wrong number of prompts.")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo!r} has incomplete QA sets.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer is too thin for {combo!r}: {qa.question!r}")
        for qa in sample.world_qa:
            if not qa.answer.endswith("."):
                raise StoryError(f"World QA answer is malformed for {combo!r}: {qa.question!r}")

    return f"OK: {len(python_set)} valid combos; ASP parity holds; generated stories pass quality checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate garden-center suspense bedtime stories.")
    parser.add_argument("--station", choices=sorted(STATIONS), default=None)
    parser.add_argument("--mystery", choices=sorted(MYSTERIES), default=None)
    parser.add_argument("--response", choices=sorted(RESPONSES), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
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
        if (args.station is None or combo[0] == args.station)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.response is None or combo[2] == args.response)
    ]
    if args.station and args.mystery and args.response and not filtered:
        raise StoryError(invalid_reason(args.station, args.mystery, args.response))
    if not filtered:
        if args.station or args.mystery or args.response:
            raise StoryError("No story: no valid station/mystery/response combination matches the requested filters.")
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
    for station_key, mystery_key, response_key in sorted(asp_valid_combos()):
        print(f"{station_key}\t{mystery_key}\t{response_key}")


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
                header = f"### {p.station} / {p.mystery} / {p.response}"
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
