#!/usr/bin/env python3
"""
Standalone storyworld: Presbyterian nursery-rhyme teamwork with repetition.

A tiny, child-facing domain:
- A small presbyterian hall or church room
- A group of children and a helpful grown-up
- A simple task that takes teamwork
- A repeated line that turns worry into rhythm
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    affords: set[str] = field(default_factory=set)
    cozy: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rhyme: str
    repeat_line: str
    teamwork_line: str
    mess: str
    strain: str
    need: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    kind: str = "tool"


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.chorus_count = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.chorus_count = self.chorus_count
        return clone


def _meet_need(world: World) -> list[str]:
    out = []
    for c in world.characters():
        if c.memes.get("helped", 0) >= THRESHOLD:
            continue
        if c.meters.get("strain", 0) >= THRESHOLD and c.memes.get("teamwork", 0) >= THRESHOLD:
            sig = ("helped", c.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            c.memes["helped"] = 1
            c.meters["strain"] = max(0.0, c.meters.get("strain", 0) - 1)
            out.append(f"{c.label} felt lighter once everyone worked together.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_meet_need,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Presbyterian nursery-rhyme teamwork storyworld."
    )
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--group", choices=["2", "3", "4"], help="number of children in the team")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.tool is None or c[2] == args.tool)
        and (args.group is None or c[3] == int(args.group))
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, tool, group = rng.choice(sorted(filtered))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, task=task, tool=tool, name=name, group=group)


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    group: int
    seed: Optional[int] = None


PLACES = {
    "hall": Place("hall", "the presbyterian hall", "hall", {"sing", "stack", "wipe"}),
    "nursery": Place("nursery", "the nursery room", "room", {"sing", "stack", "wipe", "paint"}),
    "steps": Place("steps", "the church steps", "outdoor", {"stack", "wipe"}),
}

TASKS = {
    "songs": Task(
        id="songs",
        verb="sing a simple song",
        gerund="singing a simple song",
        rhyme="one, two, three, clap-clap-clap",
        repeat_line="again and again, they sang it once more",
        teamwork_line="One held the beat, and one kept the tune, and one smiled bright as the afternoon",
        mess="echo",
        strain="worry",
        need="timing",
        keyword="presbyterian",
        tags={"music", "repeat", "teamwork", "presbyterian"},
    ),
    "stacking": Task(
        id="stacking",
        verb="stack the little chairs",
        gerund="stacking the little chairs",
        rhyme="up-up-up, nice and neat",
        repeat_line="again and again, they stacked one more",
        teamwork_line="One carried the chair, and one cleared the way, and one watched the tower sway",
        mess="wobble",
        strain="tired",
        need="balance",
        keyword="presbyterian",
        tags={"repeat", "teamwork", "presbyterian"},
    ),
    "wiping": Task(
        id="wiping",
        verb="wipe the long table",
        gerund="wiping the long table",
        rhyme="swish-swish-swish, cloth on wood",
        repeat_line="again and again, they wiped one more",
        teamwork_line="One fetched the cloth, and one held the jug, and one made room for the scrub-a-dub",
        mess="splash",
        strain="busy",
        need="care",
        keyword="presbyterian",
        tags={"repeat", "teamwork", "presbyterian"},
    ),
}

TOOLS = {
    "cloth": Tool("cloth", "a soft cloth", "a soft cloth for wiping", {"wiping"}),
    "bells": Tool("bells", "little hand bells", "little hand bells for singing", {"songs"}),
    "cart": Tool("cart", "a small chair cart", "a small cart for chairs", {"stacking"}),
}

NAMES = ["Mia", "Noah", "Lily", "Eli", "Ada", "Ben", "Zoe", "Theo"]
CHILD_TRAITS = ["cheerful", "careful", "lively", "gentle", "brave"]


def valid_combos() -> list[tuple[str, str, str, int]]:
    out = []
    for p in PLACES:
        for t in TASKS:
            for tool in TOOLS:
                for group in (2, 3, 4):
                    if t in TOOLS[tool].helps and t in PLACES[p].affords:
                        out.append((p, t, tool, group))
    return out


def reason_gate(place: str, task: str, tool: str, group: int) -> None:
    if task not in PLACES[place].affords:
        raise StoryError(f"(No story: {PLACES[place].label} does not fit {TASKS[task].gerund}.)")
    if task not in TOOLS[tool].helps:
        raise StoryError(f"(No story: {TOOLS[tool].label} does not help with {TASKS[task].verb}.)")
    if group < 2:
        raise StoryError("(No story: teamwork needs at least two children.)")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    world = World(place)
    team = []
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    team.append(hero)
    for i in range(params.group - 1):
        team.append(world.add(Entity(id=f"child{i+2}", kind="character", type="boy", label=f"the {['second','third','fourth'][i]} child")))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label="the helper"))
    for ch in team:
        ch.memes["teamwork"] = 0
        ch.meters["strain"] = 0
    helper.memes["calm"] = 1

    world.say(f"In the presbyterian hall, {hero.label} and friends found a small task to do.")
    world.say(f"They wanted to {task.verb}, and the room felt ready for a nursery-rhyme tune: “{task.rhyme}.”")
    world.para()
    world.say(f"{hero.label} began to {task.verb}, and the others joined in to match the rhythm.")
    world.say(task.repeat_line.capitalize() + ".")
    world.say(task.teamwork_line + ".")
    for ch in team:
        ch.memes["teamwork"] += 1
        ch.meters["strain"] += 1
    if task.id == "songs":
        world.say(f"They shook {tool.label} in time, and the presbyterian hall sounded bright and round.")
    elif task.id == "stacking":
        world.say(f"They rolled {tool.label} beside the wall, one careful chair after another.")
    else:
        world.say(f"They used {tool.label} to make the table shine, one gentle swipe after another.")
    propagate(world)
    world.para()
    world.say(f"Again and again, they did one more {task.id}-step together.")
    world.say(f"At last, the job was done, and the presbyterian hall looked tidy and glad.")
    world.say(f"{hero.label} smiled because teamwork had made the little task easy enough to finish.")
    world.facts.update(place=place, task=task, tool=tool, team=team, helper=helper, hero=hero)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    return [
        f'Write a short nursery-rhyme story about a presbyterian room where children do "{task.keyword}" together.',
        f"Tell a gentle story with repetition and teamwork in {world.place.label} about {task.gerund}.",
        f'Write a child-friendly story that repeats the line "{task.repeat_line}" and ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    hero: Entity = f["hero"]
    tool: Tool = f["tool"]
    place = world.place.label
    return [
        QAItem(
            question=f"Where did {hero.label} and the others work together?",
            answer=f"They worked together in {place}, which was the presbyterian hall or room in this story.",
        ),
        QAItem(
            question=f"What did {hero.label} and friends keep doing again and again?",
            answer=f"They kept {task.gerund}, repeating the little rhythm until the job was done.",
        ),
        QAItem(
            question=f"What helped the children do the task?",
            answer=f"{tool.label.capitalize()} helped, and the bigger help was teamwork because each child did a small part.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The work was finished, the room looked tidy, and the children felt proud instead of worried.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and share the job so it gets done more easily.",
        ),
        QAItem(
            question="Why do children repeat songs or actions in nursery rhymes?",
            answer="They repeat them because repetition makes the words easy to remember and fun to say out loud.",
        ),
        QAItem(
            question="What is a presbyterian church or hall?",
            answer="It is a church place or room where people may gather, sing, talk, or do helpful jobs together.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
helpful(Task,Tool) :- task(Task), tool(Tool), helps(Tool,Task).
valid(Place,Task,Tool,Group) :- place(Place), task(Task), tool(Tool), group(Group),
    affords(Place,Task), helpful(Task,Tool), Group >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tg))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
    for g in (2, 3, 4):
        lines.append(asp.fact("group", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params_from_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.task or args.tool or args.group:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.task is None or c[1] == args.task)
            and (args.tool is None or c[2] == args.tool)
            and (args.group is None or c[3] == int(args.group))
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, tool, group = rng.choice(sorted(combos))
    return StoryParams(place=place, task=task, tool=tool, name=args.name or rng.choice(NAMES), group=group)


def generate(params: StoryParams) -> StorySample:
    reason_gate(params.place, params.task, params.tool, params.group)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="hall", task="songs", tool="bells", name="Mia", group=3),
        StoryParams(place="nursery", task="stacking", tool="cart", name="Noah", group=4),
        StoryParams(place="nursery", task="wiping", tool="cloth", name="Ada", group=2),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        valid = asp_valid()
        print(f"{len(valid)} compatible (place, task, tool, group) combos:\n")
        for p, t, u, g in valid:
            print(f"  {p:8} {t:10} {u:8}  group={g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params_from_all(args, random.Random(seed))
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
            header = f"### {p.name}: {p.task} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
