#!/usr/bin/env python3
"""
A small heartwarming storyworld about carving a wooden keepsake and listening
for the sound effects that reveal how careful work changes a worried heart.
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
class Setting:
    id: str
    place: str
    affords: set[str]


@dataclass
class Tool:
    id: str
    label: str
    action: str
    sound: str


@dataclass(frozen=True)
class Design:
    id: str
    object_label: str
    shape: str
    meaning: str
    final_image: str


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    worry: str
    first_plan: str
    clue: str
    exchange: tuple[str, str]
    turning_action: str
    helper: str
    sounds: str
    resolution: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    design: str
    tool: str
    name: str
    companion: str
    trait: str
    scenario: str = ""
    telling: str = ""
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
    "shed": Setting(
        id="shed",
        place="the little workshop beside the garden",
        affords={"carving"},
    )
}

TOOLS = {
    "small_knife": Tool(
        id="small_knife",
        label="a small carving knife",
        action="shaved one thin curl",
        sound="scritch-scritch",
    ),
    "wood_chisel": Tool(
        id="wood_chisel",
        label="a round-ended chisel",
        action="tapped a shallow groove",
        sound="tap-tap",
    ),
    "sandpaper": Tool(
        id="sandpaper",
        label="a square of smooth sandpaper",
        action="rubbed a rough edge",
        sound="shh-shh",
    ),
}

DESIGNS = {
    "heart": Design(
        id="heart",
        object_label="a little wooden heart",
        shape="a heart",
        meaning="a promise that someone is loved and remembered",
        final_image="a small heart glowing warmly in the window light",
    ),
    "bird": Design(
        id="bird",
        object_label="a wooden bird",
        shape="a bird with lifted wings",
        meaning="a brave wish to keep moving toward home",
        final_image="the carved bird casting a wing-shaped shadow on the wall",
    ),
    "star": Design(
        id="star",
        object_label="a wooden star",
        shape="a five-pointed star",
        meaning="a small light for a dark or lonely evening",
        final_image="the star resting beside the lamp like a second little light",
    ),
}

PEOPLE = [
    ("Luna", "grandmother"),
    ("Milo", "neighbor"),
    ("Ari", "father"),
    ("Nell", "friend"),
    ("Sam", "brother"),
]

TRAITS = ["patient", "hopeful", "quiet", "careful", "kind"]
TELLINGS = ["sound_first", "clue_first", "dialogue_first", "quiet_start", "warm_finish"]

SCENARIOS = {
    item.id: item
    for item in [
        Scenario(
            id="birthday_surprise",
            opening="Luna wanted to carve a birthday gift for her grandmother before the first evening star appeared.",
            worry="But the blank piece of cedar looked stubborn, and Luna worried that her hands were too shaky to make anything beautiful.",
            first_plan="She pressed hard, hoping speed would solve the problem.",
            clue="The knife skipped and left a jagged mark, while a loose curl of wood pointed along the grain.",
            exchange=(
                '"It does not have to be fast," said Grandma May. "What can the wood tell you?"',
                '"Maybe I should listen before I push," Luna answered.',
            ),
            turning_action="Luna turned the cedar, followed the grain, and made each small cut away from her fingers.",
            helper="Grandma May steadied the board and showed Luna how to pause after every curve.",
            sounds="Scritch-scritch went the knife, then shh-shh went the sandpaper.",
            resolution="The rough mark softened, and the shape slowly became a heart.",
            ending="When the candle was lit, the little heart sat beside the birthday cake, smooth enough to hold the candlelight.",
            lesson="Careful hands can turn a mistake into part of a loving gift.",
        ),
        Scenario(
            id="welcome_home",
            opening="Milo wanted to carve a wooden bird for his father, who was coming home after a long journey.",
            worry="The workshop felt unusually quiet, and Milo feared that the waiting had made his heart too heavy to work.",
            first_plan="He tried to cut the wings in one long sweep.",
            clue="The cedar gave a sharp crack, and one wing tilted lower than the other.",
            exchange=(
                '"That sound means stop and look," said his friend Nell.',
                '"Then I will make the bird listen to me too," Milo said, taking a breath.',
            ),
            turning_action="Milo turned the block and carved the lower wing in tiny matching steps.",
            helper="Nell held a lantern close and helped compare the two sides without rushing.",
            sounds="Tap-tap answered from the chisel, and shh-shh followed along the wing.",
            resolution="The uneven wing became a gentle lift, as if the bird were ready to fly home.",
            ending="At the gate, Milo placed the bird in his father's hands, and its raised wings pointed toward the warm house.",
            lesson="A patient repair can give waiting a hopeful shape.",
        ),
        Scenario(
            id="storm_light",
            opening="Ari decided to carve a wooden star for Nell during a rainy afternoon.",
            worry="The clouds made the room dim, and Nell had been afraid of the thunder since morning.",
            first_plan="Ari began carving deep points so the star would be finished before the next rumble.",
            clue="The chisel struck too sharply, and a thin point broke away.",
            exchange=(
                '"The storm is loud enough already," Nell said. "Can the star be gentle?"',
                '"Yes," Ari replied. "We can make its light in little sounds."',
            ),
            turning_action="Ari rounded the broken point and carved five shallow rays instead of forcing a sharp edge.",
            helper="Nell held the lamp near the wood and counted each quiet tap.",
            sounds="Tap-tap, pause; tap-tap, pause—the little rhythm stayed calm beneath the rain.",
            resolution="The star became softer and stronger, with a rounded point that shone beside the lamp.",
            ending="When thunder rolled again, Nell held the star close and watched its small shadow stay steady.",
            lesson="Gentle work can make room for courage.",
        ),
        Scenario(
            id="thank_you",
            opening="Sam wanted to carve a wooden heart to thank his neighbor for caring for his lost kitten.",
            worry="He had many grateful words, but none seemed large enough to fit inside a small piece of wood.",
            first_plan="He planned to carve every word around the edge.",
            clue="The first letters crowded together and made the rim weak.",
            exchange=(
                '"You do not need to carve all the words," said the neighbor, Jo.',
                '"Then I will carve the feeling," Sam replied.',
            ),
            turning_action="Sam erased the crowded letters and shaped one deep, simple heart.",
            helper="Jo held the wood while Sam traced one clean line around its middle.",
            sounds="Scritch-scritch marked the line, and shh-shh smoothed the places where worry had shown.",
            resolution="The heart grew plain enough for anyone to understand.",
            ending="Sam gave it to Jo, and the little heart rested in Jo's palm as warmly as a spoken thank-you.",
            lesson="A simple gift can carry a very big feeling.",
        ),
    ]
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting_id, design_id, tool_id)
        for setting_id, setting in SETTINGS.items()
        for activity in setting.affords
        if activity == "carving"
        for design_id in DESIGNS
        for tool_id in TOOLS
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming carving stories with gentle sound effects."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--design", choices=DESIGNS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--scenario", choices=SCENARIOS)
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


def _validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("The story must take place in the little workshop beside the garden.")
    if params.design not in DESIGNS:
        raise StoryError("Choose a known wooden design.")
    if params.tool not in TOOLS:
        raise StoryError("Choose a carving tool from the workshop.")
    if not params.name.strip():
        raise StoryError("The carver needs a name.")
    if not params.companion.strip():
        raise StoryError("The story needs someone to share the work or its meaning.")
    if params.scenario not in SCENARIOS:
        raise StoryError("Choose a known carving situation.")


def tell(params: StoryParams, rng: random.Random) -> World:
    _validate(params)
    setting = SETTINGS[params.setting]
    design = DESIGNS[params.design]
    tool = TOOLS[params.tool]
    scenario = SCENARIOS[params.scenario]

    world = World(setting)
    carver = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"skill": 0.2, "worry": 1.0},
        memes={"patience": 0.0, "love": 1.0},
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="helper",
        label=params.companion,
        meters={"warmth": 1.0},
        memes={"trust": 1.0},
    ))
    wood = world.add(Entity(
        id="cedar",
        kind="thing",
        type="wood",
        label="the cedar",
        meters={"roughness": 1.0, "shape": 0.0},
        memes={"meaning": 0.0},
    ))
    keepsake = world.add(Entity(
        id="keepsake",
        kind="thing",
        type=design.id,
        label=design.object_label,
        meters={"roughness": 1.0, "shape": 0.0},
        memes={"meaning": 0.0},
    ))

    openers = {
        "sound_first": f"{tool.sound} went the first time {params.name}, a {params.trait} carver, touched the cedar.",
        "clue_first": f"{params.name}, a {params.trait} carver, noticed a pale curl of cedar on the workshop floor.",
        "dialogue_first": f'"I want to make something that lasts," said {params.name}, a {params.trait} carver.',
        "quiet_start": f"The workshop beside the garden was quiet when {params.name}, a {params.trait} carver, opened the cedar box.",
        "warm_finish": f"{params.name}, a {params.trait} carver, had chosen cedar because its warm smell reminded everyone of home.",
    }
    world.say(openers[params.telling])
    world.say(scenario.opening)
    world.say(f"The plan was to carve {design.object_label} as {design.meaning}.")
    world.para()

    world.say(scenario.worry)
    world.say(scenario.first_plan)
    world.say(scenario.clue)
    world.trace.append("The first attempt raised worry and revealed the direction of the wood.")
    world.facts["clue"] = scenario.clue
    world.para()

    world.say(scenario.exchange[0])
    world.say(scenario.exchange[1])
    world.say("The answer changed the plan: the carver would listen to the wood instead of fighting it.")
    carver.meters["worry"] = 0.5
    carver.memes["patience"] = 1.0
    world.facts["dialogue_changed_plan"] = True
    world.para()

    world.say(scenario.turning_action)
    world.say(scenario.helper)
    world.say(f"{tool.action.capitalize()}—{tool.sound}—and the cedar gave way in small, safe pieces.")
    world.say(scenario.sounds)
    world.trace.extend(["The grain changed the cutting direction.", "Sound effects marked careful progress."])
    wood.meters["roughness"] = 0.4
    wood.meters["shape"] = 0.7
    keepsake.meters["roughness"] = 0.4
    keepsake.meters["shape"] = 0.7
    world.para()

    world.say(scenario.resolution)
    world.say(f"{params.name} ran a fingertip over the edge and found no sharp splinter.")
    keepsake.meters["roughness"] = 0.0
    keepsake.meters["shape"] = 1.0
    keepsake.memes["meaning"] = 1.0
    carver.meters["skill"] = 1.0
    carver.meters["worry"] = 0.0
    world.facts["resolved"] = True
    world.trace.append("The finished keepsake was smooth, recognizable, and safe to hold.")
    world.para()

    world.say(scenario.ending)
    world.say(f"The carved {design.shape} now held {design.meaning}.")
    if params.telling == "warm_finish":
        world.say(f"{params.name} smiled because {scenario.lesson.lower()}")
    else:
        world.say(f"{params.name} carried this lesson from the workshop: {scenario.lesson}")
    world.facts.update(
        carver=carver,
        companion=companion,
        wood=wood,
        keepsake=keepsake,
        design=design,
        tool=tool,
        scenario=scenario,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    design: Design = world.facts["design"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about carving {design.object_label} in a small workshop.",
        f"Use the sound effect {tool.sound} to show careful carving and emotional change.",
        "Include dialogue that helps the carver change an unsafe first plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    design: Design = world.facts["design"]  # type: ignore[assignment]
    carver: Entity = world.facts["carver"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {carver.label} decide to carve?",
            answer=f"{carver.label} decided to carve {design.object_label}.",
        ),
        QAItem(
            question="What worry made the carving difficult at first?",
            answer=scenario.worry,
        ),
        QAItem(
            question="What clue changed the carver's first plan?",
            answer=scenario.clue,
        ),
        QAItem(
            question="What did the spoken exchange teach the carver to do?",
            answer="The exchange taught the carver to listen to the wood, follow its grain, and work in small safe pieces instead of pushing too hard.",
        ),
        QAItem(
            question="Which sound effects showed the careful work?",
            answer=scenario.sounds,
        ),
        QAItem(
            question="How did the story end?",
            answer=scenario.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to carve?",
            answer="To carve means to shape wood or another material by carefully cutting or scraping it.",
        ),
        QAItem(
            question="Why should a child use a carving tool with an adult's help?",
            answer="A carving tool can be sharp, so a child should use it only with a trusted adult's guidance and careful safety rules.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are written or spoken sounds, such as scritch-scritch or tap-tap, that help us imagine an action.",
        ),
        QAItem(
            question="Why can sanding help after carving?",
            answer="Sanding can smooth rough edges and remove small splinters so the finished object is safer to hold.",
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
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:8}) meters={meters} memes={memes}")
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
safe_tool(T) :- tool(T), carving_tool(T).
meaningful(D) :- design(D), finished(D).
story_ok(S,D,T) :- setting(S), design(D), tool(T), affords(S,carving),
                    safe_tool(T), meaningful(D).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for activity in setting.affords:
            lines.append(asp.fact("affords", setting_id, activity))
    for tool_id in TOOLS:
        lines.extend([
            asp.fact("tool", tool_id),
            asp.fact("carving_tool", tool_id),
        ])
    for design_id in DESIGNS:
        lines.extend([
            asp.fact("design", design_id),
            asp.fact("finished", design_id),
        ])
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "story_ok"))


def asp_verify() -> int:
    python_count = len(valid_combos())
    try:
        asp_count = len(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if python_count != asp_count:
        print(f"MISMATCH: Python has {python_count} combos; ASP has {asp_count}.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "carv" not in sample.story.lower():
            print("MISMATCH: curated story failed generation.")
            return 1
    print(f"OK: Python and ASP both recognize {python_count} carving combinations.")
    print(f"OK: verified {len(CURATED)} generated stories.")
    return 0


CURATED = [
    StoryParams(
        setting="shed",
        design="heart",
        tool="small_knife",
        name="Luna",
        companion="Grandma May",
        trait="patient",
        scenario="birthday_surprise",
        telling="sound_first",
        seed=17,
    ),
    StoryParams(
        setting="shed",
        design="bird",
        tool="wood_chisel",
        name="Milo",
        companion="Nell",
        trait="hopeful",
        scenario="welcome_home",
        telling="dialogue_first",
        seed=31,
    ),
    StoryParams(
        setting="shed",
        design="star",
        tool="sandpaper",
        name="Ari",
        companion="Nell",
        trait="careful",
        scenario="storm_light",
        telling="quiet_start",
        seed=53,
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "shed":
        raise StoryError("This small storyworld only includes the workshop beside the garden.")
    if args.design and args.design not in DESIGNS:
        raise StoryError("That design is not available in this workshop.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("That tool is not available for this carving story.")

    if args.name:
        name = args.name
        companion = args.companion or rng.choice([person for person, _ in PEOPLE if person != name])
    elif args.companion:
        companion = args.companion
        name = rng.choice([person for person, _ in PEOPLE if person != companion])
    else:
        name, companion = rng.choice(PEOPLE)
        if companion == name:
            companion = "Jo"

    return StoryParams(
        setting="shed",
        design=args.design or rng.choice(sorted(DESIGNS)),
        tool=args.tool or rng.choice(sorted(TOOLS)),
        name=name,
        companion=companion,
        trait=args.trait or rng.choice(TRAITS),
        scenario=args.scenario or rng.choice(sorted(SCENARIOS)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def generate(params: StoryParams) -> StorySample:
    detail_seed = params.seed if params.seed is not None else sum(
        ord(char) for char in f"{params.name}:{params.design}:{params.scenario}:{params.telling}"
    )
    world = tell(params, random.Random(detail_seed ^ 0xC4A7))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        print("Valid carving combinations:")
        for setting_id, design_id, tool_id in valid_combos():
            print(f"  {setting_id} {design_id} {tool_id}")
        return

    if args.n < 1:
        raise SystemExit("The number of stories must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(20, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
