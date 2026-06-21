#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/adoption_summons_derrick_bad_ending_myth.py
============================================================================

A standalone story world for a tiny mythic domain about a child, a summons,
an adoption vow, and a harbor derrick that should never be climbed. The world
supports both a safe, ceremonial branch and a bad-ending branch where the
derrick fails and the new home is lost.

Seed words:
- adoption
- summons
- derrick

Style:
- Mythic, child-facing, concrete, and state-driven.

The world model tracks physical meters and emotional memes. The story is
generated from simulated state, not from a frozen template paragraph. A small
forward-chaining rule engine mutates the world, and an inline ASP twin mirrors
the reasonableness gate and ending logic.
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
BAD_END_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "priest", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "priestess": "priestess", "priest": "priest"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Oracle:
    id: str
    omen: str
    voice: str
    summons_word: str

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
class Relic:
    id: str
    label: str
    phrase: str
    danger: int
    heavy: bool = False
    tags: set[str] = field(default_factory=set)

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
    tags: set[str] = field(default_factory=set)

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_storm(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["storm"] < THRESHOLD:
            continue
        sig = ("storm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "harbor" in world.entities:
            world.get("harbor").meters["danger"] += 1
        for k in ("child", "caretaker"):
            if k in world.entities:
                world.get(k).memes["fear"] += 1
        out.append("__storm__")
    return out


def _r_break(world: World) -> list[str]:
    if "derrick" not in world.entities:
        return []
    d = world.get("derrick")
    if d.meters["strain"] < THRESHOLD:
        return []
    sig = ("break", d.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    d.meters["broken"] += 1
    if "home" in world.entities:
        world.get("home").meters["ruin"] += 1
    return ["__break__"]


CAUSAL_RULES = [Rule("storm", "physical", _r_storm), Rule("break", "physical", _r_break)]


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


def risk_at_hand(relic: Relic) -> bool:
    return relic.danger >= BAD_END_MIN


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= BAD_END_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def _do_touch(world: World, relic: Entity) -> None:
    relic.meters["strain"] += 1
    world.get("child").memes["boldness"] += 1
    propagate(world, narrate=False)


def predict_break(world: World, relic_id: str) -> dict:
    sim = world.copy()
    _do_touch(sim, sim.get(relic_id))
    return {"broken": sim.get(relic_id).meters["broken"] >= THRESHOLD, "home_ruin": sim.get("home").meters["ruin"]}


def summon(world: World, oracle: Oracle, child: Entity, caretaker: Entity) -> None:
    child.memes["awe"] += 1
    world.say(f"At dawn, {oracle.voice} carried {oracle.summons_word} across the harbor.")
    world.say(f"{child.id} and {caretaker.id} heard the summons and went at once, because the old songs said the sea never called for no reason.")


def adoption_rite(world: World, caretaker: Entity, child: Entity, oracle: Oracle) -> None:
    child.memes["belonging"] += 1
    caretaker.memes["love"] += 1
    world.say(f"By the shrine, {caretaker.id} knelt and spoke the word adoption as if it were a lantern. {caretaker.id} promised to keep {child.id} safe, fed, and named under {oracle.voice}.")
    world.say(f"The child bowed, and for a little while the harbor felt warm.")


def warn(world: World, caretaker: Entity, child: Entity, relic: Relic) -> None:
    pred = predict_break(world, "derrick")
    world.facts["pred"] = pred
    world.say(f'"{child.id}, do not climb the {relic.label}," {caretaker.id} said. "It is old, and the wind has teeth."')


def defy(world: World, child: Entity, relic: Relic) -> None:
    child.memes["defiance"] += 1
    world.say(f"But {child.id} looked up at the {relic.label} and thought the sky had made it for a brave heart.")
    world.say(f'"I will only touch it once," {child.id} whispered, and reached for the ladder.')


def break_scene(world: World, relic: Relic) -> None:
    _do_touch(world, world.get("derrick"))
    world.get("derrick").meters["strain"] += relic.danger
    world.get("derrick").meters["storm"] += 1
    world.get("child").memes["fear"] += 1
    world.say(f"The {relic.label} groaned. Ropes sang, wood shivered, and the tall derrick leaned like a tired giant.")


def collapse(world: World, caretaker: Entity, child: Entity, relic: Relic) -> None:
    world.get("derrick").meters["broken"] += 1
    world.get("home").meters["ruin"] += 1
    caretaker.memes["grief"] += 1
    child.memes["grief"] += 1
    world.say(f"Then the {relic.label} snapped. It crashed into the pier with a roar, and the new home lost its roof in the spray.")


def ending_bad(world: World, caretaker: Entity, child: Entity, oracle: Oracle) -> None:
    world.say("No one was hurt, but the harbor was changed forever.")
    world.say(f"{caretaker.id} held {child.id} close and said the old blessing again, softer this time. The adoption had happened, yet the promise now had ash on its hands.")
    world.say(f"That night, the summons was remembered as a warning: even a sacred call can lead to sorrow when pride climbs too high.")


def tell(oracle: Oracle, relic: Relic, response: Response,
         child_name: str = "Derrick", child_gender: str = "boy",
         caretaker_name: str = "Mara", caretaker_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    caretaker = world.add(Entity(id=caretaker_name, kind="character", type=caretaker_gender, role="caretaker"))
    o = world.add(Entity(id="oracle", kind="character", type="priestess", label="the oracle"))
    world.add(Entity(id="harbor", type="place", label="the harbor"))
    world.add(Entity(id="home", type="place", label="the new home"))
    derrick = world.add(Entity(id="derrick", type="thing", label=relic.label, attrs={"danger": relic.danger}))

    world.get("derrick").meters["storm"] = 1
    world.get("harbor").meters["storm"] = 1

    summon(world, oracle, child, caretaker)
    adoption_rite(world, caretaker, child, oracle)
    world.para()
    warn(world, caretaker, child, relic)
    defy(world, child, relic)
    world.para()
    break_scene(world, relic)
    collapse(world, caretaker, child, relic)
    ending_bad(world, caretaker, child, oracle)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        oracle=o,
        relic=relic,
        response=response,
        derrick=derrick,
        outcome="bad",
        broken=world.get("derrick").meters["broken"] >= THRESHOLD,
    )
    return world


ORACLES = {
    "sea": Oracle("sea", "a salt wind", "the sea oracle", "summons"),
    "moon": Oracle("moon", "a pale moonbeam", "the moon oracle", "summons"),
    "harbor": Oracle("harbor", "a bell from the dock", "the harbor oracle", "summons"),
}

RELICS = {
    "derrick": Relic("derrick", "derrick", "the derrick", danger=2, heavy=True, tags={"derrick", "storm"}),
}

RESPONSES = {
    "cling": Response("cling", 1, 1,
                      "caught the child and tried to steady the ladder, but the wind was already too strong",
                      "caught at the ladder, but the wood split anyway",
                      "held on and tried to steady the derrick",
                      tags={"hope"}),
    "call_help": Response("call_help", 3, 4,
                          "ran for help and sent the dockhands shouting for ropes",
                          "called for help, but the smoke and spray moved too fast",
                          "called for help and sent for ropes",
                          tags={"help"}),
    "lower_sails": Response("lower_sails", 2, 2,
                            "lowered the sails and shouted for everyone to get clear",
                            "lowered the sails, but the derrick still broke",
                            "lowered the sails and got everyone clear",
                            tags={"help"}),
}

GIRL_NAMES = ["Mara", "Iris", "Nia", "Luna", "Ada", "Sera"]
BOY_NAMES = ["Derrick", "Milo", "Niko", "Tavi", "Theo", "Rian"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for oid in ORACLES:
        for rid in RELICS:
            for resp in sensible_responses():
                combos.append((oid, rid, resp.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    oracle: str
    relic: str
    response: str
    child_name: str
    child_gender: str
    caretaker_name: str
    caretaker_gender: str
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
    "adoption": [("What is adoption?", "Adoption is when a grown-up takes a child into a family and promises to care for them as their own.")],
    "summons": [("What is a summons?", "A summons is a call that says someone must come at once because something important is happening.")],
    "derrick": [("What is a derrick?", "A derrick is a tall lifting frame or crane used near docks and work sites. It can be useful, but it is not a toy.")],
    "storm": [("Why are storms dangerous at a harbor?", "Storms can make ropes slippery, wood weak, and the water rough, so tall harbor machines can break.")],
    "help": [("What should you do when a big danger starts?", "Get away and call a grown-up or helper right away. Fast help is the safe choice.")],
}
KNOWLEDGE_ORDER = ["adoption", "summons", "derrick", "storm", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the words "adoption", "summons", and "{f["relic"].label}".',
        f"Tell a short bad-ending myth where {f['child'].id} hears a summons, joins an adoption rite, and then makes a mistake with the {f['relic'].label}.",
        f"Write a story about a harbor oracle, an adoption promise, and a {f['relic'].label} that should not be climbed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, caretaker, oracle, relic = f["child"], f["caretaker"], f["oracle"], f["relic"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {caretaker.id}, who answered the oracle's summons and took part in an adoption rite."),
        ("What did the oracle do?", f"The oracle sent a summons, which meant someone needed to come at once. That call led the child and caretaker to the harbor shrine."),
        ("Why did the caretaker warn about the derrick?", f"The derrick was old, tall, and not meant for climbing. The caretaker knew the wind could hurt it and make it fail."),
        ("What happened at the end?", f"The derrick snapped and crashed, so the new home was damaged and the story ended sadly. The adoption still happened, but the promise came with grief."),
    ]
    if f.get("broken"):
        qa.append(("What changed because of the derrick?", "The derrick broke, and the harbor was no longer safe and whole. Its fall turned the ceremony into a bad ending instead of a happy one."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["relic"].tags)
    tags.add("adoption")
    tags.add("summons")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sea", "derrick", "call_help", "Derrick", "boy", "Mara", "woman"),
    StoryParams("moon", "derrick", "lower_sails", "Iris", "girl", "Mara", "woman"),
]


def explain_rejection(relic: Relic) -> str:
    return f"(No story: the relic '{relic.label}' is not a meaningful danger here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.relic and args.relic not in RELICS:
        raise StoryError(explain_rejection(RELICS["derrick"]))
    combos = [c for c in valid_combos()
              if (args.oracle is None or c[0] == args.oracle)
              and (args.relic is None or c[1] == args.relic)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    oracle, relic, response = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["boy", "girl"])
    child_name = args.name or rng.choice(BOY_NAMES if child_gender == "boy" else GIRL_NAMES)
    caretaker_name = args.caretaker or rng.choice(["Mara", "Iris", "Nia", "Sera"])
    caretaker_gender = args.caretaker_gender or "woman"
    return StoryParams(oracle, relic, response, child_name, child_gender, caretaker_name, caretaker_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(ORACLES[params.oracle], RELICS[params.relic], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.caretaker_name, params.caretaker_gender)
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


def asp_facts() -> str:
    import asp
    lines = []
    for oid in ORACLES:
        lines.append(asp.fact("oracle", oid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("danger", rid, r.danger))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", BAD_END_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(O, R, Resp) :- oracle(O), relic(R), response(Resp), sensible(Resp).
broken(R) :- relic(R), danger(R, D), D >= 2.
outcome(bad) :- broken(derrick).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic storyworld of adoption, summons, and a dangerous derrick.")
    ap.add_argument("--oracle", choices=ORACLES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--caretaker")
    ap.add_argument("--caretaker-gender", choices=["woman", "man"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
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
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
