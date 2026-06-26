#!/usr/bin/env python3
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
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mate: object | None = None
    tool: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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


@dataclass
class Harbor:
    place: str = "the small harbor"
    tide: str = "calm"
    risk: str = "rocks"
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
class Treasure:
    label: str
    phrase: str
    spoil_kind: str
    spoil_word: str
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
class Tool:
    id: str
    label: str
    prep: str
    protects: set[str] = field(default_factory=set)
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
class World:
    harbor: Harbor
    entity: Entity
    mate: Entity
    treasure: Entity
    tool: Optional[Entity] = None
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
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


HARBOURS = {
    "harbor": Harbor(place="the small harbor", tide="calm", risk="rocks"),
    "cove": Harbor(place="the windy cove", tide="rough", risk="reef"),
    "island": Harbor(place="the palm island dock", tide="low", risk="sandbars"),
}

TREASURES = {
    "prosciutto": Treasure(
        label="prosciutto",
        phrase="a paper-wrapped bundle of prosciutto",
        spoil_kind="salt",
        spoil_word="ruined",
    ),
    "map": Treasure(
        label="map",
        phrase="a rolled-up treasure map",
        spoil_kind="water",
        spoil_word="soggy",
    ),
    "lantern": Treasure(
        label="lantern",
        phrase="a brass lantern",
        spoil_kind="smoke",
        spoil_word="blackened",
    ),
}

TOOLS = {
    "cloth": Tool(id="cloth", label="oilcloth cover", prep="pull up the oilcloth cover", protects={"salt"}),
    "crate": Tool(id="crate", label="dry crate", prep="stow it in the dry crate", protects={"water"}),
    "hood": Tool(id="hood", label="smoke hood", prep="fit the smoke hood", protects={"smoke"}),
}

