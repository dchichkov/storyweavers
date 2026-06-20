#!/usr/bin/env python3
"""
storyworlds/worlds/station_garden_center_suspense_bedtime_story_2.py
====================================================================

Bedtime-story storyworld for a garden-center suspense seed.

Internal source tale
--------------------
At closing time in a garden center, a child helps a trusted grown-up finish a
small chore at one station. A tiny hidden sound breaks the calm. Instead of
rushing, they use one gentle, station-appropriate method to investigate, find
the ordinary cause, and end with a sleepy image that proves the station is safe
and quiet again.
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


GARDEN_CENTER_NAME = "Duskpetal Garden Center"


@dataclass(frozen=True)
class StationArea:
    key: str
    phrase: str
    night_detail: str
    closing_task: str
    ending_image: str
    allowed_methods: tuple[str, ...]


@dataclass(frozen=True)
class MysteryCause:
    key: str
    label: str
    source_phrase: str
    sound_phrase: str
    truth: str
    cause_reason: str
    fix_text: str
    settled_image: str
    compatible_methods: tuple[str, ...]
    stations: tuple[str, ...]


@dataclass(frozen=True)
class MethodPlan:
    key: str
    phrase: str
    action_text: str
    safety_reason: str


@dataclass
class StoryParams:
    station: str
    mystery: str
    method: str
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
class Beat:
    key: str
    text: str


@dataclass
class World:
    params: StoryParams
    station_cfg: StationArea
    mystery_cfg: MysteryCause
    method_cfg: MethodPlan
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[Beat] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

    def note(self, key: str, text: str) -> None:
        self.history.append(Beat(key=key, text=text))

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  station={self.station_cfg.key}")
        rows.append(f"  mystery={self.mystery_cfg.key}")
        rows.append(f"  method={self.method_cfg.key}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name}<{ent.kind}> location={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append("  history=")
        for beat in self.history:
            rows.append(f"    - {beat.key}: {beat.text}")
        return "\n".join(rows)


STATIONS: dict[str, StationArea] = {
    "misting_station": StationArea(
        key="misting_station",
        phrase="the misting station beside the fern tunnel",
        night_detail=(
            "the fern fronds held cool pearls of water, and the brass pipes glimmered "
            "softly under the glass roof"
        ),
        closing_task="wipe the mist timer and count the little spray nozzles",
        ending_image="the fern tunnel shone with still silver beads, as if the leaves were already dreaming",
        allowed_methods=("listen_for_pulse", "turn_sleep_knob"),
    ),
    "potting_station": StationArea(
        key="potting_station",
        phrase="the potting station near the clay shelves",
        night_detail=(
            "round terracotta pots waited in neat towers, and the dark soil smelled warm and sleepy"
        ),
        closing_task="brush the last crumbs of soil from the table and line up the herb carts",
        ending_image="the clay pots sat moon-round and quiet, each one tucked into its place",
        allowed_methods=("lantern_peek", "steady_cart"),
    ),
    "seed_counter_station": StationArea(
        key="seed_counter_station",
        phrase="the seed-counter station beside the drawer wall",
        night_detail=(
            "tiny paper seed envelopes rested in shallow trays, and the labels looked like rows of bedtime notes"
        ),
        closing_task="count seed scoops and press the little drawers shut one by one",
        ending_image="the drawer wall rested in straight rows, calm as a shelf full of sleeping blocks",
        allowed_methods=("listen_for_pulse", "lantern_peek", "steady_cart", "close_drawer_slowly"),
    ),
}

MYSTERIES: dict[str, MysteryCause] = {
    "timer_click": MysteryCause(
        key="timer_click",
        label="the mist rail",
        source_phrase="behind the mist rail",
        sound_phrase="a patient tick...tick...ting that seemed to hide between the pipes",
        truth="a brass mist timer nudging the pipe whenever the last drop shivered through it",
        cause_reason="the watering line still held one stubborn bead, and the timer arm was loose enough to tap",
        fix_text="Together they turned the timer to its tiny moon mark until the pipe grew still.",
        settled_image="The ticking folded away, and the fern tunnel breathed in silence again.",
        compatible_methods=("listen_for_pulse", "turn_sleep_knob"),
        stations=("misting_station",),
    ),
    "copper_tag": MysteryCause(
        key="copper_tag",
        label="the herb cart",
        source_phrase="under a rosemary cart",
        sound_phrase="a light ting-ting, as if a spoon were ringing inside its sleep",
        truth="a copper plant tag brushing the cart wheel whenever the evening fan sighed",
        cause_reason="the cart had rolled a finger-width sideways, and the loose tag could just reach the spoke",
        fix_text="They held the cart still and tucked the copper tag back into the rosemary pot.",
        settled_image="The tinging stopped, and the rosemary sent out a warm, drowsy smell.",
        compatible_methods=("lantern_peek", "steady_cart"),
        stations=("potting_station", "seed_counter_station"),
    ),
    "seed_scoop": MysteryCause(
        key="seed_scoop",
        label="the drawer wall",
        source_phrase="inside one half-shut seed drawer",
        sound_phrase="a hush-tik, hush-tik, like a pencil whispering against wood",
        truth="a seed scoop handle sliding against a divider inside a crooked drawer",
        cause_reason="one drawer had closed a little sideways after the last counting game",
        fix_text="The crooked drawer was guided shut with two slow hands until it rested square in its frame.",
        settled_image="The drawers settled without a murmur, each one tucked neatly into line.",
        compatible_methods=("listen_for_pulse", "close_drawer_slowly"),
        stations=("seed_counter_station",),
    ),
}

METHODS: dict[str, MethodPlan] = {
    "listen_for_pulse": MethodPlan(
        key="listen_for_pulse",
        phrase="stand still and listen for the next tiny pulse",
        action_text=(
            "{hero} and {helper} stood so still that they could hear the lamps hum. "
            "They waited for the sound to repeat before moving at all."
        ),
        safety_reason=(
            "Waiting let the sound point to its own hiding place, which kept the search gentle and true."
        ),
    ),
    "turn_sleep_knob": MethodPlan(
        key="turn_sleep_knob",
        phrase="follow the pipe and turn the sleep knob one careful step",
        action_text=(
            "With {helper} holding the pipe steady, {hero} followed the ticking to the brass timer "
            "and turned its sleep knob only one careful step."
        ),
        safety_reason=(
            "The knob belonged to the watering line, so the fix matched the object that was speaking."
        ),
    ),
    "lantern_peek": MethodPlan(
        key="lantern_peek",
        phrase="lift the paper lantern and peek under the shadows",
        action_text=(
            "{helper} lifted the small paper lantern while {hero} bent close enough to look, "
            "but not close enough to bump the shelves. The light stayed warm and narrow."
        ),
        safety_reason=(
            "A small lantern reveals shape without turning the quiet station into a scramble."
        ),
    ),
    "steady_cart": MethodPlan(
        key="steady_cart",
        phrase="hold the cart still before touching anything else",
        action_text=(
            "{hero} placed two careful hands on the cart while {helper} watched the wheels. "
            "Once the rattling stopped, they checked what had been brushing the metal."
        ),
        safety_reason=(
            "Steadying the moving object first prevents extra clatter and shows which piece was loose."
        ),
    ),
    "close_drawer_slowly": MethodPlan(
        key="close_drawer_slowly",
        phrase="follow the whisper to the drawer and close it slowly",
        action_text=(
            "{hero} traced the whispering sound to the drawer wall while {helper} kept one finger beneath the handle. "
            "Together they eased the crooked drawer inward until the wood sat square."
        ),
        safety_reason=(
            "A slow close fits a crooked drawer and keeps hidden packets from spilling."
        ),
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Lila", "Tessa", "Nora"),
    "boy": ("Eli", "Theo", "Ravi", "Jonah"),
}

HELPERS = ("Auntie Fern", "Grandpa Reed", "Mama Wren", "Uncle Moss")


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[gender])


def _pick_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)


def valid_combo(station_key: str, mystery_key: str, method_key: str) -> bool:
    if station_key not in STATIONS or mystery_key not in MYSTERIES or method_key not in METHODS:
        return False
    station = STATIONS[station_key]
    mystery = MYSTERIES[mystery_key]
    return (
        station_key in mystery.stations
        and method_key in station.allowed_methods
        and method_key in mystery.compatible_methods
    )


def invalid_reason(station_key: str, mystery_key: str, method_key: str) -> str:
    if station_key not in STATIONS:
        return f"No story: unknown station {station_key!r}."
    if mystery_key not in MYSTERIES:
        return f"No story: unknown mystery {mystery_key!r}."
    if method_key not in METHODS:
        return f"No story: unknown method {method_key!r}."

    station = STATIONS[station_key]
    mystery = MYSTERIES[mystery_key]
    method = METHODS[method_key]

    if station_key not in mystery.stations:
        return (
            f"No story: {mystery.label} does not belong at {station.phrase}. "
            f"It only fits: {', '.join(mystery.stations)}."
        )
    if method_key not in station.allowed_methods:
        return (
            f"No story: {station.phrase} does not support {method_key!r}. "
            f"Try one of: {', '.join(station.allowed_methods)}."
        )
    if method_key not in mystery.compatible_methods:
        return (
            f"No story: {method.phrase} does not sensibly solve the sound from {mystery.source_phrase}. "
            f"Use one of: {', '.join(mystery.compatible_methods)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for station_key in sorted(STATIONS):
        for mystery_key in sorted(MYSTERIES):
            for method_key in sorted(METHODS):
                if valid_combo(station_key, mystery_key, method_key):
                    combos.append((station_key, mystery_key, method_key))
    return combos


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    index: int = 0,
) -> StoryParams:
    seed = args.seed + index
    rng = random.Random(seed)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(gender, rng)
    helper = args.helper or _pick_helper(rng)
    return StoryParams(
        station=combo[0],
        mystery=combo[1],
        method=combo[2],
        hero=hero,
        gender=gender,
        helper=helper,
        seed=seed,
    )


def build_world(params: StoryParams) -> World:
    station_cfg = STATIONS[params.station]
    mystery_cfg = MYSTERIES[params.mystery]
    method_cfg = METHODS[params.method]
    world = World(
        params=params,
        station_cfg=station_cfg,
        mystery_cfg=mystery_cfg,
        method_cfg=method_cfg,
    )

    hero = world.add(
        Entity(
            name=params.hero,
            kind=params.gender,
            phrase=f"little {params.gender}",
            location="garden_center",
            meters={"steps": 0.0, "distance_to_sound": 2.2},
            memes={"calm": 0.9, "curiosity": 0.7, "worry": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="adult",
            phrase="trusted grown-up",
            location="garden_center",
            meters={"steadiness": 1.2},
            memes={"calm": 1.3, "care": 1.1},
        )
    )
    station = world.add(
        Entity(
            name=station_cfg.key,
            kind="station",
            phrase=station_cfg.phrase,
            location="garden_center",
            meters={"quiet": 0.9, "lamp_glow": 0.8},
            memes={"cozy": 1.1},
        )
    )
    source = world.add(
        Entity(
            name=mystery_cfg.key,
            kind="physical_cause",
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
            "garden_center": GARDEN_CENTER_NAME,
            "hero": hero.name,
            "helper": helper.name,
            "station": station_cfg.key,
            "mystery": mystery_cfg.key,
            "method": method_cfg.key,
            "task": station_cfg.closing_task,
        }
    )
    world.note("opening", f"{hero.name} begins the closing chore at {station.phrase}.")
    world.note("carrier", f"The suspense is carried by {source.phrase} at the station.")
    return world


def _hero(world: World) -> Entity:
    return world.get(world.params.hero)


def _helper(world: World) -> Entity:
    return world.get(world.params.helper)


def _station(world: World) -> Entity:
    return world.get(world.station_cfg.key)


def _source(world: World) -> Entity:
    return world.get(world.mystery_cfg.key)


def _introduce(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    station = world.station_cfg

    world.say(
        f"One dusky evening, {hero.name} stayed with {helper.name} at {GARDEN_CENTER_NAME} "
        f"to finish the last small chore at {station.phrase}. Around them, {station.night_detail}."
    )
    world.say(
        f"{hero.name}'s job was to {station.closing_task}. "
        f"It felt nice to help the station get ready for sleep."
    )


def _raise_suspense(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    station = _station(world)
    source = _source(world)
    mystery = world.mystery_cfg

    hero.memes["worry"] += 1.0
    hero.memes["curiosity"] += 0.4
    hero.meters["steps"] += 0.6
    hero.meters["distance_to_sound"] = 1.4
    station.meters["quiet"] = 0.2
    source.meters["sound"] = 1.3
    source.memes["uncertainty"] = 1.2
    world.facts["sound"] = mystery.sound_phrase
    world.note("disturbance", f"A sound starts at {mystery.source_phrase}.")

    world.para()
    world.say(
        f"Then the calm broke. From {mystery.source_phrase} came {mystery.sound_phrase}, "
        f"and the whole station seemed to hold its breath."
    )
    world.say(
        f"{hero.name} moved close to {helper.name} and listened again. "
        f"{helper.name} whispered that evening sounds can feel bigger before their true shape is known."
    )


def _apply_method(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    station = _station(world)
    source = _source(world)
    method = world.method_cfg

    hero.memes["worry"] = max(0.25, hero.memes["worry"] - 0.2)
    hero.memes["curiosity"] += 0.5
    helper.memes["care"] += 0.2
    station.meters["lamp_glow"] += 0.1
    source.meters["sound"] = 1.1
    world.facts["method_phrase"] = method.phrase
    world.note("method", f"{hero.name} and {helper.name} choose to {method.phrase}.")

    world.para()
    world.say(method.action_text.format(hero=hero.name, helper=helper.name))
    world.say(method.safety_reason)


def _reveal(world: World) -> None:
    mystery = world.mystery_cfg
    method = world.method_cfg
    hero = _hero(world)
    source = _source(world)

    source.meters["hidden"] = 0.0
    source.meters["resolved"] = 0.6
    hero.memes["relief"] += 0.7
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    world.facts["truth"] = mystery.truth
    world.facts["why"] = mystery.cause_reason
    world.note("reveal", f"The sound is revealed as {mystery.truth}.")

    world.para()
    if mystery.key == "timer_click":
        if method.key == "turn_sleep_knob":
            world.say(
                f"As the knob settled, the truth showed itself: {mystery.truth}. "
                f"It had sounded mysterious only because {mystery.cause_reason}."
            )
        else:
            world.say(
                f"On the next small tick, they found the answer: {mystery.truth}. "
                f"It had sounded mysterious only because {mystery.cause_reason}."
            )
        return

    if mystery.key == "copper_tag":
        if method.key == "steady_cart":
            world.say(
                f"Once the wheel stopped wobbling, they saw the answer: {mystery.truth}. "
                f"The gentle ringing had begun because {mystery.cause_reason}."
            )
        else:
            world.say(
                f"In the lantern's warm pocket of light, they found the answer: {mystery.truth}. "
                f"The gentle ringing had begun because {mystery.cause_reason}."
            )
        return

    if mystery.key == "seed_scoop":
        if method.key == "close_drawer_slowly":
            world.say(
                f"As the drawer moved square, the answer came with it: {mystery.truth}. "
                f"The whispering had started because {mystery.cause_reason}."
            )
        else:
            world.say(
                f"After one more hush-tik, they understood the sound: {mystery.truth}. "
                f"The whispering had started because {mystery.cause_reason}."
            )
        return

    raise StoryError(f"No reveal logic for mystery {mystery.key!r}.")


def _resolve(world: World) -> None:
    hero = _hero(world)
    station = _station(world)
    source = _source(world)
    mystery = world.mystery_cfg

    source.meters["sound"] = 0.0
    source.meters["resolved"] = 1.0
    source.memes["uncertainty"] = 0.0
    station.meters["quiet"] = 1.2
    hero.memes["calm"] += 0.8
    hero.memes["relief"] += 0.8
    hero.meters["distance_to_sound"] = 0.3
    world.facts["fix"] = mystery.fix_text
    world.facts["ending_image"] = world.station_cfg.ending_image
    world.note("resolution", mystery.fix_text)

    world.para()
    world.say(mystery.fix_text)
    world.say(mystery.settled_image)
    world.say(
        f"When the last lamp clicked low, {world.station_cfg.ending_image}. "
        f"{hero.name} carried that picture home the way some children carry a night-light."
    )


def simulate(world: World) -> World:
    _introduce(world)
    _raise_suspense(world)
    _apply_method(world)
    _reveal(world)
    _resolve(world)
    return world


def _prompts(world: World) -> list[str]:
    station = world.station_cfg
    mystery = world.mystery_cfg
    method = world.method_cfg
    return [
        f"Write a bedtime story set in a garden center at {station.phrase}.",
        f"Include the word station and build gentle suspense around a sound from {mystery.source_phrase}.",
        f"Resolve the sound by having the child {method.phrase} and end on a sleepy image that proves the station is calm again.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    helper = world.params.helper
    station = world.station_cfg
    mystery = world.mystery_cfg
    method = world.method_cfg
    return [
        QAItem(
            "What first made the station feel suspenseful?",
            f"The suspense began when a hidden sound came from {mystery.source_phrase} at {station.phrase}. "
            f"Because {hero} could hear it before seeing its cause, the familiar garden center suddenly felt secret for a moment.",
        ),
        QAItem(
            f"How did {hero} investigate without making the problem bigger?",
            f"{hero} chose to {method.phrase} with {helper}. "
            f"That method matched the place and the object, so the search stayed careful instead of turning into a rush.",
        ),
        QAItem(
            "What was actually making the sound, and why?",
            f"The sound was really {mystery.truth}. "
            f"It happened because {mystery.cause_reason}, which turned the suspense into an ordinary answer.",
        ),
        QAItem(
            "How does the ending prove the station is peaceful again?",
            f"The problem is over because {mystery.fix_text.lower()} "
            f"After that, {mystery.settled_image.lower()}",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    station = world.station_cfg
    mystery = world.mystery_cfg
    method = world.method_cfg
    return [
        QAItem(
            f"Why is {method.key} a reasonable method at {station.key}?",
            f"It is reasonable because {station.phrase} contains the kind of object that method handles safely. "
            f"It also fits the actual sound source at {mystery.source_phrase}, so cause and response stay aligned.",
        ),
        QAItem(
            "What physical thing carries the suspense in this world?",
            f"The suspense rides on a real object inside the garden center instead of on a floating feeling. "
            f"In this sample, that object is {mystery.label}, which is why the reveal can stay concrete and answerable.",
        ),
        QAItem(
            "How does this world keep suspense gentle enough for a bedtime story?",
            f"It keeps the suspense gentle by using a small sound, a trusted helper, and a slow method instead of a shock. "
            f"The ending then proves calm has returned with a visible station image rather than a vague promise.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.helper:
        raise StoryError("No story: hero and helper need different names.")
    if not valid_combo(params.station, params.mystery, params.method):
        raise StoryError(invalid_reason(params.station, params.mystery, params.method))

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
combo(S,M,P) :-
    station(S),
    mystery(M),
    method(P),
    mystery_at(M,S),
    station_allows(S,P),
    mystery_allows(M,P).

ok :- chosen(S,M,P), combo(S,M,P).

#show combo/3.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for station_key, station in sorted(STATIONS.items()):
        rows.append(fact("station", station_key))
        for method_key in station.allowed_methods:
            rows.append(fact("station_allows", station_key, method_key))
    for mystery_key, mystery in sorted(MYSTERIES.items()):
        rows.append(fact("mystery", mystery_key))
        for station_key in mystery.stations:
            rows.append(fact("mystery_at", mystery_key, station_key))
        for method_key in mystery.compatible_methods:
            rows.append(fact("mystery_allows", mystery_key, method_key))
    for method_key in sorted(METHODS):
        rows.append(fact("method", method_key))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.station, params.mystery, params.method) + "\n"
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
            method=combo[2],
            hero=HERO_NAMES["girl"][0],
            gender="girl",
            helper=HELPERS[0],
            seed=index,
        )
        if not _asp_accepts(params):
            raise StoryError(f"ASP failed to accept valid combo {combo!r}.")

        sample = generate(params)
        story_lc = sample.story.lower()
        if "garden center" not in story_lc:
            raise StoryError(f"Generated story for {combo!r} forgot the garden center setting.")
        if "station" not in story_lc:
            raise StoryError(f"Generated story for {combo!r} forgot the seed word 'station'.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated story for {combo!r} leaked a template field.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} is missing a full beginning, turn, or ending.")
        if not sample.story.rstrip().endswith("."):
            raise StoryError(f"Generated story for {combo!r} does not end cleanly.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated story for {combo!r} has the wrong number of prompts.")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo!r} has incomplete QA sets.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer is too thin for {combo!r}: {qa.question!r}")
        for qa in sample.world_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"World QA answer is too thin for {combo!r}: {qa.question!r}")

    return f"OK: {len(python_set)} valid combos; ASP parity holds; generated stories pass quality checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate suspense bedtime stories in a garden center station world.")
    parser.add_argument("--station", choices=sorted(STATIONS), default=None)
    parser.add_argument("--mystery", choices=sorted(MYSTERIES), default=None)
    parser.add_argument("--method", choices=sorted(METHODS), default=None)
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
        and (args.method is None or combo[2] == args.method)
    ]
    if args.station and args.mystery and args.method and not filtered:
        raise StoryError(invalid_reason(args.station, args.mystery, args.method))
    if not filtered:
        if args.station or args.mystery or args.method:
            raise StoryError("No story: no valid station/mystery/method combination matches the requested filters.")
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
    for station_key, mystery_key, method_key in sorted(asp_valid_combos()):
        print(f"{station_key}\t{mystery_key}\t{method_key}")


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
            for index, combo in enumerate(valid_combos(), 1):
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
                header = f"### {p.station} / {p.mystery} / {p.method}"
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
