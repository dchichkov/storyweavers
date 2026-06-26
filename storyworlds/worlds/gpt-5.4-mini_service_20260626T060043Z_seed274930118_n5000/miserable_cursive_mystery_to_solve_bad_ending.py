#!/usr/bin/env python3
"""
A small storyworld about a ghostly cursive mystery with sound effects and a bad ending.
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
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    clue_ent: object | None = None
    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    mood: str
    echo: str
    flicker: str
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
class Clue:
    label: str
    phrase: str
    risk: str
    solve_step: str
    bad_end: str
    sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    setting: str
    clue: str
    name: str
    gender: str
    companion: str
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
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "attic": Setting(place="the attic", mood="miserable", echo="an anxious echo", flicker="a thin flicker"),
    "library": Setting(place="the old library", mood="miserable", echo="a creaky echo", flicker="a dusty flicker"),
    "hallway": Setting(place="the long hallway", mood="miserable", echo="a hollow echo", flicker="a cold flicker"),
}

CLUES = {
    "note": Clue(
        label="note",
        phrase="a torn note in cursive",
        risk="the ink might vanish",
        solve_step="follow the looping letters",
        bad_end="the note dissolved into gray dust",
        sound="whisper-whisper",
        tags={"cursive", "mystery", "ghost"},
    ),
    "key": Clue(
        label="key",
        phrase="a key wrapped in cursive ribbon",
        risk="the door might stay locked",
        solve_step="trace the ribbon's curls",
        bad_end="the key slipped through the floorboards",
        sound="clink-clack",
        tags={"mystery", "ghost"},
    ),
    "book": Clue(
        label="book",
        phrase="an old book with cursive names",
        risk="the names might be lost",
        solve_step="read the slanted pages",
        bad_end="the book shut with a sigh and never opened again",
        sound="thump-thrum",
        tags={"cursive", "mystery"},
    ),
}

GHOSTLY_NAMES = ["Mina", "Theo", "June", "Eli", "Rose", "Nora"]
COMPANIONS = ["cat", "lantern", "dog", "little brother", "friend"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story mystery with cursive clues and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GHOSTLY_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    if clue == "key" and getattr(args, "setting", None) == "attic":
        pass
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, companion=companion)


def reasonableness_gate(params: StoryParams) -> None:
    if params.clue == "note" and params.setting == "hallway":
        return
    if params.clue == "book" and params.setting == "library":
        return
    if params.clue == "key" and params.setting in SETTINGS:
        return
    pass


ASP_RULES = r"""
setting(attic). setting(library). setting(hallway).
clue(note). clue(key). clue(book).
cursive(note). cursive(book).
ghostly(attic). ghostly(library). ghostly(hallway).
valid(S,C) :- setting(S), clue(C), ghostly(S), mystery(C).
mystery(note). mystery(key). mystery(book).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        if "cursive" in _safe_lookup(CLUES, cid).tags:
            lines.append(asp.fact("cursive", cid))
        lines.append(asp.fact("mystery", cid))
    for sid in SETTINGS:
        lines.append(asp.fact("ghostly", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((s, c) for s in SETTINGS for c in CLUES)
    asp_set = set(asp_valid())
    py_set = set(py)
    if asp_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - py_set:
        print("only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in python:", sorted(py_set - asp_set))
    return 1


def scene(world: World, params: StoryParams) -> None:
    clue = _safe_lookup(CLUES, params.clue)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"fear": 0.0, "sadness": 0.0, "resolve": 0.0},
        memes={"miserable": 1.0},
    ))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=params.companion))
    clue_ent = world.add(Entity(id="clue", type=clue.label, label=clue.label, phrase=clue.phrase, tags=set(clue.tags)))

    setting = world.setting
    world.say(f"{hero.id} walked into {setting.place}, where {setting.mood} air hung like a wet sheet.")
    world.say(f"Nearby, {hero.pronoun('possessive')} {companion.label} made a small sound: {clue.sound}.")
    world.para()
    world.say(f"Then {hero.id} found {clue_ent.phrase}. The slanted letters looked like a secret trying not to be seen.")
    hero.meters["fear"] += 1
    hero.memes["miserable"] += 1
    world.say(f"{hero.id} felt {clue.risk}, so {hero.pronoun()} took a shaky breath and tried to {clue.solve_step}.")
    hero.meters["resolve"] += 1
    world.say(f"{setting.echo} answered back: {clue.sound}, {clue.sound}, {clue.sound}.")
    world.para()
    world.say(f"{hero.id} followed the clue to a hidden seam in the wall, but the room only sighed.")
    world.say(f"The answer was almost there, yet the last curl of cursive slipped away.")
    world.say(f"In the end, {clue.bad_end}, and the mystery stayed shut like a black lid.")
    world.say(f"{hero.id} stood very still, listening to the fading {clue.sound}, and the attic/library/hallway stayed miserably quiet.")
    world.facts.update(hero=hero, clue=clue_ent, clue_cfg=clue, companion=companion, params=params)
    return None


def generate_story_text(world: World, params: StoryParams) -> str:
    scene(world, params)
    return world.render()


def prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    clue = _safe_fact(world, world.facts, "clue_cfg")
    return [
        f'Write a short ghost story for a child in {_safe_lookup(SETTINGS, p.setting).place} with {clue.phrase}.',
        f"Tell a miserable mystery where {p.name} tries to solve a cursive clue but the ending goes wrong.",
        f"Write a spooky child-friendly story with sound effects like {clue.sound} and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    clue = _safe_fact(world, world.facts, "clue_cfg")
    hero = _safe_fact(world, world.facts, "hero")
    return [
        QAItem(
            question=f"Where did {p.name} look for the mysterious clue?",
            answer=f"{p.name} looked in {_safe_lookup(SETTINGS, p.setting).place}, a place that felt miserably quiet and ghostly.",
        ),
        QAItem(
            question=f"What made the mystery feel cursive?",
            answer=f"It felt cursive because {clue.phrase} had slanted writing that looked like a secret being whispered on paper.",
        ),
        QAItem(
            question=f"Did {p.name} solve the mystery?",
            answer=f"No. {hero.id} tried to follow the clue, but the ending was bad and the answer slipped away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    clue = _safe_fact(world, world.facts, "clue_cfg")
    return [
        QAItem(
            question="What is cursive writing?",
            answer="Cursive writing is a style of handwriting where the letters are joined and can look swoopy or slanted.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to solve by looking for clues.",
        ),
        QAItem(
            question="What do sound effects do in a story?",
            answer="Sound effects help the story feel alive by suggesting noises like whispers, creaks, or clinks.",
        ),
    ] + [
        QAItem(
            question=f"Why did the clue sound like {clue.sound}?",
            answer=f"It sounded like {clue.sound} because the ghostly room echoed each tiny movement and made the clue feel spooky.",
        )
    ]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(_safe_lookup(SETTINGS, params.setting))
    story = generate_story_text(world, params)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", clue="note", name="Mina", gender="girl", companion="cat"),
    StoryParams(setting="library", clue="book", name="Theo", gender="boy", companion="lantern"),
    StoryParams(setting="hallway", clue="key", name="June", gender="girl", companion="dog"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_sample(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for s, c in vals:
            print(f"{s} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                sample = build_sample(args, rng)
            except StoryError:
                continue
            sample.params.seed = base_seed + i - 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
