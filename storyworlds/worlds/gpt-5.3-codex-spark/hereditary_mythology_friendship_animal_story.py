#!/usr/bin/env python3
"""Hereditary mythology and friendship in an animal world."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ModuleNotFoundError:  # Script execution fallback when package path is not configured.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from results import QAItem, StoryError, StorySample


ASP_RULES = """
% Facts supplied by asp_facts() are predicates: lineage/1, relic/1, companion/1, trial/1.
% Incompatible combinations are blocked here as the Python reasonableness gate mirrors.

invalid(C, R, P, T) :-
    lineage(C), relic(R), companion(P), trial(T),
    C=moonfox, R=tide_shell, T=flood_bridge.
invalid(C, R, P, T) :-
    lineage(C), relic(R), companion(P), trial(T),
    C=clouddeer, R=moon_horn, T=storm_pass.
invalid(C, R, P, T) :-
    lineage(C), relic(R), companion(P), trial(T),
    C=riverotter, P=turtle, T=storm_pass.

valid(C, R, P, T) :- lineage(C), relic(R), companion(P), trial(T), not invalid(C, R, P, T).
#show valid/4.
"""


@dataclass(frozen=True)
class StoryParams:
    lineage: str
    relic: str
    companion: str
    trial: str


@dataclass(frozen=True)
class Lineage:
    id: str
    name: str
    animal: str
    hero_name: str
    mythology: str
    hereditary_trait: str
    courage: int
    fear_softening: int
    friendship_start: int


@dataclass(frozen=True)
class Relic:
    id: str
    name: str
    element: str
    glow: int
    element_bonus: dict[str, int]
    meaning: str


@dataclass(frozen=True)
class Companion:
    id: str
    name: str
    species: str
    steadiness: int
    helpfulness: int


@dataclass(frozen=True)
class Trial:
    id: str
    name: str
    location: str
    element: str
    difficulty: int
    description: str


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    actor_meters: dict[str, int] = field(default_factory=dict)
    actor_memes: dict[str, int] = field(default_factory=dict)
    target_meters: dict[str, int] = field(default_factory=dict)
    target_memes: dict[str, int] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def change_meters(self, entity_id: str, **meters: int) -> None:
        ent = self.get(entity_id)
        for key, value in meters.items():
            ent.meters[key] = max(0, ent.meters.get(key, 0) + value)

    def change_memes(self, entity_id: str, **memes: int) -> None:
        ent = self.get(entity_id)
        for key, value in memes.items():
            ent.memes[key] = max(0, ent.memes.get(key, 0) + value)

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        *,
        actor_meters: dict[str, int] | None = None,
        actor_memes: dict[str, int] | None = None,
        target_meters: dict[str, int] | None = None,
        target_memes: dict[str, int] | None = None,
    ) -> None:
        actor_meters = actor_meters or {}
        actor_memes = actor_memes or {}
        target_meters = target_meters or {}
        target_memes = target_memes or {}
        self.events.append(
            Event(
                id=event_id,
                text=text,
                actor=actor,
                target=target,
                actor_meters=dict(actor_meters),
                actor_memes=dict(actor_memes),
                target_meters=dict(target_meters),
                target_memes=dict(target_memes),
            )
        )
        if actor_meters:
            self.change_meters(actor, **actor_meters)
        if actor_memes:
            self.change_memes(actor, **actor_memes)
        if target is not None:
            if target_meters:
                self.change_meters(target, **target_meters)
            if target_memes:
                self.change_memes(target, **target_memes)

    def trace(self) -> str:
        lines = ["Trace:"]
        for idx, event in enumerate(self.events, start=1):
            lines.append(f"{idx}. [{event.id}] {event.text}")
        return "\n".join(lines)


LINEAGES: dict[str, Lineage] = {
    "moonfox": Lineage(
        id="moonfox",
        name="Moonfox",
        animal="fox",
        hero_name="Lio",
        mythology="In their mythology, the first Moonfox taught stars to listen to lonely hearts.",
        hereditary_trait="hereditary silver-sense",
        courage=3,
        fear_softening=2,
        friendship_start=1,
    ),
    "riverotter": Lineage(
        id="riverotter",
        name="Riverotter",
        animal="otter",
        hero_name="Mina",
        mythology="In Riverotter mythology, inherited tides guide families to safe crossings.",
        hereditary_trait="hereditary current-mind",
        courage=2,
        fear_softening=1,
        friendship_start=2,
    ),
    "clouddeer": Lineage(
        id="clouddeer",
        name="Clouddeer",
        animal="deer",
        hero_name="Aya",
        mythology="Clouddeer mythology says ancestral stars tie a family by helping each other cross fear.",
        hereditary_trait="hereditary star-step",
        courage=2,
        fear_softening=0,
        friendship_start=2,
    ),
}

RELICS: dict[str, Relic] = {
    "moon_horn": Relic(
        id="moon_horn",
        name="moon-horn",
        element="wind",
        glow=2,
        element_bonus={"wind": 4, "night": 2, "water": 0},
        meaning="A curved horn with calm silver carvings that hums in strong wind.",
    ),
    "tide_shell": Relic(
        id="tide_shell",
        name="tide shell",
        element="water",
        glow=1,
        element_bonus={"water": 4, "wind": 0, "night": 1},
        meaning="A shell that catches current-music and steadies shaky paws.",
    ),
    "ember_ribbon": Relic(
        id="ember_ribbon",
        name="ember ribbon",
        element="night",
        glow=3,
        element_bonus={"night": 3, "wind": 1, "water": 2},
        meaning="A warm ribbon that remembers every brave promise it touches.",
    ),
}

FRIENDS: dict[str, Companion] = {
    "hare": Companion(
        id="hare",
        name="Pip",
        species="hare",
        steadiness=2,
        helpfulness=3,
    ),
    "badger": Companion(
        id="badger",
        name="Bran",
        species="badger",
        steadiness=3,
        helpfulness=2,
    ),
    "turtle": Companion(
        id="turtle",
        name="Tui",
        species="turtle",
        steadiness=4,
        helpfulness=2,
    ),
}

TRIALS: dict[str, Trial] = {
    "flood_bridge": Trial(
        id="flood_bridge",
        name="the Flood Bridge",
        location="the mossy flood bridge over the old river",
        element="water",
        difficulty=6,
        description="A rushing river shakes the bridge boards and tests patient teamwork.",
    ),
    "storm_pass": Trial(
        id="storm_pass",
        name="the Storm Pass",
        location="the wind-bent pass above cloud cliffs",
        element="wind",
        difficulty=7,
        description="The pass is loud with wind, and fear can grow louder than courage.",
    ),
    "moon_glade": Trial(
        id="moon_glade",
        name="the Moon Glade",
        location="the quiet moonlit glade in the old woods",
        element="night",
        difficulty=5,
        description="Dark branches hide old roots, but shared trust turns shadows into clear paths.",
    ),
}


def choices() -> list[StoryParams]:
    return [
        StoryParams(lineage, relic, companion, trial)
        for lineage in LINEAGES
        for relic in RELICS
        for companion in FRIENDS
        for trial in TRIALS
        if valid_params(StoryParams(lineage, relic, companion, trial))[0]
    ]


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.lineage not in LINEAGES:
        return False, f"unknown lineage: {params.lineage}"
    if params.relic not in RELICS:
        return False, f"unknown relic: {params.relic}"
    if params.companion not in FRIENDS:
        return False, f"unknown companion: {params.companion}"
    if params.trial not in TRIALS:
        return False, f"unknown trial: {params.trial}"
    if params.lineage == "moonfox" and params.relic == "tide_shell" and params.trial == "flood_bridge":
        return False, "Moonfox silver-sense is not enough for the flood bridge without a wind-tuned relic."
    if params.lineage == "clouddeer" and params.relic == "moon_horn" and params.trial == "storm_pass":
        return False, "Clouddeer star-step lore cannot hold the moon-horn during storm winds."
    if params.lineage == "riverotter" and params.companion == "turtle" and params.trial == "storm_pass":
        return False, "That trio does not handle the cliff wind safely in one try."
    return True, ""


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = {
        "lineage": args.lineage,
        "relic": args.relic,
        "companion": args.companion,
        "trial": args.trial,
    }
    if any(value is not None for value in explicit.values()):
        valid = [
            params
            for params in choices()
            if (explicit["lineage"] is None or params.lineage == explicit["lineage"])
            and (explicit["relic"] is None or params.relic == explicit["relic"])
            and (explicit["companion"] is None or params.companion == explicit["companion"])
            and (explicit["trial"] is None or params.trial == explicit["trial"])
        ]
        if not valid:
            raise StoryError(
                "explicit options are not a valid combination in this world; "
                f"lineage={args.lineage or 'any'}, relic={args.relic or 'any'}, "
                f"companion={args.companion or 'any'}, trial={args.trial or 'any'}"
            )
        return rng.choice(valid)
    return rng.choice(choices())


def make_world(params: StoryParams) -> World:
    lineage = LINEAGES[params.lineage]
    relic = RELICS[params.relic]
    companion = FRIENDS[params.companion]
    trial = TRIALS[params.trial]
    world = World(params=params)
    world.add(
        Entity(
            id="hero",
            name=lineage.hero_name,
            kind="animal",
            meters={"courage": lineage.courage, "energy": 5},
            memes={"Fear": 6, "Friendship": lineage.friendship_start, "Joy": 1},
        )
    )
    world.add(
        Entity(
            id="companion",
            name=companion.name,
            kind="animal",
            meters={"steadiness": companion.steadiness, "energy": 5},
            memes={"Friendship": 1, "Support": 1},
        )
    )
    world.add(
        Entity(
            id="relic",
            name=f"{relic.name}",
            kind="relic",
            meters={"glow": relic.glow},
            memes={"MythicTrust": 0},
        )
    )
    world.add(
        Entity(
            id="place",
            name=trial.location,
            kind="place",
            meters={"danger": trial.difficulty + 1},
            memes={"Heritage": 1},
        )
    )
    world.facts["location"] = trial.location
    world.facts["lineage_name"] = lineage.name
    world.facts["trial_name"] = trial.name
    world.facts["relic_meaning"] = relic.meaning
    return world


def invoke_heritage(world: World) -> None:
    lineage = LINEAGES[world.params.lineage]
    world.record(
        "heritage",
        f"{world.get('hero').name} remembered a hereditary promise from the {lineage.name}: "
        f"\"{lineage.mythology}\" The {lineage.hereditary_trait} rose through {world.get('hero').name}'s chest.",
        "hero",
        actor_memes={"Fear": -lineage.fear_softening, "Joy": 1},
    )
    world.facts["heritage_invoked"] = True


def face_trial(world: World) -> None:
    trial = TRIALS[world.params.trial]
    companion = FRIENDS[world.params.companion]
    world.record(
        "arrival",
        f"{world.get('hero').name} and {world.get('companion').name} reached {trial.location}, "
        f"where {trial.description.lower()}",
        "hero",
        "place",
        actor_meters={"energy": -1, "courage": 1},
        actor_memes={"Fear": 1},
        target_memes={"Fear": 1},
    )
    world.facts["approached"] = trial.id
    world.change_memes("companion", Support=companion.helpfulness)

def friend_and_relic(world: World) -> None:
    relic = RELICS[world.params.relic]
    companion = FRIENDS[world.params.companion]
    world.record(
        "teamwork",
        f"{world.get('companion').name} steadied the path, and the {relic.name} glimmered with {relic.meaning}",
        "companion",
        "relic",
        actor_memes={"Friendship": 1},
        target_meters={"glow": 1},
    )
    world.facts["teamwork"] = companion.id


def resolve_turn(world: World) -> None:
    lineage = LINEAGES[world.params.lineage]
    relic = RELICS[world.params.relic]
    companion = FRIENDS[world.params.companion]
    trial = TRIALS[world.params.trial]
    hero = world.get("hero")
    place = world.get("place")

    hero_strength = hero.meters["courage"] + relic.element_bonus[trial.element] + companion.helpfulness
    fear_block = place.meters["danger"] + hero.memes["Fear"]
    hero_win = hero_strength >= fear_block or (hero_strength >= trial.difficulty)

    if hero_win:
        world.record(
            "turn",
            f"{world.get('hero').name} called the inherited note and asked {world.get('companion').name} to follow.",
            "hero",
            "relic",
            actor_meters={"courage": 2, "energy": -1},
            actor_memes={"Fear": -1, "Friendship": 2, "Joy": 1},
            target_memes={"MythicTrust": 2},
            target_meters={"glow": 1},
        )
        world.record(
            "success",
            f"The {TRIALS[world.params.trial].name} calmed. The pair crossed together, and their shadows leaned in one direction.",
            "companion",
            "place",
            actor_memes={"Support": 2},
            target_meters={"danger": -2},
            target_memes={"Heritage": 1},
        )
        world.facts["outcome"] = "woven_triumph"
    else:
        world.record(
            "turn",
            f"{world.get('hero').name} felt fear rise as the {trial.name} pushed back, but did not panic.",
            "hero",
            actor_meters={"energy": -2},
            actor_memes={"Fear": 1},
        )
        world.record(
            "second_attempt",
            f"At {world.get('hero').name}'s request, {world.get('companion').name} stayed close and kept to the steadier rhythm.",
            "companion",
            "hero",
            actor_memes={"Friendship": 1, "Support": 1},
            actor_meters={"energy": -1},
            target_memes={"Fear": -1, "Friendship": 1},
            target_meters={"courage": 1},
        )
        world.record(
            "success",
            f"They used the {relic.name} to cross anyway, and the final move tied both courage and friendship together.",
            "relic",
            "place",
            target_meters={"danger": -1},
            target_memes={"Heritage": 1},
        )
        world.facts["outcome"] = "shared_push"

    world.change_meters("place", danger=max(0, place.meters["danger"]))


def settle_ending(world: World) -> None:
    if world.facts["outcome"] == "woven_triumph":
        world.record(
            "ending",
            f"As evening settled, the glade behind them held a warm line of glow. "
            "The relic was now a quiet family image: the first friend and the second friend walking the same shadow.",
            "hero",
        )
    else:
        world.record(
            "ending",
            f"The crossing was slower, but the line between them stayed true. "
            "The relic now held a steady glow, marking a picture of both animals beside a safer edge.",
            "companion",
        )
    world.facts["finished"] = True


def build_story(world: World) -> str:
    lineage = LINEAGES[world.params.lineage]
    relic = RELICS[world.params.relic]
    companion = FRIENDS[world.params.companion]
    trial = TRIALS[world.params.trial]
    hero = world.get("hero")
    place = world.get("place")
    outcome = world.facts["outcome"]

    ending_image = (
        f"At last, {place.name} wore a soft ring of light, a clear image of {hero.name} and {companion.name} stepping through together."
        if outcome == "woven_triumph"
        else f"By dawn, the moss held a brighter knot mark of three names: {hero.name}, {companion.name}, and the {relic.name}."
    )

    lines = [
        f"In a meadow of wind and fern, there was a young {lineage.animal} named {hero.name}.",
        f"{hero.name} was from the {lineage.name} family, whose {lineage.hereditary_trait} carried a clear hereditary mythology from their oldest stories.",
        (
            f"To test what this inheritance meant, {hero.name} and {companion.name} the {companion.species} "
            f"walked to {trial.location}, carrying a {relic.name}."
        ),
        (
            f"{lineage.mythology} On this day it helped the two friends decide which myth-rooted move to make."
        ),
        (
            f"During the heart of the trial, fear, friendship, and courage all shifted at once. "
            f"{hero.name} had {hero.memes['Fear']} fear, {hero.memes['Friendship']} friendship strength in name, "
            f"and {companion.name} added steadiness {world.get('companion').meters['steadiness']}."
        ),
        ending_image,
    ]
    return "\n".join(lines)


def qa_prompts() -> list[str]:
    return [
        "Write a short hereditary mythology animal story with friendship as the key lesson.",
        "Include a clear beginning, a difficult middle turn, and an ending image that changes the world.",
        "Make sure the story ends with proof that the relationship is stronger after the trial.",
    ]


def story_qa(world: World) -> list[QAItem]:
    lineage = LINEAGES[world.params.lineage]
    relic = RELICS[world.params.relic]
    companion = FRIENDS[world.params.companion]
    trial = TRIALS[world.params.trial]
    hero = world.get("hero")

    return [
        QAItem(
            "How did hereditary myth change what the hero did in the story?",
            f"{hero.name} remembered the {lineage.name} hereditary myth before the trial and used it as a cue. "
            f"That memory gave {hero.name} the confidence to treat the trial as a shared family lesson instead of a private panic.",
        ),
        QAItem(
            "Why was the companion important at the turning point?",
            f"{companion.name} kept the pace steady when the place became risky. "
            f"By matching courage and steadiness with {companion.name}'s support, {hero.name} could finish the action with the relic.",
        ),
        QAItem(
            "How is the ending image linked to what changed in the world?",
            f"The final image appears as glowing marks and calm shadows at {trial.location}. "
            f"It shows that the relic, {hero.name}, and {companion.name} changed the place from a risky trial into a cooperative path.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    relic = RELICS[world.params.relic]
    trial = TRIALS[world.params.trial]
    hero = world.get("hero")
    companion = world.get("companion")
    place = world.get("place")
    result = "overcame the obstacle together" if world.facts["outcome"] != "shared_push" else "crossed with a slower, shared push"
    return [
        QAItem(
            "Which relic was used and what element did it support best?",
            f"The relic was the {relic.name}, and it was strongest where its element matched the trial. "
            f"In this sample the trial was {trial.id}, so its element was {trial.element}.",
        ),
        QAItem(
            "What world entities were most central during the trial?",
            f"The central entities were {hero.name}, {companion.name}, the {relic.name}, and the place at {place.name}. "
            f"These four changed each other's meters and memes over the middle turn.",
        ),
        QAItem(
            "Did the pair finish the trial as a cooperative team?",
            f"Yes, because the world records the event as {result}. "
            f"The ending shows {hero.name} and {companion.name} moving in shared rhythm rather than separately.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    invoke_heritage(world)
    face_trial(world)
    friend_and_relic(world)
    resolve_turn(world)
    settle_ending(world)
    story = build_story(world)

    return StorySample(
        params=params,
        story=story,
        prompts=qa_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    lines = []
    for lineage in sorted(LINEAGES):
        lines.append(f"lineage({lineage}).")
    for relic in sorted(RELICS):
        lines.append(f"relic({relic}).")
    for companion in sorted(FRIENDS):
        lines.append(f"companion({companion}).")
    for trial in sorted(TRIALS):
        lines.append(f"trial({trial}).")
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def verify_asp() -> str:
    py_valid = {
        (params.lineage, params.relic, params.companion, params.trial)
        for params in choices()
    }
    import asp

    models = asp.solve(asp_program())
    if not models:
        raise StoryError("ASP produced no models")
    atoms = asp.atoms(models[0], "valid")
    asp_valid = {tuple(a for a in atom) for atom in atoms}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch: missing={missing[:5]} extra={extra[:5]}")
    for params in choices():
        sample = generate(params)
        if sample.world is None:
            raise StoryError(f"Generation failed to keep world model for params={params}")
        if len(sample.world.events) < 5:
            raise StoryError(f"Generated world too small for params={params}")
        if world_facts(sample.world).get("finished") is not True:
            raise StoryError(f"Generated story did not finish for params={params}")
    return f"OK: ASP and Python parity on {len(py_valid)} combinations and generation checks passed."


def world_facts(world: World) -> dict[str, object]:
    return dict(world.facts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lineage", choices=sorted(LINEAGES))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--companion", choices=sorted(FRIENDS))
    parser.add_argument("--trial", choices=sorted(TRIALS))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in choices():
            yield generate(params)
        return
    rng = random.Random(args.seed)
    explicit = any(
        value is not None
        for value in (args.lineage, args.relic, args.companion, args.trial)
    )
    for _ in range(max(1, args.n)):
        params = resolve_params(args, rng)
        yield generate(params)


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if args.qa:
        print("\n== Story-grounded QA ==")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\n== World-knowledge QA ==")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify_asp())
            return 0
        if args.asp:
            import asp

            print(asp.solve(asp_program()))
            return 0
        for index, sample in enumerate(iter_samples(args), start=1):
            if index > 1:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
