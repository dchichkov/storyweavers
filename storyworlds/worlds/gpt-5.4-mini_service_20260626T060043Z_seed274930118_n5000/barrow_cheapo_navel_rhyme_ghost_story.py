#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/barrow_cheapo_navel_rhyme_ghost_story.py
===============================================================================================================

A tiny story world about a child, a ghostly rhyme, and a small barrow of cheap things
that should not be left near a lonely grave at night.

Premise:
- A child likes to chant a silly rhyme.
- A cheapo toy barrow and a glowing navel charm are part of the problem.
- A friendly ghost is startled, then gently helps set things right.

The world is constrained so that every generated story is a complete little
ghost story: it begins with a spooky setup, turns on a rhyme-related mishap,
and ends with a safe, clear resolution image.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- eager results import, lazy ASP import
- build_parser / resolve_params / generate / emit / main
- reasonableness gate + inline ASP twin
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
class Setting:
    place: str
    indoors: bool = False
    offers: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    allowed_places: set[str] = field(default_factory=set)
    rhyme_key: str = ""
    is_spooky: bool = False


@dataclass
class Ghost:
    id: str
    label: str
    phrase: str
    charm: str
    is_kind: bool = True
    rhyme_key: str = "rhyme"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    rhyme_on: bool = False
    moon: str = "full"

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


def _default_meters() -> dict[str, float]:
    return {"spook": 0.0, "dust": 0.0, "shine": 0.0}


def _default_memes() -> dict[str, float]:
    return {"fear": 0.0, "curiosity": 0.0, "relief": 0.0, "joy": 0.0, "rhythm": 0.0}


