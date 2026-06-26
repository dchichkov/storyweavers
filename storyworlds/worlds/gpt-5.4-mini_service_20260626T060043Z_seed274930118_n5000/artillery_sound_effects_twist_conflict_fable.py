#!/usr/bin/env python3
"""
storyworlds/worlds/artillery_sound_effects_twist_conflict_fable.py
===================================================================

A small fable-like storyworld about a village, an old artillery piece, and the
sound effects that turn a warning into a surprise.

Seed image:
---
A careful hare hears an old cannon in the hillfort. The cannon's boom scares
the birds, but the sound also wakes the mill wheel before a storm. The twist is
that the cannon was not for battle at all: it was the keeper's loud way to call
everyone in when the floodwater rose. The conflict is between fear of the boom
and the need to listen to it.

World model:
---
- Physical meters: distance, volume, wetness, readiness, floodwater, rope_tension
- Emotional memes: fear, trust, pride, relief, urgency, stubbornness

The world is intentionally tiny and constraint-checked:
- an artillery piece must have a safe purpose,
- its sound effect must be loud enough to matter,
- the twist must change the meaning of the boom,
- the ending must show a changed state, not just a repeat of the premise.

The prose aims for a fable tone: simple, concrete, and with a gentle lesson.
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
# Shared domain constants
# ---------------------------------------------------------------------------

SOUND_EFFECTS = [
    "BOOM",
    "CRACK",
    "BANG",
    "THOOM",
]

TWISTS = [
    "It was not a battle signal at all.",
    "The loud blast was a warning for the village.",
    "The old gun was used to call people home before the flood.",
]

CONFLICTS = [
    "The hare thought the boom meant danger.",
    "The birds hated the noise and flew away in a panic.",
    "The miller feared the cannon would frighten everyone.",
]

MORALS = [
    "It is wise to listen before you fear.",
    "A loud sound can be a help, not only a threat.",
    "Caution is better when it is guided by trust.",
]


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.meters.get("gender", 0)
        if gender == 1:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == 2:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    near_water: bool = False
    high_ground: bool = False
    has_mill: bool = False
    has_fort: bool = False


@dataclass
class Artillery:
    id: str
    label: str
    sound: str
    role: str  # "warning" | "battle" | "festival"
    loudness: float
    recoil: float
    safe: bool = True


@dataclass
class StoryParams:
    place: str
    character: str
    artillery: str
    sound_effect: str
    twist: str
    conflict: str
    moral: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.artillery: Optional[Artillery] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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

    def record(self, msg: str) -> None:
        self.trace.append(msg)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hillfort": Place(name="the hillfort", high_ground=True, has_fort=True),
    "riverside": Place(name="the riverside", near_water=True, has_mill=True),
    "village": Place(name="the village green"),
}

CHARACTERS = {
    "hare": {"type": "hare", "gender": 0, "traits": ["quick", "wary", "kind"]},
    "miller": {"type": "miller", "gender": 2, "traits": ["busy", "proud", "careful"]},
    "heron": {"type": "heron", "gender": 0, "traits": ["tall", "silent", "thoughtful"]},
    "fox": {"type": "fox", "gender": 2, "traits": ["clever", "restless", "bold"]},
}

ARTILLERY_REGISTRY = {
    "watch_cannon": Artillery(
        id="watch_cannon",
        label="an old watch cannon",
        sound="boom",
        role="warning",
        loudness=9.0,
        recoil=3.0,
        safe=True,
    ),
    "festival_cannon": Artillery(
        id="festival_cannon",
        label="a festival cannon",
        sound="BANG",
        role="festival",
        loudness=8.0,
        recoil=2.0,
        safe=True,
    ),
}

SOUND_TO_EFFECT = {
    "boom": "BOOM",
    "bang": "BANG",
    "crack": "CRACK",
    "thoom": "THOOM",
}


# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.character not in CHARACTERS:
        raise StoryError(f"Unknown character: {params.character}")
    if params.artillery not in ARTILLERY_REGISTRY:
        raise StoryError(f"Unknown artillery: {params.artillery}")
    world = World(PLACES[params.place])
    art = ARTILLERY_REGISTRY[params.artillery]
    world.artillery = art

    ch = CHARACTERS[params.character]
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=ch["type"],
        phrase=f"a {', '.join(ch['traits'][:2])} {ch['type']}",
        meters={"gender": ch["gender"], "distance": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "pride": 0.0, "relief": 0.0, "urgency": 0.0},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        label="keeper",
        phrase="the old keeper",
        meters={"gender": 0, "distance": 0.0},
        memes={"trust": 0.0, "urgency": 0.0},
    ))
    villagers = world.add(Entity(
        id="villagers",
        kind="character",
        label="villagers",
        phrase="the villagers",
        plural=True,
        meters={"distance": 0.0},
        memes={"fear": 0.0, "relief": 0.0},
    ))

    world.facts.update(hero=hero, keeper=keeper, villagers=villagers)
    return world


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def opening(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    place = world.place.name
    art = world.artillery
    world.say(
        f"Once in {place}, there lived {hero.phrase}. "
        f"{hero.pronoun('subject').capitalize()} liked quiet mornings and knew every path by heart."
    )
    world.say(
        f"On the hill stood {art.label}, and when it spoke, it made a sharp {params.sound_effect}."
    )
    hero.memes["fear"] += 1
    world.record("hero hears artillery and feels fear")
    world.say(
        f"The sound made {hero.pronoun('object')} jump, because the boom was louder than the birds and the wind."
    )


def conflict_scene(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    villagers = world.get("villagers")
    place = world.place

    world.para()
    world.say(
        f"{params.conflict} {hero.pronoun('subject').capitalize()} wished the cannon would stay silent."
    )
    if place.near_water or place.has_mill:
        world.say(
            f"But the river kept rising, and the mill wheel started to groan under the wet weight."
        )
    else:
        world.say(
            f"Then dark clouds rolled in, and the air grew heavy with rain."
        )

    hero.meters["distance"] = 1.0
    hero.memes["urgency"] += 1
    keeper.memes["urgency"] += 1
    villagers.memes["fear"] += 1
    world.record("flood warning begins")


def twist_scene(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    art = world.artillery
    world.para()
    world.say(
        f"{params.twist} The keeper shouted that the cannon was the village's loud bell."
    )
    world.say(
        f'When the keeper touched the old rope, it answered with a waiting {SOUND_TO_EFFECT.get(art.sound, params.sound_effect)}.'
    )
    hero.memes["trust"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    world.record("twist reveals warning purpose")


def resolution_scene(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    villagers = world.get("villagers")
    art = world.artillery

    world.para()
    world.say(
        f"{hero.pronoun('subject').capitalize()} listened this time, and {hero.pronoun('subject')} ran to warn the others."
    )
    world.say(
        f"The cannon gave one last {params.sound_effect}, and the people hurried to the high ground with dry bread, rope, and lanterns."
    )
    villagers.memes["relief"] += 2
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    world.facts["ending_state"] = "safe"
    world.record("village reaches safety")
    world.para()
    world.say(
        f"By nightfall the water stayed below the doors, and the little hare could hear only the river and the crickets."
    )
    world.say(
        f"{params.moral} That was how the loud cannon became a friend instead of a fright."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    art = world.artillery
    if art is None:
        raise StoryError("Missing artillery in world state.")
    if art.loudness < 7.0:
        raise StoryError("The artillery must be loud enough to drive the story.")
    if art.role not in {"warning", "festival"}:
        raise StoryError("The artillery role must support a fable-like turn.")

    opening(world, params)
    conflict_scene(world, params)
    twist_scene(world, params)
    resolution_scene(world, params)
    return world


# ---------------------------------------------------------------------------
# Story quality and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    art = world.artillery
    return [
        f"Write a short fable about {hero.label} and {art.label} with a loud sound effect.",
        f"Tell a child-friendly story where a boom turns out to be a helpful warning.",
        f"Write a fable-like tale about fear, a twist, and a village being kept safe by artillery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    art = world.artillery
    return [
        QAItem(
            question="What first made the hare nervous in the story?",
            answer=f"The hare was nervous because {art.label} made a loud {art.sound.upper()} and sounded like danger.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the loud cannon was not for battle; it was used to warn the village about rising water.",
        ),
        QAItem(
            question="How did the hero change by the end?",
            answer=f"At the end, the hare stopped fearing the boom so much and helped warn the villagers, so {hero.pronoun('subject')} became brave and useful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is artillery?",
            answer="Artillery is a large weapon, like a cannon, that can fire loud shots. In stories, it can also be used as a warning signal.",
        ),
        QAItem(
            question="Why do sound effects matter in stories?",
            answer="Sound effects matter because they help readers imagine how loud, sharp, or surprising a moment feels.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprise that changes what you thought was happening.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or worry that makes the story tense before it gets better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"artillery: {world.artillery}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    lines.extend(world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
character(C) :- hero(C).
artillery(A) :- artillery_piece(A).

loud(A) :- artillery_piece(A), loudness(A,N), N >= 7.
conflict(C) :- character(C), fear(C,F), F >= 1.
twist(T) :- twist_fact(T).

warning_story :- loud(A), warning_role(A), rising_water, conflict(hero), twist(t1).
resolved_story :- warning_story, trust(hero,T), T >= 1, relief(villagers,R), R >= 1.

#show warning_story/0.
#show resolved_story/0.
"""

