#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/enclave_harp_happy_ending_surprise_suspense_rhyming.py
===============================================================================================================

A small rhyming storyworld about an enclave, a harp, a surprise, and a happy ending.

Premise:
- A child or small creature lives in a sheltered enclave.
- They find or cherish a harp.
- A surprise creates suspense: something unknown, hidden, or suddenly changed.
- Music, kindness, or courage turns worry into a happy ending.

The prose is intentionally rhythmic and child-facing, while the simulation tracks
physical meters and emotional memes so the story is driven by state rather than
template swapping.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    echo: str


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "moon_enclave": Setting(
        place="the moonlit enclave",
        mood="silver",
        echo="The little walls held the night like a bowl of light.",
    ),
    "wood_enclave": Setting(
        place="the mossy enclave",
        mood="green",
        echo="The trees leaned close and kept the wind polite.",
    ),
    "garden_enclave": Setting(
        place="the garden enclave",
        mood="bright",
        echo="The hedges made a secret ring, a cozy, quiet sight.",
    ),
}

ITEMS = {
    "harp": Item(label="harp", phrase="a little golden harp", type="harp"),
    "small_harp": Item(label="small harp", phrase="a small silver harp", type="harp"),
    "old_harp": Item(label="old harp", phrase="an old wooden harp", type="harp"),
}

TRAITS = ["brave", "gentle", "curious", "cheery", "patient", "shy"]
NAMES = ["Mina", "Lio", "Nia", "Pip", "Rosa", "Tavi", "Eli", "Zara"]


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def _conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("surprise", 0) >= THRESHOLD and ent.memes.get("worry", 0) >= THRESHOLD:
            sig = ("conflict", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["suspense"] = max(ent.memes.get("suspense", 0), 1.0)
            out.append("__suspense__")
    return out


def _music_calm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("music", 0) < THRESHOLD:
            continue
        if ent.memes.get("suspense", 0) < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] = 0.0
        ent.memes["joy"] = ent.memes.get("joy", 0) + 1.0
        out.append(f"The tune grew warm, and the worry grew small.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_conflict, _music_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__suspense__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_result(world: World, hero: Entity, item: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["music"] += 1
    sim.get(hero.id).memes["surprise"] += 1
    sim.get(hero.id).memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "calmed": sim.get(hero.id).memes.get("worry", 0) <= 0,
        "joy": sim.get(hero.id).memes.get("joy", 0),
    }


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.memes['trait_word']} {hero.type}, "
        f"small in size but big in delight."
    )


def setting_line(world: World) -> None:
    world.say(world.setting.echo)


def find_harp(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["curiosity"] += 1
    hero.memes["joy"] += 1
    item.owner = hero.id
    world.say(
        f"{hero.id} found {item.phrase} tucked by a stone, in a nook soft and white."
    )


def want_to_play(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["music"] += 1
    world.say(
        f"{hero.id} wanted to pluck the harp strings and sing to the night."
    )


def surprise(world: World, hero: Entity) -> None:
    hero.memes["surprise"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"Then came a surprise: a hush from above, and a flutter of light."
    )


def build_suspense(world: World, hero: Entity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"{hero.id} held still, heart thumping, and listened with care."
    )


def play_song(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["music"] += 1
    world.say(
        f"{hero.id} struck a soft chord on the harp, and a hush filled the air."
    )
    propagate(world, narrate=True)


def reveal_and_resolve(world: World, hero: Entity) -> None:
    if hero.memes.get("worry", 0) > 0:
        world.say(
            f"The surprise was no stormy ghost, but a tiny lost bird in a tear."
        )
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"{hero.id} played a lullaby tune, soft as a feather and clear."
    )
    world.say(
        f"The bird found its nest, the harp sang bright, and the enclave shone with a cheer."
    )


def tell(setting: Setting, item_cfg: Item, name: str, gender: str, trait: str, caretaker: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        memes={"trait_word": trait, "joy": 0.0, "surprise": 0.0, "worry": 0.0, "suspense": 0.0},
        meters={"curiosity": 0.0, "music": 0.0},
    ))
    parent = world.add(Entity(id="Caretaker", kind="character", type=caretaker))
    harp = world.add(Entity(
        id="Harp",
        type="harp",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=item_cfg.plural,
    ))

    intro(world, hero)
    setting_line(world)
    world.para()
    find_harp(world, hero, harp)
    want_to_play(world, hero, harp)
    surprise(world, hero)
    build_suspense(world, hero)
    play_song(world, hero, harp)
    world.para()
    reveal_and_resolve(world, hero)
    world.say(
        f"So the night went from hush to song, and all was well in the glow."
    )

    world.facts.update(hero=hero, parent=parent, harp=harp, setting=setting, item=item_cfg)
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place in SETTINGS:
        for item in ITEMS:
            combos.append((place, item))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a rhyming short story about {hero.id} in {f["setting"].place} with a harp, surprise, and suspense, ending happily.',
        f"Tell a child-sized rhyme where {hero.id} finds {f['item'].phrase} in an enclave and turns worry into a happy ending.",
        f"Make a gentle rhyming story with an enclave, a harp, a sudden surprise, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the harp?",
            answer=f"{hero.id} found the harp in {f['setting'].place}, tucked by a stone in a cozy nook.",
        ),
        QAItem(
            question=f"What surprise made the story suspenseful?",
            answer="A tiny lost bird fluttered from above, and that unknown little trouble made everyone hold still and listen.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily: the harp song calmed the moment, the bird found its nest, and the enclave shone bright again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an enclave?",
            answer="An enclave is a small, sheltered place that feels tucked away from the busy world, like a secret pocket of safety.",
        ),
        QAItem(
            question="What is a harp?",
            answer="A harp is a stringed musical instrument that makes soft, twinkly sounds when you pluck its strings.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to see what will happen next, especially when something is still unknown.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("label", iid, item.label))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, I) :- setting(S), item(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming enclave-and-harp story world with surprise and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if args.item and args.item not in ITEMS:
        raise StoryError("Unknown item.")
    if args.gender and args.item and args.gender not in ITEMS[args.item].genders:
        raise StoryError("That item does not fit the requested gender in this world.")
    return StoryParams(place=place, item=item, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], params.name, params.gender, params.trait, params.caretaker)
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
    StoryParams(place="moon_enclave", item="harp", name="Mina", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(place="wood_enclave", item="small_harp", name="Pip", gender="boy", caretaker="father", trait="shy"),
    StoryParams(place="garden_enclave", item="old_harp", name="Rosa", gender="girl", caretaker="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
