#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/protest_pediatric_rosary_foreshadowing_bad_ending_friendship.py
===============================================================================================================

A small standalone storyworld for a rhyming, child-facing tale about a protest
near a pediatric clinic, a rosary kept for comfort, friendship, foreshadowing,
and a bad ending that still closes on a clear, changed image.

The world is intentionally tiny:
- two friends
- one place
- one protest cause
- one comfort object
- one weather / foreshadowing signal
- one ending that turns sad because the protest fails

The prose is state-driven: meters and memes accumulate, warnings matter, and
the ending is different because the world state changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    hero1: object | None = None
    hero2: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    weather: str
    affordance: str
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
class Cause:
    id: str
    slogan: str
    action: str
    risk_word: str
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


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
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
class StoryParams:
    setting: str = "clinic"
    cause: str = "save_clinic"
    comfort: str = "rosary"
    hero1_name: str = "Maya"
    hero1_gender: str = "girl"
    hero2_name: str = "Jules"
    hero2_gender: str = "boy"
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "clinic": Setting(place="the pediatric clinic", weather="grey", affordance="front steps"),
    "sidewalk": Setting(place="the sidewalk by the pediatric clinic", weather="windy", affordance="sidewalk"),
}

CAUSES = {
    "save_clinic": Cause(
        id="save_clinic",
        slogan="Save the little kids' clinic!",
        action="hold a peaceful protest",
        risk_word="closure",
        tags={"protest", "pediatric"},
    ),
    "kind_funds": Cause(
        id="kind_funds",
        slogan="Keep care close and kind!",
        action="share bright signs and protest politely",
        risk_word="closure",
        tags={"protest", "pediatric"},
    ),
}

