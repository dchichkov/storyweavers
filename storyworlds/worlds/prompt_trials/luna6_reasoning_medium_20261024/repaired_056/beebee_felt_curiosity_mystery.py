#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# This script may live several directories below the repository root. Find the
# shared result module without making the storyworld depend on its own location.
_HERE = Path(__file__).resolve()
_STORYWORLDS = next(
    (parent for parent in _HERE.parents if (parent / "results.py").is_file()),
    None,
)
if _STORYWORLDS is None:
    raise RuntimeError("Could not locate storyworlds/results.py")
sys.path.insert(0, str(_STORYWORLDS))
from results import QAItem, StoryError, StorySample  # noqa: E402


ROOMS = {
    "reading nook": {
        "setting": "the reading nook",
        "has_felt": True,
        "has_light": True,
        "has_clues": True,
    },
    "art room": {
        "setting": "the art room",
        "has_felt": True,
        "has_light": True,
        "has_clues": True,
    },
    "puppet corner": {
        "setting": "the puppet corner",
        "has_felt": True,
        "has_light": True,
        "has_clues": True,
    },
    "sunny hall": {
        "setting": "the sunny hall",
        "has_felt": True,
        "has_light": True,
        "has_clues": True,
    },
}

NAMES = ("Luna", "Milo", "Nina", "Toby", "Iris", "Pip", "Mara", "Jasper")
MOODS = ("curious", "patient", "thoughtful", "bold")

MYSTERIES = (
    {
        "title": "the case of the vanished felt bee",
        "opening": (
            "At story-circle time, Luna reached for Beebee, the little bee made "
            "of yellow felt, but its cushion was empty."
        ),
        "first_guess": (
            "Milo wondered if someone had carried Beebee off to play."
        ),
        "dialogue": (
            ("Maybe someone took Beebee.", "Let us look for clues before we decide."),
        ),
        "clue": (
            "a yellow thread curled beside an open picture book, and one page "
            "kept lifting at its corner"
        ),
        "turn": (
            "the thread belonged to Beebee's soft wing, which had caught in the "
            "book's cloth bookmark"
        ),
        "action": (
            "carefully freed the bookmark and lifted Beebee from the book's "
            "fold without pulling its wing"
        ),
        "result": (
            "Beebee was safe, and the children discovered that a gentle breeze "
            "had nudged the open book over the toy"
        ),
        "ending": (
            "They set Beebee on the cushion beside the book, where its bright "
            "felt wings rested in a square of sunshine."
        ),
        "lesson": (
            "curiosity works best when you follow clues instead of blaming someone"
        ),
        "sound": "flip-flap",
    },
    {
        "title": "the tapping behind the curtain",
        "opening": (
            "A soft tap-tap interrupted the puppet show, but no puppet was "
            "moving on the little stage."
        ),
        "first_guess": (
            "Nina thought Beebee, the yellow felt bee, might be knocking from "
            "inside the puppet box."
        ),
        "dialogue": (
            ("Is Beebee trying to tell us something?", "Let us find where the tapping begins."),
        ),
        "clue": (
            "the wooden curtain pull trembled whenever the open window let in "
            "a puff of air"
        ),
        "turn": (
            "Beebee was tucked safely behind the curtain, while the moving pull "
            "made the mysterious tapping"
        ),
        "action": (
            "held the curtain still, found Beebee resting in a soft fold, and "
            "closed the window a little"
        ),
        "result": (
            "the tapping stopped, and the puppet show could continue without "
            "anyone mistaking a draft for a secret message"
        ),
        "ending": (
            "Beebee sat in the front row as the curtain stayed quiet and the "
            "puppets danced beneath the stage lights."
        ),
        "lesson": (
            "a mystery becomes clearer when you check what changes and what stays still"
        ),
        "sound": "tap-tap",
    },
    {
        "title": "the moonlit mark",
        "opening": (
            "After sunset, a bright golden spot appeared high on the wall, "
            "though nobody had hung a new picture."
        ),
        "first_guess": (
            "Toby wondered if the spot was a tiny lamp left on for Beebee, "
            "the felt bee."
        ),
        "dialogue": (
            ("That golden spot looks like a secret signal.", "What nearby things could be shining?"),
        ),
        "clue": (
            "when Iris tilted a shiny paper star, the golden spot slid across "
            "the wall"
        ),
        "turn": (
            "moonlight was reflecting from the paper star, and Beebee was safe "
            "on the low shelf beneath it"
        ),
        "action": (
            "turned the paper star toward the window and helped Beebee down "
            "from the shelf"
        ),
        "result": (
            "the golden spot disappeared from the wall, and everyone understood "
            "how the moonlight had made it"
        ),
        "ending": (
            "Beebee nestled beside the paper star as the moon shone plainly "
            "through the window."
        ),
        "lesson": (
            "curiosity can turn a surprising sight into something you understand"
        ),
        "sound": "whoosh",
    },
    {
        "title": "the missing wing",
        "opening": (
            "When the children set up their felt friends for a picture, "
            "Beebee seemed to have lost one yellow wing."
        ),
        "first_guess": (
            "Pip feared the wing had been torn away during the busy morning."
        ),
        "dialogue": (
            ("What if Beebee is broken?", "We can look carefully before we worry."),
        ),
        "clue": (
            "a matching yellow shape peeked from beneath a folded blue scarf, "
            "with no loose stitches nearby"
        ),
        "turn": (
            "the wing was a separate felt piece that had slipped under the "
            "scarf, not a torn part of Beebee"
        ),
        "action": (
            "lifted the scarf and placed the soft wing back beside Beebee "
            "for its maker to attach"
        ),
        "result": (
            "the maker found both pieces together and could mend Beebee "
            "carefully with an adult's help"
        ),
        "ending": (
            "Later, Beebee's two bright wings rested together on the picture "
            "table, ready for the next story."
        ),
        "lesson": (
            "look for evidence before deciding that something has gone wrong"
        ),
        "sound": "rustle",
    },
    {
        "title": "the fluttering shelf",
        "opening": (
            "A row of paper pictures fluttered on the shelf, even though "
            "the room seemed still."
        ),
        "first_guess": (
            "Mara thought a tiny creature might be hiding with Beebee, the "
            "little bee made of felt."
        ),
        "dialogue": (
            ("Something must be hiding in there.", "Let us notice what makes the papers move."),
        ),
        "clue": (
            "the pictures fluttered each time the heater clicked on, and a "
            "thin ribbon lifted near its warm air"
        ),
        "turn": (
            "a gentle stream of warm air was moving the pictures, while "
            "Beebee was tucked safely behind them"
        ),
        "action": (
            "moved the pictures away from the warm air with the teacher's "
            "permission and brought Beebee back to the table"
        ),
        "result": (
            "the shelf grew still, and the children knew the flutter had "
            "a simple cause"
        ),
        "ending": (
            "Beebee sat in the middle of the table while the paper pictures "
            "rested quietly on the shelf."
        ),
        "lesson": (
            "careful observation can explain a strange sound or movement"
        ),
        "sound": "whirr",
    },
)

