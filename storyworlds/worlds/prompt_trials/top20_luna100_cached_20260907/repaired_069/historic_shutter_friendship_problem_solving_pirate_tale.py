#!/usr/bin/env python3
"""A child-friendly pirate tale about a historic shutter, friendship, and clever repair."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Luna"
    friend: str = "Pip"
    parrot: str = "Coco"
    island: str = "Harbor Isle"
    trial: int = 0
    opening: int = 0
    dialogue: int = 0
    turn: int = 0
    ending: int = 0


CAPTAINS = ["Luna", "Mara", "Tess", "Nia", "Ruby"]
FRIENDS = ["Pip", "Finn", "Bram", "Jo", "Kit"]
PARROTS = ["Coco", "Pepper", "Skipper", "Blue"]
ISLANDS = ["Harbor Isle", "Bell Reef", "Coral Cay", "Maple Key"]

TRIALS = [
    {
        "title": "the lighthouse shutter",
        "place": "the old lighthouse",
        "problem": "A storm tore one hinge from the lighthouse's historic wooden shutter, and rain blew toward the lamp.",
        "clue": "Luna noticed a spare mast ring beside the tool chest and saw that its curve matched the broken hinge.",
        "action": "Luna held the ring in place while Pip threaded rope through its holes and Coco fetched a smooth peg.",
        "result": "The shutter swung closed against the rain, and the lamp stayed bright for every ship at sea.",
        "lesson": "Friends solve more when each person notices a different part of the problem.",
        "object": "historic shutter",
        "ending": "By sunrise, the repaired shutter rested proudly beside the golden lighthouse lamp.",
    },
    {
        "title": "the museum window",
        "place": "the island history house",
        "problem": "A loose historic shutter banged against the museum window and threatened an old map inside.",
        "clue": "Pip found that the shutter's lower corner was catching on a raised stone step.",
        "action": "Pip lifted the corner while Luna wedged a flat shell beneath it, and Coco called, 'Heave-ho!'",
        "result": "The shutter rested evenly, and the treasured map remained dry and safe.",
        "lesson": "Looking for the cause is wiser than pushing harder at the trouble.",
        "object": "old map",
        "ending": "The old map gleamed beneath the quiet, carefully repaired shutter.",
    },
    {
        "title": "the harbor signal",
        "place": "the historic harbor tower",
        "problem": "A storm jammed its shutter open, hiding the signal lantern from a small boat.",
        "clue": "Luna saw salt packed inside the hinge and remembered a flask of warm water in the galley.",
        "action": "Pip loosened the salt with the warm water while Luna guided the hinge and Coco kept watch from the rail.",
        "result": "The shutter moved again, and the boat followed the safe signal into the harbor.",
        "lesson": "A patient team can free a stuck problem without breaking what matters.",
        "object": "signal lantern",
        "ending": "The harbor lantern blinked through the repaired shutter like a friendly star.",
    },
    {
        "title": "the captain's cabin",
        "place": "the historic captain's cabin",
        "problem": "A broken shutter let moonlight spill across the floor, making the crew's treasure map hard to read.",
        "clue": "Pip saw that two matching oars could brace the shutter from the inside.",
        "action": "Luna measured the gap, Pip placed the oars, and Coco tugged the rope until the brace held.",
        "result": "The cabin grew calm and dark enough for everyone to follow the map.",
        "lesson": "A simple plan can work when friends test it together.",
        "object": "treasure map",
        "ending": "The treasure map lay flat beneath the steady historic shutter.",
    },
]

OPENINGS = [
    "At dawn, Captain {captain} sailed toward {island} with {friend} beside the wheel.",
    "The sea glittered around {island} while Captain {captain} and {friend} checked the ship's gear.",
    "Captain {captain} had promised to protect the old buildings of {island}, and {friend} eagerly joined the watch.",
    "A salty breeze carried Captain {captain}, {friend}, and their bright-feathered parrot toward {island}.",
]

DIALOGUES = [
    "'The shutter is important,' said {captain}. '{friend}, will you help me find out why it failed?'",
    "'We can fix it,' said {friend}. Captain {captain} smiled and answered, 'Then we will listen to the problem together.'",
    "‘Should we force it?’ asked {captain}. ‘No,’ said {friend}. ‘Let us find what is holding it back.’",
    "'A true crew shares its eyes and its hands,' said {captain}. {friend} nodded. 'I will search for a clue.'",
]

TURNS = [
    "Luna almost reached for a heavy hammer, but Pip shook their head. The friends chose the gentler plan instead.",
    "The first tug failed with a loud CLACK! Rather than blame one another, the friends checked the hinge again.",
    "For a moment the repair slipped. Luna listened to Pip's idea, and that changed the next move.",
    "Coco squawked at the wrong corner. The crew laughed, then followed the useful clue Coco had spotted.",
]

ENDINGS = [
    "The friends shared warm biscuits while the repaired shutter creaked softly in the sea breeze.",
    "Captain {captain} gave {friend} the first look through the safe window, and both friends cheered.",
    "That evening, the crew painted a tiny blue star beside the shutter to remember their teamwork.",
    "The historic building stood safe, and the friends sailed on with a new song about solving trouble together.",
]


ASP_RULES = r"""
#show friendship/2.
#show repaired/1.

