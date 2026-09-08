#!/usr/bin/env python3
"""
A child-facing adventure about a dorky mistake, an inflatable raft, and a
canned message that helps friendship survive a misunderstanding.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    name: str
    affordances: set[str]


@dataclass(frozen=True)
class Adventure:
    id: str
    opening: str
    obstacle: str
    clue: str
    careless_action: str
    careful_action: str
    consequence: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.events.append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(
    name="the windy Blueberry Gorge",
    affordances={"river", "cliff trail", "cave", "campfire", "teamwork"},
)

ADVENTURES = [
    Adventure(
        "silver_cave",
        "A silver bell in a cave rang whenever the river wind blew.",
        "The cave entrance stood across a fast stream, and the old footbridge had lost two boards.",
        "A line of blue paint on the rocks showed where a shallow crossing began.",
        "Luna puffed the raft too quickly and sent one side bulging like a giant cheek.",
        "Luna let out a little air, tied the rope to a tree, and asked Milo to test each knot.",
        "The raft carried both friends safely to the cave, where they found the bell's loose clapper.",
        "At sunset, the silver bell rang clearly while the repaired raft rested beside the warm campfire.",
    ),
    Adventure(
        "maple_cliff",
        "A red kite became tangled on a ledge above the gorge.",
        "The narrow trail was safe only if the climbers kept one hand on the rope.",
        "Tiny footprints stopped beside a flat stone where the wind changed direction.",
        "Luna rushed ahead with the inflatable tube tucked under one arm.",
        "Luna shared the tube as a cushion, checked the rope anchors, and let Milo lead the tricky turn.",
        "They reached the kite without stepping on the crumbling edge.",
        "The red kite flew again, and its tail pointed toward home.",
    ),
    Adventure(
        "canned_signal",
        "The explorers found a canned note wedged inside a hollow tree.",
        "The note's short words sounded angry, and Milo thought Luna had written them.",
        "A smear of berry jam on the lid matched the camp cook's basket, not Luna's pocket.",
        "Luna grabbed the note and declared that Milo did not trust her.",
        "Luna read the note aloud, asked who had sealed it, and listened before choosing sides.",
        "The message turned out to be a warning from a friendly ranger about a fallen branch.",
        "The friends moved the branch together and left their own cheerful note in the tree.",
    ),
]

NAMES = ["Luna", "Milo", "Tara", "Niko", "Pip", "Suri"]
TRAITS = ["curious", "brave", "bouncy", "thoughtful", "quick-footed"]
DIALOGUES = [
    ("“You called me a dork,” Luna said. “Did you mean it that way?”",
     "“No,” Milo answered. “I meant the raft looked funny, and I was worried.”"),
    ("“Wait,” Milo said. “What did you hear me say?”",
     "“I heard that you thought I ruined the adventure,” Luna replied."),
    ("“Friends should check the clue before they blame each other,” Luna said.",
     "“Then let us check it together,” Milo answered."),
]


@dataclass
class StoryParams:
    adventure: str
    name: str
    trait: str
    partner: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an adventure about friendship and a misunderstanding."
    )
    parser.add_argument("--adventure", choices=ADVENTURES.keys())
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--partner")
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
    adventure = args.adventure or rng.choice(list(ADVENTURES))
    if adventure not in ADVENTURES:
        raise StoryError("That adventure is not available.")
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    if name == partner:
        raise StoryError("The explorer and the partner must have different names.")
    return StoryParams(adventure, name, trait, partner)


def reasonableness_gate(params: StoryParams) -> None:
    if params.adventure not in ADVENTURES:
        raise StoryError("The chosen adventure is unknown.")
    if not params.name.strip() or not params.partner.strip():
        raise StoryError("Both adventurers need names.")
    if params.name == params.partner:
        raise StoryError("Two friends cannot share the same name in this story.")


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.meme(key) + amount


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meter(key) + amount


def tell(world: World, params: StoryParams) -> None:
    adventure = ADVENTURES[params.adventure]
    hero = world.add(Entity(params.name, "character", "child", params.name))
    partner = world.add(Entity(params.partner, "character", "child", params.partner))
    raft = world.add(Entity("raft", "thing", "inflatable raft", "the inflatable raft"))
    note = world.add(Entity("note", "thing", "canned message", "the canned message"))

    add_meme(hero, "curiosity")
    add_meme(hero, "friendship")
    add_meme(partner, "friendship")
    add_meter(raft, "air", 1.0)

    world.say(
        f"{params.name}, a {params.trait} explorer, and {params.partner}, a loyal friend, "
        f"set off through {world.setting.name} with {raft.label} and a small food tin."
    )
    world.say(adventure.opening)
    world.say(adventure.obstacle)
    world.paragraph()

    world.say(
        f"At the riverbank, {params.name} tried to inflate the raft while {params.partner} "
        f"held its rope. The raft puffed up unevenly, and {params.partner} laughed."
    )
    world.say(
        f"{params.name} heard the laugh as an insult and thought, “Everyone must think I am a dork.”"
    )
    add_meme(hero, "worry")
    add_meme(partner, "worry")

    dialogue = DIALOGUES[(params.seed or 0) % len(DIALOGUES)]
    world.say(dialogue[0])
    world.say(dialogue[1])
    world.say(
        f"{params.partner} explained that the laugh came from surprise, not dislike, and "
        f"{params.name} admitted that the crooked raft had made embarrassment grow into a "
        f"misunderstanding."
    )
    add_meme(hero, "trust")
    add_meme(partner, "trust")
    world.paragraph()

    world.say(f"Then they noticed the clue: {adventure.clue}")
    world.say(
        f"Instead of arguing, {params.name} and {params.partner} shared the work. "
        f"{params.name} {adventure.careful_action}"
    )
    add_meter(raft, "air", 1.0)
    add_meter(hero, "care", 1.0)
    add_meter(partner, "care", 1.0)
    world.say(adventure.consequence)
    world.paragraph()

    world.say(
        f"Inside the next hollow, they found {note.label}. Its words were brief, and "
        f"brief words can sound sharp when a friendship is already shaky."
    )
    world.say(
        f"{params.name} held up the tin and said, “Let us read this carefully before we guess who wrote it.”"
    )
    world.say(
        f"{params.partner} nodded. Together they checked the jam mark, the footprints, and the direction of the wind."
    )
    world.say(
        f"The clue showed that the message was meant to protect them, not scold them."
    )
    add_meme(hero, "understanding")
    add_meme(partner, "understanding")
    world.say(
        f"They followed the warning, moved the danger aside, and left a friendly message for the next travelers."
    )
    world.say(adventure.ending)

    world.facts.update(
        hero=hero,
        partner=partner,
        raft=raft,
        note=note,
        adventure=adventure,
        dialogue=dialogue,
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
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    adventure = world.facts["adventure"]
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    return [
        f"Write an adventure about {hero.label} and {partner.label}, friendship, and a misunderstanding.",
        f"Include a dorky mistake, an inflatable raft, and a canned message in a child-friendly adventure.",
        f"Show how {hero.label} and {partner.label} repair trust by checking clues together.",
        adventure.opening,
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    partner: Entity = world.facts["partner"]
    adventure: Adventure = world.facts["adventure"]
    return [
        QAItem(
            f"Who went on the adventure?",
            f"{hero.label} and {partner.label} went exploring together through Blueberry Gorge.",
        ),
        QAItem(
            "What caused the first misunderstanding?",
            f"{hero.label} thought {partner.label}'s laugh meant that {hero.label} was a dork, "
            "but the laugh came from surprise and worry about the uneven raft.",
        ),
        QAItem(
            "What did the friends do to repair their friendship?",
            f"They spoke honestly about what they had heard, listened to each other, and then "
            f"worked together after noticing this clue: {adventure.clue}",
        ),
        QAItem(
            "How did the inflatable raft help?",
            f"They carefully adjusted the inflatable raft and used it to cross the dangerous water safely.",
        ),
        QAItem(
            "What was the canned message really for?",
            "The canned message was a friendly warning about danger, not an angry message blaming either friend.",
        ),
        QAItem(
            "What changed by the end?",
            f"{hero.label} and {partner.label} trusted each other more, solved the danger together, "
            f"and left a cheerful note for the next travelers.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or sees something but gives it the wrong meaning.",
        ),
        QAItem(
            "Why is listening useful in a friendship?",
            "Listening lets friends explain what they meant, so a mistake does not grow into a fight.",
        ),
        QAItem(
            "What does inflate mean?",
            "To inflate something means to fill it with air so it becomes larger and ready to use.",
        ),
        QAItem(
            "What does canned mean?",
            "Canned means sealed in a container, such as food or a message protected inside a tin.",
        ),
        QAItem(
            "What makes an adventure safer?",
            "Checking clues, sharing jobs, and speaking honestly can make an adventure safer.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"setting: {world.setting.name}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append("events:")
    lines.extend(f"- {event}" for event in world.events)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


ASP_RULES = r"""
valid(silver_cave).
valid(maple_cliff).
valid(canned_signal).
friendship_repairs_misunderstanding :- valid(silver_cave).
friendship_repairs_misunderstanding :- valid(maple_cliff).
friendship_repairs_misunderstanding :- valid(canned_signal).
#show valid/1.
#show friendship_repairs_misunderstanding/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("domain", "friendship_adventure"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("object", "inflatable_raft"),
            asp.fact("object", "canned_message"),
            asp.fact("character", "dorky_explorer"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    models = asp.solve(asp_program(), models=1)
    if not models:
        print("MISMATCH: ASP produced no model.")
        return 1
    valid = set(asp.atoms(models[0], "valid"))
    expected = {(adventure.id,) for adventure in ADVENTURES}
    if valid != expected:
        print("MISMATCH: ASP adventure registry differs from Python.")
        return 1
    print(f"OK: ASP matches Python ({len(expected)} adventures).")
    for index, params in enumerate(curated_params(), 1):
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 4:
            print(f"MISMATCH: generated sample {index} is incomplete.")
            return 1
    print("OK: generated stories passed.")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("silver_cave", "Luna", "curious", "Milo", 11),
        StoryParams("maple_cliff", "Tara", "brave", "Niko", 17),
        StoryParams("canned_signal", "Suri", "thoughtful", "Pip", 23),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.adventure}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
