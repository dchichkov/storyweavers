#!/usr/bin/env python3
"""
A gentle whodunit about a loverdover note, a misunderstanding, and careful questions.
"""

from __future__ import annotations

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
    helper_name: str = "Milo"
    recipient_name: str = "Nora"
    note_color: str = "blue"
    style: str = "whodunit"
    feature: str = "misunderstanding"
    seed_word: str = "loverdover"


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
    detective: Entity
    helper: Entity
    recipient: Entity
    note: Entity
    clues: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        for entity in [self.detective, self.helper, self.recipient, self.note]:
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {entity.id:12} ({entity.kind:10}) {' '.join(bits)}")
        lines.append(f"  setting: {self.setting}")
        lines.append(f"  clues: {self.clues}")
        return "\n".join(lines)


SETTINGS = {
    "garden": "the community garden",
    "library": "the little library",
    "bakery": "the sunny bakery",
    "clubhouse": "the neighborhood clubhouse",
}

NAMES = ["Luna", "Ari", "Mina", "Theo", "Juno", "Pip"]
HELPERS = ["Milo", "Bea", "Ollie", "Sana", "Finn"]
RECIPIENTS = ["Nora", "Ivy", "Remy", "Zoe", "Kai"]
COLORS = ["blue", "yellow", "green", "red"]

