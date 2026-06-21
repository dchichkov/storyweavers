#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/diarrhea_happy_ending_kindness_heartwarming.py
===============================================================================

A standalone story world for a small heartwarming tale about a child who gets
diarrhea, a kind helper, a careful grown-up, and a gentle happy ending.

The world model uses typed entities with physical meters and emotional memes.
The story is driven by state: a tummy trouble begins, someone notices, kindness
changes the mood, a grown-up helps in a sensible way, and the ending proves the
child is safe, cared for, and back to smiling.

This world keeps the prose child-facing and concrete, with a warm tone and a
clear beginning, turn, and resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        for k in ("sick", "rushed", "soothed", "clean", "safe", "helped", "worried", "kindness", "care"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
class Place:
    id: str
    label: str
    setting_line: str
    has_bathroom: bool = True
    has_parent_nearby: bool = True

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
class Trigger:
    id: str
    phrase: str
    start: str
    sign: str
    needs_help: str
    can_wait: bool = False

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
class HelperTool:
    id: str
    label: str
    phrase: str
    comfort_line: str
    clean_line: str
    safe: bool = True

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
    for e in list(world.entities.values()):
        if e.meters["sick"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            for other in list(world.entities.values()):
                if other.kind == "character" and other.id != e.id:
                    other.memes["worried"] += 1
            out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["kindness"] < THRESHOLD or ("kindness", e.id) in world.fired:
            continue
        world.fired.add(("kindness", e.id))
        e.meters["soothed"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("kindness", "social", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TRIGGERS:
            for h in TOOLS:
                if t.can_wait or (p.has_bathroom and h.safe):
                    combos.append((p.id, t.id, h.id))
    return combos


def reasonableness_ok(place: Place, trigger: Trigger, tool: HelperTool) -> bool:
    return place.has_bathroom and tool.safe and trigger.id in {"diarrhea", "tummy_ache"}


def intensity(trigger: Trigger, delay: int) -> int:
    return 2 + delay if trigger.id == "diarrhea" else 1 + delay


def is_controlled(response: Response, trigger: Trigger, delay: int) -> bool:
    return response.power >= intensity(trigger, delay)


def predict_need(world: World, trigger_id: str) -> dict:
    sim = world.copy()
    sim.get("child").meters["sick"] += 1
    propagate(sim, narrate=False)
    return {"worry": sim.get("adult").memes["worried"], "sick": sim.get("child").meters["sick"]}


def tell(place: Place, trigger: Trigger, tool: HelperTool, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Nora", helper_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "mother",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    world.facts["place"] = place
    world.facts["trigger"] = trigger
    world.facts["tool"] = tool
    world.facts["response"] = response
    world.facts["delay"] = delay

    child.memes["joy"] += 1
    helper.memes["kindness"] += 1
    adult.memes["care"] += 1

    world.say(
        f"At {place.label}, {child_name} was having a happy day with {helper_name}. "
        f"{place.setting_line}"
    )
    world.say(
        f"Then {child_name} felt a sudden tummy twist. {trigger.start} {child.pronoun()} needed help fast."
    )
    world.para()
    world.say(
        f"{helper_name} noticed right away and stayed close. "
        f'"That looks like {trigger.sign}," {helper_name} said softly. '
        f'"Let\'s get a grown-up and keep you comfortable."'
    )

    child.meters["sick"] += 1
    child.memes["worried"] += 1
    child.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    adult.memes["care"] += 1
    predicted = predict_need(world, "diarrhea")
    world.facts["predicted_worry"] = predicted["worry"]

    world.say(
        f"{child_name} nodded, a little embarrassed, but {helper_name} took {child.pronoun('possessive')} hand. "
        f"{adult_name} came quickly, smiling kindly and already knowing how to help."
    )

    if trigger.id == "diarrhea":
        world.say(
            f'"No one is in trouble," {adult_name} said gently. '
            f'"We will clean up, wash hands, and let your tummy rest."'
        )
    else:
        world.say(
            f'"No one is in trouble," {adult_name} said gently. '
            f'"We will clean up and help your tummy rest."'
        )

    world.say(
        f"{adult_name} used {tool.phrase}, and {tool.comfort_line}. "
        f"{tool.clean_line}."
    )
    child.meters["sick"] = 0.0
    child.meters["clean"] += 1
    child.meters["safe"] += 1
    child.memes["soothed"] += 1
    child.memes["worried"] = 0.0
    helper.memes["safe"] += 1
    adult.memes["care"] += 1

    world.para()
    world.say(
        f"After that, {child_name} rested on a soft couch with a blanket and a sip of water. "
        f"{helper_name} stayed nearby, and {adult_name} read a calm story."
    )
    world.say(
        f"Before long, {child_name} felt much better, and even smiled at a tiny joke from {helper_name}. "
        f"The room felt warm again, and the scary moment had turned into a tender one."
    )
    world.say(
        f"By the end, {child_name} was clean, safe, and cuddled close to {adult_name}, "
        f"while {helper_name} grinned because kindness had made the whole day kinder."
    )

    world.facts.update(
        child=child, helper=helper, adult=adult, room=room, outcome="happy",
        cleaned=True, soothed=True, trigger_story=trigger.id,
    )
    return world


PLACES = [
    Place("kitchen", "the kitchen", "The kitchen smelled like toast, and a sunny chair sat by the table."),
    Place("living_room", "the living room", "The living room had a blanket on the sofa and a quiet lamp nearby."),
    Place("school", "the classroom", "The classroom had little chairs, a calm corner, and a sink close by."),
]

TRIGGERS = [
    Trigger("diarrhea", "diarrhea", "It was diarrhea.", "a messy tummy sign", "clean up and rest"),
    Trigger("tummy_ache", "a tummy ache", "Her tummy hurt all of a sudden.", "a sick tummy sign", "rest and water", can_wait=True),
]

TOOLS = [
    HelperTool("change", "clean clothes", "clean clothes and a fresh towel", "wrapped the child in a soft towel", "set out fresh clothes and helped with a quick clean-up"),
    HelperTool("bathroom", "the bathroom", "the bathroom", "opened the bathroom door and turned on the light", "kept everything private and calm"),
    HelperTool("water", "water and soap", "water and soap", "washed hands with warm soap and water", "helped everyone wash up carefully"),
]

RESPONSES = {
    "gentle_help": Response("gentle_help", 3, 4,
                            "helped right away with calm hands and a kind voice",
                            "tried to help, but the problem was already too messy",
                            "helped right away with calm hands and a kind voice"),
    "quick_clean": Response("quick_clean", 2, 3,
                            "cleaned up quickly, changed the clothes, and made the child feel private and safe",
                            "worked quickly, but still could not keep up",
                            "cleaned up quickly, changed the clothes, and made the child feel private and safe"),
    "hug_and_water": Response("hug_and_water", 2, 2,
                              "gave a hug, a sip of water, and a fresh blanket",
                              "gave comfort, but it was not enough to settle the child yet",
                              "gave a hug, a sip of water, and a fresh blanket"),
}

NAMES = ["Mia", "Noah", "Lily", "Eli", "Ava", "Theo", "Nora", "Sam"]
TRAITS = ["gentle", "kind", "careful", "patient", "warm"]


@dataclass
@dataclass
class StoryParams:
    place: str
    trigger: str
    tool: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
    delay: int = 0
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


KNOWLEDGE = {
    "diarrhea": [("What is diarrhea?", "Diarrhea is when a person has very loose, runny poop and needs a bathroom quickly.")],
    "kindness": [("What is kindness?", "Kindness means helping, sharing, and using gentle words so someone feels cared for.")],
    "water": [("Why do people wash their hands after using the bathroom?", "Washing hands with soap and water helps remove germs and keeps people healthier.")],
    "blanket": [("Why can a blanket help a sick child?", "A blanket can help a child feel warm, safe, and comforted while they rest.")],
    "privacy": [("Why do people close the bathroom door?", "A closed bathroom door helps give privacy, which makes a child feel more comfortable and calm.")],
}

KNOWLEDGE_ORDER = ["diarrhea", "kindness", "water", "blanket", "privacy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p, t, tool = f["place"], f["trigger"], f["tool"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "{t.id}" and ends happily.',
        f"Tell a kind story where a child at {p.label} has diarrhea, a friend helps, and a grown-up responds with patience.",
        f"Write a gentle story about {t.sign}, clean-up, and kindness, with a happy ending and caring words.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult = f["child"], f["helper"], f["adult"]
    place, trigger, tool = f["place"], f["trigger"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {adult.label_word}. They are the ones who turn a scary moment into a caring one."),
        ("What happened to the child?",
         f"{child.id} got diarrhea and needed help quickly. That is why the story moves from play to gentle care."),
        ("How did the helper act?",
         f"{helper.id} noticed right away, held {child.pronoun('possessive')} hand, and stayed kind. That kindness helped the child feel less embarrassed."),
    ]
    qa.append((
        "How did the grown-up help?",
        f"{adult.label_word.capitalize()} came quickly, cleaned things up, and helped {child.id} rest. {adult.label_word.capitalize()} also made sure nobody felt ashamed, which turned the moment into a safe one."
    ))
    qa.append((
        "How did the story end?",
        f"It ended happily, with {child.id} clean, safe, and smiling again. {helper.id} and {adult.label_word} stayed close, so the child felt cared for."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"diarrhea", "kindness", "water", "blanket", "privacy"}
    return [qa for tag in KNOWLEDGE_ORDER if tag in tags for qa in KNOWLEDGE[tag]]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("living_room", "diarrhea", "change", "quick_clean", "Mia", "girl", "Nora", "girl", "Mom", "mother", 0),
    StoryParams("kitchen", "diarrhea", "water", "gentle_help", "Noah", "boy", "Lily", "girl", "Dad", "father", 0),
    StoryParams("school", "diarrhea", "bathroom", "hug_and_water", "Ava", "girl", "Eli", "boy", "Mom", "mother", 0),
]


def explain_rejection(place: Place, trigger: Trigger, tool: HelperTool) -> str:
    return f"(No story: this setup is not a sensible kind and safe diaper-change story.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        if p.has_bathroom:
            lines.append(asp.fact("has_bathroom", p.id))
    for t in TRIGGERS:
        lines.append(asp.fact("trigger", t.id))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        if tool.safe:
            lines.append(asp.fact("safe", tool.id))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
        lines.append(asp.fact("power", r.id, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,O) :- place(P), trigger(T), tool(O), has_bathroom(P), safe(O), trigger(T).
controlled(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show controlled/1."))
    return sorted(r for (r,) in asp.atoms(model, "controlled"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if not sample_smoke():
        rc = 1
    return rc


def sample_smoke() -> bool:
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        return True
    except Exception as e:
        print(f"SMOKE FAILED: {e}")
        return False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming diarrhea kindness story world.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--trigger", choices=[t.id for t in TRIGGERS])
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--response", choices=list(RESPONSES))
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--adult-name")
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
    if not combos:
        raise StoryError("No valid stories available.")
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.trigger:
        combos = [c for c in combos if c[1] == args.trigger]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trigger, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    adult_gender = rng.choice(["mother", "father"])
    return StoryParams(
        place, trigger, tool, response,
        args.child_name or rng.choice(NAMES),
        child_gender,
        args.helper_name or rng.choice([n for n in NAMES if n != args.child_name]),
        helper_gender,
        args.adult_name or ("Mom" if adult_gender == "mother" else "Dad"),
        adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[[p.id for p in PLACES].index(params.place)],
        TRIGGERS[[t.id for t in TRIGGERS].index(params.trigger)],
        TOOLS[[t.id for t in TOOLS].index(params.tool)],
        RESPONSES[params.response],
        params.child_name, params.child_gender,
        params.helper_name, params.helper_gender,
        params.adult_name, params.adult_gender,
        params.delay,
    )
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
        print(asp_program("", "#show valid/3.\n#show controlled/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
