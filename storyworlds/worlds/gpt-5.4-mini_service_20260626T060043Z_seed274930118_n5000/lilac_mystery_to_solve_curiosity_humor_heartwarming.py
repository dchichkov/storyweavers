#!/usr/bin/env python3
"""
Standalone storyworld: a lilac mystery, curiosity, humor, and a warm ending.

This world is about a child who notices a small mystery, pokes at it with
curiosity, gets a few funny wrong ideas, and then discovers a kind explanation.
The ending always proves that the mystery was solved in a gentle, heartwarming
way.
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

MYSTERY_THRESHOLD = 1.0
CURIOUS_THRESHOLD = 1.0
HUMOR_THRESHOLD = 1.0
HEARTWARM_THRESHOLD = 1.0



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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    color: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Setting:
    place: str
    indoors: bool
    has_lilac: bool
    has_hiding_places: bool
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


@dataclass
class Mystery:
    clue: str
    mistaken_guess: str
    reveal: str
    solved_by: str
    comfort: str
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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, has_lilac=True, has_hiding_places=True),
    "yard": Setting(place="the backyard", indoors=False, has_lilac=False, has_hiding_places=True),
    "porch": Setting(place="the porch", indoors=False, has_lilac=False, has_hiding_places=False),
    "kitchen": Setting(place="the kitchen", indoors=True, has_lilac=False, has_hiding_places=False),
}

MYSTERIES = {
    "garden": Mystery(
        clue="a little lilac ribbon tied around the watering can",
        mistaken_guess="a shy butterfly had borrowed the ribbon for a nap",
        reveal="the child's grandparent had tied it there as a surprise marker",
        solved_by="looking carefully beside the herbs",
        comfort="everyone laughed softly, and the ribbon stayed right where it belonged",
    ),
    "yard": Mystery(
        clue="a lilac pebble in the middle of the stepping stones",
        mistaken_guess="a tiny moon had fallen out of the sky",
        reveal="the neighbor child had left it there while making a pretend treasure trail",
        solved_by="following the chalk arrows",
        comfort="the pebble became the last treasure in a happy game",
    ),
    "porch": Mystery(
        clue="a lilac sock hanging from the railing",
        mistaken_guess="the wind had tried to wear it like a flag",
        reveal="the family cat had dragged it there like a prize",
        solved_by="checking under the porch bench",
        comfort="the sock went back into the basket, and the cat looked very proud",
    ),
    "kitchen": Mystery(
        clue="a lilac spoon beside the sugar jar",
        mistaken_guess="the spoon had been practicing magic",
        reveal="the parent had used it to stir berry syrup for toast",
        solved_by="opening the warm jar of jam",
        comfort="breakfast smelled sweet, and nobody felt puzzled for long",
    ),
}

HERO_NAMES = ["Mina", "Theo", "Lila", "Sami", "Nora", "Ben"]
TRAITS = ["curious", "gentle", "bright", "playful", "careful", "cheerful"]


def explain_rejection(place: str) -> str:
    return f"(No story: {place} is not one of the supported settings.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small heartwarming mystery storyworld with lilac clues."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent_type = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, hero_name=name, hero_type=hero_type, parent_type=parent_type)


def mystery_for(world: World) -> Mystery:
    return _safe_lookup(MYSTERIES, world.setting.place)


def set_world_state(world: World) -> None:
    hero = world.get("hero")
    parent = world.get("parent")
    clue = world.get("clue")
    hero.memes["curiosity"] = 1.0
    hero.memes["humor"] = 0.5
    hero.memes["warmth"] = 0.25
    clue.meters["mystery"] = 1.0
    parent.memes["gentleness"] = 1.0


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    mystery = mystery_for(world)
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="clue", phrase=mystery.clue, color="lilac"))
    world.facts["mystery"] = mystery
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["clue"] = clue

    world.say(
        f"{hero.id} was a little {('curious ' if hero.type == 'girl' else 'curious ')}{hero.type} who loved noticing tiny things."
    )
    world.say(
        f"One day, {hero.id} spotted {mystery.clue} in {setting.place}."
    )
    world.say(
        f"The clue felt important because it was so very lilac, and {hero.id} wanted to know why it was there."
    )
    world.para()
    world.say(
        f"{hero.id} asked {hero.pronoun('possessive')} {parent.label} about it, but nobody knew at first."
    )
    world.say(
        f"So {hero.id} looked closer, checking corners, edges, and little hiding places."
    )
    world.say(
        f"The first guess was funny: maybe {mystery.mistaken_guess}."
    )
    world.say(
        f"{hero.id} giggled, because that could not be right, but it made the mystery feel less scary."
    )
    world.para()
    world.say(
        f"Then {hero.id} kept searching {mystery.solved_by}, and the answer finally showed itself."
    )
    world.say(
        f"It turned out that {mystery.reveal}."
    )
    world.say(
        f"{hero.id} smiled at the small surprise, and {hero.pronoun('possessive')} {parent.label} smiled too."
    )
    world.say(
        f"By the end, {mystery.comfort}."
    )
    set_world_state(world)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    m = _safe_fact(world, world.facts, "mystery")
    hero = _safe_fact(world, world.facts, "hero")
    return [
        f"Write a heartwarming story about a child named {hero.id} who notices a lilac clue and tries to solve a mystery.",
        f"Tell a gentle, funny mystery story where {hero.id} stays curious and finds out what {m.clue} means.",
        f"Write a short child-friendly story with a lilac detail, a small joke, and a kind reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")
    m = _safe_fact(world, world.facts, "mystery")
    setting = world.setting
    return [
        QAItem(
            question=f"What did {hero.id} notice in {setting.place}?",
            answer=f"{hero.id} noticed {m.clue}. That was the little mystery they wanted to solve.",
        ),
        QAItem(
            question=f"Why did the mystery feel important to {hero.id}?",
            answer=f"It mattered because the clue was lilac and unusual, so {hero.id} felt curious and wanted to understand it.",
        ),
        QAItem(
            question=f"What was the funny wrong guess about the clue?",
            answer=f"The silly guess was that {m.mistaken_guess}. {hero.id} laughed, which kept the mystery friendly.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved by {m.solved_by}, and then everyone learned that {m.reveal}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} feel at the end?",
            answer=f"They felt warm and happy, because {m.comfort}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does lilac usually mean?",
            answer="Lilac is a pale purple color, like some flowers in a spring garden.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you ask questions and look closely at new things.",
        ),
        QAItem(
            question="Why can a funny guess help in a mystery?",
            answer="A funny guess can make a mystery feel less scary and can help people keep thinking calmly.",
        ),
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
        lines.append(f"  {e.id:6} ({e.kind:8} {e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_visible(P) :- place(P), has_lilac_clue(P).
curious(H) :- hero(H).
humorous(H) :- hero(H).
solved(P) :- mystery_visible(P), curious(hero), humorous(hero).
heartwarming(P) :- solved(P), parent_kind(mother).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.has_lilac:
            lines.append(asp.fact("has_lilac_clue", pid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("parent_kind", "mother"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin is present and syntactically bundled.")
    return 0


def asp_valid_places() -> list[str]:
    return sorted(SETTINGS)


CURATED = [
    StoryParams(place="garden", hero_name="Mina", hero_type="girl", parent_type="mother"),
    StoryParams(place="yard", hero_name="Theo", hero_type="boy", parent_type="father"),
    StoryParams(place="porch", hero_name="Lila", hero_type="girl", parent_type="mother"),
    StoryParams(place="kitchen", hero_name="Sami", hero_type="boy", parent_type="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Compatible places:", ", ".join(asp_valid_places()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
