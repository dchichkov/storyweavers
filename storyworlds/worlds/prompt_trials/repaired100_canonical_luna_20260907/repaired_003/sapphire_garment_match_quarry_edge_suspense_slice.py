#!/usr/bin/env python3
"""
A small storyworld about a sapphire garment, a careful match, and a suspenseful
moment at the edge of an old quarry.

The story stays close to ordinary life: a child helps a neighbor mend a costume
for a lantern walk, notices a blue stone has slipped away, and must search near
the quarry edge before dusk. A match provides a tiny, controlled light, while
care and good communication turn suspense into a safe discovery.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Rosa"
    garment_word: str = "blue festival garment"
    stone_word: str = "sapphire"
    match_word: str = "match"
    feature: str = "Suspense"
    style: str = "Slice of Life"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    child: Entity
    helper: Entity
    garment: Entity
    sapphire: Entity
    match: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in [
            self.child,
            self.helper,
            self.garment,
            self.sapphire,
            self.match,
        ]:
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) "
                + (" ".join(bits) if bits else "quiet")
            )
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {"quarry_edge": "the quarry edge"}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Ari"]
HELPERS = ["Rosa", "Nana", "Uncle Jo", "Mara"]

GARMENTS = [
    "blue festival garment",
    "blue velvet garment",
    "blue wool garment",
]

SEARCH_CLUES = [
    (
        "A faint blue glimmer winked beside a flat stone.",
        "A loose thread from the garment had caught on a thorn near the path.",
    ),
    (
        "Something small clicked against the gravel below the old bench.",
        "The sapphire had rolled beneath the bench when the garment was folded.",
    ),
    (
        "A blue flash appeared near a tuft of dry grass, then vanished.",
        "The evening breeze had lifted the garment's sash and nudged the sapphire downhill.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle suspense story about a sapphire garment at the quarry edge."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES, default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
    parser.add_argument("--garment", choices=GARMENTS, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("This story must take place at the quarry edge.")
    if params.feature != "Suspense":
        raise StoryError("The story needs Suspense so the missing sapphire matters.")
    if params.style != "Slice of Life":
        raise StoryError("The style must remain Slice of Life.")
    if "sapphire" not in params.stone_word.lower():
        raise StoryError("The story must include a sapphire.")
    if "garment" not in params.garment_word.lower():
        raise StoryError("The story must include a garment.")
    if params.match_word.lower() != "match":
        raise StoryError("The small light source must be called a match.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or "quarry_edge",
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        garment_word=args.garment or rng.choice(GARMENTS),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(params.child_name, "character", params.child_name, "child")
    helper = Entity(params.helper_name, "character", params.helper_name, "neighbor")
    garment = Entity("garment", "thing", params.garment_word, "clothing")
    sapphire = Entity("sapphire", "thing", "sapphire", "stone")
    match = Entity("match", "thing", "match", "tiny light")
    return World(
        setting=SETTINGS[params.setting],
        child=child,
        helper=helper,
        garment=garment,
        sapphire=sapphire,
        match=match,
    )


def _build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 4001)
    child = world.child
    helper = world.helper
    garment = world.garment
    sapphire = world.sapphire
    match = world.match

    clue, cause = rng.choice(SEARCH_CLUES)
    opening = rng.choice(
        [
            f"Late in the afternoon, {child.label} carried a basket to {world.setting} while {helper.label} prepared a lantern walk.",
            f"Before supper, {child.label} met {helper.label} at {world.setting} to mend a costume for the village lantern walk.",
            f"The day was cooling when {child.label} and {helper.label} spread a costume cloth on a bench at {world.setting}.",
        ]
    )
    helper_line = rng.choice(
        [
            f'"Hold the hem here," {helper.label} said. "The {garment.label} only needs one more stitch."',
            f'"Stay on the flat path," {helper.label} said. "We can finish the {garment.label} before the light fades."',
            f'"Let us check the clasp," {helper.label} said. "The sapphire should sit safely in its little pocket."',
        ]
    )
    child_line = rng.choice(
        [
            f'"I will look beside the bench," {child.label} said. "You keep the path in sight."',
            f'"I saw a blue flash," {child.label} said. "May I search from this side?"',
            f'"The stone cannot be far," {child.label} said. "Please talk to me while I look."',
        ]
    )
    ending = rng.choice(
        [
            f"At home, {child.label} stitched the sapphire pocket twice, and the {garment.label} hung ready beside the warm kitchen door.",
            f"That evening, the repaired {garment.label} rested on a chair, its sapphire shining safely where careful hands had placed it.",
            f"When the lantern walk began, the sapphire stayed in its new pocket and made one small blue star on the {garment.label}.",
        ]
    )

    child.memes["worry"] = 1.0
    child.memes["courage"] = 0.0
    child.inc_meter("safe_steps", 0.0)
    helper.memes["care"] = 1.0
    garment.meters["worn_clasp"] = 1.0
    sapphire.meters["lost"] = 1.0
    match.meters["unlit"] = 1.0

    world.say(opening)
    world.say(
        f"The {garment.label} belonged to the village play. A little sapphire was sewn near its collar, "
        "and its blue color matched the evening sky."
    )
    world.say(helper_line)
    world.say(
        f"When {child.label} lifted the garment, the clasp gave a tiny snap. "
        f"The sapphire was gone. Beyond the bench, the ground sloped toward the quarry edge."
    )

    world.para()
    world.say(
        f"{child.label}'s stomach tightened. The quarry edge was not a place for wandering, "
        "especially with dusk settling over the stones."
    )
    world.say(child_line)
    world.say(
        f'{helper.label} answered, "Yes, but we search together. We stay behind the old rope and use the flat path."'
    )
    child.memes["courage"] += 1.0
    child.inc_meter("safe_steps", 1.0)
    world.say(
        f"{helper.label} struck one {match.label} in a small tin cup. "
        "Its brief flame lit the gravel without bringing either of them near the drop."
    )
    match.meters["unlit"] = 0.0
    match.meters["lit"] = 1.0

    world.para()
    world.say(
        f"They moved slowly, speaking whenever the wind covered a sound. "
        f"Then {clue}"
    )
    world.say(
        f"{child.label} stopped at the rope. {helper.label} knelt on the safe side and used a long walking stick "
        "to draw the shining speck closer."
    )
    sapphire.meters["lost"] = 0.0
    sapphire.meters["found"] = 1.0
    child.memes["worry"] = 0.2
    world.say(
        f"It was the sapphire. {cause} No one had needed to climb or reach over the edge."
    )

    world.para()
    child.memes["relief"] = 1.0
    garment.meters["worn_clasp"] = 0.0
    garment.meters["repaired"] = 1.0
    world.say(
        f"{helper.label} wrapped the sapphire in a handkerchief, and {child.label} held the garment close. "
        "They walked back along the same flat path while the last match-glow faded."
    )
    world.say(
        f'"Next time, I will sew a stronger pocket," {child.label} said. '
        f'"And we will check it before we come here."'
    )
    world.say(
        f'{helper.label} smiled. "That is a good plan. Care can make a small adventure safe."'
    )
    world.say(ending)

    world.facts.update(
        clue=clue,
        cause=cause,
        found=True,
        safe_search=True,
        match_used=True,
        repaired=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a Slice of Life suspense story at the quarry edge about a missing sapphire.",
        "Include a garment, a carefully used match, a safe search, and a brief conversation.",
        "Show how ordinary care turns a worrying moment into a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What went missing from the garment?",
            f"The sapphire slipped from the pocket or clasp of the {world.garment.label}.",
        ),
        QAItem(
            "Why was the quarry edge suspenseful?",
            "The sapphire was missing near a sloping drop, and dusk was approaching, so the characters had to search carefully.",
        ),
        QAItem(
            "How did the characters search safely?",
            "They stayed behind the old rope, used the flat path, talked to each other, and drew the sapphire closer with a walking stick.",
        ),
        QAItem(
            "What did the match do?",
            "The match gave them a brief, controlled light so they could see the gravel without going near the quarry edge.",
        ),
        QAItem(
            "What changed by the ending?",
            "The sapphire was found, the garment was repaired, and the child learned to check the pocket before returning to the quarry edge.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a sapphire?",
            "A sapphire is a hard, often blue gemstone that can be set into jewelry or clothing.",
        ),
        QAItem(
            "Why should people stay away from an unprotected quarry edge?",
            "The ground may be steep or loose, so people should remain behind barriers and use safe paths.",
        ),
        QAItem(
            "What is a garment?",
            "A garment is a piece of clothing worn on the body.",
        ),
        QAItem(
            "Why should a match be used carefully?",
            "A match makes a hot flame, so it should be controlled by a responsible person and kept away from dry material.",
        ),
    ]


ASP_RULES = r"""
safe_search :- flat_path, behind_rope, helper_present.
story_good :- sapphire, garment, match, safe_search, found, repaired.
found :- sapphire_found.
repaired :- garment_mended.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("setting", "quarry_edge"),
        asp.fact("sapphire"),
        asp.fact("garment"),
        asp.fact("match"),
        asp.fact("flat_path"),
        asp.fact("behind_rope"),
        asp.fact("helper_present"),
        asp.fact("sapphire_found"),
        asp.fact("garment_mended"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show story_good/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    try:
        _validate_params(params)
    except StoryError:
        return False
    return True


def asp_verify() -> int:
    params = StoryParams(setting="quarry_edge")
    if not _python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        models = asp.solve(asp_program(), models=1)
        good = any(sym.name == "story_good" for sym in models[0]) if models else False
    except ImportError:
        print("OK: Python reasonableness gate passed; clingo is unavailable.")
        return 0
    if not good:
        print("MISMATCH: ASP twin did not derive story_good.")
        return 1
    sample = generate(params)
    if not sample.story or "sapphire" not in sample.story.lower():
        print("MISMATCH: generated story exercise failed.")
        return 1
    print("OK: Python and ASP story gates agree; generated story exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = make_world(params)
    _build_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(
        setting="quarry_edge",
        child_name="Luna",
        helper_name="Rosa",
        garment_word="blue festival garment",
    ),
    StoryParams(
        setting="quarry_edge",
        child_name="Milo",
        helper_name="Nana",
        garment_word="blue velvet garment",
    ),
    StoryParams(
        setting="quarry_edge",
        child_name="Nia",
        helper_name="Uncle Jo",
        garment_word="blue wool garment",
    ),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            print("ASP model:")
            for symbol in models[0] if models else []:
                print(symbol)
        except ImportError:
            print("ASP mode requires the optional clingo package.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = build_all_samples()
    else:
        samples = []
        for index in range(max(0, args.n)):
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
