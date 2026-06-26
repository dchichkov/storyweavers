#!/usr/bin/env python3
"""
A small comedy storyworld about a troublesome thingamajig, a slew of spinach,
and repeated problem-solving attempts that eventually work.

Premise:
- A child wants to make a simple spinach snack.
- A thingamajig in the kitchen keeps making the task harder in funny ways.
- The hero tries several fixes, learns from each one, and finally solves it.

The simulated world tracks:
- physical meters: spinach amount, mess, tool readiness, bowl fill, toastiness
- emotional memes: frustration, confidence, joy, embarrassment

The story should feel like:
- beginning: setup and a funny goal
- middle: a repeated sequence of failures and adjustments
- ending: a concrete resolution showing what changed
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["spinach", "mess", "readiness", "fill", "toast", "smell"]:
            self.meters.setdefault(k, 0.0)
        for k in ["frustration", "confidence", "joy", "embarrassment"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    target: str
    repeated_action: str
    fix_hint: str
    comic_line: str
    solution: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str] = field(default_factory=set)
    makes_worse: set[str] = field(default_factory=set)
    comic_reaction: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", afford={"spinach", "thingamajig"}),
    "porch": Setting(place="the porch", afford={"spinach", "thingamajig"}),
    "garden": Setting(place="the garden table", afford={"spinach"}),
}

PROBLEMS = {
    "spinach_sticks": Problem(
        id="spinach_sticks",
        target="spinach",
        repeated_action="stir the spinach again",
        fix_hint="it needs less squeezing and more gentle stirring",
        comic_line="the spinach stuck to the spoon like it had rent to pay",
        solution="fold it slowly with a fork",
        keyword="spinach",
    ),
    "thingamajig_sputters": Problem(
        id="thingamajig_sputters",
        target="thingamajig",
        repeated_action="tap the thingamajig again",
        fix_hint="it wants a calm reset, not a harder tap",
        comic_line="the thingamajig coughed, blinked, and made a tiny grumpy beep",
        solution="turn it off and back on, then use it gently",
        keyword="thingamajig",
    ),
}

TOOLS = {
    "fork": Tool(
        id="fork",
        label="a fork",
        use="folding",
        helps={"spinach"},
        comic_reaction="the fork looked polite, which was promising",
    ),
    "spoon": Tool(
        id="spoon",
        label="a spoon",
        use="stirring",
        helps=set(),
        makes_worse={"spinach"},
        comic_reaction="the spoon tried its best but mostly chased the leaves around",
    ),
    "button": Tool(
        id="button",
        label="the reset button",
        use="resetting",
        helps={"thingamajig"},
        comic_reaction="the reset button seemed tiny for such a dramatic job",
    ),
}

NAMES = ["Maya", "Leo", "Nina", "Owen", "Lina", "Theo"]
TRAITS = ["curious", "cheerful", "determined", "silly", "patient"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("target", pid, p.target))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", tid, a))
        for a in sorted(t.makes_worse):
            lines.append(asp.fact("worsens", tid, a))
    return "\n".join(lines)


ASP_RULES = r"""
good_fix(T, P) :- tool(T), problem(P), helps(T, X), target(P, X).
bad_fix(T, P) :- tool(T), problem(P), worsens(T, X), target(P, X).
valid_attempt(T, P) :- good_fix(T, P), not bad_fix(T, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_attempt/2."))
    clingo_set = set(asp.atoms(model, "valid_attempt"))
    py_set = set()
    for tid, t in TOOLS.items():
        for pid, p in PROBLEMS.items():
            if p.target in t.helps and p.target not in t.makes_worse:
                py_set.add((tid, pid))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} valid attempts).")
        return 0
    print("MISMATCH")
    print("only clingo:", sorted(clingo_set - py_set))
    print("only python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about spinach and a thingamajig.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if place == "garden" and problem == "thingamajig_sputters":
        raise StoryError("(No story: the garden has no lively thingamajig scene here.)")
    return StoryParams(place=place, problem=problem, name=name, trait=trait)


def _attempt_fix(world: World, hero: Entity, problem: Problem, tool: Tool, attempt_num: int) -> str:
    key = (problem.id, tool.id, attempt_num)
    if key in world.fired:
        return ""
    world.fired.add(key)
    if tool.id == "spoon" and problem.id == "spinach_sticks":
        hero.memes["frustration"] += 1
        hero.memes["embarrassment"] += 0.5
        return f"{hero.pronoun().capitalize()} tried again with {tool.label}, but it only chased the {problem.keyword} around."
    if tool.id == "button" and problem.id == "thingamajig_sputters":
        hero.memes["confidence"] += 1
        return f"{hero.pronoun().capitalize()} pressed {tool.label}, and the thingamajig finally took a deep breath."
    if tool.id == "fork" and problem.id == "spinach_sticks":
        hero.memes["confidence"] += 1
        world.get("bowl").meters["spinach"] -= 1
        world.get("bowl").meters["fill"] += 1
        return f"Then {hero.pronoun().subject if False else hero.pronoun('subject')} used {tool.label} to fold the leaves gently, and the spinach stopped sticking."
    return f"{tool.comic_reaction.capitalize()}."


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    bowl = world.add(Entity(id="bowl", type="bowl", label="the bowl"))
    thing = world.add(Entity(id="thingamajig", type="thing", label="the thingamajig"))
    spinach = world.add(Entity(id="spinach", type="food", label="a slew of spinach", plural=True))
    fork = world.add(Entity(id="fork", type="tool", label="a fork"))
    spoon = world.add(Entity(id="spoon", type="tool", label="a spoon"))
    button = world.add(Entity(id="button", type="button", label="the reset button"))

    problem = PROBLEMS[params.problem]
    hero.memes["joy"] += 1
    spinach.meters["spinach"] = 8.0
    bowl.meters["spinach"] = 8.0
    thing.meters["readiness"] = 0.3
    world.say(f"{hero.id} was a {params.trait} child in {world.setting.place} who wanted a quick snack.")
    world.say(f"There was a slew of spinach on the counter, and the thingamajig sat nearby like it had a secret.")

    world.para()
    world.say(f"{hero.id} tried to make the snack, but {problem.comic_line}.")
    world.say(f"So {hero.id} started problem-solving, because comedy sometimes begins with a kitchen puzzle.")

    world.para()
    if problem.id == "spinach_sticks":
        world.say(f"First {hero.id} used {spoon.label}.")
        world.say(_attempt_fix(world, hero, problem, spoon, 1))
        world.say(f"{hero.id} tried again.")
        world.say(_attempt_fix(world, hero, problem, spoon, 2))
        world.say(f"At last, {hero.id} grabbed {fork.label}.")
        world.say(_attempt_fix(world, hero, problem, fork, 3))
        bowl.meters["spinach"] = 0.0
        bowl.meters["fill"] = 1.0
        hero.memes["joy"] += 2
    else:
        world.say(f"{hero.id} tapped the thingamajig once.")
        world.say("It sputtered anyway.")
        world.say(f"{hero.id} tapped it again, more carefully this time.")
        world.say("It sputtered even more, which was rude for a machine.")
        world.say(f"Then {hero.id} found {button.label}.")
        world.say(_attempt_fix(world, hero, problem, button, 3))
        thing.meters["readiness"] = 1.0
        hero.memes["confidence"] += 2
        world.say(f"After that, the thingamajig worked, and {hero.id} used it gently.")

    world.para()
    world.say(f"In the end, the snack was ready, the spinach was useful instead of sticky, and the thingamajig was calm.")
    world.say(f"{hero.id} smiled at the neat result and laughed at the two silly tries that came before it.")

    world.facts.update(hero=hero, problem=problem, bowl=bowl, thing=thing, spinach=spinach, params=params)
    story_qa = [
        QAItem(
            question=f"What did {hero.id} want to make in {world.setting.place}?",
            answer=f"{hero.id} wanted a simple snack with spinach, even though the thingamajig made the job tricky.",
        ),
        QAItem(
            question=f"What did {hero.id} do when the first try failed?",
            answer=f"{hero.id} tried again, then changed the method instead of giving up.",
        ),
        QAItem(
            question=f"What finally solved the problem?",
            answer=f"The problem was solved by using the better tool or reset step for the troublemaker and by folding the spinach gently.",
        ),
    ]
    if problem.id == "spinach_sticks":
        story_qa.append(QAItem(
            question=f"Why was the spoon not a good fix for the spinach?",
            answer="The spoon kept chasing the leaves around, so the spinach stayed sticky until a fork folded it gently.",
        ))
    else:
        story_qa.append(QAItem(
            question=f"Why did the reset button help the thingamajig?",
            answer="The thingamajig needed a calm reset, and the tiny button let it start over without sputtering.",
        ))
    world_qa = [
        QAItem(
            question="What is spinach?",
            answer="Spinach is a leafy green vegetable that people can cook, stir, fold, or eat in a snack.",
        ),
        QAItem(
            question="What is a thingamajig?",
            answer="A thingamajig is a funny word for a gadget or object when someone does not want to name it exactly.",
        ),
        QAItem(
            question="Why do people try different fixes when something goes wrong?",
            answer="People try different fixes because one idea may fail, but a new method can solve the problem better.",
        ),
    ]
    prompts = [
        f"Write a funny story about {hero.id}, a slew of spinach, and a mysterious thingamajig in {world.setting.place}.",
        "Tell a child-friendly comedy where the hero tries, fails, tries again, and eventually solves the kitchen problem.",
        "Write a short story that repeats a problem-solving step twice before the final fix works.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_attempt/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_attempt/2."))
        print(sorted(set(asp.atoms(model, "valid_attempt"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        all_params = [
            StoryParams(place="kitchen", problem="spinach_sticks", name="Maya", trait="curious"),
            StoryParams(place="kitchen", problem="thingamajig_sputters", name="Leo", trait="cheerful"),
            StoryParams(place="porch", problem="spinach_sticks", name="Nina", trait="determined"),
        ]
        for p in all_params:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
