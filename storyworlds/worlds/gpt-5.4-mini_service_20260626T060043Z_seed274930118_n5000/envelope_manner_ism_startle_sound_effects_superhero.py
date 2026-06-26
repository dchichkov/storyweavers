#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/envelope_manner_ism_startle_sound_effects_superhero.py
====================================================================================================================================

A small superhero-story world about an envelope, a distinctive manner-ism, a
startle, and loud sound effects that help the hero turn a mistake into a save.

Premise:
- A young superhero admires a brave helper with a peculiar manner-ism.
- A sealed envelope carries an important note to a place where it must arrive.
- A sudden startle and noisy sound effects make the delivery go wrong.
- The hero uses calm, gear, and action to recover the envelope and finish the job.

This world is deliberately compact: it models just enough physical state
(meters) and emotional state (memes) to generate a complete child-facing story.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Hero:
    name: str
    type: str
    manner_ism: str
    costume: str
    seed_word: str = "envelope"


@dataclass
class StoryParams:
    name: str
    gender: str
    mannerism: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    sidekick: Entity
    envelope: Entity
    place: str
    note: str
    mannerism: str
    startled_by: str
    sound_effects: list[str]
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

    def copy(self) -> "World":
        import copy as _copy
        return World(
            hero=_copy.deepcopy(self.hero),
            sidekick=_copy.deepcopy(self.sidekick),
            envelope=_copy.deepcopy(self.envelope),
            place=self.place,
            note=self.note,
            mannerism=self.mannerism,
            startled_by=self.startled_by,
            sound_effects=list(self.sound_effects),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
        )


PLACES = [
    "the city rooftop",
    "the bright museum hall",
    "the busy corner store",
    "the train platform",
    "the school courtyard",
]

MANNERISMS = [
    "taps one glove twice before speaking",
    "straightens the cape with two quick tugs",
    "nods once, then twice, like a drum beat",
    "points at the sky before every brave plan",
    "snaps the wrist open like a flag before running",
]

SOUND_EFFECTS = [
    "BAM!",
    "WHAM!",
    "ZIP!",
    "CRACK!",
    "POW!",
    "WHOOSH!",
    "KRAK!",
]

NAMES = {
    "girl": ["Ava", "Maya", "Nina", "Luna", "Zoe"],
    "boy": ["Leo", "Max", "Eli", "Noah", "Finn"],
}

COLORS = ["red", "blue", "gold", "green", "silver"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with an envelope, a manner-ism, and a startle.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mannerism", choices=MANNERISMS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _hero_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _hero_name(gender, rng)
    mannerism = args.mannerism or rng.choice(MANNERISMS)
    return StoryParams(name=name, gender=gender, mannerism=mannerism)


def _startle_phrase(startled_by: str, effects: list[str]) -> str:
    return f"{random.choice(effects)} {startled_by} made everyone jump."


def _make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed or 0)
    hero = Entity(id=params.name, kind="character", type=params.gender, meters={"speed": 0.0}, memes={"bravery": 1.0, "calm": 0.5})
    sidekick = Entity(id="Sidekick", kind="character", type="boy" if params.gender == "girl" else "girl", meters={"speed": 0.0}, memes={"admiration": 1.0})
    envelope = Entity(
        id="envelope",
        type="envelope",
        label="envelope",
        phrase="a sealed envelope with a red star",
        owner=hero.id,
        carrier=hero.id,
        protective=False,
        meters={"safe": 1.0, "torn": 0.0, "wet": 0.0},
    )
    place = rng.choice(PLACES)
    note = rng.choice([
        "a map to the hidden clocktower",
        "a thank-you note for the mayor",
        "a rescue request for the library roof",
        "a clue about the missing kitten",
        "a message for the parade captain",
    ])
    startled_by = rng.choice([
        "a loud scooter horn",
        "a sudden cat leap",
        "a popping balloon",
        "a clattering trash lid",
        "a burst of siren noise",
    ])
    effects = [rng.choice(SOUND_EFFECTS) for _ in range(3)]
    return World(hero=hero, sidekick=sidekick, envelope=envelope, place=place, note=note,
                 mannerism=params.mannerism, startled_by=startled_by, sound_effects=effects)


def _do_setup(world: World) -> None:
    h = world.hero
    s = world.sidekick
    e = world.envelope
    world.say(f"{h.id} was a little superhero who always {world.mannerism}.")
    world.say(f"{s.id} loved that manner-ism, because it made {h.id} look ready for action.")
    world.say(f"One morning, {h.id} carried {e.phrase} to {world.place}, where {e.owner}'s important note needed to arrive.")
    world.say(f"Inside was {world.note}.")


def _do_conflict(world: World) -> None:
    h = world.hero
    e = world.envelope
    h.memes["focus"] = 1.0
    world.para()
    world.say(f"Then came a startle: {world.startled_by}.")
    world.say(f"{' '.join(world.sound_effects[:2])} The noise bounced through the air, and {h.id} flinched so hard that {e.label} slipped.")
    e.carrier = None
    e.meters["safe"] = 0.0
    e.meters["torn"] += 1.0
    h.memes["worry"] = 1.0
    world.say(f"The envelope bumped the pavement and got a little bent.")


