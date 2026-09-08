#!/usr/bin/env python3
"""
A standalone fairy-tale story world about hearing a warning, a speedometer,
and crossing a dangerous enchanted road through repetition and courage.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


TRAVELERS = ["Luna", "Mira", "Pip", "Elian", "Nessa", "Tavi"]
GUIDES = ["the moon fox", "Grandmother Willow", "the silver owl", "the old ferryman"]
ROADS = ["Whispering Road", "Moonbeam Lane", "the Briar Crossing", "Starfall Path"]
VEHICLES = ["a pumpkin coach", "a little blue cart", "a brass carriage", "a red wagon"]
CHARMS = ["a bell charm", "a silver ribbon", "a lantern bead", "a glass feather"]
TRAITS = ["curious", "brave", "patient", "kind", "quick-thinking"]
WEATHERS = ["a violet mist", "a cold starlit wind", "a shower of silver leaves", "a hush before dawn"]

TALES = [
    {
        "id": "sleeping_speed",
        "danger": "the coach's speedometer began climbing even though the driver had not touched the reins",
        "warning": "a tiny bell beneath the dashboard rang three times",
        "clue": "the needle pointed toward the dark bridge rather than toward the road ahead",
        "conflict": "the coachman insisted that the fastest road was the only road worth taking",
        "safe_plan": "stop before the bridge, listen for the bell, and cross only when the needle rested at zero",
        "turn": "Luna heard a second bell from below the bridge and realized that the river was hiding a broken gate",
        "resolution": "the moon fox closed the gate while Luna guided the coach along the dry stepping stones",
        "ending": "the speedometer settled at zero, and the coach rolled beneath a sky full of quiet stars",
    },
    {
        "id": "thorny_meter",
        "danger": "the speedometer glowed red as thorn vines pulled the wagon toward a narrow forest crossing",
        "warning": "the wagon wheels began spinning although the path was blocked",
        "clue": "the red needle trembled whenever the vines whispered Luna's name",
        "conflict": "a proud forest knight said that no fairy-tale traveler should fear a few thorns",
        "safe_plan": "repeat the warning, keep the wheels still, and cross only after the vines loosened",
        "turn": "Luna heard the vines repeat the knight's boast, so she knew the thorns were copying careless words",
        "resolution": "she answered with the same calm warning until the vines grew tired and released the wagon",
        "ending": "green leaves folded into a little crown around the quiet speedometer",
    },
    {
        "id": "silver_rush",
        "danger": "a silver road appeared across the marsh, and the carriage speedometer urged everyone to rush across",
        "warning": "the needle jumped whenever anyone looked at the glittering water",
        "clue": "Luna could hear frogs calling from only the safe stones, never from the shining road",
        "conflict": "the carriage guard wanted to cross first and prove that the road was real",
        "safe_plan": "repeat the frog call, test one stone at a time, and turn back whenever the sound disappeared",
        "turn": "the frogs answered Luna's repeated call from a hidden path behind the reeds",
        "resolution": "the travelers crossed by following the living sounds instead of the tempting silver road",
        "ending": "the false road melted into moonlight while muddy footprints marked the true way home",
    },
]

OPENINGS = [
    "At the edge of the moonlit kingdom,",
    "Long ago, when roads could whisper,",
    "One evening beneath a purple moon,",
    "Beyond the last golden village,",
]

REPETITIONS = [
    "Hear first, check twice, cross last.",
    "Stop the wheels, listen well, choose the safe way.",
    "No rushing, no guessing, one careful crossing.",
    "Hear the warning, say the plan, follow it together.",
]


@dataclass
class Traveler:
    name: str
    trait: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Guide:
    name: str
    wisdom: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    traveler: Traveler
    guide: Guide
    road: str
    vehicle: str
    charm: str
    weather: str
    tale: dict
    refrain: str
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.facts.setdefault("lines", []).append(text)

    def render(self) -> str:
        return " ".join(self.facts.get("lines", []))


@dataclass
class StoryParams:
    traveler: str
    guide: str
    road: str
    vehicle: str
    charm: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale world of hearing a speedometer warning before crossing."
    )
    parser.add_argument("--traveler", choices=TRAVELERS)
    parser.add_argument("--guide", choices=GUIDES)
    parser.add_argument("--road", choices=ROADS)
    parser.add_argument("--vehicle", choices=VEHICLES)
    parser.add_argument("--charm", choices=CHARMS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_combo(params: StoryParams) -> bool:
    return (
        params.traveler in TRAVELERS
        and params.guide in GUIDES
        and params.road in ROADS
        and params.vehicle in VEHICLES
        and params.charm in CHARMS
        and params.trait in TRAITS
    )


def asp_facts() -> str:
    import asp

    lines = []
    for name in TRAVELERS:
        lines.append(asp.fact("traveler", name))
    for name in GUIDES:
        lines.append(asp.fact("guide", name))
    for name in ROADS:
        lines.append(asp.fact("road", name))
    for name in VEHICLES:
        lines.append(asp.fact("vehicle", name))
    for name in CHARMS:
        lines.append(asp.fact("charm", name))
    for name in TRAITS:
        lines.append(asp.fact("trait", name))
    return "\n".join(lines)


ASP_RULES = r"""
choice(T,R,V,G,C,Trait) :- traveler(T), road(R), vehicle(V), guide(G), charm(C), trait(Trait).
hears_warning(T) :- choice(T,_,_,_,_,_).
uses_speedometer(V) :- vehicle(V).
may_cross(R) :- road(R).
valid(T,R,V,G,C,Trait) :-
    choice(T,R,V,G,C,Trait),
    hears_warning(T),
    uses_speedometer(V),
    may_cross(R).
