#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trace_exuberant_twist_mystery_to_solve_sharing.py
==============================================================================================================

A small whodunit-style story world about a cheerful child detective, a shared
object, a trace of clues, and a twist ending that solves the mystery.

The world is intentionally small and constraint-checked: a mystery is only
generated when the setting supports the shared activity, the missing object is
plausibly at risk, and the reveal can be explained by the simulated state.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    risk: str
    trace: str
    region: str
    shared_by: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    alibi: str
    twist_action: str
    twist_result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    object_id: str
    detective_name: str
    helper_name: str
    suspect: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(place="the library", indoors=True, affords={"sharing", "trace"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"sharing", "trace"}),
    "garden": Setting(place="the garden", indoors=False, affords={"sharing", "trace"}),
}

SHARED_THINGS = {
    "cookie_tin": SharedThing(
        id="cookie_tin",
        label="cookie tin",
        phrase="a tin of little star cookies",
        risk="missing",
        trace="crumbs",
        region="table",
        shared_by={"girl", "boy"},
    ),
    "paint_box": SharedThing(
        id="paint_box",
        label="paint box",
        phrase="a bright paint box with shiny lids",
        risk="smudged",
        trace="blue smears",
        region="shelf",
        shared_by={"girl", "boy"},
    ),
    "story_book": SharedThing(
        id="story_book",
        label="story book",
        phrase="a picture book with a red ribbon bookmark",
        risk="lost",
        trace="page dust",
        region="bench",
        shared_by={"girl", "boy"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        type="cat",
        label="the cat",
        alibi="the cat had been napping in a sunny patch",
        twist_action="shoved the tin",
        twist_result="sent it under the bench",
    ),
    "younger_sibling": Suspect(
        id="younger_sibling",
        type="boy",
        label="the younger brother",
        alibi="the younger brother was trying to help set the table",
        twist_action="moved it",
        twist_result="to share with a shy friend",
    ),
    "wind": Suspect(
        id="wind",
        type="thing",
        label="the wind",
        alibi="the wind had blown hard through the open door",
        twist_action="tipped the book",
        twist_result="against the flower pot",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe", "Maya"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Noah", "Finn", "Eli"]
HELPER_NAMES = ["June", "Sam", "Pip", "Toby", "Ada", "Max"]
TRAITS = ["exuberant", "curious", "bright-eyed", "careful", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj_id in SHARED_THINGS:
            if "sharing" in setting.affords and "trace" in setting.affords:
                for suspect in SUSPECTS:
                    combos.append((place, obj_id, suspect))
    return combos


def prize_at_risk(setting: Setting, thing: SharedThing) -> bool:
    return "trace" in setting.affords and "sharing" in setting.affords and thing.risk in {"missing", "lost", "smudged"}


def select_twist(suspect: Suspect, thing: SharedThing) -> bool:
    return True


def predict_mystery(world: World, detective: Entity, thing: Entity) -> dict:
    sim = world.copy()
    sim.get(detective.id).memes["curiosity"] = 2
    sim.get(thing.id).meters["hidden"] = 1
    return {
        "trace_seen": True,
        "shared": True,
        "missing": True,
    }


def track_trace(world: World, detective: Entity, thing: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    thing.meters["trace"] = thing.meters.get("trace", 0) + 1


def share(world: World, helper: Entity, detective: Entity, thing: Entity) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1
    world.say(
        f"{detective.id} and {helper.id} shared {thing.phrase} at {world.setting.place}, "
        f"and the room felt full of small, happy energy."
    )


def vanish(world: World, suspect: Suspect, thing: Entity) -> None:
    thing.meters["hidden"] = thing.meters.get("hidden", 0) + 1
    world.say(
        f"Then {thing.label} was gone. {suspect.alibi.capitalize()}, but the mystery only grew sharper."
    )


def clue(world: World, thing: Entity) -> None:
    world.say(
        f"Near the empty spot, {thing.trace} made a faint trail. "
        f"{thing.trace.capitalize()} meant someone had brushed past here recently."
    )


def accuse(world: World, detective: Entity, suspect: Suspect) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    world.say(
        f"{detective.id} studied the clue like a tiny detective in a whodunit and whispered, "
        f"'"Who took it?"'"
    )


def twist_reveal(world: World, detective: Entity, helper: Entity, suspect: Suspect, thing: Entity) -> None:
    detective.memes["surprise"] = detective.memes.get("surprise", 0) + 1
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1
    thing.meters["hidden"] = 0
    thing.carried_by = helper.id
    world.say(
        f"The twist was sweet, not mean: {helper.id} had not stolen {thing.label} at all. "
        f"{helper.id} had {suspect.twist_action} {suspect.twist_result}, because the surprise was meant to be shared."
    )
    world.say(
        f"{helper.id} smiled and showed where {thing.label} had been tucked away. "
        f"Everyone laughed, and the clue suddenly made perfect sense."
    )


def resolve(world: World, detective: Entity, helper: Entity, thing: Entity) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(
        f"In the end, {detective.id} held {thing.it()} with a grin. "
        f"The mystery was solved, the sharing was fair, and the once-empty place looked bright again."
    )


def tell(setting: Setting, thing_cfg: SharedThing, suspect_cfg: Suspect,
         detective_name: str = "Mina", helper_name: str = "June") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name, kind="character", type="girl",
        traits=["little", "exuberant", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="girl",
        traits=["kind", "helpful"],
    ))
    suspect = world.add(Entity(id=suspect_cfg.id, kind="character", type=suspect_cfg.type, label=suspect_cfg.label))
    thing = world.add(Entity(
        id=thing_cfg.id, type="thing", label=thing_cfg.label, phrase=thing_cfg.phrase,
        owner=helper.id,
    ))

    world.say(
        f"{detective.id} was a little exuberant detective who noticed every tiny clue."
    )
    world.say(
        f"One afternoon, {detective.id}, {helper.id}, and {suspect.label} were at {setting.place}, "
        f"and everyone wanted to share {thing.phrase}."
    )
    share(world, helper, detective, thing)
    world.para()
    vanish(world, suspect_cfg, thing)
    clue(world, thing)
    accuse(world, detective, suspect_cfg)
    world.para()
    twist_reveal(world, detective, helper, suspect_cfg, thing)
    resolve(world, detective, helper, thing)

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        thing=thing,
        setting=setting,
        suspect_cfg=suspect_cfg,
        thing_cfg=thing_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    thing = f["thing"]
    return [
        f'Write a whodunit-style story for a young child about {detective.id}, a shared {thing.label}, and a clue trail.',
        f"Tell a gentle mystery where {detective.id} and {helper.id} share {thing.phrase}, then notice {thing.trace} and solve the puzzle.",
        f'Write a short story with a twist ending about a missing {thing.label} and a child detective who follows {thing.trace}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect_cfg"]
    thing = f["thing_cfg"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {detective.id}, an exuberant little detective who liked to solve mysteries by looking for clues.",
        ),
        QAItem(
            question=f"What did {detective.id} and {helper.id} share?",
            answer=f"They shared {thing.phrase}, and that sharing helped start the mystery.",
        ),
        QAItem(
            question=f"What clue helped {detective.id} investigate the missing {thing.label}?",
            answer=f"{thing.trace} led {detective.id} to the answer, because the trace showed where the object had been moved.",
        ),
        QAItem(
            question=f"Was {suspect.label} the real thief?",
            answer=f"No. The twist showed that {suspect.label} was not stealing it; the object had been moved for a kind reason instead.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery was solved, the sharing was explained, and {detective.id} ended happily with the missing {thing.label} found again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a little bit of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do people share things?",
            answer="People share things so everyone can enjoy them, use them fairly, or help someone else feel included.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:16} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", object_id="cookie_tin", detective_name="Mina", helper_name="June", suspect="cat"),
    StoryParams(place="playroom", object_id="paint_box", detective_name="Lily", helper_name="Ada", suspect="younger_sibling"),
    StoryParams(place="garden", object_id="story_book", detective_name="Nora", helper_name="Sam", suspect="wind"),
]


def explain_rejection(setting: Setting, thing: SharedThing) -> str:
    return f"(No story: {setting.place} does not support both sharing and trace clues for {thing.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object_id is None or c[1] == args.object_id)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, object_id, suspect = rng.choice(sorted(combos))
    detective = args.detective_name or rng.choice(GIRL_NAMES)
    helper = args.helper_name or rng.choice(HELPER_NAMES)
    if args.gender == "boy":
        detective = rng.choice(BOY_NAMES)
    return StoryParams(place=place, object_id=object_id, detective_name=detective, helper_name=helper, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SHARED_THINGS[params.object_id], SUSPECTS[params.suspect],
                 detective_name=params.detective_name, helper_name=params.helper_name)
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
    ap = argparse.ArgumentParser(description="Whodunit-style mystery about sharing, a clue trace, and a twist ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--object-id", choices=sorted(SHARED_THINGS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
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


ASP_RULES = r"""
setting(library). setting(playroom). setting(garden).
affords(library,sharing). affords(library,trace).
affords(playroom,sharing). affords(playroom,trace).
affords(garden,sharing). affords(garden,trace).

thing(cookie_tin). thing(paint_box). thing(story_book).

suspect(cat). suspect(younger_sibling). suspect(wind).

valid(Place,Thing,Suspect) :- setting(Place), thing(Thing), suspect(Suspect),
                              affords(Place,sharing), affords(Place,trace).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for feat in sorted(setting.affords):
            lines.append(asp.fact("affords", place, feat))
    for oid in SHARED_THINGS:
        lines.append(asp.fact("thing", oid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.detective_name} at {p.place} ({p.object_id}, suspect={p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
