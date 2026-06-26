#!/usr/bin/env python3
"""
storyworlds/worlds/yucko_teamwork_happy_ending_tall_tale.py
============================================================

A small tall-tale story world about a yucko mess, teamwork, and a happy ending.

Premise:
- A grand, slightly exaggerated place gets covered in yucko.
- One tiny character tries to solve it alone and cannot.
- Helpful neighbors bring the right tools and work together.
- The mess is cleaned up, the place shines, and everyone celebrates.

This world is intentionally compact: fewer story variants, but each one is
causal, state-driven, and ends with a clear proof of change.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

MESS_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    tall_detail: str = ""


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    boosts: set[str]
    use_line: str
    end_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.focus: str = ""

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
        clone.fired = set(self.fired)
        clone.focus = self.focus
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spread_yucko(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("yucko", 0.0) < MESS_THRESHOLD:
            continue
        sig = ("spread", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["mess_active"] = True
        out.append(f"The yucko splashed and splatted everywhere.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helpers = [e for e in world.characters() if e.memes.get("helping", 0.0) >= MESS_THRESHOLD]
    if len(helpers) < 2:
        return out
    sig = ("teamwork", tuple(sorted(h.id for h in helpers)))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["teamwork"] = True
    for h in helpers:
        h.memes["pride"] = h.memes.get("pride", 0.0) + 1.0
    out.append("The whole crew worked as one, like a wagon pulled by six sturdy horses.")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("teamwork"):
        return out
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.meters.get("yucko", 0.0) < MESS_THRESHOLD:
            continue
        sig = ("clean", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["yucko"] = 0.0
        ent.meters["clean"] = 1.0
        out.append(f"With teamwork, the yucko was wiped right off {ent.label}.")
    return out


CAUSAL_RULES = [
    Rule("spread_yucko", _r_spread_yucko),
    Rule("teamwork", _r_teamwork),
    Rule("cleanup", _r_cleanup),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_cleanup(world: World, actor: Entity, task: Task, helper_count: int) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["yucko"] = 1.0
    for i in range(helper_count):
        hid = f"helper{i}"
        if hid not in sim.entities:
            sim.add(Entity(id=hid, kind="character", type="person", label=f"helper {i+1}"))
        sim.get(hid).memes["helping"] = 1.0
    sim.facts["teamwork"] = helper_count >= 2
    propagate(sim, narrate=False)
    dirty = any(e.meters.get("yucko", 0.0) >= MESS_THRESHOLD for e in sim.entities.values() if e.kind == "thing")
    return {"clean": not dirty, "teamwork": bool(sim.facts.get("teamwork"))}


def tall_tale_line(task: Task) -> str:
    return {
        "barn": "The barn stood so tall it seemed to tickle the clouds.",
        "bridge": "The bridge stretched long as a fiddle string over the water.",
        "schoolyard": "The schoolyard was wide enough for three games of tag and a parade of geese.",
        "town_square": "The town square was broad and bright, with a fountain singing in the middle.",
    }.get(task.id, "The place looked ready for a mighty bit of trouble.")


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big heart and a bigger hat."
    )
    world.say(
        f"Folks said {hero.id} could spot trouble from across the county."
    )


def setup(world: World, hero: Entity, task: Task, mess: Entity) -> None:
    world.say(tall_tale_line(task))
    world.say(
        f"{hero.id} loved to {task.verb}, but one day the place was covered in yucko."
    )
    world.say(
        f"The yucko was so thick it looked like a green pudding mountain had sat down and refused to move."
    )
    world.say(
        f"{hero.id} knew {mess.label} could not stay that way."
    )


def try_alone(world: World, hero: Entity, task: Task, mess: Entity) -> None:
    hero.meters["yucko"] = 1.0
    world.say(
        f"{hero.id} tried to {task.rush} and clean everything all by {hero.pronoun('possessive')}self."
    )
    world.say(
        f"But one small pair of hands could not beat a whole heap of yucko."
    )


def call_team(world: World, hero: Entity, helpers: list[Entity], task: Task, tool: Tool) -> None:
    helper_names = ", ".join(h.id for h in helpers[:-1]) + (f", and {helpers[-1].id}" if len(helpers) > 1 else helpers[0].id)
    world.say(
        f"{hero.id} called for {helper_names}, and they came running with {tool.label}."
    )
    for h in helpers:
        h.memes["helping"] = 1.0
    world.say(
        f"{tool.use_line}"
    )


def clean_up(world: World, hero: Entity, helpers: list[Entity], task: Task, mess: Entity, tool: Tool) -> None:
    propagate(world, narrate=True)
    world.say(
        f"{tool.end_line}"
    )
    world.say(
        f"By sunset, {mess.label} was clean, and the whole place shone like a silver spoon."
    )
    world.say(
        f"{hero.id} laughed with {', '.join(h.id for h in helpers)} because the job had been done together."
    )


SETTINGS = {
    "barn": Setting(
        place="the old red barn",
        affords={"sweep_barn"},
        tall_detail="the old red barn",
    ),
    "bridge": Setting(
        place="the river bridge",
        affords={"scrub_bridge"},
        tall_detail="the river bridge",
    ),
    "schoolyard": Setting(
        place="the schoolyard",
        affords={"rake_yard"},
        tall_detail="the schoolyard",
    ),
    "town_square": Setting(
        place="the town square",
        affords={"mop_square"},
        tall_detail="the town square",
    ),
}

TASKS = {
    "sweep_barn": Task(
        id="sweep_barn",
        verb="sweep the barn",
        gerund="sweeping the barn",
        rush="dash through the hay and sweep",
        mess="dusty yucko",
        soil="dusty and yucky",
        tags={"barn", "dust"},
    ),
    "scrub_bridge": Task(
        id="scrub_bridge",
        verb="scrub the bridge",
        gerund="scrubbing the bridge",
        rush="scrape the boards and scrub",
        mess="slimy yucko",
        soil="slippery and slimy",
        tags={"bridge", "water"},
    ),
    "rake_yard": Task(
        id="rake_yard",
        verb="rake the yard",
        gerund="raking the yard",
        rush="race through the leaves and rake",
        mess="leafy yucko",
        soil="leafy and stuck",
        tags={"schoolyard", "leaves"},
    ),
    "mop_square": Task(
        id="mop_square",
        verb="mop the square",
        gerund="mopping the square",
        rush="spin the mop and scrub",
        mess="muddy yucko",
        soil="muddy and splashed",
        tags={"town", "mud"},
    ),
}

TOOLS = {
    "hay_rake": Tool(
        id="hay_rake",
        label="three hay rakes",
        helps={"dusty yucko", "leafy yucko"},
        boosts={"sweep_barn", "rake_yard"},
        use_line="They raked in great sweeping swings, and the dust lifted like a brown cloud of feathers.",
        end_line="The last dust bunny rolled away like a tumbleweed with a tune.",
    ),
    "river_brush": Tool(
        id="river_brush",
        label="river scrub brushes",
        helps={"slimy yucko", "muddy yucko"},
        boosts={"scrub_bridge", "mop_square"},
        use_line="They scrubbed with long, brave strokes, and the slime gave up its grip.",
        end_line="The boards and stones flashed clean as a whistle in winter.",
    ),
    "super_sponges": Tool(
        id="super_sponges",
        label="six super sponges",
        helps={"dusty yucko", "slimy yucko", "muddy yucko", "leafy yucko"},
        boosts={"sweep_barn", "scrub_bridge", "rake_yard", "mop_square"},
        use_line="They squeezed and swiped and squeaked, and the yucko soaked right up.",
        end_line="The sponges came out squishy, but the place came out shining.",
    ),
}

HERO_NAMES = ["Mabel", "Otis", "Dora", "Hank", "June", "Clancy", "Pearl", "Rufus"]
HELPER_NAMES = ["Nell", "Bo", "Cora", "Wes", "Ivy", "Jeb", "Sadie", "Toby"]


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    hero: str
    helper1: str
    helper2: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for tool_id, tool in TOOLS.items():
                if task.id in tool.boosts and task.mess in tool.helps:
                    combos.append((place, task_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about yucko, teamwork, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
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
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, tool = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    helper1 = args.helper1 or rng.choice([n for n in HELPER_NAMES if n != hero])
    helper2 = args.helper2 or rng.choice([n for n in HELPER_NAMES if n not in {hero, helper1}])
    return StoryParams(place=place, task=task, tool=tool, hero=hero, helper1=helper1, helper2=helper2)


def _story_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="person"))
    h1 = world.add(Entity(id=params.helper1, kind="character", type="person"))
    h2 = world.add(Entity(id=params.helper2, kind="character", type="person"))
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    mess = world.add(Entity(id="mess", type="thing", label=world.setting.place))
    world.facts.update(hero=hero, helpers=[h1, h2], task=task, tool=tool, mess=mess, place=params.place)
    intro(world, hero)
    world.para()
    setup(world, hero, task, mess)
    try_alone(world, hero, task, mess)
    world.para()
    call_team(world, hero, [h1, h2], task, tool)
    clean_up(world, hero, [h1, h2], task, mess, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    tool: Tool = f["tool"]
    return [
        f'Write a tall-tale story for a small child about yucko, teamwork, and a happy ending at {world.setting.place}.',
        f'Tell a funny story where {f["hero"].id} tries to {task.verb}, but only teamwork with {tool.label} can fix the yucko.',
        f'Create a child-friendly tall tale that uses the word "yucko" and ends with everyone smiling together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helpers: list[Entity] = f["helpers"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    mess: Entity = f["mess"]
    return [
        QAItem(
            question=f"What did {hero.id} try to do at {world.setting.place}?",
            answer=f"{hero.id} tried to {task.verb} in the yucko-covered place.",
        ),
        QAItem(
            question=f"Why could not {hero.id} finish the job alone?",
            answer=f"The yucko was too big and slippery for one small helper, so {hero.id} needed teamwork.",
        ),
        QAItem(
            question=f"Who helped {hero.id}, and what did they bring?",
            answer=f"{helpers[0].id} and {helpers[1].id} helped by bringing {tool.label}.",
        ),
        QAItem(
            question=f"What happened to the yucko by the end?",
            answer=f"The yucko was cleaned off {mess.label}, and the place ended bright and tidy.",
        ),
        QAItem(
            question="What kind of ending did the story have?",
            answer="It had a happy ending, because the friends worked together and finished the job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is yucko in this story?",
            answer="Yucko is a messy, gross stuff that needs cleaning up.",
        ),
        QAItem(
            question="Why is a happy ending important in a story?",
            answer="A happy ending shows that the trouble got solved and things turned out well.",
        ),
        QAItem(
            question="Why can tools help with big chores?",
            answer="Tools can make hard work easier, faster, and safer.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _story_world(params)
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


ASP_RULES = r"""
% A task/place/tool triple is valid when the place affords the task and the tool
% can handle the task's mess.
valid(Place, Task, Tool) :- affords(Place, Task), task_mess(Task, Mess), helps(Tool, Mess), boosts(Tool, Task).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for task in sorted(setting.affords):
            lines.append(asp.fact("affords", place, task))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("task_mess", task_id, task.mess))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for m in sorted(tool.helps):
            lines.append(asp.fact("helps", tool_id, m))
        for t in sorted(tool.boosts):
            lines.append(asp.fact("boosts", tool_id, t))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="barn", task="sweep_barn", tool="hay_rake", hero="Mabel", helper1="Nell", helper2="Bo"),
        StoryParams(place="bridge", task="scrub_bridge", tool="river_brush", hero="Otis", helper1="Cora", helper2="Wes"),
        StoryParams(place="schoolyard", task="rake_yard", tool="super_sponges", hero="June", helper1="Ivy", helper2="Jeb"),
        StoryParams(place="town_square", task="mop_square", tool="super_sponges", hero="Clancy", helper1="Sadie", helper2="Toby"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, tool) combos:\n")
        for p, t, u in combos:
            print(f"  {p:12} {t:14} {u}")
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
            header = f"### {p.hero}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
