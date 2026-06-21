#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pork_matter_tiki_misunderstanding_mystery_to_solve.py
======================================================================================

A tiny fairy-tale storyworld about a banquet, a carved tiki charm, and a
misunderstanding over "matter" that turns into a mystery to solve.

Premise
-------
A child hears a strange word at a feast and assumes the wrong meaning. The tale
builds a small social puzzle: a missing pork pie, a puzzled helper, and a tiki
charm that points the way to the truth. The ending resolves by revealing that
"matter" meant importance, not a substance to scoop up.

This world uses:
- typed entities with physical meters and emotional memes
- a forward-chaining causal model
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in simulated state

The story style aims for fairy-tale simplicity, with a calm misunderstanding and
a gentle mystery solved by observation and honesty.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen"}
        male = {"boy", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class TaleSetting:
    id: str
    place: str
    scene: str
    mood: str
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
class Food:
    id: str
    label: str
    phrase: str
    smell: str
    edible: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class TikiCharm:
    id: str
    label: str
    phrase: str
    clue: str
    glows: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Misunderstanding:
    id: str
    mistaken_meaning: str
    true_meaning: str
    confession: str
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
class Mystery:
    id: str
    question: str
    solved_by: str
    reveal: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setting: str
    food: str
    tiki: str
    misunderstanding: str
    mystery: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    ruler: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["confusion"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        child.memes["worry"] += 1
        out.append("")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("tiki").meters["glow"] >= THRESHOLD and ("clue",) not in world.fired:
        world.fired.add(("clue",))
        world.get("helper").memes["hope"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("clue", _r_clue)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid in FOODS:
            for tid in TIKIS:
                for mid in MISUNDERSTANDINGS:
                    for myid in MYSTERIES:
                        if confusion_can_drive_mystery(mid, myid, fid, tid):
                            combos.append((sid, fid, tid, mid, myid))
    return combos


def confusion_can_drive_mystery(mid: str, myid: str, food: str, tiki: str) -> bool:
    return food in {"pork", "pie", "feast"} and tiki in TIKIS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale misunderstanding and mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--tiki", choices=TIKIS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler", choices=["queen", "king"])
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


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.food is None or c[1] == args.food)
              and (args.tiki is None or c[2] == args.tiki)
              and (args.misunderstanding is None or c[3] == args.misunderstanding)
              and (args.mystery is None or c[4] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, fid, tid, mid, myid = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child = args.child or rng.choice(CHILDREN)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPERS)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    ruler = args.ruler or rng.choice(["queen", "king"])
    return StoryParams(
        setting=sid, food=fid, tiki=tid, misunderstanding=mid, mystery=myid,
        response=response, child=child, child_gender=child_gender,
        helper=helper, helper_gender=helper_gender, ruler=ruler
    )


def _child_desc(e: Entity) -> str:
    return f"young {e.type} {e.id}"


def tell(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    food = FOODS[params.food]
    tiki = TIKIS[params.tiki]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    mystery = MYSTERIES[params.mystery]
    response = RESPONSES[params.response]

    child = w.add(Entity(id="child", kind="character", type=params.child_gender, role="child", attrs={"name": params.child}))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper", attrs={"name": params.helper}))
    ruler = w.add(Entity(id="ruler", kind="character", type=params.ruler, role="ruler"))
    feast = w.add(Entity(id="feast", type="place", label=setting.place))
    dish = w.add(Entity(id="dish", type="food", label=food.label))
    charm = w.add(Entity(id="tiki", type="charm", label=tiki.label))
    child.attrs["name"] = params.child
    helper.attrs["name"] = params.helper

    child.memes["curiosity"] = 1
    child.memes["confusion"] = 1
    helper.memes["care"] = 1
    charm.meters["glow"] = 0.0

    w.say(f"Once in a fairy-tale hall, young {params.child} came to {setting.place}, where {setting.scene}.")
    w.say(f"On the table sat {food.phrase}, and beside it rested {tiki.phrase}.")
    w.say(f"The room felt {setting.mood}, as if it were waiting for a small surprise.")

    w.para()
    w.say(f"{params.child} heard the courtly word '{mis.mistaken_meaning}' and frowned.")
    w.say(f"{params.child} thought the word '{params.food}' must mean {mis.mistaken_meaning}, which was the first misunderstanding.")
    helper.memes["concern"] += 1
    w.say(f"{params.helper} noticed the frown and asked what was wrong.")

    w.para()
    w.say(f"Then came the mystery to solve: {mystery.question}")
    w.say(f"{params.helper} followed the clue of the tiki charm, because {tiki.clue}.")
    charm.meters["glow"] += 1
    charm.memes["attention"] += 1
    propagate(w)

    if params.response == "taste":
        w.say(f"{params.helper} took a careful taste and saw that the matter was not what it seemed.")
    elif params.response == "ask":
        w.say(f"{params.helper} asked the cook, who laughed kindly and began to explain.")
    elif params.response == "inspect":
        w.say(f"{params.helper} lifted the lid and saw the truth hiding in plain sight.")
    else:
        w.say(f"{params.helper} compared the clue to the feast and found the answer at once.")

    w.para()
    if params.food == "pork":
        w.say(f"The answer was simple: the pork was for the feast, not for any strange charm.")
    else:
        w.say(f"The answer was simple: {food.label} belonged to the feast, and no one had lost it.")
    w.say(f"What mattered was not a thing to scoop up, but the importance of telling the truth.")
    w.say(f"{params.child} blushed, because the matter had been a misunderstanding all along.")

    w.para()
    w.say(f"{params.helper} smiled and said, '{mis.confession}'")
    w.say(f"{params.ruler} nodded wisely, and {params.child} finally understood the mystery.")
    w.say(f"The little {tiki.label} glimmered beside the meal, and the feast felt peaceful again.")

    w.facts.update(
        child=child, helper=helper, ruler=ruler, setting=setting, food=food,
        tiki=tiki, misunderstanding=mis, mystery=mystery, response=response
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "{f["food"].label}", "matter", and "tiki".',
        f"Tell a gentle misunderstanding story where {f['child'].attrs['name']} thinks the word matter means something else, and a mystery gets solved by a tiki charm.",
        f"Write a simple fairy tale about a feast, a tiki clue, and a child who learns what matter really means.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].attrs["name"]
    helper = f["helper"].attrs["name"]
    food = f["food"].label
    tiki = f["tiki"].label
    return [
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{child} thought the word matter meant something you could hold in your hands. In truth, it meant importance, so the worry came from a wrong idea."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{helper} followed the clue from the {tiki} charm and looked closely at the feast. That careful looking showed that the {food} belonged to the table and nothing had gone missing."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{child} stopped worrying and understood the truth, and the hall grew calm again. The mystery turned into a lesson about listening before guessing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tiki charm in this story?", answer="It is a small carved charm that can point someone toward a clue. In fairy tales, little objects like that often help solve a mystery."),
        QAItem(question="What does matter mean?", answer="Matter can mean something important. It is not always a thing you can carry or eat."),
        QAItem(question="What is pork?", answer="Pork is meat from a pig, and people can cook it for a meal. It belongs on a plate, not as a magic object."),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for tid in TIKIS:
        lines.append(asp.fact("tiki", tid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for myid in MYSTERIES:
        lines.append(asp.fact("mystery", myid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,F,T,M,Y) :- setting(S), food(F), tiki(T), misunderstanding(M), mystery(Y).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(7))
        s = generate(p)
        _ = s.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            emit(generate(resolve_params(build_parser().parse_args([]), random.Random(8))))
    except Exception as e:
        print(f"EMIT SMOKE FAILED: {e}")
        return 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("food", FOODS), ("tiki", TIKIS),
                       ("misunderstanding", MISUNDERSTANDINGS), ("mystery", MYSTERIES),
                       ("response", RESPONSES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
    world = tell(params)
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


SETTINGS = {
    "feast_hall": TaleSetting("feast_hall", "the feast hall", "golden banners and long tables", "warm and wondering"),
    "forest_clearing": TaleSetting("forest_clearing", "the forest clearing", "fireflies dancing over moss", "soft and secret"),
    "castle_kitchen": TaleSetting("castle_kitchen", "the castle kitchen", "pots singing on the hearth", "busy and bright"),
}

FOODS = {
    "pork": Food("pork", "pork", "a plate of pork", "savory and rich"),
    "pie": Food("pie", "pie", "a round pie", "sweet and buttery"),
    "pudding": Food("pudding", "pudding", "a bowl of pudding", "cool and creamy"),
}

TIKIS = {
    "tiki": TikiCharm("tiki", "tiki", "a little tiki charm", "it points toward the truest clue", glows=True),
    "mask": TikiCharm("mask", "mask", "a carved mask", "its grin seems to watch for lies"),
}

MISUNDERSTANDINGS = {
    "word_mixup": Misunderstanding("word_mixup", "some matter to gather", "importance", "I see now: matter means what is important."),
    "spoon_mixup": Misunderstanding("spoon_mixup", "a spoonful of mystery", "importance", "I was wrong to treat the word as if it were food."),
}

MYSTERIES = {
    "missing_pork": Mystery("missing_pork", "Who took the pork from the feast table?", "looked_at_the_tray", "The pork had not been stolen; it had been moved by a helper."),
    "tiki_clue": Mystery("tiki_clue", "Why does the tiki charm glow beside the plate?", "noticed_glow", "The glow shows which dish matters to the story."),
}

RESPONSES = {
    "ask": Response("ask", 3, 2, "asked the cook and listened to the answer", "asked too late and learned nothing"),
    "inspect": Response("inspect", 3, 2, "inspected the table and found the clue", "looked too quickly and missed the clue"),
    "taste": Response("taste", 2, 1, "tasted a tiny bite and realized the truth", "tasted the wrong thing and stayed confused"),
}

CHILDREN = ["Mila", "Pip", "Elsie", "Robin", "Tobias", "Finn"]
HELPERS = ["Nell", "Mara", "Ivo", "Gwen", "Otis", "Jun"]


CURATED = [
    StoryParams(setting="feast_hall", food="pork", tiki="tiki", misunderstanding="word_mixup", mystery="missing_pork",
                response="inspect", child="Mila", child_gender="girl", helper="Nell", helper_gender="girl", ruler="queen"),
    StoryParams(setting="castle_kitchen", food="pork", tiki="mask", misunderstanding="spoon_mixup", mystery="tiki_clue",
                response="ask", child="Tobias", child_gender="boy", helper="Otis", helper_gender="boy", ruler="king"),
]


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
