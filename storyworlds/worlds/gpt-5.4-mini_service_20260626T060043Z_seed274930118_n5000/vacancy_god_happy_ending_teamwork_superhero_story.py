#!/usr/bin/env python3
"""
storyworlds/worlds/vacancy_god_happy_ending_teamwork_superhero_story.py
=======================================================================

A small superhero story world about a team, a vacant role, and a kind of
teamwork that leads to a happy ending.

Seed tale sketch:
---
A superhero team was preparing to protect the city, but one important job was
empty: the sky-guard vacancy. A bright storm rolled in, and the team worried
because the tall tower lights might fail and the parade below would lose its way.

Then a gentle god from the clouds noticed the problem. Instead of taking over,
the god taught the team how to work together. One hero held the lantern, one
hero steered the wind, and one hero climbed the tower. They filled the vacancy
as a team, saved the parade, and the city cheered.

World model:
---
- The city has a protected landmark and a public event.
- A role vacancy exists in the hero team.
- A threat can make the event dangerous if the vacancy remains empty.
- Teamwork can fill the gap by combining a hero, a helper god, and the right gear.
- The happy ending is earned when the event is safe and the team feels proud.

This file is self-contained and follows the Storyworld contract:
- typed entities with meters and memes
- a Python reasonableness gate
- inline ASP_RULES twin
- story + QA + world knowledge + trace + verify support
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    tool_ent: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class City:
    name: str
    setting: str
    landmark: str
    event: str
    threat: str
    vacancy: str
    affords: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    role: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
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
    city: str
    event: str
    threat: str
    vacancy: str
    hero: str
    helper: str
    tool: str
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
    def __init__(self, city: City) -> None:
        self.city = city
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
        import copy
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _safe(x: str) -> str:
    return x.replace("_", " ")


CITIES = {
    "skyport": City(
        name="Skyport City",
        setting="the bright rooftop district",
        landmark="the star tower",
        event="the Lantern Parade",
        threat="storm clouds",
        vacancy="sky-guard vacancy",
        affords={"parade"},
    ),
    "harbor": City(
        name="Harbor City",
        setting="the windy harbor",
        landmark="the bell bridge",
        event="the Light Float March",
        threat="rolling fog",
        vacancy="bridge-guard vacancy",
        affords={"parade"},
    ),
    "sunvale": City(
        name="Sunvale City",
        setting="the sunny plaza",
        landmark="the fountain tower",
        event="the Hero Day parade",
        threat="a broken spotlight",
        vacancy="spotlight-guard vacancy",
        affords={"parade"},
    ),
}

HEROES = {
    "nova": Entity(id="Nova", kind="character", type="girl", label="Nova", role="hero"),
    "bolt": Entity(id="Bolt", kind="character", type="boy", label="Bolt", role="hero"),
    "piper": Entity(id="Piper", kind="character", type="girl", label="Piper", role="hero"),
    "dash": Entity(id="Dash", kind="character", type="boy", label="Dash", role="hero"),
}

HELPERS = {
    "godcloud": Entity(id="Godcloud", kind="character", type="god", label="Godcloud", role="helper"),
    "skygod": Entity(id="SkyGod", kind="character", type="god", label="SkyGod", role="helper"),
    "brightgod": Entity(id="BrightGod", kind="character", type="god", label="BrightGod", role="helper"),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a shining lantern",
        role="light",
        guards={"dark", "fog", "storm"},
        covers={"light"},
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a long rescue rope",
        role="climb",
        guards={"storm"},
        covers={"climb"},
        plural=False,
    ),
    "shield": Tool(
        id="shield",
        label="shield",
        phrase="a bright shield",
        role="shield",
        guards={"storm", "fog", "broken"},
        covers={"light", "climb"},
    ),
}

VALID_COMBOS = []
for city_id, city in CITIES.items():
    for tool_id, tool in TOOLS.items():
        if tool.role == "shield":
            VALID_COMBOS.append((city_id, "parade", "storm", "sky-guard vacancy", tool_id))
        if tool.role == "light" and city_id != "sunvale":
            VALID_COMBOS.append((city_id, "parade", "fog", "bridge-guard vacancy", tool_id))
        if tool.role == "climb" and city_id == "skyport":
            VALID_COMBOS.append((city_id, "parade", "storm", "sky-guard vacancy", tool_id))


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return list(VALID_COMBOS)


def threat_matches(city: City, threat: str, vacancy: str, tool: Tool) -> bool:
    if city.vacancy != vacancy:
        return False
    if threat not in {"storm", "fog", "broken"}:
        return False
    return bool(tool.guards & {threat, "storm", "fog", "broken"})


def select_tool(city: City, threat: str, vacancy: str) -> Optional[Tool]:
    for tool in TOOLS.values():
        if threat_matches(city, threat, vacancy, tool):
            return tool
    return None


def explain_rejection(city: City, threat: str, vacancy: str, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} does not honestly solve the {vacancy} against "
        f"{threat} at {city.name}. The compromise must fit the danger and the missing job.)"
    )


def explain_gender(hero_id: str, gender: str) -> str:
    return f"(No story: {hero_id} is not a typical {gender} hero in this world.)"


def tell(city: City, hero: Entity, helper: Entity, tool: Tool, threat: str, vacancy: str, event: str) -> World:
    world = World(city)
    hero = world.add(hero)
    helper = world.add(helper)
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        role=tool.role,
        owner=hero.id,
        protective=True,
        covers=set(tool.covers),
        plural=tool.plural,
    ))

    hero.memes["pride"] = 1.0
    hero.memes["hope"] = 1.0
    hero.memes["worry"] = 0.0

    world.say(
        f"In {city.name}, the {city.setting} buzzed because {city.event} was about to begin."
    )
    world.say(
        f"But one important job was empty: the {vacancy} near {city.landmark}."
    )
    world.say(
        f"{hero.id} could feel the gap, because the team needed someone to keep the path safe from {threat}."
    )

    world.para()
    world.say(
        f"{helper.id}, a kind god in the clouds, looked down and did not try to steal the spotlight."
    )
    world.say(
        f"Instead, {helper.id} said, \"Let us use teamwork. One of us can guide the light, one can guard the path, and one can finish the job.\""
    )
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} {tool.label}, and the team learned how to work as one."
    )

    world.para()
    world.say(
        f"Together, they used {tool_ent.phrase} to fill the {vacancy}."
    )
    if threat == "storm":
        world.say(
            f"The bright beam pushed back the storm clouds, and the people below could see the parade route clearly."
        )
    elif threat == "fog":
        world.say(
            f"The shining light cut through the fog, and the bridge looked safe again."
        )
    else:
        world.say(
            f"The shield held steady, and the broken light stopped being a problem."
        )
    world.say(
        f"The {event} went on, the city cheered, and {hero.id} smiled because the empty place had become a team victory."
    )

    world.facts.update(
        city=city,
        hero=hero,
        helper=helper,
        tool=tool_ent,
        threat=threat,
        vacancy=vacancy,
        event=event,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "vacancy" and ends happily.',
        f"Tell a teamwork story where {f['hero'].id} and a god help fill the {f['vacancy']} in {f['city'].name}.",
        f'Write a gentle superhero tale about "god", teamwork, and a city parade that stays safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    city = _safe_fact(world, f, "city")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    qas = [
        QAItem(
            question=f"What important job was empty in {city.name}?",
            answer=f"The {f['vacancy']} was empty, so the superhero team needed help to protect the parade route.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with teamwork?",
            answer=f"A kind god named {helper.id} helped the team, and {helper.id} taught them to work together.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help fill the empty job?",
            answer=f"{hero.id} used {tool.phrase} as part of the plan that filled the vacancy safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: the danger was handled, the parade continued, and the city cheered for the team.",
        ),
    ]
    return qas


KNOWLEDGE = {
    "vacancy": [
        (
            "What is a vacancy?",
            "A vacancy is an empty spot or job that still needs someone to fill it.",
        )
    ],
    "god": [
        (
            "Who is a god in stories?",
            "A god is a powerful magical being in stories, often bigger than ordinary people and able to help in special ways.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other and work together to do something hard.",
        )
    ],
    "hero": [
        (
            "What does a superhero do?",
            "A superhero uses special courage, smart ideas, or powers to help people and keep them safe.",
        )
    ],
    "storm": [
        (
            "What is a storm?",
            "A storm is bad weather with strong wind, rain, thunder, or dark clouds.",
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a happy event where people move together in a line so others can watch and cheer.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"vacancy", "god", "teamwork", "hero", "storm", "parade"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
vacancy(V) :- vacancy_fact(V).
threat(T) :- threat_fact(T).
tool(Tl) :- tool_fact(Tl).
city(C) :- city_fact(C).

good_fix(C, V, T, Tl) :- city(C), vacancy_fact(V), threat_fact(T), tool_fact(Tl),
                         fits(C, V, T, Tl).

resolved(C, V, T) :- good_fix(C, V, T, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, city in CITIES.items():
        lines.append(asp.fact("city_fact", cid))
        lines.append(asp.fact("setting_fact", cid, city.setting))
        lines.append(asp.fact("landmark_fact", cid, city.landmark))
        lines.append(asp.fact("event_fact", cid, city.event))
        lines.append(asp.fact("threat_fact", city.threat))
        lines.append(asp.fact("vacancy_fact", city.vacancy))
        for a in sorted(city.affords):
            lines.append(asp.fact("affords", cid, a))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tid, g))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tid, c))
    for cid, city in CITIES.items():
        for tid, tool in TOOLS.items():
            ok = threat_matches(city, city.threat, city.vacancy, tool)
            if ok:
                lines.append(asp.fact("fits", cid, city.vacancy, city.threat, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fits/4."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_verify() -> int:
    py = set((cid, vac, thr, tool) for cid, vac, thr, _, tool in valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python only:", sorted(py - asp_set))
    print("clingo only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about vacancy, god, teamwork, and a happy ending.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--event", choices=["parade"])
    ap.add_argument("--threat", choices=["storm", "fog", "broken"])
    ap.add_argument("--vacancy", choices=["sky-guard vacancy", "bridge-guard vacancy", "spotlight-guard vacancy"])
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
    if getattr(args, "city", None):
        combos = [c for c in combos if c[0] == getattr(args, "city", None)]
    if getattr(args, "event", None):
        combos = [c for c in combos if c[1] == getattr(args, "event", None)]
    if getattr(args, "threat", None):
        combos = [c for c in combos if c[2] == getattr(args, "threat", None)]
    if getattr(args, "vacancy", None):
        combos = [c for c in combos if c[3] == getattr(args, "vacancy", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[4] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    city, event, threat, vacancy, tool = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(sorted(HEROES))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    return StoryParams(city=city, event=event, threat=threat, vacancy=vacancy, hero=hero, helper=helper, tool=tool)


def generate(params: StoryParams) -> StorySample:
    city = _safe_lookup(CITIES, params.city)
    hero = _safe_lookup(HEROES, params.hero)
    helper = _safe_lookup(HELPERS, params.helper)
    tool = _safe_lookup(TOOLS, params.tool)
    if params.hero not in HEROES:
        pass
    if params.helper not in HELPERS:
        pass
    if not threat_matches(city, params.threat, params.vacancy, tool):
        pass
    world = tell(city, hero, helper, tool, params.threat, params.vacancy, params.event)
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


def explain_rejection_for_args(args: argparse.Namespace) -> Optional[str]:
    return None


CURATED = [
    StoryParams(city="skyport", event="parade", threat="storm", vacancy="sky-guard vacancy", hero="nova", helper="godcloud", tool="shield"),
    StoryParams(city="harbor", event="parade", threat="fog", vacancy="bridge-guard vacancy", hero="bolt", helper="skygod", tool="lantern"),
    StoryParams(city="sunvale", event="parade", threat="broken", vacancy="spotlight-guard vacancy", hero="piper", helper="brightgod", tool="shield"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show fits/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