DIALOGUE_FOLLOWUPS = (
    ("I see a clue by the book.", "Then let us check what it tells us."),
    ("The tapping stopped when you held the curtain.", "That helps us find its real cause."),
    ("The bright spot moved with the star.", "Now we can test that idea gently."),
    ("The wing is here, not torn.", "Good looking saved us from worrying too soon."),
    ("The papers move when the heater clicks.", "Now we know where to look for Beebee."),
)

INVESTIGATION_LINES = (
    "They paused, described what they could see, and kept their guesses separate from the evidence.",
    "Together, they checked the nearest objects without tugging, poking, or disturbing anything.",
    "They followed the smallest clue and asked what had changed since the room was quiet.",
    "Instead of rushing to a conclusion, they watched and listened once more.",
    "They made a careful search, checking each safe place before moving to the next.",
)

ASP_RULES = r"""
kind(beebee).
kind(felt).
kind(curiosity).
kind(mystery).

feature(beebee) :- kind(beebee).
feature(felt) :- kind(felt).
feature(curiosity) :- kind(curiosity).
feature(mystery) :- kind(mystery).

room(R) :- has_felt(R), has_light(R), has_clues(R).
compatible(R, beebee) :- room(R).
compatible(R, felt) :- room(R).
compatible_story(R) :- compatible(R, beebee), compatible(R, felt).

#show compatible/2.
#show compatible_story/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    room: str
    hero: str
    friend: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in paragraph if part) for paragraph in self.paragraphs if paragraph)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A small curiosity mystery about Beebee, a little bee made of felt."
    )
    parser.add_argument("--room", choices=ROOMS)
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


def asp_facts() -> str:
    import asp

    lines = []
    for room, metadata in ROOMS.items():
        term = room.replace(" ", "_")
        lines.append(asp.fact("has_felt", term)) if metadata["has_felt"] else None
        lines.append(asp.fact("has_light", term)) if metadata["has_light"] else None
        lines.append(asp.fact("has_clues", term)) if metadata["has_clues"] else None
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_compatibilities() -> set[tuple]:
    return {
        (room.replace(" ", "_"), feature)
        for room, metadata in ROOMS.items()
        if metadata["has_felt"] and metadata["has_light"] and metadata["has_clues"]
        for feature in ("beebee", "felt")
    }


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program("#show compatible/2.\n#show compatible_story/1."))
        actual = set(asp.atoms(model, "compatible"))
        expected = python_compatibilities()
        expected_stories = {
            (room.replace(" ", "_"),)
            for room, metadata in ROOMS.items()
            if metadata["has_felt"] and metadata["has_light"] and metadata["has_clues"]
        }
        actual_stories = set(asp.atoms(model, "compatible_story"))
    except ImportError as exc:
        print(f"ASP verification requires clingo: {exc}")
        return 1

    if actual != expected or actual_stories != expected_stories:
        print("MISMATCH: ASP and Python compatibility gates disagree.")
        print("only in ASP:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        print("story mismatch:", sorted(actual_stories ^ expected_stories))
        return 1

    examples = [
        StoryParams(room="reading nook", hero="Luna", friend="Milo", mood="curious", seed=i)
        for i in range(len(MYSTERIES))
    ]
    for params in examples:
        sample = generate(params)
        if not sample.story.strip() or "Beebee" not in sample.story or "felt" not in sample.story:
            print("MISMATCH: a generated story is missing its central character or felt clue.")
            return 1
        if not any('"' in sentence for sentence in sample.story.split(". ")):
            print("MISMATCH: a generated story is missing spoken dialogue.")
            return 1
        if sample.world is None or len(sample.world.trace) < 4:
            print("MISMATCH: a generated story is missing its world-state trace.")
            return 1

    print(f"OK: ASP and Python gates agree ({len(actual)} compatibility facts); generated stories passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(
        [
            name
            for name, metadata in ROOMS.items()
            if metadata["has_felt"] and metadata["has_light"] and metadata["has_clues"]
        ]
    )
    if room not in ROOMS:
        raise StoryError(f"Unknown room: {room!r}. Choose one of {', '.join(ROOMS)}.")
    metadata = ROOMS[room]
    if not (metadata["has_felt"] and metadata["has_light"] and metadata["has_clues"]):
        raise StoryError("This mystery needs a felt clue, a light source, and observable details.")
    hero = rng.choice(NAMES)
    friend = rng.choice([name for name in NAMES if name != hero])
    return StoryParams(room=room, hero=hero, friend=friend, mood=rng.choice(MOODS))


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join((params.room, params.hero, params.friend, params.mood))
    return int.from_bytes(hashlib.blake2b(identity.encode("utf-8"), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"Unknown room: {params.room!r}. Choose one of {', '.join(ROOMS)}.")
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("The mystery needs two named friends.")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood {params.mood!r}. Choose one of {', '.join(MOODS)}.")
    metadata = ROOMS[params.room]
    if not (metadata["has_felt"] and metadata["has_light"] and metadata["has_clues"]):
        raise StoryError("This mystery needs a felt clue, a light source, and observable details.")

    seed = _story_seed(params)
    mystery_index = seed % len(MYSTERIES)
    mystery = MYSTERIES[mystery_index]
    followup = DIALOGUE_FOLLOWUPS[mystery_index]
    rng = random.Random(seed ^ 0xBEEBEE)
    investigation = rng.choice(INVESTIGATION_LINES)
    setting = metadata["setting"]

    hero = Entity(
        id=params.hero,
        kind="character",
        label="young mystery-solver",
        type="child",
        meters={"attention": 0.7, "confidence": 0.5},
        memes={"curiosity": 0.8, "care": 0.7},
        location=params.room,
    )
    friend = Entity(
        id=params.friend,
        kind="character",
        label="friend",
        type="child",
        meters={"attention": 0.6, "confidence": 0.4},
        memes={"curiosity": 0.7, "care": 0.7},
        location=params.room,
    )
    beebee = Entity(
        id="beebee",
        kind="toy",
        label="yellow felt bee",
        type="felt_toy",
        meters={"safe": 1.0},
        memes={"beloved": 1.0},
        location=params.room,
    )
    world = World(room=setting, entities={hero.id: hero, friend.id: friend, beebee.id: beebee})

    world.say(f"In {setting}, {params.hero} was helping {params.friend} arrange the toys.")
    world.say(mystery["opening"])
    world.say(f"{params.hero} was feeling {params.mood}, but both friends agreed that a puzzle was a reason to look closely, not to worry.")
    world.say(f"“{mystery['dialogue'][0][0]}” said {params.friend}. “{mystery['dialogue'][0][1]}” replied {params.hero}.")

    world.para()
    world.say(mystery["first_guess"])
    world.say(investigation)
    world.say(f"Then {params.hero} noticed that {mystery['clue']}.")
    world.say(f"“{followup[0]}” said {params.hero}. “{followup[1]}” answered {params.friend}.")
    world.say(f"That clue changed their minds: {mystery['turn']}.")

    world.para()
    world.say(f"Working together, {params.hero} and {params.friend} {mystery['action']}.")
    world.say(f"Because they followed the evidence, {mystery['result']}.")
    world.say(f"They learned that {mystery['lesson']}.")
    world.say(mystery["ending"])

    hero.meters.update({"attention": 1.0, "confidence": 0.8})
    friend.meters.update({"attention": 0.9, "confidence": 0.7})
    hero.memes.update({"curiosity": 1.0, "care": 1.0})
    friend.memes.update({"curiosity": 0.9, "care": 1.0})
    beebee.memes["safe_and_found"] = 1.0
    world.trace = [
        f"mystery:{mystery['title']}",
        f"first_guess:{mystery['first_guess']}",
        f"observed_clue:{mystery['clue']}",
        f"new_understanding:{mystery['turn']}",
        f"action:{mystery['action']}",
        f"resolution:{mystery['result']}",
    ]
    world.facts = {
        "hero": hero,
        "friend": friend,
        "beebee": beebee,
        "room": params.room,
        "setting": setting,
        "mystery": mystery["title"],
        "clue": mystery["clue"],
        "turn": mystery["turn"],
        "resolution": mystery["result"],
        "lesson": mystery["lesson"],
    }

    prompts = [
        f"Write a child-friendly curiosity mystery about Beebee, a felt bee, in {setting}.",
        f"Show how {params.hero} and {params.friend} use the clue that {mystery['clue']}.",
        "Include a spoken exchange, a changed understanding, a safe solution, and a clear ending image.",
    ]
    story_qa = [
        QAItem(
            question="Who or what is Beebee?",
            answer="Beebee is the little bee made of yellow felt, a toy the children care about.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.friend} solve the mystery?",
            answer=f"They noticed that {mystery['clue']}. This observation helped them reconsider their first guess.",
        ),
        QAItem(
            question="What did the friends discover?",
            answer=f"They discovered that {mystery['turn']}. The clue explained what had seemed mysterious.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"{params.hero} and {params.friend} {mystery['action']}. As a result, {mystery['result']}.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {mystery['lesson']}. Their careful search helped them understand the mystery without jumping to conclusions.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is felt?",
            answer="Felt is a soft fabric made by pressing fibers together, and it can be cut into shapes for toys and pictures.",
        ),
        QAItem(
            question="Why is curiosity useful in a mystery?",
            answer="Curiosity encourages people to ask questions and look for evidence before deciding what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail that can help someone understand or solve a question.",
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = [f"label={entity.label}", f"location={entity.location}"]
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(details)}")
        for event in sample.world.trace:
            print(f"  {event}")
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


CURATED = [
    StoryParams(room="reading nook", hero="Luna", friend="Milo", mood="curious", seed=0),
    StoryParams(room="art room", hero="Nina", friend="Toby", mood="patient", seed=1),
    StoryParams(room="puppet corner", hero="Iris", friend="Pip", mood="thoughtful", seed=2),
    StoryParams(room="sunny hall", hero="Mara", friend="Jasper", mood="bold", seed=3),
    StoryParams(room="reading nook", hero="Luna", friend="Milo", mood="curious", seed=4),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show compatible/2.\n#show compatible_story/1."))
        print("compatible:", asp.atoms(model, "compatible"))
        print("compatible_story:", asp.atoms(model, "compatible_story"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < args.n * 30:
            attempts += 1
            local_rng = random.Random(rng.randrange(2**63))
            params = resolve_params(args, local_rng)
            params.seed = rng.randrange(2**63)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not make enough distinct stories; try a smaller -n value.")

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
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
