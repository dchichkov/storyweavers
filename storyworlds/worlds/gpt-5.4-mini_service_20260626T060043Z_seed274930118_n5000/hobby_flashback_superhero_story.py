#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hobby_flashback_superhero_story.py
==============================================================================================================

A small, standalone story world in a superhero style, built around a hobby
that becomes useful through a flashback. The world is intentionally narrow:
each story is a short, child-facing rescue tale with a clear turn, a remembered
skill, and a happy ending image proving what changed.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    roof: bool = False
    windy: bool = False


@dataclass
class Hobby:
    id: str
    name: str
    verb: str
    gerund: str
    skill: str
    flashback_line: str
    aid: str
    aid_label: str
    aid_effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    danger: str
    risk: str
    zone: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    covers: set[str]
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    hobby: str
    problem: str
    hero_name: str
    hero_type: str
    mentor_name: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting(place="the rooftop", roof=True, windy=True),
    "plaza": Setting(place="the city plaza", roof=False, windy=True),
    "harbor": Setting(place="the harbor wall", roof=False, windy=True),
}

HOBBIES = {
    "gliders": Hobby(
        id="gliders",
        name="paper gliders",
        verb="fold paper gliders",
        gerund="folding paper gliders",
        skill="watch the wind and angle the nose just right",
        flashback_line="Back then, the old paper gliders had spun and wobbled until the folds were neat and careful.",
        aid="glider",
        aid_label="paper glider",
        aid_effect="could ride the wind and turn the gust away",
        tags={"wind", "paper"},
    ),
    "knots": Hobby(
        id="knots",
        name="knot tying",
        verb="tie fast knots",
        gerund="tying fast knots",
        skill="make a loop that never slipped",
        flashback_line="Back then, the little practice ropes had slipped through small fingers again and again, until the knots held tight.",
        aid="rope",
        aid_label="practice rope",
        aid_effect="could hold a banner steady",
        tags={"rope", "steady"},
    ),
    "signals": Hobby(
        id="signals",
        name="flashlight signaling",
        verb="blink secret signals",
        gerund="blinking secret signals",
        skill="flash a message in a tiny pattern",
        flashback_line="Back then, the hallway walls had blinked back at a tiny flashlight, and every dot-and-dash had finally made sense.",
        aid="light",
        aid_label="signal light",
        aid_effect="could call help from far away",
        tags={"light", "message"},
    ),
}

PROBLEMS = {
    "kite": Problem(
        id="kite",
        verb="chase the runaway kite",
        danger="the kite could vanish over the river",
        risk="the child might lose the kite forever",
        zone="sky",
        source="the wind",
        tags={"wind", "paper"},
    ),
    "banner": Problem(
        id="banner",
        verb="catch the parade banner",
        danger="the banner could rip and fall into the crowd",
        risk="the city would lose its bright sign",
        zone="air",
        source="a sudden gust",
        tags={"rope", "steady"},
    ),
    "signal": Problem(
        id="signal",
        verb="send a rescue signal",
        danger="the team on the other roof could not see the hero",
        risk="the rescue would stay stuck",
        zone="far roof",
        source="the dark",
        tags={"light", "message"},
    ),
}

TOOLS = {
    "glider": Tool(id="glider", label="a paper glider", use="swerve into the gust", covers={"sky", "air"}, helps={"wind", "paper"}),
    "rope": Tool(id="rope", label="a long rope", use="hold the banner steady", covers={"air"}, helps={"rope", "steady"}),
    "light": Tool(id="light", label="a bright signal light", use="shine across the roofs", covers={"far roof"}, helps={"light", "message"}),
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Toby", "Iris", "Jasper"]
MENTOR_NAMES = ["Aunt June", "Uncle Ray", "Grandma Sol", "Coach Ben"]
TRAITS = ["brave", "curious", "cheerful", "determined", "quick", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for hobby_id, hobby in HOBBIES.items():
            for problem_id, problem in PROBLEMS.items():
                if hobby.tags & problem.tags:
                    combos.append((setting_id, hobby_id, problem_id))
    return combos


def explain_rejection(hobby: Hobby, problem: Problem) -> str:
    return (
        f"(No story: {hobby.name} does not help with {problem.verb}. "
        f"The flashback skill and the rescue problem need to match.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero story world built from a hobby and a flashback."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hobby", choices=HOBBIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--mentor")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.hobby and args.problem:
        if not (HOBBIES[args.hobby].tags & PROBLEMS[args.problem].tags):
            raise StoryError(explain_rejection(HOBBIES[args.hobby], PROBLEMS[args.problem]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hobby is None or c[1] == args.hobby)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, hobby, problem = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    mentor = args.mentor or rng.choice(MENTOR_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, hobby=hobby, problem=problem, hero_name=name, hero_type=gender, mentor_name=mentor, seed=args.seed)


def intro(world: World, hero: Entity, mentor: Entity, hobby: Hobby) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'brave')} {hero.type} with a cape that fluttered like a flag."
    )
    world.say(
        f"{hero.id} loved {hobby.name}, and {mentor.id} always said the hobby was not just play. It was practice."
    )


def flashback(world: World, mentor: Entity, hobby: Hobby) -> None:
    world.say(
        f"One afternoon, {mentor.id} had shown {hobby.verb} on the table."
    )
    world.say(hobby.flashback_line)


