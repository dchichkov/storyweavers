#!/usr/bin/env python3
"""A small slice-of-life StoryWorld about an invasion, a treasury, and an introduction."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))

from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "The Treasury Invasion"

SETTINGS = [
    "the small town library",
    "the community hall",
    "the corner bakery",
]
VISITORS = [
    "a family of curious pigeons",
    "three bold garden snails",
    "a line of lost ducklings",
]
TREASURES = [
    "a tin of shiny buttons",
    "a wooden box of old keys",
    "a jar of colorful marbles",
]
KEEPERS = [
    "Luna",
    "Mara",
    "Niko",
]
SOUNDS = [
    ("tap-tap", "tiny feet tapped across the floor"),
    ("flap-flap", "wings flapped beside the open window"),
    ("scritch-scritch", "little claws scritched against the mat"),
]
ROUTES = [
    (
        "Luna was labeling jars when the quiet room suddenly filled with a soft tap-tap.",
        "The sound was small, but it came from the direction of the locked treasury shelf.",
    ),
    (
        "The morning had been ordinary until a flap-flap sounded near the back door.",
        "Luna looked up and saw movement between the chairs beside the treasury.",
    ),
    (
        "While Luna counted the treasury's treasures, she heard a careful scritch-scritch.",
        "Something was entering the room one tiny step at a time.",
    ),
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    keeper: str = "Luna"
    setting: str = "the small town library"
    visitors: str = "a family of curious pigeons"
    treasure: str = "a tin of shiny buttons"
    sound: str = "tap-tap"
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Incident:
    name: str
    problem: str
    clue: str
    mistake: str
    consequence: str
    plan: str
    resolution: str
    ending: str


INCIDENTS = [
    Incident(
        "the open window",
        "the visitors had flown through an open window and crowded around the treasury shelf",
        "their feathers were dusted with flour from the bakery next door",
        "Luna waved a towel and tried to shoo everyone out at once",
        "the pigeons fluttered higher and knocked a soft cloth over the treasure box",
        "close the inner door, sprinkle a trail of crumbs toward the sunny windowsill, and invite the visitors out one group at a time",
        "the pigeons followed the safe trail and left the treasury shelf untouched",
        "the treasury stood neat again while the pigeons cooed outside in the afternoon sun",
    ),
    Incident(
        "the loose gate",
        "the visitors had slipped through a loose garden gate and were nibbling beside the treasury cart",
        "tiny green leaves clung to their shells",
        "Luna reached toward the snails before checking where the cart wheels rested",
        "the cart wobbled and one jar rolled toward the edge",
        "steady the cart with a block, place a leafy board beside the path, and let each snail crawl away at its own pace",
        "the snails crossed the leafy board while every jar remained safely on the cart",
        "the treasury cart waited in a sunny corner, and the snails rested beneath the leaves",
    ),
    Incident(
        "the rainy doorway",
        "the visitors had waddled in through a rainy doorway and gathered around the treasury basket",
        "their wet footprints made a clear line back to the umbrella stand",
        "Luna opened the basket quickly and tried to lift it over the ducklings",
        "the lid slipped and the old keys jingled across the floor",
        "close the basket, dry the floor, and guide the ducklings back along the clear path with a soft towel",
        "the ducklings followed the dry path and the keys were counted back into their basket",
        "the treasury keys rested under their lid while the ducklings peeped beside the warm umbrella rack",
    ),
]


def choose_incident(params: StoryParams) -> Incident:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)]


def setup_world(params: StoryParams, incident: Incident) -> World:
    world = World(params.setting)
    keeper = world.add(Entity("keeper", "character", params.keeper))
    visitors = world.add(Entity("visitors", "visitors", params.visitors))
    treasure = world.add(Entity("treasury", "treasury", params.treasure, owner=keeper.id))
    keeper.memes["curiosity"] = 1
    visitors.meters["inside"] = 1
    treasure.meters["secure"] = 1
    world.facts.update(
        keeper=keeper,
        visitors=visitors,
        treasury=treasure,
        incident=incident,
        sound=params.sound,
        setting=params.setting,
    )
    return world


def tell(params: StoryParams) -> World:
    incident = choose_incident(params)
    world = setup_world(params, incident)
    keeper = world.entities["keeper"]
    visitors = world.entities["visitors"]
    treasury = world.entities["treasury"]

    world.say(
        f"At {world.setting}, {keeper.label} cared for a little treasury. "
        f"It held {treasury.label}, a collection saved for the town's history table."
    )
    world.say(
        f"That morning, {keeper.label} prepared an introduction for {visitors.label}. "
        "They were supposed to be welcomed gently, not invited into the treasury."
    )
    world.say(ROUTES[(params.seed or 0) % len(ROUTES)][0])
    world.say(ROUTES[(params.seed or 0) % len(ROUTES)][1])
    world.para()

    world.say(f"Soon, {incident.problem}.")
    world.say(f"{incident.clue.capitalize()}.")
    world.say(
        f'"I hear you," said {keeper.label}. "But the treasury needs space. '
        f'First I will introduce myself, then we will find a safe way out."'
    )
    world.say(
        f'{keeper.label} tried to {incident.mistake}. As a result, {incident.consequence}.'
    )
    treasury.meters["secure"] = 0
    keeper.memes["worry"] = 1
    world.fired.add(("invasion_caused_setback", incident.name))
    world.para()

    world.say(
        f'{keeper.label} took a breath and repeated the plan: '
        '"Close the way, make a path, move slowly."'
    )
    world.say(
        f'"Close the way, make a path, move slowly," {keeper.label} repeated. '
        f'"Did you hear me?"'
    )
    world.say(f'"Yes, slowly," answered the visitors in their own busy way.')
    world.say(f"Together, they began to {incident.plan}.")
    world.fired.add(("repetition_made_plan_clear", incident.name))
    world.facts["plan"] = incident.plan
    world.para()

    visitors.meters["inside"] = 0
    treasury.meters["secure"] = 1
    keeper.memes["worry"] = 0
    keeper.memes["patience"] = 1
    world.say(f"Because the plan was repeated and followed, {incident.resolution}.")
    world.say(
        f'{keeper.label} smiled. "Welcome to the neighborhood," {keeper.label} said. '
        '"An introduction is nicer when everyone has room to listen."'
    )
    world.say(f"By lunchtime, {incident.ending}.")
    world.fired.add(("invasion_resolved", incident.name))
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a gentle slice-of-life story about {facts['keeper'].label} handling an invasion of {facts['visitors'].label} in {facts['setting']}.",
        f"Include an introduction, the treasury holding {facts['treasury'].label}, the sound effect {facts['sound']}, and a repeated plan.",
        "Show how careful words and a safe path resolve the problem without frightening anyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    keeper = facts["keeper"]
    visitors = facts["visitors"]
    treasury = facts["treasury"]
    incident = facts["incident"]
    return [
        QAItem(
            question=f"What was invaded in {world.setting}?",
            answer=f"{visitors.label} invaded the area around the treasury shelf, where {treasury.label} was kept.",
        ),
        QAItem(
            question=f"What introduction did {keeper.label} prepare?",
            answer=f"{keeper.label} prepared a gentle introduction for {visitors.label} so they could be welcomed outside the treasury.",
        ),
        QAItem(
            question="What sound helped reveal the invasion?",
            answer=f"The sound effect was {facts['sound']}; it announced that movement was coming from near the treasury.",
        ),
        QAItem(
            question="Why did the first attempt cause trouble?",
            answer=f"{keeper.label} tried to {incident.mistake}, which meant that {incident.consequence}.",
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"{keeper.label} repeated the plan to close the way, make a safe path, and move slowly. Then the visitors followed that plan: {incident.resolution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a treasury?",
            answer="A treasury is a place or collection where valuable objects or money are kept safely.",
        ),
        QAItem(
            question="What is an introduction?",
            answer="An introduction is a first welcome or explanation that helps people meet and understand one another.",
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repetition can help people remember important words or steps, especially when a plan needs to be followed carefully.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are written or performed sounds, such as tap-tap or flap-flap, that help show what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted({rule for rule, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("theme", "invasion"),
        asp.fact("theme", "treasury"),
        asp.fact("theme", "introduction"),
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "repetition"),
        asp.fact("style", "slice_of_life"),
    ]
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for visitor in VISITORS:
        lines.append(asp.fact("visitors", visitor))
    for treasure in TREASURES:
        lines.append(asp.fact("treasure", treasure))
    return "\n".join(lines)


ASP_RULES = r"""
has_problem :- theme(invasion), theme(treasury).
needs_welcome :- theme(introduction).
safe_plan :- has_problem, needs_welcome, feature(sound_effects), feature(repetition).
complete_story :- safe_plan, style(slice_of_life).
#show has_problem/0.
#show needs_welcome/0.
#show safe_plan/0.
#show complete_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show complete_story/0."))
    if asp.atoms(model, "complete_story"):
        for seed in range(6):
            sample = generate(
                StoryParams(
                    keeper=KEEPERS[seed % len(KEEPERS)],
                    setting=SETTINGS[seed % len(SETTINGS)],
                    visitors=VISITORS[seed % len(VISITORS)],
                    treasure=TREASURES[seed % len(TREASURES)],
                    sound=SOUNDS[seed % len(SOUNDS)][0],
                    seed=seed,
                )
            )
            if not sample.story or "treasury" not in sample.story:
                print("Verification failed: generated story was incomplete.")
                return 1
        print("OK: ASP parity and generated stories verified.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice-of-life story world about an invasion, treasury, and introduction."
    )
    parser.add_argument("--keeper", choices=KEEPERS, default=None)
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--visitors", choices=VISITORS, default=None)
    parser.add_argument("--treasure", choices=TREASURES, default=None)
    parser.add_argument("--sound", choices=[sound for sound, _ in SOUNDS], default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        keeper=args.keeper or rng.choice(KEEPERS),
        setting=args.setting or rng.choice(SETTINGS),
        visitors=args.visitors or rng.choice(VISITORS),
        treasure=args.treasure or rng.choice(TREASURES),
        sound=args.sound or rng.choice([sound for sound, _ in SOUNDS]),
        seed=args.seed,
    )


