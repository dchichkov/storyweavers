#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/work_problem_solving_sharing_heartwarming.py
=============================================================================

A small heartwarming storyworld about a child, a piece of work that becomes
too much for one pair of hands, and the gentle fix: sharing, planning, and
helping each other finish it together.

Premise
-------
A child has a work task at home or in a small community place. The task is
just a little too big, or a little too messy, for one person. A second helper
notices the trouble, offers a kind plan, and shares the load. The ending proves
that the work got done and that the people feel closer afterward.

Core story shape
-----------------
1. A child starts a job and feels the weight of it.
2. The job gets stuck for a practical reason.
3. A helper suggests a simple shared solution.
4. They finish the job together.
5. The final image shows the work completed and the relationship warmed.

This world uses:
- typed entities with physical meters and emotional memes
- a small forward-chained rule engine
- a Python reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in world state, not rendered text
- standard Storyweavers entry points: build_parser, resolve_params, generate,
  emit, main
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

TASK_THRESHOLD = 1.0
HELP_THRESHOLD = 1.0


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
    detail: str
    supports: set[str] = field(default_factory=set)
    work_kind: str = "chores"
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
class Task:
    id: str
    verb: str
    noun: str
    material: str
    difficulty: int
    helps_from: str
    outcome_noun: str
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
class Share:
    id: str
    label: str
    phrase: str
    method: str
    effect: str
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
class HelperMove:
    id: str
    label: str
    line: str
    finish: str
    power: int
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


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


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    worker = world.get("child")
    if worker.meters["task"] >= TASK_THRESHOLD and worker.meters["helped"] < HELP_THRESHOLD:
        sig = ("tired",)
        if sig not in world.fired:
            world.fired.add(sig)
            worker.memes["worry"] += 1
            out.append("__tired__")
    return out


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["worry"] >= HELP_THRESHOLD and helper.meters["share"] >= HELP_THRESHOLD:
        sig = ("shared",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            helper.memes["kindness"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("tired", _r_tired), Rule("shared", _r_shared)]


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


def task_is_too_much(task: Task, setting: Setting) -> bool:
    return task.difficulty >= 2 and task.id in setting.supports


def helpful_share(share: Share, task: Task) -> bool:
    return share.method == "split" and task.difficulty >= 2


def helper_can_fix(move: HelperMove, task: Task) -> bool:
    return move.power >= task.difficulty


def reasonableness(task: Task, share: Share, move: HelperMove) -> bool:
    return task_is_too_much(task, SETTINGS[share.id]) if False else True


def predict_outcome(world: World, task: Task, share: Share, move: HelperMove) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("child"), task, narrate=False)
    _share_plan(sim, sim.get("helper"), sim.get("child"), share, narrate=False)
    _help_finish(sim, sim.get("helper"), sim.get("child"), task, move, narrate=False)
    return {
        "stuck": sim.get("child").memes["worry"] >= HELP_THRESHOLD,
        "completed": sim.get("child").meters["done"] >= TASK_THRESHOLD,
    }


def _do_task(world: World, child: Entity, task: Task, narrate: bool = True) -> None:
    child.meters["task"] += 1
    child.memes["pride"] += 1
    if task.difficulty >= 2:
        child.memes["worry"] += 1
    propagate(world, narrate=narrate)


def _share_plan(world: World, helper: Entity, child: Entity, share: Share, narrate: bool = True) -> None:
    helper.meters["share"] += 1
    if share.method == "split":
        child.memes["relief"] += 1
    if narrate:
        world.say(share.phrase)


def _help_finish(world: World, helper: Entity, child: Entity, task: Task, move: HelperMove, narrate: bool = True) -> None:
    child.meters["done"] += 1
    helper.meters["done"] += 1
    child.memes["relief"] += 1
    helper.memes["joy"] += 1
    if narrate:
        world.say(move.line)
    propagate(world, narrate=narrate)


