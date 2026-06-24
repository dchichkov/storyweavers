#!/usr/bin/env python3
"""
A small story world: an obstinate antelope, a ghostly rhyme, and a spooky room
that only feels better when the right words are sung.

Seed tale inspiration:
---
An obstinate antelope wandered into a moonlit old house and refused to turn back,
even when the floorboards creaked and a pale ghost whispered from the hall. The
ghost did not want to scare the antelope away. Instead, it taught the antelope a
little rhyme about brave steps, soft lights, and staying together in the dark.
The antelope listened, repeated the rhyme, and finally saw that the ghost only
wanted company. The house felt warmer, the antelope felt braver, and the two of
them hummed the rhyme as they walked on.
---
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"antelope"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    mood: str
    echo: bool = False
    dark: bool = True


@dataclass
class Rhyme:
    id: str
    lines: list[str]
    effect: str
    soothe: str
    keyword: str = "rhyme"


@dataclass
class StoryParams:
    place: str
    rhyme: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_echo(world: World) -> list[str]:
    out = []
    ant = world.entities.get("antelope")
    ghost = world.entities.get("ghost")
    if not ant or not ghost:
        return out
    if ant.memes.get("fear", 0) >= THRESHOLD and not world.fired.__contains__(("echo",)):
        world.fired.add(("echo",))
        ghost.meters["glow"] = ghost.meters.get("glow", 0) + 1
        ant.memes["attention"] = ant.memes.get("attention", 0) + 1
        out.append("The hall answered back with a soft echo.")
    return out


def _r_rhyme(world: World) -> list[str]:
    out = []
    ant = world.entities.get("antelope")
    ghost = world.entities.get("ghost")
    if not ant or not ghost:
        return out
    if ant.memes.get("say_rhyme", 0) < THRESHOLD:
        return out
    sig = ("rhyme",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ant.memes["brave"] = ant.memes.get("brave", 0) + 1
    ant.memes["fear"] = max(0.0, ant.memes.get("fear", 0) - 1)
    ghost.memes["lonely"] = max(0.0, ghost.memes.get("lonely", 0) - 1)
    ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
    out.append("The rhyme made the dark feel smaller.")
    return out


def _r_friend(world: World) -> list[str]:
    out = []
    ant = world.entities.get("antelope")
    ghost = world.entities.get("ghost")
    if not ant or not ghost:
        return out
    if ant.memes.get("brave", 0) < THRESHOLD or ghost.memes.get("joy", 0) < THRESHOLD:
        return out
    sig = ("friend",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ant.memes["warmth"] = ant.memes.get("warmth", 0) + 1
    ghost.memes["company"] = ghost.memes.get("company", 0) + 1
    out.append("The antelope and the ghost were not alone anymore.")
    return out


CAUSAL_RULES = [_r_echo, _r_rhyme, _r_friend]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_world(place: Place, rhyme: Rhyme, hero_name: str) -> World:
    world = World(place)
    antelope = world.add(Entity(
        id="antelope",
        kind="character",
        type="antelope",
        label=hero_name,
        traits=["obstinate", "small", "bright-eyed"],
        meters={"feet": 1.0},
        memes={"stubbornness": 1.0, "fear": 0.0, "bravery": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        traits=["pale", "gentle", "lonely"],
        meters={"glow": 1.0},
        memes={"lonely": 1.0, "kindness": 1.0},
    ))

    world.say(
        f"On a moonlit night, {hero_name} the obstinate antelope stepped into {place.name}."
    )
    world.say(
        f"The old place felt {place.mood}, and every board gave a tiny creak under {hero_name}'s hooves."
    )
    world.para()
    world.say(
        f"At the end of the hall, a pale ghost floated near the wall and said, "
        f'"Please do not hurry away."'
    )
    world.say(
        f"{hero_name} lifted her chin. She wanted to be brave, but the dark corners still made her ears twitch."
    )

    antelope.memes["fear"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The ghost did not wave its arms or go boo. Instead, it whispered a little rhyme:"
    )
    for line in rhyme.lines:
        world.say(f'"{line}"')
    world.say(
        f"{hero_name} listened, then repeated the rhyme in a steady voice."
    )
    antelope.memes["say_rhyme"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The hall grew softer, as if the echo had changed into a song."
    )
    if antelope.memes.get("brave", 0) >= THRESHOLD:
        world.say(
            f"{hero_name} took one more step, and the ghost took one, too."
        )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"In the end, {hero_name} and the ghost walked together through {place.name}."
    )
    world.say(
        f"The antelope was still obstinate, but now she was obstinate about staying."
    )
    world.say(
        f"The ghost glowed like a small lamp, and the rhyme stayed warm in the air."
    )

    world.facts.update(
        hero=antelope,
        ghost=ghost,
        place=place,
        rhyme=rhyme,
        hero_name=hero_name,
    )
    return world


PLACES = {
    "old_house": Place(name="the old house", mood="cold and echoing", echo=True, dark=True),
    "attic": Place(name="the attic", mood="dusty and whispery", echo=True, dark=True),
    "tower": Place(name="the tower room", mood="high and windy", echo=True, dark=True),
}

RHYMES = {
    "moon_steps": Rhyme(
        id="moon_steps",
        lines=[
            "One soft step, two soft steps,",
            "Follow the moonlit glow;",
            "Three small breaths, four small breaths,",
            "Then the brave feet go.",
        ],
        effect="brave",
        soothe="smaller",
        keyword="rhyme",
    ),
    "little_lantern": Rhyme(
        id="little_lantern",
        lines=[
            "A little light, a little song,",
            "A little friend nearby;",
            "When the dark looks big and strong,",
            "We let our voices fly.",
        ],
        effect="company",
        soothe="gentler",
        keyword="rhyme",
    ),
}

NAMES = ["Mara", "Nina", "Luna", "Tessa", "Ivy", "Pippa", "Rosa"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, r) for p in PLACES for r in RHYMES]


@dataclass
class StoryParams:
    place: str
    rhyme: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with an obstinate antelope and a rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rhyme", choices=RHYMES)
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
    places = [args.place] if args.place else list(PLACES)
    rhymes = [args.rhyme] if args.rhyme else list(RHYMES)
    combos = [(p, r) for p in places for r in rhymes]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, rhyme = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, rhyme=rhyme, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for young children that includes the word "{f["rhyme"].keyword}".',
        f"Tell a short story about an obstinate antelope named {f['hero_name']} who meets a ghost in {f['place'].name} and learns a rhyme.",
        f"Write a moonlit story where a lonely ghost and a stubborn antelope become friends by repeating a little rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {f['hero_name']}, an obstinate antelope, and a gentle ghost in {f['place'].name}.",
        ),
        QAItem(
            question=f"What did the ghost share with {f['hero_name']}?",
            answer=f"The ghost shared a little rhyme, and {f['hero_name']} repeated it in a steady voice.",
        ),
        QAItem(
            question=f"How did {f['hero_name']} feel at the end?",
            answer=f"{f['hero_name']} felt braver and warmer, because the rhyme made the dark feel smaller and the ghost had a friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="In a gentle story, a ghost is a spooky-looking character who can still be kind, lonely, and friendly.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of lines with matching sounds that make words feel like a little song.",
        ),
        QAItem(
            question="What does obstinate mean?",
            answer="Obstinate means someone keeps holding on to what they want and does not easily change their mind.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n,) in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_rhyme(R) :- rhyme(R).
valid(P,R) :- place(P), rhyme(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    if py - ac:
        print("  only in python:", sorted(py - ac))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(PLACES[params.place], RHYMES[params.rhyme], params.name)
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


CURATED = [
    StoryParams(place="old_house", rhyme="moon_steps", name="Mara"),
    StoryParams(place="attic", rhyme="little_lantern", name="Nina"),
    StoryParams(place="tower", rhyme="moon_steps", name="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, rhyme) combos:\n")
        for p, r in combos:
            print(f"  {p:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.place} / {p.rhyme}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
