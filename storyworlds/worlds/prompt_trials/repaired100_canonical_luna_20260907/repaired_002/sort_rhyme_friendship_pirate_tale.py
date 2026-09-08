#!/usr/bin/env python3
"""
A small pirate-tale storyworld about sorting a mixed treasure chest, a rhyme,
and the friendship that helps a young crew solve a deckside problem.
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
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


OPENERS = [
    "Once, aboard the little ship Moonfin,",
    "Long ago, when the sea shone like blue glass,",
    "On a bright morning in a friendly pirate harbor,",
    "Far beyond the sandy islands, there sailed a small crew",
]

SCENES = [
    "Gulls dipped beside the mast, and the brass bell chimed above the waves.",
    "The sail puffed softly while the deck boards warmed in the sun.",
    "A trail of silver fish flashed beside the ship's wooden hull.",
    "Clouds shaped like ships sailed across the wide morning sky.",
]

RHYME_LINES = {
    "sea": "Sort by the sea, and the way will be free!",
    "chest": "Sort each chest, and the crew will do their best!",
    "blue": "Sort what is true, and the ship will sail blue!",
}

ENDING_IMAGES = {
    "lantern": "That night, the sorted treasures shone beneath the lantern like a tiny map of friendship.",
    "bell": "The harbor bell rang, and every neatly sorted treasure seemed to smile from the shelf.",
    "stars": "Above the quiet ship, the stars glittered like the treasures their friends had sorted together.",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str = "moonfin"
    place: str = "the deck of the Moonfin"
    affords: set[str] = field(default_factory=lambda: {"sorting", "sailing"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    problem: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    group: str
    phrase: str
    colors: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    treasures: list[Treasure] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = copy.deepcopy(self)
        clone.paragraphs = [[]]
        return clone


ACTIVITIES = {
    "sorting": Activity(
        id="sorting",
        verb="sort the treasures",
        gerund="sorting the treasures",
        problem="the mixed treasures have hidden the captain's friendship compass",
        zone={"deck"},
        tags={"sort", "rhyme", "friendship"},
    ),
    "sailing": Activity(
        id="sailing",
        verb="prepare the ship to sail",
        gerund="preparing the ship to sail",
        problem="the mixed treasures are blocking the rope locker",
        zone={"deck"},
        tags={"sort", "friendship"},
    ),
}

TREASURES = [
    Treasure("shells", "shells", "shell", "a handful of pearly shells", "white"),
    Treasure("coins", "coins", "coin", "three bright gold coins", "gold"),
    Treasure("feathers", "feathers", "feather", "a bundle of blue feathers", "blue"),
    Treasure("beads", "beads", "bead", "a string of red beads", "red"),
]

NAMES = ["Luna", "Pip", "Mara", "Tavi", "Nico"]
FRIEND_NAMES = ["Finn", "Pia", "Jo", "Rafi", "Milo"]


@dataclass
class StoryParams:
    activity: str = "sorting"
    name: str = "Luna"
    friend: str = "Finn"
    rhyme: str = "sea"
    ending: str = "lantern"
    seed: Optional[int] = None


KNOWLEDGE = {
    "sort": [
        QAItem(
            "What does it mean to sort things?",
            "To sort things means to put items into groups because they share something, such as their kind or color.",
        )
    ],
    "rhyme": [
        QAItem(
            "What is a rhyme?",
            "A rhyme is a pair of words or lines that have matching ending sounds.",
        )
    ],
    "friendship": [
        QAItem(
            "What is friendship?",
            "Friendship is caring about one another, helping each other, and sharing trust.",
        )
    ],
    "pirate": [
        QAItem(
            "What is a pirate tale?",
            "A pirate tale is an adventure story about a crew, a ship, the sea, and a problem to solve.",
        )
    ],
}


def sort_treasures(world: World, hero: Entity, friend: Entity) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for treasure in world.treasures:
        groups.setdefault(treasure.group, []).append(treasure.label)
        treasure_location = f"the {treasure.group} pile"
        world.entities[treasure.id] = Entity(
            id=treasure.id,
            kind="object",
            type=treasure.group,
            label=treasure.label,
            phrase=treasure.phrase,
            owner=hero.id,
            location=treasure_location,
        )
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    world.facts["groups"] = groups
    return groups


def introduce(world: World, hero: Entity, friend: Entity, opener: str) -> None:
    world.say(
        f"{opener} there lived a young pirate named {hero.id}, who sailed with {friend.id}, "
        f"{hero.pronoun('possessive')} cheerful best friend."
    )
    world.say(
        f"They shared the same little hammock, the same lemon biscuits, and the same promise "
        f"never to leave a friend puzzling alone."
    )


def build_story(
    setting: Setting,
    activity: Activity,
    hero_name: str,
    friend_name: str,
    rhyme_id: str,
    ending_id: str,
    opener: str,
    scene: str,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="girl",
            phrase="a young pirate",
            location="deck",
            traits=["curious", "kind"],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type="boy",
            phrase="a cheerful friend",
            location="deck",
            traits=["patient", "loyal"],
        )
    )
    chest = world.add(
        Entity(
            id="chest",
            kind="object",
            type="chest",
            label="treasure chest",
            phrase="an old wooden treasure chest",
            location="deck",
        )
    )
    world.treasures = copy.deepcopy(TREASURES)
    world.facts.update(
        hero=hero,
        friend=friend,
        chest=chest,
        activity=activity,
        rhyme_id=rhyme_id,
        rhyme=RHYME_LINES[rhyme_id],
        ending=ENDING_IMAGES[ending_id],
        scene=scene,
        opener=opener,
        ending_id=ending_id,
    )

    introduce(world, hero, friend, opener)
    world.para()
    world.say(
        f"One afternoon, the captain opened {chest.phrase}. Inside were {TREASURES[0].phrase}, "
        f"{TREASURES[1].phrase}, {TREASURES[2].phrase}, and {TREASURES[3].phrase}, all mixed together."
    )
    world.say(scene)
    world.say(
        f"The captain frowned. \"We need to {activity.verb} before sunset, but {activity.problem}.\""
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} stared at the jumble and felt a small knot of worry.")

    world.say(
        f'"I can sort them by kind," {hero.id} said. "But I might mix them up."'
    )
    world.say(
        f'"Then I will read the labels while you make the piles," {friend.id} replied. '
        f'"Friends can use two pairs of eyes."'
    )
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1

    world.para()
    world.say(
        f"Then {friend.id} tapped the chest and chanted, \"{RHYME_LINES[rhyme_id]}\""
    )
    world.say(
        f"The rhyme gave {hero.id} a plan. {hero.pronoun('subject').capitalize()} drew a shell pile, "
        f"a coin pile, a feather pile, and a bead pile with four pieces of chalk."
    )
    groups = sort_treasures(world, hero, friend)
    pile_words = ", ".join(f"the {group} pile" for group in groups)
    world.say(
        f"Together they placed each treasure in {pile_words}. The deck became clear, "
        f"and beneath the last coin they found the captain's friendship compass."
    )
    world.say(
        f'"You did not sort alone," {friend.id} said. "You listened, and we solved it together."'
    )
    world.say(
        f'"A good crew shares the work," {hero.id} answered. "And a good rhyme helps us remember the way."'
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0

    world.para()
    world.say(
        f"With the compass safe and every treasure in its proper pile, the Moonfin turned toward home."
    )
    world.say(ENDING_IMAGES[ending_id])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly pirate tale in which {f['hero'].id} must {f['activity'].verb}.",
        f"Include this rhyme: \"{f['rhyme']}\" and show how it helps {f['hero'].id} and {f['friend'].id}.",
        f"Make friendship change the action, then end with this image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    groups = ", ".join(f"the {group} pile" for group in world.facts["groups"])
    return [
        QAItem(
            "Who were the friends aboard the Moonfin?",
            f"{hero.id}, a young pirate, and {friend.id}, a cheerful friend, sailed together aboard the Moonfin.",
        ),
        QAItem(
            f"Why did {hero.id} need to sort the treasures?",
            f"{hero.id} needed to {activity.verb} because the mixed treasures had hidden what the crew needed and crowded the deck.",
        ),
        QAItem(
            "How did the rhyme help the friends?",
            f"{friend.id} chanted \"{f['rhyme']}\". The rhyme helped {hero.id} remember the plan while they made {groups}.",
        ),
        QAItem(
            "How did friendship solve the problem?",
            f"{hero.id} made the piles while {friend.id} read the labels. By sharing the work, they found the friendship compass and cleared the deck.",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [item for topic in ["sort", "rhyme", "friendship", "pirate"] for item in KNOWLEDGE[topic]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id}: {'; '.join(details)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        activity=args.activity or rng.choice(list(ACTIVITIES)),
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        rhyme=args.rhyme or rng.choice(list(RHYME_LINES)),
        ending=args.ending or rng.choice(list(ENDING_IMAGES)),
    )


def validate_params(params: StoryParams) -> None:
    if params.name == params.friend:
        raise StoryError("The pirate and the friend must have different names.")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}")
    if params.rhyme not in RHYME_LINES:
        raise StoryError(f"Unknown rhyme: {params.rhyme}")
    if params.ending not in ENDING_IMAGES:
        raise StoryError(f"Unknown ending: {params.ending}")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_story(
        Setting(),
        ACTIVITIES[params.activity],
        params.name,
        params.friend,
        params.rhyme,
        params.ending,
        rng.choice(OPENERS),
        rng.choice(SCENES),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
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


ASP_RULES = r"""
setting(moonfin).
activity(sorting).
activity(sailing).
feature(sort).
feature(rhyme).
feature(friendship).
treasure(shells, shell).
treasure(coins, coin).
treasure(feathers, feather).
treasure(beads, bead).
friendship_changes_action(sorting).
rhyme_guides_sorting(sorting).
valid_story(S, A) :-
    setting(S),
    activity(A),
    feature(sort),
    feature(rhyme),
    feature(friendship),
    friendship_changes_action(A),
    rhyme_guides_sorting(A).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "moonfin"),
        asp.fact("activity", "sorting"),
        asp.fact("activity", "sailing"),
        asp.fact("feature", "sort"),
        asp.fact("feature", "rhyme"),
        asp.fact("feature", "friendship"),
        asp.fact("treasure", "shells", "shell"),
        asp.fact("treasure", "coins", "coin"),
        asp.fact("treasure", "feathers", "feather"),
        asp.fact("treasure", "beads", "bead"),
        asp.fact("friendship_changes_action", "sorting"),
        asp.fact("rhyme_guides_sorting", "sorting"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("moonfin", "sorting")]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        actual = set(asp_valid_combos())
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    expected = set(valid_combos())
    if actual != expected:
        print("MISMATCH between ASP and Python:")
        print("  only in ASP:", sorted(actual - expected))
        print("  only in Python:", sorted(expected - actual))
        return 1
    sample = generate(StoryParams(seed=7))
    if not sample.story or "friend" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1
    print(f"OK: ASP matches Python ({len(actual)} valid combination).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A small pirate tale about sorting treasures, rhyme, and friendship."
    )
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--rhyme", choices=RHYME_LINES)
    parser.add_argument("--ending", choices=ENDING_IMAGES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
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
    if args.asp:
        try:
            import asp

            symbols = asp.one_model(asp_program())
            print("\n".join(str(symbol) for symbol in symbols))
        except ImportError:
            raise SystemExit("ASP mode requires clingo.")
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, activity in enumerate(ACTIVITIES):
            params = StoryParams(
                activity=activity,
                name=NAMES[index % len(NAMES)],
                friend=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                rhyme=list(RHYME_LINES)[index % len(RHYME_LINES)],
                ending=list(ENDING_IMAGES)[index % len(ENDING_IMAGES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

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
