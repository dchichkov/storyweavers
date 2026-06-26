#!/usr/bin/env python3
"""
storyworlds/worlds/pack_evade_suspense_inner_monologue_heartwarming.py
=====================================================================

A small heartwarming story world about packing a surprise and trying to evade
the little sounds, sights, and interruptions that could spoil it.

Seed-tale premise:
---
A child wants to pack a surprise breakfast for someone they love. The kitchen
is sleepy and full of tiny dangers: a creaky chair, a clattering spoon, and a
curious pet that might give away the secret. The child keeps a worried inner
monologue going while they pack, evade the distractions, and eventually reveal
a warm surprise.

World model:
---
- Physical meters: packed, noise, hidden, warmth, ready
- Emotional memes: worry, suspense, relief, love, pride
- Suspense rises when the child must avoid notice.
- Inner monologue is narrated as self-talk that tracks the child's plan.
- Heartwarming resolution happens when the surprise is delivered safely and the
  recipient feels cared for.

This file is self-contained and follows the Storyweavers storyworld contract.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["packed", "noise", "hidden", "warmth", "ready"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "suspense", "relief", "love", "pride", "tenderness"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    afford_pack: bool = True
    afford_evade: bool = True
    cozy: bool = True


@dataclass
class Goal:
    id: str
    verb: str
    noun: str
    reason: str
    outcome: str
    requires_quiet: bool = True
    keyword: str = ""


@dataclass
class Obstacle:
    id: str
    label: str
    kind: str
    danger: str
    avoid_method: str
    reveals_if: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    warmth: str
    loved_by: str


@dataclass
class StoryParams:
    place: str
    goal: str
    obstacle: str
    gift: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


GOALS = {
    "breakfast": Goal(
        id="breakfast",
        verb="pack a surprise breakfast",
        noun="breakfast tray",
        reason="someone they love needs a gentle wake-up",
        outcome="the breakfast could arrive warm and quiet",
        keyword="pack",
    ),
    "lunch": Goal(
        id="lunch",
        verb="pack a lunch basket",
        noun="lunch basket",
        reason="someone they love is going on a long day",
        outcome="the lunch can stay neat and ready",
        keyword="pack",
    ),
    "comfort": Goal(
        id="comfort",
        verb="pack a comfort bag",
        noun="comfort bag",
        reason="someone they love needs soft, steady care",
        outcome="the bag can carry warmth and kindness",
        keyword="pack",
    ),
}

OBSTACLES = {
    "cat": Obstacle(
        id="cat",
        label="sleepy cat",
        kind="pet",
        danger="a sudden meow could spoil the surprise",
        avoid_method="tiptoe past the nap spot",
        reveals_if="jumps up and starts a noisy yawn",
    ),
    "floor": Obstacle(
        id="floor",
        label="creaky kitchen floorboard",
        kind="place",
        danger="one creak could wake the whole house",
        avoid_method="step on the soft rug instead",
        reveals_if="squeaks under a hurried foot",
    ),
    "shelf": Obstacle(
        id="shelf",
        label="clattering shelf of cups",
        kind="thing",
        danger="a bumped cup could ring like a bell",
        avoid_method="reach carefully and use both hands",
        reveals_if="shivers when the child stretches too fast",
    ),
}

GIFTS = {
    "toast": Gift(
        id="toast",
        label="toast and fruit",
        phrase="warm toast with sliced fruit",
        warmth="golden and cozy",
        loved_by="mom",
    ),
    "tea": Gift(
        id="tea",
        label="tea and biscuits",
        phrase="a small tray with tea and biscuits",
        warmth="gentle and soothing",
        loved_by="dad",
    ),
    "sandwich": Gift(
        id="sandwich",
        label="sandwiches and soup",
        phrase="sandwiches wrapped beside a small cup of soup",
        warmth="soft and filling",
        loved_by="grandma",
    ),
}

SETTINGS = {
    "kitchen": Setting(place="the kitchen", afford_pack=True, afford_evade=True, cozy=True),
    "hall": Setting(place="the hallway", afford_pack=True, afford_evade=True, cozy=False),
    "garden_room": Setting(place="the garden room", afford_pack=True, afford_evade=True, cozy=True),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Rose", "Leah"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max", "Ben", "Sam", "Jack"]
TRAITS = ["careful", "quiet", "loving", "brave", "gentle", "hopeful"]


def inner_monologue(world: World, child: Entity, line: str) -> None:
    world.say(f"{child.pronoun('subject').capitalize()} thought, '{line}'")


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    goal = GOALS[params.goal]
    obstacle = OBSTACLES[params.obstacle]
    gift = GIFTS[params.gift]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"worry": 0.0, "suspense": 0.0, "relief": 0.0, "love": 1.0, "pride": 0.0, "tenderness": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        memes={"worry": 0.0, "suspense": 0.0, "relief": 0.0, "love": 1.0, "pride": 0.0, "tenderness": 1.0},
    ))
    recipient = world.add(Entity(
        id="Recipient",
        kind="character",
        type=gift.loved_by,
        label=f"the {gift.loved_by}",
        memes={"worry": 0.0, "suspense": 0.0, "relief": 0.0, "love": 2.0, "pride": 0.0, "tenderness": 2.0},
    ))
    tray = world.add(Entity(
        id="Gift",
        type="thing",
        label=gift.label,
        phrase=gift.phrase,
        owner=child.id,
        caretaker=helper.id,
        meters={"packed": 0.0, "noise": 0.0, "hidden": 0.0, "warmth": 0.0, "ready": 0.0},
    ))
    world.facts.update(
        child=child, helper=helper, recipient=recipient, tray=tray,
        goal=goal, obstacle=obstacle, gift=gift, place=setting.place,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about packing quietly and evading interruptions.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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


def reasonableness_gate(goal: Goal, obstacle: Obstacle, gift: Gift) -> bool:
    return goal.requires_quiet and obstacle.kind in {"pet", "place", "thing"} and gift.warmth in {"golden and cozy", "gentle and soothing", "soft and filling"}


def explain_rejection(goal: Goal, obstacle: Obstacle, gift: Gift) -> str:
    return f"(No story: the chosen goal, obstacle, and gift do not make a believable quiet-suspense scene. Try a quieter obstacle or a warmer gift.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.obstacle and args.gift:
        if not reasonableness_gate(GOALS[args.goal], OBSTACLES[args.obstacle], GIFTS[args.gift]):
            raise StoryError(explain_rejection(GOALS[args.goal], OBSTACLES[args.obstacle], GIFTS[args.gift]))

    combos = []
    for place in SETTINGS:
        for goal in GOALS:
            for obstacle in OBSTACLES:
                for gift in GIFTS:
                    if reasonableness_gate(GOALS[goal], OBSTACLES[obstacle], GIFTS[gift]):
                        combos.append((place, goal, obstacle, gift))
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if args.goal is None or c[1] == args.goal
              if args.obstacle is None or c[2] == args.obstacle
              if args.gift is None or c[3] == args.gift]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, goal, obstacle, gift = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, obstacle=obstacle, gift=gift, name=name, gender=gender, helper=helper, trait=trait)


def pack_step(world: World, child: Entity, tray: Entity, goal: Goal) -> None:
    child.memes["worry"] += 1
    tray.meters["packed"] += 1
    tray.meters["ready"] += 1
    world.say(f"{child.label} began to {goal.verb}. {child.pronoun('subject').capitalize()} moved one careful thing at a time.")
    inner_monologue(world, child, f"Easy does it. If I am gentle, the surprise will stay lovely.")


def evade_step(world: World, child: Entity, obstacle: Obstacle) -> None:
    child.memes["suspense"] += 1
    world.say(f"Then {child.label} had to evade {obstacle.label}. {obstacle.danger.capitalize()}.")
    inner_monologue(world, child, f"Not the noisy way. I can slip by if I stay small and quiet.")
    world.say(f"{child.label} chose to {obstacle.avoid_method}, and the little plan kept going.")


def near_miss(world: World, child: Entity, obstacle: Obstacle, tray: Entity) -> None:
    child.memes["worry"] += 1
    tray.meters["noise"] += 1
    world.say(f"Once, {obstacle.reveals_if}, and the room held its breath for a tiny second.")
    inner_monologue(world, child, "Please stay calm. Please let the surprise finish.")
    world.say("But the danger passed, and nothing important fell.")


def resolve_story(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    recipient = world.facts["recipient"]
    tray = world.facts["tray"]
    goal = world.facts["goal"]
    child.memes["relief"] += 2
    child.memes["pride"] += 1
    child.memes["love"] += 1
    tray.meters["warmth"] += 1
    tray.meters["hidden"] += 1
    world.say(f"At last, {helper.label} smiled and lifted the lid just enough to peek.")
    world.say(f"They carried the {tray.label} together to {recipient.label}, where the warm smell drifted out like a hug.")
    world.say(f"{recipient.label.capitalize()} looked surprised, then soft-eyed and happy. {goal.outcome.capitalize()}.")
    world.say(f"{child.label} felt the suspense melt away. The surprise had been packed safely, and the love inside it was bigger than the scare.")


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.facts["child"]
    helper = world.facts["helper"]
    tray = world.facts["tray"]
    goal = world.facts["goal"]
    obstacle = world.facts["obstacle"]

    world.say(f"{child.label} was a {params.trait} {params.gender} who wanted to {goal.verb} in {world.setting.place}.")
    world.say(f"{child.label} kept thinking about {goal.reason}.")
    pack_step(world, child, tray, goal)
    world.para()
    world.say(f"But the kitchen was not easy. {helper.label.capitalize()} was nearby, and {obstacle.label} made every sound feel important.")
    evade_step(world, child, obstacle)
    near_miss(world, child, obstacle, tray)
    world.para()
    resolve_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    obstacle = f["obstacle"]
    return [
        f'Write a short heartwarming story for a child about a {child.label} who must {goal.keyword} quietly while trying to evade {obstacle.label}.',
        f'Tell a suspenseful but gentle story with inner monologue about packing a surprise and avoiding {obstacle.label}.',
        f'Write a cozy story where the main character packs a gift, evades a small problem, and ends with a warm family moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    obstacle = f["obstacle"]
    helper = f["helper"]
    recipient = f["recipient"]
    return [
        QAItem(
            question=f"What did {child.label} want to do?",
            answer=f"{child.label} wanted to {goal.verb} for someone they loved.",
        ),
        QAItem(
            question=f"What did {child.label} have to evade while packing?",
            answer=f"{child.label} had to evade {obstacle.label}, because {obstacle.danger}.",
        ),
        QAItem(
            question=f"Who helped at the end?",
            answer=f"{helper.label.capitalize()} helped bring the surprise to {recipient.label}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the surprise arriving safely, the worry fading, and everyone feeling warm and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to pack something?",
            answer="To pack something means to put it together carefully so it is ready to carry or take somewhere.",
        ),
        QAItem(
            question="What does evade mean?",
            answer="To evade something means to slip away from it or avoid it, often by being careful and quick.",
        ),
        QAItem(
            question="Why can a surprise feel exciting?",
            answer="A surprise can feel exciting because you do not know exactly when it will happen, so you wait with curiosity.",
        ),
    ]


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


ASP_RULES = r"""
goal_ok(G) :- goal(G).
obstacle_ok(O) :- obstacle(O).
gift_ok(F) :- gift(F).

