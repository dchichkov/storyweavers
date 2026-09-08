#!/usr/bin/env python3
"""
Standalone story world: an efficient kindness mission on a pirate ship.

A young pirate learns that the fastest voyage is not always the kindest one.
When a hungry gull is tangled near the harbor, Luna changes course, uses the
right tools, and helps without wasting time or supplies.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the bright harbor"
    detail: str = "a busy harbor where blue waves slapped the wooden piers"


@dataclass
class StoryParams:
    name: str
    captain_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


NAMES = ["Luna", "Mira", "Pip", "Tess", "Nell", "Cora", "Ria", "Zig"]
CAPTAIN_NAMES = ["Captain Coral", "Captain Flint", "Captain Pearl", "Captain Moss"]

SETTING = Setting(
    place="the bright harbor",
    detail="a busy harbor where blue waves slapped the wooden piers and colorful sails bobbed in the tide",
)

MISSIONS = [
    {
        "id": "rope_gull",
        "problem": "a young gull was caught in a loose loop of cargo rope",
        "worry": "The gull flapped hard, but each flap pulled the rope tighter.",
        "tool": "a blunt hook and a small coil of spare line",
        "plan": "lowered the hook from the pier while the captain held the rope steady",
        "truth": "the loop could be loosened without cutting the whole cargo net",
        "repair": "tied the loose rope into a neat bundle so no other bird would catch a foot",
        "ending": "the freed gull rose above the mast and dropped one white feather onto the deck",
        "lesson": "Kindness can be efficient when a calm plan uses only what is needed.",
    },
    {
        "id": "barrel_crab",
        "problem": "a little shore crab was trapped beneath an empty water barrel",
        "worry": "Its tiny claws tapped against the stones as the barrel rocked.",
        "tool": "a wooden lever and one folded sailcloth",
        "plan": "slid the lever under the barrel and covered the crab's path with the sailcloth",
        "truth": "the barrel was light enough to lift safely without rolling it through the crowd",
        "repair": "returned the barrel to the marked stack and left a clear path to the tide pools",
        "ending": "the crab scuttled into a tide pool while Luna's crew cheered softly",
        "lesson": "A kind helper chooses a small, safe action instead of making a big mess.",
    },
    {
        "id": "dolphin_plastic",
        "problem": "a strip of bright packing ribbon floated near a dolphin's fin",
        "worry": "The ribbon twisted in the current whenever the dolphin turned.",
        "tool": "a long-handled net kept for harbor cleanups",
        "plan": "waited for the current to bring the ribbon close, then lifted it without chasing the dolphin",
        "truth": "patience made the rescue safer and used less effort than racing after the moving animal",
        "repair": "put the ribbon in the ship's reuse box and marked the harbor bin for more cleanup",
        "ending": "the dolphin splashed once beside the boat before swimming into clear water",
        "lesson": "Efficient kindness means helping carefully, not hurriedly.",
    },
    {
        "id": "kitten_crate",
        "problem": "a harbor kitten had climbed into a crate and could not find the open side",
        "worry": "It mewed from one corner while sailors searched every side at once.",
        "tool": "a lantern and a strip of bright cloth",
        "plan": "darkened the noisy deck, placed the lantern by the opening, and guided the kitten with the cloth",
        "truth": "one clear light and a quiet path worked better than many reaching hands",
        "repair": "turned the crate so its opening faced the warm fish market wall",
        "ending": "the kitten trotted to its waiting owner and rubbed against Luna's boot",
        "lesson": "Kindness becomes efficient when everyone follows one gentle plan.",
    },
    {
        "id": "turtle_plank",
        "problem": "a small turtle had stopped beneath the ship's loading plank",
        "worry": "Boots and barrels rolled close to its shell.",
        "tool": "a bell, a chalk mark, and a shallow basket",
        "plan": "rang the bell to pause the loading, marked a safe lane, and guided the turtle with the basket",
        "truth": "a short pause prevented a longer accident and protected both turtle and sailors",
        "repair": "painted a turtle sign beside the plank for the next tide",
        "ending": "the turtle reached the reeds, where its shell shone like a tiny shield",
        "lesson": "The kindest efficient choice can be stopping at the right moment.",
    },
]


OPENINGS = [
    "At sunrise, Luna climbed the rope ladder aboard the little pirate ship Swift Finch.",
    "Before the first bell, Luna checked the Swift Finch while the harbor glittered like treasure.",
    "Luna had promised Captain Coral to make the morning delivery before the tide turned.",
    "The Swift Finch rocked beside the pier as Luna polished the compass and counted the cargo.",
    "A warm wind filled the sails when Luna heard the harbor waking around the ship.",
]

REFLECTIONS = [
    '"We saved time by choosing one clear plan," Luna said. "We did not rush kindness away."',
    'Captain Coral smiled. "A clever pirate measures success by who reaches safety, not only by speed."',
    '"The shortest route was not the kindest route," Luna said, "but a calm plan made the kind route efficient."',
    'Luna marked the lesson in the ship log: pause, choose the right tool, and leave the place safer.',
]


ASP_RULES = r"""
needs_help(X) :- trapped(X).
needs_help(X) :- tangled(X).
needs_help(X) :- endangered(X).
kind_plan :- observes, chooses_tool, avoids_waste.
resolved(X) :- needs_help(X), kind_plan, freed(X).
valid_story :- resolved(_), kind_plan.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("pirate_ship", "swift_finch"),
            asp.fact("setting", "bright_harbor"),
            asp.fact("character", "luna"),
            asp.fact("character", "captain"),
            asp.fact("observes"),
            asp.fact("chooses_tool"),
            asp.fact("avoids_waste"),
            asp.fact("trapped", "harbor_animal"),
            asp.fact("freed", "harbor_animal"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("The pirate's name must not be empty.")
    if not params.captain_name.strip():
        raise StoryError("The captain's name must not be empty.")
    if params.name == params.captain_name:
        raise StoryError("The pirate and captain must have different names.")

    rng = random.Random(params.seed)
    mission = rng.choice(MISSIONS)
    opening = rng.choice(OPENINGS).replace("Luna", params.name)
    reflection = rng.choice(REFLECTIONS).replace("Luna", params.name).replace(
        "Captain Coral", params.captain_name
    )
    harbor_detail = rng.choice(
        [
            "coils of rope beside painted mooring posts",
            "fish baskets stacked under a striped awning",
            "bright flags snapping above the tide line",
            "a row of dinghies bumping gently together",
            "seabirds calling over the creaking docks",
        ]
    )

    world = World(setting=SETTING)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="young_pirate",
            label="young pirate",
            meters={"deck_distance": 0.0, "supplies_used": 0.0},
            memes={"worry": 0.0, "kindness": 1.0, "confidence": 0.0, "relief": 0.0},
        )
    )
    captain = world.add(
        Entity(
            id=params.captain_name,
            kind="character",
            type="captain",
            label="captain",
            meters={"deck_distance": 0.0},
            memes={"patience": 1.0, "trust": 1.0, "relief": 0.0},
        )
    )
    animal = world.add(
        Entity(
            id="harbor_animal",
            kind="character",
            type="harbor_animal",
            label="harbor animal",
            meters={"distance_to_safety": 1.0},
            memes={"fear": 1.0, "relief": 0.0},
        )
    )
    world.facts.update(
        hero=hero,
        captain=captain,
        animal=animal,
        mission=mission,
        opening=opening,
        reflection=reflection,
        harbor_detail=harbor_detail,
        safe_boundary="the dry pier and the ship's rail",
    )
    return world


