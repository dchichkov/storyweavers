#!/usr/bin/env python3
"""
A small bedtime-story world about Luna, a curious child, and the comfort of
having a question acknowledged before sleep.
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

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    window_view: str
    night_sound: str


@dataclass(frozen=True)
class Curiosity:
    id: str
    question: str
    clue: str
    small_answer: str
    comforting_image: str


@dataclass
class StoryWorld:
    setting: Setting
    curiosity: Curiosity
    hero: str
    helper: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "attic_room": Setting(
        "attic_room",
        "the little attic room",
        "the moonlit chimney pots",
        "the soft tick of the clock",
    ),
    "garden_room": Setting(
        "garden_room",
        "the garden room",
        "the silver leaves",
        "the hush of crickets",
    ),
    "window_nook": Setting(
        "window_nook",
        "the window nook",
        "the sleeping rooftops",
        "the whisper of curtains",
    ),
}

CURIOSITIES = {
    "moon_shadow": Curiosity(
        "moon_shadow",
        "Why does the moon make a long shadow when the moon is so far away?",
        "a spoon shining in a cup of water",
        "Light travels in straight lines, and anything that blocks it can make a shadow.",
        "a pale shadow resting quietly beside Luna's bed",
    ),
    "night_bird": Curiosity(
        "night_bird",
        "Which bird sings when nearly everyone else is asleep?",
        "three notes beyond the open window",
        "Some birds wake at night because the dark is their busy time.",
        "a small bird folding its wings under the stars",
    ),
    "star_path": Curiosity(
        "star_path",
        "Could a tiny star show a traveler the way home?",
        "a bright point above the roof",
        "People can use familiar stars as gentle markers, while maps and grown-ups help them travel safely.",
        "a bright star keeping watch over the quiet roofs",
    ),
}

HERO_NAMES = ["Luna", "Mira", "Nell", "Ivy"]
HELPER_NAMES = ["Mama", "Papa", "Grandma", "Auntie"]

OPENINGS = [
    "{hero} was tucked beneath a quilt when {sound} began its tiny bedtime song.",
    "The house had grown quiet, but {hero}'s question was still awake.",
    "{hero} placed a book beside the pillow and looked toward {view}.",
    "Just as the lamp became a golden dot, {hero} noticed something curious.",
]

@dataclass
class StoryParams:
    setting: str
    curiosity: str
    name: str
    helper: str
    seed: Optional[int] = None


def reasonability_gate(setting: Setting, curiosity: Curiosity) -> bool:
    if not setting.place or not curiosity.question:
        return False
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    curiosity = args.curiosity or rng.choice(list(CURIOSITIES))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if curiosity not in CURIOSITIES:
        raise StoryError(f"Unknown curiosity: {curiosity}")
    if not reasonability_gate(SETTINGS[setting], CURIOSITIES[curiosity]):
        raise StoryError("The selected bedtime world is not reasonable.")
    return StoryParams(
        setting=setting,
        curiosity=curiosity,
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        seed=args.seed,
    )


def tell(params: StoryParams) -> StoryWorld:
    setting = SETTINGS[params.setting]
    curiosity = CURIOSITIES[params.curiosity]
    world = StoryWorld(setting, curiosity, params.name, params.helper)
    opening = OPENINGS[(params.seed or 0) % len(OPENINGS)]

    world.say(opening.format(hero=params.name, sound=setting.night_sound, view=setting.window_view))
    world.say(
        f"{params.name} was a thoughtful child who liked to follow Curiosity wherever it wandered."
    )
    world.say(
        f"Tonight, Curiosity brought this question: “{curiosity.question}”"
    )

    world.para()
    world.say(
        f"{params.name} carried the question to {params.helper}, who was smoothing the quilt."
    )
    world.say(
        f"“I hear you,” {params.helper} said. “Let us acknowledge it before we rest.”"
    )
    world.say(
        f"“Thank you,” said {params.name}. “I do not need to solve everything tonight. I just want to understand a little.”"
    )
    world.say(
        f"{params.helper} smiled. “That is a wise kind of wondering.”"
    )

    world.para()
    world.say(
        f"Together they looked for one small clue: {curiosity.clue}."
    )
    world.say(
        f"{params.helper} explained, “{curiosity.small_answer}”"
    )
    world.say(
        f"{params.name} repeated the idea softly, and the question felt less like a knock and more like a lantern."
    )

    world.para()
    world.say(
        f"They wrote the question on a bedside card so tomorrow could hold the next part of the search."
    )
    world.say(
        f"Then {params.helper} tucked the card beneath the lamp and said, “Curiosity can sleep safely when someone has listened.”"
    )
    world.say(
        f"{params.name} listened to {setting.night_sound}, watched {setting.window_view}, and let one slow breath out."
    )
    world.say(
        f"At last, {params.name} dreamed of {curiosity.comforting_image}."
    )

    world.meters["curiosity"] = 1.0
    world.meters["worry"] = 0.0
    world.memes["trust"] = 1.0
    world.memes["calm"] = 1.0
    world.facts.update(
        question=curiosity.question,
        clue=curiosity.clue,
        answer=curiosity.small_answer,
        image=curiosity.comforting_image,
        acknowledged=True,
        resolved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    curiosity = world.curiosity
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a gentle bedtime story in which {params.name}'s curiosity about {curiosity.question.lower()} is acknowledged.",
            f"Tell a quiet story where {params.helper} offers {params.name} one small clue before sleep.",
            f"End with a peaceful image connected to {curiosity.comforting_image}.",
        ],
        story_qa=[
            QAItem(
                "What question did Luna wonder about?",
                f"{params.name} wondered, “{curiosity.question}”",
            ),
            QAItem(
                f"How did {params.helper} acknowledge {params.name}'s curiosity?",
                f"{params.helper} listened, said the question was worth hearing, and explored one small clue with {params.name}.",
            ),
            QAItem(
                "What small answer did they discover?",
                curiosity.small_answer,
            ),
            QAItem(
                "How did the question change before bedtime?",
                f"It felt less like a worry and more like a lantern because someone listened and left a card for tomorrow's wondering.",
            ),
            QAItem(
                "What happened at the end?",
                f"{params.name} became calm, watched {world.setting.window_view}, and dreamed of {curiosity.comforting_image}.",
            ),
        ],
        world_qa=[
            QAItem(
                "Why can acknowledging a child's question help at bedtime?",
                "Acknowledging a question helps a child feel heard and safe, even when the whole answer can wait until morning.",
            ),
            QAItem(
                "What is curiosity?",
                "Curiosity is the wish to notice, ask, and learn about something unfamiliar.",
            ),
            QAItem(
                "Why might a small clue be enough for one night?",
                "A small clue can make an idea feel less mysterious while leaving restful time for more learning later.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"  setting: {world.setting.place}",
            f"  hero: {world.hero}",
            f"  curiosity: {world.curiosity.id}",
            f"  meters: {world.meters}",
            f"  memes: {world.memes}",
            f"  acknowledged: {world.facts['acknowledged']}",
            f"  resolved: {world.facts['resolved']}",
        ]
    )


ASP_RULES = r"""
acknowledged(Q) :- curiosity(Q), listened(Q).
calm(Q) :- acknowledged(Q), small_clue(Q).
valid(S, Q) :- setting(S), curiosity(Q), calm(Q).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, curiosity in CURIOSITIES.items():
        lines.append(asp.fact("curiosity", cid))
        lines.append(asp.fact("small_clue", cid))
        lines.append(asp.fact("listened", cid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, cid) for sid in SETTINGS for cid in CURIOSITIES]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        clingo_values = set(asp_valid_combos())
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py != clingo_values:
        print("MISMATCH between Python and ASP gates")
        print("python only:", sorted(py - clingo_values))
        print("ASP only:", sorted(clingo_values - py))
        return 1
    for combo in valid_combos():
        sample = generate(StoryParams(combo[0], combo[1], "Luna", "Mama", 0))
        if "acknowledge" not in sample.story.lower():
            print("Generated story failed to acknowledge curiosity.")
            return 1
    print(f"OK: ASP and Python agree on {len(py)} bedtime worlds.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime world about acknowledging curiosity.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--curiosity", choices=sorted(CURIOSITIES))
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        import asp

        for value in sorted(set(asp.atoms(asp.one_model(asp_program()), "valid"))):
            print(value)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []

    if args.all:
        for setting in SETTINGS:
            for curiosity in CURIOSITIES:
                samples.append(
                    generate(
                        StoryParams(
                            setting,
                            curiosity,
                            args.name or "Luna",
                            args.helper or "Mama",
                            base_seed,
                        )
                    )
                )
    else:
        for index in range(max(0, args.n)):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
