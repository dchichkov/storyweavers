#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bottle_feed_arrest_flick_mystery_to_solve.py
===============================================================================================================

A small space-adventure story world about a mysterious missing signal, a tiny
creature that must be bottle-fed, a flick of light, and a careful arrest that
solves the surprise.

Premise
-------
On a quiet starship, the crew cares for a tiny moonling hatchling that needs
bottle-feeding every cycle. One evening, the ship's navigation charm goes
missing. A surprising flick of light reveals clues, and the crew must solve the
mystery without panicking the hatchling.

World model
-----------
- The hatchling has need, comfort, and hunger meters.
- The crew has suspicion and calm meters.
- The mystery has clue and solved state.
- A flick can reveal hidden evidence.
- An arrest is only reasonable when the culprit is identified by a clue trail.

This script is self-contained and uses the shared result containers plus the
shared ASP helper in the repo.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    place: str
    crew: str
    hatchling: str
    culprit: str
    seed: Optional[int] = None


@dataclass
class Mystery:
    missing_item: str
    clue_item: str
    resolved: bool = False
    culprit_found: bool = False


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "orbital_garden": Setting(
        place="the orbital garden",
        detail="Soft blue panels glowed like moonlight over the floating vines.",
    ),
    "cargo_ring": Setting(
        place="the cargo ring",
        detail="The ring hummed with cargo lights, crates, and narrow silver rails.",
    ),
    "stargazer_bay": Setting(
        place="the stargazer bay",
        detail="A dome of glass showed the stars, and the room felt wide and quiet.",
    ),
}

CREW = {
    "captain": {"type": "captain", "label": "Captain Mira"},
    "pilot": {"type": "pilot", "label": "Pilot Jun"},
    "engineer": {"type": "man", "label": "Engineer Sol"},
}

HATCHLINGS = {
    "moonling": {
        "type": "moonling",
        "label": "moonling",
        "phrase": "a tiny moonling hatchling in a warm blanket",
    }
}

CULPRITS = {
    "stowaway": {"type": "man", "label": "a sneaky stowaway"},
    "sprite": {"type": "thing", "label": "a spark sprite"},
}

MYSTERY_ITEMS = {
    "nav_charm": "the navigation charm",
    "glitter_map": "the glitter map",
    "signal_key": "the signal key",
}


class Reasoner:
    @staticmethod
    def can_arrest(mystery: Mystery, clue_seen: bool) -> bool:
        return mystery.culprit_found and clue_seen and not mystery.resolved


def flick_light(world: World, actor: Entity) -> None:
    if ("flick", actor.id) in world.fired:
        return
    world.fired.add(("flick", actor.id))
    world.facts["light_flicked"] = True
    world.say(
        f"{actor.label} gave the lantern a tiny flick, and the beam jumped across the room."
    )


def feed_hatchling(world: World, caretaker: Entity, hatchling: Entity) -> None:
    world.facts["fed"] = True
    hatchling.meters["hunger"] = max(0.0, hatchling.meters.get("hunger", 0.0) - 1.0)
    hatchling.meters["comfort"] = hatchling.meters.get("comfort", 0.0) + 1.0
    caretaker.memes["care"] = caretaker.memes.get("care", 0.0) + 1.0
    world.say(
        f"{caretaker.label} bottle-fed the moonling carefully, and the little hatchling calmed down at once."
    )


def discover_clue(world: World, actor: Entity, culprit: Entity, mystery: Mystery) -> None:
    world.facts["clue_seen"] = True
    actor.memes["surprise"] = actor.memes.get("surprise", 0.0) + 1.0
    actor.memes["certainty"] = actor.memes.get("certainty", 0.0) + 1.0
    culprit.memes["nervous"] = culprit.memes.get("nervous", 0.0) + 1.0
    mystery.culprit_found = True
    world.say(
        f"With the light flicking back and forth, {actor.label} spotted {culprit.label} hiding the missing {mystery.missing_item}."
    )
    world.say(
        f"Under a crate was a bright {mystery.clue_item}, and that was the clue that solved the mystery."
    )


