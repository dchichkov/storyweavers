#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/saddle_bad_ending_magic_misunderstanding_tall_tale.py
=================================================================================================

A standalone storyworld for a tiny tall-tale domain built from the seed word
"saddle" with Magic, Misunderstanding, and a Bad Ending.

Premise:
- A child hears that an old saddle is magic.
- The magic is real, but the instructions are misunderstood.
- The wrong use of the saddle leads to a small, clear bad ending: the ride fails,
  the saddle is damaged, and everyone must walk home under a dim sky.

The world is intentionally small, state-driven, and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    wide: bool = True
    windy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicRule:
    id: str
    label: str
    effect: str
    requires: set[str] = field(default_factory=set)
    consumes: set[str] = field(default_factory=set)


@dataclass
class Saddle:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    magic_tags: set[str] = field(default_factory=set)
    strap_strength: int = 1


@dataclass
class StoryParams:
    place: str
    saddle: str
    magic: str
    misunderstanding: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "open_plain": Place(
        id="open_plain",
        label="the wide open plain",
        wide=True,
        windy=True,
        affords={"ride", "gallop", "listen"},
    ),
    "wagon_yard": Place(
        id="wagon_yard",
        label="the wagon yard",
        wide=False,
        windy=False,
        affords={"ride", "listen"},
    ),
    "dusty_hill": Place(
        id="dusty_hill",
        label="the dusty hill",
        wide=True,
        windy=True,
        affords={"ride", "gallop", "listen"},
    ),
}

MAGIC_RULES = {
    "glow": MagicRule(
        id="glow",
        label="glow magic",
        effect="shine bright as a lantern",
        requires={"quiet"},
        consumes=set(),
    ),
    "gentle": MagicRule(
        id="gentle",
        label="gentle magic",
        effect="make a horse calm",
        requires={"placed_right"},
        consumes=set(),
    ),
    "lift": MagicRule(
        id="lift",
        label="lift magic",
        effect="make a saddle feel light",
        requires={"star_touch"},
        consumes=set(),
    ),
}

MISUNDERSTANDINGS = {
    "fly": "that the saddle could make a horse fly",
    "shrink": "that the saddle would shrink itself to fit anything",
    "sing": "that the saddle would sing a guide-song if it was buckled crooked",
}

