#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gent_venetian_cautionary_humor_bedtime_story.py
===============================================================================

A tiny bedtime storyworld about a polite little gent, a Venetian blind, a silly
near-miss, and a calm grown-up fix.

Premise
-------
A child wants to make the bedroom darker and fancier at bedtime. The child
plays with a Venetian blind cord, gets it in a silly tangle, and learns that
cords are not toys. A grown-up untangles the scene, uses a safe nightlight, and
the room settles into a cozy bedtime ending.

This world keeps the tone soft, cautionary, and a little humorous:
- the hazard is real, but not intense;
- the grown-up response is calm and sensible;
- the ending proves that the room changed from messy and tense to warm and safe.

It follows the shared StorySample/QAItem contract and includes an inline ASP
twin plus a Python reasonableness gate.
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
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "gent"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    room: str
    cozy_detail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tension:
    id: str
    label: str
    phrase: str
    where: str
    danger: str
    risk: str
    makes_tangle: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SafeItem:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tugging"] < THRESHOLD:
            continue
        sig = ("tangle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["tangled"] += 1
        out.append("__tangle__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if any(e.meters["tangled"] >= THRESHOLD for e in world.entities.values()):
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.role in {"child", "parent"}:
                    e.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("tangle", "physical", _r_tangle), Rule("worry", "emotional", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tension_at_risk(tension: Tension) -> bool:
    return tension.makes_tangle


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, t in TENSIONS.items():
            for rid, r in RESPONSES.items():
                if tension_at_risk(t) and r.sense >= SENSE_MIN:
                    combos.append((sid, tid, rid))
    return combos


def _do_tug(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["tugging"] += 1
    propagate(world, narrate=narrate)


def predict_tangle(world: World) -> dict:
    sim = world.copy()
    _do_tug(sim, sim.get("blind"), narrate=False)
    return {"tangled": sim.get("blind").meters["tangled"] >= THRESHOLD}


def introduce(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"At bedtime, {child.id} was a little gent who liked neat pillows, soft socks, "
        f"and {setting.cozy_detail}."
    )
    world.say(
        f"The room was {setting.room}, with a {setting.cozy_detail} and a {TENSIONS['blind'].phrase} by the window."
    )


def tempt(world: World, child: Entity, tension: Tension) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} peered up at {tension.where}. "I can make the room extra sleepy," '
        f"{child.id} whispered, and reached for the {tension.label}."
    )


def warn(world: World, parent: Entity, child: Entity, tension: Tension) -> None:
    pred = predict_tangle(world)
    if pred["tangled"]:
        parent.memes["care"] += 1
        world.say(
            f'{parent.id} smiled a small smile. "{child.id}, cords are not toys," '
            f"{parent.pronoun()} said. \"If we tug {tension.label}, it can knot up fast.\""
        )


def tug(world: World, child: Entity, tension: Tension) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} gave the cord one tiny tug, then another. It answered with a silly '
        f'snip-snap and made a very un-bedtime face."
    )
    _do_tug(world, world.get("blind"), narrate=True)


def untangle(world: World, parent: Entity, tension: Tension, response: Response) -> None:
    world.get("blind").meters["tangled"] = 0
    world.get("blind").meters["tugging"] = 0
    world.say(
        f"{parent.label_word.capitalize()} came over at once and {response.text.replace('{target}', tension.label)}."
    )
    world.say(
        f"The cord went straight again, and the room stopped looking like a puzzled spider had visited it."
    )


def lesson(world: World, parent: Entity, child: Entity, tension: Tension) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'For a moment, {child.id} giggled at the silly knot. Then {parent.label_word} hugged {child.pronoun("object")} and said, '
        f'"That was funny, but it was still not safe. {tension.danger}. "
        f"{tension.risk.capitalize()}."'
    )


def cozy_finish(world: World, child: Entity, parent: Entity, light: SafeItem) -> None:
    child.memes["joy"] += 1
    child.memes["safe"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} turned on {light.phrase}, which {light.glow}, "
        f"and the room became gentle and golden."
    )
    world.say(
        f"{child.id} tucked in under the blanket, the silly cord forgotten, and the little {child.pronoun('object')} fell asleep listening to a bedtime story."
    )


