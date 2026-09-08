#!/usr/bin/env python3
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass(frozen=True)
class Incident:
    id: str
    opening: str
    danger: str
    clue: str
    first_plan: str
    warning: str
    helper: str
    rescue: str
    repetition: str
    proof: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    trait: str
    scenario: str = ""
    telling: str = ""
    seed: Optional[int] = None


SETTINGS = {
    "flower_field": {
        "label": "the flower field",
        "affords": {"splish_adventure"},
    }
}

ACTIVITIES = {
    "splish_adventure": {
        "label": "a splish adventure through the flower field",
        "hazard": "a muddy stream",
    }
}

PRIZES = {
    "ten_blooms": {
        "label": "ten bright flowers",
        "count": 10,
    }
}

ANIMALS = [
    ("Luna", "rabbit"),
    ("Milo", "mouse"),
    ("Pia", "squirrel"),
    ("Tess", "fox"),
    ("Nico", "hedgehog"),
]

TRAITS = ["brave", "curious", "careful", "cheerful", "quick-thinking"]
TELLINGS = ["clue_first", "dialogue_first", "quiet_build", "question_turn", "action_turn"]

INCIDENTS = {
    "fallen_bridge": Incident(
        "fallen_bridge",
        "Luna was leading a ten-step flower-field adventure when a little bridge fell across the creek.",
        "The creek made a loud splish, and the fallen boards blocked the safest path to ten golden flowers.",
        "A bright feather floated upstream, showing that the water was deeper on the other side than it looked.",
        "Luna first wanted to hop straight across the broken bridge.",
        '"Stop, step back, and count with me!" Luna called.',
        "Gardener Bea hurried over with rope, smooth stones, and a small repair board.",
        "Bea tied the loose bridge, laid the stones in a firm crossing, and moved the sharp boards away from the flowers.",
        "Luna repeated the safe route ten times, touching one stone after another and calling, 'Splish, step, splish, step!'",
        "Every flower stood safely beyond the creek, and the water ran under the repaired bridge.",
        "Luna and her friends crossed together while ten golden petals nodded in the breeze.",
        "When a path changes, pause, look for clues, and let a trusted helper make it safe.",
    ),
    "hidden_hole": Incident(
        "hidden_hole",
        "A warm wind sent Luna racing through the flower field toward ten purple blooms.",
        "A soft patch of earth hid beneath the grass, and one more hop could send a paw into the hole.",
        "Ten wet footprints ended before the patch, proving that the ground had swallowed the morning rain.",
        "Luna almost covered the hole with a broad leaf.",
        '"No hopping here! Back, back, then look!" Luna shouted.',
        "Ranger Sol arrived with a bright marker, a shovel, and clean soil.",
        "Sol marked the hole, filled it firmly, and checked the ground from ten directions.",
        "Luna repeated the warning at every turn: 'No hop, look twice, stay on the stones!'",
        "The soil stayed firm when ten small test steps pressed it.",
        "The ten purple blooms opened above a smooth patch of safe ground.",
        "A quick cover can hide a danger, but careful checking can truly solve it.",
    ),
    "windy_pollen": Incident(
        "windy_pollen",
        "Luna and her friends planned an adventure to count ten red flowers.",
        "A gust shook a tall stalk, sending a cloud of pollen toward a narrow trail.",
        "The pollen drifted only when the wind blew from the old oak, revealing the safest direction to walk.",
        "Luna thought she could wave the cloud away with her ears.",
        '"Wait for the wind to turn. One, two, three, then go!" Luna said.',
        "Flower keeper Mina brought a screen and helped the friends use the sheltered path.",
        "Mina guided everyone behind the screen until the gust passed, then checked each flower for bent stems.",
        "The friends counted ten calm breaths and repeated the sheltered route before moving.",
        "The pollen settled, and every red flower lifted its face again.",
        "Ten red blossoms glowed beside the path as the friends cheered.",
        "Patience and repeated checks can turn a frightening moment into a safe adventure.",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("flower_field", "splish_adventure", "ten_blooms")
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure story world with ten flowers, a splish, repetition, and a happy ending."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--prize", choices=PRIZES)
    parser.add_argument("--name")
    parser.add_argument("--animal", choices=[animal for _, animal in ANIMALS])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--scenario", choices=INCIDENTS)
    parser.add_argument("--telling", choices=TELLINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "flower_field":
        raise StoryError("No story: this adventure belongs in the flower field.")
    if args.activity and args.activity != "splish_adventure":
        raise StoryError("No story: only the splish adventure fits this world.")
    if args.prize and args.prize != "ten_blooms":
        raise StoryError("No story: the prize must be ten flowers.")

    if args.name and args.animal:
        name, animal = args.name, args.animal
    elif args.name:
        name = args.name
        animal = next((kind for known, kind in ANIMALS if known == name), rng.choice(ANIMALS)[1])
    elif args.animal:
        animal = args.animal
        name = next((known for known, kind in ANIMALS if kind == animal), rng.choice(ANIMALS)[0])
    else:
        name, animal = rng.choice(ANIMALS)

    return StoryParams(
        place="flower_field",
        activity="splish_adventure",
        prize="ten_blooms",
        name=name,
        animal=animal,
        trait=args.trait or rng.choice(TRAITS),
        scenario=args.scenario or rng.choice(sorted(INCIDENTS)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    incident = INCIDENTS[params.scenario]
    world = World()
    hero = world.add(Entity(params.name, "character", params.animal, params.name))
    flowers = world.add(Entity("ten_flowers", "thing", "flowers", "ten bright flowers"))
    stream = world.add(Entity("splish_stream", "thing", "stream", "the little stream"))

    hero.memes.update(adventure=1.0, repetition=1.0)
    flowers.meters.update(count=10.0, safe=0.0)
    stream.meters.update(risk=1.0)

    openings = [
        f"Morning sunlight spilled across the flower field, where {hero.id}, a {params.trait} {params.animal}, prepared for an adventure.",
        f"The flower field shimmered with dew as {hero.id}, a {params.trait} {params.animal}, set off to find ten flowers.",
        f"Beyond the garden gate, the flower field invited {hero.id}, a {params.trait} {params.animal}, down a winding trail.",
    ]
    world.say(rng.choice(openings))
    world.say(incident.opening)
    world.para()

    if params.telling == "clue_first":
        world.say(incident.danger)
        world.say(incident.clue)
    elif params.telling == "question_turn":
        world.say(f"{incident.danger} What could {hero.id} do?")
        world.say(incident.clue)
    else:
        world.say(incident.clue)
        world.say(incident.danger)

    world.facts.update(
        hazard_seen=True,
        hazard=incident.danger,
        clue=incident.clue,
        scenario=incident.id,
    )
    world.say(f"The adventure had become risky, so {hero.id} kept all four paws on firm ground.")
    world.para()

    world.say(incident.first_plan)
    world.say(incident.warning)
    world.say("The friends repeated the warning until everyone knew which way was safe.")
    world.para()

    world.say(incident.helper)
    world.say(incident.rescue)
    world.say(incident.repetition)
    stream.meters["risk"] = 0.0
    flowers.meters["safe"] = 1.0
    world.facts["resolved"] = True
    world.para()

    world.say(f"At last, the happy ending arrived: {incident.proof}")
    world.say(incident.ending)
    world.say(f"{hero.id} smiled and remembered the lesson learned: {incident.lesson}")

    world.facts.update(
        hero=hero,
        flowers=flowers,
        stream=stream,
        incident=incident,
        helper=incident.helper,
        ten=10,
        splish="splish",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    seed = params.seed if params.seed is not None else sum(
        ord(char) for char in f"{params.name}:{params.scenario}:{params.telling}"
    )
    world = tell(params, random.Random(seed ^ 0xA17E))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    incident = world.facts["incident"]
    return [
        f"Write an adventure story in a flower field where {hero.id} faces {incident.id.replace('_', ' ')}.",
        "Include ten flowers, a cheerful splish, spoken dialogue, repetition, and a happy ending.",
        "Show a clue changing the hero's plan, a trusted helper repairing the problem, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    incident: Incident = world.facts["incident"]
    return [
        QAItem(
            f"Who led the adventure in the flower field?",
            f"{hero.label}, a {hero.type}, led the adventure through the flower field.",
        ),
        QAItem(
            "What did the clue reveal?",
            incident.clue,
        ),
        QAItem(
            "What did the characters repeat?",
            incident.repetition,
        ),
        QAItem(
            "How did the trusted helper make the adventure safe?",
            incident.rescue,
        ),
        QAItem(
            "What proved that the story had a happy ending?",
            incident.proof,
        ),
        QAItem(
            "What lesson was learned?",
            incident.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does splish mean?",
            "Splish is the light sound made when water is gently disturbed.",
        ),
        QAItem(
            "Why can repetition help during an adventure?",
            "Repetition helps everyone remember a warning, route, or careful action.",
        ),
        QAItem(
            "What is a flower field?",
            "A flower field is an open place where many flowers grow together.",
        ),
        QAItem(
            "What should a child do when a path becomes unsafe?",
            "A child should stop, move to a safe place, warn others, and ask a trusted adult for help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:16} ({entity.type:8}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts={sorted(key for key in world.facts if key not in {'hero', 'flowers', 'stream', 'incident'})}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous :- stream_risk.
safe_path :- helper_repairs, repeated_check.
happy_ending :- safe_path, ten_flowers.
lesson_learned :- happy_ending.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "flower_field"),
        asp.fact("activity", "splish_adventure"),
        asp.fact("prize", "ten_blooms"),
        asp.fact("ten_flowers"),
        asp.fact("stream_risk"),
        asp.fact("helper_repairs"),
        asp.fact("repeated_check"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show happy_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show happy_ending/0."))
    return asp.atoms(model, "happy_ending")


def asp_verify() -> int:
    python_ok = bool(valid_combos())
    try:
        asp_ok = bool(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    if python_ok != asp_ok:
        print("MISMATCH: Python and ASP disagree about valid stories.")
        return 1
    sample = generate(
        StoryParams(
            place="flower_field",
            activity="splish_adventure",
            prize="ten_blooms",
            name="Luna",
            animal="rabbit",
            trait="brave",
            scenario="fallen_bridge",
            telling="dialogue_first",
            seed=7,
        )
    )
    required = ["ten", "splish", "happy ending", "lesson learned"]
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story is missing a required narrative instrument.")
        return 1
    print("OK: Python/ASP parity and generated-story checks passed.")
    return 0


CURATED = [
    StoryParams(
        "flower_field",
        "splish_adventure",
        "ten_blooms",
        "Luna",
        "rabbit",
        "brave",
        "fallen_bridge",
        "dialogue_first",
        11,
    ),
    StoryParams(
        "flower_field",
        "splish_adventure",
        "ten_blooms",
        "Milo",
        "mouse",
        "curious",
        "hidden_hole",
        "clue_first",
        29,
    ),
    StoryParams(
        "flower_field",
        "splish_adventure",
        "ten_blooms",
        "Pia",
        "squirrel",
        "careful",
        "windy_pollen",
        "question_turn",
        43,
    ),
]


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
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        print("1 compatible story combination:")
        print("  flower_field splish_adventure ten_blooms")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(20, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
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
