#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hammock_meter_repetition_sound_effects_whodunit.py
==============================================================================================================

A small whodunit storyworld about a hammock, a meter, repeating clues, and the
little sounds that give the truth away.

The seed tale behind this world:
---
A child hears a hammock creak in the yard and a meter tick by the gate.
Someone keeps making the same sound again and again. The child follows the
sound effects, checks the meter, and solves the mystery.
---

World idea:
- The story is a child-sized mystery with a clear clue trail.
- Repetition matters: the same sound happens more than once, and that repetition
  becomes the clue.
- Sound effects matter: "creak", "tap tap", "tik-tik", "thump" are part of the
  evidence and appear in the prose naturally.
- A hammock is the victim of the mystery; a meter provides a measured clue
  about where the sound came from.
- The ending proves the culprit and the fix.

This script follows the storyworld contract:
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- imports results eagerly
- imports asp lazily in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    wears: Optional[str] = None
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
    affordance: str
    weather: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    sound: str
    habit: str
    evidence: str
    guilty: bool = False


@dataclass
class Mystery:
    label: str
    phrase: str
    damage: str
    victim_part: str
    risk_sound: str
    repeated_sound: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues: list[str] = []
        self.solve_mark: Optional[str] = None

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.clues = list(self.clues)
        return w


def _sound_repeat(sound: str) -> str:
    return f"{sound} {sound}"


def _sound_thrice(sound: str) -> str:
    return f"{sound} {sound} {sound}"


def _add_clue(world: World, clue: str) -> None:
    if clue not in world.clues:
        world.clues.append(clue)


def _narrate_clue(world: World, sound: str, placebit: str) -> None:
    world.say(f"{sound.capitalize()} came again, then again, from {placebit}.")


def _suspect_noise(world: World, hero: Entity, suspect: Suspect, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} heard {suspect.sound}, then heard {suspect.sound} again."
    )
    _add_clue(world, suspect.evidence)
    world.facts["heard_sound"] = suspect.sound
    if suspect.guilty:
        hero.memes["certainty"] = hero.memes.get("certainty", 0) + 1


def _measure(world: World, hero: Entity) -> int:
    meter = world.get("meter")
    return int(meter.meters.get("reading", 0))


def _bump_meter(world: World, amount: int) -> None:
    meter = world.get("meter")
    meter.meters["reading"] = meter.meters.get("reading", 0) + amount


def _solve(world: World, hero: Entity, suspect: Suspect, mystery: Mystery, tool: Tool) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.solve_mark = suspect.id
    world.say(
        f"At last, {hero.id} pointed at {suspect.label}. "
        f'"It was {suspect.label}," {hero.pronoun()} said, "because the same sound kept coming back."'
    )
    world.say(
        f"{suspect.label} had left {suspect.evidence}, and the meter had climbed to { _measure(world) }."
    )
    world.say(
        f"{hero.id} used the {tool.label} to fix the {mystery.label}, and the yard fell quiet."
    )


def tell(world: World, hero: Entity, suspect: Suspect, mystery: Mystery, tool: Tool) -> None:
    world.say(
        f"{hero.id} was a little detective who liked quiet afternoons and neat clues."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had a {mystery.phrase} in the yard."
    )
    world.say(
        f"Near the gate stood a small meter that liked to click whenever the yard changed."
    )
    world.say(
        f"The hammock was {mystery.damage}, and that made the whole place feel like a mystery."
    )

    world.para()
    world.say(
        f"Then the sound started: {mystery.risk_sound}, {mystery.risk_sound}, {mystery.risk_sound}."
    )
    _bump_meter(world, 1)
    _narrate_clue(world, mystery.risk_sound, "the hammock rope")
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(
        f"{hero.id} listened once, then twice, then a third time."
    )

    world.para()
    _suspect_noise(world, hero, suspect, mystery)
    _bump_meter(world, 1)
    world.say(
        f"The meter gave a tiny click-click, like it was counting the repeats."
    )
    world.say(
        f"{hero.id} looked at the floor, the rope, and the gate, one by one."
    )

    world.para()
    if suspect.guilty:
        _add_clue(world, mystery.repeated_sound)
        _solve(world, hero, suspect, mystery, tool)
    else:
        world.say(
            f"{hero.id} was not sure yet, because the clues did not fit together."
        )


SETTINGS = {
    "backyard": Setting(place="the backyard", affordance="hammock", weather="sunny"),
    "garden": Setting(place="the garden", affordance="hammock", weather="breezy"),
    "sideyard": Setting(place="the side yard", affordance="meter", weather="cloudy"),
}

