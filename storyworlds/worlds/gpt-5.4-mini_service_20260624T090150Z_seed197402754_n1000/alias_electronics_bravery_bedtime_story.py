#!/usr/bin/env python3
"""
storyworlds/worlds/alias_electronics_bravery_bedtime_story.py
==============================================================

A small bedtime-story world about a child using an alias, a few electronics,
and a brave choice before sleep.
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
    owner: Optional[str] = None
    powered_on: bool = False
    bright: bool = False
    scary_noise: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    place: str = "bedroom"
    dark: bool = True
    quiet: bool = False
    bedtime: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    kind: str
    can_brighten: bool = False
    can_make_noise: bool = False
    can_help_sleep: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        import copy
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for gadget in world.entities.values():
        if not gadget.powered_on or not gadget.scary_noise:
            continue
        sig = ("noise", gadget.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for hero in world.characters():
            hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1
        out.append("The little buzz in the room made bedtime feel harder.")
    return out


def _r_dark(world: World) -> list[str]:
    out: list[str] = []
    if not world.room.dark:
        return out
    if ("dark",) in world.fired:
        return out
    if any(g.powered_on and g.bright for g in world.entities.values()):
        world.fired.add(("dark",))
        out.append("A small light kept the room from feeling too dark.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    if not hero:
        return out
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    sig = ("bravery", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    out.append("The brave choice helped the child breathe slowly and feel ready for sleep.")
    return out


CAUSAL_RULES = [_r_noise, _r_dark, _r_bravery]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_world(world: World) -> World:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim


def start_story(world: World, hero: Entity, alias: Entity, gadget: Entity) -> None:
    world.say(
        f"At bedtime, {hero.id} liked to pretend to be {alias.phrase}, "
        f"a tiny hero with a quiet name."
    )
    world.say(
        f"Near the pillow sat {gadget.phrase}, and {hero.id} kept glancing at it "
        f"because the glowing screen felt hard to leave alone."
    )


def conflict_story(world: World, hero: Entity, alias: Entity, gadget: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    if gadget.powered_on:
        world.say(
            f"{hero.id} wanted one more look at {gadget.label}, but the bright screen "
            f"made the room feel too awake."
        )
    else:
        world.say(
            f"{hero.id} still thought about {gadget.label}, even after the room grew quiet."
        )
    world.say(
        f"Then {hero.id} whispered, 'I can be {alias.phrase} and be brave too.'"
    )


def turn_story(world: World, hero: Entity, gadget: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    gadget.powered_on = False
    world.say(
        f"{hero.id} pressed the button to turn {gadget.label} off, and the buzzing stopped."
    )
    propagate(world, narrate=True)


def ending_story(world: World, hero: Entity, alias: Entity, gadget: Entity) -> None:
    hero.memes["sleepy"] = hero.memes.get("sleepy", 0.0) + 1
    world.say(
        f"With the screen dark, {hero.id} tucked {gadget.pronoun('object')} beside the bed, "
        f"smiled at the brave name {alias.phrase}, and closed {hero.pronoun('possessive')} eyes."
    )
    world.say(
        f"The room was still, the toy light stayed off, and bedtime finally felt soft and safe."
    )


@dataclass
class StoryParams:
    alias: str
    electronics: str
    name: str
    gender: str
    seed: Optional[int] = None


ALIASES = {
    "moonfox": "Moon Fox",
    "starcap": "Star Cap",
    "nightowl": "Night Owl",
    "pockethero": "Pocket Hero",
}

ROOMS = {
    "bedroom": Room(place="bedroom", dark=True, quiet=False, bedtime=True, affords={"phone", "nightlight", "tablet"}),
}

GADGETS = {
    "phone": Gadget(
        id="phone",
        label="the phone",
        phrase="a little phone by the pillow",
        kind="phone",
        can_make_noise=True,
        tags={"electronics", "screen"},
    ),
    "tablet": Gadget(
        id="tablet",
        label="the tablet",
        phrase="a tablet with a glowing screen",
        kind="tablet",
        can_make_noise=True,
        tags={"electronics", "screen"},
    ),
    "nightlight": Gadget(
        id="nightlight",
        label="the nightlight",
        phrase="a tiny nightlight on the shelf",
        kind="nightlight",
        can_brighten=True,
        can_help_sleep=True,
        tags={"electronics", "light"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max"]


def asp_facts() -> str:
    import asp
    lines = []
    for a in ALIASES:
        lines.append(asp.fact("alias", a))
    for g in GADGETS.values():
        lines.append(asp.fact("electronics", g.id))
        if g.can_brighten:
            lines.append(asp.fact("brightener", g.id))
        if g.can_make_noise:
            lines.append(asp.fact("noisy", g.id))
        if g.can_help_sleep:
            lines.append(asp.fact("sleep_helper", g.id))
    lines.append(asp.fact("room", "bedroom"))
    lines.append(asp.fact("bedtime", "bedroom"))
    return "\n".join(lines)


ASP_RULES = r"""
story_ok(A, E) :- alias(A), electronics(E).
"""
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def story_ok_py(alias: str, electronics: str) -> bool:
    return alias in ALIASES and electronics in GADGETS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    alias = args.alias or rng.choice(sorted(ALIASES))
    electronics = args.electronics or rng.choice(sorted(GADGETS))
    if not story_ok_py(alias, electronics):
        raise StoryError("The requested alias and electronics do not fit this bedtime story.")
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    return StoryParams(alias=alias, electronics=electronics, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story about a child who uses the alias "{f["alias_phrase"]}" and learns bravery.',
        f"Tell a gentle story about {f['hero'].id}, {f['electronics'].label}, and falling asleep bravely.",
        f'Write a short bedtime tale that includes the words "alias" and "electronics" and ends quietly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    alias = f["alias_phrase"]
    gadget = f["gadget"]
    return [
        QAItem(
            question=f"What alias did {hero.id} like to use at bedtime?",
            answer=f"{hero.id} liked to use the name {alias} as a brave pretend name at bedtime.",
        ),
        QAItem(
            question=f"What electronics were near the pillow in the story?",
            answer=f"The story featured {gadget.label}, which stayed close to the bed until it was turned off.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by turning off {gadget.label} even though the glowing screen felt hard to leave alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are electronics?",
            answer="Electronics are tools or devices that run on electricity, like phones, tablets, and lights.",
        ),
        QAItem(
            question="Why is a bedtime room often kept quiet?",
            answer="A quiet bedroom helps a child calm down, feel sleepy, and get ready for rest.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something kind or sensible even when you feel nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.powered_on:
            bits.append("powered_on=True")
        if e.bright:
            bits.append("bright=True")
        if e.scary_noise:
            bits.append("scary_noise=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS["bedroom"]
    world = World(room)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    alias = world.add(Entity(id="alias", type="name", label="alias", phrase=ALIASES[params.alias]))
    gadget = world.add(Entity(
        id=params.electronics,
        kind="object",
        type=params.electronics,
        label=f"the {params.electronics}",
        phrase=GADGETS[params.electronics].phrase,
        powered_on=True,
        bright=GADGETS[params.electronics].can_brighten,
        scary_noise=GADGETS[params.electronics].can_make_noise,
    ))
    world.facts.update(
        hero=hero,
        alias_phrase=alias.phrase,
        gadget=gadget,
        electronics=GADGETS[params.electronics],
    )

    start_story(world, hero, alias, gadget)
    world.para()
    conflict_story(world, hero, alias, gadget)
    turn_story(world, hero, gadget)
    world.para()
    ending_story(world, hero, alias, gadget)

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
    ap = argparse.ArgumentParser(description="Bedtime story world about an alias, electronics, and bravery.")
    ap.add_argument("--alias", choices=sorted(ALIASES))
    ap.add_argument("--electronics", choices=sorted(GADGETS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {(a, e) for a in ALIASES for e in GADGETS if story_ok_py(a, e)}
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


CURATED = [
    StoryParams(alias="moonfox", electronics="nightlight", name="Mia", gender="girl"),
    StoryParams(alias="starcap", electronics="tablet", name="Leo", gender="boy"),
    StoryParams(alias="nightowl", electronics="phone", name="Nora", gender="girl"),
]


def resolve_params_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible alias/electronics pairs:\n")
        for a, e in combos:
            print(f"  {a:10} {e}")
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.alias} with {p.electronics}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
