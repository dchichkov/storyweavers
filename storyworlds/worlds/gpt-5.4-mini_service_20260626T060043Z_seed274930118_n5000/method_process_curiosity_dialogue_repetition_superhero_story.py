#!/usr/bin/env python3
"""
A small superhero storyworld built from a curious rescue premise.

Seed tale shape:
- A young hero notices a problem in the city.
- Curiosity leads to a methodical process of checking clues, asking questions, and trying again.
- Dialogue with a mentor or teammate clarifies the plan.
- Repetition becomes a strength: the hero practices a useful move until it works.
- The ending proves what changed in the world.

This world is intentionally small and constraint-checked: it generates only
stories where curiosity, dialogue, and repetition are all meaningful parts of
the turn from trouble to success.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Problem:
    id: str
    label: str
    threat: str
    clue: str
    fix_action: str
    fix_repeat: str
    requires: str
    restores: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    works_on: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    city: str
    hero: str
    hero_type: str
    mentor: str
    mentor_type: str
    problem: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: Place) -> None:
        self.city = city
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


HEROES = [
    ("Nova", "girl"),
    ("Bolt", "boy"),
    ("Comet", "girl"),
    ("Flash", "boy"),
]
MENTORS = [
    ("Captain Vale", "woman"),
    ("Guardian Gray", "man"),
    ("Dr. Beacon", "woman"),
    ("Major Bright", "man"),
]
CITIES = {
    "Skyport": Place(id="skyport", label="Skyport City"),
    "Rivergate": Place(id="rivergate", label="Rivergate"),
    "Sunside": Place(id="sunside", label="Sunside"),
}
TOOLS = {
    "scanner": Tool(
        id="scanner",
        label="signal scanner",
        phrase="a small signal scanner",
        method="scan the air for clues",
        works_on="signal",
        tags={"curiosity", "method"},
    ),
    "gloves": Tool(
        id="gloves",
        label="grip gloves",
        phrase="a pair of grip gloves",
        method="practice the wall climb again and again",
        works_on="climb",
        tags={"repetition", "method"},
    ),
    "map": Tool(
        id="map",
        label="city map",
        phrase="a folded city map",
        method="trace the path step by step",
        works_on="route",
        tags={"curiosity", "method"},
    ),
}
PROBLEMS = {
    "stuck_tram": Problem(
        id="stuck_tram",
        label="stuck tram",
        threat="the tram cannot move and people are waiting",
        clue="a broken switch kept blinking near the rail",
        fix_action="flip the switch the right way",
        fix_repeat="try the switch again with a better grip",
        requires="signal",
        restores="the tram line",
        tags={"curiosity", "dialogue"},
    ),
    "roof_leak": Problem(
        id="roof_leak",
        label="roof leak",
        threat="water is dripping into a school hall",
        clue="the leak came from a loose panel overhead",
        fix_action="seal the panel with a steady press",
        fix_repeat="press the panel again and hold it longer",
        requires="climb",
        restores="the school hall",
        tags={"repetition", "dialogue"},
    ),
    "lost_parade": Problem(
        id="lost_parade",
        label="lost parade float",
        threat="the parade float is turned the wrong way",
        clue="the road signs pointed to the wrong street",
        fix_action="turn the float toward the bright avenue",
        fix_repeat="check the map again and follow the next turn",
        requires="route",
        restores="the parade route",
        tags={"curiosity", "repetition"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for city in CITIES:
        for hero, hero_type in HEROES:
            for mentor, mentor_type in MENTORS:
                for prob in PROBLEMS:
                    for tool in TOOLS:
                        p = PROBLEMS[prob]
                        t = TOOLS[tool]
                        if p.requires == t.works_on and p.tags & t.tags:
                            out.append((city, hero, mentor, prob, tool))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about curiosity, dialogue, and repetition.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-type", choices=["woman", "man"])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = valid_combos()
    filt = []
    for c in combos:
        city, hero, mentor, prob, tool = c
        if args.city and args.city != city:
            continue
        if args.problem and args.problem != prob:
            continue
        if args.tool and args.tool != tool:
            continue
        filt.append(c)
    if not filt:
        raise StoryError("(No valid combination matches the given options.)")
    city, hero, mentor, prob, tool = rng.choice(sorted(filt))
    hero_type = args.hero_type or dict(HEROES)[hero]
    mentor_type = args.mentor_type or dict(MENTORS)[mentor]
    if args.hero and args.hero != hero:
        hero = args.hero
    if args.mentor and args.mentor != mentor:
        mentor = args.mentor
    return StoryParams(city=city, hero=hero, hero_type=hero_type, mentor=mentor, mentor_type=mentor_type, problem=prob, tool=tool)


def _char(name: str, typ: str) -> Entity:
    return Entity(id=name, kind="character", type=typ, label=name)


def tell(params: StoryParams) -> World:
    city = CITIES[params.city]
    world = World(city)
    hero = world.add(_char(params.hero, params.hero_type))
    mentor = world.add(_char(params.mentor, params.mentor_type))
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world.facts.update(hero=hero, mentor=mentor, problem=problem, tool=tool, city=city)

    hero.memes["curiosity"] = 1
    hero.memes["hope"] = 1

    world.say(f"In {city.label}, {hero.id} was the sort of superhero who always noticed tiny details.")
    world.say(f"{hero.pronoun().capitalize()} loved {tool.method} because curiosity made every clue feel important.")
    world.say(f"One day, {hero.id} and {mentor.id} heard about {problem.threat}.")
    world.para()
    world.say(f"{hero.id} looked at {problem.clue} and asked, \"What is the real problem here?\"")
    world.say(f"{mentor.id} answered, \"Use your method and keep your process calm. First look, then think, then act.\"")
    world.say(f"So {hero.id} used {tool.phrase} to {tool.method}.")
    world.say(f"{hero.id} tried once, then again, following the same method with patience.")
    world.say(f"At last, {problem.fix_action}.")
    world.para()
    world.say(f"The rescue worked because {hero.id} did not rush. Curiosity found the clue, dialogue shaped the plan, and repetition made the move strong.")
    world.say(f"By the end, {problem.restores} was safe again, and {city.label} shone a little brighter.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    city: Place = f["city"]
    return [
        f"Write a short superhero story for a young child set in {city.label} where {hero.id} uses {tool.label} and learns through curiosity.",
        f"Tell a gentle action story where {hero.id} and {mentor.id} talk about {problem.label}, then solve it by repeating the right method.",
        f"Write a simple superhero rescue story that includes dialogue, a process, and a happy ending in {city.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    city: Place = f["city"]
    return [
        QAItem(
            question=f"Who was the superhero in {city.label} who cared about the problem?",
            answer=f"It was {hero.id}, who paid close attention because {hero.pronoun()} was curious and wanted to help.",
        ),
        QAItem(
            question=f"What did {mentor.id} tell {hero.id} to do before acting?",
            answer=f"{mentor.id} told {hero.id} to follow a calm method and process: look, think, talk, and then try again.",
        ),
        QAItem(
            question=f"Why did {hero.id} use {tool.label} on the rescue?",
            answer=f"{hero.id} used {tool.label} because it matched the problem and helped {hero.pronoun('object')} find the right clue.",
        ),
        QAItem(
            question=f"How did the story show repetition?",
            answer=f"{hero.id} tried the rescue move once, then again, and the repeated practice made the fix work.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The trouble was solved, {problem.restores} was safe again, and {city.label} ended in a brighter, safer state.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by looking, wondering, and asking questions.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is a conversation where two or more characters talk to each other.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, often to practice or to make it better.",
        ),
        QAItem(
            question="What is a method?",
            answer="A method is a way of doing something in an organized, step-by-step manner.",
        ),
        QAItem(
            question="What is a process?",
            answer="A process is a series of steps that helps you get from a problem to a result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_requires(P,R) :- problem(P), requires(P,R).
tool_works(T,R) :- tool(T), works_on(T,R).
compatible(P,T) :- problem_requires(P,R), tool_works(T,R), problem_tag(P,X), tool_tag(T,X).
valid_story(C,H,M,P,T) :- city(C), hero(H), mentor(M), problem(P), tool(T), compatible(P,T).
#show valid_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CITIES:
        lines.append(asp.fact("city", cid))
    for h, ht in HEROES:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("hero_type", h, ht))
    for m, mt in MENTORS:
        lines.append(asp.fact("mentor", m))
        lines.append(asp.fact("mentor_type", m, mt))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("requires", pid, p.requires))
        for tag in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("works_on", tid, t.works_on))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set((c, h, m, p, t) for c, h, m, p, t in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for city, hero, mentor, prob, tool in sorted(valid_combos()):
            params = StoryParams(
                city=city,
                hero=hero,
                hero_type=dict(HEROES)[hero],
                mentor=mentor,
                mentor_type=dict(MENTORS)[mentor],
                problem=prob,
                tool=tool,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.hero} in {p.city} with {p.problem} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
