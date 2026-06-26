#!/usr/bin/env python3
"""
storyworlds/worlds/hokey_sound_effects_bad_ending_inner_monologue.py
====================================================================

A small folk-tale storyworld about a hokey little performance, noisy sound
effects, an anxious inner monologue, and a bad ending that still feels like a
complete tale.

Premise:
- In a village or by a hearth, a child or small helper tries a hokey trick
  with a noisy instrument or charm.
- The sound effects make the scene feel lively at first: "clack", "thump",
  "whirr", "toot".
- The character's inner monologue exposes worry, pride, or hope.
- The attempt goes wrong, and the ending is a loss or disappointment rather
  than a neat fix.

This world is intentionally tiny: a single folk-tale beat, simulated through
state changes in the child's feelings, the object's condition, and the final
outcome.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "daughter"}
        male = {"boy", "father", "man", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    echoes: bool = False
    hush: bool = False


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    sound: str
    risk: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    charm: str
    name: str
    gender: str
    kin: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "village": Place(id="village", label="the village green", indoors=False, echoes=False),
    "hearth": Place(id="hearth", label="the old hearth room", indoors=True, hush=True),
    "bridge": Place(id="bridge", label="the stone bridge", indoors=False, echoes=True),
    "barn": Place(id="barn", label="the red barn", indoors=True, echoes=True),
}

CHARMS = {
    "bell": Charm(
        id="bell",
        label="a hokey little bell",
        phrase="a hokey little bell with a bent handle",
        sound="clink-clink",
        risk="it might crack with a sharp clatter",
        outcome="the bell split and fell quiet",
        tags={"noise", "metal", "crack"},
    ),
    "drum": Charm(
        id="drum",
        label="a hokey hide drum",
        phrase="a hokey hide drum tied with string",
        sound="thump-thump",
        risk="the patch might tear with a hard thump",
        outcome="the drumskin tore and sagged",
        tags={"noise", "drum", "tear"},
    ),
    "flute": Charm(
        id="flute",
        label="a hokey reed flute",
        phrase="a hokey reed flute with three holes",
        sound="toot-toot",
        risk="the reed might split with a shrill toot",
        outcome="the reed split and made only a whisper",
        tags={"noise", "reed", "split"},
    ),
    "rattle": Charm(
        id="rattle",
        label="a hokey nut rattle",
        phrase="a hokey nut rattle strung on cord",
        sound="clack-clack",
        risk="the cord might snap with a busy clack",
        outcome="the cord snapped and the nuts rolled away",
        tags={"noise", "cord", "snap"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Elsa", "Nora", "Tessa", "Anya"]
BOY_NAMES = ["Oren", "Pavel", "Bram", "Tomas", "Jonah", "Drew"]
TRAITS = ["brave", "hopeful", "earnest", "small", "restless", "dreamy"]


class StoryGateError(StoryError):
    pass


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS.values():
        for charm in CHARMS.values():
            if place.indoors or place.echoes or place.label == "the village green":
                combos.append((place.id, charm.id))
    return combos


def reasonableness_gate(place: Place, charm: Charm) -> bool:
    return (place.indoors or place.echoes or place.id == "village") and "noise" in charm.tags


def explain_rejection(place: Place, charm: Charm) -> str:
    return (
        f"(No story: {charm.label} needs a setting that can carry its noisy folk-tale "
        f"business, and {place.label} is not a fit.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: hokey sound effects, an inner monologue, and a bad ending."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--kin", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    if args.place and args.charm:
        place = SETTINGS[args.place]
        charm = CHARMS[args.charm]
        if not reasonableness_gate(place, charm):
            raise StoryError(explain_rejection(place, charm))

    combos = [
        (p, c) for p, c in valid_combos()
        if (args.place is None or p == args.place)
        and (args.charm is None or c == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, charm_id = rng.choice(sorted(combos))
    charm = CHARMS[charm_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    kin = args.kin or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, charm=charm_id, name=name, gender=gender, kin=kin, trait=trait)


def _intro(world: World, hero: Entity, kin: Entity, charm: Charm) -> None:
    world.say(
        f"Once, in {world.place.label}, there was a {hero.pronoun('object')} little {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} was {hero.memes['trait_word']} and liked anything that sounded like a tale."
    )
    world.say(
        f"One day {hero.id}'s {kin.label} showed {hero.pronoun('object')} {charm.phrase}."
    )


def _sound(world: World, charm: Charm) -> None:
    world.say(
        f"The little thing went {charm.sound}, {charm.sound}, as if it wanted the whole world to listen."
    )


def _inner_monologue(world: World, hero: Entity, charm: Charm) -> None:
    world.say(
        f"In {hero.pronoun('possessive')} own mind, {hero.id} thought, "
        f"\"If I can make this work, maybe everyone will call me wise and clever.\""
    )
    world.say(
        f"But another thought came right after: \"What if it goes wrong and I look hokey in front of {hero.pronoun('possessive')} kin?\""
    )


def _attempt(world: World, hero: Entity, charm: Charm) -> None:
    hero.memes["hope"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"Still, {hero.id} lifted the {charm.label} and gave it a brave shake."
    )
    world.say(
        f"It answered with a sharp {charm.sound}, and the air seemed to hold its breath."
    )


def _bad_ending(world: World, hero: Entity, kin: Entity, charm: Charm) -> None:
    hero.meters["failure"] += 1
    hero.memes["shame"] += 1
    world.say(
        f"Then, with one last {charm.sound}, the old trick failed in the worst way."
    )
    world.say(
        f"{charm.outcome.capitalize()}, and {hero.id} stood there with empty hands while {hero.pronoun('possessive')} {kin.label} looked on in silence."
    )
    world.say(
        f"The village kept its hush, and {hero.id} learned that a hokey plan can sound grand right up until it breaks."
    )


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    charm = CHARMS[params.charm]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"failure": 0.0},
        memes={"hope": 0.0, "fear": 0.0, "shame": 0.0, "trait_word": params.trait},
    ))
    kin = world.add(Entity(id="Kin", kind="character", type=params.kin, label=f"{params.kin}"))
    relic = world.add(Entity(
        id="Charm",
        type=charm.id,
        label=charm.label,
        phrase=charm.phrase,
        owner=hero.id,
        carried_by=hero.id,
    ))

    world.facts.update(hero=hero, kin=kin, charm=charm, place=place)
    _intro(world, hero, kin, charm)
    world.say("Then came the sound of it all.")
    _sound(world, charm)
    _inner_monologue(world, hero, charm)
    _attempt(world, hero, charm)
    _bad_ending(world, hero, kin, charm)
    world.facts["relic"] = relic
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    charm = f["charm"]
    place = f["place"]
    return [
        f'Write a folk-tale story about a child named {hero.id} at {place.label} with a hokey {charm.label}.',
        f"Tell a short story that includes sound effects like {charm.sound} and ends badly after {hero.id} tries to impress a kin.",
        f'Write a child-friendly folk tale where the word "hokey" appears and the main character loses the thing they are trying to show off.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    kin = f["kin"]
    charm = f["charm"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to show at {place.label}?",
            answer=f"{hero.id} was trying to show {hero.pronoun('possessive')} {charm.label} to {kin.label}.",
        ),
        QAItem(
            question=f"What sound did the little charm make in the story?",
            answer=f"It made a {charm.sound} sound, and then it made that sound again as the attempt went on.",
        ),
        QAItem(
            question=f"How did {hero.id} feel inside while trying the hokey trick?",
            answer=f"{hero.id} felt hopeful and worried at the same time, because {hero.id} wanted to look clever but feared a mistake.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended badly: {charm.outcome}, and {hero.id} was left standing with an embarrassed, empty feeling.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hokey mean when people call a trick hokey?",
            answer="Hokey means silly, awkward, or not very polished, like a trick that tries hard but feels a little fake or clumsy.",
        ),
        QAItem(
            question="Why do sound effects make a tale feel lively?",
            answer="Sound effects help listeners imagine the action, so a story can feel lively, funny, or tense even when the words are simple.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the words a character thinks to themselves inside their own head.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when the plan fails or the character loses something important instead of getting a happy fix.",
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
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
charms(C) :- charm(C).
noisy(C) :- sound(C,S), S != "".

story_ok(P,C) :- place(P), charm(C), noisy(C), allowed(P,C).

#show story_ok/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("sound", cid, c.sound))
        lines.append(asp.fact("allowed", "village", cid))
        lines.append(asp.fact("allowed", "hearth", cid))
        lines.append(asp.fact("allowed", "bridge", cid))
        lines.append(asp.fact("allowed", "barn", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {(p, c) for p, c in valid_combos()}
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - ac))
    print("clingo-only:", sorted(ac - py))
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


CURATED = [
    StoryParams(place="village", charm="bell", name="Mira", gender="girl", kin="grandmother", trait="hopeful"),
    StoryParams(place="hearth", charm="flute", name="Oren", gender="boy", kin="father", trait="earnest"),
    StoryParams(place="bridge", charm="rattle", name="Nora", gender="girl", kin="mother", trait="dreamy"),
    StoryParams(place="barn", charm="drum", name="Bram", gender="boy", kin="grandfather", trait="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, charm) combos:\n")
        for p, c in combos:
            print(f"  {p:8} {c}")
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
            header = f"### {p.name}: {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
