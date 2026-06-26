#!/usr/bin/env python3
"""
Standalone storyworld: opa_magic_teamwork_conflict_superhero_story.py

A small superhero story domain about a magic team, a conflict, and a clever
teamwork resolution.
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
class Hero:
    id: str
    kind: str = "character"
    role: str = "hero"
    label: str = ""
    face: str = ""
    power: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Artifact:
    id: str
    label: str
    kind: str = "artifact"
    magic: str = ""
    team_use: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    conflict: str
    magic_item: str
    seed: Optional[int] = None


@dataclass
class World:
    heroes: dict[str, Hero] = field(default_factory=dict)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = [
    ("Nova", "spark hero", "she", "light bolts"),
    ("Kite", "wind hero", "they", "gust shields"),
    ("Rook", "brick hero", "he", "strong hands"),
    ("Mira", "glow hero", "she", "moon glow"),
]
HELPERS = ["opa", "captain Loop", "Aunt Zephyr", "Uncle Comet"]
CONFLICTS = [
    ("a stuck gate", "The gate was jammed shut and the crowd could not escape"),
    ("a dark cloud", "A dark cloud covered the park and made everyone worry"),
    ("a broken bridge", "The bridge had cracked, so the path was blocked"),
]
MAGIC_ITEMS = [
    ("star charm", "a star charm", "glittering magic", "light the way"),
    ("spell ring", "a spell ring", "circle magic", "join hands and focus"),
    ("moon cape", "a moon cape", "soft magic", "cover and protect"),
    ("spark lantern", "a spark lantern", "bright magic", "guide the team"),
]

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
artifact(A) :- artifact_name(A).
needs_teamwork(C) :- conflict(C).
solved(C) :- needs_teamwork(C), magic_item(A), teamwork(A,C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for n, _, _, _ in HEROES:
        lines.append(asp.fact("hero_name", n))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h))
    for a, _, _, _ in MAGIC_ITEMS:
        lines.append(asp.fact("artifact_name", a))
    for c, _ in CONFLICTS:
        lines.append(asp.fact("conflict_name", c))
    for a, _, _, _ in MAGIC_ITEMS:
        lines.append(asp.fact("magic_item", a))
        lines.append(asp.fact("teamwork", a, "gate"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with magic, teamwork, and conflict.")
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--conflict", choices=[c for c, _ in CONFLICTS])
    ap.add_argument("--magic-item", choices=[m for m, _, _, _ in MAGIC_ITEMS])
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
    name = args.name or rng.choice([n for n, _, _, _ in HEROES])
    helper = args.helper or rng.choice(HELPERS)
    conflict = args.conflict or rng.choice([c for c, _ in CONFLICTS])
    magic_item = args.magic_item or rng.choice([m for m, _, _, _ in MAGIC_ITEMS])
    return StoryParams(name=name, helper=helper, conflict=conflict, magic_item=magic_item)

def generate(params: StoryParams) -> StorySample:
    hero_def = next((h for h in HEROES if h[0] == params.name), HEROES[0])
    conflict_def = next((c for c in CONFLICTS if c[0] == params.conflict), CONFLICTS[0])
    magic_def = next((m for m in MAGIC_ITEMS if m[0] == params.magic_item), MAGIC_ITEMS[0])

    world = World()
    hero = Hero(id=params.name, label=params.name, face=hero_def[1], power=hero_def[3])
    helper = Hero(id=params.helper, role="helper", label=params.helper, face="steady hands", power="teamwork")
    artifact = Artifact(id=magic_def[0], label=magic_def[1], magic=magic_def[2], team_use=magic_def[3])

    world.heroes[hero.id] = hero
    world.heroes[helper.id] = helper
    world.artifacts[artifact.id] = artifact

    world.say(f"On a bright day, {hero.id} was the city’s {hero.face} hero, and {params.helper} stayed close by with a calm smile.")
    world.say(f"{hero.id} carried {artifact.label}, a tool full of {artifact.magic}, because every hero needs a little wonder.")
    world.para()
    world.say(f"Then {conflict_def[1].lower()}. {hero.id} wanted to rush ahead, but the trouble was too big for one hero alone.")
    world.say(f"{params.helper} called out, 'opa, look at me!' and pointed to the plan: {artifact.team_use}.")
    world.say(f"{hero.id} listened, and the two of them used {artifact.label} together.")
    world.para()
    world.say(f"The magic spread like a warm flash, the danger opened a path, and the team fixed the problem without hurting anyone.")
    world.say(f"In the end, {hero.id} and {params.helper} stood side by side, smiling at the safe street and the brave little crowd.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "artifact": artifact,
        "conflict_text": conflict_def[1],
    }

    prompts = [
        "Write a superhero story where a hero and a helper use magic and teamwork to solve a conflict.",
        f"Tell a child-friendly story about {hero.id}, {params.helper}, and {artifact.label}.",
    ]

    story_qa = [
        QAItem(question=f"Who helped {hero.id} in the story?", answer=f"{params.helper} helped {hero.id} with teamwork."),
        QAItem(question=f"What magical item did they use?", answer=f"They used {artifact.label} to solve the problem."),
        QAItem(question="What did the team do when the trouble got big?", answer="They worked together instead of rushing alone."),
    ]

    world_qa = [
        QAItem(question="What is teamwork?", answer="Teamwork means people help each other and do a job together."),
        QAItem(question="What is magic in a superhero story?", answer="Magic is a special power that can do surprising things and help solve problems."),
        QAItem(question="What is a conflict?", answer="A conflict is a problem or disagreement that the characters need to fix."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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

def dump_trace(sample: StorySample) -> str:
    w = sample.world
    lines = ["--- trace ---"]
    if w:
        for h in w.heroes.values():
            lines.append(f"hero {h.id}: power={h.power}")
        for a in w.artifacts.values():
            lines.append(f"artifact {a.id}: magic={a.magic}")
    return "\n".join(lines)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample))
    if qa:
        print()
        print(format_qa(sample))

def valid_combos() -> list[tuple[str, str, str]]:
    return [(h[0], c[0], m[0]) for h in HEROES for c in CONFLICTS for m in MAGIC_ITEMS]

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show hero_name/1."))
    return 0 if model is not None else 1

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero_name/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} possible superhero combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for h, c, m in valid_combos():
            samples.append(generate(StoryParams(name=h, helper=HELPERS[0], conflict=c, magic_item=m)))
    else:
        rng = random.Random(base_seed)
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
