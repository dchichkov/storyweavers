#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/splish_tortoise_elevator_sound_effects_rhyme_comedy.py
======================================================================================

A standalone storyworld for a tiny comedy about an elevator, a slow tortoise,
and a very silly splish. The simulation keeps a small physical state
(elevator floors, puddle size, bell, cleanup tools) and a tiny emotional state
(fast/embarrassed/proud/amused). The story is driven by state changes, sound
effects, and a few light rhymes so the ending feels authored rather than
template-swapped.

The core seed image is simple:
- a tortoise rides an elevator,
- a drink or puddle makes a splish,
- the other riders react with comedy,
- someone fixes the mess in a sensible way,
- the final line proves the ride changed.

This file is self-contained and stdlib-only.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "tortoise":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    floors: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class NoiseMaker:
    id: str
    label: str
    sound: str
    rhyme: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Cleanup:
    id: str
    label: str
    method: str
    effect: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    place: str
    noise: str
    cleanup: str
    rider_name: str
    rider_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def rain_sound() -> str:
    return "splish-splash"


def rhyme_line(word: str, end: str) -> str:
    return f"{word} and {end}"


def make_noise(world: World, rider: Entity, maker: NoiseMaker) -> None:
    rider.memes["startled"] += 1
    world.get("elevator").meters["mess"] += 1
    world.get("elevator").meters["noise"] += 1
    world.get("mess").meters["wet"] += 1
    world.say(
        f"{maker.sound}! The elevator answered with a {maker.rhyme} rhyme, "
        f"and the little puddle went {maker.sound} on the floor."
    )
    world.say(
        f"{rider.id} blinked. " + '"That was a' + f' {maker.sound} surprise," {rider.pronoun()} said.'
    )


def help_fix(world: World, helper: Entity, cleanup: Cleanup) -> bool:
    if cleanup.sense < SENSE_MIN:
        return False
    mess = world.get("mess")
    elevator = world.get("elevator")
    if cleanup.power >= 1:
        mess.meters["wet"] = 0
        elevator.meters["mess"] = 0
        elevator.meters["noise"] = 0
        helper.memes["pride"] += 1
        world.say(
            f"{helper.id} grinned and used {cleanup.method}. {cleanup.effect.capitalize()}. "
            f"The floor stopped being slippery, and the elevator hummed like a sleepy drum."
        )
        return True
    return False


