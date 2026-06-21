#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deliver_conflict_adventure.py
==============================================================

A standalone storyworld about a small adventure delivery gone wrong:
a child and a helper must deliver a parcel across a tiny, obstacle-filled route,
run into a conflict, then make a careful choice that gets the delivery done.

The world is intentionally simple and classical: typed entities, physical meters,
emotional memes, forward-chained causal rules, a reasonableness gate, and an
inline ASP twin for parity checks.
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
BRAVE_INIT = 5.0
CALM_TRAITS = {"careful", "steady", "patient", "kind", "brave"}
CONFLICT_TRAITS = {"stubborn", "proud", "hasty", "bossy"}

NAMES = {
    "girl": ["Maya", "Luna", "Nora", "Ivy", "Zoe", "Ava"],
    "boy": ["Owen", "Finn", "Eli", "Noah", "Theo", "Leo"],
}
PARTNER_NAMES = {
    "girl": ["Mina", "Pia", "June", "Ruby", "Ella", "Mia"],
    "boy": ["Kai", "Max", "Ben", "Tate", "Jude", "Sam"],
}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Route:
    id: str
    place: str
    obstacle: str
    obstacle_kind: str
    risk: str
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


@dataclass
class Parcel:
    id: str
    label: str
    phrase: str
    recipient: str
    fragile: bool = True
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
class DeliveryTool:
    id: str
    label: str
    phrase: str
    helps: set[str]
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes["conflict"] < THRESHOLD:
            continue
        sig = ("conflict", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        partner = world.get(world.facts["partner"].id)
        char.memes["tension"] += 1
        partner.memes["tension"] += 1
        out.append("__conflict__")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("parcel") is None:
        return out
    parcel = world.facts["parcel"]
    route = world.facts["route"]
    carrier = world.facts["carrier"]
    if carrier.meters["blocked"] < THRESHOLD:
        return out
    sig = ("risk", parcel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parcel.meters["jostled"] += 1
    out.append(f"The parcel bumped hard on the {route.obstacle}.")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("delivered"):
        sig = ("finish", "done")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__finish__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("risk", "physical", _r_risk), Rule("finish", "social", _r_finish)]


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


def route_hazard(route: Route, parcel: Parcel) -> bool:
    return parcel.fragile and route.obstacle_kind in {"wind", "river", "rock", "crowd"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid, route in ROUTES.items():
        for pid, parcel in PARCELS.items():
            for resp in RESPONSES.values():
                if route_hazard(route, parcel) and resp.sense >= 2:
                    combos.append((rid, pid, resp.id))
    return combos


def conflict_clears(trait: str, partner_role: str) -> bool:
    return trait in CALM_TRAITS and partner_role == "helper"


def delivery_success(response: Response, delay: int) -> bool:
    return response.power >= (2 + delay)


def predict_delivery(world: World, route_id: str, parcel_id: str) -> dict:
    sim = world.copy()
    simulate_conflict(sim, narrate=False)
    return {
        "blocked": sim.get("carrier").meters["blocked"] >= THRESHOLD,
        "jostled": sim.get(parcel_id).meters["jostled"] >= THRESHOLD,
    }


def simulate_conflict(world: World, narrate: bool = True) -> None:
    carrier = world.facts["carrier"]
    helper = world.facts["partner"]
    route = world.facts["route"]
    parcel = world.facts["parcel"]
    carrier.memes["conflict"] += 1
    helper.memes["worry"] += 1
    world.say(f"But at the {route.place}, {carrier.id} and {helper.id} both wanted a different way.")
    world.say(f'"{route.risk}," {helper.id} warned. "{parcel.label} could slip there."')


def move_forward(world: World, carrier: Entity, route: Route, parcel: Parcel, tool: DeliveryTool) -> None:
    carrier.meters["blocked"] += 1
    if route.obstacle_kind in tool.helps:
        carrier.meters["blocked"] = 0.0
    parcel.meters["carried"] += 1


def confront(world: World, carrier: Entity, helper: Entity, route: Route, parcel: Parcel) -> None:
    world.say(f'{carrier.id} frowned. "We have to deliver it now," {carrier.pronoun()} said.')
    if carrier.memes["conflict"] >= THRESHOLD:
        world.say(f"{helper.id} crossed {helper.pronoun('possessive')} arms, but kept watching the path.")


def solve_conflict(world: World, carrier: Entity, helper: Entity, response: Response, route: Route, parcel: Parcel) -> bool:
    if conflict_clears(helper.traits[0] if helper.traits else "", "helper"):
        world.say(f'{helper.id} took a slow breath and pointed to the safest path.')
        return True
    world.say(f'{carrier.id} hesitated, then listened anyway when the danger looked real.')
    return True


def deliver_story(world: World, carrier: Entity, helper: Entity, route: Route, parcel: Parcel, tool: DeliveryTool, response: Response, delay: int) -> None:
    world.say(f"On a bright morning, {carrier.id} and {helper.id} set out to deliver {parcel.phrase}.")
    world.say(f"They followed a trail toward {route.place}, where {route.obstacle} waited like a small adventure.")
    world.para()
    simulate_conflict(world)
    confront(world, carrier, helper, route, parcel)
    carrier.memes["conflict"] += 1
    if not solve_conflict(world, carrier, helper, response, route, parcel):
        return
    world.para()
    move_forward(world, carrier, route, parcel, tool)
    if not delivery_success(response, delay):
        world.say(f"Their chosen fix was not enough, and the parcel slipped away into the dust.")
        world.facts["delivered"] = False
        return
    world.facts["delivered"] = True
    parcel.meters["delivered"] += 1
    world.say(f"{helper.id} used {tool.phrase}, and the hard part of the route softened at once.")
    world.say(f"At last they reached the door and delivered the parcel to {parcel.recipient}.")
    world.say(f"The recipient smiled, and the little team headed home with the wind at their backs.")


ROUTES = {
    "bridge": Route(id="bridge", place="the old bridge", obstacle="the swaying boards", obstacle_kind="wind", risk="It could blow the parcel sideways", tags={"bridge", "wind"}),
    "riverbank": Route(id="riverbank", place="the riverbank", obstacle="the muddy stones", obstacle_kind="river", risk="It could tip someone into the water", tags={"river", "mud"}),
    "market": Route(id="market", place="the busy market", obstacle="the crowd", obstacle_kind="crowd", risk="Someone could bump the parcel loose", tags={"crowd"}),
    "trail": Route(id="trail", place="the rocky trail", obstacle="the sharp rocks", obstacle_kind="rock", risk="A stumble could crack the package", tags={"rock"}),
}

PARCELS = {
    "map": Parcel(id="map", label="map case", phrase="a paper map case", recipient="the ranger", fragile=True, tags={"paper"}),
    "glass": Parcel(id="glass", label="glass jar", phrase="a glass jar of berry jam", recipient="the baker", fragile=True, tags={"glass"}),
    "kite": Parcel(id="kite", label="kite box", phrase="a kite box with bright string", recipient="the shopkeeper", fragile=True, tags={"box"}),
}

TOOLS = {
    "rope": DeliveryTool(id="rope", label="rope", phrase="a short rope", helps={"wind", "rock"}, tags={"rope"}),
    "cart": DeliveryTool(id="cart", label="cart", phrase="a small handcart", helps={"crowd", "rock"}, tags={"cart"}),
    "cloth": DeliveryTool(id="cloth", label="cloth wrap", phrase="a cloth wrap", helps={"rock", "wind"}, tags={"cloth"}),
}

RESPONSES = {
    "steady": Response(id="steady", sense=3, power=4, text="tied the parcel down and kept it steady", fail="tried to tie it down, but the parcel still jostled too much", qa_text="tied the parcel down and kept it steady", tags={"steady"}),
    "shield": Response(id="shield", sense=3, power=3, text="covered the parcel with a cloth and kept it from bumping", fail="covered the parcel too late, and it bumped anyway", qa_text="covered the parcel with a cloth", tags={"shield"}),
    "run": Response(id="run", sense=1, power=1, text="ran faster", fail="ran faster, but that only made the parcel shake more", qa_text="ran faster", tags={"run"}),
}

TRAITS = ["careful", "steady", "patient", "kind", "brave", "stubborn"]


@dataclass
class StoryParams:
    route: str
    parcel: str
    tool: str
    response: str
    carrier: str
    carrier_gender: str
    partner: str
    partner_gender: str
    trait: str
    delay: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure delivery storyworld with conflict and a safe resolution.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--carrier")
    ap.add_argument("--partner")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(route: Route, parcel: Parcel) -> str:
    return f"(No story: {route.place} and {parcel.label} do not make a good delivery conflict.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.parcel:
        if not route_hazard(ROUTES[args.route], PARCELS[args.parcel]):
            raise StoryError(explain_rejection(ROUTES[args.route], PARCELS[args.parcel]))
    combos = [c for c in valid_combos()
              if (args.route is None or c[0] == args.route)
              and (args.parcel is None or c[1] == args.parcel)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, parcel, response = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    carrier_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if carrier_gender == "girl" else "girl"
    carrier = args.carrier or rng.choice(NAMES[carrier_gender])
    partner = args.partner or rng.choice(PARTNER_NAMES[partner_gender])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(route=route, parcel=parcel, tool=tool, response=response,
                       carrier=carrier, carrier_gender=carrier_gender,
                       partner=partner, partner_gender=partner_gender, trait=trait,
                       delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES or params.parcel not in PARCELS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("(Invalid params.)")
    world = World()
    carrier = world.add(Entity(id=params.carrier, kind="character", type=params.carrier_gender, role="carrier", traits=[params.trait]))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="helper", traits=["careful"]))
    route = ROUTES[params.route]
    parcel = world.add(Entity(id="parcel", kind="thing", type="parcel", label=PARCELS[params.parcel].label))
    tool = world.add(Entity(id=params.tool, kind="thing", type="tool", label=TOOLS[params.tool].label))
    world.facts.update(carrier=carrier, partner=partner, route=route, parcel=parcel, tool=tool)
    deliver_story(world, carrier, partner, route, parcel, TOOLS[params.tool], RESPONSES[params.response], params.delay)
    world.facts["delivered"] = parcel.meters["delivered"] >= THRESHOLD
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story that includes the word "deliver" and a small conflict over how to get {f["parcel"].label} across {f["route"].place}.',
        f"Tell a child-friendly adventure about {f['carrier'].id} and {f['partner'].id} who must deliver a parcel but argue about the safest path.",
        f"Write a story where a helper warns about a risky route, the conflict is resolved, and the team finishes the delivery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    partner = f["partner"]
    route = f["route"]
    parcel = f["parcel"]
    resp = f["response"]
    qa = [
        ("Who is the story about?", f"It is about {carrier.id} and {partner.id}, who went out to deliver {parcel.label}."),
        ("Why did they argue?", f"They argued because {carrier.id} wanted to push on quickly, but {partner.id} worried about the risky part of {route.place}."),
    ]
    if f.get("delivered"):
        qa.append(("How did the story end?", f"They solved the conflict, used a careful plan, and delivered the parcel safely."))
        qa.append(("What changed by the end?", f"The parcel reached its recipient, and the team was calmer and proud of the delivery."))
    else:
        qa.append(("How did the story end?", f"The delivery did not finish, and the parcel never reached its recipient."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["route"].tags) | set(world.facts["parcel"].tags) | set(world.facts["tool"].tags) | set(world.facts["response"].tags)
    answers = []
    if "wind" in tags:
        answers.append(("What can wind do to a package?", "Wind can push, shake, or blow a package off course if it is not secured well."))
    if "glass" in tags:
        answers.append(("Why is a glass jar fragile?", "Glass can crack or break if it gets bumped or dropped, so it needs careful handling."))
    if "cart" in tags:
        answers.append(("What is a handcart for?", "A handcart helps carry things more steadily over a path, especially if the load is awkward or heavy."))
    if "steady" in tags or "shield" in tags:
        answers.append(("Why help a parcel with a tool?", "A helpful tool can keep a parcel from slipping, bumping, or getting damaged on the way."))
    return answers


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(route="bridge", parcel="glass", tool="rope", response="steady", carrier="Maya", carrier_gender="girl", partner="Kai", partner_gender="boy", trait="careful", delay=0),
    StoryParams(route="market", parcel="map", tool="cart", response="shield", carrier="Owen", carrier_gender="boy", partner="Mina", partner_gender="girl", trait="patient", delay=1),
    StoryParams(route="trail", parcel="glass", tool="cloth", response="steady", carrier="Ivy", carrier_gender="girl", partner="Ben", partner_gender="boy", trait="brave", delay=2),
]


ASP_RULES = r"""
hazard(R, P) :- route(R), parcel(P), fragile(P).
sensible(X) :- response(X), sense(X,S), S >= sense_min(M), M = 2.
valid(R, P, X) :- hazard(R, P), sensible(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for pid in PARCELS:
        lines.append(asp.fact("parcel", pid))
        if PARCELS[pid].fragile:
            lines.append(asp.fact("fragile", pid))
    for xid, x in RESPONSES.items():
        lines.append(asp.fact("response", xid))
        lines.append(asp.fact("sense", xid, x.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
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
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in sensible responses")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
