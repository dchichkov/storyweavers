#!/usr/bin/env python3
"""
A small stand-alone storyworld about a runt pirate, a magical starch treasure,
and a savory rescue at sea.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    runt: str
    captain: str
    cook: str
    ship: str
    starch: str
    savory: str
    trial: int = 0
    beginning: int = 0
    spell: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


RUNT_NAMES = ["Pip", "Nell", "Toby", "Moss", "Kit", "Bram"]
CAPTAINS = ["Captain Coral", "Captain Flint", "Captain Juniper", "Captain Blue"]
COOKS = ["Cook Saffron", "Cook Pepper", "Cook Marigold", "Cook Basil"]
SHIPS = ["the Jolly Minnow", "the Starry Spoon", "the Saucy Gull", "the Little Lantern"]
STARCHES = ["potatoes", "rice", "cornmeal", "noodles"]
SAVORIES = ["peppery stew", "garlic biscuits", "cheesy chowder", "herb dumplings"]


TRIALS = [
    {
        "lead": "Cook {cook} stirred a pot of {savory} thickened with {starch}, while {captain} polished the ship's brass compass.",
        "trigger": "A blue spark leaped from the compass into the pot. The stew rose like a foamy wave and began sliding toward the deck.",
        "risk": "If the enchanted supper spilled, the hungry crew might lose both their dinner and their way home.",
        "action": "{runt} grabbed a wooden spoon and called, 'Turn the pot toward the moon!' {cook} followed the advice and stirred three times.",
        "resolution": "The foamy wave folded back into the pot. The magic had made the meal warm, savory, and safely still.",
        "cause": "a compass spark enchanted the savory meal and sent it sliding across the deck",
        "deed": "used a wooden spoon and gave the cook the right moon-turning direction",
        "result": "the meal settled back into the pot and became a safe supper",
    },
    {
        "lead": "The crew was baking {starch} cakes beside a basket of {savory} herbs when a silver star winked above the galley.",
        "trigger": "The star sprinkled magic over the cakes, making them hop one by one toward the open porthole.",
        "risk": "The smallest cake, no bigger than a coin, bounced closest to the sea.",
        "action": "{runt} climbed onto an empty barrel and sang, 'Round and round, come back to ground!' The cakes paused to listen.",
        "resolution": "{cook} caught the cakes in a sailcloth while {runt} guided the last one away from the porthole.",
        "cause": "a silver star made the starch cakes hop toward the sea",
        "deed": "sang a returning rhyme from a barrel so the cakes would pause",
        "result": "the cook caught the cakes and saved the smallest one",
    },
    {
        "lead": "{captain} asked {cook} to prepare {savory} beside a sack of {starch} for the evening feast.",
        "trigger": "The sack whispered a spell and rolled beneath a table. Each roll left a trail of glittering flour.",
        "risk": "The trail led straight toward a hatch that opened above deep, dark water.",
        "action": "{runt} listened to the sack and heard it say, 'I am lost!' Then {runt} placed a tiny lantern beside the trail.",
        "resolution": "The glowing path led the sack back to the galley. The crew tied it gently to a post before finishing supper.",
        "cause": "a magical sack rolled toward a hatch and left a glittering flour trail",
        "deed": "listened for the sack's voice and marked its path with a tiny lantern",
        "result": "the sack followed the light back and was safely tied to a post",
    },
    {
        "lead": "At sunset, {cook} served {savory} over {starch} while the crew watched pink clouds sail past the mast.",
        "trigger": "A cloud dipped low and breathed a spell over the serving spoon. The spoon grew wings and fluttered away with dinner.",
        "risk": "It swooped toward the crow's nest, carrying the only warm bowl on the ship.",
        "action": "{runt} waved a napkin like a flag and told {captain}, 'Open the empty basket!' {captain} held it beneath the spoon.",
        "resolution": "The winged spoon dropped the bowl into the basket. Its wings vanished, and everyone ate before the stars came out.",
        "cause": "a cloud spell gave wings to the serving spoon",
        "deed": "signaled the captain to place an empty basket beneath the flying spoon",
        "result": "the bowl landed in the basket and the spoon became ordinary again",
    },
    {
        "lead": "The crew mixed {starch} with {savory} spices for a midnight snack, whispering so they would not wake the sea.",
        "trigger": "The recipe book flipped open by itself and shouted a magic word. Every spice began marching toward the rail.",
        "risk": "Without the spices, the snack would be bland, and the pepper jar was already wobbling near the edge.",
        "action": "{runt} covered the recipe book with a clean cloth and asked, 'Which word woke you?' The book quieted when {runt} found the missing comma.",
        "resolution": "The spices marched back into their bowls. The crew added them carefully, and the snack tasted wonderfully savory.",
        "cause": "a recipe book spell sent the spices marching toward the rail",
        "deed": "covered the book and found the missing comma that stopped its spell",
        "result": "the spices returned and made the snack delicious",
    },
    {
        "lead": "Before dawn, {captain} hid a warm bowl of {savory} beside a basket of {starch} for the sleepy crew.",
        "trigger": "The bowl began glowing green, and a tiny magical whirlpool spun across the galley floor.",
        "risk": "The whirlpool tugged at spoons, cups, and the ship's important key ring.",
        "action": "{runt} set a ring of dry starch around the whirlpool. The grains drank up the shining water until the spinning slowed.",
        "resolution": "The key ring stopped just short of the drain. {cook} swept up the dry starch, and the bowl kept glowing harmlessly.",
        "cause": "a glowing savory bowl created a magical whirlpool near the key ring",
        "deed": "made a dry starch ring that absorbed the whirlpool's shining water",
        "result": "the whirlpool faded before it could carry away the key ring",
    },
]


BEGINNINGS = [
    "{runt} was the runt of the crew on {ship}, but being small made it easy to squeeze between barrels and listen for trouble.",
    "On {ship}, every sailor had a job. {runt} was the runt, so the others gave {runt} the smallest bucket and the biggest chance to surprise them.",
    "The sea was calm when {runt}, the ship's runt sailor, helped {captain} steer {ship} toward an island shaped like a teacup.",
    "Although {runt} was the runt aboard {ship}, {captain} trusted {runt}'s sharp eyes more than any tall lookout's.",
    "A savory smell drifted across {ship}. {runt} followed it to the galley, where a little magic was waiting beside the starch.",
]


SPELLS = [
    "{cook} whispered, 'Salt, spice, and moonlit tide; let a careful heart be our guide.'",
    "{captain} tapped the mast and cried, 'By star and spoon, let no good food be lost!'",
    "{runt} said, 'Small hands, brave plan, safe supper for every sailor!'",
    "The crew chanted, 'Stir it slow, let the safe magic grow!'",
    "{cook} hummed a galley charm that smelled of pepper, butter, and warm bread.",
]


ENDINGS = [
    "That night, the crew ate the savory feast under a sky full of stars. {captain} gave {runt} the first spoonful and called {runt} the ship's bravest little pirate.",
    "At breakfast, the saved {starch} shone in a golden bowl. {runt} smiled as the crew hung a tiny flag beside the galley door: SMALL BUT MIGHTY.",
    "The sea carried {ship} toward home, and the magic compass pointed true. In the galley, {runt} kept the wooden spoon as a medal.",
    "From then on, nobody called {runt} too small. Whenever trouble stirred, the crew asked {runt} to notice the first clue.",
    "The moon rose over the mast while {cook} served seconds. The last bite was savory, the starch was warm, and the magic rested quietly in its pot.",
]


ASP_RULES = r"""
#show valid/2.
#show valid_story/4.

