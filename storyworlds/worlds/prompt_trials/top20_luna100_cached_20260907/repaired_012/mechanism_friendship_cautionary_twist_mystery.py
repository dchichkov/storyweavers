#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class MysteryWorld:
    place: str
    mechanism: str
    clue: str
    hidden_truth: str
    solved: bool = False
    trust: float = 0.0
    danger: float = 0.0
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    friend_name: str
    investigator_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nora", "Theo", "Ivy", "Sam", "Pia", "Jules"]
PLACES = [
    "the old clock tower",
    "the little museum",
    "the moonlit train station",
    "the closed garden theater",
]
MECHANISMS = [
    "a clockwork lantern",
    "a brass key machine",
    "a clicking cabinet lock",
    "a silver bell mechanism",
]


ARCS = [
    {
        "problem": "Every night, the {mechanism} clicked by itself and made a hidden door open.",
        "clue": "A smear of blue chalk appeared beside the mechanism, but it stopped just before the door.",
        "twist": "The friends discovered that the clicking was not a warning from a stranger; it was a safety device built to release trapped air.",
        "action": "They followed the chalk carefully, tested the mechanism with a wooden ruler, and opened the door together.",
        "resolution": "Inside was a small room filled with rescued books that the caretaker had hidden during a storm.",
        "ending": "The mechanism rested silently while one warm lamp shone over the books they had saved.",
        "fact_problem": "the mechanism opened a hidden door each night",
        "fact_clue": "blue chalk stopped beside the mechanism",
        "fact_twist": "the mechanism was a safety device rather than a threat",
        "fact_outcome": "the friends found rescued books and made the hidden room safe",
    },
    {
        "problem": "A brass key machine turned whenever someone whispered, then locked the front gate.",
        "clue": "The same tiny scratch appeared on every key, always facing the window.",
        "twist": "The machine was not locking people in. It was turning toward a loose roof latch that could have fallen on anyone below.",
        "action": "They kept their voices low, placed a cushion beneath the latch, and used the scratch to turn the machine toward the safe release.",
        "resolution": "The gate opened, and the loose latch was secured before it could drop.",
        "ending": "Their friendship felt stronger as the brass machine gave one gentle click and stayed still.",
        "fact_problem": "the key machine locked the front gate after whispers",
        "fact_clue": "each key had the same scratch facing the window",
        "fact_twist": "the machine was protecting people from a loose roof latch",
        "fact_outcome": "the gate opened and the dangerous latch was secured",
    },
    {
        "problem": "The silver bell rang three times whenever the friends tried to leave the station.",
        "clue": "Between the second and third rings, a small red light blinked beneath the platform.",
        "twist": "The bell was not calling a ghost. It was part of an old mechanism warning that a maintenance cart was still moving below.",
        "action": "They stopped guessing, found the inspection lever, and waited until the red light faded before crossing.",
        "resolution": "The cart rolled safely into its shed, and the station doors opened without another ring.",
        "ending": "Under the quiet moon, the bell became an ordinary bell again, and the friends walked home side by side.",
        "fact_problem": "the bell rang whenever they tried to leave",
        "fact_clue": "a red light blinked beneath the platform",
        "fact_twist": "the bell warned of a moving maintenance cart",
        "fact_outcome": "the cart reached its shed and the friends left safely",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.friend_name, params.investigator_name, params.place))
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> MysteryWorld:
    rng = _rng_for(params)
    arc = ARCS[(params.seed or rng.randrange(len(ARCS))) % len(ARCS)]
    mechanism = MECHANISMS[(params.seed or rng.randrange(len(MECHANISMS))) % len(MECHANISMS)]

    world = MysteryWorld(
        place=params.place,
        mechanism=mechanism,
        clue=arc["fact_clue"],
        hidden_truth=arc["fact_twist"],
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="friend",
            label="curious friend",
            meters={"courage": 3.0},
            memes={"trust": 2.0},
        )
    )
    investigator = world.add(
        Entity(
            id=params.investigator_name,
            kind="character",
            type="investigator",
            label="careful investigator",
            meters={"attention": 3.0},
            memes={"trust": 2.0},
        )
    )
    device = world.add(
        Entity(
            id="mechanism",
            kind="thing",
            type="mechanism",
            label=mechanism,
            meters={"power": 1.0},
            memes={"mystery": 1.0},
        )
    )

    world.say(
        f"At dusk, {friend.id} and {investigator.id} met at {params.place} because the {mechanism} had begun behaving strangely."
    )
    world.para()
    world.say(arc["problem"].format(mechanism=mechanism))
    world.para()
    world.say(
        f'"We should not touch it yet," said {investigator.id}. '
        f'"We can watch it together," replied {friend.id}. '
        "Their friendship made them careful instead of reckless."
    )
    world.para()
    world.say(arc["clue"])
    world.para()
    world.say(
        f"{friend.id} wanted to follow the first exciting idea, but {investigator.id} pointed out that the mechanism could hurt someone. "
        "They compared the clue with the sounds, lights, and marks around them."
    )
    world.para()
    world.say(arc["twist"])
    world.para()
    world.say(arc["action"])
    world.para()
    world.say(arc["resolution"])
    world.para()
    world.say(
        f"{friend.id} smiled. \"I almost blamed the wrong thing,\" they said. "
        f"{investigator.id} answered, \"And I almost forgot to listen to you.\" "
        "They solved the mystery by trusting one another and checking the danger first."
    )
    world.para()
    world.say(arc["ending"])

    world.solved = True
    world.trust = 4.0
    world.danger = 0.0
    friend.memes["trust"] = 4.0
    investigator.memes["trust"] = 4.0
    device.memes["mystery"] = 0.0
    world.facts = {
        "friend": friend.id,
        "investigator": investigator.id,
        "place": params.place,
        "mechanism": mechanism,
        "problem": arc["fact_problem"],
        "clue": arc["fact_clue"],
        "twist": arc["fact_twist"],
        "outcome": arc["fact_outcome"],
    }
    return world


