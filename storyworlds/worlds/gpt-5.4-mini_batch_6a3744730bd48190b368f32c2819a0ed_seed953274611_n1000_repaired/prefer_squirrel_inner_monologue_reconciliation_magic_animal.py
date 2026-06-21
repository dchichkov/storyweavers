#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prefer_squirrel_inner_monologue_reconciliation_magic_animal.py
==============================================================================================

A small animal-story world about a squirrel who prefers one thing, then learns
through inner monologue, a little magic, and reconciliation how to share or
choose kindly.

This world is intentionally tiny and state-driven:
- a squirrel and a few animal neighbors
- one preferred thing that can cause hurt feelings
- an inner-monologue beat that changes the squirrel's emotional state
- a magical helper that reveals, softens, or transforms the problem
- a reconciliation ending that proves something changed

The story is not a frozen paragraph with swapped nouns; it is assembled from
simulated state and traceable causal beats.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    species: str = "animal"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        w = World()
        w.entities = dataclasses.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Choice:
    id: str
    label: str
    mood: str
    magic: bool = False
    shareable: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    squirrel_name: str = "Sunny"
    friend_name: str = "Moss"
    friend_species: str = "rabbit"
    third_name: str = "Pip"
    third_species: str = "mouse"
    prefer: str = "cone"
    magic: str = "glow_moth"
    setting: str = "the old oak tree"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SQUIRREL_NAMES = ["Sunny", "Nutmeg", "Hazel", "Tansy", "Poppy", "Clover", "Maple"]
