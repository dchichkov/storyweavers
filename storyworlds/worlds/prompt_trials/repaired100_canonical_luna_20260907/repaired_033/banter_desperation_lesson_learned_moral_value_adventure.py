#!/usr/bin/env python3
"""
A standalone adventure storyworld about banter, desperation, and a lesson learned.

A young explorer and a boastful companion race to return a glowing compass before
a mountain storm closes the trail. Their playful banter changes when desperation
reveals that courage means asking for help and protecting one another.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


ENTITY_HUMAN = "human"
ENTITY_ANIMAL = "animal"
ENTITY_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    companion: str
    landmark: str
    route: str = "ridge"
    obstacle: str = "storm"
    opening_style: int = 0
    banter_style: int = 0
    lesson_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    mission: str
    danger: str
    clue: str
    first_try: str
    desperate_need: str
    kind_action: str
    useful_plan: str
    final_image: str
    lesson: str


SETTINGS = {
    "the Ember Ridge": "the Ember Ridge",
    "the Whispering Caves": "the Whispering Caves",
    "the Moonlit Marsh": "the Moonlit Marsh",
    "the Cloudstep Pass": "the Cloudstep Pass",
    "the Sunken Garden": "the Sunken Garden",
}

HERO_NAMES = ["Luna", "Mara", "Niko", "Tess", "Ari", "Jo", "Suri"]
COMPANION_NAMES = ["Pip", "Bram", "Kito", "Moss", "Rook", "Tavi"]
LANDMARKS = [
    "the old watchtower",
    "the bell at the cliff edge",
    "the hidden ranger hut",
    "the silver bridge",
    "the lantern shrine",
]

ROUTES = {
    "ridge": "the narrow ridge trail",
    "canyon": "the red-stone canyon",
    "forest": "the dark pine path",
    "river": "the rushing riverbank",
    "stairs": "the broken stairway",
}

SCENARIOS = {
    "storm": Scenario(
        mission="carry a glowing compass to the ranger before the mountain storm swallowed the trail",
        danger="a wall of rain rolled over the ridge and washed away the bright trail marks",
        clue="heard three hollow knocks from the old watchtower whenever lightning flashed",
        first_try="pointed at a distant cairn and claimed it was definitely the way, although the cairn was actually a sleeping goat",
        desperate_need="had lost the trail and could no longer tell the safe path from the slippery edge",
        kind_action="sheltered beside a boulder, shared the last dry biscuit, and listened for the watchtower's knocks",
        useful_plan="counted the knocks and tied a bright scarf between safe stones",
        final_image="the ranger lifting the glowing compass while their wet scarf fluttered like a tiny flag",
        lesson="When fear gets loud, calm teamwork can turn a mystery into a path.",
    ),
    "bridge": Scenario(
        mission="return a brass bridge key before the river rose over the stepping stones",
        danger="the rope bridge snapped at one side and swung above the foaming water",
        clue="noticed fresh blue paint on stones leading toward a fallen cedar",
        first_try="announced that a fearless adventurer would simply leap across, then measured the leap with a very nervous toe",
        desperate_need="was trapped on the far bank with the key and no safe way back",
        kind_action="stopped the jokes, tested the cedar, and asked the stranded companion to hold the rope",
        useful_plan="made a low handline from the cedar and crossed one careful step at a time",
        final_image="the brass key shining in the ranger's palm while the repaired rope bridge hummed behind them",
        lesson="Bravery is not pretending danger is small; it is making a careful plan together.",
    ),
    "cave": Scenario(
        mission="bring a warm ember to the cave village before its cooking fire went dark",
        danger="a cave-in blocked the marked tunnel and filled the air with dusty darkness",
        clue="felt a cool breeze under a pile of loose stones",
        first_try="challenged the mountain to move aside, which made a pebble land neatly on the speaker's helmet",
        desperate_need="was running out of air and could not find the way back to the entrance",
        kind_action="covered both mouths with cloth, shared the lantern, and cleared only the smallest safe stones",
        useful_plan="followed the cool breeze and placed pebbles as a trail for the return journey",
        final_image="the village fire waking from one orange ember as the explorers arrived covered in harmless gray dust",
        lesson="In desperation, small safe steps are wiser than a grand and dangerous gesture.",
    ),
    "marsh": Scenario(
        mission="deliver a moon seed across the marsh before dawn so the night flowers would bloom",
        danger="mist hid the stepping logs and the mud tugged at every boot",
        clue="saw fireflies gathering in a straight line above the safest puddles",
        first_try="declared the mud afraid of bold explorers, then sank up to one knee and lost a sock",
        desperate_need="was stuck in the deepest mud with the moon seed held above the water",
        kind_action="lay flat on a dry mat, reached out a walking pole, and told the trapped friend not to pull alone",
        useful_plan="followed the fireflies and pulled together on a steady count",
        final_image="the moon seed opening into a pale flower as two muddy explorers laughed beside it",
        lesson="Asking for help is a strength when it keeps a precious goal and a friend safe.",
    ),
    "garden": Scenario(
        mission="guide a lost messenger through the Sunken Garden to the waiting keeper",
        danger="the garden gates turned in the wind and every statue cast a misleading shadow",
        clue="found tiny crumbs beside one statue, showing where the messenger had passed",
        first_try="followed the tallest shadow and marched directly into a fountain",
        desperate_need="was frightened, lost, and clutching a message that had begun to tear",
        kind_action="wrapped the message in oilcloth, spoke gently, and searched for matching crumbs",
        useful_plan="marked each checked statue with a pebble and followed the crumbs to the keeper's door",
        final_image="the keeper reading the dry message while the messenger's crumbs made a cheerful trail across the tiles",
        lesson="Careful attention and gentle words can guide someone better than noisy confidence.",
    ),
}


OPENINGS = [
    "{hero} kept a travel journal, but today the mountains were writing the dangerous parts themselves.",
    "At sunrise, {hero} tightened {hero_poss} bootlaces and checked the little expedition twice.",
    "Every adventure began with a map, a snack, and one question nobody wanted to ask: what could go wrong?",
    "{hero} had crossed streams, climbed walls, and once escaped a very determined goose.",
    "The trail ahead looked small on the map and enormous in real life.",
]

BANTER = [
    '"Try not to get lost before we leave the starting point," {companion} said.',
    '"If the trail bites, I am blaming your map," {companion} announced.',
    '"That is not a heroic plan," {hero} replied. "It is barely a plan wearing a hat."',
    '"I was born ready," {companion} said, while checking the same pocket three times.',
    '"You call that a shortcut?" {hero} asked. "It has more bushes than road."',
    '"The bushes are friendly," {companion} said. "They have not bitten me yet."',
]

LESSON_STYLES = [
    "The lesson stayed with them long after the trail dried.",
    "Neither explorer forgot what the storm had taught them.",
    "From that day onward, their adventures began with listening as well as looking.",
    "The mountain offered no applause, but the two friends understood the lesson.",
]

ASP_RULES = r"""
% The mission is unsafe when the danger is active and no shared plan exists.
unsafe(S) :- setting(S), danger_active, not shared_plan.

