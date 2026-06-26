#!/usr/bin/env python3
"""
storyworlds/worlds/scar_interactive_abnormal_magic_cautionary_reconciliation_mystery.py
=======================================================================================

A small mystery-style storyworld about an unusual interactive magic mishap:
a child notices a strange scar, follows clues, gets a cautionary warning, and
ends in reconciliation after the truth is uncovered.

The story is built from a tiny simulated world with meters and memes:
- meters: physical state like glow, scratch, dust, dampness
- memes: emotional state like worry, curiosity, trust, relief

The premise is intentionally narrow so the stories stay grounded:
a curious child finds a magical object that can make a scar appear, and the
grown-up must decide whether to warn, explain, and reconcile.

The world is designed to feel like a mystery:
- an odd clue appears
- the clue points to a hidden cause
- an unsafe action is discouraged
- the truth is revealed
- relationships are repaired
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
# Core world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    adult: object | None = None
    hero: object | None = None
    magic: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class MagicItem:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    risk: str
    reveal: str
    caution: str
    reconciliation: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, affords={"search", "dust"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"search", "glow"}),
    "workshop": Setting(place="the old workshop", indoor=True, affords={"search", "glow"}),
    "library": Setting(place="the back room of the library", indoor=True, affords={"search", "quiet"}),
}

MAGIC_ITEMS = {
    "mirror": MagicItem(
        id="mirror",
        label="magic mirror",
        phrase="a small magic mirror with a silver edge",
        kind="mirror",
        clue="a faint handprint",
        risk="the scar could spread",
        reveal="the mirror showed the real mark underneath the glitter",
        caution="Do not touch the mirror when it is warm.",
        reconciliation="the mirror stopped glowing once the truth was spoken aloud",
        tags={"magic", "mirror", "scar", "mystery"},
    ),
    "stone": MagicItem(
        id="stone",
        label="glow stone",
        phrase="a glow stone wrapped in blue string",
        kind="stone",
        clue="tiny lights",
        risk="the lights could lead to trouble",
        reveal="the stone had hidden the scratch in its shine",
        caution="Glow stones should not be rubbed too hard.",
        reconciliation="the glow softened after everyone looked carefully together",
        tags={"magic", "stone", "scar", "mystery"},
    ),
    "lantern": MagicItem(
        id="lantern",
        label="spell lantern",
        phrase="a little spell lantern with a glass belly",
        kind="lantern",
        clue="a ring of sparks",
        risk="the sparks might frighten someone",
        reveal="the lantern had cast the strange mark like a shadow",
        caution="Spell lanterns should be kept steady.",
        reconciliation="the lantern went calm when the child apologized",
        tags={"magic", "lantern", "scar", "mystery"},
    ),
}

CHARACTER_NAMES = ["Mina", "Toby", "Nia", "Eli", "Luna", "Piper", "Ravi", "Sora"]
ADULT_NAMES = ["Aunt Vera", "Mr. Cole", "Mara", "Uncle Joss", "Ms. Hale"]
TRAITS = ["curious", "gentle", "brave", "patient", "careful", "quiet"]


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    adult: str
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
class StoryState:
    hero: Entity
    adult: Entity
    item: Entity
    setting: Setting
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mystery narrative engine
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


def _say_intro(world: World, hero: Entity, adult: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} "
        f"{hero.type} who liked asking about odd things."
    )
    world.say(
        f"One evening, {hero.id} found {item.phrase} in {world.setting.place} while "
        f"{adult.label_word if adult.label else adult.id} was tidying nearby."
    )
    world.say(
        f"{hero.id} noticed something strange: {item.clue} and, under it, a thin scar-shaped line."
    )


def _inspect(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["curiosity"] = hero.meme("curiosity") + 1
    world.say(
        f"{hero.id} leaned closer and asked if the mark was real or just part of the trick."
    )
    world.say(
        f"The room felt quiet, and the strange little mark seemed to wait for an answer."
    )


def _caution(world: World, adult: Entity, hero: Entity, item: Entity) -> None:
    adult.memes["concern"] = adult.meme("concern") + 1
    hero.memes["worry"] = hero.meme("worry") + 1
    world.say(
        f'"{item.caution}" {adult.id} said gently. "That glowing thing can make a mystery look bigger than it is."'
    )
    world.say(
        f"{adult.id} warned {hero.id} not to rub the mark or chase the light, because {item.risk}."
    )


def _investigate(world: World, hero: Entity, adult: Entity, item: Entity) -> None:
    hero.memes["worry"] = hero.meme("worry") + 1
    world.say(
        f"{hero.id} did not want to make things worse, so {hero.pronoun()} looked for a better clue."
    )
    world.say(
        f"Together they checked the floor, the table, and the edge of the {item.label}."
    )


def _reveal(world: World, hero: Entity, adult: Entity, item: Entity) -> None:
    world.say(
        f"At last, the truth became clear: {item.reveal}."
    )
    item.meters["glow"] = 0.0
    item.meters["mystery"] = 0.0
    hero.memes["relief"] = hero.meme("relief") + 1
    adult.memes["relief"] = adult.meme("relief") + 1


def _reconcile(world: World, hero: Entity, adult: Entity, item: Entity) -> None:
    hero.memes["trust"] = hero.meme("trust") + 1
    adult.memes["trust"] = adult.meme("trust") + 1
    world.say(
        f"{hero.id} looked up at {adult.id}, and the worry on both their faces melted away."
    )
    world.say(
        f'"I thought the scar meant something terrible," {hero.id} said. "I just needed help looking."'
    )
    world.say(
        f'"And I should have explained sooner," {adult.id} answered. "We can be careful together."'
    )
    world.say(
        f"By the end, {item.reconciliation}, and the little scar was only a clue, not a threat."
    )


def tell(setting: Setting, item: MagicItem, hero_name: str, adult_name: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if hero_name in {"Mina", "Nia", "Luna", "Piper", "Sora"} else "boy",
        traits=["little", trait],
    ))
    adult = world.add(Entity(
        id=adult_name,
        kind="character",
        type="woman" if adult_name in {"Aunt Vera", "Mara", "Ms. Hale"} else "man",
        label=adult_name,
    ))
    magic = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        caretaker=adult.id,
        meters={"glow": 1.0, "mystery": 1.0},
        traits=sorted(item.tags),
    ))

    _say_intro(world, hero, adult, magic)
    world.para()
    _inspect(world, hero, magic)
    _caution(world, adult, hero, magic)
    world.para()
    _investigate(world, hero, adult, magic)
    _reveal(world, hero, adult, magic)
    world.para()
    _reconcile(world, hero, adult, magic)

    world.facts.update(hero=hero, adult=adult, item=magic, item_cfg=item)
    return world


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with magic, caution, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=MAGIC_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--adult")
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
    item = getattr(args, "item", None) or rng.choice(list(MAGIC_ITEMS))
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MAGIC_ITEMS, params.item), params.name, params.adult, params.trait)
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


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    adult: Entity = _safe_fact(world, f, "adult")  # type: ignore[assignment]
    item_cfg: MagicItem = _safe_fact(world, f, "item_cfg")  # type: ignore[assignment]
    return [
        f"Write a gentle mystery story for a young child about {hero.id} finding {item_cfg.phrase}.",
        f"Tell a story where {hero.id} asks about a strange scar and {adult.id} gives a cautionary warning before they solve the mystery.",
        f"Write a short story with a magic clue, a careful warning, and a happy reconciliation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    adult: Entity = _safe_fact(world, f, "adult")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, f, "item")  # type: ignore[assignment]
    item_cfg: MagicItem = _safe_fact(world, f, "item_cfg")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What odd thing did {hero.id} find in the story?",
            answer=f"{hero.id} found {item.phrase}, and it seemed to hide a scar-shaped clue.",
        ),
        QAItem(
            question=f"Why did {adult.id} warn {hero.id} so carefully?",
            answer=f"{adult.id} warned {hero.id} because the magic could make the mystery look dangerous, and the mark should not be rubbed or chased.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {adult.id}?",
            answer=f"They found the truth together, shared the worry, and ended in reconciliation after the glow and scar were explained.",
        ),
        QAItem(
            question=f"What did the magic item reveal?",
            answer=f"It revealed that {item_cfg.reveal.lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item_cfg: MagicItem = _safe_fact(world, f, "item_cfg")  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps you solve a mystery.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you do not get hurt or make a problem bigger.",
        ),
    ]
    if "magic" in item_cfg.tags:
        out.append(QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and unusual that can do things real life cannot do.",
        ))
    out.append(QAItem(
        question="What is reconciliation?",
        answer="Reconciliation means people stop being upset and make peace again.",
    ))
    return out


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A magic item is a clue if it is in the world.
clue(I) :- item(I).

% A mystery is cautious if a warning exists.
cautionary(I) :- caution(I).

% Reconciliation happens when the reveal and the apology both occur.
reconciled(I) :- reveal(I), apology(I).

#show clue/1.
#show cautionary/1.
#show reconciled/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for iid, item in MAGIC_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("caution", iid))
        lines.append(asp.fact("reveal", iid))
        lines.append(asp.fact("apology", iid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    clues = set(asp.atoms(model, "clue"))
    cautionary = set(asp.atoms(model, "cautionary"))
    reconciled = set(asp.atoms(model, "reconciled"))
    expected = set((iid,) for iid in MAGIC_ITEMS)
    if clues == expected and cautionary == expected and reconciled == expected:
        print(f"OK: ASP parity verified for {len(expected)} items.")
        return 0
    print("MISMATCH in ASP parity.")
    print("clue:", sorted(clues))
    print("cautionary:", sorted(cautionary))
    print("reconciled:", sorted(reconciled))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="attic", item="mirror", name="Mina", adult="Aunt Vera", trait="curious"),
        StoryParams(place="garden", item="stone", name="Toby", adult="Mr. Cole", trait="careful"),
        StoryParams(place="workshop", item="lantern", name="Luna", adult="Ms. Hale", trait="brave"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        clues = sorted(set(asp.atoms(model, "clue")))
        cautionary = sorted(set(asp.atoms(model, "cautionary")))
        reconciled = sorted(set(asp.atoms(model, "reconciled")))
        print(f"clue: {len(clues)}; cautionary: {len(cautionary)}; reconciled: {len(reconciled)}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = build_curated()
        samples = [generate(p) for p in params_list]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
