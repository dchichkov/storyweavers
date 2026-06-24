#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/sup_candid_moral_value_myth.py
===========================================================================================================

A standalone storyworld: a small mythic domain about a sacred sup, candid speech,
and a moral value that is tested, chosen, and proven in the ending image.

The seed words are threaded through the world as concrete story matter:
- sup
- candid

The style aims for myth: simple, archetypal, and lightly ceremonial, while still
being a state-driven simulation rather than a frozen paraphrase.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    seer: object | None = None
    sup: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    sacred: bool = False
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
class Artifact:
    id: str
    label: str
    phrase: str
    kind: str
    value: str
    risk: str
    keyword: str
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
class WiseGift:
    id: str
    label: str
    phrase: str
    helps_value: str
    remedy: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("reckless", 0.0) < THRESHOLD:
            continue
        vessel = next((e for e in world.entities.values() if e.kind == "artifact"), None)
        if not vessel:
            continue
        sig = ("spill", ent.id, vessel.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        vessel.meters["stained"] = vessel.meters.get("stained", 0.0) + 1
        vessel.meters["broken"] = vessel.meters.get("broken", 0.0) + 1
        out.append(f"The {vessel.label} was stained by rash hands.")
    return out


def _r_moral_turn(world: World) -> list[str]:
    out: list[str] = []
    speaker = next((e for e in world.entities.values() if e.type == "seer"), None)
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not speaker or not hero:
        return out
    if hero.memes.get("candor", 0.0) < THRESHOLD:
        return out
    sig = ("turn", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["clarity"] = hero.memes.get("clarity", 0.0) + 1
    out.append("The path toward truth opened like dawn.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_spill, _r_moral_turn):
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(setting: Setting, value: str, artifact: Artifact, gift: WiseGift,
                hero_name: str, hero_type: str, seer_name: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    seer = w.add(Entity(id=seer_name, kind="character", type="seer", label=seer_name))
    sup = w.add(Entity(id="sup", kind="artifact", type=artifact.kind, label=artifact.label, phrase=artifact.phrase))
    hero.meters["treasure"] = 1
    hero.memes["pride"] = 1
    hero.memes["desire"] = 1

    w.say(f"In {setting.place}, where the old stones remembered vows, {hero_name} guarded a {artifact.phrase}.")
    w.say(f"It was called the {artifact.label}, and it held the people's hopes as if they were water.")
    w.para()
    w.say(f"{hero_name} wished to keep the {artifact.label} and to be praised for it.")
    w.say(f"Yet the seer {seer_name} was candid and spoke plain truth: false boasting cracks what pride cannot mend.")
    hero.memes["heard_warning"] = 1
    hero.meters["reckless"] += 1

    # The turn: candor changes the hero's state.
    w.para()
    w.say(f"At the rim of the holy grove, {seer_name} offered no sweet lie, only candid words.")
    if value == "truth":
        hero.memes["candor"] += 1
        hero.meters["reckless"] = 0
        w.say(f"{hero_name} chose truth over boasting, bowed low, and told the village what was real.")
    else:
        hero.memes["candor"] += 0.5
        w.say(f"{hero_name} listened, though the choice was still hard.")

    propagate(w, narrate=True)

    # Resolution: the wise gift restores the value and proves it.
    w.para()
    if hero.memes.get("candor", 0.0) >= THRESHOLD:
        w.say(f"In thanks, the villagers placed a {gift.phrase} beside the {artifact.label}.")
        w.say(f"The {artifact.label} was no longer a prize for pride alone; it became a sign of candid courage.")
        w.say(f"And {hero_name}, once hungry for praise, walked home with clear eyes and a steady heart.")
        w.facts["resolved"] = True
    else:
        w.say(f"The night stayed uneasy, for the {artifact.label} still trembled under the weight of pride.")
        w.facts["resolved"] = False

    w.facts.update(
        hero=hero,
        seer=seer,
        artifact=sup,
        setting=setting,
        value=value,
        gift=gift,
    )
    return w


SETTINGS = {
    "grove": Setting(place="the moonlit grove", sacred=True, affords={"truth", "warning"}),
    "hill": Setting(place="the wind hill", sacred=True, affords={"truth"}),
    "river": Setting(place="the bright riverbank", sacred=False, affords={"truth", "warning"}),
}

ARTIFACTS = {
    "sup": Artifact(
        id="sup",
        label="sup",
        phrase="a polished sup",
        kind="vessel",
        value="honor",
        risk="stain",
        keyword="sup",
        tags={"sup", "vessel"},
    ),
    "cup": Artifact(
        id="cup",
        label="cup",
        phrase="a silver cup",
        kind="vessel",
        value="honor",
        risk="stain",
        keyword="candid",
        tags={"candid", "vessel"},
    ),
}

GIFTS = {
    "lantern": WiseGift(id="lantern", label="lantern", phrase="a cedar lantern", helps_value="truth", remedy="light"),
    "shawl": WiseGift(id="shawl", label="shawl", phrase="a woven shawl", helps_value="truth", remedy="warmth"),
}

GIRL_NAMES = ["Ari", "Mina", "Lina", "Nia", "Ena"]
BOY_NAMES = ["Oren", "Tavi", "Soren", "Kian", "Milo"]
SEER_NAMES = ["Elder Vale", "Old Mira", "Sage Rowan"]


@dataclass
class StoryParams:
    place: str
    artifact: str
    gift: str
    name: str
    gender: str
    seer: str
    value: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for art in ARTIFACTS:
            for val in setting.affords:
                out.append((place, art, val))
    return out


ASP_RULES = r"""
valid(Place, Artifact, Value) :- setting(Place), artifact(Artifact), affords(Place, Value).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.sacred:
            lines.append(asp.fact("sacred", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic moral-value storyworld about sup and candid truth.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--value", choices=["truth"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--seer", choices=SEER_NAMES)
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
    if getattr(args, "place", None) and getattr(args, "artifact", None) and getattr(args, "value", None):
        if (getattr(args, "place", None), getattr(args, "artifact", None), getattr(args, "value", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "artifact", None) is None or c[1] == getattr(args, "artifact", None))
              and (getattr(args, "value", None) is None or c[2] == getattr(args, "value", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, artifact, value = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    seer = getattr(args, "seer", None) or rng.choice(SEER_NAMES)
    return StoryParams(place=place, artifact=artifact, gift=rng.choice(list(GIFTS)), name=name, gender=gender, seer=seer, value=value)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about a {f["artifact"].label} and the virtue of candid truth.',
        f'Tell a simple legend where {f["hero"].id} learns why candid words matter at {f["setting"].place}.',
        f'Write a tiny myth that includes the words "sup" and "candid" and ends with a moral change.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    seer = f["seer"]
    art = f["artifact"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who guarded the {art.label} in {setting.place}?",
            answer=f"{hero.id} guarded the {art.label}, but {seer.id} was the one who spoke candid truth.",
        ),
        QAItem(
            question=f"What moral value mattered most in this story?",
            answer=f"Candid truth mattered most, because the story shows that honest words protect what pride can damage.",
        ),
        QAItem(
            question=f"Why did the seer speak so plainly?",
            answer=f"The seer spoke plainly to keep {hero.id} from letting pride stain the {art.label} and to lead them back to truth.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does candid mean?",
            answer="Candid means honest and plain-spoken, without hiding the truth.",
        ),
        QAItem(
            question="What is a sup in this world?",
            answer="A sup is a sacred vessel that the people treat with care, because it can stand for honor and memory.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    bits.append(f"fired={sorted(world.fired)}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    world = build_world(_safe_lookup(SETTINGS, params.place), "truth", _safe_lookup(ARTIFACTS, params.artifact), _safe_lookup(GIFTS, params.gift), params.name, params.gender, params.seer)
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


CURATED = [
    StoryParams(place="grove", artifact="sup", gift="lantern", name="Ari", gender="girl", seer="Elder Vale", value="truth"),
    StoryParams(place="river", artifact="sup", gift="shawl", name="Oren", gender="boy", seer="Old Mira", value="truth"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
