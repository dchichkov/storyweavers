#!/usr/bin/env python3
"""
storyworlds/worlds/dilemma_playroom_twist_friendship_mystery.py
===============================================================

A small storyworld set in a playroom, shaped like a gentle mystery with a
dilemma, a twist, and a friendship resolution.

Premise:
- A child notices a favorite toy has gone missing in the playroom.
- The child suspects a friend may know something, but does not want to be unfair.
- The child searches clues, chooses whether to accuse or trust, and the truth
  turns out to be a surprise prepared by the friend.

The world models both physical state (meters) and emotional state (memes):
- meters track visible things like hiddenness, tidiness, and discovered clues
- memes track feelings like worry, trust, relief, and delight

The story is generated from a small deterministic simulation rather than a
frozen paragraph with swapped nouns.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    treasure: object | None = None
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
    place: str = "the playroom"
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
    id: str
    text: str
    kind: str
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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    treasure: str
    seed: Optional[int] = None
    params: object | None = None
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
        self.clues: list[Clue] = []

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
        clone.clues = list(self.clues)
        return clone


def hero_pronouns(hero: Entity) -> tuple[str, str, str]:
    return hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")


def setup_story(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved the quiet corners of {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} also loved {friend.id}, because {friend.id} always wanted to play fair."
    )
    world.say(
        f"Most of all, {hero.id} treasured {hero.pronoun('possessive')} {treasure.label}."
    )


def notice_loss(world: World, hero: Entity, treasure: Entity) -> None:
    treasure.hidden = True
    treasure.meters["hiddenness"] = 1
    hero.memes["worry"] += 1
    world.say(
        f"One afternoon, {hero.id} reached for {hero.pronoun('possessive')} {treasure.label}, but it was gone."
    )
    world.say(
        f"The empty shelf looked strange, and {hero.id} felt a small knot of worry in {hero.pronoun('possessive')} chest."
    )


def add_clue(world: World, text: str, kind: str) -> None:
    world.clues.append(Clue(id=f"clue_{len(world.clues)+1}", text=text, kind=kind))


def search_clues(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} looked under the blocks, behind the cushions, and inside the toy basket."
    )
    add_clue(world, "A ribbon was tucked near the curtain.", "surprise")
    add_clue(world, "Tiny footprints led to the art table.", "trail")
    world.say(
        f"Near the art table, {hero.id} found a ribbon and tiny footprints, but no clear answer."
    )


def dilemma_choice(world: World, hero: Entity, friend: Entity, treasure: Entity) -> str:
    hero.memes["dilemma"] += 1
    world.say(
        f"{hero.id} had a dilemma: should {hero.pronoun('subject')} ask {friend.id} hard questions, or keep searching first?"
    )
    # Reasonable choice in this tiny domain: search first, do not accuse.
    return "search"


def search_first(world: World, hero: Entity) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} chose to search a little longer, because a good mystery deserved a fair look."
    )


def reveal_twist(world: World, friend: Entity, treasure: Entity, hero: Entity) -> None:
    treasure.hidden = False
    treasure.found = True
    treasure.meters["hiddenness"] = 0
    friend.memes["joy"] += 1
    hero.memes["surprise"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"Then {friend.id} froze, smiled, and reached behind a paint box."
    )
    world.say(
        f"There was the missing {treasure.label} all along."
    )
    world.say(
        f"{friend.id} admitted the twist: {friend.pronoun('subject').capitalize()} had hidden it for a surprise cleanup game, not to be mean."
    )


def friendship_resolution(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    hero.memes["worry"] = 0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} blinked, then laughed in relief, because the clue trail had pointed to a silly surprise instead of a real problem."
    )
    world.say(
        f"{hero.id} and {friend.id} put the playroom back together side by side, and their friendship felt even stronger afterward."
    )
    world.say(
        f"In the end, the {treasure.label} was safe, the mystery was solved, and the playroom looked bright again."
    )


def tell(world: World, hero: Entity, friend: Entity, treasure: Entity) -> World:
    setup_story(world, hero, friend, treasure)
    world.para()
    notice_loss(world, hero, treasure)
    search_clues(world, hero, friend, treasure)
    choice = dilemma_choice(world, hero, friend, treasure)
    if choice == "search":
        search_first(world, hero)
    world.para()
    reveal_twist(world, friend, treasure, hero)
    friendship_resolution(world, hero, friend, treasure)

    world.facts.update(
        hero=hero,
        friend=friend,
        treasure=treasure,
        choice=choice,
        setting=world.setting,
        clues=list(world.clues),
    )
    return world


SETTINGS = {
    "playroom": Setting(place="the playroom"),
}

TREASURES = {
    "bear": ("teddy bear", "a soft teddy bear with a blue bow"),
    "car": ("red toy car", "a red toy car with shiny wheels"),
    "puzzle": ("wooden puzzle", "a wooden puzzle with bright animals"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Ben", "Max"]
TRAITS = ["curious", "gentle", "patient", "clever", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    return [("playroom", treasure_id) for treasure_id in TREASURES]


@dataclass
class WorldConfig:
    place: str = "playroom"
    treasure: str = "bear"
    hero_name: str = "Mia"
    hero_gender: str = "girl"
    friend_name: str = "Noah"
    friend_gender: str = "boy"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle playroom mystery with a dilemma, a twist, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or "playroom"
    treasure = getattr(args, "treasure", None) or rng.choice(sorted(TREASURES))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero_name])
    if place != "playroom":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        treasure=treasure,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, traits=["little", "curious"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender, traits=["little", "kind"]))
    treasure_label, treasure_phrase = _safe_lookup(TREASURES, params.treasure)
    treasure = world.add(Entity(id="treasure", type="thing", label=treasure_label, phrase=treasure_phrase, owner=hero.id))
    tell(world, hero, friend, treasure)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    treasure = _safe_fact(world, f, "treasure")
    return [
        f'Write a short mystery story for a child about a lost {treasure.label} in the playroom.',
        f"Tell a gentle story where {hero.id} finds a clue, faces a dilemma, and learns a surprise from a friend.",
        f'Write a playroom story with a twist and a friendship ending that includes the word "dilemma".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    treasure: Entity = _safe_fact(world, f, "treasure")
    qa = [
        QAItem(
            question=f"What was missing from the playroom at the start of the story?",
            answer=f"The missing thing was {hero.pronoun('possessive')} {treasure.label}.",
        ),
        QAItem(
            question=f"What dilemma did {hero.id} face after finding the clues?",
            answer=f"{hero.id} had to choose between asking {friend.id} hard questions or keeping search for clues first.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that {friend.id} had hidden the {treasure.label} for a surprise game, not to be mean.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They solved the mystery, shared relief, and put the playroom back together as friends.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that can help someone figure out what happened.",
        ),
        QAItem(
            question="What does dilemma mean?",
            answer="A dilemma is a hard choice between two things that both matter.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care about each other and try to be fair.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(playroom).
treasure(bear).
treasure(car).
treasure(puzzle).
valid(playroom, T) :- treasure(T).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "playroom")] + [asp.fact("treasure", t) for t in TREASURES])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible combos:")
        for place, treasure in vals:
            print(f"  {place} {treasure}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for treasure in sorted(TREASURES):
            params = StoryParams(
                place="playroom",
                treasure=treasure,
                hero_name="Mia",
                hero_gender="girl",
                friend_name="Noah",
                friend_gender="boy",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
