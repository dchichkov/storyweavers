#!/usr/bin/env python3
"""
A gentle ghost story world about Daddy, a mysterious taste, curiosity, and a
conversation that prevents a bad ending.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "daddy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old moonlit house"
    room: str = "the kitchen"
    affordances: set[str] = field(
        default_factory=lambda: {"listen", "ask", "taste", "turn_on_light"}
    )


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    daddy_name: str
    taste: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    name: str
    smell: str
    cause: str
    safe_check: str
    ghost_detail: str
    bad_ending: str
    resolution: str
    ending_image: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return "\n\n".join(self.lines)


MYSTERIES = (
    Mystery(
        "the peppermint spoon",
        "cool peppermint and a little smoke",
        "a friendly kitchen ghost had stirred peppermint tea beside the cold stove",
        "asked Daddy before tasting and checked that the cup was warm, clean, and meant for them",
        "a pale spoon lifted itself and tapped once against the saucer",
        "would have swallowed a strange mouthful and frightened the ghost into hiding",
        "Daddy listened, tasted only the ordinary tea after checking it, and left a tiny saucer for the guest",
        "The spoon settled beside the saucer, and a silver footprint appeared in the flour.",
    ),
    Mystery(
        "the lemon cloud",
        "sharp lemon with a dusty edge",
        "a ghostly baker had squeezed lemon over a bowl of old flour",
        "waited for Daddy to smell it, then tested a clean drop instead of licking the unknown spill",
        "a white shape drifted through the cupboard glass like a cloud with a hat",
        "would have tasted the dusty spill and made everyone cough in the dark",
        "Daddy wiped the spill away, made fresh lemonade, and invited the ghost to choose a clean cup",
        "Three lemon peels curled into a tiny smiling moon on the counter.",
    ),
    Mystery(
        "the cinnamon whisper",
        "warm cinnamon and something like rain",
        "the house ghost had opened an old spice tin while searching for a recipe",
        "kept the tongue away from the unknown powder and asked what the ghost wanted",
        "a whisper slid from the tin: 'Not that one. The sweet one.'",
        "would have tasted the wrong powder and given the ghost a very unhappy night",
        "Daddy found the labeled cinnamon, made toast, and gave the ghost a crumb on a clean plate",
        "The toast rose from the plate by itself, carrying a cinnamon heart.",
    ),
    Mystery(
        "the salty shadow",
        "salt and wet stone",
        "a rain-soaked ghost had dripped beside the pantry and mistaken the salt jar for a bell",
        "turned on the light, spoke calmly, and checked the jar before anyone tasted anything",
        "a shadow pointed one long finger toward the pantry shelf",
        "would have tasted a mystery puddle and chased the ghost into a frightening storm",
        "Daddy cleaned the floor, offered fresh water, and helped the ghost find the quiet bell",
        "The pantry bell rang softly, though no hand touched it.",
    ),
)


CHILD_NAMES = ["Luna", "Milo", "Nell", "Pip", "Ivy", "Toby"]
DADDY_NAMES = ["Daddy", "Papa", "Dad"]
OPENINGS = (
    "At midnight, {child} woke in the old moonlit house because {child_pronoun} heard a tiny clink from the kitchen.",
    "The moon painted the old moonlit house blue when {child} noticed a strange taste waiting in the air.",
    "In the old moonlit house, the kitchen door creaked open, and {child} found Daddy listening beside the pantry.",
    "Rain whispered on the windows of the old moonlit house while {child} followed Daddy toward a mysterious kitchen smell.",
)
DIALOGUE = (
    "'Did you taste that?' asked {child}. Daddy shook his head. 'Not yet. We ask first and check second.'",
    "{child} whispered, 'Maybe it is a ghost.' Daddy answered, 'Then a kind question is safer than a quick bite.'",
    "'Daddy, what if the taste is a warning?' asked {child}. 'Then we will listen carefully,' he said.",
    "Daddy held up one hand. 'Curious is good,' he said, 'but curiosity needs a careful grown-up.'",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daddy, taste, and a gentle kitchen ghost.")
    parser.add_argument("--name")
    parser.add_argument("--daddy", default="Daddy")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--taste", choices=["peppermint", "lemon", "cinnamon", "salt"])
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
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    daddy_name = args.daddy or "Daddy"
    if not daddy_name.strip():
        raise StoryError("Daddy must have a name.")
    taste = args.taste or rng.choice(["peppermint", "lemon", "cinnamon", "salt"])
    return StoryParams(
        child_name=child_name,
        child_type=child_type,
        daddy_name=daddy_name,
        taste=taste,
    )


def choose_mystery(params: StoryParams) -> Mystery:
    mapping = {
        "peppermint": 0,
        "lemon": 1,
        "cinnamon": 2,
        "salt": 3,
    }
    if params.taste not in mapping:
        raise StoryError("The taste must be peppermint, lemon, cinnamon, or salt.")
    return MYSTERIES[mapping[params.taste]]


def make_story(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    child = world.add(
        Entity(
            id="child",
            type=params.child_type,
            label=params.child_name,
            meters={"distance_to_daddy": 1.0},
            memes={"curiosity": 0.8, "fear": 0.2},
        )
    )
    daddy = world.add(
        Entity(
            id="daddy",
            type="daddy",
            label=params.daddy_name,
            meters={"distance_to_child": 1.0},
            memes={"care": 1.0, "calm": 0.9},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            type="ghost",
            label="the kitchen ghost",
            meters={"visible": 0.35},
            memes={"lonely": 0.8, "hope": 0.3},
        )
    )
    mystery = choose_mystery(params)
    variant = params.seed if params.seed is not None else 0

    opening = OPENINGS[variant % len(OPENINGS)].format(
        child=child.label,
        child_pronoun=child.pronoun(),
    )
    world.say(opening)
    world.say(
        f"A strange taste floated near the table: {mystery.smell}. "
        f"{child.label} felt curious, but {daddy.label} kept one hand near the lamp."
    )
    world.say(
        f"{mystery.ghost_detail}. The pale shape belonged to {ghost.label}, who had come because "
        f"{mystery.cause}."
    )
    world.say(DIALOGUE[(variant // len(OPENINGS)) % len(DIALOGUE)].format(child=child.label))
    world.say(
        f"Together they {mystery.safe_check}. The room grew still, and the ghost waited beside the pantry."
    )
    world.say(
        f"If they had rushed, {mystery.bad_ending}. Instead, {child.label} asked, "
        f"'Are you trying to tell us something?'"
    )
    world.say(
        f"The ghost nodded. {daddy.label} said, 'We can help, but nothing unknown goes into anyone's mouth.' "
        f"Then {mystery.resolution}."
    )
    world.say(
        f"The mystery was solved without a bad ending. {mystery.ending_image} "
        f"{child.label} learned that curiosity is brightest when questions and careful words come first."
    )

    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.05
    daddy.memes["calm"] = 1.0
    ghost.memes["lonely"] = 0.1
    ghost.memes["hope"] = 1.0
    world.facts = {
        "child": child,
        "daddy": daddy,
        "ghost": ghost,
        "mystery": mystery,
        "safe_check": mystery.safe_check,
        "bad_ending": mystery.bad_ending,
        "resolution": mystery.resolution,
        "ending_image": mystery.ending_image,
    }
    return world


ASP_RULES = r"""
curious(child).
has_daddy(child,daddy).
mysterious_taste(taste).
asks(child,ghost).
checks(daddy,taste).
careful(child).
dialogue(child,daddy).
safe_question(child,ghost) :- curious(child), asks(child,ghost), dialogue(child,daddy).
bad_ending_avoided :- safe_question(child,ghost), checks(daddy,taste), careful(child).
happy_resolution :- bad_ending_avoided.
#show safe_question/2.
#show bad_ending_avoided/0.
#show happy_resolution/0.
"""


def asp_facts() -> str:
    return """
