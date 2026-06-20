#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thingamajigger_gravel_hobble_sound_effects_conflict_transformation.py
====================================================================================================

A standalone storyworld for a tiny slice-of-life domain built from the seed
words thingamajigger, gravel, hobble, with sound effects, a small conflict, and
a gentle transformation.

Premise
-------
A child and a parent are doing an ordinary neighborhood errand. A loose
thingamajigger on a garden cart makes a clatter on gravel. That sound causes a
small conflict. The child hobbles awkwardly, then transforms the problem into a
safer, nicer moment by fixing the cart and using a calmer tool.

The world is designed so every story is state-driven:
- physical meters: wobble, scatter, clatter, bruise, tidiness
- emotional memes: worry, patience, pride, relief, care

The narrative always starts with a slice-of-life setup, passes through a
sound-effect conflict, and ends with a concrete transformed scene.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_MIN = 1.0
PATCH_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Theme:
    id: str
    place: str
    play: str
    errand: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Thingamajigger:
    id: str
    label: str
    phrase: str
    uses: str
    sound: str
    wobble: float = 1.0

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gravel:
    id: str
    label: str
    phrase: str
    crunch: str
    slippery: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Transformation:
    id: str
    label: str
    tool: str
    action: str
    result: str
    power: float

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if cart and cart.meters["clatter"] >= SOUND_MIN and ("sound", "cart") not in world.fired:
        world.fired.add(("sound", "cart"))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("The clatter made everyone look up.")
    return out


def _r_conflict(world: World) -> list[str]:
    if ("conflict",) in world.fired:
        return []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if child and parent and child.meters["hobble"] >= THRESHOLD and child.memes["frustration"] >= THRESHOLD:
        world.fired.add(("conflict",))
        child.memes["conflict"] += 1
        parent.memes["concern"] += 1
        return ["__conflict__"]
    return []


def _r_transform(world: World) -> list[str]:
    tool = world.entities.get("tool")
    cart = world.entities.get("cart")
    if not tool or not cart:
        return []
    if tool.meters["used"] >= THRESHOLD and cart.meters["fixed"] >= THRESHOLD:
        if ("transform",) in world.fired:
            return []
        world.fired.add(("transform",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
                e.memes["pride"] += 1
        return ["__transform__"]
    return []


CAUSAL_RULES = [
    Rule("sound", "physical", _r_sound),
    Rule("conflict", "social", _r_conflict),
    Rule("transform", "physical", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    _make_noise(sim, narrate=False)
    return {
        "conflict": sim.get("child").memes["conflict"] >= THRESHOLD,
        "worry": sim.get("parent").memes["concern"],
    }


def _make_noise(world: World, narrate: bool = True) -> None:
    world.get("cart").meters["clatter"] += 1
    propagate(world, narrate=narrate)


def hobble(world: World, child: Entity, target: Gravel) -> None:
    child.meters["hobble"] += 1
    child.memes["frustration"] += 1
    world.say(
        f"{child.id} tried to cross the yard, but {child.pronoun('possessive')} foot "
        f"had to {target.crunch} along the gravel."
    )


def setup(world: World, theme: Theme, child: Entity, parent: Entity, thing: Thingamajigger, gravel: Gravel) -> None:
    child.memes["care"] += 1
    parent.memes["care"] += 1
    world.say(
        f"On an ordinary afternoon, {child.id} and {parent.id} were busy near {theme.place}. "
        f"They had {theme.play}, and a little {thing.label} sat on the garden cart."
    )
    world.say(
        f"The path was covered in {gravel.phrase}, and the day felt calm until the cart moved."
    )


def conflict_beat(world: World, child: Entity, parent: Entity, thing: Thingamajigger) -> None:
    pred = predict_conflict(world)
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'Then came a sharp sound: "{thing.sound}" The {thing.label} had slipped and bumped the cart.'
    )
    if pred["conflict"]:
        world.say(
            f'{parent.id} frowned. "{child.id}, that {thing.label} could fall off and make a bigger mess," '
            f'{parent.pronoun()} warned.'
        )


def argue(world: World, child: Entity, parent: Entity, thing: Thingamajigger) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} crossed {child.pronoun("possessive")} arms and said, "I can fix it." '
        f"But {child.id} still had to {thing.uses} to keep up."
    )


def transform_beat(world: World, child: Entity, parent: Entity, thing: Thingamajigger, trans: Transformation) -> None:
    cart = world.get("cart")
    tool = world.get("tool")
    world.say(
        f"After a small pause, {child.id} grabbed {trans.tool} and {trans.action}."
    )
    tool.meters["used"] += 1
    cart.meters["fixed"] += trans.power
    cart.meters["tidy"] += 1
    child.meters["hobble"] = 0.0
    child.memes["frustration"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"The cart stopped wobbling. The {thing.label} sat still, and the gravel no longer snagged it."
    )
    world.say(
        f'{parent.id} smiled, and {child.id} smiled back. That little fix turned the noisy problem into something neat.'
    )


def ending(world: World, theme: Theme, child: Entity, parent: Entity, thing: Thingamajigger) -> None:
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"By the time they finished, {theme.ending_image}. {child.id} hobbled a little less, "
        f"and the {thing.label} was ready for the rest of the day."
    )


