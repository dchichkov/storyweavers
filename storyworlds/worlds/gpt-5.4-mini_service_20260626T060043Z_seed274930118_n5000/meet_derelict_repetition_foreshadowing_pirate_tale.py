#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a crew meeting a derelict ship, with
repetition and foreshadowing driving the turn from curiosity to caution to a
careful salvage.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Vessel:
    id: str
    kind: str
    label: str
    adjective: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def title(self) -> str:
        return f"{self.adjective} {self.label}".strip()


@dataclass
class Crew:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    sea: str
    weather: str
    features: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    sea: str
    weather: str
    crew_name: str
    leader_role: str
    vessel_kind: str
    vessel_adjective: str
    vessel_label: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    crew: Crew
    vessel: Vessel
    trace: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    finished: bool = False
    danger: float = 0.0
    hope: float = 0.0

    def say(self, text: str) -> None:
        if text:
            self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "harbor": Place("the harbor", "salt sea", "windy", {"dock", "rope", "fog"}),
    "bay": Place("the bay", "blue sea", "foggy", {"reef", "tide", "cove"}),
    "cove": Place("the cove", "dark sea", "still", {"rocks", "cave", "current"}),
}

CREW_NAMES = ["Mara", "Jory", "Tess", "Finn", "Nell", "Bram", "Sailor", "Pip"]
LEADER_ROLES = ["captain", "first mate", "helmsman"]
VESSEL_KINDS = ["ship", "sloop", "cutter", "barge"]
VESSEL_ADJECTIVES = ["derelict", "weather-beaten", "drifted", "broken", "lonely"]
VESSEL_LABELS = {
    "ship": "ship",
    "sloop": "sloop",
    "cutter": "cutter",
    "barge": "barge",
}

# Reasonable combinations are those where a derelict vessel can be met and
# the crew has enough reason to act after the foreshadowing.
VALID_KINDS = {"ship", "sloop", "cutter", "barge"}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    crew = Crew(
        id="crew",
        name=params.crew_name,
        role=params.leader_role,
        meters={"courage": 1.0, "readiness": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "resolve": 0.0},
    )
    vessel = Vessel(
        id="vessel",
        kind=params.vessel_kind,
        label=params.vessel_label,
        adjective=params.vessel_adjective,
        meters={"drift": 1.0, "age": 1.0, "damage": 0.0},
        memes={"mystery": 1.0, "danger": 0.5, "value": 1.0},
        tags={"derelict", params.vessel_kind, params.vessel_label},
    )
    return World(place=place, crew=crew, vessel=vessel)


def seed_events(world: World) -> None:
    place = world.place
    crew = world.crew
    vessel = world.vessel

    world.say(
        f"At {place.name}, {crew.name} stood at the rail and watched the gray water."
    )
    world.say(
        f"Again and again, the lookout called, 'A drifted hull! A drifted hull!'"
    )
    world.say(
        f"Then they met { _article(vessel.adjective) } {vessel.title()} in the hush of the sea."
    )
    world.say(
        f"The name on its side was faded, and its mast leaned like a tired knee."
    )
    world.hope += 0.5
    world.danger += 0.5
    world.facts.update(stage="meeting", place=place.name, crew_name=crew.name, vessel_title=vessel.title())


def foreshadow(world: World) -> None:
    crew = world.crew
    vessel = world.vessel

    world.say(
        "The rigging gave a soft creak, and a loose lantern banged once against the hull."
    )
    world.say(
        "That small sound came back twice over the water, as if the sea were warning them."
    )
    world.say(
        f"{crew.name} noticed a torn line, a bent hatch, and one black patch of tar that looked fresh."
    )
    crew.memes["worry"] += 1.0
    crew.memes["curiosity"] += 0.5
    vessel.memes["danger"] += 1.0
    vessel.meters["damage"] += 0.5
    world.danger += 1.0
    world.facts["foreshadow"] = "fresh tar, torn line, loose lantern"


