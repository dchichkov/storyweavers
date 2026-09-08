#!/usr/bin/env python3
"""
A small standalone rhyming storyworld about a bazooka, a slither, bravery,
and the moral value of careful kindness.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


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
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
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
    hero: str
    friend: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    task: str
    threat: str
    rushed_action: str
    consequence: str
    clue: str
    brave_action: str
    reveal: str
    repair: str
    outcome: str
    moral: str
    ending: str


HERO_NAMES = ["Luna", "Milo", "Nia", "Tara", "Oren", "Pia"]
FRIEND_NAMES = ["Pip", "Bram", "Zee", "Cora", "Finn", "Mina"]
PLACES = [
    "the moonlit meadow",
    "the whispering wood",
    "the rainbow ridge",
    "the little village square",
]
TELLING_MODES = ["arrival", "warning", "question", "countdown", "memory", "song"]

SCENARIOS = [
    Scenario(
        "garden_gate",
        "carry bright seeds to a sleepy garden",
        "a silver slither curled across the garden gate",
        "aimed the bazooka at the slither",
        "the blast shook the gate and scattered seeds into the lane",
        "the slither hummed whenever the garden bell rang",
        "lowered the bazooka and followed the gentle bell tune",
        "the slither was a shy vine guarding the garden's thirsty roots",
        "gathered the seeds, moved the vine with care, and watered its roots",
        "the gate opened wide and every seed found a soft place to grow",
        "Bravery is not making the loudest sound; it is choosing the kindest safe act",
        "green shoots rose in rows as the silver vine curled beneath the sun",
    ),
    Scenario(
        "bridge_riddle",
        "bring warm bread across a small wooden bridge",
        "a quick green slither blocked the bridge rails",
        "lifted the bazooka and shouted for the creature to flee",
        "the frightened slither slipped away and loosened the bridge rope",
        "tiny crumbs led from the bridge to a cold nest below",
        "stood still, spoke softly, and used the bazooka's empty tube as a warm shelter",
        "the slither was a parent snake protecting hungry hatchlings",
        "shared the bread, tied the rope, and guided the family to a sunny bank",
        "the bridge held firm while the hatchlings napped in a golden patch",
        "Moral value grows when courage makes room for another creature's need",
        "warm bread was shared on the bank, and the bridge sang in the breeze",
    ),
    Scenario(
        "bell_tower",
        "ring the village bell before the evening storm",
        "a long slither wrapped around the bell rope",
        "fired the bazooka's harmless puff to knock it loose",
        "the rope snapped and the bell stayed silent",
        "the slither tightened only when thunder shook the tower",
        "climbed carefully, covered the slither from the rain, and waited for calm",
        "the creature had wedged there to keep its tiny eggs dry",
        "built a leaf shelter, repaired the rope, and rang the bell by hand",
        "the villagers reached safe homes before the storm poured down",
        "Real bravery protects the small, even when no crowd can cheer",
        "the bell rang clear while little silver tracks shone below the tower",
    ),
    Scenario(
        "river_lantern",
        "float a lantern down the river for the night festival",
        "a dark slither tangled the lantern in the reeds",
        "poked at the reeds with the bazooka",
        "the lantern tipped and its flame nearly went out",
        "a soft blue glow blinked beneath the water",
        "set the bazooka down and used a branch to lift the tangle slowly",
        "the slither was a river eel caught in the festival ribbon",
        "freed the eel, relit the lantern, and tied the ribbon to a safe post",
        "the lantern floated on while the eel flashed beside it",
        "Courage joins careful hands with a heart that refuses to harm",
        "blue ripples carried the lantern toward stars reflected in the stream",
    ),
    Scenario(
        "hilltop_flag",
        "raise a bright flag above the hilltop school",
        "a restless slither hid inside the flag basket",
        "swung the bazooka toward the basket in alarm",
        "the flag tore and the frightened creature slid toward the cliff",
        "a tiny whistle sounded from the basket's shadow",
        "held the basket steady and called for help instead of firing",
        "the slither was a lost lizard whose nest lay beneath the flagpole",
        "moved the nest to a warm stone and stitched the flag with red thread",
        "the flag flew again, and the lizard returned safely to its nest",
        "The moral value of bravery is care for life, not victory over fear",
        "red and gold cloth waved while the lizard basked below",
    ),
    Scenario(
        "orchard_path",
        "guide a cart of apples along the orchard path",
        "a striped slither crossed the wheels",
        "revved the bazooka cart and tried to rush past",
        "the wheel bumped a basket and apples rolled downhill",
        "the slither paused beside a patch of broken glass",
        "stopped the cart, gathered the apples, and cleared the glass first",
        "the slither had been warning travelers away from the sharp path",
        "marked a safer trail and offered the creature a sunny stone",
        "the apples arrived whole and the orchard path became safe for all",
        "Bravery means stopping for the truth, even when haste feels easier",
        "apples glowed in baskets while the striped slither rested by the clear trail",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming storyworld about a bazooka, a slither, and brave kindness."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != hero])
    return StoryParams(
        hero=hero,
        friend=friend,
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("domain", "rhyming_story"),
            asp.fact("object", "bazooka"),
            asp.fact("creature", "slither"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "moral_value"),
            asp.fact("rule", "care_before_force"),
        ]
    )


ASP_RULES = r"""
safe_choice :- feature(bravery), rule(care_before_force).
#show domain/1.
#show object/1.
#show creature/1.
#show feature/1.
#show rule/1.
#show safe_choice/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    objects = asp.atoms(model, "object")
    creatures = asp.atoms(model, "creature")
    features = sorted(asp.atoms(model, "feature"))
    safe = asp.atoms(model, "safe_choice")
    if objects == [("bazooka",)] and creatures == [("slither",)] and features == [
        ("bravery",),
        ("moral_value",),
    ] and safe == [()]:
        print("OK: ASP and Python story features agree.")
        return 0
    print("MISMATCH: ASP twin did not produce the required domain facts.")
    return 1