% Desperation can become a turning point when a helper is heard.
turn(S) :- unsafe(S), desperate_need, helper_heard, shared_plan.

% A valid adventure has danger, a turn, and a safe resolution.
valid_story(S) :- setting(S), danger_active, turn(S), resolved.
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines.extend(
        [
            asp.fact("danger_active"),
            asp.fact("desperate_need"),
            asp.fact("helper_heard"),
            asp.fact("shared_plan"),
            asp.fact("resolved"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(SETTINGS)
    found = {name for (name,) in asp_valid()}
    if expected == found:
        print(f"OK: ASP model covers {len(expected)} settings.")
        return 0
    print("MISMATCH between Python and ASP setting coverage.")
    print("only python:", sorted(expected - found))
    print("only asp:", sorted(found - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about banter, desperation, and a lesson learned."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--landmark")
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--obstacle", choices=SCENARIOS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        companion=args.companion or rng.choice(COMPANION_NAMES),
        landmark=args.landmark or rng.choice(LANDMARKS),
        route=args.route or rng.choice(list(ROUTES)),
        obstacle=args.obstacle or rng.choice(list(SCENARIOS)),
        opening_style=rng.randrange(len(OPENINGS)),
        banter_style=rng.randrange(len(BANTER)),
        lesson_style=rng.randrange(len(LESSON_STYLES)),
    )


def validate(params: StoryParams) -> None:
    if not params.hero.strip() or not params.companion.strip():
        raise StoryError("The hero and companion need names.")
    if params.hero.lower() == params.companion.lower():
        raise StoryError("The hero and companion need different names for clear banter.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown route: {params.route}.")
    if params.obstacle not in SCENARIOS:
        raise StoryError(f"Unknown obstacle: {params.obstacle}.")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="hero",
            kind=ENTITY_HUMAN,
            type="explorer",
            label=params.hero,
            phrase=params.hero,
            meters={"energy": 1.0, "safety": 1.0},
            memes={"confidence": 1.0, "worry": 0.0, "trust": 0.5},
            location="trailhead",
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind=ENTITY_HUMAN,
            type="explorer",
            label=params.companion,
            phrase=params.companion,
            meters={"energy": 1.0, "safety": 1.0},
            memes={"confidence": 1.0, "worry": 0.0, "trust": 0.5},
            location="trailhead",
        )
    )
    compass = world.add(
        Entity(
            id="mission_token",
            kind=ENTITY_OBJECT,
            type="mission token",
            label="glowing compass",
            phrase="the glowing compass",
            meters={"brightness": 1.0, "safe": 1.0, "delivered": 0.0},
            owner=params.hero,
            location="trailhead",
        )
    )
    world.add(
        Entity(
            id="landmark",
            kind=ENTITY_OBJECT,
            type="landmark",
            label=params.landmark,
            phrase=params.landmark,
            meters={"visible": 0.0},
            location="destination",
        )
    )

    world.facts.update(
        params=params,
        scenario=SCENARIOS[params.obstacle],
        hero=hero,
        companion=companion,
        compass=compass,
        danger_active=False,
        need_understood=False,
        helper_heard=False,
        shared_plan=False,
        resolved=False,
    )
    return world


def act_opening(world: World) -> None:
    params = world.facts["params"]
    hero = world.get("hero")
    companion = world.get("companion")
    scenario = world.facts["scenario"]

    hero_poss = "their" if hero.label.lower() in {"luna", "mara", "tess", "suri"} else "his"
    world.say(OPENINGS[params.opening_style].format(hero=hero.label, hero_poss=hero_poss))
    world.say(
        f"In {world.setting}, {hero.label} and {companion.label} took {ROUTES[params.route]} "
        f"because they had to {scenario.mission}."
    )
    world.say(BANTER[params.banter_style].format(hero=hero.label, companion=companion.label))
    world.say(
        f"{hero.label} tapped the {params.landmark} on the map, while {companion.label} "
        f"pretended not to worry about the long climb."
    )


def act_danger(world: World) -> None:
    params = world.facts["params"]
    hero = world.get("hero")
    companion = world.get("companion")
    compass = world.get("mission_token")
    scenario = world.facts["scenario"]

    hero.location = "danger zone"
    companion.location = "danger zone"
    compass.location = "danger zone"
    hero.meters["safety"] = 0.4
    companion.meters["safety"] = 0.4
    world.facts["danger_active"] = True

    world.para()
    world.say(f"At midday, {scenario.danger}.")
    world.say(f"{hero.label} tried to solve it quickly: {hero.label} {scenario.first_try}.")
    world.say(
        f"The banter vanished when {companion.label} admitted, \"I am in desperation. "
        f"I cannot find the safe way, and I am scared.\""
    )
    world.say(f"{hero.label} stopped at once and asked, \"What do you need me to notice?\"")
    world.say(f"{companion.label} answered, \"{scenario.clue}.\"")
    world.facts["helper_heard"] = True


def act_turn(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    scenario = world.facts["scenario"]

    companion.memes["worry"] = 1.0
    companion.memes["trust"] = 1.0
    hero.memes["confidence"] = 0.7
    hero.memes["trust"] = 1.0
    world.facts["need_understood"] = True

    world.say(
        f"That clue explained the trouble: {companion.label} {scenario.desperate_need}."
    )
    world.say(
        f"{hero.label} did not tease {companion.label}. Instead, {hero.label} "
        f"{scenario.kind_action}."
    )
    world.say(f'"We can do this carefully," {hero.label} said. "Your clue and my hands can work together."')
    world.say(f'"Then I will watch the route," {companion.label} replied. "You watch our steps."')
    world.say(f"Together they {scenario.useful_plan}.")
    world.facts["shared_plan"] = True


def act_resolution(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    compass = world.get("mission_token")
    landmark = world.get("landmark")
    scenario = world.facts["scenario"]
    params = world.facts["params"]

    hero.location = "destination"
    companion.location = "destination"
    compass.location = "destination"
    landmark.meters["visible"] = 1.0
    compass.meters["delivered"] = 1.0
    hero.meters["safety"] = 1.0
    companion.meters["safety"] = 1.0
    hero.memes["confidence"] = 1.0
    companion.memes["worry"] = 0.0
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"At last, {hero.label} and {companion.label} reached {params.landmark} and "
        f"placed the glowing compass in the keeper's waiting hands."
    )
    world.say(f"Their adventure ended with {scenario.final_image}.")
    world.say(
        f"{companion.label} grinned. \"Next time, I will bring two maps.\" "
        f"{hero.label} replied, \"And I will listen before calling anything a shortcut.\""
    )
    world.say(LESSON_STYLES[params.lesson_style])
    world.say(f"Lesson Learned: {scenario.lesson}")
    world.say(
        "Moral Value: Courage grows through honest words, careful choices, and helping "
        "a friend instead of leaving them alone with fear."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    act_danger(world)
    act_turn(world)
    act_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write an adventure in {world.setting} about {params.hero} and {params.companion}.",
        f"Include banter that changes when {params.companion} faces desperation: {scenario.desperate_need}.",
        f"End with a Lesson Learned and a Moral Value about teamwork and courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question=f"What mission did {params.hero} and {params.companion} undertake?",
            answer=f"They traveled through {world.setting} to {scenario.mission}.",
        ),
        QAItem(
            question=f"What danger threatened the adventure?",
            answer=f"{scenario.danger.capitalize()}",
        ),
        QAItem(
            question=f"How did banter change during the adventure?",
            answer=(
                f"At first, {params.hero} and {params.companion} joked with each other. "
                f"When {params.companion} faced desperation, the jokes stopped and they spoke honestly about fear and safety."
            ),
        ),
        QAItem(
            question=f"What clue did {params.companion} provide?",
            answer=f"{params.companion} {scenario.clue}.",
        ),
        QAItem(
            question="How did the explorers solve the problem?",
            answer=f"They listened to the clue and {scenario.useful_plan}.",
        ),
        QAItem(
            question="What was the Lesson Learned?",
            answer=f"Lesson Learned: {scenario.lesson}",
        ),
        QAItem(
            question="What Moral Value does the story express?",
            answer=(
                "Moral Value: Courage grows through honest words, careful choices, "
                "and helping a friend instead of leaving them alone with fear."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is banter?",
            answer="Banter is playful back-and-forth teasing between people who can understand one another's feelings and boundaries.",
        ),
        QAItem(
            question="What does desperation mean?",
            answer="Desperation is a powerful feeling of needing help or a solution because a situation seems frightening or urgent.",
        ),
        QAItem(
            question="What makes an adventure?",
            answer="An adventure is a journey with a goal, uncertainty, obstacles, choices, and a changed understanding at the end.",
        ),
        QAItem(
            question="Why can asking for help be brave?",
            answer="Asking for help can be brave because it admits the truth about a problem and gives people a chance to solve it safely together.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a principle about how people should act, such as honesty, kindness, responsibility, or courage.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = [f"type={entity.type}", f"location={entity.location}"]
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {entity.label} ({', '.join(parts)})")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(
        setting="the Ember Ridge",
        hero="Luna",
        companion="Pip",
        landmark="the old watchtower",
        route="ridge",
        obstacle="storm",
        opening_style=0,
        banter_style=1,
        lesson_style=0,
    ),
    StoryParams(
        setting="the Whispering Caves",
        hero="Mara",
        companion="Bram",
        landmark="the hidden ranger hut",
        route="cave",
        obstacle="cave",
        opening_style=1,
        banter_style=3,
        lesson_style=1,
    ),
    StoryParams(
        setting="the Moonlit Marsh",
        hero="Tess",
        companion="Kito",
        landmark="the lantern shrine",
        route="marsh",
        obstacle="marsh",
        opening_style=2,
        banter_style=4,
        lesson_style=2,
    ),
    StoryParams(
        setting="the Sunken Garden",
        hero="Ari",
        companion="Rook",
        landmark="the silver bridge",
        route="stairs",
        obstacle="garden",
        opening_style=3,
        banter_style=5,
        lesson_style=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("Compatible ASP story settings:")
        for setting, in asp_valid():
            print(f"  {setting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(0, args.n) and attempts < max(50, args.n * 30):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
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
            params = sample.params
            header = (
                f"### {params.hero} / {params.companion} / "
                f"{params.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
