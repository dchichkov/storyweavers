#!/usr/bin/env python3
"""
Small adventure storyworld: a child solves a mystery by listening closely, noticing
repeated clues, and choosing whether to resign from a risky task.

Seed words:
- resign
- still
- lotion

Narrative instruments:
- Repetition
- Sound Effects
- Mystery to Solve

Style:
- Adventure
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


@dataclass
class Item:
    id: str
    kind: str
    label: str
    phrase: str
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    characters: dict[str, Item] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)
    beats: list[str] = field(default_factory=list)
    mystery_solved: bool = False
    resigned: bool = False
    loud_sound_count: int = 0
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.beats.append(text)

    def render(self) -> str:
        return " ".join(self.beats)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


PLACES = {
    "garden_gate": "the garden gate",
    "harbor_path": "the harbor path",
    "old_lighthouse": "the old lighthouse",
    "market_lane": "the market lane",
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Jasper", "Aria", "Nico"]
COMPANION_NAMES = ["Pip", "Ravi", "Nell", "Milo", "Sia", "Iris"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a mystery solved by repetition and sound.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, companion_name=companion_name)


def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = Item(id="hero", kind="character", label=params.hero_name, phrase=params.hero_name)
    companion = Item(id="companion", kind="character", label=params.companion_name, phrase=params.companion_name)
    lotion = Item(
        id="lotion",
        kind="thing",
        label="lotion bottle",
        phrase="a small bottle of lotion",
        owner=hero.id,
        held_by=hero.id,
        location="satchel",
    )
    note = Item(
        id="note",
        kind="thing",
        label="ink note",
        phrase="a muddy note",
        owner=None,
        held_by=None,
        location=params.place,
    )
    world.characters[hero.id] = hero
    world.characters[companion.id] = companion
    world.items[lotion.id] = lotion
    world.items[note.id] = note
    world.facts.update(hero=hero, companion=companion, lotion=lotion, note=note, place=params.place)
    return world


def _repeat_clue(world: World, sound: str, clue: str) -> None:
    world.loud_sound_count += 1
    world.clues.append(clue)
    world.say(sound)


def tell_story(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    lotion = world.facts["lotion"]
    note = world.facts["note"]
    place = world.facts["place"]

    world.say(f"At {PLACES[place]}, {hero.label} and {companion.label} followed a narrow path where the wind kept whispering.")
    world.say(f"{hero.label} carried {lotion.phrase} because the air felt dry and sharp.")
    world.say(f"Then the first clue came with a soft sound: tap-tap-tap.")
    _repeat_clue(world, "tap-tap-tap", "tiny wet marks on the stones")
    world.say(f"{companion.label} pointed down and said, 'Still, that is odd.'")
    world.say(f"Again the sound came: tap-tap-tap.")
    _repeat_clue(world, "tap-tap-tap", "more tiny wet marks leading toward a cracked crate")
    world.say(f"Behind the crate, they found {note.phrase}, and the mystery grew deeper instead of smaller.")
    world.say(f"The note had one word written three times: 'resign, resign, resign.'")
    world.say(f"{hero.label} frowned. 'Someone wanted a message hidden in plain sight,' {hero.label} said.")
    world.say(f"Then came the third sound: shhff, shhff, shhff.")
    _repeat_clue(world, "shhff, shhff, shhff", "a trail of lotion smears on the crate handle")
    world.say(f"{companion.label} sniffed the air. 'That smells like your lotion.'")
    world.say(f"{hero.label} held the bottle up. One corner was open, so the lotion had dripped in a repeating trail.")
    world.say(f"At last, the clue fit: the trail did not belong to a thief. It belonged to {hero.label}.")
    world.say(f"While hurrying earlier, {hero.label} had brushed the bottle against the crate again and again.")
    world.say(f"The repeated tap-tap-tap came from the lotion bottle knocking the stones.")
    world.say(f"{hero.label} laughed in relief. 'So the mystery was not a stranger at all.'")
    world.say(f"{companion.label} smiled. 'Right. Sometimes the best detective work is just listening still enough to hear the same sound twice.'")
    world.say(f"Together they closed the bottle, and the trail ended.")
    world.say(f"After that, the path was quiet, the note made sense, and the two friends walked on toward the harbor light.")
    world.mystery_solved = True
    world.resigned = True
    world.say(f"{hero.label} resigned from the fear of the unknown and kept going with a calmer heart.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"].label
    companion = world.facts["companion"].label
    place = world.facts["place"]
    return [
        f"Write an adventure story at {PLACES[place]} where {hero} and {companion} solve a mystery by noticing repeating sounds.",
        f"Tell a child-friendly mystery story that uses the words resign, still, and lotion.",
        f"Write a short adventure where a repeated sound effect helps two friends uncover why a lotion bottle left a trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].label
    companion = world.facts["companion"].label
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Where did {hero} and {companion} look for the mystery clue?",
            answer=f"They looked at {PLACES[place]} and followed the path until the clues led them to a crate.",
        ),
        QAItem(
            question="What repeated sound helped them notice the clue?",
            answer="They heard tap-tap-tap more than once, and that repeating sound helped them follow the wet trail.",
        ),
        QAItem(
            question="What was the mystery really about?",
            answer="The mystery was solved when they learned the strange trail came from the lotion bottle, not from a stranger.",
        ),
        QAItem(
            question="How did the hero feel at the end?",
            answer=f"{hero} felt relieved and calmer after the mystery was solved and the fear of the unknown was gone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lotion used for?",
            answer="Lotion is a creamy liquid that people rub on skin to help it feel soft and less dry.",
        ),
        QAItem(
            question="What does it mean to resign from something?",
            answer="To resign means to stop holding on to a job, role, or worry and step away from it.",
        ),
        QAItem(
            question="Why can repeating sounds matter in a mystery?",
            answer="Repeating sounds can be clues because they help someone notice a pattern and follow where it leads.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.characters.values()) + list(world.items.values()):
        bits = []
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.held_by:
            bits.append(f"held_by={ent.held_by}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.label} ({ent.kind}) {' '.join(bits)}")
    lines.append(f"mystery_solved={world.mystery_solved}")
    lines.append(f"resigned={world.resigned}")
    lines.append(f"loud_sound_count={world.loud_sound_count}")
    lines.append(f"clues={world.clues}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
#show valid_story/3.

valid_place(garden_gate).
valid_place(harbor_path).
valid_place(old_lighthouse).
valid_place(market_lane).

valid_story(P,H,C) :- valid_place(P), hero(H), companion(C), H != C.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for n in HERO_NAMES:
        lines.append(asp.fact("hero", n.lower()))
    for n in COMPANION_NAMES:
        lines.append(asp.fact("companion", n.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    py = set((k,) for k in PLACES)
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches place registry ({len(py)} places).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - cl))
    print(" clingo only:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


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
    StoryParams(place="garden_gate", hero_name="Mina", companion_name="Pip"),
    StoryParams(place="harbor_path", hero_name="Toby", companion_name="Ravi"),
    StoryParams(place="old_lighthouse", hero_name="Aria", companion_name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        places = asp_valid_places()
        print(f"{len(places)} valid places:")
        for p in places:
            print(f"  {p[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.companion_name} at {PLACES[p.place]}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
