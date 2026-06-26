#!/usr/bin/env python3
"""
A small detective-story world about a procrastinator, a flatterer, and the drive
to act bravely.

Seed tale premise:
- A young detective wants to solve a tiny mystery.
- A procrastinator keeps putting off the needed errand.
- A flatterer tries to distract them with compliments.
- Bravery and drive eventually move the case toward the truth.

The world is simulated with physical meters and emotional memes so the prose
comes from state changes rather than a fixed template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "detective"}
        masculine = {"boy", "man", "father", "detective"}
        if self.type in feminine and self.type not in masculine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine and self.type not in feminine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    mystery: str
    clue: str
    errand: str
    risk: str
    turn: str
    resolve: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Temperament:
    id: str
    label: str
    behavior: str
    effect: str
    tags: set[str] = field(default_factory=set)


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
        clone.fired = set(self.fired)
        return clone


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = meter(e, key) + delta


def add_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def has(e: Entity, key: str) -> bool:
    return meter(e, key) >= THRESHOLD or e.memes.get(key, 0.0) >= THRESHOLD


def _r_procrastinate(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.role != "procrastinator":
            continue
        if e.memes.get("delay", 0.0) < THRESHOLD:
            continue
        sig = ("procrastinate", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        add_meme(e, "drive", -0.2)
        add_meme(e, "anxiety", 0.5)
        out.append(f"{e.id} kept putting it off and the clock seemed louder.")
    return out


def _r_flatter(world: World) -> list[str]:
    out = []
    flatterers = [e for e in world.characters() if e.role == "flatterer"]
    targets = [e for e in world.characters() if e.role == "detective"]
    if not flatterers or not targets:
        return out
    f = flatterers[0]
    t = targets[0]
    if f.memes.get("flattery", 0.0) < THRESHOLD:
        return out
    sig = ("flatter", f.id, t.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meme(t, "doubt", 0.6)
    add_meme(f, "control", 0.3)
    out.append(f"{f.id} showered {t.id} with praise, hoping to steer the case.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.role != "detective":
            continue
        if e.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("bravery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        add_meme(e, "drive", 0.7)
        add_meme(e, "doubt", -0.5)
        out.append(f"{e.id} squared their shoulders and chose to follow the clue.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    detective = next((e for e in world.characters() if e.role == "detective"), None)
    if not detective:
        return out
    if detective.memes.get("drive", 0.0) < THRESHOLD:
        return out
    sig = ("solve", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue = world.facts.get("clue", "")
    world.facts["solved"] = True
    out.append(f"The clue pointed straight at the truth: {clue}.")
    return out


RULES = [
    _r_procrastinate,
    _r_flatter,
    _r_bravery,
    _r_solve,
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


SETTINGS = {
    "lantern_lane": Setting(place="Lantern Lane", indoor=False, affordances={"search", "drive"}),
    "archive_room": Setting(place="the archive room", indoor=True, affordances={"search"}),
    "harbor": Setting(place="the harbor", indoor=False, affordances={"search", "drive"}),
}

CASES = {
    "missing_key": Case(
        id="missing_key",
        mystery="a brass key had vanished",
        clue="the key was tucked inside the old blue umbrella",
        errand="search the alley and ask the neighbors",
        risk="waiting too long would let the trail go cold",
        turn="the detective noticed the umbrellas by the door",
        resolve="the key was found before the rain washed the tracks away",
        tags={"key", "umbrella", "rain"},
    ),
    "stolen_note": Case(
        id="stolen_note",
        mystery="a secret note was gone from the desk",
        clue="the note was hidden beneath a sugar jar in the pantry",
        errand="check the pantry and compare the crumbs",
        risk="every delay gave the thief more time to hide the truth",
        turn="the detective spotted sugar dust near the door",
        resolve="the note came back into the light with the afternoon sun",
        tags={"note", "pantry", "crumbs"},
    ),
    "lost_compass": Case(
        id="lost_compass",
        mystery="a small compass had disappeared",
        clue="the compass had slipped into the boat coat pocket",
        errand="walk to the dock and ask the sailor",
        risk="the tide would cover the footprints soon",
        turn="the detective saw a wet pocket flap hanging open",
        resolve="the compass clicked safely back into hand",
        tags={"compass", "dock", "tide"},
    ),
}

TEMPERAMENTS = {
    "procrastinator": Temperament(
        id="procrastinator",
        label="procrastinator",
        behavior="kept delaying the needed errand",
        effect="slowed the search and raised the suspense",
        tags={"delay"},
    ),
    "flatterer": Temperament(
        id="flatterer",
        label="flatterer",
        behavior="poured on praise to distract others",
        effect="made the detective doubt the next step",
        tags={"flattery"},
    ),
    "brave": Temperament(
        id="brave",
        label="brave",
        behavior="chose the hard clue even when it felt risky",
        effect="helped the detective move forward",
        tags={"bravery"},
    ),
}

HERO_NAMES = ["Nina", "Milo", "June", "Theo", "Iris", "Eli", "Ruby", "Finn"]
VILLAIN_NAMES = ["Mr. Vale", "Ms. Finch", "Aunt Mabel", "Mr. Reed"]
SIDE_NAMES = ["Jasper", "Luna", "Poppy", "Owen"]


@dataclass
class StoryParams:
    setting: str
    case: str
    hero_name: str
    hero_role: str
    flatter_name: str
    seed: Optional[int] = None


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    case = CASES[params.case]
    world = World(setting)
    detective = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="detective",
        label="detective",
        role="detective",
        meters={"drive": 0.2, "bravery": 0.2, "doubt": 0.0},
        memes={"drive": 0.2, "bravery": 0.2},
    ))
    procrastinator = world.add(Entity(
        id=params.hero_role,
        kind="character",
        type="person",
        label="the procrastinator",
        role="procrastinator",
        meters={"delay": 1.2},
        memes={"delay": 1.2},
    ))
    flatterer = world.add(Entity(
        id=params.flatter_name,
        kind="character",
        type="person",
        label="the flatterer",
        role="flatterer",
        meters={"flattery": 1.2},
        memes={"flattery": 1.2},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="clue",
        phrase=case.clue,
        owner=detective.id,
    ))
    world.facts.update(case=case, detective=detective, procrastinator=procrastinator,
                       flatterer=flatterer, clue=case.clue)
    return world


def tell(world: World) -> None:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    procrastinator: Entity = world.facts["procrastinator"]
    flatterer: Entity = world.facts["flatterer"]

    world.say(
        f"On {world.setting.place}, {detective.id} was working a tiny mystery: {case.mystery}."
    )
    world.say(
        f"The case smelled of hurry, because {case.risk}."
    )
    world.say(
        f"Near the doorway, {procrastinator.id} kept stalling, as if one more minute could hide the trouble."
    )

    world.para()
    add_meme(procrastinator, "delay", 0.3)
    propagate(world)
    world.say(
        f"Then {flatterer.id} leaned in with shiny words, the kind that sounded nice but bent the truth."
    )
    add_meme(flatterer, "flattery", 0.4)
    propagate(world)

    world.para()
    world.say(
        f"{case.turn.capitalize()}, and that was when {detective.id} felt the first clear spark of bravery."
    )
    add_meme(detective, "bravery", 1.0)
    propagate(world)
    world.say(
        f"{detective.id} ignored the pretty noise, kept the drive alive, and followed the clue."
    )
    add_meme(detective, "drive", 1.0)
    propagate(world)

    world.para()
    world.say(
        f"At last, the answer came together: {case.resolve}."
    )
    world.say(
        f"{detective.id} held the recovered truth like a small lantern, and the flatterer had nothing left to polish."
    )
    world.facts["solved"] = True


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    return [
        f"Write a short detective story for young children about {detective.id} solving {case.mystery}.",
        f"Tell a gentle mystery where procrastination and flattery slow a detective, but bravery and drive finish the job.",
        f"Write a tiny detective adventure that includes the words procrastinator, flatter, drive, and bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    procrastinator: Entity = world.facts["procrastinator"]
    flatterer: Entity = world.facts["flatterer"]
    return [
        QAItem(
            question=f"What mystery was {detective.id} trying to solve?",
            answer=f"{detective.id} was trying to solve a case where {case.mystery}.",
        ),
        QAItem(
            question=f"Who kept putting off the needed errand in the story?",
            answer=f"{procrastinator.id} was the procrastinator, so they kept delaying the errand and made the search slower.",
        ),
        QAItem(
            question=f"What did the flatterer try to do?",
            answer=f"{flatterer.id} tried to distract {detective.id} with praise so the detective would lose focus on the clue.",
        ),
        QAItem(
            question=f"What helped {detective.id} finish the case?",
            answer=f"Bravery and drive helped {detective.id} follow the clue and solve the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out the truth about a mystery.",
        ),
        QAItem(
            question="What is a procrastinator?",
            answer="A procrastinator is a person who keeps putting off something they need to do.",
        ),
        QAItem(
            question="What does it mean to flatter someone?",
            answer="To flatter someone means to give them lots of praise, sometimes to make them do what you want.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary when it is the right thing to do.",
        ),
        QAItem(
            question="What is drive?",
            answer="Drive is the strong energy that helps a person keep going and finish a task.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.role or e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A case is valid when the detective has enough bravery and the story includes
% both a procrastinator and a flatterer to create the needed pressure.
valid_case(C) :- case(C), has_procrastinator, has_flatterer, has_bravery.

need_pressure(C) :- case(C), case_tag(C, delay), case_tag(C, flattery).
case_ready(C) :- need_pressure(C), has_procrastinator, has_flatterer.
story_ok(C) :- valid_case(C), case_ready(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        for tag in sorted(case.tags):
            lines.append(asp.fact("case_tag", cid, tag))
    lines.append(asp.fact("has_procrastinator"))
    lines.append(asp.fact("has_flatterer"))
    lines.append(asp.fact("has_bravery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/1."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = sorted((cid,) for cid in CASES)
    cl = asp_valid_cases()
    if py == cl:
        print(f"OK: ASP parity matches ({len(py)} cases).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", py)
    print("asp:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--flatter", choices=SIDE_NAMES)
    ap.add_argument("--procrastinator", choices=VILLAIN_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    case = args.case or rng.choice(list(CASES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    flatter_name = args.flatter or rng.choice(SIDE_NAMES)
    hero_role = args.procrastinator or rng.choice(VILLAIN_NAMES)
    if hero_name == flatter_name:
        raise StoryError("The detective and the flatterer must be different characters.")
    if hero_name == hero_role or flatter_name == hero_role:
        raise StoryError("The procrastinator must be different from the other characters.")
    return StoryParams(
        setting=setting,
        case=case,
        hero_name=hero_name,
        hero_role=hero_role,
        flatter_name=flatter_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


CURATED = [
    StoryParams(setting="lantern_lane", case="missing_key", hero_name="Nina", hero_role="Mr. Vale", flatter_name="Jasper"),
    StoryParams(setting="archive_room", case="stolen_note", hero_name="Iris", hero_role="Ms. Finch", flatter_name="Luna"),
    StoryParams(setting="harbor", case="lost_compass", hero_name="Theo", hero_role="Mr. Reed", flatter_name="Poppy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/1."))
        print(f"{len(asp.atoms(model, 'story_ok'))} valid story cases")
        for t in asp.atoms(model, "story_ok"):
            print(t[0])
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero_name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
