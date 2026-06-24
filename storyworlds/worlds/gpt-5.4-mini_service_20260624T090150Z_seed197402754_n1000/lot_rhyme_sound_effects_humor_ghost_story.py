#!/usr/bin/env python3
"""
A tiny story world about a spooky lot with rhyme, sound effects, and gentle humor.

Premise:
A child visits a lot at dusk, hears strange sounds, gets briefly spooked, and
discovers the "ghost" is something funny and harmless.

The world simulates:
- physical meters: eerie, noise, courage, relief, mess? (no mess here)
- emotional memes: fear, curiosity, bravery, laughter, friendship

The story is driven by state:
- a spooky sound raises fear and eerie mood
- a rhyme helps the child stay brave
- the final reveal turns fear into laughter
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Lot:
    place: str = "the empty lot"
    nearby: str = "a creaky fence"
    affords: set[str] = field(default_factory=lambda: {"rhyme", "sound_effects", "humor"})


@dataclass
class RhymeTool:
    id: str
    label: str
    chant: str
    effect: str
    boosts: dict[str, float] = field(default_factory=dict)


@dataclass
class SoundSource:
    id: str
    label: str
    sound: str
    clue: str
    reveal: str
    effect: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, lot: Lot) -> None:
        self.lot = lot
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        w = World(self.lot)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------

LOT = Lot()

HEROES = {
    "milo": ("Milo", "boy"),
    "maya": ("Maya", "girl"),
    "noah": ("Noah", "boy"),
    "luna": ("Luna", "girl"),
}

RHYMES = [
    RhymeTool(
        id="courage_chant",
        label="a courage rhyme",
        chant="When the lot goes creak and groan, I am brave and not alone.",
        effect="bravery",
        boosts={"courage": 1.0, "fear": -1.0},
    ),
    RhymeTool(
        id="silly_song",
        label="a silly rhyme",
        chant="If a ghost says boo, I say doo-doo-doo!",
        effect="laugh",
        boosts={"laughter": 1.0, "fear": -0.5},
    ),
    RhymeTool(
        id="night_verse",
        label="a night rhyme",
        chant="Little moon, round and bright, keep my feet and heart alight.",
        effect="calm",
        boosts={"courage": 0.5, "curiosity": 0.5, "fear": -0.5},
    ),
]

SOUNDS = {
    "rattle": SoundSource(
        id="rattle",
        label="a rickety cart",
        sound="rattle-clack-rattle",
        clue="its loose wheel on the gravel",
        reveal="the cart was dragging a metal tin lid behind it",
        effect={"eerie": 1.0, "fear": 1.0},
    ),
    "whoosh": SoundSource(
        id="whoosh",
        label="a hanging tarp",
        sound="whoooosh",
        clue="the wind under a torn sheet",
        reveal="the tarp was flapping like a giant sleepy wing",
        effect={"eerie": 0.8, "fear": 0.8},
    ),
    "tap": SoundSource(
        id="tap",
        label="a loose sign",
        sound="tap-tap-tap",
        clue="a sign knocking on its post",
        reveal="the sign kept tapping because it was not tied tight",
        effect={"eerie": 0.4, "fear": 0.2, "humor": 0.4},
    ),
}

CURATED_SOUND_KEYS = ["rattle", "whoosh", "tap"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sound: str
    rhyme: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hero_key, (name, htype) in HEROES.items():
        for sound_id in SOUNDS:
            for rhyme_id in range(len(RHYMES)):
                if sound_id in SOUNDS and rhyme_id < len(RHYMES):
                    combos.append((hero_key, sound_id, RHYMES[rhyme_id].id))
    return combos


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason})"


ASP_RULES = r"""
hero(H) :- hero_name(H).
sound(S) :- sound_id(S).
rhyme(R) :- rhyme_id(R).

valid(H,S,R) :- hero(H), sound(S), rhyme(R).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in HEROES:
        lines.append(asp.fact("hero_name", key))
    for key in SOUNDS:
        lines.append(asp.fact("sound_id", key))
    for rhyme in RHYMES:
        lines.append(asp.fact("rhyme_id", rhyme.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    world = World(LOT)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"courage": 0.0, "eerie": 0.0, "noise": 0.0, "relief": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "laughter": 0.0, "bravery": 0.0},
    ))
    rhyme = next(r for r in RHYMES if r.id == params.rhyme)
    source = SOUNDS[params.sound]
    world.facts.update(hero=hero, rhyme=rhyme, source=source, params=params)
    return world


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    world.say(
        f"{hero.label} found the empty lot at dusk, where the grass was thin and "
        f"{world.lot.nearby} leaned in the wind."
    )
    world.say(
        f"{hero.pronoun().capitalize()} did not come to be scared. "
        f"{hero.pronoun().capitalize()} came because the lot was a little bit odd, and odd things were interesting."
    )


