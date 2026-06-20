#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dive_sharing_rhyme_happy_ending_rhyming_story.py
=================================================================================

A standalone story world for a tiny rhyming tale about two children, a pool,
a springboard, and a shared toy that makes the dive safe and fun.

Core idea
---------
Two children want to dive into the same little pool. One is faster and tries to
go first, but the other has the float ring they both need. A simple sharing beat
turns the moment from a squabble into a rhyme-filled, happy ending: they share
the ring, take turns, and both splash in with smiles.

This world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- state-driven story beats
- a reasonableness gate
- an inline ASP twin for parity checks
- three QA sets grounded in the simulated world

Seed words/features/style:
- dive
- Sharing
- Rhyme
- Happy Ending
- Rhyming Story
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
JOY_BOOST = 1.0
RHYME_BOOST = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"splash": 0.0, "wet": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "sharing": 0.0})

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
class Pool:
    id: str
    label: str
    depth: str
    sparkle: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

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
class Toy:
    id: str
    label: str
    phrase: str
    shares: bool = True
    bouncy: bool = False
    tags: set[str] = field(default_factory=set)

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.meters["splash"] < THRESHOLD:
            continue
        sig = ("wet", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["wet"] += 1.0
        ent.memes["joy"] += 1.0
        out.append(f"{ent.id} got wet and laughed.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("A")
    b = world.entities.get("B")
    if not a or not b:
        return out
    if a.memes["sharing"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["joy"] += JOY_BOOST
    b.memes["joy"] += JOY_BOOST
    world.get("toy").meters["shared"] = 1.0
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("wet", _r_wet), Rule("share", _r_share)]


def race_worry(world: World, winner: Entity, other: Entity, toy: Toy) -> None:
    winner.memes["worry"] += 1.0
    world.say(
        f"{winner.id} reached the edge first and held tight to {toy.phrase}. "
        f"{other.id} leaned close and frowned."
    )


def ask_share(world: World, seeker: Entity, holder: Entity, toy: Toy) -> None:
    seeker.memes["sharing"] += 1.0
    world.say(
        f'"{holder.id}, may I share {toy.phrase}?" {seeker.id} asked with a rhyme. '
        f'"A turn for me, a turn for thee?"'
    )


def share_toy(world: World, a: Entity, b: Entity, toy: Toy) -> None:
    a.memes["sharing"] += 1.0
    b.memes["sharing"] += 1.0
    world.say(
        f'{a.id} smiled and passed it on. "{toy.label} for you, then me," '
        f'{a.id} sang. "We can be a team, you see."'
    )


def dive_act(world: World, diver: Entity, toy: Toy, pool: Pool) -> None:
    diver.meters["splash"] += 1.0
    diver.meters["wet"] += 1.0
    world.say(
        f"{diver.id} took a brave little dive into the {pool.label}. "
        f"{pool.sparkle} and {pool.depth} made the water bright."
    )


def ending(world: World, a: Entity, b: Entity, pool: Pool) -> None:
    world.say(
        f"In the end, {a.id} and {b.id} took turns and shared with care. "
        f"They both dove in, the splash went high, and the day stayed sweet."
    )


def tell(pool: Pool, toy: Toy, a_name: str = "Mia", a_gender: str = "girl",
         b_name: str = "Leo", b_gender: str = "boy") -> World:
    world = World()
    a = world.add(Entity(a_name, "character", a_gender, role="first"))
    b = world.add(Entity(b_name, "character", b_gender, role="second"))
    pool_ent = world.add(Entity("pool", "thing", "pool", label=pool.label))
    world.add(Entity("toy", "thing", "toy", label=toy.label))

    world.say(
        f"On a sunny day, {a.id} and {b.id} found {pool.label}. "
        f"It shimmered {pool.sparkle}, and both children wanted a dive."
    )
    world.say(
        f"Only one toy could help: {toy.phrase}. "
        f"{a.id} grabbed it, but {b.id} wanted a turn too."
    )

    world.para()
    race_worry(world, a, b, toy)
    ask_share(world, b, a, toy)
    world.say('The tiny rhyme calmed the air: "Share with cheer, then splash right here!"')

    world.para()
    share_toy(world, a, b, toy)
    propagate(world, narrate=True)
    dive_act(world, a, toy, pool)
    dive_act(world, b, toy, pool)
    propagate(world, narrate=True)

    world.para()
    ending(world, a, b, pool)
    world.facts.update(a=a, b=b, pool=pool, toy=toy, outcome="shared")
    return world


POOLS = {
    "yard": Pool("yard", "little backyard pool", "not too deep", "with silver sparkles", tags={"pool", "dive"}),
    "lake": Pool("lake", "small lake cove", "calm and shallow", "with blue sparkles", tags={"pool", "dive"}),
    "pond": Pool("pond", "round pond", "soft and shallow", "with green sparkles", tags={"pool", "dive"}),
}

TOYS = {
    "ring": Toy("ring", "float ring", "a bright float ring", shares=True, bouncy=True, tags={"share"}),
    "board": Toy("board", "kick board", "a little kick board", shares=True, bouncy=True, tags={"share"}),
    "duck": Toy("duck", "rubber duck", "a rubber duck", shares=True, bouncy=False, tags={"share"}),
}

@dataclass
@dataclass
class StoryParams:
    pool: str
    toy: str
    a_name: str
    a_gender: str
    b_name: str
    b_gender: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in POOLS for t in TOYS if POOLS[p].safe and TOYS[t].shares]


def reasonableness_ok(pool: Pool, toy: Toy) -> bool:
    return pool.safe and toy.shares


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about sharing a dive toy.")
    ap.add_argument("--pool", choices=POOLS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              if (args.pool is None or c[0] == args.pool)
              and (args.toy is None or c[1] == args.toy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pool, toy = rng.choice(sorted(combos))
    a_gender = args.gender_a or rng.choice(["girl", "boy"])
    b_gender = args.gender_b or ("boy" if a_gender == "girl" else "girl")
    a_name = args.name_a or rng.choice(["Mia", "Nia", "Tess", "Luna", "Ava"] if a_gender == "girl" else ["Leo", "Finn", "Noah", "Owen", "Max"])
    b_name = args.name_b or rng.choice(["Milo", "Ben", "Zed", "Kai", "Eli"] if b_gender == "boy" else ["Zoe", "Maya", "Ivy", "Ruby", "Pia"])
    return StoryParams(pool, toy, a_name, a_gender, b_name, b_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story that includes the word "dive" and ends happily with {f["a"].id} and {f["b"].id} sharing {f["toy"].phrase}.',
        f"Tell a small happy-ending story where two children want to dive, but they learn to share the toy first.",
        f'Write a child-friendly rhyme about {f["a"].id}, {f["b"].id}, and a shared dive into {f["pool"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, toy, pool = f["a"], f["b"], f["toy"], f["pool"]
    return [
        QAItem(
            question="What did the children want to do?",
            answer=f"They wanted to dive into {pool.label}. The water looked fun and bright, so they both rushed toward the same game."
        ),
        QAItem(
            question=f"Why did {b.id} ask for a turn?",
            answer=f"{b.id} wanted to share {toy.phrase} because only one toy could guide the dive. Sharing meant they could both have fun without fighting."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. They shared, took turns, and both dove in with smiles, so the day stayed light and kind."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use or enjoy something too. It is a kind way to play together."
        ),
        QAItem(
            question="What is a dive?",
            answer="A dive is when someone jumps or slips into water headfirst or feetfirst in a quick, splashy way. It is a fun swim move."
        ),
        QAItem(
            question="Why is taking turns helpful?",
            answer="Taking turns helps everyone get a chance. It keeps play fair and helps children stay calm and happy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(POOLS[params.pool], TOYS[params.toy], params.a_name, params.a_gender, params.b_name, params.b_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P, T) :- pool(P), toy(T), safe(P), shares(T).
shared_story(P, T) :- valid(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in POOLS.items():
        lines.append(asp.fact("pool", pid))
        if p.safe:
            lines.append(asp.fact("safe", pid))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if t.shares:
            lines.append(asp.fact("shares", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(StoryParams("yard", "ring", "Mia", "girl", "Leo", "boy"))
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"MISMATCH: normal generation crashed: {exc}")
    if ok:
        print(f"OK: ASP and Python gate match ({len(valid_combos())} combos).")
        print("OK: smoke test generation succeeded.")
        return 0
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection(pool: Pool, toy: Toy) -> str:
    return f"(No story: {toy.label} and {pool.label} do not fit the simple sharing-and-dive pattern.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show shared_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, t in asp_valid_combos():
            print(f"  {p:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("yard", "ring", "Mia", "girl", "Leo", "boy"),
            StoryParams("lake", "board", "Ava", "girl", "Ben", "boy"),
            StoryParams("pond", "duck", "Noah", "boy", "Luna", "girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.a_name} & {p.b_name}: {p.pool} / {p.toy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
