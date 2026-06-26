#!/usr/bin/env python3
"""
A standalone story world for a small rhyming tale about a slob, a fattening
snack, and a helly helper who learns friendship through humorous dialogue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

WORDS = ("slob", "fatten", "helly")



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    buddy: object | None = None
    hero: object | None = None
    snack: object | None = None
    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"
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
        if "_tags" not in self.__dict__:
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
class StoryParams:
    setting: str = "the little kitchen"
    hero: str = "Milo"
    buddy: str = "Helly"
    snack: str = "sticky buns"
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "kitchen": "the little kitchen",
    "yard": "the sunny yard",
    "porch": "the bright porch",
}

HERO_NAMES = ["Milo", "Nina", "Pip", "Tara", "Jules"]
BUDDY_NAMES = ["Helly", "Henny", "Melly", "Lolly"]
SNACKS = ["sticky buns", "berry pie", "soft rolls", "honey cake"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming friendship story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--buddy", choices=BUDDY_NAMES)
    ap.add_argument("--snack", choices=SNACKS)
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
    setting_key = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    buddy = getattr(args, "buddy", None) or rng.choice(BUDDY_NAMES)
    if buddy == hero:
        buddy = rng.choice([b for b in BUDDY_NAMES if b != hero])
    snack = getattr(args, "snack", None) or rng.choice(SNACKS)
    return StoryParams(
        setting=_safe_lookup(SETTINGS, setting_key),
        hero=hero,
        buddy=buddy,
        snack=snack,
    )


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    w: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        return World(self.params, entities=_copy.deepcopy(self.entities), paragraphs=[[]], facts=dict(self.facts))
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def _rhymes(a: str, b: str) -> bool:
    return a[-2:] == b[-2:]


def tell(params: StoryParams) -> World:
    w = World(params=params)
    hero = w.add(Entity(id=params.hero, kind="character", label=params.hero, role="hero",
                        meters={"mess": 0.0, "hunger": 1.0, "joy": 1.0},
                        memes={"friendship": 0.0, "humor": 0.0, "helly": 0.0},
                        traits=["slob"]))
    buddy = w.add(Entity(id=params.buddy, kind="character", label=params.buddy, role="buddy",
                         meters={"care": 1.0},
                         memes={"friendship": 1.0, "humor": 1.0},
                         traits=["helly"]))
    snack = w.add(Entity(id="snack", kind="thing", label=params.snack, role="snack",
                         meters={"sweet": 1.0, "sticky": 1.0}))

    place = w.params.setting
    w.say(f"In {place} on a breezy day, {hero.label} came waddling to play.")
    w.say(f"{hero.label} was a slob with crumbs on a sleeve, yet {hero.label} had heart and liked to believe")
    w.say(f"that a little kind grin and a silly small joke could turn a slow day to a warm friendship poke.")

    w.para()
    w.say(f"Then {buddy.label} came near with a tray held high. “Want a sweet snack?” said {buddy.label} with a wink and a sigh.")
    w.say(f"{hero.label} said, “I do!” with a laugh that was loud; “But I might make a mess and look rather proud.”")
    hero.meters["mess"] += 1
    hero.memes["humor"] += 1
    buddy.memes["humor"] += 1
    w.say(f"{buddy.label} chuckled, “A mess is okay; we can tidy together and brighten the day.”")

    w.para()
    w.say(f"They sat side by side with a napkin and spoon, and talked in a rhythm that danced like a tune.")
    w.say(f"“I’m not much of a cleaner,” said {hero.label}, “I’m more of a snack-er.”")
    w.say(f"“Then let’s help each other,” said {buddy.label}, “that’s the nicest kind of clacker.”")
    hero.memes["friendship"] += 2
    buddy.memes["friendship"] += 2
    hero.memes["helly"] += 1
    buddy.memes["helly"] += 1

    w.para()
    w.say(f"They shared the {snack.label}, and crumbs did not cling for long; they brushed them away while humming a song.")
    hero.meters["mess"] = max(0.0, hero.meters["mess"] - 1.0)
    hero.meters["joy"] += 1
    buddy.meters["care"] += 1
    w.say(f"By sunset, the slob had grown kinder and neat, and friendship felt bouncy and bubbly and sweet.")

    w.facts.update(
        hero=hero,
        buddy=buddy,
        snack=snack,
        place=place,
        mess=True,
        rhyming=True,
        friendship=hero.memes["friendship"] >= 2,
        humor=hero.memes["humor"] >= 1,
        dialogue=True,
        helly=buddies if False else True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    buddy = _safe_fact(world, f, "buddy")
    snack = _safe_fact(world, f, "snack")
    return [
        f"Write a short rhyming story about {hero.label}, a slob, and {buddy.label}, with a snack called {snack.label}.",
        f"Tell a funny friendship story with dialogue where {hero.label} and {buddy.label} solve a messy moment together.",
        f"Write a child-friendly rhyming tale that includes the words slob, fatten, and helly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    buddy = _safe_fact(world, f, "buddy")
    snack = _safe_fact(world, f, "snack")
    return [
        QAItem(
            question=f"Who was the slob in the story?",
            answer=f"{hero.label} was the slob, but {hero.label} still had a warm heart and wanted to be kind.",
        ),
        QAItem(
            question=f"How did {buddy.label} help {hero.label}?",
            answer=f"{buddy.label} shared the snack, told a joke, and stayed close so they could clean up together.",
        ),
        QAItem(
            question=f"What happened when they ate the {snack.label}?",
            answer=f"They made a little mess, then brushed the crumbs away and kept laughing together.",
        ),
        QAItem(
            question="Why did the story feel like friendship?",
            answer=f"Because {hero.label} and {buddy.label} listened, shared, and helped each other with a smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be a friend?",
            answer="A friend is someone who is kind, shares, helps, and cares about you.",
        ),
        QAItem(
            question="Why can sticky snacks make a mess?",
            answer="Sticky snacks can leave crumbs or goo on hands and tables, so they often need cleaning up.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
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
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} traits={e.traits}")
    return "\n".join(out)


ASP_RULES = r"""
#show valid/1.
valid(kitchen).
valid(yard).
valid(porch).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", k) for k in SETTINGS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo_set = sorted(set(asp.atoms(model, "valid")))
    python_set = sorted((k,) for k in SETTINGS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches settings ({len(clingo_set)}).")
        return 0
    print("MISMATCH")
    return 1


def generate(params: StoryParams) -> StorySample:
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
        print(format_qa(sample))


CURATED = [
    StoryParams(setting=SETTINGS["kitchen"], hero="Milo", buddy="Helly", snack="sticky buns"),
    StoryParams(setting=SETTINGS["yard"], hero="Nina", buddy="Melly", snack="berry pie"),
    StoryParams(setting=SETTINGS["porch"], hero="Pip", buddy="Lolly", snack="honey cake"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("3 valid settings:\n")
        for k in SETTINGS:
            print(f"  {k}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.buddy} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
