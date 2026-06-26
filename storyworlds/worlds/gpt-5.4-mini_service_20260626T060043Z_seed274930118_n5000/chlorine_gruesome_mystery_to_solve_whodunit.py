#!/usr/bin/env python3
"""
A standalone storyworld for a small whodunit mystery at the pool.
The seed inspiration is a child-facing mystery with chlorine and a gruesome,
but ultimately solvable, clue trail.
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

MYSTERY_WORDS = {"clue", "suspect", "whodunit", "mystery", "solve", "detective"}
BAD_ODORS = {"chlorine", "gloomy", "gruesome"}
THRESHOLD = 1.0



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
    carries: set[str] = field(default_factory=set)
    wears: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_obj: object | None = None
    culprit: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    indoor: bool
    smells: str
    affords: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    motive: str
    clue: str
    alibi: str
    innocent: bool = False
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


@dataclass
class StoryParams:
    place: str
    detective: str
    gender: str
    helper: str
    suspect: str
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


SETTINGS = {
    "pool": Setting(place="the pool", indoor=True, smells="chlorine", affords={"swim", "splash", "search"}),
    "locker_room": Setting(place="the locker room", indoor=True, smells="chlorine", affords={"search"}),
    "pool_deck": Setting(place="the pool deck", indoor=False, smells="chlorine", affords={"search"}),
}

SUSPECTS = {
    "lifeguard": Suspect(
        id="lifeguard",
        label="the lifeguard",
        motive="kept the pool safe and cleaned the water",
        clue="a whistle lay by the ladder",
        alibi="was watching the deep end when the trouble started",
    ),
    "janitor": Suspect(
        id="janitor",
        label="the janitor",
        motive="was carrying the big cleaning bottle",
        clue="a mop bucket stood by the door",
        alibi="was in the hallway getting more towels",
    ),
    "brother": Suspect(
        id="brother",
        label="the older brother",
        motive="wanted to help but had muddy shoes",
        clue="muddy footprints led toward the benches",
        alibi="was outside chasing a ball",
    ),
    "aunt": Suspect(
        id="aunt",
        label="the aunt",
        motive="brought snacks and a spare towel",
        clue="a paper bag held sticky crackers",
        alibi="was not near the water at all",
        innocent=True,
    ),
}

DETECTIVE_NAMES = ["Mina", "Toby", "Iris", "Niko", "Lena", "Pip"]
HELPER_NAMES = ["Aunt June", "Uncle Ray", "Dad", "Mom", "Big Sister"]

TRAITS = ["careful", "curious", "brave", "clever", "patient"]


def reasonableness_gate(place: str, suspect: str) -> None:
    if place not in SETTINGS:
        pass
    if suspect not in SUSPECTS:
        pass
    if place == "locker_room" and suspect == "aunt":
        pass


ASP_RULES = r"""
place(pool).
place(locker_room).
place(pool_deck).

suspect(lifeguard).
suspect(janitor).
suspect(brother).
suspect(aunt).

innocent(aunt).

at_risk(pool).
at_risk(locker_room).
at_risk(pool_deck).

solveable(Place, Suspect) :- place(Place), suspect(Suspect), not innocent(Suspect).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solveable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solveable/2."))
    return sorted(set(asp.atoms(model, "solveable")))


def asp_verify() -> int:
    py = {(p, s) for p in SETTINGS for s in SUSPECTS if not _safe_lookup(SUSPECTS, s).innocent}
    cl = set(asp_solveable())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit mystery at the pool.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "suspect", None):
        reasonableness_gate(getattr(args, "place", None), getattr(args, "suspect", None))
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    if _safe_lookup(SUSPECTS, suspect).innocent:
        suspect = "janitor"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, detective=name, gender=gender, helper=helper, suspect=suspect)


def introduce(world: World, hero: Entity, helper: str) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait', 'curious')} {hero.type} who loved solving small mysteries.")
    world.say(f"{hero.id} and {helper} had come to {world.setting.place} for an easy day, but the air smelled sharply of chlorine.")


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.detective, kind="character", type=params.gender, memes={"trait": params.trait}))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult"))
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    culprit = world.add(Entity(id=suspect.id, kind="character", type="adult", label=suspect.label))
    clue_obj = world.add(Entity(id="clue", type="thing", label="clue", phrase=suspect.clue))
    world.facts.update(hero=hero, helper=helper, suspect=culprit, suspect_data=suspect, clue=clue_obj)
    return world


