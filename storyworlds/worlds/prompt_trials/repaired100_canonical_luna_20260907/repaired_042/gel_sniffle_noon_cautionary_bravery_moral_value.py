#!/usr/bin/env python3
"""
A small folk-tale storyworld about gel, a sniffle at noon, and brave caution.
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
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Milo"
    village: str = "Willowbrook"
    remedy: str = "silverleaf gel"
    scenario_id: int = 0
    telling_mode: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SCENARIOS = [
    {
        "place": "the old herb garden",
        "cause": "Luna had rubbed a mysterious jar of gel without asking what it was",
        "danger": "the gel began making her nose itch whenever the noon bell rang",
        "clue": "the label showed a little red moon beside the words: ask the healer first",
        "action": "Milo carried the jar away and opened the garden gate for fresh air",
        "line": "Brave hands do not rush toward a mystery; they first learn its name",
        "lesson": "caution is a brave way to protect yourself and others",
        "ending": "Luna's sniffle faded while the silverleaf gel rested safely on the healer's shelf",
    },
    {
        "place": "the sunny village square",
        "cause": "a warm noon wind blew a dab of bright gel from a market stall onto Luna's sleeve",
        "danger": "each sniffle made the gel spread closer to her eyes",
        "clue": "the market woman said clean water, not a quick rub, would loosen the sticky gel",
        "action": "Luna stood still while Milo fetched a basin and the market woman helped rinse the sleeve",
        "line": "The bravest choice can be to stand still and listen",
        "lesson": "following wise instructions is a form of bravery",
        "ending": "the noon square shone clean, and the gel sat sealed beneath the market woman's awning",
    },
    {
        "place": "the path beside the millpond",
        "cause": "Luna found a fallen pouch of cooling gel and opened it near the dusty path",
        "danger": "a sudden sniffle sent dust toward the pond and made the ducks flap wildly",
        "clue": "the pouch warned that the gel should be closed before anyone sneezed or sniffled near water",
        "action": "Milo led Luna upwind, tied the pouch shut, and asked the miller for a cloth",
        "line": "Courage is not pretending there is no danger; it is choosing the safe path",
        "lesson": "careful choices protect both people and the living world",
        "ending": "the ducks settled on the pond while the closed gel pouch rested in the miller's shed",
    },
]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is gel?",
        answer="Gel is a soft, jelly-like substance that can be spread or squeezed, but different gels may have different uses and safety rules.",
    ),
    QAItem(
        question="What is a sniffle?",
        answer="A sniffle is a small repeated sniff, often caused by a cold, dust, or irritation.",
    ),
    QAItem(
        question="Why can noon be important in a folk tale?",
        answer="Noon can mark a bright, busy turning point when a hidden problem becomes easy to notice.",
    ),
    QAItem(
        question="What is cautionary bravery?",
        answer="Cautionary bravery means facing a problem while thinking carefully and choosing a safe action.",
    ),
]


ASP_RULES = r"""
safe_action :- reads_label, asks_helper.
brave_choice :- safe_action.
moral_value(caution) :- brave_choice.
valid_story :- brave_choice, moral_value(caution).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("has_item", "hero", "gel"),
            asp.fact("has_sign", "hero", "sniffle"),
            asp.fact("time", "noon"),
            asp.fact("reads_label"),
            asp.fact("asks_helper"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_world(params: StoryParams) -> World:
    scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    world = World()
    luna = world.add(
        Entity(
            "hero",
            "child",
            params.child_name,
            ["curious", "brave"],
            {"worry": 0.0, "safety": 0.0},
            {"caution": 0.0, "confidence": 0.0},
        )
    )
    milo = world.add(
        Entity(
            "helper",
            "friend",
            params.helper_name,
            ["patient", "wise"],
            {"attention": 1.0},
            {"kindness": 1.0},
        )
    )
    gel = world.add(
        Entity(
            "gel",
            "object",
            params.remedy,
            ["sticky", "mysterious"],
            {"risk": 1.0},
            {"warning": 1.0},
        )
    )

    openings = [
        f"At noon in {params.village}, {luna.label} walked past {scene['place']}.",
        f"When the noon bell rang over {params.village}, {luna.label} was near {scene['place']}.",
        f"One bright noon, {luna.label} found a small puzzle waiting at {scene['place']}.",
    ]
    world.say(openings[params.telling_mode % len(openings)])
    world.say(f"There she met a jar of {gel.label}, and {scene['cause']}.")
    world.say(f"Then {scene['danger']}.")
    world.say(f"The danger was small, but it could grow if nobody paid attention.")
    world.para()

    luna.meters["worry"] = 1.0
    luna.memes["caution"] = 0.5
    world.say(f'"Do not rub it in," {milo.label} called. "Let us find out what the gel needs."')
    world.say(f'"I am a little afraid," {luna.label} said, "but I will listen."')
    world.say(f"{scene['clue'].capitalize()}.")
    world.say(f"{milo.label} nodded. {scene['action'].capitalize()}.")
    world.say(f'"Is that brave?" {luna.label} asked.')
    world.say(f'"Yes," said {milo.label}. "Bravery gives wisdom time to help."')
    world.para()

    luna.meters["worry"] = 0.0
    luna.meters["safety"] = 1.0
    luna.memes["caution"] = 1.0
    luna.memes["confidence"] = 1.0
    gel.meters["risk"] = 0.0
    world.say(f"The sniffle soon passed, and the trouble with the gel was safely contained.")
    world.say(f"{luna.label} understood the moral value hidden in the noon adventure: {scene['lesson'].capitalize()}.")
    world.say(f"{scene['ending'].capitalize()}.")
    world.say(f"From that day onward, the children of {params.village} called careful courage the brightest kind of bravery.")

    world.facts.update(
        hero=luna,
        helper=milo,
        gel=gel,
        scene=scene,
        village=params.village,
        resolved=True,
        moral=scene["lesson"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Tell a child-friendly folk tale involving gel, a sniffle, and noon.",
        f"Write a cautionary story in which {f['hero'].label} shows bravery by seeking help.",
        "End with a clear moral value about careful courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    hero = f["hero"].label
    helper = f["helper"].label
    return [
        QAItem(
            question=f"What happened to {hero} at noon?",
            answer=f"At noon, {scene['danger']}. The problem began because {scene['cause']}.",
        ),
        QAItem(
            question=f"How did {helper} help?",
            answer=f"{helper} noticed the danger, explained the clue, and helped the children choose a safe action: {scene['action']}.",
        ),
        QAItem(
            question="How did the story show bravery?",
            answer=f"The story showed bravery when {hero} admitted being afraid but listened carefully instead of rushing. {scene['line']}.",
        ),
        QAItem(
            question="What moral value did Luna learn?",
            answer=f"Luna learned that {scene['lesson']}.",
        ),
        QAItem(
            question="How did the ending prove the problem was over?",
            answer=f"The ending showed safety because {scene['ending']}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def python_reasonable(params: StoryParams) -> None:
    if params.child_name == params.helper_name:
        raise StoryError("The child and helper must have different names.")
    if not params.child_name or not params.helper_name:
        raise StoryError("Both characters need names.")
    if params.remedy != "silverleaf gel":
        raise StoryError("This folk tale requires the silverleaf gel.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(sym.name == "valid_story" for sym in model):
        print("OK: ASP gate accepts the cautious brave story.")
        return 0
    print("ASP gate did not find a valid story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk tale about gel, a sniffle at noon, cautionary bravery, and moral value."
    )
    ap.add_argument("--child-name", choices=["Luna", "Nia", "Pia", "Tara"])
    ap.add_argument("--helper-name", choices=["Milo", "Oren", "Bram", "Sage"])
    ap.add_argument("--village", choices=["Willowbrook", "Sunmeadow", "Brook Hollow"])
    ap.add_argument("--remedy", choices=["silverleaf gel"])
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
    params = StoryParams(
        child_name=args.child_name or rng.choice(["Luna", "Nia", "Pia", "Tara"]),
        helper_name=args.helper_name or rng.choice(["Milo", "Oren", "Bram", "Sage"]),
        village=args.village or rng.choice(["Willowbrook", "Sunmeadow", "Brook Hollow"]),
        remedy=args.remedy or "silverleaf gel",
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(3),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(WORLD_KNOWLEDGE),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind}, traits={entity.traits}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


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
    StoryParams(child_name="Luna", helper_name="Milo", village="Willowbrook", scenario_id=0),
    StoryParams(child_name="Nia", helper_name="Sage", village="Sunmeadow", scenario_id=1),
    StoryParams(child_name="Pia", helper_name="Oren", village="Brook Hollow", scenario_id=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/0."))
        print("valid_story." if any(sym.name == "valid_story" for sym in model) else "no valid story")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
