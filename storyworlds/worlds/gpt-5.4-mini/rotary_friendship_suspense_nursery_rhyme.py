#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rotary_friendship_suspense_nursery_rhyme.py
===========================================================================

A small storyworld about two friends, a rotary phone, and a gentle suspenseful
miss-and-rescue moment told in a nursery-rhyme-like style.

The premise: one child hears a mysterious ring from an old rotary phone, the
pair grow worried that someone is stuck or in need, and they work together to
solve the little mystery. The turn: they discover the phone is not a danger at
all, but a helpful call from a neighbor, grandparent, or parent. The ending:
their friendship deepens, and the rotary phone becomes a cozy tool for asking
for help.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- forward-chained causal rules
- reasonableness gate
- inline ASP twin
- three QA sets from world state
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    ringable: bool = False
    rotary: bool = False
    helpful: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Character:
    id: str
    type: str
    role: str
    trait: str

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
class Setting:
    id: str
    scene: str
    rhyme: str
    quiet: str
    nearby: str

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
class Signal:
    id: str
    label: str
    source: str
    concern: int
    truth: str
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
    text: str
    fail: str
    qa_text: str
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery") and "house" in world.entities:
        house = world.get("house")
        if house.meters["worry"] < THRESHOLD:
            house.meters["worry"] += 1
            out.append("__spook__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("revealed") and not world.facts.get("answered"):
        for e in list(world.entities.values()):
            if e.role in {"friend1", "friend2"}:
                e.memes["relief"] += 1
                e.memes["joy"] += 1
        world.facts["answered"] = True
        out.append("__comfort__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("comfort", "social", _r_comfort)]


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


def reasonableness_ok(signal: Signal, response: Response) -> bool:
    return signal.concern >= 2 and response.sense >= 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def predict_call(world: World) -> dict:
    sim = world.copy()
    sim.facts["mystery"] = True
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("house").meters["worry"],
        "friends_scared": sum(sim.get(cid).memes["fear"] for cid in ("friend1", "friend2")),
    }


def setup(world: World, setting: Setting, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a hush-hush night in {setting.scene}, {a.id} and {b.id} held hands and whispered low."
    )
    world.say(
        f"{setting.rhyme.capitalize()} {setting.quiet}, and {setting.nearby} made the shadows glow."
    )
    world.say(
        f"'{a.id} and {b.id},' {a.id} said, 'let's keep close and see what we can know.'"
    )


def hear_ring(world: World, signal: Signal, phone: Entity, a: Entity, b: Entity) -> None:
    world.facts["mystery"] = True
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"Then from the corner came a ring-rang-ring from the old {phone.label_word}, rotary and slow."
    )
    world.say(
        f"{a.id} blinked. {b.id} held tight. 'Who could be calling? We ought to go see, not go.'"
    )
    world.say(
        f"It sounded like a little lost secret, tapping in the dark as soft as snow."
    )


def worry(world: World, signal: Signal, a: Entity, b: Entity) -> None:
    pred = predict_call(world)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{a.id} wondered if someone was lonely or stuck, and {b.id} feared the sound might grow."
    )
    world.say(
        f"Together they listened and listened; their hearts beat fast, but their feet stayed in a row."
    )


def answer_phone(world: World, phone: Entity, a: Entity, b: Entity, signal: Signal) -> None:
    world.facts["revealed"] = True
    a.memes["bravery"] += 1
    b.memes["bravery"] += 1
    world.say(
        f"At last {a.id} lifted the rotary receiver, and {b.id} stood by with a brave little 'hello.'"
    )
    world.say(
        f"It was only {signal.source}, kind and warm, with news that made their worry go."
    )
    world.say(
        f"The mystery was not a monster at all; it was a message, cozy and low."
    )


