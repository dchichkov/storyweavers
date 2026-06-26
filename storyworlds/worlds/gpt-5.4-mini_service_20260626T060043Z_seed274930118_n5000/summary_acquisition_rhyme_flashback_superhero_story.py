#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/summary_acquisition_rhyme_flashback_superhero_story.py
==================================================================================================

A compact superhero storyworld about a child-friendly hero, a meaningful
acquisition, a flashback, and a rhymed ending beat.

Premise:
- A young hero learns that a new piece of gear can help them rescue the day.
- The hero briefly remembers an earlier failure in a flashback.
- The story resolves when the hero earns the gear through a brave, kind choice.

Core model:
- Physical meters: courage, tiredness, damage, speed, shine, weight.
- Emotional memes: hope, fear, pride, gratitude, doubt, joy.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports shared results eagerly
- lazily imports asp inside ASP helpers
- supports the standard CLI modes and verification
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "heroine"}
        male = {"boy", "man", "father", "uncle", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_item(self) -> bool:
        return self.kind == "item"


@dataclass
class City:
    name: str
    place: str
    danger: str
    glow: str
    weather: str = ""
    aids: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    power: str
    safe_against: set[str]
    weight: float
    shiny: bool = False
    plural: bool = False


@dataclass
class Crisis:
    id: str
    verb: str
    damage: str
    risk: str
    cause: str
    needs: set[str]
    noise: str


@dataclass
class StoryParams:
    city: str
    crisis: str
    hero_name: str
    hero_type: str
    mentor_type: str
    gadget: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.flashback_used = False
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.city)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.flashback_used = self.flashback_used
        c.paragraphs = [[]]
        return c


CITY_REGISTRY = {
    "sunport": City(
        name="Sunport",
        place="the bright harbor",
        danger="a stormy crane swing",
        glow="gold lights on the water",
        aids={"glider", "shield", "scanner"},
    ),
    "brickhill": City(
        name="Brickhill",
        place="the tall downtown",
        danger="a falling tower beam",
        glow="red beacons between rooftops",
        aids={"shield", "boots", "scanner"},
    ),
    "lumenbay": City(
        name="Lumen Bay",
        place="the windy bridge",
        danger="a sparking cable",
        glow="blue lights in the fog",
        aids={"glider", "boots", "scanner"},
    ),
}

CRISIS_REGISTRY = {
    "storm": Crisis(
        id="storm",
        verb="stop the storm machine",
        damage="blow roofs loose",
        risk="the street flooded fast",
        cause="the clouds spun wild",
        needs={"glider", "scanner"},
        noise="whirr-roar",
    ),
    "beam": Crisis(
        id="beam",
        verb="hold the broken beam",
        damage="drop sparks on the road",
        risk="the tower could crack again",
        cause="the old frame had a weak joint",
        needs={"shield", "boots"},
        noise="clang-crack",
    ),
    "cable": Crisis(
        id="cable",
        verb="steady the sparking cable",
        damage="start a chain of tiny pops",
        risk="the bridge might lose power",
        cause="salt wind had worn the wires",
        needs={"scanner", "boots"},
        noise="zzt-zzt",
    ),
}

GADGET_REGISTRY = {
    "glider": Gadget(
        id="glider",
        label="a silver glider pack",
        phrase="a silver glider pack with tiny fins",
        power="float over trouble",
        safe_against={"storm"},
        weight=2.0,
        shiny=True,
    ),
    "shield": Gadget(
        id="shield",
        label="a strong shield belt",
        phrase="a strong shield belt with a bright star",
        power="block flying wreckage",
        safe_against={"beam"},
        weight=1.5,
        shiny=True,
    ),
    "scanner": Gadget(
        id="scanner",
        label="a keen scanner visor",
        phrase="a keen scanner visor with a blue lens",
        power="spot hidden danger",
        safe_against={"storm", "cable"},
        weight=0.5,
        shiny=False,
    ),
    "boots": Gadget(
        id="boots",
        label="storm boots",
        phrase="storm boots with grippy soles",
        power="keep footing on slick ground",
        safe_against={"beam", "cable"},
        weight=1.0,
        shiny=False,
    ),
}


