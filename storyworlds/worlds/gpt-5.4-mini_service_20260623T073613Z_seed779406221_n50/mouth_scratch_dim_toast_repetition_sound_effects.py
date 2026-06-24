#!/usr/bin/env python3
"""
storyworlds/worlds/mouth_scratch_dim_toast_repetition_sound_effects.py
======================================================================

A tiny fable-style story world about a mouth that scratches a dim toast,
where repetition and sound effects matter.

Premise:
A hungry creature wants toast, but the toast is dim and stubborn. The creature
must learn that noisy rushing and repeated scratching only make crumbs and
frustration, while patience, warmth, and a careful bite change the ending.

The world tracks:
- a mouth that can nibble, chew, and pause
- a toast that can be dim, warm, buttered, and crumbly
- repeated sounds that accumulate into mood and mess
- a small moral turn from impatience to care

The prose is authored from simulated state; it is not a frozen paragraph with
swapped nouns.
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
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    hero: object | None = None
    toast_ent: object | None = None
    def p(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "neutral")
        if gender == "female":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "male":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    setting: str
    affords: set[str] = field(default_factory=set)
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
class ToastKind:
    id: str
    label: str
    phrase: str
    dimness: str
    crunch: str
    mess: str
    warms_with: set[str] = field(default_factory=set)
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


@dataclass
class MouthAction:
    id: str
    label: str
    sound: str
    repeated_sound: str
    method: str
    turns: str
    helps_with: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    creature: str
    gender: str
    toast: str
    action: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    "kitchen": Place("kitchen", "the kitchen", "a small kitchen", {"munch", "warm"}),
    "table": Place("table", "the table", "a bright table", {"munch", "warm"}),
    "porch": Place("porch", "the porch", "a sunny porch", {"munch", "warm"}),
}

TOASTS = {
    "plain": ToastKind("plain", "plain toast", "a slice of plain toast", "pale", "crisp", "crumbs", {"warm"}),
    "buttered": ToastKind("buttered", "buttered toast", "a slice of buttered toast", "golden", "buttery", "crumbs", {"warm"}),
    "jam": ToastKind("jam", "jam toast", "a slice of jam toast", "red-streaked", "sticky", "crumbs", {"warm"}),
}

ACTIONS = {
    "scratch": MouthAction("scratch", "scratch", "scritch-scritch", "scritch scritch scritch", "scratching at", "kept scratching", {"munch"}),
    "nibble": MouthAction("nibble", "nibble", "nip-nip", "nip nip nip", "nibbling", "kept nibbling", {"munch"}),
    "murmur": MouthAction("murmur", "murmur", "mhm-mhm", "mhm mhm mhm", "murmuring over", "kept murmuring", {"warm"}),
}

NAMES = ["Milo", "Tia", "Bram", "Lina", "Ned", "Pia"]
GENDERS = ["male", "female"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for act in ACTIONS.values():
            for toast in TOASTS.values():
                if place in {"kitchen", "table", "porch"} and act.id in {"scratch", "nibble", "murmur"}:
                    combos.append((place, act.id, toast.id))
    return combos


def reasonableness_gate(place: str, action: str, toast: str) -> bool:
    return (place, action, toast) in valid_combos()


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TOASTS.items():
        lines.append(asp.fact("toast", tid))
        lines.append(asp.fact("dimness", tid, t.dimness))
        for w in sorted(t.warms_with):
            lines.append(asp.fact("warms_with", tid, w))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sound", aid, a.sound))
        for h in sorted(a.helps_with):
            lines.append(asp.fact("helps_with", aid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,T) :- place(P), action(A), toast(T), affords(P,munch), sound(A,_), dimness(T,_).
"""
 
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(place: Place, toast: ToastKind, action: MouthAction, name: str, gender: str) -> World:
    world = World(place)
    hero = world.add(Entity("hero", "character", name, attrs={"gender": gender}))
    toast_ent = world.add(Entity("toast", "thing", toast.label))
    hero.memes["hunger"] = 1
    toast_ent.meters["dim"] = 1
    toast_ent.meters["crumbly"] = 0
    hero.memes["patience"] = 0
    world.say(f"{name} came to {place.setting} where {toast.phrase} waited, dim and still.")
    world.say(f"{hero.p().capitalize()} looked at the toast and {action.sound}, because {hero.p()} was hungry.")
    world.para()
    if action.id == "scratch":
        repeat = f"{action.repeated_sound}, {action.repeated_sound}, {action.repeated_sound}"
        world.say(f"{hero.p().capitalize()} kept {action.turns} {toast.label}. {repeat} went the mouth, but the toast only grew more crumbly.")
        toast_ent.meters["crumbly"] += 1
        hero.memes["irritation"] += 1
    elif action.id == "nibble":
        world.say(f"{hero.p().capitalize()} {action.turns} the edge. {action.sound}! {action.sound}! Small bites came off, and the toast began to warm in {hero.p('possessive')} mouth.")
        toast_ent.meters["crumbly"] += 1
        toast_ent.meters["warm"] += 1
    else:
        world.say(f"{hero.p().capitalize()} paused and {action.turns} the toast softly. {action.sound}, {action.sound}. That quiet made room for warmth.")
        toast_ent.meters["warm"] += 1
        hero.memes["patience"] += 1
    world.para()
    if toast_ent.meters.get("crumbly", 0) >= THRESHOLD and action.id == "scratch":
        world.say(f"At last, {name} stopped the {action.repeated_sound} and chose a slower bite. The toast stayed dim, but the noise faded.")
        hero.memes["patience"] += 1
    else:
        world.say(f"{name} finished with a careful mouthful, and the toast no longer seemed so dim.")
    world.facts.update(hero=hero, toast=toast_ent, toast_cfg=toast, action=action, place=place, outcome="moral")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tiny fable for a child about {f["hero"].id} and {f["toast_cfg"].label}, using the sound effect "{f["action"].sound}".',
        f"Tell a story where a mouth keeps {f['action'].method} toast, then learns a gentler way.",
        f'Write a simple repetition story about "{f["action"].repeated_sound}" and a dim slice of toast becoming better.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, toast, action = f["hero"], f["toast"], f["action"]
    return [
        QAItem(question=f"What did {hero.id} do to the toast at first?", answer=f"{hero.id} kept {action.turns} the toast, making a noisy {action.sound} sound over and over."),
        QAItem(question=f"Why did the toast change?", answer=f"The repeated {action.sound} sounds made the moment feel rushed, but the story turned when {hero.id} chose a slower, kinder way."),
        QAItem(question=f"How did the ending prove the change?", answer=f"The toast ended up warmer and less dim, and {hero.id} finished with a careful mouthful instead of more scratching."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is toast?", answer="Toast is bread that has been heated until it is crisp and brown."),
        QAItem(question="Why do sound effects repeat in stories?", answer="Repeated sound effects help show that something keeps happening, and they can make a story feel lively and easy to hear in your mind."),
        QAItem(question="Why should a mouth be gentle with food?", answer="A gentle mouth helps food stay neat and easy to eat, and it keeps the moment calm instead of messy."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style mouth-and-toast storyworld with repetition and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--toast", choices=TOASTS)
    ap.add_argument("--action", choices=ACTIONS)
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
    if getattr(args, "place", None) and getattr(args, "action", None) and getattr(args, "toast", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "action", None), getattr(args, "toast", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    toast = getattr(args, "toast", None) or rng.choice(list(TOASTS))
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    if not reasonableness_gate(place, action, toast):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    creature = getattr(args, "creature", None) or rng.choice(NAMES)
    return StoryParams(place=place, creature=creature, gender=gender, toast=toast, action=action)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TOASTS, params.toast), _safe_lookup(ACTIONS, params.action), params.creature, params.gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "all", None):
        samples = [generate(StoryParams(p, "Milo", "neutral", t, a)) for p in PLACES for t in TOASTS for a in ACTIONS if reasonableness_gate(p, a, t)]
    elif getattr(args, "asp", None):
        import storyworlds.asp as asp
        print(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid"))))
        return
    elif getattr(args, "verify", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        asp_set = set(asp.atoms(model, "valid"))
        py_set = set(valid_combos())
        if asp_set != py_set:
            print("MISMATCH")
            print("only asp:", sorted(asp_set - py_set))
            print("only py:", sorted(py_set - asp_set))
            raise SystemExit(1)
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
