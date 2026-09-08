#!/usr/bin/env python3
"""
A small fairy-tale petting-zoo quest world.

Scribble, a young keeper, must find a missing moonbell before sunset. The
world tracks animal care, courage, worry, trust, and the physical trail from
the animal yard to the old willow. A listening goat, a patient helper, and a
kind choice turn the quest toward a gentle resolution.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    region: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["distance", "muddy", "hidden", "secure", "hungry", "sleepy"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "worry", "courage", "trust", "patience", "kindness", "pride"]:
            self.memes.setdefault(key, 0.0)


@dataclass
class Place:
    name: str
    description: str


@dataclass
class World:
    places: dict[str, Place]
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
    seed: Optional[int] = None
    name: str = "Scribble"
    helper: str = "Pip"
    goat: str = "Nettle"
    keeper: str = "Miss Fern"
    prize: str = "a silver moonbell"
    quest: str = "find the missing moonbell before sunset"
    setting: str = "petting zoo"
    style: str = "Fairy Tale"


NAMES = ["Scribble", "Doodle", "Merry", "Tansy", "Pip", "Wisp"]
HELPERS = ["Pip", "Bram", "Lulu", "Moss", "Tilly"]
GOATS = ["Nettle", "Button", "Clover", "Thimble"]
KEEPERS = ["Miss Fern", "Aunt Willow", "Keeper Rose", "Mister Rowan"]
PRIZES = ["a silver moonbell", "a pearl bell", "a tiny star bell", "a golden chime"]

QUESTS = [
    (
        "A blue ribbon trail led from the lamb pen toward the old willow.",
        "follow the ribbon marks without tearing them from the branches",
        "The last ribbon curled beside a muddy hoofprint, but the bell was nowhere in sight.",
        "a soft silver jingle came from beneath the willow roots",
        "kneel and listen instead of digging wildly",
        "lifted a fallen basket and found the bell resting in the dry grass beneath it",
        "the moonbell was safe, and the animals heard its evening song",
        "A quest is guided by patient eyes as much as by brave feet.",
        "At sunset, the moonbell rang over the petting zoo, and every lamb lifted its sleepy head.",
    ),
    (
        "A scatter of white feathers crossed the rabbit yard toward the little pond.",
        "ask the animals before chasing every bright clue",
        "The feathers ended at the pond, where ripples hid a narrow stepping-stone path.",
        "the ducks quacked three times whenever the wind touched the reeds",
        "listen to the ducks and cross only where the stones were firm",
        "followed the duck calls to a reed bundle holding the missing bell",
        "the moonbell was found without frightening a single rabbit",
        "Good questions can shorten a long quest.",
        "The ducks waddled in a golden row while the bell chimed above the quiet pond.",
    ),
    (
        "A trail of oats ran from the pony shelter to the gate beneath the hawthorn.",
        "share the oats with hungry animals before following the trail",
        "The hungry ponies crowded the gate, and the quest could not continue until they were calm.",
        "one small pony nudged an oat toward a tuft of red wool",
        "feed the ponies and inspect the red wool carefully",
        "settled the ponies, then found the moonbell tied to a loose woolen fence strand",
        "the gate opened safely and the bell came free",
        "Care for small needs before chasing a grand answer.",
        "The ponies nibbled peacefully as the moonbell glowed beside the hawthorn.",
    ),
    (
        "A line of painted stars led from the keeper's shed toward the sleepy donkey.",
        "follow the stars while keeping the donkey's water bucket steady",
        "The donkey brayed beside a tipped bucket, and the painted trail disappeared in spilled water.",
        "a damp star shone on the donkey's blanket",
        "help the donkey first, then search the blanket",
        "refilled the bucket and discovered the moonbell tucked safely beneath the blanket fold",
        "the donkey drank, and the missing bell was ready for the evening call",
        "A true quest does not leave a thirsty friend behind.",
        "The donkey drank under the first star while the moonbell answered from its blanket fold.",
    ),
    (
        "A tiny green scribble marked the gate to the goat meadow.",
        "use the scribble as a map while asking the oldest goat for help",
        "The marks stopped where tall grass covered a narrow hollow.",
        "Nettle's beard trembled whenever the breeze passed over one flat stone",
        "move the grass gently and trust the goat's quiet signal",
        "brushed the grass aside and found the moonbell beneath the flat stone",
        "the goat meadow was safe, and the quest reached its happy end",
        "Even a small scribble can point the way when kindness reads it carefully.",
        "Scribble's green mark remained by the gate, beside the bell that rang for all.",
    ),
]


@dataclass(frozen=True)
class Arc:
    premise: str
    warning: str
    consequence: str
    clue: str
    choice: str
    action: str
    result: str
    lesson: str
    ending: str


ARCS = [Arc(*quest) for quest in QUESTS]

OPENINGS = [
    "Once, at the edge of a moonlit village, there stood a cheerful petting zoo.",
    "Beyond a sugar-maple hill lay a petting zoo where every animal knew the keeper's footsteps.",
    "In a petting zoo bordered by bluebells, a young helper named {name} loved every gentle creature.",
    "Long ago, when the afternoon sun painted the fences gold, a little quest began at a petting zoo.",
]

DIALOGUES = [
    '"I will help," said {helper}. "{name}, what clue should we follow first?"',
    'The keeper asked, "Will you hurry past the animals or care for them first?" "{name} answered, "We will care for them first."',
    '"Listen," whispered {name}. "{goat} may know something." {helper} replied, "Then we shall ask kindly."',
    '"I am worried," said {name}. "{helper} smiled. "A careful quest can still be a brave one."',
    '"The bell must be near," said {name}. "{goat} gave a soft bleat, as if agreeing."',
]


def make_world(params: StoryParams) -> World:
    places = {
        "yard": Place("the petting zoo", "a friendly yard of pens, hay, and painted gates"),
        "willow": Place("the old willow", "a shady tree at the far edge of the animal yard"),
        "shed": Place("the keeper's shed", "a little shed filled with brushes, buckets, and ribbons"),
    }
    world = World(places)
    hero = world.add(Entity("hero", "character", "child", params.name, "yard"))
    helper = world.add(Entity("helper", "character", "helper", params.helper, "yard"))
    goat = world.add(Entity("goat", "animal", "goat", params.goat, "yard"))
    keeper = world.add(Entity("keeper", "character", "keeper", params.keeper, "shed"))
    bell = world.add(Entity("bell", "thing", "bell", params.prize, "unknown", owner=keeper.id))
    hero.memes.update(joy=1.0, pride=1.0, courage=1.0)
    helper.memes.update(trust=1.0, patience=1.0)
    goat.memes.update(trust=1.0, patience=1.0)
    keeper.memes.update(trust=1.0, kindness=1.0)
    bell.meters["secure"] = 1.0
    bell.meters["hidden"] = 1.0
    world.facts.update(hero=hero, helper=helper, goat=goat, keeper=keeper, bell=bell, params=params)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    goat = world.get("goat")
    keeper = world.get("keeper")
    bell = world.get("bell")

    variant = params.seed if params.seed is not None else sum(
        ord(ch) for ch in f"{params.name}|{params.helper}|{params.goat}|{params.prize}"
    )
    arc = ARCS[variant % len(ARCS)]
    opening = OPENINGS[(variant // len(ARCS)) % len(OPENINGS)].format(name=hero.label)
    dialogue = DIALOGUES[(variant // 3) % len(DIALOGUES)].format(
        name=hero.label, helper=helper.label, goat=goat.label
    )

    world.say(f"{opening} {keeper.label} cared for the animals, while {hero.label} helped with the morning chores.")
    world.say(f"Then {keeper.label}'s {params.prize} vanished before the evening bell. Without it, the animals would not know when the gates were safely closed.")
    world.para()
    world.say(arc.premise)
    world.say(f"{keeper.label} warned, \"{arc.warning}.\"")
    world.say(f"{hero.label} wanted to hurry, but the quest led through the busy {params.setting}.")
    hero.memes["pride"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(f"At first, {hero.label} nearly rushed past the animals. {arc.consequence}")
    world.say(f"Then {hero.label} noticed that {arc.clue}.")
    world.say(dialogue)
    world.say(f"The wise choice was to {arc.choice}.")
    world.para()

    hero.memes["courage"] += 1.0
    hero.memes["kindness"] += 2.0
    hero.memes["patience"] += 1.0
    helper.memes["trust"] += 1.0
    goat.memes["trust"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    world.say(f"Together, {hero.label} and {helper.label} {arc.action}.")
    world.say(f"That careful act mattered because {arc.result}.")
    world.say(f"{keeper.label} smiled. \"You found more than a bell,\" said the keeper. \"You found the right way to finish a quest.\"")
    world.say(f"{hero.label} learned that {arc.lesson}")
    world.say(arc.ending)

    hero.meters["distance"] = 1.0
    hero.meters["muddy"] = 0.0
    hero.meters["hidden"] = 0.0
    bell.meters["hidden"] = 0.0
    bell.meters["secure"] = 1.0
    bell.region = "yard"
    world.facts.update(
        arc=arc,
        resolved=True,
        clue=arc.clue,
        choice=arc.choice,
        action=arc.action,
        result=arc.result,
        lesson=arc.lesson,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    goat: Entity = world.facts["goat"]
    keeper: Entity = world.facts["keeper"]
    bell: Entity = world.facts["bell"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            f"Who went on the quest in the petting zoo?",
            f"{hero.label} went on the quest with {helper.label} to find {bell.label}. They searched carefully among the animals and the zoo paths.",
        ),
        QAItem(
            f"Why did {hero.label} need to find {bell.label}?",
            f"The bell was needed for the petting zoo's evening call, which told the animals and helpers that the gates could be closed safely.",
        ),
        QAItem(
            f"What clue helped {hero.label} during the quest?",
            f"{hero.label} noticed that {arc.clue}. That clue pointed toward the hidden bell instead of being a random mark.",
        ),
        QAItem(
            f"What did {hero.label} choose to do when the quest became difficult?",
            f"{hero.label} chose to {arc.choice}. The choice put care and patience before rushing.",
        ),
        QAItem(
            f"How did {hero.label} and {helper.label} solve the problem?",
            f"They {arc.action}. Because of that careful work, {arc.result}.",
        ),
        QAItem(
            f"What lesson did {hero.label} learn?",
            f"{arc.lesson} The lesson mattered because the quest could have failed if the animals had been ignored.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a petting zoo?", "A petting zoo is a place where people can gently meet and feed tame animals while following safety rules."),
        QAItem("What is a quest?", "A quest is a purposeful journey to find something, help someone, or complete an important task."),
        QAItem("Why should people be gentle with animals?", "People should be gentle with animals because animals can be frightened or hurt by rough handling."),
        QAItem("What does patience mean?", "Patience means waiting and acting calmly instead of rushing when something takes time."),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    arc: Arc = world.facts["arc"]
    return [
        f"Write a fairy tale about {params.name}'s quest to find {params.prize} in a petting zoo.",
        f"Tell a child-friendly quest story where a clue says that {arc.clue}.",
        f"Write a gentle fairy tale in which {params.name} learns that {arc.lesson}",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if entity.region:
            details.append(f"region={entity.region}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:7} ({entity.type:7}) " + " ".join(details))
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The quest begins when a keeper has lost the bell.
quest(hero) :- lost(bell), needs_evening_call(bell).

% A patient, kind search reveals the clue.
clue_found(hero) :- quest(hero), patient(hero), kind(hero), listens(hero).

% The bell is recovered when the clue is found and a helper is trusted.
recovered(bell) :- clue_found(hero), helper_present(helper), trusts(hero,helper).

% The animals and keeper are safe when the bell is recovered.
resolved(hero) :- recovered(bell), animals_safe, keeper_waits.

#show quest/1.
#show clue_found/1.
#show recovered/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("lost", "bell"),
            asp.fact("needs_evening_call", "bell"),
            asp.fact("patient", "hero"),
            asp.fact("kind", "hero"),
            asp.fact("listens", "hero"),
            asp.fact("helper_present", "helper"),
            asp.fact("trusts", "hero", "helper"),
            asp.fact("animals_safe"),
            asp.fact("keeper_waits"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in symbols}
    expected = {"quest/1", "clue_found/1", "recovered/1", "resolved/1"}
    if actual != expected:
        print("MISMATCH:", sorted(actual), "expected", sorted(expected))
        return 1
    for seed in range(8):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated quest did not resolve", seed)
            return 1
    print("OK: ASP twin matches the quest logic and generated stories resolve.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fairy-tale quest in a petting zoo.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--goat", choices=GOATS)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("--prize", choices=PRIZES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        goat=args.goat or rng.choice(GOATS),
        keeper=args.keeper or rng.choice(KEEPERS),
        prize=args.prize or rng.choice(PRIZES),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if params.name == params.helper:
        raise StoryError("the quest needs two different characters")
    if params.setting != "petting zoo":
        raise StoryError("this storyworld only supports the petting zoo setting")
    if params.style != "Fairy Tale":
        raise StoryError("this storyworld only supports Fairy Tale style")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Scribble", helper="Pip", goat="Nettle", keeper="Miss Fern", prize="a silver moonbell"),
    StoryParams(name="Doodle", helper="Bram", goat="Button", keeper="Aunt Willow", prize="a pearl bell"),
    StoryParams(name="Tansy", helper="Lulu", goat="Clover", keeper="Keeper Rose", prize="a tiny star bell"),
    StoryParams(name="Merry", helper="Moss", goat="Thimble", keeper="Mister Rowan", prize="a golden chime"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        symbols = asp.one_model(asp_program())
        print(" ".join(str(symbol) for symbol in symbols))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error, file=sys.stderr)
                raise SystemExit(2)
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
