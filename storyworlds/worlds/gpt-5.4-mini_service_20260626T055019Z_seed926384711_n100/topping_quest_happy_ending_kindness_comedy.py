#!/usr/bin/env python3
"""
A tiny comedy world about a topping quest with kindness and a happy ending.

A child wants to finish a snack or treat with the perfect topping, but the
quest gets funny when the topping keeps slipping, getting shared, and turning
into a small lesson about kindness.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Quest:
    place: str
    base_food: str
    topping: str
    obstacle: str
    helper_action: str
    ending: str
    keyword: str = "topping"


@dataclass
class StoryParams:
    place: str
    quest: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, quest: Quest) -> None:
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

QUESTS: dict[str, Quest] = {
    "cake": Quest(
        place="the kitchen",
        base_food="a plain cake",
        topping="sprinkles",
        obstacle="the sprinkles kept sliding off the frosting",
        helper_action="held the bowl steady and shook the sprinkles with care",
        ending="the cake wore a cheerful rainbow coat of sprinkles",
    ),
    "toast": Quest(
        place="the breakfast table",
        base_food="a piece of toast",
        topping="jam",
        obstacle="the jam wobbled and tried to drip onto the table",
        helper_action="passed over a tiny spoon and slowed the spreading down",
        ending="the toast ended up neat, shiny, and extra sweet",
    ),
    "yogurt": Quest(
        place="the picnic blanket",
        base_food="a cup of yogurt",
        topping="berries",
        obstacle="the berries rolled away like tiny runaway marbles",
        helper_action="made a little berry wall with a spoon and a smile",
        ending="the yogurt turned into a colorful little hill of kindness",
    ),
    "pancakes": Quest(
        place="the sunny table",
        base_food="a stack of pancakes",
        topping="banana slices",
        obstacle="the banana slices kept making silly slides down the stack",
        helper_action="arranged the slices one by one and cheered each try",
        ending="the pancakes became a happy tower with a perfect top",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nina", "Sam", "Ava", "Theo", "Lily", "Ben"]
HELPER_NAMES = ["Mom", "Dad", "Aunt Jo", "Grandma", "Kai", "Mira"]
TRAITS = ["curious", "playful", "cheerful", "silly", "patient"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest(Q) :- quest_name(Q).
happy_ending(Q) :- quest(Q), obstacle(Q,O), kindness_fix(Q,K), K != none.
kindness_fix(cake,steady_hands).
kindness_fix(toast,slow_spread).
kindness_fix(yogurt,berry_wall).
kindness_fix(pancakes,one_by_one).
valid_story(Q) :- quest(Q), happy_ending(Q).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest_name", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((q,) for q in QUESTS)
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo matches Python gate ({len(python_set)} quests).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(quest: Quest) -> bool:
    return bool(quest.base_food and quest.topping and quest.obstacle and quest.ending)


def tell(quest: Quest, params: StoryParams) -> World:
    world = World(quest)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        traits=[params.trait, "kind"],
        meters={"delight": 0.0, "mess": 0.0},
        memes={"hope": 0.0, "kindness": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["helpful"],
        meters={"care": 0.0},
        memes={"kindness": 0.0, "joy": 0.0},
    ))
    topping = world.add(Entity(
        id="topping",
        label=quest.topping,
        type="topping",
        meters={"wobble": 0.0, "spill": 0.0},
    ))

    world.say(
        f"{child.id} was a {params.trait} little {params.child_type} who had one big quest: "
        f"to put {quest.topping} on {quest.base_food}."
    )
    world.say(
        f"At {quest.place}, {child.id} grinned at the bowl and said, "
        f'"The topping is the best part!"'
    )
    world.para()
    world.say(
        f"But then {quest.obstacle}, and that made {child.id} blink, then giggle, then try again."
    )
    child.memes["hope"] += 1
    topping.meters["wobble"] += 1
    child.meters["mess"] += 1

    world.say(
        f"{helper.id} saw the wobble and did not laugh at {child.id}; instead, {helper.id} "
        f"{quest.helper_action}."
    )
    helper.memes["kindness"] += 1
    child.memes["kindness"] += 1
    child.meters["mess"] = max(0.0, child.meters["mess"] - 0.5)
    topping.meters["spill"] = 0.0

    world.para()
    world.say(
        f"{child.id} tried again, slower this time, and the topping stayed put."
    )
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, {quest.ending}, and {child.id} shared the first bite with {helper.id}."
    )
    world.say(
        f"They laughed because the whole quest had been a little wobbly, a little sticky, and very kind."
    )

    world.facts.update(
        child=child,
        helper=helper,
        topping=topping,
        quest=quest,
        place=params.place,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters / QA
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a topping quest.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--place")
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
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
    quest_name = args.quest or rng.choice(sorted(QUESTS))
    if quest_name not in QUESTS:
        raise StoryError("Unknown quest.")
    if not reasonableness_gate(QUESTS[quest_name]):
        raise StoryError("That quest cannot make a complete story.")

    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=args.place or QUESTS[quest_name].place,
        quest=quest_name,
        child_name=child_name,
        child_type=gender,
        helper_name=helper_name,
        helper_type=helper_gender,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    q = world.quest
    p = world.facts["params"]
    return [
        f'Write a short comedy story for a child about a topping quest in {q.place}.',
        f"Tell a kind story where {p.child_name} tries to add {q.topping} to {q.base_food} and gets help.",
        f'Write a happy ending story with the word "topping" that includes a funny mistake and a kind fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.quest
    p = world.facts["params"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"What was {child.id}'s big quest?",
            answer=f"{child.id}'s big quest was to put {q.topping} on {q.base_food}."
        ),
        QAItem(
            question=f"What funny problem happened with the topping?",
            answer=f"{q.obstacle.capitalize()}."
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by being kind and {q.helper_action}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {q.ending}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a topping?",
            answer="A topping is something you put on top of food to make it taste better or look prettier."
        ),
        QAItem(
            question="Why do people help each other in a kitchen?",
            answer="People help each other so food can be made safely, neatly, and with less mess."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring with other people."
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
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    quest = QUESTS[params.quest]
    world = tell(quest, params)
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
    StoryParams(place="the kitchen", quest="cake", child_name="Mia", child_type="girl",
                helper_name="Mom", helper_type="girl", trait="curious"),
    StoryParams(place="the breakfast table", quest="toast", child_name="Leo", child_type="boy",
                helper_name="Dad", helper_type="boy", trait="silly"),
    StoryParams(place="the picnic blanket", quest="yogurt", child_name="Nina", child_type="girl",
                helper_name="Grandma", helper_type="girl", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("Valid quests:", sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
