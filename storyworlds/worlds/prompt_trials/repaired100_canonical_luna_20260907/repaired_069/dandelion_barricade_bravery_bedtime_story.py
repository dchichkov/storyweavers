#!/usr/bin/env python3
"""A gentle bedtime storyworld about a dandelion barricade and quiet bravery."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    friend: str = "Milo"
    place: str = "the moonlit garden"
    challenge: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0


NAMES = ["Luna", "Nora", "Mira", "Tess", "Ivy", "Wren"]
FRIENDS = ["Milo", "Pip", "Sage", "Theo", "Fern", "Bram"]
PLACES = [
    "the moonlit garden",
    "the quiet hillside",
    "the little village green",
    "the sleepy meadow",
    "the cottage garden",
]

CHALLENGES = [
    {
        "title": "the midnight path",
        "problem": "A cool night wind had pushed dry leaves across the garden path, and the smallest mice could no longer find their way home.",
        "barricade": "Luna built a low barricade from fallen twigs and dandelion stems to guide them around the slippery leaves.",
        "clue": "She noticed that the dandelions bent toward the warm stone wall, making a bright golden line beside the safe path.",
        "action": "Together, Luna and Milo tucked the stems into the soil and placed smooth pebbles along the turns.",
        "result": "Soon the mice followed the little line of yellow flowers safely to their warm nests.",
        "lesson": "Bravery can be quiet: it may look like taking one careful step and helping someone else.",
        "object": "dandelion stems",
        "ending": "By the time the moon reached the chimney, the dandelion barricade glowed like a tiny fence of stars.",
    },
    {
        "title": "the sleepy stream",
        "problem": "Rainwater had spilled over the bank and rushed toward a nest of ducklings resting near the stream.",
        "barricade": "Luna made a soft barricade from dandelion leaves, reeds, and little branches.",
        "clue": "She saw that the water slowed whenever it met a patch of thick grass.",
        "action": "Luna and Milo copied the grass's shape, weaving the dandelion leaves tightly and pressing mud around the edges.",
        "result": "The water curved away from the nest and became a quiet ribbon under the moon.",
        "lesson": "Bravery is not the absence of worry; it is caring enough to act while worry is still there.",
        "object": "dandelion leaves",
        "ending": "The ducklings slept beside the stream while the small green barricade held firm.",
    },
    {
        "title": "the garden gate",
        "problem": "The old garden gate had fallen open, and a gust was carrying seed packets into the dark.",
        "barricade": "Luna placed a dandelion barricade beneath the gate so it would rest against something soft instead of slamming shut.",
        "clue": "She heard the gate creak most when the wind came from the north.",
        "action": "She and Milo leaned the strongest stems toward the north and weighted them with three round stones.",
        "result": "The gate stayed open just wide enough for the gardener to gather the seeds.",
        "lesson": "A brave heart listens closely before it chooses what to do.",
        "object": "dandelion stems",
        "ending": "The last seed packet rested safely beneath the quiet gate.",
    },
    {
        "title": "the firefly crossing",
        "problem": "Fireflies had gathered on one side of a puddle, but the youngest glow-worms were afraid to cross.",
        "barricade": "Luna arranged dandelion stalks as a tiny barricade around the deepest water.",
        "clue": "She found a shallow place where flat stones made a stepping path.",
        "action": "Luna spoke softly to the glow-worms while Milo set dandelion stems along the dangerous edge.",
        "result": "The fireflies crossed one by one, blinking at every safe step.",
        "lesson": "Bravery grows when a kind friend makes room for fear and still keeps going.",
        "object": "dandelion stalks",
        "ending": "The fireflies rose together, and their lights floated above the dandelion barricade.",
    },
]


OPENINGS = [
    "At bedtime, {child} looked out from the cottage window and saw {place}.",
    "The evening star appeared above {place}, where {child} was putting away the garden things.",
    "When the house grew quiet, {child} heard a small sound outside {place}.",
    "Under a round silver moon, {child} and {friend} tiptoed into {place}.",
    "The world was settling down to sleep when {child} noticed something unusual near {place}.",
]

DIALOGUES = [
    "'I feel a little afraid,' said {child}. 'Then we can be careful together,' answered {friend}.",
    "'What if the wind ruins our plan?' whispered {child}. '{possessive} plan can change when we learn more,' said {friend}.",
    "'I do not feel brave yet,' said {child}. '{possessive} first step can still be brave,' replied {friend}.",
    "'Should we wake the gardener?' asked {child}. 'Let's make the path safe first, then ask for help,' said {friend}.",
]

ENDINGS = [
    "When the work was done, {child} felt the worry loosen like a knot in a ribbon.",
    "The night did not become noiseless, but {child} no longer mistook every sound for danger.",
    "{friend} smiled, and {child} discovered that courage could be gentle and small.",
    "The moon watched over them, and both friends knew they had been brave in their own quiet way.",
]


ASP_RULES = r"""
#show brave/1.
#show guides/2.
brave(C) :- cares(C), acts(C).
guides(C, P) :- brave(C), protects(C, P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("cares", "child"),
            asp.fact("acts", "child"),
            asp.fact("protects", "child", "path"),
        ]
    )


