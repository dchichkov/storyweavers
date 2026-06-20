#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/motor_gate_kindness_rhyming_story.py
=====================================================================

A standalone storyworld for a tiny rhyming tale built from the seed words
"motor" and "gate" with a kindness feature.

Premise
-------
A child wants to open a squeaky gate to reach a small play area. A helper
notices a motor with a spinning part, warns kindly, and offers a gentler way.
The child chooses kindness too: they help, fix the problem, and the gate opens
safely. The ending should feel like a short, child-facing rhyming story where
kind actions change the world state.

This world keeps the domain compact and state-driven:
- physical meters: stuck, squeaky, spinning, open, helped, safe_use, worn
- emotional memes: kind, worry, patience, pride, calm, joy, gratitude

It supports:
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- a Python reasonableness gate plus inline ASP twin
- three QA sets generated from world state, not by parsing rendered English
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stuck": 0.0, "squeaky": 0.0, "spinning": 0.0, "open": 0.0, "helped": 0.0, "safe_use": 0.0}
        if not self.memes:
            self.memes = {"kind": 0.0, "worry": 0.0, "patience": 0.0, "pride": 0.0, "calm": 0.0, "joy": 0.0, "gratitude": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    gate_line: str
    rhyme_word: str
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
class Motor:
    id: str
    label: str
    phrase: str
    hum: str
    hazard: str
    safe_fix: str
    spinning: bool = True
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
class HelperTool:
    id: str
    label: str
    phrase: str
    use_line: str
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


def _r_motor_worry(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters.get("spinning", 0.0) < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("child").memes["worry"] += 1
        world.get("helper").memes["calm"] += 1
        out.append("__worry__")
    return out


def _r_gate_stick(world: World) -> list[str]:
    gate = world.get("gate")
    motor = world.get("motor")
    child = world.get("child")
    if gate.meters["open"] >= THRESHOLD:
        return []
    if motor.meters["spinning"] >= THRESHOLD and gate.meters["stuck"] >= THRESHOLD:
        sig = ("stick",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["worry"] += 1
        return ["__gate__"]
    return []


CAUSAL_RULES = [Rule("motor_worry", "social", _r_motor_worry), Rule("gate_stick", "physical", _r_gate_stick)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonableness_ok(place: Place, motor: Motor) -> bool:
    return "gate" in place.tags and "motor" in motor.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MOTORS:
            for r in RESPONSES:
                if reasonableness_ok(PLACES[p], MOTORS[m]):
                    combos.append((p, m, r))
    return combos


def do_rhyme(text: str) -> str:
    return text


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("motor").meters["spinning"] = 1.0
    propagate(sim, narrate=False)
    return {"worry": sim.get("child").memes["worry"], "gate_open": sim.get("gate").meters["open"]}


def tell(place: Place, motor: Motor, response: Response, helper_tool: HelperTool,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         parent_type: str, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the grown-up"))
    gate = world.add(Entity(id="gate", type="gate", label="the gate"))
    gate.meters["stuck"] = 1.0
    gate.meters["squeaky"] = 1.0
    motor_ent = world.add(Entity(id="motor", type="motor", label=motor.label))
    motor_ent.meters["spinning"] = 0.0
    motor_ent.meters["safe_use"] = 0.0
    tool = world.add(Entity(id=helper_tool.id, type="tool", label=helper_tool.label))

    child.memes["joy"] += 1
    helper.memes["patience"] += 1
    world.say(
        f"{child_name} came to {place.label} in the bright morning light, "
        f"where the little gate gave a squeak and a fight. "
        f"{place.setting_line} {place.gate_line}"
    )
    world.say(
        f"{helper_name} saw a {motor.label} by the wall, a humming machine that could startle them all. "
        f'"{motor.hum}," said {helper_name}, "but kindness is best; let us keep things calm and let safety rest."'
    )
    world.para()

    child.memes["kind"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child_name} looked at the gate and then at the motor with care, "
        f"and chose to be gentle instead of a dare. "
        f'"We can help," {child_name} said, "and do it right; kindness can open the gate in the light."'
    )

    motor_ent.meters["spinning"] = 1.0
    motor_ent.meters["helped"] = 0.0
    world.facts["predicted"] = predict(world)
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{helper_name} used {helper_tool.phrase} to steady the latch, while {child_name} gave the gate a kind little patch. "
        f"The squeak turned soft, the stuck part slid, and the gate swung open with a friendly pride."
    )
    gate.meters["open"] = 1.0
    gate.meters["stuck"] = 0.0
    gate.meters["squeaky"] = 0.0
    motor_ent.meters["safe_use"] = 1.0
    child.memes["joy"] += 1
    child.memes["gratitude"] += 1
    helper.memes["pride"] += 1

    world.para()
    world.say(
        f"So {child_name} and {helper_name} walked through the gate, in a kind little row, "
        f"with the motor kept safe and the worries let go. "
        f"The sun on the path made a bright golden plate, and kindness had turned a squeaky old gate."
    )

    world.facts.update(
        child=child, helper=helper, parent=parent, gate=gate, motor=motor_ent,
        place=place, helper_tool=helper_tool, response=response, outcome="opened",
        delay=delay, kindness=True
    )
    return world


PLACES = {
    "garden_gate": Place(
        "garden_gate", "the garden gate",
        "A robin sang by the path, and the flowers swayed in a neat little row.",
        "The gate was old and squeaky, and it liked to stick and slow the day.",
        "gate", {"gate"}
    ),
    "yard_gate": Place(
        "yard_gate", "the yard gate",
        "A breeze blew soft across the grass, and the path shone after rain.",
        "The gate was heavy and tired, and it gave a creak like an old refrain.",
        "gate", {"gate"}
    ),
}

MOTORS = {
    "toy_motor": Motor(
        "toy_motor", "toy motor", "a toy motor", "whirr-whirr", "it could pinch a finger", "let the helper switch it off",
        tags={"motor"}
    ),
    "little_motor": Motor(
        "little_motor", "little motor", "a little motor", "brrr-brrr", "it could scare a small child", "let the helper guide it gently",
        tags={"motor"}
    ),
}

HELPER_TOOLS = {
    "oil_cloth": HelperTool("oil_cloth", "oiled cloth", "an oiled cloth", "wipe the latch with an oiled cloth", {"cloth"}),
    "soft_wrench": HelperTool("soft_wrench", "soft wrench", "a soft little wrench", "turn the latch with a soft little wrench", {"wrench"}),
}

RESPONSES = {
    "gentle_fix": Response(
        "gentle_fix", 3, 3,
        "smiled, used a gentle fix, and eased the gate into place",
        "tried to rush the fix, but the gate stayed stuck and the day grew tense",
        "used a gentle fix and opened the gate",
        tags={"gentle", "kind"}
    ),
    "kindness_pause": Response(
        "kindness_pause", 2, 2,
        "paused, took a breath, and let kindness guide the next step",
        "hurried, and the squeak only got louder",
        "paused and let kindness guide the next step",
        tags={"kind"}
    ),
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, parent, gate, motor = f["child"], f["helper"], f["parent"], f["gate"], f["motor"]
    place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who met by {place.label}. {parent.label_word.capitalize()} was nearby, ready to help if needed."),
        ("What was the problem at the gate?",
         f"The gate was stuck and squeaky, so it would not open easily. The little motor nearby made the moment feel busy and a bit worrisome."),
        ("How did kindness help?",
         f"{child.id} chose to be gentle, and {helper.id} used a careful fix. That kind choice calmed the worry and helped the gate open safely."),
        ("How did the story end?",
         f"The gate swung open, the motor was kept safe, and {child.id} and {helper.id} walked through together. The ending shows that kindness can turn a stuck moment into a happy one."),
    ]
    if f.get("outcome") == "opened":
        qa.append((
            "Why did they not force the gate?",
            f"They did not force it because the gate was stuck and could have made the squeak worse. A gentle fix was better, and that matched the story's kind little lesson."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a gate?",
         "A gate is a door in a fence or wall. People open it to go through and close it to keep a place tidy or safe."),
        ("What is a motor?",
         "A motor is a machine that makes something move or spin. Motors need careful use because they can pinch, buzz, or startle if people are rough."),
        ("What is kindness?",
         "Kindness means being gentle, helpful, and caring. A kind choice can make a hard moment feel calmer."),
    ]
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming story for a young child that includes the words "motor" and "gate" and shows kindness.',
        f"Tell a gentle rhyme about {f['child'].id} and {f['helper'].id} by the gate, where a motor makes the moment feel tricky but kindness helps.",
        "Write a simple rhyming story where a stuck gate is solved by a kind helper instead of by forcing it.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness(M) :- meme(M), M = kind.
gate_opened :- gate(G), open(G).
motor_present :- motor(M).
helpful(M) :- kindness(M).
safe_end :- gate_opened, motor_present, helpful(kind).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MOTORS:
        lines.append(asp.fact("motor", mid))
    for hid in HELPER_TOOLS:
        lines.append(asp.fact("tool", hid))
    lines.append(asp.fact("meme", "kind"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print(" only in ASP:", sorted(cl - py))
        if py - cl:
            print(" only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


@dataclass
@dataclass
class StoryParams:
    place: str
    motor: str
    tool: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about a motor, a gate, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--motor", choices=MOTORS)
    ap.add_argument("--tool", choices=HELPER_TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    motor = args.motor or rng.choice(list(MOTORS))
    tool = args.tool or rng.choice(list(HELPER_TOOLS))
    response = args.response or rng.choice(list(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(["Mia", "Luna", "Niko", "Finn", "Ruby", "Theo"])
    helper = args.helper or rng.choice([n for n in ["Ava", "Ben", "Cora", "Max", "Nora", "Leo"] if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    if place not in PLACES or motor not in MOTORS:
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(place, motor, tool, response, child, child_gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place], MOTORS[params.motor], RESPONSES[params.response], HELPER_TOOLS[params.tool],
        params.child, params.child_gender, params.helper, params.helper_gender, params.parent,
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


CURATED = [
    StoryParams("garden_gate", "toy_motor", "oil_cloth", "gentle_fix", "Mia", "girl", "Ava", "girl", "mother"),
    StoryParams("yard_gate", "little_motor", "soft_wrench", "kindness_pause", "Theo", "boy", "Nora", "girl", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
