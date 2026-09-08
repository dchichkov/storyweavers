#!/usr/bin/env python3
"""Animal stories about a stubborn latch, honest dialogue, and friendship."""

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
    type: str
    label: str
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

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    animal: str = "Luna"
    friend: str = "Toby"
    place: str = "garden"
    latch: int = 0
    opening: int = 0
    dialogue: int = 0
    turn: int = 0
    ending: int = 0


ANIMALS = ["Luna", "Milo", "Pip", "Nora", "Clover", "Bramble"]
FRIENDS = ["Toby", "Fern", "Otis", "Mina", "Poppy", "Wren"]
PLACES = ["garden", "orchard", "barn", "meadow", "rabbit hut", "woodland shed"]

LATCHES = [
    {
        "name": "the crooked wooden latch",
        "problem": "The gate latch had slipped sideways, so the gate would not stay closed.",
        "clue": "Luna noticed a tiny pebble wedged beneath the lower hinge.",
        "action": "Luna lifted the gate while Toby pushed the pebble free and straightened the latch.",
        "result": "The gate clicked shut, and the hens could safely peck in the grass.",
        "lesson": "A small problem is easier to solve when friends look closely together.",
        "object": "wooden gate",
    },
    {
        "name": "the rusty garden latch",
        "problem": "The rusty latch stuck fast when the animals tried to open the garden gate.",
        "clue": "Toby saw that a dry leaf had curled inside the latch's narrow opening.",
        "action": "Toby held the gate steady while Luna pulled out the leaf and rubbed the latch with a little oil.",
        "result": "The latch swung smoothly, and the friends carried water to the thirsty seedlings.",
        "lesson": "Listening to a friend's observation can reveal the simplest answer.",
        "object": "garden gate",
    },
    {
        "name": "the loose barn latch",
        "problem": "A loose latch left the barn door flapping in the evening wind.",
        "clue": "Luna heard the rattle stop whenever the door was pressed against its wooden frame.",
        "action": "Luna held the door against the frame while Toby tied the latch plate firmly in place.",
        "result": "The barn grew quiet, and the sleepy goats settled down.",
        "lesson": "Friends can turn a noisy worry into a calm solution.",
        "object": "barn door",
    },
    {
        "name": "the hidden box latch",
        "problem": "A little treasure box would not open because its latch was covered with mud.",
        "clue": "Toby remembered that the stream nearby had clean water and soft reeds.",
        "action": "The friends washed the mud away with stream water, then used a reed to lift the latch gently.",
        "result": "The box opened to reveal bright buttons for the animals' play-day game.",
        "lesson": "Careful help is kinder and more useful than impatient pulling.",
        "object": "treasure box",
    },
    {
        "name": "the moonlit fence latch",
        "problem": "The fence latch glimmered in the moonlight but would not catch.",
        "clue": "Luna discovered that one side of the latch was higher than the other.",
        "action": "Toby found a flat twig, and Luna used it as a little wedge while they adjusted the latch together.",
        "result": "The fence held firm, keeping the young lambs safe beside their mother.",
        "lesson": "Good teamwork makes room for each friend's useful idea.",
        "object": "fence gate",
    },
]

OPENINGS = [
    "In the quiet {place}, {animal} the fox was getting ready for the day's work.",
    "One bright morning at the {place}, {animal} found {friend} studying an old gate.",
    "Near the {place}, {animal} heard a small click followed by a worried sigh.",
    "The animals were gathering at the {place} when {animal} noticed something was wrong.",
    "At the edge of the {place}, {animal} and {friend} planned a cheerful afternoon together.",
]

DIALOGUES = [
    "'The latch is stuck,' said {friend}. 'I tried pulling it, but it only squeaked.'",
    "'Let us not tug harder yet,' said {animal}. 'What do you notice?'",
    "'I think the gate is leaning,' said {friend}. 'Can you hold it while I look underneath?'",
    "'A good friend tells the truth kindly,' said {animal}. 'Please tell me if my idea needs changing.'",
    "'We can solve this together,' said {friend}. 'You watch the latch, and I will check the hinge.'",
]

TURNS = [
    "At first, {animal} wanted to yank the latch. Then {friend}'s careful question made {animal} pause and inspect it.",
    "{friend}'s first guess was not quite right, but {animal} listened instead of laughing. Their new plan used both ideas.",
    "The latch gave one loud clack and stayed shut. Instead of blaming each other, the friends compared what they had seen.",
    "{animal} felt embarrassed when the first try failed. {friend} said, 'A failed try is a clue,' and they began again.",
    "The two friends discovered that neither could see the whole problem alone. They moved to opposite sides and shared their observations.",
]

ENDINGS = [
    "{animal} and {friend} bumped paws beside the freshly working latch.",
    "The gate clicked softly behind them, and the friends walked home side by side.",
    "Under the warm evening sky, the repaired latch shone like a tiny silver smile.",
    "The animals cheered, but {animal} and {friend} smiled most because they had helped each other.",
    "From then on, whenever a latch made trouble, the friends listened before they pulled.",
]


