#!/usr/bin/env python3
"""
A small animal-story world built around a foreshadowed phenomenon.

Seed tale idea:
- A young animal notices odd signs in the forest.
- Those signs foreshadow a bigger phenomenon: a storm is coming.
- The animal warns a friend, gathers gear, and reaches shelter in time.

The world is intentionally small and constraint-checked:
- a setting,
- a phenomenon,
- animal characters,
- an early clue that foreshadows the event,
- a practical response that changes the ending.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Animal:
    id: str
    species: str
    role: str
    label: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "it"

    def possessive(self) -> str:
        return "its"


@dataclass
class Setting:
    place: str
    shelter: str
    features: list[str] = field(default_factory=list)


@dataclass
class Phenomenon:
    id: str
    name: str
    clue: str
    effect: str
    danger: str
    sound: str
    smell: str = ""
    sky: str = ""


@dataclass
class Item:
    id: str
    label: str
    owner: str
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    animals: dict[str, Animal] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_animal(self, animal: Animal) -> Animal:
        self.animals[animal.id] = animal
        return animal

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def copy(self) -> "World":
        return World(
            setting=self.setting,
            animals=dataclasses.replace(self.animals) if False else __import__("copy").deepcopy(self.animals),
            items=__import__("copy").deepcopy(self.items),
            facts=dict(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
            trace=list(self.trace),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "woods": Setting(
        place="the whispering woods",
        shelter="a hollow log",
        features=["tall pines", "soft moss", "a winding creek"],
    ),
    "meadow": Setting(
        place="the open meadow",
        shelter="a stone burrow",
        features=["long grass", "wildflowers", "a little hill"],
    ),
    "riverbank": Setting(
        place="the riverbank",
        shelter="a dry root tunnel",
        features=["shiny stones", "reed beds", "muddy banks"],
    ),
}

PHENOMENA = {
    "storm": Phenomenon(
        id="storm",
        name="a storm",
        clue="the leaves kept twitching before any wind arrived",
        effect="the sky turned dark and rain began to fall hard",
        danger="the rain would soak soft fur and make the path slippery",
        sound="a low rumble rolled through the trees",
        smell="the air smelled sharp and wet",
        sky="gray clouds",
    ),
    "fog": Phenomenon(
        id="fog",
        name="fog",
        clue="the far trees looked blurry and pale",
        effect="a thick fog slid over the ground",
        danger="the path could vanish from view and make animals lose their way",
        sound="everything sounded soft and far away",
        smell="the air smelled cool and damp",
        sky="a white veil",
    ),
    "fireflies": Phenomenon(
        id="fireflies",
        name="fireflies",
        clue="tiny lights blinked in the grass before sunset",
        effect="the meadow filled with glowing fireflies",
        danger="the night would get dark fast and little animals could feel lost",
        sound="the crickets began their steady song",
        smell="the grass smelled sweet and warm",
        sky="a purple dusk",
    ),
}

ANIMALS = {
    "squirrel": ("squirrel", "scout", "small squirrel"),
    "rabbit": ("rabbit", "friend", "soft rabbit"),
    "fox": ("fox", "watcher", "red fox"),
    "badger": ("badger", "helper", "steady badger"),
}

ITEMS = {
    "leaf_cloak": ("leaf cloak", True),
    "berry_lantern": ("berry lantern", True),
    "dry_moss": ("dry moss bundle", False),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    phenomenon: str
    scout: str
    friend: str
    item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _pick(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def _animal_name(species: str) -> str:
    return {
        "squirrel": "Squeak",
        "rabbit": "Bun",
        "fox": "Pip",
        "badger": "Brum",
    }[species]


def _animal_sentence(animal: Animal) -> str:
    if animal.species == "squirrel":
        return f"{animal.label} liked to watch the treetops and listen for strange changes."
    if animal.species == "rabbit":
        return f"{animal.label} liked to nibble clover and hop where the grass was soft."
    if animal.species == "fox":
        return f"{animal.label} liked to notice every sound, even the quiet ones."
    return f"{animal.label} liked to keep the little forest paths in order."


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    phenomenon = PHENOMENA[params.phenomenon]
    world = World(setting=setting)

    scout_species, scout_role, scout_label = ANIMALS[params.scout]
    friend_species, friend_role, friend_label = ANIMALS[params.friend]
    item_label, protective = ITEMS[params.item]

    scout = world.add_animal(Animal(
        id="scout",
        species=scout_species,
        role=scout_role,
        label=f"{_animal_name(scout_species)} the {scout_label}",
        meters={"curiosity": 1.0, "courage": 0.0, "tiredness": 0.0},
        memes={"worry": 0.0, "hope": 1.0, "joy": 1.0},
    ))
    friend = world.add_animal(Animal(
        id="friend",
        species=friend_species,
        role=friend_role,
        label=f"{_animal_name(friend_species)} the {friend_label}",
        meters={"curiosity": 0.6, "courage": 0.0, "tiredness": 0.0},
        memes={"worry": 0.0, "hope": 1.0, "joy": 1.0},
    ))
    item = world.add_item(Item(
        id="item",
        label=item_label,
        owner=scout.id,
        protective=protective,
        meters={"dryness": 1.0},
    ))

    world.facts.update(
        setting=setting,
        phenomenon=phenomenon,
        scout=scout,
        friend=friend,
        item=item,
        foreshadowed=False,
        warned=False,
        sheltered=False,
        safe=False,
    )
    return world


def observe_clue(world: World) -> None:
    scout: Animal = world.facts["scout"]
    phen: Phenomenon = world.facts["phenomenon"]
    scout.meters["curiosity"] += 0.5
    scout.memes["worry"] += 0.4
    world.say(
        f"One afternoon at {world.setting.place}, {scout.label} paused by the trees. "
        f"{phen.clue.capitalize()}. That little sign foreshadowed something bigger."
    )
    world.say(
        f"{scout.label} also noticed that {phen.smell or 'the air felt different'}."
    )
    world.facts["foreshadowed"] = True


def warn_friend(world: World) -> None:
    scout: Animal = world.facts["scout"]
    friend: Animal = world.facts["friend"]
    phen: Phenomenon = world.facts["phenomenon"]
    item: Item = world.facts["item"]

    scout.meters["courage"] += 0.5
    world.say(
        f"{scout.label} trotted to {friend.label} and said, "
        f'"I think {phen.name} is coming. {phen.sound.capitalize()}."'
    )
    if item.protective:
        world.say(
            f"{scout.label} held up the {item.label} and said it could help them stay ready."
        )
    else:
        world.say(
            f"{scout.label} said they should hurry to the shelter before the weather changed."
        )
    friend.memes["worry"] += 0.3
    world.facts["warned"] = True


def turn_weather(world: World) -> None:
    phen: Phenomenon = world.facts["phenomenon"]
    scout: Animal = world.facts["scout"]
    friend: Animal = world.facts["friend"]
    item: Item = world.facts["item"]

    world.para()
    world.say(
        f"Soon, the foreshadowed moment arrived: {phen.effect}. {phen.danger.capitalize()}."
    )
    if item.protective:
        scout.meters["courage"] += 0.3
        friend.meters["courage"] += 0.3
        world.say(
            f"The {item.label} helped them move quickly, and neither little animal got too soaked."
        )
        world.facts["safe"] = True
    else:
        scout.memes["worry"] += 0.5
        friend.memes["worry"] += 0.5
        world.say(
            f"The two animals ran as fast as they could, but the wet ground still splashed their paws."
        )
        world.facts["safe"] = False


def reach_shelter(world: World) -> None:
    scout: Animal = world.facts["scout"]
    friend: Animal = world.facts["friend"]
    item: Item = world.facts["item"]

    world.say(
        f"They hurried to {world.setting.shelter}, where the branches made a snug roof."
    )
    if world.facts["safe"]:
        world.say(
            f"Inside, {scout.label} tucked {item.label} beside them, and {friend.label} smiled."
        )
    else:
        world.say(
            f"Inside, they shook out their fur and laughed at how close the storm had been."
        )
    scout.memes["joy"] += 0.7
    friend.memes["joy"] += 0.6
    world.facts["sheltered"] = True


def tell_story(world: World) -> World:
    scout: Animal = world.facts["scout"]
    friend: Animal = world.facts["friend"]

    world.say(
        f"{scout.label} was a {scout.species} who loved {world.setting.place}. "
        f"{_animal_sentence(scout)}"
    )
    world.say(
        f"{friend.label} was a {friend.species} friend who liked to stay near {world.setting.place} too. "
        f"{_animal_sentence(friend)}"
    )
    world.say(
        f"At {world.setting.place}, the animals knew the good places: {', '.join(world.setting.features)}."
    )
    world.para()
    observe_clue(world)
    warn_friend(world)
    turn_weather(world)
    reach_shelter(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    phen: Phenomenon = f["phenomenon"]
    scout: Animal = f["scout"]
    friend: Animal = f["friend"]
    return [
        f"Write a short animal story where {scout.label} notices a clue that foreshadows {phen.name}.",
        f"Tell a gentle story about two animals at {world.setting.place} who prepare for {phen.name} before it arrives.",
        f"Write a simple foreshadowing story for children with a forest animal, a friend, and a changing sky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scout: Animal = f["scout"]
    friend: Animal = f["friend"]
    phen: Phenomenon = f["phenomenon"]
    item: Item = f["item"]

    return [
        QAItem(
            question=f"Who noticed the clue that foreshadowed {phen.name}?",
            answer=f"{scout.label} noticed the clue first at {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the clue that foreshadowed {phen.name}?",
            answer=phen.clue.capitalize() + ".",
        ),
        QAItem(
            question=f"What did {scout.label} tell {friend.label} to help them get ready?",
            answer=f"{scout.label} warned {friend.label} that {phen.name} was coming and showed {item.label} if it could help.",
        ),
        QAItem(
            question=f"Where did the animals go when the weather changed?",
            answer=f"They hurried to {world.setting.shelter}.",
        ),
        QAItem(
            question=f"How did the ending prove the warning had mattered?",
            answer=f"The storm arrived, but the animals were already safe in shelter when it did.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "storm": [
        QAItem(
            question="What is a storm?",
            answer="A storm is bad weather with strong wind, rain, or thunder that can make being outside hard.",
        ),
    ],
    "fog": [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops near the ground that makes things look blurry.",
        ),
    ],
    "fireflies": [
        QAItem(
            question="What are fireflies?",
            answer="Fireflies are little insects that glow in the dark like tiny lanterns.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    phen: Phenomenon = world.facts["phenomenon"]
    out = list(WORLD_KNOWLEDGE.get(phen.id, []))
    out.append(QAItem(
        question="What does foreshadowing mean in a story?",
        answer="Foreshadowing is when a story gives a clue early on that hints at something important that will happen later.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting.place}")
    for a in world.animals.values():
        lines.append(f"animal {a.id}: {a.label} meters={a.meters} memes={a.memes}")
    for it in world.items.values():
        lines.append(f"item {it.id}: {it.label} protective={it.protective}")
    for k, v in world.facts.items():
        if k in {"scout", "friend", "phenomenon", "setting", "item"}:
            continue
        lines.append(f"fact {k}={v}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

phenomenon(storm).
phenomenon(fog).
phenomenon(fireflies).

setting(woods).
setting(meadow).
setting(riverbank).

scout(squirrel).
scout(fox).
scout(rabbit).
scout(badger).

friend(squirrel).
friend(fox).
friend(rabbit).
friend(badger).

item(leaf_cloak).
item(berry_lantern).
item(dry_moss).

clue(storm, twig_twitching).
clue(fog, blurry_trees).
clue(fireflies, blinking_lights).

shelter(woods, hollow_log).
shelter(meadow, stone_burrow).
shelter(riverbank, root_tunnel).

compatible(storm, leaf_cloak).
compatible(fog, berry_lantern).
compatible(fireflies, berry_lantern).

valid(P, X) :- setting(P), phenomenon(X), compatible(X, _).
valid_story(P, X, S) :- valid(P, X), scout(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in PHENOMENA:
        lines.append(asp.fact("phenomenon", key))
    for key in ANIMALS:
        lines.append(asp.fact("animal", key))
    for key in ITEMS:
        lines.append(asp.fact("item", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for phen in PHENOMENA:
            if place == "woods" and phen in {"storm", "fog", "fireflies"}:
                combos.append((place, phen))
            elif place == "meadow" and phen in {"storm", "fireflies"}:
                combos.append((place, phen))
            elif place == "riverbank" and phen in {"storm", "fog"}:
                combos.append((place, phen))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal foreshadowing story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--phenomenon", choices=PHENOMENA)
    ap.add_argument("--scout", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scout and args.friend and args.scout == args.friend:
        raise StoryError("The scout and friend must be different animals.")

    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.phenomenon:
        combos = [c for c in combos if c[1] == args.phenomenon]
    if not combos:
        raise StoryError("(No valid setting/phenomenon combination matches those options.)")

    setting, phenomenon = rng.choice(sorted(combos))
    scout = args.scout or rng.choice(list(ANIMALS))
    friend_choices = [a for a in ANIMALS if a != scout]
    friend = args.friend or rng.choice(friend_choices)
    item = args.item or _pick(rng, list(ITEMS))
    return StoryParams(setting=setting, phenomenon=phenomenon, scout=scout, friend=friend, item=item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(setting="woods", phenomenon="storm", scout="squirrel", friend="rabbit", item="leaf_cloak"),
    StoryParams(setting="meadow", phenomenon="fireflies", scout="fox", friend="rabbit", item="berry_lantern"),
    StoryParams(setting="riverbank", phenomenon="fog", scout="badger", friend="squirrel", item="dry_moss"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, phen in combos:
            print(f"  {place:10} {phen}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
