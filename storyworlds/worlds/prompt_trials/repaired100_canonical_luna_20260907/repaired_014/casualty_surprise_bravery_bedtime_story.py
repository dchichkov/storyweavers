#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a small casualty, a surprising discovery,
and the bravery to help.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
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
    place: str
    affordances: set[str] = field(default_factory=lambda: {"listen", "look", "help", "rest"})


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    grownup_name: str
    setting_index: int = 0
    surprise_index: int = 0
    bravery_index: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    place: str
    casualty: str
    clue: str
    surprise: str
    danger: str
    brave_action: str
    repair: str
    ending: str


SCENARIOS = [
    Scenario(
        "the moonlit garden",
        "a tiny moth with one damp wing",
        "a silver flutter beneath the lavender leaves",
        "the moth was not trapped at all; it was waiting for the moon to dry its wing",
        "a cold puddle beside the stone path",
        "cupped a warm leaf nearby without touching the frightened moth",
        "moved a fallen twig away from its resting place",
        "the moth lifted into the moonlight and vanished among the stars",
    ),
    Scenario(
        "the quiet porch",
        "a little sparrow with a loose thread around one foot",
        "a soft peep beneath the rocking chair",
        "the bird became calm when it heard a familiar song",
        "the rocking chair might roll toward it",
        "held the chair still and called gently for help",
        "snipped the thread while the grown-up held the lantern",
        "the sparrow flew to the warm roof and sang once before dawn",
    ),
    Scenario(
        "the sleepy playroom",
        "a toy bear with a torn blue ear",
        "a muffled sob from the basket of toys",
        "the bear's missing ear was tucked inside its own little pocket",
        "a tall stack of blocks leaned above the basket",
        "blocked the blocks with a cushion before reaching in",
        "sewed the ear back on with soft blue thread",
        "the bear rested proudly against the pillow with both ears smiling",
    ),
    Scenario(
        "the snowy doorstep",
        "a small robin shivering beside the mat",
        "two bright eyes blinking under the flowerpot",
        "the robin had followed a warm ribbon of light from the window",
        "the icy step was slippery",
        "placed a towel across the ice and moved slowly",
        "made a sheltered nest from straw and a dry scarf",
        "the robin tucked its head beneath one wing while snow whispered softly",
    ),
    Scenario(
        "the lantern-lit attic",
        "a paper star with a crumpled point",
        "a faint rustle inside an old hatbox",
        "the star had protected a sleeping beetle from the draft",
        "a loose board wobbled near the hatbox",
        "knelt far from the loose board and steadied the box with a broom",
        "pressed the star flat beneath a book",
        "the beetle crawled away as the bright paper star shone above the bed",
    ),
]


