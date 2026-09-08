#!/usr/bin/env python3
"""A child-facing superhero story about glamorous praise, careful clues, and a forest trail."""

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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    label: str
    detail: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


SETTINGS = {
    "forest_trail": Setting(
        label="the forest trail",
        detail="a winding path beneath tall firs, bright moss, and silver leaves",
    )
}

THREATS = {
    "fallen_bridge": {
        "name": "the fallen bridge",
        "danger": "a storm-bent tree had crushed the footbridge over a rushing stream",
        "clue": "three fresh scratches marked the bark beside a narrow upstream path",
        "plan": "follow the scratches, secure the loose guide rope, and guide everyone across the shallow stones",
        "rescue": "The travelers crossed safely while the ranger called for a proper bridge repair.",
        "ending": "By sunset, the silver stream shone beneath a safe rope crossing.",
    },
    "runaway_lantern": {
        "name": "the runaway lantern",
        "danger": "a glowing trail lantern had rolled toward a nest hidden beside dry leaves",
        "clue": "warm ash and tiny bird feathers rested in a line beneath the ferns",
        "plan": "cover the lantern with a fire blanket, move it away from the nest, and call the ranger",
        "rescue": "The ranger cooled the lantern, and the birds remained safe in their hidden nest.",
        "ending": "At dusk, the rescued nest rustled beneath a cool, steady trail light.",
    },
    "rockslide": {
        "name": "the rockslide",
        "danger": "loose stones had tumbled across the steepest part of the trail",
        "clue": "a soft ticking sound came from pebbles still shifting above the path",
        "plan": "listen for the shifting stones, close the trail, and lead hikers around the lower ridge",
        "rescue": "No one stepped beneath the slope, and the ranger marked the safer route.",
        "ending": "Moonlight touched the quiet ridge while bright ribbons marked the safe turn.",
    },
}

COSTUMES = {
    "starlight": "a glamorous midnight-blue cape with tiny silver stars",
    "sunburst": "a glamorous golden jacket that gleamed like sunrise",
    "emerald": "a glamorous green mask and cape that shimmered like leaves",
}

NAMES = ["Luna", "Maya", "Nia", "Zara", "Tess"]
PARTNERS = ["Pip", "Robin", "Kai", "Milo", "Jules"]

OPENINGS = [
    "The forest trail looked peaceful, but Luna noticed one leaf trembling where there was no wind.",
    "At the edge of the forest trail, Luna's glamorous cape flashed between the trees.",
    "The hikers cheered when the young hero arrived on the forest trail.",
    "A golden sunbeam made the forest trail look like a stage.",
]

PRAISE_LINES = [
    '"You look glamorous enough to be on a poster!" called a hiker.',
    '"That cape is dazzling!" said a little fox watcher.',
    '"Our hero deserves a mountain of praise!" cried a camper.',
    '"Everyone will praise you when you save the day!" said a cheerful squirrel.',
]

REFLECTIONS = [
    "Luna learned that praise feels best when it celebrates a careful choice, not just a sparkling costume.",
    "The glamorous cape caught the light, but listening closely revealed the real danger.",
    "A superhero does not chase applause past a warning sign.",
    "The forest rewarded patience with a safe path home.",
]