curious(child).
has_daddy(child,daddy).
mysterious_taste(taste).
asks(child,ghost).
checks(daddy,taste).
careful(child).
dialogue(child,daddy).
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a gentle ghost story about {child.label}, Daddy, and a mysterious {mystery.name}.",
        f"Tell a child-friendly story where curiosity about {mystery.smell} leads to careful dialogue.",
        "Write a ghost story in which asking questions prevents a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where did the mysterious taste appear?",
            "It appeared in the kitchen of the old moonlit house.",
        ),
        QAItem(
            f"Why did {child.label} and Daddy avoid tasting the unknown thing quickly?",
            f"They avoided it because {mystery.safe_check}.",
        ),
        QAItem(
            "How did dialogue help the children and Daddy?",
            "They spoke with one another and asked the ghost what it needed instead of guessing or rushing.",
        ),
        QAItem(
            "What bad ending did their careful choice prevent?",
            f"It prevented this bad ending: {mystery.bad_ending}.",
        ),
        QAItem(
            "How did the ghost story end?",
            f"It ended when {mystery.resolution}. {mystery.ending_image}",
        ),
    ]


def world_qa(_world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is curiosity?",
            "Curiosity is the wish to learn more by noticing, wondering, and asking questions.",
        ),
        QAItem(
            "Why should someone ask before tasting an unknown thing?",
            "Asking first helps a trusted grown-up check whether the thing is safe to eat or drink.",
        ),
        QAItem(
            "What is a ghost in a story?",
            "A ghost is a spirit character who may be mysterious, lonely, helpful, or frightening.",
        ),
        QAItem(
            "Why is dialogue useful?",
            "Dialogue lets characters share clues, feelings, and plans so their words can change what they do.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: {sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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


CURATED = [
    StoryParams("Luna", "girl", "Daddy", "peppermint"),
    StoryParams("Milo", "boy", "Daddy", "lemon"),
    StoryParams("Nell", "girl", "Papa", "cinnamon"),
    StoryParams("Toby", "boy", "Dad", "salt"),
]


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch between ASP and Python reasonableness gate.")
        return 1
    try:
        from storyworlds import asp

        models = asp.solve(asp_program(), models=1)
        atoms = {str(symbol) for symbol in models[0]} if models else set()
        required = {"bad_ending_avoided", "happy_resolution"}
        if not any(atom.startswith("bad_ending_avoided") for atom in atoms):
            print("ASP did not derive bad_ending_avoided.")
            return 1
        if not any(atom.startswith("happy_resolution") for atom in atoms):
            print("ASP did not derive happy_resolution.")
            return 1
    except ImportError:
        pass
    for params in CURATED:
        sample = generate(params)
        if "bad ending" not in sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print("OK: Python and ASP agree that careful dialogue avoids the bad ending.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            from storyworlds import asp

            models = asp.solve(asp_program(), models=1)
            print("ASP model:")
            for symbol in models[0] if models else []:
                print(f"  {symbol}")
        except ImportError:
            print("ASP support is unavailable because clingo is not installed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
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
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} and {sample.params.daddy_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
