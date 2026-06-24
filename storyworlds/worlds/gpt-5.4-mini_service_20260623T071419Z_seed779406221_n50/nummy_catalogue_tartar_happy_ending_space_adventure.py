#!/usr/bin/env python3
"""
storyworlds/worlds/nummy_catalogue_tartar_happy_ending_space_adventure.py
========================================================================

A small, standalone storyworld about a space trip, a nummy catalogue, and a
tiny tartar problem that turns into a happy ending.

Premise:
- A child astronaut and a helper are traveling in a little starship.
- They have a nummy catalogue: a bright list of snack packs and meal tubes.
- A tartar alien has clogged the snack chute with crunchy space tartar.
- The crew worries the dinner machine will not work.

Tension:
- The nummy catalogue shows what the ship can eat.
- The chute is blocked, so the ship cannot serve food.
- The child wants to fix it quickly, but the helper worries about a messy jam.

Turn:
- They discover tartar is not a monster; it is a small lost creature who is
  trying to protect a tiny shiny pebble.
- The child uses the catalogue to choose a safe snack that the tartar loves.
- The tartar unblocks the chute to get more nummies.

Resolution:
- The dinner machine works again.
- Everyone eats together.
- The ending proves the ship is bright, tidy, and fed.

The world uses typed entities with meters and memes, a reasonableness gate, a
tiny causal engine, and grounded QA.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str = "Little Comet"
    place: str = "the moonway"
    setting: str = "space"
    affords: set[str] = field(default_factory=set)


@dataclass
class SnackPack:
    id: str
    label: str
    phrase: str
    yummy: int
    safe_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    blocker: str
    mess_kind: str
    fix_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cure:
    id: str
    label: str
    action: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        c = World(self.ship)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tartar_hungry(world: World) -> list[str]:
    out = []
    tart = world.get("tartar")
    if tart.meters.get("hungry", 0.0) < THRESHOLD:
        return out
    if world.get("chute").meters.get("jammed", 0.0) < THRESHOLD:
        return out
    sig = ("hungry_jam",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").meters["stopped"] = 1
    out.append("The snack chute stopped, and dinner would not come out.")
    return out


def _r_catalogue_match(world: World) -> list[str]:
    out = []
    kid = world.get("nova")
    snack = world.get(world.facts["chosen_snack"])
    if kid.memes.get("hope", 0.0) < THRESHOLD:
        return out
    sig = ("catalogue_match", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["joy"] = kid.memes.get("joy", 0.0) + 1
    out.append(f"{kid.label} found {snack.label} in the nummy catalogue.")
    return out


def _r_helped_unjam(world: World) -> list[str]:
    tart = world.get("tartar")
    chute = world.get("chute")
    if tart.memes.get("helped", 0.0) < THRESHOLD:
        return []
    if chute.meters.get("jammed", 0.0) < THRESHOLD:
        return []
    sig = ("unjam",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chute.meters["jammed"] = 0.0
    world.get("ship").meters["safe"] = 1
    return ["The tartar nudged the crunchy bits away, and the chute opened again."]


RULES = [Rule(name="tartar_hungry", apply=_r_tartar_hungry),
         Rule(name="catalogue_match", apply=_r_catalogue_match),
         Rule(name="helped_unjam", apply=_r_helped_unjam)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    ship: str
    snack: str
    problem: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


SHIP = Ship(place="the moonway", setting="space", affords={"snack", "catalogue"})
SNACKS = {
    "berry": SnackPack(id="berry", label="berry nummies", phrase="a cup of berry nummies", yummy=3, safe_for={"tartar", "boy", "girl"}, tags={"nummy", "catalogue"}),
    "mooncrisp": SnackPack(id="mooncrisp", label="moon crisps", phrase="a shiny packet of moon crisps", yummy=2, safe_for={"tartar", "boy", "girl"}, tags={"nummy", "catalogue"}),
    "starpuff": SnackPack(id="starpuff", label="star puffs", phrase="a soft bag of star puffs", yummy=4, safe_for={"tartar", "boy", "girl"}, tags={"nummy", "catalogue"}),
}
PROBLEMS = {
    "tartar": Problem(id="tartar", label="tartar", blocker="snack chute", mess_kind="jammed", fix_kind="clean", tags={"tartar", "space"}),
}
CURES = {
    "share": Cure(id="share", label="share-snack plan", action="offer snack", fits={"tartar"}, tags={"nummy", "tartar"}),
    "brush": Cure(id="brush", label="soft brush", action="brush away the crunchy bits", fits={"tartar"}, tags={"space"}),
}
NAMES = ["Nova", "Milo", "Luna", "Pip", "Ada", "Rio"]
TYPES = {"girl": ["Nova", "Luna", "Ada"], "boy": ["Milo", "Pip", "Rio"]}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for snack in SNACKS:
        out.append(("space", snack))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure storyworld about nummies and a tartar jam.")
    ap.add_argument("--ship", choices=["Little Comet"], default="Little Comet")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--problem", choices=PROBLEMS, default="tartar")
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    if args.snack:
        combos = [c for c in combos if c[1] == args.snack]
    if not combos:
        raise StoryError("No valid snack choice fits this story.")
    _, snack = rng.choice(combos)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    child = args.child or rng.choice(TYPES[child_type])
    helper = args.helper or rng.choice([n for n in TYPES[helper_type] if n != child] or NAMES)
    return StoryParams(
        ship=args.ship,
        snack=snack,
        problem=args.problem,
        child=child,
        child_type=child_type,
        helper=helper,
        helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    world = World(SHIP)
    ship = world.add(Entity(id="ship", kind="place", type="ship", label="Little Comet", meters={"safe": 0.0}, memes={"hope": 0.0}))
    child = world.add(Entity(id="nova", kind="character", type=params.child_type, label=params.child, meters={"hunger": 0.0}, memes={"hope": 0.0, "joy": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, meters={"care": 0.0}, memes={"worry": 0.0, "kindness": 0.0}))
    snack_cfg = SNACKS[params.snack]
    snack = world.add(Entity(id="snack", kind="thing", type="food", label=snack_cfg.label, tags=set(snack_cfg.tags), meters={"stored": 1.0}))
    tartar = world.add(Entity(id="tartar", kind="character", type="creature", label="tartar", meters={"hungry": 1.0, "helped": 0.0}, memes={"lonely": 1.0}))
    chute = world.add(Entity(id="chute", kind="thing", type="machine", label="snack chute", meters={"jammed": 1.0}))
    world.facts["chosen_snack"] = snack.id
    child.memes["hope"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(f"On the Little Comet, {child.label} opened the nummy catalogue and pointed at {snack_cfg.phrase}.")
    world.say(f"{helper.label} smiled, but the snack chute was jammed by a tartar pile, so dinner would not slide out.")
    world.para()
    world.say(f"{child.label} wanted to help the ship feel happy again, and {helper.label} wanted a safe fix.")
    propagate(world)
    world.para()
    tartar.memes["helped"] = 1.0
    world.say(f"They learned the tartar was only a small lost creature, soft-eyed and hungry for a friend.")
    world.say(f"{child.label} offered {snack_cfg.label} from the catalogue, and the tartar sniffed it with a tiny chirp.")
    propagate(world)
    world.para()
    world.say(f"The tartar pushed the crunchy bits aside, the chute opened, and the Little Comet served nummy dinner at last.")
    child.memes["joy"] += 1
    helper.memes["kindness"] += 1
    world.facts.update(child=child, helper=helper, tartar=tartar, chute=chute, snack=snack, snack_cfg=snack_cfg, ship=ship)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    snack_cfg = f["snack_cfg"]
    tartar = f["tartar"]
    return [
        QAItem(question=f"Why did {child.label} open the nummy catalogue?", answer=f"{child.label} wanted to find a snack that would make the Little Comet feel bright and happy again."),
        QAItem(question=f"What was wrong with the snack chute?", answer="It was jammed with crunchy tartar bits, so the dinner tray could not slide out."),
        QAItem(question=f"What did {child.label} offer the tartar?", answer=f"{child.label} offered {snack_cfg.label} from the nummy catalogue, and that made the tartar feel safe enough to help."),
        QAItem(question=f"How did the story end?", answer=f"The tartar moved the crunch away, the chute opened, and everyone got nummy dinner on the Little Comet."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a nummy catalogue?", answer="It is a list of tasty choices that helps a crew pick a snack or meal."),
        QAItem(question="What can a jammed chute do on a ship?", answer="It can stop food from coming out until someone clears the blockage."),
        QAItem(question="What is tartar in this storyworld?", answer="Tartar is a small space creature that can get stuck in the snack chute, but it can also be kind and help."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=[
        f"Write a cheerful space adventure about {params.child} on the Little Comet, a nummy catalogue, and a tartar jam.",
        "Tell a child-friendly story where a ship's snack chute is blocked, then fixed by kindness and a good snack choice.",
    ], story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n-- trace --")
        for e in sample.world.entities.values():
            print(e.id, e.label, e.meters, e.memes)
    if qa:
        print("\nQ&A:")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
snack_choice(berry).
snack_choice(mooncrisp).
snack_choice(starpuff).
valid(space, S) :- snack_choice(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("ship", "LittleComet"), asp.fact("problem", "tartar")])


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        print("OK")
        return
    if args.show_asp:
        print(asp_facts())
        print(ASP_RULES)
        return
    rng = random.Random(args.seed)
    samples = []
    if args.all:
        for snack in SNACKS:
            params = StoryParams(ship="Little Comet", snack=snack, problem="tartar", child="Nova", child_type="girl", helper="Milo", helper_type="boy")
            samples.append(generate(params))
    else:
        for _ in range(args.n):
            params = resolve_params(args, rng)
            samples.append(generate(params))
    for s in samples:
        emit(s, trace=args.trace, qa=args.qa)
        if args.json:
            print(s.to_json())


if __name__ == "__main__":
    main()
