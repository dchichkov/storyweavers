#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gay_moray_conflict_whodunit.py
==============================================================================================================

A small whodunit storyworld about a seaside mystery, a fretful conflict,
and a clever reveal involving a moray eel.

The generated seed words are woven into the world:
- gay
- moray

The domain is intentionally small and classical:
- a pier-side aquarium
- a missing key
- a suspiciously open hatch
- a calm detective who pieces together the clues

The story engine simulates:
- physical state in meters (seen/moved/wet/hidden)
- emotional state in memes (worry, suspicion, relief, pride)
- a conflict turn that becomes a clue-driven resolution

This file is standalone and follows the Storyweavers storyworld contract.
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
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "animal"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    atmosphere: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    found_in: str
    points_to: str
    note: str


@dataclass
class StoryParams:
    place: str
    missing: str
    suspect: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location):
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""
        self.clues_found: list[str] = []
        self.solution: Optional[str] = None

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
        clone = World(self.location)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.clues_found = list(self.clues_found)
        clone.solution = self.solution
        return clone

    def room_of(self, eid: str) -> str:
        return self.entities[eid].room


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "pier": Location(
        id="pier",
        label="the pier aquarium",
        atmosphere="The salt air drifted through open boards, and the aquarium windows gleamed over the water.",
        supports={"missing_key", "wet_bootprints", "eel_silence"},
    ),
    "dock": Location(
        id="dock",
        label="the quiet dockside room",
        atmosphere="The dockside room smelled like rope, seawater, and old wood.",
        supports={"missing_key", "wet_bootprints", "eel_silence"},
    ),
}

MISSING_ITEMS = {
    "key": Entity(
        id="key_item",
        type="thing",
        label="brass key",
        phrase="a small brass key for the hatch",
        plural=False,
    ),
    "shell_box": Entity(
        id="shell_box",
        type="thing",
        label="shell box",
        phrase="a shell-shaped box with a tiny latch",
        plural=False,
    ),
}

SUSPECTS = {
    "moray": Entity(
        id="moray",
        kind="animal",
        type="animal",
        label="moray eel",
        phrase="a long moray eel with curious eyes",
    ),
    "caretaker": Entity(
        id="caretaker",
        kind="character",
        type="woman",
        label="aquarium caretaker",
        phrase="the aquarium caretaker",
    ),
    "visitor": Entity(
        id="visitor",
        kind="character",
        type="man",
        label="dock visitor",
        phrase="the dock visitor",
    ),
}

CLUES = {
    "wet_bootprints": Clue(
        id="wet_bootprints",
        label="wet bootprints",
        phrase="a trail of wet bootprints",
        found_in="boardwalk",
        points_to="dock",
        note="the bootprints came from the dock side, not the tank room",
    ),
    "open_hatch": Clue(
        id="open_hatch",
        label="open hatch",
        phrase="a hatch left open by the low shelf",
        found_in="tank_room",
        points_to="moray",
        note="the eel had nudged the latch, but only because the key was nearby",
    ),
    "salt_ribbon": Clue(
        id="salt_ribbon",
        label="salt ribbon",
        phrase="a thin ribbon of salt drying on the floor",
        found_in="hallway",
        points_to="dock",
        note="salt water had been carried in from the dock, then dried by the vents",
    ),
    "tiny_scratches": Clue(
        id="tiny_scratches",
        label="tiny scratches",
        phrase="tiny scratches around the key hook",
        found_in="hook",
        points_to="visitor",
        note="someone had pried at the hook with a pocket tool",
    ),
}

DETECTIVE_NAMES = ["Gay", "Mina", "June", "Ira", "Noel", "Ruth", "Pia", "Tess"]
HELPER_NAMES = ["Pip", "Milo", "Kit", "Jo", "Bea", "Nell", "Wren", "Sami"]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def negate(name: str) -> str:
    return f"not {name}"


def who_text(ent: Entity) -> str:
    return ent.label or ent.id


def room_text(location: Location) -> str:
    return location.label


def story_day(location: Location) -> str:
    return f"One evening at {room_text(location)}, "


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def clue_at(world: World, clue_id: str) -> bool:
    return clue_id not in world.clues_found


def find_clue(world: World, clue_id: str, finder: Entity) -> Optional[str]:
    if clue_id in world.clues_found:
        return None
    world.clues_found.append(clue_id)
    clue = CLUES[clue_id]
    if clue_id == "wet_bootprints":
        finder.memes["focus"] = finder.memes.get("focus", 0.0) + 1
        return f"{finder.id} spotted {clue.phrase} near the boards."
    if clue_id == "open_hatch":
        return f"{finder.id} found {clue.phrase} beside the tank room."
    if clue_id == "salt_ribbon":
        return f"{finder.id} noticed {clue.phrase} in the hallway."
    if clue_id == "tiny_scratches":
        return f"{finder.id} noticed {clue.phrase} on the hook."
    return None


def infer_solution(world: World) -> str:
    if {"wet_bootprints", "salt_ribbon", "open_hatch", "tiny_scratches"}.issubset(set(world.clues_found)):
        return "visitor"
    if {"wet_bootprints", "open_hatch"}.issubset(set(world.clues_found)):
        return "moray"
    return "unknown"


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------

