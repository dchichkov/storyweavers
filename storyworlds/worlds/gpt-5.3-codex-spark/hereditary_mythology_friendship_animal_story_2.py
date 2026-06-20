#!/usr/bin/env python3
"""Hereditary animal mythology with friendship, written as a state-driven world.

Internal source tale:
A young forest animal from a hereditary family has to cross a myth-marked trial
with a chosen companion and a ritual relic. An old inheritance myth gives the
turning courage at the crucial moment, but the safe and successful ending comes
from friendship: both animals cooperate, solve the trial together, and leave a
visible ending image that proves the world changed.
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
STORYWORLDS = Path(__file__).resolve().parents[2]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class StoryParams:
    lineage: str
    relic: str
    companion: str
    trial: str
    seed: int | None = None


@dataclass(frozen=True)
class Lineage:
    key: str
    family: str
    hero_name: str
    species: str
    hero_article: str
    mythology: str
    hereditary_word: str
    base_courage: float
    fear_soften: float
    friendship_seed: float


@dataclass(frozen=True)
class Relic:
    key: str
    name: str
    element: str
    glow: float
    element_bonus: dict[str, float]
    meaning: str


@dataclass(frozen=True)
class Companion:
    key: str
    name: str
    species: str
    steadiness: float
    helpfulness: float


@dataclass(frozen=True)
class Trial:
    key: str
    name: str
    location: str
    element: str
    danger: float
    image: str
    risk_text: str


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    traits: tuple[str, ...] = ()
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        if self.kind in {"fox", "hare", "cat", "otter", "deer", "wolf", "badger"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        if self.kind in {"heron", "tortoise", "badger"}:
            # Keep species choices stable even when mixed; the stories are still child-facing.
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table.get(case, "they")


@dataclass
class Event:
    key: str
    text: str
    actor: str


@dataclass
class World:
    params: StoryParams
    lineage: Lineage
    relic: Relic
    companion: Companion
    trial: Trial
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    facts: dict[str, str | float | bool] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def change_meters(self, entity_id: str, **changes: float) -> None:
        ent = self.get(entity_id)
        for name, delta in changes.items():
            ent.meters[name] = max(0.0, ent.meters.get(name, 0.0) + delta)

    def change_memes(self, entity_id: str, **changes: float) -> None:
        ent = self.get(entity_id)
        for name, delta in changes.items():
            ent.memes[name] = max(0.0, ent.memes.get(name, 0.0) + delta)

    def log(self, key: str, text: str, actor: str) -> None:
        self.events.append(Event(key, text, actor))

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity_id, ent in self.entities.items():
            lines.append(
                f"  {entity_id}: name={ent.name} kind={ent.kind} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        lines.append(f"  facts: {dict(self.facts)}")
        lines.append("  events:")
        for event in self.events:
            lines.append(f"    - {event.key}: {event.text}")
        return "\n".join(lines)


LINEAGES: dict[str, Lineage] = {
    "moonbark_fox": Lineage(
        key="moonbark_fox",
        family="Moonbark Fox",
        hero_name="Liro",
        species="fox",
        hero_article="a",
        mythology="the Moonbark mythology says a family star can be heard as a quiet note in every shared problem",
        hereditary_word="hereditary moon-note",
        base_courage=4.5,
        fear_soften=2.0,
        friendship_seed=2.2,
    ),
    "riverotter_guard": Lineage(
        key="riverotter_guard",
        family="Riverotter",
        hero_name="Mina",
        species="otter",
        hero_article="an",
        mythology="the Riverotter mythology says currents keep the patient heart moving forward when paws are not alone",
        hereditary_word="hereditary current-song",
        base_courage=3.2,
        fear_soften=1.1,
        friendship_seed=2.6,
    ),
    "emberbadger_kin": Lineage(
        key="emberbadger_kin",
        family="Emberbadger",
        hero_name="Tavi",
        species="badger",
        hero_article="an",
        mythology="the Emberbadger mythology teaches that inherited embers grow brighter when two animals help each other think",
        hereditary_word="hereditary ember-trace",
        base_courage=3.8,
        fear_soften=1.8,
        friendship_seed=1.9,
    ),
}

RELICS: dict[str, Relic] = {
    "moon_stone_flute": Relic(
        key="moon_stone_flute",
        name="moon-stone flute",
        element="night",
        glow=2.8,
        element_bonus={"night": 3.2, "water": 0.6, "wind": 0.7, "earth": 0.9},
        meaning="A small white stone flute that hums when the moon touches it.",
    ),
    "tide_shell": Relic(
        key="tide_shell",
        name="tide shell",
        element="water",
        glow=3.1,
        element_bonus={"water": 3.1, "wind": 1.0, "night": 1.0, "earth": 1.2},
        meaning="A broad shell that glows stronger where water moves nearby.",
    ),
    "breeze_bone_whistle": Relic(
        key="breeze_bone_whistle",
        name="breeze-bone whistle",
        element="wind",
        glow=2.4,
        element_bonus={"wind": 3.0, "night": 1.0, "water": 1.2, "earth": 1.0},
        meaning="A thin carved whistle that bends the wind just enough to give rhythm to fear.",
    ),
}

COMPANIONS: dict[str, Companion] = {
    "tortoise": Companion(
        key="tortoise",
        name="Tumi",
        species="tortoise",
        steadiness=3.8,
        helpfulness=2.8,
    ),
    "sparrow": Companion(
        key="sparrow",
        name="Sera",
        species="sparrow",
        steadiness=2.4,
        helpfulness=3.3,
    ),
    "heron": Companion(
        key="heron",
        name="Nell",
        species="heron",
        steadiness=2.6,
        helpfulness=2.9,
    ),
}

TRIALS: dict[str, Trial] = {
    "storm_pass": Trial(
        key="storm_pass",
        name="the Storm Pass",
        location="a narrow pass between tall cedar heads",
        element="wind",
        danger=8.1,
        image="a ribbon of cloud snapped over the edge and then drifted open",
        risk_text="gusts could pull any small step sideways and drop an unsteady traveler",
    ),
    "flood_ledge": Trial(
        key="flood_ledge",
        name="the Flood Ledge",
        location="a slick stone ledge above the braided river",
        element="water",
        danger=8.0,
        image="the river fog cleared enough to show a bright reflected path on the stones",
        risk_text="water had made the stones slick and could push a single creature off the line",
    ),
    "root_tunnel": Trial(
        key="root_tunnel",
        name="the Root Tunnel",
        location="a low tunnel beneath old cedar roots",
        element="earth",
        danger=8.2,
        image="the tunnel stones gleamed with steady handprints where panic had been",
        risk_text="a dim tunnel can make even brave paws move too fast when eyes lose the floor",
    ),
}


ASP_RULES = r"""
% Domain constraints for the Python reasonableness gate.
valid(L, R, C, T) :- lineage(L), relic(R), companion(C), trial(T), not invalid(L, R, C, T).

