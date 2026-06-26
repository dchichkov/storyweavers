#!/usr/bin/env python3
"""
storyworlds/worlds/animator_pop_basement_stairs_foreshadowing_repetition_tall.py
=================================================================================

A small standalone Storyweavers world for a tall-tale basement-stairs story
with foreshadowing and repetition.

Premise:
- An animator child loves making a tiny pop-up show in the basement stairwell.
- A loose step and a pop-open prop box make trouble.
- Repeated warning phrases and an early foreshadowed creak lead to a safer plan.

The world model keeps:
- physical meters: wobble, noise, dust, brightness, dropped_items
- emotional memes: joy, worry, pride, patience, surprise, attachment

The story is authored from state changes rather than a frozen template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prop: object | None = None
    stairs: object | None = None
    def __post_init__(self) -> None:
        for k in ("wobble", "noise", "dust", "brightness", "dropped_items", "care"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "pride", "patience", "surprise", "attachment", "fear"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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


@dataclass
class Setting:
    place: str = "the basement stairs"
    affords: set[str] = field(default_factory=lambda: {"animate", "pop", "show"})
    world: object | None = None
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
class Prop:
    id: str
    label: str
    phrase: str
    mess: str
    trigger: str
    risk_region: str
    fix: str
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
    prop: str = "jack-in-the-box"
    name: str = "Milo"
    gender: str = "boy"
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _say_repetition(prefix: str, line: str) -> str:
    return f"{prefix} {line} {line.lower()}"


def _tick(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    prop = world.get("prop")
    stairs = world.get("stairs")
    if child.meters["wobble"] >= THRESHOLD and ("wobble",) not in world.fired:
        world.fired.add(("wobble",))
        stairs.meters["noise"] += 1
        child.memes["worry"] += 1
        out.append("The stairs gave a long little creak, like they were clearing their throat before trouble.")
    if prop.meters["noise"] >= THRESHOLD and ("pop", prop.id) not in world.fired:
        world.fired.add(("pop", prop.id))
        child.memes["surprise"] += 1
        out.append(f"There came a sharp {prop.trigger}, and the little show jumped higher than a kite in a windstorm.")
    if prop.meters["dust"] >= THRESHOLD and ("dust", prop.id) not in world.fired:
        world.fired.add(("dust", prop.id))
        child.meters["brightness"] += 1
        out.append("A thin ribbon of dust floated in the beam of light, making the stairwell look like a silver cave.")
    if child.memes["worry"] >= THRESHOLD and child.memes["patience"] >= THRESHOLD and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        out.append("Then the worry softened, because patience has a way of smoothing even a bumpy stair.")
    return out


def foreshadow(world: World) -> None:
    child = world.get("child")
    stairs = world.get("stairs")
    child.memes["surprise"] += 0.5
    stairs.meters["noise"] += 0.5
    world.say(
        "Before anybody climbed a step, the basement stairs already whispered a warning: "
        "one board liked to creak, and when that board creaked, it usually meant a pop, "
        "a hop, and a tumble of tiny things."
    )


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who worked as an animator, which meant "
        f"{hero.pronoun('subject')} could make still things seem to dance."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.pronoun('subject')} knew that when {hero.id} said "
        f'"just one more pop," there would likely be three more after that.'
    )


def love_show(world: World, hero: Entity, prop: Entity) -> None:
    hero.memes["attachment"] += 1
    world.say(
        f"{hero.id} loved the little pop show. {hero.pronoun('subject').capitalize()} liked to tap, tap, tap the prop "
        f"and watch it spring open like a surprise sunflower."
    )


def begin_play(world: World, hero: Entity, prop: Entity) -> None:
    hero.meters["brightness"] += 1
    prop.meters["noise"] += 1
    prop.meters["dust"] += 1
    world.say(
        f"Down on the basement stairs, {hero.id} set up {hero.pronoun('possessive')} animation show."
    )
    world.say(
        f"{hero.id} tapped the prop once, and then again, and then again, because in a tall tale a good pop "
        f"is worth repeating."
    )
    for sent in _tick(world):
        world.say(sent)


def warn(world: World, parent: Entity, hero: Entity, prop: Entity) -> None:
    parent.memes["worry"] += 1
    world.say(
        f'"Careful," said {parent.id}, "careful, careful, careful. Those basement stairs are steep, and a pop can become a slip."'
    )
    world.say(
        f'{parent.id} pointed at the wobbly step below, the one that had been foreshadowing trouble all afternoon.'
    )


def attempt(world: World, hero: Entity, prop: Entity) -> None:
    hero.meters["wobble"] += 1
    prop.meters["noise"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} tried one more grand trick anyway. {hero.pronoun('subject').capitalize()} made the prop pop, then pop, then pop again."
    )
    world.say(
        f"The little animator grinned, but the stairs answered with a creak so loud it sounded like an old drum saying, 'Not so fast.'"
    )
    for sent in _tick(world):
        world.say(sent)


def pivot(world: World, hero: Entity, parent: Entity, prop: Entity) -> None:
    hero.memes["patience"] += 1
    parent.memes["pride"] += 1
    prop.meters["noise"] = 0
    world.say(
        f"Then {hero.id} remembered the warning, and remembered it twice, and remembered it a third time."
    )
    world.say(
        f'{hero.id} said, "I can make the pop without making the trouble," and {parent.id} smiled as if {hero.id} had just caught a moonbeam in a jar.'
    )


def resolution(world: World, hero: Entity, parent: Entity, prop: Entity) -> None:
    hero.memes["joy"] += 1
    parent.memes["pride"] += 1
    stairs = world.get("stairs")
    stairs.meters["noise"] = max(0.0, stairs.meters["noise"] - 0.5)
    world.say(
        f"So {hero.id} moved the show to the middle landing, where the step was steady and the light was kind."
    )
    world.say(
        f"There {hero.id} made the prop pop one last time, and this time the pop stayed a happy pop, not a tumble-pop."
    )
    world.say(
        f"In the end, the basement stairs were quiet, the old warning had proved true, and the little animator had turned caution into a better trick."
    )


def tell(hero_name: str, gender: str, parent_type: str, prop_key: str) -> World:
    props = PROPS
    prop_cfg = props[prop_key]
    world = World(Setting())
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    stairs = world.add(Entity(id="stairs", kind="thing", type="stairs", label="the basement stairs"))
    prop = world.add(Entity(id="prop", kind="thing", type="prop", label=prop_cfg.label, phrase=prop_cfg.phrase))
    world.facts = {
        "hero": hero,
        "parent": parent,
        "stairs": stairs,
        "prop": prop,
        "prop_cfg": prop_cfg,
        "setting": world.setting,
    }

    introduce(world, hero, parent)
    world.para()
    foreshadow(world)
    love_show(world, hero, prop)
    begin_play(world, hero, prop)
    world.para()
    warn(world, parent, hero, prop)
    attempt(world, hero, prop)
    pivot(world, hero, parent, prop)
    world.para()
    resolution(world, hero, parent, prop)
    return world


PROPS: dict[str, Prop] = {
    "jack-in-the-box": Prop(
        id="jack-in-the-box",
        label="a jack-in-the-box",
        phrase="a painted spring box that loved to pop",
        mess="noise",
        trigger="pop!",
        risk_region="stairs",
        fix="the middle landing",
    ),
    "paper-goat": Prop(
        id="paper-goat",
        label="a paper goat",
        phrase="a folded paper goat with a brave grin",
        mess="dust",
        trigger="pop!",
        risk_region="stairs",
        fix="the middle landing",
    ),
    "tin-soldier": Prop(
        id="tin-soldier",
        label="a tin soldier",
        phrase="a shiny tin soldier that clicked and popped on its tiny spring",
        mess="noise",
        trigger="clack-pop!",
        risk_region="stairs",
        fix="the middle landing",
    ),
}

GENDERS = ["boy", "girl"]
NAMES = ["Milo", "June", "Pia", "Otis", "Nia", "Theo", "Luna", "Ezra"]
PARENTS = ["mother", "father"]
CURATED = [
    StoryParams(prop="jack-in-the-box", name="Milo", gender="boy", parent="mother"),
    StoryParams(prop="paper-goat", name="June", gender="girl", parent="father"),
    StoryParams(prop="tin-soldier", name="Theo", gender="boy", parent="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale basement stairs story with foreshadowing and repetition.")
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    if not name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(prop=prop, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prop_cfg = _safe_fact(world, f, "prop_cfg")
    return [
        f'Write a tall tale about an animator named {hero.id} on the basement stairs, where a "pop" keeps coming back.',
        f"Tell a child-friendly story where {hero.id} tries to animate {prop_cfg.label} in the basement stairs and learns from a warning.",
        f'Write a short story that uses repetition, foreshadowing, and the word "pop" in a basement-stairs adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prop = _safe_fact(world, f, "prop")
    prop_cfg = _safe_fact(world, f, "prop_cfg")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little animator who loved making {prop_cfg.label} pop on the basement stairs.",
        ),
        QAItem(
            question=f"What warning did {parent.id} give about the stairs?",
            answer=f"{parent.id} warned that the basement stairs were steep and that a pop could turn into a slip.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem in the end?",
            answer=f"{hero.id} moved the show to the middle landing so {prop.label} could pop safely without making trouble.",
        ),
        QAItem(
            question=f"What repeated word or sound carried through the story?",
            answer="The story kept repeating the pop sound, along with the warning to be careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a basement?",
            answer="A basement is a room or level below the main part of a house, often under the floor.",
        ),
        QAItem(
            question="What does an animator do?",
            answer="An animator makes still things seem to move by planning or showing motion step by step.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something may happen later.",
        ),
        QAItem(
            question="Why can repetition help a story?",
            answer="Repetition can make a story feel musical, funny, or important because the same word or idea comes back again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(basement_stairs).
affords(basement_stairs, animate).
affords(basement_stairs, pop).
affords(basement_stairs, show).

prize_at_risk(A) :- affects(A, stairs).
valid_story(basement_stairs, A, P) :- affords(basement_stairs, A), prop(P), prop_risky(P), focuses_on(P, A).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "basement_stairs")]
    for a in ["animate", "pop", "show"]:
        lines.append(asp.fact("affords", "basement_stairs", a))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("prop_risky", pid))
        lines.append(asp.fact("focuses_on", pid, "pop"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("basement_stairs", "animate", pid) for pid in PROPS} | {("basement_stairs", "pop", pid) for pid in PROPS} | {("basement_stairs", "show", pid) for pid in PROPS}
    if atoms == expected:
        print(f"OK: ASP gate matches Python registry ({len(atoms)} facts).")
        return 0
    print("Mismatch between ASP and Python.")
    print("asp:", sorted(atoms))
    print("py :", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.prop)
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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
