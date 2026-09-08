#!/usr/bin/env python3
"""
A child-friendly superhero storyworld about a grizzly, a dangerous scour, and
a quest to terminate the trouble without hurting anyone.

The world tracks physical meters and emotional memes. Luna's inner monologue
changes as she learns that a superhero's strongest move may be a careful one.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
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
class Quest:
    id: str
    danger: str
    clue: str
    tool: str
    helper: str
    careful_action: str
    result: str
    lesson: str
    ending: str


@dataclass
class Setting:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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


SETTING = Setting(
    name="the bright city park",
    affords={"rescue", "listening", "safe_shelter", "teamwork"},
)

QUESTS = [
    Quest(
        "humming_bridge",
        "A storm drain roared beneath the old footbridge, and a frightened grizzly cub was trapped on a muddy ledge.",
        "The cub's pawprints circled a dry patch beneath the bridge instead of leading toward the rushing water.",
        "a silver rescue rope and a warm red blanket",
        "the park gardener",
        "anchored the rope to the bridge rail, lowered the blanket, and guided the cub toward the dry patch",
        "the cub climbed safely into the blanket while the rushing water passed below",
        "real courage protects the frightened instead of making fear louder",
        "At sunrise, the grizzly family padded back toward the forest while Luna's red cape shone above the quiet bridge.",
    ),
    Quest(
        "berry_alarm",
        "A grizzly wandered into the picnic field after a loud berry-cart alarm scared it from the woods.",
        "The grizzly kept looking at the empty berry crates, not at the people waving their arms.",
        "a trail of berry baskets and a blue park whistle",
        "the berry seller",
        "made a calm trail away from the crowd and blew one soft whistle to call the ranger",
        "the grizzly followed the scent into the quiet forest edge",
        "a calm path can end a problem better than a noisy chase",
        "The grizzly disappeared among the pines, and the berry seller left a thankful basket on Luna's doorstep.",
    ),
    Quest(
        "thorned_camp",
        "A grizzly was caught behind a fallen sign near a camp where a sharp metal scour had scraped the ground.",
        "The scrape marks stopped beside a loose signpost, showing that the grizzly was blocked rather than hunting.",
        "thick gloves and a bright safety flag",
        "the camp cook",
        "raised the flag, cleared the people back, and helped the ranger lift the sign from a safe distance",
        "the grizzly backed away without being chased or hurt",
        "understanding the danger helps a hero choose the gentlest strength",
        "The repaired sign pointed hikers home, while the grizzly returned to the berry-dark woods.",
    ),
    Quest(
        "moonlit_hollow",
        "A grizzly's growl echoed through the hollow whenever a broken beacon flashed.",
        "The growl came each time the beacon's red light swept across the animal's den.",
        "a folded tarp and a hand-crank lantern",
        "the night ranger",
        "covered the flashing beacon and lit a steady lantern beside the safe trail",
        "the grizzly settled down and moved away from the hikers",
        "sometimes the brave answer is to remove the confusion",
        "The hollow grew peaceful, and Luna watched moonlight replace the troublesome flash.",
    ),
    Quest(
        "river_gate",
        "A grizzly stood beside a river gate while a swirling scour carved a hole in the bank.",
        "The animal was guarding two cubs on the high side of the gate.",
        "a long wooden pole and a roll of warning tape",
        "the bridge keeper",
        "marked the soft bank, opened the quiet side gate, and gave the cubs room to pass",
        "the family crossed to firm ground before the bank crumbled",
        "a hero notices who needs a safe exit before making a grand move",
        "The river flowed through its new channel, and the grizzly family vanished beneath the green trees.",
    ),
]

HERO_NAMES = ["Luna", "Mira", "Nova", "Tala", "Zia"]
DIALOGUES = [
    "What is the grizzly trying to tell us?",
    "Can we make a safe path instead of making more noise?",
    "What changed just before the trouble began?",
    "Where could the grizzly go without meeting the crowd?",
    "May we watch first and act carefully?",
]
INNER_THOUGHTS = [
    "I can be brave without being reckless, Luna thought.",
    "A cape is not a reason to hurry, Luna told herself.",
    "If I listen closely, perhaps the danger is giving me a clue.",
    "The grizzly needs space before it needs a dramatic rescue.",
    "My strongest power may be choosing the safest next step.",
]


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def valid_combos() -> list[tuple[str, str]]:
    return [("park", q.id) for q in QUESTS]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    power: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero quest about Luna, a grizzly, and a careful rescue."
    )
    parser.add_argument("--place", choices=["park"])
    parser.add_argument("--quest", choices=[q.id for q in QUESTS])
    parser.add_argument("--name")
    parser.add_argument(
        "--power",
        choices=["bright-cape", "super-listening", "gentle-strength"],
    )
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
    place = args.place or "park"
    quest = args.quest or rng.choice([q.id for q in QUESTS])
    name = args.name or rng.choice(HERO_NAMES)
    power = args.power or rng.choice(
        ["bright-cape", "super-listening", "gentle-strength"]
    )
    if place != "park":
        raise StoryError("This superhero quest takes place in the bright city park.")
    if quest not in {q.id for q in QUESTS}:
        raise StoryError("That quest is not part of the park's rescue map.")
    return StoryParams(place, quest, name, power)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "park":
        raise StoryError("The park is the only setting supported by this storyworld.")
    if params.quest not in {q.id for q in QUESTS}:
        raise StoryError("The requested quest is not a safe, known rescue quest.")
    if not params.name.strip():
        raise StoryError("A superhero needs a name.")
    if params.power not in {"bright-cape", "super-listening", "gentle-strength"}:
        raise StoryError("Choose a bright cape, super-listening, or gentle strength.")


def tell(world: World, params: StoryParams) -> None:
    quest = next(q for q in QUESTS if q.id == params.quest)
    variant = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(params.name + params.power)
    )
    dialogue = DIALOGUES[variant % len(DIALOGUES)]
    thought = INNER_THOUGHTS[(variant // len(DIALOGUES)) % len(INNER_THOUGHTS)]
    opening_style = variant % 4

    hero = world.add(
        Entity(
            params.name,
            kind="character",
            type="superhero",
            label=params.name,
            memes={"hope": 1.0, "courage": 1.0},
        )
    )
    grizzly = world.add(
        Entity(
            "Grizzly",
            kind="animal",
            type="grizzly",
            label="grizzly",
            memes={"fear": 1.0},
        )
    )
    helper = world.add(
        Entity(
            "Helper",
            kind="character",
            type="helper",
            label=quest.helper,
        )
    )
    danger = world.add(
        Entity(
            "Scour",
            kind="hazard",
            type="scour",
            label="scour",
            meters={"danger": 1.0},
        )
    )

    openings = [
        f"In the bright city park, {params.name} wore a red cape and watched over every path.",
        f"Each morning, the park birds greeted {params.name}, the young superhero with {params.power.replace('-', ' ')}.",
        f"People in the city knew that {params.name} protected the park with courage, questions, and a very bright cape.",
        f"At the edge of the city park stood a small rescue station where {params.name} began each superhero day.",
    ]
    world.say(openings[opening_style])
    world.say(
        f"One afternoon, a grizzly was near the path, and a dangerous scour made the ground and water unsafe."
    )
    world.say(quest.danger)
    world.para()

    add_meme(hero, "worry", 1.0)
    world.say(
        f"{params.name} started a quest to terminate the danger and help the grizzly reach safety."
    )
    world.say(thought)
    world.say(f"{params.name} almost rushed forward, but {quest.helper} called, \"{dialogue}\"")
    world.say(f"{params.name} answered, \"I will listen before I leap.\"")
    world.say(
        f"Together they noticed the clue: {quest.clue}"
    )

    world.para()
    add_meter(hero, "listening", 1.0)
    add_meme(hero, "focus", 1.0)
    world.say(
        f"The clue changed the plan. Instead of chasing the grizzly, {params.name} gathered {quest.tool}."
    )
    world.say(
        f"{params.name} and {quest.helper} worked as a team: {quest.careful_action}."
    )
    add_meter(hero, "care", 1.0)
    add_meter(helper, "teamwork", 1.0)
    add_meter(danger, "contained", 1.0)
    add_meme(grizzly, "trust", 1.0)
    world.say(f"At last, the careful plan worked: {quest.result}.")

    world.para()
    add_meme(hero, "joy", 1.0)
    add_meme(hero, "wisdom", 1.0)
    world.say(
        f"The park ranger thanked {params.name}. The scour was terminated without turning the rescue into a battle."
    )
    world.say(f"{params.name} smiled and said, \"{quest.lesson.capitalize()}.\"")
    world.say(quest.ending)

    world.facts.update(
        hero=hero,
        grizzly=grizzly,
        helper=helper,
        danger=danger,
        quest=quest,
        dialogue=dialogue,
        thought=thought,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    quest: Quest = world.facts["quest"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a superhero story for children about {hero.id}, a grizzly, and a quest to terminate a dangerous scour.",
        f"Tell a gentle superhero tale in which {hero.id} uses inner monologue and careful teamwork to solve this problem: {quest.danger}",
        f"Write a happy-ending rescue story where a grizzly is helped by noticing this clue: {quest.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    quest: Quest = world.facts["quest"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"Who went on the quest?",
            answer=f"{hero.id}, a young superhero, went on the quest to protect the grizzly and the park.",
        ),
        QAItem(
            question="What danger did the hero need to terminate?",
            answer=f"The hero needed to terminate a dangerous scour while dealing with this problem: {quest.danger}",
        ),
        QAItem(
            question="What did the hero think before acting?",
            answer=f"The hero's inner monologue was, \"{world.facts['thought']}\" This helped the hero pause instead of rushing.",
        ),
        QAItem(
            question="Who helped the superhero?",
            answer=f"{helper.label} helped the superhero by sharing observations and working on the rescue plan.",
        ),
        QAItem(
            question="What clue changed the plan?",
            answer=f"The clue was that {quest.clue} It showed that a calm, careful rescue would work better than a chase.",
        ),
        QAItem(
            question="How did the rescue end?",
            answer=f"The hero {quest.careful_action}, and then {quest.result}.",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"The ending was happy because the grizzly was safe, the scour was terminated, and {quest.ending.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear that lives in parts of North America.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or stop it.",
        ),
        QAItem(
            question="What is a scour?",
            answer="A scour is a strong washing or scraping action, often caused by moving water.",
        ),
        QAItem(
            question="Why should people give wild animals space?",
            answer="People should give wild animals space because distance helps the animals feel less threatened and keeps everyone safer.",
        ),
        QAItem(
            question="What makes a superhero?",
            answer="A superhero uses courage and special skills to help others, while also making careful and kind choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(park, humming_bridge).
valid(park, berry_alarm).
valid(park, thorned_camp).
valid(park, moonlit_hollow).
valid(park, river_gate).
safe_rescue(Q) :- valid(park,Q).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [asp.fact("place", "park")]
        + [asp.fact("quest", quest.id) for quest in QUESTS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_pairs = set(valid_combos())
        asp_pairs = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if python_pairs != asp_pairs:
        print("MISMATCH")
        print(f"Python: {sorted(python_pairs)}")
        print(f"ASP: {sorted(asp_pairs)}")
        return 1
    rng = random.Random(17)
    for _ in range(3):
        params = resolve_params(build_parser().parse_args([]), rng)
        generate(params)
    print(f"OK: ASP matches Python ({len(python_pairs)} combos); stories exercised.")
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


CURATED = [
    StoryParams("park", "humming_bridge", "Luna", "super-listening"),
    StoryParams("park", "river_gate", "Nova", "gentle-strength"),
    StoryParams("park", "berry_alarm", "Mira", "bright-cape"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
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
            header = f"### {sample.params.name}: {sample.params.quest}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
