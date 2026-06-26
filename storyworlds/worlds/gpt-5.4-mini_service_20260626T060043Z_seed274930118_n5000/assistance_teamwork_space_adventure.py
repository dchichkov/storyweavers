#!/usr/bin/env python3
"""
storyworlds/worlds/assistance_teamwork_space_adventure.py
=========================================================

A standalone story world about a small space adventure where teamwork and
assistance solve a concrete problem.

Premise:
- A tiny crew is on a short mission in space.
- One crew member needs help with a task that cannot be done alone.
- A useful assistant, tool, or teammate changes the outcome.

The world model tracks physical meters and emotional memes so the narration is
driven by simulated state rather than a fixed template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper: Optional[str] = None
    tool_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") or self.id.endswith("s") else "it"


@dataclass
class Place:
    id: str
    label: str
    cold: bool = False
    dark: bool = False
    drift: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    blocker: str
    need: str
    room: str
    place_tags: set[str] = field(default_factory=set)
    keywords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str]
    helps: set[str]
    prep: str
    finish: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def crew(self) -> list[Entity]:
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

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def safe_join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.drift:
        return out
    for e in world.crew():
        if e.meters.get("floating", 0.0) < THRESHOLD:
            continue
        sig = ("drift", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["risk"] = e.meters.get("risk", 0.0) + 1
        out.append(f"{e.id} drifted too close to the open hatch.")
    return out


def _r_assist(world: World) -> list[str]:
    out: list[str] = []
    for e in world.crew():
        if e.memes.get("helped", 0.0) < THRESHOLD:
            continue
        sig = ("assist", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] = e.memes.get("relief", 0.0) + 1
        out.append(f"{e.id} felt steadier with a teammate nearby.")
    return out


CAUSAL_RULES = [_r_drift, _r_assist]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    perform_task(sim, actor.id, task, narrate=False)
    target = sim.entities[actor.id]
    return {
        "risk": target.meters.get("risk", 0.0) >= THRESHOLD,
        "helped": target.memes.get("helped", 0.0) >= THRESHOLD,
    }


def perform_task(world: World, actor_id: str, task: Task, narrate: bool = True) -> None:
    actor = world.get(actor_id)
    if task.id not in world.place.affords:
        return
    actor.meters[task.need] = actor.meters.get(task.need, 0.0) + 1
    propagate(world, narrate=narrate)


def setup_line(world: World, hero: Entity, friend: Entity, task: Task) -> None:
    world.say(
        f"{hero.id} was a {hero.type} on a small space mission, and {hero.id} loved working with {friend.id}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {task.verb}, because the ship needed careful hands and teamwork."
    )


def introduce_place(world: World, task: Task) -> None:
    p = world.place
    if p.cold and p.dark:
        world.say(
            f"The ship was quiet in the cold dark of space, where every move had to be gentle."
        )
    elif p.dark:
        world.say("The station lights glowed softly, and the corridor felt long and still.")
    else:
        world.say(f"The module was bright, and the work bay waited for the crew.")
    if task.id in p.affords:
        world.say(f"That was exactly the kind of place where they could {task.verb}.")


def need_help(world: World, hero: Entity, friend: Entity, task: Task, tool: Tool) -> bool:
    pred = predict_risk(world, hero, task)
    if not pred["risk"]:
        return False
    world.facts["predicted_risk"] = True
    world.say(
        f'"If you try to {task.verb}, you could get into {task.blocker}," {friend.pronoun("possessive")} friend said.'
    )
    return True


def offer_help(world: World, helper: Entity, hero: Entity, task: Task, tool: Tool) -> Optional[Tool]:
    if task.id not in tool.helps:
        return None
    hero.memes["helped"] = hero.memes.get("helped", 0.0) + 1
    world.say(
        f'{helper.id} held up {tool.phrase} and said, "{tool.prep}."'
    )
    return tool


def accept_help(world: World, hero: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    world.say(
        f"{hero.id} nodded and smiled. With {helper.id}'s help, {hero.id} could stay safe and still get the job done."
    )
    world.say(
        f"They {tool.finish}, and soon {hero.id} was {task.gerund} without any trouble."
    )


def tell(place: Place, task: Task, tool: Tool, hero_name: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="pilot", traits=["careful", "brave"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="engineer", traits=["kind", "clever"]))
    bot = world.add(Entity(id="Robot", kind="character", type="robot", traits=["steady"]))

    world.facts.update(hero=hero, helper=helper, bot=bot, task=task, tool=tool)

    setup_line(world, hero, helper, task)
    world.para()
    introduce_place(world, task)
    need_help(world, hero, helper, task, tool)
    world.say(f"{hero.id} wanted to do it alone, but the job needed more than one pair of hands.")
    world.say(f"{helper.id} and {bot.id} moved closer so the work would be easier together.")
    world.para()
    offer_help(world, helper, hero, task, tool)
    accept_help(world, hero, helper, task, tool)

    if helper.memes.get("helped", 0.0) >= THRESHOLD:
        helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    world.facts["resolved"] = True
    return world


PLACES = {
    "dock": Place(id="dock", label="the docking bay", cold=True, dark=True, affords={"repair", "tow"}),
    "cargo": Place(id="cargo", label="the cargo hold", dark=True, affords={"lift", "repair"}),
    "window": Place(id="window", label="the observatory window", cold=True, affords={"clean", "repair"}),
    "bay": Place(id="bay", label="the bright service bay", affords={"repair", "sort"}),
    "orbit": Place(id="orbit", label="the orbit ring", drift=True, affords={"tow", "repair"}),
}

TASKS = {
    "repair": Task(
        id="repair",
        verb="repair the broken panel",
        gerund="repairing the broken panel",
        risk="a loose spark",
        blocker="the wrong wire",
        need="steady_hands",
        room="panel",
        place_tags={"dock", "cargo", "window", "bay", "orbit"},
        keywords={"repair", "panel", "teamwork"},
    ),
    "tow": Task(
        id="tow",
        verb="guide the tiny shuttle back",
        gerund="guiding the tiny shuttle back",
        risk="drifting off course",
        blocker="the cold pull of space",
        need="direction",
        room="shuttle",
        place_tags={"dock", "orbit"},
        keywords={"tow", "shuttle", "assistance"},
    ),
    "clean": Task(
        id="clean",
        verb="clean the window",
        gerund="cleaning the window",
        risk="smearing the glass",
        blocker="a slippery cloth",
        need="care",
        room="window",
        place_tags={"window", "bay"},
        keywords={"clean", "window", "help"},
    ),
    "sort": Task(
        id="sort",
        verb="sort the cargo crates",
        gerund="sorting the cargo crates",
        risk="mixing up the labels",
        blocker="too many heavy boxes",
        need="strength",
        room="crates",
        place_tags={"cargo", "bay"},
        keywords={"sort", "cargo", "teamwork"},
    ),
}

TOOLS = {
    "tether": Tool(
        id="tether",
        label="a safety tether",
        phrase="a safety tether",
        protects={"drift"},
        helps={"tow"},
        prep="Clip this on, and we'll guide the shuttle together",
        finish="clipped on the tether and steered the shuttle home",
    ),
    "wrench": Tool(
        id="wrench",
        label="a small wrench",
        phrase="a small wrench",
        protects={"spark"},
        helps={"repair"},
        prep="Use this wrench, and I can hold the panel steady",
        finish="held the panel and tightened the last bolt",
    ),
    "cloth": Tool(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth",
        protects={"smear"},
        helps={"clean"},
        prep="Wipe in slow circles, and the glass will shine",
        finish="wiped the window until it sparkled",
    ),
    "lift": Tool(
        id="lift",
        label="a cargo lifter",
        phrase="a cargo lifter",
        protects={"crush"},
        helps={"sort"},
        prep="Share the load, and the crates will move faster",
        finish="lifted the heavy crates without dropping one",
    ),
}

NAMES = ["Mira", "Jace", "Nora", "Tao", "Ivy", "Luz", "Finn", "Rin"]
HELPERS = ["Ari", "Bea", "Cole", "Dax", "Ena", "Pax"]


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            if pid not in task.place_tags:
                continue
            for toid, tool in TOOLS.items():
                if tid in tool.helps:
                    combos.append((pid, tid, toid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny teamwork space adventure story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
        raise StoryError("No valid combination matches the given options.")
    place, task, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        task=task,
        tool=tool,
        hero=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, tool = f["hero"], f["helper"], f["task"], f["tool"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {world.place.label}?",
            answer=f"{hero.id} was trying to {task.verb}. {helper.id} stayed close so the work would be safe."
        ),
        QAItem(
            question=f"Why did {helper.id} offer {tool.label}?",
            answer=f"{helper.id} offered {tool.label} because it made it possible to {task.verb} together without getting into {task.blocker}."
        ),
        QAItem(
            question=f"How did teamwork change the ending?",
            answer=f"Teamwork turned a risky job into a shared job, so {hero.id} could finish {task.gerund} with help from {helper.id}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and use their different strengths to finish a job together."
        ),
        QAItem(
            question="What is assistance?",
            answer="Assistance is help that one person gives to another when a task is hard to do alone."
        ),
        QAItem(
            question="Why do spaceships use tools?",
            answer="Spaceships use tools because careful work in space can be hard, and the right tool helps the crew stay safe and solve problems."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space adventure story that includes the word "assistance" and shows teamwork.',
        f"Tell a short story where {f['hero'].id} and {f['helper'].id} work together to {f['task'].verb} using {f['tool'].label}.",
        f"Write a gentle spaceship story with a problem, an offer of help, and a happy ending in {world.place.label}.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place_valid(P) :- place(P).
task_valid(T) :- task(T).
tool_valid(U) :- tool(U).

compatible(P,T,U) :- place_valid(P), task_valid(T), tool_valid(U),
                    place_affords(P,T), tool_helps(U,T).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.cold:
            lines.append(asp.fact("cold", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.drift:
            lines.append(asp.fact("drift", pid))
        for t in sorted(p.affords):
            lines.append(asp.fact("place_affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for pt in sorted(t.place_tags):
            lines.append(asp.fact("task_place", tid, pt))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("tool_helps", uid, h))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], TOOLS[params.tool], params.hero, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="dock", task="tow", tool="tether", hero="Mira", helper="Ari"),
    StoryParams(place="cargo", task="sort", tool="lift", hero="Jace", helper="Bea"),
    StoryParams(place="window", task="clean", tool="cloth", hero="Nora", helper="Cole"),
    StoryParams(place="bay", task="repair", tool="wrench", hero="Tao", helper="Dax"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, task, tool) combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
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
            except StoryError as e:
                print(e)
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
