#!/usr/bin/env python3
"""
storyworlds/worlds/pharaoh_tree_kindness_happy_ending_tall_tale.py
===================================================================

A tiny tall-tale story world about a pharaoh, a tree, and a kind choice that
leads to a happy ending.

The seed image is simple:
- a proud pharaoh
- a lonely tree
- a dry place
- kindness that changes the outcome

The world is a small simulation: thirst, shade, water, growth, gratitude, and a
shared ending image that proves something changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    planted_by: Optional[str] = None
    planted_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"queen", "girl", "mother", "woman"}
        masculine = {"pharaoh", "king", "boy", "father", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dry: bool = True
    shade: bool = False
    water: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    trigger: str
    risk: str
    zone: str
    weather: str = ""
    keyword: str = ""


@dataclass
class Aid:
    id: str
    label: str
    action: str
    effect: str
    prep: str
    tail: str
    gives: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def trees(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.type == "tree"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_thirst(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.dry:
        return out
    for tree in world.trees():
        if tree.meters["water"] >= THRESHOLD:
            continue
        sig = ("thirst", tree.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        tree.memes["longing"] += 1
        out.append(f"The {tree.label} stood thirsty in the dry air.")
    return out


def _r_growth(world: World) -> list[str]:
    out: list[str] = []
    for tree in world.trees():
        if tree.meters["water"] < THRESHOLD:
            continue
        sig = ("growth", tree.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        tree.meters["growth"] += 1
        tree.memes["hope"] += 1
        out.append(f"The {tree.label} drank deep and began to grow brighter and taller.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["pride"] += 1
        out.append(f"{hero.id} felt glad to be gentle and wise.")
    return out


CAUSAL_RULES = [Rule("thirst", _r_thirst), Rule("growth", _r_growth), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def water_needed(need: Need) -> bool:
    return need.id == "tree"


def choose_aid(need: Need) -> Optional[Aid]:
    for aid in AIDS:
        if need.trigger in aid.gives:
            return aid
    return None


def predict_outcome(world: World, hero: Entity, need: Need, aid: Aid) -> dict:
    sim = world.copy()
    _apply_aid(sim, sim.get(hero.id), aid, narrate=False)
    tree = next(iter(sim.trees()), None)
    return {"grew": bool(tree and tree.meters["growth"] >= THRESHOLD),
            "water": tree.meters["water"] if tree else 0.0}


def _apply_aid(world: World, hero: Entity, aid: Aid, narrate: bool = True) -> None:
    hero.memes["kindness"] += 1
    if "water" in aid.gives:
        for tree in world.trees():
            tree.meters["water"] += 1
    if "shade" in aid.gives:
        world.setting.shade = True
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, tree: Entity) -> None:
    world.say(f"{hero.id} was a mighty pharaoh with a soft heart for small, living things.")
    world.say(f"In the palace court stood {tree.phrase}, waiting through the hot, dry day.")


def conflict(world: World, hero: Entity, tree: Entity, need: Need) -> None:
    world.say(
        f"{hero.id} saw that the {tree.label} was thirsty, for the {need.zone} held no cool water."
    )
    world.say(f"The wind felt like a whisper of hot dust, and the branches drooped low.")


def choose_kindness(world: World, hero: Entity, need: Need, aid: Aid) -> None:
    world.say(
        f"Then {hero.id} chose kindness. {hero.pronoun('possessive').capitalize()} advisers brought {aid.label}, "
        f"and {hero.id} made room for the thirsty tree."
    )
    world.say(f"{aid.prep}. {aid.tail}.")


def happy_ending(world: World, hero: Entity, tree: Entity, aid: Aid) -> None:
    world.say(
        f"Soon the {tree.label} stood straighter, with fresh leaves shining like green lanterns in the sun."
    )
    world.say(
        f"{hero.id} smiled at the tall tree, and the court seemed twice as grand because kindness had done the work."
    )


def tell(setting: Setting, need: Need, aid: Aid, hero_name: str = "Pharaoh Amun", tree_name: str = "Date Tree") -> World:
    world = World(setting)
    world.weather = need.weather

    hero = world.add(Entity(id=hero_name, kind="character", type="pharaoh", label="pharaoh"))
    tree = world.add(Entity(
        id=tree_name,
        kind="thing",
        type="tree",
        label="date tree",
        phrase="a tall date tree with a narrow trunk and dusty roots",
    ))

    introduce(world, hero, tree)
    world.para()
    conflict(world, hero, tree, need)
    hero.memes["concern"] += 1

    world.para()
    if aid is None:
        raise StoryError("No kind and useful aid exists for this dry-tree story.")
    choose_kindness(world, hero, need, aid)
    _apply_aid(world, hero, aid, narrate=True)

    world.para()
    happy_ending(world, hero, tree, aid)

    world.facts.update(hero=hero, tree=tree, need=need, aid=aid, setting=setting)
    return world


SETTINGS = {
    "court": Setting(place="the palace court", dry=True, shade=False, water=False, affords={"tree"}),
    "garden": Setting(place="the royal garden", dry=True, shade=False, water=False, affords={"tree"}),
    "oasis": Setting(place="the oasis garden", dry=False, shade=True, water=True, affords={"tree"}),
}

NEEDS = {
    "tree": Need(id="tree", trigger="tree", risk="thirst", zone="court", weather="hot", keyword="tree"),
}

AIDS = [
    Aid(
        id="water_jars",
        label="cool water jars",
        action="water the tree",
        effect="water",
        prep="The jars were carried in by careful hands",
        tail="The pharaoh poured the water around the roots",
        gives={"tree"},
    ),
    Aid(
        id="shade_cloth",
        label="a broad shade cloth",
        action="give the tree shade",
        effect="shade",
        prep="The cloth was lifted high between tall poles",
        tail="The tree rested in a kinder, cooler spot",
        gives={"tree"},
    ),
]

PHARAOH_NAMES = ["Pharaoh Amun", "Pharaoh Nari", "Pharaoh Sefu", "Pharaoh Tiya"]
TREE_NAMES = ["Date Tree", "Palm Tree", "Fig Tree"]
TRAITS = ["wise", "gentle", "grand", "bright-hearted"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for need_id, need in NEEDS.items():
            for aid in AIDS:
                if need.trigger in aid.gives and setting.affords:
                    combos.append((place, need_id, aid.id))
    return combos


@dataclass
class StoryParams:
    place: str
    need: str
    aid: str
    hero: str
    tree: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "tree": [
        ("What does a tree need to grow?",
         "A tree needs water, sunlight, and room for its roots to spread so it can grow strong."),
    ],
    "water": [
        ("Why do plants like water?",
         "Plants use water to stay alive and to help their roots and leaves grow."),
    ],
    "shade": [
        ("What is shade?",
         "Shade is a cool dark place made when something blocks the hot sunlight."),
    ],
    "kindness": [
        ("What is kindness?",
         "Kindness means choosing to help, share, or care for someone or something in a gentle way."),
    ],
    "pharaoh": [
        ("What is a pharaoh?",
         "A pharaoh was a ruler in ancient Egypt, like a king for the land by the river."),
    ],
    "oasis": [
        ("What is an oasis?",
         "An oasis is a place in a dry land where water and plants can be found."),
    ],
}

KNOWLEDGE_ORDER = ["pharaoh", "tree", "water", "shade", "kindness", "oasis"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a tall tale for a child about a pharaoh who notices a thirsty tree and chooses kindness.",
        f"Tell a short story where {f['hero'].id} helps {f['tree'].label} in {f['setting'].place} and ends with a happy ending.",
        f"Write a gentle ancient-Egypt story about a {f['tree'].label} that grows because {f['hero'].id} acts kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, tree, aid, setting = f["hero"], f["tree"], f["aid"], f["setting"]
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a {hero.traits[0] if hero.traits else 'kind'} pharaoh, and a tall {tree.label}.",
        ),
        QAItem(
            question=f"What problem did the {tree.label} have at first?",
            answer=f"The {tree.label} was thirsty because the day was dry and the ground in {setting.place} had no water for its roots.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help the tree?",
            answer=f"{hero.id} chose kindness and used {aid.label} to help the {tree.label} get the water or cool shade it needed.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the {tree.label} standing straighter and greener while {hero.id} smiled at the royal court.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"kindness", "pharaoh", "tree"}
    if f["setting"].shade:
        tags.add("shade")
    if f["setting"].water:
        tags.add("water")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
kind(Entity) :- hero(Entity).
kind_tree(Tree) :- tree(Tree).

needs_water(Tree) :- tree(Tree), dry_place.
kind_action(Hero, tree, Aid) :- hero(Hero), aid(Aid), gives(Aid, tree).

helpful(Place, tree, Aid) :- place(Place), aid(Aid), gives(Aid, tree).
valid_story(Place, tree, Aid) :- place(Place), helpful(Place, tree, Aid).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("dry_place"))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for g in sorted(aid.gives):
            lines.append(asp.fact("gives", aid.id, g))
    lines.append(asp.fact("hero", "pharaoh"))
    lines.append(asp.fact("tree", "tree"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = {(place, need, aid) for (place, need, aid) in asp_valid_stories()}
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - python_set))
    print("  only in python:", sorted(python_set - asp_set))
    return 1


def explain_rejection() -> str:
    return "(No story: this world needs a dry place, a thirsty tree, and a kind aid that can actually help.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: pharaoh, tree, kindness, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--aid", choices=[a.id for a in AIDS])
    ap.add_argument("--hero")
    ap.add_argument("--tree")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.aid and args.need:
        need = NEEDS[args.need]
        aid = next(a for a in AIDS if a.id == args.aid)
        if need.trigger not in aid.gives:
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.need is None or c[1] == args.need)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError(explain_rejection())
    place, need, aid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(PHARAOH_NAMES)
    tree = args.tree or rng.choice(TREE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, need=need, aid=aid, hero=hero, tree=tree, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], NEEDS[params.need], next(a for a in AIDS if a.id == params.aid),
                 hero_name=params.hero, tree_name=params.tree)
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


CURATED = [
    StoryParams(place="court", need="tree", aid="water_jars", hero="Pharaoh Amun", tree="Date Tree", trait="wise"),
    StoryParams(place="garden", need="tree", aid="shade_cloth", hero="Pharaoh Tiya", tree="Palm Tree", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for item in stories:
            print("  ", item)
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
            header = f"### {p.hero}: {p.need} at {p.place} (aid: {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