friendship(A, B) :- crew(A), crew(B), A != B.
repaired(O) :- useful_clue(O), patient_team.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("crew", "captain"),
            asp.fact("crew", "friend"),
            asp.fact("useful_clue", "historic_shutter"),
            asp.fact("patient_team"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--parrot", choices=PARROTS)
    parser.add_argument("--island", choices=ISLANDS)
    parser.add_argument("--trial", type=int, choices=range(len(TRIALS)))
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
    return StoryParams(
        seed=args.seed,
        captain=args.captain or rng.choice(CAPTAINS),
        friend=args.friend or rng.choice(FRIENDS),
        parrot=args.parrot or rng.choice(PARROTS),
        island=args.island or rng.choice(ISLANDS),
        trial=args.trial if args.trial is not None else rng.randrange(len(TRIALS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.captain == params.friend:
        raise StoryError("Captain and friend must have different names.")
    if not 0 <= params.trial < len(TRIALS):
        raise StoryError("Trial number is outside the available pirate problems.")

    world = World()
    captain = world.add(
        Entity(
            id="captain",
            type="pirate",
            label=params.captain,
            meters={"reach": 1.0, "balance": 0.8},
            memes={"courage": 1.0, "trust": 0.8},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            type="sailor",
            label=params.friend,
            meters={"reach": 0.8, "care": 1.0},
            memes={"curiosity": 1.0, "friendship": 1.0},
        )
    )
    parrot = world.add(
        Entity(
            id="parrot",
            type="parrot",
            label=params.parrot,
            meters={"flight": 1.0},
            memes={"attention": 1.0},
        )
    )
    trial = TRIALS[params.trial]

    replacements = {
        "{captain}": captain.label,
        "{friend}": friend.label,
        "{parrot}": parrot.label,
        "{island}": params.island,
    }

    def fill(text: str) -> str:
        for key, value in replacements.items():
            text = text.replace(key, value)
        return text

    world.say(fill(OPENINGS[params.opening]))
    world.say(f"They were guarding {trial['place']} when {trial['problem']}")
    world.say(fill(DIALOGUES[params.dialogue]))
    world.say(f"{parrot.label} gave a sharp cry: 'Pieces, not panic!'")
    world.say(fill(TURNS[params.turn]))
    world.say(f"{trial['clue']}")
    world.say(f"{trial['action']}")
    world.say(f"{trial['result']}")

    captain.memes["confidence"] = 1.0
    friend.memes["trust"] = 1.0
    parrot.memes["helpfulness"] = 1.0

    world.say(f"Captain {captain.label} said, 'We did it because we listened to one another.'")
    world.say(f"{friend.label} replied, 'And every good friend gets a chance to help.'")
    world.say(f"Lesson learned: {trial['lesson']}")
    world.say(fill(ENDINGS[params.ending]))

    world.facts.update(
        captain=captain,
        friend=friend,
        parrot=parrot,
        island=params.island,
        trial=trial,
        friendship=True,
        problem_solving=True,
        historic=True,
        shutter=True,
        repaired=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    trial = world.facts["trial"]
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    return [
        f"Write a child-friendly pirate tale in which Captain {captain.label} and {friend.label} repair {trial['title']}.",
        f"Tell a friendship story about problem solving, a historic shutter, and a clever clue.",
        f"Write a pirate adventure with back-and-forth dialogue and an ending image involving the {trial['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trial = world.facts["trial"]
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    parrot = world.facts["parrot"]

    return [
        QAItem(
            question=f"What problem did Captain {captain.label} and {friend.label} face?",
            answer=f"They had to repair {trial['title']}: {trial['problem']}",
        ),
        QAItem(
            question=f"What clue helped {captain.label} and {friend.label}?",
            answer=trial["clue"],
        ),
        QAItem(
            question=f"How did {parrot.label} help the friends?",
            answer=f"{parrot.label} helped by watching carefully and adding a useful warning during the repair.",
        ),
        QAItem(
            question="How did friendship change the way the problem was solved?",
            answer=(
                f"The friends listened to each other, shared the work, and tested a gentle plan instead of "
                f"blaming one another. Together they solved the problem and protected {trial['object']}."
            ),
        ),
        QAItem(
            question="What lesson did the crew learn?",
            answer=f"The crew learned that {trial['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a cover fitted over a window or opening to protect it from light, rain, wind, or damage.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important in history or connected with the past.",
        ),
        QAItem(
            question="Why is problem solving easier with friends?",
            answer="Friends can share clues, skills, and ideas, so they may notice causes and solutions that one person could miss.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> tuple[set[tuple], set[tuple]]:
    import asp

    model = asp.one_model(asp_program("#show friendship/2.\n#show repaired/1."))
    friendships = set(asp.atoms(model, "friendship"))
    repairs = set(asp.atoms(model, "repaired"))
    return friendships, repairs


def asp_verify() -> int:
    friendships, repairs = asp_valid()
    expected_friendships = {("captain", "friend"), ("friend", "captain")}
    expected_repairs = {("historic_shutter",)}
    if friendships == expected_friendships and repairs == expected_repairs:
        print("OK: ASP parity matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python story gate.")
    print("  ASP friendship:", sorted(friendships))
    print("  expected friendship:", sorted(expected_friendships))
    print("  ASP repairs:", sorted(repairs))
    print("  expected repairs:", sorted(expected_repairs))
    return 1


CURATED = [
    StoryParams(captain="Luna", friend="Pip", parrot="Coco", island="Harbor Isle", trial=0),
    StoryParams(
        captain="Mara",
        friend="Finn",
        parrot="Pepper",
        island="Bell Reef",
        trial=1,
        opening=1,
        dialogue=2,
        turn=1,
        ending=2,
    ),
    StoryParams(
        captain="Tess",
        friend="Bram",
        parrot="Blue",
        island="Coral Cay",
        trial=2,
        opening=3,
        dialogue=3,
        turn=2,
        ending=3,
    ),
    StoryParams(
        captain="Nia",
        friend="Jo",
        parrot="Skipper",
        island="Maple Key",
        trial=3,
        opening=2,
        dialogue=1,
        turn=3,
        ending=1,
    ),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show friendship/2.\n#show repaired/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        friendships, repairs = asp_valid()
        print(f"{len(friendships)} friendship facts")
        for fact in sorted(friendships):
            print("friendship:", fact)
        print(f"{len(repairs)} repaired-object facts")
        for fact in sorted(repairs):
            print("repaired:", fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.captain}: pirate friendship tale"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
