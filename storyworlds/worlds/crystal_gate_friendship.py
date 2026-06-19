#!/usr/bin/env python3
"""
A standalone storyworld for this seed:

    Words: quiet hill, crystal gate
    Features: Conflict, Problem Solving, Friendship
    Style: Tall Tale

Two friends climb a quiet hill and find a crystal gate. The gate responds to
their relationship state, so a quarrel is not decorative: conflict drains the
gate, a compatible repair rebuilds friendship, and only then can the gate open.
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
FRIENDSHIP_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    need: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "sister"}
        male = {"boy", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Hill:
    id: str
    phrase: str
    marvel: str
    affords: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Gate:
    id: str
    phrase: str
    shimmer: str
    need: str
    beyond: str
    tall: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quarrel:
    id: str
    object: str
    reason: str
    need: str
    sting: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    action: str
    solves: set[str]
    virtues: set[str]
    friendship: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, hill: Hill) -> None:
        self.hill = hill
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.hill)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _friends(world: World) -> tuple[Optional[Entity], Optional[Entity]]:
    return world.entities.get("a"), world.entities.get("b")


def _r_conflict_dims_gate(world: World) -> list[str]:
    a, b = _friends(world)
    gate = world.entities.get("gate")
    if not a or not b or not gate:
        return []
    if a.memes["conflict"] < THRESHOLD and b.memes["conflict"] < THRESHOLD:
        return []
    sig = ("dim", gate.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["dim"] += 1
    gate.meters["closed"] = 1
    return ["__dim__"]


def _r_repair_friendship(world: World) -> list[str]:
    a, b = _friends(world)
    repair = world.entities.get("repair")
    if not a or not b or not repair or repair.meters["done"] < THRESHOLD:
        return []
    sig = ("friendship", repair.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["friendship"] += repair.meters["friendship"]
    b.memes["friendship"] += repair.meters["friendship"]
    return ["__friendship__"]


def _r_open_gate(world: World) -> list[str]:
    a, b = _friends(world)
    gate = world.entities.get("gate")
    repair = world.entities.get("repair")
    if not a or not b or not gate or not repair:
        return []
    if gate.need not in repair.traits:
        return []
    if min(a.memes["friendship"], b.memes["friendship"]) < FRIENDSHIP_MIN:
        return []
    sig = ("open", gate.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["closed"] = 0.0
    gate.meters["open"] = 1
    gate.meters["dim"] = 0.0
    return ["__open__"]


CAUSAL_RULES = [
    Rule("conflict_dims_gate", "social", _r_conflict_dims_gate),
    Rule("repair_friendship", "social", _r_repair_friendship),
    Rule("open_gate", "physical", _r_open_gate),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    made: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                made.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in made:
            world.say(sent)
    return made


def repair_answers(repair: Repair, quarrel: Quarrel) -> bool:
    return quarrel.need in repair.solves and repair.friendship >= FRIENDSHIP_MIN


def gate_accepts(repair: Repair, gate: Gate) -> bool:
    return gate.need in repair.virtues


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hill_id, hill in HILLS.items():
        for gate_id in sorted(hill.affords):
            gate = GATES[gate_id]
            for quarrel_id, quarrel in QUARRELS.items():
                for repair_id, repair in REPAIRS.items():
                    if repair_answers(repair, quarrel) and gate_accepts(repair, gate):
                        combos.append((hill_id, gate_id, quarrel_id, repair_id))
    return combos


def predict_gate(world: World, repair: Repair) -> dict:
    sim = world.copy()
    rep = sim.get("repair")
    rep.meters["done"] = 1
    rep.meters["friendship"] = repair.friendship
    rep.traits = sorted(repair.virtues)
    propagate(sim, narrate=False)
    gate = sim.get("gate")
    return {
        "opens": gate.meters["open"] >= THRESHOLD,
        "friendship": min(sim.get("a").memes["friendship"], sim.get("b").memes["friendship"]),
    }


def introduce(world: World, a: Entity, b: Entity, hill: Hill) -> None:
    world.say(
        f"Once, in a valley so wide that a sneeze needed three echoes to cross it, "
        f"{a.id} and {b.id} climbed {hill.phrase}."
    )
    world.say(
        f"The hill was called quiet because even the grass whispered politely, "
        f"but that day {hill.marvel}"
    )


def discover_gate(world: World, gate_cfg: Gate) -> None:
    gate = world.add(Entity("gate", type="gate", label=gate_cfg.phrase, need=gate_cfg.need))
    gate.meters["closed"] = 1
    world.say(
        f"At the top stood {gate_cfg.phrase}. {gate_cfg.shimmer} "
        f"Beyond it, they could see {gate_cfg.beyond}."
    )


def quarrel(world: World, a: Entity, b: Entity, q: Quarrel) -> None:
    a.memes["want"] += 1
    b.memes["want"] += 1
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(
        f"Then the trouble started over {q.object}. {a.id} said {q.reason}, "
        f"and {b.id} said it just as loudly back."
    )
    propagate(world, narrate=False)
    world.say(
        f"The crystal gate heard every sharp word. Its colors shrank to a thin "
        f"gray line, and {q.sting}"
    )


def think(world: World, a: Entity, b: Entity, gate: Gate, repair: Repair) -> None:
    rep = world.add(Entity("repair", type="repair", label=repair.label,
                           traits=sorted(repair.virtues)))
    pred = predict_gate(world, repair)
    world.facts["predicted_gate"] = pred
    world.say(
        f"{a.id} and {b.id} sat on the quiet hill and thought until the clouds "
        f"looked bored. The gate did not need a kick. It needed {gate.need}."
    )
    world.say(
        f'"Maybe {repair.label} would work," said {b.id}. '
        f'"It answers the fight instead of winning it."'
    )


def repair_friendship(world: World, a: Entity, b: Entity, repair: Repair) -> None:
    rep = world.get("repair")
    world.say(f"So the two friends {repair.action}.")
    rep.meters["done"] = 1
    rep.meters["friendship"] = repair.friendship
    rep.traits = sorted(repair.virtues)
    propagate(world, narrate=False)


def open_gate(world: World, a: Entity, b: Entity, gate: Gate) -> None:
    actual = world.get("gate")
    if actual.meters["open"] >= THRESHOLD:
        a.memes["joy"] += 1
        b.memes["joy"] += 1
        world.say(
            f"The crystal gate rang like a spoon on a star. {gate.tall} "
            f"It swung open wide enough for friendship, which is wider than it sounds."
        )
        world.say(
            f"{a.id} and {b.id} walked through together, still disagreeing about "
            f"small things, but no longer letting small things become walls."
        )
    else:
        world.say(
            f"The gate stayed shut, so {a.id} and {b.id} decided to ask for help "
            f"before trying again."
        )


def tell(hill: Hill, gate: Gate, quarrel_cfg: Quarrel, repair: Repair,
         name_a: str, gender_a: str, name_b: str, gender_b: str,
         trait_a: str, trait_b: str) -> World:
    world = World(hill)
    a = world.add(Entity("a", kind="character", type=gender_a, label=name_a,
                         traits=[trait_a], role="friend"))
    b = world.add(Entity("b", kind="character", type=gender_b, label=name_b,
                         traits=[trait_b], role="friend"))
    a.id = name_a
    b.id = name_b
    world.entities["a"] = a
    world.entities["b"] = b
    a.memes["friendship"] = 1
    b.memes["friendship"] = 1
    introduce(world, a, b, hill)
    discover_gate(world, gate)
    world.para()
    quarrel(world, a, b, quarrel_cfg)
    world.para()
    think(world, a, b, gate, repair)
    repair_friendship(world, a, b, repair)
    open_gate(world, a, b, gate)
    world.facts.update(a=a, b=b, hill=hill, gate_cfg=gate, quarrel=quarrel_cfg,
                       repair=repair, opened=world.get("gate").meters["open"] >= THRESHOLD)
    return world


HILLS = {
    "quiet": Hill("quiet", "the quiet hill", "a moon-sized shadow rolled uphill instead of down.",
                  {"rainbow", "echo"}, {"quiet_hill", "hill"}),
    "thimble": Hill("thimble", "Thimbletop Hill", "the daisies wore hats as large as dinner plates.",
                    {"rainbow", "honest"}, {"quiet_hill", "tall_tale"}),
    "sleepy": Hill("sleepy", "the sleepy green hill", "a cloud was napping on the path and snoring snowflakes.",
                   {"echo", "honest"}, {"quiet_hill", "hill"}),
}

GATES = {
    "rainbow": Gate("rainbow", "a crystal gate striped with seven colors",
                    "It shimmered like a jar of rainbows being gently shaken.",
                    "sharing", "a meadow where giant strawberries rang like bells",
                    "Seven colors leaped back into the bars.", {"crystal", "gate", "sharing"}),
    "echo": Gate("echo", "a crystal gate full of tiny echoes",
                 "Every whisper bounced inside it and came back kinder.",
                 "listening", "a creek that told jokes in silver bubbles",
                 "The echoes lined up and made a shining doorway.", {"crystal", "gate", "listening"}),
    "honest": Gate("honest", "a clear crystal gate with no place to hide a fib",
                   "It was so clear they could see tomorrow polishing its shoes.",
                   "honesty", "a road paved with blue marbles and warm sunlight",
                   "The clear bars flashed bright as clean water.", {"crystal", "gate", "honesty"}),
}

QUARRELS = {
    "map": Quarrel("map", "the only map", '"I should carry it because I saw the hill first"',
                   "sharing", "the latch grew colder than a snowman's pocket.", {"map", "sharing"}),
    "echo": Quarrel("echo", "whose echo sounded biggest", '"My echo is the boss echo"',
                    "listening", "the gate stopped repeating them at all.", {"echo", "listening"}),
    "shortcut": Quarrel("shortcut", "which shortcut was true", '"My way is right and yours is silly"',
                        "honesty", "a cloudy crack ran down the crystal.", {"honesty", "problem_solving"}),
}

REPAIRS = {
    "take_turns": Repair("take_turns", "taking turns",
                         "folded the map once for each hand and agreed to carry it together",
                         {"sharing"}, {"sharing"}, 2, {"sharing", "friendship"}),
    "listen_back": Repair("listen_back", "listening first",
                          "each repeated the other friend's idea before adding a new one",
                          {"listening"}, {"listening"}, 2, {"listening", "friendship"}),
    "truth_test": Repair("truth_test", "testing the truth together",
                         "checked both shortcuts with pebble marks and admitted which path was safer",
                         {"honesty"}, {"honesty"}, 2, {"honesty", "problem_solving"}),
    "sorry_share": Repair("sorry_share", "saying sorry and sharing",
                          "said sorry, split the job fairly, and put both hands on the latch",
                          {"sharing", "listening"}, {"sharing", "listening"}, 3, {"friendship"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Eli"]
TRAITS = ["bold", "patient", "curious", "kind", "quick", "thoughtful"]


@dataclass
class StoryParams:
    hill: str
    gate: str
    quarrel: str
    repair: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "quiet_hill": [("What is a hill?", "A hill is a raised part of the land, smaller than a mountain.")],
    "crystal": [("What is crystal?", "Crystal is a hard material that can be clear and shiny, like glass or ice.")],
    "gate": [("What does a gate do?", "A gate opens and closes a way through a fence, wall, or special entrance.")],
    "sharing": [("Why is sharing useful?", "Sharing lets people use something fairly, so one person does not take all of it.")],
    "listening": [("Why does listening help friends?", "Listening shows you care about what the other person means, not just what you want to say next.")],
    "honesty": [("Why is honesty important?", "Honesty helps people solve the real problem because they are not hiding or pretending.")],
    "friendship": [("What makes a friendship stronger?", "Friendship grows stronger when people are kind, listen, apologize, and solve problems together.")],
    "problem_solving": [("What is problem solving?", "Problem solving means looking at what is wrong and trying a plan that truly fixes it.")],
}
KNOWLEDGE_ORDER = ["quiet_hill", "crystal", "gate", "sharing", "listening",
                   "honesty", "friendship", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, hill, gate = f["a"], f["b"], f["hill"], f["gate_cfg"]
    return [
        'Write a tall tale for young children that includes "quiet hill" and "crystal gate".',
        f"Tell a friendship story where {a.id} and {b.id} argue on {hill.phrase}, then solve the problem so {gate.phrase} can open.",
        "Write a playful story where a magical gate responds to friendship, not pushing or shouting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["a"], f["b"]
    hill, gate, quarrel_cfg, repair = f["hill"], f["gate_cfg"], f["quarrel"], f["repair"]
    return [
        ("Who is the story about?",
         f"It is about two friends, {a.id} and {b.id}, who climbed {hill.phrase}."),
        ("What did they find on the hill?",
         f"They found {gate.phrase}. It would not open while they were arguing."),
        ("Why did the gate become dim?",
         f"The friends argued over {quarrel_cfg.object}, and the conflict made the crystal gate lose its shine. Both friends were stuck in the quarrel until they repaired it together."),
        ("How did they solve the problem?",
         f"They solved it by {repair.label}. That repair matched the real quarrel, rebuilt their friendship, and gave the gate the {gate.need} it needed."),
        ("What happened at the end?",
         f"The crystal gate opened after their friendship was repaired. {a.id} and {b.id} walked through together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["hill"].tags) | set(f["gate_cfg"].tags) | set(f["quarrel"].tags) | set(f["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.need:
            bits.append(f"need={e.need}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("quiet", "rainbow", "map", "take_turns", "Lily", "girl", "Tom", "boy", "curious", "bold"),
    StoryParams("quiet", "echo", "echo", "listen_back", "Mia", "girl", "Ben", "boy", "patient", "quick"),
    StoryParams("thimble", "honest", "shortcut", "truth_test", "Zoe", "girl", "Sam", "boy", "kind", "thoughtful"),
    StoryParams("sleepy", "echo", "map", "sorry_share", "Ava", "girl", "Leo", "boy", "bold", "patient"),
]


def explain_rejection(gate: Gate, quarrel_cfg: Optional[Quarrel], repair: Optional[Repair]) -> str:
    if quarrel_cfg and repair and not repair_answers(repair, quarrel_cfg):
        return (f"(No story: {repair.label} does not answer the fight over "
                f"{quarrel_cfg.object}; the repair must solve {quarrel_cfg.need}.)")
    if repair and not gate_accepts(repair, gate):
        return (f"(No story: {gate.phrase} needs {gate.need}, but {repair.label} "
                f"does not carry that virtue.)")
    return "(No story: the hill, gate, quarrel, and repair are not compatible.)"


ASP_RULES = r"""
answers(R, Q) :- repair(R), quarrel(Q), solves(R, Need), quarrel_need(Q, Need),
                 friendship_power(R, P), friendship_min(M), P >= M.
