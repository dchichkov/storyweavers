#!/usr/bin/env python3
"""
A tiny craft-workshop world about Luna, vanilla paint, and the joy of teamwork.
The story uses a nursery-rhyme rhythm, spoken dialogue, and a brief flashback.
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


@dataclass(frozen=True)
class Workshop:
    id: str
    label: str
    affords: frozenset[str]


@dataclass(frozen=True)
class Paint:
    id: str
    label: str
    color: str
    scent: str
    drying_time: int


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    purpose: str


@dataclass
class Character:
    id: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Workshop
    hero: Character
    helper: Character
    paint: Paint
    tool: Tool
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


WORKSHOPS = {
    "craft_workshop": Workshop(
        "craft_workshop",
        "the craft workshop",
        frozenset({"paint", "cut", "glue", "teamwork"}),
    ),
    "sunny_studio": Workshop(
        "sunny_studio",
        "the sunny craft studio",
        frozenset({"paint", "teamwork"}),
    ),
}

PAINTS = {
    "vanilla": Paint("vanilla", "vanilla paint", "warm cream", "sweet vanilla", 3),
    "berry": Paint("berry", "berry paint", "bright red", "ripe berries", 2),
    "sky": Paint("sky", "sky-blue paint", "soft blue", "fresh rain", 2),
}

TOOLS = {
    "wide_brush": Tool("wide_brush", "a wide brush", "cover large spaces"),
    "little_brush": Tool("little_brush", "a little brush", "paint tiny details"),
    "sponge": Tool("sponge", "a round sponge", "stamp gentle circles"),
}

HERO_NAMES = ["Luna", "Mira", "Pip", "Toby", "Nell"]
HELPER_NAMES = ["Aunt Bea", "Milo", "Grandma June", "Ollie"]


@dataclass(frozen=True)
class StoryParams:
    setting: str
    paint: str
    tool: str
    name: str
    helper: str
    seed: Optional[int] = None


def reasonability_gate(setting: Workshop, paint: Paint, tool: Tool) -> bool:
    return (
        "paint" in setting.affords
        and paint.drying_time >= 2
        and tool.purpose in {"cover large spaces", "paint tiny details", "stamp gentle circles"}
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(WORKSHOPS))
    paint = args.paint or rng.choice(list(PAINTS))
    tool = args.tool or rng.choice(list(TOOLS))
    if not reasonability_gate(WORKSHOPS[setting], PAINTS[paint], TOOLS[tool]):
        raise StoryError("The selected workshop, paint, and tool cannot make a reasonable craft story.")
    return StoryParams(
        setting=setting,
        paint=paint,
        tool=tool,
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    setting = WORKSHOPS[params.setting]
    paint = PAINTS[params.paint]
    tool = TOOLS[params.tool]
    hero = Character(params.name, params.name, "young painter")
    helper = Character(params.helper, params.helper, "workshop helper")

    world = World(setting, hero, helper, paint, tool)
    world.meters.update({"shared_space": 1.0, "unfinished_banner": 1.0})
    world.memes.update({"hope": 1.0, "trust": 0.0, "joy": 0.0})

    world.say(
        f"In {setting.label,} where bright brushes sang, {hero.label} came dancing with a plan."
    )
    world.say(
        f"She wished to paint a moon-and-star banner in {paint.label}, "
        f"soft as cream and sweet with a {paint.scent} smell."
    )
    world.say(
        f"{helper.label} carried {tool.label}, while {hero.label} carried the cloth. "
        "Together they would make the workshop window shine."
    )

    world.para()
    world.say(
        f"But the banner was broad, and {hero.label} brushed too fast. "
        f"A vanilla-colored wave spread toward the table's edge."
    )
    world.say(
        f'"We need more than one pair of hands," said {helper.label}. '
        f'"Will you guide the stars while I guide the wide brush?"'
    )
    world.say(
        f'"Yes, and you tell me when to pause," answered {hero.label}. '
        "Her words made a careful plan."
    )

    world.para()
    world.say(
        f"Then {hero.label} remembered a little flashback from last spring, "
        "when a lonely paper kite tore because nobody held its corners."
    )
    world.say(
        f"Back then, {helper.label} had said, "
        '"A craft grows strong when friends hold it together."'
    )
    world.say(
        f"The memory helped {hero.label} stop rushing. "
        f"She held the banner flat while {helper.label} swept {tool.label} in long, even strokes."
    )
    world.say(
        f"One painted moon, two painted stars, and three tiny dots appeared. "
        f"They waited {paint.drying_time} quiet minutes before touching the cloth again."
    )

    world.para()
    world.say(
        f"When the banner dried, {hero.label} was overjoyed. "
        f"The {paint.label} glowed like morning cream, and every star stayed in its place."
    )
    world.say(
        f'"We made it together!" cried {hero.label}. '
        f'"Together is the best color," replied {helper.label}.'
    )
    world.say(
        "Up went the banner, flutter-flap, over the workshop door. "
        "The moon smiled, the stars danced, and the two friends bowed to their teamwork."
    )

    hero.meters["rushing"] = 0.0
    hero.meters["shared_space"] = 0.0
    hero.memes["joy"] = 2.0
    hero.memes["trust"] = 2.0
    helper.memes["trust"] = 2.0
    world.meters["unfinished_banner"] = 0.0
    world.memes["joy"] = 2.0
    world.memes["teamwork"] = 2.0

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        paint=paint,
        tool=tool,
        flashback="The paper kite tore because nobody held its corners.",
        plan="Luna held the banner flat while the helper painted in long, even strokes.",
        outcome="The banner dried with every moon and star in place.",
        teamwork=True,
        dialogue=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Nursery Rhyme story about {f['hero'].label} using {f['paint'].label} in {f['setting'].label}.",
        f"Show Teamwork and Dialogue as {f['hero'].label} and {f['helper'].label} make a banner.",
        f"Include a Flashback about a torn paper kite and end with an overjoyed craft-maker.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    return [
        QAItem(
            f"What did {hero} want to paint?",
            f"{hero} wanted to paint a moon-and-star banner in {f['paint'].label}.",
        ),
        QAItem(
            f"How did {hero} and {helper} use teamwork?",
            f"{hero} held the banner flat while {helper} painted in long, even strokes.",
        ),
        QAItem(
            "What did the flashback remind Luna to do?",
            "The flashback reminded Luna to stop rushing and have friends hold the craft together.",
        ),
        QAItem(
            "What happened when the banner dried?",
            "The banner dried with every moon and star in place.",
        ),
        QAItem(
            "How did Luna feel at the end?",
            "Luna was overjoyed because the finished banner showed what she and her helper had made together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should people share a large painting job?",
            "Sharing a large painting job helps friends control the material, protect the work, and make careful progress together.",
        ),
        QAItem(
            "What is a flashback in a story?",
            "A flashback is a short return to an earlier event that helps a character understand or decide something in the present.",
        ),
        QAItem(
            "Why must paint dry before a craft is handled?",
            "Paint must dry so the colors stay in place instead of smearing onto hands or other parts of the craft.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"setting: {world.setting.label}",
            f"hero: {world.hero.label}",
            f"helper: {world.helper.label}",
            f"paint: {world.paint.label}, scent={world.paint.scent}",
            f"tool: {world.tool.label}, purpose={world.tool.purpose}",
            f"meters: {world.meters}",
            f"memes: {world.memes}",
            f"hero_meters: {world.hero.meters}",
            f"hero_memes: {world.hero.memes}",
            f"resolved: {world.facts.get('resolved')}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
paint_ready(P) :- paint(P), dries_in(P, T), T >= 2.
teamwork_plan(S, P, T) :- setting(S), paint_ready(P), tool(T), affords(S, paint), useful(T).
valid(S, P, T) :- teamwork_plan(S, P, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in WORKSHOPS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, affordance))
    for pid, paint in PAINTS.items():
        lines.append(asp.fact("paint", pid))
        lines.append(asp.fact("dries_in", pid, paint.drying_time))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("useful", tid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (sid, pid, tid)
        for sid, setting in WORKSHOPS.items()
        for pid, paint in PAINTS.items()
        for tid, tool in TOOLS.items()
        if reasonability_gate(setting, paint, tool)
    ]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_values = set(valid_combos())
        asp_values = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if python_values != asp_values:
        print("MISMATCH between Python and ASP:")
        print("python only:", sorted(python_values - asp_values))
        print("asp only:", sorted(asp_values - python_values))
        return 1
    for combo in valid_combos():
        sample = generate(StoryParams(*combo, "Luna", "Aunt Bea", 1))
        if not sample.story or "overjoyed" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(python_values)} craft combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Nursery Rhyme craft-workshop world about vanilla paint and teamwork."
    )
    parser.add_argument("--setting", choices=WORKSHOPS)
    parser.add_argument("--paint", choices=PAINTS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
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


CURATED = [
    StoryParams("craft_workshop", "vanilla", "wide_brush", "Luna", "Aunt Bea", 1),
    StoryParams("sunny_studio", "vanilla", "sponge", "Mira", "Grandma June", 2),
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

        model = asp.one_model(asp_program())
        for combo in sorted(set(asp.atoms(model, "valid"))):
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params = StoryParams(
                params.setting,
                params.paint,
                params.tool,
                params.name,
                params.helper,
                base_seed + index,
            )
            samples.append(generate(params))

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
