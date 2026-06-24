#!/usr/bin/env python3
"""
Space-adventure story world: a child astronaut, a concert on a station, and a
wreath that becomes the key to a surprising solution.

The seed tale idea:
- A small crew is preparing for a concert in a space station hall.
- A child has a special wreath for the stage.
- Something goes wrong with the sound or lights.
- The child notices a clue, solves the problem, and the concert ends with a twist.

This world simulates:
- physical meters: sound, glow, drift, charge, dust
- emotional memes: worry, hope, pride, surprise, joy
- a problem-solving turn plus a twist ending
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    used_for: str = ""
    wearing: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Problem:
    id: str
    title: str
    cause: str
    clue: str
    fix: str
    twist: str
    keyword: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, problem: Problem) -> None:
        self.setting = setting
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


SETTINGS = {
    "space_station": Setting(
        place="the bright space station",
        detail="The hall had silver rails, big windows, and a stage that floated just above the floor.",
    ),
    "moon_base": Setting(
        place="the moon base",
        detail="The dome room glowed softly, and moon dust clung to every boot.",
    ),
    "orbital_ship": Setting(
        place="the orbiting ship",
        detail="The ship hummed gently, and the concert room looked out at tiny stars.",
    ),
}

PROBLEMS = {
    "hush": Problem(
        id="hush",
        title="a quiet sound problem",
        cause="A control panel had switched the music into a hush mode.",
        clue="A wreath of tiny bells on the wall was trembling even when the speakers were silent.",
        fix="The child used the wreath to find the loose wire behind the panel and tap it back into place.",
        twist="When the sound came back, the bells on the wreath made the chorus sparkle like stardust.",
        keyword="wreath",
    ),
    "lights": Problem(
        id="lights",
        title="a light problem",
        cause="The stage lights kept dimming because a dust filter was blocking the glow.",
        clue="The wreath’s shiny leaves reflected a thin path of light toward the vent.",
        fix="The child followed the reflection, opened the vent, and cleared the filter.",
        twist="The concert ended with the wreath shining brighter than the stage lamps.",
        keyword="wreath",
    ),
    "echo": Problem(
        id="echo",
        title="an echo problem",
        cause="The concert hall was making the singers sound doubled and strange.",
        clue="The wreath had soft ribbons that fluttered toward the curved wall.",
        fix="The child hung the wreath on the wall to break the echo and calm the sound.",
        twist="The twist was that the wreath was not only decoration; it became the best sound tool in the room.",
        keyword="concert",
    ),
}

GENDER_NAMES = {
    "girl": ["Luna", "Mira", "Nia", "Zoe", "Aria", "Nova"],
    "boy": ["Kai", "Toby", "Finn", "Leo", "Milo", "Ezra"],
}

HELPERS = ["robot", "pilot", "captain", "mechanic"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a concert, a wreath, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, problem=problem, name=name, gender=gender, helper=helper)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("keyword", pid, pr.keyword))
    return "\n".join(lines)


ASP_RULES = r"""
good_story(S,P) :- setting(S), problem(P).
#show good_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def story_ok(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.problem in PROBLEMS


def generate(params: StoryParams) -> StorySample:
    if not story_ok(params):
        raise StoryError("Invalid setting or problem.")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    world = World(setting, problem)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    wreath = world.add(Entity(
        id="wreath",
        type="thing",
        label="wreath",
        phrase="a bright wreath with tiny bells and shiny leaves",
        owner=hero.id,
        used_for="concert",
        meters={"glow": 0.5, "dust": 0.0},
        memes={"hope": 0.4},
    ))
    console = world.add(Entity(
        id="console",
        type="thing",
        label="music console",
        phrase="the music console",
        owner=helper.id,
        meters={"sound": 0.2, "charge": 0.5},
        memes={"worry": 0.6},
    ))

    hero.memes["joy"] = 0.5
    hero.memes["worry"] = 0.2
    helper.memes["worry"] = 0.4

    # Beginning
    world.say(f"{hero.label} lived on {setting.place} and loved the big concert nights.")
    world.say(f"{hero.pronoun().capitalize()} carried {wreath.phrase} for the stage because the wreath made the hall feel brave and bright.")
    world.say(f"{helper.label.capitalize()} checked the room while everyone waited for the music to begin.")

    # Middle problem
    world.para()
    world.say(f"Then {problem.cause}")
    console.meters["sound"] = 0.0
    console.memes["worry"] += 0.7
    hero.memes["worry"] += 0.8
    world.say(f"The singers looked at one another, and {hero.label} noticed that the concert was in trouble.")

    # Problem solving
    world.para()
    world.say(f"{hero.label} did not give up.")
    world.say(f"{hero.pronoun().capitalize()} watched carefully for a clue, and saw that {problem.clue}")
    world.say(f"{hero.label} and {helper.label} worked together: {problem.fix}")
    console.meters["sound"] = 1.0
    console.memes["worry"] = 0.0
    wreath.meters["glow"] += 0.5
    wreath.memes["hope"] += 0.6
    hero.memes["pride"] = 0.8
    hero.memes["joy"] = 1.0

    # Twist ending
    world.para()
    world.say(f"{problem.twist}")
    world.say(f"The band played on, the crowd cheered, and {hero.label} smiled at the wreath as if it had been waiting for this all along.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "wreath": wreath,
        "console": console,
        "problem": problem,
        "setting": setting,
        "params": params,
    }

    prompts = [
        "Write a short space-adventure story about a child, a concert, and a wreath that helps solve a problem.",
        f"Tell a gentle story where {hero.label} notices a trouble at {setting.place} and fixes it with help.",
        f"Write a child-friendly story with the words '{problem.keyword}', 'concert', and 'wreath'.",
    ]

    story_qa = [
        QAItem(
            question=f"What was the problem at {setting.place}?",
            answer=f"It was {problem.title}, and it made the concert hard to hear or see until {hero.label} helped fix it.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the problem?",
            answer=f"{hero.label} looked for a clue, worked with {helper.label}, and used the wreath or nearby station parts to solve it.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer="The concert worked again, the crowd was happy, and the wreath became part of the surprise ending.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a wreath?",
            answer="A wreath is a круг? No. A wreath is a circular decoration often made of leaves, ribbons, flowers, or shiny pieces.",
        ),
        QAItem(
            question="What is a concert?",
            answer="A concert is a performance where musicians play music for an audience.",
        ),
        QAItem(
            question="What is a problem solver?",
            answer="A problem solver is someone who notices trouble, thinks carefully, and tries different ways until something works.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        parts.append(f"{ent.id}: {', '.join(bits)}")
    return "\n".join(parts)


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
    StoryParams(setting="space_station", problem="hush", name="Luna", gender="girl", helper="robot"),
    StoryParams(setting="moon_base", problem="lights", name="Kai", gender="boy", helper="mechanic"),
    StoryParams(setting="orbital_ship", problem="echo", name="Mira", gender="girl", helper="pilot"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = set(asp.atoms(model, "good_story"))
    expected = {(s, p) for s in SETTINGS for p in PROBLEMS}
    if atoms == expected:
        print(f"OK: ASP parity matches Python reasoning ({len(atoms)} combinations).")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("only in ASP:", sorted(atoms - expected))
    print("only in Python:", sorted(expected - atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(combos)} combinations:")
        for s, p in combos:
            print(f"  {s} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name} / {p.setting} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