accepted(R, G) :- repair(R), gate(G), virtue(R, Need), gate_need(G, Need).
valid(H, G, Q, R) :- hill(H), affords(H, G), answers(R, Q), accepted(R, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("friendship_min", FRIENDSHIP_MIN)]
    for hid, hill in HILLS.items():
        lines.append(asp.fact("hill", hid))
        for gid in sorted(hill.affords):
            lines.append(asp.fact("affords", hid, gid))
    for gid, gate in GATES.items():
        lines.append(asp.fact("gate", gid))
        lines.append(asp.fact("gate_need", gid, gate.need))
    for qid, quarrel_cfg in QUARRELS.items():
        lines.append(asp.fact("quarrel", qid))
        lines.append(asp.fact("quarrel_need", qid, quarrel_cfg.need))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("friendship_power", rid, repair.friendship))
        for need in sorted(repair.solves):
            lines.append(asp.fact("solves", rid, need))
        for virtue in sorted(repair.virtues):
            lines.append(asp.fact("virtue", rid, virtue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: quiet hill, crystal gate, friendship.")
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--gate", choices=GATES)
    ap.add_argument("--quarrel", choices=QUARRELS)
    ap.add_argument("--repair", choices=REPAIRS)
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gate = GATES[args.gate] if args.gate else None
    quarrel_cfg = QUARRELS[args.quarrel] if args.quarrel else None
    repair = REPAIRS[args.repair] if args.repair else None
    if gate and quarrel_cfg and repair:
        if not repair_answers(repair, quarrel_cfg) or not gate_accepts(repair, gate):
            raise StoryError(explain_rejection(gate, quarrel_cfg, repair))
    elif quarrel_cfg and repair and not repair_answers(repair, quarrel_cfg):
        fake_gate = next(iter(GATES.values()))
        raise StoryError(explain_rejection(fake_gate, quarrel_cfg, repair))
    elif gate and repair and not gate_accepts(repair, gate):
        raise StoryError(explain_rejection(gate, None, repair))
    combos = [c for c in valid_combos()
              if (args.hill is None or c[0] == args.hill)
              and (args.gate is None or c[1] == args.gate)
              and (args.quarrel is None or c[2] == args.quarrel)
              and (args.repair is None or c[3] == args.repair)]
    if not combos:
        raise StoryError("(No valid crystal-gate story matches the given options.)")
    hill, gate_id, quarrel_id, repair_id = rng.choice(sorted(combos))
    name_a, gender_a = _pick_child(rng)
    name_b, gender_b = _pick_child(rng, avoid=name_a)
    trait_a, trait_b = rng.sample(TRAITS, 2)
    return StoryParams(hill, gate_id, quarrel_id, repair_id,
                       name_a, gender_a, name_b, gender_b, trait_a, trait_b)


def generate(params: StoryParams) -> StorySample:
    world = tell(HILLS[params.hill], GATES[params.gate], QUARRELS[params.quarrel],
                 REPAIRS[params.repair], params.name_a, params.gender_a,
                 params.name_b, params.gender_b, params.trait_a, params.trait_b)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hill, gate, quarrel, repair) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{part:12}" for part in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} & {p.name_b}: {p.gate} / {p.quarrel} / {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
