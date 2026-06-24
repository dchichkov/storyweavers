#!/usr/bin/env python3
"""
A small fable-style story world about a mouth, a scratch-dim, and toast.

Premise:
A hungry little creature wants to eat toast, but a scratch on the toast leaves
a dim, crumbly mark that makes the first bite unsatisfying. Through repetition,
the creature listens, tries again, and learns a gentle habit: check the toast
carefully, then share the crunch with a friend.

Narrative instruments:
- Repetition: a repeated action phrase becomes important to the turn.
- Sound effects: child-facing crunch, scratch, tap, and nibble sounds anchor the prose.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "boy", "cat", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "bird", "rabbit"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Character:
    kind: str
    type: str
    name: str
    trait: str
    mouthful: str
    likes: str


@dataclass
class Snack:
    label: str
    phrase: str
    scratch_dim: bool
    bite_sound: str
    smell: str
    shines: bool = True


@dataclass
class StoryParams:
    place: str
    character: str
    snack: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="warm", affords={"toast"}),
    "porch": Setting(place="the porch", mood="bright", affords={"toast"}),
    "garden": Setting(place="the garden table", mood="green", affords={"toast"}),
}

CHARACTERS = {
    "mouse": Character(kind="character", type="mouse", name="Milo", trait="little and patient",
                       mouthful="tiny mouth", likes="listening"),
    "bird": Character(kind="character", type="bird", name="Pippa", trait="small and lively",
                      mouthful="small beak", likes="singing"),
    "rabbit": Character(kind="character", type="rabbit", name="Junie", trait="soft and careful",
                        mouthful="gentle mouth", likes="nibbling"),
}

SNACKS = {
    "toast": Snack(
        label="toast",
        phrase="a warm slice of toast with a tiny scratch-dim on one corner",
        scratch_dim=True,
        bite_sound="crisp-crisp",
        smell="buttery",
        shines=False,
    ),
}

TRAIT_WORDS = ["patient", "careful", "gentle", "earnest", "kind"]
REPEAT_PHRASES = [
    "look first, then bite",
    "look first, then bite",
    "look first, then bite",
]


def mouth_word(char: Character) -> str:
    return char.mouthful


def build_story_plan(params: StoryParams) -> tuple[Setting, Character, Snack]:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.character not in CHARACTERS:
        raise StoryError("Unknown character.")
    if params.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    return SETTINGS[params.place], CHARACTERS[params.character], SNACKS[params.snack]


def tell(setting: Setting, char: Character, snack: Snack) -> World:
    world = World(setting)
    eater = world.add(Entity(
        id=char.name,
        kind="character",
        type=char.type,
        label=char.name,
        phrase=f"{char.trait} {char.type}",
        owner=None,
        meters={"hunger": 1.0, "joy": 0.0, "care": 0.0, "crumbs": 0.0},
        memes={"hope": 1.0, "patience": 0.0, "surprise": 0.0},
    ))
    toast = world.add(Entity(
        id="toast",
        kind="thing",
        type="toast",
        label="toast",
        phrase=snack.phrase,
        owner=eater.id,
        meters={"scratch_dim": 1.0 if snack.scratch_dim else 0.0, "crumbs": 0.0, "warmth": 1.0},
        memes={"worry": 0.0},
    ))

    world.say(f"In {setting.place}, {eater.label} was a {char.trait} little {char.type}.")
    world.say(f"{eater.label} had {char.likes} and a {mouth_word(char)} that was ready for breakfast.")
    world.say(f"On the table waited {toast.phrase}.")
    if toast.meters["scratch_dim"] >= 1.0:
        world.say("But one corner held a scratch-dim, a faint mark that looked small and still felt important.")

    world.say(f"{eater.label} tapped the plate. Tap-tap.")
    world.say(f'"{REPEAT_PHRASES[0].capitalize()}," {eater.label} whispered. "Look first, then bite."')
    world.say(f"{eater.label} leaned in close and sniffed. Sniff, sniff.")
    world.say(f"{eater.label} tried one careful nibble: nibble, nibble.")
    world.say(f"Crunch-crunch! The toast answered with {snack.bite_sound}, but the scratch-dim made the first bite feel unfinished.")

    toast.meters["crumbs"] += 1.0
    eater.memes["surprise"] += 1.0
    eater.meters["hunger"] -= 0.25

    world.say(f"So {eater.label} remembered the rule again: {REPEAT_PHRASES[1]}.")
    world.say(f"{eater.label} turned the toast over and chose the bright side.")
    world.say(f"Crunch-crisp! This time the bite was clean, warm, and kind.")
    world.say(f"{eater.label} smiled with a {char.mouthful}, and the toast was shared in little pieces.")

    eater.meters["joy"] += 1.0
    eater.meters["care"] += 1.0
    eater.memes["patience"] += 1.0
    toast.meters["crumbs"] += 1.0

    world.say(f"By the end, the scratch-dim had been forgotten, and the table held only happy crumbs.")
    world.facts.update(
        setting=setting,
        character=char,
        snack=snack,
        eater=eater,
        toast=toast,
        repeated_rule=REPEAT_PHRASES[0],
        sound_primary=snack.bite_sound,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    char = f["character"]
    snack = f["snack"]
    return [
        f'Write a short fable for a child about a {char.type}, a {snack.label}, and a small mistake.',
        f'Create a gentle story where a {char.trait} {char.type} learns to "{REPEAT_PHRASES[0]}" before eating.',
        f'Write a simple tale with sound effects like "tap-tap" and "crunch-crisp" about {char.name} and toast.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    char: Character = f["character"]
    snack: Snack = f["snack"]
    place: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {char.name}, a {char.trait} little {char.type} in {place.place}.",
        ),
        QAItem(
            question=f"What was waiting on the table?",
            answer=f"Warm {snack.label} was waiting on the table, and it had a tiny scratch-dim on one corner.",
        ),
        QAItem(
            question=f"What did {char.name} keep saying to remember?",
            answer=f"{char.name} kept saying, \"{REPEAT_PHRASES[0].capitalize()}\" before biting the toast.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the toast shared in little pieces and the table left with happy crumbs.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is toast?",
            answer="Toast is bread that has been browned by heat, so it can become warm and crisp.",
        ),
        QAItem(
            question="Why is a scratch-dim important in the story?",
            answer="A scratch-dim is important because it is a small mark that makes the first bite feel a little wrong or unfinished.",
        ),
        QAItem(
            question="What do sound effects do in a fable?",
            answer="Sound effects help the story feel lively and clear, so a child can hear the crunches, taps, and nibbles in their mind.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
character(milo).
place(kitchen).
place(porch).
place(garden).
snack(toast).
has_mark(toast,scratch_dim).

ready_to_bite(C) :- character(C).
needs_care(T) :- snack(T), has_mark(T,scratch_dim).
repeated_rule("look first, then bite").
story_ok(P,C,T) :- place(P), character(C), snack(T), ready_to_bite(C), needs_care(T).
#show story_ok/3.
#show repeated_rule/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    for sid, snack in SNACKS.items():
        if snack.scratch_dim:
            lines.append(asp.fact("has_mark", sid, "scratch_dim"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = {(p, c, t) for p in SETTINGS for c in CHARACTERS for t in SNACKS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry coverage ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python coverage:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about mouth, scratch-dim, and toast.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--character", choices=sorted(CHARACTERS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    character = args.character or rng.choice(list(CHARACTERS))
    snack = args.snack or rng.choice(list(SNACKS))
    return StoryParams(place=place, character=character, snack=snack)


def generate(params: StoryParams) -> StorySample:
    setting, char, snack = build_story_plan(params)
    world = tell(setting, char, snack)
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
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    StoryParams(place="kitchen", character="mouse", snack="toast", seed=1),
    StoryParams(place="porch", character="bird", snack="toast", seed=2),
    StoryParams(place="garden", character="rabbit", snack="toast", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_ok/3."))
        triples = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(triples)} compatible story triples:")
        for t in triples:
            print(" ", t)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        while len(samples) < args.n:
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