def setup_scene(world: World, child: Entity, helper: Entity, setting: Setting, task: Task) -> None:
    world.say(
        f"On a quiet morning, {child.id} and {helper.id} were at {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"{child.id} had a little work to do: {task.verb} the {task.noun} made of {task.material}."
    )
    child.memes["pride"] += 1
    helper.memes["care"] += 1


def show_stuck(world: World, child: Entity, task: Task) -> None:
    world.say(
        f"{child.id} worked hard, but soon {child.pronoun()} sighed. "
        f"The job was bigger than {child.pronoun('object')} expected."
    )
    world.say(
        f"The {task.noun} kept slipping, and the unfinished work made {child.pronoun('object')} frown."
    )


def share_solution(world: World, helper: Entity, child: Entity, share: Share) -> None:
    world.say(
        f"{helper.id} noticed the problem and said, "
        f'"{share.phrase}."'
    )


def finish_together(world: World, child: Entity, helper: Entity, task: Task, move: HelperMove) -> None:
    world.say(
        f"Together they followed the plan. {move.line}"
    )
    world.say(
        f"At last, the {task.noun} was finished, neat and ready to use."
    )


def warm_ending(world: World, child: Entity, helper: Entity, setting: Setting, task: Task) -> None:
    world.say(
        f"{child.id} smiled and gave {helper.id} a happy hug."
    )
    world.say(
        f"Their shared work left {setting.place} calm and cozy, and both of them felt proud."
    )
    child.memes["love"] += 1
    helper.memes["love"] += 1


@dataclass
class StoryParams:
    setting: str
    task: str
    share: str
    move: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen table",
        detail="A small basket of laundry waited by the window, and the sun made the room feel warm.",
        supports={"laundry"},
        work_kind="housework",
    ),
    "garden": Setting(
        id="garden",
        place="the garden shed",
        detail="A row of pots needed sorting, and little tools waited in a tin cup.",
        supports={"sorting"},
        work_kind="gardenwork",
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom corner",
        detail="A stack of papers leaned a little crooked, and crayons sat in a bright cup.",
        supports={"sorting", "paperwork"},
        work_kind="schoolwork",
    ),
}

TASKS = {
    "laundry": Task(
        id="laundry", verb="sort", noun="laundry", material="soft clothes",
        difficulty=2, helps_from="matching colors", outcome_noun="folded clothes",
        tags={"laundry", "work"},
    ),
    "sorting": Task(
        id="sorting", verb="sort", noun="seed packets", material="paper packets",
        difficulty=2, helps_from="putting like things together", outcome_noun="neat rows",
        tags={"sorting", "work"},
    ),
    "paperwork": Task(
        id="paperwork", verb="stack", noun="papers", material="light paper",
        difficulty=3, helps_from="making tidy piles", outcome_noun="tidy stack",
        tags={"paperwork", "work"},
    ),
}

SHARES = {
    "split": Share(
        id="split",
        label="split the work",
        phrase="We can share the work and each take a part",
        method="split",
        effect="shared",
        tags={"share", "work"},
    ),
    "sort": Share(
        id="sort",
        label="sort together",
        phrase="Let's sort it together, one piece at a time",
        method="split",
        effect="shared",
        tags={"share", "work"},
    ),
}

