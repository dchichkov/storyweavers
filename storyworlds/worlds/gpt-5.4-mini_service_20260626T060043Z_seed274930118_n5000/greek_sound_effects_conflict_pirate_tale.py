#!/usr/bin/env python3
"""
A small pirate tale storyworld with sound effects and a Greek-flavored conflict.

Premise:
- A young pirate loves making loud sound effects on deck.
- A found Greek trinket or map matters to the captain.
- The sounds stir tension when they echo at the wrong moment.
- A clever compromise turns the clash into a celebration.

This file is self-contained and follows the Storyweavers world contract.
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

SFX = {
    "clang": "clang",
    "whoosh": "whoosh",
    "thump": "thump",
    "boom": "boom",
    "creak": "creak",
    "tap": "tap",
    "splash": "splash",
    "fizz": "fizz",
}

GREEK_WORDS = {
    "alpha": "alpha",
    "beta": "beta",
    "zeus": "Zeus",
    "athens": "Athens",
    "mosaic": "mosaic",
    "trident": "trident",
    "lyre": "lyre",
    "olive": "olive",
}

LOCATIONS = {
    "deck": "the deck",
    "harbor": "the harbor",
    "cove": "the cove",
    "cabin": "the cabin",
}

CONFLICTS = {
    "map": "a Greek map",
    "coin": "a Greek coin",
    "idol": "a tiny Greek idol",
    "lyre": "a little Greek lyre",
}

COMPROMISES = {
    "hush": "speak softly and tap the rhythm on the rail",
    "shanty": "turn the sounds into a shanty instead of a racket",
    "signal": "use hand signals and one brave sound at the end",
}


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    place: str
    seas: list[str]
    allowed_sfx: set[str]
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    conflict: str
    sound: str
    name: str
    gender: str
    captain: str
    seed: Optional[int] = None


WORLD_PLACES = {
    "deck": LOCATIONS["deck"],
    "harbor": LOCATIONS["harbor"],
    "cove": LOCATIONS["cove"],
    "cabin": LOCATIONS["cabin"],
}

WORLD_CONFLICTS = CONFLICTS
WORLD_SOUNDS = SFX
CAPTAINS = ["captain", "old captain", "sea captain"]
NAMES_BOY = ["Finn", "Orrin", "Tomas", "Jace", "Eli", "Nico"]
NAMES_GIRL = ["Mira", "Poppy", "Sena", "Lena", "Tara", "Iris"]

THRESHOLD = 1.0

ASP_RULES = r"""
sound_rises(S) :- sound(S).
conflict_boils(C) :- conflict(C).
loud(S) :- sound_rises(S), S != tap.
disturbs(C,S) :- conflict_boils(C), loud(S).
calm_plan(hush) :- sound(tap), conflict(C), item(C, greek).
calm_plan(shanty) :- sound(fizz), conflict(C).
calm_story :- calm_plan(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in WORLD_SOUNDS:
        lines.append(asp.fact("sound", s))
    for c in WORLD_CONFLICTS:
        lines.append(asp.fact("conflict", c))
        lines.append(asp.fact("item", c, "greek"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show calm_plan/1.\n#show disturbs/2.\n")
    model = asp.one_model(program)
    shown = asp.atoms(model, "calm_plan")
    if shown:
        print("OK: ASP reasoning produced a calm_plan.")
        return 0
    print("MISMATCH: ASP reasoning failed to produce a calm_plan.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with Greek conflict and sound effects.")
    ap.add_argument("--place", choices=WORLD_PLACES)
    ap.add_argument("--conflict", choices=WORLD_CONFLICTS)
    ap.add_argument("--sound", choices=WORLD_SOUNDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(WORLD_PLACES))
    conflict = args.conflict or rng.choice(list(WORLD_CONFLICTS))
    sound = args.sound or rng.choice(list(WORLD_SOUNDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    captain = args.captain or rng.choice(CAPTAINS)
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(place=place, conflict=conflict, sound=sound, name=name, gender=gender, captain=captain)


def _say_sound(word: str) -> str:
    return {
        "clang": "CLANG!",
        "whoosh": "WHOOOSH!",
        "thump": "THUMP!",
        "boom": "BOOM!",
        "creak": "CREAK!",
        "tap": "tap tap",
        "splash": "SPLASH!",
        "fizz": "fizz fizz",
    }[word]


def generate_world(params: StoryParams) -> Ship:
    ship = Ship(place=WORLD_PLACES[params.place], seas=["blue sea", "gray sea"], allowed_sfx=set(WORLD_SOUNDS))
    child = ship.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name, meters={"joy": 0.0}, memes={"pride": 1.0, "restraint": 0.0, "worry": 0.0}))
    captain = ship.add(Entity(id="captain", kind="character", type="man", label=params.captain, meters={"calm": 1.0}, memes={"worry": 0.0, "trust": 0.0}))
    treasure = ship.add(Entity(id="treasure", type="thing", label=WORLD_CONFLICTS[params.conflict], phrase=WORLD_CONFLICTS[params.conflict], caretaker="captain"))
    ship.facts.update(child=child, captain=captain, treasure=treasure, params=params)
    return ship


def tell(params: StoryParams) -> Ship:
    ship = generate_world(params)
    child: Entity = ship.facts["child"]
    captain: Entity = ship.facts["captain"]
    treasure: Entity = ship.facts["treasure"]

    sfx = _say_sound(params.sound)
    greek_note = {
        "map": "It had Greek letters on it.",
        "coin": "One side showed a Greek face.",
        "idol": "It looked like a tiny Greek hero.",
        "lyre": "Its strings looked ready for a Greek song.",
    }[params.conflict]

    ship.say(f"On {ship.place}, {child.id} was a little pirate who loved making sound effects. {sfx}")
    ship.say(f"{child.id} had found {treasure.phrase}. {greek_note}")
    ship.say(f"But {captain.label} held it close, because that Greek thing mattered for the next trip.")

    ship.para()
    ship.say(f"One evening, {child.id} tried a big {params.sound} for fun.")
    child.meters["noise"] = child.meters.get("noise", 0.0) + 1.0
    ship.say(f"The sound bounced off the boards and made the ropes answer with a { _say_sound('creak') }.")
    captain.memes["worry"] += 1.0
    ship.say(f"{captain.label} frowned. 'Easy now,' {captain.pronoun('subject')} said, 'that could scramble the chart and stir trouble.'")

    ship.para()
    ship.say(f"{child.id} wanted to keep going, but {captain.label} explained that the Greek treasure was not a toy.")
    child.memes["conflict"] = 1.0
    ship.say(f"{child.id} felt hot with stubborn pride, then looked at the treasure and the worried crew.")

    ship.para()
    if params.sound == "tap":
        plan = COMPROMISES["hush"]
    elif params.sound in {"fizz", "whoosh"}:
        plan = COMPROMISES["shanty"]
    else:
        plan = COMPROMISES["signal"]
    child.meters["restraint"] = child.meters.get("restraint", 0.0) + 1.0
    captain.memes["trust"] += 1.0
    child.memes["conflict"] = 0.0
    child.meters["joy"] = child.meters.get("joy", 0.0) + 1.0

    ship.say(f"Then {captain.label} gave a better idea: {plan}.")
    ship.say(f"{child.id} nodded and tried it. {sfx} became part of a pirate tune instead of a rowdy racket.")
    ship.say(f"At the end, the Greek treasure stayed safe, the crew laughed, and the deck sounded merry instead of mean.")
    ship.say(f"{child.id} stood by the rail, smiling at the dark sea while the last {params.sound} drifted away like a friendly wave.")

    ship.facts["resolved"] = True
    ship.facts["plan"] = plan
    return ship


def generation_prompts(ship: Ship) -> list[str]:
    p: StoryParams = ship.facts["params"]
    return [
        f"Write a short pirate tale for children that includes the sound effect '{p.sound}' and the word greek.",
        f"Tell a story where {p.name} the pirate makes a noisy {p.sound} while a Greek treasure worries the captain.",
        f"Write a gentle conflict-and-fix story on a ship, ending with the crew choosing a quieter way to handle the Greek treasure.",
    ]


def story_qa(ship: Ship) -> list[QAItem]:
    p: StoryParams = ship.facts["params"]
    child: Entity = ship.facts["child"]
    captain: Entity = ship.facts["captain"]
    treasure: Entity = ship.facts["treasure"]
    return [
        QAItem(
            question=f"Who loved making sound effects on the ship?",
            answer=f"{child.id} loved making sound effects on {ship.place}.",
        ),
        QAItem(
            question=f"What Greek thing caused the trouble?",
            answer=f"The trouble came from {treasure.phrase}, and it mattered to {captain.label}.",
        ),
        QAItem(
            question=f"How did the pirate story end?",
            answer=f"It ended with {child.id} choosing a calmer plan so the Greek treasure stayed safe and the crew could smile again.",
        ),
    ]


def world_knowledge_qa(ship: Ship) -> list[QAItem]:
    return [
        QAItem(question="What is a pirate?", answer="A pirate is a person in a sea adventure who sails ships and looks for treasure."),
        QAItem(question="What is a sound effect?", answer="A sound effect is a strong sound, like clang or whoosh, that makes a scene feel lively."),
        QAItem(question="What does Greek mean here?", answer="Greek points to things from Greece, like Greek letters, stories, art, or old treasures."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
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


def dump_trace(ship: Ship) -> str:
    lines = ["--- world model ---"]
    for e in ship.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    ship = tell(params)
    sample = StorySample(
        params=params,
        story=ship.render(),
        prompts=generation_prompts(ship),
        story_qa=story_qa(ship),
        world_qa=world_knowledge_qa(ship),
        world=ship,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="deck", conflict="map", sound="clang", name="Mira", gender="girl", captain="old captain"),
        StoryParams(place="harbor", conflict="coin", sound="whoosh", name="Finn", gender="boy", captain="captain"),
        StoryParams(place="cove", conflict="idol", sound="tap", name="Sena", gender="girl", captain="sea captain"),
        StoryParams(place="cabin", conflict="lyre", sound="fizz", name="Orrin", gender="boy", captain="captain"),
    ]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show calm_plan/1.\n"))
    return sorted(set(asp.atoms(model, "calm_plan")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show calm_plan/1.\n#show disturbs/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} calm-plan models")
        for t in vals:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
