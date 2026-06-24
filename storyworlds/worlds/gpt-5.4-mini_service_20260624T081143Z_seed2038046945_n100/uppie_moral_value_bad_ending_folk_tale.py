#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/uppie_moral_value_bad_ending_folk_tale.py
===============================================================================================================

A small folk-tale storyworld about uppie, a moral test, and a bad ending.

Premise:
- A child or traveler wants something easy and shiny.
- Uppie is a tiny forest helper who offers a shortcut or bargain.
- The bargain promises quick gain, but it costs a kind act or a shared rule.
- The hero chooses badly, then loses something important.

The world is intentionally classical and simple: a few typed entities, a few
meters and memes, and a state-driven turn toward a bad ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wealth": 0.0, "loss": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"greed": 0.0, "kindness": 0.0, "fear": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    has_path: bool = True
    has_bridge: bool = False
    has_well: bool = False
    has_tree: bool = False


@dataclass
class Bargain:
    id: str
    offer: str
    cost: str
    result: str
    moral: str
    loss_kind: str
    gain_kind: str
    needs: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    bargain: str
    seed: Optional[int] = None


PLACES = {
    "village": Place("the village", "village", has_path=True, has_bridge=True, has_tree=True),
    "woods": Place("the woods", "woods", has_path=True, has_tree=True),
    "river": Place("the riverbank", "river", has_path=True, has_bridge=True),
    "hill": Place("the hill", "hill", has_path=True, has_tree=True),
}

BARGAINS = {
    "golden_berry": Bargain(
        id="golden_berry",
        offer="a basket of golden berries",
        cost="share one berry with the old woman at the path",
        result="the berries would glow in the dark",
        moral="sharing matters more than quick riches",
        loss_kind="berries",
        gain_kind="gold",
        needs={"tree"},
    ),
    "silver_song": Bargain(
        id="silver_song",
        offer="a silver song from the brook",
        cost="tell the truth about the broken cup",
        result="the song would lead home faster",
        moral="truth keeps a heart light",
        loss_kind="way",
        gain_kind="time",
        needs={"path"},
    ),
    "small_lantern": Bargain(
        id="small_lantern",
        offer="a small lantern with a bright flame",
        cost="leave bread for the hungry fox",
        result="the lantern would never go out",
        moral="kindness can light the road",
        loss_kind="lantern",
        gain_kind="light",
        needs={"path"},
    ),
}

NAMES = ["Milo", "Tessa", "Pip", "Nina", "Bram", "Lena", "Jory", "Sela"]
HERO_TYPES = ["boy", "girl"]


class WorldState:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale world about uppie, moral value, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bargain", choices=BARGAINS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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


