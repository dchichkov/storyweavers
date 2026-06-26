#!/usr/bin/env python3
"""
A standalone storyworld for a small ghost-story domain: a tenor haunted by
desperation, a flashback to an old stage night, and a quest to sing the lost
note that can calm a lonely spirit.

The world is intentionally small and constraint-checked: it models one singer,
one haunted place, one lost object, one ghost, one remembered flashback, and a
quest with a real turning point and ending image.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"man", "boy", "tenor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "soprano"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    echo: bool = True
    cold: bool = True
    dim: bool = True


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    hidden: bool = True
    found: bool = False


@dataclass
class Ghost:
    id: str
    label: str
    mood: str = "restless"
    soothed: bool = False
    bound_to: str = "the old stage"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.relics: dict[str, Relic] = {}
        self.ghost: Optional[Ghost] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.flashback_seen: bool = False
        self.quest_started: bool = False
        self.quest_finished: bool = False
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_relic(self, rel: Relic) -> Relic:
        self.relics[rel.id] = rel
        return rel

    def set_ghost(self, ghost: Ghost) -> Ghost:
        self.ghost = ghost
        return ghost

    def character(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def log(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    tenor_name: str
    tenor_trait: str
    relic: str
    ghost_name: str
    seed: Optional[int] = None


PLACES = {
    "old_theater": Place(id="old_theater", label="the old theater", echo=True, cold=True, dim=True),
    "river_stage": Place(id="river_stage", label="the river stage", echo=True, cold=True, dim=True),
    "moon_attic": Place(id="moon_attic", label="the moonlit attic", echo=False, cold=True, dim=True),
}

TENOR_NAMES = ["Eli", "Noah", "Theo", "Leon", "Milo", "Ari"]
TENOR_TRAITS = ["brave", "gentle", "nervous", "hopeful", "steady"]
GHOST_NAMES = ["Mrs. Vale", "The White Lady", "Old Bram", "Miss Echo"]
RELICS = {
    "missing_note": Relic(id="missing_note", label="missing note", phrase="one lost note from the song", hidden=True),
    "silver_key": Relic(id="silver_key", label="silver key", phrase="a silver key that opens the choir room", hidden=True),
    "lantern": Relic(id="lantern", label="lantern", phrase="a lantern that can light the dark aisle", hidden=True),
}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, tenor: Entity, relic: Relic) -> None:
    world.say(
        f"{tenor.id} was a {tenor.meters.get('age_word', 'young')} tenor who sang carefully because "
        f"{tenor.memes.get('desperation', 0) > 0 and 'desperation already lived in his chest' or 'his voice was soft and clear'}."
    )
    world.say(
        f"He loved the old {world.place.label.split('the ', 1)[-1]} because its long hall kept every song like a secret."
    )
    world.say(
        f"But he had lost {relic.phrase}, and without it the last line of his song would not feel whole."
    )


def flashback(world: World, tenor: Entity, ghost: Ghost, relic: Relic) -> None:
    world.flashback_seen = True
    tenor.memes["memory"] = tenor.memes.get("memory", 0) + 1
    world.say(
        f"Then {tenor.id} remembered a night long ago, when the lamps were bright and {ghost.label} stood by the curtain."
    )
    world.say(
        f"In that flashback, {ghost.label} had hummed the same tune and pointed toward the dark stair where {relic.label} was last heard."
    )
    world.say(
        f"{tenor.id} had been too young to understand, but now the memory shone like a candle in fog."
    )


def begin_quest(world: World, tenor: Entity, relic: Relic) -> None:
    world.quest_started = True
    tenor.memes["desperation"] = tenor.memes.get("desperation", 0) + 1
    world.say(
        f"So {tenor.id} began a quiet quest through the empty theater, following the creak of boards and the whisper of dust."
    )
    world.say(
        f"He searched under the velvet seats, behind the painted backdrop, and along the cold brass rail."
    )
    world.say(
        f"Every step felt small, but the hope of finding {relic.label} kept him moving."
    )


def encounter_ghost(world: World, tenor: Entity, ghost: Ghost) -> None:
    if world.ghost is None:
        return
    tenor.memes["fear"] = tenor.memes.get("fear", 0) + 1
    world.say(
        f"At the far end of the hall, {ghost.label} appeared like a pale cloud in the dark."
    )
    world.say(
        f"{tenor.id} stopped at once, but the ghost only listened, as if waiting for an old promise to be kept."
    )


def find_relic(world: World, tenor: Entity, relic: Relic, ghost: Ghost) -> None:
    relic.hidden = False
    relic.found = True
    tenor.meters["found"] = tenor.meters.get("found", 0) + 1
    world.say(
        f"Near the broken piano, {tenor.id} found {relic.phrase}, tucked beneath a loose board."
    )
    world.say(
        f"The note was dusty, but it was still there, and the air around it felt less cold."
    )


def resolve(world: World, tenor: Entity, relic: Relic, ghost: Ghost) -> None:
    world.quest_finished = True
    tenor.memes["desperation"] = max(0, tenor.memes.get("desperation", 0) - 1)
    ghost.soothed = True
    ghost.mood = "soft"
    world.say(
        f"{tenor.id} lifted his chin and sang {relic.label} into the empty hall."
    )
    world.say(
        f"The sound climbed the walls, touched the rafters, and reached {ghost.label} like warm moonlight."
    )
    world.say(
        f"Then the ghost smiled, faded like mist, and the theater at last felt like a place that could rest."
    )


def ending(world: World, tenor: Entity, relic: Relic) -> None:
    world.say(
        f"By the end, {tenor.id} stood alone on the stage, and his song was whole again."
    )
    world.say(
        f"The lost {relic.label} was no longer a secret in the dark; it was a bright note in his voice, and the empty seats seemed to listen kindly."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    tenor = world.add(Entity(
        id=params.tenor_name,
        kind="character",
        type="tenor",
        label="tenor",
        meters={"age_word": "young"},
        memes={"desperation": 1, "hope": 1},
    ))
    ghost = world.set_ghost(Ghost(id="ghost", label=params.ghost_name))
    relic = world.add_relic(dataclasses.replace(RELICS[params.relic]))
    tenor.memes["desperation"] += 1

    intro(world, tenor, relic)
    world.para()
    flashback(world, tenor, ghost, relic)
    world.para()
    begin_quest(world, tenor, relic)
    encounter_ghost(world, tenor, ghost)
    find_relic(world, tenor, relic, ghost)
    world.para()
    resolve(world, tenor, relic, ghost)
    ending(world, tenor, relic)

    world.facts.update(
        tenor=tenor,
        ghost=ghost,
        relic=relic,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tenor: Entity = f["tenor"]
    relic: Relic = f["relic"]
    place: Place = f["place"]
    ghost: Ghost = f["ghost"]
    return [
        f"Write a short ghost story for children about {tenor.id}, a tenor who feels desperation in {place.label}.",
        f"Tell a story with a flashback and a quest where {tenor.id} searches for {relic.label} and meets {ghost.label}.",
        f"Write a gentle haunted-theater tale where a singer remembers an old night and finds what was lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tenor: Entity = f["tenor"]
    ghost: Ghost = f["ghost"]
    relic: Relic = f["relic"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {tenor.id}, a young tenor who is trying to be brave in {place.label}.",
        ),
        QAItem(
            question=f"What did {tenor.id} want to find?",
            answer=f"He wanted to find {relic.phrase} so his song could feel whole again.",
        ),
        QAItem(
            question=f"Why did the story have a flashback?",
            answer=f"The flashback showed an old night with {ghost.label}, which helped {tenor.id} remember where to look.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The lost {relic.label} was found, the ghost was soothed, and {tenor.id} could sing without the same desperation.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tenor?",
            answer="A tenor is a singing voice that is usually high for an adult man, often used in songs and choirs.",
        ),
        QAItem(
            question="What is desperation?",
            answer="Desperation is a very strong feeling of needing something badly and being worried it may not happen.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to an earlier time to explain something important.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, usually with a goal that the hero wants to reach.",
        ),
        QAItem(
            question="Why are ghost stories often dark and quiet?",
            answer="Ghost stories are often dark and quiet because that mood makes the strange little sounds and shadows feel more spooky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.label}")
    lines.append(f"flashback_seen={world.flashback_seen}")
    lines.append(f"quest_started={world.quest_started}")
    lines.append(f"quest_finished={world.quest_finished}")
    if world.ghost:
        lines.append(f"ghost={world.ghost.label} mood={world.ghost.mood} soothed={world.ghost.soothed}")
    for e in world.entities.values():
        lines.append(f"entity {e.id}: meters={e.meters} memes={e.memes}")
    for r in world.relics.values():
        lines.append(f"relic {r.id}: hidden={r.hidden} found={r.found}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(old_theater).
place(river_stage).
place(moon_attic).

tenor_name(eli).
tenor_name(noah).
tenor_name(theo).
tenor_name(leon).
tenor_name(milo).
tenor_name(ari).

relic(missing_note).
relic(silver_key).
relic(lantern).

ghost_name(mrs_vale).
ghost_name(the_white_lady).
ghost_name(old_bram).
ghost_name(miss_echo).

% A story is valid when it has a place, a tenor, a relic, and a ghost.
valid_story(P, N, R, G) :- place(P), tenor_name(N), relic(R), ghost_name(G).

#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for n in TENOR_NAMES:
        lines.append(asp.fact("tenor_name", n.lower()))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for g in GHOST_NAMES:
        token = g.lower().replace(" ", "_").replace(".", "")
        lines.append(asp.fact("ghost_name", token))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_count = len(PLACES) * len(TENOR_NAMES) * len(RELICS) * len(GHOST_NAMES)
    asp_count = len(asp_valid_stories())
    if asp_count == python_count:
        print(f"OK: ASP gate matches Python registry count ({asp_count} stories).")
        return 0
    print(f"MISMATCH: ASP={asp_count}, Python={python_count}")
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: tenor, desperation, flashback, quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tenor-name", choices=TENOR_NAMES)
    ap.add_argument("--tenor-trait", choices=TENOR_TRAITS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
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
    tenor_name = args.tenor_name or rng.choice(TENOR_NAMES)
    tenor_trait = args.tenor_trait or rng.choice(TENOR_TRAITS)
    relic = args.relic or rng.choice(list(RELICS))
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(
        place=place,
        tenor_name=tenor_name,
        tenor_trait=tenor_trait,
        relic=relic,
        ghost_name=ghost_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="old_theater", tenor_name="Eli", tenor_trait="brave", relic="missing_note", ghost_name="Mrs. Vale"),
    StoryParams(place="river_stage", tenor_name="Noah", tenor_trait="hopeful", relic="lantern", ghost_name="The White Lady"),
    StoryParams(place="moon_attic", tenor_name="Theo", tenor_trait="gentle", relic="silver_key", ghost_name="Old Bram"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.tenor_name} in {p.place} with {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
