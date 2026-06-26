#!/usr/bin/env python3
"""
storyworlds/worlds/minimize_cardboard_illustrator_bad_ending_conflict_teamwork.py
==================================================================================

A small adventure story world about an illustrator, a pile of cardboard,
a tight deadline, and a team that must minimize waste before the day turns
into a bad ending.

The domain premise:
- An illustrator is making a big adventure display out of cardboard.
- The room starts with too many scraps, too little time, and a real conflict
  about what to keep.
- The team must work together to minimize cardboard use while still finishing
  the picture.
- If they fail, the ending is bad; if they cooperate, the story ends with a
  neat, brave, finished scene.

This world is intentionally tiny and classical:
- one problem
- one emotional turn
- one practical teamwork fix
- one ending image proving what changed
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("cardboard", 0.0)
        self.meters.setdefault("waste", 0.0)
        self.meters.setdefault("finish", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("conflict", 0.0)
        self.memes.setdefault("teamwork", 0.0)
        self.memes.setdefault("worry", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "illustrator"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the workshop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    reduces: int = 1
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.task_zone: set[str] = set()
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
        clone.fired = set(self.fired)
        clone.task_zone = set(self.task_zone)
        clone.paragraphs = [[]]
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["worry"] < THRESHOLD or ch.memes["teamwork"] >= THRESHOLD:
            continue
        sig = ("conflict", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["conflict"] += 1
        out.append(f"{ch.label} felt the argument knot up in the room.")
    return out


def _r_minimize(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["teamwork"] < THRESHOLD:
            continue
        if ch.meters["cardboard"] < THRESHOLD:
            continue
        sig = ("minimize", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.meters["waste"] = max(0.0, ch.meters["waste"] - 1.0)
        ch.meters["finish"] += 1.0
        out.append(f"The team trimmed the scraps and the cardboard pile got smaller.")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.meters["finish"] < THRESHOLD:
            continue
        sig = ("finish", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["joy"] += 1
        ch.memes["conflict"] = 0.0
        out.append(f"The picture was ready at last.")
    return out


CAUSAL_RULES = [
    _r_conflict,
    _r_minimize,
    _r_finish,
]


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


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.keyword in tool.guards or task.mess in tool.guards:
            return tool
    return None


def predict(world: World, hero: Entity, task: Task) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(hero.id), task, narrate=False)
    return {
        "bad_ending": sim.entities[hero.id].meters["waste"] > 2.0 and sim.entities[hero.id].memes["conflict"] >= THRESHOLD,
        "finish": sim.entities[hero.id].meters["finish"],
    }


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        return
    world.task_zone = set(task.zone)
    hero.meters["cardboard"] += 1.0
    hero.meters["waste"] += 1.0
    hero.memes["worry"] += 1.0
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.label} was a little {trait} illustrator who loved drawing maps, ships, and secret caves."
    )


def setup(world: World, hero: Entity, helper: Entity, task: Task, target: Entity) -> None:
    world.say(
        f"One afternoon, {hero.label} started a big adventure picture with {target.phrase}."
    )
    world.say(
        f"{hero.label} wanted to {task.verb}, because the scene needed to feel wild and bold."
    )
    world.say(
        f"But every new piece of cardboard made the table look messier, and the team had to minimize the scraps."
    )


def conflict_scene(world: World, hero: Entity, helper: Entity, task: Task, target: Entity) -> None:
    pred = predict(world, hero, task)
    if pred["bad_ending"]:
        world.say(
            f"{helper.label} worried that if they kept cutting without care, the story could end in a bad ending."
        )
    world.say(
        f"{hero.label} wanted speed, but {helper.label} wanted neat edges and less cardboard waste."
    )
    world.say(
        f'“We need teamwork,” {helper.label} said. “If we rush, we may ruin the picture.”'
    )


def teamwork_scene(world: World, hero: Entity, helper: Entity, task: Task, target: Entity) -> Optional[Tool]:
    tool = select_tool(task)
    if tool is None:
        return None
    hero.memes["teamwork"] += 1.0
    helper.memes["teamwork"] += 1.0
    world.say(
        f"Then {helper.label} handed over {tool.label}, and the two of them worked side by side."
    )
    world.say(
        f"They used the tool to {tool.prep}, so the cardboard stayed useful instead of becoming waste."
    )
    return tool


def resolution_scene(world: World, hero: Entity, helper: Entity, task: Task, target: Entity, tool: Tool) -> None:
    hero.meters["finish"] += 1.0
    hero.memes["joy"] += 1.0
    helper.memes["joy"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"At last, the adventure picture was finished, with {target.phrase} shining in the middle."
    )
    world.say(
        f"{tool.tail.capitalize()}, and the once-bulky cardboard pile was now small and tidy."
    )
    world.say(
        f"{hero.label} smiled at the clean edges, and {helper.label} smiled too, because teamwork had saved the day."
    )


def tell(setting: Setting, task: Task, target: Entity, hero_name: str = "Mina",
         helper_name: str = "Jo", hero_trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="illustrator", label=hero_name, traits=["little", hero_trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type="friend", label=helper_name))
    target = world.add(target)

    introduce(world, hero)
    setup(world, hero, helper, task, target)
    world.para()
    conflict_scene(world, hero, helper, task, target)
    tool = teamwork_scene(world, hero, helper, task, target)
    world.para()
    if tool is None:
        world.say("Without the right help, the day would have ended badly.")
    else:
        resolution_scene(world, hero, helper, task, target, tool)

    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        target=target,
        tool=tool,
        resolved=tool is not None,
    )
    return world


SETTINGS = {
    "workshop": Setting(place="the workshop", affords={"castle", "map", "dragon"}),
    "studio": Setting(place="the studio", affords={"poster", "ship", "cave"}),
    "attic": Setting(place="the attic", affords={"castle", "ship"}),
}

TASKS = {
    "castle": Task(
        id="castle",
        verb="build a castle from cardboard",
        gerund="building a cardboard castle",
        rush="grab too many boxes",
        mess="cardboard",
        soil="too much cardboard",
        zone={"table"},
        keyword="cardboard",
        tags={"cardboard", "adventure"},
    ),
    "map": Task(
        id="map",
        verb="make a treasure map from cardboard",
        gerund="making a treasure map",
        rush="cut the whole stack at once",
        mess="cardboard",
        soil="a huge pile of cardboard scraps",
        zone={"table"},
        keyword="cardboard",
        tags={"cardboard", "adventure"},
    ),
    "dragon": Task(
        id="dragon",
        verb="shape a dragon from cardboard",
        gerund="shaping a cardboard dragon",
        rush="fold the big pieces too fast",
        mess="cardboard",
        soil="a messy drift of cardboard scraps",
        zone={"table"},
        keyword="cardboard",
        tags={"cardboard", "adventure"},
    ),
    "poster": Task(
        id="poster",
        verb="paint an adventure poster",
        gerund="painting an adventure poster",
        rush="stack the backing boards",
        mess="cardboard",
        soil="too many backing boards",
        zone={"table"},
        keyword="cardboard",
        tags={"cardboard"},
    ),
    "ship": Task(
        id="ship",
        verb="make a ship for the parade",
        gerund="making a parade ship",
        rush="cut every scrap without measuring",
        mess="cardboard",
        soil="a pile of cut-off corners",
        zone={"table"},
        keyword="cardboard",
        tags={"cardboard", "adventure"},
    ),
    "cave": Task(
        id="cave",
        verb="build a cave entrance",
        gerund="building a cave entrance",
        rush="tear the sheets into rough shapes",
        mess="cardboard",
        soil="ragged scraps everywhere",
        zone={"table"},
        keyword="cardboard",
        tags={"cardboard"},
    ),
}

TARGETS = {
    "castle": Entity(id="castle", type="thing", label="the castle", phrase="a tall cardboard castle"),
    "map": Entity(id="map", type="thing", label="the map", phrase="a treasure map with a bright red X"),
    "dragon": Entity(id="dragon", type="thing", label="the dragon", phrase="a bright dragon with paper wings"),
    "poster": Entity(id="poster", type="thing", label="the poster", phrase="a poster for a grand adventure"),
    "ship": Entity(id="ship", type="thing", label="the ship", phrase="a brave cardboard ship"),
    "cave": Entity(id="cave", type="thing", label="the cave", phrase="a cave mouth with dark shadows"),
}

TOOLS = [
    Tool(id="ruler", label="a ruler", prep="measure the pieces before cutting them", tail="The ruler kept the cuts neat", guards={"cardboard"}),
    Tool(id="tape", label="a roll of tape", prep="join only the needed parts", tail="The tape held the little pieces together", guards={"cardboard"}),
    Tool(id="template", label="a paper template", prep="trace only the shapes they truly needed", tail="The paper template helped them use less cardboard", guards={"cardboard"}),
]


@dataclass
class StoryParams:
    place: str
    task: str
    target: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="workshop", task="castle", target="castle", name="Mina", helper="Jo", trait="curious"),
    StoryParams(place="studio", task="map", target="map", name="Tess", helper="Ari", trait="brave"),
    StoryParams(place="attic", task="ship", target="ship", name="Lena", helper="Bo", trait="spirited"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task, target = f["hero"], f["helper"], f["task"], f["target"]
    return [
        f'Write an adventure story for a young child about an illustrator named {hero.label} who must minimize cardboard scraps.',
        f"Tell a short story where {hero.label} and {helper.label} disagree about {task.verb}, then solve the conflict with teamwork.",
        f'Write a gentle adventure with the words "minimize", "cardboard", and "illustrator", ending with a neat finished picture.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, target = f["hero"], f["helper"], f["task"], f["target"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a little illustrator who wanted to make {target.phrase}.",
        ),
        QAItem(
            question=f"What problem did {hero.label} have with the cardboard?",
            answer=f"{hero.label} had too many scraps, so the team needed to minimize the cardboard waste.",
        ),
        QAItem(
            question=f"Why did {helper.label} and {hero.label} argue?",
            answer=f"They argued because {hero.label} wanted to work fast, but {helper.label} wanted to keep the cuts neat and avoid a bad ending.",
        ),
    ]
    if tool is not None:
        qa.append(QAItem(
            question=f"How did {tool.label} help the team?",
            answer=f"{tool.label} helped them measure, join, or trace only the pieces they needed, so they could finish without using too much cardboard.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended well: {hero.label} and {helper.label} worked together, finished {target.phrase}, and left the table tidy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cardboard?",
            answer="Cardboard is a stiff paper material used for boxes, signs, and craft projects.",
        ),
        QAItem(
            question="What does it mean to minimize something?",
            answer="To minimize something means to make it as small as possible or use as little of it as you can.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same goal.",
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
task_problem(T) :- task(T), task_needs_cardboard(T).
conflict(H) :- hero(H), worry(H), wants_fast(H), wants_neat(H).
teamwork(H) :- hero(H), helper(_), agrees_to_help(H).
minimized(H) :- hero(H), teamwork(H), task_problem(_), has_tool(H).
bad_ending(H) :- hero(H), conflict(H), not minimized(H).
good_ending(H) :- hero(H), minimized(H), finished(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for t in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_needs_cardboard", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
    for name in TARGETS:
        lines.append(asp.fact("target", name))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("worry", "hero"))
    lines.append(asp.fact("wants_fast", "hero"))
    lines.append(asp.fact("wants_neat", "helper"))
    lines.append(asp.fact("agrees_to_help", "hero"))
    lines.append(asp.fact("has_tool", "hero"))
    lines.append(asp.fact("finished", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            if task_id in TARGETS:
                combos.append((place, task_id, task_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: minimize cardboard, handle conflict, finish with teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, target = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mina", "Tess", "Lena", "Nora", "Ari"])
    helper = args.helper or rng.choice(["Jo", "Bo", "Kai", "Ira", "Pip"])
    trait = args.trait or rng.choice(["curious", "brave", "spirited", "careful"])
    return StoryParams(place=place, task=task, target=target, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], TARGETS[params.target],
                 hero_name=params.name, helper_name=params.helper, hero_trait=params.trait)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3.\n"))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4.\n"))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, task, target) combos ({len(stories)} with story model):\n")
        for place, task, target in triples:
            print(f"  {place:10} {task:10} {target:10}")
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
