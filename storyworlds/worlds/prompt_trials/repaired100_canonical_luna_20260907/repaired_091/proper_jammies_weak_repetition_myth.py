#!/usr/bin/env python3
"""
Story world: proper jammies, a weak refrain, and a small bedtime myth.
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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    moon_garden: str = "the Moon Garden"
    hero: str = "Luna"
    helper: str = "Milo"
    seed: Optional[int] = None


SCENARIOS = (
    {
        "name": "the three-fold whisper",
        "problem": "the moon's bedtime whisper grew weak each night",
        "clue": "the same silver feather lay beside the bell three mornings in a row",
        "first": "Luna thought the moon had simply forgotten the words",
        "cause": "a little moth had carried away one thread from the bell's hanging cord each night",
        "repair": "Milo tied three proper knots in the cord and returned the feather to the moth's nest",
        "dialogue": '"The whisper is not gone," Milo said. "It is repeating a smaller path."',
        "change": "the moon's whisper became strong enough to reach every sleeping flower",
        "ending": "the bell rang once, twice, and three times, and the whole garden dreamed beneath a bright moon",
        "lesson": "repeated clues can make a weak truth strong enough to hear",
    },
    {
        "name": "the backwards slippers",
        "problem": "Luna's proper jammies kept appearing with their slippers facing the wrong way",
        "clue": "each pair left two matching crescent marks in the flour by the hearth",
        "first": "Luna wondered if a night sprite was teasing her",
        "cause": "the warm hearth breeze turned the slippers whenever the door opened",
        "repair": "the children moved the slippers onto a low rack and placed a smooth stone against the door",
        "dialogue": '"Ask what happens every time," Luna said. "The same breeze may be answering us."',
        "change": "a puzzling prank became a simple lesson in noticing repeated causes",
        "ending": "the slippers waited toe to toe while Luna slept in her proper jammies",
        "lesson": "a repeated pattern can reveal an ordinary cause hiding inside a magical-looking mystery",
    },
    {
        "name": "the dim star stitch",
        "problem": "one star stitched on Luna's jammies gave only a weak glow",
        "clue": "it brightened whenever Luna repeated the old garden verse",
        "first": "They believed the star had become lonely",
        "cause": "the verse's repeating rhythm warmed the tiny moon-thread sewn beneath it",
        "repair": "Luna and Milo sang the verse three times while a tailor secured the loose thread",
        "dialogue": '"Say it again," Luna whispered. "The star remembers through repetition."',
        "change": "the weak star shone steadily and helped guide a lost moth home",
        "ending": "the golden stitch blinked above Luna's heart as the moth settled safely by the gate",
        "lesson": "patient repetition can help something small recover its strength",
    },
    {
        "name": "the shy night drum",
        "problem": "the garden drum made a weak sound whenever the first star appeared",
        "clue": "its deepest note returned after Luna tapped the same gentle pattern three times",
        "first": "Milo feared the drum had forgotten how to call the stars",
        "cause": "a dry leaf had slipped beneath its skin and softened the first blow",
        "repair": "the children asked the keeper to lift the drum safely and brush away the leaf",
        "dialogue": '"Listen between the taps," Milo said. "The quiet part is telling us where to look."',
        "change": "the drum became a calm signal instead of a frightening riddle",
        "ending": "three round notes floated over the garden, and the stars answered without hurry",
        "lesson": "careful repetition helps us hear what a first attempt hides",
    },
)

OPENINGS = (
    "In the first age, when the stars still learned their names, Luna lived beside a garden that opened only at moonrise.",
    "Long ago, the Moon Garden kept a small secret for every child who wore proper jammies to bed.",
    "Before the night birds knew their songs, Luna discovered that even a weak sound might carry a strong message.",
    "At the edge of the sleeping world stood a silver garden where every repeated thing became a clue.",
)

TRANSITIONS = (
    "So Luna and Milo did not guess again. They watched, listened, and counted what happened each time.",
    "They repeated the test gently, because a myth may begin with wonder but wisdom begins with care.",
    "The children marked the first clue with a pebble, then waited for the pattern to return.",
    "They compared the first night with the second and the second with the third, until the garden's secret grew clear.",
)

VERSES = (
    "Moon above, moon below, guide the quiet seeds to grow.",
    "Softly turn, silver light; keep the little dreams upright.",
    "One small word, then one more; let the night remember its door.",
)

QA_STYLES = (
    (
        "What troubled Luna in {name}?",
        "What repeated clue helped her?",
        "What caused the trouble?",
        "How was it repaired?",
        "What changed after the repair?",
        "What lesson did Luna learn?",
    ),
    (
        "Why did the mystery of {name} begin?",
        "Which observation pointed toward the answer?",
        "What had really happened?",
        "What safe action solved the problem?",
        "How did the weak thing become stronger?",
        "What did the children understand?",
    ),
)


@dataclass
class World:
    garden: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


def tell(params: StoryParams) -> World:
    if not params.hero.strip() or not params.helper.strip():
        raise StoryError("hero and helper names must not be empty")
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    transition = TRANSITIONS[rng.randrange(len(TRANSITIONS))]
    verse = VERSES[rng.randrange(len(VERSES))]
    repeats = 3 + rng.randrange(2)

    world = World(params.moon_garden)
    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="girl",
            label=params.hero,
            traits=["curious", "patient"],
            memes={"wonder": 1, "courage": 1},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="boy",
            label=params.helper,
            traits=["careful", "kind"],
            memes={"friendship": 1},
        )
    )
    moon = world.add(
        Entity(
            id="moon",
            kind="celestial",
            type="moon",
            label="the moon",
            meters={"light": 1, "voice": 0.35},
            memes={"watchfulness": 1},
        )
    )
    jammies = world.add(
        Entity(
            id="jammies",
            kind="clothing",
            type="jammies",
            label="proper jammies",
            owner=hero.id,
            meters={"proper": 1, "warmth": 1},
            memes={"comfort": 1},
        )
    )

    world.facts = {
        "hero": hero.id,
        "helper": helper.id,
        "scenario": scenario["name"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "first": scenario["first"],
        "cause": scenario["cause"],
        "repair": scenario["repair"],
        "dialogue": scenario["dialogue"],
        "change": scenario["change"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
        "verse": verse,
        "repeats": repeats,
        "qa_style": rng.randrange(len(QA_STYLES)),
    }

    world.say(opening)
    world.say(
        f"{hero.id} wore {jammies.label}, buttoned properly from chin to ankle, "
        f"and met {helper.id} beside the silver gate of {world.garden}."
    )
    world.say(f"That night, {scenario['problem']}.")
    world.para()

    world.say(f"{scenario['first']}.")
    world.say(f"On the first morning, {scenario['clue']}.")
    world.say(transition)
    world.say(
        f"{hero.id} and {helper.id} repeated their gentle watch {repeats} times. "
        f"Each time they whispered, “{verse}” and wrote down what changed."
    )
    world.say(scenario["dialogue"])
    world.para()

    world.say(f"At last, the pattern revealed the cause: {scenario['cause']}.")
    world.say(f"They called for the garden keeper, and {scenario['repair']}.")
    world.say(f"Then {scenario['change']}.")
    moon.meters["voice"] = 1
    moon.memes["radiance"] = 1
    hero.memes["understanding"] = 1
    helper.memes["confidence"] = 1
    jammies.memes["bedtime_ready"] = 1

    world.say(
        f'"I thought the first sign was magic enough," {hero.id} admitted. '
        f'"It was," {helper.id} replied, "but repeating it helped us understand what kind of magic it was."'
    )
    world.para()
    world.say(f"They carried home the lesson that {scenario['lesson']}.")
    world.say(f"Before sleep, {scenario['ending']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Tell a child-friendly myth in {world.garden} about {facts['problem']}; include proper jammies and a repeated clue.",
        f"Show {facts['hero']} and {facts['helper']} using this clue: {facts['clue']}.",
        f"End with a transformation in which {facts['change']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    template = QA_STYLES[facts["qa_style"]]
    questions = [
        item.format(
            name=facts["scenario"],
            hero=facts["hero"],
            helper=facts["helper"],
        )
        for item in template
    ]
    return [
        QAItem(
            question=questions[0],
            answer=f"The trouble was that {facts['problem']}.",
        ),
        QAItem(
            question=questions[1],
            answer=f"They noticed that {facts['clue']}. Repeating the watch showed that this clue belonged to the pattern.",
        ),
        QAItem(
            question=questions[2],
            answer=f"They discovered that {facts['cause']}.",
        ),
        QAItem(
            question=questions[3],
            answer=f"The children used a safe repair: {facts['repair']}.",
        ),
        QAItem(
            question=questions[4],
            answer=f"After the repair, {facts['change']}.",
        ),
        QAItem(
            question=questions[5],
            answer=f"They learned that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are jammies?",
            answer="Jammies are comfortable clothes worn for sleeping. Proper jammies fit safely and comfortably before bedtime.",
        ),
        QAItem(
            question="Why can repetition help solve a mystery?",
            answer="Repetition lets observers compare several similar events, making a reliable pattern easier to notice.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style imaginative story that uses memorable characters and events to explain an idea or teach a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


ASP_RULES = r"""
character(X) :- girl(X).
character(X) :- boy(X).
proper_jammies(J,X) :- jammies(J), worn_by(J,X), proper(J).
repeated_clue(X) :- clue(X), observed_three_times(X).
understood(H) :- character(H), repeated_clue(C), uses(H,C).
strong_voice(M) :- moon(M), repaired.
myth_resolved(H,M) :- character(H), moon(M), understood(H), strong_voice(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("girl", "luna"),
            asp.fact("boy", "milo"),
            asp.fact("jammies", "jammies"),
            asp.fact("worn_by", "jammies", "luna"),
            asp.fact("proper", "jammies"),
            asp.fact("clue", "feather"),
            asp.fact("observed_three_times", "feather"),
            asp.fact("uses", "luna", "feather"),
            asp.fact("uses", "milo", "feather"),
            asp.fact("moon", "moon"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show proper_jammies/2.\n"
            "#show repeated_clue/1.\n"
            "#show myth_resolved/2.\n"
        )
    )
    atoms = {(symbol.name, len(symbol.arguments)) for symbol in model}
    needed = {
        ("proper_jammies", 2),
        ("repeated_clue", 1),
        ("myth_resolved", 2),
    }
    if not atoms >= needed:
        print("MISMATCH: ASP rules did not produce expected facts.")
        return 1

    for seed in range(5):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or "jammies" not in sample.story or "repeated" not in sample.story:
            print("MISMATCH: generated story failed domain checks.")
            return 1
        if len(sample.story_qa) < 3:
            print("MISMATCH: generated story lacks grounded QA.")
            return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime myth about proper jammies, a weak sign, and repetition."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--moon-garden", default="the Moon Garden")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--helper", default=None)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        moon_garden=args.moon_garden,
        hero=args.hero or rng.choice(["Luna", "Nora", "Mira", "Tala"]),
        helper=args.helper or rng.choice(["Milo", "Pip", "Oren", "Theo"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: {world.facts}")
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
        print(
            asp_program(
                "#show proper_jammies/2.\n"
                "#show repeated_clue/1.\n"
                "#show myth_resolved/2."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show proper_jammies/2.\n"
                "#show repeated_clue/1.\n"
                "#show myth_resolved/2."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(SCENARIOS)):
            params = StoryParams(seed=base_seed + index)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
