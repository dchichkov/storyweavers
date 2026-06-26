#!/usr/bin/env python3
"""
A small heartwarming storyworld about a minister, an instrument, and a season.

Premise:
- A kind minister notices that the church's little instrument has gone missing
  right before the season celebration.
- The mystery is solved through careful dialogue, gentle clues, and a warm
  community search.
- The ending proves the change: the instrument is found, the season event can
  begin, and everyone feels closer.

This world is intentionally small and constraint-checked: the instrument,
setting, and season must fit together, and the mystery must be solvable by
talking to the right helper at the right place.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"minister", "man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    season: str
    ambience: str
    affords: set[str] = field(default_factory=set)


@dataclass
class InstrumentSpec:
    id: str
    label: str
    phrase: str
    sound: str
    carried_by: str
    easy_to_lose: bool = True


@dataclass
class MysterySpec:
    missing_item: str
    clue_location: str
    culprit_hint: str
    solved_by: str
    resolution: str


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "chapel": Setting(place="the little chapel", season="winter", ambience="snowlight", affords={"rehearsal", "search"}),
    "garden_room": Setting(place="the garden room", season="spring", ambience="fresh blossoms", affords={"rehearsal", "search"}),
    "hall": Setting(place="the community hall", season="autumn", ambience="leafy warmth", affords={"rehearsal", "search"}),
}

INSTRUMENTS = {
    "bell": InstrumentSpec(
        id="bell",
        label="handbell",
        phrase="a small silver handbell",
        sound="ding",
        carried_by="choir helper",
    ),
    "flute": InstrumentSpec(
        id="flute",
        label="flute",
        phrase="a smooth wooden flute",
        sound="toot",
        carried_by="young helper",
    ),
    "ukulele": InstrumentSpec(
        id="ukulele",
        label="ukulele",
        phrase="a tiny bright ukulele",
        sound="plunk",
        carried_by="music helper",
    ),
}

MYSTERIES = {
    "misplaced_case": MysterySpec(
        missing_item="case",
        clue_location="the piano bench",
        culprit_hint="the open windows let a breeze move it",
        solved_by="asking gentle questions",
        resolution="the instrument was tucked safely under a folded shawl",
    ),
    "borrowed_for_song": MysterySpec(
        missing_item="songbook",
        clue_location="the hymn shelf",
        culprit_hint="a child borrowed it for a practice song",
        solved_by="talking kindly to the child",
        resolution="the instrument had been set beside the songbook by the practice table",
    ),
    "wrapped_as_gift": MysterySpec(
        missing_item="wrapping paper",
        clue_location="the table by the tea tray",
        culprit_hint="a helper was wrapping the instrument as a surprise",
        solved_by="following the ribbon and asking who was being thoughtful",
        resolution="the instrument was waiting in a gift basket for the season celebration",
    ),
}

MINISTER_NAMES = ["Reverend June", "Minister Mara", "Pastor Eli", "Minister Noah", "Reverend Mira"]
HELPER_NAMES = ["Tessa", "Owen", "Mina", "Jonah", "Lena", "Iris"]
SEASON_NAMES = ["winter", "spring", "autumn"]

CURATED = [
    ("chapel", "bell", "misplaced_case"),
    ("hall", "ukulele", "borrowed_for_song"),
    ("garden_room", "flute", "wrapped_as_gift"),
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    instrument: str
    mystery: str
    minister_name: str
    helper_name: str
    season: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reasonable(setting: Setting, instrument: InstrumentSpec, mystery: MysterySpec) -> bool:
    if "search" not in setting.affords:
        return False
    if instrument.label == "handbell" and setting.season == "winter":
        return True
    if instrument.label == "flute" and setting.season == "spring":
        return True
    if instrument.label == "ukulele" and setting.season == "autumn":
        return True
    return True


def explain_rejection(setting: Setting, instrument: InstrumentSpec, mystery: MysterySpec) -> str:
    return (
        f"(No story: the {instrument.label} and the {setting.place} do not make a "
        f"clear season celebration mystery together.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def introduce(world: World, minister: Entity, instrument: Entity, helper: Entity) -> None:
    world.say(
        f"{minister.id} was a kind minister who loved quiet songs and warm smiles. "
        f"{minister.pronoun('possessive').capitalize()} church used {instrument.phrase} to welcome people, "
        f"and {helper.id} often helped with the music."
    )


def set_scene(world: World, minister: Entity, instrument: Entity) -> None:
    world.say(
        f"It was {world.setting.season} at {world.setting.place}, and {world.setting.ambience} filled the air. "
        f"The season celebration was almost ready, but the {instrument.label} was nowhere to be found."
    )
    minister.memes["worry"] = 1.0
    instrument.meters["missing"] = 1.0


def ask_and_listen(world: World, minister: Entity, helper: Entity, instrument: Entity, mystery: MysterySpec) -> None:
    world.say(
        f"{minister.id} took a slow breath and asked, \"Have you seen {instrument.pronoun('possessive')} {instrument.label}?\" "
        f"{helper.id} listened carefully and answered, \"I saw a clue near {mystery.clue_location}.\""
    )
    world.say(
        f"{minister.id} smiled with gratitude and asked one more gentle question. "
        f"That kind conversation made the mystery feel smaller right away."
    )
    helper.memes["trusted"] = 1.0
    minister.memes["hope"] = 1.0


def search_and_solve(world: World, minister: Entity, helper: Entity, instrument: Entity, mystery: MysterySpec) -> None:
    world.say(
        f"Together they walked to {mystery.clue_location}. {helper.id} pointed to the clue, "
        f"and {minister.id} followed it with patient eyes."
    )
    world.say(
        f"At last they found the answer: {mystery.resolution}. "
        f"{minister.id} laughed softly and said that {mystery.solved_by} had worked beautifully."
    )
    instrument.location = "with the minister"
    instrument.meters["missing"] = 0.0
    instrument.meters["found"] = 1.0
    minister.memes["relief"] = 1.0
    minister.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0


def ending(world: World, minister: Entity, helper: Entity, instrument: Entity) -> None:
    world.para()
    world.say(
        f"Before long, {minister.id} held the {instrument.label} up for the room to see. "
        f"The first clear note rang out, and the people nearby smiled at once."
    )
    world.say(
        f"The season celebration could begin, and {helper.id} stood beside {minister.id} with a happy, proud grin. "
        f"The missing thing had been found, and the whole place felt warmer than before."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    instrument = INSTRUMENTS[params.instrument]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    minister = world.add(Entity(
        id=params.minister_name,
        kind="character",
        type="minister",
        label="minister",
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="helper",
        label="helper",
    ))
    item = world.add(Entity(
        id=instrument.id,
        kind="thing",
        type="instrument",
        label=instrument.label,
        phrase=instrument.phrase,
        owner=minister.id,
        location="music shelf",
    ))

    world.facts.update(
        minister=minister,
        helper=helper,
        instrument=item,
        instrument_spec=instrument,
        mystery=mystery,
        setting=setting,
    )

    introduce(world, minister, item, helper)
    world.para()
    set_scene(world, minister, item)
    world.para()
    ask_and_listen(world, minister, helper, item, mystery)
    search_and_solve(world, minister, helper, item, mystery)
    ending(world, minister, helper, item)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about {f["minister"].id}, a {f["instrument"].label}, and a {f["setting"].season} celebration, where a small mystery is solved through dialogue.',
        f"Tell a gentle mystery story set at {f['setting'].place} in {f['setting'].season} about a minister and a missing {f['instrument'].label}.",
        f"Write a child-friendly story in which asking kind questions helps find a missing instrument before a season event.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    minister = f["minister"]
    helper = f["helper"]
    instrument = f["instrument"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was looking for the {instrument.label} in the story?",
            answer=f"{minister.id} was looking for the {instrument.label}, because the season celebration was about to begin.",
        ),
        QAItem(
            question=f"What helped solve the mystery?",
            answer=f"Kind dialogue helped solve the mystery. {minister.id} asked gentle questions, and {helper.id} answered with a clue.",
        ),
        QAItem(
            question=f"Where was the clue found?",
            answer=f"The clue was found near {mystery.clue_location} at {setting.place}.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The missing {instrument.label} was found, the celebration could begin, and everyone felt happy and warm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    instrument = f["instrument_spec"]
    setting = f["setting"]
    mystery = f["mystery"]
    return [
        QAItem(
            question="What is a minister?",
            answer="A minister is a person who helps lead worship, cares for people, and often speaks kindly to a community.",
        ),
        QAItem(
            question="What is an instrument?",
            answer=f"An instrument is something people use to make music, like a {instrument.label} or a flute.",
        ),
        QAItem(
            question=f"What is {setting.season} like?",
            answer=f"{setting.season.capitalize()} is a season of the year. In this story it feels like {setting.ambience}.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer=f"To solve a mystery means to find the answer to something confusing, usually by noticing clues and asking careful questions; here the answer came by {mystery.solved_by}.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the setting can host a search and the instrument/season pair fits.
reasonable(S, I, M) :- setting(S), instrument(I), mystery(M), search_capable(S).

% Minimal compatibility: each instrument has one preferred season.
fits_season(bell, winter).
fits_season(flute, spring).
fits_season(ukulele, autumn).

valid_story(S, I, M) :- reasonable(S, I, M), fits_season(I, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("season_of", sid, s.season))
        if "search" in s.affords:
            lines.append(asp.fact("search_capable", sid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (s, i, m)
        for s, setting in SETTINGS.items()
        for i, inst in INSTRUMENTS.items()
        for m, mys in MYSTERIES.items()
        if reasonable(setting, inst, mys)
    }
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming mystery storyworld about a minister and an instrument.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--minister-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--season", choices=SEASON_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for setting_id, setting in SETTINGS.items():
        if args.setting and setting_id != args.setting:
            continue
        for instrument_id, instrument in INSTRUMENTS.items():
            if args.instrument and instrument_id != args.instrument:
                continue
            for mystery_id, mystery in MYSTERIES.items():
                if args.mystery and mystery_id != args.mystery:
                    continue
                if not reasonable(setting, instrument, mystery):
                    continue
                choices.append((setting_id, instrument_id, mystery_id))
    if not choices:
        raise StoryError("No valid story matches the given options.")
    setting_id, instrument_id, mystery_id = rng.choice(choices)
    setting = SETTINGS[setting_id]
    season = args.season or setting.season
    if args.season and args.season != setting.season:
        raise StoryError("The requested season does not fit the chosen setting.")
    minister_name = args.minister_name or rng.choice(MINISTER_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != minister_name])
    return StoryParams(
        setting=setting_id,
        instrument=instrument_id,
        mystery=mystery_id,
        minister_name=minister_name,
        helper_name=helper_name,
        season=season,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} compatible stories:")
        for s, i, m in models:
            print(f"  {s}  {i}  {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting_id, instrument_id, mystery_id in CURATED:
            params = StoryParams(
                setting=setting_id,
                instrument=instrument_id,
                mystery=mystery_id,
                minister_name=MINISTER_NAMES[0],
                helper_name=HELPER_NAMES[0],
                season=SETTINGS[setting_id].season,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.minister_name}: {p.instrument} at {p.setting} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