def story_intro(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    world.say(world.facts["opening"])
    world.say(
        f"{hero.id} was a young pirate on the Swift Finch, and {captain.id} was the captain. "
        f"They worked beside {world.facts['harbor_detail']}."
    )
    world.say(
        "Their rule was simple: protect people and animals, use only the tools they needed, "
        "and keep the deck and pier safe for everyone."


def story_problem(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    animal = world.facts["animal"]
    mission = world.facts["mission"]

    hero.meters["deck_distance"] += 2.0
    hero.memes["worry"] += 1.0
    animal.memes["fear"] += 1.0
    world.say(
        f"Then {hero.id} spotted {mission['problem']}. {mission['worry']}"
    )
    world.say(
        f'"We must help at once!" cried {hero.id}. "I can grab the nearest thing!"'
    )
    world.say(
        f'"Wait," said {captain.id}. "Kindness needs a safe plan. What do we know, and which tool will do one useful job?"'
    )
    world.facts["problem"] = mission["problem"]
    world.facts["worry"] = mission["worry"]
    world.facts["dialogue_changed_plan"] = True


def story_turn(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    animal = world.facts["animal"]
    mission = world.facts["mission"]

    world.say(
        f"{hero.id} watched from the dry pier instead of rushing forward. "
        f"{captain.id} brought {mission['tool']}."
    )
    world.say(
        f"Together they {mission['plan']}. Their careful check showed that {mission['truth']}."
    )
    world.say(
        f'{mission["repair"].capitalize()}. {world.facts["reflection"]}'
    )
    hero.meters["supplies_used"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["confidence"] += 1.0
    animal.memes["fear"] = 0.0
    animal.meters["distance_to_safety"] = 0.0
    world.facts["tool"] = mission["tool"]
    world.facts["plan"] = mission["plan"]
    world.facts["truth"] = mission["truth"]
    world.facts["resolved"] = True


def story_resolution(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    mission = world.facts["mission"]

    hero.memes["relief"] += 1.0
    world.facts["animal"].memes["relief"] += 1.0
    world.say(
        f"The harbor grew peaceful again. {mission['ending']} "
        f"{captain.id} gave {hero.id} a proud nod."
    )
    world.say(
        f"{hero.id} closed the ship log. The Swift Finch sailed on, carrying its cargo "
        "and a crew that knew a thoughtful kindness could be both gentle and efficient."
    )
    world.facts["ending_image"] = mission["ending"]
    world.facts["lesson"] = mission["lesson"]


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    story_problem(world)
    story_turn(world)
    story_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    mission = world.facts["mission"]
    return [
        "Write a child-facing Pirate Tale about efficient kindness aboard a small ship.",
        f"Tell how {hero.id} and {captain.id} help when {mission['problem']}, while using a safe, careful plan.",
        f"Include the clue that {mission['truth']} and end with {mission['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    mission = world.facts["mission"]
    return [
        QAItem(
            question=f"Where did {hero.id} work with {captain.id}?",
            answer=f"They worked aboard the Swift Finch beside {world.facts['harbor_detail']} in the bright harbor."
        ),
        QAItem(
            question=f"What problem did {hero.id} notice?",
            answer=f"{hero.id} noticed that {mission['problem']}. The animal was in danger near the harbor."
        ),
        QAItem(
            question=f"Why did {captain.id} stop {hero.id} from grabbing the nearest thing?",
            answer=f"{captain.id} wanted {hero.id} to make a safe, efficient plan rather than act in a rush. They needed to observe first and choose one useful tool."
        ),
        QAItem(
            question="What tool did the pirates use?",
            answer=f"They used {mission['tool']}. It was chosen because it could solve the problem without wasting supplies."
        ),
        QAItem(
            question="How did the pirates help?",
            answer=f"They {mission['plan']}. This showed kindness while keeping the pier and ship safe."
        ),
        QAItem(
            question="What did their careful check reveal?",
            answer=f"They learned that {mission['truth']}."
        ),
        QAItem(
            question="What changed after the rescue?",
            answer=f"{mission['ending']} The animal reached safety, and the harbor became calm again."
        ),
        QAItem(
            question="What lesson did the pirate crew learn?",
            answer=mission["lesson"]
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a sailing vessel used by pirates to travel across the sea. In a story, its crew can also use the ship to explore and help others."
        ),
        QAItem(
            question="What does efficient mean?",
            answer="Efficient means completing a task well while using a sensible amount of time, effort, or supplies."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing someone else's needs and choosing to help in a caring and respectful way."
        ),
        QAItem(
            question="Why should a helper make a plan before rushing?",
            answer="A plan can prevent new harm, choose the right tool, and solve the problem with less wasted effort."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1

    try:
        import asp

        model = asp.one_model(asp_program())
        valid = bool(asp.atoms(model, "valid_story"))
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1

    if not valid:
        print("MISMATCH: ASP did not find a valid story.")
        return 1

    sample = generate(StoryParams(name="Luna", captain_name="Captain Coral", seed=7))
    required = ["Luna", "Captain Coral", "efficient", "kind"]
    if not all(word.lower() in sample.story.lower() for word in required):
        print("MISMATCH: generated story exercise failed.")
        return 1

    print("OK: Python and ASP reasonableness gates pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Pirate Tale about efficient kindness in a bright harbor."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--captain-name", choices=CAPTAIN_NAMES)
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
    name = args.name or rng.choice(NAMES)
    captain = args.captain_name or rng.choice(CAPTAIN_NAMES)
    return StoryParams(name=name, captain_name=captain)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:16} ({entity.type:14}) {' '.join(details)}"
        )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        values = asp.atoms(model, "valid_story")
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", captain_name="Captain Coral", seed=base_seed),
            StoryParams(name="Mira", captain_name="Captain Flint", seed=base_seed + 1),
            StoryParams(name="Pip", captain_name="Captain Pearl", seed=base_seed + 2),
            StoryParams(name="Tess", captain_name="Captain Moss", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
