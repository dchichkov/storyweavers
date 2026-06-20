#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/literal_constructive_continue_mystery_to_solve_teamwork.py
=========================================================================================

A small standalone storyworld for a ghost-story flavored mystery about a team of
children who keep hearing a whisper, solve the clue together, and continue an
unfinished task. The domain is intentionally tiny: a few rooms, a few clues, a
few constructive actions, and a forward-simulated inner monologue that steers the
story from worry into teamwork.

Seed words: literal, constructive, continue
Features: Mystery to Solve, Teamwork, Inner Monologue
Style: Ghost Story
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
class Setting:
    id: str
    name: str
    mood: str
    room: str
    dim_spot: str
    object_word: str

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
class Mystery:
    id: str
    whisper: str
    clue: str
    source: str
    reveal: str
    carries: str
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
class ConstructiveTool:
    id: str
    label: str
    action: str
    result: str
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


@dataclass
class ContinueGoal:
    id: str
    label: str
    unfinished: str
    finished: str
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
    setting: Setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("unease", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "investigator":
                kid.memes["unease"] += 1
        out.append("__unease__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork_spot", False) and ("teamwork",) not in world.fired:
        world.fired.add(("teamwork",))
        for kid in list(world.entities.values()):
            if kid.role in {"investigator", "helper"}:
                kid.memes["hope"] += 1
                kid.memes["trust"] += 1
        out.append("__teamwork__")
    return out


def _r_continue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("goal_mended", False) and ("continue",) not in world.fired:
        world.fired.add(("continue",))
        for kid in list(world.entities.values()):
            if kid.role in {"investigator", "helper"}:
                kid.memes["relief"] += 1
        out.append("__continue__")
    return out


CAUSAL_RULES = [Rule("unease", _r_unease), Rule("teamwork", _r_teamwork), Rule("continue", _r_continue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mystery(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("clue").meters["mystery"] += 1
    propagate(sim, narrate=False)
    return {
        "uneasy": sim.get("leader").memes["unease"] >= THRESHOLD,
        "teamwork": sim.facts.get("teamwork_spot", False),
    }


def setup(world: World, leader: Entity, helper: Entity, setting: Setting) -> None:
    leader.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At {setting.name}, {leader.id} and {helper.id} heard the house breathe in the dark. "
        f"{setting.mood} drifted through {setting.room}, and {setting.dim_spot} looked very still."
    )
    world.say(
        f"{leader.id} thought, 'If I listen closely, maybe the whisper will tell a literal secret.' "
        f"{helper.id} thought, 'We can be brave together.'"
    )


def whisper(world: World, mystery: Mystery, leader: Entity, helper: Entity) -> None:
    world.say(
        f"Then came the whisper: '{mystery.whisper}' It seemed to come from {mystery.source}, "
        f"right beside {world.setting.object_word}."
    )
    leader.meters["mystery"] += 1
    helper.meters["mystery"] += 1


def doubt(world: World, leader: Entity) -> None:
    leader.memes["worry"] += 1
    world.say(
        f"{leader.id} swallowed hard. 'Maybe this is a ghost story,' {leader.id} thought. "
        f"'Maybe I should run.'"
    )


def inspect(world: World, helper: Entity, mystery: Mystery) -> None:
    helper.memes["focus"] += 1
    world.say(
        f"But {helper.id} pointed at the clue: {mystery.clue}. "
        f"'Ghosts can be tricky,' {helper.id} said, 'but clues are real.'"
    )


def build(world: World, tool: ConstructiveTool, leader: Entity, helper: Entity) -> None:
    leader.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"Together they chose a constructive idea: {tool.action}. "
        f"{tool.result.capitalize()}, and the room felt less spooky."
    )


def reveal(world: World, mystery: Mystery) -> None:
    world.say(
        f"At last they found the answer. It was not a ghost at all, just {mystery.reveal}. "
        f"The whisper had been carrying {mystery.carries} the whole time."
    )


def finish_goal(world: World, goal: ContinueGoal, leader: Entity, helper: Entity) -> None:
    world.facts["goal_mended"] = True
    propagate(world, narrate=False)
    world.say(
        f"That fixed the unfinished thing: {goal.finished}. "
        f"{leader.id} and {helper.id} could continue, shoulder to shoulder, without fear."
    )
    world.say(
        f"The lantern glow landed on their faces, and the old shadow in {world.setting.dim_spot} "
        f"looked small and harmless now."
    )


def tell(setting: Setting, mystery: Mystery, tool: ConstructiveTool, goal: ContinueGoal,
         leader_name: str = "Mina", leader_gender: str = "girl",
         helper_name: str = "Jon", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="investigator"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue))
    lantern = world.add(Entity(id=tool.id, type="thing", label=tool.label))
    task = world.add(Entity(id=goal.id, type="thing", label=goal.label))

    setup(world, leader, helper, setting)
    world.para()
    whisper(world, mystery, leader, helper)
    doubt(world, leader)
    inspect(world, helper, mystery)
    if predict_mystery(world, mystery)["uneasy"]:
        world.say(f"{helper.id} reached for {parent.label_word} and said, 'We should keep going, but together.'")
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} nodded and brought a lantern. "
        f"{tool.help}s in a calm way."
    )
    build(world, tool, leader, helper)
    world.facts["teamwork_spot"] = True
    propagate(world, narrate=False)
    world.para()
    reveal(world, mystery)
    world.para()
    finish_goal(world, goal, leader, helper)

    world.facts.update(
        setting=setting, mystery=mystery, tool=tool, goal=goal, leader=leader,
        helper=helper, parent=parent, clue=clue, lantern=lantern, task=task,
        solved=True, continued=True
    )
    return world


