#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spurt_robot_beg_repetition_tall_tale.py
=======================================================================

A tall-tale storyworld about a small robot, a big wish, a spurt of mishap,
and a repeated begging chorus that turns the trouble into a cheerful fix.

The story grows from a simple source-tale shape:
- setup: a boastful little robot wants to show off
- tension: a strange spurt interrupts the plan
- turn: the robot must beg for help more than once
- resolution: a clever human answers, and the town ends in a brighter image

The domain is deliberately tiny: one robot, one helper, one fountain-like
machine, one tall-tale problem, and one safe repair. The prose uses repetition
as an instrument: repeated lines, repeated pleas, and repeated action beats.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    scene: str
    items: list[str] = field(default_factory=list)
    supports: str = ""
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
class Machine:
    id: str
    label: str
    phrase: str
    spurt_kind: str
    spurt_name: str
    can_fix: bool = False
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
class Helper:
    id: str
    label: str
    action: str
    answer: str
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
class StoryParams:
    place: str
    machine: str
    helper: str
    robot_name: str
    robot_type: str
    helper_name: str
    helper_type: str
    tone: str = "tall tale"
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_spurt(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["spurt"] < THRESHOLD:
            continue
        sig = ("spurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["astonishment"] += 1
        if "street" in world.entities:
            world.get("street").meters["mess"] += 1
        out.append("__spurt__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    robot = world.get("robot")
    if robot.meters["spurt"] >= THRESHOLD and ("worry", "robot") not in world.fired:
        world.fired.add(("worry", "robot"))
        robot.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("spurt", _r_spurt), Rule("worry", _r_worry)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for machine in MACHINES:
            for helper in HELPERS:
                if PLACES[place].supports == MACHINES[machine].spurt_kind:
                    combos.append((place, machine, helper))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about a robot, a spurt, and repeated begging."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--robot-name")
    ap.add_argument("--robot-type", choices=["robot"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.machine is None or c[1] == args.machine)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, machine, helper = rng.choice(sorted(combos))
    robot_name = args.robot_name or rng.choice(ROBOT_NAMES)
    helper_name = args.helper_name or rng.choice(HUMAN_NAMES)
    robot_type = args.robot_type or "robot"
    helper_type = args.helper_type or rng.choice(["girl", "boy", "woman", "man"])
    return StoryParams(
        place=place, machine=machine, helper=helper,
        robot_name=robot_name, robot_type=robot_type,
        helper_name=helper_name, helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    world = World()
    robot = world.add(Entity(id="robot", kind="character", type=params.robot_type,
                             label=params.robot_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type,
                              label=params.helper_name, role="helper"))
    place = world.add(Entity(id="place", kind="place", type="place",
                             label=PLACES[params.place].label))
    machine = world.add(Entity(id="machine", kind="thing", type="machine",
                               label=MACHINES[params.machine].label))
    world.facts.update(place=params.place, machine=params.machine, helper=params.helper)

    robot.memes["pride"] += 1
    world.say(
        f"Long ago, in {PLACES[params.place].label}, there was a little robot named "
        f"{robot.label}. {robot.label} was small as a stove pin and proud as a peacock."
    )
    world.say(
        f"Every morning {robot.label} wanted to show off beside the {machine.label}."
        f" The machine was famous for a funny {MACHINES[params.machine].spurt_name}."
    )

    world.para()
    world.say(
        f"{robot.label} tapped the lever once, then twice, then once more."
        f" And oh, what a sight! A great {MACHINES[params.machine].spurt_name} spurted"
        f" up like a fountain in boots."
    )
    machine.meters["spurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {MACHINES[params.machine].spurt_name} splashed the floor, the boards,"
        f" and the air itself. It was a grand spurt, a wild spurt, a spurt with whiskers."
    )

    world.para()
    robot.memes["fear"] += 1
    world.say(
        f"{robot.label} froze. {robot.label} looked once, looked twice, and then beggeder"
        f" than a raincloud in a drought."
    )
    world.say(
        f'"Please, please, please help me!" {robot.label} begged. "Please, please, please!"'
    )
    world.say(
        f"{helper.label} came striding in, calm as a porch cat and brisk as a broom."
        f" {helper.label} said, '{HELPERS[params.helper].action}.'"
    )

    world.para()
    world.say(
        f"{helper.label} did {HELPERS[params.helper].answer}, and the spurt settled down."
        f" The machine stopped its bubbling song, and the floor shone wet but safe."
    )
    robot.memes["relief"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f"{robot.label} bowed low and thanked {helper.label} three times over."
        f" 'I begged, and you came,' {robot.label} said. 'I begged, and you fixed it.'"
    )
    world.say(
        f"Then the little robot laughed so hard its bolts seemed to ring like dinner bells,"
        f" and the town went on shining by the light of a clean, clever spurt."
    )

    world.facts.update(robot=robot, helper_ent=helper, place_ent=place, machine_ent=machine)
    return world


def story_qa(world: World) -> list[tuple[str, str]]:
    robot = world.facts["robot"]
    helper = world.facts["helper_ent"]
    machine = world.facts["machine_ent"]
    place = world.facts["place_ent"]
    return [
        ("Who is the story about?",
         f"It is about {robot.label}, a little robot, and {helper.label}, who helped when things went wrong."),
        ("What happened to the machine?",
         f"It made a great spurt that splashed everywhere. The spurt was wild enough to make the robot beg for help."),
        ("What did the robot do when the trouble began?",
         f"{robot.label} begged, 'Please, please, please help me!' and kept begging until help arrived."),
        ("How did the story end?",
         f"The helper fixed the problem, the spurt settled down, and the town stayed bright and safe in {place.label}."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a robot?",
         "A robot is a machine that can move and do jobs. Some robots are small, shiny, and busy all day."),
        ("What does it mean to beg?",
         "To beg means to ask over and over, usually because something is urgent. In stories, begging can show fear or hope."),
        ("What is a spurt?",
         "A spurt is a quick burst that shoots out suddenly, like water from a pipe or juice from a jar."),
    ]


def generation_prompts(world: World) -> list[str]:
    robot = world.facts["robot"]
    helper = world.facts["helper_ent"]
    return [
        f'Write a tall-tale story for a young child that includes the words "spurt", "robot", and "beg".',
        f"Tell a silly story about {robot.label}, a robot who makes a spurt and then has to beg for help more than once.",
        f"Write a repetition-filled tale where {helper.label} saves a robot after a messy spurt.",
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.machine not in MACHINES or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa(world)],
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


ASP_RULES = r"""
valid(P, M, H) :- place(P), machine(M), helper(H), supports(P, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MACHINES:
        lines.append(asp.fact("machine", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for pid, p in PLACES.items():
        for kind in p.supports:
            lines.append(asp.fact("supports", pid, kind))
    for mid, m in MACHINES.items():
        lines.append(asp.fact("spurt_kind", mid, m.spurt_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, machine=None, helper=None, robot_name=None, robot_type=None,
            helper_name=None, helper_type=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


PLACES = {
    "millpond": Place(id="millpond", label="the millpond", scene="a wide millpond",
                      items=["dock", "splash bank"], supports="water"),
    "ferry": Place(id="ferry", label="the ferry dock", scene="a windy ferry dock",
                   items=["planks", "chain rail"], supports="water"),
    "orchard": Place(id="orchard", label="the orchard", scene="a bright orchard",
                     items=["ladder", "apple crates"], supports="sap"),
}

MACHINES = {
    "spout": Machine(id="spout", label="spout machine", phrase="a brass spout machine",
                     spurt_kind="water", spurt_name="water spurt", can_fix=True),
    "pump": Machine(id="pump", label="pump", phrase="an old pump",
                    spurt_kind="water", spurt_name="water spurt", can_fix=True),
    "sapvat": Machine(id="sapvat", label="sap vat", phrase="a sticky sap vat",
                      spurt_kind="sap", spurt_name="sap spurt", can_fix=True),
}

HELPERS = {
    "girl": Helper(id="girl", label="a quick-thinking girl",
                   action="I'll twist the valve and hush the hopper",
                   answer="twisted the valve and hush-hushed the hopper"),
    "boy": Helper(id="boy", label="a lanky boy",
                  action="I'll patch the pipe and pinch the leak",
                  answer="patched the pipe and pinched the leak"),
    "woman": Helper(id="woman", label="a sturdy woman",
                    action="I'll wedge the wheel and mop the mess",
                    answer="wedged the wheel and mopped the mess"),
}

ROBOT_NAMES = ["Rollo", "Bim", "Tinker", "Dot", "Sprocket", "Milo"]
HUMAN_NAMES = ["Nell", "Ira", "June", "Otis", "Mara", "Bea"]


CURATED = [
    StoryParams(place="millpond", machine="spout", helper="girl", robot_name="Rollo", robot_type="robot",
                helper_name="Nell", helper_type="girl"),
    StoryParams(place="ferry", machine="pump", helper="boy", robot_name="Tinker", robot_type="robot",
                helper_name="Ira", helper_type="boy"),
    StoryParams(place="orchard", machine="sapvat", helper="woman", robot_name="Dot", robot_type="robot",
                helper_name="Mara", helper_type="woman"),
]


def generation_prompts_for_verify() -> list[str]:
    return ["Tell a tall-tale story with repetition.", "Include spurt, robot, beg."]


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
