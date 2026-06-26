#!/usr/bin/env python3
"""
A tiny storyworld for a winter pirate tale with a little magic.

The premise is classical and small:
- a young pirate crew member wants to enjoy winter sea work
- a magical mishap makes the ship's gear fail or become inconvenient
- the crew must use a sensible magical fix to keep sailing
- the ending proves the world state changed

The script follows the Storyweavers contract:
- typed entities with meters and memes
- a reasonableness gate in Python
- an inline ASP twin
- story + Q&A + trace + JSON support
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protects: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "cold": 0.0, "shimmer": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "worry": 0.0,
                "wonder": 0.0,
                "squall": 0.0,
                "trickery": 0.0,
                "calm": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain", "sailor", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "pirate", "captain-boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    winter: bool
    sea: bool


@dataclass
class Magic:
    id: str
    label: str
    spell: str
    effect: str
    mess: str
    clears: set[str]
    safe_with: set[str]


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


PLACES = {
    "harbor": Place("harbor", "the harbor", winter=True, sea=True),
    "icecove": Place("icecove", "the ice cove", winter=True, sea=True),
    "deck": Place("deck", "the ship's deck", winter=True, sea=True),
}

MAGICS = {
    "frost_glimmer": Magic(
        "frost_glimmer",
        "a frost-glimmer spell",
        "spark a frost-glimmer spell",
        "made the ropes shine with silver ice",
        "sparkly",
        {"rope", "deck"},
        {"lantern", "cloak"},
    ),
    "snow_whisper": Magic(
        "snow_whisper",
        "a snow-whisper charm",
        "murmur a snow-whisper charm",
        "brought soft snowflakes dancing onto the deck",
        "snowy",
        {"deck", "boots"},
        {"coat", "boots"},
    ),
    "moon_tide": Magic(
        "moon_tide",
        "a moon-tide spell",
        "call a moon-tide spell",
        "made the sea rise and slap the hull",
        "wet",
        {"hull", "deck"},
        {"cloak", "lantern"},
    ),
}

PRIZES = {
    "lantern": Prize("lantern", "a little lantern", "the little lantern", "hand"),
    "cloak": Prize("cloak", "a wool cloak", "the wool cloak", "shoulders"),
    "boots": Prize("boots", "sea boots", "the sea boots", "feet", plural=True),
}

REMEDIES = [
    Remedy("sealed_lantern", "a sealed lantern", "wrap the lantern in wax cloth", "walked back to fetch the wax cloth", {"hand"}, {"wet", "sparkly"}),
    Remedy("warm_cloak", "a warm cloak", "tie on a warm cloak first", "went below to get the warm cloak", {"shoulders"}, {"wet", "snowy"}),
    Remedy("dry_boots", "dry boots", "put on dry boots first", "hiked below to get dry boots", {"feet"}, {"wet", "snowy"}),
    Remedy("spark_net", "a spark-net", "set up a spark-net over the rail", "lashed the spark-net to the rail", {"hand", "shoulders"}, {"sparkly"}),
]

NAMES = ["Finn", "Mara", "Pip", "Lena", "Jory", "Nell"]
TITLES = ["young pirate", "little deckhand", "brave sailor", "tiny mate"]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def at_risk(magic: Magic, prize: Prize) -> bool:
    return prize.region in magic.clears or prize.id in magic.clears or prize.id in magic.safe_with or prize.region in {"hand", "shoulders", "feet"}


def select_remedy(magic: Magic, prize: Prize) -> Optional[Remedy]:
    for rem in REMEDIES:
        if prize.region in rem.covers and magic.mess in rem.guards:
            return rem
    return None


def predict_damage(world: World, hero: Entity, magic: Magic, prize: Prize) -> bool:
    sim = copy_world(world)
    hero2 = sim.get(hero.id)
    hero2.meters[magic.mess] += 1.0
    prize2 = sim.get(prize.id)
    if prize2.worn_by == hero2.id and prize.region in getattr(sim, "covered_regions", set()):
        return False
    return True


def copy_world(world: World) -> World:
    import copy

    sim = World()
    sim.entities = copy.deepcopy(world.entities)
    sim.fired = set(world.fired)
    sim.paragraphs = [[]]
    sim.facts = dict(world.facts)
    return sim


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(place: Place, magic: Magic, prize: Prize, name: str, title: str) -> World:
    w = World()
    hero = w.add(Entity(id=name, kind="character", type="pirate", label=title))
    captain = w.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    prize_ent = w.add(Entity(id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=captain.id, plural=prize.plural))
    prize_ent.worn_by = hero.id
    w.facts.update(place=place, magic=magic, prize=prize, hero=hero, captain=captain)
    return w


def setup(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    prize = world.get(world.facts["prize"].id)
    magic: Magic = world.facts["magic"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a {hero.label} who loved winter sails on {place.label}.")
    world.say(f"{hero.id} also loved to {magic.spell}, because magic made the cold sea feel like a game.")
    world.say(f"{hero.id} wore {prize.phrase} and kept it close like treasure.")


def conflict(world: World) -> bool:
    hero = world.get(world.facts["hero"].id)
    captain = world.get(world.facts["captain"].id)
    prize = world.get(world.facts["prize"].id)
    magic: Magic = world.facts["magic"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]

    world.para()
    world.say(f"One winter evening, {hero.id} and {captain.label} went to {place.label}.")
    world.say(f"{hero.id} wanted to {magic.spell}, but the captain warned that the spell could make {prize.label} hard to use.")
    hero.memes["worry"] += 1
    hero.memes["trickery"] += 1
    if magic.id == "moon_tide":
        world.say(f"The moon-tide spell lifted the water high and splashed the deck.")
    elif magic.id == "snow_whisper":
        world.say(f"The snow-whisper charm filled the boards with soft drifting snow.")
    else:
        world.say(f"The frost-glimmer spell made the ropes glitter, but the shine turned slippery.")
    hero.meters[magic.mess] += 1.0
    return True


def resolve(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    captain = world.get(world.facts["captain"].id)
    prize = world.get(world.facts["prize"].id)
    magic: Magic = world.facts["magic"]  # type: ignore[assignment]

    remedy = select_remedy(magic, prize)
    world.para()
    if remedy is None:
        raise StoryError("No sensible magical remedy exists for this combination.")

    world.say(f"{captain.label.capitalize()} smiled and offered a safer plan: {remedy.prep}.")
    world.say(f"Then {hero.id} {remedy.tail}, and the spell could still happen without spoiling {prize.label}.")
    hero.memes["joy"] += 1
    hero.memes["wonder"] += 1
    hero.memes["calm"] += 1
    hero.memes["worry"] = 0.0
    prize_entity = world.get(prize.id)
    prize_entity.meters["wet"] = 0.0
    prize_entity.meters["shimmer"] = 0.0
    world.say(f"Soon {hero.id} was {magic.effect}, while {prize.phrase} stayed dry and ready for the next wave.")


def tell(place: Place, magic: Magic, prize: Prize, name: str, title: str) -> World:
    world = build_world(place, magic, prize, name, title)
    setup(world)
    conflict(world)
    resolve(world)
    world.facts["remedy"] = select_remedy(magic, prize)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    magic: Magic = f["magic"]  # type: ignore[assignment]
    prize: Prize = f["prize"]  # type: ignore[assignment]
    return [
        f'Write a short winter pirate tale where {hero.id} tries to {magic.spell} at {place.label}.',
        f"Tell a child-friendly story with magic, a winter sea, and a problem with {prize.label}.",
        f"Write a tiny pirate adventure where a spell seems risky until the crew finds a safer way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    captain: Entity = f["captain"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    magic: Magic = f["magic"]  # type: ignore[assignment]
    prize: Prize = f["prize"]  # type: ignore[assignment]
    remedy: Remedy = f["remedy"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted to use magic on the winter ship?",
            answer=f"{hero.id}, the {hero.label}, wanted to use {magic.label} on the winter ship.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about the spell?",
            answer=f"{captain.label.capitalize()} worried because {magic.effect} could make {prize.phrase} hard to keep safe.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"They used {remedy.label} first, so {hero.id} could still enjoy the magic while {prize.phrase} stayed dry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic: Magic = f["magic"]  # type: ignore[assignment]
    prize: Prize = f["prize"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is winter?",
            answer="Winter is the coldest season of the year, when days can feel crisp and the weather may bring snow or ice.",
        ),
        QAItem(
            question="What does magic mean in stories?",
            answer="Magic in stories means something strange and wondrous happens, like a spell, charm, or enchantment that changes the world.",
        ),
        QAItem(
            question="Why do pirates use a ship's deck?",
            answer="Pirates use the deck as the open top of the ship where they walk, watch the sea, and work with ropes and sails.",
        ),
    ]
    if place.winter:
        out.append(QAItem(
            question=f"Why is {place.label} a good setting for a winter pirate tale?",
            answer=f"{place.label} works well because it is on the sea, and winter wind, ice, and waves make the voyage feel lively.",
        ))
    if magic.id == "snow_whisper":
        out.append(QAItem(
            question="Why can snow make a deck slippery?",
            answer="Snow can melt a little or pack into a smooth layer, and then shoes may slip on it.",
        ))
    if prize.id == "boots":
        out.append(QAItem(
            question="Why are sea boots useful on a ship?",
            answer="Sea boots help keep feet drier and warmer when the deck is wet, snowy, or splashy.",
        ))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk when the magic's effect can spoil its region.
at_risk(M, P) :- magic(M), prize(P), mess_of(M, X), prize_region(P, X).
at_risk(M, P) :- magic(M), prize(P), spoils_region(M, R), prize_region(P, R).

% A remedy is reasonable if it covers the prize's region and guards against the mess.
good_fix(M, P, R) :- at_risk(M, P), remedy(R), covers(R, X), prize_region(P, X), guards(R, G), mess_of(M, G).

valid_story(Place, M, P) :- place(Place), winter_place(Place), magic(M), prize(P), at_risk(M, P), good_fix(M, P, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.winter:
            lines.append(asp.fact("winter_place", pid))
        if place.sea:
            lines.append(asp.fact("sea_place", pid))
    for mid, magic in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("mess_of", mid, magic.mess))
        for r in sorted(magic.clears):
            lines.append(asp.fact("spoils_region", mid, r))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("prize_region", prid, prize.region))
        if prize.plural:
            lines.append(asp.fact("plural", prid))
    for rid, rem in ((r.id, r) for r in REMEDIES):
        lines.append(asp.fact("remedy", rid))
        for c in sorted(rem.covers):
            lines.append(asp.fact("covers", rid, c))
        for g in sorted(rem.guards):
            lines.append(asp.fact("guards", rid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for magic in MAGICS.values():
            for prize in PRIZES.values():
                if prize.region in magic.clears or prize.id in magic.clears:
                    if select_remedy(magic, prize):
                        out.append((place.id, magic.id, prize.id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    magic: str
    prize: str
    name: str
    title: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Winter magic pirate tale storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)]
    combos = [c for c in combos if (args.magic is None or c[1] == args.magic)]
    combos = [c for c in combos if (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid winter pirate magic combination matches the given options.")
    place, magic, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        magic=magic,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        title=args.title or rng.choice(TITLES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MAGICS[params.magic], PRIZES[params.prize], params.name, params.title)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("deck", "snow_whisper", "boots", "Mara", "captain"),
            StoryParams("harbor", "frost_glimmer", "lantern", "Finn", "young pirate"),
            StoryParams("icecove", "moon_tide", "cloak", "Nell", "little deckhand"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = rng_base + i
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
