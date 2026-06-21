#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini/store_pound_sound_effects_kindness_ghost_story.py
===================================================================================

A small standalone story world for a child-friendly ghost-story in a store.

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: store, pound
Features: Sound Effects, Kindness
Style: Ghost Story

World premise
-------------
A child goes into a quiet old store where strange "pound" sounds seem spooky.
The sounds turn out to come from a trapped helper behind a wall, and kindness
plus careful listening leads to a gentle rescue. The ending proves the change:
the store is no longer scary, the hidden helper feels safe, and the child learns
that scary sounds can have a kind explanation.

This script follows the Storyweavers contract:
- stdlib only
- typed entities with meters and memes
- state-driven prose
- QA from world state
- inline ASP twin plus Python reasonableness gate
- --verify exercises generation and parity
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

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    quiet: bool = True
    spooky: bool = False
    wall: str = "the old wall"
    echoes: str = "the sound of the floorboards"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Noise:
    id: str
    sound: str
    source: str
    intensity: int = 1
    spooky: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class KindnessMove:
    id: str
    label: str
    method: str
    effect: str
    comfort: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spooky"] < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "store" in world.entities:
            world.get("store").meters["unease"] += 1
        out.append("__echo__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ghost" in world.entities:
            ghost = world.get("ghost")
            ghost.meters["safe"] += 1
            ghost.meters["spooky"] = max(0.0, ghost.meters["spooky"] - 1.0)
        if "store" in world.entities:
            world.get("store").meters["unease"] = max(0.0, world.get("store").meters["unease"] - 1.0)
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("echo", "sound", _r_echo), Rule("kindness", "social", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, noise: Noise, move: KindnessMove) -> bool:
    return place.spooky and noise.spooky and move.effect in {"safe", "calm"}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p.id, n.id, m.id) for p in PLACES.values() for n in NOISES.values() for m in MOVES.values()
            if reasonableness_gate(p, n, m)]


def predict(world: World, move: KindnessMove) -> dict:
    sim = world.copy()
    sim.get("child").memes["kindness"] += 1
    sim.get("ghost").meters["safe"] += 1
    sim.get("ghost").meters["spooky"] = max(0.0, sim.get("ghost").meters["spooky"] - 1.0)
    propagate(sim, narrate=False)
    return {
        "unease": sim.get("store").meters["unease"],
        "safe": sim.get("ghost").meters["safe"],
        "settled": sim.get("store").meters["unease"] < 1.0,
    }


def setup(world: World, place: Place, noise: Noise) -> None:
    world.say(
        f"On a chilly evening, {world.get('child').id} pushed open the door to {place.label}. "
        f"The air was still, and the only sound was {place.echoes}."
    )
    world.say(
        f"Then came a low {noise.sound}... pound, pound, pound... from somewhere deep in the store."
    )


def fright(world: World, child: Entity, place: Place, noise: Noise) -> None:
    child.memes["fear"] += 1
    world.say(
        f'{child.id} froze. "Did you hear that?" {child.pronoun()} whispered. '
        f'"Something is pounding in {place.label}."'
    )


def listen(world: World, child: Entity) -> None:
    child.memes["listening"] += 1
    world.say(
        f"{child.id} took a slow breath and listened again instead of running away."
    )


def reveal(world: World, ghost: Entity, place: Place) -> None:
    ghost.meters["spooky"] = 1.0
    ghost.memes["lonely"] += 1
    world.say(
        f"Behind a loose panel, {world.get('child').id} found a tiny ghost with a torn ribbon. "
        f"The little ghost was not mean at all -- just stuck and lonely in {place.label}."
    )


def kind_help(world: World, child: Entity, ghost: Entity, move: KindnessMove) -> None:
    child.memes["kindness"] += 1
    child.memes["bravery"] += 1
    ghost.meters["spooky"] = max(0.0, ghost.meters["spooky"] - 1.0)
    ghost.meters["safe"] += 1
    world.say(
        f'{child.id} smiled and used {move.method}. {move.comfort}'
    )
    world.say(
        f"The pounding stopped. The ghost stopped shaking and looked much happier."
    )


