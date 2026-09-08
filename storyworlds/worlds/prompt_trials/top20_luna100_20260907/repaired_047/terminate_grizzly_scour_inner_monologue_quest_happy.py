#!/usr/bin/env python3
"""
A standalone superhero storyworld about a quest to stop a grizzly's runaway
storm machine before it can terminate every warm light in the valley.
Seed words: terminate, grizzly, scour.
Narrative instruments: inner monologue, quest, happy ending.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
setting(aurora_valley).
feature(inner_monologue).
feature(quest).
feature(happy_ending).
hero(luna).
enemy(grizzly).
goal(restore_lights).
tool(compass).
tool(star_lantern).
tool(silver_rope).
tool(thunder_badge).
safe_tool(compass).
safe_tool(star_lantern).
safe_tool(silver_rope).
safe_tool(thunder_badge).
quest_story(S) :- setting(S), feature(inner_monologue), feature(quest),
                   feature(happy_ending), hero(luna), enemy(grizzly),
                   goal(restore_lights).
can_stop_machine :- quest_story(aurora_valley), safe_tool(compass),
                    safe_tool(star_lantern).
happy_result :- can_stop_machine, goal(restore_lights).
"""


PLACE = "Aurora Valley"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    foe: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    danger: str
    failed_try: str
    clue: str
    luna_line: str
    foe_line: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = PLACE
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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            details = []
            if entity.meters:
                details.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                details.append(f"memes={dict(entity.memes)}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) "
                f"label={entity.label!r} {' '.join(details)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        key="frozen_beacon",
        opening="Luna was checking the moonlit beacon above Aurora Valley",
        danger="when a dark machine on the ridge began sucking the warmth from every lantern below",
        failed_try="she blasted its iron door, but the cold only made the gears turn faster",
        clue="the machine's shadow pointed toward a tiny silver switch beneath the snow",
        luna_line='"If the shadow points there, the answer must be there too," Luna said.',
        foe_line='"You cannot stop my storm," the grizzly boomed from inside.',
        repair="scoured the snow away with her star-lantern, turned the silver switch, and held the compass steady",
        result="The machine coughed, released the stolen warmth, and went quiet before the last lantern faded.",
        ending="warm lights blossomed across the valley while the grizzly shared cocoa with the neighbors",
    ),
    Scenario(
        key="runaway_roof",
        opening="Luna was flying over the village roofs after a bright afternoon patrol",
        danger="when the grizzly's storm engine tore loose and began dragging clouds toward the children's school",
        failed_try="she pulled on the engine's chain, but the runaway roof spun even faster",
        clue="a painted arrow on the chain pointed back to the engine's loose anchor",
        luna_line='"The chain is not the problem; the anchor is," Luna told herself.',
        foe_line='"I only wanted a louder thunder song," the grizzly admitted.',
        repair="scoured mud from the anchor, looped the silver rope through its ring, and pulled with the grizzly",
        result="The roof settled gently, and the storm clouds opened into a harmless silver drizzle.",
        ending="the children waved from the school steps as the grizzly helped plant umbrellas in a neat row",
    ),
    Scenario(
        key="vanished_sun",
        opening="At sunrise, Luna noticed that the valley's golden sunbeam had disappeared",
        danger="because the grizzly had trapped it inside a crystal tower that was beginning to crack",
        failed_try="she tapped the tower with her power, but each tap made another crack",
        clue="the cracks formed a map leading to a soft place in the crystal base",
        luna_line='"A strong hero can still choose a gentle touch," Luna thought.',
        foe_line='"I thought keeping the sun would make me powerful," the grizzly whispered.',
        repair="scoured dust from the soft place, pressed the thunder badge against it, and opened the tower slowly",
        result="The sunbeam slipped free without breaking the tower or hurting anyone.",
        ending="morning poured over the valley, and the grizzly used the crystal tower as a warm greenhouse",
    ),
    Scenario(
        key="echo_cave",
        opening="Luna followed a blue signal into the Echo Cave beyond the village",
        danger="where a grizzly-made alarm was shouting so loudly that nobody could hear the rescue bell",
        failed_try="she shouted over it, but the cave threw her voice back in a dozen confusing echoes",
        clue="one quiet patch behind a stone showed where the alarm's sound pipe ended",
        luna_line='"Listening will be stronger than shouting," Luna decided.',
        foe_line='"I built the alarm to warn everyone, but now it warns nobody," said the grizzly.',
        repair="scoured pebbles from the quiet patch, capped the sound pipe, and moved the alarm toward the cave mouth",
        result="The rescue bell rang clearly, and the valley could hear it from every path.",
        ending="the grizzly painted friendly arrows in the cave while Luna listened for every new bell",
    ),
    Scenario(
        key="river_shadow",
        opening="Luna was guarding the stepping stones when a giant shadow crossed the river",
        danger="and a grizzly-powered bridge began lowering toward a nest of ducklings",
        failed_try="she pushed the bridge upward, but its rusty wheel jammed tighter",
        clue="a yellow feather was caught beneath the wheel beside a hidden release",
        luna_line='"The smallest life here needs the biggest care," Luna thought.',
        foe_line='"I never saw the nest," the grizzly said, lowering his paws.',
        repair="scoured the wheel clean, freed the feather, and used the compass to guide the bridge into its safe notch",
        result="The ducklings paddled away, and the bridge became a steady crossing again.",
        ending="the grizzly built a little sign for the nest while Luna led travelers across the shining stones",
    ),
    Scenario(
        key="silent_sky",
        opening="Luna reached the highest hill when every bird in the valley suddenly went quiet",
        danger="because the grizzly's cloud net had caught the morning wind",
        failed_try="she tugged the net from above, but the trapped wind pulled her toward the cliff",
        clue="a bright thread ran from the net to a stone ring at the hill's edge",
        luna_line='"I need a path back before I make the rescue," Luna reminded herself.',
        foe_line='"Please help me undo it," called the grizzly. "The net is stuck too."',
        repair="scoured grit from the stone ring, anchored the silver rope, and loosened the cloud net from below",
        result="The wind returned in a gentle rush, carrying birdsong over the hill.",
        ending="the grizzly turned the cloud net into a kite while Luna watched the sky sparkle",
    ),
]


