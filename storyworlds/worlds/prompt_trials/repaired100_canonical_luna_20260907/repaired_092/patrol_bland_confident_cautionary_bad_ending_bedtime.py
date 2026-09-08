#!/usr/bin/env python3
"""A gentle bedtime patrol about bland clues, confident guesses, and a cautionary bad ending."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Route:
    key: str
    place: str
    bland_clue: str
    confident_guess: str
    careful_test: str
    turn: str
    cause: str
    safe_plan: str
    bad_result: str
    ending_image: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    hero_type: str = "girl"
    helper: str = "Grandpa Moss"
    route: str = "garden_path"
    object_key: str = "moon_bell"
    weather: str = "quiet"
    opening_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


@dataclass
class World:
    route: Route
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

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


ROUTES = {
    "garden_path": Route(
        "garden_path",
        "the moonlit garden path",
        "a bland brown feather lay beside the gate",
        "the night bird had carried away the moon bell",
        "compare the feather with the nests under the porch, without climbing or touching them",
        "the feather was soft but dry, while the bell's cord had left a bright thread on the gate",
        "the wind had pulled the moon bell from its hook and rolled it beneath the old bench",
        "ask Grandpa Moss to lift the bench with a long-handled rake while Luna waits on the path",
        "the bench shifts only halfway, and the bell stays in the dark until morning",
        "a pale cord glimmers beneath the bench as the garden closes its sleepy eyes",
        "A plain clue deserves a patient look before a confident guess.",
    ),
    "pond_walk": Route(
        "pond_walk",
        "the quiet pond walk",
        "three dull ripples crossed the water near the reeds",
        "a frog had taken the missing lantern charm",
        "watch the ripples from the dry bank and compare their direction with the breeze",
        "the ripples traveled toward the reeds, but a loose branch floated away from them",
        "the branch had nudged the charm off the railing and into a shallow pocket of reeds",
        "let the adult patrol leader use a reaching pole after checking the bank",
        "the pole catches on a root, leaving the charm safely out of reach for the night",
        "the lantern shines without its little charm while the pond turns black and still",
        "A moving mark can be caused by wind or water, not a creature.",
    ),
    "porch_steps": Route(
        "porch_steps",
        "the sleepy porch steps",
        "a bland gray smudge marked the lowest step",
        "the delivery cat had brushed against the missing story key",
        "compare the smudge with the porch paint and the cat's fur from a respectful distance",
        "the smudge matched dry porch dust, and tiny wheel tracks crossed it",
        "a toy wagon had carried the key beneath the welcome mat",
        "have the grown-up patrol leader lift the mat and keep the steps clear",
        "the bedtime bell rings before the key is found, so the story room stays closed",
        "warm light spills beneath the door while the key waits under the mat",
        "A confident answer should change when a better test gives new evidence.",
    ),
    "pine_corner": Route(
        "pine_corner",
        "the pine-tree corner",
        "a bland pinecone rested beside a missing blue ribbon",
        "a squirrel had hidden the ribbon in its tree",
        "look for a safe trail of thread on the ground instead of reaching into the branches",
        "the thread led under a dry leaf, not upward, and ended beside a wheel rut",
        "a little cart had rolled over the ribbon and pushed it beneath the leaf",
        "ask the adult to move the leaf with a flashlight and gloved hand",
        "a gust scatters the leaf and ribbon into the tall grass before they can reach it",
        "one blue thread shines in the grass as the patrol turns toward home",
        "A simple clue can point to a careful search, not a risky climb.",
    ),
}

OBJECTS = {
    "moon_bell": "small moon bell",
    "lantern_charm": "lantern charm",
    "story_key": "brass story key",
    "blue_ribbon": "blue ribbon",
}

OPENINGS = (
    "At bedtime, Luna put on her little patrol cape.",
    "The house was quiet, and the moon had climbed above the roofs.",
    "Before the last lamp was turned down, Luna began her evening patrol.",
    "The night seemed ordinary until one small thing was not where it belonged.",
    "A soft bell marked the start of Luna's careful bedtime walk.",
    "The stars came out while Luna checked the familiar path.",
)

DIALOGUES = (
    '"A patrol is for noticing, not for rushing," said {helper}.',
    '"Tell me what you saw before you tell me what you think," {helper} said.',
    '"Even a bland clue may have an important story," said {helper}.',
    '"Confidence is useful when it listens to evidence," {helper} reminded her.',
    '"We can stay safe and still solve the puzzle," said {helper}.',
    '"Let us test the guess gently," {helper} whispered.',
)

TURNS = (
    "That small test changed Luna's confident idea.",
    "The quiet clue became clearer when they looked at what it could not explain.",
    "The patrol slowed down, and the mystery began to point somewhere else.",
    "A careful comparison turned a tempting guess into a better question.",
    "The night offered no dramatic confession, only one useful physical fact.",
    "Luna's first answer softened as the real cause came into view.",
)

ASP_RULES = r"""
item(X) :- item_fact(X).
route(R) :- route_fact(R).
patrol_safe(R) :- route_fact(R), adult_supervision(R).
bad_ending(R) :- route_fact(R), unresolved(R).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("item_fact", key) for key in OBJECTS]
    lines += [asp.fact("route_fact", key) for key in ROUTES]
    lines += [asp.fact("adult_supervision", key) for key in ROUTES]
    lines += [asp.fact("unresolved", key) for key in ROUTES]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime patrol with a bland clue and a cautionary bad ending.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--object", dest="object_key", choices=sorted(OBJECTS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    hero = args.hero or rng.choice(["Luna", "Milo", "Nia", "Oren"])
    if not hero.strip():
        raise StoryError("--hero cannot be empty.")
    route = args.route or rng.choice(list(ROUTES))
    return StoryParams(
        seed=args.seed,
        hero=hero,
        hero_type="girl" if hero in {"Luna", "Nia"} else "boy",
        helper=args.helper or rng.choice(["Grandpa Moss", "Aunt Fern", "Uncle Rowan"]),
        route=route,
        object_key=args.object_key or rng.choice(list(OBJECTS)),
        weather=rng.choice(["quiet", "cool", "silver", "still"]),
        opening_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURNS)),
    )


