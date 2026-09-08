#!/usr/bin/env python3
"""
A tiny Storyweavers world about a young superhero's quest to help an
exterminator recover a magical orange peel. The story uses a brief flashback
to show how the hero learned that careful kindness can solve a sticky problem.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Arc:
    key: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    flashback: tuple[str, str]
    quest: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    method: str
    result: str
    image: str


ARCS = (
    Arc(
        "moon_lamp",
        (
            "In {place}, {hero} wore a bright cape and practiced brave rescue leaps.",
            "Then an exterminator named {helper} hurried in with a worried face.",
        ),
        (
            "A golden peel from a healing orange had slipped beneath a buzzing beetle lamp.",
            '"I need that peel to make a gentle garden spray," said {helper}. "But I cannot reach it safely."',
        ),
        (
            "At first, {hero} wanted to blast the lamp with a mighty beam.",
            "Then {hero} remembered a quiet rescue: a small touch can be stronger than a wild one.",
        ),
        (
            '{hero} whispered, "I will dim the lamp, and you can sweep the peel into this tin."',
            "{helper} nodded. Together they worked slowly, and the beetles flew toward the open window.",
        ),
        (
            "The peel slid free without harming a single beetle.",
            "The exterminator smiled as the little hero raised the rescued treasure like a golden shield.",
        ),
        "the orange peel was trapped under a buzzing lamp",
        "dim the lamp and sweep the peel into a tin",
        "the peel was recovered and the beetles were guided outside",
        "a golden peel held up like a shield",
    ),
    Arc(
        "rainy_roof",
        (
            "On the roof of {place}, {hero} watched clouds tumble like gray capes.",
            "An exterminator named {helper} climbed up carrying a small rescue box.",
        ),
        (
            "A slippery orange peel had landed beside a nest of sleepy moths.",
            '"I need the peel for a safe scent trail," said {helper}, "but one careless step could frighten the moths."',
        ),
        (
            "{hero} remembered a day when a loud super-landing scattered birds from a tree.",
            "The hero had learned that real courage sometimes means landing softly.",
        ),
        (
            '{hero} said, "I will hold this umbrella. You can slide the peel along the dry board."',
            "The exterminator pushed gently while the hero kept the rain away from the moth nest.",
        ),
        (
            "The peel reached the rescue box, and the moths stayed tucked together.",
            "When the clouds parted, {hero} and {helper} stood proudly beneath a silver rainbow.",
        ),
        "the peel was beside a nest of sleepy moths on a wet roof",
        "shield the nest from rain while sliding the peel along a board",
        "the peel was saved without disturbing the moths",
        "a silver rainbow above the careful rescuers",
    ),
    Arc(
        "market_crate",
        (
            "At {place}, {hero} zoomed between market stalls, checking every corner for trouble.",
            "An exterminator named {helper} called from behind a stack of fruit crates.",
        ),
        (
            "A fragrant peel had rolled into a crate where tiny ants were marching in neat lines.",
            '"Please help," said {helper}. "The peel belongs in my scent kit, but the ants are using it as a bridge."',
        ),
        (
            "{hero} remembered how a friend once shared a crumb instead of squashing a line of ants.",
            "That old lesson flashed through the hero's mind: make a path for everyone.",
        ),
        (
            '{hero} said, "I will place a leaf bridge beside the crate. Can you lift the peel when the ants cross?"',
            '"That is a clever plan," said {helper}. The ants followed the leaf, and the peel became free.',
        ),
        (
            "The exterminator tucked the peel into the scent kit and left the ants a safe path.",
            "The hero's cape fluttered over the market as everyone cheered for the kind of superpower that thinks first.",
        ),
        "the peel had become a bridge for ants inside a fruit crate",
        "make a leaf bridge so the ants could leave before lifting the peel",
        "the peel was recovered while the ants received a safe path",
        "a cape fluttering above a cheering market",
    ),
    Arc(
        "garden_gate",
        (
            "Behind {place}, {hero} guarded a garden gate with a star on it.",
            "An exterminator named {helper} arrived with a basket and a careful plan.",
        ),
        (
            "A bright orange peel was wedged in a gate hinge beside a family of ladybugs.",
            '"I need it for my plant-safe remedy," said {helper}, "but the hinge must not pinch the ladybugs."',
        ),
        (
            "{hero} flashed back to a time when rushing had broken a toy bridge.",
            "Since then, the hero had learned to look closely before using super strength.",
        ),
        (
            '{hero} said, "I will hold the gate still. You can loosen the hinge with this wooden spoon."',
            "The exterminator eased the peel out, and the ladybugs crawled safely onto a leaf.",
        ),
        (
            "The gate swung freely, the peel rested in the basket, and the ladybugs kept their sunny home.",
            "{hero} saluted {helper}, and together they marched beneath a row of red-and-black wings.",
        ),
        "the peel was wedged in a gate hinge beside ladybugs",
        "hold the gate still while loosening the hinge with a wooden spoon",
        "the peel came free and the ladybugs stayed safe",
        "a row of ladybugs beneath the hero's salute",
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "child"
    helper_gender: str = "adult"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PLACES = {
    "sunny_market": Place("sunny_market", "the sunny market", {"outdoor", "busy"}),
    "rooftop_garden": Place("rooftop_garden", "the rooftop garden", {"outdoor", "high"}),
    "moonlit_alley": Place("moonlit_alley", "the moonlit alley", {"outdoor", "quiet"}),
}
HERO_NAMES = ["Luna", "Nova", "Ray", "Comet"]
HELPER_NAMES = ["Mara", "Pip", "Tess", "Rowan"]

CURATED = [
    StoryParams("sunny_market", "Luna", "Mara", seed=11),
    StoryParams("rooftop_garden", "Nova", "Pip", seed=22),
    StoryParams("moonlit_alley", "Ray", "Tess", seed=33),
    StoryParams("sunny_market", "Comet", "Rowan", seed=44),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, arc.key) for place in PLACES for arc in ARCS]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest with an exterminator and an orange peel.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HERO_NAMES)
    choices = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(choices)
    if hero == helper:
        raise StoryError("The superhero and exterminator must have different names.")
    return StoryParams(place, hero, helper)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("Hero and exterminator names cannot be empty.")
    if params.hero_name.strip().lower() == params.helper_name.strip().lower():
        raise StoryError("The hero and exterminator need different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PLACES[params.place])

    hero = world.add(Entity("hero", "character", "child", params.hero_name, "superhero"))
    helper = world.add(Entity("exterminator", "character", "adult", params.helper_name, "exterminator"))
    peel = world.add(Entity("peel", "object", "orange_peel", "golden orange peel"))
    world.add(Entity("quest_box", "object", "tin", "small rescue tin"))

    values = {
        "place": world.place.label,
        "hero": hero.label,
        "helper": helper.label,
    }
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    peel.meters["trapped"] = 1
    helper.memes["worry"] = 1
    hero.memes["curiosity"] = 1
    world.events.append("problem")
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    hero.memes["memory"] = 1
    world.events.append("flashback")
    for line in arc.flashback:
        world.say(line.format(**values))
    world.para()

    hero.meters["careful_action"] = 1
    helper.meters["careful_action"] = 1
    peel.meters["trapped"] = 0
    peel.meters["recovered"] = 1
    helper.memes["relief"] = 1
    hero.memes["courage"] = 1
    world.events.append("quest_solved")
    for line in arc.quest:
        world.say(line.format(**values))
    world.para()

    world.facts.update(
        hero=hero,
        helper=helper,
        peel=peel,
        arc=arc,
        problem=arc.problem,
        method=arc.method,
        result=arc.result,
        image=arc.image,
        recovered=True,
        flashback_used=True,
        quest_complete=True,
    )
    for line in arc.ending:
        world.say(line.format(**values))
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            'Write a child-friendly superhero story using the words "exterminator" and "peel".',
            f"Tell a quest in which {params.hero_name} helps {params.helper_name}, an exterminator, recover an orange peel.",
            "Include a flashback showing that careful kindness is a superhero strength.",
        ],
        story_qa=[
            QAItem(
                "What was the superhero's quest?",
                f"{params.hero_name}'s quest was to help {params.helper_name}, the exterminator, recover the orange peel because {facts['problem']}."
            ),
            QAItem(
                "How did the hero and the exterminator solve the problem?",
                f"They solved it by working carefully together: they {facts['method']}. As a result, {facts['result']}."
            ),
            QAItem(
                "What did the flashback teach the hero?",
                "The flashback reminded the hero that rushing or using too much power can cause harm, while a careful plan can protect everyone."
            ),
            QAItem(
                "What final image showed that the quest succeeded?",
                f"The ending showed success with {facts['image']}."
            ),
        ],
        world_qa=[
            QAItem(
                "What does an exterminator do?",
                "An exterminator helps control unwanted pests safely, often by finding gentle ways to keep people, animals, and homes safe."
            ),
            QAItem(
                "Why can an orange peel be useful?",
                "An orange peel can have a strong scent and can be used in some safe scent trails, cleaners, or garden remedies."
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.label}: meters={meters} memes={memes}")
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  events: {', '.join(world.events)}")
    return "\n".join(lines)


ASP_RULES = r"""
trapped(peel) :- problem(peel).
careful(hero) :- flashback(hero), quest(hero).
careful(exterminator) :- quest(exterminator).
recovered(peel) :- trapped(peel), careful(hero), careful(exterminator).
quest_complete :- recovered(peel).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("peel", "peel"),
        asp.fact("hero", "hero"),
        asp.fact("exterminator", "exterminator"),
        asp.fact("problem", "peel"),
        asp.fact("flashback", "hero"),
        asp.fact("quest", "hero"),
        asp.fact("quest", "exterminator"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show quest_complete/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_complete/0."))
    return asp.atoms(model, "quest_complete")


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not any(atom.name == "quest_complete" for atom in model):
            print("ASP parity failed: quest did not complete.")
            return 1
        params = StoryParams("sunny_market", "Luna", "Mara", seed=7)
        sample = generate(params)
        if not sample.story.strip():
            print("Generation smoke test failed: empty story.")
            return 1
        if "exterminator" not in sample.story.lower() or "peel" not in sample.story.lower():
            print("Generation smoke test failed: required words missing.")
            return 1
        if not sample.world.facts["recovered"]:
            print("Python parity failed: peel was not recovered.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: ASP/Python parity and generation smoke tests passed.")
    return 0


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            seed = base_seed + index
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
