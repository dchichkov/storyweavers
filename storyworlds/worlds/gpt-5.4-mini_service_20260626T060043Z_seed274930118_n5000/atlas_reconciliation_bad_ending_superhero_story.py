#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/atlas_reconciliation_bad_ending_superhero_story.py
==============================================================================================================================

A tiny superhero storyworld about Atlas, a young hero who can read routes in a city
of tall roofs and windy bridges. The world supports a reconciliation beat, but the
ending stays bad: the team makes up, yet the lost atlas is still gone.

The premise is simple:
- Atlas loves being a hero and carrying a city atlas that marks safe routes.
- A stormy chase causes a fight with a teammate.
- They reconcile, but the atlas is lost in the final rush.
- The story ends with them together, disappointed, proving that peace returned
  even though the mission did not fully succeed.

This script follows the shared storyworld contract:
- StoryParams plus registries
- build_parser / resolve_params / generate / emit / main
- inline ASP rules and facts
- deterministic simulation with meters and memes
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str
    places: list[str]
    stormy: bool = True
    safe_routes: list[str] = field(default_factory=list)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    loss: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    tag: str
    precious: bool = True


@dataclass
class Ally:
    id: str
    label: str
    type: str


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.current_place: str = city.name

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        c = World(self.city)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.current_place = self.current_place
        return c


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
CITIES = {
    "starport": City(
        name="Starport City",
        places=["the harbor", "the bridge", "the rooftop line", "the tall archive tower"],
        stormy=True,
        safe_routes=["the bridge", "the harbor"],
    ),
    "neon": City(
        name="Neon Bay",
        places=["the pier", "the clock tower roof", "the wind tunnel alley", "the rescue docks"],
        stormy=True,
        safe_routes=["the rescue docks", "the pier"],
    ),
}

MISSIONS = {
    "atlas_run": Mission(
        id="atlas_run",
        verb="deliver the atlas",
        gerund="delivering the atlas",
        rush="dash across the bridge",
        risk="the pages would tear in the wind",
        loss="the atlas would be lost in the storm",
        location="the bridge",
        tags={"atlas", "map", "storm"},
    ),
    "roof_sweep": Mission(
        id="roof_sweep",
        verb="check the rooftops",
        gerund="checking the rooftops",
        rush="swing to the next roof",
        risk="the atlas would slip from a pocket",
        loss="the pages would scatter across the chimneys",
        location="the rooftop line",
        tags={"atlas", "roof", "wind"},
    ),
    "dock_guard": Mission(
        id="dock_guard",
        verb="guard the harbor",
        gerund="guarding the harbor",
        rush="run to the edge of the pier",
        risk="the atlas would fall into the water",
        loss="the atlas would sink and never be easy to find",
        location="the harbor",
        tags={"atlas", "water", "rescue"},
    ),
}

RELICS = {
    "atlas": Relic(
        id="atlas",
        label="city atlas",
        phrase="a folded city atlas with bright route lines",
        type="atlas",
        tag="atlas",
        precious=True,
    ),
    "signalmap": Relic(
        id="signalmap",
        label="signal map",
        phrase="a pocket map of rescue signals",
        type="map",
        tag="map",
        precious=True,
    ),
}

ALLY_TYPES = {
    "partner": Ally(id="partner", label="the partner", type="boy"),
    "partner_girl": Ally(id="partner_girl", label="the partner", type="girl"),
}

HERO_NAMES = ["Atlas", "Sky", "Nova", "Bolt", "Mira", "Rex", "Iris", "Jet"]
ALLY_NAMES = ["Pip", "Tess", "Milo", "June", "Bea", "Kai", "Zane", "Lena"]
TRAITS = ["brave", "quick", "bold", "restless", "steady", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    city: str
    mission: str
    relic: str
    hero_name: str
    hero_type: str
    ally_name: str
    ally_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _hero_desc(hero: Entity) -> str:
    trait = hero.memes.get("trait_word", "")
    if trait:
        return f"young {trait} {hero.type}"
    return f"young {hero.type}"


def _mission_risk(mission: Mission, relic: Relic) -> bool:
    return relic.tag in mission.tags


def _reasonableness_gate(mission: Mission, relic: Relic) -> bool:
    return _mission_risk(mission, relic)


def predict_loss(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity) -> bool:
    sim = world.copy()
    _start_mission(sim, sim.get(hero.id), sim.get(ally.id), mission, narrate=False)
    relic_entity = sim.get(relic.id)
    return relic_entity.meters.get("lost", 0.0) >= THRESHOLD or relic_entity.meters.get("wet", 0.0) >= THRESHOLD


def _start_mission(world: World, hero: Entity, ally: Entity, mission: Mission, narrate: bool = True) -> None:
    world.current_place = mission.location
    hero.meters["speed"] = hero.meters.get("speed", 0.0) + 1
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} and {ally.id} hurried toward {mission.location} for the mission.")


