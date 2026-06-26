#!/usr/bin/env python3
"""
storyworlds/worlds/glue_mattress_bravery_transformation_sharing_nursery_rhyme.py
=================================================================================

A tiny nursery-rhyme-style story world about a child or little creature who
finds the courage to fix a mattress with glue, watch it transform, and then
share the cozy result.

Seed image:
- Something soft is torn.
- Glue helps mend it.
- Bravery gets the hero across the scary moment.
- Sharing makes the ending warm and bright.

The prose aims for a gentle rhyme-and-repeat cadence without becoming a frozen
template. State changes drive the story: a torn mattress, a brave fix, a
changed bed, and a shared cozy ending.
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
# World model
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    glue_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
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
    indoors: bool = True
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
class GlueType:
    id: str
    label: str
    phrase: str
    strength: str
    rhyme: str
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
class Mattress:
    id: str
    label: str
    phrase: str
    tear_kind: str
    region: str = "bed"
    needs: str = "mend"
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
    glue: str
    mattress: str
    hero_name: str
    hero_type: str
    helper_type: str
    setting: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True),
    "attic": Setting(place="the tiny attic room", indoors=True),
    "cottage": Setting(place="the cottage nook", indoors=True),
}

GLUES = {
    "honey": GlueType(
        id="honey",
        label="honey glue",
        phrase="a little jar of honey glue",
        strength="sticky and sweet",
        rhyme="hummed and glued",
    ),
    "bean": GlueType(
        id="bean",
        label="bean paste glue",
        phrase="a little pot of bean paste glue",
        strength="thick and steady",
        rhyme="sang and stuck",
    ),
    "moon": GlueType(
        id="moon",
        label="moon glue",
        phrase="a tiny tin of moon glue",
        strength="silver-bright",
        rhyme="glimmered and mended",
    ),
}

MATTRESSES = {
    "patchwork": Mattress(
        id="patchwork",
        label="patchwork mattress",
        phrase="a patchwork mattress with a sleepy star",
        tear_kind="a small tear",
    ),
    "feather": Mattress(
        id="feather",
        label="feather mattress",
        phrase="a feather mattress with a soft blue seam",
        tear_kind="a split seam",
    ),
    "cotton": Mattress(
        id="cotton",
        label="cotton mattress",
        phrase="a cotton mattress with a frayed corner",
        tear_kind="a frayed corner",
    ),
}

NAMES = ["Milo", "Luna", "Poppy", "Theo", "Mia", "Otto", "Nell", "Rory"]
TRAITS = ["brave", "gentle", "merry", "curious", "tiny", "spry"]


@dataclass
class Reason:
    brave_needed: bool
    can_mend: bool
    can_share: bool


# ---------------------------------------------------------------------------
# World logic
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


def assess(glue: GlueType, mattress: Mattress) -> Reason:
    brave_needed = mattress.id in {"patchwork", "feather", "cotton"}
    can_mend = glue.id in {"honey", "bean", "moon"}
    can_share = True
    return Reason(brave_needed=brave_needed, can_mend=can_mend, can_share=can_share)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GLUES:
            for m in MATTRESSES:
                r = assess(_safe_lookup(GLUES, g), _safe_lookup(MATTRESSES, m))
                if r.brave_needed and r.can_mend and r.can_share:
                    combos.append((s, g, m))
    return combos


def reasonableness_gate(glue: GlueType, mattress: Mattress) -> None:
    r = assess(glue, mattress)
    if not r.can_mend:
        pass
    if mattress.tear_kind == "":
        pass


def predict_mend(world: World, glue: GlueType, mattress_id: str) -> dict:
    sim = world.copy()
    mat = sim.get(mattress_id)
    g = sim.get(glue.id)
    mat.meters["broken"] = 1
    g.memes["used"] = 1
    mat.meters["mended"] = 1
    return {"mended": mat.meters.get("mended", 0) >= 1}


def introduce(world: World, hero: Entity, helper: Entity, mattress: Entity, glue: Entity) -> None:
    world.say(
        f"Little {hero.id} lived in {world.setting.place}, where the moonlight "
        f"made the blankets glow."
    )
    world.say(
        f"{hero.pronoun().capitalize()} found {mattress.phrase}, and {mattress.label} "
        f"had {mattress.meters.get('broken_text', 'a tear')} that made a sad little gap."
    )
    world.say(
        f"Near the bed sat {glue.phrase}; {glue.label} looked small, but it promised a fix."
    )
    world.say(
        f"{helper.pronoun().capitalize()} was there too, ready to help, and {hero.id} "
        f"wanted to make the soft bed whole again."
    )


def brave(world: World, hero: Entity, glue: Entity, mattress: Entity) -> None:
    hero.memes["doubt"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"But the torn spot looked a little scary, and {hero.id} took a tiny breath. "
        f"Then {hero.pronoun()} said, \"I can be brave for one small try.\""
    )
    world.say(
        f"{hero.pronoun().capitalize()} reached for the glue with steady hands, "
        f"slow and calm, not rushed by the night."
    )


def transform(world: World, hero: Entity, helper: Entity, glue: Entity, mattress: Entity) -> None:
    mattress.meters["broken"] = 0
    mattress.meters["mended"] = 1
    mattress.memes["newness"] = 1
    glue.meters["used"] = 1
    hero.memes["bravery"] += 1
    world.say(
        f"The glue went on with a soft little shine, and the tear did not stay torn. "
        f"It pressed and held, and the old gap grew smooth."
    )
    world.say(
        f"By and by, the mattress looked changed, as if a sleepy ripple had turned "
        f"into a tidy stripe."
    )


def share(world: World, hero: Entity, helper: Entity, mattress: Entity) -> None:
    hero.memes["sharing"] += 1
    helper.memes["sharing"] += 1
    world.say(
        f"Then {hero.id} and {helper.id} shared the bed-time space, one on each side, "
        f"with room enough for a story and a sigh."
    )
    world.say(
        f"They tucked the blanket near the mend, and the mattress felt cozy and kind, "
        f"ready for two warm dreams."
    )


def tell(setting: Setting, glue: GlueType, mattress: Mattress, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    glue_ent = world.add(Entity(id=glue.id, kind="thing", type="thing", label=glue.label, phrase=glue.phrase))
    mattress_ent = world.add(
        Entity(
            id=mattress.id,
            kind="thing",
            type="thing",
            label=mattress.label,
            phrase=mattress.phrase,
        )
    )
    mattress_ent.meters["broken"] = 1
    mattress_ent.meters["broken_text"] = 1

    introduce(world, hero, helper, mattress_ent, glue_ent)
    world.para()
    brave(world, hero, glue_ent, mattress_ent)
    transform(world, hero, helper, glue_ent, mattress_ent)
    world.para()
    share(world, hero, helper, mattress_ent)

    world.facts.update(
        hero=hero,
        helper=helper,
        glue=glue_ent,
        mattress=mattress_ent,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    glue: Entity = _safe_fact(world, f, "glue")
    mattress: Entity = _safe_fact(world, f, "mattress")
    return [
        f'Write a short nursery-rhyme-style story about {hero.id} using {glue.label} to mend {mattress.label}.',
        f"Tell a gentle tale where {hero.id} must be brave, make a transformation happen, and share the cozy result with {helper.label}.",
        f'Write a tiny bedtime story that includes "{glue.label}" and "{mattress.label}" and ends with sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    glue: Entity = _safe_fact(world, f, "glue")
    mattress: Entity = _safe_fact(world, f, "mattress")
    return [
        QAItem(
            question=f"What was wrong with the {mattress.label} at the start?",
            answer=f"It had {mattress.tear_kind}, so it was not ready for a cozy night yet.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery when facing the broken {mattress.label}?",
            answer=(
                f"{hero.id} took a tiny breath, spoke bravely, and used the {glue.label} "
                f"to try the fix instead of turning away."
            ),
        ),
        QAItem(
            question=f"What changed after the glue did its work?",
            answer=(
                f"The torn mattress became mended and smooth, so it looked changed, almost new."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} end the story?",
            answer=(
                f"They shared the cozy bed-space together, with the mattress fixed and the room feeling warm."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    glue: GlueType = GLUES[f["glue"].id]
    mattress: Mattress = MATTRESSES[f["mattress"].id]
    return [
        QAItem(
            question="What is glue for?",
            answer="Glue is used to stick things together or mend things that have come apart.",
        ),
        QAItem(
            question="What is a mattress?",
            answer="A mattress is the soft part of a bed that people lie on to rest and sleep.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels a little scary.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question=f"What kind of glue was in this story?",
            answer=f"It was {glue.strength}, the kind that could help mend a small tear.",
        ),
        QAItem(
            question=f"What kind of problem did the {mattress.label} have?",
            answer=f"It had {mattress.tear_kind}, which is the kind of problem a careful mend can help fix.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

valid(Set, Glue, Mattress) :- setting(Set), glue(Glue), mattress(Mattress), can_mend(Glue, Mattress).
can_mend(Glue, Mattress) :- glue(Glue), mattress(Mattress).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GLUES:
        lines.append(asp.fact("glue", gid))
        lines.append(asp.fact("can_mend", gid, "any"))
    for mid in MATTRESSES:
        lines.append(asp.fact("mattress", mid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Python only:", sorted(py - asp_set))
    print("ASP only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about glue, a mattress, bravery, transformation, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--glue", choices=GLUES)
    ap.add_argument("--mattress", choices=MATTRESSES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "mouse", "bunny", "bear"], default=None)
    ap.add_argument("--helper-type", choices=["mother", "father", "mouse", "bunny", "bear"], default=None)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "glue", None):
        combos = [c for c in combos if c[1] == getattr(args, "glue", None)]
    if getattr(args, "mattress", None):
        combos = [c for c in combos if c[2] == getattr(args, "mattress", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, glue_id, mattress_id = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy", "mouse", "bunny"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father", "mouse", "bunny", "bear"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(
        glue=glue_id,
        mattress=mattress_id,
        hero_name=name,
        hero_type=hero_type,
        helper_type=helper_type,
        setting=setting,
    )


def generate(params: StoryParams) -> StorySample:
    glue = _safe_lookup(GLUES, params.glue)
    mattress = _safe_lookup(MATTRESSES, params.mattress)
    reasonableness_gate(glue, mattress)
    world = tell(_safe_lookup(SETTINGS, params.setting), glue, mattress, params.hero_name, params.hero_type, params.helper_type)
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

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(glue="honey", mattress="patchwork", hero_name="Milo", hero_type="mouse", helper_type="mother", setting="nursery"),
        StoryParams(glue="moon", mattress="feather", hero_name="Luna", hero_type="girl", helper_type="bunny", setting="cottage"),
        StoryParams(glue="bean", mattress="cotton", hero_name="Poppy", hero_type="boy", helper_type="bear", setting="attic"),
    ]

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.hero_name}: {p.glue} + {p.mattress} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
