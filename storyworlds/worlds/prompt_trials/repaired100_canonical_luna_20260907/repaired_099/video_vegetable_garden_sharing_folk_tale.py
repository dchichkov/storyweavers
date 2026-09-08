#!/usr/bin/env python3
"""
A small folk tale about a vegetable garden, a sharing video, and a lesson
learned when a generous plan meets a hungry crowd.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("fullness", "distance", "supply", "readiness", "hunger"):
            self.meters.setdefault(key, 0.0)
        for key in ("kindness", "worry", "pride", "surprise", "relief", "gratitude"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    grandmother_name: str = "Nella"
    neighbor_name: str = "Tavi"
    place: str = "the vegetable garden"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SCENARIOS = [
    {
        "crop": "round red tomatoes",
        "problem": "the tomato basket was so full that its handle bent",
        "first_plan": "carry the whole basket at once",
        "clue": "a broad leaf could hold a few tomatoes safely, but not a great many",
        "fix": "made small leaf bundles and invited the neighbors to carry one bundle each",
        "result": "everyone received a fair share before the tomatoes could bruise",
        "ending": "red tomatoes gleamed in many little baskets along the garden path",
    },
    {
        "crop": "crisp cucumbers",
        "problem": "the cucumbers ripened faster than one family could eat them",
        "first_plan": "hide the extra cucumbers under a blanket",
        "clue": "the garden birds and nearby families also needed something cool for supper",
        "fix": "set out a sharing table and marked a basket for every nearby home",
        "result": "the harvest traveled from the vines to hungry tables without waste",
        "ending": "empty vines rested beneath a sign that said, 'Take what you need.'",
    },
    {
        "crop": "golden carrots",
        "problem": "the carrots were buried in different corners of the garden",
        "first_plan": "pull them all quickly and pile them by the gate",
        "clue": "the smallest carrots were easiest for children to carry",
        "fix": "sorted the harvest into little bundles and let each helper choose a manageable bundle",
        "result": "young and old helpers worked together without dropping the food",
        "ending": "bright carrot bundles formed a cheerful circle around the old well",
    },
    {
        "crop": "purple beans",
        "problem": "the bean vines made one tangled wall, so nobody could reach the ripe pods",
        "first_plan": "tug the whole wall until it came loose",
        "clue": "one gentle hand could lift a vine while another hand picked beneath it",
        "fix": "worked in pairs and passed each filled bowl down the row",
        "result": "the beans were gathered carefully and shared before sunset",
        "ending": "purple beans filled a line of bowls like little boats on green water",
    },
]


def _scenario(params: StoryParams) -> dict[str, str]:
    index = params.seed if params.seed is not None else sum(map(ord, params.child_name))
    return SCENARIOS[index % len(SCENARIOS)]


def tell(params: StoryParams) -> World:
    if not params.child_name.strip():
        raise StoryError("child_name must not be empty")
    if not params.grandmother_name.strip():
        raise StoryError("grandmother_name must not be empty")
    if not params.neighbor_name.strip():
        raise StoryError("neighbor_name must not be empty")

    scenario = _scenario(params)
    world = World()
    child = world.add(Entity(
        "child", "character", "child", params.child_name,
        memes={"kindness": 1.0, "worry": 0.0, "pride": 0.0, "surprise": 0.0,
               "relief": 0.0, "gratitude": 0.0},
    ))
    grandmother = world.add(Entity(
        "grandmother", "character", "gardener", params.grandmother_name,
        memes={"kindness": 1.0, "worry": 0.0, "pride": 0.0, "surprise": 0.0,
               "relief": 0.0, "gratitude": 0.0},
    ))
    neighbor = world.add(Entity(
        "neighbor", "character", "neighbor", params.neighbor_name,
        memes={"kindness": 0.5, "worry": 0.0, "pride": 0.0, "surprise": 0.0,
               "relief": 0.0, "gratitude": 0.0},
    ))
    harvest = world.add(Entity("harvest", "thing", "vegetable", scenario["crop"]))
    video = world.add(Entity("video", "thing", "recording", "a sharing video"))
    table = world.add(Entity("table", "thing", "sharing_table", "the garden sharing table"))

    child.meters["readiness"] = 1.0
    grandmother.meters["supply"] = 1.0
    harvest.meters["supply"] = 4.0
    grandmother.memes["kindness"] += 1.0

    world.say(
        f"Long ago, in {params.place}, {params.child_name} helped "
        f"{params.grandmother_name} tend a generous patch of {scenario['crop']}."
    )
    world.say(
        f"That morning, {params.grandmother_name} said, "
        f"\"Our garden has given us more than we can use. Let us share the harvest.\" "
        f"{params.child_name} lifted a small camera and replied, "
        f"\"I can make a video so people will see how sharing works.\""
    )
    world.say(
        f"They placed the camera beside the garden gate. The video showed the soil, "
        f"the ripe vegetables, and {params.grandmother_name} filling a basket for "
        f"{params.neighbor_name}."
    )

    world.para()
    grandmother.meters["supply"] -= 1.0
    child.memes["pride"] += 1.0
    grandmother.memes["worry"] += 1.0
    world.say(
        f"But {scenario['problem']}. {params.child_name} frowned and announced, "
        f"\"I will {scenario['first_plan']}. Then our sharing will be finished quickly.\""
    )
    world.say(
        f"{params.grandmother_name} shook her head. \"A gift should arrive safely, "
        f"and helpers should not struggle just to look fast.\" "
        f"{params.neighbor_name} pointed to the garden and said, "
        f"\"Look closely. {scenario['clue'].capitalize()}\""
    )
    child.memes["surprise"] += 1.0
    world.say(
        f"The camera kept recording as {params.child_name} listened. "
        f"\"Then the video should show the better way,\" {params.child_name} said."
    )

    world.para()
    child.meters["readiness"] += 1.0
    child.memes["kindness"] += 1.0
    grandmother.memes["relief"] += 1.0
    neighbor.memes["kindness"] += 1.0
    world.say(
        f"Together they {scenario['fix']}. "
        f"{params.grandmother_name} checked each bundle, while {params.neighbor_name} "
        f"carried the first one to the sharing table."
    )
    world.say(f"The new plan worked: {scenario['result']}.")
    harvest.meters["supply"] = 0.0
    table.meters["supply"] = 4.0
    child.memes["relief"] += 1.0
    neighbor.memes["gratitude"] += 1.0
    world.say(
        f"{params.neighbor_name} smiled. \"Your video taught me that sharing is not "
        f"just giving food away. It is noticing what keeps the food and the helpers safe.\""
    )
    world.say(
        f"{params.child_name} saved the video with a title: \"Many Hands, One Garden.\" "
        f"By sunset, {scenario['ending']}"
    )

    world.facts.update(
        params=params,
        scenario=scenario,
        child=child,
        grandmother=grandmother,
        neighbor=neighbor,
        harvest=harvest,
        video=video,
        table=table,
        resolved=True,
        shared=True,
        video_recorded=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a folk tale about {p.child_name} sharing {s['crop']} in a vegetable garden.",
        f"Include a video that shows why the family changes its first sharing plan.",
        "Show sharing as a careful action that helps both food and people.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    s = f["scenario"]
    return [
        QAItem(
            "Who made the sharing video?",
            f"{p.child_name} made the video while helping {p.grandmother_name} share the garden harvest."
        ),
        QAItem(
            "What problem did the gardeners face?",
            f"They faced this problem: {s['problem']}. That made their first idea unsafe or impractical."
        ),
        QAItem(
            "What clue changed the plan?",
            f"They noticed that {s['clue']}. The clue showed them how to share more carefully."
        ),
        QAItem(
            "How did the helpers solve the problem?",
            f"They {s['fix']}. This meant that {s['result']}."
        ),
        QAItem(
            "What did the video teach?",
            "The video taught that sharing means noticing what others need and choosing a safe, fair way to give."
        ),
        QAItem(
            "How did the garden look at the end?",
            f"At the end, {s['ending']}"
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is a vegetable garden?",
        "A vegetable garden is a place where people grow edible plants such as carrots, beans, cucumbers, or tomatoes."
    ),
    QAItem(
        "Why can sharing a harvest be helpful?",
        "Sharing a harvest helps food reach people who can use it and keeps extra food from being wasted."
    ),
    QAItem(
        "What is a video?",
        "A video is a recording of moving pictures and sound that people can watch later."
    ),
    QAItem(
        "Why should helpers make a careful plan?",
        "A careful plan can protect the food, make the work fair, and keep people from getting hurt or too tired."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if abs(v) > 1e-9}
        lines.append(f"  {entity.id:12} ({entity.type:14}) meters={meters} memes={memes}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  shared={world.facts.get('shared')}")
    lines.append(f"  video_recorded={world.facts.get('video_recorded')}")
    return "\n".join(lines)


ASP_RULES = r"""
shared :- harvest, sharing_table, resolved.
video_documented :- video, shared.
safe_plan :- clue, shared.
folk_tale_complete :- video_documented, safe_plan, resolved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("harvest", "garden_vegetables"),
        asp.fact("sharing_table", "garden_table"),
        asp.fact("video", "sharing_video"),
        asp.fact("clue", "observed_garden_clue"),
        asp.fact("resolved"),
    ])


