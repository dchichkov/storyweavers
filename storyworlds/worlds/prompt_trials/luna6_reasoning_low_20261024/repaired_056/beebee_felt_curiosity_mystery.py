#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_HERE = os.path.abspath(__file__)
_ROOT = os.path.dirname(_HERE)
while _ROOT != os.path.dirname(_ROOT) and not os.path.exists(os.path.join(_ROOT, "results.py")):
    _ROOT = os.path.dirname(_ROOT)
if os.path.exists(os.path.join(_ROOT, "results.py")):
    sys.path.insert(0, _ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "willow library": {
        "setting": "the willow library",
        "has_felt": True,
        "has_clue": True,
        "description": "a little reading room with a sunny craft table",
    },
    "bluebird school": {
        "setting": "the Bluebird School",
        "has_felt": True,
        "has_clue": True,
        "description": "a bright classroom with a felt-board wall",
    },
    "lantern hall": {
        "setting": "Lantern Hall",
        "has_felt": True,
        "has_clue": True,
        "description": "a community room being readied for a puppet show",
    },
    "rainy station": {
        "setting": "the rainy station",
        "has_felt": False,
        "has_clue": True,
        "description": "a small waiting room with a notice board",
    },
}
NAMES = ("Nina", "Milo", "Iris", "Toby", "Luna", "Pip", "Mara", "Jasper")
MOODS = ("curious", "patient", "thoughtful", "brave")

MYSTERIES = (
    {
        "name": "the missing felt wing",
        "opening": "A tiny felt bee named Beebee was ready to lead the story hour, but one soft yellow wing was missing.",
        "first_guess": "Milo thought a gust had carried the wing out through the open window.",
        "dialogue": (
            ("Maybe the wind took Beebee's wing!", "Let's look for a trail before we decide."),
        ),
        "clue": "a row of tiny blue paper stars led from the craft table to the book cart, and one star was caught on its lower shelf",
        "test": "They checked the window ledge, where not a single paper star had landed.",
        "discovery": "the wing had stuck to a strip of blue paper tucked beneath the cart's shelf",
        "action": "carefully peeled the felt wing from the paper and pressed it back onto Beebee",
        "result": "Beebee was whole again, and the children could begin their puppet story",
        "ending": "When Beebee fluttered across the felt-board sky, the rescued wing glowed like a little piece of sunshine.",
        "lesson": "curiosity works best when you follow clues instead of settling for the first guess",
    },
    {
        "name": "the quiet bell",
        "opening": "Beebee, the felt bee puppet, was supposed to ring a tiny bell at the start of the puppet show. The bell had vanished.",
        "first_guess": "Nina wondered whether someone had taken the bell home by mistake.",
        "dialogue": (
            ("Someone must have carried the bell away," "Let's ask what the clues say before we blame anyone."),
        ),
        "clue": "a thin silver thread trailed from Beebee's felt pocket to the curtain hem",
        "test": "They lifted the curtain edge and heard a faint ting, then stopped to look rather than tugging hard.",
        "discovery": "the bell was caught in a loose curtain loop, still attached to its thread",
        "action": "freed the thread gently and tied the bell securely inside Beebee's felt pocket",
        "result": "the bell rang clearly without anyone losing or taking it",
        "ending": "Beebee gave one bright ting beneath the curtain, and every waiting face turned toward the stage.",
        "lesson": "a careful question can solve a mystery without making an unfair accusation",
    },
    {
        "name": "the upside-down clue",
        "opening": "Beebee, a bright felt bee, had been left beside a map for the garden puppet show. By morning, the map seemed to point the wrong way.",
        "first_guess": "Toby said someone must have drawn the garden path backward.",
        "dialogue": (
            ("The map must be wrong," "Or perhaps we should check how it is being held."),
        ),
        "clue": "a thumb-sized smudge on the map matched the blue chalk on the table, and the map's small north arrow was upside down",
        "test": "They turned the map around and compared its drawn pond with the real pond visible through the window.",
        "discovery": "the map was right; it had simply been turned around when Beebee was set on top of it",
        "action": "rotated the map to match its north arrow and moved Beebee to the starting mark",
        "result": "the puppeteers found the garden path and carried their show to the right place",
        "ending": "Beebee sat at the map's starting mark while the real pond winked blue beyond the window.",
        "lesson": "before changing a clue, check whether your point of view has changed",
    },
    {
        "name": "the disappearing stripe",
        "opening": "The children had painted a tiny paper hive for Beebee's felt-bee story, but one golden stripe seemed to disappear whenever they looked away.",
        "first_guess": "Iris suspected that someone was taking the stripe for another picture.",
        "dialogue": (
            ("I think someone is borrowing it," "Let's watch the table together and see what really happens."),
        ),
        "clue": "the golden stripe reappeared on Beebee's fuzzy felt back whenever the puppet was lifted",
        "test": "They watched the table closely and noticed that a paper strip clung to the puppet's rough felt.",
        "discovery": "the stripe had not been taken; static and the fuzzy felt made it stick to Beebee",
        "action": "slid the stripe off gently and smoothed it onto the paper hive",
        "result": "the hive was finished, and Beebee could move without carrying its painted stripe away",
        "ending": "The golden stripe stayed on the paper hive as Beebee bobbed past, ready for the first scene.",
        "lesson": "noticing what changes can reveal a cause that no one intended",
    },
)

