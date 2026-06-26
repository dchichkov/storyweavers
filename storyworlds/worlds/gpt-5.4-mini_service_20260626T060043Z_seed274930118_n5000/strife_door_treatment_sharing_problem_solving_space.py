#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale about strife, a
stuck door, and a shared treatment that helps the crew solve a problem together.
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
# Core model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
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


@dataclass
class Setting:
    place: str
    afford_door: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    shareable: bool = True


@dataclass
class Problem:
    id: str
    verb: str
    noun: str
    mess: str
    zone: str
    fix_kind: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable


def _r_strife(world: World) -> list[str]:
    out = []
    crew = [e for e in world.entities.values() if e.kind == "character"]
    if len(crew) >= 2 and world.facts.get("argument") and ("strife",) not in world.fired:
        world.fired.add(("strife",))
        for e in crew:
            e.memes["strife"] = e.memes.get("strife", 0.0) + 1.0
        out.append("The air in the ship felt tight with strife.")
    return out


def _r_door_stuck(world: World) -> list[str]:
    out = []
    door = world.entities.get("door")
    if not door:
        return out
    if world.facts.get("jammed") and not world.facts.get("door_open") and ("door_stuck",) not in world.fired:
        world.fired.add(("door_stuck",))
        door.meters["stuck"] = 1.0
        out.append("The door would not slide open.")
    return out


def _r_share_treatment(world: World) -> list[str]:
    out = []
    if world.facts.get("treatment_shared") and ("share",) not in world.fired:
        world.fired.add(("share",))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["hope"] = e.memes.get("hope", 0.0) + 1.0
        out.append("The crew felt better once they shared the treatment.")
    return out


def _r_fix_door(world: World) -> list[str]:
    out = []
    door = world.entities.get("door")
    if not door:
        return out
    if world.facts.get("fix_used") and ("fix_door",) not in world.fired:
        world.fired.add(("fix_door",))
        door.meters["stuck"] = 0.0
        world.facts["door_open"] = True
        out.append("The door slid open at last.")
    return out


