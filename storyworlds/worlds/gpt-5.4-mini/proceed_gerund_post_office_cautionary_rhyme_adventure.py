#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/proceed_gerund_post_office_cautionary_rhyme_adventure.py
========================================================================================

A standalone story world about a child in a post office who wants to proceed by
doing something risky, but a cautious rhyme turns the choice toward a safer
adventure.

The world is built from typed entities with physical meters and emotional memes,
a small causal engine, a reasonableness gate, an inline ASP twin, and three
Q&A sets grounded in the simulated state.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    dangerous: bool = False
    useful: bool = False

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
class Setting:
    id: str
    label: str
    bustle: str
    afford: set[str] = field(default_factory=set)

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
class Item:
    id: str
    label: str
    phrase: str
    dangerous: bool = False
    useful: bool = False
    tags: set[str] = field(default_factory=set)

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
class Plan:
    id: str
    verb: str
    gerund: str
    risky_action: str
    danger: str
    risk: str
    safe_alternative: str
    zone: str
    tags: set[str] = field(default_factory=set)

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
class Rhyme:
    id: str
    line1: str
    line2: str
    line3: str
    lesson: str
    tags: set[str] = field(default_factory=set)

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
class Response:
    id: str
    sense: int
    power: int
    line: str
    fail: str
    tags: set[str] = field(default_factory=set)

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.meters["spill"] < THRESHOLD:
            continue
        sig = ("spill", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        kid.memes["worry"] += 1
        out.append("__spill__")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("alarm", "social", _r_alarm)]


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


def is_risky(plan: Plan, item: Item) -> bool:
    return plan.danger == item.label and item.dangerous


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for pid, plan in PLANS.items():
            for iid, item in ITEMS.items():
                if is_risky(plan, item):
                    combos.append((sid, pid, iid))
    return combos


def _pick_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def warn_prediction(world: World, kid: Entity, plan: Plan, item_id: str) -> dict:
    sim = world.copy()
    _do_risky(sim, sim.get(kid.id), plan, sim.get(item_id), narrate=False)
    item = sim.get(item_id)
    return {"soiled": item.meters["soaked"] >= THRESHOLD, "mess": sim.get("floor").meters["mess"]}


def _do_risky(world: World, kid: Entity, plan: Plan, item: Entity, narrate: bool = True) -> None:
    item.meters["soaked"] += 1
    kid.memes["daring"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, kid: Entity, parent: Entity, setting: Setting, plan: Plan, item: Item) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"At {setting.label}, {kid.id} and {parent.label_word} moved past the stamps, "
        f"the scales, and the rows of envelopes. {setting.bustle}"
    )
    world.say(
        f'{kid.id} wanted to {plan.verb} and see what would happen, '
        f'but the post office was a place for careful hands.'
    )


def caution(world: World, parent: Entity, kid: Entity, plan: Plan, item: Item, rhyme: Rhyme) -> None:
    pred = warn_prediction(world, kid, plan, item.id)
    world.facts["prediction"] = pred
    world.say(
        f'"{rhyme.line1} {rhyme.line2}" {parent.label_word} said. '
        f'"If you {plan.risky_action}, that {item.label} could get {plan.risk}."'
    )


def choose_safe(world: World, kid: Entity, parent: Entity, plan: Plan, rhyme: Rhyme) -> None:
    kid.memes["prudence"] += 1
    kid.memes["relief"] += 1
    world.say(
        f'{kid.id} slowed down and listened. {rhyme.line3} '
        f'{kid.id} decided to {plan.safe_alternative} instead.'
    )
    world.say(
        f"That turned the moment into a little adventure: they looked for the right counter, "
        f"watched the mail sorter blink, and found a safer way to keep going."
    )


def do_risky(world: World, kid: Entity, plan: Plan, item: Entity) -> None:
    kid.memes["defiance"] += 1
    world.say(
        f'"I can proceed!" {kid.id} said, and tried to {plan.risky_action}. '
        f'The {item.label} tipped and a splash went everywhere.'
    )
    _do_risky(world, kid, plan, item)


def alarm(world: World, kid: Entity, parent: Entity, item: Item) -> None:
    kid.memes["fear"] += 1
    world.say(f'"Oh no!" {kid.id} gasped. "{item.label.capitalize()}!"')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, item: Entity, rhyme: Rhyme) -> None:
    item.meters["soaked"] = 0.0
    world.get("floor").meters["mess"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.line}. "
        f"{rhyme.lesson} The spill was stopped before it could spread."
    )


