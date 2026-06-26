#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/injection_wall_problem_solving_misunderstanding_adventure.py
==============================================================================================================

A small adventure storyworld about a child explorer, a nervous misunderstanding,
and a careful problem-solving turn involving an injection and a wall.

Seed tale shape:
- A child loves adventure.
- A needed injection creates fear because it is misunderstood.
- A wall blocks a simple path, so the family must solve the problem together.
- The end shows that the child is brave, the misunderstanding is cleared, and
  the wall no longer feels like an impossible barrier.

The world is tiny and classical: a few entities, a few state changes, and a
single grounded story per sample.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the clinic hall"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    challenge: str
    child: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "clinic": Setting(place="the clinic hall", affords={"injection", "wall"}),
    "garden": Setting(place="the garden gate", affords={"wall"}),
    "station": Setting(place="the station room", affords={"injection", "wall"}),
}

CHALLENGES = {
    "injection": Challenge(
        id="injection",
        verb="get the injection",
        gerund="getting the injection",
        rush="back away from the chair",
        keyword="injection",
        tags={"needle", "medicine", "scary"},
    ),
    "wall": Challenge(
        id="wall",
        verb="climb the wall",
        gerund="climbing the wall",
        rush="run toward the wall",
        keyword="wall",
        tags={"wall", "climb", "stone"},
    ),
}

FIXES = {
    "counting": Fix(id="counting", label="a counting game", prep="count together from one to five", tail="counted slowly together"),
    "stepstool": Fix(id="stepstool", label="a small step stool", prep="bring over a small step stool", tail="moved the stool into place"),
    "picture": Fix(id="picture", label="a picture of the plan", prep="draw the plan on a picture card", tail="looked at the picture card"),
}

GIRL_NAMES = ["Maya", "Luna", "Iris", "Nora", "Ruby", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Milo", "Eli", "Noah", "Ben"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, chall) for place, s in SETTINGS.items() for chall in s.affords for _ in [0]]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_worry(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("worry", 0) >= THRESHOLD and not child.memes.get("seen_worry", 0):
        child.memes["seen_worry"] = 1
        return ["The child looked worried."]
    return []


def _r_wall_block(world: World) -> list[str]:
    child = world.get("child")
    if child.meters.get("blocked", 0) >= THRESHOLD and not world.facts.get("blocked_seen"):
        world.facts["blocked_seen"] = True
        return ["The wall would not let the child pass."]
    return []


RULES = [Rule("worry", _r_worry), Rule("wall_block", _r_wall_block)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, child: Entity, chall: Challenge) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] = 1
    if chall.id == "wall":
        sim.get("child").meters["blocked"] = 1
    return {
        "worry": sim.get("child").memes.get("worry", 0) >= THRESHOLD,
        "blocked": sim.get("child").meters.get("blocked", 0) >= THRESHOLD,
    }