MYSTERIES = {
    "rope_tug": Mystery(
        label="hammock rope",
        phrase="soft rope on a swingy hammock",
        damage="frayed at one end",
        victim_part="rope",
        risk_sound="creak-creak",
        repeated_sound="creak",
    ),
    "seat_drop": Mystery(
        label="hammock seat",
        phrase="a cozy hammock seat",
        damage="tilted low to the ground",
        victim_part="seat",
        risk_sound="thump-thump",
        repeated_sound="thump",
    ),
}

SUSPECTS = {
    "raccoon": Suspect(
        id="raccoon",
        label="a raccoon",
        type="thing",
        sound="scuffle-scuffle",
        habit="sniffing for crumbs",
        evidence="muddy paw prints by the meter",
        guilty=True,
    ),
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="thing",
        sound="pat-pat",
        habit="slipping through small spaces",
        evidence="one white whisker on the chair",
        guilty=False,
    ),
    "wind": Suspect(
        id="wind",
        label="the wind",
        type="thing",
        sound="whoosh-whoosh",
        habit="bumping loose things",
        evidence="dust in the corner",
        guilty=False,
    ),
}

TOOLS = {
    "tie": Tool(
        id="tie",
        label="garden tie",
        phrase="a soft garden tie",
        use="bind the loose rope",
        covers={"rope"},
    ),
    "patch": Tool(
        id="patch",
        label="patch kit",
        phrase="a little patch kit",
        use="patch the torn seat",
        covers={"seat"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Lina", "Tara", "Nora"]
BOY_NAMES = ["Owen", "Cal", "Ezra", "Noah", "Milo"]
TRAITS = ["curious", "careful", "quiet", "clever", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for sid, suspect in SUSPECTS.items():
                if suspect.guilty:
                    combos.append((place, mid, sid))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    suspect: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with a hammock and a meter.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection() -> str:
    return "(No story: the clues do not make a solvable whodunit.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError(explain_rejection())
    place, mystery, suspect = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, suspect=suspect, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS["tie"] if mystery.victim_part == "rope" else TOOLS["patch"]
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        traits=["little", params.trait],
    ))
    meter = world.add(Entity(id="meter", kind="thing", type="meter", label="meter"))
    meter.meters["reading"] = 0
    world.facts.update(hero=hero, mystery=mystery, suspect=suspect, tool=tool, meter=meter)
    tell(world, hero, suspect, mystery, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for a child about {f['hero'].id}, a hammock, and a meter.",
        f"Tell a mystery story where the same sound repeats again and again until the culprit is found.",
        f"Write a gentle detective story that uses the sound effect {f['mystery'].risk_sound} and ends with the hammock fixed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    suspect: Suspect = f["suspect"]
    tool: Tool = f["tool"]
    qa = [
        QAItem(
            question=f"What did {hero.id} hear first in the yard?",
            answer=f"{hero.id} heard the same sound again and again: {mystery.risk_sound}. That repeating sound was the first clue.",
        ),
        QAItem(
            question=f"Why did {hero.id} know it was {suspect.label}?",
            answer=f"{hero.id} knew because {suspect.label} left {suspect.evidence}, and the sound repeated in the same way more than once.",
        ),
        QAItem(
            question=f"What did {hero.id} use to fix the {mystery.label}?",
            answer=f"{hero.id} used the {tool.label} to fix the {mystery.label} after solving the mystery.",
        ),
    ]
    if suspect.guilty:
        qa.append(QAItem(
            question=f"What clue kept coming back and helped solve the case?",
            answer=f"The clue was the repeated sound {mystery.risk_sound}. It happened more than once, so {hero.id} knew to follow it.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hammock?",
            answer="A hammock is a soft hanging bed or swing made of cloth or netting, and people lie in it to rest.",
        ),
        QAItem(
            question="What does a meter do?",
            answer="A meter measures or counts something, like distance, time, or how much of a change has happened.",
        ),
        QAItem(
            question="Why do sound effects repeat in mystery stories?",
            answer="Repeated sound effects can act like clues, because hearing the same sound again can help a detective notice a pattern.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  clues={world.clues}")
    lines.append(f"  solve_mark={world.solve_mark}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="backyard", mystery="rope_tug", suspect="raccoon", name="Mina", gender="girl", trait="clever"),
    StoryParams(place="garden", mystery="seat_drop", suspect="raccoon", name="Owen", gender="boy", trait="curious"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("has", pid, s.affordance))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("repeats", mid, m.repeated_sound))
        lines.append(asp.fact("risk_sound", mid, m.risk_sound))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.guilty:
            lines.append(asp.fact("guilty", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Mystery, Suspect) :- place(Place), mystery(Mystery), suspect(Suspect), guilty(Suspect).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, mystery, suspect in combos:
            print(f"  {place:10} {mystery:12} {suspect}")
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
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