def validate_params(params: StoryParams) -> None:
    if params.keeper not in KEEPERS:
        raise StoryError(f"Unknown keeper: {params.keeper}")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.visitors not in VISITORS:
        raise StoryError(f"Unknown visitors: {params.visitors}")
    if params.treasure not in TREASURES:
        raise StoryError(f"Unknown treasure: {params.treasure}")
    if params.sound not in [sound for sound, _ in SOUNDS]:
        raise StoryError(f"Unknown sound effect: {params.sound}")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(params)
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
    StoryParams(
        keeper="Luna",
        setting="the small town library",
        visitors="a family of curious pigeons",
        treasure="a tin of shiny buttons",
        sound="tap-tap",
        seed=0,
    ),
    StoryParams(
        keeper="Mara",
        setting="the community hall",
        visitors="three bold garden snails",
        treasure="a wooden box of old keys",
        sound="scritch-scritch",
        seed=1,
    ),
    StoryParams(
        keeper="Niko",
        setting="the corner bakery",
        visitors="a line of lost ducklings",
        treasure="a jar of colorful marbles",
        sound="flap-flap",
        seed=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show complete_story/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show has_problem/0. "
                "#show needs_welcome/0. "
                "#show safe_plan/0. "
                "#show complete_story/0."
            )
        )
        for predicate in ("has_problem", "needs_welcome", "safe_plan", "complete_story"):
            print(asp.atoms(model, predicate))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not generate the requested number of distinct stories")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.keeper} / {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
