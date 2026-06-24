#!/usr/bin/env python3
"""
storyworlds/worlds/demolition_teamwork_dialogue_flashback_myth.py
=================================================================

A small mythic story world about a gentle demolition at an old wall,
where teamwork, dialogue, and a brief flashback turn a risky task into a
safe, shared win.

The premise is simple: a young builder and a small crew must bring down
one crumbling ruin without toppling the wrong part of the village. The
tension is not greed or battle, but hesitation: the wall is old, the tools
matter, and everyone must speak clearly, remember the lesson of the past,
and work together.

This storyworld is intentionally compact and classical:
- physical meters track dust, cracks, and safety
- emotional memes track courage, worry, trust, and pride
- dialogue changes state
- a flashback reveals why the careful plan matters
- teamwork resolves the demolition safely
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Setting:
    place: str
    landmark: str
    weather: str = "clear"


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    safe_for: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    topic: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    task: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "temple_hill": Setting(place="the hill temple", landmark="the old stone wall"),
    "harbor": Setting(place="the harbor shrine", landmark="the cracked sea gate"),
    "forest": Setting(place="the forest shrine", landmark="the fallen arch"),
}

TASKS = {
    "wall": Task(
        id="wall",
        verb="bring down the wall",
        gerund="demolishing the wall",
        risk="the stones could fall the wrong way",
        zone={"wall"},
        topic="demolition",
        tags={"stone", "dust", "wall"},
    ),
    "arch": Task(
        id="arch",
        verb="take apart the arch",
        gerund="dismantling the arch",
        risk="the arch could break before the supports are ready",
        zone={"arch"},
        topic="demolition",
        tags={"stone", "dust", "arch"},
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="strong rope", helps="hold the stones steady", safe_for={"wall", "arch"}),
    "chisels": Tool(id="chisels", label="small chisels", helps="loosen the weak seams", safe_for={"wall", "arch"}),
    "chalk": Tool(id="chalk", label="white chalk marks", helps="show where to strike", safe_for={"wall", "arch"}),
}

NAMES = ["Ari", "Mira", "Tavi", "Nilo", "Sera", "Ivo", "Lena", "Doro"]
GENDERS = ["girl", "boy"]
TYPES = {"girl": ["girl"], "boy": ["boy"]}


ASP_RULES = r"""
task_risky(T) :- task(T), risk_zone(T, R), fragile(R).
good_tool(T, U) :- task(T), tool(U), safe_for(U, T).
valid_plan(T, U) :- task_risky(T), good_tool(T, U).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("risk_zone", tid, r))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for s in sorted(u.safe_for):
            lines.append(asp.fact("safe_for", uid, s))
    for z in {"wall", "arch"}:
        lines.append(asp.fact("fragile", z))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_plans() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_plan/2."))
    return sorted(set(asp.atoms(model, "valid_plan")))


def reasonableness_gate(task: Task, tool: Tool) -> bool:
    return task.id in tool.safe_for


def validate_combo(task: Task, tool: Tool) -> None:
    if not reasonableness_gate(task, tool):
        raise StoryError(f"(No story: {tool.label} is not a reasonable match for {task.gerund}.)")


def predict_demolition(world: World, hero: Entity, task: Task, tool: Tool) -> dict:
    sim = world.copy()
    _do_work(sim, sim.get(hero.id), task, tool, narrate=False)
    return {
        "dust": sim.get("site").meters.get("dust", 0.0),
        "safe": sim.get("site").memes.get("safe", 0.0) >= THRESHOLD,
    }


def _do_work(world: World, actor: Entity, task: Task, tool: Tool, narrate: bool = True) -> None:
    site = world.get("site")
    if task.id not in tool.safe_for:
        return
    key = ("work", actor.id, task.id, tool.id)
    if key in world.fired:
        return
    world.fired.add(key)
    site.meters["dust"] = site.meters.get("dust", 0.0) + 1
    site.meters["cracks"] = site.meters.get("cracks", 0.0) + 1
    site.memes["ready"] = site.memes.get("ready", 0.0) + 1
    actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} used {tool.label} to {task.verb}, and the old stones began to yield.")


