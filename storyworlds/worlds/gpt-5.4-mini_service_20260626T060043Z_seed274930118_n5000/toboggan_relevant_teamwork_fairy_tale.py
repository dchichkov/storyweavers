#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/toboggan_relevant_teamwork_fairy_tale.py
======================================================================================================================

A small fairy-tale storyworld about a toboggan, a "relevant" choice, and
teamwork turning a stuck day into a happy ride.

Premise:
- A child and their tiny winter companions want to bring a toboggan to the hill.
- The toboggan is too heavy to move alone.
- A fairy-tale guide insists that only the relevant helpers should come along.
- The team works together, the toboggan moves, and the story ends in a joyful slide.

This world is constraint-checked and deterministic from its parameters.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"weight": 0.0, "stuck": 0.0, "progress": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "frustration": 0.0, "teamwork": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "princess", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "woodcutter"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    sparkle: str
    path: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    obstacle: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    role: str
    boost: float
    needed: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    hero_type: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "castle_lane": Setting(
        place="the castle lane",
        sparkle="snow",
        path="the lane",
        afford={"pull_toboggan"},
    ),
    "pine_hill": Setting(
        place="the pine hill",
        sparkle="frost",
        path="the hill path",
        afford={"pull_toboggan", "ride_toboggan"},
    ),
    "frozen_pond": Setting(
        place="the frozen pond path",
        sparkle="ice",
        path="the pond path",
        afford={"pull_toboggan"},
    ),
}

TASKS = {
    "pull_toboggan": Task(
        id="pull_toboggan",
        verb="pull the toboggan to the hill",
        gerund="pulling the toboggan",
        obstacle="the toboggan was too heavy for one small helper",
        result="the toboggan moved at last",
        keyword="toboggan",
        tags={"toboggan", "winter", "teamwork", "relevant"},
    ),
    "ride_toboggan": Task(
        id="ride_toboggan",
        verb="ride the toboggan down the hill",
        gerund="riding the toboggan",
        obstacle="the hill was too steep without a safe start",
        result="the toboggan slid fast and safe",
        keyword="toboggan",
        tags={"toboggan", "winter", "teamwork", "relevant"},
    ),
}

HELPERS = {
    "rope": Helper(
        id="rope",
        label="a stout rope",
        phrase="a stout rope with a silver knot",
        role="pulls with everyone",
        boost=2.0,
        needed={"pull_toboggan"},
    ),
    "lantern": Helper(
        id="lantern",
        label="a lantern",
        phrase="a warm lantern",
        role="lights the path",
        boost=0.5,
        needed={"pull_toboggan", "ride_toboggan"},
    ),
    "mittens": Helper(
        id="mittens",
        label="warm mittens",
        phrase="warm mittens",
        role="keeps hands strong in the cold",
        boost=1.0,
        needed={"pull_toboggan"},
        plural=True,
    ),
    "friends": Helper(
        id="friends",
        label="two little friends",
        phrase="two little friends",
        role="share the pulling",
        boost=2.5,
        needed={"pull_toboggan", "ride_toboggan"},
        plural=True,
    ),
}

NAMES = ["Mia", "Finn", "Luna", "Theo", "Ava", "Noah", "Ivy", "Eli"]
HERO_TYPES = ["girl", "boy", "princess", "prince"]
TRAITS = ["brave", "kind", "curious", "cheerful", "patient"]


class _Rules:
    @staticmethod
    def total_help(world: World, task: Task) -> float:
        total = 0.0
        for e in world.entities.values():
            if e.kind == "character":
                total += e.memes.get("teamwork", 0.0)
            else:
                total += e.meters.get("help", 0.0)
        return total

    @staticmethod
    def apply_stuck(world: World) -> list[str]:
        out: list[str] = []
        team = [c for c in world.characters() if c.meters["progress"] < THRESHOLD]
        if not team:
            return out
        lead = team[0]
        if lead.meters["weight"] >= THRESHOLD and "toboggan" in world.facts:
            sig = ("stuck", lead.id)
            if sig in world.fired:
                return out
            world.fired.add(sig)
            lead.memes["frustration"] += 1
            out.append("The toboggan would not budge.")
        return out

    @staticmethod
    def apply_teamwork(world: World) -> list[str]:
        out: list[str] = []
        task: Task = world.facts["task"]
        required = 3.0 if task.id == "pull_toboggan" else 2.0
        total = _Rules.total_help(world, task)
        if total >= required:
            sig = ("teamwork", task.id)
            if sig in world.fired:
                return out
            world.fired.add(sig)
            for c in world.characters():
                c.memes["teamwork"] += 1
                c.memes["hope"] += 1
            world.facts["solved"] = True
            out.append("Together, they made a way.")
        return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    for fn in (_Rules.apply_stuck, _Rules.apply_teamwork):
        lines.extend(fn(world))
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def select_helper(task: Task, helper: Helper) -> bool:
    return task.id in helper.needed


