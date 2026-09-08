#!/usr/bin/env python3
"""The Mystery of the Missing Moon Bell.

A small mystery about a catch, a collection, and a hungry garden visitor.
Sound effects belong to the world events, not to a frozen paragraph.
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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    sound: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Pip"
    clue: str = "feather"
    visitor: str = "raccoon"
    approach: str = "listen"
    item: str = "moon bell"
    seed: int = 777


NAMES = ("Luna", "Mira", "Nia", "Zoe", "Tara", "Pip")
CLUES = {
    "feather": ("a silver feather", "silver"),
    "button": ("a blue button", "blue"),
    "seed": ("a striped seed", "striped"),
}
VISITORS = {
    "raccoon": ("a raccoon", "crunch"),
    "hedgehog": ("a hedgehog", "snuffle"),
    "crow": ("a crow", "caw"),
}
APPROACHES = ("listen", "rush")
ITEMS = ("moon bell", "star bell", "shell bell")

PROMPT = (
    "Write a child-facing mystery in which two friends investigate a missing bell, "
    "catch the real visitor, collect clues, and feed it kindly."
)

ASP_RULES = """
valid_clue(C) :- clue(C).
valid_visitor(V) :- visitor(V).
compatible(C,V) :- clue(C), visitor(V).
#show compatible/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                "hero", params.hero, "character", "garden",
                memes={"curiosity": 1.0, "kindness": 0.6},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "garden",
                memes={"curiosity": 0.8, "kindness": 0.8},
            ),
            "bell": Entity(
                "bell", f"the {params.item}", "object", "gate",
                meters={"ringed": 0, "hidden": 1},
                memes={"importance": 1.0},
            ),
            "collection": Entity(
                "collection", "the clue collection", "collection", "table",
                meters={"count": 0},
            ),
            "food": Entity(
                "food", "a bowl of apple pieces", "food", "shed",
                meters={"pieces": 3, "fed": 0},
            ),
            "visitor": Entity(
                "visitor", VISITORS[params.visitor][0], "animal", "unknown",
                meters={"caught": 0, "fed": 0},
                memes={"hunger": 1.0, "fear": 0.4},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        sound: str = "",
        question: str = "",
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(
            Event(
                kind=kind,
                text=text,
                sound=sound,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(self, speaker: str, text: str) -> None:
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(kind="speech", text=f'"{text}" {label} {verb}.', state=self.snapshot())
        )

    def collect(self, clue: str) -> None:
        if self.entities["collection"].meters["count"] >= 3:
            raise StoryError("The collection already has every planned clue.")
        self.entities["collection"].meters["count"] += 1
        self.entities["collection"].beliefs[f"clue_{self.entities['collection'].meters['count']}"] = clue

    def catch_visitor(self) -> None:
        visitor = self.entities["visitor"]
        if visitor.location != "feeding_stone":
            raise StoryError("The visitor must be lured to the feeding stone before it can be caught.")
        if self.entities["bell"].location != "feeding_stone":
            raise StoryError("The bell must be found before the mystery can be closed.")
        visitor.meters["caught"] = 1
        visitor.memes["fear"] = 0.0

    def feed_visitor(self, pieces: int) -> None:
        food = self.entities["food"]
        visitor = self.entities["visitor"]
        if visitor.meters["caught"] != 1:
            raise StoryError("The visitor must be safely caught before feeding.")
        if pieces <= 0 or pieces > food.meters["pieces"] - food.meters["fed"]:
            raise StoryError("There is not enough food for that feeding.")
        food.meters["fed"] += pieces
        visitor.meters["fed"] += pieces
        visitor.memes["hunger"] = 0.0


def validate_params(params: StoryParams) -> None:
    if params.hero == params.helper:
        raise StoryError("The two investigators must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Use simple capitalized names, such as Luna and Pip.")
    if params.clue not in CLUES:
        raise StoryError("Choose a registered clue.")
    if params.visitor not in VISITORS:
        raise StoryError("Choose a registered visitor.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either listen or rush.")
    if params.item not in ITEMS:
        raise StoryError("Choose a registered bell.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    clue_text, _ = CLUES[params.clue]
    world.entities["first_clue"] = Entity(
        "first_clue", clue_text, "clue", "garden",
        memes={"useful": 0.4},
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    animal, animal_sound = VISITORS[params.visitor]
    clue_text, clue_color = CLUES[params.clue]
    item = params.item

    world.narrate(
        "beginning",
        f"At dusk, {hero} reached the garden gate and pulled the cord. "
        f"The {item} should have answered, but the gate stayed silent.",
        sound="ting... silence",
        question="What first showed that something was wrong?",
        cause=f"The {item} usually rang when the gate cord moved.",
        result="That evening, the gate gave no bell sound.",
    )
    world.say("hero", f"The {item} is missing.")
    world.say("helper", "Then we should look for what it left behind.")
    world.say("hero", "I will check the path.")
    world.say("helper", "And I will listen near the shed.")

    if params.approach == "rush":
        world.narrate(
            "false_start",
            f"{hero} hurried across the stones. Clatter! A tin cup rolled under a bench, "
            f"but it was only a cup.",
            sound="CLATTER!",
            question="Why was the tin cup not the answer?",
            cause="It rolled when Luna hurried past, not when the missing bell rang.",
            result="The investigators learned that a loud sound could still be an ordinary accident.",
        )
        world.say("hero", "I nearly chased a cup.")
        world.say("helper", "A mystery needs a clue, not just a noise.")
    else:
        world.narrate(
            "listening",
            f"{hero} and {helper} stood still. Far beyond the hedge came a tiny scrape, "
            f"then three soft taps.",
            sound="scrape... tap, tap, tap",
            question="What did careful listening reveal?",
            cause="A small sound came from the feeding stone beyond the hedge.",
            result="The friends decided to investigate that place instead of guessing.",
        )
        world.say("hero", "That sound came from the feeding stone.")
        world.say("helper", "Then our feet should follow our ears.")

    world.narrate(
        "first_clue",
        f"Near the hedge, they found {clue_text} caught on a thorn. "
        f"It matched the {clue_color} thread tied around the bell cord.",
        sound="snip",
        question="Why did the first clue matter?",
        cause=f"The {clue_text} matched the thread beside the empty bell hook.",
        result="The friends knew the missing bell had passed near the hedge.",
    )
    world.collect(clue_text)
    world.say("hero", "This belongs in our collection.")
    world.say("helper", "A collection helps us compare clues instead of forgetting them.")

    world.narrate(
        "second_clue",
        f"Under the thorn bush, {hero} found a damp trail of apple crumbs leading "
        f"toward the feeding stone.",
        sound="crick",
        question="What did the crumbs suggest?",
        cause="The crumbs made a path from the shed toward the feeding stone.",
        result=f"They suspected a hungry {animal} had carried something that way.",
    )
    world.collect("apple crumbs")
    world.say("hero", f"Someone hungry walked this trail.")
    world.say("helper", f"Then we should offer food and wait for the {animal} to return.")

    world.narrate(
        "third_clue",
        f"At the feeding stone, the friends found a round mark in the mud and a bent "
        f"piece of cord beside it.",
        sound="plop",
        question="How did the third clue strengthen their idea?",
        cause="The muddy mark was beside the bent cord and the crumb trail.",
        result=f"The clues pointed to a small {animal}, not a person pulling the gate.",
    )
    world.collect("muddy paw mark")
    world.entities["visitor"].location = "feeding_stone"
    world.entities["bell"].location = "feeding_stone"
    world.entities["bell"].meters["hidden"] = 0
    world.say("hero", f"The {animal} carried the bell here.")
    world.say("helper", "We can find out without frightening it.")

    world.entities["food"].location = "feeding_stone"
    world.narrate(
        "lure",
        f"They placed three apple pieces beside the stone and hid behind the rain barrel. "
        f"The {animal} crept out, dragging the {item} by its cord.",
        sound=f"{animal_sound}... jingle",
        question="How did the friends make the visitor appear?",
        cause="They placed apple pieces at the feeding stone where the crumb trail ended.",
        result=f"The hungry {animal} came out while the friends watched quietly.",
    )
    world.say("hero", "There it is!")
    world.say("helper", "Slowly. Let it see that we brought food.")

    world.catch_visitor()
    world.narrate(
        "catch",
        f"{hero} lowered a soft basket over the {animal}. It was a gentle catch, "
        f"with plenty of air and room to blink.",
        sound="whoosh... thump",
        question="Why was the catch gentle?",
        cause=f"The {animal} was hungry and frightened, so the friends used a soft basket instead of chasing it.",
        result="The visitor stayed safe while they checked the missing bell.",
    )
    world.say("hero", "The bell is not broken.")
    world.say("helper", "It was pulled loose by the cord. We can return it after we help our guest.")

    world.feed_visitor(2)
    world.entities["visitor"].location = "garden"
    world.entities["bell"].location = "gate"
    world.entities["bell"].meters["hidden"] = 0
    world.entities["bell"].meters["ringed"] = 1
    world.narrate(
        "resolution",
        f"They fed the {animal} two apple pieces, released it beside the hedge, "
        f"and tied the {item} back to the gate.",
        sound="crunch, crunch... jingle!",
        question="How did the friends solve both parts of the mystery?",
        cause=f"They fed the hungry {animal} and returned the {item} to its hook.",
        result="The visitor left safely, and the gate could ring again.",
    )
    world.say("hero", "A mystery can end with kindness.")
    world.say("helper", "And with one last sound.")

    world.narrate(
        "ending",
        f"The {animal} vanished into the moonlit grass. {hero} pulled the gate cord, "
        f"and the {item} sang over the quiet garden while the three collected clues rested on the table.",
        sound="JINGLE!",
        question="What proved that the mystery was finished?",
        cause=f"The {item} was back on the gate, and the {animal} had been fed and released.",
        result="The bell rang over the garden while the clue collection told the whole story.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "What does a collection do in this mystery?",
                "It keeps the silver clue, apple crumbs, and muddy paw mark together so the friends can compare them.",
            ),
            QAItem(
                "Why did the friends feed the visitor?",
                f"They fed the {animal} because it was hungry, and kindness helped them release it safely.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise StoryError("A generated sample must retain its world.")
    if world.entities["bell"].location != "gate":
        raise StoryError("The bell must return to the gate.")
    if world.entities["bell"].meters["ringed"] != 1:
        raise StoryError("The ending must include a ringing bell.")
    if world.entities["visitor"].meters["caught"] != 1:
        raise StoryError("The visitor must be caught before release.")
    if world.entities["visitor"].meters["fed"] != 2:
        raise StoryError("The visitor must receive the planned feeding.")
    if world.entities["collection"].meters["count"] != 3:
        raise StoryError("The complete clue collection must contain three clues.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 12:
        raise StoryError("The mystery needs a sustained back-and-forth exchange.")
    if len(sample.story_qa) < 6:
        raise StoryError("The story needs several cause-and-result questions.")
    if any(not qa.answer.strip() for qa in sample.story_qa):
        raise StoryError("Every story question needs a natural-language answer.")


def valid_combos() -> list[tuple[str, str]]:
    return [(clue, visitor) for clue in CLUES for visitor in VISITORS]


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("clue", clue) for clue in CLUES]
        + [fact("visitor", visitor) for visitor in VISITORS]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--clue", choices=tuple(CLUES))
    parser.add_argument("--visitor", choices=tuple(VISITORS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--item", choices=ITEMS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice(tuple(CLUES))
    visitor = args.visitor or rng.choice(tuple(VISITORS))
    hero = args.hero or "Luna"
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        clue=clue,
        visitor=visitor,
        approach=args.approach or rng.choice(APPROACHES),
        item=args.item or rng.choice(ITEMS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about registered clue and visitor pairs.")
    tested = 0
    for clue, visitor in valid_combos():
        for approach in APPROACHES:
            for item in ITEMS:
                generate(
                    StoryParams(
                        clue=clue,
                        visitor=visitor,
                        approach=approach,
                        item=item,
                        seed=777,
                    )
                )
                tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} ASP-compatible clue/visitor pairs.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for clue, visitor in valid_combos():
                for approach in APPROACHES:
                    params = StoryParams(
                        hero=args.hero or "Luna",
                        helper=args.helper or "Pip",
                        clue=clue,
                        visitor=visitor,
                        approach=args.approach or approach,
                        item=args.item or rng.choice(ITEMS),
                        seed=args.seed,
                    )
                    samples.append(generate(params))
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]

        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