def resolve(world: World, a: Entity, b: Entity, phone: Entity, signal: Signal, response: Response) -> None:
    phone.helpful = True
    if response.id == "ask_softly":
        world.say(
            f"{a.id} used {response.text.replace('{source}', signal.source)}."
        )
    else:
        world.say(
            f"{b.id} used {response.text.replace('{source}', signal.source)}."
        )
    world.say(
        f"{response.qa_text.replace('{source}', signal.source)}"
    )
    a.memes["love"] += 1
    b.memes["love"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1


def ending(world: World, a: Entity, b: Entity, signal: Signal, phone: Entity) -> None:
    world.say(
        f"So the two friends tucked the rotary phone back in its spot and smiled at each other in the glow."
    )
    world.say(
        f"Now when it rang, they knew it could bring a friend, a word, or help they needed most of all below."
    )
    world.say(
        f"Hand in hand, {a.id} and {b.id} sang their little night song, happy as a candle's quiet show."
    )


def tell(setting: Setting, signal: Signal, response: Response, a_name: str = "Mina", a_type: str = "girl",
         b_name: str = "Noah", b_type: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(a_name, kind="character", type=a_type, role="friend1", traits=["kind"]))
    b = world.add(Entity(b_name, kind="character", type=b_type, role="friend2", traits=["careful"]))
    parent = world.add(Entity("Parent", kind="character", type=parent_type, role="helper", label="the grown-up"))
    house = world.add(Entity("house", type="house", label="the house"))
    phone = world.add(Entity("phone", type="thing", label="rotary phone", rotary=True, ringable=True))
    setup(world, setting, a, b)
    world.para()
    hear_ring(world, signal, phone, a, b)
    worry(world, signal, a, b)
    world.para()
    answer_phone(world, phone, a, b, signal)
    resolve(world, a, b, phone, signal, response)
    world.para()
    ending(world, a, b, signal, phone)
    world.facts.update(setting=setting, signal=signal, response=response, friend1=a, friend2=b, parent=parent, house=house, phone=phone)
    return world


SETTINGS = {
    "nursery": Setting("nursery", "a nursery with a moon on the wall", "soft and small", "the lamp was low", "a teddy sat nearby"),
    "kitchen": Setting("kitchen", "a kitchen by the sink and stool", "the kettle was still", "the clock ticked slow", "a warm pie cooled nearby"),
    "hall": Setting("hall", "a long hall by the coat rack", "the echoes were light", "the stair was hushed", "a row of shoes sat nearby"),
}

SIGNALS = {
    "grandma": Signal("grandma", "Grandma's call", "Grandma", 3, "Grandma wanted to say good night", tags={"family", "call"}),
    "neighbor": Signal("neighbor", "the neighbor's call", "the neighbor", 3, "The neighbor needed help finding a cat", tags={"family", "call"}),
    "parent": Signal("parent", "the parent's call", "the grown-up", 3, "The grown-up was calling from outside", tags={"family", "call"}),
}

RESPONSES = {
    "ask_softly": Response("ask_softly", 3, 3, "asked softly, 'Who is there, and what do you need, {source}?'", "asked too loudly and missed the gentle answer", "They asked softly and heard the kind answer from {source}.", tags={"call"}),
    "listen_together": Response("listen_together", 3, 3, "held the receiver together and listened for the answer from {source}", "held the phone but could not hear well enough", "They listened together and heard the answer from {source}.", tags={"call"}),
    "call_back": Response("call_back", 3, 4, "called back right away to {source} and spoke with a steady voice", "called back, but the line stayed silent", "They called back right away and got the answer from {source}.", tags={"call"}),
    "too_quiet": Response("too_quiet", 1, 1, "whispered to the phone and hoped the answer would come", "whispered, but the call still felt lost", "They whispered, but that was not enough to answer the mystery.", tags={"call"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nia", "Ada", "Zoe"]
BOY_NAMES = ["Noah", "Theo", "Owen", "Ezra", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for sig in SIGNALS:
            for resp in sensible_responses():
                if reasonableness_ok(SIGNALS[sig], resp):
                    combos.append((sid, sig, resp.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    signal: str
    response: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
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


KNOWLEDGE = {
    "rotary": [("What is a rotary phone?", "A rotary phone is an old-style phone with a dial that you turn around to make a call.")],
    "call": [("What does a phone call do?", "A phone call lets people talk to each other even when they are far apart.")],
    "family": [("Why do people call family?", "People call family to share news, say hello, or ask for help.")],
    "listen": [("Why is listening important?", "Listening helps you hear the answer, understand the problem, and choose what to do next.")],
    "help": [("What should you do when someone needs help?", "Tell a grown-up right away so the right person can help safely.")],
    "quiet": [("Why can quiet rooms feel suspenseful?", "When a room is very quiet, a tiny sound can feel important and mysterious.")],
}
KNOWLEDGE_ORDER = ["rotary", "call", "family", "listen", "help", "quiet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style friendship story that includes the word "rotary" and a little suspenseful ring from a phone.',
        f"Tell a gentle suspense story where {f['friend1'].id} and {f['friend2'].id} hear a rotary phone ring, worry for a moment, and then solve the mystery kindly.",
        f"Write a short rhyme-like story about two friends, an old rotary phone, and a happy answer at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, signal = f["friend1"], f["friend2"], f["signal"]
    return [
        ("Who is the story about?", f"It is about two friends, {a.id} and {b.id}, who stayed close when the phone rang."),
        ("What made the friends feel suspenseful?", f"The old rotary phone rang in the quiet room, so they worried for a moment about who might need help. The small sound made the night feel mysterious."),
        ("What was the mystery in the story?", f"The mystery was {signal.truth.lower()}. The ring sounded a little scary at first, but it turned out to be a kind message."),
        ("How did the story end?", f"It ended with the friends feeling safe, happy, and closer than before. The rotary phone became a sign that help and friendship could arrive together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rotary", "call", "family", "listen", "help", "quiet"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.rotary:
            bits.append("rotary=True")
        if e.ringable:
            bits.append("ringable=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(signal: Signal, response: Response) -> str:
    return f"(No story: {signal.label} needs a sensible, helpful response. Try one with sense >= 2.)"


def outcome_of(params: StoryParams) -> str:
    return "answered"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        lines.append(asp.fact("concern", sid, s.concern))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(Setting, Signal, Response) :- setting(Setting), signal(Signal), sensible(Response), concern(Signal, C), C >= 2.
"""


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
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if {r.id for r in sensible_responses()} == set(asp_sensible()):
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    # Smoke test generation
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, signal=None, response=None, n=1, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: rotary friendship suspense in a nursery-rhyme style.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_rejection(SIGNALS[args.signal or "grandma"], RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.signal is None or c[1] == args.signal)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, signal, response = rng.choice(sorted(combos))
    f1 = args.friend1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    f1g = "girl" if f1 in GIRL_NAMES else "boy"
    f2_choices = [n for n in (GIRL_NAMES + BOY_NAMES) if n != f1]
    f2 = args.friend2 or rng.choice(f2_choices)
    f2g = "girl" if f2 in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(setting, signal, response, f1, f1g, f2, f2g, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SIGNALS[params.signal], RESPONSES[params.response], params.friend1, params.friend1_gender, params.friend2, params.friend2_gender, params.parent)
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


CURATED = [
    StoryParams("nursery", "grandma", "ask_softly", "Mina", "girl", "Noah", "boy", "mother"),
    StoryParams("kitchen", "neighbor", "listen_together", "Lily", "girl", "Finn", "boy", "grandmother"),
    StoryParams("hall", "parent", "call_back", "Ada", "girl", "Theo", "boy", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, sig, r in asp_valid_combos():
            print(f"  {s:8} {sig:10} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