#show valid/6.
"""


def asp_program(show: str = "#show valid/6.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_values = {
        (traveler, road, vehicle, guide, charm, trait)
        for traveler in TRAVELERS
        for road in ROADS
        for vehicle in VEHICLES
        for guide in GUIDES
        for charm in CHARMS
        for trait in TRAITS
        if valid_combo(StoryParams(traveler, guide, road, vehicle, charm, trait))
    }
    clingo_values = asp_valid()
    if python_values == clingo_values:
        print(f"OK: clingo gate matches Python ({len(clingo_values)} combinations).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_values - python_values))
    print("only in Python:", sorted(python_values - clingo_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        traveler=args.traveler or rng.choice(TRAVELERS),
        guide=args.guide or rng.choice(GUIDES),
        road=args.road or rng.choice(ROADS),
        vehicle=args.vehicle or rng.choice(VEHICLES),
        charm=args.charm or rng.choice(CHARMS),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The selected fairy-tale characters or travel objects are invalid.")
    return params


def make_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__str__())))
    rng = random.Random(seed)
    traveler = Traveler(
        name=params.traveler,
        trait=params.trait,
        meters={"distance": 0.0, "danger": 1.0},
        memes={"courage": 1.0, "attention": 0.0, "trust": 0.0},
    )
    guide = Guide(
        name=params.guide,
        wisdom="listens before choosing",
        memes={"patience": 1.0, "wisdom": 1.0},
    )
    return World(
        traveler=traveler,
        guide=guide,
        road=params.road,
        vehicle=params.vehicle,
        charm=params.charm,
        weather=rng.choice(WEATHERS),
        tale=rng.choice(TALES),
        refrain=rng.choice(REPETITIONS),
    )


def generate_story(world: World) -> None:
    traveler = world.traveler
    guide = world.guide
    tale = world.tale

    world.say(
        f"{world.facts.get('opening', 'Long ago,')} {traveler.name}, a {traveler.trait} traveler, "
        f"reached {world.road} in {world.weather} with {world.vehicle}."
    )
    world.say(
        f"A small {world.charm} shone beside the dashboard, but {tale['danger']}."
    )
    world.say(f"{tale['warning'].capitalize()} {traveler.name} gripped the reins.")
    traveler.memes["attention"] += 1

    world.say(
        f'"Do we cross?" asked {traveler.name}. '
        f'"Not yet," answered {guide.name}. "Tell me what you can hear."'
    )
    world.say(
        f"{traveler.name} listened and discovered that {tale['clue']}."
    )
    world.say(
        f"Then {tale['conflict'].capitalize()} The road grew dark, and the speedometer needle "
        "trembled like a red eye."
    )
    traveler.memes["courage"] += 1

    world.say(
        f'{guide.name} raised a hand. "Repeat the safe plan: {world.refrain}" '
        f'{traveler.name} repeated, "{world.refrain}" '
        "The guide repeated it again, and even the waiting horses repeated it with soft hoofbeats."
    )
    traveler.memes["trust"] += 1

    world.say(
        f"The suspense deepened because {tale['turn']}. "
        f"Still, nobody rushed. They followed the plan to {tale['safe_plan']}."
    )
    world.say(f"At last, {tale['resolution']}.")
    traveler.meters["distance"] = 1.0
    traveler.meters["danger"] = 0.0

    world.say(
        f"When the journey ended, {tale['ending']}. "
        f"{guide.name} smiled and said, 'A brave traveler does not merely cross a road; "
        "a brave traveler hears what the road is saying.'"
    )


def story_qa(world: World) -> list[QAItem]:
    traveler = world.traveler.name
    tale = world.tale
    return [
        QAItem(
            question="Who traveled along the enchanted road?",
            answer=f"{traveler}, a {world.traveler.trait} traveler, traveled along {world.road}.",
        ),
        QAItem(
            question="What did the speedometer warn them about?",
            answer=f"The speedometer warned them because {tale['danger']}.",
        ),
        QAItem(
            question=f"What did {traveler} hear?",
            answer=f"{traveler} heard that {tale['clue']}.",
        ),
        QAItem(
            question="What safe words did the travelers repeat?",
            answer=f'They repeated, "{world.refrain}" This helped everyone wait and act together.',
        ),
        QAItem(
            question="Why did the travelers not cross at once?",
            answer=f"They did not cross at once because {tale['warning'].lower()} They needed to understand the danger first.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{tale['ending'].capitalize()} The travelers reached safety by listening instead of rushing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a speedometer?",
            answer="A speedometer is a device that shows how fast something is moving.",
        ),
        QAItem(
            question="Why can repetition help during danger?",
            answer="Repetition can help people remember the same safe plan and follow it together.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What does it mean to cross carefully?",
            answer="To cross carefully means to check the way, listen for danger, and move only when it is safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly fairy tale using hearing, a speedometer, and a dangerous crossing.",
        f"Tell how {world.traveler.name} uses the repeated words '{world.refrain}' to solve a conflict on {world.road}.",
        f"Create suspense when {world.vehicle}'s speedometer warns the travelers before they cross.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"traveler={world.traveler.name} trait={world.traveler.trait}",
            f"traveler_meters={world.traveler.meters}",
            f"traveler_memes={world.traveler.memes}",
            f"guide={world.guide.name} wisdom={world.guide.wisdom}",
            f"road={world.road} vehicle={world.vehicle} charm={world.charm}",
            f"tale={world.tale['id']} danger={world.tale['danger']}",
            f"resolution={world.tale['resolution']}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "the moon fox", "Whispering Road", "a pumpkin coach", "a bell charm", "curious"),
    StoryParams("Mira", "Grandmother Willow", "the Briar Crossing", "a little blue cart", "a silver ribbon", "brave"),
    StoryParams("Pip", "the silver owl", "Starfall Path", "a brass carriage", "a glass feather", "patient"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["opening"] = "Long ago, when roads could whisper,"
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