def tell(setting: Setting, task: Task, tool: Tool, hero_name: str, helper_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    site = world.add(Entity(id="site", kind="place", type="site", label=setting.landmark))
    rope = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label))
    world.facts.update(hero=hero, helper=helper, site=site, task=task, tool=tool, setting=setting)

    world.say(f"Long ago, at {setting.place}, there stood {setting.landmark}.")
    world.say(f"{hero.id} was a careful little builder, and {helper.id} was wise in old work.")
    world.say(f"They looked at {setting.landmark} and knew it had to be changed, for the stones were tired.")

    world.para()
    world.say(f"{hero.id} wanted to {task.verb}, but {task.risk}.")
    world.say(f"{helper.id} said, \"We must speak plainly, measure twice, and work as one.\"")
    world.say(f"{hero.id} answered, \"Then teach me the right way.\"")

    world.para()
    world.say(f"Before they began, {hero.id} remembered a flashback of another day.")
    world.say(f"Once, a careless strike had sent dust into a doorway and frightened the children there.")
    world.say(f"Since then, {hero.id} had feared fast hands and rough plans.")
    world.say(f"{helper.id} nodded and said, \"That is why we go slow.\"")

    world.para()
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    world.say(f"Together they marked the weak seams with chalk, tied the rope, and checked the path.")
    _do_work(world, hero, task, tool, narrate=True)
    _do_work(world, helper, task, tool, narrate=True)
    site.memes["safe"] = site.memes.get("safe", 0.0) + 1
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1

    world.say(f"When the wall at last fell, it fell where they had planned, like a sleeping giant laying down.")
    world.say(f"Dust rose in a bright cloud, and {hero.id} and {helper.id} laughed with relief.")
    world.say(f"What remained was a safe open space, and the village could pass by again without fear.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story about "{f["task"].topic}" with teamwork, dialogue, and a flashback.',
        f"Tell a gentle tale where {f['hero'].id} and {f['helper'].id} carefully {f['task'].verb} at {f['setting'].place}.",
        f"Write a myth-style story for children about an old stone place, a careful plan, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who worked together at {setting.place}?",
            answer=f"{hero.id} and {helper.id} worked together with care at {setting.place}.",
        ),
        QAItem(
            question=f"What did they want to do to {setting.landmark}?",
            answer=f"They wanted to {task.verb}, but they did it carefully so the stones would fall the right way.",
        ),
        QAItem(
            question=f"What helped them do the work safely?",
            answer=f"They used {tool.label}, and it helped them {tool.helps}.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the old mistake?",
            answer="The flashback reminded the child that careless striking could frighten people and send dust the wrong way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is demolition?", answer="Demolition is the careful taking down of a building, wall, or other structure."),
        QAItem(question="Why do builders mark weak places first?", answer="They mark weak places first so they can work safely and avoid a sudden collapse."),
        QAItem(question="What is teamwork?", answer="Teamwork is when people share a task, help one another, and work toward the same goal."),
        QAItem(question="What is a flashback?", answer="A flashback is a story moment that shows something from before so we understand why a character feels a certain way."),
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    tool = args.tool or rng.choice(list(TOOLS))
    validate_combo(TASKS[task], TOOLS[tool])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    gender = args.gender or rng.choice(GENDERS)
    helper_gender = args.helper_gender or rng.choice(GENDERS)
    return StoryParams(place=place, hero=hero, helper=helper, task=task, tool=tool, seed=args.seed)


CURATED = [
    StoryParams(place="temple_hill", hero="Ari", helper="Mira", task="wall", tool="rope"),
    StoryParams(place="harbor", hero="Tavi", helper="Sera", task="arch", tool="chisels"),
    StoryParams(place="forest", hero="Lena", helper="Doro", task="wall", tool="chalk"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], TOOLS[params.tool], params.hero, params.helper, "girl", "boy")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic demolition teamwork story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper-gender", choices=GENDERS)
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


def asp_verify() -> int:
    py = {(t.id, u.id) for t in TASKS.values() for u in TOOLS.values() if reasonableness_gate(t, u)}
    cl = set(asp_valid_plans())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} plans).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_plan/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        plans = asp_valid_plans()
        print(f"{len(plans)} valid plans:")
        for plan in plans:
            print(" ", plan)
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
            header = f"### {p.hero} and {p.helper}: {p.task} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
