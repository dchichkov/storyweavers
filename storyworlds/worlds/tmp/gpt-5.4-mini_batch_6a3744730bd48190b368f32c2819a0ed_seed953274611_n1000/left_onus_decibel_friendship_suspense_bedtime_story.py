#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/left_onus_decibel_friendship_suspense_bedtime_story.py
======================================================================================

A tiny bedtime-story world about friendship, a small suspenseful problem, and a
gentle resolution. The seed words are woven into the model as real state:
*left* as something that gets left behind, *onus* as the shared responsibility
to keep things calm, and *decibel* as the tiny sound level that must stay low.

The domain is intentionally small:
- two friends are getting ready for bed,
- a missing comfort object creates suspense,
- they search quietly,
- one friend takes on the onus of listening closely,
- a soft sound helps them find the missing thing,
- the ending proves the room is calm again.

The story reads like a bedtime story, but it is still state-driven: meters of
noise, worry, relief, and closeness change over time, and the prose reflects
those changes.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
QUIET_LIMIT = 3.0
LOUD_LIMIT = 6.0

NAME_PAIRS = [
    ("Mina", "Luca"),
    ("Ari", "Noa"),
    ("Pip", "Jules"),
    ("Tia", "Owen"),
    ("Nia", "Ben"),
]

PLACES = {
    "nursery": "the nursery",
    "attic_room": "the attic room",
    "cabin": "the little cabin",
}

OBJECTS = {
    "lantern": "a small lantern",
    "teddy": "a soft teddy bear",
    "blanket": "a striped blanket",
}

