#!/usr/bin/env python3
"""
storyworlds/worlds/regurgitate_cursive_famed_teamwork_inner_monologue_folk.py
===============================================================================

A small folk-tale storyworld about a village errand, a famed helper, a cursive
message, teamwork, and a private inner monologue that nudges a brave choice.

Seed tale used as the simulation premise:
---
In a little village, a famed white goose named Bramble had once carried the
mayor's silver key in its throat during a flood. The key was never lost, because
Bramble could regurgitate it when asked, but the goose grew shy of the villagers'
laughing.

One morning, a child named Tessa found a cursive note from her grandmother. The
note said the old bell would ring only if the key, the rope, and the latch were
mended together. Tessa wanted to help, but the note was smudged, and Bramble did
not like being crowded.

Tessa stood still and listened to her own inner monologue. If she could ask
kindly, maybe the famed goose would trust her. She spoke gently, Bramble
regurgitated the key, and then Tessa, Bramble, and the miller tied the rope
together. The bell rang again, and the village remembered that small teamwork
can mend big things.
---

The world model tracks a tiny physical state and emotional state:
- a message may be written in cursive or smudged by weather
- a famed helper may be proud, shy, or trusted
- a lost object may need regurgitation before the teamwork can succeed
- the final image proves the change: the bell rings, the key is back, and the
  characters share the work

Narrative instruments:
- teamwork
- inner monologue
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

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
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    needs: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    can_return: bool
    return_verb: str
    pride: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# Registries
SETTINGS = {
    "village_square": Setting(place="the village square", weather="misty", affords={"letter", "rope"}),
    "old_bridge": Setting(place="the old bridge", weather="windy", affords={"key", "rope"}),
    "mill_road": Setting(place="the mill road", weather="drizzly", affords={"key", "letter", "rope"}),
}

HERO_NAMES = ["Tessa", "Mina", "Annie", "Liora", "Pippa", "Nell"]
HELPER_NAMES = ["Bramble", "Moss", "Peregrine"]
ADULT_NAMES = ["the miller", "the mayor", "Grandmother"]

RELICS = {
    "key": Relic(
        id="key",
        label="silver key",
        phrase="a small silver key",
        needs="regurgitate",
        type="key",
        region="beak",
    ),
    "letter": Relic(
        id="letter",
        label="cursive note",
        phrase="a cursive note from Grandmother",
        needs="read",
        type="letter",
        region="hands",
    ),
}

HELPERS = {
    "goose": Helper(
        id="goose",
        label="famed goose",
        phrase="the famed goose",
        can_return=True,
        return_verb="regurgitate",
        pride="famed",
    ),
}

WORDS = ["regurgitate", "cursive", "famed", "teamwork", "inner monologue"]


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    relic: str
    seed: Optional[int] = None


ASP_RULES = r"""
helper_famed(goose).
needs_regurgitate(key).
needs_read(letter).
teamwork_possible(P) :- place(P), affords(P, key), affords(P, rope).
good_story(P, R) :- place(P), relic(R), helper_famed(goose), needs_regurgitate(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting", pid))
        if s.weather:
            lines.append(asp.fact("weather", pid, s.weather))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(p, r) for p in SETTINGS for r in RELICS if r == "key"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of a famed goose, a cursive note, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--relic", choices=RELICS)
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
    if args.relic and args.relic != "key":
        raise StoryError("This storyworld only works when the lost thing is the silver key; the goose can regurgitate that, and the bell depends on it.")
    combos = [(p, h, g, r) for p in SETTINGS for h in HERO_NAMES for g in HELPERS for r in RELICS if r == "key"]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hero:
        combos = [c for c in combos if c[1] == args.hero]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if args.relic:
        combos = [c for c in combos if c[3] == args.relic]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, hero, helper, relic = rng.choice(sorted(combos))
    return StoryParams(place=place, hero=hero, helper=helper, relic=relic)


def _new_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="goose", label="the famed goose", traits=["famed"]))
    adult = world.add(Entity(id="adult", kind="character", type="mother", label="Grandmother"))
    relic = world.add(Entity(id=params.relic, kind="thing", type="key", label="silver key", phrase="a small silver key", owner=helper.id, caretaker=adult.id))
    note = world.add(Entity(id="note", kind="thing", type="letter", label="cursive note", phrase="a cursive note from Grandmother", owner=adult.id))
    bell = world.add(Entity(id="bell", kind="thing", type="bell", label="old bell", phrase="the old bell"))
    world.facts.update(hero=hero, helper=helper, adult=adult, relic=relic, note=note, bell=bell)
    return world


