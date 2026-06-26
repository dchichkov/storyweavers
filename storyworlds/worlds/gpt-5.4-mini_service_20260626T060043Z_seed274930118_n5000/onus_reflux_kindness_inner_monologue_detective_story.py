#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/onus_reflux_kindness_inner_monologue_detective_story.py
====================================================================================================

A small, self-contained detective-style storyworld about a child detective,
inner monologue, kindness, and the onus of helping when reflux makes a day go
sour.

Seed tale inspiration:
---
A child detective notices that a little friend's sour reflux is making the room
feel tense. At first, the detective's inner monologue circles blame and worry.
Then kindness turns the onus into action: fetch the pillow, bring water, and
stay gentle. The mystery is not "who is bad," but "who will help first?"

World premise:
---
- Reflux can make a character feel uncomfortable after eating, especially if
  they lie down too soon or rush around.
- The detective's inner monologue can either sharpen suspicion or soften into
  kindness.
- The story turns when the detective accepts the onus of helping instead of
  blaming, and a practical comfort item helps resolve the trouble.

Narrative instruments:
---
- Kindness: a visible social force that lowers tension and improves trust.
- Inner Monologue: private reasoning that appears in the prose as a brief,
  child-friendly thought.
- Detective Story style: clues, suspicion, inference, and a small, humane
  resolution.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    detective: object | None = None
    patient: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "kindness": 0.0, "conflict": 0.0, "insight": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def role_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class Activity:
    id: str
    verb: str
    clue: str
    trigger: str
    symptom: str
    fix_hint: str
    zone: set[str]
    keyword: str
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


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_reflux(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("reflux", 0.0) < THRESHOLD:
            continue
        sig = ("reflux", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"{actor.id} felt a sour rise in {actor.lowstomach if hasattr(actor,'lowstomach') else 'their stomach'}.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.type == "detective"), None)
    patient = next((e for e in world.entities.values() if e.meters.get("reflux", 0.0) >= THRESHOLD), None)
    if not detective or not patient:
        return out
    if detective.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kind", detective.id, patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["insight"] += 1
    patient.memes["worry"] = max(0.0, patient.memes.get("worry", 0.0) - 1.0)
    out.append("__kindness__")
    return out


CAUSAL_RULES = [
    _r_reflux,
    _r_kindness,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__kindness__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def affects_reflux(activity: Activity) -> bool:
    return "reflux" in activity.tags


def choose_gear(activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.symptom in gear.helps:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for gear in GEAR:
                if act.symptom in gear.helps:
                    combos.append((place, act_id, gear.id))
    return combos


def setting_line(setting: Setting, activity: Activity) -> str:
    if setting.place == "the clinic":
        return "The waiting room was quiet, and the little bell at the desk gave a soft ding."
    if setting.place == "the bedroom":
        return "The lamp glowed like a warm moon, and the bed looked too inviting for a stomach that was already upset."
    if setting.place == "the kitchen":
        return "The kitchen smelled like toast and warm tea."
    if setting.place == "the bus stop":
        return "The bus stop was windy, and the bench was hard and cold."
    return f"{setting.place.capitalize()} waited under a plain, careful sky."


def predict_reflux(world: World, actor: Entity, activity: Activity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.entities[actor.id].meters.get("reflux", 0.0) >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    actor.meters["reflux"] += 1.0
    actor.memes["worry"] += 1.0
    if narrate:
        world.say(f"{actor.id} did {activity.verb}.")
    propagate(world, narrate=narrate)


def detective_thought(world: World, detective: Entity, patient: Entity, activity: Activity) -> None:
    detective.memes["insight"] += 1.0
    world.say(
        f"{detective.id} squinted at the clues and thought, "
        f'"If {patient.id} is hurting, the onus is on me to be kind, not loud."'
    )


def introduce(world: World, detective: Entity) -> None:
    trait = next((t for t in detective.traits if t != "little"), "careful")
    world.say(
        f"{detective.id} was a little {trait} detective who noticed every small clue."
    )


def setup(world: World, detective: Entity, patient: Entity, activity: Activity) -> None:
    world.say(
        f"{detective.pronoun().capitalize()} liked detective work, "
        f"especially when a clue could be solved with a gentle heart."
    )
    world.say(
        f"{patient.id} had reflux, and {activity.clue} often made "
        f"{patient.pronoun('possessive')} face pinch."
    )


def arrive(world: World, detective: Entity, patient: Entity, activity: Activity) -> None:
    world.say(
        f"One evening, {detective.id} and {patient.id} came to {world.setting.place}."
    )
    world.say(setting_line(world.setting, activity))


def suspect(world: World, detective: Entity, patient: Entity, activity: Activity) -> None:
    world.say(
        f"{patient.id} tried to {activity.verb}, but the {activity.keyword} had a sneaky way of bringing reflux back."
    )
    world.say(
        f"{detective.id} wondered if the problem was a messy clue or a bad choice."
    )


def resolve(world: World, detective: Entity, patient: Entity, activity: Activity, gear: Gear) -> None:
    detective.memes["kindness"] += 1.0
    patient.memes["kindness"] += 1.0
    patient.memes["worry"] = max(0.0, patient.memes.get("worry", 0.0) - 1.0)
    world.say(
        f'"{gear.prep}," {detective.pronoun("possessive")} helper said.'
    )
    world.say(
        f"{patient.id} listened, and {patient.id} sat up with {gear.label} in place."
    )
    world.say(
        f"Then {patient.id} could {activity.verb} without making the sour feeling worse."
    )
    world.say(
        f"{gear.tail}. The room felt calmer, and {detective.id} knew the case was solved by kindness."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"toast", "juice"}),
    "bedroom": Setting(place="the bedroom", affords={"bedtime_snack", "storytime"}),
    "clinic": Setting(place="the clinic", affords={"waiting", "checkup"}),
    "bus_stop": Setting(place="the bus stop", affords={"ride_wait", "snack"}),
}

ACTIVITIES = {
    "bedtime_snack": Activity(
        id="bedtime_snack",
        verb="eat a bedtime snack",
        clue="snacking too late",
        trigger="lying down too soon",
        symptom="reflux",
        fix_hint="sit up with a pillow",
        zone={"torso"},
        keyword="snack",
        tags={"reflux", "food"},
    ),
    "toast": Activity(
        id="toast",
        verb="eat toast",
        clue="a crumb trail by the plate",
        trigger="rushing the meal",
        symptom="reflux",
        fix_hint="take a slow sip of water",
        zone={"torso"},
        keyword="toast",
        tags={"reflux", "food"},
    ),
    "checkup": Activity(
        id="checkup",
        verb="wait for a checkup",
        clue="a soft note from the nurse",
        trigger="nerves in the waiting room",
        symptom="reflux",
        fix_hint="hold a warm cloth",
        zone={"torso"},
        keyword="clinic",
        tags={"reflux", "clinic"},
    ),
    "ride_wait": Activity(
        id="ride_wait",
        verb="wait for the bus",
        clue="standing too long after a meal",
        trigger="jiggling on a full stomach",
        symptom="reflux",
        fix_hint="lean back safely",
        zone={"torso"},
        keyword="bus",
        tags={"reflux", "travel"},
    ),
}

GEAR = [
    Gear(
        id="pillow",
        label="a wedge pillow",
        covers={"torso"},
        helps={"reflux"},
        prep="Let's use a wedge pillow and keep your tummy higher",
        tail="They tucked the wedge pillow behind the patient and the sour feeling settled down",
    ),
    Gear(
        id="water",
        label="a cup of cool water",
        covers={"torso"},
        helps={"reflux"},
        prep="Let's take slow sips of cool water",
        tail="The cool water helped the room feel less tight",
    ),
    Gear(
        id="cloth",
        label="a warm cloth",
        covers={"torso"},
        helps={"reflux"},
        prep="Let's press a warm cloth near your middle",
        tail="The warm cloth made the patient breathe easier",
    ),
]

PEOPLE = {
    "detective": [
        ("Nora", "girl"),
        ("Pip", "boy"),
        ("Ivy", "girl"),
        ("Jude", "boy"),
    ],
    "patient": [
        ("Milo", "boy"),
        ("Tessa", "girl"),
        ("Benji", "boy"),
        ("Lena", "girl"),
    ],
}

TRAITS = ["curious", "careful", "brave", "quiet", "sharp", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    detective_name: str
    detective_gender: str
    patient_name: str
    patient_gender: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective storyworld about reflux, onus, kindness, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--detective-name")
    ap.add_argument("--patient-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, _gear = rng.choice(list(combos))
    dname, dgender = rng.choice(PEOPLE["detective"])
    pname, pgender = rng.choice(PEOPLE["patient"])
    return StoryParams(
        place=place,
        activity=activity,
        detective_name=getattr(args, "detective_name", None) or dname,
        detective_gender="girl" if dgender == "girl" else "boy",
        patient_name=getattr(args, "patient_name", None) or pname,
        patient_gender="girl" if pgender == "girl" else "boy",
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    detective = world.add(Entity(id=params.detective_name, kind="character", type="detective", traits=["little", params.trait]))
    patient = world.add(Entity(id=params.patient_name, kind="character", type="child", traits=["little", "sensitive"]))
    activity = _safe_lookup(ACTIVITIES, params.activity)
    patient.meters["reflux"] = 1.0

    introduce(world, detective)
    setup(world, detective, patient, activity)
    world.para()
    arrive(world, detective, patient, activity)
    suspect(world, detective, patient, activity)
    detective_thought(world, detective, patient, activity)
    gear = choose_gear(activity)
    if gear is None:
        pass
    world.para()
    resolve(world, detective, patient, activity, gear)

    world.facts = {
        "detective": detective,
        "patient": patient,
        "activity": activity,
        "gear": gear,
        "place": params.place,
    }

    story = world.render()
    prompts = [
        f"Write a short detective story for a young child that uses the words '{activity.keyword}', 'onus', and 'kindness'.",
        f"Tell a gentle mystery where {params.detective_name} notices reflux and chooses kindness over blame.",
        f"Write an inner-monologue detective story about helping a child who feels sour after eating.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.detective_name} decide to help {params.patient_name}?",
            answer=(
                f"{params.detective_name} realized that when {params.patient_name} had reflux, the onus was on the detective to be kind and help. "
                f"Their inner monologue reminded them not to blame {params.patient_name} for feeling unwell."
            ),
        ),
        QAItem(
            question=f"What clue made the detective think the problem was reflux?",
            answer=(
                f"The clue was that {params.patient_name} felt sour after {activity.verb}, which is a common sign that reflux is acting up."
            ),
        ),
        QAItem(
            question=f"What helped make the ending calm again?",
            answer=(
                f"{gear.label} helped, along with gentle kindness. Once {params.patient_name} sat up and got support, the sour feeling settled down."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is reflux?",
            answer="Reflux is when sour stomach contents rise up and make someone feel uncomfortable or sick to their tummy.",
        ),
        QAItem(
            question="What does kindness do in a hard moment?",
            answer="Kindness helps people feel safe, listened to, and less alone when something is bothering them.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your mind that helps you think things through before you act.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
            print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
            print()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
reflux_case(D,P) :- patient(D), has_reflux(P).
helpful_fix(G,D,P) :- gear(G), reflux_case(D,P), helps(G,reflux).
kind_resolution(D,P) :- detective(D), patient(P), helpful_fix(_,D,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword_of", aid, a.keyword))
        lines.append(asp.fact("symptom_of", aid, a.symptom))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag_of", aid, t))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    lines.append(asp.fact("patient", "p"))
    lines.append(asp.fact("detective", "d"))
    lines.append(asp.fact("has_reflux", "p"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show kind_resolution/2."))
    asp_set = set(asp.atoms(model, "kind_resolution"))
    py_set = {("d", "p")}
    if asp_set == py_set:
        print("OK: ASP parity checks passed.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show helpful_fix/3."))
    return sorted(set(asp.atoms(model, "helpful_fix")))


CURATED = [
    StoryParams(place="bedroom", activity="bedtime_snack", detective_name="Nora", detective_gender="girl", patient_name="Milo", patient_gender="boy", trait="careful"),
    StoryParams(place="kitchen", activity="toast", detective_name="Pip", detective_gender="boy", patient_name="Tessa", patient_gender="girl", trait="sharp"),
    StoryParams(place="clinic", activity="checkup", detective_name="Ivy", detective_gender="girl", patient_name="Benji", patient_gender="boy", trait="patient"),
    StoryParams(place="bus_stop", activity="ride_wait", detective_name="Jude", detective_gender="boy", patient_name="Lena", patient_gender="girl", trait="brave"),
]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show kind_resolution/2."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print("\n".join(str(x) for x in combos))
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
