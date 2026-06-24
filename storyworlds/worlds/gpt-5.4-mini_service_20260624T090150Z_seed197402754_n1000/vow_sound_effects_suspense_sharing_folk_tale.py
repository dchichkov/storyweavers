#!/usr/bin/env python3
"""
A small folk-tale storyworld about a vow, a shared treat, and a spooky little
suspense that turns into a kind ending.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    setting: str
    sounds: list[str] = field(default_factory=list)
    shares: list[str] = field(default_factory=list)
    spooky: bool = False


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    edible: bool = False
    shareable: bool = True


@dataclass
class StoryParams:
    place: str
    treasure: str
    hero_name: str
    hero_type: str
    helper_type: str
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def sound_effect(kind: str) -> str:
    return {
        "knock": "Tap-tap-tap!",
        "wind": "Whooooosh!",
        "owl": "Hoo-hoo!",
        "door": "Creak...",
        "sharing": "Nibble-nibble.",
    }.get(kind, "Tap!")


def build_places() -> dict[str, Place]:
    return {
        "cottage": Place(
            name="the little cottage",
            setting="by the lane",
            sounds=["knock", "door", "wind"],
            shares=["bread", "honeycake"],
            spooky=True,
        ),
        "forest": Place(
            name="the pine forest",
            setting="past the hill",
            sounds=["wind", "owl"],
            shares=["bread", "berries"],
            spooky=True,
        ),
        "mill": Place(
            name="the old mill",
            setting="near the river",
            sounds=["wind", "knock"],
            shares=["bread", "cheese"],
            spooky=False,
        ),
    }


TREASURES = {
    "bread": Treasure("bread", "round bread", "a round loaf of bread"),
    "honeycake": Treasure("honeycake", "honeycake", "a honey-sweet cake"),
    "berries": Treasure("berries", "berries", "a bowl of bright berries"),
    "cheese": Treasure("cheese", "cheese", "a wedge of cheese"),
}


HERO_NAMES = ["Mina", "Tobin", "Lina", "Pavel", "Anya", "Rowan"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["fox", "owl", "grandmother", "old man", "hare"]
TRAITS = ["brave", "gentle", "careful", "small", "steady"]


PLACES = build_places()


def vow_text(hero: Entity, treasure: Treasure, helper: str) -> str:
    return (
        f'"I make a vow," {hero.id} said softly. '
        f'"If the night grows strange, I will still share my {treasure.label} with a friend."'
    )


def detect_suspense(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> bool:
    if not world.place.spooky:
        return False
    return hero.memes.get("worry", 0.0) >= THRESHOLD and treasure.shareable


def reasonableness_gate(place: Place, treasure: Treasure) -> bool:
    return treasure.label in place.shares


def predict_story(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] = 1.0
    return {
        "suspense": detect_suspense(sim, sim.get(hero.id), sim.get(helper.id), treasure),
        "shared": True,
    }


def tell_story(place: Place, treasure: Treasure, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "kind"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(id=treasure.id, type=treasure.id, label=treasure.label, phrase=treasure.phrase, owner=hero.id))

    hero.meters["hunger"] = 1.0
    hero.memes["hope"] = 1.0

    world.say(
        f"Long ago, beside {place.name}, little {hero.id} lived with a warm heart and a quiet step."
    )
    world.say(
        f"That evening the wind began to sing, {sound_effect('wind')} and {sound_effect('owl')} from the trees."
    )
    world.say(
        f"{hero.id} carried {prize.phrase}, and {hero.id} liked how it smelled like home."
    )
    world.say(vow_text(hero, treasure, helper_type))

    world.para()
    world.say(
        f"Then came a small sound at the door: {sound_effect('knock')} {sound_effect('door')}"
    )
    helper.memes["mystery"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"{hero.id} held very still. In folk tales, a dark knock can mean a stranger, a riddle, or a trick."
    )

    if detect_suspense(world, hero, helper, treasure):
        world.say(
            f"But the little heart inside {hero.id} remembered the vow."
        )
        world.say(
            f'{hero.id} opened the door a little way and found {helper.pronoun("subject")} there, wet with rain and shivering.'
        )

    world.para()
    helper.meters["cold"] = 1.0
    world.say(
        f'"Please," said {helper.pronoun("subject")}, "may I have a bite?"'
    )
    world.say(
        f"{hero.id} looked at the loaf, then at the stranger, and cut it in two."
    )
    world.say(
        f"{sound_effect('sharing')} {hero.id} shared {prize.label} with the {helper.type}."
    )
    hero.memes["kindness"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    helper.memes["thankful"] = 1.0

    world.para()
    world.say(
        f"The {helper.type} smiled, and the rain seemed less sharp."
    )
    world.say(
        f"After that, the cottage felt bright, and the wind outside only hummed like a lullaby."
    )
    world.say(
        f"By the time the moon climbed high, {hero.id} had kept {hero.pronoun('possessive')} vow, and the last crumb was gone."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        place=place,
        treasure=treasure,
        suspense=detect_suspense(world, hero, helper, treasure),
        shared=True,
    )
    return world


SETTINGS = PLACES
PRIZES = TREASURES


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in SETTINGS.items():
        for tid, treasure in PRIZES.items():
            if reasonableness_gate(place, treasure):
                combos.append((pid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    place = f["place"]
    return [
        f"Write a short folk tale about {hero.id} and a vow made at {place.name}.",
        f"Tell a gentle suspense story where a child shares {treasure.phrase} after a mysterious knock.",
        f"Write a child-friendly tale with a wind sound, a little worry, and a sharing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["prize"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} vow to do if the night grew strange?",
            answer=f"{hero.id} vowed to share {hero.pronoun('possessive')} {treasure.label} with a friend.",
        ),
        QAItem(
            question=f"What sound did {hero.id} hear at the door in {place.name}?",
            answer=f"{hero.id} heard {sound_effect('knock').replace('!', '')} and a creaky door sound before looking outside.",
        ),
        QAItem(
            question=f"How did {hero.id} help the {helper.type} in the end?",
            answer=f"{hero.id} shared {treasure.label} with the {helper.type}, and the two of them were no longer lonely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vow?",
            answer="A vow is a serious promise someone makes and means to keep.",
        ),
        QAItem(
            question="What does a sharing ending mean in a story?",
            answer="It means the characters decide to give, divide, or enjoy something together instead of keeping it all for one person.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help readers hear the action in their minds, like knocking, whooshing wind, or soft nibbling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.

valid(P, T) :- place(P), treasure(T), shares(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.spooky:
            lines.append(asp.fact("spooky", pid))
        for s in p.shares:
            lines.append(asp.fact("shares", pid, s))
    for tid, t in PRIZES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_label", tid, t.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk tale world about a vow, suspense, and sharing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--treasure", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    if args.place or args.treasure:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.treasure is None or c[1] == args.treasure)
        ]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, treasure = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_type = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, treasure=treasure, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(SETTINGS[params.place], PRIZES[params.treasure], params.hero_name, params.hero_type, params.helper_type)
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
    StoryParams(place="cottage", treasure="bread", hero_name="Mina", hero_type="girl", helper_type="fox"),
    StoryParams(place="forest", treasure="berries", hero_name="Tobin", hero_type="boy", helper_type="owl"),
    StoryParams(place="mill", treasure="cheese", hero_name="Lina", hero_type="girl", helper_type="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for p, t in vals:
            print(p, t)
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
            header = f"### {p.hero_name}: {p.place} with {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
