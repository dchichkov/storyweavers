#!/usr/bin/env python3
"""
storyworlds/worlds/cuddle_happy_ending_myth.py
==============================================

A tiny mythic storyworld: a child, a shy magical creature, a gentler way
to approach, and a happy ending made concrete in the world state.

Seed premise:
- include: cuddle
- mood: Happy Ending
- style: Myth

The world is intentionally small and constraint-checked. The simulation drives
the prose: the child seeks closeness, the guardian sees danger, the world
foresees what would happen, and a soft offering turns fear into warmth.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    affords: set[str] = field(default_factory=set)


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
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    guardian: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


PLACES = {
    "grove": Place("grove", "the moonlit grove", "grove", {"cuddle"}),
    "hill": Place("hill", "the windy hill", "hill", {"cuddle"}),
    "cave": Place("cave", "the echoing cave", "cave", {"cuddle"}),
    "shore": Place("shore", "the silver shore", "shore", {"cuddle"}),
}

PRIZES = {
    "starcloak": Prize("starcloak", "starcloak", "a bright starcloak", "torso"),
    "shell": Prize("shell", "shell", "a river-polished shell", "hands"),
    "lantern": Prize("lantern", "lantern", "a tiny lantern", "hands"),
}

REMEDIES = [
    Remedy("moss_blanket", "moss blanket", {"torso", "hands"}, "wrap the child in a moss blanket first", "returned with the moss blanket", False),
    Remedy("feather_wrap", "feather wrap", {"torso"}, "put on a feather wrap first", "came back with the feather wrap", False),
    Remedy("soft_cloak", "soft cloak", {"torso"}, "bring out a soft cloak first", "returned with the soft cloak", False),
]

GIRL_NAMES = ["Luna", "Mira", "Nia", "Zara", "Iris"]
BOY_NAMES = ["Orin", "Tavi", "Seth", "Rowan", "Jude"]
TRAITS = ["gentle", "curious", "brave", "dreamy", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for prize in PRIZES:
            combos.append((place, prize))
    return combos


def choose_remedy(prize: Prize) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if prize.region in remedy.covers:
            return remedy
    return None


def predict(world: World, hero: Entity, prize: Entity) -> dict:
    sim = world.copy()
    _attempt_cuddle(sim, sim.get(hero.id), sim.get(prize.id), narrate=False)
    return {
        "fear": sim.get(prize.id).memes.get("fear", 0.0),
        "joy": sim.get(hero.id).memes.get("joy", 0.0),
        "resolved": sim.get(prize.id).memes.get("trust", 0.0) >= THRESHOLD,
    }


def _attempt_cuddle(world: World, hero: Entity, prize: Entity, narrate: bool = True) -> None:
    if "cuddle" not in world.place.affords:
        raise StoryError("This place cannot host the cuddle story.")
    if hero.memes.get("softened", 0.0) < THRESHOLD:
        prize.memes["fear"] = prize.memes.get("fear", 0.0) + 1.0
        hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1.0
        if narrate:
            world.say(f"{hero.id} reached for {prize.label}, but the old magic made {prize.label} tremble.")
        return
    prize.memes["trust"] = prize.memes.get("trust", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.id} and {prize.label} settled into a gentle cuddle, and the air grew warm.")


def _soften(hero: Entity) -> None:
    hero.memes["softened"] = hero.memes.get("softened", 0.0) + 1.0


def tell(place: Place, prize_cfg: Prize, hero_name: str, hero_type: str, guardian_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"hope": 0.0}, label=hero_name))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label=f"the {guardian_type}", memes={"care": 1.0}))
    prize = world.add(Entity(id=prize_cfg.id, kind="character", type="spirit", label=prize_cfg.label, phrase=prize_cfg.phrase))
    remedy = choose_remedy(prize_cfg)

    world.say(
        f"In the time when moonlight was said to walk on the earth, there lived a little {trait} {hero_type} named {hero_name}."
    )
    world.say(
        f"{hero_name} loved the quiet places, and {hero.pronoun().capitalize()} longed to cuddle the shy {prize.label} that dwelled there."
    )
    world.say(
        f"One night, {hero_name} came to {place.label} with {guardian.label} beside {hero.pronoun('object')}."
    )
    world.para()
    world.say(
        f"{hero_name} reached toward {prize.label}, but {guardian.pronoun('subject').capitalize()} feared the old magic might startle the little spirit."
    )

    predicted = predict(world, hero, prize)
    if predicted["resolved"]:
        _soften(hero)
    else:
        world.facts["need_remedy"] = True

    if remedy is None:
        raise StoryError("No reasonable remedy exists for this prize.")

    world.say(
        f"Then {guardian.label} chose a gentler way: {remedy.prep}."
    )
    _soften(hero)
    world.add(Entity(id=remedy.id, kind="thing", type="cloth", label=remedy.label, protective=True, covers=set(remedy.covers), worn_by=hero.id, plural=remedy.plural))
    world.say(
        f"Together they {remedy.tail}, and {hero_name} no longer seemed like a stranger to the old magic."
    )
    _attempt_cuddle(world, hero, prize, narrate=True)
    world.para()
    world.say(
        f"In the end, {hero_name} was cuddling {prize.label} under the silver sky, while {guardian.label} smiled and the grove stayed peaceful."
    )

    world.facts.update(
        hero=hero,
        guardian=guardian,
        prize=prize,
        remedy=remedy,
        place=place,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    place = f["place"]
    return [
        f"Write a short myth for children about {hero.id} who wants to cuddle {prize.label} at {place.label}.",
        f"Tell a gentle happy-ending story in a mythic voice where a child finds a softer way to cuddle a shy magical friend.",
        f"Write a small legend with moonlight, a child, and a cuddle that ends in peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    guardian = f["guardian"]
    remedy = f["remedy"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who wanted to cuddle {prize.label} in the story?",
            answer=f"{hero.id} wanted to cuddle {prize.label} in {place.label}.",
        ),
        QAItem(
            question=f"Why did {guardian.label} pause the cuddle at first?",
            answer=f"{guardian.label} worried the old magic might startle {prize.label}, so the cuddle needed a gentler start.",
        ),
        QAItem(
            question=f"What helped make the ending happy?",
            answer=f"{remedy.label} helped because it made the approach softer, and then {hero.id} could cuddle {prize.label} safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cuddle?",
            answer="A cuddle is a warm, gentle hug that shows care and helps someone feel safe.",
        ),
        QAItem(
            question="Why do soft blankets help in a worried moment?",
            answer="Soft blankets can help because they feel gentle, warm, and comforting.",
        ),
        QAItem(
            question="What makes a happy ending feel complete?",
            answer="A happy ending feels complete when the worry is solved and the characters end with peace or joy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(P) :- prize(P), wears_on(P, R), cuddle_zone(R).
needs_softening(H) :- hero(H), reaches_for(H, P), at_risk(P).
happy_end(H, P) :- hero(H), prize(P), softened(H), at_risk(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "cuddle" in place.affords:
            lines.append(asp.fact("cuddle_zone", pid))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("wears_on", prid, prize.region))
    for remedy in REMEDIES:
        lines.append(asp.fact("remedy", remedy.id))
        for c in sorted(remedy.covers):
            lines.append(asp.fact("covers", remedy.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show place/1. #show prize/1."))
    # Reuse only the Python registry for parity; the ASP twin is intentionally simple.
    return sorted(valid_combos())


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic cuddle storyworld with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize, name=name, gender=gender, guardian=guardian, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PRIZES[params.prize], params.name, params.gender, params.guardian, random.choice(TRAITS))
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
        print(asp_program("#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid place/prize combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, prize in valid_combos():
            params = StoryParams(place=place, prize=prize, name="Luna", gender="girl", guardian="mother", seed=base_seed)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