SADDLES = {
    "star_saddle": Saddle(
        id="star_saddle",
        label="star-scarred saddle",
        phrase="an old star-scarred saddle",
        fits={"horse"},
        magic_tags={"glow", "gentle"},
        strap_strength=1,
    ),
    "copper_saddle": Saddle(
        id="copper_saddle",
        label="copper saddle",
        phrase="a copper saddle with a bright buckle",
        fits={"horse"},
        magic_tags={"lift", "gentle"},
        strap_strength=2,
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Ruby", "June", "Lila", "Nora"]
BOY_NAMES = ["Sam", "Jeb", "Finn", "Owen", "Cal", "Theo"]
TRAITS = ["curious", "bold", "dreamy", "stubborn", "cheery"]

# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------


def saddle_is_reasonable(saddle: Saddle, magic: MagicRule, misunderstanding: str, place: Place) -> bool:
    if "horse" not in saddle.fits:
        return False
    if magic.id not in saddle.magic_tags:
        return False
    if misunderstanding == "fly" and magic.id != "lift":
        return False
    if misunderstanding == "shrink" and saddle.id != "copper_saddle":
        return False
    if misunderstanding == "sing" and magic.id != "glow":
        return False
    if place.id == "wagon_yard" and misunderstanding == "fly":
        return False
    return True


def explain_rejection(saddle: Saddle, magic: MagicRule, misunderstanding: str, place: Place) -> str:
    return (
        f"(No story: {saddle.label} with {magic.label} does not make a reasonable tall tale "
        f"for the misunderstanding {misunderstanding!r} at {place.label}.)"
    )


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------


def _do_magic(world: World, hero: Entity, saddle: Entity, magic: MagicRule, misunderstands: str) -> None:
    sig = ("magic", magic.id, saddle.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    if magic.id == "glow":
        saddle.meters["shine"] = saddle.meters.get("shine", 0.0) + 1
        world.say(f"The saddle gave off a lantern-bright glow, clear as a campfire on a moonless night.")
    elif magic.id == "gentle":
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
        world.say(f"The magic promised to make the ride calm and easy, like a hush over the grass.")
    elif magic.id == "lift":
        saddle.meters["light"] = saddle.meters.get("light", 0.0) + 1
        world.say(f"The saddle felt light as a feather, which was mighty curious indeed.")

    if misunderstands == "fly":
        hero.memes["misbelief"] = hero.memes.get("misbelief", 0.0) + 1
        world.say(f"But {hero.id} misread the sparkle and thought it meant the horse could fly.")
    elif misunderstands == "shrink":
        hero.memes["misbelief"] = hero.memes.get("misbelief", 0.0) + 1
        world.say(f"But {hero.id} mistook the magic for a shrinking trick and hurried too fast.")
    else:
        hero.memes["misbelief"] = hero.memes.get("misbelief", 0.0) + 1
        world.say(f"But {hero.id} thought the glow was a secret song, and the guess was not quite right.")


def _apply_bad_ending(world: World, hero: Entity, parent: Entity, horse: Entity, saddle: Entity, misunderstanding: str) -> None:
    sig = ("bad_ending", saddle.id, misunderstanding)
    if sig in world.fired:
        return
    world.fired.add(sig)

    saddle.meters["damage"] = saddle.meters.get("damage", 0.0) + 1
    horse.memes["spook"] = horse.memes.get("spook", 0.0) + 1
    hero.memes["sadness"] = hero.memes.get("sadness", 0.0) + 1
    parent.meters["repair"] = parent.meters.get("repair", 0.0) + 1

    if misunderstanding == "fly":
        world.say(f"The horse only stamped and snorted, and the old saddle slipped sideways with a slap and a sigh.")
    elif misunderstanding == "shrink":
        world.say(f"The saddle did not shrink at all; it only pinched, twisted, and made the whole plan flop in the dust.")
    else:
        world.say(f"The saddle never sang a guide-song; it only creaked, and the horse backed away in a frightened hurry.")

    world.say(f"By sunset, {hero.id} and {parent.id} had to walk home, leading the horse and carrying the battered saddle low in their arms.")


def _has_bad_ending(world: World, saddle: Entity) -> bool:
    return saddle.meters.get("damage", 0.0) >= THRESHOLD


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, parent: Entity, saddle: Saddle, place: Place) -> str:
    return (
        f"{hero.id} was a {hero.memes.get('trait_word', 'curious')} {hero.type} with a head full of big prairie tales, "
        f"and {parent.id} knew every trail had a secret or two. Near {place.label}, there waited {saddle.phrase}, "
        f"said to be magic as a thundercloud."
    )


def generate_story_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    saddle_cfg = SADDLES[params.saddle]
    magic = MAGIC_RULES[params.magic]
    misunderstanding = params.misunderstanding

    if not saddle_is_reasonable(saddle_cfg, magic, misunderstanding, place):
        raise StoryError(explain_rejection(saddle_cfg, magic, misunderstanding, place))

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait_word": 1.0},
    ))
    parent = world.add(Entity(
        id="AuntMae" if params.parent == "aunt" else "UncleJed" if params.parent == "uncle" else "Parent",
        kind="character",
        type="mother" if params.parent in {"aunt", "mother"} else "father",
    ))
    horse = world.add(Entity(id="Blue", kind="character", type="horse"))
    saddle = world.add(Entity(
        id=saddle_cfg.id,
        type="saddle",
        label=saddle_cfg.label,
        phrase=saddle_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    hero.memes["trait_word"] = 1.0
    world.say(intro_line(hero, parent, saddle_cfg, place))
    world.say(f"{hero.id} loved the saddle because it looked like it had ridden through three sunsets and a lightning storm.")
    world.para()
    world.say(f"One day at {place.label}, {hero.id} found a tiny note tied to the saddle horn.")
    world.say(f"It said the magic would {magic.effect}, but only if the saddle was used the right way.")
    world.say(f"{hero.id} blinked at the note and guessed it meant {MISUNDERSTANDINGS[misunderstanding]}.")
    world.para()
    world.say(f"So {hero.id} brought the saddle out to the horse and tried to make the tall-tale trick happen at once.")
    _do_magic(world, hero, saddle, magic, misunderstanding)
    _apply_bad_ending(world, hero, parent, horse, saddle, misunderstanding)
    world.para()
    if _has_bad_ending(world, saddle):
        world.say(
            f"In the end, the magic was real, but the guess was wrong, and the old saddle ended the day dusty, bent, and silent on the fence rail."
        )
    else:
        world.say(
            f"In the end, the magic never truly took hold, and the saddle sat quiet beside the trail like a riddle nobody solved."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        horse=horse,
        saddle=saddle,
        place=place,
        magic=magic,
        misunderstanding=misunderstanding,
        bad_ending=_has_bad_ending(world, saddle),
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the saddle is compatible with the magic and the
% misunderstanding, and the place can host the tale.
reason(saddle, magic, misunderstanding, place) :-
    saddle_cfg(saddle), magic_rule(magic), misunderstanding_kind(misunderstanding), place_kind(place),
    fits_horse(saddle), magic_tag(saddle, magic), can_happen(place),
    compatible(magic, misunderstanding, saddle, place).

compatible(lift, fly, copper_saddle, open_plain).
compatible(gentle, sing, star_saddle, dusty_hill).
compatible(lift, shrink, copper_saddle, open_plain).
compatible(glow, sing, star_saddle, wagon_yard).
compatible(gentle, shrink, copper_saddle, dusty_hill).

valid_story(P, S, M, U) :- reason(S, M, U, P).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_kind", pid))
        if p.wide:
            lines.append(asp.fact("can_happen", pid))
    for mid, m in MAGIC_RULES.items():
        lines.append(asp.fact("magic_rule", mid))
    for uid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding_kind", uid))
    for sid, s in SADDLES.items():
        lines.append(asp.fact("saddle_cfg", sid))
        lines.append(asp.fact("fits_horse", sid))
        for tag in s.magic_tags:
            lines.append(asp.fact("magic_tag", sid, tag))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set()
    for place in PLACES.values():
        for saddle_id, saddle in SADDLES.items():
            for magic_id, magic in MAGIC_RULES.items():
                for u in MISUNDERSTANDINGS:
                    if saddle_is_reasonable(saddle, magic, u, place):
                        py.add((place.id, saddle_id, magic_id, u))
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall tale for a child about a magic saddle and a misunderstanding, and include the word "saddle".',
        f"Tell a story where {f['hero'].id} finds a magic saddle at {f['place'].label} and guesses the magic wrong.",
        f"Write a simple bad-ending tall tale about {f['hero'].id}, {f['horse'].id}, and a saddle that does not do what was hoped.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    horse: Entity = f["horse"]
    saddle: Entity = f["saddle"]
    place: Place = f["place"]
    magic: MagicRule = f["magic"]
    misunderstanding: str = f["misunderstanding"]

    return [
        QAItem(
            question=f"Who found the magic saddle at {place.label}?",
            answer=f"{hero.id} found the {saddle.label} at {place.label}.",
        ),
        QAItem(
            question=f"What was the magic supposed to do with the saddle?",
            answer=f"It was supposed to {magic.effect}.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand about the magic?",
            answer=f"{hero.id} misunderstood it and thought {MISUNDERSTANDINGS[misunderstanding]}.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The ending was bad because the guess was wrong, the horse got spooked, and the saddle was damaged."
            ),
        ),
        QAItem(
            question=f"What had to happen at the end?",
            answer=(
                f"{hero.id} and {parent.id} had to walk home and carry the battered saddle, while {horse.id} went slowly beside them."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saddle for?",
            answer="A saddle is a seat for riding a horse or another animal, and it helps a rider sit more safely.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets a message wrong and acts on the wrong idea.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic in a story means something surprising or impossible that seems to have special powers.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things do not turn out well and the characters end the story upset, stuck, or disappointed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="open_plain",
        saddle="copper_saddle",
        magic="lift",
        misunderstanding="fly",
        name="Mina",
        gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="dusty_hill",
        saddle="star_saddle",
        magic="glow",
        misunderstanding="sing",
        name="Jeb",
        gender="boy",
        parent="uncle",
    ),
    StoryParams(
        place="wagon_yard",
        saddle="star_saddle",
        magic="glow",
        misunderstanding="sing",
        name="Ruby",
        gender="girl",
        parent="aunt",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a magic saddle and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--saddle", choices=SADDLES)
    ap.add_argument("--magic", choices=MAGIC_RULES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
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
    if args.place and args.saddle and args.magic and args.misunderstanding:
        if not saddle_is_reasonable(SADDLES[args.saddle], MAGIC_RULES[args.magic], args.misunderstanding, PLACES[args.place]):
            raise StoryError(explain_rejection(SADDLES[args.saddle], MAGIC_RULES[args.magic], args.misunderstanding, PLACES[args.place]))

    combos = []
    for place in PLACES.values():
        if args.place and place.id != args.place:
            continue
        for saddle in SADDLES.values():
            if args.saddle and saddle.id != args.saddle:
                continue
            for magic in MAGIC_RULES.values():
                if args.magic and magic.id != args.magic:
                    continue
                for misunderstanding in MISUNDERSTANDINGS:
                    if args.misunderstanding and misunderstanding != args.misunderstanding:
                        continue
                    if saddle_is_reasonable(saddle, magic, misunderstanding, place):
                        combos.append((place.id, saddle.id, magic.id, misunderstanding))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, saddle, magic, misunderstanding = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        place=place,
        saddle=saddle,
        magic=magic,
        misunderstanding=misunderstanding,
        name=name,
        gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.saddle} / {p.magic} / {p.misunderstanding} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