def first_sound(world: World) -> None:
    hero = world.facts["hero"]
    source = world.facts["source"]
    hero.meters["eerie"] += source.effect.get("eerie", 0.0)
    hero.meters["noise"] += 1.0
    hero.memes["fear"] += source.effect.get("fear", 0.0)
    hero.memes["curiosity"] += 0.5
    world.say(
        f"Then came a sound: {source.sound}! "
        f"{hero.label} froze and listened."
    )
    world.say(
        f"It sounded like {source.clue}, and that made the lot feel spooky."
    )


def rhyme_help(world: World) -> None:
    hero = world.facts["hero"]
    rhyme = world.facts["rhyme"]
    hero.memes["bravery"] += rhyme.boosts.get("courage", 0.0)
    hero.memes["fear"] += rhyme.boosts.get("fear", 0.0)
    hero.memes["laughter"] += rhyme.boosts.get("laugh", 0.0)
    hero.memes["curiosity"] += rhyme.boosts.get("curiosity", 0.0)
    hero.meters["courage"] += rhyme.boosts.get("courage", 0.0)
    world.say(
        f"To stay brave, {hero.label} whispered a rhyme:"
    )
    world.say(f'"{rhyme.chant}"')
    world.say(
        f"The little verse did not chase the dark away, but it made {hero.label}'s knees feel less wobbly."
    )


def reveal_and_joke(world: World) -> None:
    hero = world.facts["hero"]
    source = world.facts["source"]
    hero.memes["curiosity"] += 0.5
    hero.meters["eerie"] = max(0.0, hero.meters["eerie"] - 0.5)
    world.say(
        f"{hero.label} followed the sound step by step: crunch, crunch, tip-toe, stop."
    )
    world.say(
        f"At last, the mystery showed itself. {source.reveal}."
    )
    hero.memes["laughter"] += 1.0
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.meters["relief"] += 1.0
    world.say(
        f"{hero.label} blinked, then laughed. 'So the ghost was just a noisy cart!'\n"
        f"Even the fence seemed to grin."
    )
    world.say(
        f"The lot was still a little spooky, but now it was the kind of spooky that made a story better."
    )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    introduce(world)
    world.para()
    first_sound(world)
    rhyme_help(world)
    world.para()
    reveal_and_joke(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short ghost story for children set in an empty lot, with a funny twist, and include the sound "{SOUNDS[p.sound].sound}".',
        f"Tell a rhyme-filled spooky story about {p.hero_name} who hears a strange noise in a lot and learns it is harmless.",
        f"Write a gentle story with sound effects, rhyme, and humor where a child investigates a mystery in the lot and laughs at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    source = world.facts["source"]
    rhyme = world.facts["rhyme"]
    return [
        QAItem(
            question=f"Where did {hero.label} go in the story?",
            answer=f"{hero.label} went to the empty lot at dusk, where the fence and the wind made everything feel spooky."
        ),
        QAItem(
            question=f"What sound did {hero.label} hear?",
            answer=f"{hero.label} heard {source.sound}, which sounded like {source.clue}."
        ),
        QAItem(
            question=f"What did {hero.label} say or do to feel braver?",
            answer=f"{hero.label} whispered a rhyme: {rhyme.chant} It helped {hero.pronoun('object')} feel steadier before finding the answer."
        ),
        QAItem(
            question=f"What was the spooky mystery really?",
            answer=f"The spooky mystery was not a ghost at all; it was {source.reveal}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} laughing, because the scary sound turned out to be silly and harmless."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lot?",
            answer="A lot is an open piece of land, often empty or partly empty, where people might notice fences, weeds, or old things."
        ),
        QAItem(
            question="Why are sound effects useful in a ghost story?",
            answer="Sound effects help the reader imagine what is happening and make the story feel spooky, funny, or exciting."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words that sound alike at the end, like a little song or chant."
        ),
        QAItem(
            question="Why can ghost stories be funny sometimes?",
            answer="Ghost stories can be funny when the spooky thing turns out to be harmless or silly, so the reader laughs after feeling a little scared."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# StorySample interface
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_key = args.hero or rng.choice(list(HEROES))
    hero_name, hero_type = HEROES[hero_key]
    sound = args.sound or rng.choice(list(SOUNDS))
    rhyme = args.rhyme or rng.choice([r.id for r in RHYMES])
    return StoryParams(hero_name=hero_name, hero_type=hero_type, sound=sound, rhyme=rhyme)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world set in an empty lot.")
    ap.add_argument("--hero", choices=HEROES.keys())
    ap.add_argument("--sound", choices=SOUNDS.keys())
    ap.add_argument("--rhyme", choices=[r.id for r in RHYMES])
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


CURATED = [
    StoryParams(hero_name="Maya", hero_type="girl", sound="rattle", rhyme="courage_chant"),
    StoryParams(hero_name="Milo", hero_type="boy", sound="whoosh", rhyme="silly_song"),
    StoryParams(hero_name="Luna", hero_type="girl", sound="tap", rhyme="night_verse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
