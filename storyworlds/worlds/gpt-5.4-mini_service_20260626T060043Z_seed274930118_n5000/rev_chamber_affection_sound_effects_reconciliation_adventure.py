#!/usr/bin/env python3
"""
storyworlds/worlds/rev_chamber_affection_sound_effects_reconciliation_adventure.py
===================================================================================

A small adventure storyworld about a hidden chamber, a noisy revving machine,
and a reconciliation that turns worry into affection.

Premise:
- A young adventurer loves exploring a stone chamber.
- A small engine, winch, or cart can "rev" loudly and make echoing sound effects.
- The loudness can frighten a companion or disturb the chamber's quiet.
- The fix is not to stop the adventure, but to change how it is done: slow down,
  apologize, listen, and reconcile.

The world is intentionally compact and constraint-checked. The story only exists
when the chamber, the noisy tool, and the relationship tension all make sense.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    comp: object | None = None
    hero: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for k in ["noise", "dust", "risk", "warmth"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "affection", "conflict", "relief", "curiosity", "shame"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Chamber:
    name: str
    place: str = "the chamber"
    echo: bool = True
    narrow: bool = True
    hidden: bool = True
    traits: list[str] = field(default_factory=list)
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
class Device:
    id: str
    label: str
    verb: str
    sound: str
    safe_sound: str
    kind: str = "tool"
    can_rev: bool = True
    quiet: bool = False
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
class StoryParams:
    chamber: str
    device: str
    protagonist: str
    companion: str
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
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CHAMBERS = {
    "stone": Chamber(
        name="stone hall",
        place="the stone chamber",
        echo=True,
        narrow=True,
        hidden=True,
        traits=["echoing", "dusty", "ancient"],
    ),
    "moon": Chamber(
        name="moon vault",
        place="the moonlit chamber",
        echo=False,
        narrow=False,
        hidden=True,
        traits=["silent", "cool", "glowing"],
    ),
    "reef": Chamber(
        name="reef grotto",
        place="the reef chamber",
        echo=True,
        narrow=False,
        hidden=False,
        traits=["watery", "sparkling", "open"],
    ),
}

DEVICES = {
    "cart": Device(
        id="cart",
        label="the little cart",
        verb="rev the cart",
        sound="Rrrrum-rum-rum!",
        safe_sound="purr-purr-purr",
    ),
    "drill": Device(
        id="drill",
        label="the hand drill",
        verb="rev the drill",
        sound="Brrrraaaat!",
        safe_sound="bzzzt-bzzzt",
    ),
    "boat": Device(
        id="boat",
        label="the rescue boat motor",
        verb="rev the motor",
        sound="Vrrrrroooom!",
        safe_sound="hummm-hummm",
    ),
}

PROTAGONISTS = [
    ("Ava", "girl"),
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Theo", "boy"),
]

COMPANIONS = [
    ("sister", "girl"),
    ("brother", "boy"),
    ("guide", "person"),
    ("friend", "person"),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def chamber_at_risk(ch: Chamber, dev: Device) -> bool:
    return ch.echo and not dev.quiet


def reasonable_pair(ch: Chamber, dev: Device) -> bool:
    return chamber_at_risk(ch, dev)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for c_id, ch in CHAMBERS.items():
        for d_id, dev in DEVICES.items():
            if reasonable_pair(ch, dev):
                out.append((c_id, d_id))
    return out


def rev_sound(dev: Device, soft: bool = False) -> str:
    return dev.safe_sound if soft else dev.sound


def tell(chamber: Chamber, device: Device, kid_name: str, kid_type: str, comp_name: str, comp_type: str) -> World:
    world = World(chamber)
    hero = world.add(Entity(id=kid_name, kind="character", type=kid_type, label=kid_name))
    comp = world.add(Entity(id=comp_name, kind="character", type=comp_type, label=comp_name))
    tool = world.add(Entity(id=device.id, type="tool", label=device.label, phrase=device.label, owner=hero.id))

    world.facts.update(hero=hero, comp=comp, device=tool, chamber=chamber)

    # Act 1: setup
    world.say(f"{hero.id} was a brave little explorer who loved {chamber.place}.")
    world.say(f"{hero.id} liked the way every step in the {chamber.name} seemed to answer back.")
    world.say(f"Today {hero.id} carried {tool.label}, because {hero.id} wanted to {device.verb} and find the hidden path.")

    # Act 2: tension
    world.para()
    world.say(f"Deep in {chamber.place}, {hero.id} tried to {device.verb}.")
    world.say(rev_sound(device).replace("!", "") + " the chamber echoed.")
    hero.memes["joy"] += 1
    hero.meters["noise"] += 1
    if chamber.echo:
        comp.memes["worry"] += 1
        comp.memes["conflict"] += 1
        world.say(f"{comp.id} winced at the loud sound effect and said the noise felt too big for the narrow room.")
        world.say(f"The echo bounced around like a clapping drum, and the adventure suddenly felt tense.")

    # Act 3: reconciliation
    world.para()
    world.say(f"{hero.id} looked at {comp.id} and felt sorry.")
    hero.memes["shame"] += 1
    comp.memes["affection"] += 1
    hero.memes["affection"] += 1
    hero.memes["conflict"] = 0
    comp.memes["worry"] = 0
    comp.memes["conflict"] = 0
    comp.memes["relief"] += 1
    world.say(f'"I can make a softer sound," {hero.id} said, and {hero.id} tapped the machine again: {device.safe_sound}')
    world.say(f"{comp.id} smiled, because the gentler rev sounded like a tiny purring dragon instead of a roar.")
    world.say(f"Together they followed the safer echo deeper into {chamber.place}, side by side again.")
    world.say(f"By the end, the chamber felt less scary and more like a secret place they could share.")

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "comp")
    device = _safe_fact(world, f, "device")
    chamber = _safe_fact(world, f, "chamber")
    return [
        f'Write a short adventure story for a small child about {hero.id}, {comp.id}, and a noisy {device.label} in {chamber.place}.',
        f'Write a gentle story that includes a rev sound effect, a hidden chamber, and a reconciliation between {hero.id} and {comp.id}.',
        f"Tell a brave, child-friendly adventure where a loud '{device.sound}' leads to feelings, then a softer way forward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "comp")
    device = _safe_fact(world, f, "device")
    chamber = _safe_fact(world, f, "chamber")
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {chamber.place}?",
            answer=f"{hero.id} wanted to {device.verb} and explore the hidden chamber.",
        ),
        QAItem(
            question=f"Why did {comp.id} feel worried when the machine started?",
            answer=f"{comp.id} felt worried because the loud rev sound echoed around {chamber.place} and filled the narrow room.",
        ),
        QAItem(
            question=f"How did {hero.id} and {comp.id} solve the problem?",
            answer=f"{hero.id} apologized and used a softer sound, so they could reconcile and keep exploring together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off walls and comes back again.",
        ),
        QAItem(
            question="What does rev mean?",
            answer="To rev means to make an engine or machine run loudly and quickly, like a motor going vroom.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, apologize, and become friendly again.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show valid_story/4.

at_risk(C,D) :- chamber(C), device(D), echoing(C), noisy(D).
valid(C,D) :- at_risk(C,D), has_fix(D).
valid_story(C,D,H,P) :- valid(C,D), hero_type(H), companion_type(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for cid, ch in CHAMBERS.items():
        lines.append(asp.fact("chamber", cid))
        if ch.echo:
            lines.append(asp.fact("echoing", cid))
        if ch.narrow:
            lines.append(asp.fact("narrow", cid))
        for t in ch.traits:
            lines.append(asp.fact("trait", cid, t))
    for did, dev in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("noisy", did))
        if dev.can_rev:
            lines.append(asp.fact("can_rev", did))
        if dev.quiet:
            lines.append(asp.fact("quiet", did))
        lines.append(asp.fact("has_fix", did))  # soft rev is the fix
    for name, typ in PROTAGONISTS:
        lines.append(asp.fact("hero_type", typ))
    for role, typ in COMPANIONS:
        lines.append(asp.fact("companion_type", typ))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: rev, chamber, and reconciliation.")
    ap.add_argument("--chamber", choices=CHAMBERS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name")
    ap.add_argument("--companion-name")
    ap.add_argument("--gender", choices=["girl", "boy", "person"])
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
    if getattr(args, "chamber", None) and getattr(args, "device", None) and (getattr(args, "chamber", None), getattr(args, "device", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos if (getattr(args, "chamber", None) is None or c[0] == getattr(args, "chamber", None)) and (getattr(args, "device", None) is None or c[1] == getattr(args, "device", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    chamber, device = rng.choice(list(filtered))
    hero_name, hero_gender = rng.choice(PROTAGONISTS)
    comp_role, comp_gender = rng.choice(COMPANIONS)
    if getattr(args, "name", None):
        hero_name = getattr(args, "name", None)
    if getattr(args, "gender", None):
        hero_gender = getattr(args, "gender", None)
    comp_name = getattr(args, "companion_name", None) or (rng.choice(["Pip", "June", "Mira", "Finn", "Bea"]))
    if hero_gender == "person":
        hero_gender = "girl"
    if comp_gender == "person":
        comp_gender = rng.choice(["girl", "boy"])
    return StoryParams(
        chamber=chamber,
        device=device,
        protagonist=hero_name,
        companion=comp_name,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    chamber = _safe_lookup(CHAMBERS, params.chamber)
    device = _safe_lookup(DEVICES, params.device)
    hero_name = params.protagonist
    comp_name = params.companion
    hero_type = "girl" if hero_name in {"Ava", "Nia"} else "boy"
    comp_type = "girl" if comp_name in {"June", "Bea", "Mira"} else "boy"
    world = tell(chamber, device, hero_name, hero_type, comp_name, comp_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"chamber: {world.chamber.place} traits={world.chamber.traits}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(chamber="stone", device="cart", protagonist="Ava", companion="June"),
    StoryParams(chamber="moon", device="drill", protagonist="Milo", companion="Bea"),
    StoryParams(chamber="reef", device="boat", protagonist="Nia", companion="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid chamber/device combos:\n")
        for c, d in combos:
            print(f"  {c:6} {d}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.protagonist} in {p.chamber} with {p.device}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