FRIEND_NAMES = ["Moss", "Bramble", "Fern", "Wren", "Pip", "Ivy", "Robin"]
PREFER_CHOICES = {
    "cone": Choice("cone", "the biggest pine cone", "proud", shareable=True, tags={"food"}),
    "berry": Choice("berry", "the shiny red berry pile", "greedy", shareable=True, tags={"food"}),
    "nest_fluff": Choice("nest_fluff", "the softest mossy fluff", "cozy", shareable=False, tags={"nest"}),
}
MAGIC_CHOICES = {
    "glow_moth": Choice("glow_moth", "a glow moth", "gentle", magic=True, tags={"light"}),
    "moon_drop": Choice("moon_drop", "a moon-drop charm", "calm", magic=True, tags={"light"}),
    "sparkle_wind": Choice("sparkle_wind", "a sparkle wind", "bright", magic=True, tags={"light"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: preference, magic, and reconciliation.")
    ap.add_argument("--squirrel", choices=SQUIRREL_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--third", choices=FRIEND_NAMES)
    ap.add_argument("--prefer", choices=PREFER_CHOICES)
    ap.add_argument("--magic", choices=MAGIC_CHOICES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PREFER_CHOICES for m in MAGIC_CHOICES]


def reasonableness_gate(prefer_id: str, magic_id: str) -> bool:
    pref = PREFER_CHOICES[prefer_id]
    mag = MAGIC_CHOICES[magic_id]
    return pref.shareable or mag.magic


ASP_RULES = r"""
valid(P, M) :- prefer(P), magic(M), shareable(P).
valid(P, M) :- prefer(P), magic(M), magical(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PREFER_CHOICES:
        lines.append(asp.fact("prefer", pid))
        if PREFER_CHOICES[pid].shareable:
            lines.append(asp.fact("shareable", pid))
    for mid in MAGIC_CHOICES:
        lines.append(asp.fact("magic", mid))
        if MAGIC_CHOICES[mid].magic:
            lines.append(asp.fact("magical", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c != p:
        print("MISMATCH in valid combos:")
        if c - p:
            print(" only in clingo:", sorted(c - p))
        if p - c:
            print(" only in python:", sorted(p - c))
        return 1
    print(f"OK: ASP matches Python gate ({len(c)} combos).")
    return 0


def _inner_monologue(world: World, squirrel: Entity, friend: Entity, pref: Choice) -> None:
    squirrel.memes["torn"] += 1
    world.say(
        f"{squirrel.id} held the {pref.label} close and thought, "
        f'"I really prefer this one. But {friend.id} looks so sad."'
    )
    world.say(
        f"In {squirrel.pronoun('possessive')} own quiet mind, {squirrel.id} wondered "
        f"if keeping it would make the day feel heavy."
    )


def _magic_reveal(world: World, magic: Choice, pref: Choice) -> None:
    world.say(
        f"Then {magic.label} fluttered in and touched the {pref.label} with a soft glow."
    )
    world.say(
        f"The glow showed that the {pref.label} was not for keeping alone; it was for a small shared game."
    )


def _reconcile(world: World, squirrel: Entity, friend: Entity, third: Entity, pref: Choice) -> None:
    squirrel.memes["kindness"] += 1
    friend.memes["relief"] += 1
    third.memes["relief"] += 1
    world.say(
        f"{squirrel.id} took a breath and said, "
        f'"I can still prefer this, but I do not want to be unfair."'
    )
    world.say(
        f"{squirrel.id} passed the {pref.label} to {friend.id} first, then to {third.id}."
    )
    world.say(
        f"The three animals made a ring beneath the branches and laughed together."
    )


def tell_story(world: World, squirrel: Entity, friend: Entity, third: Entity, pref: Choice, magic: Choice) -> None:
    squirrel.memes["hope"] += 1
    friend.memes["hurt"] += 1
    third.memes["hope"] += 1

    world.say(
        f"Under {world.facts['setting']}, {squirrel.id} found {pref.label} and decided to keep it close."
    )
    world.say(
        f"{friend.id} and {third.id} watched from the roots, wishing they could join in."
    )
    world.para()
    _inner_monologue(world, squirrel, friend, pref)
    _magic_reveal(world, magic, pref)
    world.para()
    _reconcile(world, squirrel, friend, third, pref)
    world.say(
        f"By sunset, the squirrel still preferred the {pref.label}, but now it belonged to everyone in the game."
    )


def generate_world(params: StoryParams) -> World:
    if params.prefer not in PREFER_CHOICES:
        raise StoryError(f"Unknown prefer choice: {params.prefer}")
    if params.magic not in MAGIC_CHOICES:
        raise StoryError(f"Unknown magic choice: {params.magic}")
    if not reasonableness_gate(params.prefer, params.magic):
        raise StoryError("This story needs a preference that can be shared, or magic that can open the way to sharing.")

    w = World()
    squirrel = w.add(Entity(id=params.squirrel_name, species="squirrel", kind="animal", role="main"))
    friend = w.add(Entity(id=params.friend_name, species=params.friend_species, kind="animal", role="friend"))
    third = w.add(Entity(id=params.third_name, species=params.third_species, kind="animal", role="neighbor"))

    pref = PREFER_CHOICES[params.prefer]
    magic = MAGIC_CHOICES[params.magic]

    w.facts.update(
        squirrel=squirrel,
        friend=friend,
        third=third,
        pref=pref,
        magic=magic,
        setting=params.setting,
        outcome="reconciled",
    )
    tell_story(w, squirrel, friend, third, pref, magic)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pref = f["pref"]
    magic = f["magic"]
    squirrel = f["squirrel"]
    friend = f["friend"]
    return [
        f"Write an animal story for a young child where {squirrel.id} prefers {pref.label} but learns to share after a magical moment.",
        f"Tell a story that uses the words 'prefer' and 'squirrel' and ends with reconciliation between {squirrel.id} and {friend.id}.",
        f"Create a gentle woodland story with inner monologue, magic, and reconciliation about {pref.label} and {magic.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    squirrel = f["squirrel"]
    friend = f["friend"]
    pref = f["pref"]
    return [
        QAItem(
            question="What did the squirrel prefer?",
            answer=f"The squirrel preferred {pref.label}. At first it wanted to keep it close, because it seemed special and important.",
        ),
        QAItem(
            question="What did the squirrel think about in its own mind?",
            answer=f"It wondered whether keeping the {pref.label} would make the other animals feel left out. That quiet thought helped the squirrel choose a kinder path.",
        ),
        QAItem(
            question="How did the animals make up?",
            answer=f"{squirrel.id} shared the {pref.label} with {friend.id} and the third animal, and they all played together. The story ends with reconciliation because the squirrel chose kindness over keeping everything for itself.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a squirrel?",
            answer="A squirrel is a small animal that can climb trees and carry food or treasures with its paws and tail.",
        ),
        QAItem(
            question="What does prefer mean?",
            answer="Prefer means to like one thing more than another. You can prefer something and still choose to be fair or kind.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people or animals stop being upset and make up again. It often ends with sharing, kindness, or a hug.",
        ),
        QAItem(
            question="What can magic do in a story?",
            answer="Magic can help show a feeling, reveal a truth, or change a problem in a gentle way. In stories, it often helps characters understand each other better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.species:
            bits.append(f"species={e.species}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: " + " ".join(bits))
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prefer and args.prefer not in PREFER_CHOICES:
        raise StoryError(f"Unknown prefer choice: {args.prefer}")
    if args.magic and args.magic not in MAGIC_CHOICES:
        raise StoryError(f"Unknown magic choice: {args.magic}")
    if args.prefer and args.magic and not reasonableness_gate(args.prefer, args.magic):
        raise StoryError("Chosen pair cannot support the story's sharing turn.")

    pref = args.prefer or rng.choice(list(PREFER_CHOICES))
    magic = args.magic or rng.choice(list(MAGIC_CHOICES))
    if not reasonableness_gate(pref, magic):
        magic = next(m for m in MAGIC_CHOICES if MAGIC_CHOICES[m].magic)
    squirrel = args.squirrel or rng.choice(SQUIRREL_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    third = args.third or rng.choice([n for n in FRIEND_NAMES if n != friend])
    return StoryParams(
        squirrel_name=squirrel,
        friend_name=friend,
        friend_species="rabbit",
        third_name=third,
        third_species="mouse",
        prefer=pref,
        magic=magic,
        setting="the old oak tree",
    )


def generate(params: StoryParams) -> StorySample:
    try:
        world = generate_world(params)
    except KeyError as e:
        raise StoryError(f"Invalid parameter: {e}") from e
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
    StoryParams(squirrel_name="Sunny", friend_name="Moss", friend_species="rabbit", third_name="Pip", third_species="mouse", prefer="cone", magic="glow_moth", setting="the old oak tree"),
    StoryParams(squirrel_name="Hazel", friend_name="Wren", friend_species="rabbit", third_name="Ivy", third_species="mouse", prefer="berry", magic="moon_drop", setting="the old oak tree"),
    StoryParams(squirrel_name="Nutmeg", friend_name="Fern", friend_species="rabbit", third_name="Robin", third_species="mouse", prefer="nest_fluff", magic="sparkle_wind", setting="the old oak tree"),
]


def asp_verify_smoke() -> int:
    rc = asp_verify()
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("FAIL: generated story is empty.")
            return 1
    except Exception as e:
        print(f"FAIL: smoke test generation crashed: {e}")
        return 1
    print("OK: smoke test generation succeeded.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_smoke())
    if args.asp:
        print("valid combos:")
        for p, m in asp_valid_combos():
            print(f"  {p:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
