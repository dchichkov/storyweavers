#!/usr/bin/env python3
"""
A standalone animal story about a brave, pacifist choice during a conflict.

A small meadow world models animals with physical meters and emotional memes.
Luna's nod of sympathy helps two frightened neighbors stop a quarrel without
fighting. Bravery means staying close, listening, and choosing peace.
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

_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_base, "results.py")):
    _base = os.path.dirname(_base)
sys.path.insert(0, _base)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Animal:
    id: str
    species: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class Meadow:
    place: str = "Willow Meadow"
    animals: dict[str, Animal] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, animal: Animal) -> Animal:
        self.animals[animal.id] = animal
        return animal

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
    luna_name: str = "Luna"
    rabbit_name: str = "Pip"
    badger_name: str = "Bramble"
    object_name: str = "the bright berry basket"
    scene_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    action_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


SCENES = [
    {
        "conflict": "Pip and Bramble were tugging at the same bright berry basket",
        "fear": "each animal thought the other would take all the berries",
        "clue": "a torn vine showed that the basket had been caught between two roots",
        "turn": "Luna nodded with sympathy when each friend described being hungry",
        "action": "placed a flat stone between them and asked them to pull one paw at a time",
        "result": "the basket came free without a fight, and the berries were divided into two leafy bowls",
        "image": "two bowls of berries rested beneath the willow while Pip and Bramble shared a peaceful smile",
        "lesson": "bravery can mean stopping a quarrel long enough to understand both sides",
    },
    {
        "conflict": "Pip accused Bramble of blocking the path to the spring",
        "fear": "Bramble believed the rabbit was trying to chase him from his cool resting place",
        "clue": "fresh hoofprints showed that a fallen branch, not either animal, covered the path",
        "turn": "Luna gave a slow nod of sympathy to both animals before speaking",
        "action": "rolled the branch aside with a sturdy log while the two animals stood safely apart",
        "result": "the spring path opened, and neither friend had to surrender a resting place",
        "image": "clear water sparkled between two shady patches where the friends rested side by side",
        "lesson": "a pacifist choice looks for a shared answer instead of a winner",
    },
    {
        "conflict": "Pip and Bramble shouted over a striped feather found beside the pond",
        "fear": "each animal worried that giving it up would mean losing a treasured memory",
        "clue": "the feather had a matching pair floating near the reeds",
        "turn": "Luna nodded with sympathy because both friends were protecting something dear",
        "action": "carried the matching feathers to a quiet stump and suggested a fair trade",
        "result": "each friend kept one feather, and the matching pair became a sign of peace",
        "image": "the two striped feathers stood together in a wreath above the quiet pond",
        "lesson": "sympathy helps brave friends notice that another heart may be worried too",
    },
    {
        "conflict": "a storm knocked down the little bridge, and Pip blamed Bramble for standing on it",
        "fear": "Bramble feared the smaller animals would never trust him again",
        "clue": "the broken rails were cracked by wind and rain, not by a paw",
        "turn": "Luna nodded with sympathy and asked both animals to help repair what they could",
        "action": "gathered reeds while Pip fetched twine and Bramble carried smooth sticks",
        "result": "the bridge became safe again, and the animals crossed only after checking it together",
        "image": "a small reed bridge arched over the stream beneath a rainbow",
        "lesson": "bravery can repair trust after fear has made a conflict louder",
    },
    {
        "conflict": "Pip and Bramble faced each other beside a hollow tree and refused to move",
        "fear": "both believed the hollow was the only safe shelter before nightfall",
        "clue": "a second dry hollow opened just beyond the fern patch",
        "turn": "Luna nodded with sympathy instead of choosing one friend over the other",
        "action": "led them to the second shelter and marked both doors with white pebbles",
        "result": "each animal found a safe home, and the hollow tree no longer felt like a prize",
        "image": "two white-pebble doorways glowed softly as evening fireflies rose",
        "lesson": "peace grows when someone is brave enough to look for room for everyone",
    },
]

OPENINGS = [
    "In Willow Meadow, Luna the deer found a tense silence beside {object_name}.",
    "One warm morning, Luna saw a conflict begin near {object_name}.",
    "The meadow birds stopped singing when {conflict}.",
    "Luna was carrying clover home when she noticed {conflict}.",
    "At the edge of the willow shade, Luna discovered that {conflict}.",
]

DIALOGUES = [
    '"Let us pause before our paws make the problem bigger," Luna said.',
    '"I will listen to each of you," Luna promised.',
    '"Being brave does not mean being the loudest," Luna said.',
    '"Tell me what you feared," Luna invited gently.',
    '"A peaceful answer may take courage," Luna reminded them.',
]

ACTIONS = [
    "Luna took one careful step between the friends and",
    "Instead of fighting, Luna breathed slowly and",
    "The deer lowered her antlers, showing she would not attack, and",
    "Luna stood nearby with steady hooves while",
    "With courage but no anger, Luna",
]

ENDINGS = [
    "By sunset, {result}.",
    "Soon the meadow was calm again because {result}.",
    "After the careful work, {result}.",
    "The conflict ended gently: {result}.",
    "When the evening breeze arrived, {result}.",
]


def tell(params: StoryParams) -> Meadow:
    if not params.luna_name or not params.rabbit_name or not params.badger_name:
        raise StoryError("animal names must not be empty")
    if len({params.luna_name, params.rabbit_name, params.badger_name}) != 3:
        raise StoryError("the three animal names must be different")

    scene = SCENES[params.scene_id % len(SCENES)]
    world = Meadow()
    luna = world.add(Animal(
        "luna", "deer", params.luna_name,
        meters={"distance": 0.0, "steadiness": 1.0},
        memes={"bravery": 1.0, "sympathy": 1.0, "anger": 0.0},
        props={"choice": "pacifist"},
    ))
    rabbit = world.add(Animal(
        "rabbit", "rabbit", params.rabbit_name,
        meters={"hunger": 1.0, "tension": 1.0},
        memes={"fear": 1.0, "trust": 0.0},
    ))
    badger = world.add(Animal(
        "badger", "badger", params.badger_name,
        meters={"hunger": 1.0, "tension": 1.0},
        memes={"fear": 1.0, "trust": 0.0},
    ))

    world.facts.update(
        luna=luna,
        rabbit=rabbit,
        badger=badger,
        object=params.object_name,
        conflict=scene["conflict"],
        fear=scene["fear"],
        clue=scene["clue"],
        turn=scene["turn"],
        action=scene["action"],
        result=scene["result"],
        image=scene["image"],
        lesson=scene["lesson"],
        resolved=False,
        bravery="Luna chose a pacifist path",
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        object_name=params.object_name,
        conflict=scene["conflict"],
    ))
    world.say(
        f"{params.rabbit_name} and {params.badger_name} looked frightened and angry. "
        f"{scene['fear'].capitalize()}."
    )
    world.para()
    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)])
    world.say(
        f'"I found it first!" {params.rabbit_name} cried. '
        f'"But I need it too," {params.badger_name} replied.'
    )
    world.say(
        f"Luna did not charge or shout. {scene['turn']}. "
        f'"Both of you matter," she said.'
    )
    world.para()
    world.say(f"Then Luna noticed an important clue: {scene['clue']}.")
    world.say(
        f'{ACTIONS[params.action_id % len(ACTIONS)]} {scene["action"]}.'
    )
    world.say(
        f'"I thought you wanted to hurt me," {params.rabbit_name} admitted. '
        f'"I thought you would leave me with nothing," {params.badger_name} said.'
    )
    world.say(
        f'Luna gave a gentle nod. "Your worries were different, but both were real."'
    )
    world.para()

    rabbit.memes["fear"] = 0.0
    badger.memes["fear"] = 0.0
    rabbit.memes["trust"] = 1.0
    badger.memes["trust"] = 1.0
    rabbit.meters["tension"] = 0.0
    badger.meters["tension"] = 0.0
    luna.memes["bravery"] = 2.0
    world.facts["resolved"] = True

    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(result=scene["result"]))
    world.say(f"At the end, {scene['image'].capitalize()}.")
    world.say(f"Luna learned that {scene['lesson']}.")
    return world


def valid_combo(params: StoryParams) -> bool:
    return (
        bool(params.luna_name and params.rabbit_name and params.badger_name)
        and len({params.luna_name, params.rabbit_name, params.badger_name}) == 3
    )


ASP_RULES = r"""
pacifist_choice(luna) :- chose_pacifist(luna).
brave(luna) :- pacifist_choice(luna), showed_sympathy(luna).
conflict_resolved :- brave(luna), listened(luna), shared_solution.
#show pacifist_choice/1.
#show brave/1.
#show conflict_resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("chose_pacifist", "luna"),
        asp.fact("showed_sympathy", "luna"),
        asp.fact("listened", "luna"),
        asp.fact("shared_solution"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    needed = ("pacifist_choice", "brave", "conflict_resolved")
    if all(any(name in atom for atom in names) for name in needed):
        return 0
    print("MISMATCH: ASP twin did not resolve the pacifist conflict.")
    return 1


def generation_prompts(world: Meadow) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story where {f['luna'].label} uses bravery and sympathy during this conflict: {f['conflict']}.",
        f"Tell a child-friendly pacifist story with a nod, a spoken exchange, a clue, and this resolution: {f['result']}.",
        f"Write a complete meadow story in which animals replace fighting with listening and a shared solution.",
    ]


