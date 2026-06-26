#!/usr/bin/env python3
"""
piper_talk_dim_problem_solving_inner_monologue.py
=================================================

A small slice-of-life story world about Piper, a quiet voice, and a careful
problem-solution turn. The core premise is simple: Piper tends to talk dimly,
wants something ordinary, worries about being understood, and finds a gentle
way to solve it without breaking the mood of the place.

The simulated state tracks:
- physical meters: voice volume, distance, noise level, note legibility
- emotional memes: worry, caution, confidence, relief, patience

Story shape:
- beginning: Piper wants to speak up in a quiet setting
- middle: the talk-dim problem creates friction and inner monologue
- turn: Piper tries a safer, clearer strategy
- ending: the problem is solved in a small, satisfying way

This world is intentionally close to Slice of Life: no big adventure, just a
small human problem, a thought process, and a reassuring end image.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    quiet: bool
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
class StoryParams:
    place: str
    errand: str
    method: str
    name: str = "Piper"
    parent: str = "mother"
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "library": Setting(place="the library", quiet=True, affords={"ask-book", "find-book"}),
    "classroom": Setting(place="the classroom", quiet=True, affords={"ask-help", "show-paper"}),
    "kitchen": Setting(place="the kitchen", quiet=False, affords={"ask-snack", "point-shelf"}),
    "porch": Setting(place="the porch", quiet=False, affords={"call-friend", "wave"}),
}

ERRANDS = {
    "book": {
        "thing": "a picture book",
        "goal": "borrow a picture book",
        "place_hint": "library",
        "risk": "it would be easy to miss the answer",
        "caution": "keep a library voice",
        "ending": "the book tucked safely under {name}'s arm",
    },
    "help": {
        "thing": "a worksheet",
        "goal": "ask for help with a worksheet",
        "place_hint": "classroom",
        "risk": "the room could get noisy",
        "caution": "speak clearly and wait politely",
        "ending": "the worksheet finished and neat",
    },
    "snack": {
        "thing": "a snack bowl",
        "goal": "ask for a snack",
        "place_hint": "kitchen",
        "risk": "a soft voice might disappear in the clatter",
        "caution": "use a clear voice near the counter",
        "ending": "the snack bowl set on the table",
    },
}

METHODS = {
    "whisper": {
        "title": "talking dimly",
        "physical": "voice_volume",
        "delta": 0.2,
        "fix": "write it on a small note",
        "fix_action": "pinned the note where it could be seen",
    },
    "mumble": {
        "title": "mumbling",
        "physical": "voice_volume",
        "delta": 0.3,
        "fix": "step closer and try again",
        "fix_action": "stood nearer so the words could land",
    },
    "soft-say": {
        "title": "speaking softly",
        "physical": "voice_volume",
        "delta": 0.4,
        "fix": "use a clear voice and slow down",
        "fix_action": "breathed in and said the words carefully",
    },
}

GIRL_NAMES = ["Piper", "Maya", "Nora", "Lina", "Ruby", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Eli", "Noah"]


ASP_RULES = r"""
quiet_place(P) :- quiet(P).
low_voice(M) :- method(M), voice_delta(M,D), D < 1.
problem(P,E,M) :- setting(P), errand(E), method(M), quiet(P), low_voice(M).
fixable(P,E,M) :- problem(P,E,M), workaround(E,W), safe_fix(M,W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.quiet:
            lines.append(asp.fact("quiet", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid in ERRANDS:
        lines.append(asp.fact("errand", eid))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("voice_delta", mid, m["delta"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show problem/3.")
    model = asp.one_model(program)
    clingo = set(asp.atoms(model, "problem"))
    python = set(valid_combos())
    if clingo == python:
        print(f"OK: ASP matches Python ({len(clingo)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(clingo - python))
    print("only in Python:", sorted(python - clingo))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for errand in ERRANDS:
            for method in METHODS:
                if setting.quiet and _safe_lookup(METHODS, method)["delta"] < 0.5:
                    combos.append((place, errand, method))
                elif not setting.quiet:
                    combos.append((place, errand, method))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life world about Piper, talk-dim speech, and a small fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "errand", None):
        combos = [c for c in combos if c[1] == getattr(args, "errand", None)]
    if getattr(args, "method", None):
        combos = [c for c in combos if c[2] == getattr(args, "method", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, errand, method = rng.choice(list(combos))
    name = getattr(args, "name", None) or "Piper"
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, errand=errand, method=method, name=name, parent=parent)


def _do_problem(world: World, hero: Entity, errand: dict, method: dict) -> None:
    hero.meters["voice_volume"] = method["delta"]
    hero.memes["worry"] += 1
    if world.setting.quiet and hero.meters["voice_volume"] < 0.5:
        hero.memes["caution"] += 1
    world.facts["dim_voice"] = hero.meters["voice_volume"] < 0.5


def tell(setting: Setting, errand_id: str, method_id: str, name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if name in GIRL_NAMES else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    errand = _safe_lookup(ERRANDS, errand_id)
    method = _safe_lookup(METHODS, method_id)
    item = world.add(Entity(id="item", type=errand_id, label=errand["thing"], owner=hero.id, caretaker=parent.id))

    world.say(f"{hero.id} was a small child who liked ordinary days and little jobs.")
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place} to {errand['goal']}."
    )
    world.say(
        f"{hero.id} wanted to ask for {item.label}, but {hero.pronoun('possessive')} voice came out {method['title']}."
    )

    world.para()
    world.say(
        f"In {hero.id}'s head, a careful thought appeared: if the words were too soft, "
        f"{errand['risk']}."
    )
    world.say(
        f"{hero.id} listened to that worry and remembered the caution to {errand['caution']}."
    )
    world.say(
        f"{hero.id} took one breath and tried to solve the problem without making a fuss."
    )

    _do_problem(world, hero, errand, method)

    world.para()
    if method_id == "whisper":
        world.say(
            f"So {hero.id} wrote {hero.pronoun('possessive')} question on a small note and held it up with both hands."
        )
        world.say(
            f"The helper smiled, read it right away, and gave an answer that made {hero.id} relax."
        )
    elif method_id == "mumble":
        world.say(
            f"{hero.id} stepped closer, took another breath, and said the request again where it could be heard."
        )
        world.say(
            f"This time the words landed, and the answer came back warm and clear."
        )
    else:
        world.say(
            f"{hero.id} slowed down, used a clear voice, and said the request one careful piece at a time."
        )
        world.say(
            f"The helper understood at once, and the little errand turned easy."
        )

    world.para()
    world.say(
        f"At the end, {errand['ending'].format(name=hero.id)} was the quiet proof that the problem had been solved."
    )
    world.say(
        f"{hero.id} felt proud, not because the moment was loud, but because the small plan had worked."
    )

    world.facts.update(hero=hero, parent=parent, item=item, errand=errand, method=method, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    return [
        f"Write a gentle story about {hero.id}, a child with a talk-dim voice, who solves a small problem in {world.setting.place}.",
        f"Tell a slice-of-life story where {hero.id} worries about being heard, thinks carefully, and finds a polite way to ask for help.",
        f"Create a short child-friendly story with inner monologue, caution, and a simple solution for a quiet place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    errand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "errand")
    method = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "method")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a child who wanted to {errand['goal']} at {place}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} have?",
            answer=f"{hero.id} talked too dimly at first, so the request might not have been heard in {place}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} used {method['fix']} and made the request in a way that worked.",
        ),
        QAItem(
            question=f"Why did {hero.id} listen carefully before acting?",
            answer=f"{hero.id} remembered the caution that {errand['caution']} in that place.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and relieved when the small errand was done well with {parent.id if hasattr(parent,'id') else 'a parent'} nearby.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to talk dimly?", answer="Talking dimly means speaking in a very soft, low voice."),
        QAItem(question="Why can a quiet place be tricky?", answer="A quiet place can make a soft voice hard to hear, so people may need to speak more clearly."),
        QAItem(question="What is a helpful way to ask again?", answer="A helpful way to ask again is to slow down, get closer, or write the words down."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", errand="book", method="whisper", name="Piper", parent="mother"),
    StoryParams(place="classroom", errand="help", method="mumble", name="Piper", parent="father"),
    StoryParams(place="kitchen", errand="snack", method="soft-say", name="Piper", parent="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.errand, params.method, params.name, params.parent)
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
        print(asp_program("#show problem/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show problem/3."))
        atoms = sorted(set(asp.atoms(model, "problem")))
        print(f"{len(atoms)} compatible problems:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} in {p.place} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
