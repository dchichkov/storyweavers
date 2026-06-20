#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/administrative_skeletal_retardo_surprise_cautionary_flashback_ghost.py
======================================================================================================

A standalone story world for a tiny ghost-story domain: a child or clerk enters
an administrative office after hours, meets a skeletal helper named Retardo, is
startled by a surprise, receives a cautionary warning, and remembers a flashback
that explains the haunting. The ending proves the room changed from eerie to
understood and orderly.

This script is self-contained, stdlib-only, and follows the Storyweavers
storyworld contract.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FEAR_START = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    administrative: bool = False
    after_hours: bool = False
    quiet: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostThing:
    id: str
    label: str
    phrase: str
    spooky_sound: str
    makes_surprise: bool = False
    makes_flashback: bool = False
    cautionary: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["surprise"] < THRESHOLD:
            continue
        sig = ("surprise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.entities.values():
            if kid.kind == "character":
                kid.memes["fear"] += 1
        out.append("__surprise__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("flashback_seen") and ("flashback", "seen") not in world.fired:
        world.fired.add(("flashback", "seen"))
        narrator = world.facts.get("narrator")
        if narrator:
            narrator.memes["understanding"] += 1
        out.append("__flashback__")
    return out


def _r_caution(world: World) -> list[str]:
    out: list[str] = []
    helper = world.facts.get("helper")
    if helper and helper.memes["caution"] >= THRESHOLD and ("caution", helper.id) not in world.fired:
        world.fired.add(("caution", helper.id))
        world.facts["caution_spoken"] = True
        out.append("__caution__")
    return out


CAUSAL_RULES = [
    Rule("surprise", "social", _r_surprise),
    Rule("flashback", "social", _r_flashback),
    Rule("caution", "social", _r_caution),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(place: Place, thing: GhostThing) -> bool:
    return place.administrative and thing.makes_surprise and thing.makes_flashback and thing.cautionary


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for tid, t in THINGS.items():
            if is_reasonable(p, t):
                combos.append((pid, tid))
    return combos


def _do_haunting(world: World, ghost: Entity, thing: GhostThing) -> None:
    ghost.meters["surprise"] += 1
    world.facts["flashback_seen"] = True
    propagate(world, narrate=False)


def predict_dread(world: World, thing_id: str) -> dict:
    sim = world.copy()
    _do_haunting(sim, sim.get("retardo"), THINGS[thing_id])
    return {
        "surprise": sim.get("retardo").meters["surprise"] >= THRESHOLD,
        "understanding": sim.facts.get("flashback_seen", False),
    }


@dataclass
class StoryParams:
    place: str
    thing: str
    narrator_name: str
    helper_name: str
    narrator_gender: str
    helper_gender: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    thing = THINGS[params.thing]
    world = World(place)

    narrator = world.add(Entity(id=params.narrator_name, kind="character", type=params.narrator_gender, role="narrator"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    ghost = world.add(Entity(id="retardo", kind="character", type="thing", label="Retardo", role="ghost"))
    world.facts.update(narrator=narrator, helper=helper, ghost=ghost, place=place, thing=thing)

    narrator.memes["curiosity"] += 1
    helper.memes["caution"] += 1

    world.say(
        f"At the end of the day, the {place.label} grew quiet, and {params.narrator_name} "
        f"wandered through the administrative hallway with a lamp in hand. The filing room "
        f"smelled like paper and dust, and the metal cabinets stood in straight little rows."
    )
    world.say(
        f"Then a soft clack came from behind the drawer cart. A skeletal shape lifted from the shadows: "
        f"{ghost.label}, all ribs and paper-thin fingers, holding {thing.phrase} like it had waited there forever."
    )
    ghost.meters["surprise"] += 1
    _do_haunting(world, ghost, thing)

    world.para()
    world.say(
        f'"What is that?" {params.narrator_name} gasped. {params.helper_name} stepped closer, then stopped '
        f"with a careful look."
    )
    if predict_dread(world, thing.id)["surprise"]:
        world.say(
            f'"Do not touch it yet," {params.helper_name} said softly. "A strange thing in an office after hours '
            f"can be a warning, not a toy."'
        )
    else:
        world.say(f'"That should stay where it is," {params.helper_name} said, still calm.')

    world.facts["caution_spoken"] = True
    world.facts["flashback_seen"] = True
    world.say(
        f"The warning pulled a flashback into {params.narrator_name}'s mind: earlier that afternoon, the manager "
        f"had locked the records away and told everyone that the old room kept its secrets until closing time."
    )
    world.say(
        f"In the memory, Retardo had not been scary at all. He had been a tiny skeletal clerk, forever late with "
        f"forms, forever tidying the shelves, forever muttering that the {thing.label} belonged back in the correct file."
    )

    world.para()
    world.say(
        f"{params.narrator_name} blinked, and the fright changed into understanding. {ghost.label} set "
        f"{thing.label} on the desk and bowed his bony head."
    )
    ghost.memes["sad"] += 1
    ghost.memes["relief"] += 1
    world.say(
        f'The "ghost" was only guarding the room. The old {thing.label} was the last missing piece of the office '
        f"archive, and the room felt less eerie once it was back in order."
    )
    world.say(
        f'Together, they slid the {thing.label} into its labeled drawer, closed the cabinet, and left the {place.label} '
        f"neat and quiet. By the time they reached the door, even the hallway seemed lighter."
    )

    world.facts["outcome"] = "understood"
    world.facts["resolved"] = True
    return world


PLACES = {
    "records_room": Place("records_room", "records room", administrative=True, after_hours=True, quiet=True, tags={"administrative"}),
    "town_hall": Place("town_hall", "town hall", administrative=True, after_hours=True, quiet=True, tags={"administrative"}),
    "library_archive": Place("library_archive", "library archive", administrative=True, after_hours=True, quiet=True, tags={"administrative"}),
}

THINGS = {
    "stamp": GhostThing("stamp", "rubber stamp", "a rubber stamp", "clack", makes_surprise=True, makes_flashback=True, cautionary=True, tags={"administrative"}),
    "folder": GhostThing("folder", "missing folder", "a missing folder", "flutter", makes_surprise=True, makes_flashback=True, cautionary=True, tags={"administrative"}),
    "key": GhostThing("key", "iron key", "an iron key", "jingle", makes_surprise=True, makes_flashback=True, cautionary=True, tags={"administrative"}),
}

NARRATORS = ["Mina", "Theo", "Lena", "Owen", "June", "Iris"]
HELPERS = ["Ms. Bell", "Mr. Finch", "Aunt Cora", "Mr. Hale"]
GENDERS = {"girl": "girl", "boy": "boy", "woman": "woman", "man": "man"}


KNOWLEDGE = {
    "administrative": [("What does administrative mean?",
                        "Administrative means related to running a place, like keeping records, papers, and rules in order.")],
    "skeletal": [("What does skeletal mean?",
                  "Skeletal means having the look of bones or a very thin frame, like a skeleton.")],
    "surprise": [("What is a surprise?",
                  "A surprise is something you do not expect, so it can make you jump or gasp for a moment.")],
    "cautionary": [("What does cautionary mean?",
                    "Cautionary means it gives a careful warning so someone can avoid trouble.")],
    "flashback": [("What is a flashback?",
                   "A flashback is a memory scene that shows something from earlier and helps explain what is happening now.")],
    "ghost": [("What is a ghost in a story?",
               "A ghost in a story is often a spooky-looking figure, but it can also be a clue, a helper, or a misunderstanding.")],
    "retardo": [("Who is Retardo in this world?",
                 "Retardo is the skeletal office keeper who appears spooky at first, but turns out to be guarding an important file.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    thing = f["thing"]
    place = f["place"]
    return [
        f'Write a ghost story for a young child that includes the words "administrative", "skeletal", and "retardo".',
        f"Tell a cautionary story set in the {place.label} where {f['narrator'].id} meets a skeletal figure named Retardo and learns what the surprise means.",
        f"Write a spooky but gentle story with a flashback that explains why the missing {thing.label} belongs in the office."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    narrator = f["narrator"]
    helper = f["helper"]
    ghost = f["ghost"]
    thing = f["thing"]
    return [
        ("Who is the story about?",
         f"It is about {narrator.id}, {helper.id}, and {ghost.label}. The three of them are the ones who discover that the spooky room has a real reason for being strange."),
        ("Why did the office feel spooky at first?",
         f"It felt spooky because the room was quiet, the lights were low, and a skeletal figure suddenly appeared with {thing.phrase}. That surprise made the moment feel like a ghost story."),
        ("What did the flashback show?",
         f"The flashback showed that the office manager had said the room kept its records in order after hours. It also showed that Retardo was really guarding the missing {thing.label}, not trying to scare anyone."),
        ("How did the story end?",
         f"It ended safely and neatly. {ghost.label} put the {thing.label} back where it belonged, and the room stopped feeling haunted."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["thing"].tags) | {"administrative", "skeletal", "surprise", "cautionary", "flashback"}
    out: list[tuple[str, str]] = []
    for key in ["administrative", "skeletal", "surprise", "cautionary", "flashback", "ghost", "retardo"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
administrative(place(records_room)).
administrative(place(town_hall)).
administrative(place(library_archive)).
makes_surprise(stamp).
makes_surprise(folder).
makes_surprise(key).
makes_flashback(stamp).
makes_flashback(folder).
makes_flashback(key).
cautionary(stamp).
cautionary(folder).
cautionary(key).
valid(P, T) :- administrative(place(P)), makes_surprise(T), makes_flashback(T), cautionary(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in THINGS:
        lines.append(asp.fact("thing", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(resolve_params(argparse.Namespace(seed=0), random.Random(0)))
        _ = sample.story
        print("OK: smoke-tested normal generation.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc!r}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with an administrative, skeletal Retardo and a cautionary flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--narrator")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
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
    combos = valid_combos()
    if args.place and args.thing and (args.place, args.thing) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    if not combos:
        raise StoryError("(No valid story combinations available.)")
    place, thing = rng.choice(combos)
    narrator = args.narrator or rng.choice(NARRATORS)
    helper = args.helper or rng.choice(HELPERS)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["woman", "man"])
    return StoryParams(place, thing, narrator, helper, gender, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("records_room", "stamp", "Mina", "Ms. Bell", "girl", "woman", 0),
    StoryParams("town_hall", "folder", "Theo", "Mr. Finch", "boy", "man", 1),
    StoryParams("library_archive", "key", "June", "Aunt Cora", "girl", "woman", 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, thing) combos:")
        for p, t in asp_valid_combos():
            print(f"  {p:15} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.narrator_name}: {p.place} / {p.thing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
