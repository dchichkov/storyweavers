#!/usr/bin/env python3
"""
storyworlds/worlds/bass_seize_laboratory_flashback_foreshadowing_detective_story.py
===================================================================================

A compact detective-story world with a laboratory, a missing bass, and two
narrative instruments: flashback and foreshadowing.

Seed premise:
- A bass is seized from a laboratory.
- A small detective must learn who took it and why.
- A flashback reveals a prior promise.
- Foreshadowing points to a clue before the reveal.

The simulation keeps one small, typed world model with physical meters and
emotional memes. Story text is generated from state transitions rather than a
fixed template.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    located_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "scientist"}
        male = {"boy", "man", "father", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the laboratory"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    location: str
    reveal_text: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    clue: str
    innocent_reason: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    scientist_name: str
    suspect: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "laboratory": Setting(place="the laboratory", indoor=True, affords={"search", "flashback", "foreshadow"}),
}

DETECTIVE_TYPES = ["girl", "boy"]
DETECTIVE_TRAITS = ["careful", "curious", "patient", "sharp-eyed", "quiet"]
DETECTIVE_NAMES = ["Mina", "Toby", "June", "Arlo", "Nia", "Pip", "Lina", "Eli"]

SCIENTIST_NAMES = ["Dr. Vale", "Dr. Quinn", "Dr. Mira", "Dr. Stone"]
SCIENTIST_TYPES = ["scientist"]

CLAUSES = [
    "the door was left half-open",
    "a wet footprint pointed toward the archive shelf",
    "a tiny scale shimmered under the lamp",
    "the locker lock had one scratch too many",
]

CLUES = {
    "scale": Clue(
        id="scale",
        text="a silver fish scale",
        location="the sink drain",
        reveal_text="The scale came from the bass's shiny side.",
    ),
    "receipt": Clue(
        id="receipt",
        text="a borrowing slip with the word BASS written in red ink",
        location="the clipboard rack",
        reveal_text="The slip showed the bass had been borrowed, not stolen.",
    ),
    "net": Clue(
        id="net",
        text="a little net with a damp corner",
        location="the storage hook",
        reveal_text="The damp net matched the specimen tank.",
    ),
}

SUSPECTS = {
    "assistant": Suspect(
        id="assistant",
        label="the lab assistant",
        type="scientist",
        motive="to move the bass into a safer tank",
        clue="receipt",
        innocent_reason="she had written the borrowing slip herself.",
    ),
    "janitor": Suspect(
        id="janitor",
        label="the janitor",
        type="man",
        motive="to clean the floor near the specimen shelf",
        clue="net",
        innocent_reason="he only found the wet net after the tank was already empty.",
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor child",
        type="girl",
        motive="to show the bass to a school project group",
        clue="scale",
        innocent_reason="she had never entered the lab at all.",
    ),
}

BASS = {
    "id": "bass",
    "label": "bass",
    "phrase": "the striped bass in the glass tank",
    "type": "fish",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective story world with a laboratory mystery, flashback, and foreshadowing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
    ap.add_argument("--scientist-name", choices=SCIENTIST_NAMES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("laboratory", clue) for clue in CLUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "laboratory":
        raise StoryError("This world only supports the laboratory setting.")
    if args.suspect and args.clue and SUSPECTS[args.suspect].clue != args.clue:
        raise StoryError("That suspect does not match the chosen clue.")
    place = "laboratory"
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    detective_type = args.detective_type or rng.choice(DETECTIVE_TYPES)
    scientist_name = args.scientist_name or rng.choice(SCIENTIST_NAMES)
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    clue = args.clue or SUSPECTS[suspect].clue
    return StoryParams(
        place=place,
        detective_name=detective_name,
        detective_type=detective_type,
        scientist_name=scientist_name,
        suspect=suspect,
        clue=clue,
    )


def _speak(w: World, who: Entity, text: str) -> None:
    w.say(f"{who.id} {text}")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        traits=["little", rng_trait()],
        meters={"alert": 0.0},
        memes={"curiosity": 1.0, "doubt": 0.0, "confidence": 0.0},
    ))
    scientist = world.add(Entity(
        id=params.scientist_name,
        kind="character",
        type="scientist",
        traits=["careful"],
        meters={"work": 0.0},
        memes={"worry": 1.0, "hope": 0.0},
    ))
    bass = world.add(Entity(
        id="bass",
        kind="thing",
        type="fish",
        label="bass",
        phrase=BASS["phrase"],
        owner=scientist.id,
        caretaker=scientist.id,
        held_by=None,
        located_in="tank",
        meters={"safeness": 1.0},
    ))
    clue = world.add(Entity(
        id=params.clue,
        kind="thing",
        type="clue",
        label=CLUES[params.clue].text,
        located_in=CLUES[params.clue].location,
        meters={"noticed": 0.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect,
        kind="character",
        type=SUSPECTS[params.suspect].type,
        label=SUSPECTS[params.suspect].label,
        memes={"suspicion": 0.0, "relief": 0.0},
    ))

    world.facts.update(detective=detective, scientist=scientist, bass=bass, clue=clue, suspect=suspect)

    world.say(f"In {world.setting.place}, {detective.id} was a little detective who noticed everything.")
    world.say(f"One morning, {scientist.id} gasped because {bass.label} was gone from the glass tank.")
    world.say(f"On the floor, {clue.label} waited near {clue.located_in}, almost like it wanted to be found.")
    world.say(f"{detective.id} felt their curiosity sharpen. In a detective story, a small clue can change everything.")

    world.para()
    world.say("Foreshadowing made the room feel quiet: the scratch on the locker, the open door, and the wet corner all pointed somewhere.")
    detective.meters["alert"] += 1.0
    detective.memes["confidence"] += 1.0
    scientist.memes["worry"] += 1.0

    world.para()
    world.say(f"{detective.id} searched the room and knelt by {clue.located_in}.")
    world.say(clue.label.capitalize() + " was real, and it was fresh.")
    world.say(f"That clue led {detective.id} to {suspect.label}, who stood by the archive shelf.")

    world.para()
    world.say("Then came a flashback.")
    world.say(f"Earlier that day, {scientist.id} had promised to move {bass.label} into a safer tank before the lights went off.")
    world.say(f"{suspect.label} had helped carry the net, which made the room seem guilty for a moment, but not everyone was hiding something.")

    world.para()
    world.say(f"{detective.id} asked careful questions, and {suspect.label} answered with a nervous smile.")
    world.say(f"The truth was simple: {SUSPECTS[params.suspect].motive}.")
    world.say(CLUES[params.clue].reveal_text)
    world.say(f"{suspect.label.capitalize()} was not a thief at all. {SUSPECTS[params.suspect].innocent_reason}")

    world.para()
    bass.held_by = scientist.id
    bass.located_in = "safer tank"
    bass.meters["safeness"] = 2.0
    scientist.memes["hope"] += 1.0
    scientist.memes["worry"] = 0.0
    detective.memes["confidence"] += 1.0
    world.say(f"By the end, {bass.label} was back in water, safe and shining.")
    world.say(f"{detective.id} smiled because the case was solved, and the laboratory felt calm again.")

    world.facts["resolved"] = True
    return world


def rng_trait() -> str:
    return random.choice(DETECTIVE_TRAITS)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    scientist = f["scientist"]
    suspect = f["suspect"]
    clue = f["clue"]
    return [
        f"Write a short detective story set in a laboratory where a bass goes missing and a clue leads to the truth.",
        f"Tell a child-friendly mystery about {detective.id}, {scientist.id}, and {suspect.label}, using a flashback and a foreshadowed clue.",
        f"Write a simple detective story that includes the words bass, seize, and laboratory, and ends with the bass safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    scientist = f["scientist"]
    suspect = f["suspect"]
    clue = f["clue"]
    bass = f["bass"]
    return [
        QAItem(
            question=f"Who solved the mystery in the laboratory?",
            answer=f"{detective.id} solved the mystery by following the clue and asking careful questions.",
        ),
        QAItem(
            question=f"What went missing from the laboratory tank?",
            answer=f"The {bass.label} went missing from the tank, which made {scientist.id} worry.",
        ),
        QAItem(
            question=f"Why did the clue matter?",
            answer=f"The clue mattered because it pointed toward {suspect.label} and helped explain what happened to the bass.",
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer=f"The flashback showed that {scientist.id} had promised to move the bass into a safer tank earlier that day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laboratory?",
            answer="A laboratory is a place where people do careful scientific work, like checking samples or keeping specimens safe.",
        ),
        QAItem(
            question="What is a bass?",
            answer="A bass is a kind of fish. It can live in water and may be kept in a tank for study.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something important before it happens.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them understand what happened and who was involved.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(detective; scientist; bass; clue; suspect).
kind(detective, character). kind(scientist, character). kind(suspect, character).
kind(bass, thing). kind(clue, thing).
place(laboratory).

missing(bass) :- held_by(bass, none).
foreshadowed(C) :- clue(C), located_in(C, _).
flashback(earlier_promise) :- promise_move_bass.

solved :- missing(bass), foreshadowed(C), clue(C), reveal(C).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "laboratory")]
    lines.append(asp.fact("bass"))
    lines.append(asp.fact("scientist", "scientist"))
    lines.append(asp.fact("detective", "detective"))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("located_in", cid, c.location))
        lines.append(asp.fact("reveal", cid))
    lines.append(asp.fact("promise_move_bass"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show solved/0.")
    model = asp.one_model(program)
    ok = any(sym.name == "solved" for sym in model)
    if ok:
        print("OK: ASP twin can derive solved/0 for the story world.")
        return 0
    print("MISMATCH: ASP twin did not derive solved/0.")
    return 1


def asp_valid_combos() -> list[tuple]:
    return [("laboratory", cid) for cid in CLUES]


def asp_valid_stories() -> list[tuple]:
    return [("laboratory", cid, sid) for cid in CLUES for sid in SUSPECTS]


def build_asp_output() -> str:
    lines = []
    for place, clue in asp_valid_combos():
        lines.append(f"{place} {clue}")
    return "\n".join(lines)


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "laboratory":
        raise StoryError("This story world only supports the laboratory setting.")
    if args.clue and args.suspect and SUSPECTS[args.suspect].clue != args.clue:
        raise StoryError("That suspect and clue do not belong together in this mystery.")
    return StoryParams(
        place="laboratory",
        detective_name=args.detective_name or rng.choice(DETECTIVE_NAMES),
        detective_type=args.detective_type or rng.choice(DETECTIVE_TYPES),
        scientist_name=args.scientist_name or rng.choice(SCIENTIST_NAMES),
        suspect=args.suspect or rng.choice(list(SUSPECTS)),
        clue=args.clue or rng.choice(list(CLUES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(build_asp_output())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for clue in CLUES:
            params = StoryParams(
                place="laboratory",
                detective_name=DETECTIVE_NAMES[0],
                detective_type="girl",
                scientist_name=SCIENTIST_NAMES[0],
                suspect=next(iter(SUSPECTS)),
                clue=clue,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params_from_args(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
