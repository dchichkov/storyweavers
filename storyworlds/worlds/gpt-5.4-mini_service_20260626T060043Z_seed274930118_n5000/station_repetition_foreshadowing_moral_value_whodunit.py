#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/station_repetition_foreshadowing_moral_value_whodunit.py
===============================================================================================================================

A small whodunit storyworld set at a station, with repetition, foreshadowing,
and a moral-value turn. The domain is intentionally tiny: a missing object,
a handful of suspects, a few concrete clues, and a final reveal driven by the
simulated world state.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class CharacterSpec:
    id: str
    label: str
    type: str


@dataclass
class ClueSpec:
    id: str
    label: str
    phrase: str
    place: str
    tells_on: str
    weight: str


@dataclass
class StoryParams:
    station: str
    missing: str
    thief: str
    helper: str
    witness: str
    seed: Optional[int] = None


class World:
    def __init__(self, station: str) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.station)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


STATIONS = {
    "north_station": "North Station",
    "river_station": "River Station",
    "old_station": "Old Station",
}

CHARACTERS = {
    "mara": CharacterSpec("mara", "Mara", "girl"),
    "owen": CharacterSpec("owen", "Owen", "boy"),
    "nina": CharacterSpec("nina", "Nina", "girl"),
    "leo": CharacterSpec("leo", "Leo", "boy"),
    "paz": CharacterSpec("paz", "Paz", "girl"),
}

MISSING = {
    "red_ticket": ClueSpec("red_ticket", "red ticket", "a red ticket", "ticket window", "conductor", "small"),
    "silver_key": ClueSpec("silver_key", "silver key", "a silver key", "bench by the kiosk", "porter", "tiny"),
    "blue_note": ClueSpec("blue_note", "blue note", "a blue note", "waiting room", "clock keeper", "thin"),
}

HELPERS = {
    "porter": "porter",
    "vendor": "vendor",
    "conductor": "conductor",
    "clockkeeper": "clock keeper",
}

REASONS = [
    "kept the station safe",
    "wanted to help before the train left",
    "knew a kind thing was the right thing to do",
    "did not want anyone blamed unfairly",
]

NAME_POOL = ["Mara", "Owen", "Nina", "Leo", "Paz"]
STATION_ORDER = ["north_station", "river_station", "old_station"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in STATIONS:
        lines.append(asp.fact("station", sid))
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("type_of", cid, c.type))
    for mid, m in MISSING.items():
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("place", mid, m.place))
        lines.append(asp.fact("suspect", mid, m.tells_on))
    return "\n".join(lines)