NOISES = {
    "thump": {"label": "a tiny thump", "decibel": 4, "source": "the floorboard"},
    "jingle": {"label": "a little jingle", "decibel": 3, "source": "the bedside bell"},
    "tap": {"label": "a soft tap", "decibel": 2, "source": "the window latch"},
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    place: str
    friend_a: str
    friend_b: str
    friendship: str
    suspense: str
    missing_item: str
    noise: str
    search_helper: str
    left_word: str = "left"
    onus_word: str = "onus"
    decibel_word: str = "decibel"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_noise_spreads(world: World) -> list[str]:
    out = []
    listener = world.get("friend_b")
    if world.get("room").meters["noise"] >= THRESHOLD and ("spread",) not in world.fired:
        world.fired.add(("spread",))
        listener.memes["worry"] += 1
        out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            sents = rule.apply(world)
            if len(world.fired) != before:
                changed = True
            if narrate:
                for s in sents:
                    if s:
                        world.say(s)


CAUSAL_RULES = [Rule("noise_spreads", _r_noise_spreads)]


def soothe(world: World) -> None:
    room = world.get("room")
    room.meters["noise"] = max(0.0, room.meters["noise"] - 2)
    for eid in ("friend_a", "friend_b"):
        world.get(eid).memes["worry"] = max(0.0, world.get(eid).memes["worry"] - 1)
        world.get(eid).memes["closeness"] += 1


def tell(world: World, params: StoryParams) -> None:
    a = world.add(Entity(id="friend_a", kind="character", type="girl", label=params.friend_a, role="friend"))
    b = world.add(Entity(id="friend_b", kind="character", type="boy", label=params.friend_b, role="friend"))
    room = world.add(Entity(id="room", type="room", label=PLACES[params.place]))
    item = world.add(Entity(id="item", type="thing", label=OBJECTS[params.missing_item]))
    noise = NOISES[params.noise]

    a.memes["closeness"] = 2
    b.memes["closeness"] = 2
    room.meters["noise"] = 1

    world.say(
        f"In {PLACES[params.place]}, {a.label} and {b.label} were getting ready for bed. "
        f"{a.label} found {params.left_word} little lamp on the sill, but {params.friendship.lower()} "
        f"kept them close and kind."
    )
    world.say(
        f"Then {b.label} noticed {params.missing_item.replace('_', ' ')} was missing. "
        f"The room grew soft and suspenseful, because bedtime felt a little uneven without it."
    )

    world.para()
    world.say(
        f"{a.label} took on the {params.onus_word} of looking quietly, while {b.label} held still and listened. "
        f'"We need to keep the {params.decibel_word} low," {a.label} whispered, '
        f'"or we will scare the dark away too fast."'
    )
    room.meters["noise"] += noise["decibel"]
    a.memes["courage"] += 1
    b.memes["worry"] += 1

    world.para()
    world.say(
        f"They searched by the bed, the chair, and the little rug. At last, there came "
        f"{noise["label"]} from {noise["source"]}."
    )
    room.meters["noise"] += 1
    world.say(
        f"{b.label} smiled first. {a.label} bent down and found the {params.missing_item.replace('_', ' ')} tucked there, "
        f"as if it had been waiting for a gentle rescue."
    )
    item.meters["found"] += 1
    world.facts["found"] = True

    world.para()
    soothe(world)
    world.say(
        f"The suspense melted out of the room. {a.label} and {b.label} tucked the {params.missing_item.replace('_', ' ')} into place, "
        f"and the little room became quiet again, with only a sleepy hush left behind."
    )
    world.say(
        f"Before long, the friends were side by side, brave in the dark, with friendship warm enough "
        f"to carry them safely to sleep."
    )

    world.facts.update(
        room=room,
        a=a,
        b=b,
        item=item,
        noise=noise,
        params=params,
        outcome="quiet",
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about friendship and suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing-item", choices=OBJECTS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--left-word", default="left")
    ap.add_argument("--onus-word", default="onus")
    ap.add_argument("--decibel-word", default="decibel")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, n) for p in PLACES for m in OBJECTS for n in NOISES]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in OBJECTS:
        lines.append(asp.fact("item", m))
    for n, info in NOISES.items():
        lines.append(asp.fact("noise", n))
        lines.append(asp.fact("decibel", n, info["decibel"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,N) :- place(P), item(M), noise(N).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    missing_item = args.missing_item or rng.choice(list(OBJECTS))
    noise = args.noise or rng.choice(list(NOISES))
    a, b = rng.choice(NAME_PAIRS)
    return StoryParams(
        place=place,
        friend_a=a,
        friend_b=b,
        friendship="Friendship",
        suspense="Suspense",
        missing_item=missing_item,
        noise=noise,
        search_helper="quiet listening",
        left_word=args.left_word,
        onus_word=args.onus_word,
        decibel_word=args.decibel_word,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.missing_item not in OBJECTS or params.noise not in NOISES:
        raise StoryError("Invalid story parameters.")
    world = World()
    tell(world, params)
    story = world.render()
    prompts = [
        f"Write a bedtime story about friendship and suspense that includes the words '{params.left_word}', '{params.onus_word}', and '{params.decibel_word}'.",
        f"Tell a gentle story where two friends search for a missing thing quietly at bedtime.",
        f"Write a calm story with a small mystery, soft voices, and a warm ending.",
    ]
    story_qa = [
        QAItem(
            question="What was the suspense in the story?",
            answer=f"The suspense came from the missing {params.missing_item.replace('_', ' ')} and the quiet search for it. The friends kept their voices low so the bedtime mood stayed gentle."
        ),
        QAItem(
            question=f"What was the {params.onus_word} of the friends?",
            answer=f"The {params.onus_word} was to look quietly and keep the room calm. That helped them find the missing thing without breaking the sleepy hush."
        ),
    ]
    world_qa = [
        QAItem(question="What is a decibel?", answer="A decibel is a way to talk about how loud or quiet a sound is. A smaller decibel means a softer sound."),
        QAItem(question="What does friendship help people do?", answer="Friendship helps people stay kind, listen to each other, and solve small problems together."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== story qa =="]
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
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {e.label_word} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", friend_a="Mina", friend_b="Luca", friendship="Friendship", suspense="Suspense", missing_item="teddy", noise="thump", search_helper="quiet listening"),
    StoryParams(place="cabin", friend_a="Ari", friend_b="Noa", friendship="Friendship", suspense="Suspense", missing_item="blanket", noise="jingle", search_helper="quiet listening"),
    StoryParams(place="attic_room", friend_a="Pip", friend_b="Jules", friendship="Friendship", suspense="Suspense", missing_item="lantern", noise="tap", search_helper="quiet listening"),
]


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if not ok:
        print("MISMATCH")
        print("py-only", sorted(py - cl))
        print("asp-only", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: {len(py)} combos; story generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
