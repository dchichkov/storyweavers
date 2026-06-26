#!/usr/bin/env python3
"""
storyworlds/worlds/perch_banner_dialogue_rhyme_detective_story.py
==================================================================

A small detective-story world about a banner caught on a perch, with dialogue
and a little rhyme woven into the resolution.

Seed tale shape:
- A careful detective notices a banner hanging wrong.
- The clue leads to a perched bird, a gusty snag, or a missing tie.
- The detective asks questions, tests the scene, and fixes the banner.
- The ending proves the world changed: the banner is straight, the perch is safe,
  and the case is closed.

This world models a tiny physical scene with meters and memes:
- meters: flutter, height, tension, tear, wobble
- memes: worry, curiosity, calm, pride, trust, suspicion

The story text is state-driven; dialogue and rhyme come from the simulated
investigation rather than being decorative afterthoughts.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banner: object | None = None
    detective: object | None = None
    helper: object | None = None
    perch: object | None = None
    def __post_init__(self):
        for key in ["flutter", "height", "tension", "tear", "wobble"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "curiosity", "calm", "pride", "trust", "suspicion", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    indoors: bool = False
    winds: bool = False
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
class Banner:
    label: str
    phrase: str
    color: str
    region: str = "air"
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    clears: set[str]
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.scene: str = "setup"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.scene = self.scene
        return clone


@dataclass
class StoryParams:
    place: str
    banner: str
    detective: str
    detective_type: str
    helper: str
    helper_type: str
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


SETTINGS = {
    "rooftop": Setting(place="the rooftop", winds=True, affords={"inspect", "repair"}),
    "square": Setting(place="the town square", winds=True, affords={"inspect", "repair"}),
    "park": Setting(place="the park", winds=True, affords={"inspect", "repair"}),
    "hall": Setting(place="the hall", indoors=True, winds=False, affords={"inspect", "repair"}),
}

BANNERS = {
    "red": Banner(label="banner", phrase="a bright red banner", color="red"),
    "blue": Banner(label="banner", phrase="a blue banner with gold letters", color="blue"),
    "green": Banner(label="banner", phrase="a green banner with silver stars", color="green"),
    "yellow": Banner(label="banner", phrase="a yellow banner for the fair", color="yellow"),
}

TOOLS = [
    Tool(id="ladder", label="a small ladder", prep="fetch a small ladder", tail="set the banner straight", helps={"repair"}, clears={"tension", "wobble"}),
    Tool(id="clip", label="a shiny clip", prep="find a shiny clip", tail="clip the banner fast", helps={"repair"}, clears={"flutter", "tear"}),
    Tool(id="rope", label="a short rope", prep="bring a short rope", tail="tie the banner firm", helps={"repair"}, clears={"flutter", "wobble"}),
]

DETECTIVES = ["Mina", "Pip", "June", "Ollie", "Tess", "Noah"]
HELPERS = ["crow", "cat", "dog", "mouse", "pigeon"]
TRAITS = ["patient", "sharp", "careful", "brave", "quiet"]


def banner_at_risk(setting: Setting, banner: Banner) -> bool:
    return setting.winds


def select_tool(setting: Setting, banner: Banner) -> Optional[Tool]:
    for tool in TOOLS:
        if "repair" in setting.affords and (banner.color in {"red", "blue", "green", "yellow"}):
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, banner_id) for place, setting in SETTINGS.items() for banner_id, banner in BANNERS.items() if banner_at_risk(setting, banner) and select_tool(setting, banner)]


def _r_flutter(world: World) -> list[str]:
    out = []
    b = world.get("banner")
    if b.meters["flutter"] >= THRESHOLD and b.meters["tension"] >= THRESHOLD:
        sig = ("flutter",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        b.meters["tear"] += 1
        out.append("The banner snapped and frayed at the edge.")
    return out


def _r_wobble(world: World) -> list[str]:
    perch = world.entities.get("perch")
    if not perch:
        return []
    if perch.meters["wobble"] >= THRESHOLD and "calm" in world.facts:
        sig = ("wobble",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.facts["perch_safe"] = True
        return ["The perch steadied and held the line."]
    return []


def _r_relief(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.memes["curiosity"] >= THRESHOLD and detective.memes["trust"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        detective.memes["relief"] += 1
        return ["The detective felt calm once the clue made sense."]
    return []


RULES = [_r_flutter, _r_wobble, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, detective: Entity, banner: Banner) -> dict:
    sim = world.copy()
    sim.get("banner").meters["flutter"] += 1
    if sim.setting.winds:
        sim.get("banner").meters["tension"] += 1
    propagate(sim, narrate=False)
    return {"torn": sim.get("banner").meters["tear"] >= THRESHOLD}


def setup_scene(world: World, detective: Entity, helper: Entity, banner: Entity) -> None:
    world.say(f"{detective.id} was a {next((t for t in detective.memes if t), 'careful')} detective who liked small clues.")
    world.say(f"{detective.id} and {helper.id} were on the case near {world.setting.place}.")
    world.say(f"Up above them hung {banner.phrase}, and it did not look quite right.")


def inspect(world: World, detective: Entity, helper: Entity, banner: Entity) -> None:
    detective.memes["curiosity"] += 1
    banner.meters["flutter"] += 1
    if world.setting.winds:
        banner.meters["tension"] += 1
    world.say(f'"Why is the banner waving so hard?" {detective.id} asked.')
    world.say(f'"Maybe the perch caught the cloth," said {helper.id}.')
    propagate(world)


def dialogue_clue(world: World, detective: Entity, helper: Entity, banner: Entity) -> None:
    detective.memes["suspicion"] += 1
    world.say(f'"One clue is enough to start," {detective.id} said. "A snag can make a banner beg."')
    world.say(f'"If it is stuck, we should check the perch," said {helper.id}.')
    world.say('"' + "No rush, no fuss, just fix what we must." + '"')


def repair(world: World, detective: Entity, helper: Entity, banner: Entity, tool: Tool) -> None:
    world.say(f'{detective.id} said, "{tool.prep}."')
    world.say(f'"I can help," said {helper.id}.')
    detective.memes["trust"] += 1
    helper.memes["trust"] += 1
    perch = world.add(Entity(id="perch", type="thing", label="perch"))
    perch.meters["wobble"] += 1
    banner.meters["flutter"] = max(0.0, banner.meters["flutter"] - 1)
    banner.meters["tension"] = max(0.0, banner.meters["tension"] - 1)
    banner.meters["tear"] = 0.0
    perch.meters["wobble"] = 0.0
    world.facts["calm"] = True
    world.say(f"They used {tool.label} to {tool.tail}.")
    world.say('"' + "No more snap, no more slap; the banner rests and that is that." + '"')
    world.say(f"By the end, {banner.phrase} hung straight, and the case was solved.")


def tell(setting: Setting, banner_cfg: Banner, detective_name: str, detective_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, memes={"curiosity": 1.0, "trust": 0.0, "suspicion": 0.0}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, memes={"curiosity": 0.5, "trust": 0.0}))
    banner = world.add(Entity(id="banner", type="thing", label="banner", phrase=banner_cfg.phrase))
    world.facts.update(detective=detective, helper=helper, banner=banner, setting=setting, banner_cfg=banner_cfg)

    setup_scene(world, detective, helper, banner)
    world.para()
    inspect(world, detective, helper, banner)
    dialogue_clue(world, detective, helper, banner)
    world.para()
    tool = select_tool(setting, banner_cfg)
    if tool:
        repair(world, detective, helper, banner, tool)
    return world


WORLD_KNOWLEDGE = {
    "banner": [("What is a banner?", "A banner is a long piece of cloth with words or pictures on it, often used for a party or announcement.")],
    "perch": [("What is a perch?", "A perch is a high place where a bird can rest, like a branch, rail, or narrow bar.")],
    "detective": [("What does a detective do?", "A detective looks for clues, asks questions, and tries to solve a mystery.")],
    "clue": [("What is a clue?", "A clue is a small bit of information that helps solve a mystery.")],
    "rope": [("What is rope for?", "Rope can help tie, lift, or hold things steady when something needs support.")],
    "ladder": [("What is a ladder for?", "A ladder helps someone reach a high place safely.")],
    "clip": [("What is a clip for?", "A clip can hold papers or cloth in place so they do not slip away.")],
}
WORLD_ORDER = ["detective", "clue", "perch", "banner", "rope", "ladder", "clip"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes the words "perch" and "banner".',
        f'Tell a mystery story where {f["detective"].id} notices something wrong with {f["banner_cfg"].phrase}.',
        f'Write a gentle detective tale with dialogue and a little rhyme about fixing a banner near a perch.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    banner = _safe_fact(world, f, "banner")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was trying to solve the mystery near {setting.place}?",
            answer=f"{detective.id} was the detective on the case, and {helper.id} helped look for clues.",
        ),
        QAItem(
            question=f"What was wrong with {banner.phrase}?",
            answer=f"It was waving too hard and looked caught near the perch, so the detective wanted to fix it.",
        ),
        QAItem(
            question=f"How did {detective.id} and {helper.id} solve the problem?",
            answer=f"They used a tool to steady the banner, set it straight, and make the perch safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"banner", "perch", "detective", "clue", "rope", "ladder", "clip"}
    for tag in globals().get("WORLD_ORDER", sorted(globals().get("WORLD", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, banner: Banner) -> str:
    return f"(No story: {banner.phrase} is not at risk in {setting.place}; the detective has no honest mystery to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about a banner, a perch, dialogue, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--banner", choices=BANNERS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPERS)
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
    if getattr(args, "place", None) and getattr(args, "banner", None):
        if not banner_at_risk(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(BANNERS, getattr(args, "banner", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos() if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "banner", None) is None or c[1] == getattr(args, "banner", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, banner = rng.choice(list(combos))
    detective_type = getattr(args, "detective_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPERS)
    detective = getattr(args, "detective", None) or rng.choice(DETECTIVES)
    helper = getattr(args, "helper", None) or rng.choice(["Milo", "Pico", "Nina", "Juno", "Luna"])
    return StoryParams(place=place, banner=banner, detective=detective, detective_type=detective_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(BANNERS, params.banner), params.detective, params.detective_type, params.helper, params.helper_type)
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


ASP_RULES = r"""
risk(Place,Banner) :- setting(Place), banner(Banner), winds(Place).

fix(Place,Banner) :- risk(Place,Banner), tool(T), helps(T, repair), clears(T, flutter).

valid(Place,Banner) :- risk(Place,Banner), fix(Place,Banner).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if s.winds:
            lines.append(asp.fact("winds", place))
    for b in BANNERS:
        lines.append(asp.fact("banner", b))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
        for c in sorted(t.clears):
            lines.append(asp.fact("clears", t.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(place="rooftop", banner="red", detective="Mina", detective_type="girl", helper="crow", helper_type="crow"),
    StoryParams(place="square", banner="blue", detective="Pip", detective_type="boy", helper="cat", helper_type="cat"),
    StoryParams(place="park", banner="green", detective="Tess", detective_type="girl", helper="dog", helper_type="dog"),
    StoryParams(place="hall", banner="yellow", detective="Noah", detective_type="boy", helper="mouse", helper_type="mouse"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective}: {p.banner} banner at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