def generate_prompts(world: MysteryWorld) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly mystery about a strange mechanism and two friends who investigate it carefully.",
        f"Tell a cautious mystery in which {f['friend']} and {f['investigator']} solve a puzzle at {f['place']} through friendship.",
        "Write a short mystery with a surprising but safe twist: the suspicious device is helping rather than hurting.",
    ]


def story_qa(world: MysteryWorld) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['friend']} and {f['investigator']} investigate the mystery?",
            answer=f"They investigated the strange mechanism at {f['place']}.",
        ),
        QAItem(
            question="What seemed mysterious at first?",
            answer=f"At first, {f['problem']}.",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=f"The important clue was that {f['clue']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {f['twist']}.",
        ),
        QAItem(
            question="How did friendship help solve the mystery?",
            answer=f"{f['friend']} and {f['investigator']} listened to each other, checked the danger, and worked together, so {f['outcome']}.",
        ),
    ]


def world_knowledge_qa(world: MysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, close, ring, or perform another task.",
        ),
        QAItem(
            question="Why is caution useful during a mystery?",
            answer="Caution helps people observe clues and avoid touching or changing something dangerous before they understand it.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or readers thought was true.",
        ),
        QAItem(
            question="What makes friendship helpful?",
            answer="Friendship can help people share ideas, listen honestly, and stay brave while solving a problem together.",
        ),
    ]


def dump_trace(world: MysteryWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:14} ({entity.type:12}) {' '.join(details)}")
    lines.append(f"  place={world.place}")
    lines.append(f"  mechanism={world.mechanism}")
    lines.append(f"  solved={world.solved}")
    lines.append(f"  trust={world.trust}")
    lines.append(f"  danger={world.danger}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_mystery :-
    theme(mechanism),
    feature(friendship),
    feature(cautionary),
    feature(twist),
    style(mystery),
    safe_resolution.
safe_resolution.
#show valid_mystery/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("theme", "mechanism"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("style", "mystery"),
        ]
    )


def asp_program(show: str = "#show valid_mystery/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program())
    if not any(symbol.name == "valid_mystery" for symbol in model):
        print("MISMATCH: ASP twin rejected the mystery domain.")
        return 1

    params = StoryParams("Luna", "Milo", PLACES[0], seed=17)
    sample = generate(params)
    required = ("mechanism", "friendship", "careful", "twist")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required narrative instruments.")
        return 1
    if not sample.world or not sample.world.solved or sample.world.danger != 0.0:
        print("MISMATCH: Python world did not reach a safe solved state.")
        return 1

    print("OK: ASP and Python recognize the mechanism friendship mystery.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly mystery about a mechanism, friendship, caution, and a twist."
    )
    parser.add_argument("--friend-name")
    parser.add_argument("--investigator-name")
    parser.add_argument("--place", choices=PLACES)
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
    friend = args.friend_name or rng.choice(NAMES)
    candidates = [name for name in NAMES if name != friend]
    investigator = args.investigator_name or rng.choice(candidates)
    place = args.place or rng.choice(PLACES)
    return StoryParams(
        friend_name=friend,
        investigator_name=investigator,
        place=place,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")

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
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            if models:
                print("1 compatible mystery pattern: mechanism + friendship + caution + twist")
            else:
                print("No compatible mystery pattern found.")
                raise SystemExit(1)
        except ImportError as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", PLACES[0], seed=3),
            StoryParams("Nora", "Theo", PLACES[1], seed=11),
            StoryParams("Ivy", "Sam", PLACES[2], seed=19),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
