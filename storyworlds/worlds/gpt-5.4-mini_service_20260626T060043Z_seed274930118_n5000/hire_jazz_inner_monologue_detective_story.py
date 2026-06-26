#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hire_jazz_inner_monologue_detective_story.py
===============================================================================================================

A small detective-story world built from the seed words "hire" and "jazz".

Premise:
A worried club owner hires a detective after a jazz horn disappears before a
late set. The detective follows clues, listens to an inner monologue, and
solves the case by understanding who wanted the horn and why.

The world is intentionally tiny:
- a few typed entities with physical meters and emotional memes,
- a short causal chain from setup to clue to reveal to resolution,
- a child-facing final story that reads like a complete detective tale.

This file is standalone and uses only the stdlib plus the shared result/ASP
helpers from storyworlds/.
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
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    jazz_level: str
    clue_look: str


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    can_hide: bool
    likes_jazz: bool
    motive: str


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    valuable: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    detective: str
    owner: str
    suspect: str
    missing: str
    seed: Optional[int] = None


PLACES = {
    "jazz_club": Place(
        id="jazz_club",
        label="the Blue Note Club",
        kind="club",
        jazz_level="soft",
        clue_look="glittering brass and a sticky stage",
    ),
    "back_room": Place(
        id="back_room",
        label="the back room",
        kind="room",
        jazz_level="quiet",
        clue_look="dusty shelves and a locked cabinet",
    ),
}

DETECTIVES = [
    ("Mara", "woman"),
    ("Ivy", "girl"),
    ("Noah", "boy"),
    ("June", "woman"),
]

OWNERS = [
    ("Mr. Vale", "man"),
    ("Ms. Reed", "woman"),
]

SUSPECTS = {
    "horn_player": Suspect(
        id="horn_player",
        type="man",
        label="the horn player",
        can_hide=True,
        likes_jazz=True,
        motive="he needed the horn for the late set",
    ),
    "stage_hand": Suspect(
        id="stage_hand",
        type="woman",
        label="the stage helper",
        can_hide=False,
        likes_jazz=False,
        motive="she was only moving chairs",
    ),
    "music_teacher": Suspect(
        id="music_teacher",
        type="woman",
        label="the music teacher",
        can_hide=True,
        likes_jazz=True,
        motive="she wanted to borrow the horn for practice",
    ),
}

MISSING = {
    "trumpet": MissingThing(
        id="trumpet",
        label="trumpet",
        phrase="a bright brass trumpet",
    ),
    "sheet_music": MissingThing(
        id="sheet_music",
        label="sheet music",
        phrase="the night's jazz sheet music",
    ),
}