def story_qa(world: Meadow) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Why did {f['rabbit'].label} and {f['badger'].label} begin to argue?",
            f"They argued because {f['conflict']}. Each animal feared that {f['fear']}.",
        ),
        QAItem(
            "How did Luna show sympathy?",
            f"Luna listened to both animals and {f['turn']}. She treated both worries as important.",
        ),
        QAItem(
            "What clue changed the conflict?",
            f"The clue was that {f['clue']}. It showed that the animals did not need to blame each other.",
        ),
        QAItem(
            "Why was Luna's action brave?",
            f"Luna chose a pacifist answer instead of charging or fighting. She {f['action']}.",
        ),
        QAItem(
            "How did the story end?",
            f"{f['result']}. The ending image was that {f['image']}.",
        ),
    ]


def world_knowledge_qa(world: Meadow) -> list[QAItem]:
    return [
        QAItem(
            "What is bravery?",
            "Bravery is doing what is right or helpful even when something feels frightening.",
        ),
        QAItem(
            "What does pacifist mean?",
            "Pacifist means choosing peace and refusing to solve a conflict through violence.",
        ),
        QAItem(
            "What is sympathy?",
            "Sympathy is noticing another creature's pain or worry and caring about how it feels.",
        ),
        QAItem(
            "Why can listening help during a conflict?",
            "Listening can reveal hidden worries and make it easier to find a solution that respects everyone.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="An animal story about pacifist bravery.")
    parser.add_argument("--luna", dest="luna_name")
    parser.add_argument("--rabbit", dest="rabbit_name")
    parser.add_argument("--badger", dest="badger_name")
    parser.add_argument("--object", dest="object_name")
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
    luna = getattr(args, "luna_name", None) or rng.choice(["Luna", "Mira", "Fern", "Dawn"])
    rabbit = getattr(args, "rabbit_name", None) or rng.choice(["Pip", "Clover", "Nibbles", "Toby"])
    badger = getattr(args, "badger_name", None) or rng.choice(["Bramble", "Otis", "Moss", "Grumble"])
    if len({luna, rabbit, badger}) != 3:
        raise StoryError("animal names must be different")
    return StoryParams(
        luna_name=luna,
        rabbit_name=rabbit,
        badger_name=badger,
        object_name=getattr(args, "object_name", None) or rng.choice([
            "the bright berry basket",
            "the smooth river stone",
            "the striped feather",
            "the willow bridge",
        ]),
        scene_id=rng.randrange(len(SCENES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        action_id=rng.randrange(len(ACTIONS)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=getattr(args, "seed", None),
    )


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
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: Meadow) -> str:
    lines = ["--- world model state ---"]
    for animal in world.animals.values():
        lines.append(
            f"  {animal.label}: species={animal.species} "
            f"meters={animal.meters} memes={animal.memes} props={animal.props}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show conflict_resolved/0."))
        return
    if args.verify:
        sample = generate(StoryParams())
        if not valid_combo(sample.params) or not sample.world.facts["resolved"]:
            print("MISMATCH: Python world did not resolve the conflict.")
            sys.exit(1)
        try:
            code = asp_verify()
        except ImportError:
            print("OK: Python world verified; clingo unavailable for ASP check.")
            return
        if code:
            sys.exit(code)
        print("OK: Python and ASP twins agree.")
        return
    if args.asp:
        try:
            import asp
            print("\n".join(str(atom) for atom in asp.one_model(asp_program())))
        except ImportError:
            print("ASP mode requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        fixed = [
            StoryParams("Luna", "Pip", "Bramble", "the bright berry basket", 0, 0, 0, 0, 0),
            StoryParams("Mira", "Clover", "Otis", "the striped feather", 2, 1, 2, 3, 1),
            StoryParams("Fern", "Toby", "Moss", "the willow bridge", 3, 3, 4, 1, 4),
        ]
        samples = [generate(p) for p in fixed]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + i)
            try:
                sample = generate(resolve_params(args, rng))
            except StoryError:
                continue
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.luna_name} and the meadow conflict"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
