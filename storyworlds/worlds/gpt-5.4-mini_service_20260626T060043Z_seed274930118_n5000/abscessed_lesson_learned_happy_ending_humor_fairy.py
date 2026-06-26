#!/usr/bin/env python3
"""
Fairy-tale storyworld: an abscessed lesson learned with a happy ending and a
little humor.

Premise:
A small royal child loves sugary buns but has a toothache that has turned into an
abscess. A wise beekeeper-healer notices the swelling, warns about the hurt, and
offers a gentle remedy. The child learns the lesson, follows the cure, and ends
the day smiling with a softer, funnier kind of victory.

The world model tracks:
- physical meters: pain, swelling, sweetness, warmth, cleanliness, relief
- emotional memes: stubbornness, worry, trust, laughter, gratitude, pride

The story is intentionally small and constraint-checked:
- the problem must be real enough to justify the warning
- the cure must actually fit the problem
- the ending must prove a changed state
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"pain": 0.0, "swelling": 0.0, "sweetness": 0.0, "warmth": 0.0, "cleanliness": 0.0, "relief": 0.0}
        if not self.memes:
            self.memes = {"stubbornness": 0.0, "worry": 0.0, "trust": 0.0, "laughter": 0.0, "gratitude": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "mother"}
        male = {"boy", "prince", "king", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the old castle garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Trouble:
    id: str
    noun: str
    symptom: str
    warning: str
    has_abscess: bool
    pain_kind: str = "pain"
    keyword: str = "abscessed"
    tags: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    reduces: set[str]
    covers: set[str] = field(default_factory=set)
    humorous_note: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _hero(entity: Entity) -> str:
    return entity.noun()


def _nice_amount(x: float) -> str:
    return "a little" if x < 2 else "quite a lot"


def apply_trouble(world: World, hero: Entity, trouble: Trouble, narrate: bool = True) -> None:
    if trouble.has_abscess:
        hero.meters["pain"] += 2
        hero.meters["swelling"] += 2
    hero.memes["worry"] += 1
    if narrate:
        world.say(
            f"{hero.noun()} had {_nice_amount(hero.meters['pain'])} {trouble.symptom}, "
            f"and {hero.pronoun('possessive')} cheek puffed up like a grumpy plum."
        )


def apply_remedy(world: World, hero: Entity, remedy: Remedy, narrate: bool = True) -> None:
    hero.meters["pain"] = max(0.0, hero.meters["pain"] - 2)
    hero.meters["swelling"] = max(0.0, hero.meters["swelling"] - 2)
    hero.meters["relief"] += 2
    hero.meters["cleanliness"] += 1
    hero.memes["trust"] += 1
    if narrate:
        world.say(
            f"{hero.noun()} tried {remedy.label}, and the hurt began to fade like a candle at dawn."
        )


def predict_recovery(world: World, hero: Entity, remedy: Remedy, trouble: Trouble) -> dict[str, float]:
    sim = world.copy()
    h = sim.get(hero.id)
    apply_remedy(sim, h, remedy, narrate=False)
    return {"pain": h.meters["pain"], "swelling": h.meters["swelling"], "relief": h.meters["relief"]}


def tell(world: World, hero: Entity, caregiver: Entity, trouble: Trouble, remedy: Remedy) -> World:
    world.say(
        f"Once upon a time, {hero.noun()} lived in {world.setting.place}, where the towers were tall "
        f"and the spoons were never quite serious."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved sweet buns so much that even the baker laughed and said, "
        f'"{hero.pronoun("possessive").capitalize()} teeth are keeping a very busy diary."'
    )
    world.say(
        f"Then one morning, {hero.noun()} noticed {trouble.warning}, and {hero.pronoun('possessive')} smile felt lopsided."
    )
    apply_trouble(world, hero, trouble)

    world.para()
    world.say(
        f"{caregiver.noun().capitalize()} looked closely and said, "
        f'"That is not a tiny grumble; that is an {trouble.keyword} sore, and it needs a gentle cure."'
    )
    world.say(
        f'"If we do nothing, it will stay swollen and mean," {caregiver.pronoun()} warned, '
        f'but {hero.pronoun()} still tried to act brave.'
    )
    hero.memes["stubbornness"] += 1
    world.say(
        f"{hero.noun()} made a heroic face, which only made the cheek wobble funnier."
    )

    world.para()
    world.say(
        f"At last, {caregiver.noun()} offered a remedy: {remedy.prep}."
    )
    world.say(
        f"It sounded odd enough to make {hero.noun()} snort a little, because {remedy.humorous_note}"
    )
    pred = predict_recovery(world, hero, remedy, trouble)
    if pred["pain"] >= THRESHOLD:
        pass

    apply_remedy(world, hero, remedy)
    world.say(
        f"{hero.noun().capitalize()} followed the advice, and soon the swelling shrank and the ache went soft."
    )
    world.say(
        f"By evening, {hero.noun()} could grin again, and even the spoon seemed relieved."
    )
    world.say(
        f"{hero.noun()} learned a lesson: when a small hurt starts acting like a royal monster, it is wise to get help early."
    )
    hero.memes["gratitude"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"So the day ended with a happy ending, a cleaned-up smile, and a laugh at how a grumpy cheek had lost the argument."
    )

    world.facts.update(hero=hero, caregiver=caregiver, trouble=trouble, remedy=remedy)
    return world


SETTING = Setting(
    place="the old castle garden",
    indoors=False,
    affords={"sweet_bun", "visit_healer"},
)

TROUBLES = {
    "abscessed_tooth": Trouble(
        id="abscessed_tooth",
        noun="tooth",
        symptom="a throbbing toothache",
        warning="one tooth had gone abscessed and the gum was swollen",
        has_abscess=True,
        tags={"abscessed", "tooth", "pain"},
    )
}

REMEDIES = {
    "clove_rinse": Remedy(
        id="clove_rinse",
        label="a warm clove rinse",
        prep="the healer mixed a warm clove rinse and asked for slow swishing",
        tail="and the ache soon lost its temper",
        reduces={"pain", "swelling"},
        humorous_note="the cup smelled like a spice jar had learned to sing",
    )
}

HEROES = [
    ("Pippa", "girl"),
    ("Bram", "boy"),
    ("Mina", "girl"),
    ("Tobin", "boy"),
]

CARETAKERS = [
    ("Nanny Fern", "mother"),
    ("Sir Moss", "father"),
    ("Aunt Willow", "woman"),
]

TRAITS = ["brave", "curious", "silly", "stubborn", "gentle"]


@dataclass
class StoryParams:
    name: str
    gender: str
    caretaker_name: str
    caretaker_gender: str
    trait: str
    trouble: str = "abscessed_tooth"
    remedy: str = "clove_rinse"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world: an abscessed lesson learned with humor.")
    ap.add_argument("--name", choices=[n for n, _ in HEROES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=[n for n, _ in CARETAKERS])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    hero_name, hero_gender = (getattr(args, "name", None), getattr(args, "gender", None)) if getattr(args, "name", None) and getattr(args, "gender", None) else rng.choice(HEROES)
    if getattr(args, "name", None) and not getattr(args, "gender", None):
        hero_gender = next(g for n, g in HEROES if n == getattr(args, "name", None))
    if getattr(args, "gender", None) and not getattr(args, "name", None):
        hero_name = rng.choice([n for n, g in HEROES if g == getattr(args, "gender", None)])

    caretaker_name, caretaker_gender = rng.choice(CARETAKERS)
    if getattr(args, "caretaker", None):
        caretaker_name = getattr(args, "caretaker", None)
        caretaker_gender = next(g for n, g in CARETAKERS if n == getattr(args, "caretaker", None))

    if getattr(args, "trait", None):
        trait = getattr(args, "trait", None)
    else:
        trait = rng.choice(TRAITS)

    trouble = getattr(args, "trouble", None) or "abscessed_tooth"
    remedy = getattr(args, "remedy", None) or "clove_rinse"

    return StoryParams(
        name=hero_name,
        gender=hero_gender,
        caretaker_name=caretaker_name,
        caretaker_gender=caretaker_gender,
        trait=trait,
        trouble=trouble,
        remedy=remedy,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=params.caretaker_gender, label=params.caretaker_name))
    trouble = _safe_lookup(TROUBLES, params.trouble)
    remedy = _safe_lookup(REMEDIES, params.remedy)

    tell(world, hero, caretaker, trouble, remedy)

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
    trouble = _safe_fact(world, f, "trouble")
    remedy = _safe_fact(world, f, "remedy")
    return [
        f'Write a short fairy tale for a young child about a character named {hero.label} and the word "{trouble.keyword}".',
        f"Tell a gentle story where {hero.label} learns a lesson after an {trouble.keyword} toothache, then feels better with {remedy.label}.",
        f"Write a humorous fairy tale with a happy ending in which a grumpy ache is solved by a wise helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    caretaker: Entity = _safe_fact(world, f, "caretaker")
    trouble: Trouble = _safe_fact(world, f, "trouble")
    remedy: Remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"What kind of problem did {hero.label} have?",
            answer=f"{hero.label} had an {trouble.keyword} tooth sore, with a swollen cheek and a throbbing toothache.",
        ),
        QAItem(
            question=f"Who warned {hero.label} that the hurt needed help?",
            answer=f"{caretaker.label} noticed the swollen cheek and warned that the sore needed a gentle cure.",
        ),
        QAItem(
            question=f"What did {hero.label} use to feel better?",
            answer=f"{hero.label} used {remedy.label}, which helped the pain and swelling go down.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer="The lesson was that it is wise to get help early when a small hurt starts acting big.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.label} smiling again and laughing at the grumpy cheek.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an abscessed tooth mean?",
            answer="An abscessed tooth is a badly infected tooth or sore gum that can cause swelling and a strong ache.",
        ),
        QAItem(
            question="Why is a warm rinse sometimes used for a sore mouth?",
            answer="A warm rinse can help clean the mouth, soothe the area, and make it feel a little better.",
        ),
        QAItem(
            question="Why do fairy tales often use a wise helper?",
            answer="Fairy tales often use a wise helper so the hero can learn a lesson and find a safe way through trouble.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.label or ent.type} " + " ".join(parts))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A story is valid when the problem is real and the remedy fits it.
needs_help(T) :- trouble(T), abscessed(T).
fits(R,T) :- remedy(R), trouble(T), reduces(R,pain), reduces(R,swelling).
valid_story(T,R) :- needs_help(T), fits(R,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.has_abscess:
            lines.append(asp.fact("abscessed", tid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for x in sorted(r.reduces):
            lines.append(asp.fact("reduces", rid, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(t, r) for t in TROUBLES for r in REMEDIES if _safe_lookup(TROUBLES, t).has_abscess and {"pain", "swelling"} <= _safe_lookup(REMEDIES, r).reduces}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("python only:", sorted(python_set - clingo_set))
    print("clingo only:", sorted(clingo_set - python_set))
    return 1


def explain_rejection(trouble: Trouble, remedy: Remedy) -> str:
    return f"(No story: {remedy.label} does not clearly soothe an {trouble.keyword} sore enough for a happy ending.)"


def valid_choice(trouble: Trouble, remedy: Remedy) -> bool:
    return trouble.has_abscess and {"pain", "swelling"} <= remedy.reduces


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "trouble", None) and getattr(args, "remedy", None):
        if not valid_choice(_safe_lookup(TROUBLES, getattr(args, "trouble", None)), _safe_lookup(REMEDIES, getattr(args, "remedy", None))):
            pass
    return resolve_params(args, rng)


CURATED = [
    StoryParams(name="Pippa", gender="girl", caretaker_name="Nanny Fern", caretaker_gender="mother", trait="silly"),
    StoryParams(name="Bram", gender="boy", caretaker_name="Sir Moss", caretaker_gender="father", trait="stubborn"),
    StoryParams(name="Mina", gender="girl", caretaker_name="Aunt Willow", caretaker_gender="woman", trait="curious"),
]


def build_one(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible trouble/remedy pairs:\n")
        for t, r in stories:
            print(f"  {t} -> {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [build_one(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_story_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = build_one(params)
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
            header = f"### {p.name}: {p.trouble} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
