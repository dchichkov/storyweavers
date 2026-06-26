#!/usr/bin/env python3
"""
storyworlds/worlds/suspicious_glower_foreshadowing_reconciliation_detective_story.py
====================================================================================

A small detective-style story world about a suspicious glower, a foreshadowed clue,
and a reconciliation that clears the air.

Premise:
- A child detective notices something odd in a small neighborhood setting.
- A suspicious glower and a missing object create tension.
- Foreshadowed details point to the real cause.
- The ending resolves with reconciliation instead of blame.

The simulation tracks physical meters and emotional memes.
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
# Data model
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    weather: str = ""


@dataclass
class Mystery:
    name: str
    missing_label: str
    missing_phrase: str
    clue: str
    red_herring: str
    culprit: str
    resolution: str
    foreshadow: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    suspect_name: str
    suspect_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(
        place="the little library",
        detail="Dusty shelves leaned over a round reading table, and the rain tapped the window.",
        weather="rainy",
    ),
    "garden": Setting(
        place="the community garden",
        detail="Bean poles, pebbles, and a tiny shed made neat rows under a pale sky.",
        weather="cloudy",
    ),
    "station": Setting(
        place="the old train station",
        detail="A clock clicked softly above the platform, and one dark hallway led to the back room.",
        weather="windy",
    ),
}

MYSTERIES = {
    "lantern": Mystery(
        name="lantern",
        missing_label="lantern",
        missing_phrase="a brass lantern with a blue ribbon",
        clue="a smear of chalk dust on the table",
        red_herring="the janitor's stern glower",
        culprit="the lantern was moved by the sidekick to help",
        resolution="the friends laughed and returned the lantern to its hook",
        foreshadow="the blue ribbon fluttered near the back shelf",
    ),
    "key": Mystery(
        name="key",
        missing_label="key",
        missing_phrase="a tiny silver key on a string",
        clue="a trail of mud near the side door",
        red_herring="the gardener's suspicious glower",
        culprit="the key had fallen into a pocket while the door was being fixed",
        resolution="the friends smiled and slipped the key back onto its string",
        foreshadow="a loose button near the door had snagged the cord",
    ),
    "cookie": Mystery(
        name="cookie",
        missing_label="cookie",
        missing_phrase="a jam cookie on a napkin",
        clue="a crumb on the windowsill",
        red_herring="the librarian's suspicious glower",
        culprit="the cookie was saved for the hero by the sidekick",
        resolution="the friends shared the cookie and apologized for jumping to conclusions",
        foreshadow="the napkin was folded beside the teacup all along",
    ),
}

# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"curiosity": 1.0},
        memes={"alertness": 1.0, "kindness": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type=params.sidekick_type,
        meters={"helpfulness": 1.0},
        memes={"nervousness": 0.5, "loyalty": 1.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect_name,
        kind="character",
        type=params.suspect_type,
        meters={"stillness": 1.0},
        memes={"reserve": 1.0, "frustration": 0.5},
    ))
    missing = world.add(Entity(
        id=mystery.name,
        type=mystery.missing_label,
        label=mystery.missing_label,
        phrase=mystery.missing_phrase,
        owner=params.hero_name,
        hidden=True,
        meters={"lost": 1.0},
    ))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        suspect=suspect,
        missing=missing,
        mystery=mystery,
        setting=setting,
    )

    # Act 1: setup and foreshadowing
    world.say(f"At {setting.place}, {hero.id} was a little detective who noticed small things.")
    world.say(f"{hero.id} had been looking for {mystery.missing_phrase}, and the room felt strangely quiet.")
    world.say(f"Near the table, {mystery.foreshadow}, but nobody mentioned it at first.")
    world.para()

    # Act 2: suspicion rises
    world.say(setting.detail)
    suspect.memes["suspicion"] = 1.0
    world.say(f"When {suspect.id} gave a suspicious glower, {hero.id} thought that was the answer.")
    world.say(f"{sidekick.id} pointed at {mystery.clue}, but {hero.id} was still watching {suspect.id}.")
    world.say(f"It looked like {mystery.red_herring}, and that made the mystery feel bigger than it was.")
    world.para()

    # Act 3: investigation and reconciliation
    world.say(f"{hero.id} followed the clue carefully, because detectives do not stop at one bad guess.")
    world.say(f"The clue led to a small hiding place, and soon the truth came out: {mystery.culprit}.")
    suspect.memes["hurt"] = 1.0
    world.say(f"{suspect.id} looked upset, because being stared at like that had felt unfair.")
    world.say(f"{hero.id} lowered {hero.pronoun('possessive')} head and said sorry for the suspicious glower of suspicion.")
    world.say(f"{sidekick.id} helped with the fix, and {mystery.resolution}.")
    hero.memes["guilt"] = 0.0
    hero.memes["relief"] = 1.0
    suspect.memes["frustration"] = 0.0
    suspect.memes["trust"] = 1.0
    world.say(f"In the end, {hero.id}, {sidekick.id}, and {suspect.id} shared a calm smile, and the little mystery felt solved for real.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------
HERO_NAMES = ["Mina", "Owen", "Tessa", "Noah", "Luna", "Eli", "Ruby", "Finn"]
SIDEKICK_NAMES = ["Pip", "June", "Max", "Nia", "Theo", "Bea", "Ivy", "Sam"]
SUSPECT_NAMES = ["Mr. Vale", "Ms. Green", "Mrs. Hale", "Mr. Finch"]
TRAITS = ["girl", "boy"]
SUSPECT_TYPES = ["man", "woman"]


def choose_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short detective story for a young child that includes the word "{mystery.name}".',
        f"Tell a story where {f['hero'].id} notices a suspicious glower and then solves the mystery by following a clue.",
        f"Write a gentle mystery story with foreshadowing and reconciliation at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    suspect: Entity = f["suspect"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who was the little detective at {setting.place}?",
            answer=f"{hero.id} was the little detective at {setting.place}, and {sidekick.id} helped with the case.",
        ),
        QAItem(
            question=f"What did {hero.id} first think when {suspect.id} gave a suspicious glower?",
            answer=f"{hero.id} first thought {suspect.id} might be hiding the answer, but that guess was only a red herring.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery of the missing {mystery.missing_label}?",
            answer=f"The clue was {mystery.clue}, and it led the friends to the real place where the {mystery.missing_label} had been moved.",
        ),
        QAItem(
            question=f"How did the story end after the truth came out?",
            answer=f"It ended with reconciliation: {hero.id} apologized, {suspect.id} felt better, and everyone shared a calm smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint about something important that will matter later.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make peace after a disagreement or a misunderstanding.",
        ),
        QAItem(
            question="Why can a suspicious glower make a mystery feel bigger?",
            answer="A suspicious glower can make someone look secretive, so the detective may think a problem is worse than it really is.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.hidden:
            parts.append("hidden=True")
        lines.append(f"  {e.id:12} ({e.kind:8} {e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class ParamsRegistry:
    settings: dict[str, Setting] = field(default_factory=lambda: SETTINGS)
    mysteries: dict[str, Mystery] = field(default_factory=lambda: MYSTERIES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.hero_type or rng.choice(TRAITS)
    hero_name = args.hero_name or choose_name(rng, HERO_NAMES)
    sidekick_type = args.sidekick_type or rng.choice(TRAITS)
    sidekick_name = args.sidekick_name or choose_name(rng, SIDEKICK_NAMES)
    suspect_type = args.suspect_type or rng.choice(SUSPECT_TYPES)
    suspect_name = args.suspect_name or choose_name(rng, SUSPECT_NAMES)

    if hero_name == sidekick_name:
        raise StoryError("hero and sidekick must be different characters")
    if hero_name == suspect_name or sidekick_name == suspect_name:
        raise StoryError("suspect must be distinct from the hero and sidekick")

    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        suspect_name=suspect_name,
        suspect_type=suspect_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(library).
setting(garden).
setting(station).

mystery(lantern).
mystery(key).
mystery(cookie).

foreshadow(lantern, blue_ribbon).
foreshadow(key, loose_button).
foreshadow(cookie, folded_napkin).

clue(lantern, chalk_dust).
clue(key, mud_trail).
clue(cookie, crumb).

resolution(lantern, reconciliation).
resolution(key, reconciliation).
resolution(cookie, reconciliation).

valid_story(S, M) :- setting(S), mystery(M), foreshadow(M, _), clue(M, _), resolution(M, reconciliation).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for m, c in [("lantern", "blue_ribbon"), ("key", "loose_button"), ("cookie", "folded_napkin")]:
        lines.append(asp.fact("foreshadow", m, c))
    for m, c in [("lantern", "chalk_dust"), ("key", "mud_trail"), ("cookie", "crumb")]:
        lines.append(asp.fact("clue", m, c))
    for m in MYSTERIES:
        lines.append(asp.fact("resolution", m, "reconciliation"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    valid_py = {(s, m) for s in SETTINGS for m in MYSTERIES}
    valid_asp = set(asp_valid_stories())
    if valid_py == valid_asp:
        print(f"OK: ASP parity matches Python ({len(valid_py)} stories).")
        return 0
    print("MISMATCH between ASP and Python")
    if valid_asp - valid_py:
        print("  only in ASP:", sorted(valid_asp - valid_py))
    if valid_py - valid_asp:
        print("  only in Python:", sorted(valid_py - valid_asp))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with foreshadowing and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=TRAITS)
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=TRAITS)
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-type", choices=SUSPECT_TYPES)
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
    StoryParams(setting="library", mystery="lantern", hero_name="Mina", hero_type="girl",
                sidekick_name="Pip", sidekick_type="boy", suspect_name="Mr. Vale", suspect_type="man"),
    StoryParams(setting="garden", mystery="key", hero_name="Owen", hero_type="boy",
                sidekick_name="June", sidekick_type="girl", suspect_name="Ms. Green", suspect_type="woman"),
    StoryParams(setting="station", mystery="cookie", hero_name="Luna", hero_type="girl",
                sidekick_name="Theo", sidekick_type="boy", suspect_name="Mrs. Hale", suspect_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s, m in stories:
            print(f"  {s:10} {m}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.setting} solving {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
