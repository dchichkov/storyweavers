#!/usr/bin/env python3
"""
storyworlds/worlds/virtual_maiden_surprise_curiosity_inner_monologue_animal.py
===============================================================================

A tiny animal-story world about a curious maiden, a virtual clue, and a gentle
surprise.

Premise:
- A small animal maiden follows a virtual trail that promises a secret.
- Curiosity pushes her to explore.
- Surprise appears when the "secret" turns out to be a real, live friend.
- Her inner monologue shows her changing from eager suspicion to warm delight.

The prose is authored from simulated state, not from a frozen template:
physical meters track movement and carried objects; memes track curiosity,
surprise, worry, relief, and affection.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"maiden", "girl", "doe", "cat", "fox", "rabbit", "mouse", "bird", "squirrel"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bramble garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    verb: str
    keyword: str
    wonder: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the bramble garden", affords={"seek"}),
    "orchard": Setting(place="the orchard path", affords={"seek"}),
    "pond": Setting(place="the pond bank", affords={"seek"}),
}

CLUES = {
    "glow": Clue(
        label="glow",
        verb="follow the glow",
        keyword="glow",
        wonder="a soft blue light in the grass",
        surprise="the glow came from a tiny shell lantern",
        tags={"virtual", "surprise"},
    ),
    "song": Clue(
        label="song",
        verb="follow the song",
        keyword="song",
        wonder="a humming note that seemed to float in the air",
        surprise="the song came from a cricket hiding under a leaf",
        tags={"surprise"},
    ),
    "map": Clue(
        label="map",
        verb="follow the map",
        keyword="map",
        wonder="a little virtual path drawn in bright dots",
        surprise="the dots led to a hollow stump with a note inside",
        tags={"virtual", "curiosity"},
    ),
}

TREASURES = {
    "pearl": Treasure(label="pearl", phrase="a tiny pearl in a shell", type="pearl", tags={"surprise"}),
    "feather": Treasure(label="feather", phrase="a feather with a silver tip", type="feather", tags={"curiosity"}),
    "key": Treasure(label="key", phrase="a small brass key", type="key", tags={"virtual"}),
}

GIFTS = {
    "berry": Gift(label="berry tart", phrase="a warm berry tart", type="tart", tags={"kindness"}),
    "flower": Gift(label="flower crown", phrase="a little flower crown", type="crown", tags={"kindness"}),
    "seed": Gift(label="seed packet", phrase="a packet of sweet meadow seeds", type="seeds", tags={"virtual", "kindness"}),
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nora", "Pippa", "Elin"]
ANIMAL_TYPES = ["rabbit", "fox", "deer", "cat"]
HELPER_TYPES = ["mouse", "bird", "squirrel"]


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def inner_monologue(actor: Entity, thought: str) -> str:
    return f"{actor.pronoun().capitalize()} thought, '{thought}'"


def explore(world: World, hero: Entity, clue: Clue) -> None:
    hero.meters["steps"] = hero.meters.get("steps", 0.0) + 3
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} was a little {hero.type} maiden who loved noticing small things. "
        f"One morning, she saw {clue.wonder} near {world.setting.place}."
    )
    world.say(inner_monologue(hero, f"What could be making that? I must look closer."))
    world.say(f"Her curiosity grew, so she chose to {clue.verb}.")


def virtual_hint(world: World, hero: Entity, clue: Clue) -> None:
    if "virtual" in clue.tags:
        hero.meters["screen_steps"] = hero.meters.get("screen_steps", 0.0) + 1
        world.say(
            f"On her little screen, a virtual trail blinked on and off like a path of stars."
        )
        world.say(inner_monologue(hero, "This looks like a game, but it feels like a real clue."))
    else:
        world.say(f"The clue did not need a screen; it waited quietly in the open air.")


def surprise_reveal(world: World, hero: Entity, clue: Clue, treasure: Treasure, helper: Entity) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    helper.meters["hidden"] = 0.0
    world.say(
        f"At the end of the trail, the surprise was bigger than she expected: {treasure.phrase}."
    )
    world.say(
        f"Then a small {helper.type} peeked out and waved. "
        f"It turned out the real secret was not a treasure at all."
    )
    world.say(inner_monologue(hero, "Oh! I was looking for a prize, but I found a friend."))


def resolve(world: World, hero: Entity, helper: Entity, gift: Gift) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["surprise"] = max(0.0, hero.memes.get("surprise", 0.0) - 1)
    world.say(
        f"{hero.id} smiled, reached into her basket, and shared {gift.phrase} with the little {helper.type}."
    )
    world.say(
        f"The {helper.type} brightened at once, and the two of them sat together under the leaves."
    )
    world.say(inner_monologue(hero, "Curiosity can lead to surprises, and some surprises are very kind."))
    world.say(
        f"In the end, {hero.id} carried home a warmer heart, and the virtual trail in her head felt like a lucky map."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, clue: Clue, treasure: Treasure, gift: Gift,
         hero_name: str = "Mina", hero_type: str = "rabbit",
         helper_type: str = "mouse") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"steps": 0.0},
        memes={"curiosity": 0.0, "surprise": 0.0, "joy": 0.0, "relief": 0.0, "kindness": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        meters={"hidden": 1.0},
        memes={"worry": 0.0},
    ))
    world.add(Entity(
        id="treasure",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
    ))
    world.add(Entity(
        id="gift",
        type=gift.type,
        label=gift.label,
        phrase=gift.phrase,
    ))

    world.say(
        f"{hero.id} lived near {setting.place}, where flowers leaned over the path like curious ears."
    )
    world.say(
        f"She liked quiet mornings, especially when the air felt full of {clue.label}."
    )

    world.para()
    virtual_hint(world, hero, clue)
    explore(world, hero, clue)

    world.para()
    world.say(
        f"The little trail led her to a patch of moss where {clue.surprise.lower()}."
    )
    surprise_reveal(world, hero, clue, treasure, helper)

    world.para()
    resolve(world, hero, helper, gift)

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        treasure=treasure,
        gift=gift,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    treasure: str
    gift: str
    name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="garden", clue="map", treasure="key", gift="seed", name="Mina", hero_type="rabbit", helper_type="mouse"),
    StoryParams(place="orchard", clue="glow", treasure="pearl", gift="berry", name="Luna", hero_type="fox", helper_type="bird"),
    StoryParams(place="pond", clue="song", treasure="feather", gift="flower", name="Tia", hero_type="deer", helper_type="squirrel"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, clue, treasure) for place in SETTINGS for clue in CLUES for treasure in TREASURES]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story with the words "virtual" and "maiden" about {f["hero"].id} following a clue.',
        f"Tell a gentle story where a {f['hero'].type} maiden named {f['hero'].id} feels curiosity, then surprise, then kindness.",
        f"Write a short story for children where a virtual trail leads to a real friend in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type} maiden who follows a {clue.label} at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} feel before the surprise?",
            answer=f"She felt curiosity first, because the clue looked strange and tempting.",
        ),
        QAItem(
            question=f"What was the surprise at the end of the trail?",
            answer=f"The surprise was that a little {helper.type} was hiding there, so the secret turned out to be a friend.",
        ),
        QAItem(
            question=f"What happened after {hero.id} understood the surprise?",
            answer=f"She shared a gift and sat kindly with the {helper.type}, so the ending felt warm and peaceful.",
        ),
    ]


KNOWLEDGE = {
    "virtual": [
        ("What does virtual mean?", "Virtual means something is shown on a screen or in a pretend space instead of being physically there."),
    ],
    "curiosity": [
        ("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn more."),
    ],
    "surprise": [
        ("What is a surprise?", "A surprise is something you did not expect to happen."),
    ],
    "kindness": [
        ("What does kindness look like?", "Kindness can mean sharing, helping, and being gentle with others."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags)
    tags.add("virtual")
    out: list[QAItem] = []
    for tag in ["virtual", "curiosity", "surprise", "kindness"]:
        if tag in tags or tag == "kindness":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- character(H).
virtual_clue(C) :- clue(C), tag(C, virtual).
curious_story(H) :- hero(H), feeling(H, curiosity).
surprising_story(H) :- hero(H), feeling(H, surprise).
kind_story(H) :- hero(H), feeling(H, kindness).

good_story(H, C) :- hero(H), clue(C), virtual_clue(C), curious_story(H), surprising_story(H), kind_story(H).

#show good_story/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tg))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for tg in sorted(g.tags):
            lines.append(asp.fact("tag", gid, tg))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {("Hero", clue_id) for clue_id in CLUES}
    # Python gate is intentionally simple: every clue can support a good story.
    if asp_set == py_set:
        print(f"OK: ASP and Python gates agree ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  ASP:", sorted(asp_set))
    print("  Python:", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: virtual clue, maiden, curiosity, surprise, and an inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    treasure = args.treasure or rng.choice(list(TREASURES))
    gift = args.gift or rng.choice(list(GIFTS))
    hero_type = args.hero_type or rng.choice(ANIMAL_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    name = args.name or rng.choice(GIRL_NAMES)
    return StoryParams(place=place, clue=clue, treasure=treasure, gift=gift, name=name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        TREASURES[params.treasure],
        GIFTS[params.gift],
        hero_name=params.name,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
    )
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        atoms = asp.atoms(model, "good_story")
        print(f"{len(atoms)} compatible story patterns:")
        for h, clue in sorted(atoms):
            print(f"  {h} with {clue}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.clue} at {p.place} ({p.hero_type} maiden)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