def _do_turn(world: World) -> None:
    h = world.hero
    s = world.sidekick
    e = world.envelope
    world.para()
    world.say(f"{s.id} pointed at the envelope and said, \"Your message can still be saved!\"")
    world.say(f"{h.id} took one slow breath, then did {world.mannerism}.")
    world.say(f"{world.sound_effects[2]} {h.id} darted after the envelope, scooped it up, and tucked it safely against {h.pronoun('possessive')} chest.")
    e.carrier = h.id
    e.meters["safe"] = 1.0
    if e.meters["torn"] > 0:
        world.say(f"{h.id} pressed the bent flap flat and kept the note dry and steady.")
    h.memes["worry"] = 0.0
    h.memes["bravery"] += 1.0


def _do_resolution(world: World) -> None:
    h = world.hero
    e = world.envelope
    world.para()
    world.say(f"At last, {h.id} reached {world.place} and delivered {e.label} with a proud smile.")
    world.say(f"The note was still readable, and the day ended with {h.id} and {world.sidekick.id} grinning under a sky full of quiet hero wind.")
    world.say(f"{world.sound_effects[1]} {world.sound_effects[0]} felt like a victory drum, and the envelope stayed safe at the finish.")


def generate_story(params: StoryParams) -> World:
    world = _make_world(params)
    _do_setup(world)
    _do_conflict(world)
    _do_turn(world)
    _do_resolution(world)
    world.facts = {
        "place": world.place,
        "mannerism": world.mannerism,
        "note": world.note,
        "startled_by": world.startled_by,
        "sound_effects": list(world.sound_effects),
        "hero": world.hero,
        "sidekick": world.sidekick,
        "envelope": world.envelope,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short superhero story for a young child that includes the word "envelope" and the sound effect "{world.sound_effects[0]}".',
        f"Tell a gentle superhero story about {world.hero.id}, who has a special manner-ism and must save an envelope after a startle.",
        f"Write a story where a small hero at {world.place} hears {world.startled_by}, uses calm breathing, and keeps an envelope safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    s = world.sidekick
    e = world.envelope
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {h.id}, a little {h.type} who {world.mannerism}.",
        ),
        QAItem(
            question=f"What was inside the envelope?",
            answer=f"Inside the envelope was {world.note}.",
        ),
        QAItem(
            question=f"What made the envelope slip?",
            answer=f"A startle from {world.startled_by} and the noisy sound effects made {h.id} flinch, so the envelope slipped.",
        ),
        QAItem(
            question=f"How did the hero save the envelope?",
            answer=f"{h.id} took a slow breath, used {world.mannerism}, chased the envelope, and tucked it safely against {h.pronoun('possessive')} chest.",
        ),
        QAItem(
            question=f"How did {s.id} help?",
            answer=f"{s.id} encouraged {h.id} and reminded {h.id} that the message could still be saved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an envelope for?",
            answer="An envelope is a paper cover that helps carry a letter or note from one place to another.",
        ),
        QAItem(
            question="What is a manner-ism?",
            answer="A manner-ism is a small repeated action a person does, like a special way of standing, tapping, or speaking.",
        ),
        QAItem(
            question="What does it mean to startle someone?",
            answer="To startle someone means to surprise them suddenly so they jump or flinch for a moment.",
        ),
        QAItem(
            question="Why do superhero stories use sound effects?",
            answer="Superhero stories use sound effects like BAM or WHOOSH to make action feel loud, fast, and exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    e = world.envelope
    h = world.hero
    lines = [
        "--- world trace ---",
        f"hero={h.id} type={h.type} meters={h.meters} memes={h.memes}",
        f"sidekick={world.sidekick.id} type={world.sidekick.type} meters={world.sidekick.meters} memes={world.sidekick.memes}",
        f"envelope carrier={e.carrier} meters={e.meters}",
        f"place={world.place}",
        f"startled_by={world.startled_by}",
    ]
    return "\n".join(lines)


ASP_RULES = r"""
hero(h).
envelope(e).
startle(s).
sound_effect(x).
sound_effect(y).
sound_effect(z).

requires_calm(h) :- startle(s).
can_save(h,e) :- requires_calm(h), envelope(e).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "h"),
        asp.fact("envelope", "e"),
        asp.fact("startle", "s"),
        asp.fact("sound_effect", "x"),
        asp.fact("sound_effect", "y"),
        asp.fact("sound_effect", "z"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show can_save/2."))
    ok = any(a.name == "can_save" for a in model)
    if ok:
        print("OK: ASP sanity check passed.")
        return 0
    print("MISMATCH: ASP sanity check failed.")
    return 1


def resolve_story(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate_world(params: StoryParams) -> World:
    return generate_story(params)


def generate(params: StoryParams) -> StorySample:
    return resolve_story(params)


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
        print(asp_program("#show can_save/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Ava", gender="girl", mannerism=MANNERISMS[0], seed=base_seed),
            StoryParams(name="Leo", gender="boy", mannerism=MANNERISMS[2], seed=base_seed + 1),
            StoryParams(name="Maya", gender="girl", mannerism=MANNERISMS[4], seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