NAMES = ["Luna", "Mia", "Nora", "Ivy", "Sage", "Poppy"]
HELPERS = ["Theo", "Eli", "Milo", "Noah", "Finn", "Owen"]
GROWNUPS = ["Mama", "Papa", "Aunt Rose", "Grandma June"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_story(params: StoryParams) -> World:
    scenario = SCENARIOS[params.setting_index % len(SCENARIOS)]
    setting = Setting(scenario.place)
    world = World(setting)

    child = world.add(Entity("Child", "character", "child", params.child_name))
    helper = world.add(Entity("Helper", "character", "child", params.helper_name))
    grownup = world.add(Entity("Grownup", "character", "adult", params.grownup_name))
    casualty = world.add(Entity("Casualty", "living_thing", "casualty", scenario.casualty))

    world.facts.update(
        scenario=scenario,
        child=child,
        helper=helper,
        grownup=grownup,
        casualty=casualty,
        setting=setting,
    )

    world.say(
        f"At bedtime, {child.label} heard a tiny sound near {setting.place}. "
        f"It was not a loud sound, but it made the quiet room feel suddenly wide."
    )
    world.say(
        f"{child.label} followed the sound and found {casualty.label}. "
        f"It was a casualty of a small accident, and its frightened eyes shone in the gentle light."
    )
    casualty.memes["frightened"] = 1.0
    child.memes["worried"] = 1.0
    world.say(f'"Should we wake {grownup.label}?" asked {helper.label}.')
    world.say(
        f'"We should help first, and ask carefully," said {child.label}. '
        "The words sounded small, but the brave choice inside them was growing."
    )
    child.memes["brave"] = 1.0
    helper.memes["ready"] = 1.0

    world.paragraph()
    world.say(
        f"They looked without rushing. They noticed {scenario.clue}. "
        f"Then came the surprise: {scenario.surprise}."
    )
    world.say(
        f'"A surprise does not mean we stop being careful," whispered {helper.label}. '
        f'"It means we look again."'
    )
    world.say(
        f'"You are right," said {child.label}. "We can make one safe change at a time."'
    )
    child.memes["calm"] = 1.0
    helper.memes["calm"] = 1.0

    world.paragraph()
    world.say(
        f"They saw that {scenario.danger}. {child.label} showed bravery by {scenario.brave_action}."
    )
    world.say(
        f"Then {grownup.label} came with a warm cloth and a quiet voice. "
        f"Together they {scenario.repair}."
    )
    casualty.meters["safe"] = 1.0
    casualty.memes["comforted"] = 1.0
    world.fired.add("bravery")

    world.paragraph()
    world.say(
        f"For a moment, everyone watched in silence. Then {scenario.ending}."
    )
    world.say(
        f"{child.label} climbed into bed, still thinking about the little casualty. "
        "Bravery, {child.label} learned, did not mean feeling no fear. It meant noticing fear and choosing a careful, kind action anyway."
    )
    world.say(
        f"{helper.label} tucked the blanket beneath {child.label}'s chin. "
        f'"Good night," said {helper.label}. "Good night," answered {child.label}.'
    )
    world.facts["lesson"] = (
        "Bravery means choosing a careful, kind action even when something surprising feels frightening."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a gentle bedtime story about {child.label} helping {scenario.casualty}.",
        f"Include a surprising discovery and show bravery through a careful action near {scenario.place}.",
        "Tell a child-friendly story where a small casualty becomes safe and comforted.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    grownup: Entity = world.facts["grownup"]  # type: ignore[assignment]
    casualty: Entity = world.facts["casualty"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What casualty did {child.label} find?",
            f"{child.label} found {casualty.label}, which had been hurt or unsettled by a small accident near {world.setting.place}.",
        ),
        QAItem(
            f"What was the surprising discovery?",
            f"The surprise was that {scenario.surprise}. This changed how {child.label} and {helper.label} understood the problem.",
        ),
        QAItem(
            f"How did {child.label} show bravery?",
            f"{child.label} showed bravery by {scenario.brave_action}. {child.label} felt worried but still chose a careful way to help.",
        ),
        QAItem(
            f"How did {grownup.label} help?",
            f"{grownup.label} brought a warm cloth and a quiet voice, then helped the children when they {scenario.repair}.",
        ),
        QAItem(
            "What lesson did the bedtime story teach?",
            f"It taught that {world.facts['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a casualty?",
            "A casualty is a person or living thing that has been hurt or affected by an accident or difficult event.",
        ),
        QAItem(
            "What is surprise?",
            "Surprise is the feeling that comes when something happens differently from what you expected.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing to do a careful or kind thing even when you feel afraid.",
        ),
        QAItem(
            "Why should someone help a hurt animal carefully?",
            "A hurt animal may be frightened, so a helper should move slowly, avoid sudden touching, and ask a trusted grown-up for help.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:9} ({entity.type:12}) "
            f"meters={meters or {}} memes={memes or {}}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "casualty"),
            asp.fact("feature", "surprise"),
            asp.fact("feature", "bravery"),
            asp.fact("style", "bedtime_story"),
            asp.fact("action", "help"),
            asp.fact("action", "care"),
        ]
    )


ASP_RULES = r"""
topic(casualty).
feature(surprise).
feature(bravery).
style(bedtime_story).
action(help).
action(care).

safe_help :- topic(casualty), feature(bravery), action(help), action(care).
gentle_story :- safe_help, feature(surprise), style(bedtime_story).
story_ok :- gentle_story.

#show story_ok/0.
"""


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    if not any(symbol.name == "story_ok" for symbol in model):
        print("MISMATCH: ASP twin failed.")
        return 1

    for index in range(len(SCENARIOS)):
        params = StoryParams("Luna", "Theo", "Mama", setting_index=index)
        sample = generate(params)
        if not sample.story or "bravery" not in sample.story.lower():
            print("MISMATCH: generated story lacks the required bravery arc.")
            return 1

    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime storyworld about casualty, surprise, and bravery."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--grownup-name")
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
    return StoryParams(
        child_name=args.child_name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        grownup_name=args.grownup_name or rng.choice(GROWNUPS),
        setting_index=rng.randrange(len(SCENARIOS)),
        surprise_index=rng.randrange(len(SCENARIOS)),
        bravery_index=rng.randrange(len(SCENARIOS)),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.child_name.strip():
        raise StoryError("child_name must not be empty.")
    if not params.helper_name.strip():
        raise StoryError("helper_name must not be empty.")
    if not params.grownup_name.strip():
        raise StoryError("grownup_name must not be empty.")
    if not 0 <= params.setting_index < len(SCENARIOS):
        raise StoryError("setting_index does not name a known scenario.")

    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        for index in range(len(SCENARIOS)):
            params = StoryParams(
                child_name=args.child_name or "Luna",
                helper_name=args.helper_name or "Theo",
                grownup_name=args.grownup_name or "Mama",
                setting_index=index,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        attempts = 0
        while len(samples) < max(0, args.n) and attempts < max(20, args.n * 20):
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
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
