#!/usr/bin/env python3
"""
A small detective-story world about Luna, a friendly sensor, and a quest to
solve a mysterious bell before the moonlit garden closes.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    quiet: bool = False


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    case: int = 0
    opening: int = 0
    clue_order: int = 0
    ending: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "moonlit_garden": Setting(
        place="the moonlit garden",
        affordances={"observe", "listen", "follow_clues"},
        quiet=True,
    ),
    "clock_tower": Setting(
        place="the old clock tower",
        affordances={"observe", "listen", "follow_clues"},
        quiet=False,
    ),
    "river_walk": Setting(
        place="the riverside path",
        affordances={"observe", "listen", "follow_clues"},
        quiet=False,
    ),
}

HERO_NAMES = ["Luna", "Mira", "Noah", "Iris", "Theo", "Sage"]
HELPER_NAMES = ["Pip", "Milo", "Nell", "Owen", "Bea", "Juno"]

OPENINGS = [
    "At dusk, detective {hero} received a small silver sensor with one blinking blue light.",
    "Detective {hero} was closing the casebook when a sensor chirped beside the window.",
    "The first star appeared over {place} just as {hero} clipped a listening sensor to a red notebook.",
    "On a quiet evening, {hero} and {helper} began a new detective quest with a pocket sensor.",
]

CASES = [
    {
        "mystery": "the garden bell had rung three times even though nobody had touched it",
        "wish": "to accuse the shadow by the gate",
        "clue": "the sensor recorded a soft tap followed by the rustle of broad leaves",
        "second": "a trail of damp circles led from the fountain to the bell rope",
        "answer": "a thirsty squirrel had shaken the rope while climbing past it",
        "repair": "They moved a bowl of water away from the bell and tied the rope safely above the squirrel's path.",
        "lesson": "a good detective gathers clues before naming a culprit",
        "ending": "The bell stayed quiet, and the squirrel drank from its new bowl beneath the roses.",
        "risk": "blaming someone without proof",
    },
    {
        "mystery": "a bright lamp had appeared inside the locked tool shed",
        "wish": "to pull open the door at once",
        "clue": "the sensor found warm air slipping beneath the door and heard a slow metal tick",
        "second": "a line of pale dust curved from a roof vent to an old lantern",
        "answer": "sunlight had warmed the lantern's loose reflector, making it glow through the vent",
        "repair": "They called the caretaker, who opened the shed, secured the reflector, and checked the lock.",
        "lesson": "a strange sight can have an ordinary cause",
        "ending": "The lantern rested safely on its shelf while the shed door clicked shut.",
        "risk": "forcing a locked door",
    },
    {
        "mystery": "footprints appeared beside the river path and ended at a blank stone",
        "wish": "to follow the prints into the reeds alone",
        "clue": "the sensor detected a repeating splash exactly after every third step",
        "second": "small wet feathers clung to the grass near the stone",
        "answer": "a heron had walked along the bank and stepped into the river",
        "repair": "They stayed on the path and placed a bright marker where walkers could see the slippery bank.",
        "lesson": "a trail may disappear because its traveler changes places",
        "ending": "The heron lifted off, and the marked path stayed clear for evening walkers.",
        "risk": "leaving the safe path",
    },
    {
        "mystery": "a music box played one note inside the empty clock tower",
        "wish": "to climb the dark stairs without waiting",
        "clue": "the sensor measured a tiny vibration each time the tower clock breathed out a tick",
        "second": "a loose gear was turning against a forgotten music box on the landing",
        "answer": "the clock's vibration had nudged the music box key",
        "repair": "They waited for the caretaker, who fixed the gear and carried the music box downstairs.",
        "lesson": "patience can reveal how two small movements work together",
        "ending": "The tower chimed properly, and the music box played only when someone wound it.",
        "risk": "climbing unsafe stairs",
    },
    {
        "mystery": "a red scarf kept appearing on different benches",
        "wish": "to chase the person who must be hiding it",
        "clue": "the sensor felt a steady breeze moving from the hill toward every bench",
        "second": "the scarf's loose end was caught on a bright kite string",
        "answer": "the wind was carrying the scarf after a kite tugged it free",
        "repair": "They caught the scarf, returned it to its owner, and wound the kite string around a safe reel.",
        "lesson": "movement is a clue, not proof that someone is sneaking",
        "ending": "The scarf warmed its owner, and the kite rested quietly in the grass.",
        "risk": "chasing without watching where you step",
    },
]

CLUE_LINES = [
    '"The sensor tells us what happened," said {hero}. "It does not tell us who is guilty."',
    '"Let us write each clue down," said {hero}. "A careful quest has room for questions."',
    '"We can be brave and slow," {hero} told {helper}. "Detectives protect the place they investigate."',
    '"First we observe, then we compare," said {hero}. "Guessing comes last."',
]

REFLECTIONS = [
    '"The first explanation was exciting," said {helper}, "but the clues made the true one clearer."',
    '"I nearly rushed ahead," admitted {helper}. "Waiting helped the sensor speak."',
    '"A mystery is safer when we solve it together," {helper} said.',
    '"The smallest sound gave us the biggest clue," {helper} decided.',
]

ENDINGS = [
    "Luna closed the notebook, and the solved case rested beside the quiet sensor.",
    "The friends walked home under the stars, carrying a true answer instead of a hurried guess.",
    "The sensor's blue light blinked once, as if it approved of the careful detective quest.",
    "By bedtime, every clue had a place in the notebook and every worried feeling had grown small.",
]


ASP_RULES = r"""
#show valid/2.
setting(moonlit_garden). setting(clock_tower). setting(river_walk).
affords(moonlit_garden,observe).
affords(moonlit_garden,listen).
affords(moonlit_garden,follow_clues).
affords(clock_tower,observe).
affords(clock_tower,listen).
affords(clock_tower,follow_clues).
affords(river_walk,observe).
affords(river_walk,listen).
affords(river_walk,follow_clues).
valid(Place,Action) :- affords(Place,Action).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for action in sorted(setting.affordances):
            lines.append(asp.fact("affords", place, action))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted(
        (place, action)
        for place, setting in SETTINGS.items()
        for action in setting.affordances
    )


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero_name == params.helper_name:
        raise StoryError("The detective and helper must have different names.")

    setting = SETTINGS[params.place]
    case = CASES[params.case % len(CASES)]
    world = StoryState(setting=setting)

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type="detective",
            traits=["curious", "careful"],
            memes={"confidence": 0.7, "patience": 0.8},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type="helper",
            traits=["alert", "honest"],
            memes={"wonder": 0.8, "patience": 0.6},
        )
    )
    sensor = world.add(
        Entity(
            id="sensor",
            type="sensor",
            label="a pocket sensor",
            owner=hero.id,
            meters={"range": 4.0, "sensitivity": 0.9},
            memes={"trust": 0.7},
        )
    )
    notebook = world.add(
        Entity(
            id="notebook",
            type="notebook",
            label="a red notebook",
            owner=hero.id,
            meters={"pages_left": 12.0},
        )
    )

    world.say(
        OPENINGS[params.opening % len(OPENINGS)].format(
            hero=hero.id, helper=helper.id, place=setting.place
        )
    )
    world.say(
        f"{hero.id} and {helper.id} were investigating a case: {case['mystery']}."
    )
    world.say(
        f'"That sounds like a case for us," said {helper.id}. '
        f'"Then our quest begins," replied {hero.id}.'
    )

    world.para()
    world.say(f"The sensor blinked near the first clue. {case['clue'].capitalize()}.")
    world.say(
        f"{helper.id} wanted {case['wish']}, but {hero.id} held up the notebook."
    )
    world.say(
        CLUE_LINES[params.clue_order % len(CLUE_LINES)].format(
            hero=hero.id, helper=helper.id
        )
    )
    world.say(f"Together they checked the ground and found that {case['second']}.")
    world.say(
        f"The sensor's reading changed when they tested the clue, so {hero.id} "
        f"marked the safe route and kept everyone away from the danger."
    )
    world.say(
        f"{REFLECTIONS[params.ending % len(REFLECTIONS)].format(helper=helper.id)}"
    )

    world.para()
    world.say(
        f"A caretaker arrived and listened to their report. "
        f'"The evidence points to this: {case["answer"]}," the caretaker said.'
    )
    world.say(case["repair"])
    world.say(
        f"{helper.id} smiled. "
        f'"Now I know that {case["lesson"]}," {helper.id} said.'
    )
    world.say(
        f"{hero.id} closed the notebook. "
        f'"We solved the mystery because we noticed, compared, and cared," '
        f"{hero.id} replied."
    )
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        hero=hero,
        helper=helper,
        sensor=sensor,
        notebook=notebook,
        case=case,
        place=setting.place,
        risk=case["risk"],
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a detective story about a sensor investigating {case['mystery']}.",
        f"Tell a child-friendly quest in which {world.facts['hero'].id} follows clues instead of rushing.",
        "Write a complete mystery with dialogue, a sensor, careful reasoning, and a peaceful ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    hero = facts["hero"]
    helper = facts["helper"]
    return [
        QAItem(
            question="Who led the detective quest?",
            answer=f"{hero.id} led the quest and used the sensor and notebook to examine the clues carefully.",
        ),
        QAItem(
            question=f"What mystery were {hero.id} and {helper.id} investigating?",
            answer=f"They were investigating how {case['mystery']}.",
        ),
        QAItem(
            question="What did the sensor help them notice?",
            answer=f"The sensor helped them notice that {case['clue']}. That reading gave them evidence instead of a guess.",
        ),
        QAItem(
            question="What was the real explanation?",
            answer=f"The real explanation was that {case['answer']}.",
        ),
        QAItem(
            question="What lesson did the detectives learn?",
            answer=f"They learned that {case['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sensor?",
            answer="A sensor is a device that notices a change, such as sound, movement, heat, or light, and reports what it detects.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective examines clues, asks questions, and compares evidence to understand what happened.",
        ),
        QAItem(
            question="Why should detectives avoid rushing?",
            answer="They should avoid rushing because a quick guess can miss important evidence or create a new danger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.owner:
            details.append(f"owner={entity.owner}")
        if entity.traits:
            details.append(f"traits={entity.traits}")
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) {' '.join(details)}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}.")
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        options = [name for name in HELPER_NAMES if name != hero_name]
        if not options:
            raise StoryError("Could not choose distinct detective names.")
        helper_name = rng.choice(options)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        helper_name=helper_name,
        case=rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        clue_order=rng.randrange(len(CLUE_LINES)),
        ending=rng.randrange(len(REFLECTIONS)),
    )


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective-story world with a sensor and a careful quest."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid()
        print(f"{len(combinations)} valid combinations:\n")
        for place, action in combinations:
            print(f"  {place:16} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                hero_name=f"{place.title().replace('_', '')}Detective",
                helper_name=f"{place.title().replace('_', '')}Partner",
                case=index % len(CASES),
                opening=index % len(OPENINGS),
                clue_order=index % len(CLUE_LINES),
                ending=index % len(REFLECTIONS),
            )
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce enough distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
