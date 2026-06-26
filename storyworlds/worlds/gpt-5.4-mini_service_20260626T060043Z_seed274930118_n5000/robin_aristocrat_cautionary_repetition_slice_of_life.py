#!/usr/bin/env python3
"""
storyworlds/worlds/robin_aristocrat_cautionary_repetition_slice_of_life.py
=========================================================================

A small, slice-of-life story world about a robin and an aristocrat, with a
cautionary, repeating domestic beat.

The seed image is simple:
- A robin likes to hop near a fancy breakfast table.
- An aristocrat notices a small danger in the room.
- The aristocrat warns the robin more than once.
- The robin learns to wait, and the morning ends calmly.

The world is designed so the prose is driven by state:
- the robin's hunger and curiosity
- the aristocrat's caution and concern
- a minor household hazard
- a repeated warning that changes the robin's choice
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"robin", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"woman", "girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "uncle", "aristocrat"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the breakfast room"
    afford_danger: bool = True
    afford_waiting: bool = True


@dataclass
class Hazard:
    id: str
    label: str
    risk: str
    avoid: str
    cue: str
    kind: str = "household"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "breakfast_room"
    hazard: str = "tea_cup"
    name: str = "Robin"
    aristocrat_name: str = "Lady Aurelia"
    trait: str = "curious"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


def _warn_repeat(world: World) -> list[str]:
    robin = world.get("robin")
    arist = world.get("aristocrat")
    hazard = world.facts["hazard"]
    if robin.memes.get("temptation", 0) < THRESHOLD:
        return []
    if world.fired and ("warn1",) in world.fired:
        return []
    world.fired.add(("warn1",))
    robin.memes["caution"] = robin.memes.get("caution", 0) + 1
    arist.memes["care"] = arist.memes.get("care", 0) + 1
    return [f'"Careful, little robin," {arist.pronoun("subject")} said. "Stay away from the {hazard.label}."']


def _warn_repeat_again(world: World) -> list[str]:
    robin = world.get("robin")
    arist = world.get("aristocrat")
    hazard = world.facts["hazard"]
    if robin.memes.get("temptation", 0) < THRESHOLD:
        return []
    if robin.memes.get("caution", 0) < THRESHOLD:
        return []
    if ("warn2",) in world.fired:
        return []
    world.fired.add(("warn2",))
    robin.memes["pause"] = robin.memes.get("pause", 0) + 1
    return [f'"Really, stay back," {arist.pronoun("subject")} said again. "That {hazard.label} could spill."']


def _choose_wait(world: World) -> list[str]:
    robin = world.get("robin")
    if robin.memes.get("pause", 0) < THRESHOLD or ("wait",) in world.fired:
        return []
    world.fired.add(("wait",))
    robin.meters["distance"] = 1
    robin.memes["calm"] = robin.memes.get("calm", 0) + 1
    return ["The robin hopped back and waited on the chair rail instead."]


RULES = [_warn_repeat, _warn_repeat_again, _choose_wait]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                changed = True
                for line in s:
                    world.say(line)


SETTINGS = {
    "breakfast_room": Setting(place="the breakfast room"),
    "garden_window": Setting(place="the garden window"),
}

HAZARDS = {
    "tea_cup": Hazard(
        id="tea_cup",
        label="tea cup",
        risk="spill hot tea",
        avoid="spill",
        cue="a shaky saucer",
    ),
    "silver_knife": Hazard(
        id="silver_knife",
        label="silver knife",
        risk="slip on the shining edge",
        avoid="slip",
        cue="a bright slice of silver",
    ),
}

TRAITS = ["curious", "cheerful", "restless", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small robin-and-aristocrat cautionary slice of life story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--name")
    ap.add_argument("--aristocrat-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or "Robin"
    arist = args.aristocrat_name or rng.choice(["Lady Aurelia", "Lord Cedric", "Lady Maris"])
    return StoryParams(seed=None, place=place, hazard=hazard, name=name, aristocrat_name=arist, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    robin = world.add(Entity(
        id="robin", kind="character", type="robin", label=params.name,
        meters={"hunger": 1.0}, memes={"temptation": 1.0}, location=world.setting.place
    ))
    arist = world.add(Entity(
        id="aristocrat", kind="character", type="aristocrat", label=params.aristocrat_name,
        meters={"calm": 1.0}, memes={"care": 1.0}, location=world.setting.place
    ))
    hazard = HAZARDS[params.hazard]
    world.facts.update(robin=robin, aristocrat=arist, hazard=hazard, params=params)

    world.say(f"One morning, {params.name} the robin fluttered into {world.setting.place}.")
    world.say(f"{params.aristocrat_name} was there too, tidying the table and listening to the soft room sounds.")
    world.say(f"{params.name} noticed {hazard.cue} and wanted to hop closer.")

    robin.memes["temptation"] += 1
    propagate(world)

    world.para()
    world.say(f"{params.name} looked at the {hazard.label}, then looked at {params.aristocrat_name}.")
    world.say(f'{params.aristocrat_name} repeated the warning, and {params.name} finally chose to wait.')
    world.say(f"So the morning stayed quiet, and the robin found a crumb after the danger had passed.")
    robin.memes["content"] = 1.0
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short slice-of-life story about {p.name} the robin and {p.aristocrat_name}, with a repeated warning.',
        f"Tell a cautionary story where a robin in {world.setting.place} wants to approach a {f['hazard'].label}, but an aristocrat says to stay back.",
        f'Write a gentle story that uses the words "robin" and "aristocrat" and ends with the robin choosing to wait.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = world.facts["hazard"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.name} the robin and {p.aristocrat_name}, who shared a quiet morning in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the robin want to do near the {h.label}?",
            answer=f"{p.name} wanted to hop closer, but that was not a safe choice because the {h.label} could cause trouble.",
        ),
        QAItem(
            question=f"Why did {p.aristocrat_name} repeat the warning?",
            answer=f"{p.aristocrat_name} repeated the warning because {h.risk} could hurt or start a mess, and the safe choice was to wait.",
        ),
        QAItem(
            question="What did the robin do at the end?",
            answer=f"The robin waited on the chair rail, and the morning stayed calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a robin?",
            answer="A robin is a small bird that hops, sings, and looks for crumbs or worms.",
        ),
        QAItem(
            question="What is an aristocrat?",
            answer="An aristocrat is a person from a noble family or high social class.",
        ),
        QAItem(
            question="What does it mean to be careful?",
            answer="Being careful means slowing down and paying attention so you can avoid a problem.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(list(world.fired))}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
robin(rob).
aristocrat(ari).
hazard(tea).
warns(ari,rob) :- robin(rob), aristocrat(ari), hazard(tea).
repeats(ari) :- warns(ari,rob).
waits(rob) :- repeats(ari).
#show warns/2.
#show repeats/1.
#show waits/1.
"""


def asp_facts() -> str:
    return "robin(rob).\naristocrat(ari).\nhazard(tea).\n"


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show warns/2.\n#show repeats/1.\n#show waits/1."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("warns", 2), ("repeats", 1), ("waits", 1)}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


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
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show warns/2.\n#show repeats/1.\n#show waits/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="breakfast_room", hazard="tea_cup", name="Robin", aristocrat_name="Lady Aurelia", trait="curious"),
            StoryParams(place="garden_window", hazard="silver_knife", name="Robin", aristocrat_name="Lord Cedric", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