def tell(setting: Setting, challenge: Challenge, child_name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    world.add(Entity(id="challenge", type=challenge.id, label=challenge.keyword, phrase=challenge.verb))
    world.facts.update(child=child, parent=parent, challenge=challenge)

    world.say(f"{child_name} was a little adventurer who loved surprises and secret paths.")
    world.say(
        f"{child_name} loved exploring {setting.place}, where every corner felt like a new map."
    )

    world.para()
    if challenge.id == "injection":
        world.say(f"One day, {child_name} had to go to {setting.place} for an injection.")
        world.say(
            f"{child_name} imagined a giant sharp thing and got scared, because {child_name} did not know what the injection was really like."
        )
        child.memes["worry"] = 1
        propagate(world, narrate=True)
        world.say(
            f"{parent_type.capitalize()} gently explained that the injection was a quick pinch that helped the body stay strong."
        )
        world.say(
            f"Then {parent_type} offered {FIXES['counting'].label} and said, 'We can {FIXES['counting'].prep} while the nurse gets ready.'"
        )
        child.memes["curiosity"] = 1
        world.say(
            f"{child_name} listened, took a deep breath, and {FIXES['counting'].tail} until the moment passed."
        )
        world.say(
            f"After that, {child_name} felt proud, because the scary injection had turned into a brave little victory."
        )
    else:
        world.say(f"One day, {child_name} came to {setting.place} and saw a tall wall blocking the way.")
        world.say(
            f"{child_name} thought the wall would be impossible to cross, and that was not true at all."
        )
        child.meters["blocked"] = 1
        propagate(world, narrate=True)
        world.say(
            f"{parent_type.capitalize()} smiled and said the wall was not a trap; it only needed a smart plan."
        )
        world.say(
            f"Then {parent_type} offered {FIXES['stepstool'].label} and said, 'We can {FIXES['stepstool'].prep} and try safely.'"
        )
        world.say(
            f"{child_name} used the plan, climbed carefully, and reached the other side with a happy grin."
        )
        world.say(
            f"The wall stayed there, but it no longer felt like a problem."
        )

    world.para()
    if challenge.id == "injection":
        world.say(
            f"In the end, the misunderstanding was gone, and {child_name} walked out holding {parent_type}'s hand like a tiny hero."
        )
    else:
        world.say(
            f"In the end, the wall was only part of the adventure, and {child_name} kept going with bright, steady steps."
        )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    challenge = f["challenge"]
    return [
        f"Write a short adventure story for a child named {child.label} about a misunderstanding and a clever fix involving {challenge.keyword}.",
        f"Tell a child-friendly adventure where a little hero faces {challenge.keyword} and learns to solve the problem calmly.",
        f"Write a gentle story where {child.label} is worried about {challenge.keyword}, but a parent helps with a better plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    challenge = f["challenge"]
    qas = [
        QAItem(
            question=f"What adventure was {child.label} having in the story?",
            answer=f"{child.label} was having a small adventure at {world.setting.place}. The story was about {challenge.keyword} and how {parent.label} helped solve the problem.",
        ),
        QAItem(
            question=f"What did {child.label} misunderstand about {challenge.keyword}?",
            answer=(
                "The child thought it would be much scarier and harder than it really was."
                if challenge.id == "injection"
                else "The child thought the wall could not be crossed safely."
            ),
        ),
        QAItem(
            question=f"How did {parent.label} help {child.label}?",
            answer=(
                f"{parent.label.capitalize()} gave a calm explanation and offered {FIXES['counting'].label}."
                if challenge.id == "injection"
                else f"{parent.label.capitalize()} gave a calm explanation and offered {FIXES['stepstool'].label}."
            ),
        ),
    ]
    if challenge.id == "injection":
        qas.append(
            QAItem(
                question=f"Why did the injection stop feeling so scary?",
                answer="It felt less scary because the parent explained it clearly and the child used counting to stay calm.",
            )
        )
    else:
        qas.append(
            QAItem(
                question=f"What changed after the child got help with the wall?",
                answer="The child had a safe way across, so the wall was no longer a stopping problem.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    challenge = world.facts["challenge"]
    if challenge.id == "injection":
        return [
            QAItem(
                question="What is an injection?",
                answer="An injection is a quick shot of medicine that helps protect the body or treat an illness.",
            ),
            QAItem(
                question="Why might a child feel nervous about an injection?",
                answer="A child may feel nervous because the needle looks sharp and the moment is unfamiliar.",
            ),
        ]
    return [
        QAItem(
            question="What is a wall?",
            answer="A wall is a strong upright barrier made of brick, stone, or other material.",
        ),
        QAItem(
            question="How can a person get past a low wall safely?",
            answer="A person can use a careful plan, like climbing a step stool or going around it if that is safer.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
challenge_place(P, C) :- place(P), affords(P, C).
valid_story(P, C) :- challenge_place(P, C).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Adventure storyworld about misunderstanding, problem solving, injection, and wall.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child")
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
    if args.place and args.challenge and args.challenge not in SETTINGS[args.place].affords:
        raise StoryError("That place does not support that challenge.")
    choices = [
        (p, c)
        for p, s in SETTINGS.items()
        for c in s.affords
        if (args.place is None or p == args.place) and (args.challenge is None or c == args.challenge)
    ]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, challenge = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, challenge=challenge, child=child, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], params.child, params.gender, params.parent)
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


CURATED = [
    StoryParams(place="clinic", challenge="injection", child="Maya", gender="girl", parent="mother"),
    StoryParams(place="garden", challenge="wall", child="Theo", gender="boy", parent="father"),
    StoryParams(place="station", challenge="injection", child="Iris", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, chall in combos:
            print(f"  {place} / {chall}")
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
            header = f"### {p.child}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