def tell(params: StoryParams) -> World:
    if params.route not in ROUTES:
        raise StoryError(f"Unknown patrol route: {params.route}.")
    if params.object_key not in OBJECTS:
        raise StoryError(f"Unknown patrol object: {params.object_key}.")
    route = ROUTES[params.route]
    world = World(route)
    hero = world.add(Entity(params.hero, "character", params.hero_type, params.hero, memes={"confidence": 1.0, "care": 1.0}))
    helper = world.add(Entity(params.helper, "character", "adult", params.helper, memes={"patience": 2.0}))
    missing = world.add(Entity(params.object_key, "object", "keepsake", OBJECTS[params.object_key], owner=hero.id, location=route.place, meters={"weight": 0.2}))

    world.say(OPENINGS[params.opening_mode])
    world.say(f"On a {params.weather} night, {hero.id} and {helper.id} walked along {route.place} during their bedtime patrol.")
    world.say(f"They noticed that {missing.phrase} was missing. Nearby, {route.bland_clue}.")
    world.para()
    world.say(f"{hero.id} felt confident and guessed that {route.confident_guess}.")
    world.say(DIALOGUES[params.dialogue_mode].format(helper=helper.id))
    world.say(f"Together they decided to {route.careful_test}.")
    world.say(f"The test showed that {route.turn}.")
    world.say(TURNS[params.turn_mode])
    world.para()
    world.say(f"The cause was quieter than the guess: {route.cause}.")
    world.say(f'"I was too sure too soon," {hero.id} admitted.')
    world.say(f'"That is why we patrol together," {helper.id} replied. "A careful question can keep a small problem safe."')
    world.say(f"Their safe plan was to {route.safe_plan}.")
    world.say(f"But the ending was bad: {route.bad_result}.")
    world.say("No one was hurt, and Luna did not climb, grab, or cross an unsafe place.")
    world.say(route.lesson)
    world.say(f"At last, {route.ending_image}.")

    missing.location = route.place
    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        route=route,
        first_guess=route.confident_guess,
        test=route.careful_test,
        cause=route.cause,
        safe_plan=route.safe_plan,
        bad_result=route.bad_result,
        bad_ending=True,
        patrol_safe=True,
    )
    world.trace.extend([
        f"patrol_route:{route.key}",
        f"missing:{missing.id}",
        f"bland_clue:{route.bland_clue}",
        f"confident_guess:{route.confident_guess}",
        f"test:{route.careful_test}",
        f"cause:{route.cause}",
        f"bad_result:{route.bad_result}",
    ])
    return world


