#!/usr/bin/env python3
"""
storyworlds/worlds/ghetto_chowder_repetition_happy_ending_ghost_story.py
========================================================================

A small story world about a child, a friendly ghost, a pot of chowder,
repeated warnings, and a happy ending in an old neighborhood block.

Seed tale inspiration:
---
On a chilly evening in the old neighborhood, a child hears a ghost whisper
the same two words again and again: "chowder, chowder." The ghost is not
trying to scare anyone. It is trying to remember a lost pot of chowder that
was promised to the building's neighbors. The child follows the repeating
voice, finds the missing pot, and shares the soup. The ghost finally smiles,
the repeating words stop, and the block feels warm and safe again.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    container: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old block courtyard"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    ghost_name: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Maya", "Nina", "Lena", "Ava", "Zuri", "Ivy"],
    "boy": ["Owen", "Theo", "Malik", "Eli", "Noah", "Jace"],
}
PARENTS = ["mother", "father", "grandmother", "grandfather"]
GHOST_NAMES = ["Moss", "Bells", "Milo", "Penny", "Soot", "Rue"]


def _repeat(world: World, speaker: Entity, word: str, times: int = 3) -> None:
    speaker.memes["repetition"] = speaker.memes.get("repetition", 0.0) + times
    world.say(f'{speaker.id} kept saying "{word}, {word}."')


def _find_pot(world: World, child: Entity, ghost: Entity, pot: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} followed the soft repeating voice down the hall and behind the "
        f"stairs. There, under an old crate, was a heavy pot of chowder."
    )
    pot.container = "hidden spot"


def _share_chowder(world: World, child: Entity, parent: Entity, ghost: Entity, pot: Entity) -> None:
    ghost.memes["sad"] = 0.0
    ghost.memes["joy"] = ghost.memes.get("joy", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.id} carried the pot back to the courtyard. {parent.id} lifted the lid, "
        f"and the warm chowder smelled like supper and home."
    )
    world.say(
        f"They poured bowls for the neighbors too. The ghost tasted a spoonful, smiled "
        f"wide, and said, 'Chowder!' one last time, but this time it sounded happy."
    )
    world.say(
        f"After that, {ghost.id} floated by the window like a soft lamp, and the whole "
        f"block felt peaceful."
    )


def tell_story(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent.capitalize(), kind="character", type=params.parent))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost"))
    pot = world.add(Entity(id="pot", type="pot", label="pot of chowder", phrase="a big pot of chowder"))

    world.say(
        f"On the old block courtyard, {child.id} was helping {parent.id} bring in the laundry "
        f"when a pale little ghost drifted out from beside the steps."
    )
    world.say(
        f"It did not howl or boom. It only whispered the same word again and again, as if "
        f"the night itself had a tiny spoon in it."
    )
    _repeat(world, ghost, "chowder", 2)

    world.para()
    world.say(
        f"{child.id} was not scared. {child.id} had a brave heart and a curious nose, and the word "
        f"felt too tasty to ignore."
    )
    world.say(
        f"'Why do you keep saying chowder?' {child.id} asked."
    )
    ghost.memes["sad"] = 1.0
    world.say(
        f"The ghost pointed toward the dark stairwell and repeated, 'Chowder, chowder,' with a "
        f"little shaky sigh."
    )
    world.say(
        f"{parent.id} peered into the hall and said the ghost sounded lonely, not spooky."
    )

    world.para()
    _find_pot(world, child, ghost, pot)
    world.say(
        f"{child.id} found a handwritten note tucked under the pot. It said the chowder was for "
        f"everyone in the building, but the delivery had gotten hidden when the lights went out."
    )
    world.say(
        f"{child.id} called {parent.id}, and together they carried the pot back into the warm kitchen."
    )
    _share_chowder(world, child, parent, ghost, pot)

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        pot=pot,
        place=world.setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a short ghost story for a young child about a repeated word that turns out to be kind.',
        f"Tell a gentle story where {child.id} hears a ghost say the same food word again and again, then helps it.",
        "Write a cozy neighborhood ghost story with repetition and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    ghost: Entity = f["ghost"]
    return [
        QAItem(
            question=f"Who heard the ghost in the old courtyard?",
            answer=f"{child.id} heard the ghost first, while helping {parent.id} with laundry.",
        ),
        QAItem(
            question=f"What word did the ghost keep repeating?",
            answer="The ghost kept repeating chowder, because it was trying to remember the missing pot.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {child.id} and {parent.id} sharing the chowder and the ghost smiling.",
        ),
        QAItem(
            question=f"Was the ghost scary?",
            answer="No. The ghost was lonely and unsure, not scary.",
        ),
        QAItem(
            question=f"What changed after the chowder was found?",
            answer=f"The ghost stopped sounding sad, and the whole block felt warm and peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chowder?",
            answer="Chowder is a thick soup, often made with milk or cream, potatoes, and vegetables or fish.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying or doing the same thing more than once, which can make a story feel rhythmic or important.",
        ),
        QAItem(
            question="Why can a ghost story still be gentle?",
            answer="A ghost story can be gentle when the ghost is friendly, the problem is small, and the ending feels safe and warm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% The ghost repeats the food word when it is sad and the chowder is hidden.
needs_reassurance(G) :- ghost(G), sad(G).
repeats_chowder(G) :- needs_reassurance(G), hidden(chowder_pot).

% A happy ending happens when the child finds the pot and shares the soup.
happy_ending :- found(chowder_pot), shared(chowder_pot).

#show needs_reassurance/1.
#show repeats_chowder/1.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ghost", "moss"),
        asp.fact("sad", "moss"),
        asp.fact("hidden", "chowder_pot"),
        asp.fact("found", "chowder_pot"),
        asp.fact("shared", "chowder_pot"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    happy = bool(asp.atoms(model, "happy_ending"))
    if happy:
        print("OK: ASP reasoning confirms the happy ending.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with repetition and a happy ending.")
    ap.add_argument("--name", choices=sorted({n for vals in NAMES.values() for n in vals}))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(name=name, gender=gender, parent=parent, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.container:
            bits.append(f"container={e.container}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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
    StoryParams(name="Maya", gender="girl", parent="mother", ghost_name="Moss"),
    StoryParams(name="Owen", gender="boy", parent="father", ghost_name="Bells"),
    StoryParams(name="Nina", gender="girl", parent="grandmother", ghost_name="Rue"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show needs_reassurance/1. #show repeats_chowder/1. #show happy_ending/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

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
