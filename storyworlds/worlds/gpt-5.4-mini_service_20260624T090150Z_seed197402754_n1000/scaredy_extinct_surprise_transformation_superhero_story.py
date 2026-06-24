#!/usr/bin/env python3
"""
storyworlds/worlds/scaredy_extinct_surprise_transformation_superhero_story.py
=============================================================================

A standalone story world for a small superhero tale with Surprise and
Transformation beats.

Premise:
- A very scared hero wants to help.
- An unexpected extinct creature clue appears.
- A surprise event gives the hero a chance to transform.
- The transformed hero saves the day and ends braver than before.

This world keeps the prose child-facing and state-driven: the hero starts with
fear, encounters a surprise, uses a helper object or power, transforms, and
finishes with a concrete change in behavior and emotional state.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"      # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "heroine"}
        male = {"boy", "man", "father", "dad", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the city"
    indoors: bool = False
    mood: str = "bright"


@dataclass
class Power:
    id: str
    label: str
    transform_line: str
    helps: set[str] = field(default_factory=set)
    surprise: str = ""


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    causes: str
    scary_words: set[str] = field(default_factory=set)


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "city": Setting(place="the city", indoors=False, mood="bright"),
    "museum": Setting(place="the museum", indoors=True, mood="quiet"),
    "harbor": Setting(place="the harbor", indoors=False, mood="windy"),
}

POWERS = {
    "sunburst": Power(
        id="sunburst",
        label="sunburst power",
        transform_line="a warm light swirled around the scarf and turned into a shining suit",
        helps={"dark", "fear"},
        surprise="A golden badge glowed under the dust.",
    ),
    "wind-steps": Power(
        id="wind-steps",
        label="wind-steps power",
        transform_line="the wind zipped around the boots and lifted the hero into a faster shape",
        helps={"reach", "run"},
        surprise="A hidden gust opened the old cape like a sail.",
    ),
    "heart-shield": Power(
        id="heart-shield",
        label="heart-shield power",
        transform_line="the necklace flashed and changed into a bright shield on the hero's arm",
        helps={"protect", "guard"},
        surprise="A tiny spark jumped from the necklace like a hello.",
    ),
}

THREATS = {
    "shadow-bat": Threat(
        id="shadow-bat",
        label="shadow bat",
        phrase="a flapping shadow bat in the hall",
        causes="the lights flickered and the room felt spooky",
        scary_words={"shadow", "bat", "dark"},
    ),
    "broken-bridge": Threat(
        id="broken-bridge",
        label="broken bridge",
        phrase="a cracked bridge over the river",
        causes="the path stopped right in the middle",
        scary_words={"cracked", "fall", "gap"},
    ),
    "stuck-door": Threat(
        id="stuck-door",
        label="stuck door",
        phrase="a stuck museum door",
        causes="the door would not open for the visitors",
        scary_words={"stuck", "closed", "locked"},
    ),
}

EXTINCT_CLUES = {
    "dino-toy": "an extinct dinosaur picture on the wall",
    "mammoth-bone": "an extinct mammoth bone in a display case",
    "dodo-feather": "an extinct dodo feather in a glass box",
}

HERO_NAMES = ["Milo", "Nina", "Toby", "Lena", "Aria", "Evan", "Pia", "Zane"]
HERO_TYPES = ["boy", "girl"]
CHARACTER_TRAITS = ["scaredy", "kind", "curious", "gentle", "small", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    power: str
    threat: str
    clue: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
power(X) :- power_id(X).
threat(T) :- threat_id(T).
clue(C) :- clue_id(C).

compatible(P, T, C) :- setting(P), power_id(X), threat_id(T), clue_id(C),
                       helps(X, H), threat_need(T, H), clue_theme(C, extinct),
                       place_theme(P, adventure), not bad_combo(P, T, C).

bad_combo(P, T, C) :- setting(P), threat_id(T), clue_id(C),
                      forbidden_place(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        lines.append(asp.fact("place_theme", sid, "adventure"))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power_id", pid))
        for h in sorted(p.helps):
            lines.append(asp.fact("helps", pid, h))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat_id", tid))
        for h in sorted(t.scary_words):
            lines.append(asp.fact("threat_need", tid, h))
    for cid, clue in EXTINCT_CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("clue_theme", cid, "extinct"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def reasonableness_gate(place: str, power: str, threat: str, clue: str) -> bool:
    if place not in SETTINGS or power not in POWERS or threat not in THREATS or clue not in EXTINCT_CLUES:
        return False
    if clue != "dino-toy" and "extinct" not in EXTINCT_CLUES[clue]:
        return False
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES)


def hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for power in POWERS:
            for threat in THREATS:
                for clue in EXTINCT_CLUES:
                    if reasonableness_gate(place, power, threat, clue):
                        combos.append((place, power, threat))
    return combos


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = []
    for place in SETTINGS:
        if args.place and place != args.place:
            continue
        for power in POWERS:
            if args.power and power != args.power:
                continue
            for threat in THREATS:
                if args.threat and threat != args.threat:
                    continue
                for clue in EXTINCT_CLUES:
                    if args.clue and clue != args.clue:
                        continue
                    if reasonableness_gate(place, power, threat, clue):
                        combos.append((place, power, threat, clue))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------

def generate_story(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    setting = SETTINGS[params.place]
    power = POWERS[params.power]
    threat = THREATS[params.threat]
    clue_text = EXTINCT_CLUES[params.clue]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"fear": 1.0},
        memes={"scaredy": 1.0 if params.trait == "scaredy" else 0.0, "hope": 0.0, "bravery": 0.0},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="adult",
        label="the helper",
        meters={},
        memes={"calm": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=params.clue,
        phrase=clue_text,
    ))

    sub, obj, pos = hero_pronouns(params.gender)

    # Act 1: setup and surprise.
    world.say(
        f"{hero.id} was a little {params.trait} hero who wanted to help in {setting.place}."
    )
    world.say(
        f"But {sub} was also a scaredy hero, and big crowds made {obj} feel tiny."
    )
    world.say(
        f"Then {sub} found {clue.phrase}, and that was a surprise."
    )
    world.para()

    # Act 2: the threat and the turning point.
    world.say(
        f"Nearby, {threat.phrase} caused trouble because {threat.causes}."
    )
    world.say(
        f"{sub.capitalize()} wanted to run, but {mentor.label or 'the helper'} pointed to the clue and said, "
        f'"Even extinct things can remind us to be bold."'
    )
    hero.meters["fear"] += 1.0
    hero.memes["hope"] += 1.0
    world.say(
        f"{sub.capitalize()} took a deep breath and stepped closer."
    )
    world.para()

    # Act 3: transformation and resolution.
    world.say(
        f"Then the surprise happened: {power.surprise}"
    )
    world.say(
        f"{power.transform_line}."
    )
    hero.meters["fear"] = 0.0
    hero.memes["bravery"] += 2.0
    hero.memes["scaredy"] = 0.0
    world.say(
        f"{sub.capitalize()} became a shining superhero and used {power.label} to help."
    )
    if power.id == "sunburst":
        world.say(
            f"The bright glow chased away the spooky feeling, and the room looked safe again."
        )
    elif power.id == "wind-steps":
        world.say(
            f"The fast wind helped {obj} rush across the gap before anyone got stuck."
        )
    else:
        world.say(
            f"The bright shield helped {obj} guard the way so the visitors could pass."
        )
    world.say(
        f"In the end, {hero.id} was still small, but {sub} was no longer a scaredy hero."
    )
    world.say(
        f"{sub.capitalize()} stood beside the extinct clue, smiling like a real superhero after a brave day."
    )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        clue=clue,
        setting=setting,
        power=power,
        threat=threat,
    )

    prompts = [
        f'Write a short superhero story for a small child that includes the words "scaredy" and "extinct".',
        f"Tell a story where {hero.id} faces {threat.label} in {setting.place} and then transforms with {power.label}.",
        f"Write a gentle surprise-and-transformation superhero tale that ends with a brave hero helping others.",
    ]

    story_qa = [
        QAItem(
            question=f"Why was {hero.id} called a scaredy hero at the start?",
            answer=f"{hero.id} was called a scaredy hero because {sub} felt very afraid in {setting.place}, especially before the surprise helped {obj} grow brave.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find in the story?",
            answer=f"{hero.id} found {clue.phrase}, and that surprise helped start the hero's transformation.",
        ),
        QAItem(
            question=f"What changed after the transformation?",
            answer=f"After the transformation, {hero.id} stopped feeling so scared and became a shining superhero who could help with {threat.label} trouble.",
        ),
    ]

    if params.power == "sunburst":
        story_qa.append(
            QAItem(
                question=f"How did the sunburst power help the hero?",
                answer=f"The sunburst power made a warm bright glow that chased away the spooky feeling and helped the hero act bravely.",
            )
        )
    elif params.power == "wind-steps":
        story_qa.append(
            QAItem(
                question=f"How did the wind-steps power help the hero?",
                answer=f"The wind-steps power helped the hero move quickly and reach the trouble before anyone got stuck.",
            )
        )
    else:
        story_qa.append(
            QAItem(
                question=f"How did the heart-shield power help the hero?",
                answer=f"The heart-shield power gave the hero a bright shield to guard the way and keep everyone safe.",
            )
        )

    world_qa = [
        QAItem(
            question="What does extinct mean?",
            answer="Extinct means that a kind of animal or plant does not live anywhere anymore.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a helper who uses special courage or powers to protect others.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change from one shape, form, or way of being into another.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with scaredy, extinct, Surprise, and Transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--power", choices=POWERS.keys())
    ap.add_argument("--threat", choices=THREATS.keys())
    ap.add_argument("--clue", choices=EXTINCT_CLUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
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
    if args.gender and not args.name:
        pass
    place, power, threat, clue = select_combo(args, rng)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or pick_name(gender, rng)
    trait = args.trait or rng.choice(CHARACTER_TRAITS)
    if trait != "scaredy" and rng.random() < 0.4:
        trait = "scaredy"
    return StoryParams(place=place, power=power, threat=threat, clue=clue, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, power, threat) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for power in POWERS:
                for threat in THREATS:
                    for clue in EXTINCT_CLUES:
                        if reasonableness_gate(place, power, threat, clue):
                            params = StoryParams(
                                place=place,
                                power=power,
                                threat=threat,
                                clue=clue,
                                name="Milo",
                                gender="boy",
                                trait="scaredy",
                                seed=base_seed,
                            )
                            samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