def introduce(world: World, detective: Entity, helper: Entity, missing: Entity, suspect: Entity) -> None:
    world.say(
        f"{detective.id} was {article(detective.type)} calm little detective who liked neat clues and quiet questions."
    )
    world.say(
        f"At {room_text(world.location)}, {helper.id} guarded {missing.phrase}, but one morning {missing.label} was gone."
    )
    if suspect.id == "moray":
        world.say(
            f"Everyone looked at the tank, because the moray eel had been wriggling near the hatch."
        )
    else:
        world.say(
            f"Everyone looked at the visitor, because he had been pacing near the hatch."
        )


def start_conflict(world: World, detective: Entity, helper: Entity, suspect: Entity) -> None:
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    detective.memes["suspicion"] = detective.memes.get("suspicion", 0.0) + 1
    world.say(
        f"{helper.id} grew upset and said the {suspect.label} must have taken it."
    )
    world.say(
        f"{detective.id} did not agree yet. {detective.pronoun().capitalize()} wanted proof, not a guess."
    )


def search(world: World, detective: Entity, helper: Entity) -> None:
    clue = find_clue(world, "wet_bootprints", detective)
    if clue:
        world.say(clue)
    clue = find_clue(world, "salt_ribbon", helper)
    if clue:
        world.say(clue)
    clue = find_clue(world, "open_hatch", detective)
    if clue:
        world.say(clue)


def tighten_conflict(world: World, detective: Entity, helper: Entity, suspect: Entity) -> None:
    helper.memes["frustration"] = helper.memes.get("frustration", 0.0) + 1
    world.say(
        f"{helper.id} frowned harder when the hatch creaked and the {suspect.label} slid by below."
    )
    world.say(
        f"{detective.id} kneelt by the hook and noticed one more thing: a tiny scratch where the key had hung."
    )
    clue = find_clue(world, "tiny_scratches", detective)
    if clue:
        world.say(clue)


def reveal(world: World, detective: Entity, helper: Entity, missing: Entity, suspect: Entity) -> None:
    solution = infer_solution(world)
    world.solution = solution

    if solution == "visitor":
        world.say(
            f"{detective.id} smiled and said the visitor had taken the key with a pocket tool, then left the hatch open."
        )
        world.say(
            f"The moray eel only nudged the hatch after that, because it liked the bright draft from the room."
        )
        world.say(
            f"{helper.id} blinked, then apologized to the moray eel for blaming {suspect.it()} too soon."
        )
    elif solution == "moray":
        world.say(
            f"{detective.id} pointed to the open hatch and said the moray eel had tugged the latch while chasing bubbles."
        )
        world.say(
            f"The key had slipped into the drain cup below, where the eel could not reach it again."
        )
        world.say(
            f"{helper.id} softened at once, because the eel was curious, not sneaky."
        )
    else:
        world.say(
            f"{detective.id} was not ready to guess, so the search continued until the clues made a full picture."
        )

    helper.memes["worry"] = 0.0
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    detective.memes["pride"] = detective.memes.get("pride", 0.0) + 1
    world.say(
        f"In the end, the {missing.label} was found in the locker tray, and the room felt peaceful again."
    )


# ---------------------------------------------------------------------------
# World build
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    loc = LOCATIONS[params.place]
    world = World(loc)
    world.weather = "foggy"
    detective = world.add(
        Entity(
            id=params.detective_name,
            kind="character",
            type=params.detective_type,
            label="detective",
            phrase="the detective",
            room="hallway",
            meters={"seen": 1.0},
            memes={"focus": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_type,
            label="helper",
            phrase="the helper",
            room="tank_room",
            meters={"seen": 1.0},
            memes={"worry": 1.0},
        )
    )
    missing = world.add(
        Entity(
            id=params.missing,
            kind="thing",
            type="thing",
            label=params.missing.replace("_", " "),
            phrase=MISSING_ITEMS[params.missing].phrase,
            room="unknown",
            owner=helper.id,
            caretaker=helper.id,
            meters={"hidden": 1.0},
        )
    )
    suspect = world.add(
        Entity(
            id=params.suspect,
            kind=SUSPECTS[params.suspect].kind,
            type=SUSPECTS[params.suspect].type,
            label=SUSPECTS[params.suspect].label,
            phrase=SUSPECTS[params.suspect].phrase,
            room="tank_room" if params.suspect == "moray" else "dock",
            meters={"seen": 1.0},
            memes={"suspicion": 0.0},
        )
    )
    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        suspect=suspect,
        location=loc,
    )
    return world