def generation_prompts(world: World) -> list[str]:
    route: Route = world.facts["route"]
    hero: Entity = world.facts["hero"]
    missing: Entity = world.facts["missing"]
    return [
        f"Write a child-friendly bedtime patrol story about {hero.id} searching for a {missing.phrase}.",
        f"Begin with a bland clue: {route.bland_clue}.",
        f"Let a confident guess be tested safely, reveal that {route.cause}, and end with a cautionary bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    route: Route = world.facts["route"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    missing: Entity = world.facts["missing"]
    return [
        QAItem(
            question="What was missing during the patrol?",
            answer=f"The missing item was {hero.id}'s {missing.phrase}.",
        ),
        QAItem(
            question=f"What confident guess did {hero.id} make?",
            answer=f"{hero.id} guessed that {route.confident_guess}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} test the guess?",
            answer=f"They chose to {route.careful_test}. They stayed safe and let the adult handle anything risky.",
        ),
        QAItem(
            question="What really happened?",
            answer=f"They learned that {route.cause}.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because {route.bad_result}. The mystery was understood, but the item was not recovered that night.",
        ),
        QAItem(
            question="What lesson did the patrol teach?",
            answer=route.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    route: Route = world.facts["route"]
    return [
        QAItem(
            question="Why should a child patrol with a trusted adult?",
            answer="A trusted adult can notice hazards, handle tools, and help a child investigate without climbing, grabbing, or entering unsafe places.",
        ),
        QAItem(
            question="Why can a bland clue still matter?",
            answer="A plain mark or ordinary object may show where something moved or what touched it. Careful observation can make a quiet clue useful.",
        ),
        QAItem(
            question="How should confidence work during a mystery?",
            answer="Confidence should help someone ask clear questions, but it should change when a safe test gives better evidence.",
        ),
        QAItem(
            question="What was the important turn in this patrol?",
            answer=f"The turn came when the test showed that {route.turn}.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"location={entity.location!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(route="garden_path", object_key="moon_bell"),
    StoryParams(
        hero="Milo",
        hero_type="boy",
        helper="Aunt Fern",
        route="pond_walk",
        object_key="lantern_charm",
        opening_mode=2,
        dialogue_mode=3,
        turn_mode=4,
    ),
    StoryParams(
        hero="Nia",
        hero_type="girl",
        helper="Uncle Rowan",
        route="porch_steps",
        object_key="story_key",
        opening_mode=4,
        dialogue_mode=1,
        turn_mode=2,
    ),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    show = (
        "#show item/1.\n"
        "#show route/1.\n"
        "#show patrol_safe/1.\n"
        "#show bad_ending/1.\n"
    )
    models = asp.solve(asp_program(show), models=1)
    if not models:
        print("ASP produced no model.")
        return 1
    atoms = asp.atoms(models[0], "route")
    if len(atoms) != len(ROUTES):
        print("ASP/Python parity failed for routes.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    show = "#show item/1.\n#show route/1.\n#show patrol_safe/1.\n#show bad_ending/1.\n"

    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            models = asp.solve(asp_program(show), models=1)
            print(json.dumps({"models": [[str(atom) for atom in model] for model in models]}, indent=2))
        except Exception as exc:
            raise SystemExit(f"ASP unavailable or failed: {exc}")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(args.n):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
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
