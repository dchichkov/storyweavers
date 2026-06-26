#!/usr/bin/env python3
"""
A small folk-tale story world about a Quest, a troublesome hunk, and a wiggle
that helps a child collect what is needed.

The tale premise:
- A young seeker hears that a tiny hunk is blocking the way to a needed prize.
- The seeker cannot simply push the hunk aside; that would be rude or risky.
- Instead, the seeker must wiggle through a narrow place, collect helpful items,
  and complete the quest with a kind helper.

The world model uses physical meters and emotional memes for characters and
objects. The story is simulated, then narrated from the resulting state.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "maiden", "daughter"}
        male = {"boy", "father", "king", "man", "prince", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the mossy lane"
    folk: str = "the old woods"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    name: str
    gerund: str
    effort: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    value: str = "needed"


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    can_help: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


def _get_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _get_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _bump_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = _get_meter(ent, key) + amt


def _bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = _get_meme(ent, key) + amt


def _clear_meme(ent: Entity, key: str) -> None:
    ent.memes[key] = 0.0


def _is_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def _select_tool(task: Task, prize: Prize) -> Optional[HelperTool]:
    for tool in TOOLS:
        if task.id in tool.can_help and prize.region in tool.covers:
            return tool
    return None


def _do_task(world: World, seeker: Entity, task: Task) -> None:
    _bump_meter(seeker, task.mess, 1.0)
    _bump_meme(seeker, "effort", 1.0)
    if task.id == "wiggle":
        _bump_meme(seeker, "joy", 1.0)


def predict_outcome(world: World, seeker: Entity, task: Task, prize: Prize) -> dict:
    sim_seeker = Entity(**{**seeker.__dict__})
    sim = World(world.setting)
    sim.add(sim_seeker)
    sim.add(Entity(
        id=prize.id,
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        plural=prize.plural,
    ))
    _do_task(sim, sim_seeker, task)
    soiled = _get_meter(sim.get(prize.id), "dusty") >= THRESHOLD or _get_meter(sim_seeker, "dusty") >= THRESHOLD
    return {"soiled": soiled, "effort": _get_meme(sim_seeker, "effort")}


def introduce(world: World, seeker: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"Once in {world.setting.folk}, there lived a little {seeker.type} named {seeker.id}."
    )
    world.say(
        f"{seeker.id} loved quiet paths, old songs, and a small {prize.label} that had been promised to {seeker.pronoun('object')}."
    )
    world.say(
        f"{helper.id}, a kind {helper.type}, kept watch over the trail and knew the old way to a good quest."
    )


def setup_quest(world: World, seeker: Entity, task: Task, prize: Prize) -> None:
    _bump_meme(seeker, "want", 1.0)
    world.say(
        f"One morning, {seeker.id} set out on a quest to {task.name} and bring back {prize.phrase}."
    )
    world.say(
        f"The path was narrow, and near the middle of it sat a stubborn hunk of stone."
    )
    world.say(
        f"It was no ordinary stone; it was a hunk that blocked the way and made the trail hard to cross."
    )


def warn(world: World, helper: Entity, seeker: Entity, task: Task, prize: Prize) -> bool:
    pred = predict_outcome(world, seeker, task, prize)
    if not pred["soiled"]:
        return False
    _bump_meme(helper, "care", 1.0)
    world.say(
        f'"If you try to {task.name} there," said {helper.id}, "the hunk will send dust everywhere."'
    )
    world.say(
        f'"Then your prize will not stay clean, and the quest will lose its shine."'
    )
    return True


def refuse(world: World, seeker: Entity, task: Task) -> None:
    _bump_meme(seeker, "stubborn", 1.0)
    world.say(
        f"{seeker.id} still wanted to go at once, but {seeker.pronoun('subject')} knew the warning was true."
    )
    world.say(
        f"So {seeker.pronoun('subject')} took a breath, looked at the hunk, and began to wiggle sideways instead of pushing straight on."
    )


def offer_tool(world: World, helper: Entity, seeker: Entity, task: Task, prize: Prize) -> Optional[HelperTool]:
    tool = _select_tool(task, prize)
    if tool is None:
        return None
    world.say(
        f"{helper.id} brought out {tool.phrase} and said, \"Try this first. It will help you {task.name} without troubling the prize.\""
    )
    return tool


def accept_tool(world: World, seeker: Entity, helper: Entity, task: Task, prize: Prize, tool: HelperTool) -> None:
    _bump_meme(seeker, "joy", 1.0)
    _clear_meme(seeker, "stubborn")
    world.say(
        f"{seeker.id} smiled, took {tool.label}, and listened carefully."
    )
    world.say(
        f"With the helper tool and a careful wiggle, {seeker.id} slipped past the hunk, gathered what {seeker.pronoun('subject')} needed, and kept {prize.label} safe."
    )
    world.say(
        f"At the end of the quest, the old path looked gentle again, and {seeker.id} walked home with a full heart."
    )


def tell(setting: Setting, task: Task, prize: Prize, seeker_name: str, seeker_type: str, helper_type: str) -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        label=seeker_name.lower(),
        meters={"dusty": 0.0},
        memes={"want": 0.0, "joy": 0.0, "stubborn": 0.0},
    ))
    helper = world.add(Entity(
        id="OldFriend",
        kind="character",
        type=helper_type,
        label="old friend",
        meters={"dusty": 0.0},
        memes={"care": 0.0},
    ))
    prize_ent = world.add(Entity(
        id=prize.id,
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        plural=prize.plural,
        owner=seeker.id,
        caretake r=helper.id,
        meters={"dusty": 0.0},
    ))

    introduce(world, seeker, helper, prize_ent)
    world.para()
    setup_quest(world, seeker, task, prize)
    warn(world, helper, seeker, task, prize)
    refuse(world, seeker, task)
    tool = offer_tool(world, helper, seeker, task, prize)
    world.para()
    if tool is not None:
        accept_tool(world, seeker, helper, task, prize, tool)
    world.facts.update(
        seeker=seeker,
        helper=helper,
        prize=prize_ent,
        task=task,
        tool=tool,
    )
    return world


SETTINGS = {
    "lanes": Setting(place="the mossy lane", folk="the old woods", affords={"wiggle", "collect"}),
    "grove": Setting(place="the fern grove", folk="the green hills", affords={"wiggle", "collect"}),
    "brook": Setting(place="the little brook trail", folk="the quiet valley", affords={"wiggle", "collect"}),
}

TASKS = {
    "wiggle": Task(
        id="wiggle",
        name="wiggle through the narrow gap",
        gerund="wiggling through the narrow gap",
        effort="dusty",
        mess="dusty",
        zone={"hands", "knees", "cloak"},
        keyword="wiggle",
        tags={"wiggle", "quest"},
    ),
    "collect": Task(
        id="collect",
        name="collect the lost berries",
        gerund="collecting the lost berries",
        effort="dusty",
        mess="dusty",
        zone={"hands", "cloak"},
        keyword="collect",
        tags={"collect", "quest"},
    ),
}

PRIZES = {
    "crownleaf": Prize(id="crownleaf", label="crownleaf", phrase="a bright crownleaf", region="head"),
    "goldenkey": Prize(id="goldenkey", label="golden key", phrase="the little golden key", region="hand"),
    "songstone": Prize(id="songstone", label="songstone", phrase="a singing songstone", region="pouch"),
}

TOOLS = [
    HelperTool(
        id="reedglove",
        label="reed gloves",
        phrase="a pair of reed gloves",
        can_help={"collect"},
        covers={"hand"},
        plural=True,
    ),
    HelperTool(
        id="softcloak",
        label="a soft cloak",
        phrase="a soft cloak to wrap around the shoulders",
        can_help={"wiggle"},
        covers={"cloak"},
    ),
    HelperTool(
        id="kneepads",
        label="knee pads",
        phrase="knee pads made from felt",
        can_help={"wiggle"},
        covers={"knees"},
        plural=True,
    ),
]

NAMES = ["Mira", "Tobin", "Elsa", "Perrin", "Nell", "Rowan", "Bram", "Lina"]
SEEKER_TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    seeker_type: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for prize_id, prize in PRIZES.items():
                if _is_at_risk(task, prize) and _select_tool(task, prize):
                    out.append((place, task_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale quest about wiggle and collect.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=SEEKER_TYPES)
    ap.add_argument("--helper", choices=["mother", "father", "elder", "friend"])
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
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid quest combination matches the given options.)")
    place, task, prize = rng.choice(sorted(combos))
    seeker_type = args.gender or rng.choice(SEEKER_TYPES)
    name = args.name or rng.choice(NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "elder", "friend"])
    return StoryParams(place=place, task=task, prize=prize, name=name, seeker_type=seeker_type, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a quest to {f["task"].name} and a stubborn hunk.',
        f"Tell a gentle story where {f['seeker'].id} must wiggle past a hunk to collect {f['prize'].phrase}.",
        f'Write a simple quest story that includes the words "hunk", "wiggle", and "collect".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    prize = f["prize"]
    task = f["task"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was {seeker.id} trying to do on the quest?",
            answer=f"{seeker.id} was trying to {task.name} and bring back {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {seeker.id} about the hunk?",
            answer=f"{helper.id} warned {seeker.id} because the hunk could make the trail dusty and trouble the prize.",
        ),
        QAItem(
            question=f"What helped {seeker.id} finish the quest safely?",
            answer=f"{tool.phrase if tool else 'A careful choice'} helped {seeker.id} finish the quest safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a folk tale?",
            answer="A quest is a journey to find something important, solve a problem, or help someone.",
        ),
        QAItem(
            question="What does wiggle mean?",
            answer="To wiggle means to move with small twists or side-to-side motions.",
        ),
        QAItem(
            question="What does collect mean?",
            answer="To collect means to gather things together and bring them to one place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(Task, Prize) :- zone(Task, R), region(Prize, R).
tool_fits(Task, Prize, Tool) :- at_risk(Task, Prize), helps(Tool, Task), covers(Tool, R), region(Prize, R).
valid(Place, Task, Prize) :- affords(Place, Task), at_risk(Task, Prize), tool_fits(Task, Prize, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.can_help):
            lines.append(asp.fact("helps", tool.id, t))
        for r in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize], params.name, params.seeker_type, params.helper_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams(place="lanes", task="wiggle", prize="goldenkey", name="Mira", seeker_type="girl", helper_type="elder"),
    StoryParams(place="grove", task="collect", prize="crownleaf", name="Tobin", seeker_type="boy", helper_type="friend"),
    StoryParams(place="brook", task="wiggle", prize="songstone", name="Elsa", seeker_type="girl", helper_type="mother"),
]


if __name__ == "__main__":
    main()
