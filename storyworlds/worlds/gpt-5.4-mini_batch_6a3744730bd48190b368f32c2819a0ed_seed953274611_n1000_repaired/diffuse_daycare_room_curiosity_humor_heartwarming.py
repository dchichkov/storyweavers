#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/diffuse_daycare_room_curiosity_humor_heartwarming.py
====================================================================================

A small, self-contained storyworld about a daycare room where curious children
discover how a little worry can diffuse when everyone uses humor, kindness, and
a gentle helper action.

The core premise is simple:
- a child notices a tense moment in the daycare room,
- curiosity and a playful joke help the group look more closely,
- a warm, practical action diffuses the problem,
- the room ends calmer, cozier, and happier than before.

This world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes,
- a state-driven renderer,
- a Python reasonableness gate plus inline ASP twin,
- three Q&A sets grounded in world state rather than parsed prose,
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp.

Seed words / prompt:
- diffuse
- daycare room
- Curiosity
- Humor
- Heartwarming
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
MOOD_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "teacher"}
        if self.type in female and self.type != "teacher":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type != "teacher":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    id: str
    place: str
    details: str
    noises: str
    supports: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    phrase: str
    where: str
    small_fix: str
    big_fix: str
    diffuse_word: str
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
class HelperAction:
    id: str
    label: str
    verb: str
    effect: str
    lowers: str
    lifts: str
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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["tense"] < THRESHOLD:
            continue
        sig = ("scatter", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["buzz"] += 1
        out.append("__buzz__")
    return out


def _r_diffuse(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    if room and room.meters["calm"] >= THRESHOLD and room.meters["buzz"] >= THRESHOLD:
        sig = ("diffuse", room.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["buzz"] = max(0.0, room.meters["buzz"] - 1)
            room.meters["calm"] += 1
            out.append("__diffuse__")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter), Rule("diffuse", _r_diffuse)]


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


def is_reasonable(problem: Problem) -> bool:
    return problem.id in PROBLEMS and bool(problem.diffuse_word)


def predict_turn(world: World, helper_id: str, problem_id: str) -> dict:
    sim = world.copy()
    helper = sim.get(helper_id)
    helper.memes["curiosity"] += 1
    sim.get("room").meters["buzz"] += 1
    simulate_fix(sim, helper, PROBLEM_BY_ID[problem_id], narrate=False)
    return {
        "calm": sim.get("room").meters["calm"],
        "buzz": sim.get("room").meters["buzz"],
    }


def simulate_fix(world: World, helper: Entity, problem: Problem, narrate: bool = True) -> None:
    room = world.get("room")
    room.meters["calm"] += 1
    room.meters["buzz"] = max(0.0, room.meters["buzz"] - 1)
    room.meters["warmth"] += 1
    helper.memes["humor"] += 1
    helper.memes["care"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f'{helper.id} took a breath, smiled, and used {problem.small_fix} so the room could {problem.diffuse_word}.'
        )


def tell(setting: Setting, problem: Problem, helper_action: HelperAction,
         child_name: str, child_type: str, teacher_name: str, teacher_type: str,
         second_child: str, second_type: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, role="curious child",
        traits=["curious", "funny"], attrs={"setting": setting.id}
    ))
    teacher = world.add(Entity(
        id=teacher_name, kind="character", type=teacher_type, role="teacher",
        traits=["kind", "steady"], attrs={"setting": setting.id}
    ))
    buddy = world.add(Entity(
        id=second_child, kind="character", type=second_type, role="friend",
        traits=["helpful", "playful"], attrs={"setting": setting.id}
    ))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    room.meters["calm"] = 1.0
    room.meters["warmth"] = 1.0

    child.memes["curiosity"] = 2.0
    child.memes["joy"] = 1.0
    teacher.memes["care"] = 2.0
    buddy.memes["humor"] = 1.0

    world.say(
        f"In {setting.place}, the daycare room felt bright and busy. {setting.details}"
    )
    world.say(
        f"{child.id} noticed a little problem near {problem.where}, and {setting.noises} made it feel bigger than it was."
    )
    world.say(
        f'"What is that?" {child.id} asked, leaning closer with wide, curious eyes.'
    )

    world.para()
    child.memes["curiosity"] += 1
    child.meters["tense"] += 1
    world.say(
        f"{buddy.id} gave a tiny joke and {teacher.id} smiled at it, because humor can help everyone look without panicking."
    )
    world.say(
        f'"Maybe the room just needs a kinder face," {teacher.id} said, and the children giggled.'
    )

    world.para()
    world.say(
        f"{child.id} pointed at {problem.phrase}. {teacher.id} gently explained that it could get in the way if nobody helped."
    )
    world.say(
        f"Then {teacher.id} showed them {helper_action.label}, a small way to make the feeling {problem.diffuse_word}."
    )
    simulate_fix(world, teacher, problem, narrate=True)

    world.para()
    world.say(
        f"{child.id} and {buddy.id} helped too, making the room neat again while laughing softly together."
    )
    world.say(
        f"By the end, the daycare room felt cozy. The worry had diffused, and the day was light again."
    )

    world.facts.update(
        setting=setting,
        problem=problem,
        helper_action=helper_action,
        child=child,
        teacher=teacher,
        buddy=buddy,
        outcome="diffused",
        room=room,
    )
    return world


