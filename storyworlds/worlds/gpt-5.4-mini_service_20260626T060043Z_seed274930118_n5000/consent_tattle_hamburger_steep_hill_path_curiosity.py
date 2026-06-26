#!/usr/bin/env python3
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "hero"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the steep hill path"


@dataclass
class Action:
    id: str
    verb: str
    rush: str
    effect: str
    risk: str
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    source: str = "hamburger"
    edible: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    action: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        cur = []
        for line in self.lines:
            if line == "":
                if cur:
                    out.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            out.append(" ".join(cur))
        return "\n\n".join(out)


ACTIONS = {
    "climb": Action(
        id="climb",
        verb="climb farther up",
        rush="dart up the steep path",
        effect="climbed higher and higher",
        risk="a tumble on the narrow stones",
        keyword="curiosity",
    ),
    "investigate": Action(
        id="investigate",
        verb="investigate the hill",
        rush="run toward the bend",
        effect="investigated the path",
        risk="slipping on the loose gravel",
        keyword="Curiosity",
    ),
    "help": Action(
        id="help",
        verb="help the neighbors carry things",
        rush="hurry uphill",
        effect="helped with the load",
        risk="dropping the food on the slope",
        keyword="consent",
    ),
}

PRIZES = {
    "hamburger": Prize(
        label="hamburger",
        phrase="a warm hamburger wrapped in paper",
        type="hamburger",
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Max", "Theo", "Ben", "Finn"]
TRAITS = ["curious", "brave", "bright", "quick", "bold"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style story world on a steep hill path.")
    ap.add_argument("--place", choices=["steep hill path"], default="steep hill path")
    ap.add_argument("--action", choices=sorted(ACTIONS), default=None)
    ap.add_argument("--prize", choices=sorted(PRIZES), default="hamburger")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    action = args.action or rng.choice(list(ACTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        place=args.place,
        action=action,
        prize=args.prize,
    )


def make_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"curiosity": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label="hamburger", phrase=PRIZES[params.prize].phrase, owner=params.name))
    world.facts.update(hero=hero, parent=parent, prize=prize, action=ACTIONS[params.action], params=params)
    return world


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    action: Action = world.facts["action"]  # type: ignore[assignment]

    world.say(f"{hero.id} was a little superhero with a bright cape and a head full of Curiosity.")
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to the steep hill path.")
    world.say(f"They had {prize.phrase}, and {hero.id} loved the smell of the hamburger so much that {hero.pronoun()} could hardly wait.")

    world.para()
    world.say(f"{hero.id} wanted to {action.verb}, because {action.keyword} pulled {hero.pronoun('object')} forward like a tiny superpower.")
    world.say(f"But the hill was steep, and the stones made {action.risk} feel very real.")
    world.say(f"{parent.pronoun().capitalize()} asked for consent first: \"Do you want to go on, or should we stop and share the hamburger here?\"")
    world.say(f"{hero.id} nodded, but then saw a child nearby and decided to tattle about the shiny wrapper blowing toward the edge.")

    world.para()
    world.say(f"{hero.id} used {action.keyword} the right way by asking before grabbing the food and by warning the grown-up instead of making trouble.")
    world.say(f"{parent.pronoun().capitalize()} smiled, and the two of them made a safe plan.")
    world.say(f"After that, {hero.id} helped carry the hamburger carefully, and the little hero felt a new kind of Transformation inside {hero.pronoun('object')}: curiosity had turned into thoughtful courage.")
    world.say(f"At the top of the steep hill path, the hamburger was still warm, and {hero.id} stood taller than the slope.")


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child about a {p.gender} named {p.name} on a steep hill path, using the word "{world.facts["action"].keyword}".',
        f"Tell a gentle story where {p.name} learns about consent, chooses whether to keep going uphill, and notices a hamburger.",
        f"Write a story with Curiosity and Transformation on a steep hill path where a child learns to stop tattling and act bravely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    action: Action = world.facts["action"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {p.name} want to go farther up the steep hill path?",
            answer=f"{p.name} wanted to go farther because Curiosity was buzzing in {p.name}'s chest, and {action.keyword} made the hill feel like an adventure.",
        ),
        QAItem(
            question=f"What did the {p.parent} ask before {p.name} kept going?",
            answer=f"The {p.parent} asked for consent first and wanted to know if {p.name} really wanted to keep going or should stop and share the hamburger there.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{p.name}'s curiosity turned into thoughtful courage, so the child could help carefully on the steep hill path instead of acting carelessly.",
        ),
        QAItem(
            question=f"Why did {p.name} tattle about the wrapper?",
            answer=f"{p.name} tattle'd because the wrapper was blowing toward the edge of the path and the child wanted the grown-up to notice the danger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is consent?",
            answer="Consent means asking and clearly saying yes before you do something that affects another person.",
        ),
        QAItem(
            question="What does it mean to tattle?",
            answer="To tattle is to tell an adult about someone else's small problem or rule-breaking, sometimes when it would be better to solve it another way.",
        ),
        QAItem(
            question="What is a hamburger?",
            answer="A hamburger is a sandwich with a cooked patty inside a bun, often wrapped up to keep it warm.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to learn, explore, and ask questions.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a change from one state to another, like becoming braver or kinder over time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- name(X).
action(A) :- act(A).
prize(P) :- item(P).

needs_consent(X) :- hero(X).
safe_choice(X) :- consent(X), not danger(X).
transformed(X) :- hero(X), learned(X).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("name", name))
    for aid in ACTIONS:
        lines.append(asp.fact("act", aid))
    for pid in PRIZES:
        lines.append(asp.fact("item", pid))
    lines.append(asp.fact("theme", "consent"))
    lines.append(asp.fact("theme", "tattle"))
    lines.append(asp.fact("theme", "hamburger"))
    lines.append(asp.fact("setting", "steep_hill_path"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.memes, e.meters)
    if qa:
        print()
        print(format_qa(sample))


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show hero/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available in the inline twin, but this world uses the Python gate for generation.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", place="steep hill path", action="investigate", prize="hamburger"),
            StoryParams(name="Leo", gender="boy", parent="father", place="steep hill path", action="climb", prize="hamburger"),
            StoryParams(name="Ava", gender="girl", parent="mother", place="steep hill path", action="help", prize="hamburger"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_story_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
