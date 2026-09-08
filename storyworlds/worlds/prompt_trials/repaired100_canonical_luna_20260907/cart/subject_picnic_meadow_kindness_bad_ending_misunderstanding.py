#!/usr/bin/env python3
"""The Vanishing Basket: a picnic-meadow mystery about kindness and a mistake.

A small mystery unfolds when a picnic basket seems to disappear. A hurried
assumption makes the ending briefly bad, but careful listening and kindness
repair what the misunderstanding damaged.
"""

from __future__ import annotations

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
    question: str = ""
    cause: str = ""
    result: str = ""
    speaker: str = ""
    listener: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    object_name: str = "basket"
    clue: str = "blue ribbon"
    approach: str = "listen"
    seed: int = 777


NAMES = ("Luna", "Milo", "Nora", "Theo", "Ivy", "Owen")
OBJECTS = {
    "basket": ("picnic basket", "sandwiches"),
    "tin": ("silver picnic tin", "apple slices"),
    "box": ("lunch box", "cheese crackers"),
}
CLUES = ("blue ribbon", "yellow feather", "round pebble")
APPROACHES = ("listen", "hurry")

PROMPT = (
    "Write a mystery-style children's story in which kindness repairs a "
    "misunderstanding during a picnic in a meadow."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                "hero",
                params.hero,
                "character",
                "blanket",
                memes={"curiosity": 1.0, "kindness": 0.7, "trust": 0.6},
            ),
            "friend": Entity(
                "friend",
                params.friend,
                "character",
                "blanket",
                memes={"worry": 0.6, "kindness": 0.8, "trust": 0.6},
            ),
            "meadow": Entity(
                "meadow",
                "picnic meadow",
                "place",
                "hill",
                meters={"wind": 0.4},
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
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(
        self,
        speaker: str,
        text: str,
        *,
        listener: str = "",
        reveal: str = "",
    ):
        if speaker not in self.entities:
            raise StoryError("A story speaker must be a known character.")
        actor = self.entities[speaker]
        if reveal:
            if reveal not in actor.beliefs:
                raise StoryError("A character cannot share a clue they do not know.")
            if not listener:
                raise StoryError("Shared information needs a listener.")
            self.entities[listener].beliefs[reveal] = actor.beliefs[reveal]
        label = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {label}.',
                speaker=speaker,
                listener=listener,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "What kind of place is this story set in?",
                    "It is set in a picnic meadow.",
                ),
                QAItem(
                    "What helped solve the mystery?",
                    "Kindness and careful listening helped solve the mystery.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.hero == params.friend:
        raise StoryError("The two characters must have different names.")
    for name in (params.hero, params.friend):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Use simple capitalized names, such as Luna and Milo.")
    if params.object_name not in OBJECTS:
        raise StoryError("Choose a known picnic object.")
    if params.clue not in CLUES:
        raise StoryError("Choose a known meadow clue.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either listening or hurrying as the approach.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    object_label, food = OBJECTS[params.object_name]
    world.entities["basket"] = Entity(
        "basket",
        f"the {object_label}",
        "food",
        "blanket",
        meters={"weight": 2.0, "distance_from_blanket": 0.0},
        memes={"importance": 0.8},
    )
    world.entities["clue"] = Entity(
        "clue",
        f"the {params.clue}",
        "clue",
        "blanket",
        meters={"size": 0.2},
    )
    world.entities["food"] = Entity(
        "food",
        food,
        "food",
        "basket",
        meters={"servings": 4.0},
    )
    return world


def move_basket(world: World, destination: str):
    basket = world.entities["basket"]
    if basket.location != "blanket":
        raise StoryError("The picnic container is not on the blanket.")
    basket.location = destination
    basket.meters["distance_from_blanket"] = 3.0 if destination == "oak_tree" else 1.0


def check_ending(world: World):
    basket = world.entities["basket"]
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    if basket.location != "blanket":
        raise StoryError("The picnic basket must return to the blanket.")
    if hero.memes["kindness"] < 1.0 or friend.memes["kindness"] < 1.0:
        raise StoryError("The repaired ending must show kindness from both friends.")
    if hero.beliefs.get("truth") != "basket_under_oak":
        raise StoryError("The hero must learn where the basket really went.")
    if friend.beliefs.get("truth") != "basket_under_oak":
        raise StoryError("The friend must learn where the basket really went.")
    if world.entities["food"].location != "basket":
        raise StoryError("The picnic food must remain with the basket.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    basket = world.entities["basket"]
    clue = world.entities["clue"]
    h, f = hero.label, friend.label
    object_label, food = OBJECTS[params.object_name]

    world.narrate(
        "beginning",
        f"{h} and {f} spread a yellow blanket in the picnic meadow. "
        f"The {object_label} held {food}, and a {params.clue} rested beside it.",
    )
    world.say("hero", "The meadow is perfect for lunch.")
    world.say("friend", "I will keep an eye on the food while you find the cups.")
    world.narrate(
        "discovery",
        f"When {h} came back with the cups, the {object_label} was gone. "
        f"Only the {params.clue} remained beside the blanket.",
        question="What first made the picnic feel like a mystery?",
        cause=f"The {object_label} had vanished from the blanket while {h} was fetching cups.",
        result=f"Only the {params.clue} was left behind.",
    )
    world.say("hero", "Someone took our picnic basket!")
    world.say("friend", "I did not see anyone take it.")

    if params.approach == "hurry":
        hero.memes["kindness"] -= 0.2
        friend.memes["worry"] += 0.4
        world.say("hero", "You were watching. You must have moved it.")
        world.say("friend", "I was watching the blanket, not the whole meadow.")
        world.narrate(
            "bad_ending",
            f"{h} hurried away from the blanket, certain that {f} had hidden the {object_label}. "
            f"{f} sat alone under a low cloud of worry.",
            question="Why did the first search make things worse?",
            cause=f"{h} blamed {f} before asking what had happened.",
            result=f"{f} felt hurt, and the friends searched separately.",
        )
        world.say("friend", "I only wanted to keep the ants away.")
        world.say("hero", "Then why is the basket under the oak tree?")
        world.say("friend", "It is not under the oak tree. I never carried it there.")
        world.narrate(
            "turn",
            f"The sharp words stopped when {h} noticed a line of bent grass leading toward the oak tree. "
            f"The {params.clue} had caught on a basket handle.",
        )
    else:
        hero.beliefs["question"] = "ask_before_blame"
        friend.beliefs["question"] = "ask_before_blame"
        world.say("hero", "Before we guess, what did you notice?")
        world.say("friend", "A gust lifted the blue napkin. I moved the blanket corner, but not the basket.")
        world.narrate(
            "investigation",
            f"They knelt together and followed the bent grass instead of pointing fingers. "
            f"Near the blanket, {h} found a shallow track in the soft meadow soil.",
            question="How did the friends begin a fair search?",
            cause=f"They asked what each person had seen before making an accusation.",
            result="They searched together and looked for physical clues.",
        )
        world.say("hero", "The grass bends toward the oak tree.")
        world.say("friend", "And the ribbon is caught on something. Let us follow it.")
        world.narrate(
            "turn",
            f"The {params.clue} tugged gently in the breeze, making a tiny blue signal from the blanket to the oak tree.",
        )

    clue.location = "path_to_oak"
    hero.beliefs["clue"] = "ribbon_points_to_oak"
    world.say(
        "hero",
        "The clue points to the oak tree. Will you come with me?",
        listener="friend",
    )
    world.say(
        "friend",
        "Yes. I want to solve this with you, not against you.",
        listener="hero",
    )
    world.narrate(
        "search",
        f"Behind the oak tree they found the {object_label}, tipped safely against the trunk. "
        f"The wind had pulled its handle along the grass.",
        question="Where did the missing picnic container go?",
        cause="A strong gust caught its handle and dragged it across the meadow.",
        result=f"It stopped safely beneath the oak tree.",
    )
    basket.location = "oak_tree"
    basket.meters["distance_from_blanket"] = 3.0
    hero.beliefs["truth"] = "basket_under_oak"
    friend.beliefs["truth"] = "basket_under_oak"
    world.say("friend", "The basket moved by itself. You were right to notice the clue.")
    world.say("hero", "I was wrong to blame you. I am sorry.")
    hero.memes["kindness"] = 1.0
    friend.memes["kindness"] = 1.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    world.narrate(
        "repair",
        f"{f} accepted the apology, and {h} lifted the {object_label} carefully. "
        f"Together they carried it back to the blanket.",
        question="How did kindness repair the misunderstanding?",
        cause=f"{h} apologized for blaming {f}, and {f} accepted the apology.",
        result="They carried the basket back together instead of staying angry.",
    )
    move_basket(world, "blanket")
    world.narrate(
        "ending",
        f"The picnic ended beneath the open sky. {food.capitalize()} were shared from the returned basket, "
        f"and the {params.clue} was tied to its handle so the friends could remember the meadow mystery.",
        question="What changed by the end of the story?",
        cause="The friends discovered that wind, not either friend, had moved the basket.",
        result="They trusted each other again and shared lunch beside the oak tree.",
    )

    check_ending(world)
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 10:
        raise StoryError("The mystery needs a sustained back-and-forth conversation.")
    if sum(event.speaker == "hero" for event in speeches) < 4:
        raise StoryError("The hero needs several speaking turns.")
    if sum(event.speaker == "friend" for event in speeches) < 4:
        raise StoryError("The friend needs several speaking turns.")
    if not any(event.question for event in world.history):
        raise StoryError("The story needs grounded questions and answers.")
    if "sorry" not in sample.story.lower():
        raise StoryError("The repaired misunderstanding needs a clear apology.")
    if any(token in sample.story for token in ("hero", "friend", "{", "}")):
        raise StoryError("Internal labels or unresolved template fields leaked into prose.")


ASP_RULES = """
compatible(A,B) :- approach(A), clue(B).
kindness_repair :- compatible(_, _).
#show compatible/2.
#show kindness_repair/0.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [fact("approach", approach) for approach in APPROACHES]
        + [fact("clue", clue.replace(" ", "_")) for clue in CLUES]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(symbols, "compatible"))


def check_asp():
    expected = {
        (approach, clue.replace(" ", "_"))
        for approach in APPROACHES
        for clue in CLUES
    }
    actual = asp_combos()
    if actual != expected:
        raise StoryError("Python and ASP disagree about valid mystery combinations.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--object-name", choices=tuple(OBJECTS))
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        hero=hero,
        friend=friend,
        object_name=args.object_name or rng.choice(tuple(OBJECTS)),
        clue=args.clue or rng.choice(CLUES),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    check_asp()
    tested = 0
    for approach in APPROACHES:
        for clue in CLUES:
            sample = generate(
                StoryParams(
                    hero="Luna",
                    friend="Milo",
                    object_name="basket",
                    clue=clue,
                    approach=approach,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP and Python agree.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
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
            check_asp()
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for approach in APPROACHES:
                for clue in CLUES:
                    params = StoryParams(
                        hero=args.hero or "Luna",
                        friend=args.friend or "Milo",
                        object_name=args.object_name or "basket",
                        clue=clue,
                        approach=approach,
                        seed=args.seed,
                    )
                    samples.append(generate(params))
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(args.n)
            ]

        if args.json:
            payloads = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payloads[0] if len(payloads) == 1 else payloads,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=(
                        f"\n### Story {index + 1}\n"
                        if len(samples) > 1
                        else ""
                    ),
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