SETTINGS = {
    "daycare_room": Setting(
        id="daycare_room",
        place="the daycare room",
        details="There were blocks on one rug, crayons on the table, and a basket of soft animals by the window.",
        noises="little voices and chair-scoots mixed together",
        supports={"curious", "humor"},
    ),
    "art_corner": Setting(
        id="art_corner",
        place="the daycare room art corner",
        details="Paint cups, paper stars, and sticker sheets waited on a low table.",
        noises="the room buzzed with paint-brush taps",
        supports={"curious", "humor"},
    ),
}

PROBLEMS = {
    "missing_sticker": Problem(
        id="missing_sticker",
        label="a missing sticker",
        phrase="the missing sticker",
        where="the craft table",
        small_fix="looking under the glue box",
        big_fix="sort the stickers by color",
        diffuse_word="easier to find",
        tags={"curious", "humor"},
    ),
    "stuck_block": Problem(
        id="stuck_block",
        label="a stuck block tower",
        phrase="the wobbly block tower",
        where="the block rug",
        small_fix="turning the blocks one by one",
        big_fix="lift the tower carefully together",
        diffuse_word="less tense",
        tags={"curious", "humor"},
    ),
    "snail_trace": Problem(
        id="snail_trace",
        label="a mysterious snail trail",
        phrase="the shiny snail trail",
        where="the window mat",
        small_fix="following the line like a clue",
        big_fix="wipe the mat with a warm cloth",
        diffuse_word="gentler",
        tags={"curious", "humor"},
    ),
}

PROBLEM_BY_ID = PROBLEMS

