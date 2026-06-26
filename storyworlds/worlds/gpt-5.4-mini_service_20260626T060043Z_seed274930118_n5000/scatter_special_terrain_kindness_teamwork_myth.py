#!/usr/bin/env python3
"""
A tiny myth-style storyworld about a special terrain where kindness and teamwork
turn scattered gifts into a shared blessing.

Premise:
- A small cast travels to a special terrain.
- One character has a handful of shining tokens that are meant to be scattered
  across the ground.
- The terrain is tricky, so kindness and teamwork matter.
- The story turns on a guided choice: scatter too freely and the task fails;
  scatter carefully together and the terrain is made special for everyone.

This script implements a self-contained world model, story renderer, QA sets,
and an ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

KINDNESS_THRESHOLD = 1.0
TEAMWORK_THRESHOLD = 1.0
SCATTER_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("scatter", "special", "terrain", "kindness", "teamwork", "joy", "hope"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    terrain: str
    special: str
    scatter_kind: str
    allows_repair: bool = True


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    gift: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACES = {
    "moon_garden": Place(
        name="the moon garden",
        terrain="silver stones",
        special="a quiet, special terrain",
        scatter_kind="blessed seeds",
        allows_repair=True,
    ),
    "river_steps": Place(
        name="the river steps",
        terrain="slippery stone",
        special="a winding, special terrain",
        scatter_kind="bright petals",
        allows_repair=True,
    ),
    "hill_circle": Place(
        name="the hill circle",
        terrain="windy grass",
        special="a high, special terrain",
        scatter_kind="small lantern flowers",
        allows_repair=True,
    ),
}

GIFTS = {
    "seeds": Gift(label="seeds", phrase="a bowl of shining seeds", type="seeds", plural=True),
    "petals": Gift(label="petals", phrase="a pouch of bright petals", type="petals", plural=True),
    "stones": Gift(label="stones", phrase="a little cloth bag of polished stones", type="stones", plural=True),
}

NAMES = ["Ari", "Mira", "Niko", "Luma", "Sorin", "Tala", "Ivo", "Rhea"]
TRAITS = ["kind", "gentle", "brave", "patient", "steady", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    return [(pname, gname) for pname, place in PLACES.items() for gname, gift in GIFTS.items() if place.scatter_kind != "" and gift.plural]


def place_for(gift: Gift) -> Place:
    for p in PLACES.values():
        if gift.label in p.scatter_kind or gift.label:
            return p
    return next(iter(PLACES.values()))


def can_scatter(place: Place, gift: Gift) -> bool:
    return place.allows_repair and gift.plural


def select_plan(place: Place, gift: Gift) -> bool:
    return can_scatter(place, gift)


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    gift = world.get("gift")
    helper = world.get("helper")
    if hero.meters["scatter"] < SCATTER_THRESHOLD:
        return out
    sig = ("scatter", hero.id, gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["scattered"] = True
    if hero.memes["kindness"] >= KINDNESS_THRESHOLD and helper.memes["teamwork"] >= TEAMWORK_THRESHOLD:
        gift.meters["special"] += 1
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        out.append(f"Together, they scattered the {gift.label} in a careful ring.")
    else:
        gift.meters["special"] += 0.2
        out.append(f"The {gift.label} fell in a loose pile, not the right pattern.")
    return out


def _r_bless_terrain(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    if gift.meters["special"] < SCATTER_THRESHOLD:
        return out
    sig = ("bless", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["terrain_blessed"] = True
    out.append("The special terrain seemed to shine a little brighter.")
    return out


RULES = [_r_scatter, _r_bless_terrain]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, hero: Entity, helper: Entity, gift: Entity) -> dict:
    sim = world.copy()
    sim.get("hero").meters["scatter"] += 1
    sim.get("hero").memes["kindness"] += 1
    sim.get("helper").memes["teamwork"] += 1
    propagate(sim, narrate=False)
    return {
        "blessed": sim.facts.get("terrain_blessed", False),
        "special": sim.get("gift").meters["special"],
    }


def tell(place: Place, gift_cfg: Gift, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["little", "kind"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, traits=["steady", "helpful"]))
    gift = world.add(Entity(id="gift", kind="thing", type=gift_cfg.type, label=gift_cfg.label, phrase=gift_cfg.phrase, plural=gift_cfg.plural))

    world.say(f"Long ago, {hero.label} walked to {place.name}, where the ground was {place.terrain} and the air felt old as a song.")
    world.say(f"{hero.pronoun().capitalize()} carried {gift_cfg.phrase}, because the gift was meant for the {place.special}.")
    world.para()
    world.say(f"There, {hero.label} met {helper.label}. {helper.pronoun().capitalize()} promised help, and both of them listened to the wind over the stones.")
    world.say(f"{hero.label} wanted to scatter the {gift.label}, but only a careful pattern would do; a careless toss would waste the blessing.")
    pred = predict(world, hero, helper, gift)
    world.facts.update(hero=hero, helper=helper, gift=gift, place=place, gift_cfg=gift_cfg, predicted=pred)
    if pred["blessed"]:
        hero.memes["kindness"] += 1
        helper.memes["teamwork"] += 1
    world.para()
    hero.meters["scatter"] += 1
    hero.memes["kindness"] += 1
    helper.memes["teamwork"] += 1
    world.say(f"So {hero.label} and {helper.label} knelt together. One placed, and one guided.")
    propagate(world, narrate=True)
    if world.facts.get("terrain_blessed"):
        world.say(f"In the end, the {gift.label} rested like stars on the ground, and the special terrain looked kind enough to shelter a whole village.")
    else:
        world.say(f"In the end, the {gift.label} stayed in a heap, and the terrain kept its secret waiting for a gentler try.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about kindness and teamwork on "{world.place.name}" with the word "scatter".',
        f"Tell a gentle legend where {f['hero'].label} and {f['helper'].label} learn to scatter {f['gift'].label} across a special terrain.",
        f"Create a tiny mythic story about a careful gift, a special terrain, and a kind helper who makes the plan work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    gift: Entity = f["gift"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"Where did {hero.label} and {helper.label} go with the {gift.label}?",
            answer=f"They went to {place.name}, a place with {place.terrain} and a very special feeling.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do with the {gift.label}?",
            answer=f"{hero.label} wanted to scatter the {gift.label} in a careful pattern so the terrain could be helped, not wasted.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} helped by working with {hero.label}, and their teamwork made the scattering careful and strong.",
        ),
    ]
    if f.get("terrain_blessed"):
        qa.append(
            QAItem(
                question="What changed at the end?",
                answer=f"The special terrain grew brighter because the {gift.label} was scattered with kindness and teamwork.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "scatter": [
        QAItem(
            question="What does it mean to scatter something?",
            answer="To scatter something means to spread it out over a wider area instead of keeping it in one pile.",
        )
    ],
    "special": [
        QAItem(
            question="What does special mean?",
            answer="Special means something is different in a good way and feels important or rare.",
        )
    ],
    "terrain": [
        QAItem(
            question="What is terrain?",
            answer="Terrain is the kind of ground or land in a place, like stone, grass, sand, or hills.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other reach the same goal.",
        )
    ],
    "myth": [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story people told to explain special places, brave deeds, or how something important came to be.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [item for key in ["scatter", "special", "terrain", "kindness", "teamwork", "myth"] for item in WORLD_KNOWLEDGE[key]]


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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A gift can be scattered when the hero tries and the helper joins in.
can_scatter(H, G) :- hero(H), gift(G).

% Kindness and teamwork make the scattering special.
special_scatter(H, X) :- kindness(H), teamwork(X).

% The terrain is blessed when a gift is scattered with kindness and teamwork.
blessed(T) :- terrain(T), special_scatter(_, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pname, place in PLACES.items():
        lines.append(asp.fact("place", pname))
        lines.append(asp.fact("terrain", pname, place.terrain))
        lines.append(asp.fact("special_place", pname, place.special))
        lines.append(asp.fact("scatter_kind", pname, place.scatter_kind))
    for gname, gift in GIFTS.items():
        lines.append(asp.fact("gift", gname))
        if gift.plural:
            lines.append(asp.fact("gift_plural", gname))
    lines.append(asp.fact("virtue", "kindness"))
    lines.append(asp.fact("virtue", "teamwork"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_pairs() -> list[tuple[str, str]]:
    return [(p, g) for p in PLACES for g in GIFTS if select_plan(PLACES[p], GIFTS[g])]


def asp_valid_story_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show can_scatter/2."))
    return sorted(set(asp.atoms(model, "can_scatter")))


def asp_verify() -> int:
    py = set(valid_story_pairs())
    cl = set(asp_valid_story_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_story_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about scatter, special terrain, kindness, and teamwork.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--gift", choices=GIFTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES.keys()))
    gift = args.gift or rng.choice(list(GIFTS.keys()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    if args.place and args.gift and not select_plan(PLACES[place], GIFTS[gift]):
        raise StoryError("No reasonable mythic story fits those explicit choices.")
    return StoryParams(place=place, gift=gift, hero_name=name, hero_type=hero_type, helper_name=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GIFTS[params.gift], params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="moon_garden", gift="seeds", hero_name="Ari", hero_type="girl", helper_name="Sorin", helper_type="boy"),
    StoryParams(place="river_steps", gift="petals", hero_name="Mira", hero_type="girl", helper_name="Niko", helper_type="boy"),
    StoryParams(place="hill_circle", gift="stones", hero_name="Tala", hero_type="girl", helper_name="Ivo", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show can_scatter/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_scatter/2."))
        pairs = sorted(set(asp.atoms(model, "can_scatter")))
        print(f"{len(pairs)} compatible stories:")
        for p, g in pairs:
            print(f"  {p:12} {g}")
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
            header = f"### {p.hero_name}: {p.gift} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