def lesson(world: World, parent: Entity, kid: Entity, rhyme: Rhyme) -> None:
    kid.memes["love"] += 1
    kid.memes["lesson"] += 1
    kid.memes["fear"] = 0.0
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside {kid.id} and smiled. "
        f'"Brave does not mean rushing," {parent.pronoun()} said. '
        f'"Brave means noticing first, then choosing the safe way."'
    )
    world.say(
        f'{kid.id} nodded. {rhyme.lesson} The rhyme stuck like a friendly sign.'
    )


def ending(world: World, kid: Entity, parent: Entity, plan: Plan, item: Item, rhyme: Rhyme) -> None:
    world.say(
        f"After that, {kid.id} and {parent.id} kept exploring the post office with "
        f"gentle steps. They used the mailbox map, followed the numbered bins, and "
        f"left with the package wrapped tight and dry."
    )
    world.say(
        f"The final sight was small but bright: {kid.id} holding the safe parcel, "
        f"{parent.label_word} smiling, and the rhyme in {rhyme.id} repeating in "
        f"{kid.id}'s head."
    )


def tell(setting: Setting, plan: Plan, item: Item, rhyme: Rhyme, response: Response,
         kid_name: str = "Mia", kid_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    floor = world.add(Entity(id="floor", type="thing", label="the floor"))
    package = world.add(Entity(id="package", type="thing", label=item.label, dangerous=item.dangerous))
    world.facts["setting"] = setting
    world.facts["plan"] = plan
    world.facts["item"] = item
    world.facts["rhyme"] = rhyme
    world.facts["response"] = response

    open_scene(world, kid, parent, setting, plan, item)
    world.para()
    caution(world, parent, kid, plan, item, rhyme)

    if plan.id in {"wait", "ask"}:
        choose_safe(world, kid, parent, plan, rhyme)
        world.facts["outcome"] = "safe"
    else:
        do_risky(world, kid, plan, package)
        alarm(world, kid, parent, item)
        contained = response.power >= 1
        world.facts["outcome"] = "contained" if contained else "lost"
        world.para()
        if contained:
            rescue(world, parent, response, package, rhyme)
            lesson(world, parent, kid, rhyme)
        else:
            world.say(f"{parent.label_word.capitalize()} rushed in, but the mess was too big to stop in time.")
            world.say("They had to back away and get help from a grown-up clerk.")
            lesson(world, parent, kid, rhyme)

    world.para()
    ending(world, kid, parent, plan, item, rhyme)
    world.facts.update(kid=kid, parent=parent, floor=floor, package=package, outcome=world.facts["outcome"])
    return world


SETTINGS = {
    "post_office": Setting(
        id="post_office",
        label="the post office",
        bustle="Behind them, a stamp machine clicked, a printer hummed, and a clerk rolled a cart of parcels by.",
        afford={"proceed", "wait", "ask"},
    )
}

PLANS = {
    "proceed": Plan(
        id="proceed",
        verb="proceed to squeeze the ink bottle open",
        gerund="proceeding with the ink bottle",
        risky_action="squeeze the ink bottle open near the parcel table",
        danger="ink bottle",
        risk="blue",
        safe_alternative="ask for a scrap of paper and wait for help",
        zone="table",
        tags={"proceed-gerund", "adventure"},
    ),
    "wait": Plan(
        id="wait",
        verb="wait by the counter",
        gerund="waiting by the counter",
        risky_action="rush ahead",
        danger="ink bottle",
        risk="blue",
        safe_alternative="wait by the counter and ask for help",
        zone="table",
        tags={"adventure"},
    ),
    "ask": Plan(
        id="ask",
        verb="ask the clerk for a map",
        gerund="asking for a map",
        risky_action="tip the ink bottle",
        danger="ink bottle",
        risk="blue",
        safe_alternative="ask the clerk for a map and wait politely",
        zone="table",
        tags={"adventure"},
    ),
}

ITEMS = {
    "ink bottle": Item("ink bottle", "ink bottle", "a small ink bottle", dangerous=True, tags={"ink", "spill"}),
    "stamp tray": Item("stamp tray", "stamp tray", "a tray of bright stamps", dangerous=False, tags={"stamp"}),
}

RHYMES = {
    "cautionary": Rhyme(
        id="cautionary",
        line1="Slow feet, not quick heat,",
        line2="look first where your hands will meet.",
        line3="The rhyme told the child to look, listen, and lean on care.",
        lesson="Slow is safe, and safe is brave.",
        tags={"cautionary", "rhyme"},
    )
}

RESPONSES = {
    "paper": Response("paper", 3, 2, "grabbed a stack of scrap paper and blotted the spill dry", "tried to blot it dry, but the ink ran everywhere"),
    "cloth": Response("cloth", 2, 1, "used a clean cloth to cover the mess and keep it from spreading", "used a cloth, but the spill was already wider than the cloth"),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Zoe", "Ava"]
BOY_NAMES = ["Eli", "Theo", "Finn", "Noah", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Plan = f["plan"]
    return [
        'Write an adventure-style cautionary rhyme story set in a post office that includes the word "proceed-gerund".',
        f"Tell a post office story where {f['kid'].id} wants to {p.verb}, but a parent sings a cautionary rhyme and guides {f['kid'].id} toward a safer choice.",
        f"Write a child-facing adventure in a post office that teaches careful hands, with a rhyme and a clear ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid: Entity = f["kid"]
    parent: Entity = f["parent"]
    plan: Plan = f["plan"]
    item: Item = f["item"]
    rhyme: Rhyme = f["rhyme"]
    outcome = f["outcome"]
    qa = [
        QAItem(
            question="Where does the story happen?",
            answer="It happens in the post office, among stamps, parcels, and a busy counter. That setting matters because there are many careful things to watch there.",
        ),
        QAItem(
            question=f"What did {kid.id} want to do?",
            answer=f"{kid.id} wanted to {plan.verb}. It sounded adventurous, but it was not the safest choice near the parcel table.",
        ),
        QAItem(
            question="What did the rhyme teach?",
            answer=f"The rhyme taught: '{rhyme.lesson}' It reminded the child to look first and choose the safe way instead of rushing ahead.",
        ),
    ]
    if outcome == "safe":
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended with careful steps and a safer plan. The child stayed dry, the post office stayed calm, and the adventure continued in a gentler way.",
        ))
    else:
        qa.append(QAItem(
            question=f"What happened when {kid.id} ignored the warning?",
            answer=f"The ink bottle tipped and made a spill. The grown-up fixed it quickly so the mess would not spread through the post office.",
        ))
        qa.append(QAItem(
            question=f"How did {parent.label_word} help?",
            answer=f"{parent.label_word.capitalize()} warned first, then came quickly with a sensible response. That kept the trouble small and turned the moment into a lesson.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["plan"].tags) | set(f["item"].tags) | set(f["rhyme"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag]
            out.append(QAItem(q, a))
    return out


KNOWLEDGE = {
    "proceed-gerund": [("What does proceed mean here?",
                        "Here, proceed means to go forward and keep going. It can be fine when you are careful, but not when you rush into danger.")],
    "cautionary": [("What is a cautionary story?",
                   "A cautionary story warns about a mistake so the listener can learn a safer choice. It teaches by showing what to avoid.")],
    "rhyme": [("What is a rhyme?",
               "A rhyme is a pair of lines or words that sound alike at the end. Rhymes can help a lesson stick in your mind.")],
    "adventure": [("What makes a story feel like an adventure?",
                   "An adventure has a goal, a little risk, and a brave choice. It can still be safe and gentle for children.")],
    "ink": [("What is ink?",
             "Ink is the colored liquid inside pens and bottles that makes marks on paper.")],
    "spill": [("Why do people worry about spills?",
               "Spills can make things messy, slippery, or ruined, so people clean them up quickly.")],
}
KNOWLEDGE_ORDER = ["proceed-gerund", "cautionary", "rhyme", "adventure", "ink", "spill"]


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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("risky_action", pid, p.risky_action.replace(" ", "_")))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.dangerous:
            lines.append(asp.fact("dangerous", iid))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
risky(P,I) :- plan(P), item(I), dangerous(I).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,P,I) :- setting(S), plan(P), item(I), risky(P,I).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, plan=None, item=None, response=None, seed=None, all=False,
            trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False,
        ), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Post office cautionary rhyme adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random):
    if args.item and not ITEMS[args.item].dangerous:
        raise StoryError("That item is too harmless for a cautionary spill story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.plan is None or c[1] == args.plan)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, plan, item = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    kid, gender = _pick_name(rng)
    parent = rng.choice(["mother", "father"])
    return StoryParams(setting, plan, item, response, kid, gender, parent)


@dataclass
@dataclass
class StoryParams:
    setting: str
    plan: str
    item: str
    response: str
    kid: str
    gender: str
    parent: str
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PLANS[params.plan], ITEMS[params.item], RHYMES["cautionary"], RESPONSES[params.response], params.kid, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("post_office", "proceed", "ink bottle", "paper", "Mia", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
