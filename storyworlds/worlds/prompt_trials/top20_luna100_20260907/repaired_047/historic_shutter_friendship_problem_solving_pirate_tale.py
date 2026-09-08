#!/usr/bin/env python3
"""
A standalone pirate-tale storyworld about a historic shutter and friendship.
"""

from __future__ import annotations

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
historic_place(P) :- place(P), historic(P).
safe_plan(P) :- problem(P), friendship(P), problem_solving(P).
resolved(P) :- safe_plan(P), repaired_shutter(P), found_way(P).
"""

PLACE = "Harborwatch lighthouse"


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
    captain: str
    friend: str
    tool: str
    keepsake: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    failed_try: str
    clue: str
    friend_line: str
    repair: str
    result: str
    ending: str
    lesson: str


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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

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
        key="salt_lock",
        opening="Captain Luna and her first mate, Tavi, sailed to the historic Harborwatch lighthouse before dawn.",
        trouble="Its heavy wooden shutter had jammed shut, leaving the beacon hidden from ships beyond the reef.",
        failed_try="Luna pulled the iron ring while Tavi pushed the shutter, but the salt-swollen wood only groaned.",
        clue="Tavi noticed a pale line of dry wood beneath the rusty hinge.",
        friend_line='"The hinge is trapped by salt, not by the whole shutter," Tavi said.',
        repair="brushed the salt away, slipped the hook beneath the hinge, and lifted while Luna pulled the ring",
        result="The shutter swung open, and the lighthouse lamp sent a bright path across the dark water.",
        ending="At sunrise, the old shutter stood open like a welcoming wing above their small ship.",
        lesson="good friends inspect a problem together before pulling harder",
    ),
    Scenario(
        key="storm_latch",
        opening="Captain Luna and her friend, Mara, anchored beside the historic Harborwatch lighthouse during a sudden squall.",
        trouble="A storm latch had fallen across the old shutter, and the beacon could not warn a fishing boat near the rocks.",
        failed_try="Mara tugged the latch from the wrong side, which made it wedge tighter.",
        clue="Luna saw that the latch pin trembled whenever the wind pushed the shutter.",
        friend_line='"We must steady the door before we free the pin," Luna said.',
        repair="held the shutter against the wind, tapped the pin with the brass mallet, and slid the latch aside",
        result="The shutter opened safely, and the lighthouse keeper guided the fishing boat past the rocks.",
        ending="The storm faded while the historic shutter rested safely against the lighthouse wall.",
        lesson="problem solving begins when friends notice what makes a difficulty worse",
    ),
    Scenario(
        key="hidden_map",
        opening="Captain Luna and her cabin mate, Jo, climbed the steps of the historic Harborwatch lighthouse with a chart in hand.",
        trouble="The shutter would not open, and the chart's missing mark was painted on the wall behind it.",
        failed_try="Jo searched the floor for a key while Luna pushed at the middle boards.",
        clue="A tiny compass rose was carved near the shutter's lower corner.",
        friend_line='"The compass points to the bottom bolt," Jo said.',
        repair="followed the carved direction, loosened the bottom bolt, and raised the shutter together",
        result="The missing mark showed a safe channel through the reef.",
        ending="Their ship sailed by the new channel as the historic shutter gleamed in the afternoon sun.",
        lesson="a small clue can guide a large solution when friends share what they see",
    ),
    Scenario(
        key="broken_rope",
        opening="Captain Luna and her friend, Pip, rowed toward the historic Harborwatch lighthouse with a coil of rope.",
        trouble="The rope that lifted the shutter had frayed through, so the beacon window stayed covered.",
        failed_try="Pip tied a quick knot, but the loose end slipped through the pulley.",
        clue="Luna found three strong strands still hidden inside the worn rope.",
        friend_line='"We can braid the strong strands into a new lifting line," Luna said.',
        repair="cut away the frayed end, braided the strong strands, and tied the new rope around the pulley",
        result="The shutter rose smoothly, and the beacon shone over the waves.",
        ending="The repaired rope hung beside the historic shutter like a tidy ship's pennant.",
        lesson="patient teamwork can turn a broken tool into a useful one",
    ),
    Scenario(
        key="seagull_key",
        opening="Captain Luna and her best friend, Niko, visited the historic Harborwatch lighthouse to polish its brass bell.",
        trouble="The key to the shutter's small side lock had vanished beneath a noisy flock of seagulls.",
        failed_try="Niko waved a cloth at the birds, but they only scattered shells across the steps.",
        clue="One gull kept pecking beside a blue shell near the drain.",
        friend_line='"That gull has found something shiny," Niko whispered.',
        repair="placed crumbs away from the steps, waited for the gulls to move, and lifted the blue shell",
        result="The lost key lay beneath it, bright and dry.",
        ending="The historic shutter opened, and the brass bell rang for the birds and the sea.",
        lesson="a calm plan works better than chasing every problem at once",
    ),
    Scenario(
        key="moonlit_board",
        opening="Captain Luna and her friend, Sela, reached the historic Harborwatch lighthouse under a silver moon.",
        trouble="One board in the shutter had slipped across the latch, trapping the lighthouse keeper outside.",
        failed_try="Sela pushed the board upward, but it slid down again with a loud clack.",
        clue="Moonlight showed a small wedge-shaped gap beneath the board.",
        friend_line='"If we support the gap, the board will stay where we place it," Sela said.',
        repair="slid a wooden wedge into the gap, lifted the board, and freed the latch",
        result="The keeper stepped inside and lit the beacon before midnight.",
        ending="The moon shone through the open historic shutter onto three grateful faces.",
        lesson="the right support can make a stubborn problem manageable",
    ),
]

NAMES = ["Luna", "Rhea", "Milo", "Tavi", "Mara", "Jo", "Pip", "Niko", "Sela"]
TOOLS = ["brass mallet", "boat hook", "coil of rope", "wooden wedge"]
KEEPSAKES = ["compass", "spyglass", "silver coin", "blue shell"]

OPENING_LINES = [
    "The sea rolled beneath the moon, and the pirate flag snapped above the mast.",
    "A gull cried over the harbor as the little ship approached the old lighthouse.",
    "The tide glittered like treasure around the island, but Luna had a problem to solve.",
]

PLANS = [
    "They divided the work: one watched the hinge while the other handled the tool.",
    "They moved the fragile parts out of the wind before trying again.",
    "They named the danger, tested the smallest change, and checked the result together.",
    "They listened to the wood, the waves, and each other's ideas before making a plan.",
]

NAMES_OF_FRIENDSHIP = [
    "Neither pirate claimed the victory; they shared it like a map between them.",
    "Their friendship felt steadier than the deck beneath their boots.",
    "The friends grinned because the solution belonged to both of them.",
]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.captain.strip() or not params.friend.strip():
        raise StoryError("The pirate tale needs both a captain and a friend.")
    if params.tool not in TOOLS:
        raise StoryError("The tool must be a safe, useful object for repairing a lighthouse shutter.")
    if params.keepsake not in KEEPSAKES:
        raise StoryError("The keepsake must be a small nautical treasure.")
    if params.captain.strip().lower() == params.friend.strip().lower():
        raise StoryError("The captain and friend should have different names.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "harborwatch_lighthouse"),
            asp.fact("historic", "harborwatch_lighthouse"),
            asp.fact("problem", "harborwatch_lighthouse"),
            asp.fact("friendship", "harborwatch_lighthouse"),
            asp.fact("problem_solving", "harborwatch_lighthouse"),
            asp.fact("repaired_shutter", "harborwatch_lighthouse"),
            asp.fact("found_way", "harborwatch_lighthouse"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_params(rng: random.Random) -> StoryParams:
    captain = rng.choice(NAMES)
    friend = rng.choice([name for name in NAMES if name != captain])
    return StoryParams(
        captain=captain,
        friend=friend,
        tool=rng.choice(TOOLS),
        keepsake=rng.choice(KEEPSAKES),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Historic shutter pirate friendship storyworld.")
    parser.add_argument("--captain")
    parser.add_argument("--friend")
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--keepsake", choices=KEEPSAKES)
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
    if args.captain:
        params.captain = args.captain
    if args.friend:
        params.friend = args.friend
    if args.tool:
        params.tool = args.tool
    if args.keepsake:
        params.keepsake = args.keepsake
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="captain", kind="character", label=params.captain))
    world.add(Entity(id="friend", kind="character", label=params.friend))
    world.add(Entity(id="tool", kind="tool", label=params.tool))
    world.add(Entity(id="keepsake", kind="treasure", label=params.keepsake))
    world.add(Entity(id="shutter", kind="historic_shutter", label="historic wooden shutter"))
    world.facts.update(
        place=PLACE,
        historic=True,
        friendship=True,
        problem_solving=True,
        shutter="historic wooden shutter",
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    plan = rng.choice(PLANS)
    friendship_line = rng.choice(NAMES_OF_FRIENDSHIP)

    captain = world.get("captain")
    friend = world.get("friend")
    tool = world.get("tool")
    keepsake = world.get("keepsake")
    shutter = world.get("shutter")

    captain.bump_meme("friendship")
    friend.bump_meme("trust")
    shutter.bump_meter("stuck", 1.0)

    world.say(scenario.opening)
    world.say(
        f"{captain.label} carried a {keepsake.label}, while {friend.label} carried a "
        f"{tool.label}. They were visiting the historic Harborwatch lighthouse because its "
        f"old shutter guarded the beacon."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(f"At first, {scenario.failed_try}")
    world.say(
        f"{captain.label} took a breath. \"We will solve this together,\" "
        f"{captain.label} promised."
    )
    world.say(scenario.clue)
    world.say(scenario.friend_line)
    world.para()

    friend.bump_meme("courage")
    captain.bump_meme("patience")
    world.say(plan)
    world.say(
        f"{captain.label} held the {tool.label} ready while {friend.label} showed the safest place to begin."
    )
    world.say(f"Together, they {scenario.repair}.")
    shutter.bump_meter("stuck", -1.0)
    shutter.bump_meter("open", 1.0)
    world.say(scenario.result)
    world.para()

    captain.bump_meme("joy")
    friend.bump_meme("joy")
    world.say(friendship_line)
    world.say(f"They agreed that {scenario.lesson}.")
    world.say(
        f"The historic shutter now let the beacon shine across the sea. "
        f"{scenario.ending}"
    )

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        failed_try=scenario.failed_try,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        lesson=scenario.lesson,
        resolved=True,
        found_way=True,
        repaired_shutter=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    captain = facts["captain"].label
    friend = facts["friend"].label
    tool = facts["tool"].label
    return [
        f"Write a pirate tale in which {captain} and {friend} solve a problem together.",
        "Tell a child-friendly story using the words historic and shutter.",
        f"Write a friendship and problem-solving adventure involving a historic shutter and a {tool}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    captain = facts["captain"].label
    friend = facts["friend"].label
    tool = facts["tool"].label
    return [
        QAItem(
            question="What problem did the pirates find at the historic lighthouse?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue did {captain} and {friend} notice?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did the friends use the {tool}?",
            answer=f"They used the {tool} while they {facts['repair']}.",
        ),
        QAItem(
            question="What happened after the friends solved the problem?",
            answer=str(facts["result"]),
        ),
        QAItem(
            question="How did the ending show that their plan worked?",
            answer=str(facts["ending"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people trust one another and help each other.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, making a plan, and trying a sensible way to fix it.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a covering that can open or close over a window or opening.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important because it belongs to the past or helps people remember the past.",
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


def dump_trace(world: World) -> str:
    return world.trace()


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show historic_place/1.\n#show safe_plan/1.\n#show resolved/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(
            argument.name if argument.type != 4 else argument.string
            for argument in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"historic_place", "safe_plan", "resolved"}
    }
    expected = {
        ("historic_place", ("harborwatch_lighthouse",)),
        ("safe_plan", ("harborwatch_lighthouse",)),
        ("resolved", ("harborwatch_lighthouse",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python world gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    rng = random.Random(777)
    for _ in range(5):
        sample = generate(valid_params(rng))
        if not sample.story or not sample.world.facts.get("resolved"):
            print("Generated-story verification failed.")
            return 1
        if "historic" not in sample.story or "shutter" not in sample.story:
            print("Seed-word verification failed.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(asp.atoms(model, "resolved"))


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


CURATED = [
    StoryParams("Luna", "Tavi", "boat hook", "compass", 11),
    StoryParams("Rhea", "Mara", "brass mallet", "spyglass", 29),
    StoryParams("Milo", "Sela", "wooden wedge", "blue shell", 47),
]


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP-compatible historic shutter pirate stories:")
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
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