SETTINGS = {
    "hall": Setting("hall", "the old hall", "A moon-cold hush", "the hall", "the far corner", "floorboards"),
    "attic": Setting("attic", "the attic", "A dusty hush", "the attic", "the beam shadow", "boxes"),
    "porch": Setting("porch", "the porch", "A rain-soft hush", "the porch", "the rocking-chair shadow", "steps"),
}

MYSTERIES = {
    "keys": Mystery("keys", "The keys are not lost.", "a key ring shaped like a crescent moon", "the old piano", "the piano keys were stuck together", "a song of little clinks", {"keys", "sound"}),
    "bell": Mystery("bell", "Follow the bell, not the fear.", "a tiny bell tied to string", "under the stairs", "a wind toy tapping the wall", "a pattern of taps", {"bell", "sound"}),
    "lantern": Mystery("lantern", "The light is waiting.", "a ribbon of tape on the lantern", "beside the window", "a cracked lantern that had been repaired once before", "a bright plan", {"lantern", "light"}),
}

TOOLS = {
    "tape": ConstructiveTool("tape", "a roll of tape", "make a small map with tape and paper", "They built a clear trail of arrows", "helped them mark the path", {"tape", "build"}),
    "chalk": ConstructiveTool("chalk", "a piece of chalk", "draw a careful clue map on the floor", "They drew a picture that made the pattern obvious", "helped them see the shape of the mystery", {"chalk", "build"}),
    "lantern": ConstructiveTool("lantern", "a little lantern", "light the corner and keep working", "The glow made every clue easier to read", "helped them look without fear", {"lantern", "light"}),
}