invalid(LL, RR, CC, TT) :- lineage(LL), relic(RR), companion(CC), trial(TT), LL = moonbark_fox, RR = breeze_bone_whistle, CC = heron, TT = storm_pass.
invalid(LL, RR, CC, TT) :- lineage(LL), relic(RR), companion(CC), trial(TT), LL = emberbadger_kin, RR = moon_stone_flute, CC = tortoise, TT = storm_pass.
invalid(LL, RR, CC, TT) :- lineage(LL), relic(RR), companion(CC), trial(TT), LL = riverotter_guard, RR = tide_shell, CC = sparrow, TT = flood_ledge.

#show valid/4.
#show ok/0.
"""


def _clamp0(value: float) -> float:
    return value if value > 0 else 0.0


def valid_combo(lineage_key: str, relic_key: str, companion_key: str, trial_key: str) -> bool:
    if lineage_key not in LINEAGES or relic_key not in RELICS or companion_key not in COMPANIONS or trial_key not in TRIALS:
        return False

    # Explicit incompatible pairings.
    if lineage_key == "moonbark_fox" and relic_key == "breeze_bone_whistle" and companion_key == "heron" and trial_key == "storm_pass":
        return False
    if lineage_key == "emberbadger_kin" and relic_key == "moon_stone_flute" and companion_key == "tortoise" and trial_key == "storm_pass":
        return False
    if lineage_key == "riverotter_guard" and relic_key == "tide_shell" and companion_key == "sparrow" and trial_key == "flood_ledge":
        return False
    return True


def reasonableness_gate(params: StoryParams) -> tuple[bool, str]:
    if params.lineage not in LINEAGES:
        return False, f"No story: unknown lineage {params.lineage!r}."
    if params.relic not in RELICS:
        return False, f"No story: unknown relic {params.relic!r}."
    if params.companion not in COMPANIONS:
        return False, f"No story: unknown companion {params.companion!r}."
    if params.trial not in TRIALS:
        return False, f"No story: unknown trial {params.trial!r}."
    if not valid_combo(params.lineage, params.relic, params.companion, params.trial):
        return False, (
            "That setup is not accepted in this world: the chosen lineage, relic, companion, "
            "and trial do not hold together in the hereditary mythology as written."
        )
    return True, ""


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for lineage_key in sorted(LINEAGES):
        for relic_key in sorted(RELICS):
            for companion_key in sorted(COMPANIONS):
                for trial_key in sorted(TRIALS):
                    if valid_combo(lineage_key, relic_key, companion_key, trial_key):
                        combos.append((lineage_key, relic_key, companion_key, trial_key))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    explicit = {
        "lineage": args.lineage,
        "relic": args.relic,
        "companion": args.companion,
        "trial": args.trial,
    }
    combos = valid_combos()

    if any(value is not None for value in explicit.values()):
        filtered = [
            combo for combo in combos
            if (explicit["lineage"] is None or combo[0] == explicit["lineage"])
            and (explicit["relic"] is None or combo[1] == explicit["relic"])
            and (explicit["companion"] is None or combo[2] == explicit["companion"])
            and (explicit["trial"] is None or combo[3] == explicit["trial"])
        ]
        if not filtered:
            raise StoryError(
                "explicit options are not valid together in this world. "
                f"lineage={args.lineage or 'any'}, relic={args.relic or 'any'}, "
                f"companion={args.companion or 'any'}, trial={args.trial or 'any'}"
            )
        combo = rng.choice(filtered)
    else:
        combo = rng.choice(combos)

    base_seed = (args.seed or 13_579) + index
    return StoryParams(*combo, seed=base_seed)


def build_world(params: StoryParams) -> World:
    lineage = LINEAGES[params.lineage]
    relic = RELICS[params.relic]
    companion = COMPANIONS[params.companion]
    trial = TRIALS[params.trial]

    world = World(
        params=params,
        lineage=lineage,
        relic=relic,
        companion=companion,
        trial=trial,
    )

    hero = world.add(
        Entity(
            id="hero",
            name=lineage.hero_name,
            kind=lineage.species,
            traits=(lineage.family,),
            meters={"courage": lineage.base_courage, "stamina": 5.0},
            memes={"fear": 3.8, "friendship": lineage.friendship_seed, "joy": 1.1},
        )
    )
    partner = world.add(
        Entity(
            id="companion",
            name=companion.name,
            kind=companion.species,
            traits=("companion",),
            meters={"steadiness": companion.steadiness, "stamina": 5.0},
            memes={"friendship": 1.2, "support": companion.helpfulness},
        )
    )
    relic_ent = world.add(
        Entity(
            id="relic",
            name=relic.name,
            kind="relic",
            traits=("relic", "tool"),
            meters={"glow": relic.glow},
            memes={"help": 0.8},
        )
    )
    place = world.add(
        Entity(
            id="place",
            name=trial.location,
            kind="place",
            traits=("trial",),
            meters={"danger": trial.danger, "clarity": 1.0},
            memes={"hereditary_anchor": 1.0},
        )
    )

    world.facts["resolved"] = False
    world.facts["outcome"] = "pending"
    world.facts["ending_image"] = ""
    world.facts["hero_seed"] = (params.seed or 0)
    world.facts["friendship_start"] = float(hero.memes["friendship"])
    world.facts["place_difficulty"] = trial.danger

    world.log(
        "world_built",
        f"Built world for lineage={lineage.key}, relic={relic.key}, companion={companion.key}, trial={trial.key}.",
        "world",
    )

    # Silence static type checkers for dynamic dict initialization.
    _ = hero, partner, relic_ent, place
    return world


def call_heritage(world: World) -> None:
    hero = world.get("hero")
    lineage = world.lineage
    world.log(
        "heritage",
        f"{hero.name} listened to the {lineage.family} hereditary lesson: {lineage.mythology}.",
        "hero",
    )
    world.change_memes("hero", fear=-lineage.fear_soften, joy=1.1)
    world.facts["myth_used"] = True


def begin_trial(world: World) -> None:
    hero = world.get("hero")
    partner = world.get("companion")
    relic = world.relic
    trial = world.trial

    world.log(
        "departure",
        f"{hero.name} and {partner.name} reached {trial.location} with {relic.name} in hand.",
        "hero",
    )
    world.log("risk", f"The danger was {trial.danger:.1f}: {trial.risk_text}.", "place")
    world.change_memes("place", hereditary_anchor=0.5)
    world.change_meters("hero", courage=0.8)


def face_tension(world: World) -> None:
    trial = world.trial
    relic = world.relic
    relic_bonus = relic.element_bonus[trial.element]
    hero = world.get("hero")
    partner = world.get("companion")
    place = world.get("place")
    relic_ent = world.get("relic")

    support = (
        hero.meters["courage"]
        + relic_ent.meters["glow"]
        + relic_bonus
        + partner.meters["steadiness"]
    )
    pressure = place.meters["danger"] + 0.5 * trial.danger

    world.facts["support_start"] = support
    world.facts["pressure"] = pressure

    if support >= pressure:
        world.log(
            "turn",
            f"Before the hardest moment, {hero.name} remembered {world.lineage.hereditary_word} and called the inherited rhythm. "
            f"{partner.name} followed closely, helping keep each step steady.",
            "hero",
        )
        world.facts["outcome"] = "graceful_stalk"
        world.log(
            "outcome",
            f"The relic glowed and the path answered, turning the risk down by two and letting the pair move like one line.",
            "relic",
        )
        world.change_memes("hero", fear=-1.2, friendship=1.2, joy=1.0)
        world.change_memes("companion", friendship=1.0, support=0.5)
        world.change_meters("place", danger=-2.1, clarity=1.0)
        world.facts["ending_image"] = (
            f"By sunrise, moonlight and river-fog met on {world.trial.location}, "
            f"and a bright pair of prints showed {hero.name} and {partner.name} guiding each other across."
        )
        return

    # Shared struggle path.
    world.log(
        "turn_strain",
        f"When the first gust and shadow came, {hero.name}'s courage shook for a breath, so {partner.name} reached out and touched a shoulder.",
        "hero",
    )
    world.change_memes("hero", fear=1.2)
    world.change_meters("hero", courage=1.0)
    world.change_memes("companion", friendship=1.4)

    rebound = (
        support
        + hero.memes["friendship"]
        + partner.meters["steadiness"] * 0.5
        + relic.element_bonus[trial.element]
    )
    world.facts["rebound"] = rebound

    if rebound >= pressure:
        world.log(
            "turn_recovered",
            f"They slowed together, stepped to the rhythm of the {world.relic.meaning.lower()}, and crossed in a careful shared push.",
            "companion",
        )
        world.facts["outcome"] = "shared_push"
        world.change_memes("hero", fear=max(0.0, -0.8), friendship=1.8, joy=1.2)
        world.change_memes("companion", friendship=1.6)
        world.change_meters("place", danger=-1.8, clarity=1.3)
        world.facts["ending_image"] = (
            f"At the end, {partner.name}'s wingtip mark and {hero.name}'s paw mark sat side by side in wet dust, "
            f"and the {world.relic.name} glowed gently beside the safe route."
        )
        return

    # Fallback should not trigger when the reasonableness gate is respected, but
    # keep the world-safe and story-safe path explicit.
    world.log(
        "turn_held",
        f"The challenge stayed hard, but they kept each other safe and did not abandon the way home.",
        "hero",
    )
    world.facts["outcome"] = "deliberate"
    world.change_memes("hero", fear=0.6, friendship=0.9)
    world.change_memes("companion", friendship=1.2)
    world.change_meters("place", danger=-1.1, clarity=0.8)
    world.facts["ending_image"] = (
        f"When the wind settled, the pair still stood together at {world.trial.location}, "
        f"having made a new line of safe marks to walk back by."
    )


def seal_resolution(world: World) -> None:
    hero = world.get("hero")
    partner = world.get("companion")
    place = world.get("place")

    world.facts["resolved"] = True
    world.facts["friendship_end"] = hero.memes["friendship"] + partner.memes["friendship"]

    if world.facts["outcome"] == "graceful_stalk":
        world.log("resolve", f"{hero.name} and {partner.name} walked the rest of the way with the relic lighting their pace.", "hero")
    elif world.facts["outcome"] == "shared_push":
        world.log("resolve", f"After sharing weight and breath, {hero.name} and {partner.name} reached the far side and laughed quietly.", "companion")
    else:
        world.log("resolve", f"{hero.name} and {partner.name} finished together and changed their plan before stepping into the bright part of the day.", "hero")

    world.change_memes("hero", joy=1.4)
    world.change_memes("place", hereditary_anchor=1.0)


def build_story(world: World) -> str:
    lineage = world.lineage
    hero = world.get("hero")
    companion = world.get("companion")
    trial = world.trial

    opening = (
        f"{lineage.hero_article.capitalize()} {lineage.species} named {hero.name} lived in the {lineage.family} kin-forest.",
        f"In their hereditary tale, the family mythology taught that two friends can cross a hard place together if they listen to one shared rhythm.",
        f"{hero.name} carried a {world.relic.name} and trusted that inheritance could be a real tool, not just a story.",
    )

    middle = (
        f"Then came a tense turn: {hero.name} and {companion.name} reached {trial.location}. {trial.risk_text.capitalize()}.",
        f"The {world.relic.name} shone, the partner steadied {companion.name}, and {lineage.family} inheritance made the danger feel thinkable instead of endless.",
    )

    if world.facts["outcome"] == "graceful_stalk":
        turning = (
            f"They moved in a quick, careful rhythm as the story of their line guided the choice.",
            f"Fear dropped, and the path began to feel narrow but possible.",
        )
    elif world.facts["outcome"] == "shared_push":
        turning = (
            f"They paused, touched shoulders, and counted one-two-three in old friend-talk.",
            f"Then they leaned in together and crossed with steady pushes where luck would never have been enough.",
        )
    else:
        turning = (
            f"They did not run; they marked every safe step and moved slowly as a pair.",
            f"By keeping the relic's rhythm and each other's pace, fear lost its size before the day changed.",
        )

    closing = (
        f"The trial was not erased; it was transformed.",
        f"Now {world.facts['ending_image']}",
        f"In the clear part of the place, their friendship felt stronger than before, and the ancient hereditary myth became a living lesson.",
    )

    paragraphs = [
        " ".join(opening),
        " ".join(middle),
        " ".join(turning),
        " ".join(closing),
    ]
    return "\n\n".join(paragraphs)


def prompts_for(world: World) -> list[str]:
    return [
        "Write a brief animal story with the words hereditary and mythology.",
        "Show friendship changing the middle of the story, not just the ending.",
        "End with a concrete image that shows what changed in the world state.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    hero = world.get("hero")
    companion = world.get("companion")
    trial = world.trial
    return [
        QAItem(
            "What hereditary cue started the action for the protagonist?",
            f"{hero.name} used a hereditary mythic phrase from the {world.lineage.family} line at the first turn. "
            f"That memory changed the way fear was handled because the action became a shared task tied to the family's mythology instead of a private panic.",
        ),
        QAItem(
            "How did the companion affect the outcome?",
            f"The companion kept the pace steady, added steadiness, and boosted the second attempt with support. "
            f"Because of that cooperation, the challenge changed from a solo race into a joint crossing.",
        ),
        QAItem(
            "What was the real turning moment in the story?",
            f"The turning moment was when courage first dropped and then climbed back through the pair's shared rhythm. "
            f"The world log records this as either a graceful turn or a shared push after the fear spike.",
        ),
        QAItem(
            "What role did the relic play in the trial?",
            f"The relic matched the trial's element through its bonus and glow, then increased the relic-light trail that cut risk in the place. "
            f"That helped convert raw danger into steps the two could actually attempt safely.",
        ),
        QAItem(
            "How does the ending prove friendship changed the world?",
            f"The ending image shows matching side-by-side marks and a changed place quality with less danger, which means the crossing left physical evidence. "
            f"It is a visible result of friendship-based decisions, not just a sentiment in one line of dialogue.",
        ),
        QAItem(
            "Was the trial fully resolved in this world?",
            f"Yes. The world flag `resolved` is true after the ending section and the event log records a clear resolve action. "
            f"That means the system state moved from tension to completion.",
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What determines whether a combo is valid before generation starts?",
            "Valid combos are filtered by the Python reasonableness gate. It removes specific incompatible combinations of lineage, relic, companion, and trial that would break the hereditary logic in this world.",
        ),
        QAItem(
            "How can a story be diagnosed as having passed this world successfully?",
            "A generated world must set `resolved` to true and record an outcome tag such as `graceful_stalk` or `shared_push`.",
        ),
        QAItem(
            "Why should the ending image be factual and concrete?",
            "Because the story-world contract requires a visible final state change. The image references the place and entities that were in the active trial so a checker can confirm the changed danger path and pair marks.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = reasonableness_gate(params)
    if not ok:
        raise StoryError(reason)

    world = build_world(params)
    call_heritage(world)
    begin_trial(world)
    face_tension(world)
    seal_resolution(world)

    story = build_story(world)

    if not world.facts["resolved"]:
        raise StoryError("Generation did not finish the trial state.")

    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows = []
    for lineage in sorted(LINEAGES):
        rows.append(fact("lineage", lineage))
    for relic in sorted(RELICS):
        rows.append(fact("relic", relic))
    for companion in sorted(COMPANIONS):
        rows.append(fact("companion", companion))
    for trial in sorted(TRIALS):
        rows.append(fact("trial", trial))
    if params is not None:
        rows.append(fact("chosen", params.lineage, params.relic, params.companion, params.trial))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str]] = set()
    for model in solve(asp_program()):
        for combo in atoms(model, "valid"):
            combos.add(tuple(str(part) for part in combo))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    rows = atoms(one_model(asp_program(fact_clause_for_params(params))), "ok")
    return bool(rows)


def fact_clause_for_params(params: StoryParams) -> str:
    from storyworlds.asp import fact

    return f"\n{fact('chosen', params.lineage, params.relic, params.companion, params.trial)}\nok :- chosen({params.lineage},{params.relic},{params.companion},{params.trial}).\n"


def verify() -> str:
    python_valid = set(valid_combos())
    asp_valid = asp_valid_combos()
    if python_valid != asp_valid:
        only_py = sorted(python_valid - asp_valid)
        only_asp = sorted(asp_valid - python_valid)
        raise StoryError(f"ASP/Python mismatch: python_only={only_py} asp_only={only_asp}")

    for index, combo in enumerate(sorted(python_valid)):
        params = StoryParams(*combo, seed=index)
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected validated params={params}")
        sample = generate(params)
        text_lower = sample.story.lower()
        if "hereditary" not in text_lower or "mythology" not in text_lower:
            raise StoryError(f"Missing required seed words for params={params}")
        if not sample.world or not sample.world.facts.get("resolved"):
            raise StoryError(f"World did not resolve for params={params}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if sample.world.facts.get("friendship_end", 0.0) < 2.0:
            raise StoryError(f"Friendship did not grow enough for params={params}")

    return f"OK: Python and ASP each accept {len(python_valid)} combos, and story generation completed for each verified sample."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lineage", choices=sorted(LINEAGES))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--companion", choices=sorted(COMPANIONS))
    parser.add_argument("--trial", choices=sorted(TRIALS))
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n" + sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for item in sample.prompts:
            print(f"- {item}")
        print("\n== Story-grounded QA ==")
        for qa_item in sample.story_qa:
            print(f"Q: {qa_item.question}")
            print(f"A: {qa_item.answer}")
        print("\n== World-knowledge QA ==")
        for qa_item in sample.world_qa:
            print(f"Q: {qa_item.question}")
            print(f"A: {qa_item.answer}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
        samples: list[StorySample] = []

        if args.all:
            for index, combo in enumerate(valid_combos()):
                params = StoryParams(*combo, seed=base_seed + index)
                samples.append(generate(params))
        else:
            count = max(1, args.n)
            for index in range(count):
                params = resolve_params(args, random.Random(base_seed + index), index=index)
                samples.append(generate(params))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            if index:
                print("\n---\n")
            header = ""
            if args.all:
                p = sample.params
                header = f"### lineage={p.lineage} relic={p.relic} companion={p.companion} trial={p.trial}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
        return 0
    except StoryError as exc:
        print(exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