def explain_rejection(task: Task, helper: Helper) -> str:
    return f"(No story: {helper.label} is not relevant to {task.verb}. Try a helper that truly helps with that task.)"


def tell(setting: Setting, task: Task, hero_name: str, hero_type: str, helper: Helper) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=["little", "fair", "bright"],
        meters={"weight": 1.0, "stuck": 0.0, "progress": 0.0},
        memes={"hope": 1.0, "frustration": 0.0, "teamwork": 0.0, "joy": 0.0},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type="fairy",
        label="a small fairy",
        traits=["sparkly", "wise"],
    ))
    toboggan = world.add(Entity(
        id="toboggan",
        type="toboggan",
        label="toboggan",
        phrase="a red wooden toboggan",
        owner=hero.id,
        meters={"weight": 3.0, "stuck": 2.0, "progress": 0.0},
    ))
    helper_ent = world.add(Entity(
        id=helper.id,
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        carries={task.id},
        plural=helper.plural,
        meters={"help": helper.boost},
    ))

    world.facts.update(hero=hero, companion=companion, toboggan=toboggan, task=task, helper=helper, setting=setting)

    world.say(f"Once in {setting.place}, there lived a little {hero_type} named {hero_name}.")
    world.say(f"{hero_name} loved {task.gerund}, for the winter air was bright and the lane glittered with {setting.sparkle}.")
    world.say(f"At the gate stood {toboggan.phrase}, but {task.obstacle}.")

    world.para()
    world.say(f"The small fairy looked at the load and said, 'Only the relevant helper should come.'")
    world.say(f"So {hero_name} brought {helper.label}, and everyone gathered at {setting.path}.")

    # state change from joining forces
    hero.meters["weight"] += 0.0
    hero.memes["hope"] += 1.0
    hero.memes["teamwork"] += 1.0
    helper_ent.meters["help"] += 0.0

    propagate(world, narrate=False)
    if world.facts.get("solved"):
        hero.meters["progress"] = 1.0
        toboggan.meters["progress"] = 1.0
        toboggan.meters["stuck"] = 0.0
        hero.memes["joy"] += 1.0
        world.say(f"{hero_name} tied on the rope, and the fairy and friends leaned in together.")
        world.say(f"With a deep breath and many helping hands, {task.result}.")
        world.say(f"At last, {hero_name} smiled as the toboggan slid where it was meant to go.")
    else:
        world.say("But the toboggan still would not move, and the lane stayed quiet.")

    world.facts["toboggan"] = toboggan
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.afford:
            task = TASKS[task_id]
            for helper_id, helper in HELPERS.items():
                if select_helper(task, helper):
                    combos.append((place, task_id, helper_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child about a toboggan and teamwork, and include the word "relevant".',
        f"Tell a gentle winter tale where {f['hero'].id} must {f['task'].verb} with help from {f['helper'].label}.",
        f"Write a short fairy tale that begins with a stuck toboggan and ends with everyone working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Helper = f["helper"]
    task: Task = f["task"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who was the fairy-tale story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and a tiny fairy who helped in {setting.place}.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do with the toboggan?",
            answer=f"{hero.id} was trying to {task.verb}, but the toboggan was too heavy to move alone.",
        ),
        QAItem(
            question=f"Why did the fairy say only the relevant helper should come?",
            answer=f"Because {helper.label} was the right helper for {task.verb}, and the story needed real teamwork, not extra clutter.",
        ),
        QAItem(
            question=f"What changed after everyone worked together?",
            answer=f"The toboggan stopped being stuck, {hero.id} felt joyful, and the team made a way for it to move.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toboggan?",
            answer="A toboggan is a long sled that slides over snow and ice.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and share the work to do something together.",
        ),
        QAItem(
            question="What does relevant mean?",
            answer="Relevant means something is important and fits the job or question at hand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A task is valid with a helper when the helper is relevant to that task.
relevant_helper(T, H) :- task(T), helper(H), fits(H, T).

% A story is valid when a setting affords a task and a relevant helper exists.
valid_story(S, T, H) :- setting(S), affords(S, T), relevant_helper(T, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.afford):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_word", tid, t.keyword))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.needed):
            lines.append(asp.fact("fits", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:9} type={e.type:10} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a toboggan and teamwork.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPERS.keys())
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the chosen options.)")
    place, task, helper = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero = args.hero or rng.choice(NAMES)
    if args.helper and not select_helper(TASKS[task], HELPERS[helper]):
        raise StoryError(explain_rejection(TASKS[task], HELPERS[helper]))
    return StoryParams(place=place, task=task, hero=hero, hero_type=hero_type, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], params.hero, params.hero_type, HELPERS[params.helper])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for row in triples:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, task=t, hero="Mia", hero_type="girl", helper=h))
                   for p, t, h in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
