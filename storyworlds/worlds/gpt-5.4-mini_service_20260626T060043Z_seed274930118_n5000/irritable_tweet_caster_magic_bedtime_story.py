#!/usr/bin/env python3
"""
A small bedtime-story world about a magical tweet caster, a cranky evening mood,
and a gentle turn toward sleep.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    trait: object | None = None
    caster: object | None = None
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
class Setting:
    place: str = "the little bedroom"
    afford: set[str] = field(default_factory=lambda: {"tweet", "magic", "bedtime"})
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
    name: str = "Milo"
    gender: str = "boy"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the little bedroom"),
}

ACTIVITIES = {
    "tweet": {
        "verb": "tweet from the window",
        "gerund": "tweeting softly",
        "noise": "bright little tweets",
        "mood": "tweet",
    },
    "magic": {
        "verb": "practice magic under the moon lamp",
        "gerund": "making tiny sparkles",
        "noise": "soft sparkles",
        "mood": "magic",
    },
}

TREATS = {
    "tea": "a warm mug of honey tea",
    "book": "a sleepy picture book",
    "blanket": "a fluffy blanket",
}

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, parent: Entity, caster: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.trait if hero.traits else 'gentle'} {hero.type} "
        f"who lived in {world.setting.place} with {parent.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f"At night, {hero.id} loved the tiny {caster.label} who could make magic shine "
        f"like a firefly in a jar."
    )


def source_tension(world: World, hero: Entity, caster: Entity) -> None:
    hero.memes["irritable"] = 1
    caster.meters["spark"] = 1
    world.say(
        f"But when bedtime came, {hero.id} felt irritable and small things felt too loud."
    )
    world.say(
        f"The {caster.label} began to tweet and flicker, and the room filled with bright little tweets."
    )


def warning(world: World, parent: Entity, hero: Entity, caster: Entity) -> None:
    world.say(
        f"{parent.pronoun().capitalize()} smiled and said, "
        f"\"Too much tweet magic will keep your eyes open, {hero.id}.\""
    )


def upset_and_reach(world: World, hero: Entity, caster: Entity) -> None:
    hero.memes["irritable"] += 1
    hero.memes["worry"] = 1
    world.say(
        f"{hero.id} frowned and hugged the pillow tighter, because the bright magic still buzzed."
    )
    world.say(
        f"{hero.pronoun().capitalize()} asked the {caster.label} to be quieter, but the little {caster.label} only knew how to tweet."
    )


def gentle_turn(world: World, parent: Entity, hero: Entity, caster: Entity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    caster.meters["spark"] = 0
    caster.meters["glow"] = 1
    world.say(
        f"{parent.pronoun().capitalize()} picked up the {caster.label} and wrapped it in a soft blue scarf."
    )
    world.say(
        f"Then {parent.pronoun('subject')} whispered, \"Magic can whisper too.\""
    )
    world.say(
        f"The {caster.label} changed from tweeting bright and busy to glowing slow and sleepy."
    )


def ending(world: World, hero: Entity, parent: Entity, caster: Entity) -> None:
    hero.memes["irritable"] = 0
    hero.memes["sleepy"] = 1
    world.say(
        f"{hero.id}'s shoulders relaxed. The room was quiet, except for one tiny warm glow by the bed."
    )
    world.say(
        f"{hero.id} yawned, smiled at the {caster.label}, and drifted off while {parent.pronoun('subject')} tucked in the blanket."
    )


def tell(name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(SETTINGS["bedroom"])
    hero = world.add(Entity(id=name, kind="character", type=gender, trait=trait, traits=[trait, "little"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    caster = world.add(Entity(id="Caster", kind="thing", type="caster", label="tweet caster", owner=hero.id))
    world.facts.update(hero=hero, parent=parent, caster=caster)

    introduce(world, hero, parent, caster)
    world.para()
    source_tension(world, hero, caster)
    warning(world, parent, hero, caster)
    upset_and_reach(world, hero, caster)
    world.para()
    gentle_turn(world, parent, hero, caster)
    ending(world, hero, parent, caster)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, caster = f["hero"], f["parent"], f["caster"]
    return [
        f'Write a short bedtime story for a young child about a {caster.label} with magic, an irritable feeling, and a soft ending.',
        f"Tell a gentle story where {hero.id} gets irritable at bedtime because the {caster.label} keeps tweeting, and {parent.pronoun('subject')} helps.",
        f'Write a cozy story that includes the words "irritable", "tweet", and "caster", and ends with sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, caster = f["hero"], f["parent"], f["caster"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {hero.type}, and the kind parent who helped at bedtime.",
        ),
        QAItem(
            question=f"What made {hero.id} feel irritable?",
            answer=f"The {caster.label} kept tweeting bright little tweets, and that made bedtime feel too lively.",
        ),
        QAItem(
            question=f"How did the parent help?",
            answer=f"{parent.pronoun().capitalize()} wrapped the {caster.label} in a soft scarf and turned the noisy magic into a sleepy glow.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"{hero.id} grew calm and sleepy, and the {caster.label} glowed quietly beside the bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime?",
            answer="Bedtime is the time when children get ready to rest, lie down, and go to sleep.",
        ),
        QAItem(
            question="What does it mean to be irritable?",
            answer="Irritable means feeling cranky or easily annoyed, so small things can seem too bothersome.",
        ),
        QAItem(
            question="What is a tweet?",
            answer="A tweet is a tiny bird sound, like a quick chirp or cheep.",
        ),
        QAItem(
            question="What is magic in a bedtime story?",
            answer="Magic is something special and impossible in real life, like glowing lights or gentle sparkles in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(h1).
parent(p1).
caster(c1).

activity(tweet).
activity(magic).

can_make_too_loud(tweet).
can_make_too_loud(magic).

bedtime_sensitive(tweet).
bedtime_sensitive(magic).

irritable_story :- hero(h1), parent(p1), caster(c1), can_make_too_loud(tweet), bedtime_sensitive(tweet).
resolved_story :- irritable_story.
"""

def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "h1"),
            asp.fact("parent", "p1"),
            asp.fact("caster", "c1"),
            asp.fact("activity", "tweet"),
            asp.fact("activity", "magic"),
            asp.fact("can_make_too_loud", "tweet"),
            asp.fact("can_make_too_loud", "magic"),
            asp.fact("bedtime_sensitive", "tweet"),
            asp.fact("bedtime_sensitive", "magic"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show irritable_story/0.\n#show resolved_story/0."))
    atoms = {sym.name for sym in model}
    required = {"irritable_story", "resolved_story"}
    if atoms == required:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH: ASP parity check failed.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(required))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about irritable tweet magic.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--trait", default=None)
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


TRAITS = ["curious", "sleepy", "gentle", "playful", "shy"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Leo", "Noah"]
GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Zoe"]
CURATED = [
    StoryParams(name="Milo", gender="boy", parent="mother", trait="curious"),
    StoryParams(name="Luna", gender="girl", parent="father", trait="gentle"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show irritable_story/0.\n#show resolved_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
