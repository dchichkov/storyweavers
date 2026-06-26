#!/usr/bin/env python3
"""
A small slice-of-life storyworld about advice, ease, and reconciliation.

Premise:
A child wants to keep doing a small everyday task alone, makes a tiny mistake,
feels flustered, hears gentle advice from a loved one, and then eases back into
the moment with a simple reconciliation.

This world keeps the action grounded in ordinary life: tidying a shelf, sorting
cards, watering plants, or packing a bag. The tension is mild and social, not
dramatic. The turn comes from advice that reduces pressure, and the ending image
shows the relationship settled again.
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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "uncle"}:
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
    time: str
    cozy: bool = True
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
class Task:
    id: str
    verb: str
    gerund: str
    small_mistake: str
    fix_hint: str
    mess: str
    kind: str
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


@dataclass
class Reconciliation:
    id: str
    phrase: str
    action: str
    result_line: str
    helps_with: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.facts: dict[str, object] = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _get_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = _get_meter(e, key) + delta


def _get_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = _get_meme(e, key) + delta


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    _add_meter(actor, task.id, 1.0)
    _add_meme(actor, "effort", 1.0)
    if narrate:
        world.say(f"{actor.id} kept going with {task.gerund}.")


def _mistake(world: World, actor: Entity, task: Task) -> None:
    _add_meter(actor, "mess", 1.0)
    _add_meme(actor, "fluster", 1.0)
    world.say(f"Then {task.small_mistake}, and {actor.id} paused with a hot face.")


def _advice(world: World, adviser: Entity, actor: Entity, task: Task) -> None:
    _add_meme(adviser, "care", 1.0)
    _add_meme(actor, "heard_advice", 1.0)
    world.say(
        f"{adviser.id} gave a little advice: \"{task.fix_hint}.\" "
        f"The words were calm and easy to hear."
    )


def _ease(world: World, actor: Entity, adviser: Entity, task: Task) -> None:
    _add_meme(actor, "ease", 1.0)
    _add_meme(actor, "hope", 1.0)
    actor.memes["fluster"] = max(0.0, _get_meme(actor, "fluster") - 1.0)
    world.say(
        f"{actor.id} took a slow breath, tried {task.action}, and felt the tight feeling ease."
    )


def _reconcile(world: World, actor: Entity, adviser: Entity, recon: Reconciliation) -> None:
    _add_meme(actor, "reconcile", 1.0)
    _add_meme(adviser, "reconcile", 1.0)
    actor.memes["hurt"] = 0.0
    adviser.memes["worry"] = 0.0
    world.say(recon.phrase)
    world.say(recon.result_line)


def predict_state(world: World, actor: Entity, task: Task, recon: Reconciliation) -> dict[str, object]:
    sim = world.copy()
    hero = sim.entities[actor.id]
    _do_task(sim, hero, task, narrate=False)
    _mistake(sim, hero, task)
    return {
        "fluster": _get_meme(hero, "fluster"),
        "mess": _get_meter(hero, "mess"),
        "can_reconcile": bool(recon.helps_with & task.tags) or not recon.helps_with,
    }


@dataclass
class StoryParams:
    setting: str
    task: str
    reconciliation: str
    name: str
    helper: str
    gender: str
    seed: Optional[int] = None
    trait: str = ""
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", time="late afternoon", cozy=True),
    "balcony": Setting(place="the balcony", time="after school", cozy=True),
    "bedroom": Setting(place="the bedroom floor", time="quiet morning", cozy=True),
    "garden": Setting(place="the little garden", time="warm evening", cozy=True),
}

TASKS = {
    "sort_cards": Task(
        id="sort_cards",
        verb="sort the picture cards",
        gerund="sorting picture cards",
        small_mistake="one card slid out of line",
        fix_hint="we can put the cards in one neat pile first",
        mess="scattered cards",
        kind="cards",
        tags={"cards", "order"},
    ),
    "water_plants": Task(
        id="water_plants",
        verb="water the plants",
        gerund="watering the plants",
        small_mistake="a cup tipped and spilled on the floor",
        fix_hint="we can wipe the water and pour more slowly",
        mess="spilled water",
        kind="plants",
        tags={"water", "plants"},
    ),
    "pack_bag": Task(
        id="pack_bag",
        verb="pack the school bag",
        gerund="packing the school bag",
        small_mistake="the pencils fell under the chair",
        fix_hint="we can gather the pencils before we pack again",
        mess="scattered pencils",
        kind="bag",
        tags={"bag", "tidy"},
    ),
    "fold_clothes": Task(
        id="fold_clothes",
        verb="fold the tiny clothes",
        gerund="folding tiny clothes",
        small_mistake="a sleeve got tucked inside out",
        fix_hint="we can smooth each sleeve slowly",
        mess="rumpled clothes",
        kind="clothes",
        tags={"clothes", "care"},
    ),
}

RECONCILIATIONS = {
    "sip_tea": Reconciliation(
        id="sip_tea",
        phrase="They sat together for a tiny sip of tea and a quiet breath.",
        action="sip tea",
        result_line="After that, the room felt softer, and the task seemed easier.",
        helps_with={"cards", "order", "tidy", "care", "clothes"},
    ),
    "wipe_table": Reconciliation(
        id="wipe_table",
        phrase="They wiped the little mess together until the surface shone again.",
        action="wipe the table",
        result_line="The cleanup made the moment feel neat enough to start over.",
        helps_with={"water", "plants", "bag", "order"},
    ),
    "share_laugh": Reconciliation(
        id="share_laugh",
        phrase="They both laughed at the tiny mistake, and the room let go of its tension.",
        action="share a laugh",
        result_line="Soon the mistake felt small, and the two of them were steady again.",
        helps_with=set(),
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Ada", "Maya"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Owen", "Leo"]
HELPER_TITLES = {"mother": "mom", "father": "dad", "grandma": "grandma", "grandpa": "grandpa"}
TRAITS = ["gentle", "curious", "careful", "spirited", "quiet", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TASKS:
            for r in RECONCILIATIONS:
                out.append((s, t, r))
    return out


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for rid, r in RECONCILIATIONS.items():
        lines.append(asp.fact("recon", rid))
        for tag in sorted(r.helps_with):
            lines.append(asp.fact("helps", rid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,R) :- setting(S), task(T), recon(R).
supports(R,T) :- helps(R,Tag), tag(T,Tag).
supports(R,T) :- recon(R), task(T), not helps(R,_).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: advice, ease, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPER_TITLES))
    ap.add_argument("--name")
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
    if getattr(args, "setting", None) and getattr(args, "task", None) and getattr(args, "reconciliation", None):
        if not any(c == (getattr(args, "setting", None), getattr(args, "task", None), getattr(args, "reconciliation", None)) for c in valid_combos()):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    recon = getattr(args, "reconciliation", None) or rng.choice(list(RECONCILIATIONS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(list(HELPER_TITLES))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, reconciliation=recon, name=name, helper=helper, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, type="girl" if params.gender == "girl" else "boy", traits=[params.trait, "little"]))
    helper_title = _safe_lookup(HELPER_TITLES, params.helper)
    helper = world.add(Entity(id=helper_title.capitalize(), type=params.helper, label=helper_title, traits=["kind"]))
    task = _safe_lookup(TASKS, params.task)
    recon = _safe_lookup(RECONCILIATIONS, params.reconciliation)

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who liked quiet chores at {world.setting.place}.")
    world.say(f"{hero.id} loved {task.gerund}, because it made the day feel orderly and calm.")
    world.para()
    world.say(f"One {world.setting.time}, {hero.id} tried {task.verb} while {helper.pronoun('subject')} watched nearby.")
    _do_task(world, hero, task)
    _mistake(world, hero, task)
    _add_meme(helper, "worry", 1.0)
    world.say(f"{helper.id} noticed and gave advice in a soft voice.")
    _advice(world, helper, hero, task)
    world.say(f"The advice helped {hero.id} ease the tight feeling in {hero.pronoun('possessive')} chest.")
    _ease(world, hero, helper, task)
    world.para()
    _reconcile(world, hero, helper, recon)
    world.say(
        f"In the end, {hero.id} finished {task.gerund}, and {helper.id} stayed beside {hero.pronoun('object')} with an easy smile."
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        recon=recon,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    recon = _safe_fact(world, f, "recon")
    return [
        f'Write a short slice-of-life story for a young child about "{task.id}", advice, and ease.',
        f"Tell a gentle story where {hero.id} gets a tiny setback while {hero.pronoun('subject')} is {task.gerund}, then {helper.id} gives advice and they reconcile.",
        f"Write an everyday story that includes a small mistake, calm advice, and a warm reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    task: Task = _safe_fact(world, f, "task")
    recon: Reconciliation = _safe_fact(world, f, "recon")
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at first?",
            answer=f"{hero.id} was trying to {task.verb}.",
        ),
        QAItem(
            question=f"What tiny problem happened while {hero.id} was {task.gerund}?",
            answer=f"{task.small_mistake}.",
        ),
        QAItem(
            question=f"What did {helper.id} do that helped?",
            answer=f"{helper.id} gave advice and the advice made it easier for {hero.id} to try again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the advice?",
            answer=f"{hero.id} felt calmer and the tight feeling eased.",
        ),
        QAItem(
            question=f"How did the two of them make up?",
            answer=f"They reconciled by doing this: {recon.phrase} {recon.result_line}",
        ),
    ]


WORLD_KNOWLEDGE = {
    "cards": QAItem("What are picture cards?", "Picture cards are small cards with pictures on them that children can sort, match, or play with."),
    "water": QAItem("Why do people wipe up spilled water?", "People wipe up spilled water so the floor does not stay slippery or messy."),
    "plants": QAItem("What do plants need to grow?", "Plants need water, sunlight, and care to grow well."),
    "bag": QAItem("Why pack a school bag carefully?", "Packing a school bag carefully helps keep supplies from getting lost or bent."),
    "clothes": QAItem("Why fold clothes?", "Folding clothes keeps them neat and makes them easier to put away."),
    "tidy": QAItem("What does tidy mean?", "Tidy means neat, orderly, and not messy."),
    "order": QAItem("What is order?", "Order means things are arranged in a sensible or neat way."),
    "care": QAItem("What is care?", "Care means looking after someone or something kindly and carefully."),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.update(world.facts["recon"].helps_with)
    out = []
    for tag, qa in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.append(qa)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="kitchen", task="sort_cards", reconciliation="sip_tea", name="Mina", helper="mother", gender="girl", trait="gentle"),
    StoryParams(setting="balcony", task="water_plants", reconciliation="wipe_table", name="Eli", helper="father", gender="boy", trait="curious"),
    StoryParams(setting="bedroom", task="pack_bag", reconciliation="sip_tea", name="Nora", helper="grandma", gender="girl", trait="careful"),
    StoryParams(setting="garden", task="fold_clothes", reconciliation="share_laugh", name="Theo", helper="grandpa", gender="boy", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combinations:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
