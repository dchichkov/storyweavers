#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/funnel_awkward_nauseous_teamwork_whodunit.py
=============================================================================

A standalone storyworld for a tiny whodunit-style teamwork mystery.

Seed premise
------------
A small group gets an awkward, nauseous feeling when they find strange clues:
a funnel, a spill, and a missing treat. They work together, follow the clues,
and discover the harmless truth: someone was making a science demo and used the
funnel to pour a smelly mixture into a jar. The ending proves the team fixed the
mess, comforted the worried child, and turned suspicion into shared relief.

The world is kept intentionally small:
- a handful of typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate and inline ASP twin
- three QA sets generated from world state, not from rendered text
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class PersonCfg:
    name: str
    gender: str

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
class Setting:
    id: str
    place: str
    clue_spot: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    smell: str
    role: str
    useful: bool = False

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
class IssueCfg:
    id: str
    symptom: str
    awkward_line: str
    nauseous_line: str
    strength: int
    cause: str
    fix: str
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
class TeamTool:
    id: str
    label: str
    use_line: str
    helps: str
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


def _r_rumor(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    if case.meters["mystery"] < THRESHOLD:
        return out
    sig = ("rumor",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["curiosity"] += 1
    out.append("__rumor__")
    return out


def _r_nausea(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    if case.meters["mystery"] < THRESHOLD:
        return out
    if case.meters["smell"] < THRESHOLD:
        return out
    sig = ("nausea",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["unease"] += 1
    out.append("__nausea__")
    return out


def _r_teamwork(world: World) -> list[str]:
    case = world.get("case")
    if case.meters["clues"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for c in world.characters():
        c.memes["trust"] += 1
    return ["__teamwork__"]


CAUSAL_RULES = [Rule("rumor", "social", _r_rumor), Rule("nausea", "physical", _r_nausea), Rule("teamwork", "social", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_case(world: World, issue: IssueCfg, tool: TeamTool) -> dict:
    sim = world.copy()
    sim.get("case").meters["mystery"] += 1
    sim.get("case").meters["smell"] += 1
    if tool.id == "funnel":
        sim.get("case").meters["clues"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("case").meters["mystery"],
        "nausea": sim.get("case").meters["smell"],
        "resolved": tool.id == "funnel" and issue.id == "smelly_spill",
    }


def setup(world: World, setting: Setting, kid: Entity, helper: Entity) -> None:
    world.say(
        f"That afternoon, {kid.id} and {helper.id} were in {setting.place}. "
        f"Everything looked ordinary except for one odd clue near {setting.clue_spot}: "
        f"a funnel."
    )
    world.say(
        f'{kid.id} frowned. "That is awkward," {kid.pronoun()} said, because '
        f'the air had a strange smell that made {helper.id} feel nauseous.'
    )


def inspect(world: World, kid: Entity, helper: Entity, issue: IssueCfg, obj: ObjectCfg) -> None:
    kid.memes["fear"] += 1
    helper.memes["curiosity"] += 1
    case = world.get("case")
    case.meters["mystery"] += 1
    case.meters["smell"] += 1
    case.attrs["clue"] = obj.id
    world.say(
        f"{kid.id} pointed at the {obj.label}. {helper.id} leaned closer and "
        f"noticed the smell was coming from the spill, not from any bad person."
    )
    world.say(
        f'"We should check the clue carefully," {helper.id} said. "A whodunit only '
        f'feels scary until the team looks together."'
    )
    propagate(world, narrate=True)


def use_tool(world: World, helper: Entity, tool: TeamTool, issue: IssueCfg) -> None:
    helper.memes["confidence"] += 1
    world.get("case").meters["clues"] += 1
    world.say(
        f"Then {helper.id} picked up the {tool.label}. {tool.use_line} "
        f"It was the kind of helpful move that made the whole mystery clearer."
    )


def reveal(world: World, kid: Entity, helper: Entity, obj: ObjectCfg, issue: IssueCfg) -> None:
    world.get("case").meters["mystery"] = 0
    world.get("case").meters["smell"] = 0
    world.get("case").meters["solved"] = 1
    kid.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"At last, the clue fit: {obj.label} had been used to pour a smelly mixture "
        f"into a jar for a science demo, and nobody had done anything wrong."
    )
    world.say(
        f"{kid.id} and {helper.id} laughed because the truth was simple, and the "
        f"awkward feeling could float away."
    )


def ending(world: World, setting: Setting, kid: Entity, helper: Entity, tool: TeamTool) -> None:
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"They wiped the spill, set the {tool.label} back on the table, and "
        f"looked around {setting.place} with bright, relieved faces."
    )
    world.say(
        f"In the end, the funnel was only a clue, the nausea was only a smell, "
        f"and teamwork made the whole room feel safe again."
    )
    world.say(setting.ending_image)


def tell(setting: Setting, issue: IssueCfg, obj: ObjectCfg, tool: TeamTool,
         kid_cfg: PersonCfg, helper_cfg: PersonCfg, parent_type: str = "mother") -> World:
    world = World()
    kid = world.add(Entity(id=kid_cfg.name, kind="character", type=kid_cfg.gender, role="investigator"))
    helper = world.add(Entity(id=helper_cfg.name, kind="character", type=helper_cfg.gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="adult", label="the grown-up"))
    case = world.add(Entity(id="case", type="case", label="the case"))
    case.meters["mystery"] = 1
    case.meters["smell"] = 1
    world.add(Entity(id=obj.id, type="object", label=obj.label, attrs={"smell": obj.smell}))
    world.add(Entity(id=tool.id, type="tool", label=tool.label))
    world.facts["parent"] = parent
    world.facts["setting"] = setting
    world.facts["issue"] = issue
    world.facts["object"] = obj
    world.facts["tool"] = tool
    world.facts["kid"] = kid
    world.facts["helper"] = helper

    setup(world, setting, kid, helper)
    world.para()
    inspect(world, kid, helper, issue, obj)
    use_tool(world, helper, tool, issue)
    reveal(world, kid, helper, obj, issue)
    world.para()
    ending(world, setting, kid, helper, tool)
    return world


SETTINGS = {
    "lab": Setting("lab", "the little lab", "the sink", "A clean funnel sat beside a tidy jar, and the whole room smelled fresh again."),
    "kitchen": Setting("kitchen", "the kitchen", "the counter", "The funnel hung from a hook, and the kitchen looked neat and calm."),
    "classroom": Setting("classroom", "the classroom", "the science shelf", "The funnel rested beside the markers, and the class corner felt peaceful."),
}

OBJECTS = {
    "jar": ObjectCfg("jar", "jar", "a glass jar", "sour", "clue"),
    "spill": ObjectCfg("spill", "spill", "a sticky spill", "odd", "clue"),
    "beaker": ObjectCfg("beaker", "beaker", "a beaker", "sharp", "clue"),
}

ISSUES = {
    "smelly_spill": IssueCfg("smelly_spill", "smelly spill", "that is awkward", "made nauseous", 1, "a science mixture", "the funnel", tags={"funnel", "awkward", "nauseous"}),
    "mystery_jar": IssueCfg("mystery_jar", "mystery jar", "that is awkward", "made nauseous", 1, "a jar clue", "the funnel", tags={"funnel", "awkward", "nauseous"}),
}

TOOLS = {
    "funnel": TeamTool("funnel", "funnel", '"Let me use the funnel," {helper} said. "Then we can pour the mixture neatly and see what it was."', "the funnel helped them follow the clue", tags={"funnel", "teamwork"}),
    "gloves": TeamTool("gloves", "pair of gloves", '"Let me wear the gloves," {helper} said. "Then we can clean without making it worse."', "the gloves helped with cleanup", tags={"teamwork"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava"]
BOY_NAMES = ["Ben", "Noah", "Leo", "Max", "Eli"]
TRAITS = ["careful", "curious", "thoughtful", "brave"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    issue: str
    obj: str
    tool: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid in ISSUES:
            for oid in OBJECTS:
                for tid in TOOLS:
                    if tid == "funnel" and iid == "smelly_spill":
                        combos.append((sid, iid, oid, tid))
    return combos


def explain_rejection(issue: IssueCfg, tool: TeamTool) -> str:
    return (
        f"(No story: this mystery needs the smell-and-clue logic to be tied to "
        f"the funnel, and the helper tool must actually support teamwork. "
        f"Try the funnel with the smelly spill.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about a funnel, an awkward clue, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--object", dest="obj", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.tool and args.tool != "funnel":
        raise StoryError("(No story: the mystery in this world is solved with the funnel.)")
    if args.issue and args.issue != "smelly_spill":
        raise StoryError(explain_rejection(ISSUES[args.issue], TOOLS.get(args.tool or "funnel", TOOLS["funnel"])))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.issue is None or c[1] == args.issue)
              and (args.obj is None or c[2] == args.obj)
              and (args.tool is None or c[3] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, issue, obj, tool = rng.choice(sorted(combos))
    kid_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if kid_gender == "girl" else "girl"
    kid_name = rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    helper_name = rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != kid_name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, issue, obj, tool, kid_name, kid_gender, helper_name, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ISSUES[params.issue],
        OBJECTS[params.obj],
        TOOLS[params.tool],
        PersonCfg(params.kid_name, params.kid_gender),
        PersonCfg(params.helper_name, params.helper_gender),
        params.parent,
    )
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
    setting = f["setting"]
    issue = f["issue"]
    tool = f["tool"]
    return [
        f'Write a whodunit story for a young child that includes the words "funnel", "awkward", and "nauseous".',
        f"Tell a teamwork mystery set in {setting.place} where a child feels awkward and nauseous because of a clue, and the funnel helps solve it.",
        f"Write a gentle detective story where the funnel is not scary at all, just the clue that helps the team understand the spill.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    tool = f["tool"]
    issue = f["issue"]
    setting = f["setting"]
    obj = f["object"]
    parent = f["parent"]
    return [
        ("Who solved the mystery?",
         f"{kid.id} and {helper.id} solved it together. They worked as a team, so the clue stopped feeling scary."),
        ("Why did the story feel awkward at first?",
         f"It felt awkward because there was a strange clue and nobody knew what it meant yet. The uncertain smell made everyone slow down and look more carefully."),
        ("Why did someone feel nauseous?",
         f"The smell from the spill was strong enough to make {helper.id} feel nauseous. Once the team found the source, the feeling made sense and got easier."),
        ("What did the funnel help them do?",
         f"The funnel helped them pour the messy mixture neatly and follow the clue. That teamwork made the mystery easier to understand."),
        ("What turned out to be the truth?",
         f"The truth was that {obj.label} and the spill were part of a science demo, not a bad trick. The grown-up was nearby, and nobody had done anything wrong."),
        ("How did the story end?",
         f"They cleaned the spill, set the funnel back down, and felt relieved. The room looked calm again, which showed the case was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a funnel?",
         "A funnel is a tool that helps pour liquid into a small opening without spilling. It has a wide top and a narrow bottom."),
        ("What does awkward mean?",
         "Awkward means uncomfortable or hard to know how to act. A situation can feel awkward when people are unsure what is happening."),
        ("What does nauseous mean?",
         "Nauseous means feeling like you might throw up because of a strong smell, sickness, or motion. It is a very yucky feeling."),
        ("What is teamwork?",
         "Teamwork means people help one another to do something together. Each person does a part, and the group works better that way."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(C) :- case(C), mystery_level(C, N), N >= 1.
smelly(C) :- case(C), smell_level(C, N), N >= 1.
nauseous(P) :- person(P), case(C), smell_level(C, N), N >= 1.
teamwork(T) :- tool(T), funnel(T).
solved(C) :- case(C), mystery(C), tool(funnel), teamwork(funnel).
valid_story(S, I, O, T) :- setting(S), issue(I), object(O), tool(T), funnel(T), smelly_issue(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ISSUES:
        lines.append(asp.fact("issue", iid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("funnel", "funnel"))
    lines.append(asp.fact("smelly_issue", "smelly_spill"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    sample = generate(resolve_params(argparse.Namespace(setting=None, issue=None, obj=None, tool=None, parent=None), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: story generation produced empty text.")
    else:
        print("OK: story generation smoke test passed.")
    return rc


def explain_story(world: World) -> None:
    pass


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
    StoryParams("lab", "smelly_spill", "jar", "funnel", "Mia", "girl", "Ben", "boy", "mother", "curious"),
    StoryParams("kitchen", "smelly_spill", "beaker", "funnel", "Leo", "boy", "Zoe", "girl", "father", "thoughtful"),
    StoryParams("classroom", "smelly_spill", "spill", "funnel", "Nora", "girl", "Max", "boy", "mother", "careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for row in asp_valid_combos():
            print(" ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.kid_name} and {p.helper_name}: {p.setting} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