quiet_scene(P, G, O, F) :- place(P), goal_ok(G), obstacle_ok(O), gift_ok(F),
                          needs_quiet(G), good_fit(O, F).

good_fit(cat, toast).
good_fit(cat, tea).
good_fit(floor, toast).
good_fit(floor, tea).
good_fit(shelf, sandwich).
good_fit(shelf, tea).

valid_story(P, G, O, F) :- quiet_scene(P, G, O, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g, goal in GOALS.items():
        lines.append(asp.fact("goal", g))
        if goal.requires_quiet:
            lines.append(asp.fact("needs_quiet", g))
    for o in OBSTACLES:
        lines.append(asp.fact("obstacle", o))
    for f in GIFTS:
        lines.append(asp.fact("gift", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = {
        (p, g, o, f)
        for p in SETTINGS
        for g in GOALS
        for o in OBSTACLES
        for f in GIFTS
        if reasonableness_gate(GOALS[g], OBSTACLES[o], GIFTS[f])
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", goal="breakfast", obstacle="cat", gift="toast", name="Mia", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="hall", goal="lunch", obstacle="floor", gift="tea", name="Leo", gender="boy", helper="father", trait="quiet"),
    StoryParams(place="garden_room", goal="comfort", obstacle="shelf", gift="sandwich", name="Nora", gender="girl", helper="mother", trait="loving"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for goal in GOALS:
            for obstacle in OBSTACLES:
                for gift in GIFTS:
                    if reasonableness_gate(GOALS[goal], OBSTACLES[obstacle], GIFTS[gift]):
                        combos.append((place, goal, obstacle, gift))
    return combos


def explain_gender(gift: str, gender: str) -> str:
    return f"(No story: this gift/role pairing does not fit the requested {gender} story.)"


def resolve_params_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.name is None:
        pass
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.goal is None or c[1] == args.goal
              if args.obstacle is None or c[2] == args.obstacle
              if args.gift is None or c[3] == args.gift]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal, obstacle, gift = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, obstacle=obstacle, gift=gift, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
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
            params = resolve_params_args(args, random.Random(seed))
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
            header = f"### {p.name}: {p.goal} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
