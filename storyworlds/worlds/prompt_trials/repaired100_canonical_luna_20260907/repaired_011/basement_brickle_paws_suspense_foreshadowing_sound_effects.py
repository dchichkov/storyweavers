#!/usr/bin/env python3
"""
A small pirate-style storyworld about a basement, a brickle, and mysterious paws.

The story follows a child and a pirate friend who hear clues below an old house.
Foreshadowing, suspense, and playful sound effects lead to a gentle discovery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    pirate: str
    pet: str
    treasure: str
    basement_item: str
    clue: str
    incident: int = 0
    premise: int = 0
    chant: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Luna", "Milo", "Pip", "Nora", "Tess", "Jory", "Bea", "Finn"]
PIRATES = ["Captain Brine", "Captain Pebble", "Captain Poppy", "Captain Rook"]
PETS = ["Scruff", "Mittens", "Button", "Socks", "Whisker"]
TREASURES = ["a brass compass", "a moon-blue marble", "a silver button", "a tiny golden bell"]
BASEMENT_ITEMS = ["an old trunk", "a wooden barrel", "a crooked shelf", "a lantern crate"]
CLUES = ["a red ribbon", "a seashell", "a blue feather", "a strip of sailcloth"]

INCIDENTS = [
    {
        "lead": "Near {item}, {name} noticed four dusty paw marks leading toward a little brickle tucked beneath a barrel.",
        "trigger": "Then the basement lantern blinked. From behind the barrel came a soft sound: tap... tap... tap.",
        "risk": "The paw marks stopped at a dark corner, while something there gave a tiny scrape.",
        "action": "{name} held up the lantern and said, 'Captain, we should look slowly. The clues are telling us where to go.'",
        "resolution": "The light revealed a loose plank. Behind it sat {pet}, who had nudged the brickle while searching for the missing treasure.",
        "cause": "the lantern blinked and tapping came from behind the barrel",
        "deed": "used the lantern and followed the paw marks carefully",
        "result": "{pet} was found safely behind a loose plank",
    },
    {
        "lead": "A red ribbon was tied around {item}, and beside it rested a brickle shaped like a tiny ship.",
        "trigger": "A gust slipped down the stairwell. The ribbon fluttered, and the brickle rolled across the floor. Clink!",
        "risk": "It rolled toward a dark drain beneath the old shelves.",
        "action": "{name} shouted, 'Avast! Block the drain!' {pirate} slid a cushion across the floor just in time.",
        "resolution": "The brickle bumped softly into the cushion, where a line of little paws pointed straight to a hidden basket.",
        "cause": "a gust sent the brickle rolling toward a dark drain",
        "deed": "warned the pirate and helped block the drain with a cushion",
        "result": "the brickle stopped safely and led them to a hidden basket",
    },
    {
        "lead": "On the floor beside {item}, {name} found paw marks circling a brickle three times.",
        "trigger": "From inside the trunk came a muffled sound: thump... sniff... thump.",
        "risk": "The trunk lid trembled, and dust puffed from its rusty hinge.",
        "action": "{name} whispered, 'Whoever is inside, we will open it gently.' {pirate} lifted the latch while {name} kept the lantern steady.",
        "resolution": "The trunk opened to reveal {pet}, curled beside the missing treasure and wagging a very dusty tail.",
        "cause": "a trembling trunk made thumping sounds beneath its lid",
        "deed": "kept the lantern steady while the pirate opened the latch gently",
        "result": "{pet} was discovered safe beside the treasure",
    },
    {
        "lead": "A blue feather rested on {item}, and a brickle sat beneath it like a warning sign.",
        "trigger": "Three quick scratches answered from the shadows: scritch-scritch-scritch!",
        "risk": "The sound moved closer, although no creature could be seen.",
        "action": "{name} called, 'Friend or foe, show your paws!' {pirate} placed the treasure on a high shelf and waited.",
        "resolution": "Two paws appeared first, then {pet} stepped out and followed the feather trail to the safe shelf.",
        "cause": "scratching sounds moved closer through the basement shadows",
        "deed": "called out calmly and moved the treasure to a safe shelf",
        "result": "{pet} followed the clue trail out of the shadows",
    },
    {
        "lead": "{name} spotted a strip of sailcloth beside {item}, with a brickle balanced on top.",
        "trigger": "The shelf creaked: kreeeak. A row of boxes leaned toward the paw marks below.",
        "risk": "One more wobble might send the boxes tumbling across the narrow path.",
        "action": "{name} said, 'No rushing, matey.' Together, {name} and {pirate} moved the light boxes away from the edge.",
        "resolution": "Behind them they found {pet}'s paw-print trail and the treasure tucked in a warm blanket.",
        "cause": "a creaking shelf made boxes lean over the paw-print trail",
        "deed": "helped move the light boxes away from the edge",
        "result": "the path cleared and the treasure was found in a blanket",
    },
]

PREMISES = [
    "{name} lived above a basement that smelled of dust, apples, and old sea stories. One rainy afternoon, {pirate} arrived with a captain's hat and a serious look.",
    "The rain drummed on the roof while {name} and {pirate} played pirates upstairs. Then a trail of tiny paws appeared beside the basement door.",
    "{name} had been warned never to enter the basement alone, but {pirate} promised to bring a lantern and a careful plan.",
    "A treasure map in {name}'s storybook ended with one strange word: basement. That was when {pirate} heard a faint tap below the stairs.",
    "The house was quiet except for the clock. Suddenly, something left dusty paws beside the basement steps, and {name} knew the adventure had begun.",
]

CHANTS = [
    "{pirate} whispered, 'Read the clue, mind the crew, and let brave kindness guide you.'",
    "'Tap by tap, we track the map!' chanted {name}. {pirate} answered, 'Paws by paws, we solve the cause!'",
    "{name} asked, 'What do careful pirates do?' {pirate} replied, 'They listen first, then choose what is safe.'",
    "Together they sang, 'No stomp, no dash, no wild crash; slow feet find the hidden stash!'",
    "{pirate} raised a finger. 'A good captain watches small signs.' {name} nodded. 'Even a brickle can point the way.'",
]

ENDINGS = [
    "At last, {pet} curled beside the recovered {treasure}. The brickle became a paperweight for their map, and the basement no longer seemed dark.",
    "Upstairs, {name} drew the paw trail on a new treasure map. At the bottom, {pirate} wrote, 'Solved by patience, lantern light, and a kind crew.'",
    "The rain stopped. In the quiet basement, the lantern glowed over clean paw prints and the safely wrapped {treasure}.",
    "{pet} received a blanket, and {name} received the captain's hat for excellent clue-keeping. The final sound was a happy purr.",
    "Before bedtime, {name} placed the brickle on a shelf. Whenever it clicked in the breeze, everyone remembered to listen before they leaped.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

name(N) :- name_option(N).
pirate(P) :- pirate_option(P).
pet(P) :- pet_option(P).
item(I) :- item_option(I).
clue(C) :- clue_option(C).

valid(N, P, T) :- name_option(N), pirate_option(P), treasure_option(T).
valid_story(N, P, T, I) :- valid(N, P, T), item_option(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in NAMES:
        lines.append(asp.fact("name_option", value))
    for value in PIRATES:
        lines.append(asp.fact("pirate_option", value))
    for value in PETS:
        lines.append(asp.fact("pet_option", value))
    for value in BASEMENT_ITEMS:
        lines.append(asp.fact("item_option", value))
    for value in TREASURES:
        lines.append(asp.fact("treasure_option", value))
    for value in CLUES:
        lines.append(asp.fact("clue_option", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(n, p, t) for n in NAMES for p in PIRATES for t in TREASURES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_values = set(asp_valid_combos())
    if py == clingo_values:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        for params in build_curated():
            sample = generate(params)
            if not sample.story or "basement" not in sample.story.lower():
                print("Generated-story verification failed.")
                return 1
        print("OK: generated stories passed.")
        return 0
    print("MISMATCH between Python and clingo.")
    print("Only in Python:", sorted(py - clingo_values))
    print("Only in clingo:", sorted(clingo_values - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate-style basement storyworld with brickles, paws, suspense, and clues."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--pirate", choices=PIRATES)
    parser.add_argument("--pet", choices=PETS)
    parser.add_argument("--treasure", choices=TREASURES)
    parser.add_argument("--basement-item", choices=BASEMENT_ITEMS)
    parser.add_argument("--clue", choices=CLUES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        pirate=args.pirate or rng.choice(PIRATES),
        pet=args.pet or rng.choice(PETS),
        treasure=args.treasure or rng.choice(TREASURES),
        basement_item=args.basement_item or rng.choice(BASEMENT_ITEMS),
        clue=args.clue or rng.choice(CLUES),
        incident=rng.randrange(len(INCIDENTS)),
        premise=rng.randrange(len(PREMISES)),
        chant=rng.randrange(len(CHANTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.premise = (seed // len(INCIDENTS)) % len(PREMISES)
    params.chant = (seed // 3) % len(CHANTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "name": params.name,
        "pirate": params.pirate,
        "pet": params.pet,
        "treasure": params.treasure,
        "item": params.basement_item,
        "clue": params.clue,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    world = World()
    child = world.add(Entity(params.name, "character", params.name, memes={"curiosity": 1.0}))
    pirate = world.add(Entity(params.pirate, "character", params.pirate, memes={"care": 1.0}))
    pet = world.add(Entity(params.pet, "character", params.pet, memes={"hidden": 1.0}))
    treasure = world.add(Entity("treasure", "thing", params.treasure, meters={"weight": 0.4}))
    brickle = world.add(Entity("brickle", "thing", "brickle", meters={"roll": 0.0}, memes={"clue": 1.0}))
    basement = world.add(Entity("basement", "place", "basement", meters={"darkness": 0.8}, memes={"mystery": 1.0}))

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(
        f"{pirate.label} carried a lantern, while {child.label} carried a folded map and watched the basement steps for clues."
    )
    world.say(incident["lead"].format(**values))

    world.para()
    basement.meters["darkness"] = 1.0
    brickle.meters["roll"] = 1.0
    basement.memes["tension"] = 1.0
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(CHANTS[params.chant % len(CHANTS)].format(**values))
    world.say(incident["action"].format(**values))

    world.para()
    basement.meters["darkness"] = 0.2
    basement.memes["tension"] = 0.0
    pet.memes["hidden"] = 0.0
    pet.memes["safe"] = 1.0
    child.memes["relief"] = 1.0
    treasure.memes["recovered"] = 1.0
    world.say(incident["resolution"].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.name,
        pirate=params.pirate,
        pet=params.pet,
        treasure=params.treasure,
        basement_item=params.basement_item,
        clue=params.clue,
        brickle="brickle",
        incident=params.incident % len(INCIDENTS),
        suspense_cause=incident["cause"],
        helpful_action=incident["deed"],
        result=incident["result"],
        foreshadowing="paw marks, the brickle, and the repeated sound pointed toward the hidden place",
        resolved=True,
    )

    prompts = [
        "Write a child-friendly pirate tale set in a basement with a brickle, mysterious paws, suspense, foreshadowing, and playful sound effects.",
        f"Tell a pirate adventure in which {params.name} and {params.pirate} follow paws and a brickle through a basement.",
        f"Write a suspenseful but gentle story where sound clues lead {params.name} to {params.pet} and a hidden treasure.",
    ]

    story_qa = [
        QAItem(
            question="Where did the adventure happen?",
            answer=f"The adventure happened in the basement, where {params.name} and {params.pirate} followed clues.",
        ),
        QAItem(
            question="What clues foreshadowed the discovery?",
            answer=f"The paw marks, the brickle, and the repeated sound foreshadowed that something was hidden nearby.",
        ),
        QAItem(
            question="What made the scene suspenseful?",
            answer=f"It was suspenseful because {incident['cause']}. The characters did not yet know what was making the sound.",
        ),
        QAItem(
            question=f"How did {params.name} help?",
            answer=f"{params.name} {incident['deed']}. That careful choice helped the crew solve the mystery safely.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"In the end, {incident['result']}. The basement became a place of relief instead of fear.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue placed earlier in a story that hints at something important later.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are written sounds, such as 'tap' or 'scritch,' that help readers imagine an action.",
        ),
        QAItem(
            question="Why should explorers use a lantern in a dark basement?",
            answer="A lantern helps explorers see obstacles, clues, and safe paths in a dark basement.",
        ),
        QAItem(
            question="What makes suspense?",
            answer="Suspense grows when characters face uncertainty and readers wonder what will happen next.",
        ),
        QAItem(
            question="Why is it helpful to move carefully near old boxes?",
            answer="Moving carefully keeps old boxes from falling and gives explorers time to notice important clues.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Captain Brine", "Scruff", "a brass compass", "an old trunk", "a red ribbon", 0, 0, 0, 0),
        StoryParams("Milo", "Captain Pebble", "Mittens", "a moon-blue marble", "a wooden barrel", "a seashell", 1, 1, 1, 1),
        StoryParams("Tess", "Captain Poppy", "Button", "a silver button", "a crooked shelf", "a blue feather", 2, 2, 2, 2),
        StoryParams("Finn", "Captain Rook", "Socks", "a tiny golden bell", "a lantern crate", "a strip of sailcloth", 3, 3, 3, 3),
    ]


CURATED = build_curated()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible name, pirate, treasure combinations:\n")
        for name, pirate, treasure in combinations[:20]:
            print(f"  {name:8} | {pirate:18} | {treasure}")
        if len(combinations) > 20:
            print(f"  ... and {len(combinations) - 20} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: the basement brickle mystery"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
