#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/axle_happy_ending_bad_ending_rhyming_story.py
===============================================================================================================

A small story world about a wheeled toy, a wobbly axle, and two possible
endings: a happy ending when the axle is fixed, or a bad ending when the ride
breaks apart. The narration aims for a gentle rhyming-story feel.

Seed premise:
A child wants to race a little cart, but the axle is loose or bent. A helper
can tighten it with a nut and wrench, or the child can ignore the warning and
end up with a broken ride.

The storyworld models:
- a child
- a cart with a wheel and axle
- a helper
- a tool kit
- physical meters: wobble, brokenness, tightness, speed, pride, worry
- emotional memes: joy, patience, frustration, relief, care

The "happy ending" is available only when the helper fixes the axle before the
ride. The "bad ending" is available when the child rushes ahead and the axle
snaps or the wheel falls off.
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
    parts: list[str] = field(default_factory=list)
    can_roll: bool = False
    fixed: bool = False

    axle: object | None = None
    cart: object | None = None
    child: object | None = None
    helper: object | None = None
    wrench: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the shed"
    afford_fix: bool = True
    afford_ride: bool = True
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
    ending: str
    name: str
    gender: str
    helper: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "tool"]
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


def rhyme(a: str, b: str) -> str:
    return f"{a} / {b}"


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def setup_world(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.place])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"worry": 0.0, "pride": 1.0},
        memes={"joy": 1.0, "care": 0.0, "patience": 0.5},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"calm": 1.0},
        memes={"care": 1.0, "patience": 1.0},
    ))
    cart = world.add(Entity(
        id="Cart",
        kind="thing",
        type="cart",
        label="little cart",
        phrase="a little cart with a bright red wheel",
        meters={"wobble": 1.0, "broken": 0.0, "speed": 0.0, "tightness": 0.0},
        parts=["wheel", "axle", "frame"],
        can_roll=True,
    ))
    axle = world.add(Entity(
        id="Axle",
        kind="thing",
        type="axle",
        label="axle",
        phrase="the cart's axle",
        owner="Cart",
        meters={"wobble": 1.0, "broken": 0.0, "tightness": 0.0},
        fixed=False,
    ))
    wrench = world.add(Entity(
        id="Wrench",
        kind="tool",
        type="wrench",
        label="small wrench",
        phrase="a small wrench and a shiny nut",
        owner="Helper",
        meters={"useful": 1.0},
    ))
    world.facts.update(child=child, helper=helper, cart=cart, axle=axle, wrench=wrench, params=params)
    return world


def predict_break(world: World) -> bool:
    sim = world.copy()
    cart = sim.get("Cart")
    axle = sim.get("Axle")
    if axle.meters.get("tightness", 0.0) < THRESHOLD:
        add_meter(axle, "wobble", 1.0)
        add_meter(cart, "speed", 1.0)
        if axle.meters.get("wobble", 0.0) >= 2.0:
            add_meter(axle, "broken", 1.0)
    return axle.meters.get("broken", 0.0) >= THRESHOLD


def tighten_axle(world: World) -> None:
    cart = world.get("Cart")
    axle = world.get("Axle")
    helper = world.get("Helper")
    if axle.meters.get("broken", 0.0) >= THRESHOLD:
        return
    add_meter(axle, "tightness", 1.0)
    add_meter(axle, "wobble", -0.5)
    axle.fixed = True
    cart.fixed = True
    add_meme(helper, "care", 0.5)


def roll_cart(world: World) -> None:
    cart = world.get("Cart")
    axle = world.get("Axle")
    child = world.get(world.facts["child"].id)
    add_meter(cart, "speed", 1.0)
    if axle.meters.get("tightness", 0.0) < THRESHOLD:
        add_meter(axle, "wobble", 1.0)
        add_meme(child, "frustration", 1.0)
        if axle.meters.get("wobble", 0.0) >= 2.0:
            add_meter(axle, "broken", 1.0)
            add_meter(cart, "broken", 1.0)
    else:
        add_meme(child, "joy", 1.0)


