#!/usr/bin/env python3
"""
storyworlds/worlds/dog_flip_sound_effects_superhero_story.py
============================================================

A small standalone story world in a superhero-story style, centered on a hero,
a dog sidekick, a flip action, and comic-book sound effects.

Seed premise:
- A little superhero and a brave dog hear a strange sound effect in the city.
- Something important is stuck, and the hero needs a clever flip to fix it.
- The dog helps, the sounds get louder, and the rescue ends in a bright win.

The world is deliberately small and constraint-checked:
- The rescue must be plausible for the chosen setting and obstacle.
- The dog and hero both have physical state (meters) and emotional state (memes).
- Sound effects are authored from world events instead of pasted as a frozen block.
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
# World data
# ---------------------------------------------------------------------------

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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    zone: set[str]
    risk_word: str
    hint: str


@dataclass
class Gear:
    id: str
    label: str
    action: str
    protects: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.sound_log: list[str] = []

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
    "city": Setting(place="the city square", outdoors=True, affords={"flip", "rescue"}),
    "rooftop": Setting(place="the rooftop", outdoors=True, affords={"flip", "rescue"}),
    "park": Setting(place="the park", outdoors=True, affords={"flip", "rescue"}),
}

PROBLEMS = {
    "banner": Problem(
        id="banner",
        verb="flip the banner",
        gerund="flipping the banner",
        rush="dash to the banner pole",
        sound="FLAP!",
        zone={"arms"},
        risk_word="stuck",
        hint="The banner was tangled on the pole.",
    ),
    "draincover": Problem(
        id="draincover",
        verb="flip the drain cover",
        gerund="flipping the drain cover",
        rush="run to the drain cover",
        sound="CLANK!",
        zone={"arms", "legs"},
        risk_word="jammed",
        hint="The cover had tipped and wedged itself in place.",
    ),
    "kite": Problem(
        id="kite",
        verb="flip the kite free",
        gerund="flipping the kite free",
        rush="leap for the kite string",
        sound="WHOOSH!",
        zone={"arms", "torso"},
        risk_word="caught",
        hint="The kite line had snagged high above the street.",
    ),
}

GEAR = {
    "cape": Gear(
        id="cape",
        label="the bright cape",
        action="snap the cape open",
        protects={"torso"},
        covers={"torso"},
    ),
    "gloves": Gear(
        id="gloves",
        label="the grippy gloves",
        action="pull on the grippy gloves",
        protects={"arms"},
        covers={"arms"},
    ),
    "boots": Gear(
        id="boots",
        label="the red boots",
        action="step into the red boots",
        protects={"legs"},
        covers={"legs"},
    ),
}

DOG_NAMES = ["Flash", "Scout", "Dot", "Sunny", "Bolt"]
HERO_NAMES = ["Milo", "Nina", "Zara", "Leo", "Ivy"]
VILLAIN_NAMES = ["Murmur", "Snag", "Rumble"]
TRAITS = ["brave", "quick", "kind", "curious", "bold"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    problem: str
    hero_name: str
    dog_name: str
    villain: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen setting can host the problem and the gear
% can cover the at-risk region.
problem_ok(S, P) :- setting(S), problem(P), affords(S, flip), zone_of(P, Z), coverable(P, Z).

gear_ok(P, G) :- problem(P), gear(G), zone_of(P, Z), protects(G, Z).

valid_story(S, P) :- problem_ok(S, P), gear_ok(P, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone_of", pid, z))
        lines.append(asp.fact("coverable", pid, next(iter(p.zone))))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for z in sorted(g.protects):
            lines.append(asp.fact("protects", gid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def can_resolve(problem: Problem, gear: Gear) -> bool:
    return bool(problem.zone & gear.protects)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for sid, setting in SETTINGS.items():
        if "flip" not in setting.affords:
            continue
        for pid, prob in PROBLEMS.items():
            if any(can_resolve(prob, g) for g in GEAR.values()):
                out.append((sid, pid))
    return out


def resolve_plan(problem: Problem) -> Gear:
    for gear in GEAR.values():
        if can_resolve(problem, gear):
            return gear
    raise StoryError("No reasonable gear exists for this problem.")


def sound_for(event: str, problem: Problem) -> str:
    return {
        "arrive": "ZIP!",
        "notice": problem.sound,
        "try": "WHAM!",
        "flip": "FLIP!",
        "rescue": "HURRAY!",
        "dog_help": "BARK-BARK!",
        "end": "TA-DA!",
    }[event]


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the words "{f["dog_name"]}" and "flip".',
        f"Tell a comic-book style rescue story where {f['hero_name']} and a dog solve a problem with a flip and loud sound effects.",
        f"Write a bright, child-friendly superhero tale set at {f['place']} with a brave dog sidekick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {f['hero_name']}, {f['dog_name']}, and a problem at {f['place']}.",
        ),
        QAItem(
            question=f"What sound effect showed that the rescue was starting?",
            answer=f"The first big sound was {f['notice_sound']}, which showed that something was stuck and needed help.",
        ),
        QAItem(
            question=f"What did {f['hero_name']} do to fix the problem?",
            answer=f"{f['hero_name']} used a careful flip with {f['gear_label']} while {f['dog_name']} helped and barked encouragement.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses courage, special gear, and smart choices to help people.",
        ),
        QAItem(
            question="Why do comic stories use sound effects?",
            answer="Comic stories use sound effects to make actions feel exciting, loud, and easy to imagine.",
        ),
        QAItem(
            question="What does a dog often do when it wants to help?",
            answer="A dog may bark, run close, or watch carefully, which makes it a good helper in a rescue.",
        ),
    ]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    gear = resolve_plan(problem)

    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    dog = world.add(Entity(id=params.dog_name, kind="character", type="dog", label=params.dog_name))
    villain = world.add(Entity(id=params.villain, kind="character", type="villain", label=params.villain))
    prop = world.add(Entity(id="prop", kind="thing", type=problem.id, label=problem.id.replace("draincover", "drain cover")))

    hero.meters["courage"] = 1
    hero.memes["hope"] = 1
    dog.meters["speed"] = 1
    dog.memes["loyalty"] = 1

    world.facts = {
        "hero_name": hero.id,
        "dog_name": dog.id,
        "place": setting.place,
        "villain": villain.id,
        "problem": problem.id,
        "gear_label": gear.label,
        "notice_sound": problem.sound,
    }

    world.say(f"{hero.id} was a {params.trait} little superhero, and {dog.id} was {hero.pronoun('possessive')} brave dog.")
    world.say(f"Together they watched the sky over {setting.place}.")
    world.say(f"Then they heard {sound_for('notice', problem)} and looked at the {problem.id.replace('draincover', 'drain cover')}.")

    world.para()
    world.say(f"It was {problem.risk_word} and ready to cause trouble. {problem.hint}")
    world.say(f"{hero.id} wanted to {problem.verb}, but {hero.pronoun('possessive')} plan had to be careful.")
    world.say(f"{dog.id} gave a loud {sound_for('dog_help', problem)} and bounced in a little circle.")

    world.para()
    hero.memes["focus"] = 1
    dog.meters["action"] = 1
    world.say(f"{hero.id} put on {gear.label} and listened to the beat of the city.")
    world.say(f"With a deep breath, {hero.id} said, \"{sound_for('try', problem)}\" and made a quick flip.")
    world.say(f"{dog.id} ran beside {hero.id}, as if the dog were cheering in every paw step.")

    world.para()
    prop.meters["fixed"] = 1
    hero.meters["success"] = 1
    hero.memes["joy"] = 1
    dog.memes["joy"] = 1
    world.say(f"The flip worked. {prop.label.capitalize()} settled into place, and the danger was gone.")
    world.say(f"{villain.id} could only stare as {sound_for('rescue', problem)} filled the air.")
    world.say(f"At the end, {hero.id} and {dog.id} stood tall while {sound_for('end', problem)} echoed through {setting.place}.")

    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        for title, items in [
            ("(1) Generation prompts", sample.prompts),
            ("(2) Story questions", sample.story_qa),
            ("(3) World questions", sample.world_qa),
        ]:
            print(title)
            if title == "(1) Generation prompts":
                for p in items:
                    print(p)
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="city", problem="banner", hero_name="Milo", dog_name="Flash", villain="Snag", trait="brave"),
    StoryParams(setting="rooftop", problem="kite", hero_name="Ivy", dog_name="Scout", villain="Murmur", trait="bold"),
    StoryParams(setting="park", problem="draincover", hero_name="Nina", dog_name="Bolt", villain="Rumble", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with a dog, a flip, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--dog-name", choices=DOG_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    prob = PROBLEMS[problem]
    gear = resolve_plan(prob)
    if not can_resolve(prob, gear):
        raise StoryError("Chosen problem has no valid rescue gear.")
    return StoryParams(
        setting=setting,
        problem=problem,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        dog_name=args.dog_name or rng.choice(DOG_NAMES),
        villain=args.villain or rng.choice(VILLAIN_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Only ASP:", sorted(asp_set - py_set))
    print("Only Python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        if len(samples) > 1:
            p = sample.params
            print(f"### {p.hero_name} and {p.dog_name} at {p.setting} ({p.problem})")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
