#!/usr/bin/env python3
"""
A small fairy-tale storyworld about an ensemble, a shy runt, and a transformation
that reveals moral value through kindness.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Tale:
    tale_id: str
    place: str
    ensemble: str
    runt: str
    trouble: str
    kindness: str
    transformation: str
    moral: str
    ending: str


TALES = {
    "moon_court": Tale(
        "moon_court",
        "the Moon Court",
        "a traveling ensemble of silver musicians",
        "a runt moon-mouse named Pip",
        "the Moon Court's bell had lost its voice before the midnight dance",
        "Pip shared his last crumb with the silent bell's tiny keeper",
        "the crumb glowed, and Pip became a bright little moon-mouse whose whiskers rang like chimes",
        "a small creature may carry a great gift, and kindness awakens it",
        "Pip led the ensemble home with a trail of soft silver notes",
    ),
    "thorn_garden": Tale(
        "thorn_garden",
        "the Rose Queen's garden",
        "an ensemble of fairy gardeners",
        "a runt beetle called Bramble",
        "a sleeping rose had wrapped its thorns around the garden gate",
        "Bramble freed a trapped ladybird before asking anyone to notice him",
        "his spotted shell unfolded into a golden shield that gently parted the thorns",
        "helping another creature is worth more than being praised",
        "the gate opened, and every rose bowed toward Bramble",
    ),
    "cloud_tower": Tale(
        "cloud_tower",
        "the Cloud Queen's tower",
        "an ensemble of cloud-weavers",
        "a runt sprite named Nib",
        "the tower's rain thread snapped above a thirsty village",
        "Nib gave his own warm cloak to a shivering cloud-child",
        "the cloak became wings of blue mist, and Nib stitched the rain thread across the sky",
        "generosity can make courage grow where no one expects it",
        "kind rain fell while the ensemble sang from the tower roof",
    ),
    "ember_hollow": Tale(
        "ember_hollow",
        "Ember Hollow",
        "an ensemble of firefly dancers",
        "a runt firefly called Flick",
        "the hollow had gone dark on the night of the lantern festival",
        "Flick guided a lost moth back to its family instead of joining the grand parade",
        "his tiny light transformed into a warm golden lantern bright enough for every path",
        "a good deed shines farther than a proud display",
        "the ensemble danced around Flick's lantern until dawn",
    ),
}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    tale: Tale
    hero_name: str
    helper_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    tale_id: str
    hero_name: str
    helper_name: str
    detail_id: int = 0
    seed: Optional[int] = None


def story_reasonable(tale_id: str) -> bool:
    return tale_id in TALES


def explain_rejection(tale_id: str) -> str:
    return f"No fairy tale is registered for '{tale_id}'."


def _case(params: StoryParams) -> Tale:
    if not story_reasonable(params.tale_id):
        raise StoryError(explain_rejection(params.tale_id))
    return TALES[params.tale_id]


BRIDGES = (
    "The others laughed softly, but the smallest heart listened most carefully.",
    "The old herald whispered that every true tale hides its answer in a gentle deed.",
    "The ensemble hurried on, while the runt stayed behind to notice what the proud dancers missed.",
    "A silver moth circled the little creature as if it already knew a secret.",
)


def tell(params: StoryParams) -> World:
    tale = _case(params)
    world = World(tale, params.hero_name, params.helper_name)
    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_name,
            meters={"courage": 1.0, "size": 0.3},
            memes={"kindness": 1.0, "hope": 0.5},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper_name,
            meters={"wisdom": 1.0},
            memes={"trust": 1.0},
        )
    )
    world.facts.update(hero=hero, helper=helper, tale=tale)

    world.say(
        f"Once, in {tale.place}, {tale.ensemble} gathered beneath a starry arch."
    )
    world.say(
        f"Among them sat {tale.runt}, the runt of the company, while the tallest fairies "
        "polished their crowns and practiced their grandest steps."
    )
    world.say(
        f"'{tale.trouble.capitalize()}. What shall we do?' cried {params.helper_name}."
    )
    world.say(
        f"'{params.hero_name} should sit this one out,' said a proud dancer. "
        f"But {params.helper_name} answered, 'A small helper may see what we cannot.'"
    )
    world.say(BRIDGES[params.detail_id % len(BRIDGES)])
    world.say(
        f"Then {params.hero_name} noticed a lonely creature in need and chose to {tale.kindness}."
    )
    world.say(
        f"The kindness changed the whole tale: {tale.transformation}."
    )
    world.say(
        f"'{params.hero_name}, you have changed!' cried {params.helper_name}. "
        f"'{params.hero_name} replied, 'I only tried to help.'"
    )
    world.say(
        f"The ensemble followed the new little hero, and together they solved the trouble. "
        f"At last, {tale.ending}."
    )
    world.say(
        f"And so the kingdom learned that {tale.moral}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.tale
    return [
        f"Write a child-friendly fairy tale about {tale.ensemble} and {tale.runt}.",
        f"Include a transformation caused by this moral choice: {tale.kindness}.",
        f"Show how the ensemble changes after learning that {tale.moral}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.tale
    return [
        QAItem(
            "Who was the runt in the ensemble?",
            f"The runt was {tale.runt}, the smallest member of {tale.ensemble}.",
        ),
        QAItem(
            "What trouble did the ensemble face?",
            f"They faced this trouble: {tale.trouble}.",
        ),
        QAItem(
            "What kind act began the transformation?",
            f"The runt chose to {tale.kindness}.",
        ),
        QAItem(
            "What transformation happened?",
            f"{tale.transformation}. The change gave the runt a way to help everyone.",
        ),
        QAItem(
            "What moral value did the tale teach?",
            f"It taught that {tale.moral}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended when {tale.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an ensemble?",
            "An ensemble is a group of performers or companions who work together.",
        ),
        QAItem(
            "What does transformation mean?",
            "Transformation means a powerful change in shape, ability, or character.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle about how people can choose to behave well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_tale/1.
#show has_ensemble/1.
#show has_runt/1.
valid_tale(T) :- has_ensemble(T), has_runt(T), has_transformation(T), has_moral(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for tale_id in TALES:
        lines.extend(
            [
                asp.fact("has_ensemble", tale_id),
                asp.fact("has_runt", tale_id),
                asp.fact("has_transformation", tale_id),
                asp.fact("has_moral", tale_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_tale/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tales() -> set[str]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return {row[0] for row in asp.atoms(model, "valid_tale")}


def asp_verify() -> int:
    expected = set(TALES)
    actual = asp_valid_tales()
    if actual != expected:
        print("MISMATCH between ASP and Python:")
        print("ASP only:", sorted(actual - expected))
        print("Python only:", sorted(expected - actual))
        return 1
    for tale_id in TALES:
        sample = generate(
            StoryParams(
                tale_id=tale_id,
                hero_name="Luna",
                helper_name="Mira",
                seed=7,
            )
        )
        if not sample.story or "Luna" not in sample.story:
            print(f"Generated story failed for {tale_id}.")
            return 1
    print(f"OK: ASP gate matches Python registry ({len(expected)} tales).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale ensemble storyworld about a runt, transformation, and moral value."
    )
    parser.add_argument("--tale-id", choices=sorted(TALES))
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    tale_id = args.tale_id or rng.choice(sorted(TALES))
    if not story_reasonable(tale_id):
        raise StoryError(explain_rejection(tale_id))
    hero_name = args.hero_name or rng.choice(["Luna", "Pip", "Nell", "Tavi", "Milo"])
    helper_name = args.helper_name or rng.choice(["Mira", "Thelma", "Orin", "Ada", "Rowan"])
    return StoryParams(
        tale_id=tale_id,
        hero_name=hero_name,
        helper_name=helper_name,
        detail_id=(sample_seed or 0) % len(BRIDGES),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"tale: {world.tale.tale_id}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print("\n".join(sorted(asp_valid_tales())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, tale_id in enumerate(sorted(TALES)):
            params = StoryParams(
                tale_id=tale_id,
                hero_name="Luna",
                helper_name="Mira",
                detail_id=index % len(BRIDGES),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed), seed)
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