CAUSAL_RULES = [
    Rule("strife", _r_strife),
    Rule("door_stuck", _r_door_stuck),
    Rule("share_treatment", _r_share_treatment),
    Rule("fix_door", _r_fix_door),
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


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def crew_name_list(crew: list[Entity]) -> str:
    names = [c.id for c in crew]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def intro(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(f"{hero.id} and {friend.id} were small crewmates aboard the {setting.place}.")
    world.say(f"They loved floating past bright panels and silver windows, where every day could become an adventure.")


def set_problem(world: World, hero: Entity, friend: Entity, problem: Problem, tool: Tool) -> None:
    world.facts["argument"] = True
    world.facts["jammed"] = True
    world.say(
        f"One day, a {problem.noun} near the hatch caused {hero.id} and {friend.id} to feel a little strife."
    )
    world.say(
        f"The {problem.noun} had made the door {problem.mess}, and nobody could go through."
    )
    world.say(
        f"Both crewmates wanted to help, but they had to solve the problem without making it worse."
    )


def propose_share(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    world.say(
        f"{hero.id} found the {tool.label} and said, \"Let's share it.\""
    )
    world.say(
        f"{friend.id} nodded, because sharing made the treatment feel like a team plan instead of a lonely chore."
    )
    world.facts["treatment_shared"] = True


def use_treatment(world: World, hero: Entity, friend: Entity, tool: Tool, problem: Problem) -> None:
    world.facts["fix_used"] = True
    world.say(
        f"They used the {tool.label} together, one careful step at a time."
    )
    world.say(
        f"The treatment helped loosen the jam and gave them a calm way to fix the {problem.noun}."
    )
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, friend: Entity, problem: Problem, tool: Tool) -> None:
    world.para()
    world.say(
        f"After that, the door opened easily, and {hero.id} and {friend.id} floated through side by side."
    )
    world.say(
        f"Their shared {tool.label} had turned strife into problem solving, and the ship felt peaceful again."
    )
    world.say(
        f"Inside the {world.setting.place}, the little crew smiled at the open doorway and the quiet space beyond."
    )


# ---------------------------------------------------------------------------
# Story registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "spaceship": Setting(place="spaceship"),
    "orbital station": Setting(place="orbital station"),
    "moon base": Setting(place="moon base"),
}

PROBLEMS = {
    "door": Problem(
        id="door",
        verb="stuck",
        noun="door",
        mess="stuck",
        zone="hatch",
        fix_kind="treatment",
    ),
}

TOOLS = {
    "treatment": Tool(
        id="treatment",
        label="treatment kit",
        phrase="a small treatment kit with gentle tools",
        helps="loosen the jam",
    ),
    "shared treatment": Tool(
        id="shared treatment",
        label="shared treatment kit",
        phrase="a shared treatment kit",
        helps="help the crew work together",
    ),
}

NAMES = ["Ari", "Mina", "Jett", "Nova", "Kai", "Luna", "Rin", "Sol"]
TRAITS = ["brave", "curious", "careful", "cheerful", "steady", "bright"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World build
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="pilot"))
    friend = world.add(Entity(id=params.friend, kind="character", type="pilot"))
    door = world.add(Entity(id="door", kind="thing", type="door", label="hatch door"))
    kit = world.add(Entity(id="treatment", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["door"] = door
    world.facts["tool"] = kit
    world.facts["problem"] = problem
    world.facts["trait"] = params.trait

    intro(world, hero, friend, setting)
    world.para()
    set_problem(world, hero, friend, problem, tool)
    world.para()
    propose_share(world, hero, friend, tool)
    use_treatment(world, hero, friend, tool, problem)
    ending(world, hero, friend, problem, tool)
    return world


# ---------------------------------------------------------------------------
# Quality gate / ASP twin
# ---------------------------------------------------------------------------

def is_reasonable(params: StoryParams) -> bool:
    return params.problem in PROBLEMS and params.tool in TOOLS and params.setting in SETTINGS


ASP_RULES = r"""
setting(spaceship).
setting(orbital_station).
setting(moon_base).

problem(door).
tool(treatment).

reasonable(S,P,T) :- setting(S), problem(P), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid.replace(" ", "_")))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid.replace(" ", "_")))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tool = world.facts["tool"]
    return [
        f"Write a short space adventure story about {hero.id} and {friend.id} solving a problem together.",
        f"Tell a gentle story where a shared {tool.label} helps fix a stuck door on a ship.",
        f"Write a child-friendly story with strife, a door, and treatment, ending in teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question="What problem caused the strife in the ship?",
            answer="A door near the hatch was stuck, so the crew could not move through it.",
        ),
        QAItem(
            question=f"Who shared the {tool.label}?",
            answer=f"{hero.id} and {friend.id} shared the {tool.label} together.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The door opened, and the crew turned their problem into teamwork.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a treatment kit for?",
            answer="A treatment kit is used to help fix a problem carefully and safely.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means more than one person uses or enjoys something together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking and working to find a way to make a problem better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or "door"
    tool = args.tool or "treatment"
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if tool not in TOOLS:
        raise StoryError("Unknown tool.")
    name = args.name or rng.choice(NAMES)
    friend_choices = [n for n in NAMES if n != name]
    friend = args.friend or rng.choice(friend_choices)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        name=name,
        friend=friend,
        trait=trait,
    )
    if not is_reasonable(params):
        raise StoryError("The chosen story does not form a reasonable space-adventure problem.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld: strife, door, treatment, sharing, and problem solving.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--tool", choices=list(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show reasonable/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "reasonable"))
    py_set = {(s, p, t) for s in SETTINGS for p in PROBLEMS for t in TOOLS}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        program = asp_program("#show reasonable/3.")
        model = asp.one_model(program)
        combos = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(combos)} reasonable combos:")
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="spaceship", problem="door", tool="treatment", name="Ari", friend="Nova", trait="curious"),
            StoryParams(setting="orbital station", problem="door", tool="treatment", name="Mina", friend="Kai", trait="steady"),
            StoryParams(setting="moon base", problem="door", tool="treatment", name="Jett", friend="Luna", trait="bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
