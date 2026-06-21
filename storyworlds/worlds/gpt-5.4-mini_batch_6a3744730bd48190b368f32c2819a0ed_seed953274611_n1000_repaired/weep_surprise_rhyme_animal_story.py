#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/weep_surprise_rhyme_animal_story.py
===================================================================

A small standalone storyworld for an animal-story seed with the words
"weep", "surprise", and "rhyme".

Premise
-------
A little animal feels left out during a surprise rhyme performance, worries
that the show is ruined, then learns the surprise was meant for them all along.
The emotional turn is driven by the world state: the planned surprise, the
unfinished rhyme, the visible tears, and the final shared performance.

This world keeps the story child-facing, concrete, and state-driven:
- typed entities with physical meters and emotional memes,
- a short causal model,
- a reasonableness gate,
- an inline ASP twin,
- prompts, story QA, and world-knowledge QA generated from world state.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/weep_surprise_rhyme_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/weep_surprise_rhyme_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/weep_surprise_rhyme_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/weep_surprise_rhyme_animal_story.py --verify
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
    plural: bool = False
    can_sing: bool = False
    can_weep: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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


@dataclass
class Animal:
    id: str
    type: str
    label: str
    role: str
    sound: str
    habitat: str
    surprise_role: str
    rhyme_word: str
    kind: str = "character"
    can_sing: bool = True
    can_weep: bool = True
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}
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
class Token:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    surprise: bool = False
    rhyme: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    animal_a: str
    animal_b: str
    animal_c: str
    setting: str
    surprise: str
    rhyme: str
    weeper: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def animals(self) -> list:
        return [e for e in self.entities.values() if getattr(e, "kind", "") == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_weep(world: World) -> list[str]:
    out = []
    for a in world.animals():
        if a.memes["sad"] >= THRESHOLD and a.meters["tears"] < THRESHOLD:
            sig = ("weep", a.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            a.meters["tears"] += 1
            out.append("__weep__")
    return out


def _r_comfort(world: World) -> list[str]:
    out = []
    if world.facts.get("surprise_revealed") and world.facts.get("rhyme_shared"):
        for a in world.animals():
            if a.memes["relief"] < THRESHOLD:
                a.memes["relief"] += 1
                a.memes["joy"] += 1
                out.append(f"{a.id} felt lighter at last.")
    return out


RULES = [Rule("weep", _r_weep), Rule("comfort", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def rhyme_choice(word: str) -> str:
    return {
        "bell": "shell",
        "moon": "spoon",
        "star": "car",
        "hive": "five",
    }.get(word, "song")


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for surprise in SURPRISES:
            for rhyme in RHYMES:
                for weeper in ANIMALS:
                    if weeper in surprise.lower():
                        continue
                    combos.append((setting, surprise, rhyme, weeper))
    return combos


def reasonableness_ok(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.surprise in SURPRISES and params.rhyme in RHYMES and params.weeper in ANIMALS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with surprise and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--weeper", choices=ANIMALS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    weeper = args.weeper or rng.choice(list(ANIMALS))
    params = StoryParams(
        animal_a="rabbit",
        animal_b="fox",
        animal_c="bear",
        setting=setting,
        surprise=surprise,
        rhyme=rhyme,
        weeper=weeper,
    )
    if not reasonableness_ok(params):
        raise StoryError("Invalid animal story choices.")
    return params


def tell(params: StoryParams) -> World:
    if not reasonableness_ok(params):
        raise StoryError("Invalid animal story choices.")
    world = World()
    a = world.add(Entity(id=params.animal_a, kind="character", type="rabbit", label="rabbit", role="helper", traits=["quick"], can_sing=True, can_weep=True))
    b = world.add(Entity(id=params.animal_b, kind="character", type="fox", label="fox", role="planner", traits=["bright"], can_sing=True, can_weep=True))
    c = world.add(Entity(id=params.animal_c, kind="character", type="bear", label="bear", role="weeper", traits=["shy"], can_sing=True, can_weep=True))
    s = world.add(Token(id="surprise", label=params.surprise, phrase=params.surprise, surprise=True))
    r = world.add(Token(id="rhyme", label=params.rhyme, phrase=params.rhyme, rhyme=True))

    world.say(f"In the {params.setting}, a rabbit, a fox, and a bear planned a little show.")
    world.say(f"The fox said the {params.surprise} should stay hidden until the last bright moment.")
    world.say(f"The rabbit practiced a rhyme about {params.rhyme}, soft as a song on a warm breeze.")

    world.para()
    c.memes["sad"] += 1
    world.say(f"But the bear felt left out and began to weep.")
    propagate(world, narrate=False)
    world.say(f"Tiny tears shone on the bear's nose, and the others paused to listen.")

    world.para()
    world.say(f"Then the fox nudged the curtain aside and the surprise appeared at once: {params.surprise}.")
    world.facts["surprise_revealed"] = True
    world.say(f"It was not a trick at all, but a gift for the bear, and the bear's eyes went wide.")

    world.para()
    world.facts["rhyme_shared"] = True
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    c.memes["joy"] += 1
    world.say(f"The rabbit, the fox, and the bear sang the rhyme together, and the weeping stopped.")
    world.say(f"They ended the night with {params.surprise}, a shared rhyme, and a smile that stayed.")

    world.facts.update(
        params=params,
        setting=params.setting,
        surprise=params.surprise,
        rhyme=params.rhyme,
        weeper=params.weeper,
        animals=(a, b, c),
        token_surprise=s,
        token_rhyme=r,
        outcome="shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write an animal story that includes the word "weep" and a surprise ending in {p.setting}.',
        f"Tell a gentle animal story where a bear begins to weep, then a surprise is revealed and a rhyme is shared.",
        f'Write a child-friendly story about animals making a rhyme and ending with the word "{p.surprise}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts["params"]
    return [
        ("Who was the story about?",
         f"It was about a rabbit, a fox, and a bear in the {p.setting}. The bear was the one who began to weep."),
        ("Why did the bear weep?",
         f"The bear thought the others had left it out of the fun. Then the surprise was revealed, and the bear could see the show was meant to include it."),
        ("What happened at the end?",
         f"The animals sang the rhyme together and shared the surprise. The weeping stopped because the bear felt wanted and happy."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to weep?",
         "To weep means to cry with tears. People or animals may weep when they feel sad, hurt, or worried."),
        ("What is a rhyme?",
         "A rhyme is a word or sound that matches another word at the end, like bell and shell. Rhymes make songs and stories fun to hear."),
        ("What is a surprise?",
         "A surprise is something that is hidden until the right moment. It can make a story exciting and full of wonder."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {"meadow": "meadow", "barn": "barn", "riverbank": "riverbank"}
SURPRISES = {"basket of berries": "basket of berries", "new scarf": "new scarf", "tiny drum": "tiny drum"}
RHYMES = {"moon": "moon", "bell": "bell", "star": "star"}
ANIMALS = {"bear": "bear", "rabbit": "rabbit", "fox": "fox"}

CURATED = [
    StoryParams(animal_a="rabbit", animal_b="fox", animal_c="bear", setting="meadow", surprise="basket of berries", rhyme="moon", weeper="bear"),
    StoryParams(animal_a="rabbit", animal_b="fox", animal_c="bear", setting="barn", surprise="new scarf", rhyme="bell", weeper="rabbit"),
]


ASP_RULES = r"""
surprise_ok(S) :- surprise(S).
rhyme_ok(R) :- rhyme(R).
valid(Setting, Surprise, Rhyme, Weeper) :- setting(Setting), surprise_ok(Surprise), rhyme_ok(Rhyme), animal(Weeper).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for r in RHYMES:
        lines.append(asp.fact("rhyme", r))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    else:
        print(f"OK: ASP and Python agree on {len(valid_combos())} combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
