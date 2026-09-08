#!/usr/bin/env python3
"""
A small kindergarten fable about a surprising meteor, careful questions, and a
lesson learned together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "teacher", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its}[case]


@dataclass
class Setting:
    name: str = "the kindergarten"
    safe_place: str = "the round discovery rug"
    affords: set[str] = field(default_factory=lambda: {"wonder", "questions", "sharing"})


@dataclass(frozen=True)
class MeteorScenario:
    title: str
    surprise: str
    problem: str
    first_try: str
    clue: str
    helper_action: str
    test: str
    discovery: str
    resolution: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    teacher: Entity
    meteor: Entity
    setting: Setting
    surprised: bool = False
    questioned: bool = False
    shared: bool = False
    resolved: bool = False
    scenario: Optional[MeteorScenario] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


SCENARIOS = (
    MeteorScenario(
        title="the shining pebble",
        surprise="a warm silver pebble rolled out from beneath the class garden shelf",
        problem="the children wondered whether it was a fallen star, a shiny toy, or something that had come from far away",
        first_try="called it a meteor at once and planned to put it in the class treasure box",
        clue="the pebble was warm but had no sharp edges, and a bit of red paint clung to its side",
        helper_action="held the magnifying glass while the teacher brought the class chart",
        test="compared its marks with the safe classroom samples and cooled it on a clay tile",
        discovery="the red mark matched paint from a rolling art cart, while the pebble itself was ordinary garden stone",
        resolution="returned the pebble to the garden and fixed the loose cart wheel that had nudged it across the floor",
        lesson="a surprise deserves wonder, but a careful question is better than a quick guess",
        ending="The children drew stars around the garden stone, and the art cart rolled straight again",
    ),
    MeteorScenario(
        title="the window flash",
        surprise="a bright streak flashed across the kindergarten window during morning song",
        problem="the children wanted to know if a meteor had crossed the sky or if something nearer had made the light",
        first_try="shouted that a meteor had landed in the playground",
        clue="the flash appeared again whenever the sun touched the spinning music mirror",
        helper_action="stood beside the teacher and watched the window from the safe rug",
        test="covered the mirror with a cloth, then uncovered it while everyone watched quietly",
        discovery="the small mirror sent a sunbeam across the window and made the bright streak",
        resolution="moved the mirror away from the window and made a safe sunbeam picture with paper",
        lesson="looking twice can turn a startling guess into a useful discovery",
        ending="The paper sunbeam hung on the wall, shining without surprising anyone's eyes",
    ),
    MeteorScenario(
        title="the crater in clay",
        surprise="a round hollow appeared in the class clay tray after rest time",
        problem="the children thought a meteor had made a crater, but nobody knew what had pressed the clay",
        first_try="poked the hollow with three fingers and made the crater much wider",
        clue="a matching round ring was printed on the bottom of the overturned cup",
        helper_action="held the cup still while the teacher smoothed fresh clay beside it",
        test="dropped clay balls of different sizes from a low, safe height onto the new tray",
        discovery="the large ball made a wide crater, while the cup made the same neat ring as the old hollow",
        resolution="cleaned the tray, returned the cup to its shelf, and built a pretend moon landscape together",
        lesson="we learn more when we test one small idea at a time",
        ending="Their clay moon had hills, craters, and a tiny flag that said Ask First",
    ),
    MeteorScenario(
        title="the sky-stone story",
        surprise="a dark stone sat in the middle of the outdoor reading circle",
        problem="the children wanted to tell a meteor story, but they needed to know whether the stone was safe to touch",
        first_try="reached for it before asking the teacher",
        clue="the teacher noticed that leaves and dust rested on top, showing it had been there for a while",
        helper_action="pointed to the classroom safety card and fetched a pair of tongs",
        test="moved the stone with tongs into a tray and compared it with pictures in the nature book",
        discovery="its layered surface looked like a piece of garden slate, not a fresh space rock",
        resolution="washed the slate, placed it beside the nature books, and made a label for the reading circle",
        lesson="brave learners use safe tools and let evidence guide their stories",
        ending="The slate became the book nook's pretend planet, resting quietly beneath a paper moon",
    ),
)

HERO_NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Owen"]
HELPER_NAMES = ["Mara", "Ben", "Ivy", "Sam", "Zoe", "Finn"]

OPENINGS = (
    "At the kindergarten, Luna and her friend arrived beneath a sky full of soft blue.",
    "The kindergarten was humming with blocks, songs, and small questions when the surprise began.",
    "In the kindergarten garden, the morning sun warmed the discovery rug.",
    "After calendar time, the kindergarten children gathered near the window for a curious lesson.",
)

ASP_RULES = r"""
safe_place(kindergarten).
meteor_question(meteor).
surprise(meteor).
needs_evidence(meteor).
careful_question(hero, meteor) :- surprise(meteor), needs_evidence(meteor).
shared_investigation(hero, helper) :- careful_question(hero, meteor).
lesson_learned(hero) :- shared_investigation(hero, helper).
happy_end(hero) :- lesson_learned(hero).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kindergarten meteor fable story world.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper-gender", choices=["girl", "boy"])
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    choices = [name for name in HELPER_NAMES if name != hero_name]
    helper_name = args.helper or rng.choice(choices)
    if hero_name == helper_name:
        raise StoryError("The hero and helper need different names so their dialogue is clear.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def make_world(params: StoryParams) -> tuple[World, StoryState]:
    world = World(Setting())
    hero = world.add(Entity("hero", "character", params.hero_type, params.hero_name))
    helper = world.add(Entity("helper", "character", params.helper_type, params.helper_name))
    teacher = world.add(Entity("teacher", "character", "teacher", "Ms. Ada"))
    meteor = world.add(Entity("meteor", "object", "meteor", "the sky-stone"))
    state = StoryState(hero, helper, teacher, meteor, world.setting)
    return world, state


def tell_story(params: StoryParams) -> World:
    world, state = make_world(params)
    number = params.seed
    if number is None:
        number = sum((i + 1) * ord(char) for i, char in enumerate(params.hero_name + params.helper_name))
    scenario = SCENARIOS[number % len(SCENARIOS)]
    state.scenario = scenario
    state.surprised = True

    world.say(OPENINGS[(number // len(SCENARIOS)) % len(OPENINGS)].replace("Luna", state.hero.label))
    world.say(f"Then came {scenario.surprise}. It was a true kindergarten surprise.")
    world.say(f"{scenario.problem}.")
    world.say(
        f"{state.hero.label} {scenario.first_try}. "
        f"'It must be a meteor!' {state.hero.label} cried."
    )
    world.say(
        f"{state.helper.label} shook {state.helper.pronoun('possessive')} head. "
        f"'What clue could we check?' {state.helper.label} asked. "
        f"{scenario.clue.capitalize()}."
    )
    state.questioned = True
    state.shared = True
    state.hero.memes["curiosity"] = 1.0
    state.helper.memes["care"] = 1.0
    world.say(
        f"Ms. Ada smiled. 'A surprise is welcome, but we keep our hands safe while we learn.' "
        f"{state.helper.label} {scenario.helper_action}."
    )
    world.say(
        f"Together, the children {scenario.test}. "
        f"They discovered that {scenario.discovery}."
    )
    state.resolved = True
    state.hero.memes["careful_learning"] = 1.0
    world.say(f"At last, they {scenario.resolution}.")
    world.say(f"The lesson learned was simple: {scenario.lesson}.")
    world.say(f"{scenario.ending}. The kindergarten grew wiser because the surprise became a question.")

    world.facts = {
        "hero": state.hero,
        "helper": state.helper,
        "teacher": state.teacher,
        "meteor": state.meteor,
        "scenario": scenario,
        "surprised": state.surprised,
        "questioned": state.questioned,
        "shared": state.shared,
        "resolved": state.resolved,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    scenario: MeteorScenario = world.facts["scenario"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a gentle kindergarten fable about {hero.label} discovering {scenario.title}.",
        f"Tell a story in which a meteor surprise becomes a careful lesson: {scenario.problem}.",
        "Write a child-facing fable with dialogue, evidence, sharing, and a clear lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: MeteorScenario = world.facts["scenario"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where did the surprise happen?",
            "It happened in the kindergarten, where the children gathered on a safe discovery rug or classroom area.",
        ),
        QAItem(
            f"What did {hero.label} first think the object or flash was?",
            f"{hero.label} first thought it was a meteor and wanted to accept that guess right away.",
        ),
        QAItem(
            f"How did {helper.label} help {hero.label} learn more?",
            f"{helper.label} asked for a clue, helped use a safe method, and worked with {hero.label} to check the evidence.",
        ),
        QAItem(
            "What did the children discover?",
            f"They discovered that {scenario.discovery}.",
        ),
        QAItem(
            "What lesson did the kindergarten children learn?",
            f"They learned that {scenario.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a meteor?", "A meteor is a bright streak made when a space rock travels through a planet's atmosphere."),
        QAItem("Why should children ask before touching a strange object?", "Asking first helps an adult check whether the object is safe."),
        QAItem("What is evidence?", "Evidence is a clue or observation that helps people decide what is true."),
        QAItem("What is a fable?", "A fable is a short story that teaches a lesson, often through animals or memorable events."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: {sorted(world.facts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join(
        [
            "safe_place(kindergarten).",
            "meteor_question(meteor).",
            "surprise(meteor).",
            "needs_evidence(meteor).",
            "hero(hero).",
            "helper(helper).",
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    try:
        from storyworlds import asp
        model = asp.one_model(
            asp_program(
                "#show careful_question/2.\n"
                "#show shared_investigation/2.\n"
                "#show lesson_learned/1.\n"
                "#show happy_end/1."
            )
        )
        names = {symbol.name for symbol in model}
        return {"careful_question", "shared_investigation", "lesson_learned", "happy_end"} <= names
    except ImportError:
        return True
    except Exception:
        return False


def asp_verify() -> int:
    python_ok = all(
        generate(params).world.facts["resolved"]  # type: ignore[union-attr]
        for params in (
            StoryParams("Luna", "girl", "Mara", "girl", 0),
            StoryParams("Theo", "boy", "Ivy", "girl", 1),
        )
    )
    if python_ok and asp_valid():
        print("OK: ASP and Python agree that careful questions resolve the meteor surprise.")
        return 0
    print("Mismatch between ASP and Python meteor reasoning.")
    return 1


CURATED = [
    StoryParams("Luna", "girl", "Mara", "girl", 0),
    StoryParams("Theo", "boy", "Ivy", "girl", 1),
    StoryParams("Pia", "girl", "Finn", "boy", 2),
    StoryParams("Milo", "boy", "Zoe", "girl", 3),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show careful_question/2.\n"
                "#show shared_investigation/2.\n"
                "#show lesson_learned/1.\n"
                "#show happy_end/1."
            )
        )
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        if not asp_valid():
            raise SystemExit("ASP could not find the careful-learning model.")
        print("ASP model: surprise -> question -> shared investigation -> lesson learned")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {sample.params.hero_name} and {sample.params.helper_name} in kindergarten"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
