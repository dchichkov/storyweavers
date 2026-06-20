#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bandana_happy_ending_cautionary_friendship_slice_of.py
=======================================================================================

A standalone story world for a small slice-of-life domain: two friends helping
in a cozy kitchen, a bandana, a near-miss with a warm stove, and a safe ending
that proves friendship can be both caring and brave.

The world is built as a tiny simulation with typed entities, physical meters,
emotional memes, forward-chained causal rules, a reasonableness gate, an ASP
twin, and child-facing Q&A grounded in state rather than rendered prose.
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
    flammable: bool = False
    wearable: bool = False
    safe_item: bool = False

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
    scene: str
    setting_line: str
    goal: str
    safe_alternative: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Hazard:
    id: str
    label: str
    phrase: str
    near: str
    risk: str
    makes_heat: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out = []
    for kid in list(world.entities.values()):
        if kid.role != "friend" or kid.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in list(world.entities.values()):
            if other.role == "friend" and other.id != kid.id:
                other.memes["care"] += 1
        out.append("__worry__")
    return out


def _r_heat(world: World) -> list[str]:
    out = []
    stove = world.entities.get("stove")
    if stove and stove.meters["heat"] >= THRESHOLD:
        sig = ("heat", "stove")
        if sig not in world.fired:
            world.fired.add(sig)
            for ent in list(world.entities.values()):
                if ent.wearable and not ent.safe_item:
                    ent.meters["risk"] += 1
            out.append("__heat__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("heat", "physical", _r_heat)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def hazard_at_risk(hazard: Hazard) -> bool:
    return hazard.makes_heat


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} turned the kitchen into a little "
        f"place for sharing. {theme.setting_line}"
    )
    world.say(
        f'They were happy to help together. The plan was simple: make a snack, keep '
        f'it tidy, and enjoy the time before dinner.'
    )


def want_bandana(world: World, a: Entity, bandana: Entity) -> None:
    a.memes["play"] += 1
    world.say(
        f'{a.id} picked up the {bandana.label} and smiled. "This will make me look '
        f'ready for our kitchen game," {a.id} said.'
    )


def warn(world: World, b: Entity, a: Entity, hazard: Hazard) -> None:
    b.memes["care"] += 1
    b.memes["worry"] += 1
    world.facts["warned"] = True
    world.say(
        f"{b.id} looked toward the stove and bit {b.pronoun('possessive')} lip. "
        f'"If you tie that {hazard.label} too close to the heat, it could get too '
        f'warm and start to smell like smoke," {b.id} said softly.'
    )
    propagate(world, narrate=True)


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["stubborn"] += 1
    world.say(
        f'"I just want to wear it for a minute," {a.id} said, but {b.id} stayed '
        f'kind and kept watching.'
    )


def accident(world: World, a: Entity, hazard: Hazard) -> None:
    band = world.get("bandana")
    stove = world.get("stove")
    band.meters["near_heat"] += 1
    stove.meters["heat"] += 1
    band.meters["smell"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hazard.label.capitalize()} near the stove was not a good mix. The {hazard.label} '
        f'grew warm, then a little smoky at the edge.'
    )


def alarm(world: World, b: Entity, hazard: Hazard) -> None:
    world.say(
        f'"{a_name(world)}!" {b.id} called. "Please move the {hazard.label} away '
        f'from the stove!"'
    )


def a_name(world: World) -> str:
    return world.facts["friend_a"].id


