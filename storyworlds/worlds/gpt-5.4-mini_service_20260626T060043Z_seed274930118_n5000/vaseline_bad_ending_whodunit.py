#!/usr/bin/env python3
"""
storyworlds/worlds/vaseline_bad_ending_whodunit.py
===================================================

A small whodunit-style storyworld with a bad ending.

Premise:
- A child detective notices something strange in a small household setting.
- A jar of vaseline becomes the central clue.
- The story follows a careful investigation with suspects, clues, and a reveal.
- The ending is deliberately bad: the detective makes the wrong call, and the
  real problem remains.

This script is self-contained and fits the Storyweavers storyworld contract.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched: bool = False
    sticky: bool = False
    suspicious: bool = False
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
    detail: str
    clue_spot: str
    indoors: bool = True


@dataclass
class SuspectProfile:
    id: str
    type: str
    label: str
    alibi: str
    access: set[str] = field(default_factory=set)
    likely: float = 0.0


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_type: str
    sidekick_name: str
    sidekick_type: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bathroom": Setting(
        place="the little bathroom",
        detail="The sink was bright, and the tiled floor showed every small mark.",
        clue_spot="the doorknob",
        indoors=True,
    ),
    "hallway": Setting(
        place="the hallway",
        detail="The hallway was narrow, with one lamp and a row of shoes by the wall.",
        clue_spot="the front latch",
        indoors=True,
    ),
    "nursery": Setting(
        place="the nursery",
        detail="The nursery was quiet, with blocks on the rug and a toy shelf nearby.",
        clue_spot="the shelf edge",
        indoors=True,
    ),
}

SUSPECTS = {
    "mom": SuspectProfile(
        id="Mom",
        type="mother",
        label="Mom",
        alibi="She had been folding laundry in the next room.",
        access={"bathroom", "hallway", "nursery"},
        likely=0.2,
    ),
    "dad": SuspectProfile(
        id="Dad",
        type="father",
        label="Dad",
        alibi="He had been looking for a missing flashlight.",
        access={"hallway", "nursery"},
        likely=0.2,
    ),
    "sibling": SuspectProfile(
        id="Milo",
        type="boy",
        label="Milo",
        alibi="He said he was building a tower, but the blocks were still wobbly.",
        access={"bathroom", "hallway", "nursery"},
        likely=0.5,
    ),
    "cat": SuspectProfile(
        id="Cat",
        type="thing",
        label="the cat",
        alibi="The cat was asleep on a warm chair.",
        access={"hallway", "nursery"},
        likely=0.1,
    ),
}

DETECTIVE_NAMES = ["Nina", "Eli", "June", "Owen", "Maya", "Theo"]
SIDEKICK_NAMES = ["Pip", "Bee", "Lulu", "Max", "Dot", "Finn"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

class MysteryWorld(World):
    pass


def clue_text(suspect: Entity, setting: Setting) -> str:
    if suspect.id == "Milo":
        return f"tiny fingerprints near {setting.clue_spot}"
    if suspect.id == "Mom":
        return f"a clean folded cloth left beside {setting.clue_spot}"
    if suspect.id == "Dad":
        return f"a dropped screwdriver near {setting.clue_spot}"
    return f"a strand of fur caught near {setting.clue_spot}"


def build_world(params: StoryParams) -> MysteryWorld:
    setting = SETTINGS[params.setting]
    world = MysteryWorld(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        meters={"curiosity": 1.0, "unease": 0.0},
        memes={"doubt": 0.0, "focus": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type=params.sidekick_type,
        label=params.sidekick_name,
        meters={"curiosity": 0.6},
        memes={"trust": 1.0},
    ))
    suspect_profile = SUSPECTS[params.suspect]
    suspect = world.add(Entity(
        id=suspect_profile.id,
        kind="character",
        type=suspect_profile.type,
        label=suspect_profile.label,
        meters={"calm": 1.0},
        memes={"suspicion": suspect_profile.likely},
    ))
    jar = world.add(Entity(
        id="vaseline",
        kind="thing",
        type="jar",
        label="a jar of vaseline",
        phrase="a jar of vaseline with a blue lid",
        owner=suspect.id,
        sticky=True,
        suspicious=True,
        meters={"smudged": 0.0},
    ))
    hidden_note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="a tiny note",
        phrase="a tiny note under the mat",
        suspicious=False,
        meters={"seen": 0.0},
    ))

    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        suspect=suspect,
        suspect_profile=suspect_profile,
        jar=jar,
        note=hidden_note,
    )

    # Act 1: the strange clue.
    world.say(
        f"{detective.id} was a little detective who loved solving small mysteries."
    )
    world.say(
        f"One quiet afternoon, {detective.id} and {sidekick.id} went into {setting.place}."
    )
    world.say(setting.detail)
    world.say(
        f"Then {detective.id} spotted {setting.clue_spot}: {clue_text(suspect, setting)}."
    )
    world.say(
        f"Right beside it sat {jar.phrase}, and the blue lid looked as if someone had opened it in a hurry."
    )

    # Act 2: the search.
    world.para()
    detective.meters["curiosity"] += 1.0
    detective.memes["focus"] += 1.0
    world.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes and whispered, "
        f'"Who touched the vaseline?"'
    )
    world.say(
        f"{sidekick.id} checked the floor first and found a faint sticky shine leading toward the door."
    )
    world.say(
        f"They asked {suspect.label}, and {suspect.label} gave {suspect_profile.alibi.lower()}"
    )

    # A wrong deduction on purpose.
    world.para()
    suspect.memes["suspicion"] += 1.0
    detective.memes["doubt"] += 1.0
    world.say(
        f"{detective.id} noticed the {clue_text(suspect, setting).split(' ', 1)[0]} and made a quick guess."
    )
    world.say(
        f'"It must have been {suspect.label}," {detective.id} said.'
    )
    world.say(
        f"But {sidekick.id} found a better clue: a tiny note under the mat that said, "
        f'"For slipping boots."'
    )

    # Bad ending: the detective ignores the real clue and the mystery stays messy.
    world.para()
    world.say(
        f"By the time {detective.id} looked again, the jar of vaseline was gone from the shelf."
    )
    world.say(
        f"{suspect.label} had already walked away, and nobody knew who moved it."
    )
    world.say(
        f"{detective.id} put away the notebook and felt the case slip right out of {detective.pronoun('possessive')} hands."
    )
    world.say(
        f"At the end, {setting.clue_spot} was still sticky, the note was still unread, and the real whodunit was never solved."
    )

    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        suspect=suspect,
        jar=jar,
        setting=setting,
        resolved=False,
        wrong_guess=suspect.id,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(setting_key: str, suspect_key: str) -> bool:
    if setting_key not in SETTINGS or suspect_key not in SUSPECTS:
        return False
    setting = SETTINGS[setting_key]
    suspect = SUSPECTS[suspect_key]
    return setting.place in {"the little bathroom", "the hallway", "the nursery"} and setting_key in suspect.access


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: MysteryWorld) -> list[str]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    setting = f["setting"]
    return [
        f'Write a child-friendly whodunit set in {setting.place} that includes vaseline.',
        f"Tell a short mystery where {detective.id} investigates a sticky clue and wrongly blames {suspect.label}.",
        f'Write a bad-ending detective story with a jar of vaseline, a false guess, and one last clue left behind.',
    ]


def story_qa(world: MysteryWorld) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    sidekick = f["sidekick"]
    setting = f["setting"]
    jar = f["jar"]

    return [
        QAItem(
            question=f"Where did {detective.id} find the sticky clue?",
            answer=f"{detective.id} found it in {setting.place}, near {setting.clue_spot}.",
        ),
        QAItem(
            question=f"What did {detective.id} think the clue meant?",
            answer=f"{detective.id} thought {suspect.label} had touched the vaseline, but that guess was wrong.",
        ),
        QAItem(
            question=f"Who found the better clue under the mat?",
            answer=f"{sidekick.id} found the better clue: a tiny note that pointed to slipping boots.",
        ),
        QAItem(
            question=f"What was the important object in the mystery?",
            answer=f"The important object was {jar.phrase}.",
        ),
        QAItem(
            question="Did the detective solve the mystery in the end?",
            answer="No. The detective guessed wrong, and the real mystery was still unsolved at the end.",
        ),
    ]


def world_qa(world: MysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is vaseline used for?",
            answer="Vaseline is a soft greasy jelly people put on skin to help it feel smooth and protected.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a little piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to solve a problem or mystery.",
        ),
    ]


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
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(S, X) :- setting(S), suspect(X), allowed(X, S).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for key, sp in SUSPECTS.items():
        lines.append(asp.fact("suspect", key))
        for place in sorted(sp.access):
            lines.append(asp.fact("allowed", key, place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((s, x) for s in SETTINGS for x in SUSPECTS if valid_story(s, x))
    cl = asp_valid_stories()
    if py == cl:
        print(f"OK: clingo gate matches valid_story() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# Params / generation / emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small vaseline whodunit with a bad ending.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    if not valid_story(setting, suspect):
        raise StoryError("No reasonable whodunit fits that setting and suspect combination.")
    detective_name = args.name or rng.choice(DETECTIVE_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    detective_type = rng.choice(["girl", "boy"])
    sidekick_type = "girl" if detective_type == "boy" else "boy"
    return StoryParams(
        setting=setting,
        detective_name=detective_name,
        detective_type=detective_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        suspect=suspect,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: MysteryWorld) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.sticky:
            bits.append("sticky=True")
        if ent.suspicious:
            bits.append("suspicious=True")
        lines.append(f"  {ent.id}: {ent.kind}/{ent.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="bathroom", detective_name="Nina", detective_type="girl", sidekick_name="Pip", sidekick_type="boy", suspect="sibling"),
    StoryParams(setting="hallway", detective_name="Theo", detective_type="boy", sidekick_name="Dot", sidekick_type="girl", suspect="mom"),
    StoryParams(setting="nursery", detective_name="Maya", detective_type="girl", sidekick_name="Finn", sidekick_type="boy", suspect="cat"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid_stories()
        print(f"{len(items)} valid story combinations:")
        for s, x in items:
            print(f"  {s:8} {x}")
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
            header = f"### {p.detective_name} in {p.setting} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
