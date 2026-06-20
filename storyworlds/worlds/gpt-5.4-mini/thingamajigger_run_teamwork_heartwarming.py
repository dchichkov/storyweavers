#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thingamajigger_run_teamwork_heartwarming.py
=============================================================================

A standalone story world for a small heartwarming teamwork tale: a child and a
helper race to finish a silly "thingamajigger" before a family gathering, the
first attempt goes wrong, and then everyone works together to repair it, run it
to the right place, and end with a warm, shared smile.

The seed words "thingamajigger" and "run" are built into the world. The story
model is state-driven: characters have physical meters and emotional memes, the
thingamajigger can be assembled, carried, dropped, and fixed, and a teamwork
turn changes the ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/thingamajigger_run_teamwork_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/thingamajigger_run_teamwork_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/thingamajigger_run_teamwork_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/thingamajigger_run_teamwork_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/thingamajigger_run_teamwork_heartwarming.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    place: str
    warmth: str
    backdrop: str

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
class Tool:
    id: str
    label: str
    parts: int
    can_carry: bool = False
    can_fix: bool = False
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
class Challenge:
    id: str
    issue: str
    risk: str
    carry_weight: int
    fix_need: int
    helpful_place: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_weight(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["heavy"] < THRESHOLD:
            continue
        sig = ("wobble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["wobble"] += 1
        out.append("__wobble__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["hope"] >= THRESHOLD and world.get("helper").memes["help"] >= THRESHOLD:
        sig = ("teamwork", "done")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["joy"] += 1
            world.get("helper").memes["joy"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("weight", "physical", _r_weight),
    Rule("teamwork", "social", _r_teamwork),
]


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


def predict_stability(world: World, challenge: Challenge, tool: Tool) -> dict:
    sim = world.copy()
    sim.get("thing").meters["assembled"] += 1
    sim.get("thing").meters["heavy"] += challenge.carry_weight
    propagate(sim, narrate=False)
    return {
        "wobbly": sim.get("thing").meters["wobble"] >= THRESHOLD,
        "needs_fix": challenge.fix_need > 0,
    }


def set_up(world: World, child: Entity, helper: Entity, challenge: Challenge) -> None:
    child.memes["hope"] += 1
    helper.memes["help"] += 1
    world.say(
        f"On a soft afternoon in the {world.setting.place}, {child.id} and {helper.id} "
        f"found a half-built thingamajigger beside the table. {world.setting.backdrop}"
    )
    world.say(
        f'"We can finish it before everyone arrives," {child.id} said, and '
        f"{helper.id} nodded at once."
    )


def build(world: World, child: Entity, helper: Entity, tool: Tool, challenge: Challenge) -> None:
    child.meters["worked"] += 1
    helper.meters["worked"] += 1
    thing = world.get("thing")
    thing.meters["assembled"] += 1
    thing.meters["heavy"] += challenge.carry_weight
    world.say(
        f"They used the {tool.label} to snap the last pieces together. The thingamajigger "
        f"looked funny but sturdy, and both children grinned."
    )
    propagate(world, narrate=False)


def trouble(world: World, child: Entity, helper: Entity, challenge: Challenge) -> None:
    thing = world.get("thing")
    thing.meters["wobble"] += 1
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"Then {child.id} tried to run with it, and the thingamajigger tipped sideways. "
        f"The little wheels skidded, and one part popped loose."
    )
    world.say(
        f'"Oh no," whispered {helper.id}, and both of them stared at the broken piece.'
    )


def teamwork_fix(world: World, child: Entity, helper: Entity, tool: Tool, challenge: Challenge) -> None:
    thing = world.get("thing")
    child.memes["hope"] += 1
    helper.memes["hope"] += 1
    child.meters["carried"] += 1
    helper.meters["carried"] += 1
    thing.meters["fixed"] += 1
    thing.meters["wobble"] = 0
    world.say(
        f"Then they worked together. {helper.id} held the frame still while {child.id} "
        f"slid the loose piece back into place, and the {tool.label} clicked shut."
    )
    world.say(
        f"Together they could run the thingamajigger to the porch without dropping it."
    )
    world.say(
        f"At last, the thingamajigger rolled straight and true, ready for the family to see."
    )
    propagate(world, narrate=False)


def ending(world: World, child: Entity, helper: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"When the family came outside, the thingamajigger was waiting in the sun, "
        f"and {child.id} and {helper.id} beamed like they had built a tiny treasure together."
    )
    world.say(
        f"They sat side by side, warm and proud, happy that the best part was not the machine itself but how they had fixed it together."
    )


def tell(setting: Setting, challenge: Challenge, tool: Tool, child_name: str, child_type: str,
         helper_name: str, helper_type: str, parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="builder"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    thing = world.add(Entity(id="thing", type="thing", label="thingamajigger"))
    world.facts.update(setting=setting, challenge=challenge, tool=tool, child=child, helper=helper, parent=parent, thing=thing)

    set_up(world, child, helper, challenge)
    world.para()
    build(world, child, helper, tool, challenge)
    trouble(world, child, helper, challenge)
    world.para()
    teamwork_fix(world, child, helper, tool, challenge)
    ending(world, child, helper)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "workshop": Setting("workshop", "the workshop", "cozy", "Sunlight spilled through the window, and little screws sparkled on the floor."),
    "garage": Setting("garage", "the garage", "warm", "The garage smelled like wood glue and fresh paint."),
    "porch": Setting("porch", "the porch", "bright", "A breeze moved the curtains, and a kitten watched from the steps."),
}

TOOLS = {
    "glue": Tool("glue", "glue and tape", parts=2, can_fix=True),
    "wrench": Tool("wrench", "a tiny wrench", parts=1, can_fix=True),
    "string": Tool("string", "soft string", parts=1, can_carry=True, can_fix=True),
}

CHALLENGES = {
    "wheel": Challenge("wheel", "one wheel wobbled loose", "it might tip over", carry_weight=1, fix_need=1, helpful_place="porch"),
    "handle": Challenge("handle", "the handle kept slipping", "they could not run it safely", carry_weight=2, fix_need=1, helpful_place="garage"),
    "basket": Challenge("basket", "the basket was too heavy to carry alone", "it would fall if they hurried", carry_weight=2, fix_need=1, helpful_place="workshop"),
}

NAMES = ["Maya", "Luca", "Nora", "Eli", "Ava", "Theo", "Zoe", "Ben"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    challenge: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid in CHALLENGES:
            for tid, tool in TOOLS.items():
                if tool.can_fix:
                    out.append((sid, cid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming teamwork storyworld with a thingamajigger.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, tool = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child = rng.choice(NAMES)
    helper = rng.choice([n for n in NAMES if n != child])
    parent = rng.choice(["mother", "father"])
    return StoryParams(setting, challenge, tool, child, child_gender, helper, helper_gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a small child that includes the word "thingamajigger" and a team effort to fix it.',
        f"Tell a story where {f['child'].id} and {f['helper'].id} work together to repair a thingamajigger and run it safely.",
        f'Write a gentle teamwork story with the word "run" in it, ending with pride and a shared smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, challenge = f["child"], f["helper"], f["challenge"]
    return [
        QAItem(
            question=f"What was the thingamajigger like at the start?",
            answer=f"It was partly built and a little tricky, because {challenge.issue}. That made it hard to run safely until the children fixed it."
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} solve the problem?",
            answer=f"They worked together. One held the thing still while the other fit the loose part back, and then they could run it without it tipping."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the thingamajigger finished and the two children proud of working as a team."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork means people help each other and do a job together. It works best when everyone uses their own strengths."),
        QAItem("What does it mean to run something carefully?", "It means moving it quickly but paying attention so it does not fall or break."),
        QAItem("What is a thingamajigger?", "A thingamajigger is a funny word for a made-up machine or gadget. It can be anything the story needs it to be."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
teamwork :- child_hope(H), helper_help(E), H >= 1, E >= 1.
wobbly :- thing_heavy(H), H >= 1.
resolved :- teamwork.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", sid) for sid in SETTINGS
    ] + [
        asp.fact("challenge", cid) for cid in CHALLENGES
    ] + [
        asp.fact("tool", tid) for tid in TOOLS
    ] + [
        asp.fact("sense_min", SENSE_MIN)
    ])


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, challenge=None, tool=None), random.Random(0)))
        _ = sample.story
        print("OK: smoke test generated a normal story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHALLENGES[params.challenge],
        TOOLS[params.tool],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
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


CURATED = [
    StoryParams("workshop", "wheel", "string", "Maya", "girl", "Eli", "boy", "mother"),
    StoryParams("garage", "handle", "glue", "Luca", "boy", "Nora", "girl", "father"),
    StoryParams("porch", "basket", "wrench", "Ava", "girl", "Theo", "boy", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