def rescue(world: World, parent: Entity, response: Response) -> None:
    bandana = world.get("bandana")
    stove = world.get("stove")
    bandana.meters["near_heat"] = 0
    stove.meters["heat"] = 0
    world.say(
        f"{parent.label_word.capitalize()} came in right away and {response.text}."
    )
    world.say("The smoky smell faded, and the kitchen felt calm again.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, hazard: Hazard) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["worry"] = 0
    world.say(
        f"Then {parent.label_word.capitalize()} knelt by the table and hugged them both. "
        f'"Thank you for telling me right away," {parent.pronoun()} said. '
        f'"{hazard.label.capitalize()} and heat do not belong together."'
    )
    world.say(
        f"{a.id} and {b.id} promised to keep the {hazard.label} away from the stove "
        f"from then on."
    )


def safe_end(world: World, a: Entity, b: Entity, theme: Theme, safe: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next minute, they switched to {safe.label}. It stayed cool and bright, "
        f"and it looked much better for a kitchen game."
    )
    world.say(
        f'{a.id} tucked the {safe.label} in place, {b.id} smiled, and the two friends '
        f"{theme.ending_image}."
    )


def tell(theme: Theme, hazard: Hazard, response: Response, delay: int,
         a_name: str = "Mina", a_gender: str = "girl",
         b_name: str = "Tess", b_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    bandana = world.add(Entity(id="bandana", type="thing", label="bandana", wearable=True))
    stove = world.add(Entity(id="stove", type="thing", label="stove", flammable=False))
    safe = world.add(Entity(id="headband", type="thing", label=theme.safe_alternative, safe_item=True))
    world.facts.update(friend_a=a, friend_b=b, parent=parent, hazard=hazard, response=response, delay=delay)

    setup(world, a, b, theme)
    world.para()
    want_bandana(world, a, bandana)
    warn(world, b, a, hazard)
    defy(world, a, b)
    world.para()
    accident(world, a, hazard)
    alarm(world, b, hazard)
    if is_contained(response, delay):
        rescue(world, parent, response)
        lesson(world, parent, a, b, hazard)
        world.para()
        safe_end(world, a, b, theme, safe)
        outcome = "contained"
    else:
        rescue(world, parent, response)
        world.say("But the heat had already spread too far, and they had to leave the kitchen quickly.")
        outcome = "burned"
    world.facts["outcome"] = outcome
    world.facts["bandana"] = bandana
    world.facts["safe"] = safe
    return world


THEMES = {
    "kitchen": Theme(
        "kitchen",
        "The kitchen smelled like toast and warm jam, and the table was set with two cups of water.",
        "The window was open, a little sun came in, and the room felt cozy and ordinary.",
        "their snack",
        "a cool headband",
        "they finished their afternoon together, happy and calm",
    ),
    "after_school": Theme(
        "after_school",
        "The kitchen smelled like apples, and a lunchbox sat by the sink.",
        "There was still time before dinner, so the room felt quiet and gentle.",
        "their snack",
        "a cool headband",
        "they laughed over the snack and tucked the day away",
    ),
}

HAZARDS = {
    "bandana_heat": Hazard(
        "bandana_heat",
        "bandana",
        "the bandana",
        "the edge of the stove",
        "It can get too warm and catch a little singe",
        makes_heat=True,
    )
}

RESPONSES = {
    "dry_towel": Response(
        "dry_towel",
        3,
        3,
        "picked up a dry towel, moved the bandana away from the stove, and waved away the smoke",
        "used a dry towel, but the heat was already too much to calm down in time",
        "moved the bandana away from the stove with a dry towel",
    ),
    "open_window": Response(
        "open_window",
        2,
        2,
        "opened the window, turned off the burner, and let the smoky smell drift out",
        "opened the window, but the heat had already spread too far",
        "opened the window and turned off the burner",
    ),
    "ask_help": Response(
        "ask_help",
        3,
        4,
        "called a grown-up right away, who came in quickly and fixed the problem",
        "called for help, but the kitchen was already too hot to make it safe",
        "called a grown-up right away",
    ),
    "water_cup": Response(
        "water_cup",
        1,
        1,
        "threw a cup of water near the stove, which was not the right way to help",
        "threw a cup of water, but it did not solve the problem",
        "threw a cup of water",
    ),
}

SAFE_CHOICES = ["headband", "hair_clip", "apron"]
NAME_PAIRS = [("Mina", "Tess"), ("Lila", "June"), ("Nora", "Pia"), ("Ava", "Mia")]


@dataclass
@dataclass
class StoryParams:
    theme: str
    hazard: str
    response: str
    delay: int = 0
    a_name: str = "Mina"
    a_gender: str = "girl"
    b_name: str = "Tess"
    b_gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(t, h) for t in THEMES for h in HAZARDS if hazard_at_risk(HAZARDS[h])]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    best = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {best}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["friend_a"], f["friend_b"]
    hazard = f["hazard"]
    theme = f["theme"]
    return [
        f'Write a slice-of-life story for a young child that includes the word "bandana" and shows two friends helping each other in a kitchen.',
        f"Tell a gentle cautionary friendship story where {a.id} wants to wear a bandana near a warm stove, but {b.id} notices the risk and helps them choose a safer way.",
        f"Write a happy-ending story set in {theme.id} where a bandana, a warning, and a kind repair all matter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent = f["friend_a"], f["friend_b"], f["parent"]
    hazard = f["hazard"]
    response = f["response"]
    outcome = f["outcome"]
    answers = [
        QAItem(
            question="Who are the story's friends?",
            answer=f"The story is about {a.id} and {b.id}, two friends who were helping in the kitchen. They cared about each other and stayed together through the little problem.",
        ),
        QAItem(
            question="Why did the friend warn about the bandana?",
            answer=f"{b.id} warned because the bandana was too close to the stove. Heat can make cloth get smoky, so the warning was a careful and friendly one.",
        ),
    ]
    if outcome == "contained":
        answers.append(
            QAItem(
                question="How was the problem fixed?",
                answer=f"{parent.label_word.capitalize()} used a calm response and {response.qa_text}. That kept the kitchen safe and let the friends keep playing in a safer way.",
            )
        )
        answers.append(
            QAItem(
                question="What did the friends use at the end?",
                answer=f"They used the safe {world.facts['safe'].label} instead of the bandana near the stove. It was cooler, easier to handle, and much safer for a kitchen game.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="What happened when the heat got too strong?",
                answer="The smoky smell grew worse, and the friends had to back away quickly. They stayed safe, but the moment showed why the warning mattered.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bandana?",
            answer="A bandana is a small cloth square that people can wear on their head, neck, or wrist. It is handy, but it should stay away from hot burners or flames.",
        ),
        QAItem(
            question="Why can a stove be dangerous?",
            answer="A stove can be dangerous because it gets very hot. Hot burners can burn skin or make cloth smoke if it gets too close.",
        ),
        QAItem(
            question="What is a safer choice for hair near heat?",
            answer="A soft headband or a hair clip is safer near heat because it stays cooler and does not brush close to the burner.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.flammable:
            bits.append("flammable")
        if e.wearable:
            bits.append("wearable")
        if e.safe_item:
            bits.append("safe_item")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "bandana_heat", "ask_help", 0, "Mina", "girl", "Tess", "girl", "mother"),
    StoryParams("after_school", "bandana_heat", "open_window", 0, "Lila", "girl", "June", "girl", "mother"),
]


def explain_rejection(hazard: Hazard) -> str:
    return f"(No story: {hazard.label} can be risky near a stove, but this combination does not yet produce a good slice-of-life cautionary scene.)"


ASP_RULES = r"""
hazard(H) :- makes_heat(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, H) :- theme(T), hazard(H), sensible(_).

smoke_risk(B) :- bandana(B), near_stove(B), stove_hot.
contained :- chosen_response(R), power(R, P), delay(D), P >= D + 1.
outcome(contained) :- contained.
outcome(cautionary) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_heat:
            lines.append(asp.fact("makes_heat", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("stove_hot"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_response", params.response), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    samples = list(CURATED)
    for i in range(20):
        try:
            samples.append(resolve_params(build_parser().parse_args([]), _random.Random(i)))
        except StoryError:
            pass
    # smoke test generate
    try:
        sample = generate(samples[0])
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    bad = sum(1 for p in samples if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcomes match Python outcomes on {len(samples)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(samples)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a bandana, a warm stove, friendship, and a safe happy ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    theme = args.theme or rng.choice(list(THEMES))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    na, nb = (args.name_a or rng.choice(["Mina", "Lila", "Nora", "Ava"])), (args.name_b or rng.choice(["Tess", "June", "Pia", "Mia"]))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme, hazard, response, delay, na, "girl", nb, "girl", parent)


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "burned"


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], HAZARDS[params.hazard], RESPONSES[params.response], params.delay,
                 params.a_name, params.a_gender, params.b_name, params.b_gender, params.parent)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, hazard) combos:")
        for t, h in combos:
            print(f"  {t:12} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