def tell(setting: Setting, tension: Tension, response: Response, light: SafeItem,
         child_name: str = "Theo", child_gender: str = "boy",
         parent_name: str = "Mum", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    blind = world.add(Entity(id="blind", kind="thing", type="thing", label="the Venetian blind"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="thing", label=light.label))

    introduce(world, child, setting)
    world.para()
    tempt(world, child, tension)
    warn(world, parent, child, tension)
    tug(world, child, tension)
    world.para()
    untangle(world, parent, tension, response)
    lesson(world, parent, child, tension)
    world.para()
    cozy_finish(world, child, parent, light)

    world.facts.update(
        child=child,
        parent=parent,
        tension=tension,
        response=response,
        light=light,
        setting=setting,
        blind=blind,
        lamp=lamp,
        tangled=blind.meters["tangled"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting(id="bedroom", room="soft and sleepy", cozy_detail="a moon-shaped lamp"),
    "nursery": Setting(id="nursery", room="warm and drowsy", cozy_detail="a teddy bear on the shelf"),
}

TENSIONS = {
    "blind": Tension(
        id="blind",
        label="the blind cord",
        phrase="a Venetian blind with long white cords",
        where="the window",
        danger="a cord can tangle around a hand or a wrist",
        risk="cords are for windows, not games",
        makes_tangle=True,
        tags={"venetian", "cord", "window"},
    ),
    "shutter": Tension(
        id="shutter",
        label="the shutter latch",
        phrase="old shutters that clicked in the night breeze",
        where="the window",
        danger="latches can pinch fingers if they are poked and pulled",
        risk="window parts are for grown-up hands",
        makes_tangle=False,
        tags={"venetian", "window"},
    ),
}

SAFE_ITEMS = {
    "nightlight": SafeItem(id="nightlight", label="a tiny nightlight", phrase="a tiny nightlight", glow="glowed like a sleepy star", tags={"light"}),
    "lamp": SafeItem(id="lamp", label="the moon lamp", phrase="the moon lamp", glow="made the wall look cozy and blue", tags={"light"}),
}

RESPONSES = {
    "untangle": Response(
        id="untangle",
        sense=3,
        power=3,
        text="untangled the cord with careful fingers",
        fail="tried to untangle the cord, but it only knotted itself tighter",
        qa_text="untangled the cord with careful fingers",
        tags={"cord"},
    ),
    "nudge": Response(
        id="nudge",
        sense=2,
        power=2,
        text="slid the cord back into place and smoothed it flat",
        fail="nudged the cord, but the knot stayed put",
        qa_text="slid the cord back into place and smoothed it flat",
        tags={"cord"},
    ),
    "pull_harder": Response(
        id="pull_harder",
        sense=1,
        power=1,
        text="pulled harder until the whole blind rattled",
        fail="pulled harder, but that only made the cord sillier",
        qa_text="pulled harder",
        tags={"bad"},
    ),
}

CURATED = [
    StoryParams = None
]

@dataclass
class StoryParams:
    setting: str
    tension: str
    response: str
    light: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(setting="bedroom", tension="blind", response="untangle", light="nightlight", child_name="Theo", child_gender="gent", parent_name="Mum", parent_gender="mother"),
    StoryParams(setting="nursery", tension="blind", response="nudge", light="lamp", child_name="Ned", child_gender="gent", parent_name="Dad", parent_gender="father"),
]


def explain_rejection(tension: Tension) -> str:
    return "(No story: this world needs a real, risky window-cord temptation, not a harmless scene.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "gent" and "venetian".',
        f"Tell a gentle cautionary story where {f['child'].id} reaches for a Venetian blind cord, gets a silly tangle, and learns a safety lesson.",
        f"Write a humorous bedtime story about a window cord that should be left alone, ending with a cozy nightlight.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, tension, response = f["child"], f["parent"], f["tension"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, a little gent, and {parent.id}, who kept bedtime calm and safe."),
        ("What did {0} reach for?".format(child.id),
         f"{child.id} reached for {tension.label} by the window because {child.id} wanted to make the room extra sleepy."),
        ("What happened when the child tugged the cord?",
         f"The cord made a silly little tangle, and the blind looked puzzled. It was funny for a moment, but it showed why the cord should not be played with."),
        ("How did the grown-up fix it?",
         f"{parent.id} {response.qa_text}, and the cord went straight again. That stopped the knot from getting worse."),
        ("How did the story end?",
         f"It ended with a cozy nightlight, a calm room, and {child.id} tucked in safely for sleep."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a Venetian blind?",
         "A Venetian blind is a window covering made of slats and cords that you can raise or lower."),
        ("Why are cords not toys?",
         "Cords can tangle, pinch, or pull things down, so they are meant to be handled by grown-ups."),
        ("What is a nightlight for?",
         "A nightlight gives a little soft light in the dark so bedtime feels cozy without a bright lamp."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
tangled(X) :- tugging(X), makes_tangle(X).
worry(X) :- tangled(X), child(X).
valid(S, T, R) :- setting(S), tension(T), response(R), makes_tangle(T), sensible(R).
outcome(cozy) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TENSIONS.items():
        lines.append(asp.fact("tension", tid))
        if t.makes_tangle:
            lines.append(asp.fact("makes_tangle", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c != p:
        print("MISMATCH in valid combos")
        return 1
    print(f"OK: gate matches valid_combos() ({len(c)} combos).")
    cases = [CURATED[0]]
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            return 1
        print("OK: smoke test generated a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime cautionary humor storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tension", choices=TENSIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--light", choices=SAFE_ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["gent", "boy", "girl"])
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
    if args.tension and not TENSIONS[args.tension].makes_tangle:
        raise StoryError(explain_rejection(TENSIONS[args.tension]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tension is None or c[1] == args.tension)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tension, response = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(SAFE_ITEMS))
    child_gender = args.child_gender or "gent"
    child_name = args.child_name or rng.choice(["Theo", "Ned", "Milo", "Arlo"])
    parent_name = args.parent_name or rng.choice(["Mum", "Dad"])
    parent_gender = args.parent_gender or ("mother" if parent_name == "Mum" else "father")
    return StoryParams(setting=setting, tension=tension, response=response, light=light,
                       child_name=child_name, child_gender=child_gender,
                       parent_name=parent_name, parent_gender=parent_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.tension not in TENSIONS:
        raise StoryError("Unknown tension.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if params.light not in SAFE_ITEMS:
        raise StoryError("Unknown safe item.")
    world = tell(SETTINGS[params.setting], TENSIONS[params.tension],
                 RESPONSES[params.response], SAFE_ITEMS[params.light],
                 child_name=params.child_name, child_gender=params.child_gender,
                 parent_name=params.parent_name, parent_gender=params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