@dataclass
class StoryParams:
    setting: str = "forest_trail"
    threat: str = "fallen_bridge"
    costume: str = "starlight"
    name: str = "Luna"
    partner_name: str = "Pip"
    opening: int = 0
    praise: int = 0
    reflection: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about glamorous praise on a forest trail."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--threat", choices=THREATS, default=None)
    parser.add_argument("--costume", choices=COSTUMES, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--partner-name", default=None)
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
    name = args.name or rng.choice(NAMES)
    partner_choices = [item for item in PARTNERS if item != name]
    return StoryParams(
        setting=args.setting or "forest_trail",
        threat=args.threat or rng.choice(list(THREATS)),
        costume=args.costume or rng.choice(list(COSTUMES)),
        name=name,
        partner_name=args.partner_name or rng.choice(partner_choices),
        opening=rng.randrange(len(OPENINGS)),
        praise=rng.randrange(len(PRAISE_LINES)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def _require_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.threat not in THREATS:
        raise StoryError(f"Unknown threat: {params.threat}")
    if params.costume not in COSTUMES:
        raise StoryError(f"Unknown costume: {params.costume}")
    if not params.name.strip() or not params.partner_name.strip():
        raise StoryError("Hero and partner names must not be empty.")
    if params.name == params.partner_name:
        raise StoryError("Hero and partner must have different names.")


def tell(params: StoryParams) -> World:
    _require_params(params)
    setting = SETTINGS[params.setting]
    threat = THREATS[params.threat]
    world = World(setting)

    hero = world.add(
        Entity(
            id=params.name,
            kind="hero",
            label=params.name,
            meters={"courage": 0.0, "danger_awareness": 0.0, "joy": 0.0},
            memes={"praise": 0.0, "showmanship": 0.0},
        )
    )
    partner = world.add(
        Entity(
            id=params.partner_name,
            kind="partner",
            label=params.partner_name,
            meters={"attention": 0.0, "helpfulness": 0.0},
            memes={"trust": 0.0},
        )
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        threat=threat,
        costume=COSTUMES[params.costume],
        foreshadowing=threat["clue"],
        resolved=False,
    )

    world.say(
        f"{OPENINGS[params.opening % len(OPENINGS)]} "
        f"{params.name} wore {COSTUMES[params.costume]}, and the bright fabric made "
        f"{params.name} look like a superhero from a glamorous storybook."
    )
    world.say(PRAISE_LINES[params.praise % len(PRAISE_LINES)])
    world.say(
        f"{params.name} smiled at the praise, but {params.partner_name} pointed to the ground. "
        f'"The forest is telling us something," {params.partner_name} said.'
    )
    hero.memes["praise"] += 1
    hero.memes["showmanship"] += 1
    partner.meters["attention"] += 1
    world.para()

    world.say(
        f"Then they found trouble: {threat['danger']}. "
        f"{params.name} stepped forward, ready to make a dramatic leap, but {params.partner_name} held up a hand."
    )
    world.say(
        f'"Wait. What did you notice before we arrived?" asked {params.partner_name}. '
        f'"The scratches, the ash, and the feathers gave us a warning," said {params.name}.'
    )
    world.say(
        f"The clue was clear: {threat['clue']}. This foreshadowing had appeared before the danger, "
        "but the cheering had almost made the heroes miss it."
    )
    hero.meters["danger_awareness"] += 1
    partner.meters["attention"] += 1
    partner.memes["trust"] += 1
    world.para()

    world.say(
        f'"A real superhero protects people before chasing praise," said {params.name}. '
        f'"And a real partner helps the hero notice what a cape cannot see," replied {params.partner_name}.'
    )
    world.say(f"Together they chose a careful plan: {threat['plan']}.")
    hero.meters["courage"] += 1
    partner.meters["helpfulness"] += 1
    world.say(
        f"{params.name} used the glamorous costume to be easy to spot, while "
        f"{params.partner_name} watched the warning signs and guided the group."
    )
    world.para()

    world.say(
        f"The plan worked. {threat['rescue']} The cheers returned, but this time the praise was different."
    )
    world.say(
        f'"Praise {params.name} for listening!" called a hiker. '
        f'"Praise {params.partner_name} for seeing the clue!" added another.'
    )
    hero.meters["joy"] += 1
    hero.memes["praise"] += 1
    world.facts["resolved"] = True
    world.say(
        f"{REFLECTIONS[params.reflection % len(REFLECTIONS)]} "
        f"{threat['ending']}"
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    threat = world.facts["threat"]
    prompts = [
        "Write a child-friendly superhero story in which glamorous praise must not distract from safety.",
        f"Use foreshadowing on a forest trail to show how {hero.label} and {partner.label} notice danger.",
        f"Show why the final praise belongs to both {hero.label} and {partner.label}, not only to the glamorous hero.",
    ]
    story_questions = [
        QAItem(
            question=f"What made {hero.label}'s costume glamorous?",
            answer=f"{hero.label} wore {world.facts['costume']}, which made the young hero easy to notice on the forest trail.",
        ),
        QAItem(
            question=f"What foreshadowing clue did {hero.label} and {partner.label} notice?",
            answer=f"They noticed {threat['clue']}, a warning that appeared before the main danger.",
        ),
        QAItem(
            question="Why did the heroes stop chasing praise?",
            answer="They stopped chasing praise because protecting people required careful attention to the warning signs and a safe plan.",
        ),
        QAItem(
            question="What happened after the heroes followed their plan?",
            answer=threat["rescue"],
        ),
        QAItem(
            question="What did the final praise celebrate?",
            answer=f"It celebrated {hero.label} for listening and {partner.label} for noticing the clue, so the praise honored teamwork.",
        ),
    ]
    world_questions = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that hints at something important that will happen later.",
        ),
        QAItem(
            question="What does glamorous mean?",
            answer="Glamorous means especially bright, beautiful, or exciting in appearance.",
        ),
        QAItem(
            question="What is praise?",
            answer="Praise is kind approval or admiration for something someone did well.",
        ),
        QAItem(
            question="What makes someone a superhero?",
            answer="A superhero uses courage, care, and good judgment to protect others, not merely a costume or public applause.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_questions,
        world_qa=world_questions,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
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
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  setting={world.setting.label}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  foreshadowing={world.facts.get('foreshadowing')}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h).
partner(p).
noticed_clue(h,p).
careful_plan(h,p).
danger_resolved(h,p) :- noticed_clue(h,p), careful_plan(h,p).
team_praise(h,p) :- danger_resolved(h,p).
#show danger_resolved/2.
#show team_praise/2.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "h"),
            asp.fact("partner", "p"),
            asp.fact("noticed_clue", "h", "p"),
            asp.fact("careful_plan", "h", "p"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(
        asp_program("#show danger_resolved/2. #show team_praise/2.")
    )
    found = {
        (symbol.name, tuple(argument.name for argument in symbol.arguments))
        for symbol in symbols
        if symbol.name in {"danger_resolved", "team_praise"}
    }
    expected = {
        ("danger_resolved", ("h", "p")),
        ("team_praise", ("h", "p")),
    }
    if found != expected:
        print("MISMATCH between ASP and Python.")
        print("  asp:", sorted(found))
        print("  expected:", sorted(expected))
        return 1

    sample = generate(
        StoryParams(
            threat="fallen_bridge",
            costume="starlight",
            name="Luna",
            partner_name="Pip",
        )
    )
    if not sample.story or not sample.world.facts["resolved"]:
        print("MISMATCH: generated story did not resolve.")
        return 1
    print("OK: ASP twin matches the Python story gate.")
    return 0


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
        print(asp_program("#show danger_resolved/2. #show team_praise/2."))
        return

    if args.asp:
        import asp

        symbols = asp.one_model(
            asp_program("#show danger_resolved/2. #show team_praise/2.")
        )
        print("\n".join(sorted(str(symbol) for symbol in symbols)))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for threat in THREATS:
            params = StoryParams(
                threat=threat,
                costume="starlight",
                name="Luna",
                partner_name="Pip",
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