def crisis(world: World, hero: Entity, problem: Problem, setting: Setting) -> None:
    world.say(
        f"Now, at {setting.place}, a sudden gust brought trouble."
    )
    world.say(
        f"{hero.id} had to {problem.verb}, because {problem.danger}."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1


def recall(world: World, hero: Entity, hobby: Hobby) -> None:
    hero.memes["flashback"] = hero.memes.get("flashback", 0.0) + 1
    world.say(
        f"Then {hero.id} remembered the hobby lesson: {hobby.skill}."
    )


def use_hobby(world: World, hero: Entity, hobby: Hobby, problem: Problem) -> Tool:
    tool = None
    for candidate in TOOLS.values():
        if hobby.tags & candidate.helps and problem.tags & candidate.helps:
            tool = candidate
            break
    if tool is None:
        raise StoryError("No tool in the catalog can connect this hobby to this problem.")
    if problem.id == "kite":
        hero.meters["wind_control"] = hero.meters.get("wind_control", 0.0) + 1
    elif problem.id == "banner":
        hero.meters["steady"] = hero.meters.get("steady", 0.0) + 1
    else:
        hero.meters["signal"] = hero.meters.get("signal", 0.0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    world.say(
        f"{hero.id} grabbed {tool.label} and used it to {tool.use}."
    )
    return tool


def resolve(world: World, hero: Entity, mentor: Entity, hobby: Hobby, problem: Problem, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"The trick worked, and {problem.risk.lower()}."
    )
    world.say(
        f"{hero.id} smiled under the cape while {mentor.id} cheered, because the hobby had become a hero skill."
    )
    world.say(
        f"At the end, {hero.id} stood in the wind with {tool.label}, and the rescue felt light and easy."
    )


def tell(setting: Setting, hobby: Hobby, problem: Problem, hero_name: str, hero_type: str, mentor_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="adult"))
    intro(world, hero, mentor, hobby)
    world.para()
    flashback(world, mentor, hobby)
    world.para()
    crisis(world, hero, problem, setting)
    recall(world, hero, hobby)
    tool = use_hobby(world, hero, hobby, problem)
    resolve(world, hero, mentor, hobby, problem, tool)
    world.facts = {
        "hero": hero,
        "mentor": mentor,
        "hobby": hobby,
        "problem": problem,
        "tool": tool,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes "{f["hobby"].name}" and a flashback.',
        f"Tell a brave rescue story where {f['hero'].id} remembers how to {f['hobby'].verb} before fixing a problem.",
        f"Write a child-friendly superhero tale set at {f['setting'].place} with a remembered hobby helping the hero win.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    hobby: Hobby = f["hobby"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What hobby did {hero.id} love before the trouble at {setting.place}?",
            answer=f"{hero.id} loved {hobby.name}. That hobby mattered later because it taught {hero.id} how to {hobby.skill}.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the old lesson during the rescue?",
            answer=f"{hero.id} remembered the lesson because {problem.verb} looked hard at first, but the flashback showed the right move.",
        ),
        QAItem(
            question=f"What did {mentor.id} teach {hero.id} in the flashback?",
            answer=f"{mentor.id} taught {hero.id} how to {hobby.verb}. The memory came back when the problem started.",
        ),
        QAItem(
            question=f"How did {tool.label} help in the end?",
            answer=f"{tool.label.capitalize()} helped because it let {hero.id} {tool.use}, which solved the problem and kept the rescue safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} felt proud instead of worried, and the trouble at {setting.place} was fixed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    hobby: Hobby = f["hobby"]
    problem: Problem = f["problem"]
    qa = [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a remembered scene from earlier that helps explain why something matters now.",
        ),
        QAItem(
            question="Why can a hobby be useful?",
            answer="A hobby can be useful because it gives practice with a skill, and practice can help when there is trouble.",
        ),
    ]
    if hobby.id == "gliders":
        qa.append(QAItem(question="What does wind do to a paper glider?", answer="Wind can carry a paper glider or knock it off course, so the folder has to aim carefully."))
    if problem.id == "banner":
        qa.append(QAItem(question="Why do people use ropes for banners?", answer="People use ropes for banners because ropes can hold something steady when the wind pulls hard."))
    if problem.id == "signal":
        qa.append(QAItem(question="Why do heroes use bright lights to signal?", answer="Bright lights can be seen from far away, so they can help people notice a rescue message."))
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="rooftop", hobby="gliders", problem="kite", hero_name="Maya", hero_type="girl", mentor_name="Aunt June", seed=1),
    StoryParams(setting="plaza", hobby="knots", problem="banner", hero_name="Leo", hero_type="boy", mentor_name="Uncle Ray", seed=2),
    StoryParams(setting="harbor", hobby="signals", problem="signal", hero_name="Iris", hero_type="girl", mentor_name="Grandma Sol", seed=3),
]


ASP_RULES = r"""
hobby_match(H, P) :- hobby(H), problem(P), tag(H, T), tag(P, T).
valid(Setting, Hobby, Problem) :- setting(Setting), hobby(Hobby), problem(Problem), hobby_match(Hobby, Problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, hobby in HOBBIES.items():
        lines.append(asp.fact("hobby", hid))
        for t in sorted(hobby.tags):
            lines.append(asp.fact("tag", hid, t))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(problem.tags):
            lines.append(asp.fact("tag", pid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        HOBBIES[params.hobby],
        PROBLEMS[params.problem],
        params.hero_name,
        params.hero_type,
        params.mentor_name,
        params.trait if hasattr(params, "trait") else "brave",
    )
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
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hobby, problem) combos:")
        for row in combos:
            print(" ", row)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