def arrest_culprit(world: World, actor: Entity, culprit: Entity, mystery: Mystery) -> None:
    if not Reasoner.can_arrest(mystery, world.facts.get("clue_seen", False)):
        raise StoryError("An arrest only makes sense after the culprit is identified by a clue.")
    mystery.resolved = True
    actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1.0
    culprit.memes["captured"] = culprit.memes.get("captured", 0.0) + 1.0
    world.facts["arrested"] = True
    world.say(
        f"{actor.label} arrested {culprit.label} carefully, not with anger, but so the ship could stay safe."
    )
    world.say(
        f"Then the crew found the missing {mystery.missing_item}, and the starship finally felt peaceful again."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    captain = world.add(Entity(id="captain", kind="character", type="captain", label="Captain Mira"))
    pilot = world.add(Entity(id="pilot", kind="character", type="pilot", label="Pilot Jun"))
    engineer = world.add(Entity(id="engineer", kind="character", type="man", label="Engineer Sol"))
    hatchling = world.add(Entity(
        id="moonling", kind="character", type="moonling", label="the moonling",
        phrase=HATCHLINGS["moonling"]["phrase"],
    ))
    culprit = world.add(Entity(
        id=params.culprit, kind="character", type=CULPRITS[params.culprit]["type"],
        label=CULPRITS[params.culprit]["label"],
    ))

    mystery = Mystery(
        missing_item=MYSTERY_ITEMS["nav_charm"],
        clue_item="silver thread",
    )

    captain.meters["calm"] = 1.0
    hatchling.meters["hunger"] = 1.0
    hatchling.meters["comfort"] = 0.0

    world.say(
        f"On {setting.place}, {captain.label} watched over {hatchling.phrase} while the crew listened to the ship's soft hum."
    )
    world.say(
        f"The moonling needed a bottle-feed before sleep, and that gentle job kept everyone's hands busy."
    )
    world.para()
    feed_hatchling(world, pilot, hatchling)
    world.say(
        f"After that, {engineer.label} noticed the navigation charm was missing, and the room went quiet with worry."
    )
    world.say(
        f"{captain.label} did not want a long panic; instead, {captain.label.split()[0]} asked for a careful search."
    )
    world.para()
    flick_light(world, engineer)
    discover_clue(world, captain, culprit, mystery)
    world.para()
    arrest_culprit(world, captain, culprit, mystery)

    world.facts.update(
        setting=setting,
        captain=captain,
        pilot=pilot,
        engineer=engineer,
        hatchling=hatchling,
        culprit=culprit,
        mystery=mystery,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a small child that includes "bottle-feed", "flick", and "arrest".',
        f"Tell a gentle mystery where {f['captain'].label} solves a missing-item surprise on {f['setting'].place}.",
        f"Write a story about a moonling hatchling, a flick of light, and a safe arrest that fixes the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    pilot = f["pilot"]
    engineer = f["engineer"]
    hatchling = f["hatchling"]
    culprit = f["culprit"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question="Who bottle-fed the moonling hatchling?",
            answer=f"{pilot.label} bottle-fed the moonling hatchling so it would feel calm and full before sleep.",
        ),
        QAItem(
            question="What happened when the light was flicked?",
            answer=(
                f"When {engineer.label} gave the lantern a flick, the beam moved across the crates and showed {culprit.label} hiding the missing {mystery.missing_item}."
            ),
        ),
        QAItem(
            question="Why was the arrest possible?",
            answer=(
                f"The arrest was possible because {captain.label} had already seen the clue, knew who was hiding the missing item, and could act safely without guessing."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with the mystery solved, the missing {mystery.missing_item} found, and the starship feeling peaceful again on {setting.place}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bottle-feeding mean?",
            answer="Bottle-feeding means giving milk or another drink from a bottle so a baby or hatchling can eat safely.",
        ),
        QAItem(
            question="What is a flick?",
            answer="A flick is a small quick movement, like tapping or snapping a light so it flashes on and off.",
        ),
        QAItem(
            question="What is an arrest?",
            answer="An arrest is when a guard or officer takes someone into custody because they think that person broke the rules.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where someone must find missing facts or clues before they can explain what really happened.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people stop, look, and feel amazed or startled.",
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
    lines.append("== World questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for crew_id in CREW:
        lines.append(asp.fact("crew", crew_id))
    for hatch_id in HATCHLINGS:
        lines.append(asp.fact("hatchling", hatch_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
    lines.append(asp.fact("missing_item", "nav_charm"))
    lines.append(asp.fact("clue_item", "silver_thread"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_scene(P, C, H, X) :- place(P), crew(C), hatchling(H), culprit(X).
can_arrest(X) :- culprit(X).
solve_mystery(P, X) :- valid_scene(P, _, _, X), can_arrest(X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_scene/4."))
    return sorted(set(asp.atoms(model, "valid_scene")))


def asp_verify() -> int:
    py = set((p, c, h, x) for p in SETTINGS for c in CREW for h in HATCHLINGS for x in CULPRITS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python combinations ({len(py)} scenes).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--crew", choices=CREW)
    ap.add_argument("--hatchling", choices=HATCHLINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    crew = args.crew or rng.choice(list(CREW))
    hatchling = args.hatchling or rng.choice(list(HATCHLINGS))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    return StoryParams(place=place, crew=crew, hatchling=hatchling, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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

    if args.show_asp:
        print(asp_program("#show valid_scene/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible scenes")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for crew in CREW:
                for hatchling in HATCHLINGS:
                    for culprit in CULPRITS:
                        samples.append(generate(StoryParams(place, crew, hatchling, culprit, seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
