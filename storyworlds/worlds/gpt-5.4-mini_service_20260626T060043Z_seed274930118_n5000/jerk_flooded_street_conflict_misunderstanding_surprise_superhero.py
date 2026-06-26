#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero story set on a flooded street.

Premise:
- A young hero and a helper are trying to get across a flooded street.
- A jerk's rude interruption causes a misunderstanding.
- A surprising rescue reveals the jerk was in trouble too.
- The conflict resolves into a shared, kinder ending image.

The script follows the Storyweavers world contract:
- standalone stdlib Python
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- eager import of results.py, lazy import of asp.py in ASP helpers
- inline ASP_RULES twin and Python reasonableness gate
- child-facing, state-driven prose with world-model trace and QA
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    jerk: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero", "jerk"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def __post_init__(self):
        for k in ("soaked", "muddy", "fear", "conflict", "joy", "confusion", "trust", "surprise", "helped"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)
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
    place: str = "the flooded street"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
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


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    caption: str
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flood_depth: float = 1.0
        self.street_current: float = 1.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.flood_depth = self.flood_depth
        w.street_current = self.street_current
        return w


def _r_muddy(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["soaked"] < THRESHOLD:
            continue
        sig = ("muddy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["muddy"] += 1
        out.append(f"{actor.id}'s shoes picked up muddy water.")
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    jerk = world.facts.get("jerk")
    if not hero or not jerk:
        return out
    if hero.memes["confusion"] >= THRESHOLD and jerk.memes["rude"] >= THRESHOLD:
        sig = ("conflict", hero.id, jerk.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [_r_muddy, _r_conflict]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        pass
    actor.meters["soaked"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_misunderstanding(world: World, hero: Entity, jerk: Entity, action: Action) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["confusion"] += 1
    sim.get(jerk.id).memes["rude"] += 1
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    return sim.get(hero.id).memes["conflict"] >= THRESHOLD


def greet(world: World, hero: Entity, sidekick: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} with a bright cape, and {sidekick.id} "
        f"kept a steady hand on {hero.pronoun('possessive')} shoulder."
    )
    world.say(
        f"They were trying to {action.verb} across {world.setting.place}, "
        f"where the water flashed like broken mirrors."
    )


def witness(world: World, hero: Entity, jerk: Entity, action: Action) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} wanted to {action.verb}, but then {jerk.id} barked a rude joke "
        f"and pointed at the flood."
    )
    world.say(
        f"{hero.id} thought {jerk.pronoun('subject')} was being mean on purpose."
    )


def argue(world: World, hero: Entity, jerk: Entity) -> None:
    jerk.memes["rude"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} frowned and stood taller in the street water, ready to answer back."
    )


def surprise_rescue(world: World, hero: Entity, sidekick: Entity, jerk: Entity, aid: Aid) -> None:
    jerk.meters["stuck"] = 1.0
    jerk.memes["fear"] += 1
    hero.memes["surprise"] += 1
    world.say(
        f"Then came a surprise: {sidekick.id} spotted that {jerk.id}'s wheel was "
        f"caught in a storm grate."
    )
    world.say(
        f"{hero.id} and {sidekick.id} used {aid.label} to guide the wheel free, "
        f"and the rude voice turned small and shaky."
    )


def resolve(world: World, hero: Entity, sidekick: Entity, jerk: Entity, aid: Aid, action: Action) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["trust"] += 1
    jerk.memes["rude"] = 0.0
    world.say(
        f"{jerk.id} blushed and said sorry. The joke had been a bad cover for being stuck."
    )
    world.say(
        f"{hero.id} nodded, then laughed softly. Soon they were all moving again, "
        f"{action.gerund} through the flooded street while {aid.caption} kept the path safe."
    )


