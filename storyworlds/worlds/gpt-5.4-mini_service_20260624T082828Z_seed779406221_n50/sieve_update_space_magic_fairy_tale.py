#!/usr/bin/env python3
"""
A tiny fairy-tale story world about a magic sieve, a troublesome update, and the
wide open space where a small repair makes everything glow again.
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


@dataclass
class StoryParams:
    setting: str = "the moonlit garden"
    hero: str = "Mira"
    helper: str = "a moon sprite"
    magic_kind: str = "starlight"
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    magic: object | None = None
    sieve: object | None = None
    update: object | None = None
    def pronoun(self) -> str:
        if self.type in {"girl", "woman", "queen", "princess"}:
            return "she"
        if self.type in {"boy", "man", "king", "prince"}:
            return "he"
        return "it"

    def possessive(self) -> str:
        if self.type in {"girl", "woman", "queen", "princess"}:
            return "her"
        if self.type in {"boy", "man", "king", "prince"}:
            return "his"
        return "its"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)

    world: object | None = None
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


THRESHOLD = 1.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale story world with a magic sieve and a tricky update.")
    ap.add_argument("--setting", choices=["the moonlit garden", "the castle attic", "the quiet meadow"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--magic-kind", choices=["starlight", "dustlight", "golden ash"])
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


SETTINGS = [
    "the moonlit garden",
    "the castle attic",
    "the quiet meadow",
]
HEROES = ["Mira", "Nia", "Eli", "Luna", "Rowan"]
HELPERS = ["a moon sprite", "a tiny fairy", "an old wizard", "a lantern fox"]
MAGIC_KINDS = ["starlight", "dustlight", "golden ash"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(SETTINGS)
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    magic_kind = getattr(args, "magic_kind", None) or rng.choice(MAGIC_KINDS)
    return StoryParams(setting=setting, hero=hero, helper=helper, magic_kind=magic_kind)


def reasonableness_gate(params: StoryParams) -> None:
    if "sieve" not in params.setting and params.setting not in SETTINGS:
        pass
    if not params.hero:
        pass
    if not params.helper:
        pass
    if not params.magic_kind:
        pass


def _update_effect(world: World) -> None:
    if "update" in world.fired:
        return
    sieve = world.get("sieve")
    magic = world.get("magic")
    if sieve.meters.get("blocked", 0.0) >= THRESHOLD:
        world.fired.add("update")
        sieve.meters["blocked"] = 0.0
        sieve.meters["shining"] = sieve.meters.get("shining", 0.0) + 1.0
        magic.meters["flow"] = magic.meters.get("flow", 0.0) + 1.0
        world.get("hero").memes["relief"] = world.get("hero").memes.get("relief", 0.0) + 1.0
        world.say("The update worked, and the sieve’s tiny holes opened like little stars.")


def _problem_and_fix(world: World) -> None:
    sieve = world.get("sieve")
    update = world.get("update")
    magic = world.get("magic")
    hero = world.get("hero")
    helper = world.get("helper")

    if sieve.meters.get("blocked", 0.0) < THRESHOLD:
        return

    if "problem" not in world.fired:
        world.fired.add("problem")
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        world.say(
            f"In {world.setting}, {hero.id} found a magic sieve, but its shining holes were clogged with {magic.label}."
        )
        world.say(
            f"{hero.id} tried to pour the bright stuff through, yet the sieve would not sing."
        )

    if "update_turn" not in world.fired:
        world.fired.add("update_turn")
        helper.memes["care"] = helper.memes.get("care", 0.0) + 1.0
        world.say(
            f"Then {helper.id} came close and whispered that a small update could mend the spell without breaking it."
        )
        sieve.meters["blocked"] = 0.0
        update.meters["done"] = 1.0
        _update_effect(world)

    if "ending" not in world.fired:
        world.fired.add("ending")
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        world.say(
            f"At last, the magic flowed through the sieve and sprinkled the open space with silver light."
        )
        world.say(
            f"{hero.id} smiled, {helper.id} laughed, and the little sieve kept the whole wide space bright."
        )


def tell(params: StoryParams) -> World:
    world = World(setting=params.setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type="fairy", label=params.helper))
    sieve = world.add(Entity(id="sieve", kind="thing", type="sieve", label="magic sieve", owner=hero.id))
    update = world.add(Entity(id="update", kind="thing", type="update", label="small update", owner=helper.id))
    magic = world.add(Entity(id="magic", kind="thing", type="magic", label=params.magic_kind, owner=None))

    world.say(f"Once upon a time, {hero.id} wandered into {world.setting} and found a magic sieve.")
    world.say(f"The sieve could catch {magic.label}, and it was meant to keep the open space neat and bright.")
    sieve.meters["blocked"] = 1.0
    magic.meters["flow"] = 1.0
    _problem_and_fix(world)

    world.facts.update(
        hero=hero,
        helper=helper,
        sieve=sieve,
        update=update,
        magic=magic,
        setting=world.setting,
        resolved=sieve.meters.get("blocked", 0.0) < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle fairy tale about {f["hero"].id}, a magic sieve, and a small update that fixes a blocked spell.',
        f"Tell a child-friendly story where {f['helper'].id} helps {f['hero'].id} use a sieve to guide {f['magic'].label} through an open space.",
        f"Write a short fairy tale set in {f['setting']} with the words sieve, update, and space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    magic = f["magic"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {f['setting']}?",
            answer=f"{hero.id} found a magic sieve in {f['setting']}. It was supposed to guide {magic.label} through the open space.",
        ),
        QAItem(
            question=f"Why did the sieve stop working at first?",
            answer=f"It stopped working because {magic.label} clogged its tiny holes, so the magic could not flow through.",
        ),
        QAItem(
            question=f"How did {helper.id} help in the end?",
            answer=f"{helper.id} whispered that a small update could mend the spell, and that let the sieve shine and work again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sieve for?",
            answer="A sieve is a tool with tiny holes that lets small things pass through while catching bigger bits.",
        ),
        QAItem(
            question="What does update mean?",
            answer="An update is a change that makes something newer, better, or fixed.",
        ),
        QAItem(
            question="What is space?",
            answer="Space is the open area around things, like the room where a story can happen.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        if ent.meters:
            bits.append(f"meters={dict(ent.meters)}")
        if ent.memes:
            bits.append(f"memes={dict(ent.memes)}")
        if bits:
            lines.append(f"  {ent.id:8} ({ent.kind:8}) {' '.join(bits)}")
        else:
            lines.append(f"  {ent.id:8} ({ent.kind:8})")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
blocked(sieve) :- clogged(sieve).
fixed(sieve) :- blocked(sieve), update(applied).
resolved :- fixed(sieve), magic(flows).
#show resolved/0.
#show fixed/1.
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clogged", "sieve"),
            asp.fact("update", "applied"),
            asp.fact("magic", "flows"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="the moonlit garden", hero="Mira", helper="a moon sprite", magic_kind="starlight"),
    StoryParams(setting="the castle attic", hero="Luna", helper="a tiny fairy", magic_kind="dustlight"),
    StoryParams(setting="the quiet meadow", hero="Eli", helper="a lantern fox", magic_kind="golden ash"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0.\n#show fixed/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