ASP_RULES = r"""
#show solvable/1.
solvable(S) :- station(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    found = sorted(set(asp.atoms(model, "solvable")))
    expected = [(sid,) for sid in sorted(STATIONS)]
    if found == expected:
        print(f"OK: ASP parity matches ({len(found)} stations).")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("ASP:", found)
    print("PY :", expected)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A station whodunit with repetition, foreshadowing, and a moral ending.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--thief", choices=CHARACTERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--witness", choices=CHARACTERS)
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
    station = args.station or rng.choice(list(STATIONS))
    missing = args.missing or rng.choice(list(MISSING))
    thief = args.thief or rng.choice(list(CHARACTERS))
    helper = args.helper or rng.choice(list(HELPERS))
    witness = args.witness or rng.choice([k for k in CHARACTERS if k != thief])

    if helper == "conductor" and missing == "red_ticket":
        pass
    if thief == witness:
        raise StoryError("The witness must be a different character than the thief.")
    return StoryParams(station=station, missing=missing, thief=thief, helper=helper, witness=witness)


def _build_world(params: StoryParams) -> World:
    world = World(STATIONS[params.station])
    missing = MISSING[params.missing]
    thief = CHARACTERS[params.thief]
    witness = CHARACTERS[params.witness]
    helper_name = HELPERS[params.helper]

    for spec in {thief.id: thief, witness.id: witness, "helper": CharacterSpec("helper", helper_name.title(), "man")} .values():
        pass

    hero = world.add(Entity(id="detective", kind="character", label="the detective", type="girl"))
    t = world.add(Entity(id=thief.id, kind="character", label=thief.label, type=thief.type))
    w = world.add(Entity(id=witness.id, kind="character", label=witness.label, type=witness.type))
    h = world.add(Entity(id="helper", kind="character", label=helper_name, type="man"))
    obj = world.add(Entity(id=missing.id, label=missing.label, phrase=missing.phrase, owner=t.id))
    obj.meters["hidden"] = 1.0
    t.memes["nervous"] = 1.0
    w.memes["alert"] = 1.0
    h.memes["kind"] = 1.0
    hero.memes["curious"] = 1.0

    world.facts.update(hero=hero, thief=t, witness=w, helper=h, missing=obj, clue=missing)
    return world


def _repeated_clue_lines(missing: ClueSpec, station: str) -> list[str]:
    return [
        f"At {station}, the detective noticed the same thing twice: {missing.phrase} was gone.",
        f"Again and again, the station showed the same odd sign: a trail from the {missing.place}.",
        f"The little clue kept coming back, as if it wanted to be seen at {station}.",
    ]


def _foreshadow(world: World, params: StoryParams) -> None:
    clue = world.facts["clue"]
    helper = world.facts["helper"]
    world.say(
        f"At {world.station}, the detective saw {clue.phrase} missing from the {clue.place}. "
        f"{helper.label.title()} kept glancing at a small smear near the bench, then quickly looking away."
    )


def _investigate(world: World, params: StoryParams) -> None:
    clue = world.facts["clue"]
    thief = world.facts["thief"]
    witness = world.facts["witness"]
    world.para()
    for line in _repeated_clue_lines(clue, world.station):
        world.say(line)
    world.para()
    world.say(
        f"The detective asked the same question twice. First: who had been near the {clue.place}? "
        f"Then again: who had been near the {clue.place} when the station bell rang?"
    )
    world.say(
        f"{witness.label} said {thief.label} had waited there, watching the {clue.place}, and then stepping away too fast."
    )
    world.facts["hint"] = f"{thief.label} lingered near the {clue.place}"


def _reveal(world: World, params: StoryParams) -> None:
    clue = world.facts["clue"]
    thief = world.facts["thief"]
    helper = world.facts["helper"]
    witness = world.facts["witness"]
    world.para()
    world.say(
        f"The clue fit at last. {thief.label} had taken {clue.phrase}, but only because {helper.label.title()} had said, "
        f'"If you find it first, hand it back."'
    )
    world.say(
        f"The detective looked from {thief.label} to {helper.label} and then to {witness.label}. "
        f"It was not a story about punishment. It was a story about telling the truth before the train left."
    )
    world.say(
        f"{thief.label} gave the missing thing back, and {witness.label} nodded. "
        f"The station grew quiet again, and the detective remembered the lesson: a small lie can travel far, "
        f"but a small kindness can stop it."
    )
    thief.memes["guilt"] = 1.0
    thief.memes["relief"] = 1.0
    helper.memes["moral_value"] = 1.0
    witness.memes["trust"] = 1.0
    world.facts["solved"] = True


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    clue = world.facts["clue"]
    thief = world.facts["thief"]
    helper = world.facts["helper"]
    witness = world.facts["witness"]
    world.say(
        f"At {world.station}, the detective was called to a puzzling case: {clue.phrase} had vanished."
    )
    world.say(
        f"The detective noticed that {clue.phrase} belonged near the {clue.place}, not in a pocket or a bag."
    )
    _foreshadow(world, params)
    _investigate(world, params)
    _reveal(world, params)
    world.facts["story_end"] = f"{thief.label} returned {clue.label} at {world.station}"
    return world


def generation_prompts(world: World) -> list[str]:
    clue = world.facts["clue"]
    thief = world.facts["thief"]
    return [
        f"Write a short whodunit set at {world.station} about {clue.phrase} going missing.",
        f"Tell a child-friendly mystery where {thief.label} seems suspicious but the ending teaches a kind moral.",
        f"Write a station detective story that repeats a clue, foreshadows the truth, and ends with the missing item returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    clue = world.facts["clue"]
    thief = world.facts["thief"]
    helper = world.facts["helper"]
    witness = world.facts["witness"]
    return [
        QAItem(
            question=f"What was missing at {world.station}?",
            answer=f"{clue.phrase} was missing from the {clue.place}. The detective kept noticing that fact again and again.",
        ),
        QAItem(
            question=f"Who seemed suspicious at first?",
            answer=f"{thief.label} seemed suspicious because {thief.label} lingered near the {clue.place}, but the truth was gentler than it looked.",
        ),
        QAItem(
            question=f"What clue foreshadowed the ending?",
            answer=f"A small smear near the bench and {witness.label}'s careful memory foreshadowed that {thief.label} had only taken the item briefly.",
        ),
        QAItem(
            question=f"What moral value did the ending show?",
            answer=f"The ending showed that telling the truth and returning what does not belong to you is better than hiding a mistake.",
        ),
        QAItem(
            question=f"How did {helper.label} matter to the story?",
            answer=f"{helper.label.title()} mattered because the helper gave the first push toward honesty, which helped the case end kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a station?",
            answer="A station is a place where people wait for trains, look for signs, and pass through on their way to somewhere else.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of evidence that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do detectives repeat questions?",
            answer="Detectives repeat questions because hearing the same answer more than once can help them notice what matters.",
        ),
        QAItem(
            question="What does foreshadowing mean?",
            answer="Foreshadowing means giving a small hint early so the reader can understand the ending later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.label} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(station="north_station", missing="red_ticket", thief="mara", helper="conductor", witness="owen"),
    StoryParams(station="river_station", missing="silver_key", thief="leo", helper="porter", witness="nina"),
    StoryParams(station="old_station", missing="blue_note", thief="paz", helper="vendor", witness="mara"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, t) for s in STATIONS for m in MISSING for t in CHARACTERS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thief and args.witness and args.thief == args.witness:
        raise StoryError("The thief and the witness must be different people.")
    return StoryParams(
        station=args.station or rng.choice(list(STATIONS)),
        missing=args.missing or rng.choice(list(MISSING)),
        thief=args.thief or rng.choice(list(CHARACTERS)),
        helper=args.helper or rng.choice(list(HELPERS)),
        witness=args.witness or rng.choice([k for k in CHARACTERS if k != (args.thief or "")]),
    )


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        combos = asp.atoms(model, "solvable")
        print(f"{len(combos)} solvable stations")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