def reasonableness_gate(params: StoryParams) -> None:
    place = PLACES[params.place]
    bargain = BARGAINS[params.bargain]
    if "tree" in bargain.needs and not place.has_tree:
        raise StoryError("This bargain needs a treey place for the folk-tale bargain to make sense.")
    if "path" in bargain.needs and not place.has_path:
        raise StoryError("This bargain needs a path so the traveler can meet uppie on the road.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    bargain = args.bargain or rng.choice(list(BARGAINS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero = args.hero or rng.choice(NAMES)
    params = StoryParams(place=place, hero=hero, hero_type=hero_type, bargain=bargain)
    reasonableness_gate(params)
    return params


def _story_intro(world: World, hero: Entity, barg: Bargain) -> None:
    world.say(f"Once, in {world.place.name}, there lived a little {hero.type} named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} loved the shine of small treasures and dreamed of getting {barg.offer}.")


def _meet_uppie(world: World, hero: Entity, barg: Bargain) -> None:
    uppie = world.add(Entity(id="uppie", kind="character", type="sprite", label="uppie"))
    uppie.memes["hope"] += 1
    world.say(
        f"By the path sat uppie, a tiny sprite with twig-brown shoes and a voice like a bell."
        f' "Take my bargain," said uppie, "and you will have {barg.result}."'
    )
    hero.memes["hope"] += 1
    hero.meters["wealth"] += 1


def _warn(world: World, hero: Entity, barg: Bargain) -> None:
    world.say(
        f"An old sign by the lane whispered the rule: {barg.cost}."
        f" But {hero.id} listened only to the bright promise."
    )


def _choose_badly(world: World, hero: Entity, barg: Bargain) -> None:
    hero.memes["greed"] += 2
    hero.memes["kindness"] -= 1
    world.say(
        f"{hero.id} chose the easy gleam and would not share, would not confess, would not leave bread."
        f" {hero.pronoun().capitalize()} took the bargain and stepped past the warning."
    )


def _consequence(world: World, hero: Entity, barg: Bargain) -> None:
    sig = ("loss", barg.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["loss"] += 1
    hero.memes["fear"] += 2
    if barg.id == "golden_berry":
        world.say(
            f"The berries turned dull as mud in {hero.pronoun('possessive')} hands, and the old woman took the basket away."
        )
    elif barg.id == "silver_song":
        world.say(
            f"The silver song broke into thin little cracks, and {hero.id} could no longer find the way home at once."
        )
    else:
        world.say(
            f"The small lantern guttered out in the fog, and the dark road grew long and cold."
        )


def _ending(world: World, hero: Entity, barg: Bargain) -> None:
    world.say(
        f"In the end, {hero.id} went home with less than before, and remembered that {barg.moral}."
    )
    world.say(
        f"Uppie was gone by morning, and the empty place where the bargain had gleamed looked colder than the rest of the road."
    )


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    barg = BARGAINS[params.bargain]
    _story_intro(world, hero, barg)
    world.para()
    _meet_uppie(world, hero, barg)
    _warn(world, hero, barg)
    _choose_badly(world, hero, barg)
    world.para()
    _consequence(world, hero, barg)
    _ending(world, hero, barg)
    world.facts.update(hero=hero, bargain=barg, place=world.place)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    barg = world.facts["bargain"]
    return [
        QAItem(
            question=f"Who met uppie in {world.place.name}?",
            answer=f"{hero.id} met uppie in {world.place.name}.",
        ),
        QAItem(
            question=f"What did uppie offer {hero.id}?",
            answer=f"Uppie offered {hero.id} {barg.offer}.",
        ),
        QAItem(
            question=f"Why did things end badly for {hero.id}?",
            answer=f"Things ended badly because {hero.id} chose the easy bargain and did not keep the rule to {barg.cost}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a story passed along for a long time, usually with a lesson, a little magic, and a clear ending.",
        ),
        QAItem(
            question="What is greed?",
            answer="Greed is wanting more than you should and caring too much about getting a reward.",
        ),
        QAItem(
            question="Why can a broken promise cause trouble?",
            answer="A broken promise can cause trouble because other people stop trusting the one who broke it, and the choice may bring a loss.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    barg = world.facts["bargain"]
    return [
        f"Write a short folk tale about {hero.id}, uppie, and {barg.offer}.",
        f"Tell a moral-value story where a small hero ignores a fair rule and learns a hard lesson.",
        f"Make a bad-ending tale in which uppie offers a tempting bargain and the hero chooses wrongly.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
place(village; woods; river; hill).
hero_type(boy; girl).
bargain(golden_berry; silver_song; small_lantern).

needs(golden_berry, tree).
needs(silver_song, path).
needs(small_lantern, path).

has_tree(village; woods; hill).
has_path(village; woods; river; hill).

compatible(P,B) :- bargain(B), place(P), needs(B, tree), has_tree(P).
compatible(P,B) :- bargain(B), place(P), needs(B, path), has_path(P).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for b in BARGAINS:
        lines.append(asp.fact("bargain", b))
    for p, place in PLACES.items():
        if place.has_tree:
            lines.append(asp.fact("has_tree", p))
        if place.has_path:
            lines.append(asp.fact("has_path", p))
    for b, bargain in BARGAINS.items():
        for need in sorted(bargain.needs):
            lines.append(asp.fact("needs", b, need))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    clingo_set = set(asp.atoms(model, "compatible"))
    py_set = set()
    for p, place in PLACES.items():
        for b, bargain in BARGAINS.items():
            ok = True
            if "tree" in bargain.needs and not place.has_tree:
                ok = False
            if "path" in bargain.needs and not place.has_path:
                ok = False
            if ok:
                py_set.add((p, b))
    if clingo_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} compatible pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(clingo_set - py_set))
    print("only in Python:", sorted(py_set - clingo_set))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="village", hero="Milo", hero_type="boy", bargain="golden_berry"),
        StoryParams(place="woods", hero="Tessa", hero_type="girl", bargain="silver_song"),
        StoryParams(place="river", hero="Pip", hero_type="boy", bargain="small_lantern"),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero=args.hero or rng.choice(NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        bargain=args.bargain or rng.choice(list(BARGAINS)),
    )
    reasonableness_gate(params)
    return params


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for p, b in sorted(set(asp.atoms(model, "compatible"))):
            print(p, b)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
