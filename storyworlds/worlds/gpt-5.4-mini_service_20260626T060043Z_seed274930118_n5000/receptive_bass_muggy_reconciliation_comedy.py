#!/usr/bin/env python3
"""
storyworlds/worlds/receptive_bass_muggy_reconciliation_comedy.py
===============================================================

A small storyworld about a muggy day, a bass guitar, and a silly misunderstanding
that ends in reconciliation.

Seeded premise:
---
A patient kid loves playing bass in a little neighborhood music nook. On a muggy
afternoon, the bass sounds extra boomy, and the kid's friend thinks the music is
too loud for their snack table. A small argument starts, but both children are
receptive to a compromise: the bass goes softer, the snacks move to the porch,
and everyone laughs at how serious the argument sounded.

Narrative shape:
---
setup -> a bass-loving child in a muggy place
tension -> a friend gets bothered by the booming sound and sticky air
turn -> both children listen and switch to a better arrangement
resolution -> reconciliation, shared music, and a comic ending image
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the backyard porch"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    volume: str
    can_turn_down: bool = True


@dataclass
class Fix:
    id: str
    label: str
    action: str
    result: str


@dataclass
class StoryParams:
    place: str
    activity: str
    instrument: str
    name: str
    friend_name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "porch": Setting(place="the backyard porch", indoor=False, affords={"practice"}),
    "garage": Setting(place="the garage", indoor=True, affords={"practice"}),
    "bandroom": Setting(place="the tiny band room", indoor=True, affords={"practice"}),
}

ACTIVITIES = {
    "practice": Activity(
        id="practice",
        verb="play music",
        gerund="playing music",
        rush="start a giant jam session",
        mess="boomy",
        soil="too loud and goofy",
        keyword="practice",
        tags={"music", "sound", "comedy"},
    ),
    "jam": Activity(
        id="jam",
        verb="jam together",
        gerund="jamming together",
        rush="launch into a noisy tune",
        mess="boomy",
        soil="extra boomy",
        keyword="jam",
        tags={"music", "sound", "comedy"},
    ),
}

INSTRUMENTS = {
    "bass": Instrument(
        id="bass",
        label="bass guitar",
        phrase="a shiny bass guitar",
        sound="boom-bom, boom-bom",
        volume="low and round",
        can_turn_down=True,
    ),
    "drum": Instrument(
        id="drum",
        label="drum",
        phrase="a little drum",
        sound="bap-bap-bap",
        volume="loud and bouncy",
        can_turn_down=False,
    ),
}

FIXES = {
    "soften": Fix(
        id="soften",
        label="turning the amp down",
        action="turn the amp down",
        result="the music got soft enough for talking and snacking",
    ),
    "porch": Fix(
        id="porch",
        label="moving the snacks to the porch",
        action="move the snacks to the porch",
        result="the snacks had room and the music could still wiggle along",
    ),
    "pause": Fix(
        id="pause",
        label="taking a tiny break",
        action="take a tiny break",
        result="everyone could laugh before trying again",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ava", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Noah", "Theo", "Ben", "Sam"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def noisy_enough(activity: Activity, instrument: Instrument) -> bool:
    return activity.mess == "boomy" and instrument.id in {"bass", "drum"}


def choose_fix(activity: Activity, instrument: Instrument) -> Optional[Fix]:
    if instrument.id == "bass" and activity.id in {"practice", "jam"}:
        return FIXES["soften"]
    return None


def tell(setting: Setting, activity: Activity, instrument: Instrument,
         hero_name: str, friend_name: str, gender: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        meters={"joy": 1.0},
        memes={"receptive": 1.0, "love_music": 1.0},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type="child",
        meters={"patience": 1.0},
        memes={"curious": 1.0},
    ))
    bass = world.add(Entity(
        id=instrument.id,
        type="instrument",
        label=instrument.label,
        phrase=instrument.phrase,
        owner=hero.id,
    ))

    # Setup
    world.say(
        f"{hero.id} was a receptive kid who loved a {bass.label} and the way it went "
        f"{instrument.sound} when nobody was rushing them."
    )
    world.say(
        f"{hero.id} and {friend.id} often met at {setting.place}, where the air could get "
        f"muggy and the jokes got sillier the longer they stayed."
    )

    # Tension
    world.para()
    world.say(
        f"One muggy afternoon, {hero.id} started to {activity.verb} with the {bass.label}, "
        f"and the notes felt {instrument.volume} in the sticky air."
    )
    if noisy_enough(activity, instrument):
        hero.meters["boomy"] = hero.meters.get("boomy", 0.0) + 1.0
        friend.memes["grumpy"] = friend.memes.get("grumpy", 0.0) + 1.0
        world.say(
            f"{friend.id} blinked and said the music was so boomy it made the snack plate "
            f"vibrate like a tiny joke drum."
        )
        world.say(
            f"{hero.id} looked surprised, because {hero.pronoun('subject')} had not meant to "
            f"boss around the whole porch."
        )

    # Turn
    world.para()
    fix = choose_fix(activity, instrument)
    if not fix:
        raise StoryError("This world only makes sense when the bass can be softened into a compromise.")

    world.say(
        f"{hero.id} listened, then nodded. {hero.pronoun('subject').capitalize()} was receptive "
        f"to the complaint and said they could try {fix.action}."
    )
    world.say(
        f"{friend.id} stopped frowning and suggested they also {FIXES['porch'].action}, "
        f"because the lemons on the table were not ready for a concert."
    )

    # Resolution
    world.para()
    hero.memes["reconciliation"] = 1.0
    friend.memes["reconciliation"] = 1.0
    hero.meters["boomy"] = 0.0
    friend.memes["grumpy"] = 0.0
    world.say(
        f"They did it together, and {fix.result}. Then {hero.id} played again, softer now, "
        f"with {friend.id} tapping a spoon on a cup like a very serious rhythm coach."
    )
    world.say(
        f"By the end, they were both laughing at how a bass guitar had almost started an argument "
        f"with a plate of crackers, and the muggy afternoon felt friendly again."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        instrument=instrument,
        activity=activity,
        setting=setting,
        fix=fix,
    )
    return world


# ---------------------------------------------------------------------------
# Registries for generation and QA
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for inst_id in INSTRUMENTS:
                if noisy_enough(ACTIVITIES[act], INSTRUMENTS[inst_id]):
                    out.append((place, inst_id))
    return out


@dataclass
class StoryWorldTrace:
    world: World


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    inst = f["instrument"]
    return [
        f'Write a short comedy story for a young child about a muggy day, a {inst.label}, and a happy reconciliation.',
        f"Tell a funny story where {hero.id} wants to {act.verb} with a {inst.label}, but {friend.id} has a complaint and they fix it together.",
        f'Write a gentle story using the words "receptive", "bass", and "muggy" that ends with the children laughing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    inst = f["instrument"]
    act = f["activity"]
    fix = f["fix"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What kind of kid was {hero.id}?",
            answer=f"{hero.id} was a receptive kid who loved music and was willing to listen when {friend.id} spoke up.",
        ),
        QAItem(
            question=f"What did the {inst.label} sound like when {hero.id} started to {act.verb}?",
            answer=f"It went {inst.sound}, and in the muggy air it felt extra boomy and funny.",
        ),
        QAItem(
            question=f"Why did {friend.id} complain at {setting.place}?",
            answer=f"{friend.id} complained because the bass was so boomy that even the snack plate seemed to rattle.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {fix.label} and also moved the snacks to the porch, which made the whole scene calmer and sillier in a good way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with both children laughing, playing more softly, and feeling friends again after their reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bass guitar?",
            answer="A bass guitar is a string instrument that makes low notes that support the music underneath the melody.",
        ),
        QAItem(
            question="What does muggy mean?",
            answer="Muggy means the air feels hot, damp, and sticky, like it wants to cling to your shirt.",
        ),
        QAItem(
            question="What does receptive mean?",
            answer="Receptive means open to listening, noticing, and accepting another person's idea or feeling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A combo is valid when the place supports practice and the instrument can create
% a boomy-comedy situation that still admits a softening fix.
valid_combo(Place, Inst) :- affords(Place, practice), instrument(Inst), boomy(Inst), softenable(Inst).

% Reconciliation is reasonable when there is a valid combo and the hero is receptive.
reconciliation_story(Place, Inst) :- valid_combo(Place, Inst), receptive(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.mess == "boomy":
            lines.append(asp.fact("boomy", aid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if inst.id == "bass" and inst.can_turn_down:
            lines.append(asp.fact("softenable", iid))
    lines.append(asp.fact("receptive", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a muggy day, a bass, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.instrument is None or c[1] == args.instrument)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")

    place, inst = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(place=place, activity="practice", instrument=inst, name=name, friend_name=friend_name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        INSTRUMENTS[params.instrument],
        params.name,
        params.friend_name,
        params.gender,
    )
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="porch", activity="practice", instrument="bass", name="Mia", friend_name="Leo", gender="girl"),
    StoryParams(place="garage", activity="practice", instrument="bass", name="Noah", friend_name="Ivy", gender="boy"),
    StoryParams(place="bandroom", activity="practice", instrument="bass", name="Ava", friend_name="Max", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciliation_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/2."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:\n")
        for place, inst in combos:
            print(f"  {place:10} {inst}")
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
            header = f"### {p.name}: bass at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