def tell(place: Place, maker: NoiseMaker, cleanup: Cleanup,
         rider_name: str = "Milo", rider_type: str = "tortoise",
         helper_name: str = "June", helper_type: str = "girl") -> World:
    world = World(place)
    rider = world.add(Entity(id=rider_name, kind="character", type=rider_type, role="rider"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    elevator = world.add(Entity(id="elevator", type="place", label="the elevator"))
    mess = world.add(Entity(id="mess", type="thing", label="the puddle"))
    world.facts.update(rider=rider, helper=helper, maker=maker, cleanup=cleanup,
                       place=place, elevator=elevator, mess=mess)

    world.say(
        f"On a day with a shiny button and a tiny bell, {rider.id} the {rider.type} stepped into "
        f"{place.label}. {helper.id} stepped in too, carrying a cup that tried very hard to stay put."
    )
    world.say(
        f"{rider.id} loved the ride up, because every ding felt like a song. "
        f'Then the cup tipped a little -- {rain_sound()} -- and the elevator got a surprise.'
    )

    world.para()
    make_noise(world, rider, maker)
    world.say(
        f'{helper.id} laughed, not meanly, but the kind of laugh that says, "Oops, that was a slip!" '
        f"{rider.id} tried to back away, but the tiny floor shine made a wobbly line."
    )

    world.para()
    fixed = help_fix(world, helper, cleanup)
    if fixed:
        world.say(
            f"{rider.id} wiped {rider.pronoun('possessive')} shell and bowed like a careful star. "
            f'"No more splish in the elevator," {rider.id} said. "{cleanup.label} and a tidy road, '
            f"so up we go, not in a woe!"
        )
        world.say(
            f"The bell dinged again, and this time the ride was calm, clean, and completely not squishy."
        )
    else:
        world.say(
            f"The mess stayed put, and the elevator had to wait. The riders called for help and hoped "
            f"the next stop would bring a wiser mop."
        )

    world.facts["fixed"] = fixed
    world.facts["outcome"] = "fixed" if fixed else "stuck"
    return world


THEMES = {
    "elevator": Place("elevator", "the elevator", 8, tags={"elevator"}),
}

NOISES = {
    "splish": NoiseMaker("splish", "splish", "splish", "squish", tags={"sound", "rhyme"}),
    "ding": NoiseMaker("ding", "ding", "ding", "ring", tags={"sound", "rhyme"}),
    "plop": NoiseMaker("plop", "plop", "plop", "hop", tags={"sound", "rhyme"}),
}

CLEANUPS = {
    "mop": Cleanup("mop", "a paper towel", "wiped the splash away", "the floor shone again", 1, 3, tags={"cleanup"}),
    "cloth": Cleanup("cloth", "a little cloth", "polished the spot clean", "the floor shone again", 1, 3, tags={"cleanup"}),
    "warning": Cleanup("warning", "a warning sign", "stood there doing nothing", "the puddle stayed put", 0, 1, tags={"cleanup"}),
}

GIRL_NAMES = ["June", "Mina", "Lia", "Penny", "Ivy"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Ollie", "Toby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in THEMES:
        for n in NOISES:
            for c in CLEANUPS:
                if CLEANUPS[c].sense >= SENSE_MIN:
                    combos.append((p, n, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old in an elevator that includes the word "{f["maker"].id}".',
        f"Tell a comedy story where {f['rider'].id} the {f['rider'].type} hears a silly sound effect and a helper tidies the mess.",
        f'Write a rhyming elevator story with the words "splish" and "{f["rider"].type}" and a happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider = f["rider"]
    helper = f["helper"]
    cleanup = f["cleanup"]
    qa = [
        ("Who is the story about?", f"It is about {rider.id} the {rider.type} and {helper.id}, who were riding an elevator."),
        ("What happened in the elevator?", f"A cup tipped and made a {f['maker'].sound} sound, so the floor got a little wet."),
        ("How did they fix it?", f"{helper.id} used {cleanup.label} to clean the puddle, and the elevator was safe again."),
    ]
    if f["fixed"]:
        qa.append((
            f"How did {rider.id} feel at the end?",
            f"{rider.id} felt silly, relieved, and proud because the splish was cleaned up. The ride could keep going without any slipping."
        ))
    else:
        qa.append((
            f"Why did the ride pause?",
            f"The mess was not cleaned yet, so everyone had to wait. They wanted to be careful before the elevator moved again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does an elevator do?", "An elevator carries people up and down between floors in a building."),
        ("What is a tortoise?", "A tortoise is a slow reptile with a hard shell. It walks carefully and never hurries."),
        ("What is a sound effect?", "A sound effect is a fun noise that helps a story feel lively, like ding or splish."),
        ("What is a rhyme?", "A rhyme is when words sound alike at the end, like splish and squish."),
    ]


ASP_RULES = r"""
valid(P,N,C) :- place(P), noise(N), cleanup(C), sense(C, S), sense_min(M), S >= M.
fixed :- cleanup(C), sense(C, S), S >= sense_min(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in THEMES:
        lines.append(asp.fact("place", p))
    for n in NOISES:
        lines.append(asp.fact("noise", n))
    for c, v in CLEANUPS.items():
        lines.append(asp.fact("cleanup", c))
        lines.append(asp.fact("sense", c, v.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    got, exp = set(asp_valid_combos()), set(valid_combos())
    ok = got == exp
    sample = generate(CURATED[0])
    try:
        _ = sample.story
    except Exception:
        ok = False
    if ok:
        print(f"OK: ASP parity and smoke story generation passed ({len(exp)} combos).")
        return 0
    print("MISMATCH or smoke failure.")
    if got - exp:
        print("only in ASP:", sorted(got - exp))
    if exp - got:
        print("only in Python:", sorted(exp - got))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy elevator storyworld with splish and rhyme.")
    ap.add_argument("--place", choices=THEMES)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cleanup and CLEANUPS[args.cleanup].sense < SENSE_MIN:
        raise StoryError("That cleanup choice is too weak for a real story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.noise is None or c[1] == args.noise)
              and (args.cleanup is None or c[2] == args.cleanup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, noise, cleanup = rng.choice(sorted(combos))
    rider_type = "tortoise"
    helper_type = rng.choice(["girl", "boy"])
    rider_name = "Tilly"
    helper_name = rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    return StoryParams(place, noise, cleanup, rider_name, rider_type, helper_name, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.place], NOISES[params.noise], CLEANUPS[params.cleanup],
                 params.rider_name, params.rider_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if parts:
            lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [StoryParams("elevator", "splish", "mop", "Tilly", "tortoise", "June", "girl")]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