OPENINGS = (
    "A small puzzle arrived just as the room grew busy.",
    "The mystery began with one missing thing and several possible explanations.",
    "Outside, rain tapped the windows while a curious question waited inside.",
    "No one was worried, but everyone wanted to know what had happened.",
    "The room looked ordinary until Beebee's little mystery appeared.",
)
INVESTIGATIONS = (
    "They wrote down what they knew, then kept their guesses separate from the evidence.",
    "They searched slowly, taking turns to watch and to listen.",
    "They looked at the nearby objects without moving anything that might hold a clue.",
    "They retraced Beebee's short journey and compared each detail with their first idea.",
    "They asked one another what the clue proved—and what it did not prove.",
)
REFLECTIONS = (
    "They thanked each other for checking the evidence before acting.",
    "Together they added the real explanation to Beebee's storybook.",
    "They promised to ask another question whenever a clue seemed puzzling.",
    "They put the room back in order, leaving the useful clues easy to find.",
)

ASP_RULES = r"""
kind(beebee).
kind(felt).
kind(curiosity).
kind(mystery).

setting("willow_library").
setting("bluebird_school").
setting("lantern_hall").
setting("rainy_station").

compatible(P, beebee) :- setting(P), clue_ok(P).
compatible(P, felt) :- setting(P), felt_ok(P).
compatible_story(P) :- compatible(P, beebee), compatible(P, felt).

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
    place: str
    hero: str
    partner: str
    mood: str
    feature: str = "Curiosity"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

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
        description="A child-friendly curiosity mystery about Beebee, a felt bee."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--feature", choices=("Curiosity",), default="Curiosity")
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
    for place, meta in PLACES.items():
        key = place.replace(" ", "_")
        lines.append(asp.fact("setting", key))
        if meta["has_clue"]:
            lines.append(asp.fact("clue_ok", key))
        if meta["has_felt"]:
            lines.append(asp.fact("felt_ok", key))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/2.\n#show compatible_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_compatibilities() -> set[tuple[str, str]]:
    result = set()
    for place, meta in PLACES.items():
        key = place.replace(" ", "_")
        if meta["has_clue"]:
            result.add((key, "beebee"))
        if meta["has_felt"]:
            result.add((key, "felt"))
    return result


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    actual = set(asp.atoms(model, "compatible"))
    expected = python_compatibilities()
    if actual != expected:
        print("MISMATCH:")
        print("only in ASP:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        return 1
    print(f"OK: ASP and Python agree on {len(actual)} compatibility facts.")
    checks = [
        StoryParams("willow library", "Nina", "Milo", "curious", seed=i)
        for i in range(len(MYSTERIES) * 2)
    ]
    for params in checks:
        sample = generate(params)
        if not sample.story.strip() or not sample.story.endswith("."):
            print("MISMATCH: generated story is incomplete.")
            return 1
        if params.hero not in sample.story or params.partner not in sample.story:
            print("MISMATCH: a generated story omitted a character.")
            return 1
        if "said." not in sample.story:
            print("MISMATCH: a generated story omitted spoken dialogue.")
            return 1
    print(f"OK: exercised {len(checks)} complete, dialogue-bearing stories.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(
        [name for name, meta in PLACES.items() if meta["has_felt"] and meta["has_clue"]]
    )
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}.")
    if not (PLACES[place]["has_felt"] and PLACES[place]["has_clue"]):
        raise StoryError(
            "Beebee's mystery needs a felt object and a nearby clue; choose a place with both."
        )
    hero = rng.choice(NAMES)
    partner = rng.choice([name for name in NAMES if name != hero])
    return StoryParams(place, hero, partner, rng.choice(MOODS), args.feature)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join((params.place, params.hero, params.partner, params.mood, params.feature))
    return int.from_bytes(
        hashlib.blake2b(identity.encode("utf-8"), digest_size=8).digest(), "big"
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if not (PLACES[params.place]["has_felt"] and PLACES[params.place]["has_clue"]):
        raise StoryError(
            "Beebee's mystery needs a felt object and a nearby clue; choose a place with both."
        )
    if params.feature != "Curiosity":
        raise StoryError("This mystery uses the Curiosity feature.")
    if params.hero == params.partner:
        raise StoryError("The detective and partner must be different people.")
    if params.mood not in MOODS:
        raise StoryError(f"Choose a mood from: {', '.join(MOODS)}.")

    seed = _story_seed(params)
    case = MYSTERIES[seed % len(MYSTERIES)]
    dialogue = case["dialogue"][0]
    opening_line = OPENINGS[(seed // len(MYSTERIES)) % len(OPENINGS)]
    investigation = INVESTIGATIONS[
        (seed // (len(MYSTERIES) * len(OPENINGS))) % len(INVESTIGATIONS)
    ]
    reflection = REFLECTIONS[
        (seed // (len(MYSTERIES) * len(OPENINGS) * len(INVESTIGATIONS)))
        % len(REFLECTIONS)
    ]
    meta = PLACES[params.place]
    world = World(place=meta["setting"])
    hero = Entity(
        params.hero,
        "character",
        "young detective",
        "detective",
        meters={"attention": 0.7},
        memes={"curiosity": 0.7},
        location=params.place,
    )
    partner = Entity(
        params.partner,
        "character",
        "investigation partner",
        "helper",
        meters={"attention": 0.6},
        memes={"curiosity": 0.6},
        location=params.place,
    )
    beebee = Entity(
        "beebee",
        "puppet",
        "Beebee, the felt bee",
        "felt_puppet",
        meters={"condition": 0.7},
        memes={"beloved": 1.0},
        location=params.place,
    )
    world.entities = {e.id: e for e in (hero, partner, beebee)}

    world.say(opening_line)
    world.say(
        f"In {world.place}, {params.hero} was a {params.mood} young detective, and "
        f"{params.partner} was their good friend. Together they watched over Beebee, "
        "a small bee puppet sewn from soft felt."
    )
    world.say(case["opening"])
    world.para()
    world.say(case["first_guess"])
    world.say(
        f"'{dialogue[0]},' {params.hero} said. "
        f"'{dialogue[1]},' {params.partner} replied."
    )
    world.say(case["test"])
    world.say(investigation)
    world.para()
    world.say(f"Then they noticed that {case['clue']}.")
    world.say(f"That clue showed them that {case['discovery']}.")
    world.say(
        f"They had not solved the mystery by guessing; they had followed the evidence "
        f"and let their curiosity change their minds."
    )
    world.para()
    world.say(f"Together, {params.hero} and {params.partner} {case['action']}.")
    world.say(f"Because they checked the clue first, {case['result']}.")
    world.say(reflection)
    world.say(f"They learned that {case['lesson']}.")
    world.say(case["ending"])

    hero.meters["attention"] = 1.0
    partner.meters["attention"] = 0.9
    hero.memes["careful_reasoning"] = 1.0
    partner.memes["careful_reasoning"] = 1.0
    beebee.meters["condition"] = 1.0
    beebee.memes["mystery_solved"] = 1.0
    world.trace = [
        f"mystery:{case['name']}",
        f"first_guess:{case['first_guess']}",
        f"observed:{case['clue']}",
        f"discovered:{case['discovery']}",
        f"resolved:{case['result']}",
    ]
    world.facts = {
        "place": params.place,
        "mystery": case["name"],
        "hero": params.hero,
        "partner": params.partner,
        "character": "Beebee",
        "material": "felt",
        "first_guess": case["first_guess"],
        "clue": case["clue"],
        "discovery": case["discovery"],
        "resolution": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Tell a child-friendly curiosity mystery about Beebee, a felt bee, in {world.place}.",
        f"Show how {params.hero} and {params.partner} use the clue to solve {case['name']}.",
        "Include a brief spoken exchange that changes how the friends investigate.",
    ]
    story_qa = [
        QAItem(
            question="Who was Beebee?",
            answer="Beebee was a small bee puppet sewn from soft felt, and the friends cared about keeping the puppet safe.",
        ),
        QAItem(
            question=f"What did {params.hero} first suspect?",
            answer=f"{params.hero} first suspected that {case['first_guess'][0].lower() + case['first_guess'][1:]} They checked the evidence instead of treating that idea as a fact.",
        ),
        QAItem(
            question="Which clue helped solve the mystery?",
            answer=f"They noticed that {case['clue']}. This detail led them to discover that {case['discovery']}.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"{params.hero} and {params.partner} {case['action']}. As a result, {case['result']}.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {case['lesson']}. Their curiosity helped them follow the clue rather than stick with their first guess.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is felt?",
            answer="Felt is a soft fabric made by pressing fibers together. People use it for crafts, puppets, and decorations.",
        ),
        QAItem(
            question="Why is curiosity useful in a mystery?",
            answer="Curiosity encourages people to ask questions, notice clues, and test ideas before deciding what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective gathers clues and checks what they show in order to understand a puzzle or solve a mystery.",
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = [f"label={entity.label}", f"location={entity.location}"]
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(details)}")
        for entry in sample.world.trace:
            print(f"  {entry}")
    if qa:
        for title, items in (
            ("prompts", sample.prompts),
            ("story qa", sample.story_qa),
            ("world qa", sample.world_qa),
        ):
            print(f"\n== {title} ==")
            for item in items:
                if isinstance(item, QAItem):
                    print(f"Q: {item.question}\nA: {item.answer}")
                else:
                    print(f"- {item}")


CURATED = [
    StoryParams("willow library", "Nina", "Milo", "curious", seed=0),
    StoryParams("bluebird school", "Iris", "Toby", "patient", seed=1),
    StoryParams("lantern hall", "Luna", "Pip", "thoughtful", seed=2),
    StoryParams("willow library", "Mara", "Jasper", "brave", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("compatible:", sorted(asp.atoms(model, "compatible")))
        print("compatible stories:", sorted(asp.atoms(model, "compatible_story")))
        return

    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        attempts = 0
        while len(samples) < args.n and attempts < args.n * 30:
            attempts += 1
            params = resolve_params(args, random.Random(rng.randrange(2**63)))
            params.seed = rng.randrange(2**63)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(payload)
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