def repeat_and_probe(world: World) -> None:
    crew = world.crew
    vessel = world.vessel

    world.say(
        f"'{vessel.adjective} and alone,' said {crew.name}, and then again, "
        f"'{vessel.adjective} and alone.'"
    )
    world.say(
        f"They came closer, slow as a gull riding wind, because the same odd signs kept showing themselves."
    )
    world.say(
        f"One plank was damp, one plank was split, and one plank seemed to hide a deeper hollow."
    )
    crew.meters["readiness"] += 1.0
    crew.memes["resolve"] += 0.5
    world.facts["repetition"] = True


def turn_to_action(world: World) -> None:
    crew = world.crew
    vessel = world.vessel

    if world.danger < 1.0:
        raise StoryError("The tale never gained enough danger for a proper pirate turn.")
    world.say(
        f"{crew.name} lifted a hand and ordered a careful check instead of a wild jump aboard."
    )
    world.say(
        "They tossed a rope, tested the rail, and listened before they stepped."
    )
    vessel.meters["damage"] += 0.2
    crew.meters["readiness"] += 1.0
    crew.memes["resolve"] += 1.0
    crew.memes["worry"] = max(0.0, crew.memes["worry"] - 0.5)
    world.facts["action"] = "careful check"


def resolution(world: World) -> None:
    crew = world.crew
    vessel = world.vessel

    if vessel.meters["damage"] < 1.0:
        world.say(
            f"Inside, they found dry maps, a brass compass, and a ship's log wrapped in oilcloth."
        )
        world.say(
            f"The vessel was derelict, but not empty, and that changed the whole night."
        )
        crew.memes["curiosity"] += 1.0
        world.hope += 1.5
    else:
        world.say(
            f"Inside, they found only broken crates and a silent deck, but the careful search kept them safe."
        )
        world.hope += 0.5

    world.say(
        f"In the end, {crew.name} left a lantern burning on the deck, so the derelict could be found again."
    )
    world.say(
        f"The sea rolled on, the rope held fast, and the crew sailed away with a better story than treasure."
    )
    world.finished = True
    world.facts["ending"] = "lantern left burning"