def tell_world(params: StoryParams) -> World:
    world = setup_world(params)
    child = _safe_fact(world, world.facts, "child")
    helper = _safe_fact(world, world.facts, "helper")
    cart = _safe_fact(world, world.facts, "cart")
    axle = _safe_fact(world, world.facts, "axle")

    world.say(f"{child.id} found a little cart that loved to roll and race.")
    world.say(f"But the {axle.label} went wibble and wobble, and the wheel did not feel right.")

    world.para()
    world.say(f"{child.id} wanted a quick zoom, a bright fast bloom, a merry little tune.")
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1.0

    if params.ending == "happy":
        world.say(f"The {helper.label} smiled and said, \"Let's fix it right, so the ride will be light.\"")
        if world.setting.afford_fix and not predict_break(world):
            tighten_axle(world)
            world.say(f"The {helper.label} used the wrench and snugged the nut, with a twist and a tuck.")
            world.say(f"Then {child.id} gave the cart a test, and the axle held fast, firm, and best.")
            roll_cart(world)
            world.para()
            world.say(f"At last the cart went clip and clack, with no more wobble in the track.")
            world.say(f"{child.id} laughed a lot, for the little cart was sturdy and smart.")
            world.facts["resolved"] = True
        else:
            pass
    else:
        world.say(f"{child.id} said, \"No wait, no slow; I want to go, go, go.\"")
        world.say(f"{child.id} rushed the cart across the floor, and the axle groaned for more and more.")
        roll_cart(world)
        roll_cart(world)
        if axle.meters.get("broken", 0.0) >= THRESHOLD:
            world.say(f"Crack went the axle, snap went the tune, and the wheel fell off by noon.")
            world.say(f"The cart could not race; it sat in place, and {child.id} wore a frown on face.")
            world.facts["resolved"] = False
        else:
            pass

    world.facts["cart"] = cart
    world.facts["axle"] = axle
    return world


SETTING_REGISTRY = {
    "shed": Setting(place="the shed", afford_fix=True, afford_ride=True),
    "yard": Setting(place="the yard", afford_fix=True, afford_ride=True),
    "garage": Setting(place="the garage", afford_fix=True, afford_ride=True),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTING_REGISTRY:
        for ending in {"happy", "bad"}:
            for gender in {"girl", "boy"}:
                out.append((place, ending, gender))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about an axle and its ending.")
    ap.add_argument("--place", choices=sorted(SETTING_REGISTRY))
    ap.add_argument("--ending", choices=["happy", "bad"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandparent", "mechanic"])
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTING_REGISTRY))
    ending = getattr(args, "ending", None) or rng.choice(["happy", "bad"])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandparent", "mechanic"])
    name = getattr(args, "name", None) or rng.choice(["Mia", "Leo", "Nora", "Ben", "Ava", "Finn"])
    if ending == "happy" and place not in SETTING_REGISTRY:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, ending=ending, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    child = _safe_fact(world, world.facts, "child")
    return [
        f'Write a short rhyming story for a child named {child.id} about an axle that can go "wibble" and "whirr."',
        f"Tell a gentle story where {child.id} wants to race a cart, but the axle may be loose, and the ending is {p.ending}.",
        f'Write a tiny story in rhyme about a cart, an axle, and a fix-or-fail choice at {p.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    axle = _safe_fact(world, world.facts, "axle")
    helper = _safe_fact(world, world.facts, "helper")
    p = _safe_fact(world, world.facts, "params")
    if p.ending == "happy":
        ans = f"The {helper.label} fixed the axle with a wrench, and the cart rolled safe and sound."
    else:
        ans = f"The child rushed ahead, the axle broke, and the cart could not keep racing."
    return [
        QAItem(question=f"What was wobbly in the story?", answer=f"The {axle.label} was wobbly."),
        QAItem(question=f"Who tried to help at {p.place}?", answer=f"The {helper.label} tried to help."),
        QAItem(question=f"What ending did {child.id}'s cart get?", answer=ans),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an axle do?",
            answer="An axle helps a wheel turn and stay in place on a cart or wagon.",
        ),
        QAItem(
            question="Why do people tighten a loose axle?",
            answer="People tighten a loose axle so the wheel will not wobble or fall off while something rolls.",
        ),
    ]


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.parts:
            bits.append(f"parts={e.parts}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
ending(happy;bad).

axle_ok(A) :- axle(A), tight(A), not broken(A).
axle_bad(A) :- axle(A), broken(A).

happy_story(P) :- place(P), ending(happy).
bad_story(P) :- place(P), ending(bad).

safe_fix(P) :- place(P), afford_fix(P).
unsafe_rush(P) :- place(P), afford_ride(P).

valid_story(P, E, G) :- place(P), ending(E), gender(G), safe_fix(P).
valid_story(P, E, G) :- place(P), ending(E), gender(G), unsafe_rush(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTING_REGISTRY.items():
        lines.append(asp.fact("place", place))
        if setting.afford_fix:
            lines.append(asp.fact("afford_fix", place))
        if setting.afford_ride:
            lines.append(asp.fact("afford_ride", place))
    lines.append(asp.fact("gender", "girl"))
    lines.append(asp.fact("gender", "boy"))
    lines.append(asp.fact("ending", "happy"))
    lines.append(asp.fact("ending", "bad"))
    lines.append(asp.fact("axle", "axle"))
    lines.append(asp.fact("tight", "axle"))
    lines.append(asp.fact("broken", "axle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
    StoryParams(place="shed", ending="happy", name="Mia", gender="girl", helper="father"),
    StoryParams(place="yard", ending="bad", name="Leo", gender="boy", helper="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
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