GOALS = {
    "songbook": ContinueGoal("songbook", "the torn songbook", "its pages were stuck and unfinished", "the torn songbook was mended and could be read again", {"paper", "continue"}),
    "mobile": ContinueGoal("mobile", "the hanging mobile", "one string had come loose", "the hanging mobile was tied back together and could spin again", {"string", "continue"}),
    "castle": ContinueGoal("castle", "the cardboard castle", "one tower was slumped over", "the cardboard castle stood straight again with one more tower fixed", {"cardboard", "continue"}),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Maya", "Zoe"]
BOY_NAMES = ["Jon", "Theo", "Eli", "Ben", "Finn", "Noah"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    goal: str
    leader: str
    leader_gender: str
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
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in MYSTERIES:
            for tid in TOOLS:
                for gid in GOALS:
                    combos.append((sid, mid, gid))
    return combos


KNOWLEDGE = {
    "keys": [("What are keys used for?", "Keys open locks. People carry keys to unlock doors, boxes, and other things that need a matching key.")],
    "bell": [("What does a bell do?", "A bell makes a ringing sound when it is tapped, shaken, or pulled. People use bells to get attention or make music.")],
    "lantern": [("What is a lantern?", "A lantern is a light that helps you see in the dark. Some lanterns use batteries and are safe to carry around.")],
    "tape": [("What can tape do?", "Tape can hold paper together or mark a spot. It is useful for fixing, building, and making signs.")],
    "chalk": [("What is chalk for?", "Chalk can draw lines and pictures on a board or floor. It is easy to see and easy to wipe away.")],
    "continue": [("What does continue mean?", "Continue means to keep going after a pause. If something is not finished, you can continue it later.")],
    "build": [("What does constructive mean?", "Constructive means making something helpful or building something in a careful way. It is a word for useful actions that solve a problem.")],
    "sound": [("Why do quiet places feel spooky?", "Quiet places make little sounds seem bigger, so a whisper or tap can feel mysterious. That is why children sometimes imagine ghosts.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for children that includes the words "literal", "constructive", and "continue".',
        f"Tell a mystery-to-solve story where {f['leader'].id} and {f['helper'].id} hear a whisper, work together, and keep going until they solve it.",
        f"Write a gentle spooky story about {f['setting'].name} where teamwork and inner monologue help two children finish an unfinished job.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader, helper, mystery, goal, setting = f["leader"], f["helper"], f["mystery"], f["goal"], f["setting"]
    qa = [
        ("Who is the story about?", f"It is about {leader.id} and {helper.id}, two children who hear a strange whisper in {setting.name}. They work together instead of running away."),
        ("What did the whisper say?", f'The whisper said, "{mystery.whisper}" It sounded spooky, but it was really a clue about what they needed to notice.'),
        ("What did {0} think at first?".format(leader.id), f"{leader.id} thought it might be a ghost story and felt worried for a moment. Then {leader.pronoun('subject')} remembered that clues can be real even when a place feels spooky."),
        ("How did they solve the mystery?", f"They listened, checked the clue, and used a constructive tool to make the answer clear. Then they found out the whisper was really carrying {mystery.carries}."),
        ("How did the story end?", f"They fixed {goal.label} and could continue their work together. The ending shows that the mystery was solved and the unfinished thing was made whole again."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["tool"].tags) | set(world.facts["goal"].tags)
    tags.add("continue")
    tags.add("build")
    out: list[tuple[str, str]] = []
    for tag in ["keys", "bell", "lantern", "tape", "chalk", "continue", "build", "sound"]:
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "keys", "chalk", "songbook", "Mina", "girl", "Jon", "boy", "mother"),
    StoryParams("attic", "bell", "tape", "mobile", "Luna", "girl", "Theo", "boy", "father"),
    StoryParams("porch", "lantern", "lantern", "castle", "Eli", "boy", "Nora", "girl", "mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with teamwork, inner monologue, and constructive problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--leader")
    ap.add_argument("--helper")
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


def explain_rejection() -> str:
    return "(No story: the requested combination does not support a solvable mystery with a constructive finish.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid story combinations available.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    tool = args.tool or rng.choice(sorted(TOOLS))
    goal = args.goal or rng.choice(sorted(GOALS))
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.setting and args.mystery and args.tool and args.goal is None:
        pass
    leader_gender = "girl" if rng.random() < 0.5 else "boy"
    helper_gender = "boy" if leader_gender == "girl" else "girl"
    leader = args.leader or rng.choice(GIRL_NAMES if leader_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != leader])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, mystery, tool, goal, leader, leader_gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], TOOLS[params.tool], GOALS[params.goal],
                 params.leader, params.leader_gender, params.helper, params.helper_gender, params.parent)
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


ASP_RULES = r"""
valid(S, M, G) :- setting(S), mystery(M), goal(G).
solved(M) :- mystery(M), clue(M, _).
teamwork :- helper(H), investigator(I), H != I.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        return 1 if not print(e) else 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