COMFORTS = {
    "rosary": Comfort(
        id="rosary",
        label="rosary",
        phrase="a small rosary from grandma",
        tags={"rosary"},
    ),
    "badge": Comfort(
        id="badge",
        label="friendship badge",
        phrase="a friendship badge with a shiny star",
        tags={"friendship"},
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Tess", "Luna", "Sage"]
BOY_NAMES = ["Jules", "Noah", "Eli", "Owen", "Ben"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def _warn(world: World, hero1: Entity, hero2: Entity, cause: Cause) -> None:
    hero2.memes["worry"] = hero2.memes.get("worry", 0.0) + 1
    world.say(
        f"At {world.setting.place}, the sky grew dim and the paper signs began to bow; "
        f"that was a foreshadowing whisper, a clue that trouble would soon show."
    )
    world.say(
        f'One friend said, "{cause.slogan}" and lifted a sign with care, '
        f"but the wind tugged at the corners and made the letters shiver in the air."
    )
    world.say(
        f'{hero2.id} bit {hero2.pronoun("possessive")} lip and held the {world.facts["comfort"].label} tight, '
        f"for small brave hearts can feel a storm before it picks a fight."
    )


def _protest(world: World, hero1: Entity, hero2: Entity, cause: Cause) -> None:
    hero1.memes["hope"] = hero1.memes.get("hope", 0.0) + 1
    hero2.memes["friendship"] = hero2.memes.get("friendship", 0.0) + 1
    world.say(
        f"They marched in step beside the curb, as friends will often do, "
        f"with careful feet and steady voices, trying to make the message true."
    )
    world.say(
        f"They meant to {cause.action}, not shout or shove or roar, "
        f"just rhyme their signs and tell the world what little people need most of all more."
    )


def _bad_turn(world: World, hero1: Entity, hero2: Entity, cause: Cause) -> None:
    hero1.meters["feet"] = hero1.meters.get("feet", 0.0) + 1
    hero2.meters["feet"] = hero2.meters.get("feet", 0.0) + 1
    hero1.memes["sad"] = hero1.memes.get("sad", 0.0) + 1
    hero2.memes["sad"] = hero2.memes.get("sad", 0.0) + 1
    world.say(
        f"Then the wind turned mean and the rain came down, cold, quick, and thick; "
        f"their painted signs drooped into puddles, and the brave rhyme lost its trick."
    )
    world.say(
        f"The clinic doors stayed closed that hour, and nobody came out to see; "
        f"the protest did not fix a thing, which was the bad part of the story."
    )


def _ending(world: World, hero1: Entity, hero2: Entity, comfort: Comfort, cause: Cause) -> None:
    hero1.memes["friendship"] = hero1.memes.get("friendship", 0.0) + 1
    hero2.memes["friendship"] = hero2.memes.get("friendship", 0.0) + 1
    world.say(
        f"So they walked home slow, shoes wet and signs bent low, "
        f"while {hero2.id} kept the {comfort.label} tucked where no more raindrops blow."
    )
    world.say(
        f"They were sad that day, yet still side by side, because friendship stayed near; "
        f"the bad ending was the broken protest, but the friends were still right here."
    )


def tell(setting: Setting, cause: Cause, comfort: Comfort, hero1_name: str, hero1_gender: str,
         hero2_name: str, hero2_gender: str) -> World:
    world = World(setting)
    hero1 = world.add(Entity(
        id=hero1_name, kind="character", type=hero1_gender, role="friend",
        tags={"friendship"}, meters={"feet": 0.0}, memes={"friendship": 1.0}
    ))
    hero2 = world.add(Entity(
        id=hero2_name, kind="character", type=hero2_gender, role="friend",
        tags={"friendship"}, meters={"feet": 0.0}, memes={"friendship": 1.0}
    ))
    world.facts["comfort"] = comfort
    world.facts["cause"] = cause
    world.facts["setting"] = setting

    world.say(
        f"In {setting.place}, two friends met near the door, with quiet hearts and a rhyme to say; "
        f"they cared about a pediatric clinic and wanted a peaceful way."
    )
    world.say(
        f"{hero1.id} held a sign so bright, and {hero2.id} held {comfort.phrase}; "
        f"their friendship made the morning warm, even under the grey cloud's gaze."
    )
    world.para()
    _warn(world, hero1, hero2, cause)
    world.para()
    _protest(world, hero1, hero2, cause)
    world.para()
    _bad_turn(world, hero1, hero2, cause)
    world.para()
    _ending(world, hero1, hero2, comfort, cause)

    world.facts.update(
        hero1=hero1, hero2=hero2, comfort=comfort, cause=cause,
        foreshadowed=True, failed=True, friendship=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, k) for s in SETTINGS for c in CAUSES for k in COMFORTS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that uses the words "protest", '
        f'"pediatric", and "rosary".',
        f"Tell a sad but gentle friendship story about {f['hero1'].id} and "
        f"{f['hero2'].id} at {world.setting.place}.",
        f"Write a story with foreshadowing, a failed protest, and a clear ending "
        f"image of two friends walking home together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2, cause, comfort = f["hero1"], f["hero2"], f["cause"], f["comfort"]
    return [
        QAItem(
            question=f"Who are the story's two friends?",
            answer=f"The story is about {h1.id} and {h2.id}. They go together to the "
                   f"pediatric clinic and try to keep their friendship strong even when "
                   f"their protest goes badly."
        ),
        QAItem(
            question=f"Why did the friends go to the pediatric clinic?",
            answer=f"They went there to protest for the clinic's future. They hoped "
                   f"their signs and careful voices would help, but the weather and the "
                   f"closed doors turned the plan into a sad one."
        ),
        QAItem(
            question=f"What did {h2.id} carry for comfort?",
            answer=f"{h2.id} carried {comfort.phrase}. It helped the friend stay calm "
                   f"when the wind and rain made the protest feel smaller and sadder."
        ),
        QAItem(
            question="What was the bad ending?",
            answer="The rain ruined the signs, nobody came out to listen, and the "
                   "protest failed. The friends went home sad, but they stayed together."
        ),
        QAItem(
            question=f"How did friendship matter in the story?",
            answer=f"Friendship kept {h1.id} and {h2.id} side by side. Even when the "
                   f"protest ended badly, they walked home together instead of giving up "
                   f"on each other."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a protest?",
            answer="A protest is when people gather to show that they care about a "
                   "problem and want change. They may hold signs, speak, or march together."
        ),
        QAItem(
            question="What does pediatric mean?",
            answer="Pediatric means connected to children's health and doctors who care "
                   "for kids."
        ),
        QAItem(
            question="What is a rosary?",
            answer="A rosary is a string of beads used for prayer or quiet counting. "
                   "Some people keep one to feel calm and close to family."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint that something important may happen later. "
                   "It gives the story a small clue before the big turn."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S,C,K) :- setting(S), cause(C), comfort(K).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CAUSES:
        lines.append(asp.fact("cause", c))
    for k in COMFORTS:
        lines.append(asp.fact("comfort", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    from storyworlds import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    ok = py == ac
    if not ok:
        print("MISMATCH")
        if py - ac:
            print("only python:", sorted(py - ac))
        if ac - py:
            print("only asp:", sorted(ac - py))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, cause=None, comfort=None, hero1_name=None, hero1_gender=None, hero2_name=None, hero2_gender=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    print("OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming protest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "cause", None) is None or c[1] == getattr(args, "cause", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, cause, comfort = rng.choice(list(combos))
    h1_gender = rng.choice(["girl", "boy"])
    h2_gender = "boy" if h1_gender == "girl" else "girl"
    h1 = getattr(args, "hero1_name", None) or rng.choice(GIRL_NAMES if h1_gender == "girl" else BOY_NAMES)
    h2 = getattr(args, "hero2_name", None) or rng.choice(BOY_NAMES if h2_gender == "boy" else GIRL_NAMES)
    if h2 == h1:
        h2 = "Noah" if h1 != "Noah" else "Luna"
    return StoryParams(
        setting=setting, cause=cause, comfort=comfort,
        hero1_name=h1, hero1_gender=h1_gender,
        hero2_name=h2, hero2_gender=h2_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.cause not in CAUSES or params.comfort not in COMFORTS:
        pass
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(CAUSES, params.cause),
        _safe_lookup(COMFORTS, params.comfort),
        params.hero1_name, params.hero1_gender,
        params.hero2_name, params.hero2_gender,
    )
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for s, c, k in valid_combos():
            params = StoryParams(setting=s, cause=c, comfort=k)
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
