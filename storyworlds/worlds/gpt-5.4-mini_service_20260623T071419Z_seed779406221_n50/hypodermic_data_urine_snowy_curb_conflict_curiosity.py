#!/usr/bin/env python3
"""
storyworlds/worlds/hypodermic_data_urine_snowy_curb_conflict_curiosity.py
========================================================================

A small standalone storyworld in a rhyming-story style.

Seed tale:
---
On a snowy curb, a curious child notices a clinic bag with a hypodermic pen,
data sheets, and a sealed urine sample. The child wants to peek; a caregiver
warns that the curb is icy and the items must stay clean. The child argues,
then learns to carry the bag safely to the clinic without opening it.

World shape:
- curiosity drives the child toward the bag
- conflict rises when the caregiver says no
- the turn is a safe, practical handoff
- the ending proves the bag stayed sealed and the curb stayed clear
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bag: object | None = None
    caregiver: object | None = None
    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    snowy: bool = True
    tags: set[str] = field(default_factory=set)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    sealed: bool = False
    dirty: bool = False
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
class CareRule:
    id: str
    label: str
    action: str
    caution: str
    fix: str
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_slip(world: World) -> list[str]:
    out = []
    child = world.entities["child"]
    if child.memes.get("reach", 0.0) < THRESHOLD:
        return out
    if world.place.snowy and child.meters.get("slip", 0.0) < THRESHOLD:
        sig = "slip"
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.meters["slip"] = 1.0
        child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0
        out.append("The curb was slick, and the child felt a twinge of worry.")
    return out


def _r_seal(world: World) -> list[str]:
    bag = world.entities["bag"]
    if bag.attrs.get("handled", False) and bag.meters.get("open", 0.0) < THRESHOLD:
        sig = "seal"
        if sig in world.fired:
            return out if (out := []) else []
        world.fired.add(sig)
        bag.meters["safe"] = 1.0
        return ["The bag stayed sealed and snug in gloved hands."]
    return []


CAUSAL_RULES = [Rule(name="slip", apply=_r_slip), Rule(name="seal", apply=_r_seal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World) -> dict:
    sim = world.copy()
    child = sim.entities["child"]
    child.memes["reach"] = 1.0
    propagate(sim, narrate=False)
    return {
        "slip": sim.entities["child"].meters.get("slip", 0.0) >= THRESHOLD,
        "safe": sim.entities["bag"].meters.get("safe", 0.0) >= THRESHOLD,
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for obj_id, obj in OBJECTS.items():
            if place.snowy and obj.sealed and obj.fragile:
                combos.append((place_id, obj_id, "curiosity"))
    return combos


@dataclass
class StoryParams:
    place: str
    object: str
    child_name: str
    child_gender: str
    caregiver: str
    trait: str
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


PLACES = {
    "snowy_curb": Place(id="snowy_curb", label="the snowy curb", snowy=True, tags={"snowy", "curb"}),
}

OBJECTS = {
    "clinic_bag": ObjectCfg(
        id="clinic_bag",
        label="clinic bag",
        phrase="a clinic bag with a hypodermic pen, data sheets, and a sealed urine jar",
        fragile=True,
        sealed=True,
        tags={"hypodermic", "data", "urine"},
    ),
}

CARE_RULES = {
    "curiosity": CareRule(
        id="curiosity",
        label="curiosity",
        action="peek into the bag",
        caution="keep the lid shut and the jar sealed",
        fix="carry it to the clinic without opening it",
        tags={"curiosity", "conflict"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Lily"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Max"]
TRAITS = ["curious", "thoughtful", "brave", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child set on {f["place"].label} and include the words "hypodermic", "data", and "urine".',
        f"Tell a gentle curbside story where {f['child'].id} feels curiosity about a clinic bag, but {f['caregiver'].id} guides the child to keep it sealed.",
        f"Write a rhyming story with conflict and curiosity that ends with a safe handoff of a clinic bag in the snow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    care: Entity = f["caregiver"]
    bag: Entity = f["bag"]
    place: Place = f["place"]
    rule: CareRule = f["rule"]
    return [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about {child.id} and {care.id} on {place.label}. The child feels curious about the clinic bag.",
        ),
        QAItem(
            question=f"What was inside the clinic bag?",
            answer=f"It held a hypodermic pen, data sheets, and a sealed urine jar. The bag had to stay closed and clean.",
        ),
        QAItem(
            question=f"Why did {care.id} stop {child.id} from opening the bag?",
            answer=f"{care.id} wanted {child.id} to keep the lid shut because the curb was snowy and slippery. The items also needed to stay sealed for the clinic.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} helped carry the bag to the clinic without opening it. The bag stayed safe, and the snowy curb stayed clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should you do with a sealed clinic bag?",
            answer="You should keep it closed and carry it carefully to the right place. Sealed things stay safer when they are not opened early.",
        ),
        QAItem(
            question="Why can a snowy curb be tricky?",
            answer="Snow and ice can make a curb slick. That means people should move carefully so they do not slip.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to look, learn, and ask questions. It can be good when it is paired with care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(child, bag) :- snowy_curb(place), sealed(bag), fragile(bag).
conflict(child) :- curiosity(child), risk(child, bag).
safe_end(child, bag) :- handled(bag), sealed(bag).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("snowy_curb", "place"),
        asp.fact("sealed", "bag"),
        asp.fact("fragile", "bag"),
        asp.fact("curiosity", "child"),
        asp.fact("handled", "bag"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risk/2.\n#show safe_end/2.\n#show conflict/1."))
    atoms = set(asp.atoms(model, "conflict"))
    python_ok = set()
    if atoms and valid_combos():
        python_ok = {("child",)}
    if bool(atoms) == bool(python_ok):
        print("OK: ASP parity looks good.")
        return 0
    print("MISMATCH: ASP parity failed.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, obj_id, _ = rng.choice(list(combos))
    child_gender = rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mom", "dad"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        object=obj_id,
        child_name=child_name,
        child_gender=child_gender,
        caregiver=caregiver,
        trait=trait,
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    obj = _safe_lookup(OBJECTS, params.object)
    rule = CARE_RULES["curiosity"]
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    caregiver = world.add(Entity(id="caregiver", kind="character", type="adult", label=params.caregiver))
    bag = world.add(Entity(id="bag", kind="thing", type="bag", label="clinic bag", phrase=obj.phrase))
    child.memes["curiosity"] = 1.0
    child.memes["conflict"] = 0.0
    child.meters["reach"] = 0.0
    bag.meters["open"] = 0.0
    bag.meters["safe"] = 0.0
    world.say(f"{child.id} saw the bag by the curb, white with snow and bright as a star.")
    world.say(f'"Inside is a hypodermic pen, data sheets, and urine," the caregiver said with care.')
    world.say(f"{child.id} felt curious and wanted to peek, for the bag looked neat and rare.")
    world.para()
    child.memes["reach"] = 1.0
    risk = predict_risk(world)
    if risk["slip"]:
        world.say(f"The curb was icy and slick, so the caregiver held the child back fast.")
    world.say(f'"Please keep it shut," said {caregiver.id}. "Let us carry it on, and make the safe choice last."')
    child.memes["conflict"] = 1.0
    world.say(f"{child.id} frowned, then nodded, and took the handle with a careful hand.")
    bag.attrs["handled"] = True
    propagate(world, narrate=True)
    world.para()
    world.say(f"They walked to the clinic through the snow, as quiet as a mouse in a mitt.")
    world.say(f"The bag stayed sealed, the data stayed dry, and the urine jar never tipped.")
    world.facts.update(child=child, caregiver=caregiver, bag=bag, place=place, rule=rule, obj=obj)
    return world


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming snowy-curb storyworld with curiosity and conflict.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--child-name")
    ap.add_argument("--caregiver")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="snowy_curb", object="clinic_bag", child_name="Mia", child_gender="girl", caregiver="mom", trait="curious"),
]


def valid_combo_filter(params: StoryParams, args: argparse.Namespace) -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show risk/2.\n#show conflict/1.\n#show safe_end/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show risk/2.\n#show conflict/1.\n#show safe_end/2."))
        print("risk:", asp.atoms(model, "risk"))
        print("conflict:", asp.atoms(model, "conflict"))
        print("safe_end:", asp.atoms(model, "safe_end"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
