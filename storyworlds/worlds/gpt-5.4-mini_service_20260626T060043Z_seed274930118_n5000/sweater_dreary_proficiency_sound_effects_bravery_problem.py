#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sweater_dreary_proficiency_sound_effects_bravery_problem.py
===============================================================================================================

A small slice-of-life story world about a dreary day, a favorite sweater,
a noisy little problem, and the brave problem-solving it takes to fix it.

Seed tale:
---
On a dreary afternoon, Junie was wearing a soft blue sweater and trying to
finish a puzzle at the kitchen table. Then the window started to rattle,
clack-clack, in the wind. Junie's grandpa said the latch was loose. Junie felt
a little scared of the high step stool, but she still wanted to help. With a
flashlight, a roll of tape, and lots of careful tries, Junie held the latch
steady while grandpa tightened the screw. The rattle stopped. Junie smiled,
because the noisy problem was solved, and Junie felt more capable than before.

Narrative instruments:
- Sound effects: small, concrete noises that mark the problem and the fix.
- Bravery: the child chooses to help even while feeling unsure.
- Problem solving: the child and helper use the right tool, step by step.
- Proficiency: the child becomes better at a practical task and feels it.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    thing: str
    noise: str
    fix_action: str
    fix_method: str
    resolution_sound: str
    risk: str
    keyword: str = "problem"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.noise_level: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.noise_level = self.noise_level
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    if world.noise_level < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.kind == "thing" and ent.label == "window latch":
            sig = ("noise", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append("The window went clack-clack in the wind.")
    return out


def _r_proficiency(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child or child.memes["practice"] < THRESHOLD:
        return out
    sig = ("proficiency", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["proficiency"] += 1
    out.append(f"{child.id} got a little better at helping with careful fixes.")
    return out


CAUSAL_RULES = [
    Rule("noise", "physical", _r_noise),
    Rule("proficiency", "social", _r_proficiency),
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


def predict_fix(world: World, child: Entity, problem: Problem) -> dict:
    sim = world.copy()
    sim.noise_level += 1
    return {
        "still_noisy": sim.noise_level >= THRESHOLD,
        "confidence": child.memes["proficiency"],
    }


def activity_detail(problem: Problem) -> str:
    return {
        "rattle": "The noise came and went with each gust, like the house was tapping its foot.",
        "buzz": "The sound was small but stubborn, like a tiny bee trapped in a jar.",
        "creak": "The sound stretched long and slow, like the room was yawning.",
    }.get(problem.noise, "The sound kept asking for attention.")


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the air felt still and a little dreary."
    return f"Outside {setting.place}, the day looked dreary and gray."


def choose_gear(problem: Problem) -> Optional[Gear]:
    for gear in GEAR:
        if problem.risk in gear.guards:
            return gear
    return None


def tell(setting: Setting, problem: Problem, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "kind", "careful"],
    ))
    parent = world.add(Entity(id="helper", kind="character", type=parent_type, label="grandpa"))
    sweater = world.add(Entity(
        id="sweater", type="sweater", label="sweater",
        phrase="a soft blue sweater", owner=child.id, caretaker=parent.id
    ))
    latch = world.add(Entity(id="latch", type="thing", label="window latch", phrase="a loose window latch"))
    tape = world.add(Entity(id="tape", type="thing", label="tape roll", phrase="a roll of tape"))
    flashlight = world.add(Entity(id="flashlight", type="thing", label="flashlight", phrase="a small flashlight"))

    child.worn_by = child.id
    world.facts.update(child=child, parent=parent, sweater=sweater, problem=problem, latch=latch, tape=tape, flashlight=flashlight)

    world.say(f"{hero_name} was a little {hero_type} who loved a soft sweater on dreary days.")
    world.say(f"{hero_name} liked how the sweater felt warm and snug, even when the house seemed sleepy.")
    world.say(f"{hero_name} also liked little sound effects, especially clink, tap, and whisper-soft swooshes.")

    world.para()
    world.say(setting_detail(setting))
    world.say(f"Then the {problem.thing} started to make a {problem.noise}-noise.")
    world.say(activity_detail(problem))
    world.say(f"{hero_name} wanted to help, but {hero_name.lower() if hero_name != hero_name.lower() else 'they'} felt unsure about trying something new.")

    world.para()
    world.say(f"{parent.id} noticed the problem and said the latch was loose.")
    world.say(f"{hero_name} took a small breath, held the flashlight, and chose to be brave.")
    world.say(f'"I can try," {hero_name} said, even though {hero_name} was not sure at first.')
    world.noise_level += 1
    child.memes["bravery"] += 1
    child.memes["practice"] += 1
    propagate(world, narrate=True)

    world.para()
    gear = choose_gear(problem)
    if not gear:
        raise StoryError("No reasonable fix gear exists for this problem.")
    world.say(f"{parent.id} handed over {gear.label} and showed the first step.")
    world.say(f"{hero_name} used {problem.fix_method}, while {parent.id} kept the latch steady.")
    world.say(f'Then came a tiny {problem.resolution_sound}.')
    child.memes["proficiency"] += 1
    child.memes["bravery"] += 1
    world.noise_level = 0.0
    world.say(f"The noisy {problem.thing} was fixed, and the room went quiet again.")
    world.say(f"{hero_name} smiled, because being brave had helped solve the problem.")
    world.say(f"By the end, {hero_name} felt more capable than before, and the sweater stayed cozy all through the dreary afternoon.")

    world.facts.update(gear=gear, resolved=True)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"rattle", "creak"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"buzz", "creak"}),
    "porch": Setting(place="the porch", indoor=False, affords={"rattle"}),
}

