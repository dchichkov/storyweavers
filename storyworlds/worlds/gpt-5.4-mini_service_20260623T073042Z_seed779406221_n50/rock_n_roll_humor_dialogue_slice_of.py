#!/usr/bin/env python3
"""
storyworlds/worlds/rock_n_roll_humor_dialogue_slice_of.py
==========================================================

A small standalone storyworld for a slice-of-life rock'n'roll scene with humor
and dialogue.

Seed tale, used as the world premise:
---
A kid named Mina loves rock'n'roll. One afternoon, she brings a toy guitar and
a tiny drum to the kitchen while her older brother Jules tries to finish a quiet
puzzle. Mina wants to play a loud song, but the apartment is already full of
soft evening sounds: a simmering pot, a sleepy cat, and Mom on a work call.

Mina strums too hard and the cat darts under the table. Jules laughs and says
the song is starting to sound like a thunderstorm in sneakers. Mom pauses her
call and reminds Mina that the neighbors can hear everything through the wall.

Mina pouts, then spots a cereal box and an empty tea tin. She taps out a new
beat on the counter and whispers a goofy chorus instead of shouting it. Jules
adds claps, Mom smiles, and even the cat peeks back out.

By the end, the music is still rock'n'roll, but it is careful and playful too.
The apartment becomes a tiny family stage, and nobody has to yell.

World idea:
- The hero wants noisy rock'n'roll.
- The tension is about volume in a shared home.
- The turn is a clever quieter jam using ordinary objects.
- The ending proves the change by showing the room calm, the cat back, and
  everyone laughing together.

This file follows the storyworld contract:
- stdlib only
- shared result containers imported eagerly
- lazy ASP import inside helper functions
- params registry, parser, resolver, generate, emit, main
- trace, qa, json, asp, verify, show-asp support
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
LOUD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setup:
    place: str
    time: str
    shared_wall: bool = True
    cozy: bool = True


@dataclass
class Instrument:
    id: str
    label: str
    sound: str
    loudness: float
    can_whisper: bool = False


@dataclass
class Fix:
    id: str
    label: str
    method: str
    mood: str
    quiet_bonus: float


class World:
    def __init__(self, setup: Setup) -> None:
        self.setup = setup
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setup)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_noise(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters.get("volume", 0.0) < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("cat").memes["startle"] += 1
    world.get("brother").memes["amusement"] += 1
    out.append("The cat shot under the table.")
    return out


def _r_wall(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters.get("volume", 0.0) < THRESHOLD:
        return out
    if not world.setup.shared_wall:
        return out
    sig = ("wall",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("parent").memes["worry"] += 1
    out.append("The wall carried the music right into the next room.")
    return out


RULES = [Rule("noise", _r_noise), Rule("wall", _r_wall)]


def setup_at_risk(instrument: Instrument) -> bool:
    return instrument.loudness >= 1.0


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room in SETUPS:
        for instr in INSTRUMENTS:
            if setup_at_risk(INSTRUMENTS[instr]):
                combos.append((room, instr))
    return combos


@dataclass
class StoryParams:
    setup: str
    instrument: str
    fix: str
    hero: str
    hero_type: str
    sibling: str
    sibling_type: str
    parent: str
    seed: Optional[int] = None


SETUPS = {
    "kitchen": Setup(place="the kitchen", time="evening", shared_wall=True, cozy=True),
    "living_room": Setup(place="the living room", time="evening", shared_wall=True, cozy=True),
}
INSTRUMENTS = {
    "guitar": Instrument("guitar", "toy guitar", "twang", 1.4, can_whisper=True),
    "drum": Instrument("drum", "tiny drum", "bap-bap", 1.5, can_whisper=False),
    "keyboard": Instrument("keyboard", "little keyboard", "plink", 1.1, can_whisper=True),
}
FIXES = {
    "whisper_song": Fix("whisper_song", "a whisper-song", "play the riff softly", "gentle", 0.8),
    "table_beat": Fix("table_beat", "a table beat", "tap the cereal box and tea tin", "funny", 0.7),
    "headphone_jam": Fix("headphone_jam", "headphones", "plug in headphones and nod along", "cool", 0.9),
}
HEROES = ["Mina", "Nia", "Luna", "Ada", "Tess"]
SIBLINGS = ["Jules", "Ben", "Owen", "Milo", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rock'n'roll slice-of-life storyworld.")
    ap.add_argument("--setup", choices=SETUPS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sibling")
    ap.add_argument("--sibling-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def reasonableness_gate(setup: Setup, instrument: Instrument, fix: Fix) -> bool:
    return setup.shared_wall and instrument.loudness >= 1.0 and fix.quiet_bonus > 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setup is None or c[0] == args.setup)
              and (args.instrument is None or c[1] == args.instrument)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setup, instrument = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sibling_type = args.sibling_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HEROES if hero_type == "girl" else SIBLINGS)
    sibling = args.sibling or rng.choice([n for n in SIBLINGS + HEROES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    if not reasonableness_gate(SETUPS[setup], INSTRUMENTS[instrument], FIXES[fix]):
        raise StoryError("That setup would not support a sensible rock'n'roll fix.")
    return StoryParams(setup, instrument, fix, hero, hero_type, sibling, sibling_type, parent)


def tell(params: StoryParams) -> World:
    world = World(SETUPS[params.setup])
    hero = world.add(Entity("hero", "character", params.hero_type, params.hero, role="hero"))
    sibling = world.add(Entity("sibling", "character", params.sibling_type, params.sibling, role="sibling"))
    parent = world.add(Entity("parent", "character", "mother" if params.parent == "mother" else "father", f"the {params.parent}"))
    cat = world.add(Entity("cat", "character", "cat", "the cat"))
    instr = world.add(Entity("instrument", "thing", params.instrument, INSTRUMENTS[params.instrument].label))
    fix = world.add(Entity("fix", "thing", "thing", FIXES[params.fix].label))
    for e in [hero, sibling, parent, cat, instr, fix]:
        e.meters.setdefault("volume", 0.0)
        e.meters.setdefault("quiet", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("worry", 0.0)
        e.memes.setdefault("amusement", 0.0)
        e.memes.setdefault("startle", 0.0)
    world.say(f"{hero.id} loved rock'n'roll and wanted the song to bounce around {world.setup.place}.")
    world.say(f"{sibling.id} was already there, saying, \"Keep it fun, but maybe not thunder-fun.\"")
    world.para()
    world.say(f"\"I know,\" {hero.id} said, and picked up the {instr.label}.")
    hero.meters["volume"] += INSTRUMENTS[params.instrument].loudness
    propagate(world, narrate=True)
    world.para()
    world.say(f"{parent.id} looked over from {world.setup.place} and said, \"That sounded like sneakers in a storm.\"")
    world.say(f"\"I can do better,\" {hero.id} said. \"I just need a cleverer chorus.\"")
    world.say(f"{sibling.id} grinned. \"Try the {fix.label}.\"")
    hero.meters["quiet"] += fix.quiet_bonus
    hero.meters["volume"] = 0.2
    sibling.memes["amusement"] += 1
    parent.memes["worry"] = max(0.0, parent.memes["worry"] - 1.0)
    cat.memes["startle"] = 0.0
    world.para()
    world.say(f"So {hero.id} used {fix.method}, and the beat turned small enough to fit the kitchen table.")
    world.say(f"{sibling.id} added claps, {parent.id} smiled, and the cat came back to the doorway like an encore.")
    world.say(f"By the end, the whole room was still rock'n'roll, just in a whispering, grinny way.")
    world.facts.update(hero=hero, sibling=sibling, parent=parent, cat=cat, instr=instr, fix=fix, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a young child about {f["hero"].id} and a rock\'n\'roll practice that gets too loud in {world.setup.place}.',
        f'Tell a funny home story where {f["hero"].id} wants to play {f["instr"].label}, {f["sibling"].id} teases them, and they find a quieter way to keep the music going.',
        f'Write a gentle dialogue-driven story where a family turns loud rock\'n\'roll into a small indoor jam using {f["fix"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]; sibling = f["sibling"]; parent = f["parent"]; fix = f["fix"]; instr = f["instr"]
    return [
        QAItem(question=f"What did {hero.id} want to do?", answer=f"{hero.id} wanted to play rock'n'roll on the {instr.label} in {world.setup.place}."),
        QAItem(question=f"Why did {sibling.id} make a joke about the music?", answer=f"Because the first try sounded so loud that it was like a thunderstorm in sneakers."),
        QAItem(question=f"What did {parent.id} worry about?", answer=f"{parent.id} worried that the music could be heard through the wall and bother other people."),
        QAItem(question=f"How did they fix the problem?", answer=f"They used {fix.label} and made the beat softer, funny, and easier for everyone in the apartment."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is rock'n'roll?", answer="Rock'n'roll is lively music with a beat that makes people want to tap, clap, and dance."),
        QAItem(question="Why do people practice music quietly at home?", answer="People practice quietly at home so they can enjoy music without bothering neighbors or waking someone up."),
        QAItem(question="What is a whisper song?", answer="A whisper song is a song sung softly so it sounds playful but stays gentle."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
loud(I) :- volume(I,V), V >= 1.
quiet_fix(F) :- fix(F), quiet_bonus(F,B), B > 0.
reasonable(S,I,F) :- shared_wall(S), loud(I), quiet_fix(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETUPS.items():
        lines.append(asp.fact("shared_wall", sid) if s.shared_wall else f"not_shared_wall({sid}).")
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("volume", iid, int(inst.loudness * 10)))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("quiet_bonus", fid, int(fx.quiet_bonus * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    asp_set = set(asp.atoms(model, "reasonable"))
    py_set = set((s, i, f) for s, i in valid_combos() for f in FIXES if reasonableness_gate(SETUPS[s], INSTRUMENTS[i], FIXES[f]))
    if asp_set == py_set:
        print("OK: ASP matches Python reasonableness.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show reasonable/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for p in [StoryParams("kitchen", "guitar", "table_beat", "Mina", "girl", "Jules", "boy", "mother")]:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
