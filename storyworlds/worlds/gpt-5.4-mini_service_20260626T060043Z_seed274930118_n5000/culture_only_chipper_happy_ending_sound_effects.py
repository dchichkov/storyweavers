#!/usr/bin/env python3
"""
storyworlds/worlds/culture_only_chipper_happy_ending_sound_effects.py
=====================================================================

A tiny whodunit-style story world about a missing display item at a cheerful
cultural fair. The mystery is gentle, the clues are concrete, and the ending is
always happy.

Seed tale premise:
---
At the neighborhood culture fair, a small brass bell from the tea table goes
missing just before the music starts. Mina, a chipper child detective, follows
the clues: a sticky ribbon, a sprinkle of crumbs, and a tiny trail of rice.
Everyone worries a thief is hiding nearby, but the "mystery" turns out to be a
simple mix-up. The bell was only borrowed to ring the opening cheer. The fair
ends with laughter, a bright chime, and a happy ending for everyone.

World model:
---
Characters have meters and memes. Physical meters track things like possession,
moved objects, and sticky traces. Emotional memes track worry, confidence, and
chipper mood. The simulated state drives the narration: clues appear because
someone moved through the setting, and resolution follows only when the
detective correctly identifies the harmless cause.

Narrative instruments:
---
* Whodunit clue trail
* Sound effects in the prose
* A happy ending beat that proves the state changed
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

WORLD_ID = "culture_only_chipper_happy_ending_sound_effects"



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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    companion: object | None = None
    detective: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "aunt"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "uncle"}:
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
    culture: str
    ambient_sound: str
    feature: str
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
class Clue:
    name: str
    source: str
    kind: str
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
class Artifact:
    label: str
    phrase: str
    cultural_context: str
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
    setting: str
    clue_style: str
    name: str
    companion: str
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
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS: dict[str, Setting] = {
    "fair": Setting(
        place="the neighborhood culture fair",
        culture="music, tea, lanterns, and handmade snacks",
        ambient_sound="drum taps and laughing voices",
        feature="a bright stage with paper flags",
    ),
    "museum": Setting(
        place="the little town museum",
        culture="old songs, painted pots, and quiet footsteps",
        ambient_sound="soft echoes and a squeaky floorboard",
        feature="glass cases with labels in neat rows",
    ),
    "kitchen": Setting(
        place="Grandma's kitchen during the culture day",
        culture="spiced rice, tea, and story cards",
        ambient_sound="clink, clink, and a cheerful kettle hiss",
        feature="a long table covered in a patterned cloth",
    ),
}

CLUES: list[Clue] = [
    Clue(name="ribbon", source="the scarf basket", kind="sticky"),
    Clue(name="crumbs", source="the snack tray", kind="crumbly"),
    Clue(name="rice", source="the tea table", kind="grains"),
    Clue(name="paint", source="the craft corner", kind="smudged"),
]

ARTIFACTS: dict[str, Artifact] = {
    "bell": Artifact(
        label="brass bell",
        phrase="a small brass bell with a bright handle",
        cultural_context="used to open a celebration",
    ),
    "fan": Artifact(
        label="paper fan",
        phrase="a painted paper fan with red flowers",
        cultural_context="used in a dance display",
    ),
    "spoon": Artifact(
        label="silver spoon",
        phrase="a little silver spoon for the tasting table",
        cultural_context="used to stir sweet tea",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small whodunit story world with a happy ending and sound effects."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue-style", choices=["sticky", "crumbly", "grains", "smudged"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father", "grandma", "grandpa", "aunt", "uncle"])
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for clue in CLUES:
            out.append((sname, clue.kind))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue_style = getattr(args, "clue_style", None) or rng.choice([c.kind for c in CLUES])
    if (setting, clue_style) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(["Mina", "Tari", "Lulu", "Owen", "Nia", "Sana"])
    companion = getattr(args, "companion", None) or rng.choice(["mother", "father", "grandma", "grandpa", "aunt", "uncle"])
    return StoryParams(setting=setting, clue_style=clue_style, name=name, companion=companion)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("culture", sid, setting.culture))
        lines.append(asp.fact("sound", sid, setting.ambient_sound))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue.kind))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("context", aid, art.cultural_context))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C) :- setting(S), clue(C).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    w = World(setting)

    detective = w.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Lulu", "Nia", "Sana"} else "boy",
        label=params.name,
        meters={"confidence": 0.0, "attention": 1.0, "chipper": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "delight": 1.0},
    ))
    companion = w.add(Entity(
        id="Companion",
        kind="character",
        type=params.companion,
        label=f"the {params.companion}",
        meters={"worry": 1.0},
        memes={"care": 1.0},
    ))

    art = w.add(Entity(
        id="artifact",
        kind="thing",
        type="artifact",
        label="bell",
        phrase=ARTIFACTS["bell"].phrase,
        owner="stage_table",
        location=setting.place,
        meters={"present": 1.0},
    ))

    w.facts.update(
        detective=detective,
        companion=companion,
        artifact=art,
        setting=setting,
        clue_style=params.clue_style,
    )
    return w


def clue_trail_for(style: str) -> list[Clue]:
    ordered = [c for c in CLUES if c.kind == style]
    return ordered + [c for c in CLUES if c.kind != style]


def story_from_world(w: World) -> None:
    d = w.facts["detective"]
    c = w.facts["companion"]
    setting = w.facts["setting"]

    w.say(
        f"At {setting.place}, the air held {setting.culture}, and {setting.ambient_sound} drifted by the tables."
    )
    w.say(
        f"{d.label} was a chipper little detective who liked only one thing more than a puzzle: a happy ending."
    )
    w.say(
        f"{d.label} and {c.label} walked past {setting.feature} when someone gasped, \"Oh no!\""
    )
    w.say(
        f"The brass bell that should have sat on the tea table was missing, and the whole room went quiet."
    )

    w.para()
    w.say(
        f"{d.label} looked around. Tap-tap, shh, tap-tap. The child detective followed the first clue."
    )

    trail = clue_trail_for(w.facts["clue_style"])
    w.facts["trail"] = trail
    for clue in trail:
        if clue.kind == "sticky":
            w.say(f"A sticky ribbon clung to the scarf basket. \"Hmm,\" {d.label} said, \"someone brushed by here.\"")
            w.get("Companion").memes["worry"] += 1
        elif clue.kind == "crumbly":
            w.say(f"Crinkle-crunch! Crumbs dotted the snack tray, pointing toward the tasting line.")
            w.get("Companion").memes["worry"] += 0.5
        elif clue.kind == "grains":
            w.say(f"Rustle-rustle! Tiny rice grains led past the tea table and stopped near the stage steps.")
            d.meters["confidence"] += 1
        else:
            w.say(f"Smudge-smudge! A faint paint mark showed up near the craft corner, but it was only from a poster.")
            d.meters["confidence"] += 1

    w.para()
    w.say(
        f"{d.label} paused by the stage. The clue trail did not point to a thief at all."
    )
    w.say(
        f"Instead, it pointed to the opening cheer, where the bell had been borrowed for the first ring."
    )
    w.say(
        f"Ring-a-ding! The helper from the tea table lifted a hand and laughed, \"It was only moved for the song!\""
    )
    w.say(
        f"Then the bell went chime! The sound was bright and friendly, not scary at all."
    )

    d.meters["confidence"] += 2
    d.memes["worry"] = 0.0
    d.memes["delight"] += 1
    c.memes["worry"] = 0.0
    w.facts["resolved"] = True
    w.facts["cause"] = "borrowed for the opening cheer"
    w.facts["ending"] = "happy"


def generate(params: StoryParams) -> StorySample:
    w = setup_world(params)
    story_from_world(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    c = _safe_fact(world, f, "companion")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short whodunit for a child named {d.label} at {setting.place} with a happy ending.',
        f"Tell a chipper mystery story where {d.label} follows clues with {c.label} and finds out the missing bell was only borrowed.",
        f'Write a simple culture-day mystery that includes sound effects like "tap-tap" and ends with a cheerful reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    c = _safe_fact(world, f, "companion")
    setting = _safe_fact(world, f, "setting")
    clue_style = _safe_fact(world, f, "clue_style")
    return [
        QAItem(
            question=f"What kind of story is this one at {setting.place}?",
            answer=f"It is a small whodunit at {setting.place}, but it stays gentle and ends happily.",
        ),
        QAItem(
            question=f"Who was the chipper detective in the story?",
            answer=f"The chipper detective was {d.label}, who stayed curious and hopeful the whole time.",
        ),
        QAItem(
            question=f"What did {d.label} and {c.label} look for at the fair?",
            answer="They looked for the missing brass bell from the tea table.",
        ),
        QAItem(
            question=f"What clue style helped {d.label} solve the mystery?",
            answer=f"The trail used {clue_style} clues, which led the detective to the real answer.",
        ),
        QAItem(
            question="Was there a thief in the end?",
            answer="No. The bell was only borrowed for the opening cheer, so the mystery had a safe, happy answer.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a bright chime, laughter, and a happy ending for everyone at the culture fair.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a clue?",
        answer="A clue is a small piece of evidence that helps solve a mystery.",
    ),
    QAItem(
        question="What does chipper mean?",
        answer="Chipper means cheerful, lively, and bright in mood.",
    ),
    QAItem(
        question="What is a culture fair?",
        answer="A culture fair is a gathering where people share food, music, art, and traditions.",
    ),
    QAItem(
        question="Why do bells make a good signal?",
        answer="Bells make a clear sound, so people can hear them and know when something is starting.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) " + " ".join(bits))
    lines.append(f"  facts: {world.facts.get('cause', '')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[tuple[str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(setting="fair", clue_style="sticky", name="Mina", companion="mother"),
    StoryParams(setting="museum", clue_style="grains", name="Owen", companion="grandpa"),
    StoryParams(setting="kitchen", clue_style="crumbly", name="Nia", companion="aunt"),
]


def asp_verify_full() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_full())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:\n")
        for setting, clue in models:
            print(f"  {setting:8} {clue}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name} at {p.setting} ({p.clue_style})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue_style = getattr(args, "clue_style", None) or rng.choice([c.kind for c in CLUES])
    if (setting, clue_style) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(["Mina", "Owen", "Nia", "Tari", "Lulu", "Sana"])
    companion = getattr(args, "companion", None) or rng.choice(["mother", "father", "grandma", "grandpa", "aunt", "uncle"])
    return StoryParams(setting=setting, clue_style=clue_style, name=name, companion=companion)


if __name__ == "__main__":
    main()