def _scenario(params: StoryParams) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.key == params.scenario:
            return scenario
    raise StoryError(f"Unknown scenario: {params.scenario}")


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    hero = params.hero
    friend = params.friend
    place = params.place
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Look out!" cried {friend}, in a worried shout.',
            f"{hero} held the bazooka tight as they entered {place}.",
        ]
    if mode == "question":
        return [
            f'"Can bravery be quiet?" asked {hero}, bright-eyed.',
            f'"It can," said {friend}. "Let kindness be our guide."',
            f"Together they reached {place}, where they {scenario.task}.",
        ]
    if mode == "countdown":
        return [
            f"Three, two, one—the festival drum beat bright.",
            f"{hero} and {friend} hurried through {place} before night.",
            f"They {scenario.task}.",
        ]
    if mode == "memory":
        return [
            f"Years later, {hero} remembered that day.",
            f"The bazooka was loud, but a kinder choice showed the way.",
            f"It began in {place}, where they {scenario.task}.",
        ]
    if mode == "song":
        return [
            f"With a tap and a clap and a brave little cheer,",
            f"{hero} and {friend} went where the path was clear.",
            f"In {place}, they {scenario.task}.",
        ]
    return [
        f"{hero} and {friend} set out with a bright morning glow.",
        f"They carried a bazooka wherever they would go.",
        f"Through {place}, they {scenario.task}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.hero or not params.friend or not params.place:
        raise StoryError("hero, friend, and place must all be supplied.")
    if params.hero == params.friend:
        raise StoryError("hero and friend must be different characters.")

    scenario = _scenario(params)
    world = World(params.place)
    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="heroine" if params.hero in {"Luna", "Nia", "Tara", "Pia"} else "hero",
            label="brave child",
            phrase=params.hero,
            location=params.place,
            meters={"courage": 0.4, "danger": 0.2},
            memes={"bravery": 0.5},
            traits=["curious", "kind"],
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type="friend",
            label="helpful friend",
            phrase=params.friend,
            location=params.place,
            meters={"courage": 0.3, "care": 0.7},
            memes={"moral_value": 0.6},
            traits=["watchful", "gentle"],
        )
    )
    bazooka = world.add(
        Entity(
            id="bazooka",
            kind="thing",
            type="tool",
            label="bazooka",
            phrase="the bazooka",
            owner=params.hero,
            location=params.place,
            meters={"noise": 1.0, "usefulness": 0.2},
            memes={"fear": 0.4},
        )
    )
    slither = world.add(
        Entity(
            id="slither",
            kind="creature",
            type="slither",
            label="slither",
            phrase="the slither",
            location=params.place,
            meters={"danger": 0.3, "safety": 0.5},
            memes={"mystery": 0.8, "trust": 0.1},
        )
    )
    world.facts.update(
        scenario=scenario.key,
        task=scenario.task,
        threat=scenario.threat,
        rushed_action=scenario.rushed_action,
        consequence=scenario.consequence,
        clue=scenario.clue,
        reveal=scenario.reveal,
        repair=scenario.repair,
        moral=scenario.moral,
    )

    for line in _opening(params, scenario):
        world.say(line)
    world.say(f"Then came a shiver, a shimmer, a warning bright: {scenario.threat}.")
    world.para()

    world.say(
        f'"I can blast it away!" cried {params.hero}. "Wait and watch," said {params.friend}, '
        f"but fear made the bazooka feel large and the path feel tight."
    )
    world.say(f"Still, {params.hero} {scenario.rushed_action}.")
    world.say(f"The result was rough: {scenario.consequence}.")
    world.say(
        f'"A loud deed is not always a brave deed," said {params.friend}. '
        f'"Let us learn what this slither needs."'
    )
    world.para()

    world.say(f"They watched in the hush and discovered that {scenario.clue}.")
    world.say(f"Then {params.hero} chose bravery: {scenario.brave_action}.")
    world.say(f"The quiet choice revealed that {scenario.reveal}.")
    world.say(
        f'"I was scared, and I hurried," said {params.hero}. '
        f'"You were brave to stop," replied {params.friend}.'
    )
    world.para()

    world.say(f"Together they {scenario.repair}.")
    world.say(f"At once, {scenario.outcome}.")
    world.say(f"The moral value shone clear: {scenario.moral}.")
    world.say(f"{scenario.ending} And that is the brave rhyme they carried home.")

    bazooka.meters["noise"] = 0.0
    bazooka.memes["fear"] = 0.1
    slither.meters["danger"] = 0.1
    slither.meters["safety"] = 1.0
    slither.memes["trust"] = 1.0
    hero.meters["courage"] = 1.0
    hero.memes["bravery"] = 1.0
    friend.memes["moral_value"] = 1.0
    world.facts.update(resolved=True, bravery_shown=True, moral_value="care before force")

    prompts = [
        f"Write a rhyming story about {params.hero}, a bazooka, and a slither in {params.place}.",
        f"Tell a child-friendly tale showing how {params.hero} learns that bravery can be gentle.",
        f"Create a story with the moral value: {scenario.moral}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} first want to do with the bazooka?",
            answer=f"{params.hero} first wanted to use the bazooka because {scenario.threat}. "
            f"{params.hero} then {scenario.rushed_action}.",
        ),
        QAItem(
            question="What clue helped the children understand the slither?",
            answer=f"They noticed that {scenario.clue}. This showed them that {scenario.reveal}.",
        ),
        QAItem(
            question="How did the story show bravery?",
            answer=f"The story showed bravery when {params.hero} {scenario.brave_action}. "
            f"That choice protected the slither instead of using force.",
        ),
        QAItem(
            question="What moral value did the friends learn?",
            answer=f"They learned that {scenario.moral}. Their repair showed this moral value in action.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing a wise or kind action even when something feels frightening.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a guide for choosing what is good, fair, careful, or kind.",
        ),
        QAItem(
            question="What is a slither?",
            answer="A slither is a creature or movement that travels by sliding or wriggling along.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = [f"location={entity.location}"]
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Pip", "the moonlit meadow", 101, "garden_gate", "arrival"),
            StoryParams("Milo", "Cora", "the whispering wood", 202, "bridge_riddle", "question"),
            StoryParams("Nia", "Finn", "the little village square", 303, "bell_tower", "song"),
            StoryParams("Tara", "Bram", "the rainbow ridge", 404, "hilltop_flag", "warning"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target and attempt < max(50, target * 20):
            attempt += 1
            seed = base_seed + attempt
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
            header = f"### {sample.params.hero} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