def asp_program(show: str = "#show brave/1.\n#show guides/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about a dandelion barricade and bravery."
    )
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--challenge", type=int, choices=range(len(CHALLENGES)))
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
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
        challenge=args.challenge if args.challenge is not None else rng.randrange(len(CHALLENGES)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if params.child == params.friend:
        raise StoryError("The child and friend must have different names.")
    if not params.place:
        raise StoryError("A bedtime story needs a place.")
    if not 0 <= params.challenge < len(CHALLENGES):
        raise StoryError("The selected challenge is not available.")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    challenge = CHALLENGES[params.challenge]

    world = World()
    child = world.add(Entity(id=params.child, type="child", label=params.child))
    friend = world.add(Entity(id=params.friend, type="friend", label=params.friend))
    dandelion = world.add(Entity(id="dandelion", type="plant", label="dandelion"))
    barricade = world.add(Entity(id="barricade", type="structure", label="dandelion barricade"))

    child.meters.update(balance=1.0, carefulness=0.9)
    child.memes.update(bravery=0.2, concern=0.8)
    friend.memes.update(kindness=1.0, courage=0.8)
    dandelion.meters.update(stems=1.0, softness=0.9)
    barricade.meters.update(stability=0.0, protection=0.0)

    possessive = "Your" if friend.id in {"Milo", "Pip", "Theo", "Bram"} else "A"
    substitutions = {
        "{child}": child.id,
        "{friend}": friend.id,
        "{place}": params.place,
        "{possessive}": possessive,
    }

    def fill(text: str) -> str:
        for key, value in substitutions.items():
            text = text.replace(key, value)
        return text

    world.say(fill(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(challenge["problem"])
    world.say(
        f"Near the path stood a tall dandelion, its pale seeds trembling in the night air."
    )
    world.say(fill(DIALOGUES[params.dialogue % len(DIALOGUES)]))
    world.say(challenge["clue"])
    world.say(challenge["barricade"])
    world.say(challenge["action"])

    barricade.meters["stability"] = 1.0
    barricade.meters["protection"] = 1.0
    child.memes["bravery"] = 1.0
    child.memes["concern"] = 0.1
    world.facts.update(
        child=child,
        friend=friend,
        dandelion=dandelion,
        barricade=barricade,
        place=params.place,
        challenge=challenge,
        solved=True,
        bravery=True,
    )

    world.say(challenge["result"])
    world.say(fill(ENDINGS[params.ending % len(ENDINGS)]))
    world.say(f"That night, {child.id} learned: {challenge['lesson']}")
    world.say(challenge["ending"])
    world.say(
        f"Then {child.id} and {friend.id} went inside, where the blankets were warm and the moon kept watch."
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    child = facts["child"]
    challenge = facts["challenge"]
    return [
        f"Write a gentle bedtime story about {child.id} facing {challenge['title']} with a dandelion barricade.",
        f"Tell a child-friendly story where a small act of bravery protects a nighttime path.",
        "Write a quiet bedtime tale with spoken dialogue, a dandelion, a barricade, and a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    friend = facts["friend"]
    challenge = facts["challenge"]
    return [
        QAItem(
            question=f"What problem did {child.id} notice?",
            answer=challenge["problem"],
        ),
        QAItem(
            question=f"How did {child.id} use the dandelion?",
            answer=challenge["barricade"],
        ),
        QAItem(
            question=f"How did {friend.id} help?",
            answer=challenge["action"],
        ),
        QAItem(
            question="What did the barricade change?",
            answer=challenge["result"],
        ),
        QAItem(
            question="What did the child learn about bravery?",
            answer=f"{challenge['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dandelion?",
            answer="A dandelion is a flowering plant with a bright yellow flower and seed heads that can carry seeds on the wind.",
        ),
        QAItem(
            question="What is a barricade?",
            answer="A barricade is a barrier placed to block, protect, or guide people and animals.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing what is caring or right even when you feel worried or afraid.",
        ),
        QAItem(
            question="Why can bedtime stories feel comforting?",
            answer="Bedtime stories use gentle words, familiar patterns, and safe endings to help a listener feel calm before sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:9}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show guides/2."))
    return set(asp.atoms(model, "brave")) | set(asp.atoms(model, "guides"))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show guides/2."))
    brave = set(asp.atoms(model, "brave"))
    guides = set(asp.atoms(model, "guides"))
    if brave == {("child",)} and guides == {("child", "path")}:
        print("OK: ASP bravery and protection match the Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("  ASP brave:", sorted(brave))
    print("  ASP guides:", sorted(guides))
    return 1


CURATED = [
    StoryParams(
        seed=1,
        child="Luna",
        friend="Milo",
        place="the moonlit garden",
        challenge=0,
        opening=0,
        dialogue=2,
        ending=0,
    ),
    StoryParams(
        seed=2,
        child="Nora",
        friend="Sage",
        place="the sleepy meadow",
        challenge=1,
        opening=3,
        dialogue=0,
        ending=2,
    ),
    StoryParams(
        seed=3,
        child="Mira",
        friend="Theo",
        place="the cottage garden",
        challenge=3,
        opening=4,
        dialogue=1,
        ending=3,
    ),
]


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
        sys.exit(asp_verify())

    if args.asp:
        facts = sorted(asp_valid())
        print(f"{len(facts)} ASP-derived bravery facts")
        for item in facts:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.child}: dandelion barricade"
        elif len(samples) > 1:
            header = f"### bedtime story variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