OPENINGS = {
    "garden": [
        "{detective} was watering bean sprouts in the community garden when a blue envelope appeared beneath the rose trellis.",
        "At the community garden, {detective} found a folded note resting beside the seed box.",
    ],
    "library": [
        "{detective} was returning picture books in the little library when a blue envelope slipped from a storybook.",
        "The little library was quiet when {detective} discovered a folded note between two mystery novels.",
    ],
    "bakery": [
        "While carrying napkins through the sunny bakery, {detective} noticed a blue envelope beside the flour tin.",
        "The bakery smelled of cinnamon when {detective} found a folded note near the warm bread.",
    ],
    "clubhouse": [
        "{detective} was tidying the neighborhood clubhouse when a blue envelope turned up under a board game.",
        "In the clubhouse, {detective} found a folded note tucked beside the box of crayons.",
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle whodunit about a loverdover note and a misunderstanding."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--recipient", choices=RECIPIENTS)
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Choose a real story setting.")
    if params.child_name == params.recipient_name:
        raise StoryError("The detective and the note's recipient must be different people.")
    if params.child_name == params.helper_name:
        raise StoryError("The detective and helper must be different people.")
    if params.feature != "misunderstanding":
        raise StoryError("This whodunit must center on a misunderstanding.")
    if params.seed_word != "loverdover":
        raise StoryError("The seed word must remain loverdover.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.name or rng.choice(NAMES)
    helper_choices = [name for name in HELPERS if name != child]
    recipient_choices = [name for name in RECIPIENTS if name != child]
    helper = args.helper or rng.choice(helper_choices)
    recipient = args.recipient or rng.choice(recipient_choices)
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        child_name=child,
        helper_name=helper,
        recipient_name=recipient,
        note_color=args.color or rng.choice(COLORS),
    )
    validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    detective = Entity(params.child_name, "character", params.child_name, "detective")
    helper = Entity(params.helper_name, "character", params.helper_name, "helper")
    recipient = Entity(params.recipient_name, "character", params.recipient_name, "recipient")
    note = Entity("note", "object", f"{params.note_color} envelope", "love note")
    detective.memes["curiosity"] = 1.0
    helper.memes["patience"] = 1.0
    note.meters["hidden"] = 1.0
    note.meters["meaning_unclear"] = 1.0
    return World(
        setting=SETTINGS[params.setting],
        detective=detective,
        helper=helper,
        recipient=recipient,
        note=note,
    )


def build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 211)
    d = world.detective
    h = world.helper
    r = world.recipient
    note = world.note

    opening = rng.choice(OPENINGS[params.setting]).format(detective=d.label)
    accusation = rng.choice([
        f'"The note says, \'For my loverdover, meet me after lunch,\'" {d.label} whispered. "It must be for {r.label}, but who hid it?"',
        f'{d.label} read the note aloud: "For my loverdover." Then {d.label} frowned. "Someone wanted {r.label} to find this, but the note is in the wrong place."',
    ])
    helper_reply = rng.choice([
        f'"Let us ask before we guess," said {h.label}. "A mystery can have a kind heart."',
        f'"We need clues, not a quick blame," {h.label} replied. "The writer may have made a simple mistake."',
    ])
    reveal_line = rng.choice([
        f'{h.label} remembered seeing {r.label} carry a red basket toward the craft table, so they checked the basket together.',
        f'{d.label} noticed a tiny smear of berry jam on the envelope and remembered that {r.label} had been making jam sandwiches nearby.',
        f'The paper had a crooked fold shaped like the corner of a paper flower, just like the flowers {r.label} had been folding.',
    ])
    exchange = rng.choice([
        f'"Did you write this for me?" {d.label} asked {r.label}. "{r.label}, please tell me what you meant."',
        f'"I found your note," {d.label} said. "Was it meant to be secret?" {r.label} blinked and answered, "Secret? I thought you had it."',
    ])
    ending = rng.choice([
        f'They delivered the note to {r.label}, who laughed gently and gave {d.label} a paper flower. The loverdover mystery ended with a hug and a promise to write names clearly next time.',
        f'The note belonged to {r.label}, but it was meant for a kind friend at the flower table, not a secret sweetheart. Everyone smiled when the misunderstanding was cleared up.',
        f'By sunset, the note was safely in the right hands, and {d.label} had learned that asking a gentle question can turn a puzzling clue into a happy ending.',
    ])

    world.say(opening)
    world.say(
        f"The envelope was {params.note_color}, its flap was crooked, and no name appeared on the front. "
        f"Inside, one line read, 'For my loverdover.'"
    )
    world.say(accusation)
    d.inc_meter("clues_seen", 1.0)
    world.clues.append("unsigned loverdover note")

    world.para()
    world.say(helper_reply)
    h.inc_meter("questions_encouraged", 1.0)
    world.say(
        f"{d.label} looked at the envelope instead of pointing at anyone. "
        "There was a faint jam mark, a fold in the paper, and a crumb near the flap."
    )
    world.clues.extend(["jam mark", "crooked flower fold", "crumb"])
    d.inc_meter("clues_seen", 2.0)
    world.say(reveal_line)

    world.para()
    world.say(exchange)
    r.inc_meme("honesty", 1.0)
    d.inc_meme("understanding", 1.0)
    note.meters["hidden"] = 0.0
    note.meters["meaning_unclear"] = 0.0
    note.meters["delivered"] = 1.0
    world.say(
        f"{r.label} explained that " + rng.choice([
            "the word loverdover was a silly friendship word, not a secret accusation.",
            "the note was part of a surprise thank-you for the person who had helped with the flowers.",
            "the note had been moved by the wind, so the wrong place made the right message look mysterious.",
        ])
    )
    world.say(ending)

    world.facts.update(
        opening=opening,
        clue_count=len(world.clues),
        reveal=reveal_line,
        misunderstanding_resolved=True,
        note_recipient=r.label,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a gentle whodunit in {world.setting} about {world.note.label} and a loverdover misunderstanding.",
        f"Tell a child-friendly mystery where {world.detective.label} follows clues before making an accusation.",
        "Write a story in which a kind question resolves a confusing note and changes what the detective decides.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.detective
    h = world.helper
    r = world.recipient
    return [
        QAItem(
            question="What started the mystery?",
            answer=f"{d.label} found an unsigned {world.note.label} that said, 'For my loverdover,' so the message was hard to understand.",
        ),
        QAItem(
            question="How did the detective solve the misunderstanding?",
            answer=f"{d.label} listened to {h.label}, followed small clues such as the jam mark and flower fold, and asked {r.label} a gentle question instead of blaming anyone.",
        ),
        QAItem(
            question="What did the loverdover message mean?",
            answer=f"It was a kind, playful message connected with {r.label}'s surprise or friendship plan, not proof of a dangerous secret.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The note reached the right hands, its meaning became clear, and the characters felt relieved because they had asked and listened.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone receives the wrong meaning from words, actions, or clues.",
        ),
        QAItem(
            question="Why are clues useful in a whodunit?",
            answer="Clues help characters test guesses and discover what really happened instead of blaming someone too quickly.",
        ),
        QAItem(
            question="Why should people ask kind questions?",
            answer="A kind question gives another person a chance to explain, which can turn confusion into understanding.",
        ),
        QAItem(
            question="What does loverdover mean in this story?",
            answer="Loverdover is a playful seed word used in the note as a warm, silly expression rather than a frightening secret.",
        ),
    ]


ASP_RULES = r"""
clear_meaning(N) :- note(N), clue(N), asks_gently.
resolved(M) :- misunderstanding(M), clear_meaning(note).
good_whodunit :- resolved(misunderstanding), follows_clues, no_blame.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("misunderstanding", "misunderstanding"),
        asp.fact("note", "note"),
        asp.fact("clue", "jam_mark"),
        asp.fact("clue", "flower_fold"),
        asp.fact("follows_clues"),
        asp.fact("asks_gently"),
        asp.fact("no_blame"),
    ]
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    return "\n".join(lines)


def asp_program(show: str = "#show good_whodunit/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.feature == "misunderstanding"
        and params.seed_word == "loverdover"
        and params.style == "whodunit"
    )


def asp_verify() -> int:
    if not python_reasonable(StoryParams(setting="garden")):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        models = asp.solve(asp_program(), models=1)
        atoms = {str(atom) for atom in models[0]} if models else set()
        if "good_whodunit" not in atoms:
            print("MISMATCH: ASP twin did not approve the whodunit.")
            return 1
    except ImportError:
        print("OK: Python gate passed; clingo is unavailable for ASP execution.")
        return 0
    print("OK: Python and ASP gates agree.")
    return 0


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = make_world(params)
    build_story(world, params)
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
    StoryParams(setting="garden", child_name="Luna", helper_name="Milo", recipient_name="Nora", note_color="blue"),
    StoryParams(setting="library", child_name="Ari", helper_name="Bea", recipient_name="Ivy", note_color="yellow"),
    StoryParams(setting="bakery", child_name="Mina", helper_name="Ollie", recipient_name="Remy", note_color="green"),
    StoryParams(setting="clubhouse", child_name="Theo", helper_name="Sana", recipient_name="Zoe", note_color="red"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
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