def _storm(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity, narrate: bool = True) -> None:
    if not world.city.stormy:
        return
    world.facts["storm"] = True
    hero.meters["wind"] = hero.meters.get("wind", 0.0) + 1
    if narrate:
        world.say(f"The wind snapped around their capes, and {mission.risk}.")


def _argument(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity, narrate: bool = True) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    ally.memes["frustration"] = ally.memes.get("frustration", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} wanted to keep the {relic.label} safe, but {ally.id} wanted to move faster.")
        world.say(f"Their voices grew sharp because {mission.risk}.")


def _separate(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity, narrate: bool = True) -> None:
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    ally.memes["guilt"] = ally.memes.get("guilt", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} hugged the atlas close, and {ally.id} ran ahead by mistake.")
        world.say(f"That made the situation worse, because {mission.loss}.")


def _reconciliation(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity, narrate: bool = True) -> None:
    if hero.memes.get("hurt", 0.0) < THRESHOLD and ally.memes.get("guilt", 0.0) < THRESHOLD:
        return
    hero.memes["hurt"] = 0.0
    ally.memes["guilt"] = 0.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    ally.memes["trust"] = ally.memes.get("trust", 0.0) + 1
    if narrate:
        world.say(f"{ally.id} came back first and said sorry, and {hero.id} nodded.")
        world.say(f"They promised to stay together even if the mission turned rough.")


def _bad_ending(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity, narrate: bool = True) -> None:
    relic.meters["lost"] = relic.meters.get("lost", 0.0) + 1
    if narrate:
        world.say(f"They searched the wind-blown steps, but the {relic.label} was gone.")
        world.say(f"In the end, {mission.loss}.")


def run_story(world: World, hero: Entity, ally: Entity, mission: Mission, relic: Entity) -> None:
    _start_mission(world, hero, ally, mission)
    world.para()
    _storm(world, hero, ally, mission, relic)
    _argument(world, hero, ally, mission, relic)
    _separate(world, hero, ally, mission, relic)
    world.para()
    _reconciliation(world, hero, ally, mission, relic)
    _bad_ending(world, hero, ally, mission, relic)
    world.say(f"At last, {hero.id} and {ally.id} stood together on the roof, sad but no longer angry.")


