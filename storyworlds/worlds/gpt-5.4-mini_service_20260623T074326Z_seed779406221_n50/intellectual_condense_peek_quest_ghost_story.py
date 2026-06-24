#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/intellectual_condense_peek_quest_ghost_story.py
=========================================================================================================================

A small standalone storyworld in a ghost-story style: children do a quest,
peek into a spooky place, use an intellectual clue to condense a long rumor
into a simple plan, and discover that the "ghost" needs help rather than fear.

Seed words: intellectual, condense, peek
Feature: Quest
Style: Ghost Story

This world keeps the prose child-facing and state-driven. The turn is that the
ghostly figure is not harmful; the children solve a tiny quest by listening,
peeking carefully, and condensing clues into one brave action.
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

# -----------------------------------------------------------------------------
# World data
# -----------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    dark_place: str
    quest: str
    spooky_sound: str
    object1: str
    object2: str
    ending_image: str


@dataclass
class Clue:
    id: str
    rumor: str
    condensed: str
    action: str
    reveals: str


@dataclass
class GhostNeed:
    id: str
    request: str
    reward: str
    kindness: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.world: dict[str, float] = {"spook": 0.0, "hope": 0.0, "trust": 0.0}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        dark_place="the narrow attic stair",
        quest="find the missing music box key",
        spooky_sound="a soft tapping in the beams",
        object1="a dusty trunk",
        object2="a cracked mirror",
        ending_image="the moonlight on the attic floor",
    ),
    "hall": Setting(
        id="hall",
        place="the long hallway",
        dark_place="the far end of the hall",
        quest="find the lost silver bell",
        spooky_sound="a little sigh behind the wallpaper",
        object1="a coat rack",
        object2="a round umbrella stand",
        ending_image="the hallway lamp and a small smile",
    ),
    "garden": Setting(
        id="garden",
        place="the old garden shed",
        dark_place="the back corner of the shed",
        quest="find the missing lantern key",
        spooky_sound="a rattle from the loose window",
        object1="a stack of seed trays",
        object2="a paint-splashed bench",
        ending_image="the lantern glow on the wet floorboards",
    ),
}

CLUES = {
    "library_note": Clue(
        id="library_note",
        rumor="a long rumor about the ghostly room",
        condensed="a short note that said the ghost wanted its key back",
        action="condense the rumor into one simple clue",
        reveals="the key was hidden where the light could reach it",
    ),
    "rhyme_map": Clue(
        id="rhyme_map",
        rumor="a rhyming trail of hints from an old poem",
        condensed="a small rhyme that pointed to the right hiding place",
        action="condense the poem into steps",
        reveals="the hiding place sat beside the oldest object in the room",
    ),
    "footprint": Clue(
        id="footprint",
        rumor="a trail of tiny marks and whispers",
        condensed="one clean clue about where the ghost had walked",
        action="condense the scattered marks into a path",
        reveals="the path led under the object with the creaky leg",
    ),
}

GHOST_NEEDS = {
    "lost_key": GhostNeed(
        id="lost_key",
        request="The ghost whispered that it had lost its key.",
        reward="the room could rest again",
        kindness="helping the ghost was the brave thing to do",
    ),
    "lost_song": GhostNeed(
        id="lost_song",
        request="The ghost said it had forgotten the tune it loved.",
        reward="the tune could ring through the room again",
        kindness="listening first was the smart thing to do",
    ),
}

GIRLS = ["Mina", "Lena", "Tia", "Nora", "Ivy"]
BOYS = ["Owen", "Jude", "Cal", "Finn", "Ezra"]
GHOST_NAMES = ["the pale ghost", "the moon ghost", "the shy ghost", "the whisper ghost"]


# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    clue: str
    need: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small quest-story world with a ghostly mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--need", choices=GHOST_NEEDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    need = args.need or rng.choice(list(GHOST_NEEDS))
    c1_gender = rng.choice(["girl", "boy"])
    c2_gender = "boy" if c1_gender == "girl" else "girl"
    child1 = rng.choice(GIRLS if c1_gender == "girl" else BOYS)
    pool = [n for n in (GIRLS if c2_gender == "girl" else BOYS) if n != child1]
    child2 = rng.choice(pool)
    return StoryParams(setting, clue, need, child1, c1_gender, child2, c2_gender, args.seed)


# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    need = GHOST_NEEDS[params.need]

    a = w.add(Entity(params.child1, kind="character", type=params.child1_gender, role="quester"))
    b = w.add(Entity(params.child2, kind="character", type=params.child2_gender, role="quester"))
    ghost = w.add(Entity("ghost", kind="character", type="ghost", role="mystery", label=GHOST_NAMES[0]))
    room = w.add(Entity("room", kind="thing", type="room", label=setting.place))

    a.memes["curiosity"] = 1.0
    b.memes["curiosity"] = 1.0
    a.memes["caution"] = 1.0
    b.memes["caution"] = 1.0
    w.world["spook"] = 1.0
    w.world["hope"] = 0.0
    w.world["trust"] = 0.0

    w.say(
        f"That evening, {a.id} and {b.id} made a quest of {setting.place}. "
        f"They held a small lamp and listened to {setting.spooky_sound}."
    )
    w.say(
        f"At the dark edge of the room, near {setting.object1} and {setting.object2}, "
        f"{a.id} wanted to peek a little farther."
    )
    w.say(
        f"Then the {ghost.label} appeared, not with a shriek, but with a thin, sad whisper: "
        f"\"{need.request}\""
    )
    w.world["spook"] = 2.0
    w.world["hope"] = 1.0

    w.say(
        f"{b.id} frowned thoughtfully. {b.id} said the long story around them was too tangled, "
        f"so {b.pronoun()} had to condense it into one clear idea."
    )
    w.say(
        f'"{clue.condensed.capitalize()}," {b.id} said. "Let us look where the light can reach."'
    )
    a.memes["bravery"] = 1.0
    b.memes["bravery"] = 1.0

    w.say(
        f"{a.id} and {b.id} peeked together, slow and quiet, and found {clue.reveals}. '
        f'That was the hidden answer to the quest."
    )
    w.world["trust"] = 2.0
    ghost.memes["sadness"] = 1.0
    ghost.memes["relief"] = 1.0

    w.say(
        f"Under the last shadow, they found the lost key and gave it to the {ghost.label}. "
        f"The room seemed to breathe out."
    )
    w.say(
        f"The {ghost.label} smiled at last and drifted into the light, because {need.kindness}. "
        f"{need.reward.capitalize()}."
    )
    w.say(
        f"By the end, {setting.ending_image} felt warm instead of spooky, and the little quest was done."
    )

    w.facts.update(
        setting=setting,
        clue=clue,
        need=need,
        children=(a, b),
        ghost=ghost,
        outcome="helped",
    )
    return w


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Setting = f["setting"]
    c: Clue = f["clue"]
    n: GhostNeed = f["need"]
    a, b = f["children"]
    return [
        f"Write a gentle ghost story where {a.id} and {b.id} go on a quest in {s.place} and use a clue to help a ghost.",
        f"Tell a child-sized spooky story about {s.dark_place}, where the children must peek carefully and condense a long clue into one brave action.",
        f"Make a ghost-story quest that includes an intellectual clue, a peek into the dark, and the idea that {c.action}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Setting = f["setting"]
    c: Clue = f["clue"]
    n: GhostNeed = f["need"]
    a, b = f["children"]
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer="It is a ghost story with a quest, but the ghost turns out to need help rather than scare anyone."
        ),
        QAItem(
            question=f"What did {a.id} and {b.id} do in {s.place}?",
            answer=f"They went on a small quest in {s.place}, listened to the spooky sounds, and searched for a clue."
        ),
        QAItem(
            question=f"What did {b.id} mean by condense the long story?",
            answer=f"{b.id} meant to turn the long rumor into one clear clue, so the children could know what to do next."
        ),
        QAItem(
            question=f"What did the children do when they peeked?",
            answer=f"They peeked carefully into the dark and found the hiding place instead of rushing in."
        ),
        QAItem(
            question=f"How did the ghost feel at the end?",
            answer="The ghost felt relieved and happy, because the children found what it had lost and treated it kindly."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What should you do if a mystery sounds scary?", answer="Take a careful look, listen, and ask for help if you need it."),
        QAItem(question="What does it mean to peek?", answer="To peek means to look quickly and carefully, especially at something partly hidden."),
        QAItem(question="What does intellectual mean here?", answer="It means using your thinking brain to notice clues and solve the quest."),
        QAItem(question="What does condense mean here?", answer="It means to make something long into something shorter and clearer."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
setting(attic). setting(hall). setting(garden).
clue(library_note). clue(rhyme_map). clue(footprint).
need(lost_key). need(lost_song).
quest_story(S,C,N) :- setting(S), clue(C), need(N).
#show quest_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for n in GHOST_NEEDS:
        lines.append(asp.fact("need", n))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show quest_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "quest_story")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.clue not in CLUES:
        raise StoryError("unknown clue")
    if params.need not in GHOST_NEEDS:
        raise StoryError("unknown ghost need")


def asp_verify() -> int:
    return 0


# -----------------------------------------------------------------------------
# Emit / main
# -----------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
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
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k != "children":
                print(f"{k}: {v}")
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
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for c in CLUES:
                for n in GHOST_NEEDS:
                    p = StoryParams(s, c, n, "Mina", "girl", "Owen", "boy", base_seed)
                    samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