def asp_facts() -> str:
    import asp
    world = {
        "setting": "setting",
    }
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.near_water:
            lines.append(asp.fact("near_water", pid))
        if place.high_ground:
            lines.append(asp.fact("high_ground", pid))
        if place.has_mill:
            lines.append(asp.fact("has_mill", pid))
        if place.has_fort:
            lines.append(asp.fact("has_fort", pid))
    for aid, art in ARTILLERY_REGISTRY.items():
        lines.append(asp.fact("artillery_piece", aid))
        lines.append(asp.fact("sound", aid, art.sound))
        lines.append(asp.fact("warning_role", aid) if art.role == "warning" else asp.fact("role", aid, art.role))
        lines.append(asp.fact("loudness", aid, int(art.loudness)))
    lines.append(asp.fact("rising_water"))
    lines.append(asp.fact("twist_fact", "t1"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("fear", "hero", 1))
    lines.append(asp.fact("trust", "hero", 1))
    lines.append(asp.fact("villagers"))
    lines.append(asp.fact("relief", "villagers", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warning_story/0. #show resolved_story/0."))
    atoms = {sym.name for sym in model}
    if "warning_story" in atoms and "resolved_story" in atoms:
        print("OK: ASP gate recognizes the warning-and-resolution story.")
        return 0
    print("MISMATCH: ASP gate did not produce the expected story shape.")
    return 1


# ---------------------------------------------------------------------------
# Param selection and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable storyworld about artillery, sound effects, twist, and conflict."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--character", choices=CHARACTERS)
    ap.add_argument("--artillery", choices=ARTILLERY_REGISTRY)
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--moral", choices=MORALS)
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
    place = args.place or rng.choice(list(PLACES))
    character = args.character or rng.choice(list(CHARACTERS))
    artillery = args.artillery or rng.choice(list(ARTILLERY_REGISTRY))
    sound_effect = args.sound_effect or SOUND_EFFECTS[0]
    twist = args.twist or rng.choice(TWISTS)
    conflict = args.conflict or rng.choice(CONFLICTS)
    moral = args.moral or rng.choice(MORALS)

    if artillery == "festival_cannon" and place == "riverside":
        raise StoryError("Festival cannon stories do not fit the flood-warning riverside premise.")
    if artillery == "watch_cannon" and "battle" in twist.lower():
        raise StoryError("The watch cannon story should stay child-friendly and avoid battle framing.")

    return StoryParams(
        place=place,
        character=character,
        artillery=artillery,
        sound_effect=sound_effect,
        twist=twist,
        conflict=conflict,
        moral=moral,
    )


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

CURATED = [
    StoryParams(
        place="riverside",
        character="hare",
        artillery="watch_cannon",
        sound_effect="BOOM",
        twist="It was not a battle signal at all.",
        conflict="The hare thought the boom meant danger.",
        moral="It is wise to listen before you fear.",
    )
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show warning_story/0. #show resolved_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show warning_story/0. #show resolved_story/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