def asp_program(show: str = "#show folk_tale_complete/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    needed = {"shared", "video_documented", "safe_plan", "folk_tale_complete"}
    if needed.issubset(names):
        print("OK: ASP and Python agree that the garden tale is resolved.")
        return 0
    print("MISMATCH: ASP did not derive the complete garden tale.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk tale about sharing a vegetable garden harvest.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--child-name")
    parser.add_argument("--grandmother-name")
    parser.add_argument("--neighbor-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child_name=args.child_name or rng.choice(["Luna", "Mira", "Oren", "Pia"]),
        grandmother_name=args.grandmother_name or rng.choice(["Nella", "Rosa", "Tessa", "Bina"]),
        neighbor_name=args.neighbor_name or rng.choice(["Tavi", "Gus", "Ivo", "Sela"]),
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(child_name="Luna", grandmother_name="Nella", neighbor_name="Tavi"),
    StoryParams(child_name="Mira", grandmother_name="Rosa", neighbor_name="Gus"),
    StoryParams(child_name="Oren", grandmother_name="Tessa", neighbor_name="Sela"),
    StoryParams(child_name="Pia", grandmother_name="Bina", neighbor_name="Ivo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(args.n)
        ]
        for index, sample in enumerate(samples):
            sample.params.seed = base_seed + index

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
