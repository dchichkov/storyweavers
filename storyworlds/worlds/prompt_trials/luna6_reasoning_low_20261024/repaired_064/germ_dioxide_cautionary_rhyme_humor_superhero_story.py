#!/usr/bin/env python3
"""A playful superhero storyworld about germs, fresh air, and careful choices."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scenario:
    germ: str
    source: str
    mess: str
    test: str
    truth: str
    fix: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    germ: str
    dioxide: str
    hero: str = "Luna"
    helper: str = "Pip"
    scenario: str = ""
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


GERMS = {
    "glitter_germ": "a glittery pretend germ",
    "muddy_germ": "a muddy little germ",
    "sneaky_germ": "a sneaky pretend germ",
}
DIOXIDES = {
    "breath": "the carbon dioxide people breathe out",
    "bubbles": "carbon dioxide bubbles in a fizzy drink",
    "classroom": "carbon dioxide in a busy classroom",
}
HEROES = {"Luna": "girl", "Milo": "boy", "Ari": "child", "Zara": "girl"}
HELPERS = {"Pip": "robot", "Nia": "girl", "Bo": "boy", "Kit": "child"}

SCENARIOS = {
    "open_window": Scenario(
        "a pretend germ had left sparkly dots near the art table",
        "the room felt stuffy after everyone made paper capes",
        "dusty paper scraps were mistaken for germs",
        "waved a paper fan and watched where the light scraps drifted",
        "the scraps moved in the draft, while the pretend germ was only glitter on a craft star",
        "opened the window with their teacher, tidied the scraps, and washed their hands",
        "fresh air helps a room feel comfortable, but it does not make every surface germ-free",
        "colorful capes rested by the breezy window as the class made a clean-up cheer",
    ),
    "fizzy_mixup": Scenario(
        "a tiny germ-shaped doodle appeared beside a cup",
        "a fizzy drink made a soft pop and released carbon dioxide bubbles",
        "someone thought every bubble carried a germ",
        "asked the teacher to show how bubbles rose from the drink",
        "the bubbles came from the fizzy drink; the doodle was just a drawing",
        "moved the drink away from the craft paper and wiped the table together",
        "carbon dioxide bubbles in a drink are not the same thing as germs",
        "the cup fizzed gently while the brave team drew a smiling bubble hero",
    ),
    "quiet_corner": Scenario(
        "a pretend germ was drawn on a classroom poster",
        "the classroom felt warm and crowded after a lively game",
        "a silly rumor said carbon dioxide was a germ",
        "listened to their teacher explain that people breathe out carbon dioxide",
        "carbon dioxide is a gas, not a germ, and the room needed a little fresh air",
        "took a calm break, asked the teacher to air the room, and washed up before snack",
        "a gas and a germ are different things, so learning the facts matters",
        "the poster's germ wore a tiny cape as everyone enjoyed the freshened room",
    ),
    "soap_signal": Scenario(
        "a pretend germ was hiding in a washable paint smudge",
        "the children had touched many props while acting out a hero rescue",
        "a cape was blamed for making the whole room unsafe",
        "checked which marks washed away and asked an adult about the rest",
        "the smudge was washable paint, while ordinary handwashing was still a sensible habit",
        "washed their hands with soap and water and put the props back neatly",
        "wash hands at helpful times, and do not let a scary guess replace a careful check",
        "the clean cape fluttered proudly as the team practiced its soap-and-water salute",
    ),
}

ASP_RULES = """
valid(Germ, Dioxide) :- germ(Germ), dioxide(Dioxide).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle superhero storyworld about germs and carbon dioxide."
    )
    parser.add_argument("--germ", choices=sorted(GERMS))
    parser.add_argument("--dioxide", choices=sorted(DIOXIDES))
    parser.add_argument("--hero")
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [
        (germ, dioxide)
        for germ in sorted(GERMS)
        for dioxide in sorted(DIOXIDES)
    ]


def asp_facts() -> str:
    import asp

    facts = [
        *(asp.fact("germ", germ) for germ in GERMS),
        *(asp.fact("dioxide", dioxide) for dioxide in DIOXIDES),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_choices = set(valid_combos())
    asp_choices = set(asp_valid_combos())
    if python_choices == asp_choices:
        print(f"OK: clingo gate matches valid_combos() ({len(python_choices)} combos).")
        return 0
    print("MISMATCH:", sorted(python_choices - asp_choices), sorted(asp_choices - python_choices))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if (not args.germ or pair[0] == args.germ)
        and (not args.dioxide or pair[1] == args.dioxide)
    ]
    if not choices:
        raise StoryError("No germ and dioxide combination fits those options.")
    germ, dioxide = rng.choice(choices)
    hero = args.hero or "Luna"
    if not hero.strip():
        raise StoryError("The hero's name must not be empty.")
    helpers = [name for name in sorted(HELPERS) if name != hero]
    if not helpers:
        helpers = sorted(HELPERS)
    return StoryParams(
        germ=germ,
        dioxide=dioxide,
        hero=hero,
        helper=args.helper or rng.choice(helpers),
        scenario=rng.choice(sorted(SCENARIOS)),
    )