ACTIONS = {
    "peek": HelperAction(
        id="peek",
        label="a careful peek under the table",
        verb="peek",
        effect="notice what was really there",
        lowers="calm",
        lifts="curiosity",
        tags={"curious"},
    ),
    "giggle_wipe": HelperAction(
        id="giggle_wipe",
        label="a giggle and a warm wipe",
        verb="wipe",
        effect="clear the tiny mess",
        lowers="buzz",
        lifts="warmth",
        tags={"humor"},
    ),
    "sort_together": HelperAction(
        id="sort_together",
        label="sorting together by color",
        verb="sort",
        effect="make the pile feel manageable",
        lowers="buzz",
        lifts="calm",
        tags={"curious", "humor"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ada", "Nina", "Ruby", "Elsie", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Max", "Ben", "Leo", "Milo", "Eli"]
TEACHERS = ["Mrs. Lane", "Ms. Park", "Mr. Reed"]
BUDDIES = ["June", "Sam", "Pip", "Noah", "Bean"]


@dataclass
class StoryParams:
    setting: str = "daycare_room"
    problem: str = "missing_sticker"
    action: str = "sort_together"
    child: str = "Mia"
    child_type: str = "girl"
    teacher: str = "Ms. Park"
    teacher_type: str = "teacher"
    buddy: str = "June"
    buddy_type: str = "girl"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if not problem.tags <= setting.supports:
                continue
            for aid, action in ACTIONS.items():
                if not problem.tags <= action.tags:
                    continue
                combos.append((sid, pid, aid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Daycare-room storyworld with curiosity, humor, and a heartwarming diffusing moment.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--teacher")
    ap.add_argument("--buddy")
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
              and (args.problem is None or c[1] == args.problem)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, action = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    teacher = args.teacher or rng.choice(TEACHERS)
    buddy = args.buddy or rng.choice([n for n in BUDDIES if n != child])
    return StoryParams(
        setting=setting,
        problem=problem,
        action=action,
        child=child,
        child_type=child_type,
        teacher=teacher,
        teacher_type="teacher",
        buddy=buddy,
        buddy_type=rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    problem = PROBLEMS.get(params.problem)
    action = ACTIONS.get(params.action)
    if not setting or not problem or not action:
        raise StoryError("Invalid params for this storyworld.")
    if not is_reasonable(problem):
        raise StoryError(f"Problem {problem.id!r} is not reasonable for this setting.")
    world = tell(setting, problem, action, params.child, params.child_type, params.teacher, params.teacher_type, params.buddy, params.buddy_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming daycare-room story that includes the word "diffuse" and shows curiosity turning a tense moment gentle.',
        f"Tell a short story where {f['child'].id} and friends use humor to look more closely at {f['problem'].phrase}.",
        f"Write a child-friendly story in a daycare room where a kind teacher helps everyone diffuse a small worry.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    teacher: Entity = f["teacher"]
    buddy: Entity = f["buddy"]
    problem: Problem = f["problem"]
    action: HelperAction = f["helper_action"]
    room: Entity = f["room"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {buddy.id}, and {teacher.id} in the daycare room. The story focuses on how they handled a small problem together."),
        ("What did the curious child notice?",
         f"{child.id} noticed {problem.phrase}. That made everyone pause and look more carefully before the worry could grow."),
        ("How did humor help?",
         f"{buddy.id} made a joke, and that helped the room feel less tight. Once they smiled, it was easier to look at the problem calmly."),
        ("What did the teacher do?",
         f"{teacher.id} used {action.label} and helped the children work together. That choice let the problem diffuse instead of spreading into a bigger fuss."),
        ("How did the story end?",
         f"The daycare room ended cozy and calm. The worry diffused, and the children finished the day feeling safe and happy."),
        ("What changed in the room?",
         f"The room's mood became warmer and calmer. There was still a little child energy, but the tense feeling was gone."),
        ("Why was the ending heartwarming?",
         f"Because nobody got in trouble, and everyone helped each other. Curiosity and humor turned a tense moment into a kind, shared fix."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem: Problem = f["problem"]
    action: HelperAction = f["helper_action"]
    return [
        ("What does it mean to be curious?",
         "Being curious means you want to look, ask questions, and learn what is really going on. Curiosity can help people solve problems."),
        ("Why can humor help?",
         "Humor can make people relax and smile. When people are less tense, they can think more clearly and work together."),
        ("What does diffuse mean?",
         "To diffuse something means to make it spread out or become less sharp. In a feeling sense, it can mean a worry gets softer and calmer."),
        ("What is a daycare room?",
         "A daycare room is a place where young children play, learn, and rest while kind grown-ups keep them safe."),
        ("Why is it nice to solve a problem together?",
         "Working together helps people feel supported. A shared fix is often calmer and kinder than trying to handle everything alone."),
        ("What does a helper action do in this world?",
         f"A helper action changes the room in a good way. Here, {action.label} helps the children settle down and make the problem feel {problem.diffuse_word}."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="daycare_room", problem="missing_sticker", action="sort_together", child="Mia", child_type="girl", teacher="Ms. Park", teacher_type="teacher", buddy="June", buddy_type="girl"),
    StoryParams(setting="daycare_room", problem="stuck_block", action="peek", child="Owen", child_type="boy", teacher="Mr. Reed", teacher_type="teacher", buddy="Pip", buddy_type="boy"),
    StoryParams(setting="art_corner", problem="snail_trace", action="giggle_wipe", child="Zoe", child_type="girl", teacher="Mrs. Lane", teacher_type="teacher", buddy="Sam", buddy_type="boy"),
]


def explain_rejection(problem: Problem, setting: Setting) -> str:
    return f"(No story: {problem.label} does not fit the tone or support of {setting.place}.)"


ASP_RULES = r"""
supported(S,P) :- setting(S), problem(P), setting_supports(S,T), problem_tag(P,T).
compatible(S,P,A) :- supported(S,P), action(A), action_tag(A,T), problem_tag(P,T).
valid(S,P,A) :- compatible(S,P,A).
outcome(diffused) :- chosen(S,P,A), valid(S,P,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(setting.supports):
            lines.append(asp.fact("setting_supports", sid, t))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(problem.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(action.tags):
            lines.append(asp.fact("action_tag", aid, t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen", params.setting, params.problem, params.action)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" python-only:", sorted(py - cl))
        print(" asp-only:", sorted(cl - py))
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke test story generation produced empty output.")
    else:
        print("OK: smoke test generation succeeded.")
    if asp_outcome(CURATED[0]) != "diffused":
        rc = 1
        print("MISMATCH: ASP outcome did not infer diffused.")
    else:
        print("OK: ASP outcome agrees on a curated story.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem:
        setting = SETTINGS[args.setting]
        problem = PROBLEMS[args.problem]
        if not problem.tags <= setting.supports:
            raise StoryError(explain_rejection(problem, setting))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, action = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        problem=problem,
        action=action,
        child=args.child or rng.choice(GIRL_NAMES + BOY_NAMES),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        teacher=args.teacher or rng.choice(TEACHERS),
        teacher_type="teacher",
        buddy=args.buddy or rng.choice(BUDDIES),
        buddy_type=rng.choice(["girl", "boy"]),
    )


def generate_story(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.action not in ACTIONS:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], ACTIONS[params.action],
                 params.child, params.child_type, params.teacher, params.teacher_type,
                 params.buddy, params.buddy_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for s, p, a in combos:
            print(f"  {s:12} {p:16} {a}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.problem} ({p.setting}, {p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
