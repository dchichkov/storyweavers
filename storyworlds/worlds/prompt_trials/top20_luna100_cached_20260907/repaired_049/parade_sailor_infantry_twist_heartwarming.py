#!/usr/bin/env python3
"""
A heartwarming storyworld about a village parade, a sailor, and an infantry
drummer who discover that a quiet change of plan can bring everyone together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    ))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
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
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    obstacle: str
    first_plan: str
    clue: str
    helper: str
    shared_item: str
    careful_action: str
    result: str
    twist: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    town: str
    parade: str
    sailor: str
    infantry: str
    child: str
    seed: Optional[int] = None


TOWNS = {
    "harbor": "the harbor square",
    "hill": "the hill town",
    "river": "the riverside village",
}

PARADES = {
    "welcome": "the welcome parade",
    "lantern": "the lantern parade",
    "harvest": "the harvest parade",
}

SAILORS = ["Mara", "Niko", "Elsa", "Tom", "Rafi", "June"]
CHILDREN = ["Lina", "Pia", "Oren", "Milo", "Sami", "Tess"]
INFANTRY_NAMES = ["Captain Vale", "Sergeant Rowan", "Corporal Ash", "Lieutenant Reed"]

SCENARIOS = [
    Scenario(
        "rainy_flags",
        "The town prepared a welcome parade for sailors returning from a long voyage.",
        "A sudden rain soaked the bright flags, and the infantry band could not keep its paper music dry.",
        "The parade leader wanted to cancel the march until the clouds passed.",
        "The sailors had tarps folded beneath their travel chests, while the children carried empty lantern frames.",
        "the children from the schoolhouse",
        "the tarps, lantern frames, and a coil of soft rope",
        "asked the sailors to raise a covered walkway and helped the children turn the lantern frames into sheltered music stands",
        "the band could play, the flags stayed bright, and the returning sailors walked beneath a warm line of lights",
        "the parade became a moving shelter where every group had a part",
        "The sailor did not need a grand welcome; a dry place to share stories was enough.",
        "Kindness often begins when people change the plan for someone who needs a little room.",
    ),
    Scenario(
        "quiet_drum",
        "An infantry drummer was meant to lead the harvest parade through the market street.",
        "His drum skin loosened in the morning mist, so each beat came out soft and sleepy.",
        "The mayor suggested replacing him with a louder drum from the town hall.",
        "The sailor noticed that the loose drum still made a gentle pulse when tapped near the rim.",
        "the returned sailor and a group of market children",
        "small bells, wooden spoons, and the quiet drum",
        "invited everyone to follow the soft pulse and add one small sound instead of covering it",
        "the parade grew into a tender rhythm that let babies, elders, and tired travelers walk comfortably",
        "the quiet drummer became the one who taught the whole parade to listen",
        "A soft sound can lead many hearts when everyone listens together.",
        "The strongest march was not always the loudest one.",
    ),
    Scenario(
        "missing_bridge",
        "The lantern parade was to cross the old bridge and end beside the sailors' boats.",
        "A loose plank made the bridge unsafe for marching feet and rolling drums.",
        "The infantry captain planned to send everyone around the long hill road.",
        "The sailor saw that the boats were tied close enough to make a floating line of lights beside the bridge.",
        "the boat builders",
        "lanterns, spare rope, and the boats' low deck boards",
        "worked with the boat builders to make a still floating path while the infantry kept watch on both banks",
        "families crossed safely by the boats and met the parade at the far shore",
        "the parade route became a circle that joined both sides of the water",
        "A detour can become a new meeting place when people build it together.",
        "The lanterns shone on the water as if the river itself had joined the celebration.",
    ),
    Scenario(
        "small_uniform",
        "A young infantry helper wanted to march in the parade but had outgrown the smallest uniform.",
        "The spare coats were too long, and the child feared being left behind.",
        "The parade marshal began to say that only perfect uniforms could enter the line.",
        "The sailor's old blue scarf had a row of strong buttons that could shorten a coat.",
        "the sailor and the coat menders",
        "the blue scarf, bright thread, and a basket of spare buttons",
        "measured the sleeves, shared the buttons, and made a sash that honored the child's own height",
        "the child marched comfortably beside the infantry and carried the first lantern",
        "the parade uniform gained sashes in many colors and sizes",
        "Belonging should be fitted to people, not the other way around.",
        "The smallest marcher held the brightest lantern, and nobody mistook her for being unimportant.",
    ),
    Scenario(
        "fog_horn",
        "The sailor's ship was due to arrive during the town's great parade.",
        "Fog covered the harbor, and the crowd could not tell whether a distant horn came from the ship or the ferry.",
        "The infantry planned to sound every drum at once so the sailor could find the square.",
        "The sailor remembered that the ship answered three short bells, not one long roar.",
        "the harbor children",
        "three handbells and a white ribbon",
        "asked the children to ring the answer while the infantry held a quiet lane for the sound to travel",
        "the ship answered, and the sailor found the welcoming parade without anyone being frightened",
        "the town added a gentle welcome signal to every future parade",
        "Good guidance leaves space for an answer.",
        "Three clear bells traveled through the fog, and a ship replied like a friend calling from a dream.",
    ),
    Scenario(
        "wheelchair_route",
        "The infantry band practiced a parade route lined with flowers and bunting.",
        "One narrow turn was blocked by a flower cart, leaving no safe path for an elder who used wheels.",
        "The marshal thought the elder could watch from the doorway instead.",
        "The sailor saw that the cart's wheels were easy to move, and the flower seller wanted everyone to see the parade.",
        "the flower seller and the elder",
        "the cart, flower baskets, and a smooth wooden board",
        "moved the cart into a bright arch, laid the board over the rough stones, and widened the turn",
        "the elder joined the parade and gave the band its first wave from inside the procession",
        "the route changed so every celebration had a welcoming turn",
        "A parade is not complete if someone must watch it from far away.",
        "Flowers made the path beautiful, but welcome made it whole.",
    ),
]

DIALOGUES = [
    "What would help everyone take part?",
    "Could the trouble be pointing toward a kinder route?",
    "What do you have that might make room for someone else?",
    "May we listen before we choose the loudest answer?",
    "How can the parade carry the people who cannot hurry?",
    "What if changing the plan is part of the celebration?",
]

REFLECTIONS = [
    "The sailor learned that returning home means noticing who is still waiting outside the circle.",
    "The infantry learned that discipline can protect gentleness as well as order.",
    "The child learned that a parade is a promise to make room for every neighbor.",
    "The town learned that a twist in the plan can reveal the heart of a celebration.",
    "No one marched alone after that day; every song had a place for another voice.",
]


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("harbor", "welcome", "sailor"),
        ("hill", "harvest", "infantry"),
        ("river", "lantern", "sailor"),
    ]


def reasonableness_gate(params: StoryParams) -> None:
    if params.town not in TOWNS:
        raise StoryError(f"Unknown town: {params.town}.")
    if params.parade not in PARADES:
        raise StoryError(f"Unknown parade: {params.parade}.")
    if params.sailor not in {"sailor", "infantry"}:
        raise StoryError("The story needs a sailor or infantry role.")
    if not params.child.strip():
        raise StoryError("The child must have a name.")
    if not any(town == params.town and parade == params.parade
               for town, parade, _ in valid_combos()):
        raise StoryError(
            "That parade does not fit this town's welcoming route; choose a listed combination."
        )


def choose_scenario(params: StoryParams) -> Scenario:
    value = params.seed
    if value is None:
        value = sum((i + 1) * ord(c) for i, c in enumerate(
            f"{params.town}|{params.parade}|{params.sailor}|{params.infantry}|{params.child}"
        ))
    return SCENARIOS[value % len(SCENARIOS)]


def tell(world: World, params: StoryParams) -> None:
    scenario = choose_scenario(params)
    child = world.add(Entity(params.child, "character", "child", params.child))
    sailor = world.add(Entity("Sailor", "character", "sailor", params.sailor))
    infantry = world.add(Entity("Infantry", "character", "infantry", params.infantry))
    parade = world.add(Entity("Parade", "event", "parade", PARADES[params.parade]))

    add_meme(child, "hope")
    add_meme(sailor, "homesickness")
    add_meme(infantry, "duty")
    add_meter(parade, "welcome", 1.0)

    scenario_index = SCENARIOS.index(scenario)
    dialogue = DIALOGUES[
        (params.seed or scenario_index) % len(DIALOGUES)
    ]
    reflection = REFLECTIONS[
        ((params.seed or scenario_index) // len(DIALOGUES)) % len(REFLECTIONS)
    ]

    world.say(
        f"In {TOWNS[params.town]}, everyone was preparing {PARADES[params.parade]}."
    )
    world.say(
        f"The parade would welcome {params.sailor} {params.infantry} home, and {params.child} had been chosen to carry the first bright ribbon."
    )
    world.say(scenario.opening)
    world.para()

    world.say(scenario.obstacle)
    world.say(scenario.first_plan)
    add_meme(child, "worry")
    world.say(
        f"{params.child} looked from the waiting crowd to {scenario.helper} and asked, \"{dialogue}\""
    )
    world.say(
        f"The sailor answered, \"We brought {scenario.shared_item}; perhaps it can help us think differently.\""
    )
    world.say(
        f"The infantry leader replied, \"Then we will keep watch while everyone works safely.\""
    )
    world.para()

    world.say(f"Then they noticed the clue: {scenario.clue}")
    add_meter(child, "careful_observation")
    add_meter(sailor, "sharing")
    add_meter(infantry, "protecting")
    world.say(
        f"Together, {params.child}, the sailor, and the infantry {scenario.careful_action}."
    )
    world.say(f"The unexpected turn was this: {scenario.twist}.")
    add_meme(child, "courage")
    add_meme(sailor, "belonging")
    add_meme(infantry, "trust")
    world.para()

    world.say(f"At last, {scenario.result}.")
    add_meter(parade, "welcome", 1.0)
    world.say(
        f"{params.child} carried the ribbon at the front, while the sailor and the infantry walked beside the people they had helped."
    )
    world.say(f"{scenario.ending} {reflection}")
    world.say(f"The parade did not become smaller when the plan changed; it became wide enough for everyone.")

    world.facts.update(
        scenario=scenario,
        child=child,
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        dialogue=dialogue,
        reflection=reflection,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(TOWNS[params.town])
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    child: Entity = f["child"]
    return [
        f"Write a heartwarming parade story about {child.label}, a sailor, and infantry facing this problem: {scenario.obstacle}",
        f"Tell a gentle story in which a parade takes an unexpected twist and makes room for everyone.",
        "Write a child-facing tale where a sailor and infantry helper solve a parade problem by sharing what they have.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    child: Entity = f["child"]
    return [
        QAItem(
            f"Who carried the first ribbon in the parade?",
            f"{child.label} carried the first ribbon at the front of the parade.",
        ),
        QAItem(
            "What problem interrupted the parade?",
            f"The parade was interrupted because {scenario.obstacle}",
        ),
        QAItem(
            "What clue helped the characters change their plan?",
            f"They noticed that {scenario.clue}",
        ),
        QAItem(
            "What did the sailor share?",
            f"The sailor shared {scenario.shared_item}, which gave the group useful materials for a kinder solution.",
        ),
        QAItem(
            "What was the unexpected twist?",
            f"The twist was that {scenario.twist} This changed the parade from a simple march into a welcome shared by everyone.",
        ),
        QAItem(
            "How did the story end?",
            f"{scenario.result} The parade ended with people walking together instead of leaving anyone outside.",
        ),
        QAItem(
            "What lesson did the parade teach?",
            f"It taught that {scenario.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a parade?",
            "A parade is an organized celebration in which people move together, often with music, flags, or decorated vehicles.",
        ),
        QAItem(
            "What does a sailor do?",
            "A sailor works or travels on a boat or ship and learns how to live safely near the water.",
        ),
        QAItem(
            "What is infantry?",
            "Infantry are soldiers who serve and move on foot rather than traveling mainly in vehicles or ships.",
        ),
        QAItem(
            "Why can changing a plan be helpful?",
            "Changing a plan can be helpful when the first plan leaves someone out or does not fit what is really happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(harbor,welcome,sailor).
valid(hill,harvest,infantry).
valid(river,lantern,sailor).
parade_kind(welcome).
parade_kind(harvest).
parade_kind(lantern).
role(sailor).
role(infantry).
reasonable(T,P,R) :- valid(T,P,R).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("town", "harbor"),
            asp.fact("parade", "welcome"),
            asp.fact("role", "sailor"),
        ]
    )


def asp_program(show: str = "#show reasonable/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if py != cl:
        print(f"MISMATCH: Python={sorted(py)} ASP={sorted(cl)}")
        return 1
    for params in [
        StoryParams("harbor", "welcome", "sailor", "infantry", "Lina", 1),
        StoryParams("hill", "harvest", "infantry", "infantry", "Milo", 2),
    ]:
        sample = generate(params)
        if not sample.story or "parade" not in sample.story:
            print("MISMATCH: generated story failed")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combos) and stories generate.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade storyworld about a sailor, infantry, and a hopeful twist."
    )
    parser.add_argument("--town", choices=sorted(TOWNS))
    parser.add_argument("--parade", choices=sorted(PARADES))
    parser.add_argument("--sailor", choices=["sailor", "infantry"])
    parser.add_argument("--infantry", default="infantry")
    parser.add_argument("--child")
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
    town = args.town or rng.choice(["harbor", "hill", "river"])
    parade_defaults = {"harbor": "welcome", "hill": "harvest", "river": "lantern"}
    parade = args.parade or parade_defaults[town]
    sailor = args.sailor or rng.choice(["sailor", "infantry"])
    if args.sailor is None:
        if not any(t == town and p == parade and r == sailor for t, p, r in valid_combos()):
            sailor = "sailor" if town != "hill" else "infantry"
    child = args.child or rng.choice(CHILDREN)
    return StoryParams(town, parade, sailor, args.infantry, child)


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


CURATED = [
    StoryParams("harbor", "welcome", "sailor", "infantry", "Lina", 3),
    StoryParams("hill", "harvest", "infantry", "infantry", "Milo", 8),
    StoryParams("river", "lantern", "sailor", "infantry", "Pia", 13),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(0, args.n)):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                print(exc, file=sys.stderr)
                raise SystemExit(2)
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
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.town} / {p.parade}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