def tell(params: StoryParams) -> World:
    if params.germ not in GERMS or params.dioxide not in DIOXIDES:
        raise StoryError("Choose a listed germ and dioxide topic.")
    if params.scenario not in SCENARIOS:
        raise StoryError("Choose a listed story scenario.")

    case = SCENARIOS[params.scenario]
    world = World()
    hero = world.add(Entity(params.hero, "character", "child", params.hero))
    helper = world.add(Entity(params.helper, "character", HELPERS.get(params.helper, "child"), params.helper))
    germ = world.add(Entity(params.germ, "microbe", "pretend germ", GERMS[params.germ]))
    air = world.add(Entity(params.dioxide, "gas_topic", "carbon dioxide", DIOXIDES[params.dioxide]))
    germ.meters["understood_as_pretend"] = 0
    hero.memes["curiosity"] = 1
    helper.memes["teamwork"] = 1

    world.say(
        f"When the class's superhero alarm gave a cheerful ding, {hero.label} zipped on a blue cape "
        f"and found {case.germ}. Nearby, the room had a question about {air.label}."
    )
    world.say(
        f"{hero.label} and {helper.label} were the Tiny Truth Team: brave enough to help, "
        "and wise enough to ask before they guessed."
    )
    world.para()
    world.say(
        f"A worried classmate pointed at {case.mess}. “Is the {germ.label} causing all this?” "
        f"asked {helper.label}. “And is {air.label} another germ?”"
    )
    world.say(
        f"“Let's check with our teacher,” {hero.label} replied. “A hero uses facts, not fright!”"
    )
    hero.memes["careful"] = 1
    world.say(
        f"With the teacher's help, the team {case.test}. They learned that {case.truth}."
    )
    germ.meters["understood_as_pretend"] = 1
    air.meters["explained"] = 1
    world.say(
        f"“So {air.label} isn't a germ,” said {helper.label}. “Right,” said {hero.label}. "
        "“Different things need different answers!”"
    )
    world.say(
        f"The friends {case.fix}. Their caution became a tiny rhyme: "
        "“Check what is true; then choose what to do!”"
    )
    hero.meters["helpful_actions"] = 1
    helper.meters["helpful_actions"] = 1
    world.para()
    world.say(
        f"The class remembered that {case.lesson}. Their teacher smiled at the team's "
        "superhero rule: be curious, be kind, and ask an adult when unsure."
    )
    world.say(
        f"At the end of the day, {case.ending}. {hero.label}'s cape swished like a flag, "
        "and the class cheered, “Truth Team to the rescue!”"
    )
    world.facts.update(hero=hero, helper=helper, germ=germ, air=air, case=case)
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a child-friendly superhero story starring {facts['hero'].label}, with "
        f"{facts['germ'].label} and {facts['air'].label}.",
        f"Tell a cautionary, humorous story in which the hero checks a worry about germs "
        f"and carbon dioxide with a trusted teacher.",
        f"Include a brief rhyme, spoken dialogue, a helpful choice, and the changed ending: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    return [
        QAItem(
            question=f"What did {facts['hero'].label} and {facts['helper'].label} notice?",
            answer=f"They noticed {case.germ}. The room also raised a question about {facts['air'].label}.",
        ),
        QAItem(
            question="How did the Tiny Truth Team find out what was happening?",
            answer=f"They asked their teacher and {case.test}. The explanation showed them that {case.truth}.",
        ),
        QAItem(
            question="What did the friends do after they understood the problem?",
            answer=f"They {case.fix}. Their rhyme reminded them to check what is true before choosing what to do.",
        ),
        QAItem(
            question="What lesson did the superhero team learn?",
            answer=f"They learned that {case.lesson} Their teacher encouraged them to be curious, kind, and willing to ask an adult when unsure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Are germs and carbon dioxide the same thing?",
            answer="No. Germs are tiny living things or agents that can cause infection, while carbon dioxide is a gas. A trusted adult can help explain a particular situation.",
        ),
        QAItem(
            question="What is a sensible thing to do when a child worries about germs?",
            answer="A child can ask a trusted adult, wash their hands with soap and water at appropriate times, and follow the adult's advice instead of guessing.",
        ),
        QAItem(
            question="Why can fresh air be helpful in a room?",
            answer="Fresh air can make a room feel more comfortable. It does not mean every surface is free of germs, so ordinary cleaning and handwashing still matter.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(("", "== story qa =="))
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams("glitter_germ", "breath", "Luna", "Pip", "open_window", 101),
    StoryParams("muddy_germ", "bubbles", "Milo", "Nia", "fizzy_mixup", 202),
    StoryParams("sneaky_germ", "classroom", "Ari", "Bo", "quiet_corner", 303),
    StoryParams("glitter_germ", "classroom", "Zara", "Kit", "soap_signal", 404),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all:
        print("Please choose at least one story with -n 1 or greater.")
        return
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        status = asp_verify()
        if status:
            raise SystemExit(status)
        try:
            samples = [generate(params) for params in CURATED]
            assert all(sample.story and sample.story_qa for sample in samples)
            assert all("germ" in sample.story.lower() for sample in samples)
            assert all("carbon dioxide" in sample.story.lower() for sample in samples)
        except Exception as error:
            print(f"Story verification failed: {error}")
            raise SystemExit(1) from error
        print(f"OK: generated and checked {len(samples)} complete stories.")
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for germ, dioxide in combos:
            print(f"  {germ:14} {dioxide}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
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
        header = "### curated story" if args.all else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
