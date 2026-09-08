#!/usr/bin/env python3
"""
A child-friendly whodunit aboard a small sailboat, where friendship and bravery
help a crew discover why a supposedly savage sea creature borrowed their flag.
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
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    friend: str = "Tavi"
    captain: str = "Captain Mara"
    creature: str = "savage-looking sea lion"
    place: str = "the bright harbor"
    boat: str = "the Starling"
    sail: str = "striped blue sail"
    object_name: str = "the friendship flag"
    task: str = "carry a friendship flag to the lighthouse"


@dataclass(frozen=True)
class Mystery:
    title: str
    trouble: str
    suspicion: str
    clue: str
    false_step: str
    cause: str
    brave_job: str
    friend_job: str
    repair: str
    lesson: str
    ending: str


MYSTERIES = [
    Mystery(
        "The Vanished Flag",
        "the friendship flag disappeared from the mast before the boat could sail",
        "the savage-looking sea lion had taken it",
        "wet blue threads trailed from the mast toward a stack of empty fish crates",
        "the children searched the creature's beach and called for it to show itself",
        "the sea lion had dragged the flag away from a sharp hook that was tearing its cloth",
        "approached the creature calmly and held out a fish-shaped toy instead of a stone",
        "followed the thread trail and freed the flag from the crate nails",
        "the captain stitched a bright patch over the torn place",
        "asked questions before judging a frightening face",
        "the repaired flag flew beside the striped blue sail while the sea lion watched from the waves",
    ),
    Mystery(
        "The Silent Sail",
        "the striped blue sail would not rise when the harbor bell rang",
        "someone believed the savage creature had climbed aboard and tangled the ropes",
        "three pale scales rested beside the knot, but no muddy prints crossed the deck",
        "the friends pulled every rope at once and made the knot tighter",
        "a frightened sea turtle had brushed the rope while hiding beneath the boat",
        "leaned over the rail with a safety rope tied around the waist",
        "untied the knot one loop at a time and comforted the hidden turtle",
        "the captain marked the rope with red and green ribbons",
        "bravery works best with care, not with wild rushing",
        "the sail opened like a blue wing after the turtle slipped safely into the bay",
    ),
    Mystery(
        "The Missing Compass",
        "the brass compass vanished from the captain's table",
        "the savage sea lion was blamed because wet whisker marks circled the cabin door",
        "the compass needle had left a faint line of salt toward the storage locker",
        "the friends accused the creature and locked the cabin",
        "a wave had rolled the compass beneath a loose storage box",
        "stood watch at the open door so no one would trip near the water",
        "lifted the box and returned the compass to its velvet case",
        "the captain added a wooden rim around the table",
        "a clue can be stronger than a scary guess",
        "the compass pointed north as the friendship flag snapped over the calm deck",
    ),
    Mystery(
        "The Scratched Sea Chest",
        "the sea chest had fresh scratches and the harbor map inside was missing",
        "the children thought the savage creature had stolen the map",
        "small grains of red sand led from the chest to the old pier",
        "they followed the marks without telling the captain and nearly stepped through a rotten plank",
        "the wind had blown the map under the pier, where a crab pulled at its corner",
        "warned everyone away from the weak plank and tied a safe line",
        "reached for the map with a boat hook while Tavi watched the tide",
        "the captain replaced the broken chest latch",
        "bravery includes protecting friends while solving a mystery",
        "the map dried beside the red-sailed dinghy, safe and readable again",
    ),
    Mystery(
        "The Three Harbor Knocks",
        "three knocks sounded beneath the boat just before sunset",
        "the crew feared the savage creature was trying to tip the hull",
        "the knocks matched the rhythm of a loose anchor chain",
        "the friends beat back at the hull and frightened every bird from the pier",
        "the anchor chain tapped the boat whenever the tide lifted its buoy",
        "held the lantern low and listened from the safest part of the deck",
        "secured the chain while explaining the pattern to the captain",
        "the captain tied a cork around the noisy link",
        "listening carefully can turn fear into a useful answer",
        "the quiet boat rocked under a sky full of stars and friendly lanterns",
    ),
    Mystery(
        "The Silver Scale",
        "a silver scale appeared inside the captain's locked hat",
        "the crew guessed that the savage sea creature had slipped aboard",
        "the hat's wet brim matched a puddle beneath the open skylight",
        "they searched every bunk before checking where rainwater had fallen",
        "a gust had blown the scale through the skylight while the sea lion surfaced nearby",
        "climbed the short ladder with a rope around the waist to close the skylight",
        "checked the lock and found no sign that anyone had entered",
        "the captain placed a cover over the skylight",
        "courage is not pretending danger is absent; it is using a safe plan",
        "the silver scale shone in a dish while the covered skylight kept the cabin dry",
    ),
    Mystery(
        "The Crooked Signal",
        "the lighthouse signal flashed the wrong pattern during the evening watch",
        "the crew suspected a savage prank from the rocks",
        "a gull's feather was caught in the signal wheel",
        "the friends waved their own lantern wildly and confused the harbor boats",
        "the feather had jammed the wheel when a gull flew through the open window",
        "climbed the lighthouse steps with a safety cord and steady hands",
        "read the signal chart and told the boats to wait",
        "the keeper cleaned the wheel and closed the window",
        "bravery and friendship help people stay calm when others depend on them",
        "the lighthouse blinked the true pattern as every boat reached the harbor safely",
    ),
    Mystery(
        "The Stolen Snack",
        "the basket of cinnamon rolls vanished from the deck",
        "the children blamed the savage sea lion and planned to chase it away",
        "crumbs led upward, not toward the water, and a loose hatch cover rocked in the breeze",
        "they shouted at the waves while the hungry crew searched the wrong place",
        "the basket had slid beneath the hatch cover when the boat tilted",
        "opened the hatch only after securing the cover and checking the dark space",
        "used a broom to draw the basket close without reaching blindly",
        "the captain tied the basket to a deck ring",
        "friends can be brave without being reckless or unkind",
        "the crew shared warm cinnamon rolls beneath the striped blue sail",
    ),
]

OPENINGS = [
    "At dawn in the bright harbor",
    "On a morning when gulls circled the pier",
    "Before the first harbor bell",
    "Beside a row of bobbing boats",
    "Under a sky washed clean by rain",
    "At the edge of the quiet bay",
]

QUESTIONS = [
    "What did we actually see, and what did we only imagine?",
    "Let us follow the clue before we blame anyone.",
    "I am scared too, but I will stay beside you.",
    "What changed when we checked the evidence?",
    "We can be brave and gentle at the same time.",
    "Tell me what you noticed. I will listen.",
]

TEAMWORK_LINES = [
    "They placed each clue on the deck in a careful row.",
    "They divided the work: one watched, one listened, and one checked the ropes.",
    "They made a safe plan before touching anything.",
    "They compared their observations instead of competing over guesses.",
    "They asked the captain for a lantern, a line, and time to think.",
]

PERSPECTIVES = [
    "Luna remembered that a brave question could open a door that fear had shut.",
    "Tavi kept the first clue in a little notebook for future voyages.",
    "Captain Mara praised the friends for protecting both the crew and the creature.",
    "The harbor keeper said the calmest sailor was often the bravest one.",
    "The sea lion surfaced once, as if it too had learned that trust could grow.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    captain: Entity
    creature: Entity
    mystery: Mystery
    suspicion_active: bool = False
    evidence_found: bool = False
    brave: bool = False
    friendship: bool = False
    solved: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A whodunit of friendship and bravery aboard a sailing boat."
    )
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--captain")
    parser.add_argument("--creature")
    parser.add_argument("--place")
    parser.add_argument("--boat")
    parser.add_argument("--sail")
    parser.add_argument("--object-name")
    parser.add_argument("--task")
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
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Milo", "Nia", "Oren"]),
        friend=args.friend or rng.choice(["Tavi", "Pia", "Joss", "Mina"]),
        captain=args.captain or rng.choice(["Captain Mara", "Captain Sol", "Captain Inez"]),
        creature=args.creature or rng.choice(
            ["savage-looking sea lion", "wild-faced seal", "rough-whiskered otter"]
        ),
        place=args.place or rng.choice(
            ["the bright harbor", "the moonlit pier", "the little island bay"]
        ),
        boat=args.boat or rng.choice(["the Starling", "the Swift Gull", "the Kind Wave"]),
        sail=args.sail or rng.choice(
            ["striped blue sail", "golden patchwork sail", "green-and-white sail"]
        ),
        object_name=args.object_name or "the friendship flag",
        task=args.task or "carry a friendship flag to the lighthouse",
    )


def validate(params: StoryParams) -> None:
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("A whodunit needs both a named hero and a trusted friend.")
    if not params.boat.strip() or not params.sail.strip():
        raise StoryError("The sailing mystery needs a boat and a sail.")
    forbidden = {"poison", "weapon", "deadly"}
    if any(word in params.task.lower() for word in forbidden):
        raise StoryError("This child-facing voyage must have a safe, hopeful task.")
    if params.hero.lower() == params.friend.lower():
        raise StoryError("The hero and friend must be different people so their friendship can act.")


def stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA17E9)
    key = "|".join(
        [
            params.hero,
            params.friend,
            params.captain,
            params.creature,
            params.place,
            params.boat,
            params.sail,
            params.object_name,
            params.task,
        ]
    )
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big"))


def setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} and {p.friend} stood aboard {p.boat} in {p.place}. "
        f"The {p.sail} rested neatly against the mast, waiting for the wind."
    )
    world.say(
        f"They had promised {p.captain} they would {p.task}. "
        f"Their special object, {p.object_name}, was tied safely beside the wheel."
    )


def begin_mystery(world: World) -> None:
    p = world.params
    m = world.mystery
    world.para()
    world.suspicion_active = True
    world.hero.add_meme("worry", 1)
    world.friend.add_meme("curiosity", 1)
    world.creature.add_meme("wariness", 1)
    world.say(f"Then came the mystery called {m.title}. {m.trouble.capitalize()}.")
    world.say(f"At once, {m.suspicion}.")
    world.say(f"{m.false_step.capitalize()}. The more they guessed, the farther the boat seemed from its happy voyage.")
    world.say(f"{p.hero} looked toward the creature and saw a frightened eye beneath its rough, savage-looking face.")


def investigate(world: World, rng: random.Random) -> None:
    p = world.params
    m = world.mystery
    world.para()
    world.brave = True
    world.friendship = True
    world.evidence_found = True
    world.hero.add_meme("bravery", 2)
    world.friend.add_meme("friendship", 2)
    world.say(f"{p.hero} took a steady breath and said to {p.friend}, '{rng.choice(QUESTIONS)}'")
    world.say(f"{p.friend} answered, 'I am here. We will solve it together, and we will keep everyone safe.'")
    world.say(f"{rng.choice(TEAMWORK_LINES)} Then they discovered the important clue: {m.clue}.")
    world.say(
        f"The clue changed the mystery. The real cause was that {m.cause}. "
        f"The supposedly savage culprit had not been trying to hurt anyone."
    )
    world.say(
        f"{p.hero} showed bravery when they {m.brave_job}; {p.friend} showed friendship when they "
        f"{m.friend_job}."
    )


def resolve(world: World, perspective: str) -> None:
    p = world.params
    m = world.mystery
    world.para()
    world.solved = True
    world.say(f"The mystery was solved: {m.repair}.")
    world.say(
        f"{p.captain} lifted {p.object_name} into place, and the {p.sail} filled with a warm breeze. "
        f"The boat was ready to sail, while the sea creature rested safely beyond the bow."
    )
    world.say(f"{p.captain} said, '{m.lesson}'")
    world.say(f"At the end, {m.ending}. {perspective} The voyage became a story about friendship and bravery, not blame.")


def tell(params: StoryParams) -> World:
    validate(params)
    rng = stable_rng(params)
    hero = Entity(params.hero, "hero")
    friend = Entity(params.friend, "friend")
    captain = Entity(params.captain, "captain")
    creature = Entity(params.creature, "creature")
    mystery = rng.choice(MYSTERIES)
    world = World(
        params=params,
        hero=hero,
        friend=friend,
        captain=captain,
        creature=creature,
        mystery=mystery,
    )
    setup(world, rng.choice(OPENINGS))
    begin_mystery(world)
    investigate(world, rng)
    resolve(world, rng.choice(PERSPECTIVES))
    world.facts = {
        "hero": params.hero,
        "friend": params.friend,
        "captain": params.captain,
        "creature": params.creature,
        "place": params.place,
        "boat": params.boat,
        "sail": params.sail,
        "mystery": mystery.title,
        "trouble": mystery.trouble,
        "clue": mystery.clue,
        "cause": mystery.cause,
        "repair": mystery.repair,
        "bravery": world.brave,
        "friendship": world.friendship,
        "resolved": world.solved,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
friend(X) :- friend_name(X).
mystery_begins :- missing(flag), suspicion(creature).
evidence_found :- clue_seen, listens(hero), listens(friend).
bravery :- evidence_found, safe_plan, approaches(hero).
friendship :- listens(hero), helps(friend).
resolved :- mystery_begins, evidence_found, bravery, friendship, repair_done.
#show mystery_begins/0.
#show evidence_found/0.
#show bravery/0.
#show friendship/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "luna"),
            asp.fact("friend_name", "tavi"),
            asp.fact("missing", "flag"),
            asp.fact("suspicion", "creature"),
            asp.fact("clue_seen"),
            asp.fact("listens", "hero"),
            asp.fact("listens", "friend"),
            asp.fact("safe_plan"),
            asp.fact("approaches", "hero"),
            asp.fact("helps", "friend"),
            asp.fact("repair_done"),
        ]
    )


def asp_program(show: str = "") -> str:
    if not show:
        show = "\n".join(
            [
                "#show mystery_begins/0.",
                "#show evidence_found/0.",
                "#show bravery/0.",
                "#show friendship/0.",
                "#show resolved/0.",
            ]
        )
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def asp_verify() -> int:
    if not asp_available():
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    import asp

    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    required = {"mystery_begins", "evidence_found", "bravery", "friendship", "resolved"}
    if not required.issubset(names):
        print("MISMATCH: ASP twin did not reach the complete repaired state.")
        return 1
    for seed in range(3):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or not sample.world or not sample.world.solved:
            print("MISMATCH: generated story did not resolve.")
            return 1
    print("OK: ASP twin and generated stories reach the expected whodunit resolution.")
    return 0


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly whodunit about {p.hero} and {p.friend} aboard {p.boat}.",
        f"Include a savage-looking sea creature, a sail, and a mystery solved through friendship and bravery.",
        f"End with {p.object_name} flying safely as the friends learn to follow clues before blaming anyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    m = world.mystery
    return [
        QAItem(
            question=f"What mystery did {p.hero} and {p.friend} investigate?",
            answer=f"They investigated {m.trouble}. The mystery was called {m.title}.",
        ),
        QAItem(
            question="Why did the crew first suspect the savage-looking creature?",
            answer=f"They suspected it because {m.suspicion}. That was a guess, not proof.",
        ),
        QAItem(
            question="What clue changed the investigation?",
            answer=f"They noticed that {m.clue}. This clue led them to the real cause.",
        ),
        QAItem(
            question=f"How did {p.hero} show bravery and {p.friend} show friendship?",
            answer=f"{p.hero} {m.brave_job}; {p.friend} {m.friend_job}. They solved the problem with a safe plan and helped one another.",
        ),
        QAItem(
            question="What final image showed that the mystery was resolved?",
            answer=f"At the end, {m.ending}. The repaired scene showed that the boat and its friendships were safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a sail?",
            answer="A sail is a strong sheet of cloth that catches wind and helps move a boat.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing a careful, helpful thing even when something feels frightening.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people listen, help, and stand by one another.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story in which characters gather clues to discover what happened.",
        ),
        QAItem(
            question=f"Why was the {p.creature} called savage-looking?",
            answer="It looked rough and frightening, but its appearance did not prove that it was dangerous or guilty.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in [world.hero, world.friend, world.captain, world.creature]:
        lines.append(
            f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        "state: "
        f"suspicion={world.suspicion_active} evidence={world.evidence_found} "
        f"bravery={world.brave} friendship={world.friendship} resolved={world.solved}"
    )
    lines.append(f"mystery: {world.mystery.title}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Luna",
        friend="Tavi",
        captain="Captain Mara",
        creature="savage-looking sea lion",
        place="the bright harbor",
        boat="the Starling",
        sail="striped blue sail",
    ),
    StoryParams(
        hero="Nia",
        friend="Joss",
        captain="Captain Sol",
        creature="wild-faced seal",
        place="the moonlit pier",
        boat="the Kind Wave",
        sail="green-and-white sail",
    ),
]


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
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        if not asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, curated in enumerate(CURATED):
            params = curated
            if args.seed is not None:
                params = StoryParams(**{**curated.__dict__, "seed": args.seed + index})
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            seed = base_seed + index
            index += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.friend} aboard {sample.params.boat}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
