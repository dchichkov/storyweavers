#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spoon_sharing_magic_folk_tale.py
==============================================================================================================

A tiny folk-tale storyworld about sharing a spoon and a little bit of magic.

Premise:
A child, a stranger, or a small household creature has one special spoon.
Someone else arrives hungry or in need, and a fair share must be found.
Magic may help the spoon reveal a kinder way to share, but only if the
characters act with generosity instead of grasping.

The model is intentionally small:
- physical state tracks ownership, fullness, sparkle, warmth, and wear
- emotional state tracks want, trust, gratitude, pride, and peace
- a shared spoon can be lent, divided, blessed, or returned
- a magical blessing only becomes useful when someone shares first

The resulting stories should feel like compact folk tales:
beginning, trouble, a wise turn, and a gentle ending image.
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
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    shared_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class CharacterSpec:
    type: str
    label: str
    phrase: str


@dataclass
class SpoonSpec:
    label: str
    phrase: str
    magic: bool = False


@dataclass
class StoryParams:
    setting: str
    hero: str
    guest: str
    spoon: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTINGS = {
    "cottage": "a little cottage by the lane",
    "forest": "a mossy hut at the edge of the forest",
    "village": "a bright house near the village well",
}

HEROES = {
    "girl": CharacterSpec("girl", "little girl", "a little girl"),
    "boy": CharacterSpec("boy", "little boy", "a little boy"),
    "grandmother": CharacterSpec("woman", "grandmother", "an old grandmother"),
    "woodcutter": CharacterSpec("man", "woodcutter", "a kindly woodcutter"),
}

GUESTS = {
    "fox": CharacterSpec("fox", "fox", "a hungry fox"),
    "rabbit": CharacterSpec("rabbit", "rabbit", "a tired rabbit"),
    "traveler": CharacterSpec("traveler", "traveler", "a dusty traveler"),
    "bird": CharacterSpec("bird", "bird", "a small blue bird"),
}

SPOONS = {
    "wooden": SpoonSpec("wooden spoon", "an old wooden spoon", magic=False),
    "silver": SpoonSpec("silver spoon", "a bright silver spoon", magic=True),
    "carved": SpoonSpec("carved spoon", "a carved spoon with little leaves", magic=True),
}

NAMES = ["Mina", "Luka", "Nia", "Borin", "Toma", "Elin", "Pavel", "Sava"]
GUEST_NAMES = ["Pip", "Rin", "Sora", "Moss", "Fin", "Tavi"]


