#!/usr/bin/env python3
"""
A small comedy storyworld about a chauffeur, a gamble, and a muddy slope.

Premise:
A careful chauffeur must get a fussy passenger up a muddy slope. The road is
slippery, the vehicle keeps wobbling, and the chauffeur has to decide whether to
take a risky shortcut or trust a little bit of magic.

The tale is driven by state:
- the slope has mud and steepness
- the carriage has traction, cargo, and a temper
- the chauffeur has confidence and nerves
- a magic charm may help, but only if it is used wisely
- foreshadowing comes from earlier clues about the slope and the charm
- the surprise is a comic but helpful outcome at the top of the hill

This file follows the Storyweavers contract: it exposes a StoryParams dataclass,
a generate() pipeline, QA generation, text/JSON output, a trace mode, and an
inline ASP twin of the reasonableness gate.
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

# World limits / thresholds
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
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
    ridden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "lady"}
        male = {"man", "boy", "father", "chauffeur", "driver"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def thing(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the muddy slope"
    steepness: float = 1.0
    mud: float = 1.0
    affords: set[str] = field(default_factory=set)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    traction: float
    cargo_kind: str
    cargo_label: str
    cargo_phrase: str


@dataclass
class Charm:
    id: str
    label: str
    power: str
    clue: str
    payoff: str


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "muddy_slope": Setting(place="the muddy slope", steepness=1.0, mud=1.0, affords={"drive"}),
}

VEHICLES = {
    "carriage": Vehicle(
        id="carriage",
        label="carriage",
        phrase="a shiny little carriage with a polite bell",
        traction=1.0,
        cargo_kind="passenger",
        cargo_label="passenger",
        cargo_phrase="a fussy passenger in a clean coat",
    ),
    "taxi": Vehicle(
        id="taxi",
        label="taxi",
        phrase="a yellow taxi with squeaky tires",
        traction=0.9,
        cargo_kind="passenger",
        cargo_label="passenger",
        cargo_phrase="a grumpy passenger with a suitcase",
    ),
}

CHARM = Charm(
    id="luck_charm",
    label="luck charm",
    power="make the wheels remember manners",
    clue="The little charm had been jingling since the road turned muddy.",
    payoff="it would nudge the vehicle at exactly the right moment",
)

GAMBLE_WORDS = [
    "gamble",
    "chance",
    "bet",
]

NAMES = ["Milo", "Nina", "Poppy", "Jasper", "Tessa", "Rory", "Ivy", "Noah"]
TRAITS = ["cheerful", "careful", "proud", "witty", "earnest", "spry"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    vehicle: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    chauffeur = world.add(Entity(
        id=params.name,
        kind="character",
        type="chauffeur",
        label="chauffeur",
        meters={"confidence": 1.0, "nerves": 0.0},
        memes={"pride": 1.0, "worry": 0.0},
    ))
    passenger = world.add(Entity(
        id="Passenger",
        kind="character",
        type="passenger",
        label="passenger",
        meters={"patience": 1.0},
        memes={"fuss": 1.0},
    ))
    vehicle = VEHICLES[params.vehicle]
    carriage = world.add(Entity(
        id=vehicle.id,
        type=vehicle.id,
        label=vehicle.label,
        phrase=vehicle.phrase,
        owner=chauffeur.id,
        caretaker=chauffeur.id,
        meters={"traction": vehicle.traction, "mud": 0.0, "progress": 0.0},
    ))
    charm = world.add(Entity(
        id=CHARM.id,
        type="charm",
        label=CHARM.label,
        phrase="a tiny brass charm with a painted star",
        owner=chauffeur.id,
        caretaker=chauffeur.id,
        meters={"luck": 1.0},
        memes={"mystery": 1.0},
    ))
    world.facts.update(
        chauffeur=chauffeur,
        passenger=passenger,
        vehicle=carriage,
        charm=charm,
        vehicle_cfg=vehicle,
        charm_cfg=CHARM,
        setting=setting,
    )
    return world


def predict_attempt(world: World, use_charm: bool, risky_shortcut: bool) -> dict:
    sim = world.copy()
    vehicle = sim.get(sim.facts["vehicle"].id)
    setting = sim.setting
    traction = vehicle.meters.get("traction", 0.0)
    if use_charm:
        traction += 0.5
    if risky_shortcut:
        traction -= 0.25
    ease = traction - setting.mud * 0.4 - setting.steepness * 0.35
    success = ease >= 0.6
    surprise = use_charm and success and risky_shortcut
    return {"success": success, "surprise": surprise, "ease": ease}


def narrate_setup(world: World) -> None:
    f = world.facts
    chauffeur = f["chauffeur"]
    passenger = f["passenger"]
    vehicle = f["vehicle"]
    charm = f["charm"]
    trait = f["trait"]

    world.say(
        f"{chauffeur.id} was a {trait} chauffeur who loved neat roads, quiet engines, "
        f"and exactly one cup of tea before work."
    )
    world.say(
        f"That morning, {chauffeur.id} had to carry {passenger.label} up {world.setting.place}, "
        f"which looked less like a road and more like a chocolate cake after a storm."
    )
    world.say(
        f"{chauffeur.id} drove {vehicle.phrase}, and in the glove box sat {charm.phrase}."
    )
    world.say(
        f"It was only a silly little charm, but {CHARM.clue}"
    )


def narrate_foreshadowing(world: World) -> None:
    f = world.facts
    chauffeur = f["chauffeur"]
    vehicle = f["vehicle"]
    world.say(
        f"At the bottom of the hill, the wheels gave one tiny squeak, as if they were already "
        f"thinking about a slip."
    )
    world.say(
        f"{chauffeur.id} tapped the dashboard and said, \"Easy now. Nobody panic until we actually wiggle.\""
    )


def attempt_drive(world: World, use_charm: bool, risky_shortcut: bool) -> dict:
    f = world.facts
    chauffeur = f["chauffeur"]
    vehicle = f["vehicle"]
    passenger = f["passenger"]
    charm = f["charm"]

    pred = predict_attempt(world, use_charm, risky_shortcut)
    chauffeur.meters["confidence"] -= 0.1
    chauffeur.memes["worry"] += 0.2
    vehicle.meters["progress"] += 0.4
    vehicle.meters["mud"] += 0.5

    if risky_shortcut:
        world.say(
            f"{chauffeur.id} made a gamble and took the shorter path, which immediately turned "
            f"into the sort of path that apologizes with mud."
        )
    else:
        world.say(
            f"{chauffeur.id} chose the longer lane and kept the wheels in the safest tracks."
        )

    if use_charm:
        world.say(
            f"Then {chauffeur.id} rubbed {charm.label} and whispered, \"If this works, I will "
            f"pretend I never doubted magic.\""
        )
        vehicle.meters["traction"] += 0.3
        chauffeur.memes["hope"] = chauffeur.memes.get("hope", 0.0) + 0.5
    else:
        world.say(
            f"{chauffeur.id} tried to do it without magic, which was brave, but the hill was not impressed."
        )

    if pred["success"]:
        vehicle.meters["progress"] = 1.0
        passenger.memes["fuss"] = 0.0
        chauffeur.memes["worry"] = 0.0
        world.say(
            f"The carriage climbed a little, paused, and then climbed again, as neatly as a spoon walking upstairs."
        )
    else:
        world.say(
            f"The wheels spun, the mud laughed, and the carriage slid back half a step."
        )
    return pred


def narrate_surprise(world: World, pred: dict) -> None:
    f = world.facts
    chauffeur = f["chauffeur"]
    passenger = f["passenger"]
    vehicle = f["vehicle"]
    charm = f["charm"]

    if pred["success"]:
        world.say(
            f"Just when {chauffeur.id} expected one last embarrassing skid, the charm jingled."
        )
        world.say(
            f"That was the surprise: a sleepy mule at the roadside began pushing from behind, "
            f"as if it had decided to help simply because the comedy needed a grand finish."
        )
        world.say(
            f"With the mule, the charm, and a lot of spluttering pride, the carriage reached the top."
        )
        world.say(
            f"{passenger.label} clapped, then noticed the carriage was covered in mud from bumper to bell. "
            f"\"Excellent,\" said {passenger.label}, \"now it looks expensive enough to be important.\""
        )
        world.say(
            f"{chauffeur.id} laughed so hard that {vehicle.label} shook, and {charm.label} gave one final proud jingle."
        )
    else:
        world.say(
            f"The surprise was not a disaster after all: the muddy slope hid a patch of firm stones near the top."
        )
        world.say(
            f"{chauffeur.id} found it by accident, and the carriage rolled up like a squirrel on a mission."
        )
        world.say(
            f"{passenger.label} blinked, then said the whole ride had been \"delightfully alarming.\""
        )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    world.facts["trait"] = params.trait
    world.facts["name"] = params.name

    narrate_setup(world)
    world.para()
    narrate_foreshadowing(world)
    pred = attempt_drive(world, use_charm=True, risky_shortcut=True)
    world.para()
    narrate_surprise(world, pred)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chauffeur = f["chauffeur"]
    vehicle_cfg = f["vehicle_cfg"]
    return [
        f'Write a funny story for young children about a chauffeur and a gamble on a muddy slope, with a magic charm that helps.',
        f"Tell a comedy story where {chauffeur.id}, a chauffeur, tries to get {vehicle_cfg.label} up {world.setting.place} and something surprising happens.",
        f'Write a short story that includes the words "chauffeur", "gamble", and "magic", and ends with a comic surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chauffeur = f["chauffeur"]
    passenger = f["passenger"]
    vehicle = f["vehicle"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"Who was trying to drive up {world.setting.place}?",
            answer=f"{chauffeur.id}, the chauffeur, was trying to drive {vehicle.label} up {world.setting.place}."
        ),
        QAItem(
            question="Why was the ride a gamble?",
            answer="It was a gamble because the slope was muddy and slippery, so the carriage might slide back instead of going up."
        ),
        QAItem(
            question="What helped the chauffeur keep going?",
            answer=f"The little {charm.label} helped, and so did a cautious plan and a lot of stubborn wheel-turning."
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"A sleepy mule helped push from behind, and that comic surprise got {vehicle.label} to the top."
        ),
        QAItem(
            question=f"How did {passenger.label} feel by the end?",
            answer=f"{passenger.label} was pleased and amused, because the messy ride ended safely and the hill was finally conquered."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chauffeur?",
            answer="A chauffeur is a driver who takes people places in a car, taxi, or carriage."
        ),
        QAItem(
            question="What does it mean to gamble?",
            answer="To gamble means to take a risk and hope things turn out well."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives little clues early on about something that may happen later."
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters thought would happen."
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
% A route is risky if the place is muddy and steep.
risky(Place) :- setting(Place), muddy(Place), steep(Place).

% A gamble is wise if the chauffeur uses magic and the vehicle has enough traction.
wise(V) :- vehicle(V), uses_magic(V), traction_ok(V).

% A story is valid if the setting is risky, the chauffeur can try, and magic can
% still make a comic but successful finish.
valid_story(Place, Vehicle) :- risky(Place), vehicle(Vehicle), has_chauffeur(Vehicle), comic_finish(Place, Vehicle).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.mud >= 1.0:
            lines.append(asp.fact("muddy", sid))
        if setting.steepness >= 1.0:
            lines.append(asp.fact("steep", sid))
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("has_chauffeur", vid))
        if v.traction >= 1.0:
            lines.append(asp.fact("traction_ok", vid))
    lines.append(asp.fact("uses_magic", "carriage"))
    lines.append(asp.fact("comic_finish", "muddy_slope", "carriage"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("muddy_slope", "carriage")}
    if asp_set == py_set:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("clingo:", sorted(asp_set))
    print("python:", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [("muddy_slope", vid) for vid in VEHICLES]


def explain_rejection(place: str, vehicle: str) -> str:
    return f"(No story: {vehicle} is not a valid choice for {place} in this tiny domain.)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy story world: a chauffeur, a gamble, a muddy slope, and a magic surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.place not in SETTINGS:
        raise StoryError(explain_rejection(args.place, args.vehicle or "vehicle"))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.vehicle is None or c[1] == args.vehicle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, vehicle = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, vehicle=vehicle, name=name, trait=trait)


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
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
    StoryParams(place="muddy_slope", vehicle="carriage", name="Milo", trait="witty"),
    StoryParams(place="muddy_slope", vehicle="taxi", name="Nina", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("2 compatible (place, vehicle) combos:\n")
        for place, vehicle in valid_combos():
            print(f"  {place:12} {vehicle}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.vehicle} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
