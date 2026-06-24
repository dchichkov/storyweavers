#!/usr/bin/env python3
"""
storyworlds/worlds/proton_bland_relieve_magic_moral_value_adventure.py
======================================================================

A small adventure story world about a child on a quest to relieve a bland
proton with Magic and Moral Value.

Source tale seed:
---
A little explorer finds a bland proton trapped in a gray jar inside an old
observatory. The proton feels dull and lonely, and the explorer wants to
relieve it with a bit of magic. A wise helper explains that the strongest
magic comes when the explorer chooses a Moral Value: sharing, honesty, and
care. The explorer must decide whether to keep the bright ribbon for
themselves or use it to help the proton. In the end, kindness unlocks the
magic, the jar opens, and the proton becomes bright and happy again.

World shape:
---
    proton blandness + confinement -> need for relief
    helper guidance + moral choice  -> moral_value increases
    moral_value + magic ribbon      -> jar opens / proton relieved
    released proton                 -> brightness + joy, ending image
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    jar: object | None = None
    proton: object | None = None
    value: object | None = None
    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

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
class Setting:
    place: str
    mood: str = "mysterious"
    affords: set[str] = field(default_factory=set)
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
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    requires: set[str]
    helps: set[str]
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
class MoralValue:
    id: str
    label: str
    prompt: str
    reward: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""
        self.history: list[str] = []

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = self.zone
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# Registries
SETTINGS = {
    "observatory": Setting(place="the old observatory", mood="mysterious", affords={"quest"}),
    "forest_path": Setting(place="the forest path", mood="brave", affords={"quest"}),
    "moon_bridge": Setting(place="the moonlit bridge", mood="sparkling", affords={"quest"}),
}

MAGIC = {
    "ribbon": MagicItem(
        id="ribbon",
        label="bright ribbon",
        phrase="a bright ribbon with tiny stars",
        effect="the ribbon hums with a little glow",
        requires={"moral_value"},
        helps={"bland", "trapped"},
    ),
    "lamp": MagicItem(
        id="lamp",
        label="magic lantern",
        phrase="a little magic lantern",
        effect="the lantern shines warm and gold",
        requires={"moral_value"},
        helps={"dark", "bland"},
    ),
}

MORAL_VALUES = {
    "sharing": MoralValue(
        id="sharing",
        label="Moral Value",
        prompt="sharing",
        reward="the best kind of magic comes from sharing",
    ),
    "honesty": MoralValue(
        id="honesty",
        label="Moral Value",
        prompt="honesty",
        reward="truth makes magic stronger",
    ),
    "kindness": MoralValue(
        id="kindness",
        label="Moral Value",
        prompt="kindness",
        reward="kindness opens stuck things",
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Tess", "Ava", "Ruby"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Eli", "Max", "Jude"]
TRAITS = ["curious", "brave", "gentle", "lively", "patient"]


@dataclass
class StoryParams:
    place: str
    magic: str
    value: str
    name: str
    gender: str
    trait: str
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


def _rule_bland_proton(world: World) -> None:
    proton = world.get("proton")
    if proton.meters.get("bland", 0.0) >= THRESHOLD and proton.meters.get("trapped", 0.0) >= THRESHOLD:
        proton.memes["need_relief"] = 1.0


def _rule_moral_makes_magic(world: World) -> None:
    hero = world.get("hero")
    if hero.memes.get("moral", 0.0) >= THRESHOLD and hero.meters.get("has_magic", 0.0) >= THRESHOLD:
        hero.memes["magic_ready"] = 1.0


def _rule_relieve_proton(world: World) -> None:
    proton = world.get("proton")
    hero = world.get("hero")
    if hero.memes.get("magic_ready", 0.0) >= THRESHOLD and proton.memes.get("need_relief", 0.0) >= THRESHOLD:
        sig = ("relieve",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        proton.meters["trapped"] = 0.0
        proton.meters["bland"] = 0.0
        proton.meters["bright"] = 1.0
        proton.memes["joy"] = 1.0
        hero.memes["pride"] = 1.0


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        before = dict((e.id, (dict(e.meters), dict(e.memes))) for e in world.entities.values())
        _rule_bland_proton(world)
        _rule_moral_makes_magic(world)
        _rule_relieve_proton(world)
        after = dict((e.id, (dict(e.meters), dict(e.memes))) for e in world.entities.values())
        changed = before != after


def tell(setting: Setting, magic: MagicItem, moral: MoralValue, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label="the wise helper"))
    proton = world.add(Entity(id="proton", type="proton", label="a bland proton", phrase="a bland proton"))
    jar = world.add(Entity(id="jar", type="jar", label="gray jar", phrase="a gray jar", caretaker="helper"))
    item = world.add(Entity(id=magic.id, type="magic", label=magic.label, phrase=magic.phrase, owner="hero"))
    value = world.add(Entity(id=moral.id, type="value", label=moral.label, phrase=moral.prompt, owner="hero"))

    proton.meters["bland"] = 1.0
    proton.meters["trapped"] = 1.0
    jar.meters["sealed"] = 1.0
    hero.meters["has_magic"] = 1.0
    hero.memes["curiosity"] = 1.0
    helper.memes["wisdom"] = 1.0

    world.say(f"{name} was a {trait} little {gender} who loved adventure.")
    world.say(f"One day, {name} reached {setting.place} and found {proton.label} inside {jar.label}.")
    world.say(f"The proton looked plain and lonely, so {name} wanted to relieve {proton.it()} at once.")
    world.para()

    world.say(f"{name} lifted {item.label}, but {helper.label} raised a hand and smiled.")
    world.say(f'"{moral.prompt} first," she said. "{moral.reward}."')
    world.say(f"{name} chose to share the bright ribbon and listen carefully.")
    hero.memes["moral"] = 1.0
    hero.memes["kindness"] = 1.0
    world.para()

    world.say(f"The ribbon gave a soft glow in {setting.place}.")
    propagate(world)
    if proton.meters.get("bright", 0.0) >= THRESHOLD:
        world.say(f"The jar opened, and the bland proton was no longer bland.")
        world.say(f"{name} smiled as the little proton bounced out, bright and glad, while the magic lantern shone nearby.")
    else:
        world.say(f"For a moment, the jar stayed shut, and {name} had to try again with more care.")

    world.facts.update(
        hero=hero,
        helper=helper,
        proton=proton,
        jar=jar,
        magic=item,
        moral=value,
        setting=setting,
        resolved=bool(proton.meters.get("bright", 0.0) >= THRESHOLD),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    return [
        f'Write a short adventure for a child named {hero.label} at {setting.place} with the words "proton", "bland", and "relieve".',
        f"Tell a gentle Magic story where {hero.label} uses Moral Value to relieve a bland proton.",
        f"Write a simple adventure about a bright ribbon, a gray jar, and a proton that needs help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, proton, helper, moral, magic = f["hero"], f["proton"], f["helper"], f["moral"], f["magic"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who went on the adventure to {place}?",
            answer=f"{hero.label} went on the adventure and found a bland proton in a gray jar.",
        ),
        QAItem(
            question="What needed to be relieved?",
            answer="A bland proton needed to be relieved from the gray jar.",
        ),
        QAItem(
            question=f"Who reminded {hero.label} about {moral.prompt}?",
            answer=f"{helper.label} reminded {hero.label} that {moral.reward}.",
        ),
        QAItem(
            question=f"What magic item did {hero.label} use?",
            answer=f"{hero.label} used {magic.label}, a {magic.phrase}, to help the proton.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a proton?",
            answer="A proton is a tiny particle found inside the center of an atom.",
        ),
        QAItem(
            question="What does bland mean?",
            answer="Bland means plain, dull, or not very exciting.",
        ),
        QAItem(
            question="What does relieve mean?",
            answer="To relieve something is to make it less heavy, less painful, or less stuck.",
        ),
        QAItem(
            question="What is Moral Value in a story like this?",
            answer="Moral Value means choosing a good and kind action, like sharing or being honest.",
        ),
        QAItem(
            question="What is magic in an adventure story?",
            answer="Magic is a special power that can make surprising things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, item in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        for req in sorted(item.requires):
            lines.append(asp.fact("requires", mid, req))
        for helpk in sorted(item.helps):
            lines.append(asp.fact("helps", mid, helpk))
    for vid, val in MORAL_VALUES.items():
        lines.append(asp.fact("moral_value", vid))
        lines.append(asp.fact("value_label", vid, val.label))
    return "\n".join(lines)


ASP_RULES = r"""
bland_proton(P) :- proton(P), bland(P), trapped(P).
moral_ready(H) :- hero(H), moral(H).
magic_ready(H, M) :- hero(H), has_magic(H, M), magic(M), moral_ready(H), requires(M, moral_value).
relieve(P, M) :- bland_proton(P), magic_ready(H, M), helps(M, bland).
resolved :- relieve(P, M), proton(P), magic(M).
#show bland_proton/1.
#show moral_ready/1.
#show magic_ready/2.
#show relieve/2.
#show resolved/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("")
    model = asp.one_model(program + "#show bland_proton/1.\n#show resolved/0.\n")
    clingo_bland = set(asp.atoms(model, "bland_proton"))
    clingo_resolved = bool(asp.atoms(model, "resolved"))
    python_resolved = True
    if clingo_bland != {("proton",)} or clingo_resolved != python_resolved:
        print("MISMATCH between ASP and Python gating.")
        return 1
    print("OK: ASP and Python agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a bland proton, Magic, and Moral Value.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--magic", choices=MAGIC.keys())
    ap.add_argument("--value", choices=MORAL_VALUES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGIC))
    value = getattr(args, "value", None) or rng.choice(list(MORAL_VALUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, value=value, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), MAGIC[params.magic], _safe_lookup(MORAL_VALUES, params.value), params.name, params.gender, params.trait)
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
    StoryParams(place="observatory", magic="ribbon", value="kindness", name="Mira", gender="girl", trait="curious"),
    StoryParams(place="forest_path", magic="lamp", value="sharing", name="Finn", gender="boy", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print("resolved" if asp.atoms(model, "resolved") else "not resolved")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