HERO_NAMES = ["Nova", "Ruby", "Milo", "Zara", "Jasper", "Ivy", "Theo", "Maya"]
HERO_TYPES = ["hero", "heroine", "boy", "girl"]
MENTOR_TYPES = ["mentor", "captain", "aunt", "uncle"]
FLAIR = ["brave", "kind", "quick", "steady", "bright", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for city_id, city in CITY_REGISTRY.items():
        for crisis_id, crisis in CRISIS_REGISTRY.items():
            for gadget_id in city.aids:
                if crisis_id in GADGET_REGISTRY[gadget_id].safe_against and gadget_id in crisis.needs:
                    out.append((city_id, crisis_id, gadget_id))
    return out


def explain_rejection(city: City, crisis: Crisis, gadget: Gadget) -> str:
    return (
        f"(No story: {gadget.label} does not honestly solve {crisis.verb} at {city.name}. "
        f"The gear must match the crisis, or the acquisition would feel fake.)"
    )


def explain_combo_rejection() -> str:
    return "(No story: no valid city/crisis/gadget combination matches those choices.)"


def _magnitude(v: float) -> bool:
    return v >= THRESHOLD


def reasonableness_gate(city: City, crisis: Crisis, gadget: Gadget) -> bool:
    return crisis.id in gadget.safe_against and gadget.id in crisis.needs and gadget.id in city.aids


def flashback_needed(world: World, hero: Entity, crisis: Crisis) -> bool:
    return hero.memes.get("doubt", 0.0) >= THRESHOLD or crisis.id in {"storm", "beam", "cable"}


def predict_outcome(world: World, hero: Entity, crisis: Crisis, gadget: Gadget) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["courage"] += 1
    sim.get(hero.id).meters["damage"] += 0.0
    success = reasonableness_gate(sim.city, crisis, gadget)
    return {"success": success, "danger": crisis.damage, "risk": crisis.risk}


def tell(city: City, crisis: Crisis, gadget: Gadget, hero_name: str, hero_type: str, mentor_type: str) -> World:
    world = World(city)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"courage": 1.0, "tiredness": 0.0, "speed": 1.0, "shine": 0.0, "damage": 0.0},
        memes={"hope": 1.0, "doubt": 0.0, "joy": 0.0, "pride": 0.0, "gratitude": 0.0},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        label="the mentor",
        meters={"courage": 2.0, "shine": 0.5},
        memes={"hope": 1.0, "gratitude": 0.0},
    ))
    item = world.add(Entity(
        id=gadget.id,
        kind="item",
        type="gadget",
        label=gadget.label,
        phrase=gadget.phrase,
        owner=hero.id,
        keeper=mentor.id,
        meters={"weight": gadget.weight, "shine": 1.0 if gadget.shiny else 0.0},
    ))

    world.say(
        f"In {city.name}, {hero_name} was a {random.choice(FLAIR)} {hero_type} who watched the sky from {city.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to help people fast, and {mentor.label} watched with proud eyes."
    )
    world.say(
        f"One day, the city faced {crisis.damage}, because {crisis.cause}."
    )

    world.para()
    world.say(
        f"{hero_name} heard the {crisis.noise} and ran toward the danger, but {hero.pronoun('possessive')} heart felt small."
    )
    if flashback_needed(world, hero, crisis):
        world.flashback_used = True
        hero.memes["doubt"] += 1
        world.say(
            f"Flashback: once before, {hero_name} had rushed in too soon and could not stop the trouble."
        )
        world.say(
            f"That memory made {hero.pronoun('possessive')} knees wobble like jelly."
        )
    hero.meters["tiredness"] += 1
    hero.memes["hope"] += 1

    world.para()
    world.say(
        f"{mentor.label.capitalize()} opened a case and showed {hero_name} {item.phrase}."
    )
    world.say(
        f'"This can help you {gadget.power}," {mentor.pronoun()} said.'
    )
    if not predict_outcome(world, hero, crisis, gadget)["success"]:
        raise StoryError(explain_rejection(city, crisis, gadget))
    item.worn_by = hero.id
    hero.meters["shine"] += 1
    hero.memes["gratitude"] += 1
    hero.memes["doubt"] = 0.0
    hero.memes["pride"] += 1

    world.para()
    world.say(
        f"{hero_name} nodded, clipped on the {gadget.label}, and moved where the trouble shook hardest."
    )
    world.say(
        f"{hero.pronoun().capitalize()} used the {gadget.label} to {gadget.power}, and the city's fear began to shrink."
    )
    world.say(
        f"At last, {hero_name} did {crisis.verb}, and the danger turned into a quiet, safe hum."
    )
    world.say(
        f"The crowd cheered under {city.glow}, and {hero_name} stood a little taller."
    )
    world.say(
        f"Then came the summary: the hero had found the right gear, remembered the hard lesson, and saved the day."
    )
    world.say(
        f"Like a bright little rhyme, the ending rang: 'When courage is low, let good gear show; when fear feels mean, keep actions clean.'"
    )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        item=item,
        city=city,
        crisis=crisis,
        gadget=gadget,
        flashback=world.flashback_used,
        acquisition=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    crisis = f["crisis"]
    gadget = f["gadget"]
    city = f["city"]
    return [
        f"Write a short superhero story in {city.name} where {hero.id} remembers a past mistake before earning {gadget.label}.",
        f"Tell a child-friendly tale with a flashback, an acquisition, and a brave rescue using {gadget.phrase}.",
        f"Write a rhymed superhero ending about {hero.id} helping with {crisis.verb} in {city.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    item = f["item"]
    city = f["city"]
    crisis = f["crisis"]
    gadget = f["gadget"]
    qa = [
        QAItem(
            question=f"Who is the story about in {city.name}?",
            answer=f"It is about {hero.id}, a {hero.type} who learns to help people in {city.name}.",
        ),
        QAItem(
            question=f"What trouble did the city face?",
            answer=f"The city faced {crisis.damage}, because {crisis.cause}.",
        ),
        QAItem(
            question=f"What did {mentor.label} give {hero.id}?",
            answer=f"{mentor.label.capitalize()} gave {hero.id} {item.phrase}, which could help {gadget.power}.",
        ),
    ]
    if f.get("flashback"):
        qa.append(
            QAItem(
                question=f"Why did the story pause for a flashback?",
                answer=(
                    f"The story paused for a flashback because {hero.id} remembered a time when {hero.pronoun('subject')} rushed in too soon. "
                    f"That memory made {hero.pronoun('possessive')} doubt grow for a moment."
                ),
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {hero.id} using {item.label} to help with {crisis.verb}, the danger becoming safe, and the crowd cheering in {city.glow}."
            ),
        )
    )
    return qa


