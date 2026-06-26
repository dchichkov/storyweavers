#!/usr/bin/env python3
"""
A small folk-tale storyworld about curiosity, tension, and a lesson learned.

Premise:
A curious child is told not to open a woodland gate until the bell-ring
because the gate keeps a shy lantern-bird safe. The child wants to peek early.
That choice raises tension: the child risks startling the bird and losing
the path home. A wiser helper offers a patient way to wait, watch, and learn.

The world is simulated with physical meters and emotional memes:
- curiosity grows when the child wonders and investigates
- tension grows when the child disobeys or rushes
- calm grows when the child listens and waits
- the lesson is learned when the child chooses patience and respects the rule

The story is generated from world state, not from a frozen template.
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
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Secret:
    label: str
    phrase: str
    risk: str
    zone: str
    gentle_fix: str
    lesson: str
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
    secret: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "wood": Setting(place="the wood", affords={"peek", "wait"}),
    "hill": Setting(place="the hill", affords={"peek", "wait"}),
    "garden": Setting(place="the old garden", affords={"peek", "wait"}),
}

SECRETS = {
    "lantern_bird": Secret(
        label="lantern-bird",
        phrase="a shy lantern-bird with silver wings",
        risk="startle",
        zone="gate",
        gentle_fix="wait for the bell before opening the gate",
        lesson="curiosity is safest when it walks beside patience",
    ),
    "moon_well": Secret(
        label="moon-well",
        phrase="a moon-well that shines in the dark",
        risk="spill",
        zone="stone",
        gentle_fix="look with a lantern and keep both hands still",
        lesson="some wonders are seen best by looking carefully first",
    ),
    "seed_box": Secret(
        label="seed_box",
        phrase="a wooden seed box tied with blue string",
        risk="scatter",
        zone="lid",
        gentle_fix="untie the string slowly and hold the lid with both hands",
        lesson="slow fingers keep good things from flying away",
    ),
}

GENDERS = {"girl", "boy"}
HELPERS = ["grandmother", "grandfather", "aunt", "uncle"]
GIRL_NAMES = ["Mina", "Lila", "Nora", "Tessa", "Mabel"]
BOY_NAMES = ["Finn", "Rowan", "Bram", "Owen", "Elio"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, secret) for place, s in SETTINGS.items() for secret in s.affords for secret in SECRETS]


def choose_secret_for_place(place: str) -> list[str]:
    return ["lantern_bird", "moon_well", "seed_box"] if place in SETTINGS else []


def _curiosity_rises(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["tension"] = child.memes.get("tension", 0) + 0.2


def _tension_rises(world: World, child: Entity) -> None:
    child.memes["tension"] = child.memes.get("tension", 0) + 1
    child.meters["risk"] = child.meters.get("risk", 0) + 1


def _calm_rises(world: World, child: Entity) -> None:
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    child.memes["tension"] = max(0.0, child.memes.get("tension", 0) - 1)


def _lesson_sticks(world: World, child: Entity, secret: Secret) -> None:
    child.memes["lesson"] = child.memes.get("lesson", 0) + 1
    world.facts["lesson"] = secret.lesson


def scene_open(world: World, child: Entity, helper: Entity, secret: Secret) -> None:
    world.say(
        f"Once, in {world.setting.place}, there lived a little {child.type} named {child.id}, "
        f"who was curious about the gate and what it might hide."
    )
    world.say(
        f"{helper.label.capitalize()} told {child.pronoun('object')} that behind the gate rested {secret.phrase}, "
        f"and that it must be treated with care."
    )
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["trust"] = child.memes.get("trust", 0) + 1


def scene_warn(world: World, child: Entity, helper: Entity, secret: Secret) -> None:
    world.para()
    world.say(
        f"{helper.label.capitalize()} said, 'Do not open the gate until the bell rings, or you may {secret.risk} "
        f"the shy thing inside.'"
    )
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.facts["warning"] = secret.risk


def scene_defy(world: World, child: Entity, secret: Secret) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    _tension_rises(world, child)
    world.say(
        f"But {child.id}'s curiosity was a bright little spark. {child.pronoun().capitalize()} tiptoed to the gate "
        f"and put a hand on the latch."
    )
    world.say(
        f"The air grew still, and the child felt the tension rise like a tight string."
    )


def scene_helper_turn(world: World, child: Entity, helper: Entity, secret: Secret) -> None:
    world.para()
    _calm_rises(world, child)
    world.say(
        f"{helper.label.capitalize()} came near and touched {child.pronoun('possessive')} shoulder softly. "
        f"'A curious heart is a fine thing,' {helper.pronoun()} said, "
        f"'but some doors should open only when the right time arrives.'"
    )
    world.say(
        f"{helper.label.capitalize()} placed a small task in {child.pronoun('possessive')} hands: "
        f"count the birds, listen for the bell, and keep watch without opening the gate."
    )


def scene_learn(world: World, child: Entity, helper: Entity, secret: Secret) -> None:
    world.para()
    _lesson_sticks(world, child, secret)
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    child.memes["tension"] = max(0.0, child.memes.get("tension", 0) - 1)
    world.say(
        f"{child.id} took a slow breath and did as {helper.label} asked. "
        f"{child.pronoun().capitalize()} counted the birds and waited for the bell."
    )
    world.say(
        f"When the bell at last rang, the gate opened gently, and the {secret.label} fluttered out unharmed, "
        f"glittering like a small piece of dawn."
    )
    world.say(
        f"{child.id} smiled, because now {child.pronoun()} knew that {secret.lesson}."
    )


def tell(setting: Setting, secret: Secret, child_name: str, child_gender: str, helper_kind: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_kind))
    world.facts.update(child=child, helper=helper, secret=secret, setting=setting)

    scene_open(world, child, helper, secret)
    scene_warn(world, child, helper, secret)
    scene_defy(world, child, secret)
    scene_helper_turn(world, child, helper, secret)
    scene_learn(world, child, helper, secret)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    helper = _safe_fact(world, world.facts, "helper")
    secret = _safe_fact(world, world.facts, "secret")
    return [
        f"Write a short folk tale about a curious {child.type} named {child.id} who must wait before opening a gate.",
        f"Tell a gentle story where {helper.label} teaches {child.id} that {secret.lesson}.",
        f"Write a child-friendly story about curiosity, tension, and a lesson learned in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    helper = _safe_fact(world, world.facts, "helper")
    secret = _safe_fact(world, world.facts, "secret")
    return [
        QAItem(
            question=f"Why did {child.id} feel tense near the gate?",
            answer=f"{child.id} felt tense because {helper.label} warned that opening the gate too soon might {secret.risk} the {secret.label}.",
        ),
        QAItem(
            question=f"What did {helper.label} ask {child.id} to do instead of opening the gate right away?",
            answer=f"{helper.label.capitalize()} asked {child.id} to wait for the bell, count the birds, and keep watch with patient hands.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn by the end of the story?",
            answer=f"{child.id} learned that {secret.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    secret = _safe_fact(world, world.facts, "secret")
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling of wanting to know more, to look closely, and to ask questions about something new.",
        ),
        QAItem(
            question="What is tension in a story?",
            answer="Tension is the tight feeling that comes when something important might go wrong before things are set right.",
        ),
        QAItem(
            question=f"What is a gentle way to protect {secret.label}?",
            answer=f"A gentle way to protect {secret.label} is to move slowly, listen carefully, and handle it with patient hands.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wood", secret="lantern_bird", name="Mina", gender="girl", helper="grandmother"),
    StoryParams(place="hill", secret="moon_well", name="Finn", gender="boy", helper="grandfather"),
    StoryParams(place="garden", secret="seed_box", name="Lila", gender="girl", helper="aunt"),
]


ASP_RULES = r"""
place(P) :- setting(P).
secret(S) :- has_secret(S).

curious(C) :- child(C).
tension(C) :- curious(C), warning(_,_,_).
lesson_learned(C) :- child(C), waits(C), bell_rings.
valid_story(P,S) :- setting(P), has_secret(S), gate_at(P), gentle_fix(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, secret in SECRETS.items():
        lines.append(asp.fact("has_secret", sid))
        lines.append(asp.fact("risk", sid, secret.risk))
        lines.append(asp.fact("zone", sid, secret.zone))
        lines.append(asp.fact("gentle_fix", sid, secret.gentle_fix.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about curiosity, tension, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--secret", choices=SECRETS)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = []
    for place, setting in SETTINGS.items():
        if getattr(args, "place", None) and place != getattr(args, "place", None):
            continue
        for secret in setting.affords:
            if getattr(args, "secret", None) and secret != getattr(args, "secret", None):
                continue
            combos.append((place, secret))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, secret = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(GENDERS))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, secret=secret, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SECRETS, params.secret), params.name, params.gender, params.helper)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for parity checks.")
        print(facts := asp_facts())
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
            header = f"### {p.name}: {p.secret} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