def _r_spook(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("spook", 0.0) < THRESHOLD:
            continue
        sig = ("spook", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
        out.append(f"A chill ran through the {world.setting.place}.")
    return out


def _r_rhyme(world: World) -> list[str]:
    out = []
    if not world.rhyme_on:
        return out
    for actor in world.characters():
        if actor.memes.get("rhythm", 0.0) < THRESHOLD:
            continue
        sig = ("rhyme", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The rhyme bounced softly in the dark like a small drum.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if ghost.meters.get("shine", 0.0) < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    out.append("The dark felt kinder after that.")
    return out


RULES = [
    _r_spook,
    _r_rhyme,
    _r_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(child: Entity, prop: Entity, ghost: Entity) -> str:
    return (
        f"{child.id} sang, “By the barrow, by the moon, "
        f"{prop.label} will glow and wobble soon.”"
    )


def setting_line(setting: Setting) -> str:
    if setting.indoors:
        return f"The {setting.place} was quiet, with one cold window and a creaky floor."
    return f"The {setting.place} waited under the moon, with grass like dark ribbon."


def intro_line(child: Entity, prop: Entity, ghost: Entity) -> str:
    return (
        f"{child.id} was a little {next((t for t in child.traits if t != 'little'), 'curious')} "
        f"{child.type} who loved a silly rhyme."
    )


def prop_line(prop: Entity) -> str:
    return f"{prop.id} had a cheapo little look, but {prop.phrase} made it hard to ignore."


def ghost_line(ghost: Entity) -> str:
    return f"{ghost.label} was a friendly ghost who did not like loud tricks near the barrow."


def startle(world: World, child: Entity, prop: Entity, ghost: Entity) -> None:
    child.meters["spook"] = child.meters.get("spook", 0.0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"One night, {child.id} carried a little barrow to the old path, "
        f"with {prop.phrase} tucked inside."
    )
    world.say(setting_line(world.setting))
    world.say(ghost_line(ghost))
    world.say(
        f"{child.id} began to chant the rhyme again, because {child.pronoun('subject')} "
        f"thought the echo sounded funny."
    )
    world.rhyme_on = True
    child.memes["rhythm"] = child.memes.get("rhythm", 0.0) + 1
    propagate(world, narrate=True)


def turn(world: World, child: Entity, prop: Entity, ghost: Entity) -> None:
    world.para()
    world.say(
        f"Then the navel charm gave off a tiny glow, and the ghost turned to look."
    )
    ghost.meters["shine"] = ghost.meters.get("shine", 0.0) + 1
    world.say(
        f"{ghost.label} did not howl. Instead, {ghost.pronoun().capitalize()} drifted closer "
        f"and listened to the last line of the song."
    )
    world.say(
        f"{ghost.pronoun().capitalize()} said the rhyme was fine, but the barrow should not be "
        f"dragged across the stones at midnight."
    )
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    propagate(world, narrate=True)


def resolve(world: World, child: Entity, prop: Entity, ghost: Entity) -> None:
    world.para()
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    world.say(
        f"{child.id} nodded, set the cheapo barrow down, and held the navel charm in both hands."
    )
    world.say(
        f"The ghost smiled and floated beside {child.pronoun('object')}, "
        f"showing {child.pronoun('object')} a safer place for the rhyme: the porch, "
        f"where the wind could whisper instead of rattle."
    )
    world.say(
        f"At the end, the barrow rested still, the navel charm glimmered like a tiny star, "
        f"and the old path stayed peaceful."
    )
    prop.meters["shine"] = prop.meters.get("shine", 0.0) + 1


def tell(setting: Setting, child_name: str, ghost_name: str = "Moth") -> World:
    world = World(setting=setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type="boy" if child_name in BOY_NAMES else "girl",
        traits=["little", "cheerful", "curious"],
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=ghost_name,
        phrase=f"{ghost_name}, the friendly ghost",
        traits=["kind", "quiet"],
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    barrow = world.add(Entity(
        id="barrow",
        type="barrow",
        label="barrow",
        phrase="a cheapo little barrow with a loose wheel",
        meters=_default_meters(),
    ))
    charm = world.add(Entity(
        id="navel",
        type="charm",
        label="navel charm",
        phrase="a navel charm that glowed like a button moon",
        meters=_default_meters(),
    ))
    world.facts.update(child=child, ghost=ghost, barrow=barrow, charm=charm)
    world.say(intro_line(child, barrow, ghost))
    world.say(prop_line(barrow))
    world.say(
        f"{ghost.label} had a habit of listening when someone sang near the old stones."
    )
    startle(world, child, barrow, ghost)
    turn(world, child, charm, ghost)
    resolve(world, child, barrow, ghost)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "graveyard": Setting(place="the graveyard", indoors=False, offers={"rhyme"}),
    "churchyard": Setting(place="the churchyard", indoors=False, offers={"rhyme"}),
    "porch": Setting(place="the porch", indoors=True, offers={"rhyme"}),
}

BOY_NAMES = ["Ben", "Tom", "Ned", "Finn", "Owen"]
GIRL_NAMES = ["Mina", "Ivy", "June", "Lena", "Pia"]
ALL_NAMES = BOY_NAMES + GIRL_NAMES
TRAITS = ["brave", "cheerful", "curious", "silly", "gentle"]


@dataclass
class StoryParams:
    place: str
    name: str
    ghost: str
    trait: str
    seed: Optional[int] = None


def valid_places() -> list[str]:
    return list(SETTINGS.keys())


def reason_bad_place(place: str) -> str:
    return f"(No story: the rhyme-ghost tale needs a spooky place, not {place!r}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyme-and-ghost story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--ghost", default="Moth")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.place not in SETTINGS:
        raise StoryError(reason_bad_place(args.place))
    place = args.place or rng.choice(valid_places())
    name = args.name or rng.choice(ALL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    ghost = args.ghost
    return StoryParams(place=place, name=name, ghost=ghost, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short ghost story for a young child that includes the words "barrow", "cheapo", and "navel".',
        f"Tell a spooky but gentle story where {child.id} chants a rhyme near {world.setting.place} and a friendly ghost answers.",
        f"Write a tiny rhyme-filled story with a cheapo barrow, a glowing navel charm, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    barrow: Entity = f["barrow"]
    charm: Entity = f["charm"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who carried the cheapo barrow to {place}?",
            answer=f"{child.id} carried the cheapo barrow to {place}, while the friendly ghost watched nearby.",
        ),
        QAItem(
            question=f"What was inside the barrow when {child.id} began the rhyme?",
            answer=f"The barrow held the navel charm, which gave off a tiny glow in the dark.",
        ),
        QAItem(
            question=f"Why did the ghost listen to {child.id}'s song?",
            answer=f"The ghost liked hearing the rhyme, but also wanted to keep the old path calm and safe.",
        ),
        QAItem(
            question=f"How did the story end for the barrow and the navel charm?",
            answer=f"By the end, the barrow rested still and the navel charm glimmered like a tiny star.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky spirit in stories. In gentle tales, a ghost can still be kind and helpful.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like moon and soon.",
        ),
        QAItem(
            question="What is a barrow?",
            answer="A barrow is a small cart or wheelbarrow used to carry things from one place to another.",
        ),
        QAItem(
            question="What does cheapo mean?",
            answer="Cheapo means something is made to be very inexpensive or a little flimsy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  rhyme_on={world.rhyme_on}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- setting(P).

ghost_story(P) :- place_ok(P), rhyme_risk(P), has_barrow, has_navel, has_ghost.

rhyme_risk(P) :- spooky_place(P).
spooky_place(graveyard).
spooky_place(churchyard).
spooky_place(porch).

has_barrow :- barrow.
has_navel :- navel.
has_ghost :- ghost.

valid(P) :- ghost_story(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    lines.append(asp.fact("barrow"))
    lines.append(asp.fact("navel"))
    lines.append(asp.fact("ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = {(p,) for p in valid_places()}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches valid_places() ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.ghost)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="graveyard", name="Ben", ghost="Moth", trait="curious"),
    StoryParams(place="churchyard", name="Mina", ghost="Moth", trait="silly"),
    StoryParams(place="porch", name="Ivy", ghost="Moth", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        places = asp_valid_places()
        print(f"{len(places)} valid places:")
        for (p,) in places:
            print(f"  {p}")
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
            header = f"### {p.name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