NAMES = ["Luna", "Mara", "Sol", "Iris", "Nova", "Piper"]
FOES = ["grizzly", "storm grizzly", "mountain grizzly"]
TOOLS = ["compass", "star-lantern", "silver-rope", "thunder-badge"]

TOOL_ACTIONS = {
    "compass": "held the compass level to follow the safest direction",
    "star-lantern": "raised the star-lantern to reveal what the darkness hid",
    "silver-rope": "fastened the silver rope so no one would slip during the rescue",
    "thunder-badge": "pressed the thunder badge to the machine's gentle-control mark",
}


def valid_tools() -> list[str]:
    return list(TOOLS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The hero needs a name.")
    if params.foe not in FOES:
        raise StoryError("The foe must be a grizzly or a named grizzly kind.")
    if params.tool not in TOOLS:
        raise StoryError("The quest needs a safe rescue tool.")
    if params.name.lower() == params.foe.lower():
        raise StoryError("The hero and the grizzly must be different characters.")


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        foe=rng.choice(FOES),
        tool=rng.choice(TOOLS),
        seed=rng.randrange(2**31),
    )


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", "superhero", params.name))
    foe = world.add(Entity("foe", "opponent", params.foe))
    tool = world.add(Entity("tool", "rescue_tool", params.tool, owner=params.name))
    valley = world.add(Entity("valley", "place", PLACE))
    world.facts.update(
        hero=hero,
        foe=foe,
        tool=tool,
        valley=valley,
        setting=PLACE,
        feature_inner_monologue=True,
        feature_quest=True,
        feature_happy_ending=True,
        goal="restore the valley's safety",
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    foe = world.get("foe")
    tool = world.get("tool")
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)

    hero.bump_meme("courage")
    foe.bump_meme("confusion")
    tool.bump_meter("readiness")

    world.say(f"{scenario.opening}.")
    world.say(
        f"{hero.label} wore a bright cape and carried a {tool.label}. "
        f"The superhero knew a quest was beginning, but did not know how it would end."
    )
    world.para()

    world.say(f"{scenario.danger}.")
    world.say(f"At first, {hero.label} tried to fix everything with speed: {scenario.failed_try}.")
    world.say(f"{hero.label} paused. Inside, the hero thought, \"{scenario.luna_line.strip('\"')}\"")
    world.say(scenario.foe_line)
    world.para()

    hero.bump_meme("patience")
    foe.bump_meme("honesty")
    world.say(f"Then {hero.label} noticed the clue: {scenario.clue}.")
    world.say(
        f"The hero took out the {tool.label} and {TOOL_ACTIONS[tool.label]}."
    )
    world.say(
        f'"Tell me what you see," {hero.label} said. '
        f'"The clue can help both of us."'
    )
    world.say(f'"I see it now," the {foe.label} replied. "Let us repair it together."')
    world.para()

    tool.bump_meter("use", 1)
    hero.bump_meme("trust")
    foe.bump_meme("helpfulness")
    world.say(f"Together, they {scenario.repair}.")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("joy")
    foe.bump_meme("relief")
    world.say(
        f"{hero.label} listened until the valley was safe, and the {foe.label} "
        "learned that power was best used to protect rather than frighten."
    )
    world.say(f"As the happy ending, {scenario.ending}.")
    world.say(
        f"{hero.label} smiled at the quiet machine. The quest had not ended with a defeat; "
        "it had ended with a better choice."
    )

    world.facts.update(
        scenario=scenario.key,
        danger=scenario.danger,
        failed_try=scenario.failed_try,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved=True,
        words=["terminate", "grizzly", "scour"],
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"].label
    foe = facts["foe"].label
    tool = facts["tool"].label
    return [
        f"Write a superhero story in which {hero} goes on a quest to help a {foe}.",
        "Include the words terminate, grizzly, and scour, with an inner monologue and a happy ending.",
        f"Tell a child-friendly adventure where {hero} uses a {tool} to solve a dangerous problem through teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    foe = facts["foe"].label
    tool = facts["tool"].label
    return [
        QAItem(
            question=f"What danger did {hero} discover in the valley?",
            answer=str(facts["danger"]).capitalize() + ".",
        ),
        QAItem(
            question=f"What clue helped {hero} and the {foe} make a better plan?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did the {tool} help during the quest?",
            answer=f"{hero} {TOOL_ACTIONS[tool]}.",
        ),
        QAItem(
            question=f"How did {hero} and the {foe} solve the problem?",
            answer=f"Together, they {facts['repair']}.",
        ),
        QAItem(
            question="What showed that the story had a happy ending?",
            answer=str(facts["ending"]).capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey in which someone faces challenges while trying to reach an important goal.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thought a character has inside their mind.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to stop something or bring it to an end.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="Scour means to clean or search something carefully and thoroughly.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the main worry is resolved and the characters finish in a safe, hopeful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "aurora_valley"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("hero", "luna"),
            asp.fact("enemy", "grizzly"),
            asp.fact("goal", "restore_lights"),
            asp.fact("tool", "compass"),
            asp.fact("tool", "star_lantern"),
            asp.fact("tool", "silver_rope"),
            asp.fact("tool", "thunder_badge"),
            asp.fact("safe_tool", "compass"),
            asp.fact("safe_tool", "star_lantern"),
            asp.fact("safe_tool", "silver_rope"),
            asp.fact("safe_tool", "thunder_badge"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show quest_story/1.\n#show can_stop_machine/0.\n#show happy_result/0."
    )
    model = asp.one_model(program)
    found = {
        (symbol.name, tuple(asp_value(arg) for arg in symbol.arguments))
        for symbol in model
        if symbol.name in {"quest_story", "can_stop_machine", "happy_result"}
    }
    expected = {
        ("quest_story", ("aurora_valley",)),
        ("can_stop_machine", ()),
        ("happy_result", ()),
    }
    if found != expected:
        print("MISMATCH between ASP and Python story gate.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    for seed in (3, 17, 41):
        sample = generate(
            StoryParams(name="Luna", foe="grizzly", tool="compass", seed=seed)
        )
        required = ["terminate", "grizzly", "scour"]
        if any(word not in sample.story.lower() for word in required):
            print("Generated story missed a required seed word.")
            return 1
        if "happy ending" not in sample.story.lower():
            print("Generated story missed the happy-ending instrument.")
            return 1

    print("OK: ASP twin matches the Python gate and generated stories.")
    return 0


def asp_value(symbol) -> object:
    if symbol.type.name == "Number":
        return symbol.number
    if symbol.type.name == "String":
        return symbol.string
    return symbol.name


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show happy_result/0.\n#show quest_story/1."))
    return sorted(
        (symbol.name, tuple(asp_value(arg) for arg in symbol.arguments))
        for symbol in model
        if symbol.name in {"happy_result", "quest_story"}
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Luna", foe="grizzly", tool="compass", seed=11),
    StoryParams(name="Mara", foe="storm grizzly", tool="star-lantern", seed=29),
    StoryParams(name="Nova", foe="mountain grizzly", tool="silver-rope", seed=47),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero quest storyworld with an inner monologue and happy ending."
    )
    parser.add_argument("--name")
    parser.add_argument("--foe", choices=FOES)
    parser.add_argument("--tool", choices=TOOLS)
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.foe:
        params.foe = args.foe
    if args.tool:
        params.tool = args.tool
    reasonableness_gate(params)
    return params


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_story/1.\n#show happy_result/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP-compatible superhero story facts:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and attempts < limit:
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            attempts += 1
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
