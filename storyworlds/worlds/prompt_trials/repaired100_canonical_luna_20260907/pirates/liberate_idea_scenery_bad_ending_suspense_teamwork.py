#!/usr/bin/env python3
"""
A tiny fable world about liberating an idea from a locked scenery trunk.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Scene:
    id: str
    name: str
    description: str
    danger: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    name: str
    use: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Character:
    id: str
    name: str
    role: str
    trait: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    scenery: str
    idea: str
    helper: str
    tool: str
    ending: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.scenes: dict[str, Scene] = {}
        self.props: dict[str, Prop] = {}
        self.characters: dict[str, Character] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENERY = {
    "old_theater": Scene(
        "old_theater",
        "the old theater",
        "with red curtains, dusty lanterns, and a wooden stage",
        2,
        {"stage", "curtain", "dust"},
    ),
    "moon_garden": Scene(
        "moon_garden",
        "the moon garden",
        "with silver paper flowers, stepping stones, and a quiet pond",
        1,
        {"garden", "pond", "moonlight"},
    ),
    "clocktower": Scene(
        "clocktower",
        "the clocktower hall",
        "with turning gears, high windows, and a bell rope",
        3,
        {"gears", "height", "bell"},
    ),
}

IDEAS = {
    "lantern_play": (
        "a play about a little lantern that wanted to guide everyone home",
        "lantern",
    ),
    "kindness_bridge": (
        "a play about a bridge that helped every traveler cross",
        "bridge",
    ),
    "brave_seed": (
        "a play about a tiny seed that grew through a stone",
        "seed",
    ),
}

HELPERS = {
    "luna": ("Luna", "patient"),
    "orin": ("Orin", "clever"),
    "mara": ("Mara", "bold"),
    "pax": ("Pax", "careful"),
}

TOOLS = {
    "rope": Prop("rope", "a long rope", "pull together", 2, {"rope", "teamwork"}),
    "hook": Prop("hook", "a wooden hook", "lift the latch", 3, {"hook", "latch"}),
    "pole": Prop("pole", "a painted pole", "reach the key", 2, {"pole", "reach"}),
}

ENDINGS = {
    "bad": "bad",
    "safe": "safe",
}


def build_world(params: StoryParams) -> World:
    if params.scenery not in SCENERY:
        raise StoryError("Unknown scenery.")
    if params.idea not in IDEAS:
        raise StoryError("Unknown idea.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.ending not in ENDINGS:
        raise StoryError("Unknown ending.")

    scene = SCENERY[params.scenery]
    idea_text, idea_token = IDEAS[params.idea]
    helper_name, helper_trait = HELPERS[params.helper]
    tool = TOOLS[params.tool]

    if scene.danger >= 3 and params.tool == "pole":
        raise StoryError(
            "The high clocktower needs a tool that can hold fast; choose the rope or hook."
        )

    world = World()
    world.scenes[scene.id] = scene
    world.props[tool.id] = tool
    luna = Character(
        "luna",
        "Luna",
        "idea_keeper",
        "imaginative",
        meters={"time": 0, "effort": 0},
        memes={"hope": 2, "worry": 1, "courage": 1},
    )
    helper = Character(
        "helper",
        helper_name,
        "teammate",
        helper_trait,
        meters={"time": 0, "effort": 0},
        memes={"hope": 1, "worry": 1, "courage": 1},
    )
    world.characters[luna.id] = luna
    world.characters[helper.id] = helper

    world.facts.update(
        scene=scene,
        idea_text=idea_text,
        idea_token=idea_token,
        tool=tool,
        luna=luna,
        helper=helper,
        ending=params.ending,
    )

    world.say(
        f"In {scene.name}, {scene.description}, Luna carried {idea_text} "
        "inside her head like a bright seed."
    )
    world.say(
        f"She had painted the scenery for it, but the scenery trunk was locked "
        f"before the show could begin."
    )
    world.para()
    world.say(
        f'"If I cannot open the trunk, my idea will never meet the audience," '
        f"Luna whispered.'
    )
    world.say(
        f'"Then we will liberate it together," said {helper_name}. '
        f'"Tell me what to do."'
    )

    luna.memes["hope"] += 1
    helper.memes["courage"] += 1
    luna.meters["effort"] += 1
    helper.meters["effort"] += 1
    world.events.append("team formed")

    world.para()
    world.say(
        f"They studied the lock while the {scene.name} grew dim. "
        f"A wind worried the curtains, and the old floor gave a slow creak."
    )
    world.say(
        f'"The latch is high," said {helper_name}. "Can your {tool.name} reach it?"'
    )
    world.say(
        f'"Only if you hold the other end," Luna answered. '
        f'"An idea may begin in one mind, but it needs many hands to travel."'
    )

    for person in (luna, helper):
        person.meters["effort"] += 1
        person.memes["hope"] += 1
    world.events.append("plan shared")

    world.para()
    world.say(
        f"Luna tied {tool.name} around the latch. {helper_name} planted "
        f"{helper_name}'s feet beside hers, and together they pulled."
    )
    world.say("The latch groaned. The darkness seemed to lean closer.")
    world.say(
        f'"Together!" cried Luna. "{helper_name}, now!"'
    )
    world.say(
        f'"Together!" {helper_name} called back, pulling until the old lock shook.'
    )

    for person in (luna, helper):
        person.meters["effort"] += 2
        person.memes["courage"] += 1
    world.events.append("teamwork tested")

    if params.ending == "safe":
        world.say(
            "Click! The lock opened. The trunk lifted, and the scenery rolled out "
            "like a sunrise."
        )
        world.say(
            f"The {IDEAS[params.idea][1]} idea was free at last. Luna and "
            f"{helper_name} placed every piece where it belonged, and the little "
            "play made the whole hall feel warm."
        )
        for person in (luna, helper):
            person.memes["hope"] += 2
            person.memes["relief"] = 2
        world.events.append("idea liberated")
    else:
        world.say(
            "The lock sprang open, but the old scenery trunk tipped toward the pond."
        )
        world.say(
            f"Luna and {helper_name} grabbed the trunk together, yet one wheel "
            "broke loose. The painted scenery slid into the dark water."
        )
        world.say(
            "The idea was still alive in Luna's heart, but the show could not open "
            "that night."
        )
        for person in (luna, helper):
            person.memes["worry"] += 2
            person.memes["hope"] += 1
        world.events.append("scenery lost")

    world.para()
    if params.ending == "safe":
        world.say(
            f"From then on, the children remembered: when {helper_name} helped "
            "Luna, a locked idea became a shared story."
        )
    else:
        world.say(
            f"From then on, Luna remembered that courage needs care, and "
            f"{helper_name} remembered to check the wheels before pulling."
        )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    tool: Prop = f["tool"]
    return [
        f"Write a Fable about Luna trying to liberate an idea in {scene.name} using {tool.name}.",
        "Include suspense, teamwork, and scenery that changes the ending.",
        "Let two characters speak to each other so their words change what they do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene: Scene = f["scene"]
    luna: Character = f["luna"]
    helper: Character = f["helper"]
    tool: Prop = f["tool"]
    if f["ending"] == "safe":
        ending = (
            f"The lock opened, so {luna.name} and {helper.name} liberated the idea "
            f"and arranged the scenery for the play."
        )
    else:
        ending = (
            f"The lock opened, but the scenery fell into the pond, so the idea "
            f"remained safe in {luna.name}'s heart while the show was delayed."
        )
    return [
        QAItem(
            f"Where did Luna keep her idea?",
            f"Luna kept her idea inside her head while she worked in {scene.name}.",
        ),
        QAItem(
            f"Who helped Luna liberate the idea?",
            f"{helper.name} helped Luna by sharing the plan and pulling with her.",
        ),
        QAItem(
            f"What tool did the team use?",
            f"They used {tool.name} to work the locked scenery trunk.",
        ),
        QAItem(
            "How did teamwork change the story?",
            f"Their teamwork gave them enough strength to move the latch. {ending}",
        ),
    ]


KNOWLEDGE = {
    "teamwork": QAItem(
        "Why is teamwork useful?",
        "Teamwork lets people combine their strength, ideas, and care to solve a problem.",
    ),
    "suspense": QAItem(
        "What is suspense?",
        "Suspense is the feeling of waiting and wondering what will happen next.",
    ),
    "idea": QAItem(
        "What is an idea?",
        "An idea is a thought or plan that someone may share and turn into something real.",
    ),
    "scenery": QAItem(
        "What is scenery?",
        "Scenery is the painted or arranged background that helps show where a play happens.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE.values())


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for scene in world.scenes.values():
        lines.append(f"scene: {scene.id}, danger={scene.danger}, tags={sorted(scene.tags)}")
    for prop in world.props.values():
        lines.append(f"prop: {prop.id}, difficulty={prop.difficulty}, use={prop.use}")
    for char in world.characters.values():
        lines.append(
            f"character: {char.id}, role={char.role}, meters={char.meters}, memes={char.memes}"
        )
    lines.append(f"events: {world.events}")
    return "\n".join(lines)


ASP_RULES = r"""
hazardous_scene(S) :- scene(S), danger(S, D), D >= 3.
teamwork_needed :- teammate(_), teammate(_).
idea_liberated :- lock_open, teamwork_needed.
outcome(safe) :- idea_liberated, not scenery_lost.
outcome(bad) :- scenery_lost.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid, scene in SCENERY.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("danger", sid, scene.danger))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("teammate", "luna"))
    lines.append(asp.fact("teammate", "helper"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("lock_open. scenery_lost.", "#show outcome/1."))
    outcomes = {x[0] for x in asp.atoms(model, "outcome")}
    if outcomes != {"bad"}:
        print("ASP verification failed.")
        return 1
    print("OK: ASP twin recognizes the bad ending.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenery = args.scenery or rng.choice(sorted(SCENERY))
    idea = args.idea or rng.choice(sorted(IDEAS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    ending = args.ending or rng.choice(["safe", "bad"])
    if scenery == "clocktower" and tool == "pole":
        raise StoryError("The clocktower requires a rope or hook for a safe plan.")
    return StoryParams(scenery, idea, helper, tool, ending)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A Fable about liberating an idea.")
    parser.add_argument("--scenery", choices=SCENERY)
    parser.add_argument("--idea", choices=IDEAS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--ending", choices=ENDINGS)
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


CURATED = [
    StoryParams("old_theater", "lantern_play", "orin", "rope", "safe"),
    StoryParams("moon_garden", "kindness_bridge", "mara", "hook", "bad"),
    StoryParams("clocktower", "brave_seed", "pax", "rope", "safe"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("", "#show hazardous_scene/1.\n#show teamwork_needed/0."))
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed if args.seed is not None else None
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### story {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
