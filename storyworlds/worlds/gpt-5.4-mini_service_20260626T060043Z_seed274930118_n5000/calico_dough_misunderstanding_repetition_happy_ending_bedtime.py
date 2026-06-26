#!/usr/bin/env python3
"""
Bedtime-style story world: a calico cat, a bowl of dough, a misunderstanding,
repetition, and a happy ending.

The seed image:
A little calico cat named Poppy wants to help with bedtime bread dough.
A misunderstanding makes the dough seem "all gone," so Poppy repeats the same
careful action a few times, until the family notices the gentle mistake and
turns it into a cozy, happy ending.

The world model tracks:
- physical meters: dough amount, warmth, sleepiness, flour dust
- emotional memes: worry, relief, joy, confusion, patience

The narrated story is driven by state changes, not a frozen template.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type == "cat":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cozy kitchen"
    time: str = "bedtime"
    smells: str = "sweet and warm"
    indoors: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    misunderstanding_line: str
    fix_line: str


SETTINGS = {
    "kitchen": Setting(place="the cozy kitchen", time="bedtime", smells="sweet and warm", indoors=True),
    "bakery": Setting(place="the little bakery kitchen", time="late evening", smells="warm and buttery", indoors=True),
    "moonroom": Setting(place="the moonlit kitchen", time="sleepy bedtime", smells="sweet and calm", indoors=True),
}

ACTIONS = {
    "knead": Action(
        id="knead",
        verb="help knead the dough",
        gerund="kneading the dough",
        repeat_line="again and again",
        misunderstanding_line="Poppy thought the dough was being taken away for good",
        fix_line="the grown-up showed that the dough was only being rested, not lost",
    ),
    "pat": Action(
        id="pat",
        verb="pat the dough into a soft ball",
        gerund="patting the dough",
        repeat_line="once more",
        misunderstanding_line="Poppy thought the dough was too tired to touch",
        fix_line="the grown-up smiled and explained that gentle pats help dough wake up",
    ),
    "shape": Action(
        id="shape",
        verb="shape the dough into little rolls",
        gerund="shaping little rolls",
        repeat_line="one more time",
        misunderstanding_line="Poppy thought the rolls had vanished into the bowl",
        fix_line="the grown-up pointed to the tray where the little rolls were waiting",
    ),
}


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Random knobs
# ---------------------------------------------------------------------------
NAMES = ["Poppy", "Mimi", "Luna", "Clover", "Mochi", "Tilly", "Mabel"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["gentle", "curious", "sleepy", "small", "soft"]
PLACE_ORDER = ["kitchen", "bakery", "moonroom"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(place: str, action: str) -> bool:
    return place in SETTINGS and action in ACTIONS


def explain_rejection(place: str, action: str) -> str:
    return f"(No story: {place!r} and {action!r} do not describe a cozy bedtime dough scene.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place is cozy and the action is a dough activity.
valid(P, A) :- place(P), action(A), cozy(P), dough_action(A).

% A story is bedtime-like if it includes a sleepy setting and a family helper.
bedtime(P, H) :- valid(P, _), helper(H), family(H).

% The misunderstanding is present when the cat thinks the dough is gone or tired.
misunderstanding(A) :- dough_action(A).

% Repetition is part of the story if the same gentle action happens more than once.
repetition(A) :- dough_action(A).

% Happy ending requires a gentle explanation and a settled cat.
happy_ending(P, A) :- valid(P, A), misunderstanding(A), repetition(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("cozy", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("dough_action", a))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("family", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a) for p in SETTINGS for a in ACTIONS if valid_story(p, a)}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_story() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: calico, dough, misunderstanding, repetition, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name", choices=NAMES)
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
    if args.place and args.action and not valid_story(args.place, args.action):
        raise StoryError(explain_rejection(args.place, args.action))
    places = [p for p in SETTINGS if args.place in (None, p)]
    actions = [a for a in ACTIONS if args.action in (None, a)]
    combos = [(p, a) for p in places for a in actions if valid_story(p, a)]
    if not combos:
        raise StoryError("(No valid bedtime dough story matches the given options.)")
    place, action = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    action = ACTIONS["knead"] if params.place == "kitchen" else ACTIONS["pat"]
    if params.place == "bakery":
        action = ACTIONS["shape"]
    if params.place == "moonroom":
        action = ACTIONS["knead"]
    world = World(setting=setting)

    cat = world.add(Entity(
        id=params.name,
        kind="character",
        type="cat",
        label="calico cat",
        meters={"sleepy": 1.0, "confusion": 0.0, "doughdust": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    dough = world.add(Entity(
        id="dough",
        type="dough",
        label="bowl of dough",
        phrase="soft dough for bedtime bread",
        meters={"amount": 1.0, "warmth": 1.0},
    ))

    # Beginning
    world.say(
        f"In {setting.place}, at {setting.time}, a little calico cat named {cat.id} sat by a bowl of dough."
    )
    world.say(
        f"The room smelled {setting.smells}, and {cat.id} loved the way the dough looked soft and sleepy."
    )
    world.say(
        f"{cat.id} wanted to {action.verb}, because {cat.pronoun('possessive')} paws were eager to help."
    )
    world.say(
        f"The {params.helper} smiled and said that quiet kitchen work could be done before bed."
    )

    # Middle: misunderstanding + repetition
    world.say(
        f"Then {action.misunderstanding_line}."
    )
    cat.meters["confusion"] += 1.0
    cat.memes["worry"] += 1.0
    world.say(
        f"So {cat.id} tried {action.gerund} {action.repeat_line}, as if careful repeats could keep the dough from disappearing."
    )
    cat.meters["doughdust"] += 1.0
    dough.meters["amount"] -= 0.1
    world.say(
        f"Each time, tiny flour specks touched {cat.pronoun('possessive')} whiskers, and the dough stayed right there in the bowl."
    )
    world.say(
        f"{params.helper.capitalize()} watched the little repetitions and noticed the mistake."
    )

    # Turn + resolution
    world.say(
        f"At last, {params.helper} explained that the dough was not being taken away at all; it was only resting."
    )
    cat.meters["confusion"] = 0.0
    cat.memes["worry"] = 0.0
    cat.memes["relief"] = 1.0
    cat.memes["joy"] = 1.0
    world.say(
        f"That gentle truth made {cat.id} purr, because now the dough made sense."
    )
    world.say(
        f"Together they finished the last soft shape, tucked the kitchen into bedtime quiet, and left the dough to rise."
    )
    world.say(
        f"{cat.id} curled up by the warm oven and fell asleep with a happy tail and clean, floury paws."
    )

    world.facts.update(
        cat=cat,
        helper=helper,
        dough=dough,
        action=action,
        setting=setting,
        resolved=True,
        misunderstanding=True,
        repetition=True,
        happy_ending=True,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a soft bedtime story about a calico cat and a bowl of dough.",
        f"Tell a gentle story in {f['setting'].place} where {f['cat'].id} misunderstands the dough, repeats one careful action, and ends happily.",
        "Write a child-friendly bedtime tale with a misunderstanding, repetition, and a cozy happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat: Entity = f["cat"]
    helper: Entity = f["helper"]
    action: Action = f["action"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a little calico cat named {cat.id} and {helper.label}.",
        ),
        QAItem(
            question=f"What did {cat.id} want to do with the dough?",
            answer=f"{cat.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What was the misunderstanding?",
            answer=f"{action.misunderstanding_line.capitalize()}.",
        ),
        QAItem(
            question=f"How did the repetition show up in the story?",
            answer=f"{cat.id} kept {action.gerund} {action.repeat_line}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a happy ending: the helper explained the dough, {cat.id} felt relieved, and the cat fell asleep by the warm kitchen.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dough?",
            answer="Dough is a soft mixture of flour, water, and other ingredients that can be shaped before baking.",
        ),
        QAItem(
            question="Why do people let dough rest?",
            answer="People let dough rest so it can relax and rise, which helps bread become soft and fluffy.",
        ),
        QAItem(
            question="What does a calico cat look like?",
            answer="A calico cat usually has a coat with patches of different colors, often including orange, black, and white.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def asp_facts_for_show() -> str:
    return asp_facts()


def asp_program_show(show: str) -> str:
    return asp_program(show)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_pairs() -> list[tuple[str, str]]:
    return [(p, a) for p in SETTINGS for a in ACTIONS if valid_story(p, a)]


def build_from_args(args: argparse.Namespace) -> StoryParams:
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)
    params = resolve_params(args, rng)
    params.seed = seed
    return params


CURATED = [
    StoryParams(place="kitchen", name="Poppy", helper="mother"),
    StoryParams(place="bakery", name="Mimi", helper="grandmother"),
    StoryParams(place="moonroom", name="Luna", helper="father"),
]


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid place/action pairs:")
        for p, a in combos:
            print(f"  {p} {a}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + i
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
            header = f"### {sample.params.name} in {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