def ending(world: World, child: Entity, ghost: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    ghost.memes["relief"] += 1
    world.say(
        f"In the quiet store, {child.id} and the ghost waved goodbye. "
        f"Now the old store felt warm instead of scary, and the only pound left was "
        f"the child's happy heart."
    )


def tell(place: Place, noise: Noise, move: KindnessMove, child_name: str = "Mia", child_type: str = "girl",
         ghost_name: str = "Pip", ghost_type: str = "thing") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    ghost = world.add(Entity(id=ghost_name, kind="character", type=ghost_type, role="ghost", label="the ghost"))
    store = world.add(Entity(id="store", kind="place", type="place", label=place.label))
    world.add(Entity(id=noise.id, kind="thing", type="noise", label=noise.sound, role="noise"))
    world.add(Entity(id=move.id, kind="thing", type="help", label=move.label, role="help"))

    child.memes["curious"] += 1
    ghost.meters["spooky"] = 2.0
    store.meters["unease"] = 1.0

    setup(world, place, noise)
    world.para()
    fright(world, child, place, noise)
    listen(world, child)
    reveal(world, ghost, place)
    world.para()
    kind_help(world, child, ghost, move)
    propagate(world, narrate=False)
    ending(world, child, ghost, place)

    world.facts.update(
        child=child, ghost=ghost, store=store, place=place, noise=noise, move=move,
        outcome="kindly_resolved",
    )
    return world


PLACES = {
    "old_store": Place("old_store", "the old store", spooky=True, wall="the back wall", echoes="a dusty hum"),
    "thrift_shop": Place("thrift_shop", "the thrift store", spooky=True, wall="the shelf wall", echoes="a tiny creak"),
    "book_shop": Place("book_shop", "the quiet book store", spooky=True, wall="the tall shelves", echoes="a sleepy rustle"),
}

NOISES = {
    "pound": Noise("pound", "pound", "a hidden box behind the wall", intensity=2, spooky=True),
    "thud": Noise("thud", "thud", "something tapping in the back room", intensity=1, spooky=True),
    "bump": Noise("bump", "bump", "a loose board near the counter", intensity=1, spooky=True),
}

MOVES = {
    "gentle_tap": KindnessMove("gentle_tap", "a gentle tap", "a gentle tap on the panel", "safe", "The ghost's ribbon stopped snagging and it could breathe easier."),
    "kind_word": KindnessMove("kind_word", "kind words", "kind words and a soft hello", "safe", "The ghost heard a friendly voice and stopped trembling."),
    "careful_help": KindnessMove("careful_help", "careful help", "careful help with both hands", "safe", "The child held the loose panel steady until the ghost could slip free."),
}

NAMES = ["Mia", "Lily", "Ava", "Noah", "Theo", "Eli", "Rose", "Finn"]


@dataclass
@dataclass
class StoryParams:
    place: str
    noise: str
    move: str
    child_name: str
    child_type: str
    ghost_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story set in {f["place"].label} that includes the word "store" and the sound "pound".',
        f"Tell a spooky-but-kind story where {f['child'].id} hears pound, pound, pound in the store and helps the hidden ghost instead of running away.",
        f"Write a story with sound effects and kindness where a child listens carefully in an old store and discovers a lonely ghost."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    place = f["place"]
    noise = f["noise"]
    move = f["move"]
    return [
        QAItem(
            question="Where did the story happen?",
            answer=f"It happened in {place.label}. The quiet old store made the spooky sounds feel bigger at first."
        ),
        QAItem(
            question="What sound did the child hear?",
            answer=f"{child.id} heard {noise.sound}, pound, pound, pound. It sounded scary until the child listened closely and found the real source."
        ),
        QAItem(
            question="What did the child do to help?",
            answer=f"{child.id} used {move.method} and kindness. That helped the ghost feel safe, and the pounding stopped."
        ),
        QAItem(
            question="Why was the ghost making the sound?",
            answer=f"The ghost was stuck and lonely behind a loose panel. The sound was the ghost trying to get help, not trying to scare anyone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a store?", "A store is a place where people go to buy things. Some stores are quiet and a little spooky after dark."),
        QAItem("What does pound sound like?", "Pound is a heavy knocking sound. It can come from someone knocking on wood, a door, or a wall."),
        QAItem("What is kindness?", "Kindness means helping, sharing, and being gentle. Kind words can make a frightened friend feel safe."),
        QAItem("Why might a ghost story be spooky?", "Ghost stories can feel spooky because they often happen in dark places and use mysterious sounds. Even so, they can still end happily."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("old_store", "pound", "kind_word", "Mia", "girl", "Pip"),
    StoryParams("thrift_shop", "thud", "gentle_tap", "Noah", "boy", "Moss"),
    StoryParams("book_shop", "bump", "careful_help", "Ava", "girl", "Willow"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: store, pound, kindness, and a gentle ghost.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ghost")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.noise is None or c[1] == args.noise)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, noise, move = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    ghost = args.ghost or rng.choice(["Pip", "Moss", "Willow", "Bram"])
    return StoryParams(place, noise, move, name, gender, ghost)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], NOISES[params.noise], MOVES[params.move], params.child_name, params.child_type, params.ghost_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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


ASP_RULES = r"""
spooky(place) :- place(P), spooky_place(P).
valid(P, N, M) :- place(P), noise(N), move(M), spooky(P), spooky_noise(N), kind_move(M).
settled :- kindness_seen, ghost_safe.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.spooky:
            lines.append(asp.fact("spooky_place", pid))
    for nid, n in NOISES.items():
        lines.append(asp.fact("noise", nid))
        if n.spooky:
            lines.append(asp.fact("spooky_noise", nid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        if m.effect == "safe":
            lines.append(asp.fact("kind_move", mid))
    lines.append(asp.fact("kindness_seen"))
    lines.append(asp.fact("ghost_safe"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, noise=None, move=None, name=None, gender=None, ghost=None), _random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"FAIL: generation smoke test crashed: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