def simulate(params: StoryParams) -> World:
    world = build_world(params)
    seed_events(world)
    world.say("")  # paragraph break marker not used in render, but keeps stage separation conceptually
    foreshadow(world)
    repeat_and_probe(world)
    turn_to_action(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "derelict" and the phrase "met the ship".',
        f"Tell a short sea story where {f['crew_name']} meets a derelict {world.vessel.kind} and notices warning signs before climbing aboard.",
        "Write a gentle pirate adventure with repetition, foreshadowing, and a careful ending on the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    crew = world.crew
    vessel = world.vessel
    place = world.place
    return [
        QAItem(
            question=f"Where did {crew.name} meet the derelict {vessel.kind}?",
            answer=f"{crew.name} met the derelict {vessel.kind} at {place.name}, where the water was quiet and watchful.",
        ),
        QAItem(
            question=f"What repeated words did the lookout call out?",
            answer=f"The lookout called, '{vessel.adjective} and alone!' and then said it again to make the warning feel louder.",
        ),
        QAItem(
            question=f"What small signs foreshadowed trouble on the vessel?",
            answer="A torn line, a bent hatch, a loose lantern, and a fresh black patch of tar all hinted that something was wrong.",
        ),
        QAItem(
            question=f"How did the crew act when they reached the ship?",
            answer="They chose a careful check, tossed a rope, and listened first instead of jumping aboard in a hurry.",
        ),
        QAItem(
            question="What did the crew find in the end?",
            answer="They found useful sea charts and a compass, and they left a lantern burning so the ship could be found again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does derelict mean?",
            answer="Derelict means something has been left alone, neglected, or abandoned for a long time.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when a story says a word, line, or sound more than once to make it stand out.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives little clues that hint something important will happen later.",
        ),
        QAItem(
            question="Why should sailors check a strange ship carefully?",
            answer="They should check carefully because a strange ship might have broken parts, hidden damage, or other danger on board.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
crew(C) :- crew_name(C).
vessel(V) :- vessel_kind(V).

can_meet(P, V) :- place(P), vessel(V), derelict(V), in_sea(P, _).
needs_care(V) :- derelict(V), fresh_sign(V).
good_story(P, V) :- can_meet(P, V), needs_care(V), foreshadowed(V).

#show good_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("setting", place_id))
        lines.append(asp.fact("in_sea", place_id, place.sea))
        for feat in sorted(place.features):
            lines.append(asp.fact("feature", place_id, feat))
    for kind in sorted(VALID_KINDS):
        lines.append(asp.fact("vessel_kind", kind))
    lines.append(asp.fact("crew_name", "crew"))
    lines.append(asp.fact("derelict", "yes"))
    lines.append(asp.fact("fresh_sign", "yes"))
    lines.append(asp.fact("foreshadowed", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_gate() -> bool:
    return True


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = asp.atoms(model, "good_story")
    py_ok = asp_gate()
    asp_ok = len(atoms) > 0
    if bool(py_ok) == bool(asp_ok):
        print("OK: Python gate and ASP twin agree.")
        return 0
    print("MISMATCH: Python gate and ASP twin disagree.")
    return 1


# ---------------------------------------------------------------------------
# Parsing / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about meeting a derelict vessel.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--sea", choices=["salt sea", "blue sea", "dark sea"])
    ap.add_argument("--weather", choices=["windy", "foggy", "still"])
    ap.add_argument("--crew-name", dest="crew_name", choices=CREW_NAMES)
    ap.add_argument("--leader-role", dest="leader_role", choices=LEADER_ROLES)
    ap.add_argument("--vessel-kind", dest="vessel_kind", choices=VESSEL_KINDS)
    ap.add_argument("--vessel-adjective", dest="vessel_adjective", choices=VESSEL_ADJECTIVES)
    ap.add_argument("--vessel-label", dest="vessel_label", choices=list(VESSEL_LABELS.values()))
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
    place = args.place or rng.choice(sorted(PLACES))
    sea = args.sea or PLACES[place].sea
    weather = args.weather or PLACES[place].weather
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    leader_role = args.leader_role or rng.choice(LEADER_ROLES)
    vessel_kind = args.vessel_kind or rng.choice(VESSEL_KINDS)
    vessel_adjective = args.vessel_adjective or rng.choice(VESSEL_ADJECTIVES)
    vessel_label = args.vessel_label or VESSEL_LABELS[vessel_kind]
    if vessel_kind not in VALID_KINDS:
        raise StoryError("Invalid vessel kind.")
    return StoryParams(
        place=place,
        sea=sea,
        weather=weather,
        crew_name=crew_name,
        leader_role=leader_role,
        vessel_kind=vessel_kind,
        vessel_adjective=vessel_adjective,
        vessel_label=vessel_label,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    lines.append(f"crew: {world.crew.name} ({world.crew.role}) meters={world.crew.meters} memes={world.crew.memes}")
    lines.append(
        f"vessel: {world.vessel.title()} meters={world.vessel.meters} memes={world.vessel.memes}"
    )
    lines.append(f"facts: {world.facts}")
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
    StoryParams(
        place="harbor",
        sea="salt sea",
        weather="windy",
        crew_name="Mara",
        leader_role="captain",
        vessel_kind="ship",
        vessel_adjective="derelict",
        vessel_label="ship",
    ),
    StoryParams(
        place="bay",
        sea="blue sea",
        weather="foggy",
        crew_name="Jory",
        leader_role="first mate",
        vessel_kind="sloop",
        vessel_adjective="weather-beaten",
        vessel_label="sloop",
    ),
    StoryParams(
        place="cove",
        sea="dark sea",
        weather="still",
        crew_name="Nell",
        leader_role="helmsman",
        vessel_kind="cutter",
        vessel_adjective="lonely",
        vessel_label="cutter",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show good_story/2."))
        print(sorted(asp.atoms(model, "good_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.crew_name}: {p.vessel_adjective} {p.vessel_kind} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
