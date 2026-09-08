#!/usr/bin/env python3
"""Mystery StoryWorld about an ambitious plan, brave questions, and repair."""

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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the lantern-lit museum",
    "the old clock tower",
    "the moonlit library",
]
CHILD_NAMES = ["Luna", "Mira", "Tavi", "Nell", "Oren", "Pip"]
FRIEND_NAMES = ["Sora", "Bea", "Kito", "Jem", "Ivy", "Sol"]
MYSTERIES = (
    {
        "id": "star_map",
        "object": "the brass star map",
        "sign": "silver footprints circled the locked display",
        "clue": "the prints stopped beside a box of moon-dust chalk",
        "truth": "the night custodian had moved the map to clean beneath its case",
        "repair": "they returned the map and placed a clear cleaning notice beside it",
        "image": "the brass stars shining through the clean glass",
    },
    {
        "id": "bell",
        "object": "the little silver bell",
        "sign": "a faint bell-note sounded behind the sealed reading room",
        "clue": "a thread of red yarn ran from the bell to a loose curtain cord",
        "truth": "a draft had tugged the cord against the bell",
        "repair": "they tied the cord safely and rehung the bell",
        "image": "the bell resting still while children read beneath it",
    },
    {
        "id": "key",
        "object": "the moon-shaped key",
        "sign": "the key vanished from its velvet cushion",
        "clue": "a trail of flour led from the cushion to the caretaker's worktable",
        "truth": "the caretaker had borrowed it to measure a tiny cabinet hinge",
        "repair": "they returned the key and labeled the worktable tools",
        "image": "the moon key gleaming on its labeled cushion",
    },
    {
        "id": "whisper",
        "object": "the whispering shell",
        "sign": "the shell whispered Luna's name after closing time",
        "clue": "a narrow echo came from the round window behind it",
        "truth": "wind was carrying a guard's name from the courtyard",
        "repair": "they moved the shell away from the window and explained the echo",
        "image": "the shell whispering only when a friend spoke into it",
    },
)

OPENINGS = (
    "At dusk, when the first lamps blinked awake",
    "On a rainy evening full of shining puddles",
    "Just before the museum doors closed",
    "When the moon rose above the quiet roof",
)
RHYME_LINES = (
    '"Seek and peek, be brave this week," Luna whispered.',
    '"Track the clue, test what is true," said Luna.',
    '"Turn the light, ask what is right," Luna declared.',
    '"Near or far, clues show where we are," sang Sora.',
)
MISUNDERSTANDINGS = (
    '"Someone took it!" Luna cried, though she had not checked the room.',
    "Luna mistook a strange sign for proof and blamed the nearest helper.",
    "A quick misunderstanding grew when Luna guessed before asking.",
    'Luna announced, "The mystery is solved," but her answer rested on one sound.',
)
BRIDGES = (
    "Sora raised a small lantern and asked everyone to describe exactly what they had seen.",
    "The friends drew the room on a scrap of paper, leaving guesses outside the map.",
    "They paused beside the doorway and compared the time, the marks, and the direction.",
    "Bravery did not mean charging ahead; it meant asking a difficult question kindly.",
)


@dataclass
class Entity:
    id: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    child_name: str
    friend_name: str
    mystery_id: str
    opening_id: int = 0
    rhyme_id: int = 0
    misunderstanding_id: int = 0
    bridge_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery StoryWorld about ambition, rhyme, bravery, and misunderstanding."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--mystery-id", choices=[m["id"] for m in MYSTERIES])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser


def mystery_for(identifier: str) -> dict:
    for mystery in MYSTERIES:
        if mystery["id"] == identifier:
            return mystery
    raise StoryError(f"Unknown mystery: {identifier}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child_name or rng.choice(CHILD_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != child]
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        child_name=child,
        friend_name=args.friend_name or rng.choice(friend_choices),
        mystery_id=args.mystery_id or rng.choice([m["id"] for m in MYSTERIES]),
        opening_id=rng.randrange(len(OPENINGS)),
        rhyme_id=rng.randrange(len(RHYME_LINES)),
        misunderstanding_id=rng.randrange(len(MISUNDERSTANDINGS)),
        bridge_id=rng.randrange(len(BRIDGES)),
    )