ASP_RULES = r"""
shared(S) :- spoon(S).
needs_share(G) :- guest(G).
kindly_share(H,G,S) :- hero(H), guest(G), spoon(S), has_spoon(H,S), needs_share(G), willing_share(H).
magic_helps(S) :- spoon(S), magic_spoon(S), shared(S).
peaceful_end(H,G,S) :- kindly_share(H,G,S), magic_helps(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, spec in SPOONS.items():
        lines.append(asp.fact("spoon", sid))
        if spec.magic:
            lines.append(asp.fact("magic_spoon", sid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for gid in GUESTS:
        lines.append(asp.fact("guest", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show peaceful_end/3."))
    asp_res = set(asp.atoms(model, "peaceful_end"))
    py_res = set(valid_combos())
    if asp_res == py_res:
        print(f"OK: clingo gate matches valid_combos() ({len(py_res)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print(" only in clingo:", sorted(asp_res - py_res))
    print(" only in python:", sorted(py_res - asp_res))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero in HEROES:
            for guest in GUESTS:
                for spoon_id, spoon in SPOONS.items():
                    if spoon.magic:
                        combos.append((setting, hero, guest, spoon_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about sharing a spoon and a little magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--spoon", choices=SPOONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spoon and not SPOONS[args.spoon].magic:
        raise StoryError("This tale needs a magical spoon so sharing can change the ending.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hero is None or c[1] == args.hero)
              and (args.guest is None or c[2] == args.guest)
              and (args.spoon is None or c[3] == args.spoon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hero, guest, spoon = rng.choice(sorted(combos))
    return StoryParams(setting=setting, hero=hero, guest=guest, spoon=spoon)


def _line(world: World, text: str) -> None:
    world.say(text)


def generate_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero_spec = HEROES[params.hero]
    guest_spec = GUESTS[params.guest]
    spoon_spec = SPOONS[params.spoon]

    hero = world.add(Entity(
        id="hero", kind="character", type=hero_spec.type, label=hero_spec.label,
        phrase=hero_spec.phrase, meters={"hunger": 0.2, "satisfaction": 0.0, "peace": 0.0},
        memes={"want": 0.0, "trust": 0.0, "gratitude": 0.0, "pride": 0.2},
    ))
    guest = world.add(Entity(
        id="guest", kind="character", type=guest_spec.type, label=guest_spec.label,
        phrase=guest_spec.phrase, meters={"hunger": 0.7, "satisfaction": 0.0},
        memes={"want": 0.8, "trust": 0.0, "gratitude": 0.0},
    ))
    spoon = world.add(Entity(
        id="spoon", kind="thing", type="spoon", label=spoon_spec.label,
        phrase=spoon_spec.phrase, owner=hero.id, carries=hero.id,
        meters={"sparkle": 0.6 if spoon_spec.magic else 0.1, "wear": 0.0, "warmth": 0.3},
        memes={"magic": 1.0 if spoon_spec.magic else 0.0},
    ))

    hero_name = random.choice(NAMES)
    guest_name = random.choice(GUEST_NAMES)

    world.facts.update(hero=hero, guest=guest, spoon=spoon, hero_name=hero_name, guest_name=guest_name)

    _line(world, f"Once upon a time, in {world.setting}, there lived {hero_spec.phrase} named {hero_name}.")
    _line(world, f"{hero_name} kept {spoon_spec.phrase} by the hearth, and the spoon gleamed like a moonlit leaf.")
    _line(world, f"One day {guest_name} came to the door, hungry and shy, and asked for a little help.")

    world.para()
    hero.memes["want"] += 0.2
    guest.memes["want"] += 0.4
    _line(world, f"{hero_name} wanted to keep the spoon close, for it was dear to the household.")
    _line(world, f"But the bowl on the table was empty, and {guest_name} had come with an empty belly.")

    if spoon_spec.magic:
        spoon.meters["sparkle"] += 0.2
        _line(world, f"The spoon gave a soft twinkle, as if it knew a kinder answer was waiting.")
    else:
        _line(world, "The old spoon stayed plain and quiet, with no spell to help at all.")

    world.para()
    hero.memes["pride"] += 0.2
    if spoon_spec.magic:
        hero.memes["trust"] += 0.1
        _line(world, f"{hero_name} remembered the old saying: a gift grows by giving.")
        _line(world, f"So {hero_name} held out the spoon and shared the first sweet mouthful with {guest_name}.")
        hero.memes["want"] = max(0.0, hero.memes["want"] - 0.2)
        guest.memes["trust"] += 0.6
        guest.meters["satisfaction"] += 0.6
        spoon.meters["warmth"] += 0.5
        spoon.meters["wear"] += 0.1
        spoon.memes["magic"] = 1.0
        _line(world, f"At once the spoon shone brighter, and the porridge seemed to multiply kindly in the bowl.")
        _line(world, f"{guest_name} ate without fear, and {hero_name} found that sharing had made the meal feel larger.")
    else:
        _line(world, f"Yet the plain spoon could not make enough for two, so the tale would need a wiser tool.")
        _line(world, f"{hero_name} had to seek another spoon before the guest could be fed.")

    world.para()
    if spoon_spec.magic:
        hero.memes["gratitude"] += 0.5
        guest.memes["gratitude"] += 0.8
        hero.meters["satisfaction"] += 0.7
        hero.meters["peace"] += 0.8
        guest.meters["satisfaction"] += 0.9
        guest.meters["peace"] = 0.8
        world.facts["resolved"] = True
        _line(world, f"In the end, {hero_name} and {guest_name} sat side by side, and the spoon passed between them as gently as a blessing.")
        _line(world, f"When the last drop was gone, the spoon still glimmered, and nobody at the table was hungry.")
        _line(world, f"{hero_name} smiled to see that the best magic in the world was the kind that grows when it is shared.")
    else:
        world.facts["resolved"] = False

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_name = f["hero_name"]
    guest_name = f["guest_name"]
    spoon = f["spoon"]
    return [
        f"Write a short folk tale about {hero_name}, {guest_name}, and a magical spoon in {world.setting}.",
        f"Tell a gentle story where a child shares {spoon.phrase} with a hungry visitor.",
        "Write a simple tale about sharing and magic that ends with everyone feeling cared for.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guest = f["guest"]
    spoon = f["spoon"]
    hero_name = f["hero_name"]
    guest_name = f["guest_name"]
    qa = [
        QAItem(
            question=f"Who kept the spoon at the start of the story?",
            answer=f"{hero_name} kept the spoon by the hearth in {world.setting}, because it belonged to the household.",
        ),
        QAItem(
            question=f"Why did {guest_name} come to the door?",
            answer=f"{guest_name} came because they were hungry and needed help, so the meal could be shared.",
        ),
        QAItem(
            question=f"What changed when {hero_name} shared the spoon?",
            answer=f"The spoon shone brighter, the meal felt enough, and both {hero_name} and {guest_name} felt happier and safer.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the magic help the story end well?",
            answer="The magic grew brighter after the spoon was shared, and that blessing made the meal feel generous instead of scarce.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spoon for?",
            answer="A spoon is a small tool used for stirring, scooping, and eating soft food like porridge or soup.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, have, or enjoy part of something you have, so more than one person is helped.",
        ),
        QAItem(
            question="What is magic in a folk tale?",
            answer="Magic in a folk tale is a special, impossible helping power that can make ordinary things work in wondrous ways.",
        ),
    ]


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
        lines.append(
            f"  {e.id:6} ({e.kind:9}) owner={e.owner} carries={e.carries} "
            f"meters={{{', '.join(f'{k}: {v:.2f}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v:.2f}' for k, v in e.memes.items())}}}"
        )
    return "\n".join(lines)


def build_sample(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(setting="cottage", hero="girl", guest="fox", spoon="silver"),
    StoryParams(setting="forest", hero="grandmother", guest="rabbit", spoon="carved"),
    StoryParams(setting="village", hero="woodcutter", guest="traveler", spoon="silver"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show peaceful_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show peaceful_end/3."))
        triples = sorted(set(asp.atoms(model, "peaceful_end")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = build_sample(params)
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
            header = f"### {p.setting} / {p.hero} / {p.guest} / {p.spoon}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
