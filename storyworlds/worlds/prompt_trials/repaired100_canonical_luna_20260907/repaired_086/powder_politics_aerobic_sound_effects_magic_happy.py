#!/usr/bin/env python3
"""Animal StoryWorld about powder, politics, aerobic magic, and happy teamwork."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import copy
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


ANIMALS = ["Mara", "Pip", "Lulu", "Otto", "Nell", "Bram", "Tilly", "Wren"]
PLACES = ["the Sunbeam Grove", "the Bluebell Meadow", "the Acorn Square"]
POWDERS = [
    ("moonflower powder", "silver", "it makes tired muscles feel light"),
    ("sun-pollen powder", "golden", "it warms paws and wings"),
    ("mint cloud powder", "green", "it cools hot noses"),
    ("star-thistle powder", "blue", "it makes brave hearts glow"),
]
MOTIONS = [
    ("hop", "boing-boing", "a springy frog hop"),
    ("twirl", "whoosh-whoosh", "a gentle rabbit twirl"),
    ("stretch", "swoosh-swoosh", "a long cat stretch"),
    ("march", "tap-tap", "a steady badger march"),
]
POLITICAL_ISSUES = [
    ("where to hold the meadow exercise", "the shady hill", "the sunny clearing"),
    ("who should guard the powder jar", "the old oak", "the berry shed"),
    ("which song should begin the festival", "the robin song", "the cricket song"),
]
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    animal_name: str
    powder_id: int
    motion_id: int
    issue_id: int
    seed: Optional[int] = None


@dataclass
class World:
    place: str
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

    def copy(self) -> "World":
        return copy.deepcopy(self)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal StoryWorld about powder, politics, aerobic magic, and happiness."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--animal-name", choices=ANIMALS)
    parser.add_argument("--powder-id", type=int, choices=range(len(POWDERS)))
    parser.add_argument("--motion-id", type=int, choices=range(len(MOTIONS)))
    parser.add_argument("--issue-id", type=int, choices=range(len(POLITICAL_ISSUES)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(
            f"--{flag}", action="store_true", dest=flag.replace("-", "_")
        )
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        animal_name=args.animal_name or rng.choice(ANIMALS),
        powder_id=args.powder_id if args.powder_id is not None else rng.randrange(len(POWDERS)),
        motion_id=args.motion_id if args.motion_id is not None else rng.randrange(len(MOTIONS)),
        issue_id=args.issue_id if args.issue_id is not None else rng.randrange(len(POLITICAL_ISSUES)),
    )


def tell(params: StoryParams) -> World:
    if not 0 <= params.powder_id < len(POWDERS):
        raise StoryError("powder_id must name a registered powder")
    if not 0 <= params.motion_id < len(MOTIONS):
        raise StoryError("motion_id must name a registered aerobic motion")
    if not 0 <= params.issue_id < len(POLITICAL_ISSUES):
        raise StoryError("issue_id must name a registered meadow question")

    powder, color, benefit = POWDERS[params.powder_id]
    motion, sound, movement = MOTIONS[params.motion_id]
    issue, first_choice, second_choice = POLITICAL_ISSUES[params.issue_id]

    w = World(params.place)
    hero = w.add(
        Entity(
            id="hero",
            kind="character",
            type="animal",
            label=params.animal_name,
            role="young meadow organizer",
            meters={"energy": 0.45, "confidence": 0.55},
            memes={"curiosity": 0.8, "care": 0.8},
        )
    )
    council = w.add(
        Entity(
            id="council",
            kind="group",
            type="animal_council",
            label="the Meadow Council",
            role="neighbors who make shared decisions",
            meters={"agreement": 0.45},
            memes={"fairness": 0.9, "patience": 0.7},
        )
    )
    jar = w.add(
        Entity(
            id="powder_jar",
            kind="object",
            type="magic_powder",
            label=powder,
            role="shared festival ingredient",
            meters={"fullness": 0.8},
            memes={"wonder": 1.0},
        )
    )
    w.facts.update(
        hero=hero,
        council=council,
        powder=powder,
        powder_color=color,
        benefit=benefit,
        motion=motion,
        sound=sound,
        movement=movement,
        issue=issue,
        first_choice=first_choice,
        second_choice=second_choice,
        resolved=False,
        decision="undecided",
    )

    w.say(
        f"One bright morning in {params.place}, {hero.label} found the animals preparing an aerobic festival."
    )
    w.say(
        f"They would sprinkle a little {powder} on the grass, then practice a cheerful {motion}."
    )
    w.say(
        f"The powder was {color}, and its gentle magic meant that {benefit}."
    )
    w.para()

    w.say(f"But politics arrived before the music began: the animals argued about {issue}.")
    w.say(
        f"Some wanted {first_choice}; others wanted {second_choice}. "
        f"Every voice grew louder until nobody heard the smallest mice."
    )
    w.say(
        f"{hero.label} tapped a leaf and said, 'Let us hear one reason from each side before we choose.'"
    )
    w.say(
        f"The oldest squirrel replied, 'A fair decision must make room for every neighbor.'"
    )
    w.say(
        f"{hero.label} listened, counted the shade and space, and noticed that both choices could help."
    )
    w.para()

    w.say(
        f"Then a gust tipped the {powder} jar. Pffft! A {color} cloud rolled across the clearing."
    )
    w.say(
        f"The animals sneezed, 'Achoo!' and the festival nearly stopped, but {hero.label} remembered the council's reasons."
    )
    w.say(
        f"'We can use {first_choice} for the warm-up and {second_choice} for the final dance,' said {hero.label}."
    )
    w.say(
        f"'That is a plan we can all share,' said the squirrel. 'Who will help?'"
    )
    w.say(
        f"'I will!' cried {hero.label}. 'And everyone may choose a safe place to move.'"
    )
    w.say(
        f"Together they brushed the powder into two tiny circles and tested one at a time."
    )
    w.say(
        f"Clap-clap! {sound}! The animals began the {movement}, slowly enough for old tortoises and quickly enough for young rabbits."
    )
    w.para()

    w.say(
        f"The magic powder lifted tired feet, but kindness made the true difference."
    )
    w.say(
        f"Each animal changed the plan when a neighbor needed room, and the council's agreement rose from doubt to trust."
    )
    w.say(
        f"{hero.label} smiled and said, 'Politics can be peaceful when we listen and share the work.'"
    )
    w.say(
        f"At sunset, the animals finished with one happy circle. Boom-boom! went the soft drum, and whoosh-whoosh! went every tail."
    )
    w.say(
        f"The Meadow Council thanked {hero.label}, saved the remaining {powder} for another day, and declared the festival a success."
    )
    w.say(
        f"Under the {color} evening sky, tired animals rested together, pleased that their fair choice had made room for everyone."
    )

    hero.meters.update(energy=0.9, confidence=0.95)
    council.meters["agreement"] = 1.0
    council.memes.update(trust=1.0, joy=1.0)
    w.facts.update(
        decision=f"{first_choice} for warm-up and {second_choice} for the final dance",
        resolved=True,
        ending="the animals resting together beneath the colored evening sky",
    )
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f"Write an Animal Story about {f['hero'].label}, {f['powder']}, and a fair political decision in {w.place}.",
        f"Include aerobic movement, the sound effects {f['sound']} and 'Pffft!', and magic that helps the animals cooperate.",
        "End with a happy image showing that every animal belongs.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    return [
        QAItem(
            question=f"Why did the animals argue at the beginning?",
            answer=f"They argued about {f['issue']}, with some preferring {f['first_choice']} and others preferring {f['second_choice']}.",
        ),
        QAItem(
            question=f"How did {f['hero'].label} change the political discussion?",
            answer=f"{f['hero'].label} asked everyone to give a reason and then made a plan that used both {f['first_choice']} and {f['second_choice']}.",
        ),
        QAItem(
            question="What happened when the powder jar tipped?",
            answer=f"The {f['powder']} made a {f['powder_color']} cloud, but the animals tested it carefully instead of abandoning the festival.",
        ),
        QAItem(
            question="How did the magic powder help the festival?",
            answer=f"Its magic helped {f['benefit']}, while the animals' listening and shared work made the celebration safe.",
        ),
        QAItem(
            question="What proves the story had a happy ending?",
            answer=f"The animals completed their shared aerobic dance, saved powder for another day, and rested together beneath the colored evening sky.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is politics in a small community?",
            answer="Politics is the way a group discusses shared choices and makes decisions that affect its members. Fair politics includes listening to different reasons.",
        ),
        QAItem(
            question="What does aerobic mean?",
            answer="Aerobic activity uses repeated movement that makes the body breathe and work more actively, such as hopping, marching, stretching, or dancing.",
        ),
        QAItem(
            question="Why should a powder be tested carefully?",
            answer="A powder may be useful, irritating, or unsafe depending on what it is. Testing a small amount and following a trusted guide helps protect everyone.",
        ),
        QAItem(
            question="What makes a happy ending convincing?",
            answer="A convincing happy ending shows that the earlier problem was addressed and that the characters share a changed, hopeful situation.",
        ),
    ]


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
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("powder", "powder_color", "issue", "decision", "resolved", "ending"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "meadow"),
        asp.fact("domain", "animal_story"),
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "magic"),
        asp.fact("feature", "happy_ending"),
        asp.fact("topic", "powder"),
        asp.fact("topic", "politics"),
        asp.fact("topic", "aerobic"),
        asp.fact("value", "listening"),
        asp.fact("value", "sharing"),
    ]
    return "\n".join(facts)


ASP_RULES = """
valid_story :-
    setting(meadow),
    domain(animal_story),
    feature(sound_effects),
    feature(magic),
    feature(happy_ending),
    topic(powder),
    topic(politics),
    topic(aerobic),
    value(listening),
    value(sharing).