KNOWLEDGE = {
    "glider": [
        QAItem(
            question="What does a glider do?",
            answer="A glider helps someone float through the air or move over a hard place more easily.",
        )
    ],
    "shield": [
        QAItem(
            question="What is a shield for?",
            answer="A shield helps block things that are flying or bumping toward you.",
        )
    ],
    "scanner": [
        QAItem(
            question="What does a scanner help with?",
            answer="A scanner helps you notice hidden things and spot danger early.",
        )
    ],
    "boots": [
        QAItem(
            question="Why do storm boots help?",
            answer="Storm boots help keep your feet steady on slippery ground.",
        )
    ],
    "storm": [
        QAItem(
            question="What is a storm?",
            answer="A storm is strong weather with wind, rain, thunder, or other loud, wild parts.",
        )
    ],
    "beam": [
        QAItem(
            question="Why is a broken beam dangerous?",
            answer="A broken beam can fall or crack again, which can hurt people nearby.",
        )
    ],
    "cable": [
        QAItem(
            question="What can a sparking cable do?",
            answer="A sparking cable can make crackling pops and cause trouble if it is not fixed safely.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier.",
        )
    ],
    "summary": [
        QAItem(
            question="What is a story summary?",
            answer="A summary is a short way to tell the main parts of a story.",
        )
    ],
    "acquisition": [
        QAItem(
            question="What does acquisition mean?",
            answer="Acquisition means getting or obtaining something new.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["gadget"].id, world.facts["crisis"].id, "flashback", "summary", "acquisition"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "item":
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


CURATED = [
    StoryParams(city="sunport", crisis="storm", hero_name="Nova", hero_type="heroine", mentor_type="mentor", gadget="glider"),
    StoryParams(city="brickhill", crisis="beam", hero_name="Milo", hero_type="boy", mentor_type="uncle", gadget="shield"),
    StoryParams(city="lumenbay", crisis="cable", hero_name="Maya", hero_type="girl", mentor_type="aunt", gadget="scanner"),
]


ASP_RULES = r"""
city(C) :- city_name(C).
crisis(X) :- crisis_name(X).
gadget(G) :- gadget_name(G).

compatible(Cr, G) :- crisis(Cr), gadget(G), needs(Cr, G), safe_against(G, Cr), city_aids(C, G).
valid(C, Cr, G) :- city(C), crisis(Cr), gadget(G), compatible(Cr, G), city_aids(C, G).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, city in CITY_REGISTRY.items():
        lines.append(asp.fact("city_name", cid))
        for aid in city.aids:
            lines.append(asp.fact("city_aids", cid, aid))
    for crid, cr in CRISIS_REGISTRY.items():
        lines.append(asp.fact("crisis_name", crid))
        for need in cr.needs:
            lines.append(asp.fact("needs", crid, need))
    for gid, g in GADGET_REGISTRY.items():
        lines.append(asp.fact("gadget_name", gid))
        for bad in g.safe_against:
            lines.append(asp.fact("safe_against", gid, bad))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with acquisition, flashback, and rhyme.")
    ap.add_argument("--city", choices=CITY_REGISTRY)
    ap.add_argument("--crisis", choices=CRISIS_REGISTRY)
    ap.add_argument("--gadget", choices=GADGET_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--mentor-type", choices=MENTOR_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.city is None or c[0] == args.city)
        and (args.crisis is None or c[1] == args.crisis)
        and (args.gadget is None or c[2] == args.gadget)
    ]
    if not filtered:
        raise StoryError(explain_combo_rejection())
    city, crisis, gadget = rng.choice(sorted(filtered))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    mentor_type = args.mentor_type or rng.choice(MENTOR_TYPES)
    return StoryParams(city=city, crisis=crisis, hero_name=name, hero_type=hero_type, mentor_type=mentor_type, gadget=gadget)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CITY_REGISTRY[params.city],
        CRISIS_REGISTRY[params.crisis],
        GADGET_REGISTRY[params.gadget],
        params.hero_name,
        params.hero_type,
        params.mentor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (city, crisis, gadget) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name}: {p.crisis} in {p.city} (gadget: {p.gadget})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
