#!/usr/bin/env python3
"""
Story world: ten magical objects appear during a small adventure.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = "the Whispering Wilds"
    hero: str = "Luna"
    friend: str = "Pip"
    count: int = 10
    seed: Optional[int] = None


SCENARIOS = (
    {
        "title": "The Ten Lantern Seeds",
        "object": "glowing seed-lanterns",
        "problem": "the forest path had gone dark before a lost fox kit could find its den",
        "clue": "each lantern brightened when someone helped another traveler",
        "cause": "an old kindness spell had awakened the seeds beneath the moss",
        "response": "Luna and Pip carried the lanterns along the path and shared their light with every creature they met",
        "turn": "The last lantern appeared only after Luna gave her warm cloak to the shivering fox kit",
        "ending": "ten golden lanterns floated above the path and guided the fox home",
        "lesson": "kindness can reveal magic that no map can show",
    },
    {
        "title": "The Ten Silver Feathers",
        "object": "silver feathers",
        "problem": "a storm had scattered the bridge charms that kept a mountain crossing safe",
        "clue": "a feather appeared whenever Luna listened carefully instead of rushing ahead",
        "cause": "a sky spirit had hidden ten feathers inside small acts of patience",
        "response": "the friends stopped to help a tired mountain goat, repair a loose rope, and thank the wind",
        "turn": "The tenth feather appeared when Pip waited beside a frightened beetle until it crossed the trail",
        "ending": "the ten feathers formed a shining bridge across the clouded ravine",
        "lesson": "curiosity grows stronger when it makes room for gentleness",
    },
    {
        "title": "The Ten Starry Stones",
        "object": "starry stones",
        "problem": "the village well had stopped singing, and the night travelers could not find water",
        "clue": "one stone appeared whenever the friends asked a thoughtful question",
        "cause": "the well's magic answered curious hearts that noticed small needs",
        "response": "Luna and Pip followed tiny ripples, returned a dropped cup, and cleared leaves from the spring",
        "turn": "The tenth stone appeared when Luna asked what the silent well might need rather than what it could give",
        "ending": "the ten stones circled the well, which began singing a clear silver song",
        "lesson": "magic often begins with a question asked for someone else's good",
    },
    {
        "title": "The Ten Doorway Sparks",
        "object": "bright doorway sparks",
        "problem": "the castle's hidden exit had vanished while a band of small travelers was trapped inside",
        "clue": "sparks appeared whenever the friends opened a door for someone else",
        "cause": "the castle's old magic measured welcome instead of strength",
        "response": "they guided mice through cracks, lifted a fallen basket, and made space for a sleepy dragon",
        "turn": "The tenth spark appeared when Pip admitted he was afraid and asked Luna to walk beside him",
        "ending": "the sparks joined into a doorway that opened onto the moonlit road",
        "lesson": "bravery shines brightest when it includes another person",
    },
)


OPENINGS = (
    "At dawn, Luna and Pip stepped beyond the last trail marker and into an adventure.",
    "The first strange thing happened just as the forest birds began their morning song.",
    "Luna had packed a compass, a biscuit, and three questions when the path changed.",
    "Beyond the village gate, the Whispering Wilds waited beneath a veil of blue mist.",
    "Pip heard a tiny chime under the ferns, and Luna knelt to investigate.",
)

TRANSITIONS = (
    "They did not grab at the magic. They watched, listened, and looked for someone who needed help.",
    "The friends made a plan: notice carefully, act kindly, and count every new wonder.",
    "Their adventure became a trail of small choices, each one more important than a sword swing.",
    "Whenever the path seemed confusing, Luna asked what their discovery might be trying to teach them.",
)

@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    if params.count != 10:
        raise StoryError("This story domain requires exactly ten magical appearances.")
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("The hero and friend must both have names.")
    if params.hero.strip().lower() == params.friend.strip().lower():
        raise StoryError("The hero and friend need different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    transition = TRANSITIONS[rng.randrange(len(TRANSITIONS))]

    world = World(params.setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="girl",
        label=params.hero,
        memes={"curiosity": 1.0, "kindness": 1.0, "courage": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="companion",
        label=params.friend,
        memes={"curiosity": 1.0, "kindness": 1.0, "courage": 0.0},
    ))
    magic = world.add(Entity(
        id="magic",
        kind="force",
        type="enchantment",
        label=scenario["object"],
        meters={"appearances": 0.0, "active": 1.0},
        memes={"wonder": 1.0},
    ))

    world.facts = {
        "title": scenario["title"],
        "object": scenario["object"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "cause": scenario["cause"],
        "response": scenario["response"],
        "turn": scenario["turn"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }

    world.say(opening)
    world.say(
        f"{hero.label} and {friend.label} had entered {world.setting} to discover why "
        f"{scenario['problem']}."
    )
    world.say(f"Then one of the {scenario['object']} appeared beside a fern.")
    world.say(
        f"It was not the only one. By sunset, exactly ten would appear, but the friends did not know that yet."
    )
    world.para()

    world.say(f'"Did you see that?" {friend.label} asked.')
    world.say(
        f'"I did," {hero.label} replied. "Let us find out what makes the magic appear, and let us be careful with it."'
    )
    world.say(f"{scenario['clue'].capitalize()}.")
    world.say(transition)

    for number in range(1, params.count + 1):
        magic.meters["appearances"] = float(number)
        if number == 1:
            world.say(f"The first {scenario['object']} hovered above the fern.")
        elif number == 10:
            world.say(f"The tenth {scenario['object']} appeared after their kindest choice.")
        else:
            world.say(
                f"Appearance {number} came after the friends noticed a small need and answered it together."
            )

    world.say(f"{scenario['turn']}.")
    hero.memes["kindness"] = 2.0
    friend.memes["kindness"] = 2.0
    hero.memes["courage"] = 1.0
    friend.memes["courage"] = 1.0
    world.para()

    world.say(f"The mystery became clear: {scenario['cause']}.")
    world.say(f"To finish the adventure, {scenario['response']}.")
    world.say(
        f'"We were looking for treasure," {friend.label} said, "but the magic was watching how we treated others."'
    )
    world.say(
        f'"Then curiosity was the key," {hero.label} answered, "and kindness was the spell."'
    )
    world.say(f"The ten appearances transformed the dark trail into a safe way forward.")
    magic.memes["kindness"] = 1.0
    magic.memes["revealed"] = 1.0
    world.para()

    world.say(f"They carried home the lesson that {scenario['lesson']}.")
    world.say(f"At the edge of the wilds, {scenario['ending']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventurous story in which ten {f['object']} appear in {world.setting}.",
        f"Show how curiosity discovers that {f['cause']}.",
        f"End with a magical image proving that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What problem began the adventure?",
            answer=f"The adventure began because {f['problem']}.",
        ),
        QAItem(
            question="What clue helped Luna and her friend understand the magic?",
            answer=f"They noticed that {f['clue']}.",
        ),
        QAItem(
            question="Why did the ten magical objects appear?",
            answer=f"They appeared because {f['cause']}.",
        ),
        QAItem(
            question="What did the friends do to solve the problem?",
            answer=f"They solved it by {f['response']}.",
        ),
        QAItem(
            question="What important turning point happened near the end?",
            answer=f"{f['turn']}. This showed that kindness, not force, guided the magic.",
        ),
        QAItem(
            question="How did the adventure end?",
            answer=f"It ended when {f['ending']}.",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {f['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic?",
            answer="Magic is an imagined power that can make unusual and wonderful things happen.",
        ),
        QAItem(
            question="Why is curiosity useful?",
            answer="Curiosity is useful because it encourages people to ask questions, observe carefully, and learn before they act.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing another person's needs and choosing to help with care and respect.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
character(X) :- hero(X).
character(X) :- companion(X).
appeared(N) :- number(N), N >= 1, N <= 10.
ten_appearances :- appeared(1), appeared(2), appeared(3), appeared(4),
                    appeared(5), appeared(6), appeared(7), appeared(8),
                    appeared(9), appeared(10).
kindness_magic :- ten_appearances, kindness(hero), kindness(companion).
adventure_complete :- kindness_magic, curious(hero), curious(companion).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("hero", "luna"),
        asp.fact("companion", "pip"),
        asp.fact("kindness", "hero"),
        asp.fact("kindness", "companion"),
        asp.fact("curious", "hero"),
        asp.fact("curious", "companion"),
    ]
    facts.extend(asp.fact("number", number) for number in range(1, 11))
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show ten_appearances/0.\n"
            "#show kindness_magic/0.\n"
            "#show adventure_complete/0.\n"
        )
    )
    names = {symbol.name for symbol in model}
    expected = {"ten_appearances", "kindness_magic", "adventure_complete"}
    if expected <= names:
        print("OK: ASP rules produce the expected ten-appearance adventure.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected story facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An adventure in which ten magical things appear through kindness and curiosity."
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
    parser.add_argument("--setting", default="the Whispering Wilds")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--count", type=int, default=10)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting,
        hero=args.hero or rng.choice(["Luna", "Mira", "Nia", "Tala"]),
        friend=args.friend or rng.choice(["Pip", "Rowan", "Bram", "Kito"]),
        count=args.count,
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
                "#show ten_appearances/0.\n"
                "#show kindness_magic/0.\n"
                "#show adventure_complete/0."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show ten_appearances/0.\n"
                "#show kindness_magic/0.\n"
                "#show adventure_complete/0."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, scenario_seed in enumerate(range(len(SCENARIOS))):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = scenario_seed
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