def _do_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    adult: Entity = f["adult"]
    relic: Entity = f["relic"]
    note: Entity = f["note"]
    bell: Entity = f["bell"]

    world.say(f"In {world.setting.place}, {hero.id} found a {note.label} tucked beneath a stone.")
    world.say(f"The writing was {note.label} and neat, but the little curls were hard to read in the mist.")
    hero.memes["worry"] = 1
    world.say(f"{hero.id} stood very still and listened to her inner monologue: 'If I rush, I may miss the one kind thing that would help.'")
    world.para()
    world.say(f"The note said the {bell.label} would ring again if the {relic.label} and the rope were mended together.")
    hero.memes["desire"] = 1
    world.say(f"{hero.id} wanted to help, yet the famed goose was shy after all the old laughter in the square.")
    world.say(f"So {hero.id} spoke softly, and the famed goose lowered its head.")
    helper.meters["trust"] = 1
    helper.memes["pride"] = 1
    world.say(f"At last, {helper.id} did the strange helpful thing the villagers remembered: it could regurgitate the {relic.label}.")
    relic.meters["returned"] = 1
    world.say(f"With the key back in hand, {hero.id}, {helper.id}, and the miller worked together to tie the rope straight.")
    world.say(f"Their teamwork held the latch firm, and the old bell rang cleanly across the lane.")
    world.para()
    world.say(f"By evening, the {note.label} was placed in a dry box, the {relic.label} was safe, and the famed goose stood tall beside {hero.id} like a proud friend.")
    hero.memes["joy"] = 1
    helper.memes["trusted"] = 1
    bell.meters["ringing"] = 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale using the words "{WORDS[0]}", "{WORDS[1]}", and "{WORDS[2]}".',
        f"Tell a gentle story where {f['hero'].id} uses teamwork with a famed goose to recover a lost key.",
        f"Write a child-friendly tale with an inner monologue that helps a character choose a kind way to ask for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    relic: Entity = f["relic"]
    note: Entity = f["note"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {note.phrase}. The note was written in cursive, so she had to look closely.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause and listen to her inner monologue?",
            answer=f"She paused because she wanted to help without scaring the famed goose. Her inner monologue told her to speak kindly and wait.",
        ),
        QAItem(
            question=f"What strange helpful thing could the famed goose do?",
            answer=f"The famed goose could regurgitate the silver key, which was exactly what the village needed to mend the bell.",
        ),
        QAItem(
            question=f"What did teamwork fix in the end?",
            answer=f"Teamwork helped {hero.id}, the famed goose, and the miller tie the rope and bring the silver key back, so the old bell rang again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cursive?",
            answer="Cursive is a style of handwriting where the letters lean and often connect together in a flowing line.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or helpers work together and each one does a part of the job.",
        ),
        QAItem(
            question="What is regurgitate?",
            answer="Regurgitate means to bring food or something from the stomach or throat back out again.",
        ),
        QAItem(
            question="What does famed mean?",
            answer="Famed means well known and talked about by many people.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = _new_world(params)
    _do_story(world)
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
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in SETTINGS:
            samples.append(generate(StoryParams(place=p, hero=HERO_NAMES[0], helper="goose", relic="key")))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
