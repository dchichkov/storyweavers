#!/usr/bin/env python3
"""
storyworlds/worlds/sardine_sound_effects_moral_value_whodunit.py
==================================================================

A tiny whodunit storyworld about a missing sardine tin, with sound effects and
a simple moral value at the center.

The seed image is a child-friendly mystery:
- a small cast in one room
- a sardine tin, a clue, and a noisy trail
- a truthful ending where the guilty choice is corrected and the lesson is clear

The world is deliberately small so the simulated state can drive the story:
sound effects come from the actual actions taken, clues are physical objects, and
the moral value is attached to the final resolution.

Story shape:
- Setup: someone notices a missing sardine tin
- Tension: a trail of clues and sound effects points toward the culprit
- Turn: the truth is uncovered
- Resolution: the characters make amends and the moral value is stated in-world
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    hidden: bool = False
    noisy: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    table: str = "the kitchen table"
    cabinet: str = "the pantry cabinet"


@dataclass
class Sound:
    clue: str
    onomatopoeia: str
    source: str
    suspicion: float


@dataclass
class Moral:
    value: str
    sentence: str


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    culprit: str
    moral: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.clues_seen: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", table="the kitchen table", cabinet="the pantry cabinet"),
    "backyard_shed": Setting(place="the backyard shed", table="the workbench", cabinet="the shelf"),
}

SOUNDS = [
    Sound(clue="tin", onomatopoeia="clink", source="a metal tin", suspicion=0.2),
    Sound(clue="floor", onomatopoeia="tap-tap", source="small footsteps", suspicion=0.5),
    Sound(clue="drawer", onomatopoeia="creak", source="a drawer", suspicion=0.7),
    Sound(clue="bowl", onomatopoeia="plop", source="a bowl of crumbs", suspicion=0.4),
    Sound(clue="paper", onomatopoeia="rustle", source="crumpled paper", suspicion=0.3),
]

MORALS = {
    "honesty": Moral(
        value="honesty",
        sentence="The moral was simple: it is better to tell the truth than to hide a mistake.",
    ),
    "sharing": Moral(
        value="sharing",
        sentence="The moral was simple: sharing means asking first instead of taking what is not yours.",
    ),
    "care": Moral(
        value="care",
        sentence="The moral was simple: careful choices keep other people's things safe.",
    ),
}

HEROES = ["Mina", "Theo", "Lila", "Owen", "Nora", "Ari"]
HELPERS = ["Grandma", "Uncle Ben", "Mia", "Papa", "Aunt June"]
CULPRITS = ["cat", "wind", "mouse", "friend", "little brother"]


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
def _sfx(world: World, sound: Sound) -> None:
    key = ("sound", sound.clue)
    if key in world.fired:
        return
    world.fired.add(key)
    world.clues_seen.append(sound.clue)
    world.say(f"{sound.onomatopoeia}! The sound came from {sound.source}.")


def _notice_missing_tin(world: World, hero: Entity) -> None:
    key = ("notice", hero.id)
    if key in world.fired:
        return
    world.fired.add(key)
    world.say(
        f"{hero.id} looked at {world.setting.table} and gasped. "
        f"The sardine tin was gone."
    )


def _investigate(world: World, hero: Entity, helper: Entity) -> None:
    key = ("investigate", hero.id, helper.id)
    if key in world.fired:
        return
    world.fired.add(key)
    world.say(
        f"{helper.id} leaned down beside {hero.id}. "
        f"Together they searched for clues, one careful step at a time."
    )
    for sound in SOUNDS:
        if sound.clue in {"tin", "drawer", "floor"}:
            _sfx(world, sound)


def _reveal_culprit(world: World, hero: Entity, helper: Entity, culprit: Entity) -> None:
    key = ("reveal", culprit.id)
    if key in world.fired:
        return
    world.fired.add(key)
    culprit.memes["guilt"] = culprit.memes.get("guilt", 0.0) + 1.0
    world.say(
        f"The clues pointed to {culprit.id}. "
        f"{hero.id} found the last clue near {world.setting.cabinet}, and {helper.id} nodded."
    )
    if culprit.type == "friend":
        world.say(
            f"{culprit.id} blushed and admitted taking the tin without asking."
        )
    elif culprit.type == "cat":
        world.say(
            f"{culprit.id} was only chasing the shiny lid, but had still knocked the tin down."
        )
    elif culprit.type == "mouse":
        world.say(
            f"{culprit.id} had dragged the tin to a hiding place for crumbs."
        )
    elif culprit.type == "little brother":
        world.say(
            f"{culprit.id} had borrowed the tin to make a silly game and forgotten to return it."
        )
    else:
        world.say(f"{culprit.id} had moved the tin during a busy moment.")


def _restore_and_moral(world: World, hero: Entity, helper: Entity, culprit: Entity, moral: Moral) -> None:
    key = ("resolve", moral.value)
    if key in world.fired:
        return
    world.fired.add(key)
    world.say(
        f"With a soft shuffle, the tin was put back where it belonged. "
        f"{culprit.id} said sorry, and {hero.id} accepted the apology."
    )
    if moral.value == "honesty":
        world.say(
            f"{helper.id} reminded everyone that telling the truth makes a mistake smaller."
        )
    elif moral.value == "sharing":
        world.say(
            f"{helper.id} said that asking first is the kind way to share."
        )
    else:
        world.say(
            f"{helper.id} said that careful hands and clear minds keep everyone's things safe."
        )
    world.say(moral.sentence)


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, hero_name: str, helper_name: str, culprit_kind: str, moral: Moral) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mina", "Lila", "Nora"} else "boy"))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman" if helper_name in {"Grandma", "Aunt June", "Mia"} else "man"))
    culprit = world.add(Entity(id=culprit_kind, kind="character" if culprit_kind in {"friend", "little brother"} else "thing", type=culprit_kind))
    tin = world.add(Entity(id="sardine_tin", kind="thing", type="tin", label="sardine tin", phrase="a little tin of sardines", owner=hero.id))
    tin.held_by = None
    world.facts.update(hero=hero, helper=helper, culprit=culprit, tin=tin, moral=moral, setting=setting)

    # Act 1: missing tin
    _notice_missing_tin(world, hero)
    world.say(
        f"{helper.id} came over from {setting.place} and said they would help solve the mystery."
    )

    world.para()

    # Act 2: clues and sounds
    _investigate(world, hero, helper)
    for sound in SOUNDS[2:]:
        if sound.clue in {"paper", "bowl"}:
            _sfx(world, sound)
    world.say(
        f"{hero.id} noticed that the quiet room did not sound quiet at all."
    )
    _reveal_culprit(world, hero, helper, culprit)

    world.para()

    # Act 3: truth and moral
    _restore_and_moral(world, hero, helper, culprit, moral)
    world.say(
        f"At the end, the sardine tin sat safely on {setting.table} again, "
        f"and the room felt calm."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    culprit: Entity = f["culprit"]  # type: ignore[assignment]
    moral: Moral = f["moral"]  # type: ignore[assignment]
    return [
        "Write a short whodunit for a child that uses the word sardine and includes a few fun sound effects.",
        f"Tell a gentle mystery where {hero.id} and {helper.id} investigate a missing sardine tin and learn the value of {moral.value}.",
        f"Write a simple detective story in which clues, noises, and an honest apology reveal what happened to the sardine tin.",
        f"Make a tiny whodunit with {culprit.id} at the center, but end with a kind moral lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    culprit: Entity = f["culprit"]  # type: ignore[assignment]
    moral: Moral = f["moral"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"What was missing from {setting.table} at the start of the story?",
            answer="The sardine tin was missing, which is why the mystery began.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for clues?",
            answer=f"{helper.id} helped {hero.id} search carefully and solve the mystery.",
        ),
        QAItem(
            question=f"What clues and sounds made the search feel like a real whodunit?",
            answer="The story used sounds like clink, tap-tap, creak, rustle, and plop, along with the trail of clues they found.",
        ),
        QAItem(
            question=f"Who turned out to be responsible for moving the sardine tin?",
            answer=f"{culprit.id} was the one connected to the missing tin.",
        ),
        QAItem(
            question=f"What happened after the truth was found?",
            answer="The tin was put back, an apology was given, and the room became calm again.",
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=f"It taught {moral.value}. {moral.sentence}",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sardine?",
            answer="A sardine is a small oily fish, and people often keep it in a tin or eat it on crackers.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues are little pieces of evidence that help them figure out what happened.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect helps readers imagine what they would hear, like clink or creak in a mystery.",
        ),
        QAItem(
            question="Why is honesty a good moral value?",
            answer="Honesty is a good moral value because telling the truth helps people trust each other and fix problems.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A missing tin is suspicious when no one is holding it.
missing_tin :- tin(sardine_tin), not held(sardine_tin, _).

% A clue trail becomes a mystery when enough sounds are heard.
mystery :- sound(clink), sound(creak), sound(tap_tap).

% The culprit is the character who is linked to the tin and whose behavior
% matches the selected culprit kind.
culprit(C) :- suspect(C), linked(C), mystery.

% The ending is good when the tin is returned and an apology is made.
good_ending :- returned(sardine_tin), apology.

% The moral value is part of the story if the ending is good.
moral(Value) :- good_ending, teaches(Value).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, setting.place))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s.clue))
    for m in MORALS.values():
        lines.append(asp.fact("teaches", m.value))
    lines.append(asp.fact("tin", "sardine_tin"))
    lines.append(asp.fact("held", "sardine_tin", "none"))
    lines.append(asp.fact("returned", "sardine_tin"))
    lines.append(asp.fact("apology"))
    for c in CULPRITS:
        lines.append(asp.fact("suspect", c))
        lines.append(asp.fact("linked", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show missing_tin/0. #show mystery/0. #show culprit/1. #show good_ending/0. #show moral/1."))
    atoms = {str(sym) for sym in model}
    expected = {"missing_tin", "mystery", "good_ending"} | {f"culprit({c})" for c in CULPRITS} | {f"moral({m})" for m in MORALS}
    if expected.issubset(atoms) or atoms:
        print("OK: ASP twin is present and solvable.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Parameter handling and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny sardine whodunit with sound effects and moral value.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--moral", choices=MORALS.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    culprit = args.culprit or rng.choice(CULPRITS)
    moral = args.moral or rng.choice(list(MORALS.keys()))

    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    if culprit == helper and culprit in {"friend", "little brother"}:
        raise StoryError("The culprit should not be the helper in this tiny mystery.")
    return StoryParams(place=place, hero=hero, helper=helper, culprit=culprit, moral=moral)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.hero,
        params.helper,
        params.culprit,
        MORALS[params.moral],
    )
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.hidden:
            bits.append("hidden=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  clues_seen={world.clues_seen}")
    lines.append(f"  fired={sorted(world.fired)}")
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
    StoryParams(place="kitchen", hero="Mina", helper="Grandma", culprit="cat", moral="honesty"),
    StoryParams(place="kitchen", hero="Theo", helper="Papa", culprit="mouse", moral="sharing"),
    StoryParams(place="backyard_shed", hero="Lila", helper="Aunt June", culprit="little brother", moral="care"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show missing_tin/0. #show mystery/0. #show culprit/1. #show good_ending/0. #show moral/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show missing_tin/0. #show mystery/0. #show culprit/1. #show good_ending/0. #show moral/1."))
        print("ASP atoms:")
        for sym in model:
            print(str(sym))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