def tell(theme: Theme, thing: Thingamajigger, gravel: Gravel, trans: Transformation,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    cart = world.add(Entity(id="cart", type="cart", label="garden cart"))
    tool = world.add(Entity(id="tool", type="tool", label=trans.label))
    world.add(Entity(id="gravel", type="ground", label=gravel.label))

    setup(world, theme, child, parent, thing, gravel)
    world.para()
    hobble(world, child, gravel)
    conflict_beat(world, child, parent, thing)
    argue(world, child, parent, thing)
    world.para()
    transform_beat(world, child, parent, thing, trans)
    ending(world, theme, child, parent, thing)

    world.facts.update(
        theme=theme,
        child=child,
        parent=parent,
        thing=thing,
        gravel=gravel,
        trans=trans,
        cart=cart,
        tool=tool,
    )
    return world


THEMES = {
    "garden": Theme(
        "garden",
        "the side garden",
        "weeding the little bean patch",
        "watering the plants and carrying a basket of tomatoes",
        "the garden looked neat again, and the cart rolled quietly home",
    ),
    "porch": Theme(
        "porch",
        "the front porch",
        "sorting the mail and washing the chalk marks from the step",
        "bringing in the groceries from the car",
        "the porch glowed in the evening light, calm and tidy",
    ),
    "driveway": Theme(
        "driveway",
        "the driveway",
        "packing up paint cans after an afternoon project",
        "moving a tray of cups to the kitchen",
        "the driveway looked smoother, and the cart no longer rattled",
    ),
}

THINGAMAJIGGERS = {
    "bell": Thingamajigger("bell", "thingamajigger bell", "a tiny thingamajigger bell", "ring along the way", "ding-ding"),
    "clip": Thingamajigger("clip", "thingamajigger clip", "a bright thingamajigger clip", "hold the bag shut", "clink"),
    "wheel": Thingamajigger("wheel", "thingamajigger wheel", "a plastic thingamajigger wheel", "roll smoothly", "clatter"),
}

GRAVELS = {
    "pea": Gravel("pea", "pea gravel", "a patch of pea gravel", "hobble"),
    "loose": Gravel("loose", "loose gravel", "a strip of loose gravel", "hobble"),
    "white": Gravel("white", "white gravel", "a small lane of white gravel", "hobble"),
}

TRANSFORMATIONS = {
    "tighten": Transformation("tighten", "wrench", "a small wrench", "tightened the wobbly bolt", "made the cart steady", 2.0),
    "mat": Transformation("mat", "rubber mat", "a rubber mat", "spread a mat under the wheel", "quieted the clatter", 2.0),
    "wrap": Transformation("wrap", "cloth wrap", "a soft cloth wrap", "wrapped the thingamajigger carefully", "made the cart gentle and safe", 2.0),
}

CHILD_NAMES = ["Mina", "Owen", "Tia", "Ben", "Lena", "Noah", "Ruby", "Eli"]
PARENT_NAMES = [("Mom", "mother"), ("Dad", "father")]


@dataclass
@dataclass
class StoryParams:
    theme: str
    thing: str
    gravel: str
    transformation: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for thing in THINGAMAJIGGERS:
            for g in GRAVELS:
                if thing == "wheel" or g in {"pea", "loose", "white"}:
                    combos.append((t, thing, g))
    return combos


KNOWLEDGE = {
    "thingamajigger": [("What is a thingamajigger?",
                        "A thingamajigger is a made-up name for a small object when someone does not want to name it exactly. People often use it in a playful, everyday way.")],
    "gravel": [("What is gravel?",
                "Gravel is made of lots of tiny stones. It makes a crunchy sound under shoes and carts.")],
    "hobble": [("What does it mean to hobble?",
                "To hobble means to walk with a limp or with short, careful steps because something hurts or feels awkward.")],
    "sound": [("Why do sound effects matter in stories?",
               "Sound effects help readers hear what is happening, like a bang or a clatter, so the moment feels lively and real.")],
    "conflict": [("What is a conflict in a story?",
                  "A conflict is a small problem or disagreement that the characters have to work through.")],
    "transformation": [("What is a transformation in a story?",
                        "A transformation is a change from one state to another, like a messy problem turning into a better, calmer one.")],
}
KNOWLEDGE_ORDER = ["thingamajigger", "gravel", "hobble", "sound", "conflict", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "thingamajigger", "gravel", and "hobble".',
        f"Tell a gentle story where {f['child'].id} hears a sound effect from a {f['thing'].label} on the gravel and gets into a small conflict with {f['parent'].id}.",
        f"Write a story about an ordinary day where a tiny problem is transformed into something better, with a clear sound effect and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    thing: Thingamajigger = f["thing"]
    trans: Transformation = f["trans"]
    qas = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {parent.id}, who were doing an ordinary job together. The little problem happened around a {thing.label}.",
        ),
        QAItem(
            question="What sound did the thingamajigger make?",
            answer=f"It made a sharp sound like \"{thing.sound}\" when it bumped the cart. That sound was the moment that turned the quiet afternoon into a small conflict.",
        ),
        QAItem(
            question=f"What did {child.id} do to fix the problem?",
            answer=f"{child.id} used {trans.tool} and {trans.action}. That changed the cart from wobbly and noisy into something steady and calm.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the cart fixed, the gravel no longer causing trouble, and everyone feeling proud. The ordinary day became easier and nicer than before.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"thingamajigger", "gravel", "hobble", "sound", "conflict", "transformation"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "bell", "pea", "tighten", "Mina", "girl", "Mom", "mother"),
    StoryParams("porch", "clip", "loose", "mat", "Owen", "boy", "Dad", "father"),
    StoryParams("driveway", "wheel", "white", "wrap", "Tia", "girl", "Mom", "mother"),
]


def explain_rejection(thing: Thingamajigger, gravel: Gravel) -> str:
    return f"(No story: the {thing.label} and {gravel.label} do not create the kind of small everyday trouble this world is built for.)"


def valid_story(thing: Thingamajigger, gravel: Gravel) -> bool:
    return True


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid, t in THINGAMAJIGGERS.items():
        lines.append(asp.fact("thingamajigger", tid))
    for gid, g in GRAVELS.items():
        lines.append(asp.fact("gravel", gid))
    for xid, x in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", xid))
        lines.append(asp.fact("power", xid, int(x.power)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, Thing, Gravel) :- theme(T), thingamajigger(Thing), gravel(Gravel).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, thing=None, gravel=None, transformation=None, child_name=None, child_gender=None, parent_name=None, parent_gender=None, seed=None), random.Random(777)))
        assert sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: thingamajigger, gravel, hobble, sound effects, conflict, transformation.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--thing", choices=THINGAMAJIGGERS)
    ap.add_argument("--gravel", choices=GRAVELS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.thing is None or c[1] == args.thing)
              and (args.gravel is None or c[2] == args.gravel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, thing, gravel = rng.choice(sorted(combos))
    trans = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    parent_name, parent_gender = (args.parent_name or rng.choice(["Mom", "Dad"]), args.parent_gender or rng.choice(["mother", "father"]))
    return StoryParams(theme, thing, gravel, trans, child_name, child_gender, parent_name, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], THINGAMAJIGGERS[params.thing], GRAVELS[params.gravel], TRANSFORMATIONS[params.transformation], params.child_name, params.child_gender, params.parent_name, params.parent_gender)
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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