def tell(params: StoryParams) -> World:
    mystery = mystery_for(params.mystery_id)
    world = World(params.place)
    child = world.add(
        Entity(
            id="child",
            type="person",
            label=params.child_name,
            role="ambitious young detective",
            meters={"curiosity": 1.0, "bravery": 0.4},
            memes={"confidence": 0.5, "trust": 0.8},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            type="person",
            label=params.friend_name,
            role="careful friend",
            meters={"attention": 1.0, "patience": 1.0},
            memes={"trust": 0.8, "courage": 0.7},
        )
    )
    world.add(Entity(id="mystery_object", type="artifact", label=mystery["object"]))
    world.facts.update(
        mystery=mystery,
        child=child,
        friend=friend,
        solved=False,
        misunderstanding=True,
        brave_question=False,
    )

    world.say(
        f"{OPENINGS[params.opening_id]}, {child.label} entered {params.place} with an ambitious plan."
    )
    world.say(
        f"{child.label} wanted to solve one mystery before the last lamp went dark, while {friend.label} carried a notebook and a stubby pencil."
    )
    world.say(
        f"The mystery began when {mystery['sign']}. The room became quiet enough to hear rain tapping the roof."
    )
    world.para()

    world.say(f"{MISUNDERSTANDINGS[params.misunderstanding_id]}")
    world.say(
        f'"Wait," said {friend.label}. "A misunderstanding is not evidence. What do we actually know?"'
    )
    world.say(
        f'"We know the sign, but not its cause," {child.label} admitted. "I was rushing because my plan felt important."'
    )
    world.say(
        f"{child.label} felt embarrassed, yet chose bravery over a loud guess. {BRIDGES[params.bridge_id]}"
    )
    world.say(RHYME_LINES[params.rhyme_id])
    world.facts["brave_question"] = True
    child.meters["bravery"] = 1.0
    child.memes["humility"] = 1.0
    world.para()

    world.say(
        f"First they checked the lock, then the floor, then the nearby shelves. At last, {mystery['clue']}."
    )
    world.say(
        f"{friend.label} pointed to the mark. 'This clue tells us where to look next,' they said."
    )
    world.say(
        f"Behind the next door they discovered that {mystery['truth']}."
    )
    world.say(
        f"{child.label} took a slow breath. 'I blamed someone without asking. I am sorry.'"
    )
    world.say(
        f"{friend.label} answered, 'You changed the mystery by listening. Now let us repair what the guess disturbed.'"
    )
    world.facts["cause"] = mystery["truth"]
    world.facts["solved"] = True
    world.facts["misunderstanding"] = False
    child.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    world.para()

    world.say(f"Together they {mystery['repair']}.")
    world.say(
        f"The ambitious plan became better than a quick answer: it became a careful search that left the room safer and kinder."
    )
    world.say(
        f"Before they left, {child.label} wrote, 'A mystery needs a clue, a question, and the bravery to change your mind.'"
    )
    world.say(
        f"They walked home beneath the rain, while {mystery['image']}. The misunderstanding was gone, and their friendship was stronger than the mystery."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    child = world.facts["child"].label
    return [
        f"Write a child-friendly mystery about ambitious {child} investigating {mystery['object']}.",
        "Include a rhyme, a brave question, and a misunderstanding that is repaired with evidence.",
        f"End with an image proving that {mystery['truth']} and that trust returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery = world.facts["mystery"]
    child = world.facts["child"].label
    friend = world.facts["friend"].label
    return [
        QAItem(
            question=f"What ambitious mystery did {child} try to solve?",
            answer=f"{child} tried to discover why {mystery['sign']}, involving {mystery['object']}."
        ),
        QAItem(
            question="What misunderstanding happened?",
            answer=f"The misunderstanding was that the strange sign was treated as proof of blame before anyone checked its cause."
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The important clue was that {mystery['clue']}. It pointed the friends toward the real explanation."
        ),
        QAItem(
            question=f"How did {friend} help?",
            answer=f"{friend} asked what the friends truly knew, encouraged careful checking, and helped follow the clue instead of accepting a quick guess."
        ),
        QAItem(
            question="How did bravery change the ending?",
            answer=f"Bravery helped the child admit the mistake, apologize, and repair the problem after learning that {mystery['truth']}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a mistaken idea caused by incomplete or confusing information. Asking questions can correct it."
        ),
        QAItem(
            question="What does bravery mean in this story?",
            answer="Bravery means asking an honest question, facing embarrassment, and changing your mind when evidence shows that your first guess was wrong."
        ),
        QAItem(
            question="Why are clues useful in a mystery?",
            answer="Clues are details that help investigators test possible explanations. A good clue narrows the search without becoming proof all by itself."
        ),
        QAItem(
            question="How can an ambitious plan stay kind?",
            answer="It can stay kind by making room for safety, careful listening, and respect for people who may be affected by the investigation."
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("solved", "misunderstanding", "brave_question", "cause"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "mystery_place"),
            asp.fact("feature", "rhyme"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("quality", "ambitious"),
            asp.fact("resolution", "repair"),
        ]
    )


ASP_RULES = """
valid_story :-
    setting(mystery_place),
    feature(rhyme),
    feature(bravery),
    feature(misunderstanding),
    quality(ambitious),
    resolution(repair).
#show valid_story/0.
""".strip()


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the mystery story.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts["solved"]:
            print("Mismatch: Python story did not resolve its mystery.")
            return 1
        if "bravery" not in sample.story.lower() and "brave" not in sample.story.lower():
            print("Mismatch: Python story omitted bravery.")
            return 1
    print("OK: ASP and Python accepted the repaired mystery story.")
    return 0


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="the lantern-lit museum",
        child_name="Luna",
        friend_name="Sora",
        mystery_id="star_map",
        opening_id=0,
        rhyme_id=0,
        misunderstanding_id=0,
        bridge_id=0,
    ),
    StoryParams(
        place="the old clock tower",
        child_name="Mira",
        friend_name="Kito",
        mystery_id="bell",
        opening_id=2,
        rhyme_id=1,
        misunderstanding_id=2,
        bridge_id=2,
    ),
    StoryParams(
        place="the moonlit library",
        child_name="Tavi",
        friend_name="Bea",
        mystery_id="key",
        opening_id=3,
        rhyme_id=2,
        misunderstanding_id=3,
        bridge_id=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        print("compatible story:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
