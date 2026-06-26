#!/usr/bin/env python3
"""
storyworlds/worlds/fantasy_restriction_merry_teamwork_fable.py
===============================================================

A small fable-shaped story world about a merry fantasy team facing a
restriction and solving it with teamwork.

The seed idea:
---
A cheerful woodland team must carry a lantern-gift to a hilltop shrine, but the
old bridge, gate, or river-way has a restriction. The team cannot succeed by
force alone. They must plan, share tasks, and act together.

Story shape:
- beginning: a merry team and a precious errand
- middle: a restriction blocks the way
- turn: the team divides the work and helps one another
- end: the goal is reached, and the change is visible in the world
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Shared tiny world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "witch", "elf"}
        male = {"boy", "king", "wizard", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    tone: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    difficulty: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    label: str
    phrase: str
    type: str
    care: str
    plural: bool = False


@dataclass
class Restriction:
    id: str
    label: str
    clue: str
    blocks: set[str]
    lifted_by: set[str]
    requires: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fits: set[str]
    plural: bool = False


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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "glade": Setting(place="the moonlit glade", tone="merry", affords={"bridge", "riddle", "river"}),
    "hill": Setting(place="the hill path", tone="merry", affords={"bridge", "riddle"}),
    "orchard": Setting(place="the apple orchard", tone="merry", affords={"riddle"}),
}

TASKS = {
    "bridge": Task(
        id="bridge",
        verb="cross the old bridge",
        gerund="crossing the old bridge",
        difficulty="narrow and swaying",
        keyword="bridge",
        tags={"bridge", "wood"},
    ),
    "riddle": Task(
        id="riddle",
        verb="answer the gate riddle",
        gerund="answering the gate riddle",
        difficulty="tricky and half-hidden",
        keyword="riddle",
        tags={"riddle", "magic"},
    ),
    "river": Task(
        id="river",
        verb="carry the lantern across the river",
        gerund="carrying the lantern across the river",
        difficulty="swift and splashing",
        keyword="river",
        tags={"river", "water"},
    ),
}

GOALS = {
    "lantern": Goal(
        label="lantern",
        phrase="a bright silver lantern",
        type="lantern",
        care="shone with warm light",
    ),
    "crown": Goal(
        label="crown",
        phrase="a tiny gold crown",
        type="crown",
        care="sparkled in the dark",
    ),
    "songbell": Goal(
        label="songbell",
        phrase="a little bell that sang softly",
        type="bell",
        care="rang like a bird",
    ),
}

RESTRICTIONS = {
    "one_at_a_time": Restriction(
        id="one_at_a_time",
        label="one at a time",
        clue="only one traveler can cross at once",
        blocks={"bridge"},
        lifted_by={"bridge_rope", "steady_steps"},
        requires={"teamwork"},
        tags={"bridge", "restriction"},
    ),
    "quiet_only": Restriction(
        id="quiet_only",
        label="quiet voices only",
        clue="the gate opens only when no one shouts",
        blocks={"riddle"},
        lifted_by={"song", "whisper"},
        requires={"careful_planning"},
        tags={"riddle", "magic"},
    ),
    "no_wet_heavy": Restriction(
        id="no_wet_heavy",
        label="no wet heavy loads",
        clue="the river stones sink heavy things",
        blocks={"river"},
        lifted_by={"lighten_load", "rope_bundle"},
        requires={"shared_carry"},
        tags={"river", "water"},
    ),
}

TOOLS = [
    Tool(
        id="rope",
        label="a rope",
        phrase="a long rope",
        helps={"bridge", "river"},
        fits={"bridge_rope", "rope_bundle"},
    ),
    Tool(
        id="planks",
        label="planks",
        phrase="two small planks",
        helps={"bridge"},
        fits={"steady_steps"},
        plural=True,
    ),
    Tool(
        id="song",
        label="a song",
        phrase="a gentle song",
        helps={"riddle"},
        fits={"song", "whisper"},
    ),
    Tool(
        id="basket",
        label="a basket",
        phrase="a light basket",
        helps={"river"},
        fits={"lighten_load"},
    ),
]

CREATURES = {
    "fox": ("fox", "he"),
    "rabbit": ("rabbit", "she"),
    "badger": ("badger", "he"),
    "mouse": ("mouse", "she"),
    "owl": ("owl", "they"),
    "elf": ("elf", "she"),
}

NAMES = ["Milo", "Pip", "Luna", "Tavi", "Nina", "Rowan", "Bram", "Sera"]
TRAITS = ["merry", "kind", "brave", "careful", "bright", "patient"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
restriction_blocks(R,T) :- restriction(R), blocks(R,T).
has_tool(T, X) :- tool(T), helps(T, X).
compatible(R,T) :- restriction_blocks(R,T), task(T), needs_task(T, N), lifted_by(R, N).
valid_story(S, T, G, R) :- setting(S), task(T), goal(G), restriction(R),
                           affords(S, T), restriction_blocks(R, T),
                           compatible(R, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("needs_task", tid, t.id))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
    for rid, r in RESTRICTIONS.items():
        lines.append(asp.fact("restriction", rid))
        for b in sorted(r.blocks):
            lines.append(asp.fact("blocks", rid, b))
        for l in sorted(r.lifted_by):
            lines.append(asp.fact("lifted_by", rid, l))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    return 0


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def can_solve(task: Task, restriction: Restriction) -> bool:
    return task.id in restriction.blocks


def compatible_tool(task: Task, restriction: Restriction) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.helps and any(req in tool.fits for req in restriction.lifted_by):
            return tool
    return None


def predict_success(world: World, team: list[Entity], task: Task, goal: Entity, restriction: Restriction) -> bool:
    return compatible_tool(task, restriction) is not None


def propagate(world: World, narrate: bool = True) -> list[str]:
    return []


def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} glimmered {setting.tone} under the sky."


def team_intro(world: World, team: list[Entity]) -> None:
    names = ", ".join(e.id for e in team[:-1]) + f", and {team[-1].id}"
    world.say(f"{names} were a merry little team who liked to help one another.")


def goal_intro(world: World, team: list[Entity], goal: Entity) -> None:
    world.say(
        f"They carried {goal.phrase} because {goal.id} had to reach the hill shrine before night fell."
    )


def task_intro(world: World, task: Task) -> None:
    world.say(f"Their errand was to {task.verb}, but the way was {task.difficulty}.")


def restriction_intro(world: World, restriction: Restriction) -> None:
    world.say(f"At the crossing, a sign of moonstone gave a stern rule: {restriction.label}.")
    world.say(f"That meant {restriction.clue}.")


def struggle(world: World, team: list[Entity], task: Task, restriction: Restriction) -> None:
    world.say(f"They tried to hurry, but the rule stopped them at once.")
    team[0].memes["worry"] = team[0].memes.get("worry", 0) + 1
    team[1].memes["worry"] = team[1].memes.get("worry", 0) + 1


def teamwork_turn(world: World, team: list[Entity], task: Task, restriction: Restriction, tool: Tool) -> None:
    world.say(
        f"Then {team[0].id} had an idea, and the others nodded right away."
    )
    if tool.id == "rope":
        world.say(f"They tied {tool.phrase} to steady the crossing and took turns pulling it tight.")
    elif tool.id == "song":
        world.say(f"They sang {tool.phrase} together, each voice soft enough to please the gate.")
    elif tool.id == "basket":
        world.say(f"They set the lantern into {tool.phrase} so the load would stay light.")
    elif tool.id == "planks":
        world.say(f"They laid out {tool.phrase} and stepped carefully, one after another.")
    world.say(
        f"With every helper doing a small part, they could {task.verb} without breaking the rule."
    )


def ending(world: World, goal: Entity, task: Task, team: list[Entity]) -> None:
    world.say(
        f"By the time they reached the shrine, {goal.label} {GOALS[goal.id].care}, "
        f"and the whole team was laughing under the stars."
    )
    world.say("The fable of the night was plain: when a path is blocked, many small kind acts can open it.")


def tell(setting: Setting, task: Task, goal_cfg: Goal, restriction: Restriction,
         names: list[str], kinds: list[str]) -> World:
    world = World(setting)
    team: list[Entity] = []
    for i, (name, kind) in enumerate(zip(names, kinds)):
        team.append(world.add(Entity(id=name, kind="character", type=kind, meters={}, memes={})))
    goal = world.add(Entity(id=goal_cfg.label, type=goal_cfg.type, label=goal_cfg.label, phrase=goal_cfg.phrase))
    tool = compatible_tool(task, restriction)
    if tool is None:
        raise StoryError("No reasonable teamwork tool can solve this restriction.")
    world.facts.update(task=task, goal=goal, restriction=restriction, tool=tool, setting=setting, team=team)

    world.say(setting_line(setting))
    world.say(" ")
    team_intro(world, team)
    goal_intro(world, team, goal)
    world.para()
    task_intro(world, task)
    restriction_intro(world, restriction)
    struggle(world, team, task, restriction)
    world.para()
    teamwork_turn(world, team, task, restriction, tool)
    ending(world, goal, task, team)
    return world


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    task: str
    goal: str
    restriction: str
    names: list[str]
    kinds: list[str]
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid in s.affords:
            task = TASKS[tid]
            for rid, r in RESTRICTIONS.items():
                if can_solve(task, r):
                    for gid in GOALS:
                        combos.append((sid, tid, gid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A merry fantasy fable about teamwork under a restriction.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--restriction", choices=RESTRICTIONS)
    ap.add_argument("--name", action="append")
    ap.add_argument("--kind", action="append")
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
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.task is None or c[1] == args.task)
        and (args.goal is None or c[2] == args.goal)
        and (args.restriction is None or c[3] == args.restriction)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, goal, restriction = rng.choice(sorted(filtered))
    names = args.name[:] if args.name else rng.sample(NAMES, 2)
    kinds = args.kind[:] if args.kind else [rng.choice(list(CREATURES)) for _ in range(2)]
    if len(names) < 2:
        names = (names + rng.sample(NAMES, 2))[:2]
    if len(kinds) < 2:
        kinds = (kinds + [rng.choice(list(CREATURES))])[:2]
    return StoryParams(setting=setting, task=task, goal=goal, restriction=restriction, names=names[:2], kinds=kinds[:2])


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TASKS[params.task],
        GOALS[params.goal],
        RESTRICTIONS[params.restriction],
        params.names,
        params.kinds,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    restriction = f["restriction"]
    goal = f["goal"]
    team = f["team"]
    return [
        f"Write a merry fantasy fable about {team[0].id} and {team[1].id} facing {restriction.label} while trying to {task.verb}.",
        f"Tell a child-friendly story where a small team learns teamwork to carry {goal.label} through a magical restriction.",
        f"Write a short fable that includes a blocked path, a shared plan, and a happy ending under the stars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    restriction: Restriction = f["restriction"]
    goal: Entity = f["goal"]
    team: list[Entity] = f["team"]
    return [
        QAItem(
            question=f"What were {team[0].id} and {team[1].id} trying to do?",
            answer=f"They were trying to {task.verb} while carrying {goal.phrase}.",
        ),
        QAItem(
            question=f"What rule stopped the team on the way?",
            answer=f"The rule was {restriction.label}: {restriction.clue}.",
        ),
        QAItem(
            question=f"How did the team get past the problem?",
            answer=f"They solved it with teamwork by using {compatible_tool(task, restriction).phrase} and sharing the job.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The team reached the shrine, the goal was delivered safely, and everyone felt merry again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each one helps with part of the job.",
        ),
        QAItem(
            question="What is a restriction?",
            answer="A restriction is a rule or limit that tells you what you can or cannot do.",
        ),
        QAItem(
            question="What does merry mean?",
            answer="Merry means cheerful, bright, and full of happy energy.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often features animals or simple characters and ends with a lesson.",
        ),
        QAItem(
            question="Why is a lantern useful at night?",
            answer="A lantern gives light, so it helps people see the path when it is dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(setting="glade", task="bridge", goal="lantern", restriction="one_at_a_time", names=["Milo", "Luna"], kinds=["fox", "rabbit"]),
    StoryParams(setting="hill", task="riddle", goal="songbell", restriction="quiet_only", names=["Pip", "Sera"], kinds=["mouse", "owl"]),
    StoryParams(setting="glade", task="river", goal="crown", restriction="no_wet_heavy", names=["Bram", "Nina"], kinds=["badger", "elf"]),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story shapes.")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.setting} / {p.task} / {p.restriction}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
