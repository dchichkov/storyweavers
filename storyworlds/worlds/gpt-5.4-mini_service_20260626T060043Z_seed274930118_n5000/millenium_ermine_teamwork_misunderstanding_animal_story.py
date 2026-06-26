#!/usr/bin/env python3
"""
storyworlds/worlds/millenium_ermine_teamwork_misunderstanding_animal_story.py
=============================================================================

A small animal-story world about an ermine, a millenium celebration, teamwork,
and a misunderstanding that gets cleared up by helping together.

The source tale that inspired this world is a gentle animal story: a small
ermine wants to help with a once-in-a-millenium lantern ceremony, but its quick
movements and white fur make other animals misread its actions. The animals
pause, explain, and work together, turning confusion into a bright shared job.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.task: Optional[Task] = None
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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.task = self.task
        clone.paragraphs = [[]]
        return clone


TEAMWORK_RULES = [
    ("help_loaded", "physical"),
    ("misunderstanding", "social"),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule_name, _ in TEAMWORK_RULES:
            if rule_name == "help_loaded":
                for e in world.characters():
                    if e.meters.get("load", 0.0) < THRESHOLD:
                        continue
                    sig = ("help_loaded", e.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    e.memes["tired"] = e.memes.get("tired", 0.0) + 1
                    out.append(f"{e.label} felt the weight of the job.")
                    changed = True
            elif rule_name == "misunderstanding":
                for e in world.characters():
                    if e.memes.get("misunderstanding", 0.0) < THRESHOLD:
                        continue
                    sig = ("misunderstanding", e.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    e.memes["hurt"] = e.memes.get("hurt", 0.0) + 1
                    out.append(f"That left {e.label} feeling wrongly judged.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(place: Place, task: Task, tool: Tool) -> bool:
    return task.id in place.affords and task.risk in tool.helps and task.zone.issubset(tool.covers)


def predict_misunderstanding(world: World, actor: Entity, task: Task) -> bool:
    sim = world.copy()
    do_task(sim, sim.get(actor.id), task, narrate=False)
    return sim.get(actor.id).memes.get("misunderstanding", 0.0) >= THRESHOLD


def do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.id] = actor.meters.get(task.id, 0.0) + 1
    actor.meters["load"] = actor.meters.get("load", 0.0) + 1
    if task.id == "carry":
        actor.memes["misunderstanding"] = actor.memes.get("misunderstanding", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} was a small {hero.type} with quick paws and a careful heart.")


def mention_millenium(world: World, place: Place) -> None:
    world.say(
        f"At {place.name}, the animals were preparing for a millenium lantern night, "
        f"the kind of celebration that only came once in a very long while."
    )


def set_scene(world: World, hero: Entity, friend: Entity, task: Task) -> None:
    world.say(
        f"{hero.label} loved helping with long jobs, and {friend.label} knew "
        f"{hero.pronoun('subject')} could carry light things fast."
    )
    world.say(
        f"That morning, the two friends went to the lantern field to {task.verb} "
        f"for the millenium celebration."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, task: Task) -> None:
    hero.memes["misunderstanding"] = hero.memes.get("misunderstanding", 0.0) + 1
    world.say(
        f"When {hero.label} hurried off with the ribbon spool, {friend.label} frowned "
        f"and thought {hero.pronoun('subject')} had taken the ribbon without asking."
    )
    world.say(
        f"{friend.label} called out, and {hero.label} stopped so fast that the grass shook."
    )


def explain(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["misunderstanding"] = 0.0
    friend.memes["misunderstanding"] = 0.0
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    world.say(
        f"{hero.label} explained that {hero.pronoun('subject')} was only carrying the spool "
        f"to the north post, because the ribbon kept slipping in the wind."
    )
    world.say(
        f"{friend.label} blinked, then nodded, because the truth made the whole moment easy to see."
    )


def teamwork(world: World, hero: Entity, friend: Entity, tool: Tool, task: Task) -> None:
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        plural=tool.plural,
        owner=hero.id,
    ))
    tool_ent.worn_by = hero.id
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"Then {friend.label} brought {tool.label}, and the two friends worked side by side."
    )
    world.say(
        f"{tool.tail.capitalize()}, and soon the lantern posts were ready for the millenium night."
    )


TASKS = {
    "carry": Task(
        id="carry",
        verb="carry lantern posts",
        gerund="carrying lantern posts",
        rush="dash off with the poles",
        risk="wind",
        zone={"paws"},
        keyword="lantern",
        tags={"lantern", "wind", "teamwork"},
    ),
    "bundle": Task(
        id="bundle",
        verb="bundle the ribbons",
        gerund="bundling ribbons",
        rush="gather the ribbons quickly",
        risk="tangle",
        zone={"paws"},
        keyword="ribbon",
        tags={"ribbon", "teamwork"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a soft rope loop",
        prep="tie the posts together gently",
        tail="the soft rope loop helped tie the posts together gently",
        helps={"wind"},
        covers={"paws"},
    ),
    "basket": Tool(
        id="basket",
        label="a shallow basket",
        prep="carry the ribbons without dropping them",
        tail="the shallow basket kept the ribbons neat",
        helps={"tangle"},
        covers={"paws"},
    ),
}

PLACES = {
    "meadow": Place(name="the moon meadow", affords={"carry", "bundle"}),
    "grove": Place(name="the willow grove", affords={"carry"}),
}

HERO_TYPES = ["ermine", "rabbit", "fox", "mouse", "squirrel", "badger"]
HERO_NAMES = ["Mina", "Pip", "Tansy", "Nori", "Bran", "Lulu", "Moss"]
FRIEND_NAMES = ["Ivo", "Kiri", "Jem", "Sora", "Bram", "Wren"]


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    hero_name: str
    hero_type: str
    friend_name: str
    seed: Optional[int] = None


def pick_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if reasonableness_gate(PLACES["meadow"], task, tool):
            return tool
    return None


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    if not reasonableness_gate(place, task, tool):
        raise StoryError("The chosen task and tool do not fit the animal job.")
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="rabbit", label=params.friend_name))
    world.task = task

    introduce(world, hero)
    mention_millenium(world, place)
    set_scene(world, hero, friend, task)
    misunderstanding(world, hero, friend, task)
    do_task(world, hero, task)
    world.para()
    explain(world, hero, friend)
    teamwork(world, hero, friend, tool, task)

    world.facts.update(
        hero=hero,
        friend=friend,
        task=task,
        tool=tool,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    task: Task = f["task"]
    place: Place = f["place"]
    return [
        f"Write a short animal story about {hero.label}, a {hero.type}, helping at {place.name} during a millenium celebration.",
        f"Tell a gentle story where {hero.label} and {friend.label} have a misunderstanding, then solve it with teamwork.",
        f"Write a child-friendly story that uses the word millenium and ends with friends working together.",
        f"Make a small animal story about {task.gerund} and a kind misunderstanding in {place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    task: Task = f["task"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a small {hero.type}, and the friend {friend.label} at {place.name}.",
        ),
        QAItem(
            question=f"What was the big job for the millenium celebration?",
            answer=f"The animals were {task.gerund} so the lantern field could be ready for the millenium night.",
        ),
        QAItem(
            question=f"Why did the friend think there was a problem?",
            answer=f"{friend.label} thought {hero.label} had taken the ribbon spool without asking, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"How did the animals fix the misunderstanding?",
            answer=f"{hero.label} explained the truth, and then {hero.label} and {friend.label} used teamwork to finish the job together.",
        ),
    ]


KNOWLEDGE = {
    "ermine": [(
        "What is an ermine?",
        "An ermine is a small weasel with a sleek body and a white winter coat.",
    )],
    "millenium": [(
        "What does millenium mean in a story?",
        "In a story, millenium can mean a very long time or a special once-in-a-long-while celebration.",
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means people or animals help each other and do a job together.",
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone thinks the wrong thing, even though the truth is different.",
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light that helps people see in the dark.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.add("ermine")
    tags.add("millenium")
    out: list[QAItem] = []
    for tag in ["ermine", "millenium", "teamwork", "misunderstanding", "lantern"]:
        if tag in tags or tag in KNOWLEDGE:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", task="carry", tool="rope", hero_name="Mina", hero_type="ermine", friend_name="Ivo"),
    StoryParams(place="meadow", task="bundle", tool="basket", hero_name="Pip", hero_type="ermine", friend_name="Kiri"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: ermine, millenium, teamwork, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--type", choices=HERO_TYPES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, place in PLACES.items():
        for t, task in TASKS.items():
            for tool in TOOLS.values():
                if reasonableness_gate(place, task, tool):
                    combos.append((p, t, tool.id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid animal story matches those choices.")
    place, task, tool = rng.choice(sorted(combos))
    hero_type = args.type or "ermine"
    if hero_type != "ermine":
        raise StoryError("This world is built around an ermine hero.")
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, task=task, tool=tool, hero_name=name, hero_type=hero_type, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
place(P) :- setting(P).
task(T) :- task_id(T).
tool(U) :- tool_id(U).

valid(P,T,U) :- affords(P,T), helps(U,R), task_risk(T,R), covers(U,C), task_zone(T,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for t in sorted(p.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task_id", tid))
        lines.append(asp.fact("task_risk", tid, t.risk))
        for z in sorted(t.zone):
            lines.append(asp.fact("task_zone", tid, z))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool_id", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
        for c in sorted(u.covers):
            lines.append(asp.fact("covers", uid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
