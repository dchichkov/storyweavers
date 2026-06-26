#!/usr/bin/env python3
"""
A tiny whodunit storyworld about a puzzly mess, a loud wail, and a helpful fix.

The seed words are woven into the domain:
- wail: a cry that alerts everyone to trouble
- caca: the messy clue that needs cleaning
- pudgy: a small, round little pet who can be part of the mystery

This world follows the Storyweavers contract with:
- typed entities with meters and memes
- a state-driven story
- a reasonableness gate in Python and ASP
- verification helpers and QA generation
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

# Physical/emotional thresholds for narration.
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character", "pet", "object"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "dirty", "clean", "tired", "clue"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "fear", "relief", "joy", "curiosity", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    mess: str
    clue_word: str
    verb: str
    result: str
    at_risk: str
    fix_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story_parts: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_parts[-1].append(text)

    def para(self) -> None:
        if self.story_parts[-1]:
            self.story_parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story_parts if p)


def _resolve_article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def _subject_name(e: Entity) -> str:
    return e.label or e.id


def _name_or_pronoun(e: Entity, case: str = "subject") -> str:
    if e.kind == "character":
        return e.id
    return e.pronoun(case)


def place_intro(world: World) -> None:
    world.say(f"At {world.setting.place}, every corner had a little something to notice.")
    world.say("The room was quiet enough that even a tiny sound felt important.")


def add_whodunit_setup(world: World, detective: Entity, parent: Entity, pet: Entity, problem: Problem, victim: Entity) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a small detective who loved clues and careful looking."
    )
    world.say(
        f"{detective.id} had a pudgy little friend named {pet.label}, and {pet.pronoun('subject')} "
        f"liked to follow along with tiny pats and tiny hops."
    )
    world.say(
        f"One afternoon, {pet.label}'s {parent.label} gasped at a {problem.mess} mess near {victim.label}."
    )
    world.say(
        f"Then came a loud wail from the hallway, and everyone knew something had gone wrong."
    )


def produce_clue(world: World, detective: Entity, problem: Problem, victim: Entity) -> None:
    detective.meters["clue"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} knelt beside the spot and saw the clue: {problem.clue_word} on the floor."
    )
    world.say(
        f"{detective.id} looked at {victim.label} and wondered who had gotten so close to the mess."
    )


def suspect_scene(world: World, detective: Entity, suspect: Entity, problem: Problem) -> None:
    suspect.memes["worry"] += 1
    world.say(
        f"{detective.id} asked {suspect.id} a careful question."
    )
    world.say(
        f"{suspect.id} shook {suspect.pronoun('possessive')} head. "
        f'"I did not make the {problem.mess}," {suspect.pronoun()} said, still sniffly from the wail.'
    )


def solve_mystery(world: World, detective: Entity, pet: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"{detective.id} noticed a tiny trail and followed it to {pet.label}."
    )
    world.say(
        f"{pet.label} had stepped through the {problem.mess} after trying to reach {problem.result}."
    )
    world.say(
        f"That was the clue: {pet.label} was not naughty, just pudgy and hungry."
    )
    world.say(
        f'{detective.id} smiled and said, "We can solve this."'
    )
    world.say(
        f'They used {tool.label} to clean the spot and moved {problem.result} out of reach.'
    )
    pet.memes["relief"] += 1
    detective.memes["joy"] += 1
    world.facts["solved_by"] = pet.id
    world.facts["tool"] = tool.id


def ending_image(world: World, detective: Entity, pet: Entity, victim: Entity, problem: Problem) -> None:
    world.say(
        f"By the end, the floor was clean, {pet.label} was calm, and the room felt safe again."
    )
    world.say(
        f"{detective.id} gave {pet.label} a gentle pat, and {pet.label} gave a small, happy snuffle."
    )
    world.say(
        f"The little mystery was solved: the caca mess had a simple reason, and everyone knew what to do next."
    )
    world.facts["ending"] = f"{pet.id} was hungry; {problem.result} was moved; {problem.mess} was cleaned"


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"search", "clean"}),
    "hallway": Setting(place="the hallway", indoor=True, affords={"search", "clean"}),
    "mudroom": Setting(place="the mudroom", indoor=True, affords={"search", "clean"}),
}

PROBLEMS = {
    "cookie": Problem(
        id="cookie",
        name="lost cookie",
        mess="caca",
        clue_word="a smudge",
        verb="sniff around",
        result="the cookie",
        at_risk="the floor",
        fix_word="clean cloth",
        tags={"food", "mess", "clue"},
    ),
    "crumbs": Problem(
        id="crumbs",
        name="crumb puzzle",
        mess="caca",
        clue_word="tiny crumbs",
        verb="search for snacks",
        result="the crumbs",
        at_risk="the rug",
        fix_word="broom",
        tags={"food", "mess", "clue"},
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="a clean cloth",
        helps={"caca"},
        covers={"floor"},
        prep="wipe the spot",
        tail="they wiped until nothing sticky remained",
    ),
    "broom": Tool(
        id="broom",
        label="a small broom",
        helps={"caca"},
        covers={"rug", "floor"},
        prep="sweep the floor",
        tail="they swept the crumbs into a neat little pile",
    ),
    "basket": Tool(
        id="basket",
        label="a snack basket",
        helps={"search"},
        covers=set(),
        prep="move the snack basket higher",
        tail="they put the treats on a high shelf",
    ),
}

GIRL_NAMES = ["Nina", "Mina", "Luna", "Maya", "Sia"]
BOY_NAMES = ["Pip", "Otto", "Jules", "Finn", "Toby"]
TRAITS = ["careful", "brave", "curious", "gentle", "sharp"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            for tool in TOOLS.values():
                if "caca" in tool.helps:
                    out.append((place, pid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about a pudgy clue and a caca mess.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, problem=problem, name=name, gender=gender, parent=parent, trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    world = World(setting)

    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    pet = world.add(Entity(id="Pudgy", kind="pet", type="pet", label="Pudgy", phrase="a pudgy little pet"))
    victim = world.add(Entity(id="spot", kind="object", type="object", label="the floor"))

    place_intro(world)
    add_whodunit_setup(world, detective, parent, pet, problem, victim)
    world.para()
    produce_clue(world, detective, problem, victim)
    suspect_scene(world, detective, parent, problem)
    world.para()
    solve_mystery(world, detective, pet, problem, TOOLS["cloth"] if params.place != "hallway" else TOOLS["broom"])
    ending_image(world, detective, pet, victim, problem)

    world.facts.update(
        detective=detective,
        parent=parent,
        pet=pet,
        victim=victim,
        problem=problem,
        tool=TOOLS["cloth"] if params.place != "hallway" else TOOLS["broom"],
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
    detective = f["detective"]
    problem = f["problem"]
    return [
        f'Write a short whodunit for a young child about {detective.id}, a pudgy clue, and a {problem.mess} mess.',
        f"Tell a gentle mystery where {detective.id} notices a wail, asks questions, and solves the caca problem.",
        f"Write a small detective story that ends with the mess cleaned and the real reason discovered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    parent = f["parent"]
    pet = f["pet"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who solved the mystery in {world.setting.place}?",
            answer=f"{detective.id} solved it by noticing the clue and asking careful questions.",
        ),
        QAItem(
            question=f"What was the messy clue?",
            answer=f"The messy clue was {problem.mess}, and it showed someone had been close to the spot.",
        ),
        QAItem(
            question=f"Why was Pudgy involved?",
            answer=f"Pudgy had followed the smell of {problem.result} and stepped through the mess because {pet.label} was hungry.",
        ),
        QAItem(
            question=f"What did they use to fix the problem?",
            answer=f"They used {tool.label} to clean the mess and make the room tidy again.",
        ),
        QAItem(
            question=f"Why did the story begin with a wail?",
            answer=f"The wail happened because someone found the caca mess and knew something needed to be solved right away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully, asks questions, and uses clues to solve a problem.",
        ),
        QAItem(
            question="Why do people clean a mess?",
            answer="People clean a mess so the place is safe, neat, and comfortable again.",
        ),
        QAItem(
            question="What does pudgy mean?",
            answer="Pudgy means a little round or chubby, often in a cute way.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A problem is reasonable if it has a caca mess and a clean-up tool.
reasonable_problem(P) :- problem(P), mess_of(P, caca).
reasonable_tool(T) :- tool(T), helps(T, caca).

% A valid story has a place, a problem, and at least one tool that can clean it.
valid_story(Place, Problem, Tool) :- setting(Place), affords(Place, Problem),
                                     reasonable_problem(Problem), reasonable_tool(Tool).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess_of", pid, prob.mess))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, pr) for p, pr in valid_combos())
    asp_set = set((a, b) for a, b, _ in asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - asp_set))
    print("clingo only:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(place="kitchen", problem="cookie", name="Nina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="hallway", problem="crumbs", name="Pip", gender="boy", parent="father", trait="careful"),
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, pr, t in combos:
            print(f"  {p} {pr} {t}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
