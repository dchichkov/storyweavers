#!/usr/bin/env python3
"""
Standalone story world: an Olympic frolick with a surprise mystery.

A child prepares a playful Olympic-style frolick in a sunny park, but the
mystery medal disappears just before the opening. By noticing small clues and
listening to a helper, the child discovers that the medal was moved to keep it
safe and turns the search into a fair, joyful celebration.
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


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_role: str
    event: str
    object_name: str
    animal: str
    scenario: str
    opening_variant: int = 0
    clue_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "sunny_park": Setting(
        id="sunny_park",
        place="the sunny park",
        affords={"olympic_games", "clues", "surprise"},
    ),
}

EVENTS = {
    "frolick": {
        "label": "a friendly Olympic frolick",
        "activity": "hop, twirl, and race around the little course",
    },
    "relay": {
        "label": "a tiny Olympic relay",
        "activity": "carry a ribbon around the little course",
    },
    "balance": {
        "label": "an Olympic balance challenge",
        "activity": "cross the stepping stones with careful feet",
    },
}

OBJECTS = {
    "medal": {
        "label": "a bright golden medal",
        "clue": "a round golden print in the damp grass",
        "safe_place": "inside the picnic basket",
    },
    "ribbon": {
        "label": "a blue victory ribbon",
        "clue": "a blue thread caught on the fence",
        "safe_place": "under the folded picnic blanket",
    },
    "cup": {
        "label": "a little silver cup",
        "clue": "a silver shine beneath the bench",
        "safe_place": "beside the park notice board",
    },
}

ANIMALS = {
    "squirrel": {"label": "squirrel", "sound": "chitter"},
    "duck": {"label": "duck", "sound": "quack"},
    "puppy": {"label": "puppy", "sound": "yip"},
}

SCENARIOS = {
    "basket_guard": {
        "animal": "squirrel",
        "trouble": "a gust tipped the prize box, and the medal vanished before the first event",
        "discovery": "the squirrel had tugged the box toward the picnic basket while searching for a shiny snack wrapper",
        "repair": "Mina thanked the squirrel, removed the wrapper, and placed the medal safely on the judging cloth",
        "result": "the squirrel chittered from the tree while every child took a fair turn",
    },
    "fence_ribbon": {
        "animal": "puppy",
        "trouble": "the puppy raced past the course, and the victory ribbon disappeared from its hook",
        "discovery": "the ribbon had caught on a low branch beside the fence, where the puppy had been sniffing",
        "repair": "the helper freed the ribbon gently and moved the hook away from the running path",
        "result": "the puppy led the parade without carrying anyone's prize away",
    },
    "bench_glimmer": {
        "animal": "duck",
        "trouble": "the silver cup was gone when the children gathered beside the stepping stones",
        "discovery": "the cup had rolled beneath the bench after a duck brushed the display table",
        "repair": "Eli waited until the duck waddled past, then rolled the cup back with a soft stick",
        "result": "the duck quacked at the finish line as the children bowed together",
    },
}

OPENINGS = [
    "Morning light painted long stripes across {place} when {child} arrived.",
    "The park was bright and breezy when {child} opened the little Olympic sign.",
    "Before the first whistle, {child} and {helper} laid out a course in {place}.",
    "A cheerful banner waved above {place}, promising an unusual day of games.",
]

CLUE_LINES = [
    "Instead of guessing, they followed the clues one at a time.",
    "The mystery became smaller when they looked closely at the ground.",
    "They paused beside the course and searched for what had changed.",
]

ENDINGS = [
    "At sunset, the prize shone on the judging cloth, but the best surprise was how everyone celebrated together.",
    "The final Olympic cheer was quiet enough for the {animal} to stay nearby, and the mystery ended with happy smiles.",
    "Nobody cared who looked most famous anymore; the children cared that the game had become fair.",
]


def valid_combo(place: str, event: str, object_name: str, animal: str) -> bool:
    return (
        place in SETTINGS
        and event in EVENTS
        and object_name in OBJECTS
        and animal in ANIMALS
        and any(s["animal"] == animal for s in SCENARIOS.values())
    )


def explain_rejection(place: str, event: str, object_name: str, animal: str) -> str:
    return (
        f"Cannot make a reasonable story from place={place}, event={event}, "
        f"object={object_name}, animal={animal}: the Olympic mystery needs a "
        "playful event, a missing prize, and a nearby clue."
    )


def _scenario_for(animal: str, requested: Optional[str] = None) -> str:
    if requested and requested in SCENARIOS and SCENARIOS[requested]["animal"] == animal:
        return requested
    for key, value in SCENARIOS.items():
        if value["animal"] == animal:
            return key
    raise StoryError(f"No mystery scenario supports the animal {animal}.")


def tell(params: StoryParams) -> World:
    if not valid_combo(params.place, params.event, params.object_name, params.animal):
        raise StoryError(
            explain_rejection(params.place, params.event, params.object_name, params.animal)
        )

    setting = SETTINGS[params.place]
    event = EVENTS[params.event]
    prize = OBJECTS[params.object_name]
    animal_info = ANIMALS[params.animal]
    scenario = SCENARIOS[params.scenario]

    world = World(setting)
    child = world.add(Entity(params.child_name, "character", params.child_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_name))
    animal = world.add(Entity(params.animal, "animal", animal_info["label"]))
    prize_entity = world.add(Entity(params.object_name, "prize", prize["label"]))

    child.memes["excitement"] = 1.0
    child.memes["worry"] = 0.0
    helper.memes["patience"] = 1.0
    animal.memes["curiosity"] = 1.0
    prize_entity.meters["visibility"] = 1.0

    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(
        place=setting.place,
        child=child.label,
        helper=helper.label,
    )
    world.say(opening)
    world.say(
        f"{child.label} had planned {event['label']}. The game would let everyone "
        f"{event['activity']}, and the winner would hold {prize['label']} for one turn."
    )
    world.say(
        f"{helper.label} placed the prize beside the course while the {animal.label} "
        f"watched from the edge of the grass."
    )

    world.para()
    world.say(f"Then {scenario['trouble']}.")
    child.memes["worry"] = 1.0
    prize_entity.meters["visibility"] = 0.0
    animal.memes["curiosity"] = 2.0
    world.fired.add(("missing", params.object_name))
    world.facts["missing"] = True

    world.say(f'"We must find it before we blame anyone," {helper.label} said.')
    world.say(
        f'"I will look for a clue, not just hurry," {child.label} replied.'
    )
    world.say(CLUE_LINES[params.clue_variant % len(CLUE_LINES)])
    world.say(
        f"They noticed {prize['clue']}, and the marks led toward {prize['safe_place']}."
    )

    world.para()
    world.say(
        f'"There is our surprise!" {helper.label} said. '
        f"{scenario['discovery'].capitalize()}."
    )
    world.say(
        f'"The prize was safe, but our game was not ready," {child.label} said. '
        f'"Let us fix the course first."'
    )
    world.say(f"{scenario['repair'].capitalize()}.")
    child.memes["worry"] = 0.0
    child.memes["care"] = 1.0
    animal.memes["calm"] = 1.0
    prize_entity.meters["visibility"] = 1.0
    world.fired.add(("found", params.object_name))
    world.fired.add(("repair", params.object_name))
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"The Olympic frolick began again, and everyone cheered for brave tries "
        f"rather than only for first place. {scenario['result'].capitalize()}."
    )
    world.say(
        ENDINGS[params.ending_variant % len(ENDINGS)].format(animal=animal.label)
    )

    world.facts.update(
        child=child,
        helper=helper,
        animal=animal,
        prize=prize_entity,
        prize_info=prize,
        event=event,
        scenario=scenario,
        setting=setting,
        clue=prize["clue"],
        safe_place=prize["safe_place"],
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a complete child-friendly mystery about an Olympic frolick and a surprising missing prize.",
        (
            f"Tell how {f['child'].label} follows the clue "
            f"'{f['clue']}' to find {f['prize_info']['label']} without blaming the "
            f"{f['animal'].label}."
        ),
        "Show how a mystery can turn into a fair celebration when people listen and look carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    animal = f["animal"]
    prize = f["prize_info"]
    return [
        QAItem(
            question=f"What was {child.label} preparing at the park?",
            answer=(
                f"{child.label} was preparing {f['event']['label']} in {f['setting'].place}, "
                f"where children could playfully {f['event']['activity']}."
            ),
        ),
        QAItem(
            question=f"What disappeared during the mystery?",
            answer=(
                f"{prize['label']} disappeared before the game began because "
                f"{f['scenario']['trouble']}."
            ),
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=(
                f"They found {f['clue']}, which led toward {f['safe_place']}. "
                f"That clue showed where the prize had been moved."
            ),
        ),
        QAItem(
            question=f"How did {child.label} treat the {animal.label} after the surprise?",
            answer=(
                f"{child.label} did not blame the {animal.label}. With {helper.label}'s "
                f"help, {child.label} made the course safe and let the animal stay calm."
            ),
        ),
        QAItem(
            question="What changed by the end?",
            answer=(
                f"The missing prize was found and the course was repaired. The Olympic "
                f"frolick became a fair celebration in which everyone cheered for brave tries."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does Olympic mean in this story?",
            answer=(
                "Olympic means connected with a special contest or group of friendly games; "
                "in this story, the word describes a small pretend event for children."
            ),
        ),
        QAItem(
            question="What is a frolick?",
            answer="A frolick is a lively, playful time of running, hopping, and having fun.",
        ),
        QAItem(
            question="What is a mystery?",
            answer=(
                "A mystery is something not yet understood that people solve by noticing "
                "clues and thinking carefully."
            ),
        ),
        QAItem(
            question="Why is it better to follow clues than to blame someone?",
            answer=(
                "Following clues helps people discover what really happened, while blaming "
                "someone too soon can be unfair and can hide the truth."
            ),
        ),
        QAItem(
            question="What is a surprise?",
            answer=(
                "A surprise is something unexpected that someone discovers or experiences."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
event(frolick).
event(relay).
event(balance).

prize(medal).
prize(ribbon).
prize(cup).

animal(squirrel).
animal(puppy).
animal(duck).

supports_mystery(frolick, medal, squirrel).
supports_mystery(relay, ribbon, puppy).
supports_mystery(balance, cup, duck).

good_story(P, E, O, A) :-
    place(P),
    event(E),
    prize(O),
    animal(A),
    supports_mystery(E, O, A).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("place", place_id) for place_id in SETTINGS]
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted(
        (place, event, obj, animal)
        for place in SETTINGS
        for event, data in EVENTS.items()
        for obj in OBJECTS
        for animal in ANIMALS
        if valid_combo(place, event, obj, animal)
        and SCENARIOS[_scenario_for(animal)]["animal"] == animal
        and (
            (event, obj, animal)
            in {
                ("frolick", "medal", "squirrel"),
                ("relay", "ribbon", "puppy"),
                ("balance", "cup", "duck"),
            }
        )
    )
    clingo_result = asp_valid_combos()
    if py == clingo_result:
        for params in curated_params():
            sample = generate(params)
            if not sample.story or "Olympic" not in sample.story:
                print("Generated story exercise failed.")
                return 1
        print(f"OK: clingo gate matches Python gate ({len(py)} combos); stories exercised.")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", clingo_result)
    return 1


GIRL_NAMES = ["Luna", "Mina", "Ivy", "Nora", "Pia"]
BOY_NAMES = ["Eli", "Noah", "Milo", "Theo", "Finn"]
HELPERS = [
    ("Mom", "mother"),
    ("Dad", "father"),
    ("Ari", "coach"),
    ("Zoe", "older sister"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Olympic frolick mystery story world with a surprise."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--event", choices=EVENTS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--role")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "sunny_park"
    scenario_key = rng.choice(list(SCENARIOS))
    scenario = SCENARIOS[scenario_key]
    animal = args.animal or scenario["animal"]

    if args.event:
        event = args.event
    else:
        event = {
            "squirrel": "frolick",
            "puppy": "relay",
            "duck": "balance",
        }[animal]

    object_name = args.object_name or {
        "frolick": "medal",
        "relay": "ribbon",
        "balance": "cup",
    }[event]

    if not valid_combo(place, event, object_name, animal):
        raise StoryError(explain_rejection(place, event, object_name, animal))

    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    if args.helper:
        helper_name = args.helper
        helper_role = args.role or "coach"
    else:
        helper_name, helper_role = rng.choice(HELPERS)
        helper_role = args.role or helper_role

    scenario_key = _scenario_for(animal, scenario_key)
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_role=helper_role,
        event=event,
        object_name=object_name,
        animal=animal,
        scenario=scenario_key,
        opening_variant=rng.randrange(len(OPENINGS)),
        clue_variant=rng.randrange(len(CLUE_LINES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            place="sunny_park",
            child_name="Luna",
            child_gender="girl",
            helper_name="Coach Ari",
            helper_role="coach",
            event="frolick",
            object_name="medal",
            animal="squirrel",
            scenario="basket_guard",
        ),
        StoryParams(
            place="sunny_park",
            child_name="Eli",
            child_gender="boy",
            helper_name="Mom",
            helper_role="mother",
            event="relay",
            object_name="ribbon",
            animal="puppy",
            scenario="fence_ribbon",
        ),
        StoryParams(
            place="sunny_park",
            child_name="Mina",
            child_gender="girl",
            helper_name="Dad",
            helper_role="father",
            event="balance",
            object_name="cup",
            animal="duck",
            scenario="bench_glimmer",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: Olympic {p.event} with the {p.object_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