NAMES = ["Mara", "Jo", "Nell", "Cove", "Pip", "Tess", "Finn", "Rook"]
MANNERS = ["gentle", "proud", "careful", "boastful", "stern", "polite"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    mate_name: str
    manner: str
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


ASP_RULES = r"""
% A treasure is at risk when the harbor conditions can spoil it.
at_risk(T) :- treasure(T), spoil_kind(T, K), risk(R), spoils(R, K).

% A tool is a compatible fix when it protects the right spoil kind.
fix(T, U) :- at_risk(T), tool(U), spoil_kind(T, K), protects(U, K).

valid(Place, Treasure) :- harbor(Place), treasure(Treasure), at_risk(Treasure), fix(Treasure, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in HARBOURS:
        lines.append(asp.fact("harbor", pid))
    for tid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("spoil_kind", tid, tr.spoil_kind))
    lines.append(asp.fact("risk", "rocks"))
    lines.append(asp.fact("risk", "reef"))
    lines.append(asp.fact("risk", "sandbars"))
    lines.append(asp.fact("spoils", "rocks", "salt"))
    lines.append(asp.fact("spoils", "reef", "water"))
    lines.append(asp.fact("spoils", "sandbars", "water"))
    lines.append(asp.fact("spoils", "wind", "smoke"))
    for uid, ut in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for k in sorted(ut.protects):
            lines.append(asp.fact("protects", uid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _reasonably_valid(place: str, treasure: str) -> bool:
    if place == "harbor" and treasure == "prosciutto":
        return True
    if place == "cove" and treasure == "map":
        return True
    if place == "island" and treasure == "map":
        return True
    if place == "cove" and treasure == "lantern":
        return True
    return False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary pirate tale world with a prosciutto mishap.")
    ap.add_argument("--place", choices=sorted(HARBOURS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
    ap.add_argument("--manner", choices=MANNERS)
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
    place = getattr(args, "place", None) or rng.choice(sorted(HARBOURS))
    treasure = getattr(args, "treasure", None) or rng.choice(sorted(TREASURES))
    if not _reasonably_valid(place, treasure):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    manner = getattr(args, "manner", None) or rng.choice(MANNERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    mate_name = getattr(args, "mate_name", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, treasure=treasure, name=name, mate_name=mate_name, manner=manner)


def generate(params: StoryParams) -> StorySample:
    harbor = _safe_lookup(HARBOURS, params.place)
    treasure_cfg = _safe_lookup(TREASURES, params.treasure)
    hero = Entity(id=params.name, kind="character", label=params.name, type="pirate")
    mate = Entity(id=params.mate_name, kind="character", label=params.mate_name, type="pirate")
    treasure = Entity(id="treasure", kind="thing", label=treasure_cfg.label, phrase=treasure_cfg.phrase, type=treasure_cfg.label)
    world = World(harbor=harbor, entity=hero, mate=mate, treasure=treasure)

    hero.memes["desire"] = 1
    world.say(f"{hero.id} was a {params.manner} little pirate who liked to keep a tidy ship.")
    world.say(f"On the deck, {hero.id} guarded {hero.pronoun('possessive')} {treasure.label} like it was a silver coin.")
    world.say(f"{mate.id} warned that the sea near {harbor.place} could be tricky when the tide turned.")

    world.para()
    world.say(f"One gray morning, the crew sailed to {harbor.place}, and the water looked too quiet.")
    world.say(f"{hero.id} wanted to share {hero.pronoun('possessive')} {treasure.label} with the deck party, but the rocks below could spoil it.")

    if treasure_cfg.spoil_kind == "salt":
        world.say(f'The mate said, "If the spray touches that prosciutto, it will turn salty and grim."')
    elif treasure_cfg.spoil_kind == "water":
        world.say(f'The mate said, "If the spray touches that treasure, it will go soggy and weak."')
    else:
        world.say(f'The mate said, "If the smoke reaches that treasure, it will be blackened and sad."')

    world.say(f"{hero.id} tried to act brave and rushed toward the rail.")
    world.say(f"But {mate.id} gave a sharp look and reminded {hero.id} that good manners on a ship mean listening when danger is near.")

    world.para()
    tool = None
    if treasure_cfg.spoil_kind == "salt":
        tool = Entity(id="cloth", kind="thing", label="oilcloth cover", type="tool")
        world.tool = tool
        world.say(f"Then {mate.id} offered an oilcloth cover and said, \"First we wrap it well.\"")
        world.say(f"{hero.id} agreed, because a careful pirate knows haste can waste a feast.")
        world.say(f"They {TOOLS['cloth'].prep}, and the spray bounced away without touching the prosciutto.")
    elif treasure_cfg.spoil_kind == "water":
        tool = Entity(id="crate", kind="thing", label="dry crate", type="tool")
        world.tool = tool
        world.say(f"Then {mate.id} pointed to a dry crate and said, \"First we stow it safe.\"")
        world.say(f"{hero.id} nodded, because even a bold pirate can learn from a warning.")
        world.say(f"They {TOOLS['crate'].prep}, and the waves could not make the treasure soggy.")
    else:
        tool = Entity(id="hood", kind="thing", label="smoke hood", type="tool")
        world.tool = tool
        world.say(f"Then {mate.id} fetched a smoke hood and said, \"First we shield it from the fumes.\"")
        world.say(f"{hero.id} listened, and the lantern stayed bright instead of blackened.")
        world.say(f"They {TOOLS['hood'].prep}, and the ship sailed on with everything safe.")

    world.say(f"In the end, {hero.id} kept {hero.pronoun('possessive')} {treasure.label} safe, and the crew cheered the wiser way.")
    world.facts.update(
        hero=hero, mate=mate, treasure=treasure, treasure_cfg=treasure_cfg,
        harbor=harbor, tool=tool, params=params
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short pirate tale for young children that warns about keeping {params.treasure} safe at {harbor.place}.",
            f"Tell a cautionary story where {params.name} learns a careful manner near {harbor.place}.",
            f"Write a gentle sea adventure that includes the word '{params.treasure}' and ends with a safe choice.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mate = _safe_fact(world, f, "mate")
    treasure = _safe_fact(world, f, "treasure")
    harb = _safe_fact(world, f, "harbor")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who learned to be more careful at {harb.place}?",
            answer=f"{hero.id} learned to be more careful at {harb.place} after listening to {mate.id}.",
        ),
        QAItem(
            question=f"Why was the {treasure.label} in danger?",
            answer=f"It was in danger because the sea near {harb.place} could spoil it, so the crew had to protect it before the spray or waves reached it.",
        ),
        QAItem(
            question=f"What did they use to keep the {treasure.label} safe?",
            answer=f"They used {tool.label if tool else 'a safe tool'} so the {treasure.label} would stay protected.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a manner?",
            answer="A manner is the way someone behaves or acts, like being polite, careful, or bold.",
        ),
        QAItem(
            question="What is prosciutto?",
            answer="Prosciutto is a thin, salty meat that people often wrap up carefully so it stays good to eat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in [world.entity, world.mate, world.treasure] + ([world.tool] if world.tool else []):
        if not e:
            continue
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", treasure="prosciutto", name="Mara", mate_name="Pip", manner="careful"),
    StoryParams(place="cove", treasure="map", name="Nell", mate_name="Rook", manner="proud"),
    StoryParams(place="island", treasure="map", name="Finn", mate_name="Tess", manner="gentle"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t) for p in HARBOURS for t in TREASURES if _reasonably_valid(p, t)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


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
        print("\n".join(map(str, asp_valid())))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
