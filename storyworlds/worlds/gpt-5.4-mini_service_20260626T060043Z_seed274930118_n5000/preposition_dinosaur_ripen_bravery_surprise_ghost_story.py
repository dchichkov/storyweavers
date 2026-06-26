#!/usr/bin/env python3
"""
storyworlds/worlds/preposition_dinosaur_ripen_bravery_surprise_ghost_story.py
=============================================================================

A small, child-facing storyworld in a gentle ghost-story style.

Seed story sketch:
---
At dusk, Mina went to the garden with her grandmother. Mina was learning the word
"preposition" at school, and she liked how words like under, behind, and beside
could point to hidden things. Near the fence, a little toy dinosaur sat beside a
basket of pears that were starting to ripen.

Then the garden went quiet. A soft white shape floated from behind the shed and
whispered, "Look under the bench." Mina felt a shiver, but she stayed brave.
She found a candle and a ribbon, then followed the next clue to the stepping
stones. The ghost kept giving preposition clues until Mina reached the tree.

There was a surprise: the ghost was only a sheet on a string, and the "spooky"
shadow was the toy dinosaur in the moonlight. Mina laughed, because the garden
was not scary at all once she knew where to look.
---

World model:
- meters: physical conditions such as distance, hiddenness, brightness, ripeness
- memes: emotional conditions such as bravery, surprise, fear, relief
- state changes drive narration; the story is not a frozen paragraph with swaps.

Contract notes:
- includes the required seed words: preposition, dinosaur, ripen
- includes the narrative instruments: Bravery, Surprise
- keeps a gentle ghost-story tone
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

BRAVERY_THRESHOLD = 1.0
SURPRISE_THRESHOLD = 1.0
FEAR_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    place: str
    dusk: bool = True
    kind: str = "garden"


@dataclass
class StoryParams:
    place: str
    hero: str
    caregiver: str
    creature: str
    fruit: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", dusk=True, kind="garden"),
    "yard": Setting(place="the backyard", dusk=True, kind="yard"),
    "orchard": Setting(place="the little orchard", dusk=True, kind="orchard"),
    "porch": Setting(place="the porch", dusk=True, kind="porch"),
}

HEROES = ["Mina", "Lena", "Toby", "Noah", "Iris", "Nia"]
CAREGIVERS = ["grandmother", "grandfather", "mom", "dad"]
CREATURES = {
    "dinosaur": "a tiny toy dinosaur",
    "shadow": "a dinosaur-shaped shadow",
    "sheet": "a white sheet ghost",
}
FRUITS = {
    "pear": "a pear that was starting to ripen",
    "apple": "a red apple that was ripening slowly",
    "plum": "a plum that had just begun to ripen",
}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def pronoun(name: str, case: str = "subject") -> str:
    return {"subject": "she", "object": "her", "possessive": "her"}.get(case, "they")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="child",
        label=params.hero,
        phrases := "",
        meters={"brightness": 0.0, "fear": 0.0, "bravery": 0.0, "relief": 0.0},
        memes={"bravery": 0.0, "surprise": 0.0, "fear": 0.0, "curiosity": 0.0},
    ))
    caregiver = world.add(Entity(
        id=params.caregiver,
        kind="character",
        type=params.caregiver,
        label=params.caregiver,
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type=params.creature,
        label=CREATURES[params.creature],
        hidden=True,
        portable=True,
        meters={"hiddenness": 1.0, "mystery": 1.0},
        memes={"surprise": 1.0},
    ))
    fruit = world.add(Entity(
        id="fruit",
        kind="thing",
        type=params.fruit,
        label=FRUITS[params.fruit],
        portable=False,
        meters={"ripeness": 0.2},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="a small lantern",
        portable=True,
        meters={"brightness": 0.6},
    ))

    world.facts.update(hero=hero, caregiver=caregiver, creature=creature, fruit=fruit, lantern=lantern)
    return world


def advance(world: World) -> None:
    hero: Entity = world.facts["hero"]
    creature: Entity = world.facts["creature"]
    fruit: Entity = world.facts["fruit"]
    lantern: Entity = world.facts["lantern"]

    if "setup" not in world.fired:
        world.fired.add("setup")
        hero.memes["curiosity"] += 1
        fruit.meters["ripeness"] += 0.4
        world.say(
            f"{hero.id} went to {world.setting.place} at dusk with {world.facts['caregiver'].label}. "
            f"At school, {hero.id} had learned the word preposition, and {hero.id} liked clues like under, behind, and beside."
        )
        world.say(
            f"Near the path sat {world.facts['creature'].label}, and beside it was {world.facts['fruit'].label}."
        )
        return

    if "whisper" not in world.fired:
        world.fired.add("whisper")
        hero.memes["fear"] += 1
        hero.meters["fear"] = hero.meters.get("fear", 0.0) + 1
        creature.meters["hiddenness"] = 0.7
        world.say(
            f"Then a soft whisper came from behind the shed: \"Look under the bench.\""
        )
        world.say(
            f"{hero.id} felt a little shiver, because the garden had gone very quiet."
        )
        return

    if "brave" not in world.fired:
        world.fired.add("brave")
        hero.memes["bravery"] += 1
        hero.meters["bravery"] = hero.meters.get("bravery", 0.0) + 1
        lantern.meters["brightness"] += 0.4
        fruit.meters["ripeness"] += 0.2
        world.say(
            f"But {hero.id} held the lantern and took one brave step under the bench."
        )
        world.say(
            f"There was only a ribbon there, so {hero.id} followed the next clue beside the stepping stones."
        )
        return

    if "surprise" not in world.fired:
        world.fired.add("surprise")
        hero.memes["surprise"] += 1
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
        hero.memes["bravery"] += 1
        creature.hidden = False
        fruit.meters["ripeness"] += 0.2
        world.say(
            f"At the tree, {hero.id} found the surprise: the ghost was only a white sheet on a string, and the spooky shadow was the toy dinosaur in the moonlight."
        )
        world.say(
            f"{hero.id} laughed, because the preposition clues had led to a harmless trick, and the pear was ripening just softly in the dark."
        )
        return

    if "ending" not in world.fired:
        world.fired.add("ending")
        hero.memes["relief"] += 1
        world.say(
            f"{hero.id} walked home with {world.facts['caregiver'].label}, feeling brave enough to smile at every shadow."
        )
        world.say(
            f"Behind them, the little dinosaur stayed by the tree, and the garden looked only gently spooky."
        )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    advance(world)
    world.para()
    advance(world)
    world.para()
    advance(world)
    world.para()
    advance(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    caregiver: Entity = world.facts["caregiver"]
    fruit: Entity = world.facts["fruit"]
    creature: Entity = world.facts["creature"]
    qa = [
        QAItem(
            question=f"What word had {hero.id} learned at school that helped with the clues?",
            answer=f"{hero.id} had learned the word preposition, which helped {hero.id} understand words like under, behind, and beside.",
        ),
        QAItem(
            question=f"What made {hero.id} feel scared at first in {world.setting.place}?",
            answer=f"{creature.label} and the soft whisper from behind the shed made {hero.id} feel scared at first.",
        ),
        QAItem(
            question=f"How did {hero.id} stay brave when the whisper said to look under the bench?",
            answer=f"{hero.id} held the lantern, took a brave step, and kept following the clues instead of running away.",
        ),
        QAItem(
            question=f"What was the surprise at the end of the ghost story?",
            answer=f"The surprise was that the ghost was only a white sheet on a string, and the spooky shadow came from the toy dinosaur in the moonlight.",
        ),
        QAItem(
            question=f"What was happening to the fruit while the story went on?",
            answer=f"{fruit.label.capitalize()} was ripening slowly while {hero.id} followed the clues and discovered the trick.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a preposition?",
            answer="A preposition is a little word that shows where something is, like under, behind, beside, or between.",
        ),
        QAItem(
            question="What does a dinosaur mean in a story like this?",
            answer="A dinosaur can be a real prehistoric animal in stories, or it can be a toy or shape that looks dinosaur-like.",
        ),
        QAItem(
            question="What does ripen mean?",
            answer="Ripen means to become ready to eat, like a fruit turning sweet and soft.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect, so it feels sudden and new.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    return [
        f"Write a gentle ghost story for a child named {hero.id} that uses the word preposition and ends with a surprise.",
        f"Tell a small spooky story where {hero.id} stays brave while following clues like under and behind.",
        f"Write a child-friendly ghost story with a dinosaur shadow and a fruit that is beginning to ripen.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_invalid(params: StoryParams) -> None:
    raise StoryError("This storyworld expects a valid place, child name, caregiver, creature, and fruit.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for creature in CREATURES:
            for fruit in FRUITS:
                combos.append((place, creature, fruit))
    return combos


ASP_RULES = r"""
place(P) :- setting(P).
ghost_story(P,C,F) :- place(P), creature(C), fruit(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("place", p))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    for f in FRUITS:
        lines.append(asp.fact("fruit", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ghost_story/3."))
    asp_set = set(asp.atoms(model, "ghost_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(asp_set - py_set))
    print(" only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story world with prepositions, dinosaurs, ripening fruit, bravery, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--fruit", choices=FRUITS)
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
    hero = args.hero or rng.choice(HEROES)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    creature = args.creature or rng.choice(list(CREATURES))
    fruit = args.fruit or rng.choice(list(FRUITS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, hero=hero, caregiver=caregiver, creature=creature, fruit=fruit)


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="garden", hero="Mina", caregiver="grandmother", creature="dinosaur", fruit="pear"),
    StoryParams(place="orchard", hero="Toby", caregiver="dad", creature="sheet", fruit="apple"),
    StoryParams(place="yard", hero="Iris", caregiver="mom", creature="shadow", fruit="plum"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ghost_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ghost_story/3."))
        print(sorted(set(asp.atoms(model, "ghost_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
