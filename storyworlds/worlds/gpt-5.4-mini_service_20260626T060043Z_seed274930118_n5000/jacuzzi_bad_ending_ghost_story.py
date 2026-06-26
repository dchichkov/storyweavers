#!/usr/bin/env python3
"""
storyworlds/worlds/jacuzzi_bad_ending_ghost_story.py
====================================================

A small standalone story world: a spooky ghost story centered on a jacuzzi,
with a bad ending that is still coherent and state-driven.

Premise:
- A child visits a quiet room with a warm jacuzzi.
- A ghost story element makes the place feel eerie.
- The child ignores caution and follows a strange clue.
- The jacuzzi turns out to be unsafe and the ending stays bad.

This script models the story as a tiny world of typed entities with physical
meters and emotional memes. The prose is authored from the world state, not
from a frozen template swap.

The ASP twin mirrors the same reasonableness gate: only stories where the
jacuzzi is actually relevant, eerie, and capable of causing the ending are
considered valid.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("wet", 0.0)
        self.meters.setdefault("cold", 0.0)
        self.meters.setdefault("danger", 0.0)
        self.meters.setdefault("broken", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("warning", 0.0)
        self.memes.setdefault("regret", 0.0)
        self.memes.setdefault("relief", 0.0)
        self.memes.setdefault("sadness", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    place: str = "the old hotel"
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    eerie: bool = True
    has_jacuzzi: bool = True
    has_ghost: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hotel": Setting(place="the old hotel", eerie=True, has_jacuzzi=True, has_ghost=True),
    "spa": Setting(place="the empty spa", eerie=True, has_jacuzzi=True, has_ghost=True),
    "basement": Setting(place="the basement room", eerie=True, has_jacuzzi=True, has_ghost=True),
}

GHOSTS = {
    "whisperer": {
        "name": "the whispering ghost",
        "sound": "a thin whisper that slid through the steam",
        "clue": "the water rippled by itself",
        "mood": "cold and watchful",
    },
    "lady": {
        "name": "the pale lady",
        "sound": "a soft sigh from the tiled corner",
        "clue": "a wet handprint appeared on the glass",
        "mood": "sad and far away",
    },
    "boy": {
        "name": "the little ghost boy",
        "sound": "a tiny laugh from under the bubbles",
        "clue": "the bubbles popped in a strange pattern",
        "mood": "restless and lonely",
    },
}

COMPA NIONS = {
    "grandma": {"label": "grandma", "type": "woman"},
    "dad": {"label": "dad", "type": "man"},
    "aunt": {"label": "aunt", "type": "woman"},
}

# fixed typo-safe alias
COMPANIONS = COMPA NIONS  # type: ignore

# The jacuzzi is the central object.
JACUZZI = {
    "jacuzzi": {
        "label": "jacuzzi",
        "phrase": "a warm bubbling jacuzzi",
        "type": "jacuzzi",
    }
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def setting_detail(setting: Setting) -> str:
    if setting.place == "the old hotel":
        return "The hallway smelled like dust, lemon soap, and something forgotten."
    if setting.place == "the empty spa":
        return "The spa was too quiet, and even the lights seemed to hum softly."
    return "The basement room felt chilly, with pipes ticking behind the walls."


def intro_line(hero: Entity, companion: Entity, setting: Setting) -> str:
    return (
        f"{hero.id} was a little {hero.type} who had come to {setting.place} with "
        f"{companion.label}."
    )


def ghost_line(ghost: dict) -> str:
    return f"Near the jacuzzi, {ghost['name']} left behind {ghost['sound']}."


def want_line(hero: Entity) -> str:
    hero.memes["curiosity"] += 1
    return f"{hero.id} leaned closer. {hero.pronoun().capitalize()} wanted to see why the bubbling never stopped."


def warning_line(companion: Entity, ghost: dict) -> str:
    companion.memes["warning"] += 1
    return f'"Do not go near it," {companion.label} said. "Something about that jacuzzi feels wrong."'


def approach_jacuzzi(world: World, hero: Entity, ghost: dict) -> None:
    jacuzzi = world.get("jacuzzi")
    hero.memes["fear"] += 1
    jacuzzi.meters["danger"] += 1
    jacuzzi.meters["wet"] += 1
    ghost_ent = world.get("ghost")
    ghost_ent.meters["danger"] += 1
    world.say(f"{hero.id} ignored the warning and stepped closer anyway.")
    world.say(f"The steam curled up around {hero.pronoun('object')} like a pale blanket.")
    world.say(f"Then {ghost['clue']}.")


def bad_ending(world: World, hero: Entity, companion: Entity) -> None:
    jacuzzi = world.get("jacuzzi")
    ghost_ent = world.get("ghost")
    hero.memes["regret"] += 1
    hero.memes["sadness"] += 1
    jacuzzi.meters["broken"] += 1
    ghost_ent.meters["danger"] += 1
    world.say(
        f"The bubbles stopped all at once, and the room went cold. "
        f"{hero.id} felt {hero.pronoun('possessive')} heart sink."
    )
    world.say(
        f"The ghost did not smile or help. It simply faded into the dark steam, "
        f"and {hero.id} was left shivering beside the silent jacuzzi."
    )
    world.say(
        f"{companion.label} hurried over too late. By then, the water was still, "
        f"the room was eerie, and nobody wanted to stay."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=COMPANIONS[params.companion]["type"],
        label=COMPANIONS[params.companion]["label"],
    ))
    jacuzzi = world.add(Entity(
        id="jacuzzi",
        kind="thing",
        type="jacuzzi",
        label="jacuzzi",
        phrase="a warm bubbling jacuzzi",
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="thing",
        type="ghost",
        label="ghost",
        phrase=GHOSTS["whisperer"]["name"],
    ))

    world.facts.update(
        hero=hero,
        companion=companion,
        jacuzzi=jacuzzi,
        ghost=ghost,
        ghost_cfg=GHOSTS["whisperer"],
        setting=setting,
    )

    # Act 1
    world.say(intro_line(hero, companion, setting))
    world.say(setting_detail(setting))
    world.say(f"There was {jacuzzi.phrase} waiting in a tiled room.")
    world.say(ghost_line(GHOSTS["whisperer"]))

    # Act 2
    world.para()
    world.say(want_line(hero))
    world.say(warning_line(companion, GHOSTS["whisperer"]))
    approach_jacuzzi(world, hero, GHOSTS["whisperer"])

    # Act 3: bad ending
    world.para()
    bad_ending(world, hero, companion)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short ghost story for a child set at {setting.place} with a jacuzzi and a bad ending.',
        f"Tell a spooky story where {hero.id} wants to approach the jacuzzi but {companion.label} worries about it.",
        f"Write a gentle eerie story that includes a bubbling jacuzzi, a warning, and a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    ghost_cfg: dict = f["ghost_cfg"]  # type: ignore[assignment]
    jacuzzi: Entity = f["jacuzzi"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to {setting.place} with {companion.label}. There was a jacuzzi there, and it felt eerie.",
        ),
        QAItem(
            question=f"Why did {companion.label} tell {hero.id} not to go near the jacuzzi?",
            answer=(
                f"{companion.label} thought something about the jacuzzi felt wrong. "
                f"The steam, the whispering ghost, and the strange ripples all made the warning feel serious."
            ),
        ),
        QAItem(
            question=f"What made the story feel spooky?",
            answer=(
                f"The whispering ghost, the cold steam, and the silent jacuzzi made the place feel spooky and strange."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"It ended badly. The jacuzzi went still, the ghost faded away, and {hero.id} was left shivering and sad."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jacuzzi?",
            answer="A jacuzzi is a tub or pool with warm water and bubbling jets that make the water move around.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that can make a story feel mysterious, eerie, or sad.",
        ),
        QAItem(
            question="Why can steam make a room feel strange?",
            answer="Steam can hide shapes and make it hard to see clearly, so a room may feel spooky or mysterious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A jacuzzi story is valid when the setting has a jacuzzi, a ghost is present,
% the child approaches the jacuzzi, the companion warns them, and the ending is bad.
valid_story(P, G, C) :- place(P), hero(G), companion(C), has_jacuzzi(P), has_ghost(P).
eerie(P) :- place(P), has_jacuzzi(P), has_ghost(P).
bad_ending(P) :- valid_story(P, _, _), eerie(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.has_jacuzzi:
            lines.append(asp.fact("has_jacuzzi", pid))
        if setting.has_ghost:
            lines.append(asp.fact("has_ghost", pid))
        if setting.eerie:
            lines.append(asp.fact("eerie_place", pid))
    for gid, cfg in GHOSTS.items():
        lines.append(asp.fact("ghost_kind", gid))
    for cid, cfg in COMPANIONS.items():
        lines.append(asp.fact("companion_kind", cid))
    for gid in ["girl", "boy"]:
        lines.append(asp.fact("hero", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = set(asp_valid_stories())
    python = {(pid, gid, cid) for pid in SETTINGS for gid in ["girl", "boy"] for cid in COMPANIONS}
    if combos == python:
        print(f"OK: ASP gate matches Python gate ({len(combos)} stories).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("ASP only:", sorted(combos - python))
    print("Python only:", sorted(python - combos))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Max", "Sam"]


def valid_params(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for gender in ["girl", "boy"]:
            for companion in COMPANIONS:
                if args.place and args.place != place:
                    continue
                if args.gender and args.gender != gender:
                    continue
                if args.companion and args.companion != companion:
                    continue
                out.append((place, gender, companion))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A spooky jacuzzi ghost story with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_params(args)
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, gender, companion = rng.choice(combos)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(name=name, gender=gender, companion=companion, place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story settings:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", companion="grandma", place="the old hotel"),
            StoryParams(name="Leo", gender="boy", companion="dad", place="the empty spa"),
            StoryParams(name="Ava", gender="girl", companion="aunt", place="the basement room"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
