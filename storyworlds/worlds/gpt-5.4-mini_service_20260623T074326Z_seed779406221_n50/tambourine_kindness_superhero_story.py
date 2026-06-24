#!/usr/bin/env python3
"""
storyworlds/worlds/tambourine_kindness_superhero_story.py
=========================================================

A standalone storyworld for a tiny superhero-style kindness tale.

Premise:
- A child superhero hears that a shy neighbor's parade drum club has gone quiet.
- A bright tambourine is tempting: it can make a big cheerful sound, but it is
  also easy to snatch, shake too hard, or use selfishly.
- The real tension is not danger-from-fire, but whether the hero uses kindness:
  asks, shares, waits, and helps someone feel brave.

The world models:
- typed entities
- physical meters (distance, sound, sparkle, wear)
- emotional memes (joy, worry, kindness, courage, relief, trust)
- state-driven causal turns
- one clear ending image proving what changed

The story style aims at "Superhero Story": bold, concrete, kind, and active.
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


THRESHOLD = 1.0
KINDNESS_MIN = 2



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bell: object | None = None
    e: object | None = None
    helper: object | None = None
    hero: object | None = None
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
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    w: object | None = None
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
class Theme:
    id: str
    scene: str
    mission: str
    hero_title: str
    helper_title: str
    ending: str
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
class Tambourine:
    id: str
    label: str
    phrase: str
    shine: str
    shake: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


THEMES = {
    "city": Theme(
        id="city",
        scene="a bright city block",
        mission="the sidewalk concert",
        hero_title="Captain",
        helper_title="Spark",
        ending="ran home smiling under the streetlights",
    ),
    "park": Theme(
        id="park",
        scene="a breezy park path",
        mission="the picnic parade",
        hero_title="Hero",
        helper_title="Sidekick",
        ending="marched past the swing set with happy feet",
    ),
    "school": Theme(
        id="school",
        scene="the schoolyard",
        mission="the welcome rally",
        hero_title="Star",
        helper_title="Buddy",
        ending="clapped together beside the painted wall",
    ),
}

TAMBOURINES = {
    "red": Tambourine(
        id="red",
        label="tambourine",
        phrase="a bright red tambourine",
        shine="sparkled like a little sun",
        shake="jangled cheerfully",
        tags={"tambourine"},
    ),
    "blue": Tambourine(
        id="blue",
        label="tambourine",
        phrase="a blue tambourine with gold bells",
        shine="glinted like a hero badge",
        shake="rang with a soft tinkle",
        tags={"tambourine"},
    ),
}

RESPONSES = {
    "ask": Response(
        id="ask",
        sense=3,
        power=3,
        text="asked first, listened, and offered help with a gentle plan",
        fail="asked, but the moment had already turned too messy",
        qa_text="asked first and offered help",
        tags={"kindness"},
    ),
    "share": Response(
        id="share",
        sense=3,
        power=3,
        text="shared the tambourine and kept the beat slow and calm",
        fail="shared it, but the other child was too upset to join in yet",
        qa_text="shared the tambourine and kept the beat calm",
        tags={"kindness"},
    ),
    "return": Response(
        id="return",
        sense=2,
        power=2,
        text="returned the tambourine right away and waited with a kind smile",
        fail="returned it, but the helper still needed more comfort",
        qa_text="returned the tambourine and waited kindly",
        tags={"kindness"},
    ),
    "snatch": Response(
        id="snatch",
        sense=1,
        power=1,
        text="grabbed the tambourine and shook it too hard",
        fail="grabbed the tambourine, but made everything worse",
        qa_text="grabbed the tambourine",
        tags={"unkind"},
    ),
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Theo", "Ava", "Owen", "Zoe", "Finn"]
HELPER_NAMES = ["June", "Iris", "Max", "Luca", "Ruby", "Eli", "Mina", "Noah"]


@dataclass
class StoryParams:
    theme: str
    tambourine: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny superhero kindness story about a tambourine."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--tambourine", choices=sorted(TAMBOURINES))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "response", None) and _safe_lookup(RESPONSES, getattr(args, "response", None)).sense < KINDNESS_MIN:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    theme = getattr(args, "theme", None) or rng.choice(sorted(THEMES))
    tambourine = getattr(args, "tambourine", None) or rng.choice(sorted(TAMBOURINES))
    response = getattr(args, "response", None) or rng.choice([r for r in sorted(RESPONSES) if _safe_lookup(RESPONSES, r).sense >= KINDNESS_MIN])
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero = rng.choice([n for n in HERO_NAMES if n != ""])
    helper = rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(theme, tambourine, response, hero, hero_gender, helper, helper_gender, getattr(args, "seed", None))


def _other_pronoun(gender: str, case: str = "subject") -> str:
    e = Entity(id="x", type=gender)
    return e.pronoun(case)


def should_succeed(response: Response) -> bool:
    return response.sense >= KINDNESS_MIN


def tell(theme: Theme, tambourine: Tambourine, response: Response, hero: Entity, helper: Entity) -> World:
    w = World()
    w.add(hero)
    w.add(helper)
    w.add(w.add(Entity(id="hero_hat", label="mask", kind="thing", type="thing")))
    bell = w.add(Entity(id="tambourine", kind="thing", type="thing", label=tambourine.label))
    bell.meters["shine"] = 1.0
    bell.memes["attention"] = 1.0
    helper.memes["worry"] = 1.0
    hero.memes["courage"] = 1.0

    w.say(
        f"On {theme.scene}, {hero.id} became {theme.hero_title} Bright. "
        f"{hero.pronoun().capitalize()} loved using {bell.label} to help the neighborhood."
    )
    w.say(
        f"At {theme.mission}, {helper.id} stood beside the music table and looked nervous. "
        f"The {bell.phrase} {tambourine.shine}."
    )
    w.para()

    if should_succeed(response):
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
        helper.memes["trust"] += 1
        w.say(
            f"{hero.id} saw the worry and chose {response.text}. "
            f"{helper.id} relaxed because {hero.id} did not grab the tambourine away."
        )
        if response.id == "share":
            bell.meters["distance"] = 0
            bell.meters["wear"] = 0.1
            w.say(
                f"{hero.id} handed over the {bell.label} and kept the beat slow. "
                f"{bell.shake.capitalize()}, but gently, like a tiny marching song."
            )
        elif response.id == "ask":
            w.say(
                f"{hero.id} asked, 'Do you want to play too?' "
                f"Then {helper.id} nodded and tapped along."
            )
        else:
            w.say(
                f"{hero.id} returned the {bell.label} and waited with a kind smile. "
                f"That small kindness made the room feel bigger."
            )
        helper.memes["joy"] += 2
        helper.memes["worry"] = 0
        hero.memes["joy"] += 1
        hero.memes["kindness"] += 1
        w.para()
        w.say(
            f"Soon the music grew into a brave little parade, and {helper.id} found "
            f"{helper.pronoun().possessive if False else 'their'} courage in the rhythm."
        )
        w.say(
            f"By the end, {hero.id} and {helper.id} marched side by side, and the whole block cheered."
        )
        w.para()
        w.say(
            f"{hero.id} {theme.ending}. The {bell.label} was no longer just shiny; "
            f"it had become a gift that made two children feel strong together."
        )
        outcome = "kind"
    else:
        helper.memes["worry"] += 2
        hero.memes["kindness"] = 0
        w.say(
            f"But {hero.id} chose to {response.text}. "
            f"The loud jangle startled {helper.id}, and the happy beat fell apart."
        )
        w.say(
            f"{helper.id} hugged the music table and whispered for help, because the kindness was missing."
        )
        w.para()
        w.say(
            f"Then {hero.id} felt sorry, gave the {bell.label} back, and used a softer voice. "
            f"That was the first kind choice of the day."
        )
        hero.memes["remorse"] = 1
        helper.memes["trust"] = max(0, helper.memes.get("trust", 0) - 1)
        w.say(
            f"After that, the parade could begin only when everyone was ready."
        )
        w.para()
        w.say(
            f"In the end, {hero.id} learned that a superhero's biggest power was not the sound of the bells, "
            f"but the kindness used to share them."
        )
        outcome = "unkind"

    w.facts.update(
        hero=hero,
        helper=helper,
        tambourine=tambourine,
        theme=theme,
        response=response,
        outcome=outcome,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story where {f['hero'].id} finds a {f['tambourine'].label} on {f['theme'].scene} and learns kindness by helping {f['helper'].id}.",
        f"Tell a child-facing superhero tale about a {f['tambourine'].phrase} and a nervous friend, ending with a brave act of kindness.",
        f"Write a short Superhero Story-style scene where the hero uses {f['response'].id} to turn a shaky moment into a happy parade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, bell, theme, response = f["hero"], f["helper"], f["tambourine"], f["theme"], f["response"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"{hero.id} was the superhero, and {hero.pronoun()} used kindness to help {helper.id}.",
        ),
        QAItem(
            question=f"What made the helper nervous?",
            answer=f"The shiny {bell.label} and the busy parade made {helper.id} nervous at first.",
        ),
        QAItem(
            question=f"What did {hero.id} do with the tambourine?",
            answer=f"{response.qa_text}, which turned the moment toward kindness.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {helper.id} together in a happy superhero parade.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a small hand drum with little bells. When you shake or tap it, it makes a bright jingling sound.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, and be gentle with someone else's feelings.",
        ),
        QAItem(
            question="What should a hero do if someone seems worried?",
            answer="A kind hero should ask what is wrong, listen, and help in a gentle way.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
kind_resolve(H) :- hero(H), kindness(H, K), K >= kindness_min.
kind_resolve(H) :- hero(H), response(H, ask).
kind_resolve(H) :- hero(H), response(H, share).
kind_resolve(H) :- hero(H), response(H, return).
outcome(kind) :- kind_resolve(_).
outcome(unkind) :- not outcome(kind).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("kindness_min", KINDNESS_MIN)]
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for t in TAMBOURINES:
        lines.append(asp.fact("tambourine", t))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("hero", params.hero),
        asp.fact("response", params.response),
        asp.fact("kindness", params.hero, _safe_lookup(RESPONSES, params.response).sense),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    import asp
    rc = 0
    p = set(r for r, resp in RESPONSES.items() if resp.sense >= KINDNESS_MIN)
    model = asp.one_model(asp_program("", "#show response/1."))
    a = set(x for (x,) in asp.atoms(model, "response"))
    if a == set(RESPONSES):
        print("OK: ASP facts loaded.")
    else:
        rc = 1
        print("MISMATCH: ASP facts differ.")
    cases = [resolve_params(argparse.Namespace(theme=None, tambourine=None, response=r, seed=None), random.Random(i)) for i, r in enumerate(sorted(p))]
    bad = 0
    for sp in cases:
        if asp_outcome(sp) != ("kind" if should_succeed(_safe_lookup(RESPONSES, sp.response)) else "unkind"):
            bad += 1
    if bad == 0:
        print("OK: ASP outcome parity.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcomes.")
    return rc


def valid_choices() -> list[tuple[str, str, str]]:
    return [(t, b, r) for t in THEMES for b in TAMBOURINES for r, resp in RESPONSES.items() if resp.sense >= KINDNESS_MIN]


def generate(params: StoryParams) -> StorySample:
    hero = Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero")
    helper = Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper")
    w = tell(_safe_lookup(THEMES, params.theme), _safe_lookup(TAMBOURINES, params.tambourine), _safe_lookup(RESPONSES, params.response), hero, helper)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
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
    StoryParams("city", "red", "ask", "Maya", "girl", "Leo", "boy"),
    StoryParams("park", "blue", "share", "Ava", "girl", "Finn", "boy"),
    StoryParams("school", "red", "return", "Theo", "boy", "Nina", "girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "response", None) and _safe_lookup(RESPONSES, getattr(args, "response", None)).sense < KINDNESS_MIN:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    theme = getattr(args, "theme", None) or rng.choice(sorted(THEMES))
    tambourine = getattr(args, "tambourine", None) or rng.choice(sorted(TAMBOURINES))
    response = getattr(args, "response", None) or rng.choice([r for r, resp in RESPONSES.items() if resp.sense >= KINDNESS_MIN])
    hero = rng.choice(HERO_NAMES)
    helper = rng.choice([n for n in HELPER_NAMES if n != hero])
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    return StoryParams(theme, tambourine, response, hero, hero_gender, helper, helper_gender)


def build_parser_and_main():
    pass


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("", "#show outcome/1.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print("valid responses:", ", ".join(sorted(r for r, resp in RESPONSES.items() if resp.sense >= KINDNESS_MIN)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