def tell(world: World) -> World:
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    missing = world.facts["missing"]
    suspect = world.facts["suspect"]

    world.say(story_day(world.location) + world.location.atmosphere)
    introduce(world, detective, helper, missing, suspect)
    world.para()
    start_conflict(world, detective, helper, suspect)
    search(world, detective, helper)
    world.para()
    tighten_conflict(world, detective, helper, suspect)
    reveal(world, detective, helper, missing, suspect)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts_for(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    missing = f["missing"]
    suspect = f["suspect"]
    return [
        f'Write a short whodunit for a child about a missing {missing.label} at {world.location.label}, with a clue-based answer.',
        f"Tell a gentle mystery where {detective.id} and {helper.id} disagree about whether the {suspect.label} caused the trouble.",
        f"Write a simple detective story that includes {detective.id}, a moray eel, and the discovery of a hidden clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    missing = f["missing"]
    suspect = f["suspect"]
    return [
        QAItem(
            question=f"What was missing at {world.location.label}?",
            answer=f"The missing thing was {missing.phrase}.",
        ),
        QAItem(
            question=f"Who did {helper.id} blame at first?",
            answer=f"{helper.id} blamed the {suspect.label} at first because it was the first strange thing the two of them noticed.",
        ),
        QAItem(
            question=f"Why did {detective.id} not agree right away?",
            answer=f"{detective.id} wanted proof from the clues before naming the culprit.",
        ),
        QAItem(
            question="What clue helped explain the mystery?",
            answer="The wet bootprints, the open hatch, the salt ribbon, and the tiny scratches all fit together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "moray": [
        QAItem(
            question="What is a moray eel?",
            answer="A moray eel is a long, snake-like fish that lives in the sea and hides in rocky places.",
        ),
        QAItem(
            question="Why might a moray eel hide in a hole?",
            answer="A moray eel hides in a hole to feel safe and watch for food.",
        ),
    ],
    "gay": [
        QAItem(
            question="What can the word gay mean?",
            answer="The word gay can mean happy and bright, though it can also be used as a word for some people's identity.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
    ],
    "whodunit": [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who caused the trouble.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = {world.facts["suspect"].id, "clue", "whodunit", "gay"}
    out: list[QAItem] = []
    for key in ["whodunit", "clue", "moray", "gay"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is valid when the missing item, location, and suspect fit the
% small domain's logic.

mystery(place(P), missing(M), suspect(S)) :- place(P), missing_item(M), suspect(S),
    supports(P, M), supports(P, S).

% The moray is a plausible suspect in the pier aquarium because it can nudge
% latches and live near the hatch.
plausible_suspect(moray) :- suspect(moray), supports(pier, eel_silence).

% A story is reasoned as a whodunit if there is a conflict and a clue chain.
whodunit(P, M, S) :- mystery(place(P), missing(M), suspect(S)),
    conflict(P, M, S), clue_chain(P, M, S).

#show whodunit/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, loc in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        for sup in sorted(loc.supports):
            lines.append(asp.fact("supports", pid, sup))
    for mid in MISSING_ITEMS:
        lines.append(asp.fact("missing_item", mid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("conflict", "pier", "key", "moray"))
    lines.append(asp.fact("clue_chain", "pier", "key", "moray"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_candidates() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show whodunit/3."))
    return sorted(set(asp.atoms(model, "whodunit")))


def verify_asp() -> int:
    candidates = set(asp_candidates())
    python_candidates = {("pier", "key", "moray")}
    if candidates == python_candidates:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("  ASP:", sorted(candidates))
    print("  Python:", sorted(python_candidates))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in LOCATIONS:
        for missing in MISSING_ITEMS:
            for suspect in SUSPECTS:
                if place == "pier" and missing == "key" and suspect == "moray":
                    combos.append((place, missing, suspect))
    return combos


def explain_rejection(place: str, missing: str, suspect: str) -> str:
    return (
        f"(No story: this whodunit only works at the pier with the brass key and the moray eel. "
        f"The clues are built around a hatch, wet bootprints, and a tank-room mystery.)"
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit storyworld about a missing key, a conflict, and a moray eel."
    )
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--missing", choices=MISSING_ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
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
    place = args.place or "pier"
    missing = args.missing or "key"
    suspect = args.suspect or "moray"
    if (place, missing, suspect) not in valid_combos():
        raise StoryError(explain_rejection(place, missing, suspect))
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    detective_type = args.detective_type or rng.choice(["girl", "boy", "woman", "man"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "woman", "man"])
    return StoryParams(
        place=place,
        missing=missing,
        suspect=suspect,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.room:
            parts.append(f"room={e.room}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(parts)}")
    lines.append(f"  clues found: {world.clues_found}")
    lines.append(f"  solution: {world.solution}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show whodunit/3."))
    return sorted(set(asp.atoms(model, "whodunit")))


def asp_verify() -> int:
    import asp
    asp_set = set(asp_valid_stories())
    py_set = {("pier", "key", "moray")}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py_set)} combo).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in ASP:", sorted(asp_set - py_set))
    print("  only in Python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show whodunit/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible whodunit(s):")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [StoryParams(place="pier", missing="key", suspect="moray",
                                   detective_name="Gay", detective_type="woman",
                                   helper_name="Pip", helper_type="boy")]
    else:
        params_list = []
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 20):
            if len(params_list) >= max(args.n, 1):
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params_list.append(params)

    samples = [generate(p) for p in params_list]

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
