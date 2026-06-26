#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cognac_sham_moral_value_rhyming_story.py
==============================================================================================================

A small storyworld for a moral-value rhyming tale about cognac and sham.
The seed suggests a short, child-facing story with a clear turn:
someone tries a fake show of class or skill, the truth spills out, and
honesty wins the day.

The world model tracks:
- physical meters: level, sparkle, wobble, warmth, spill, polish, freshness
- emotional memes: pride, worry, shame, relief, trust, delight, honesty

The prose is intentionally rhyme-forward, simple, and concrete.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    hero: object | None = None
    item: object | None = None
    def __post_init__(self):
        for k in ["level", "sparkle", "wobble", "warmth", "spill", "polish", "freshness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "worry", "shame", "relief", "trust", "delight", "honesty"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "king", "prince"}
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    value: str = ""
    rhyme_tag: str = ""
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


@dataclass
class StoryParams:
    place: str
    prop: str
    name: str
    gender: str
    role: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "parlor": Setting(place="the parlor", affords={"toast"}),
    "feast": Setting(place="the feast hall", affords={"toast"}),
    "garden": Setting(place="the garden", affords={"toast"}),
}

PROPS = {
    "cognac": Prop(
        id="cognac",
        label="cognac",
        phrase="a small glass of cognac",
        kind="drink",
        value="golden and grown-up",
        rhyme_tag="cognac",
    ),
    "sham": Prop(
        id="sham",
        label="sham",
        phrase="a shiny sham",
        kind="mask",
        value="fake and flimsy",
        rhyme_tag="sham",
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Nora", "Lia", "June", "Wren"]
BOY_NAMES = ["Pip", "Finn", "Ollie", "Jasper", "Theo", "Nate"]
TRAITS = ["bold", "bright", "spry", "wry", "kind", "curious"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def intro_line(hero: Entity, prop: Prop, role: str) -> str:
    return f"{hero.id} was a {role} with a {hero.memes.get('trust', 0) and 'warm' or 'wide'} heart and a wish for {prop.label}."


def predict_sham(world: World, hero: Entity, prop: Prop) -> dict:
    sim = world.copy()
    _act_sham(sim, sim.get(hero.id), prop, narrate=False)
    return {
        "sham_exposed": sim.get(hero.id).memes["shame"] >= THRESHOLD,
        "trust_change": sim.get(hero.id).memes["trust"],
    }


def _act_sham(world: World, hero: Entity, prop: Prop, narrate: bool = True) -> None:
    hero.meters["sparkle"] += 1
    hero.meters["wobble"] += 1
    hero.memes["pride"] += 1
    hero.memes["worry"] += 1
    world.facts["sham_started"] = True
    if narrate:
        world.say(f"{hero.id} struck a pose, all gold and glow, like a grand parade in a merry show.")


def _act_spill(world: World, hero: Entity, prop: Prop, narrate: bool = True) -> None:
    hero.meters["spill"] += 1
    hero.memes["shame"] += 1
    hero.memes["worry"] += 1
    if narrate:
        world.say(f"But the sham went slack with a tiny slip, and the fake bright plan began to drip.")


def _act_truth(world: World, hero: Entity, prop: Prop, narrate: bool = True) -> None:
    hero.memes["honesty"] += 1
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    hero.memes["shame"] = 0.0
    hero.meters["polish"] += 1
    if narrate:
        world.say(f"{hero.id} took a breath and told the truth, as gentle as rain on a windowed roof.")


def _act_kind_fix(world: World, hero: Entity, prop: Prop, narrate: bool = True) -> None:
    hero.meters["freshness"] += 1
    hero.memes["delight"] += 1
    if narrate:
        world.say(f"Then came a kind new choice, not grand or glum: a simple, honest way was come.")


def tell(setting: Setting, prop: Prop, hero_name: str, gender: str, role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=role, traits=[trait]))
    item = world.add(Entity(id=prop.id, type=prop.kind, label=prop.label, phrase=prop.phrase, owner=hero.id))
    world.facts.update(hero=hero, prop=item, setting=setting, role=role, trait=trait)

    # Act 1
    world.say(f"In {setting.place}, {hero.id} was a {trait} {role}, light on feet and keen.")
    world.say(f"{hero.id} had heard of {prop.label}, bright and sleek, and dreamed of a fine old scene.")
    world.say(f"Yet {hero.id} could see a {PROPS['sham'].label} if pride took the lead, for a fake little plan can plant a weed.")
    world.para()

    # Act 2
    hero.memes["pride"] += 1
    _act_sham(world, hero, prop)
    world.say(f"{hero.id} tried to look grand in a rustling way, but the pose felt hollow by end of day.")
    _act_spill(world, hero, prop)
    world.say(f"The crowd grew quiet; the bright façade fell, and {hero.id} knew the truth had a tale to tell.")
    world.para()

    # Act 3
    _act_truth(world, hero, prop)
    _act_kind_fix(world, hero, prop)
    world.say(f"So {hero.id} chose honesty, plain and clear, and the room felt warmer from ear to ear.")
    world.say(f"No sham, no slant, just a truthful span: that was the moral, and that was the plan.")
    return world


def knowledge_for(tag: str) -> list[tuple[str, str]]:
    return {
        "cognac": [
            ("What is cognac?", "Cognac is a grown-up drink made from wine and aged in barrels so it can taste smooth and warm."),
        ],
        "sham": [
            ("What is a sham?", "A sham is something fake that looks real for a moment but does not truly match the truth."),
        ],
        "honesty": [
            ("What is honesty?", "Honesty means telling the truth and not pretending to be something you are not."),
        ],
        "truth": [
            ("Why is telling the truth a good thing?", "Telling the truth helps people trust each other and fix mistakes sooner."),
        ],
    }.get(tag, [])


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prop: Entity = _safe_fact(world, f, "prop")
    trait = _safe_fact(world, f, "trait")
    role = _safe_fact(world, f, "role")
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {hero.id}, a {trait} {role} who wanted {prop.label} but learned a better way.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} tried the sham?",
            answer=f"The sham turned flimsy and the pretend plan slipped, so the fake show lost its shine.",
        ),
        QAItem(
            question=f"What did {hero.id} choose at the end?",
            answer=f"{hero.id} chose honesty instead of pretending, and that made the room feel warmer and truer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"cognac", "sham", "honesty", "truth"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in knowledge_for(tag))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prop: Entity = _safe_fact(world, f, "prop")
    return [
        f"Write a short rhyming story for a child about {hero.id}, a {f['trait']} {f['role']}, who sees {prop.label} and faces a sham.",
        f"Tell a gentle moral-value story where {hero.id} learns that a sham is flimsy and honesty is strong.",
        f"Make a simple rhyming tale with the words cognac and sham, ending in a truthful choice.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


def story_knowledge_tags() -> list[str]:
    return ["cognac", "sham", "honesty", "truth"]


CURATED = [
    StoryParams(place="parlor", prop="cognac", name="Mina", gender="girl", role="waiter", trait="bold"),
    StoryParams(place="feast", prop="cognac", name="Pip", gender="boy", role="helper", trait="curious"),
    StoryParams(place="garden", prop="cognac", name="Nora", gender="girl", role="host", trait="kind"),
]


ASP_RULES = r"""
% A sham is when sparkle and wobble rise together.
sham(H) :- sparkle(H), wobble(H).

% Truth is the turn that clears shame and builds trust.
truth_turn(H) :- honesty(H), not sham(H).

% A good moral story ends with truth, relief, and no shame.
good_story(H) :- truth_turn(H), relief(H), not shame(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("value", pid, p.value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    if not model:
        print("ASP check failed: no model.")
        return 1
    print("OK: ASP program grounded successfully.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming moral-value storyworld about cognac and sham.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role")
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prop", None) and getattr(args, "prop", None) not in PROPS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "role", None):
        if getattr(args, "gender", None) == "girl" and getattr(args, "role", None) == "king":
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if getattr(args, "gender", None) == "boy" and getattr(args, "role", None) == "queen":
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    role = getattr(args, "role", None) or rng.choice(["helper", "host", "waiter", "child"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, prop=prop, name=name, gender=gender, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROPS, params.prop), params.name, params.gender, params.role, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show setting/1."))
        print(f"ASP model atoms: {len(model)}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.prop} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