runt(N) :- runt_name(N).
captain(N) :- captain_name(N).
cook(N) :- cook_name(N).
ship(N) :- ship_name(N).
starch(N) :- starch_name(N).
savory(N) :- savory_name(N).

valid(Starch, Savory) :- starch_name(Starch), savory_name(Savory), pairing(Starch, Savory).
valid_story(Runt, Starch, Savory, Ship) :-
    runt_name(Runt),
    ship_name(Ship),
    valid(Starch, Savory).
"""


PAIRINGS = [
    ("potatoes", "peppery stew"),
    ("rice", "cheesy chowder"),
    ("cornmeal", "garlic biscuits"),
    ("noodles", "herb dumplings"),
]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in RUNT_NAMES:
        lines.append(asp.fact("runt_name", value))
    for value in CAPTAINS:
        lines.append(asp.fact("captain_name", value))
    for value in COOKS:
        lines.append(asp.fact("cook_name", value))
    for value in SHIPS:
        lines.append(asp.fact("ship_name", value))
    for value in STARCHES:
        lines.append(asp.fact("starch_name", value))
    for value in SAVORIES:
        lines.append(asp.fact("savory_name", value))
    for starch, savory in PAIRINGS:
        lines.append(asp.fact("pairing", starch, savory))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return list(PAIRINGS)


def asp_valid_combos() -> set[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return {(starch, savory) for starch, savory in asp.atoms(model, "valid")}


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = asp_valid_combos()
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} pairs).")
        return 0
    print("MISMATCH between Python and ASP pairings.")
    print("Only in Python:", sorted(python_pairs - asp_pairs))
    print("Only in ASP:", sorted(asp_pairs - python_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A magical pirate tale about a runt and a savory starch feast.")
    parser.add_argument("--runt", choices=RUNT_NAMES)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--cook", choices=COOKS)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--starch", choices=STARCHES)
    parser.add_argument("--savory", choices=SAVORIES)
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
    pairs = valid_combos()
    if args.starch and args.savory and (args.starch, args.savory) not in pairs:
        raise StoryError("No story: that starch and savory pairing does not make a believable pirate supper.")
    if args.starch:
        pairs = [pair for pair in pairs if pair[0] == args.starch]
    if args.savory:
        pairs = [pair for pair in pairs if pair[1] == args.savory]
    if not pairs:
        raise StoryError("No valid starch and savory pairing matches the given options.")
    starch, savory = rng.choice(pairs)
    return StoryParams(
        runt=args.runt or rng.choice(RUNT_NAMES),
        captain=args.captain or rng.choice(CAPTAINS),
        cook=args.cook or rng.choice(COOKS),
        ship=args.ship or rng.choice(SHIPS),
        starch=starch,
        savory=savory,
        trial=rng.randrange(len(TRIALS)),
        beginning=rng.randrange(len(BEGINNINGS)),
        spell=rng.randrange(len(SPELLS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.trial = seed % len(TRIALS)
    params.beginning = (seed // len(TRIALS)) % len(BEGINNINGS)
    params.spell = (seed // 3) % len(SPELLS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "runt": params.runt,
        "captain": params.captain,
        "cook": params.cook,
        "ship": params.ship,
        "starch": params.starch,
        "savory": params.savory,
    }
    trial = TRIALS[params.trial % len(TRIALS)]

    world = World()
    runt = world.add(Entity(params.runt, "character", params.runt, memes={"courage": 0.0, "respect": 0.0}))
    captain = world.add(Entity(params.captain, "character", params.captain, memes={"trust": 0.0}))
    cook = world.add(Entity(params.cook, "character", params.cook, memes={"worry": 0.0}))
    ship = world.add(Entity("ship", "vehicle", params.ship, meters={"safety": 1.0}))
    meal = world.add(Entity("meal", "food", params.savory, meters={"warmth": 1.0}, memes={"magic": 0.0, "hunger": 0.0}))
    starch = world.add(Entity("starch", "ingredient", params.starch, meters={"dryness": 1.0}, memes={"usefulness": 0.0}))

    world.say(BEGINNINGS[params.beginning % len(BEGINNINGS)].format(**values))
    world.say(f"{captain.label} kept watch while {cook.label} prepared {meal.label} with {starch.label}. The warm smell curled through the ropes and made the crew grin.")
    world.say(trial["lead"].format(**values))

    world.para()
    meal.memes["magic"] = 1.0
    meal.memes["hunger"] = 1.0
    cook.memes["worry"] = 1.0
    ship.meters["safety"] = 0.6
    world.say(trial["trigger"].format(**values))
    world.say(trial["risk"].format(**values))
    world.say(f"{runt.label} was small enough to see beneath the table and quick enough to spot the safest idea.")
    world.say(trial["action"].format(**values))

    world.para()
    starch.memes["usefulness"] = 1.0
    runt.memes["courage"] = 1.0
    runt.memes["respect"] = 1.0
    captain.memes["trust"] = 1.0
    cook.memes["worry"] = 0.0
    ship.meters["safety"] = 1.0
    world.say(trial["resolution"].format(**values))
    world.say(SPELLS[params.spell % len(SPELLS)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        runt=params.runt,
        captain=params.captain,
        cook=params.cook,
        ship=params.ship,
        starch=params.starch,
        savory=params.savory,
        trial=params.trial % len(TRIALS),
        magic=True,
        cause=trial["cause"],
        helpful_action=trial["deed"],
        result=trial["result"],
        resolved=True,
    )

    prompts = [
        "Write a child-friendly pirate tale about a runt sailor who uses magic to save a savory starch meal.",
        f"Tell a magical pirate story in which {params.runt}, the runt aboard {params.ship}, helps {params.cook} protect {params.savory}.",
        f"Write a complete pirate adventure featuring {params.runt}, {params.starch}, {params.savory}, a magical problem, dialogue, and a brave solution.",
    ]

    story_qa = [
        QAItem(
            question="Who is the runt in the story?",
            answer=f"{params.runt} is the runt sailor aboard {params.ship}, but careful noticing makes {params.runt} important to the whole crew.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began when {trial['cause']}.",
        ),
        QAItem(
            question=f"How did {params.runt} help?",
            answer=f"{params.runt} {trial['deed']}. This gave the crew a safe way to handle the magic.",
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"In the end, {trial['result']}. The crew could enjoy their warm, savory supper.",
        ),
        QAItem(
            question="What changed for the runt?",
            answer=f"{params.runt} earned the crew's respect because a small sailor used courage, listening, and a clever plan to protect everyone.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does runt mean?",
            answer="A runt is the smallest or weakest member of a group, although a runt can still be clever and brave.",
        ),
        QAItem(
            question="What is starch?",
            answer="Starch is a food substance found in foods such as potatoes, rice, corn, and noodles.",
        ),
        QAItem(
            question="What does savory mean?",
            answer="Savory describes a food with a rich, salty, spicy, or herby taste rather than a sweet taste.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an impossible or mysterious power that changes what can happen in the story.",
        ),
        QAItem(
            question="Why do pirate stories have ships?",
            answer="Pirate stories often have ships because pirates travel across the sea to explore, solve problems, and search for treasure.",
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
        lines.append(f"  {entity.id:12} ({entity.kind:10}) {' '.join(parts)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Pip", "Captain Coral", "Cook Saffron", "the Jolly Minnow", "potatoes", "peppery stew", 0, 0, 0, 0),
        StoryParams("Nell", "Captain Flint", "Cook Pepper", "the Starry Spoon", "rice", "cheesy chowder", 1, 1, 2, 1),
        StoryParams("Toby", "Captain Juniper", "Cook Marigold", "the Saucy Gull", "cornmeal", "garlic biscuits", 3, 2, 1, 3),
        StoryParams("Moss", "Captain Blue", "Cook Basil", "the Little Lantern", "noodles", "herb dumplings", 5, 4, 3, 4),
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
        pairs = sorted(asp_valid_combos())
        print(f"{len(pairs)} compatible starch and savory pairs:\n")
        for starch, savory in pairs:
            print(f"  {starch:10} -> {savory}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
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
            header = f"### {sample.params.runt}: a magical voyage on {sample.params.ship}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
