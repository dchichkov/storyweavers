#!/usr/bin/env python3
"""
A tiny story world about a puppet theater adventure where a diverse cast solves
a live performance problem together.

The simulated premise:
- A puppet show is about to begin in a cozy theater.
- A needed prop goes missing, or a scene mechanism jams.
- The puppeteers and puppets work together, using clues, tools, and teamwork.
- The ending proves the stage is ready and the show becomes a small triumph.

This world is designed to support child-facing, state-driven stories with
clear setup, tension, turn, and resolution.
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

THEATER_NAME = "the puppet theater"



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
class Puppet:
    id: str
    name: str
    kind: str
    role: str
    age_group: str
    pronoun_subj: str
    pronoun_obj: str
    pronoun_poss: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def sub(self) -> str:
        return self.pronoun_subj

    def obj(self) -> str:
        return self.pronoun_obj

    def poss(self) -> str:
        return self.pronoun_poss
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
class Prop:
    id: str
    name: str
    type: str
    condition: str
    owner: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    prop: object | None = None
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
class Stage:
    place: str
    audience_waiting: bool = True
    curtain_open: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    stage: object | None = None
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
        return None


@dataclass
class StoryParams:
    performer: str
    helper: str
    puppet_kind: str
    problem: str
    prop: str
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


class World:
    def __init__(self, stage: Stage):
        self.stage = stage
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, obj):
        self.entities[getattr(obj, "id")] = obj
        return obj

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PUPPET_TYPES = {
    "fox": ("fox", "adventurous", "he", "him", "his"),
    "rabbit": ("rabbit", "quick", "she", "her", "her"),
    "bear": ("bear", "brave", "they", "them", "their"),
    "owl": ("owl", "wise", "she", "her", "her"),
    "cat": ("cat", "curious", "he", "him", "his"),
    "dog": ("dog", "loyal", "they", "them", "their"),
}

PROBLEMS = {
    "stuck_curtain": {
        "label": "a stuck curtain rope",
        "verb": "pulling the curtain rope",
        "clue": "the rope had tangled behind a stage peg",
        "fix": "untangle the rope and grease the pulley",
        "result": "the curtain slid open with a smooth whoosh",
        "risk": "the show could not start",
    },
    "missing_hat": {
        "label": "the missing explorer hat",
        "verb": "finding the explorer hat",
        "clue": "the hat had rolled into a prop basket",
        "fix": "search the basket and pass the hat back onstage",
        "result": "the explorer puppet looked ready for adventure again",
        "risk": "the adventure scene would feel unfinished",
    },
    "broken_lantern": {
        "label": "a broken lantern",
        "verb": "fixing the lantern light",
        "clue": "one candle clip had slipped loose",
        "fix": "clip the candle back and steady the frame",
        "result": "the lantern glowed warm and golden",
        "risk": "the cave scene would stay dark",
    },
    "lost_map": {
        "label": "the lost treasure map",
        "verb": "finding the treasure map",
        "clue": "the map had been tucked under a drum",
        "fix": "lift the drum, recover the map, and flatten its corners",
        "result": "the treasure hunt could begin at last",
        "risk": "the adventure would lose its trail",
    },
}

PROPS = {
    "map": "a folded treasure map",
    "rope": "a thick curtain rope",
    "hat": "an explorer hat with a bright feather",
    "lantern": "a little lantern prop with a painted flame",
}

AGE_GROUPS = ["child", "teen", "adult"]
NAMES = ["Mina", "Jules", "Tari", "Noor", "Ivy", "Sam", "Paz", "Levi", "Asha", "Ren"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A puppet theater problem-solving adventure.")
    ap.add_argument("--performer", choices=["child", "teen", "adult"])
    ap.add_argument("--helper", choices=["child", "teen", "adult"])
    ap.add_argument("--puppet-kind", choices=sorted(PUPPET_TYPES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--prop", choices=sorted(PROPS))
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


def _valid_combo(problem: str, prop: str) -> bool:
    return (problem == "stuck_curtain" and prop == "rope") or \
           (problem == "missing_hat" and prop == "hat") or \
           (problem == "broken_lantern" and prop == "lantern") or \
           (problem == "lost_map" and prop == "map")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "prop", None) and not _valid_combo(getattr(args, "problem", None), getattr(args, "prop", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    problem = getattr(args, "problem", None) or rng.choice(sorted(PROBLEMS))
    if getattr(args, "prop", None):
        prop = getattr(args, "prop", None)
    else:
        choices = [p for p in PROPS if _valid_combo(problem, p)]
        prop = rng.choice(choices)
    performer = getattr(args, "performer", None) or rng.choice(AGE_GROUPS)
    helper = getattr(args, "helper", None) or rng.choice(AGE_GROUPS)
    puppet_kind = getattr(args, "puppet_kind", None) or rng.choice(sorted(PUPPET_TYPES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(performer=performer, helper=helper, puppet_kind=puppet_kind,
                       problem=problem, prop=prop)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = narrate(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def _make_puppet(pid: str, name: str, kind: str, role: str, age: str) -> Puppet:
    _, trait, sub, obj, poss = _safe_lookup(PUPPET_TYPES, kind)
    return Puppet(
        id=pid,
        name=name,
        kind=kind,
        role=role,
        age_group=age,
        pronoun_subj=sub,
        pronoun_obj=obj,
        pronoun_poss=poss,
        meters={"courage": 1.0 if role == "lead" else 0.5},
        memes={"hope": 1.0, "wonder": 1.0},
    )


def build_world(params: StoryParams) -> World:
    stage = Stage(place=THEATER_NAME)
    world = World(stage)

    kind = params.puppet_kind
    pkind, trait, sub, obj, poss = _safe_lookup(PUPPET_TYPES, kind)

    lead = world.add(_make_puppet("lead", params.name, kind, "lead", params.performer))
    helper_name = next(n for n in NAMES if n != params.name)
    helper = world.add(_make_puppet("helper", helper_name, "owl" if kind != "owl" else "bear", "helper", params.helper))
    prop = world.add(Prop(id="prop", name=_safe_lookup(PROPS, params.prop), type=params.prop,
                          condition="missing", owner=lead.id))
    world.facts.update(
        lead=lead,
        helper=helper,
        prop=prop,
        problem=params.problem,
        problem_data=_safe_lookup(PROBLEMS, params.problem),
        puppet_kind=kind,
        puppet_trait=trait,
    )
    return world


def narrate(world: World) -> str:
    lead: Puppet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lead")
    helper: Puppet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    prop: Prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prop")
    problem = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "problem")
    pdata = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "problem_data")
    trait = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "puppet_trait")

    world.say(
        f"At {world.stage.place}, {lead.name} was a {lead.age_group} puppet with a {trait} spark, "
        f"and {helper.name} was ready to help backstage."
    )
    world.say(
        f"Tonight's show was an adventure, but the crew faced {pdata['label']}; "
        f"{pdata['risk']}."
    )
    world.para()
    world.say(
        f"{lead.name} noticed the trouble first because the stage had gone quiet and the audience was waiting. "
        f"{pdata['clue']}."
    )
    world.say(
        f"{helper.name} pointed to the prop table and said they could solve it together by {pdata['fix']}."
    )
    world.para()
    if problem == "stuck_curtain":
        world.stage.meters["jam"] = 0.0
        world.stage.curtain_open = True
        prop.condition = "ready"
        world.say(
            f"They worked carefully: {helper.name} guided the rope while {lead.name} untied the knot. "
            f"Then {pdata['result']}."
        )
    elif problem == "missing_hat":
        prop.condition = "found"
        world.say(
            f"They searched every basket until {lead.name} spotted the hat under a scarf. "
            f"{helper.name} dusted it off and passed it back, and {pdata['result']}."
        )
    elif problem == "broken_lantern":
        prop.condition = "fixed"
        world.say(
            f"{helper.name} steadied the frame while {lead.name} clipped the candle back into place. "
            f"At once, {pdata['result']}."
        )
    else:
        prop.condition = "found"
        world.say(
            f"{lead.name} lifted the drum, {helper.name} flattened the map, and the torn edge turned neat again. "
            f"At last, {pdata['result']}."
        )

    world.say(
        f"The audience clapped as the puppets stepped into the next scene, and the little theater felt brave again."
    )
    return world.render()


def generation_prompts(world: World) -> list[str]:
    lead = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lead")
    pdata = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "problem_data")
    return [
        f"Write a short adventure story about {lead.name} at {THEATER_NAME} where a problem must be solved before the show begins.",
        f"Tell a child-friendly story in which a puppet theater crew notices {pdata['label']} and finds a clever fix together.",
        f"Make a small stage adventure with teamwork, a missing or broken prop, and a happy performance ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    lead: Puppet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lead")
    helper: Puppet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    prop: Prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prop")
    pdata = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "problem_data")
    return [
        QAItem(
            question=f"Who was the story about in the puppet theater?",
            answer=f"The story was about {lead.name}, a {lead.age_group} puppet, and {helper.name}, who helped solve the stage problem.",
        ),
        QAItem(
            question=f"What problem had to be solved before the show could go on?",
            answer=f"They had to deal with {pdata['label']} so the adventure show could continue.",
        ),
        QAItem(
            question=f"What prop helped them fix the problem?",
            answer=f"They used {prop.name} to help solve the problem, and after that the stage was ready again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem fixed and the audience clapping while the puppets got ready for the next scene.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a place where puppets are moved and acted out in a show for an audience.",
        ),
        QAItem(
            question="Why do performers solve problems before a show starts?",
            answer="They solve problems before a show starts so the audience can watch the story without the stage getting stuck or broken.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What can a prop do in a play?",
            answer="A prop is an object used in the story, like a hat, map, rope, or lantern, to help the scene feel real.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for eid, ent in world.entities.items():
        if isinstance(ent, Puppet):
            lines.append(f"{eid}: puppet {ent.name} ({ent.age_group}, {ent.kind})")
        else:
            lines.append(f"{eid}: prop {ent.name} [{ent.condition}]")
    lines.append(f"stage_open={world.stage.curtain_open}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("problem", *PROBLEMS.keys()),
        asp.fact("prop", *PROPS.keys()),
    ]
    for problem, pdata in PROBLEMS.items():
        lines.append(asp.fact("needs", problem, list(PROPS.keys())[list(PROBLEMS.keys()).index(problem)]))
    for prop in PROPS:
        lines.append(asp.fact("available_prop", prop))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Prop) :- problem(P), available_prop(Prop), needs(P, Prop).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, prop) for p in PROBLEMS for prop in PROPS if _valid_combo(p, prop))
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid pairs).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_params_list(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if getattr(args, "all", None):
        out = []
        for p in PROBLEMS:
            for prop in PROPS:
                if _valid_combo(p, prop):
                    out.append(StoryParams(
                        performer=rng.choice(AGE_GROUPS),
                        helper=rng.choice(AGE_GROUPS),
                        puppet_kind=rng.choice(sorted(PUPPET_TYPES)),
                        problem=p,
                        prop=prop,
                        seed=getattr(args, "seed", None),
                    ))
        return out
    return [resolve_params(args, rng) for _ in range(getattr(args, "n", None))]


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{p} -> {prop}" for p, prop in asp_valid()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    if getattr(args, "all", None):
        params_list = build_params_list(args, rng)
    else:
        params_list = []
        seen = set()
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            key = (p.performer, p.helper, p.puppet_kind, p.problem, p.prop)
            if key in seen:
                continue
            seen.add(key)
            params_list.append(p)

    samples = [generate(p) for p in params_list]
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
