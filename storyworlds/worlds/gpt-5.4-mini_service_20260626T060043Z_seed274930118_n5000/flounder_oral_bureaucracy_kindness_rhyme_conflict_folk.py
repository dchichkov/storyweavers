#!/usr/bin/env python3
"""
A folk-tale storyworld about a flounder, an oral petition, and a kind way
through bureaucracy.

The seed tale:
---
In a little harbor town, Flurry the flounder wished to bring fresh seaweed to
the market on Market Day. But the harbor office was full of bureaucracy: a
stern clerk wanted forms, stamps, and signatures before any cart could roll.

Flurry could not write well on paper, but she could speak clearly. A kindly
librarian taught her an oral petition in rhyme, and the village children sang
the lines with her. The clerk listened, the rules were heard, and the market
gate opened. In the end, the flounder's seaweed was welcomed, and the town
learned that kindness can slip through hard doors when it arrives with a rhyme.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"flounder", "fish", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    action: str
    oral_need: str
    risk: str
    rhyme_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    helps: set[str]
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy as _copy

        c = World(self.place)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "harbor": Place(name="the harbor town", kind="outdoor", affords={"petition"}),
    "square": Place(name="the village square", kind="outdoor", affords={"petition"}),
    "hall": Place(name="the town hall", kind="indoor", affords={"petition"}),
}

TASKS = {
    "petition": Task(
        id="petition",
        action="ask the harbor office for permission to sell seaweed",
        oral_need="speak the request out loud",
        risk="the clerk will send her away for missing papers",
        rhyme_key="petition",
        tags={"oral", "bureaucracy", "rhyme"},
    ),
    "appeal": Task(
        id="appeal",
        action="appeal the gatekeeper's refusal",
        oral_need="tell the whole request clearly",
        risk="the gatekeeper will keep the gate shut",
        rhyme_key="appeal",
        tags={"oral", "bureaucracy", "conflict"},
    ),
    "permission": Task(
        id="permission",
        action="ask to bring the market cart through",
        oral_need="speak in a steady voice",
        risk="the market day will pass by without her",
        rhyme_key="permission",
        tags={"oral", "bureaucracy", "kindness"},
    ),
}

AIDS = {
    "rhyme": Aid(
        id="rhyme",
        label="a friendly rhyme",
        helps={"oral"},
        method="speak in rhyme",
        tags={"rhyme", "kindness"},
    ),
    "song": Aid(
        id="song",
        label="a children's song",
        helps={"oral"},
        method="sing the words together",
        tags={"rhyme", "kindness"},
    ),
    "bell": Aid(
        id="bell",
        label="a listening bell",
        helps={"oral", "bureaucracy"},
        method="ring the bell and wait for a turn",
        tags={"bureaucracy"},
    ),
}

HEROES = {
    "flurry": ("Flurry", "flounder", ["small", "patient", "brave"]),
    "mina": ("Mina", "flounder", ["small", "gentle", "steady"]),
    "sable": ("Sable", "flounder", ["small", "clever", "kind"]),
}

HELPERS = {
    "librarian": ("Librarian", "librarian"),
    "child": ("Children", "children"),
    "uncle": ("Uncle Tide", "uncle"),
}

CLERKS = {
    "clerk": ("Clerk Reed", "clerk"),
    "keeper": ("Gatekeeper Moss", "keeper"),
}


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    clerk: str
    aid: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.clerk not in CLERKS:
        raise StoryError("Unknown clerk.")
    if params.aid not in AIDS:
        raise StoryError("Unknown aid.")
    task = TASKS[params.task]
    aid = AIDS[params.aid]
    if "oral" not in task.tags or "oral" not in aid.helps:
        raise StoryError("The tale needs an oral path through bureaucracy.")
    if "rhyme" not in task.tags and "rhyme" in aid.tags:
        # allowed, but avoid weak mismatch only if no rhyme at all
        pass


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
        lines.append(asp.fact("place_kind", pid, place.kind))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("task_tag", tid, tag))
        lines.append(asp.fact("oral_need", tid, task.oral_need))
    for aid, item in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for h in sorted(item.helps):
            lines.append(asp.fact("helps", aid, h))
        for tag in sorted(item.tags):
            lines.append(asp.fact("aid_tag", aid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,A) :- place(P), task(T), aid(A), affords(P,petition), task_tag(T,oral), helps(A,oral).
featured(T) :- task_tag(T,bureaucracy), task_tag(T,kindness).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in SETTINGS.items():
        if "petition" not in place.affords:
            continue
        for tid, task in TASKS.items():
            if "oral" not in task.tags:
                continue
            for aid, item in AIDS.items():
                if "oral" in item.helps:
                    combos.append((pid, tid, aid))
    return combos


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def choose_name(hero_key: str) -> tuple[str, str, list[str]]:
    return HEROES[hero_key]


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_name, hero_type, traits = HEROES[params.hero]
    helper_name, helper_type = HELPERS[params.helper]
    clerk_name, clerk_type = CLERKS[params.clerk]
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=traits))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name))
    clerk = world.add(Entity(id="clerk", kind="character", type=clerk_type, label=clerk_name))
    task = TASKS[params.task]
    aid = AIDS[params.aid]
    world.facts.update(hero=hero, helper=helper, clerk=clerk, task=task, aid=aid, params=params)

    hero.memes["want"] = 1.0
    task_owner = world.add(Entity(id="task", type="task", label=task.id))
    task_owner.meters["importance"] = 1.0

    world.say(
        f"In {world.place.name}, there lived a little {hero_type} named {hero_name}, "
        f"who loved to help the town keep its fish-market fair."
    )
    world.say(
        f"One day, {hero_name} wished to {task.action}, but the harbor office had more "
        f"bureaucracy than a crab has pins."
    )

    world.para()
    hero.memes["anxiety"] = 1.0
    clerk.memes["sternness"] = 1.0
    world.say(
        f"The {clerk_type} at the desk said, \"No papers, no passage,\" and {hero_name} felt "
        f"the old conflict tug at {hero.pronoun('possessive')} fins."
    )
    world.say(
        f"{hero_name} could not make the forms fill themselves, and the door stayed shut."
    )

    world.para()
    helper.memes["kindness"] = 1.0
    hero.memes["hope"] = 1.0
    world.say(
        f"Then {helper_name} came with {aid.label}, because kindness travels well in a folk tale."
    )
    world.say(
        f"{helper_name} taught {hero_name} to {aid.method}, so the request could be heard by every ear in the room."
    )
    hero.memes["rhyme"] = 1.0

    world.para()
    if params.aid in {"rhyme", "song"}:
        clerk.memes["listening"] = 1.0
        world.say(
            f"{hero_name} spoke in a bright rhyme: \"I bring the seaweed, neat and clean; "
            f"let market day be fair and seen.\""
        )
        world.say(
            f"The clerk listened, the children smiled, and the hard little rules seemed less hard."
        )
    else:
        world.say(
            f"{helper_name} rang the bell and waited, and when the turn came, {hero_name} "
            f"spoke calmly and clearly."
        )
        world.say(
            f"Even the clerk could not deny a voice that was patient and true."
        )

    world.para()
    hero.memes["joy"] = 1.0
    clerk.memes["softened"] = 1.0
    world.say(
        f"At last the gate opened. {hero_name} rolled the cart through, and the seaweed reached the market."
    )
    world.say(
        f"By sunset, the town remembered that kindness and rhyme can pass where gruffness cannot."
    )
    world.trace_notes.append("conflict_resolved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    task = f["task"].action
    return [
        "Write a folk tale about a flounder who must speak to the town office instead of writing.",
        f"Tell a child-friendly story where {hero} must {task} and finds a kind way through bureaucracy.",
        "Make the ending cheerful and rhythmic, with a helper and a listening clerk.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    clerk = f["clerk"].label
    task = f["task"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero}, a little flounder who wants to {task.action}.",
        ),
        QAItem(
            question=f"Why was there conflict at the harbor office?",
            answer=f"There was conflict because the clerk wanted papers and the {hero.lower()} had to find an oral way to be heard.",
        ),
        QAItem(
            question=f"How did {helper} help {hero}?",
            answer=f"{helper} helped by bringing {aid.label} and showing {hero} how to {aid.method}.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {clerk} listened, the gate opened, and {hero}'s request was accepted.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bureaucracy?",
            answer="Bureaucracy is the set of rules, papers, and official steps people use to make decisions in an office or town.",
        ),
        QAItem(
            question="What does oral mean?",
            answer="Oral means spoken out loud with words instead of written on paper.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like song and long.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means acting gently and helpfully so someone else feels safe and welcome.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  notes={world.trace_notes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale world: a flounder, oral bureaucracy, kindness, rhyme, and conflict.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--hero", choices=HEROES.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--clerk", choices=CLERKS.keys())
    ap.add_argument("--aid", choices=AIDS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.task and args.task not in TASKS:
        raise StoryError("Unknown task.")
    if args.hero and args.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if args.clerk and args.clerk not in CLERKS:
        raise StoryError("Unknown clerk.")
    if args.aid and args.aid not in AIDS:
        raise StoryError("Unknown aid.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, task, aid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    clerk = args.clerk or rng.choice(sorted(CLERKS))
    return StoryParams(place=place, task=task, hero=hero, helper=helper, clerk=clerk, aid=aid)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


CURATED = [
    StoryParams(place="harbor", task="petition", hero="flurry", helper="librarian", clerk="clerk", aid="rhyme"),
    StoryParams(place="square", task="appeal", hero="mina", helper="child", clerk="keeper", aid="song"),
    StoryParams(place="hall", task="permission", hero="sable", helper="uncle", clerk="clerk", aid="bell"),
]


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program_for_stories(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t, a in combos:
            print(f"  {p}  {t}  {a}")
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
            header = f"### {p.hero}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