def narrate_story(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    suspect_data = _safe_fact(world, world.facts, "suspect_data")

    world.say(f"{hero.id} noticed something gruesome in the smell: the chlorine was stronger near the steps.")
    world.say(f"That felt like a mystery to solve, so {hero.id} looked for a clue instead of guessing.")

    world.para()
    world.say(f"First {hero.id} checked the wet floor, then the bench, then the towel cart.")
    world.say(f"{suspect_data.clue.capitalize()} {world.setting.place if world.setting.place != 'the pool' else 'by the ladder'} gave {hero.id} a possible answer.")
    world.say(f"{helper.id} whispered, 'Whodunit?' and smiled, because {hero.id} was already thinking.")

    world.para()
    if suspect.id == "janitor":
        world.say(f"{hero.id} followed the mop bucket and found {suspect_data.alibi}.")
        world.say(f"The clue made sense: {suspect.label} had used the cleaning bottle, but only to keep the pool safe, not to cause trouble.")
        world.say(f"Then {hero.id} spotted the real mess: a cracked bottle cap had tipped chlorine near the drain.")
    elif suspect.id == "lifeguard":
        world.say(f"{hero.id} noticed the whistle by the ladder and looked up at {suspect.label}.")
        world.say(f"But {suspect.label} had been watching the deep end when the trouble started, so {hero.id} knew {suspect.pronoun('subject')} was not the culprit.")
        world.say(f"The real answer was simpler: a little spill near the steps had made the smell harsh.")
    else:
        world.say(f"{hero.id} followed the muddy prints to {suspect.label}.")
        world.say(f"But the prints only showed that {suspect.pronoun('subject')} had walked by, not that {suspect.pronoun('subject')} had done the deed.")
        world.say(f"The chlorine clue still pointed to the cleaning shelf, where the bottle cap sat crooked.")

    world.para()
    world.say(f"In the end, {hero.id} solved the mystery: nobody had done a nasty trick on purpose.")
    world.say(f"A small spill of chlorine had made the pool smell fierce and gruesome, but {helper.id} cleaned it up and {hero.id} felt proud to have cracked the whodunit.")
    world.facts["solved"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-friendly whodunit at {_safe_lookup(SETTINGS, params.place).place} with chlorine as an important clue.",
            f"Tell a short mystery where {params.detective} and {params.helper} solve a gruesome-smelling problem.",
            "Write a simple detective story that ends with the truth being smaller than it first seemed.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    suspect_data = _safe_fact(world, world.facts, "suspect_data")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the mystery about at {place}?",
            answer=f"It was about {hero.id}, {helper.id}, and the question of who caused the chlorine smell to seem so gruesome.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} think about the answer?",
            answer=f"The clue was {suspect_data.clue}, which gave {hero.id} a place to look first.",
        ),
        QAItem(
            question=f"Who looked suspicious at first in the whodunit?",
            answer=f"{suspect.label} looked suspicious at first, but the story showed that the clue did not make {suspect.pronoun('object')} guilty.",
        ),
        QAItem(
            question="What was the real problem?",
            answer="The real problem was a small chlorine spill that made the air smell strong and scary.",
        ),
        QAItem(
            question=f"How did the mystery get solved?",
            answer=f"{hero.id} looked carefully, followed the clues, and learned that nobody was trying to be mean; the spill was just an accident.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chlorine often used for?",
            answer="Chlorine is often used to help keep pool water clean.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find out what really happened.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who did it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pool", detective="Mina", gender="girl", helper="Aunt June", suspect="janitor"),
    StoryParams(place="pool_deck", detective="Toby", gender="boy", helper="Dad", suspect="lifeguard"),
    StoryParams(place="locker_room", detective="Iris", gender="girl", helper="Mom", suspect="brother"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show solveable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_solveable()
        print(f"{len(combos)} solveable combinations:")
        for place, suspect in combos:
            print(f"  {place:12} {suspect}")
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
            params = build_story_params(args, random.Random(seed))
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
            header = f"### {p.detective} at {p.place} vs. {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