ASP_RULES = r"""
#show friendship/2.
#show solved/1.

friendship(A, B) :- listens(A, B), helps(A, B).
solved(L) :- inspected(L), repaired(L).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("listens", "luna", "toby"),
            asp.fact("helps", "luna", "toby"),
            asp.fact("inspected", "latch"),
            asp.fact("repaired", "latch"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal storyworld about a latch, dialogue, and friendship."
    )
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--latch", type=int, choices=range(len(LATCHES)))
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
    animal = args.animal or rng.choice(ANIMALS)
    friend = args.friend or rng.choice(FRIENDS)
    if animal == friend:
        raise StoryError("animal and friend must have different names")
    return StoryParams(
        seed=args.seed,
        animal=animal,
        friend=friend,
        place=args.place or rng.choice(PLACES),
        latch=args.latch if args.latch is not None else rng.randrange(len(LATCHES)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal == params.friend:
        raise StoryError("animal and friend must have different names")
    if not 0 <= params.latch < len(LATCHES):
        raise StoryError("latch choice is outside the available story domain")

    world = World()
    animal = world.add(
        Entity(
            id=params.animal,
            type="fox",
            label=params.animal,
            meters={"near_latch": 1.0},
            memes={"curiosity": 1.0, "friendship": 0.5},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            type="rabbit",
            label=params.friend,
            meters={"near_latch": 1.0},
            memes={"trust": 0.7, "friendship": 0.5},
        )
    )
    latch = LATCHES[params.latch]
    common = {
        "animal": animal.label,
        "friend": friend.label,
        "place": params.place,
    }

    world.say(OPENINGS[params.opening].format(**common))
    world.say(latch["problem"])
    world.say(DIALOGUES[params.dialogue].format(**common))
    world.say(TURNS[params.turn].format(**common))
    world.say(latch["clue"])
    world.say(f"{animal.label} said, 'Thank you for telling me. Your observation matters.'")
    world.say(f"{friend.label} replied, 'And your careful paws can make the repair work.'")
    world.say(latch["action"])
    world.say(latch["result"])

    animal.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(
        animal=animal,
        friend=friend,
        place=params.place,
        latch=latch,
        inspected=True,
        repaired=True,
        solved=True,
        friendship=True,
        dialogue=True,
    )
    world.say(ENDINGS[params.ending].format(**common))

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
    latch = facts["latch"]
    animal = facts["animal"].label
    friend = facts["friend"].label
    return [
        f"Write an animal story about {animal} and {friend} repairing {latch['name']}.",
        f"Tell a child-friendly friendship story where dialogue helps {animal} and {friend} solve a latch problem.",
        f"Write a warm animal story with a clear beginning, a failed first idea, helpful conversation, and a repaired latch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    latch = facts["latch"]
    animal = facts["animal"].label
    friend = facts["friend"].label
    return [
        QAItem(
            question=f"What problem did {animal} and {friend} find?",
            answer=f"They found that {latch['problem'][0].lower() + latch['problem'][1:]}",
        ),
        QAItem(
            question=f"What clue helped {animal} and {friend}?",
            answer=latch["clue"],
        ),
        QAItem(
            question=f"How did {animal} and {friend} repair the latch?",
            answer=latch["action"],
        ),
        QAItem(
            question="How did dialogue help the friends?",
            answer=(
                f"They spoke honestly about what they noticed, listened to each other, "
                f"and combined their ideas instead of blaming one another."
            ),
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=(
                f"The {latch['object']} was secure again, and the friends' trust grew "
                f"because they solved the problem together."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a latch?",
            answer="A latch is a device that holds a door, gate, or box closed until it is moved.",
        ),
        QAItem(
            question="What makes someone a good friend?",
            answer="A good friend listens, speaks kindly, tells the truth, and helps when help is needed.",
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters share feelings and information, so their words can change what they decide or do.",
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
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts)}")
    return "\n".join(lines)


def asp_valid() -> tuple[set[tuple], set[tuple]]:
    import asp
    model = asp.one_model(asp_program("#show friendship/2.\n#show solved/1."))
    return set(asp.atoms(model, "friendship")), set(asp.atoms(model, "solved"))


def asp_verify() -> int:
    friendships, solved = asp_valid()
    if friendships == {("luna", "toby")} and solved == {("latch",)}:
        sample = generate(
            StoryParams(
                seed=1,
                animal="Luna",
                friend="Toby",
                place="garden",
                latch=0,
            )
        )
        if "latch" in sample.story.lower() and "friend" in sample.story.lower():
            print("OK: ASP parity and generated story checks passed.")
            return 0
    print("MISMATCH: ASP parity or generated story check failed.")
    return 1


CURATED = [
    StoryParams(seed=1, animal="Luna", friend="Toby", place="garden", latch=0),
    StoryParams(
        seed=2,
        animal="Clover",
        friend="Fern",
        place="orchard",
        latch=1,
        opening=1,
        dialogue=2,
        turn=1,
        ending=2,
    ),
    StoryParams(
        seed=3,
        animal="Milo",
        friend="Wren",
        place="barn",
        latch=2,
        opening=3,
        dialogue=4,
        turn=4,
        ending=4,
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
        print(asp_program("#show friendship/2.\n#show solved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        friendships, solved = asp_valid()
        print("friendship:", sorted(friendships))
        print("solved:", sorted(solved))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1
            if attempt > max(100, args.n * 50):
                raise StoryError("could not produce enough distinct story variants")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.animal} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
