#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/weeny_paper_doily_lesson_learned_misunderstanding_ghost.py
=================================================================================================

A small ghost-story world built from the seed words:
weeny, paper, doily

Premise:
- A child finds a weeny paper doily that seems to flutter like a ghost.
- The child misunderstands the little shape, then learns what it really is.
- The ending proves a lesson learned: some spooky-looking things are only
  harmless surprises, and a careful look can turn fear into kindness.

The world uses a tiny state model with physical meters and emotional memes.
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
# Shared tiny domain vocabulary.
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": {
        "place": "the attic",
        "light": "dim",
        "sounds": "the floor boards creaking softly",
        "affords": {"peek", "play"},
    },
    "library": {
        "place": "the quiet library",
        "light": "golden",
        "sounds": "pages whispering when the door opened",
        "affords": {"peek", "play"},
    },
    "porch": {
        "place": "the front porch",
        "light": "blue-gray",
        "sounds": "wind brushing the railings",
        "affords": {"peek", "play"},
    },
}

CHARACTER_TRAITS = ["brave", "curious", "gentle", "shy", "careful"]

NAMES = ["Mina", "Theo", "Pip", "Luna", "Ned", "Ivy", "June", "Otis"]


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------


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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    trait: object | None = None
    child: object | None = None
    doily: object | None = None
    ghost: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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
class World:
    setting: dict
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters.
# ---------------------------------------------------------------------------
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
    setting: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic.
# ---------------------------------------------------------------------------
    params: object | None = None
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


THRESHOLD = 1.0


def introduce(world: World, child: Entity, ghost: Entity, doily: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.trait} child who liked quiet corners and tiny surprises."
    )
    world.say(
        f"One day, {child.id} found a weeny paper doily near the floor, and a pale shape seemed to drift beside it."
    )
    world.say(
        f"{ghost.id} was there too, but it did not look like a big scary ghost. It looked more like a whisper with feet."
    )


def build_scene(world: World, child: Entity, ghost: Entity, doily: Entity) -> None:
    world.para()
    world.say(
        f"The room was {world.setting['light']} and still, with {world.setting['sounds']}."
    )
    world.say(
        f"{child.id} stared at the little paper doily and thought the fluttering shape must be a ghost."
    )
    child.memes["worry"] = 1.0
    child.memes["misunderstanding"] = 1.0
    ghost.memes["lonely"] = 1.0
    doily.meters["flutter"] = 1.0


def misunderstanding(world: World, child: Entity, ghost: Entity, doily: Entity) -> None:
    world.say(
        f"{child.id} backed up a step and whispered, 'Oh no, a ghost!'"
    )
    world.say(
        f"But the small shape only bobbed because {doily.id} was light as a feather and caught by the draft."
    )
    ghost.memes["hurt"] = 0.5
    ghost.memes["hope"] = 1.0


def lesson_learned(world: World, child: Entity, ghost: Entity, doily: Entity) -> None:
    world.para()
    world.say(
        f"{child.id} took a closer look and noticed the tiny holes and soft edges of the doily."
    )
    world.say(
        f"Then {child.id} laughed, because the 'ghost' was only {doily.id}, a weeny paper doily dancing in the air."
    )
    child.memes["worry"] = 0.0
    child.memes["joy"] = 1.0
    child.memes["understanding"] = 1.0
    ghost.memes["hurt"] = 0.0
    ghost.memes["friendliness"] = 1.0
    world.say(
        f"{child.id} said sorry for the misunderstanding and gently set the doily on a table so it could rest."
    )
    world.say(
        f"That was the lesson learned: a spooky-looking moment can be just a tiny thing asking for a careful look."
    )


def tell(setting_key: str, name: str, trait: str) -> World:
    world = World(_safe_lookup(SETTINGS, setting_key))
    child = world.add(Entity(id=name, kind="character", type="child", trait=trait, traits=[trait]))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    doily = world.add(Entity(id="Doily", type="paper doily", label="the doily", phrase="a weeny paper doily"))
    world.facts.update(child=child, ghost=ghost, doily=doily, setting_key=setting_key)

    introduce(world, child, ghost, doily)
    build_scene(world, child, ghost, doily)
    misunderstanding(world, child, ghost, doily)
    lesson_learned(world, child, ghost, doily)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f"Write a gentle ghost story for a young child named {child.id} about a weeny paper doily.",
        f"Tell a story where {child.id} thinks a tiny fluttering thing is a ghost, then learns the truth.",
        "Write a short story with a misunderstanding, a careful look, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    ghost: Entity = _safe_fact(world, f, "ghost")
    setting = world.setting["place"]
    return [
        QAItem(
            question=f"What did {child.id} think the little fluttering thing was in {setting}?",
            answer=f"{child.id} thought it was a ghost, because the weeny paper doily moved like something spooky.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding in {setting}?",
            answer="There was a misunderstanding because the tiny doily fluttered in the draft and looked ghost-like at first.",
        ),
        QAItem(
            question=f"What did {child.id} learn by the end of the story?",
            answer="The child learned to look carefully before deciding something was scary, because the ghost was only a paper doily.",
        ),
        QAItem(
            question=f"How did the ghost feel after the misunderstanding?",
            answer=f"At first {ghost.id} felt a little hurt, but then it became friendly again after the child apologized.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a doily?",
            answer="A doily is a small decorative cloth or paper mat, often lacy and light.",
        ),
        QAItem(
            question="Why can paper move in the air?",
            answer="Paper is very light, so a breeze or draft can make it flutter and dance.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding happens when someone thinks something is true, but they are wrong at first.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone remembers after an experience teaches them something.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_story(S) :- setting(S), child(C), doily(D), ghost(G), misunderstanding(C,G,D), lesson_learned(C,D).
misunderstanding(C,G,D) :- child(C), ghost(G), doily(D), fluttering(D), looks_like_ghost(D).
lesson_learned(C,D) :- child(C), doily(D), careful_look(C,D), apology(C,D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("doily", "doily"))
    lines.append(asp.fact("fluttering", "doily"))
    lines.append(asp.fact("looks_like_ghost", "doily"))
    lines.append(asp.fact("careful_look", "child", "doily"))
    lines.append(asp.fact("apology", "child", "doily"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show child_story/1."))
    return sorted(set(asp.atoms(model, "child_story")))


def asp_verify() -> int:
    python_set = {(k,) for k in SETTINGS.keys()}
    clingo_set = set(asp_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny ghost story world about a weeny paper doily, a misunderstanding, and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS.keys()))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(CHARACTER_TRAITS)
    return StoryParams(setting=setting, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.name, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show child_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show child_story/1."))
        print(f"{len(asp.atoms(model, 'child_story'))} compatible story settings:\n")
        for (sid,) in sorted(set(asp.atoms(model, "child_story"))):
            print(f"  {sid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            params = StoryParams(
                setting=setting,
                name=_safe_lookup(NAMES, list(SETTINGS.keys()).index(setting) % len(NAMES)),
                trait=_safe_lookup(CHARACTER_TRAITS, list(SETTINGS.keys()).index(setting) % len(CHARACTER_TRAITS)),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