TRAITS = ["sharp-eyed", "patient", "quiet", "careful", "clever"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for detective, _ in DETECTIVES:
            for owner, _ in OWNERS:
                for sus_id, sus in SUSPECTS.items():
                    for miss_id in MISSING:
                        if sus.likes_jazz and miss_id == "trumpet":
                            out.append((place, detective, owner, sus_id, miss_id))
                        elif miss_id == "sheet_music":
                            out.append((place, detective, owner, sus_id, miss_id))
    return out


def choose_rng(rng: random.Random, seq):
    return rng.choice(list(seq))


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type="woman" if params.detective in {"Mara", "June", "Ivy"} else "boy",
        label=params.detective,
        meters={"energy": 1.0, "attention": 1.0},
        memes={"curiosity": 1.0, "resolve": 1.0},
    ))
    owner_type = "woman" if params.owner.startswith("Ms.") else "man"
    owner = world.add(Entity(
        id="owner",
        kind="character",
        type=owner_type,
        label=params.owner,
        meters={"worry": 1.0},
        memes={"hope": 1.0},
    ))
    suspect_cfg = SUSPECTS[params.suspect]
    suspect = world.add(Entity(
        id="suspect",
        kind="character",
        type=suspect_cfg.type,
        label=suspect_cfg.label,
        meters={"nervous": 1.0 if suspect_cfg.can_hide else 0.0},
        memes={"jazz_love": 1.0 if suspect_cfg.likes_jazz else 0.0},
    ))
    missing_cfg = MISSING[params.missing]
    missing = world.add(Entity(
        id="missing",
        type="thing",
        label=missing_cfg.label,
        phrase=missing_cfg.phrase,
        owner=owner.id,
        carried_by=None,
        hidden=False,
        meters={"present": 0.0},
    ))

    world.facts.update(
        detective=detective,
        owner=owner,
        suspect=suspect,
        missing=missing,
        suspect_cfg=suspect_cfg,
        missing_cfg=missing_cfg,
        place=place,
    )

    # Setup.
    world.say(
        f"{detective.id} was a {choose_rng(random.Random(1), TRAITS)} detective who liked "
        f"quiet rooms and loud questions."
    )
    world.say(
        f"One evening, {owner.label} hired {detective.id} to find {missing.phrase} "
        f"before the jazz show started at {place.label}."
    )
    world.say(
        f"The club smelled like polish and old curtains, and the stage looked ready "
        f"for a song."
    )

    # Tension.
    world.para()
    world.say(
        f"{detective.id} stepped into {place.label} and studied the room."
    )
    world.say(
        f"In {place.clue_look}, {detective.id} noticed one clue: a thin trail of brass dust "
        f"near a half-open cabinet."
    )
    world.say(
        f"{detective.id}'s inner monologue whispered, \"If someone hid the horn, they must "
        f"care about the music more than the trick.\""
    )

    # Causal turn: suspicion and reasoning.
    if suspect_cfg.can_hide and missing.id == "trumpet":
        suspect.hidden = True
        suspect.meters["sneak"] = 1.0
        suspect.memes["guilt"] = 1.0
        world.say(
            f"The trail led to {suspect.label}, who stood by the curtain and kept glancing "
            f"at the stage."
        )
        world.say(
            f"{detective.id} thought, \"{suspect.label.capitalize()} looks nervous, but not cruel. "
            f"This feels like a borrowed-shine problem, not a mean theft.\""
        )
    else:
        world.say(
            f"The trail led past the curtain and toward the music stand, where the papers "
            f"had been touched by careful hands."
        )
        world.say(
            f"{detective.id} thought, \"This was hidden for a reason, and the reason must be "
            f"close to the jazz itself.\""
        )

    # Resolution.
    world.para()
    if missing.id == "trumpet":
        world.say(
            f"{detective.id} asked the right question, and {suspect.label} admitted the truth."
        )
        world.say(
            f"{suspect.label.capitalize()} had hidden the trumpet only so the band could save it "
            f"from a cracked stand until the last minute."
        )
        world.say(
            f"{owner.label} sighed, then smiled, because the horn was safe and the music could begin."
        )
        world.say(
            f"When the first jazz notes floated through the club, {detective.id} knew the case was "
            f"finished."
        )
    else:
        world.say(
            f"{detective.id} found the sheet music tucked under a clean cloth and gave it back "
            f"before anyone missed another beat."
        )
        world.say(
            f"{owner.label} thanked {detective.id}, and the band lined up onstage with steady hands."
        )
        world.say(
            f"When the jazz began, the room felt lighter, as if the night had remembered how to swing."
        )

    world.facts["resolved"] = True
    return world