# ---------------------------------------------------------------------------
# Story world assembly
# ---------------------------------------------------------------------------
def tell(city: City, mission: Mission, relic_cfg: Relic, hero_name: str, hero_type: str,
         ally_name: str, ally_type: str, trait: str) -> World:
    world = World(city)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    ally = world.add(Entity(id=ally_name, kind="character", type=ally_type, label=ally_name))
    relic = world.add(Entity(id=relic_cfg.id, type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase))

    hero.memes["trait_word"] = trait
    hero.memes["heroic"] = 1
    ally.memes["heroic"] = 1
    relic.owner = hero.id

    world.say(f"{hero.id} was a {_hero_desc(hero)} who carried {hero.pronoun('possessive')} {relic.label} everywhere.")
    world.say(f"{hero.id} and {ally.id} worked as a superhero team in {city.name}.")
    world.say(f"They needed the {relic.label} because it showed the safest ways through the city.")

    world.para()
    run_story(world, hero, ally, mission, relic)

    world.facts.update(
        hero=hero,
        ally=ally,
        relic=relic,
        mission=mission,
        city=city,
        storm=world.facts.get("storm", False),
        reconciled=True,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    ally: Entity = f["ally"]
    mission: Mission = f["mission"]
    relic: Entity = f["relic"]
    return [
        f'Write a superhero story for a young child about {hero.id} and {ally.id} that includes an atlas and a stormy mistake.',
        f"Tell a short story where {hero.id} tries to {mission.verb} with {relic.label}, but {ally.id} rushes ahead and they reconcile.",
        f'Create a gentle superhero story using the word "atlas" that ends sadly even after the heroes make up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ally: Entity = f["ally"]
    mission: Mission = f["mission"]
    relic: Entity = f["relic"]
    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id} and {ally.id}, a small superhero team in {world.city.name}.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry during the mission?",
            answer=f"{hero.id} worried because they were carrying the {relic.label}, and the storm could ruin or lose it.",
        ),
        QAItem(
            question=f"What caused the fight between {hero.id} and {ally.id}?",
            answer=f"They argued because {ally.id} wanted to move faster, but {hero.id} wanted to keep the atlas safe.",
        ),
        QAItem(
            question=f"How did the heroes feel at the end?",
            answer=f"They felt sad because the {relic.label} was still lost, but they had made up and stood together again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an atlas?",
            answer="An atlas is a book or map that helps people find places and routes.",
        ),
        QAItem(
            question="Why can wind be a problem for paper maps?",
            answer="Wind can blow paper around, fold it, or carry it away before you finish reading it.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who argued stop being angry and make up with each other.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when the characters do not get everything they hoped for, even if they tried hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mission is risky for a relic when the relic's tag is among the mission tags.
risky(M, R) :- mission(M), relic(R), mission_tag(M, T), relic_tag(R, T).

% Reconciliation is possible when both hero and ally are present and the story
% includes the fight marker.
reconcile(H, A) :- hero(H), ally(A), conflict(H, A).

% The bad ending is valid when the relic is risky, the heroes reconcile, and the
% relic is still lost in the final state.
valid_story(C, M, R, H, A) :- city(C), mission(M), relic(R), hero(H), ally(A),
                              risky(M, R), reconcile(H, A), bad_end(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, city in CITIES.items():
        lines.append(asp.fact("city", cid))
        for place in city.places:
            lines.append(asp.fact("place", cid, place))
        for route in city.safe_routes:
            lines.append(asp.fact("safe_route", cid, route))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_location", mid, mission.location))
        for tag in sorted(mission.tags):
            lines.append(asp.fact("mission_tag", mid, tag))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_tag", rid, relic.tag))
    for aid, ally in ALLY_TYPES.items():
        lines.append(asp.fact("ally", aid))
        lines.append(asp.fact("ally_type", aid, ally.type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show valid_story/5.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    python_valid = sorted(
        (cid, mid, rid, hid, aid)
        for cid in CITIES
        for mid, mission in MISSIONS.items()
        for rid, relic in RELICS.items()
        for hid in HERO_NAMES
        for aid in ALLY_NAMES
        if _reasonableness_gate(mission, relic)
    )
    if atoms == python_valid:
        print(f"OK: ASP gate matches Python gate ({len(atoms)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if atoms != python_valid:
        print("ASP:", atoms[:10])
        print("PY :", python_valid[:10])
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    city: str
    mission: str
    relic: str
    hero_name: str
    hero_type: str
    ally_name: str
    ally_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for cid in CITIES:
        for mid, mission in MISSIONS.items():
            for rid, relic in RELICS.items():
                if _reasonableness_gate(mission, relic):
                    out.append((cid, mid, rid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with atlas, reconciliation, and a bad ending.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ally-name")
    ap.add_argument("--ally-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.relic:
        mission = MISSIONS[args.mission]
        relic = RELICS[args.relic]
        if not _reasonableness_gate(mission, relic):
            raise StoryError("That mission and relic do not fit: the story would not have a believable atlas risk.")

    combos = [
        c for c in valid_combos()
        if (args.city is None or c[0] == args.city)
        and (args.mission is None or c[1] == args.mission)
        and (args.relic is None or c[2] == args.relic)
    ]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")

    city, mission_id, relic_id = rng.choice(sorted(combos))
    mission = MISSIONS[mission_id]
    relic = RELICS[relic_id]

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    ally_type = args.ally_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    ally_name = args.ally_name or rng.choice(ALLY_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        city=city,
        mission=mission_id,
        relic=relic_id,
        hero_name=hero_name,
        hero_type=hero_type,
        ally_name=ally_name,
        ally_type=ally_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    city = CITIES[params.city]
    mission = MISSIONS[params.mission]
    relic = RELICS[params.relic]
    world = tell(
        city=city,
        mission=mission,
        relic_cfg=relic,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        ally_name=params.ally_name,
        ally_type=params.ally_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        city="starport",
        mission="atlas_run",
        relic="atlas",
        hero_name="Atlas",
        hero_type="boy",
        ally_name="Milo",
        ally_type="boy",
        trait="brave",
    ),
    StoryParams(
        city="neon",
        mission="roof_sweep",
        relic="signalmap",
        hero_name="Mira",
        hero_type="girl",
        ally_name="June",
        ally_type="girl",
        trait="bold",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/5."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid story combinations")
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mission} in {p.city}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
