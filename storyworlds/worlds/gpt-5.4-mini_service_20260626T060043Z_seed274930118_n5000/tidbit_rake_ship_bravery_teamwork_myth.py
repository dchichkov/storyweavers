#!/usr/bin/env python3
"""
storyworlds/worlds/tidbit_rake_ship_bravery_teamwork_myth.py
==============================================================

A small myth-shaped storyworld about a tidbit, a rake, and a ship.

Premise:
- A young hero finds a tiny tidbit from a sea altar.
- A ship is held fast by tangled driftweed and reef-rope.
- Bravery is needed to face the swaying deep.
- Teamwork is needed to free the ship.

The story is deliberately constrained so the turn and resolution feel causal:
the hero cannot simply wish the ship loose. Someone must act bravely, and the
crew must work together with a rake and ropes to make the ship sail again.

This world includes:
- physical meters: wind, tide, entanglement, readiness, wear, shine
- emotional memes: fear, bravery, trust, teamwork, hope, awe
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
HARSH_SEA = {"reef", "storm", "dark water"}
SOFT_SEA = {"harbor", "shore", "cove"}


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    sea: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    use: str
    hero_bias: set[str] = field(default_factory=lambda: {"girl", "boy"})
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    cure: str
    method: str
    end_note: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def _join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _is_harsh(place: Place) -> bool:
    return place.sea in HARSH_SEA


def _hero_name_pool(gender: str) -> list[str]:
    return ["Ari", "Nia", "Mira", "Sora", "Lena"] if gender == "girl" else ["Kai", "Toma", "Noor", "Eli", "Rin"]


def _hero_desc(name: str, trait: str, kind: str) -> str:
    return f"little {trait} {kind} {name}"


def _set_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _set_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _clear_meme(e: Entity, key: str) -> None:
    e.memes[key] = 0.0


def predict_free(world: World, hero: Entity, ship: Entity, crew: list[Entity], use_aid: Optional[Aid]) -> bool:
    sim = world.copy()
    _attempt_free(sim, sim.get(hero.id), sim.get(ship.id), [sim.get(c.id) for c in crew], use_aid, narrate=False)
    return sim.get(ship.id).meters.get("stuck", 0.0) < THRESHOLD


def _attempt_free(world: World, hero: Entity, ship: Entity, crew: list[Entity], aid: Optional[Aid], narrate: bool = True) -> bool:
    if ship.meters.get("stuck", 0.0) < THRESHOLD:
        return True
    if aid is None:
        return False
    if aid.cure != "entanglement":
        return False
    # The rake can only help if teamwork is present.
    if world.facts.get("teamwork", 0.0) < THRESHOLD:
        return False
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return False

    ship.meters["stuck"] = 0.0
    ship.meters["ready"] = 1.0
    for c in crew:
        _set_meme(c, "hope", 1.0)
        _set_meme(c, "trust", 1.0)
    if narrate:
        world.say(
            f"Together they used the {aid.label}, and the tangled weed came loose from the ship's side."
        )
    return True


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS.values():
        lines.append(asp.fact("place", p.name))
        if p.sea:
            lines.append(asp.fact("sea", p.name, p.sea))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.name, a))
    for it in ITEMS.values():
        lines.append(asp.fact("item", it.id))
        lines.append(asp.fact("use", it.id, it.use))
        for g in sorted(it.hero_bias):
            lines.append(asp.fact("hero_bias", it.id, g))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        lines.append(asp.fact("cure", aid.id, aid.cure))
        for h in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, I, A, G) :-
    affords(P, I),
    use(I, entanglement),
    cure(A, entanglement),
    hero_bias(I, G),
    helps(A, bravery),
    helps(A, teamwork).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


SETTINGS = {
    "harbor": Place(name="harbor", sea="harbor", affords={"find_tidbit", "free_ship"}),
    "cove": Place(name="cove", sea="cove", affords={"find_tidbit", "free_ship"}),
    "reef": Place(name="reef", sea="reef", affords={"find_tidbit", "free_ship"}),
}

ITEMS = {
    "tidbit": Item(
        id="tidbit",
        label="tidbit",
        phrase="a tiny tidbit of sea-salt cake",
        type="tidbit",
        use="gift",
        hero_bias={"girl", "boy"},
    ),
    "rake": Item(
        id="rake",
        label="rake",
        phrase="a long rake with a bright wooden handle",
        type="rake",
        use="entanglement",
        hero_bias={"girl", "boy"},
    ),
    "ship": Item(
        id="ship",
        label="ship",
        phrase="a deep-keeled ship with a high white sail",
        type="ship",
        use="voyage",
        hero_bias={"girl", "boy"},
    ),
}

AIDS = {
    "rake_aid": Aid(
        id="rake_aid",
        label="rake",
        phrase="a long rake",
        helps={"bravery", "teamwork"},
        cure="entanglement",
        method="lift the seaweed from the hull",
        end_note="the rake scraped the last weed from the hull",
    )
}

GIRL_NAMES = ["Ari", "Nia", "Mira", "Sora", "Lena"]
BOY_NAMES = ["Kai", "Toma", "Noor", "Eli", "Rin"]
TRAITS = ["brave", "curious", "steady", "gentle", "bold"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p.name, "tidbit") for p in SETTINGS.values()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of tidbit, rake, ship, bravery, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(_hero_name_pool(gender))
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, trait=trait)


def _make_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    hero_type = params.gender
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="ship"))
    tidbit = world.add(Entity(id="tidbit", kind="thing", type="tidbit", label="tidbit"))
    rake = world.add(Entity(id="rake", kind="thing", type="rake", label="rake"))

    hero.meters["bravery"] = 0.0
    hero.memes["bravery"] = 0.0
    hero.memes["teamwork"] = 0.0
    ship.meters["stuck"] = 1.0
    ship.meters["ready"] = 0.0
    ship.meters["shine"] = 0.2
    rake.meters["use"] = 1.0
    tidbit.meters["shine"] = 1.0
    world.facts["hero"] = hero
    world.facts["ship"] = ship
    world.facts["tidbit"] = tidbit
    world.facts["rake"] = rake
    world.facts["place"] = place
    return world


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    hero = world.get(params.name)
    ship = world.get("ship")
    tidbit = world.get("tidbit")
    rake = world.get("rake")
    place = world.place

    crew = [
        world.add(Entity(id="sailor_one", kind="character", type="woman", label="sailor")),
        world.add(Entity(id="sailor_two", kind="character", type="man", label="sailor")),
    ]

    world.say(
        f"Long ago, at the {place.name}, there lived { _hero_desc(hero.id, params.trait, hero.type) } who listened for the old songs of the sea."
    )
    world.say(
        f"One morning {hero.id} found a tiny {tidbit.label} beside the stones, shining like a crumb of moonlight."
    )
    world.say(
        f"Farther out, a great {ship.label} lay caught near the reef, held fast by weed and rope."
    )
    world.para()

    hero.memes["awe"] = 1.0
    hero.memes["bravery"] += 1.0
    hero.meters["bravery"] += 1.0
    world.facts["bravery"] = hero.memes["bravery"]
    world.say(
        f"{hero.id} felt fear, but {hero.pronoun()} stepped toward the surf anyway, for {hero.pronoun('possessive')} heart had chosen bravery."
    )
    world.say(
        f"{hero.id} lifted the {tidbit.label} high and called the crew together, because even a small gift can summon help in a mythic hour."
    )
    world.para()

    world.facts["teamwork"] = 0.0
    world.say(
        f"The two sailors heard the call and came running with ropes, and each one took a side of the line."
    )
    _set_meme(hero, "teamwork", 1.0)
    _set_meme(crew[0], "teamwork", 1.0)
    _set_meme(crew[1], "teamwork", 1.0)
    world.facts["teamwork"] = 1.0
    world.say(
        f"{hero.id} gripped the {rake.label}, and together they worked in rhythm: one pulled, one held, and one pried the weed from the keel."
    )

    if not predict_free(world, hero, ship, crew, AIDS["rake_aid"]):
        raise StoryError("This myth needs bravery and teamwork together with the rake.")
    _attempt_free(world, hero, ship, crew, AIDS["rake_aid"], narrate=True)
    world.para()

    ship.meters["shine"] = 1.0
    ship.meters["stuck"] = 0.0
    ship.meters["ready"] = 1.0
    _set_meme(hero, "hope", 1.0)
    _set_meme(hero, "trust", 1.0)
    _set_meme(hero, "teamwork", 1.0)
    for c in crew:
        _set_meme(c, "hope", 1.0)
        _set_meme(c, "trust", 1.0)

    world.say(
        f"At last the {ship.label} shuddered free, and the sea opened like a blue road before it."
    )
    world.say(
        f"{hero.id} smiled as the {tidbit.label} was set on the prow as an offering, and the ship sailed on while the crew laughed together."
    )

    world.facts.update(
        hero=hero,
        ship=ship,
        tidbit=tidbit,
        rake=rake,
        crew=crew,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    return [
        f"Write a mythic story about {hero.id}, a tidbit, a rake, and a ship at the {place.name}.",
        f"Tell a child-friendly legend where bravery and teamwork free a ship with a rake.",
        f"Write a short myth in which a tiny tidbit helps a brave hero gather a crew to move a stuck ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    ship = f["ship"]
    return [
        QAItem(
            question=f"What did {hero.id} find near the stones at the {place.name}?",
            answer=f"{hero.id} found a tiny tidbit of sea-salt cake near the stones at the {place.name}.",
        ),
        QAItem(
            question=f"Why could the ship not sail away at first?",
            answer="The ship was caught near the reef and held fast by weed and rope, so it could not move until the crew worked together.",
        ),
        QAItem(
            question=f"What did the hero use with the crew to free the ship?",
            answer=f"The hero used a rake with the sailors, and together they pried the weeds from the ship's side.",
        ),
        QAItem(
            question=f"What changed by the end of the story for the ship?",
            answer=f"By the end, the {ship.label} was free, ready, and able to sail on the open sea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidbit?",
            answer="A tidbit is a very small piece or taste of something, like a tiny morsel of food.",
        ),
        QAItem(
            question="What is a rake used for?",
            answer="A rake is a tool with a long handle and tines that can gather or pull loose material like leaves or weeds.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other to do something they could not do alone.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being willing to do something hard or scary when it matters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: {meters} {memes}")
    return "\n".join(out)


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/4.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {
        (p.name, "tidbit", "rake", g)
        for p in SETTINGS.values()
        for g in ("girl", "boy")
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("clingo only:", sorted(clingo_set - python_set))
    print("python only:", sorted(python_set - clingo_set))
    return 1


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
    StoryParams(place="harbor", name="Ari", gender="girl", trait="brave"),
    StoryParams(place="cove", name="Kai", gender="boy", trait="steady"),
    StoryParams(place="reef", name="Mira", gender="girl", trait="bold"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for t in vals:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