def story_from_world(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for a young child that includes the words "hire" and "jazz".',
        f"Tell a gentle mystery where {f['owner'].label} hires {f['detective'].id} to find {f['missing'].label}.",
        f"Write a small detective tale with an inner monologue, a clue, and a jazz ending at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    owner = f["owner"]
    suspect = f["suspect"]
    missing = f["missing"]
    place = f["place"]
    suspect_cfg = f["suspect_cfg"]

    return [
        QAItem(
            question=f"Who did {owner.label} hire to solve the mystery at {place.label}?",
            answer=f"{owner.label} hired {detective.id}, a careful detective, to solve the mystery at {place.label}.",
        ),
        QAItem(
            question=f"What was missing from the club before the jazz show?",
            answer=f"{missing.phrase} was missing before the jazz show started.",
        ),
        QAItem(
            question=f"What clue did {detective.id} notice in the room?",
            answer=f"{detective.id} noticed a thin trail of brass dust near the cabinet.",
        ),
        QAItem(
            question=f"Why did {suspect.label} seem nervous?",
            answer=(
                f"{suspect.label.capitalize()} seemed nervous because {suspect_cfg.motive}, "
                f"and that made the hiding feel like a secret about music, not a mean theft."
            ),
        ),
        QAItem(
            question=f"What did {detective.id}'s inner monologue realize?",
            answer=(
                f"{detective.id}'s inner monologue realized that someone cared about the music "
                f"and was trying to protect it, so the clue needed a kind explanation."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jazz?",
            answer="Jazz is a kind of music with swinging rhythms and room for players to improvise.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a puzzle or mystery.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the silent talking a person does in their own mind while they think.",
        ),
        QAItem(
            question="Why might someone hire a detective?",
            answer="Someone might hire a detective when they need help finding something or understanding a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.hidden:
            bits.append("hidden=True")
        lines.append(f"{ent.id}: {ent.type} {ent.label} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this detective world expects a meaningful missing object and a jazz setting.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "jazz_club"
    if place not in PLACES:
        raise StoryError(explain_rejection())

    detective = args.detective or rng.choice([d for d, _ in DETECTIVES])
    owner = args.owner or rng.choice([o for o, _ in OWNERS])
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    missing = args.missing or rng.choice(list(MISSING))

    if missing == "trumpet" and not SUSPECTS[suspect].likes_jazz:
        raise StoryError("(No story: a trumpet mystery needs a jazz-loving suspect or the hidden reason would not fit.)")

    return StoryParams(
        place=place,
        detective=detective,
        owner=owner,
        suspect=suspect,
        missing=missing,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_from_world(world),
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


ASP_RULES = r"""
#show valid/4.

place(jazz_club).

detective(mara).
detective(ivy).
detective(noah).
detective(june).

owner(mr_vale).
owner(ms_reed).

suspect(horn_player).
suspect(stage_helper).
suspect(music_teacher).

missing(trumpet).
missing(sheet_music).

likes_jazz(horn_player).
likes_jazz(music_teacher).

mystery_ok(P,D,O,S,M) :- place(P), detective(D), owner(O), suspect(S), missing(M),
                         M = sheet_music.
mystery_ok(P,D,O,S,M) :- place(P), detective(D), owner(O), suspect(S), missing(M),
                         M = trumpet, likes_jazz(S).

valid(P,D,O,S,M) :- mystery_ok(P,D,O,S,M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for d, _ in DETECTIVES:
        lines.append(asp.fact("detective", d.lower()))
    for o, _ in OWNERS:
        lines.append(asp.fact("owner", o.lower().replace(" ", "_")))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for m in MISSING:
        lines.append(asp.fact("missing", m))
    for s in SUSPECTS.values():
        if s.likes_jazz:
            lines.append(asp.fact("likes_jazz", s.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, d.lower(), o.lower().replace(" ", "_"), s, m) for p, d, o, s, m in valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with hire, jazz, and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective", choices=[d for d, _ in DETECTIVES])
    ap.add_argument("--owner", choices=[o for o, _ in OWNERS])
    ap.add_argument("--suspect", choices=list(SUSPECTS))
    ap.add_argument("--missing", choices=list(MISSING))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/5."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("jazz_club", "Mara", "Ms. Reed", "horn_player", "trumpet"),
            StoryParams("jazz_club", "Ivy", "Mr. Vale", "music_teacher", "sheet_music"),
            StoryParams("back_room", "Noah", "Mr. Vale", "horn_player", "sheet_music"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