PROBLEMS = {
    "window": Problem(
        id="window",
        thing="window latch",
        noise="rattle",
        fix_action="tighten",
        fix_method="use the screwdriver and hold the latch still",
        resolution_sound="click",
        risk="loose",
        keyword="window",
        tags={"sound_effects", "bravery", "problem_solving", "proficiency"},
    ),
    "drawer": Problem(
        id="drawer",
        thing="drawer track",
        noise="creak",
        fix_action="oil",
        fix_method="wipe the track and slide it gently",
        resolution_sound="thunk",
        risk="stiff",
        keyword="drawer",
        tags={"sound_effects", "bravery", "problem_solving", "proficiency"},
    ),
    "lamp": Problem(
        id="lamp",
        thing="lamp cord",
        noise="buzz",
        fix_action="unplug",
        fix_method="turn it off and check the plug",
        resolution_sound="zip",
        risk="wobbly",
        keyword="lamp",
        tags={"sound_effects", "bravery", "problem_solving", "proficiency"},
    ),
}

GEAR = [
    Gear(
        id="screwdriver",
        label="a small screwdriver",
        covers={"loose", "stiff", "wobbly"},
        guards={"loose"},
        prep="tighten the screw",
        tail="the little screw held firm",
    ),
    Gear(
        id="cloth",
        label="a soft cloth",
        covers={"stiff"},
        guards={"stiff"},
        prep="wipe the track clean",
        tail="the drawer slid more easily",
    ),
    Gear(
        id="plug_check",
        label="a careful hand and a flashlight",
        covers={"wobbly"},
        guards={"wobbly"},
        prep="look at the plug together",
        tail="the lamp buzzed no more",
    ),
]

GIRL_NAMES = ["Junie", "Nora", "Mina", "Lina", "Ivy", "Pia"]
BOY_NAMES = ["Owen", "Eli", "Milo", "Sam", "Theo", "Finn"]
TRAITS = ["gentle", "curious", "careful", "quiet", "thoughtful", "brave"]


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
    combos = []
    for place, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if problem.id == "window" and not setting.indoor:
                continue
            combos.append((place, pid))
    return combos


KNOWLEDGE = {
    "sweater": [("What is a sweater?", "A sweater is a warm piece of clothing you wear to stay cozy when the air feels cool.")],
    "dreary": [("What does dreary mean?", "Dreary means gray, dull, or gloomy, like a day with no bright sunshine.")],
    "proficiency": [("What is proficiency?", "Proficiency means being able to do something well because you have practiced it.")],
    "bravery": [("What is bravery?", "Bravery means doing something even when you feel a little scared.")],
    "problem_solving": [("What is problem solving?", "Problem solving means figuring out what is wrong and taking steps to fix it.")],
    "sound_effects": [("What are sound effects?", "Sound effects are little noises, like click, tap, and swoosh, that help tell what is happening.")],
}

KNOWLEDGE_ORDER = ["sweater", "dreary", "sound_effects", "bravery", "problem_solving", "proficiency"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    return [
        f'Write a slice-of-life story for a young child about a {problem.thing} on a dreary day.',
        f"Tell a warm, gentle story where {child.id} wears a sweater, hears a noisy problem, and helps solve it bravely.",
        f'Write a simple story that uses the words "sweater", "dreary", and "proficiency" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, problem, gear = f["child"], f["parent"], f["problem"], f["gear"]
    qa = [
        QAItem(
            question=f"What was {child.id} wearing while the day felt dreary?",
            answer=f"{child.id} was wearing a soft sweater that kept {child.pronoun('object')} cozy.",
        ),
        QAItem(
            question=f"What sound let everyone know there was a problem with the {problem.thing}?",
            answer=f"The {problem.thing} made a {problem.noise}-noise, and that sound told them something was loose or stuck.",
        ),
        QAItem(
            question=f"How did {child.id} help fix the problem?",
            answer=f"{child.id} held the flashlight and used {gear.label} together with {parent.id} to fix it step by step.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt brave and more capable, because the problem was solved and {child.id} had practiced something useful.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    tags.update({"sweater", "dreary", "proficiency"})
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", problem="window", name="Junie", gender="girl", parent="grandpa", trait="careful"),
    StoryParams(place="living_room", problem="drawer", name="Owen", gender="boy", parent="grandpa", trait="curious"),
    StoryParams(place="kitchen", problem="lamp", name="Mina", gender="girl", parent="grandpa", trait="brave"),
]


def explain_rejection(setting: Setting, problem: Problem) -> str:
    if problem.id == "window" and not setting.indoor:
        return "(No story: a window latch problem needs an indoor setting so the noise and the fix make sense.)"
    return "(No story: that combination does not create a believable small home problem.)"


def explain_gender(gender: str) -> str:
    return f"(No story: choose a matching character name for {gender}.)"


ASP_RULES = r"""
problem_valid(P, S) :- setting(S), problem(P), not blocked(P, S).
blocked(window, porch) :- setting(porch).
story_valid(S, P) :- setting(S), problem(P), problem_valid(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if SETTINGS[sid].indoor:
            lines.append(asp.fact("indoor", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: sweater, dreary day, and brave problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandpa", "grandma"])
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
    if args.problem and args.place:
        if (args.place, args.problem) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.place], PROBLEMS[args.problem]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "grandpa"
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], params.name, params.gender, params.parent)
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
        print(asp_program("#show story_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem) combos:\n")
        for place, problem in combos:
            print(f"  {place:12} {problem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