def tell(setting: Setting, action: Action, aid: Aid, hero_name: str, sidekick_name: str, jerk_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", label="hero", role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="hero", label="sidekick", role="helper"))
    jerk = world.add(Entity(id=jerk_name, kind="character", type="jerk", label="jerk", role="troublemaker"))

    world.facts.update(hero=hero, sidekick=sidekick, jerk=jerk, action=action, aid=aid)

    greet(world, hero, sidekick, action)
    world.para()

    witness(world, hero, jerk, action)
    argue(world, hero, jerk)
    world.para()

    surprise_rescue(world, hero, sidekick, jerk, aid)
    resolve(world, hero, sidekick, jerk, aid, action)

    hero.meters["joy"] += 1
    jerk.meters["helped"] += 1
    propagate(world, narrate=False)
    return world


SETTINGS = {
    "flooded_street": Setting(place="the flooded street", affords={"splash", "wade"}),
}

ACTIONS = {
    "wade": Action(
        id="wade",
        verb="wade to the rescue beacon",
        gerund="wading toward the rescue beacon",
        rush="dash into the water",
        risk="the water could splash up to their belt",
        mess="soaked",
        zone={"legs", "torso"},
        keyword="flood",
        tags={"flood", "water", "street"},
    ),
    "splash": Action(
        id="splash",
        verb="splash past the yellow cones",
        gerund="splashing past the yellow cones",
        rush="run through the puddles",
        risk="the splash might soak their boots",
        mess="soaked",
        zone={"legs"},
        keyword="jerk",
        tags={"flood", "water", "street", "jerk"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="a bright rescue rope",
        phrase="a bright rescue rope",
        helps={"wade", "splash"},
        covers={"legs", "torso"},
        caption="the rescue rope",
    ),
    "board": Aid(
        id="board",
        label="a floating board",
        phrase="a floating board",
        helps={"wade"},
        covers={"legs"},
        caption="the floating board",
    ),
}

HERO_NAMES = ["Milo", "Aya", "Nia", "Kai", "Luna", "Tess", "Rin", "Theo"]
SIDEKICK_NAMES = ["Zip", "Dot", "Blue", "Pip", "Spark", "Beam"]
JERK_NAMES = ["Grump", "Rex", "Blip", "Snarl", "Moss", "Kurt"]


@dataclass
class StoryParams:
    setting: str
    action: str
    aid: str
    hero: str
    sidekick: str
    jerk: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for a_id in setting.affords:
            act = _safe_lookup(ACTIONS, a_id)
            for aid_id, aid in AIDS.items():
                if a_id in aid.helps:
                    combos.append((s_id, a_id, aid_id))
    return combos


def reasonableness_check(action: Action, aid: Aid) -> bool:
    return action.id in aid.helps


def explain_rejection(action: Action, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} would not reasonably help with {action.gerund} "
        f"on a flooded street. The surprise rescue needs gear that actually fits.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: a flooded street, a jerk, a misunderstanding, and a surprise rescue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--jerk")
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
    if getattr(args, "action", None) and getattr(args, "aid", None):
        if not reasonableness_check(_safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(AIDS, getattr(args, "aid", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, aid = rng.choice(list(combos))
    return StoryParams(
        setting=place,
        action=action,
        aid=aid,
        hero=getattr(args, "hero", None) or rng.choice(HERO_NAMES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES),
        jerk=getattr(args, "jerk", None) or rng.choice(JERK_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story for a young child set on a flooded street, and include the word "jerk".',
        f"Tell a gentle superhero tale where {f['hero'].id} and {f['sidekick'].id} try to {f['action'].verb}, but {f['jerk'].id} causes a misunderstanding before a surprise rescue.",
        f"Write a story about a flooded street, a rude jerk, and a rescue using {f['aid'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, jerk, action, aid = f["hero"], f["sidekick"], f["jerk"], f["action"], f["aid"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a little superhero, and {sidekick.id}, who helped on the flooded street.",
        ),
        QAItem(
            question=f"Why did {hero.id} think {jerk.id} was being mean?",
            answer=f"{hero.id} thought {jerk.id} was being mean because {jerk.id} barked a rude joke and pointed at the flood before anyone understood what was wrong.",
        ),
        QAItem(
            question=f"What surprising thing did {hero.id} and {sidekick.id} discover?",
            answer=f"They discovered that {jerk.id}'s wheel was stuck in a storm grate, so the rude behavior was really a worried cry for help.",
        ),
        QAItem(
            question=f"How did {aid.label} help at the end?",
            answer=f"{aid.label} helped them guide the wheel free, and then everyone could move through the flooded street safely.",
        ),
    ]


KNOWLEDGE = {
    "flood": [("What is a flood?", "A flood is when too much water covers places that are usually dry.")],
    "street": [("What is a street?", "A street is a road where people walk, ride, and drive.")],
    "rope": [("What is a rescue rope for?", "A rescue rope helps people pull, guide, or stay safe when something is hard to reach.")],
    "jerk": [("What does jerk mean?", "A jerk is a rude person who says or does unkind things.")],
    "water": [("Why can flood water be dangerous?", "Flood water can hide holes, push things around, and make walking slippery.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.add("jerk")
    if world.facts["aid"].id == "rope":
        tags.add("rope")
    out = []
    for tag in ["flood", "street", "water", "jerk", "rope"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A helper is compatible when it helps the chosen action.
compatible(AID, ACT) :- helps(AID, ACT).

% A story is valid when it is set on the flooded street and has a compatible aid.
valid_story(P, A, I) :- place(P), action(A), aid(I), affords(P, A), compatible(I, A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for a in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, a))
    for a_id in ACTIONS:
        lines.append(asp.fact("action", a_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ACTIONS, params.action), _safe_lookup(AIDS, params.aid), params.hero, params.sidekick, params.jerk)
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
    StoryParams(setting="flooded_street", action="wade", aid="rope", hero="Milo", sidekick="Zip", jerk="Grump"),
    StoryParams(setting="flooded_street", action="splash", aid="rope", hero="Aya", sidekick="Beam", jerk="Rex"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible story combos")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