#show valid_story/0.
""".strip()


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(asp_program())
        accepted = any(symbol.name == "valid_story" for symbol in symbols)
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if not accepted:
        print("Mismatch: ASP gate rejected the world.")
        return 1
    params = StoryParams(
        place=PLACES[0],
        animal_name=ANIMALS[0],
        powder_id=0,
        motion_id=0,
        issue_id=0,
    )
    sample = generate(params)
    required = ("powder", "politics", "aerobic")
    if not all(word in sample.story.lower() for word in required):
        print("Mismatch: generated prose does not contain all seed concepts.")
        return 1
    if not sample.world or not sample.world.facts["resolved"]:
        print("Mismatch: generated world did not resolve.")
        return 1
    print("OK: ASP and Python accepted the powder, politics, aerobic animal story.")
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="the Sunbeam Grove",
        animal_name="Mara",
        powder_id=0,
        motion_id=0,
        issue_id=0,
    ),
    StoryParams(
        place="the Bluebell Meadow",
        animal_name="Pip",
        powder_id=1,
        motion_id=1,
        issue_id=1,
    ),
    StoryParams(
        place="the Acorn Square",
        animal_name="Lulu",
        powder_id=2,
        motion_id=2,
        issue_id=2,
    ),
    StoryParams(
        place="the Sunbeam Grove",
        animal_name="Otto",
        powder_id=3,
        motion_id=3,
        issue_id=0,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp

            print("compatible story:")
            for symbol in asp.one_model(asp_program()):
                print(symbol)
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(copy.deepcopy(params)) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce the requested number of distinct stories.")

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