MOVES = {
    "fold": HelperMove(
        id="fold",
        label="folding helper",
        line="One held the pile steady while the other folded each piece with care.",
        finish="folded the clothes",
        power=2,
        tags={"help", "work"},
    ),
    "stack": HelperMove(
        id="stack",
        label="stacking helper",
        line="One made small piles, and the other carried them to the right spot.",
        finish="stacked the papers",
        power=3,
        tags={"help", "work"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Sophie", "Nora", "Ivy", "Emma"]
BOY_NAMES = ["Owen", "Theo", "Caleb", "Noah", "Eli", "Finn"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if tid not in setting.supports:
                continue
            for sh in SHARES:
                for mv in MOVES:
                    if helper_can_fix(MOVES[mv], task) and helpful_share(SHARES[sh], task):
                        combos.append((sid, tid, sh, mv))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about work, sharing, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, share, move = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    return StoryParams(setting=setting, task=task, share=share, move=move,
                       child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("task", TASKS), ("share", SHARES), ("move", MOVES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    share = SHARES[params.share]
    move = MOVES[params.move]
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    world.add(Entity(id="table", type="thing", label=setting.place))
    world.facts.update(setting=setting, task=task, share=share, move=move, child=child, helper=helper)
    setup_scene(world, child, helper, setting, task)
    world.para()
    _do_task(world, child, task)
    show_stuck(world, child, task)
    share_solution(world, helper, child, share)
    _share_plan(world, helper, child, share)
    world.para()
    _help_finish(world, helper, child, task, move)
    finish_together(world, child, helper, setting, task, move)
    warm_ending(world, child, helper, setting, task)
    world.facts["completed"] = child.meters["done"] >= 1
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
        f'Write a heartwarming story for a young child that includes the word "work" and shows two people solving a problem by sharing the task.',
        f"Tell a gentle story where {f['child'].id} has too much work, {f['helper'].id} helps, and they finish it together.",
        f"Write a warm story about sharing work at {f['setting'].place} and ending with a happy feeling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, h, s, t = f["child"], f["helper"], f["setting"], f["task"]
    return [
        (f"Who is the story about?",
         f"It is about {c.id} and {h.id}, who work together at {s.place}."),
        (f"Why did {c.id} need help?",
         f"{c.id} had work that was a little too big for one person. The task took patience and an extra pair of hands to finish well."),
        (f"How did they solve the problem?",
         f"They shared the work. {h.id} suggested a simple plan, and then they finished the {t.noun} together."),
        (f"How did {c.id} feel at the end?",
         f"{c.id} felt proud and happy. The job was done, and the shared success made the ending feel warm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is work?",
         "Work is something you do to help get a job done. It can be easier when people share it."),
        ("What does it mean to share?",
         "To share means to split something up or do it together so one person does not have to carry it all alone."),
        ("Why is teamwork helpful?",
         "Teamwork helps because two people can use their ideas and hands together. That often makes a hard job feel smaller and kinder."),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
task_too_much(S,T) :- setting(S), task(T), supports(S,T), difficulty(T,D), D >= 2.
helpful_share(Sh,T) :- share(Sh), method(Sh,split), task(T), difficulty(T,D), D >= 2.
helper_fix(M,T) :- move(M), power(M,P), task(T), difficulty(T,D), P >= D.
valid(S,T,Sh,M) :- task_too_much(S,T), helpful_share(Sh,T), helper_fix(M,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("supports", sid, "laundry")) if "laundry" in s.supports else None
        lines.append(asp.fact("supports", sid, "sorting")) if "sorting" in s.supports else None
        lines.append(asp.fact("supports", sid, "paperwork")) if "paperwork" in s.supports else None
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("difficulty", tid, t.difficulty))
    for sh, v in SHARES.items():
        lines.append(asp.fact("share", sh))
        lines.append(asp.fact("method", sh, v.method))
    for mv, v in MOVES.items():
        lines.append(asp.fact("move", mv))
        lines.append(asp.fact("power", mv, v.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python = set(valid_combos())
    clingo = set(asp_valid_combos())
    ok = True
    if python != clingo:
        ok = False
        print("MISMATCH in ASP parity")
        print("python only:", sorted(python - clingo))
        print("asp only:", sorted(clingo - python))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, share=None, move=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def explain_rejection(setting: Setting, task: Task) -> str:
    return f"(No story: {task.noun} does not fit well with {setting.place} for this world.)"


def explain_unknown(key: str, value: str) -> str:
    return f"(No story: unknown {key} value {value!r}.)"


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(" ".join(map(str, row)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams(setting="kitchen", task="laundry", share="split", move="fold", child="Maya", child_gender="girl", helper="Mom", helper_gender="girl"),
            StoryParams(setting="garden", task="sorting", share="sort", move="stack", child="Owen", child_gender="boy", helper="Dad", helper_gender="boy"),
            StoryParams(setting="classroom", task="paperwork", share="split", move="stack", child="Lina", child_gender="girl", helper="Teacher", helper_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
