#!/usr/bin/env python3
"""
A standalone story world for a small mystery tale with inner monologue,
humor, and bravery.

Premise:
A child detective notices something odd in a quiet place. The trail includes
a hobble, a few funny clues, and a brave choice to keep looking until the
mystery is solved.
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

PLACEHOLDER = "hobble"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
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
class Setting:
    place: str
    affordance: str


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    weirdness: str
    location: str
    reveals: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    sidekick: str
    seed: Optional[int] = None


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "library": Setting(place="the quiet library", affordance="search"),
    "garden": Setting(place="the moonlit garden", affordance="search"),
    "attic": Setting(place="the dusty attic", affordance="search"),
    "pier": Setting(place="the foggy pier", affordance="search"),
}

CLUES = {
    "cookie": Clue(
        id="cookie",
        label="crumbs from a cookie",
        kind="crumbs",
        weirdness="funny",
        location="near the map table",
        reveals="someone had sneaked a snack",
    ),
    "bell": Clue(
        id="bell",
        label="a tiny bell",
        kind="sound",
        weirdness="tiny",
        location="under a chair",
        reveals="a cat had been nearby",
    ),
    "key": Clue(
        id="key",
        label="a bent brass key",
        kind="object",
        weirdness="odd",
        location="behind a stack of books",
        reveals="a little locked box existed",
    ),
    "feather": Clue(
        id="feather",
        label="one bright blue feather",
        kind="object",
        weirdness="strange",
        location="in a coat pocket",
        reveals="a bird had brushed past",
    ),
}

NAMES = ["Mina", "Arlo", "June", "Theo", "Ivy", "Noah", "Zara", "Eli"]
SIDEKICKS = ["cat", "dog", "raccoon", "parrot"]
HUMOR_LINES = {
    "cookie": "The crumbs looked so serious that they almost seemed to be wearing tiny detective hats.",
    "bell": "The bell gave the kind of chime that made even the dust look startled.",
    "key": "The bent key looked grumpy, as if it had forgotten where it was supposed to fit.",
    "feather": "The feather was so bright it looked like it had been dipped in sky paint.",
}


ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_fact(C).
odd(C) :- clue_fact(C), weird(C).
mystery(P, C) :- place(P), clue(C), odd(C).
brave(P) :- setting(P), face_fear(P).
#show mystery/2.
#show brave/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        lines.append(asp.fact("weird", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for p in SETTINGS:
        for c in CLUES:
            out.append((p, c))
    return out


def reasonableness_gate(place: str, clue: str) -> None:
    if place not in SETTINGS:
        raise StoryError(f"(No story: unknown place {place!r}.)")
    if clue not in CLUES:
        raise StoryError(f"(No story: unknown clue {clue!r}.)")


def _narrate_inner_monologue(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} paused. {hero.pronoun().capitalize()} thought, "
        f'"That is odd. Odd things usually mean a real mystery."'
    )
    world.say(
        f"{hero.id} felt a small wobble of worry, but the thought of a clue "
        f"made {hero.pronoun("possessive")} chest feel brave."
    )
    world.facts["brave"] = True


def _narrate_humor(world: World, clue: Clue) -> None:
    world.say(HUMOR_LINES[clue.id])


def _narrate_hobble(world: World, hero: Entity) -> None:
    hero.meters["hobble"] = 1
    hero.memes["hurt"] = 1
    world.say(
        f"{hero.id} had to hobble a little because one ankle was sore."
    )
    world.say(
        f"Still, {hero.id} kept going, because a mystery does not solve itself."
    )


def _narrate_bravery(world: World, hero: Entity, sidekick: Entity, clue: Clue) -> None:
    hero.memes["brave"] = 1
    world.say(
        f"{hero.id} took a slow breath, followed the clue, and whispered, "
        f'"I can be scared and still keep looking."'
    )
    world.say(
        f"{sidekick.id} stayed close, and together they found what the clue revealed."
    )
    world.say(
        f"It turned out {clue.reveals}, and the odd little trail led right to the answer."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, sidekick_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id="Sidekick", kind="character", type=sidekick_kind, label=sidekick_kind))
    clue_ent = world.add(Entity(id="Clue", type=clue.kind, label=clue.label, phrase=clue.label))

    world.say(
        f"On a quiet evening at {setting.place}, {hero.id} noticed {clue.label} "
        f"lying {clue.location}."
    )
    world.say(
        f"{hero.id} was not just curious; {hero.pronoun().capitalize()} was a little detective."
    )
    _narrate_humor(world, clue)
    world.para()
    _narrate_hobble(world, hero)
    _narrate_inner_monologue(world, hero, clue)
    world.para()
    world.say(
        f"{hero.id} and the {sidekick.id.lower()} searched carefully, because the clue was too strange to ignore."
    )
    _narrate_bravery(world, hero, sidekick, clue)
    world.para()
    world.say(
        f"By the end, the mystery felt smaller, the night felt safer, and {hero.id} "
        f"walked home with a proud little smile."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        clue=clue_ent,
        clue_cfg=clue,
        place=setting,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child named {f["hero"].id} in {f["place"].place} with a clue about {f["clue_cfg"].label}.',
        f"Tell a gentle mystery where {f['hero'].id} has to hobble, thinks to themself, laughs a little, and keeps going bravely.",
        f'Write a child-facing story with an inner monologue, a funny clue, and a brave ending at {f["place"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    clue = f["clue_cfg"]
    place = f["place"].place
    return [
        QAItem(
            question=f"Where did {hero.id} find the strange clue?",
            answer=f"{hero.id} found {clue.label} at {place}, where the mystery began.",
        ),
        QAItem(
            question=f"Why did {hero.id} have to hobble?",
            answer=f"{hero.id} had to hobble because one ankle was sore, but {hero.pronoun()} kept going anyway.",
        ),
        QAItem(
            question=f"How did the funny clue help the story?",
            answer=f"The clue made the mystery feel odd and interesting, and it pointed the search toward what {clue.reveals}.",
        ),
        QAItem(
            question=f"Who stayed with {hero.id} during the search?",
            answer=f"The {sidekick.id.lower()} stayed close and helped {hero.id} keep looking bravely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story about noticing clues, asking questions, and trying to find out what is really happening.",
        ),
        QAItem(
            question="What does it mean to hobble?",
            answer="To hobble means to walk in a difficult or uneven way, usually because something hurts or is injured.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something important even when you feel nervous or scared.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a character's thoughts inside their own head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    reasonableness_gate(place, clue)
    hero_name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(
        place=place,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick=sidekick,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.hero_name, params.hero_type, params.sidekick)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with hobble, inner monologue, humor, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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


def asp_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery/2.\n#show brave/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible place/clue pairs")
        for p, c in combos:
            print(f"{p:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in SETTINGS:
            for c in CLUES:
                params = StoryParams(place=p, clue=c, hero_name="Mina", hero_type="girl", sidekick="cat")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
