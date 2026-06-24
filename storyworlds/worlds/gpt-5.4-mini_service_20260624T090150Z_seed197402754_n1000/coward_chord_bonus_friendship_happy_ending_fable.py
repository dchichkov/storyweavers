#!/usr/bin/env python3
"""
A tiny fable world about a timid friend, a musical chord, and a happy bonus.

Seed tale used to build the world:
---
A small crow was very cowardly. He loved listening to music, but he was too shy to
strike the harp string and make the full chord at the spring meadow gathering.

One day, his friend the rabbit stayed beside him and said that a true friend does
not laugh at a trembling wing. The rabbit helped the crow practice one note, then
two notes, and finally the whole chord. The crow tried again, found his courage,
and played the chord for everyone.

The meadow cheered. As a bonus, the fox brought a basket of sweet berries for both
friends, and the cowardly little crow was not so cowardly anymore.

Causal state updates:
---
    fear + spotlight + mistake risk  -> fear rises
    friendship support               -> fear falls, courage rises
    successful chord                 -> pride rises, group joy rises
    group joy + kindness             -> bonus gift appears
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["fear", "courage", "joy", "pride", "friendship", "kindness", "stress"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "fox", "crow", "rabbit"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the meadow"
    stage: str = "the mossy stump"
    audience: str = "the little animals"
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
class Instrument:
    id: str
    label: str
    sound: str
    risk: str
    can_make_chord: bool = True
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
class BonusGift:
    label: str
    phrase: str
    cheer: str
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
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def apply_rules(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    instrument = world.facts.get("instrument")
    if not hero or not friend or not instrument:
        return out

    h = world.get(hero.id)
    f = world.get(friend.id)

    # Fear rises when the timid friend thinks about the stage.
    sig = ("fear", h.id)
    if h.memes["fear"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        h.memes["stress"] += 1
        out.append(f"{h.id} trembled near {world.setting.stage}.")

    # Friendship support lowers fear and raises courage.
    sig = ("support", h.id, f.id)
    if h.memes["friendship"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        h.memes["fear"] = max(0.0, h.memes["fear"] - 1.0)
        h.memes["courage"] += 1
        f.memes["kindness"] += 1
        out.append(f"{f.id} stayed close, and {h.id} felt braver.")

    # Successful chord raises joy/pride.
    sig = ("chord", h.id)
    if h.memes["courage"] >= THRESHOLD and h.memes["fear"] < THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        h.memes["joy"] += 1
        h.memes["pride"] += 1
        f.memes["joy"] += 1
        out.append(f"{h.id} made the full chord, and the meadow brightened.")

    # Bonus gift appears when the music and kindness have both happened.
    sig = ("bonus", h.id)
    if h.memes["joy"] >= THRESHOLD and f.memes["kindness"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        gift = _safe_fact(world, world.facts, "gift")
        world.facts["bonus_ready"] = True
        out.append(f"As a bonus, {gift.label} was brought to both friends.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_success(world: World, hero: Entity, friend: Entity, instrument: Instrument) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] += 1
    sim.get(hero.id).memes["friendship"] += 1
    apply_rules(sim, narrate=False)
    h = sim.get(hero.id)
    return h.memes["pride"] >= THRESHOLD


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there once lived a little {hero.type} named {hero.id}."
        f" {hero.id} was a coward at the sound of a crowd, but {hero.pronoun()} loved music."
    )


def setup_music(world: World, hero: Entity, friend: Entity, instrument: Instrument) -> None:
    hero.memes["fear"] += 1
    hero.memes["friendship"] += 1
    world.say(
        f"One spring day, {hero.id} stood beside {world.setting.stage} with "
        f"{friend.id}, who smiled kindly and pointed to the {instrument.label}."
    )
    world.say(
        f'"Try one note first," said {friend.id}. "Then another. A chord can grow from a tiny start."'
    )


def hesitation(world: World, hero: Entity, instrument: Instrument) -> None:
    world.say(
        f"{hero.id} looked at the string and felt cowardly. "
        f"The first note seemed small, but the full chord seemed very large."
    )
    if not predict_success(world, hero, world.get(world.facts["friend"].id), instrument):
        pass


def attempt(world: World, hero: Entity, friend: Entity, instrument: Instrument) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"{friend.id} touched {hero.pronoun('possessive')} wing and said, "
        f'"You do not have to be loud to be brave."'
    )
    world.say(
        f"So {hero.id} took a breath, tried again, and made a clear little sound."
    )
    world.say(
        f"Then {hero.id} played the next note, and then the next, until the notes fit together in a chord."
    )


def ending(world: World, hero: Entity, friend: Entity, gift: BonusGift) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'The audience cheered, and {hero.id} stopped feeling like a coward. '
        f'He stood taller beside {friend.id}, while {gift.phrase} made the ending feel extra sweet.'
    )
    world.say(
        f"From that day on, the little {hero.type} remembered that friendship can turn shaking paws into brave music."
    )


SETTINGS = {
    "meadow": Setting(place="the meadow", stage="the mossy stump", audience="the little animals"),
}

INSTRUMENTS = {
    "harp": Instrument(
        id="harp",
        label="harp",
        sound="clear notes",
        risk="a trembling mistake",
        can_make_chord=True,
    ),
}

GIFTS = {
    "berries": BonusGift(
        label="a bonus basket of sweet berries",
        phrase="a bonus basket of sweet berries",
        cheer="sweet and shiny",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Mira", "Pia"]
BOY_NAMES = ["Pip", "Cody", "Tobin", "Nell", "Hugo"]


@dataclass
class StoryParams:
    place: str = "meadow"
    instrument: str = "harp"
    gift: str = "berries"
    name: str = "Pip"
    friend_name: str = "Ria"
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    ap = argparse.ArgumentParser(description="A tiny fable world about friendship and a brave chord.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES + GIRL_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n != name])
    return StoryParams(
        place=getattr(args, "place", None) or "meadow",
        instrument=getattr(args, "instrument", None) or "harp",
        gift=getattr(args, "gift", None) or "berries",
        name=name,
        friend_name=friend_name,
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="crow", traits=["cowardly", "gentle"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="rabbit", traits=["kind", "steady"]))
    instrument = _safe_lookup(INSTRUMENTS, params.instrument)
    gift = _safe_lookup(GIFTS, params.gift)
    world.facts.update(hero=hero, friend=friend, instrument=instrument, gift=gift)

    intro(world, hero)
    world.para()
    setup_music(world, hero, friend, instrument)
    hesitation(world, hero, instrument)
    world.para()
    attempt(world, hero, friend, instrument)
    apply_rules(world, narrate=True)
    world.para()
    ending(world, hero, friend, gift)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, instrument = f["hero"], f["friend"], f["instrument"]
    return [
        'Write a short fable for a young child about a coward who becomes brave with friendship.',
        f"Tell a gentle story where {hero.id} is afraid to play a {instrument.label} chord until {friend.id} helps.",
        f"Write a happy ending fable that uses the words coward, chord, and bonus.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, instrument = f["hero"], f["friend"], f["instrument"]
    return [
        QAItem(
            question=f"Who was the cowardly little character in the story?",
            answer=f"The cowardly little character was {hero.id}, the crow who loved music but felt shy at first.",
        ),
        QAItem(
            question=f"Who helped {hero.id} feel braver near the {instrument.label}?",
            answer=f"{friend.id}, the kind rabbit, stayed close and helped {hero.id} practice until the fear went down.",
        ),
        QAItem(
            question=f"What did {hero.id} finally make after practicing the notes?",
            answer=f"{hero.id} finally made the full chord, and the whole meadow heard the happy sound.",
        ),
        QAItem(
            question=f"What was the bonus at the end of the story?",
            answer="The bonus was a basket of sweet berries brought for both friends after the music turned out well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chord in music?",
            answer="A chord is two or more notes played together so they sound like one musical shape.",
        ),
        QAItem(
            question="What does coward mean?",
            answer="A coward is someone who is very afraid to try something, even when it would be safe to do with help.",
        ),
        QAItem(
            question="What does bonus mean?",
            answer="A bonus is something extra that is given in addition to the main thing, like a small gift or treat.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about each other, help each other, and stay kind.",
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
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        if memes:
            lines.append(f"  {e.id:10} ({e.type:8}) memes={memes}")
        else:
            lines.append(f"  {e.id:10} ({e.type:8})")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
coward(H) :- hero(H), fear(H), not courage(H).
friendship_support(H) :- friend(F), helps(F,H).
brave(H) :- hero(H), friendship_support(H), chord_played(H).
bonus_ready(H) :- brave(H), kindness(H).
#show coward/1.
#show brave/1.
#show bonus_ready/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("fear", "hero"),
        asp.fact("helps", "friend", "hero"),
        asp.fact("chord_played", "hero"),
        asp.fact("kindness", "friend"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show coward/1. #show brave/1. #show bonus_ready/1."))
    atoms = set((a.name, tuple(arg.name if arg.type == a.arguments[0].type else arg.number for arg in a.arguments)) for a in model)
    expected = {("coward", ("hero",)), ("brave", ("hero",)), ("bonus_ready", ("hero",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(atoms))
    print("  expected:", sorted(expected))
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show coward/1. #show brave/1. #show bonus_ready/1."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show coward/1. #show brave/1. #show bonus_ready/1."))
        print("\n".join(sorted(str(a) for a in model)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(name="Pip", friend_name="Ria"))]
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
