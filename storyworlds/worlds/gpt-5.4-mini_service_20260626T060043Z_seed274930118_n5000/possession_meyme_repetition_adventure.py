#!/usr/bin/env python3
"""
storyworlds/worlds/possession_meyme_repetition_adventure.py
===========================================================

A small adventure storyworld about possession, a stubborn little chant
("meyme"), and repetition that turns a lost-object problem into a gentle quest.

The seed idea:
- A child feels an object is "mine, meyme" and keeps repeating that phrase.
- A helpful adult reminds them that possession is not the same as safety.
- They go on a short adventure to recover, share, or properly store the thing.
- The story resolves by changing both the object's location and the child's
  understanding of ownership.

This world stays close to a classic adventure tone: a path, a problem, a clue,
a turn, and a found ending.  The repetition is not decorative; it is the engine
of the child’s fixation and the turning point of the tale.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    path: str
    hiding_spots: list[str]


@dataclass
class Treasure:
    label: str
    phrase: str
    location: str
    size: str
    possession_word: str = "mine"


@dataclass
class StoryParams:
    place: str
    treasure: str
    hero_name: str
    hero_type: str
    guide_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", path="the wooden dock", hiding_spots=["under a crate", "beside a rope coil", "near the sail shed"]),
    "forest": Setting(place="the forest edge", path="the narrow trail", hiding_spots=["behind a fern", "under a log", "near a mossy stone"]),
    "hill": Setting(place="the hill road", path="the windy path", hiding_spots=["behind a thorn bush", "under the bench", "by the gate"]),
}

TREASURES = {
    "key": Treasure(label="key", phrase="a tiny brass key", location="a pocket", size="small"),
    "map": Treasure(label="map", phrase="a folded treasure map", location="a satchel", size="flat"),
    "shell": Treasure(label="shell", phrase="a bright shell", location="a shell pouch", size="small"),
    "lantern": Treasure(label="lantern", phrase="a little lantern", location="a rope hook", size="round"),
}

HERO_NAMES = ["Milo", "Nina", "Rae", "Toby", "Lena", "Owen", "Iris", "Pip"]
TRAITS = ["brave", "curious", "stubborn", "bright", "spirited", "patient"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def possession_phrase(hero: Entity, treasure: Entity) -> str:
    return f"{hero.pronoun('possessive')} {treasure.label}"


def chant() -> str:
    return "meyme"


def opening(world: World, hero: Entity, guide: Entity, treasure: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved adventure and liked to say "
        f'"{treasure.label} is mine, {chant()}, mine."'
    )
    world.say(
        f"{guide.pronoun().capitalize()} listened carefully, because repetition can be a clue "
        f"when a child is worried about possession."
    )
    world.say(
        f"That morning, {hero.id} and {guide.pronoun('possessive')} {guide.type} went to "
        f"{world.setting.place} along {world.setting.path}."
    )


def problem(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["wanting"] = hero.memes.get("wanting", 0) + 1
    treasure.location = "lost on the path"
    world.say(
        f"On the way, the {treasure.label} slipped away and vanished near the trail."
    )
    world.say(
        f"{hero.id} stopped and repeated, '{treasure.label} is mine, {chant()}, mine!' "
        f"again and again."
    )
    world.say(
        f"The words sounded strong, but the treasure was nowhere to be seen."
    )


def search(world: World, hero: Entity, guide: Entity, treasure: Entity) -> None:
    hero.meters["searching"] = hero.meters.get("searching", 0) + 1
    world.say(
        f"{guide.pronoun().capitalize()} pointed to the path and said they should look slowly, "
        f"one step at a time."
    )
    spot = random.choice(world.setting.hiding_spots)
    treasure.location = spot
    world.say(
        f"They checked {spot}, then another little place, and then another."
    )
    world.say(
        f"Each time {hero.id} began the chant, {guide.pronoun('subject')} answered, "
        f'"It is yours to care for, not to clutch forever."'
    )


def turn(world: World, hero: Entity, guide: Entity, treasure: Entity) -> None:
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    world.say(
        f"At last, {hero.id} saw the {treasure.label} tucked exactly where the path had hidden it."
    )
    world.say(
        f"{hero.id} picked it up with both hands and whispered, "
        f'"It was mine, but I should carry it carefully."'
    )
    world.say(
        f"{guide.pronoun().capitalize()} smiled, because the repeated words had changed into a better idea."
    )


def resolution(world: World, hero: Entity, guide: Entity, treasure: Entity) -> None:
    treasure.carried_by = hero.id
    treasure.location = f"in {hero.id}'s hands"
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"Together they walked back along {world.setting.path}, with the {treasure.label} safe at last."
    )
    world.say(
        f"This time {hero.id} did not shout the chant. {hero.id} simply kept the treasure close "
        f"and smiled at the road ahead."
    )
    world.say(
        f"It felt like the start of a bigger adventure, and also the end of the worry."
    )


def tell(setting: Setting, treasure_cfg: Treasure, hero_name: str, hero_type: str, guide_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type))
    treasure = world.add(
        Entity(
            id="Treasure",
            type=treasure_cfg.label,
            label=treasure_cfg.label,
            phrase=treasure_cfg.phrase,
            owner=hero.id,
            location=treasure_cfg.location,
        )
    )

    opening(world, hero, guide, treasure)
    world.para()
    problem(world, hero, treasure)
    world.para()
    search(world, hero, guide, treasure)
    turn(world, hero, guide, treasure)
    world.para()
    resolution(world, hero, guide, treasure)

    world.facts.update(
        hero=hero,
        guide=guide,
        treasure=treasure,
        setting=setting,
        treasure_cfg=treasure_cfg,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, treasure = f["hero"], f["treasure_cfg"]
    return [
        f'Write a short adventure story for a child about {hero.id}, a missing {treasure.label}, and the repeated word "meyme".',
        f"Tell a gentle adventure where a {hero.type} learns that saying '{treasure.label} is mine, meyme' is not enough to keep it safe.",
        f"Write a story with repetition, a lost treasure, and a helpful guide at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, treasure = f["hero"], f["guide"], f["treasure"], f["treasure_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} keep repeating at the start of the story?",
            answer=f"{hero.id} kept repeating, '{treasure.label} is mine, meyme, mine.'",
        ),
        QAItem(
            question=f"What problem started the adventure at {world.setting.place}?",
            answer=f"The {treasure.label} slipped away on the path, so {hero.id} had to search for it.",
        ),
        QAItem(
            question=f"How did {guide.pronoun('subject')} help {hero.id}?",
            answer=f"{guide.pronoun().capitalize()} helped by guiding {hero.id} to search slowly and think about careful possession, not just saying the word over and over.",
        ),
        QAItem(
            question=f"How did the story end with the {treasure.label}?",
            answer=f"The {treasure.label} was found and carried safely in {hero.id}'s hands.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is possession?",
            answer="Possession means having something or keeping something under your care or control.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing the same thing more than once, often to show a habit, a feeling, or something important.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story is a tale about a journey, a problem, a search, or a brave trip into an interesting place.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is possessed by the hero when it belongs to them.
possessed(H, T) :- owns(H, T).

% Repetition is present when the hero repeats the meyme chant.
repetition(H) :- chants(H, meyme).

% An adventure is valid when the setting exists and the treasure is at risk.
at_risk(S, T) :- setting(S), treasure(T), lost(T, S).
valid_story(S, T) :- at_risk(S, T), possesses(H, T), repetition(H).

#show valid_story/2.
#show at_risk/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    lines.append(asp.fact("owns", "hero", "treasure"))
    lines.append(asp.fact("chants", "hero", "meyme"))
    lines.append(asp.fact("lost", "treasure", "forest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    asp_atoms = sorted(set(asp.atoms(model, "valid_story")))
    python_atoms = sorted({(sid, "treasure") for sid in SETTINGS if sid == "forest"})
    if asp_atoms == python_atoms:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", asp_atoms)
    print("PY :", python_atoms)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about possession and the repeated word meyme.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--treasure", choices=TREASURES.keys())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guide-type", choices=["mother", "father", "sister", "brother"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    treasure = args.treasure or rng.choice(list(TREASURES.keys()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    guide_type = args.guide_type or rng.choice(["mother", "father", "sister", "brother"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place,
        treasure=treasure,
        hero_name=hero_name,
        hero_type=hero_type,
        guide_type=guide_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TREASURES[params.treasure],
        params.hero_name,
        params.hero_type,
        params.guide_type,
    )
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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.location:
                bits.append(f"location={e.location}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    rng_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="forest", treasure="key", hero_name="Milo", hero_type="boy", guide_type="mother"),
            StoryParams(place="harbor", treasure="map", hero_name="Nina", hero_type="girl", guide_type="father"),
            StoryParams(place="hill", treasure="shell", hero_name="Rae", hero_type="girl", guide_type="brother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(rng_seed + i))
            params.seed = rng_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
