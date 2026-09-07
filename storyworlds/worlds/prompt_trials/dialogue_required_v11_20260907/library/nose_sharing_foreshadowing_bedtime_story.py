#!/usr/bin/env python3
"""The Lantern Nose: a gentle bedtime story about sharing and a small clue."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child: str = "Mara"
    sibling: str = "Pip"
    animal: str = "hedgehog"
    treasure: str = "moonberry"
    seed: int = 777


NAMES = ("Mara", "Pip", "Nia", "Tomas", "Lena", "Sol")
ANIMALS = {
    "hedgehog": ("a small hedgehog", "snuffled", "a warm nest"),
    "rabbit": ("a sleepy rabbit", "twitched", "a ferny burrow"),
    "fox": ("a silver fox", "rustled", "a quiet hollow"),
}
TREASURES = {
    "moonberry": ("a moonberry", "blue as a tiny night sky", "sweet moonberry jam"),
    "starstone": ("a starstone", "bright as a fallen star", "sparkling star-stone tea"),
    "honeydrop": ("a honeydrop", "golden and round", "warm honey toast"),
}


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity("child", params.child, "character", "bedroom",
                            memes={"hope": 1.0, "trust": 0.5}),
            "sibling": Entity("sibling", params.sibling, "character", "bedroom",
                              memes={"hope": 0.5, "trust": 0.5}),
            "nose": Entity("nose", "the little nose", "body", "bedroom",
                           meters={"scent": 0.0}),
            "basket": Entity("basket", "the sharing basket", "container", "bedroom",
                             meters={"contents": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def say(self, speaker: str, text: str):
        if not text.endswith((".", "?", "!")):
            text += "."
        self.history.append(Event("speech", f'"{text}" said {self.entities[speaker].label}.',
                                  state=self.snapshot()))

    def share(self):
        basket = self.entities["basket"]
        if basket.meters["contents"] < 2:
            raise StoryError("The sharing basket needs both portions before the treasure can be shared.")
        self.entities["child"].memes["trust"] = 1.0
        self.entities["sibling"].memes["trust"] = 1.0
        basket.meters["shared"] = 1
        self.entities["child"].meters["treasure_received"] = 1
        self.entities["sibling"].meters["treasure_received"] = 1

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("Why is sharing helpful at bedtime?",
                       "Sharing lets everyone enjoy a small good thing together."),
                QAItem("What can a nose notice?",
                       "A nose can notice scents that may offer a clue about what is nearby.")
            ],
            world=self,
        )


PROMPT = "Write a gentle bedtime story about two children sharing a treasure after following a clue from a nose."


def validate_params(params: StoryParams):
    if params.animal not in ANIMALS or params.treasure not in TREASURES:
        raise StoryError("Choose a known bedtime animal and treasure.")
    if params.child == params.sibling:
        raise StoryError("The two children must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.child, params.sibling)):
        raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    animal, sound, nest = ANIMALS[params.animal]
    item, color, treat = TREASURES[params.treasure]
    world.entities["animal"] = Entity("animal", animal, "animal", "garden",
                                      memes={"calm": 0.5})
    world.entities["treasure"] = Entity("treasure", item, "food", "garden",
                                        meters={"portions": 0},
                                        memes={"color": 1.0})
    world.entities["child"].meters["scent"] = 0
    world.entities["sibling"].meters["scent"] = 0
    world.narrate("setup",
                  f"{params.child} and {params.sibling} were getting ready for bed. "
                  f"On the windowsill sat {item}, {color}, in a little sharing basket.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    p = params
    item, color, treat = TREASURES[p.treasure]
    animal, sound, nest = ANIMALS[p.animal]
    c, s = p.child, p.sibling

    world.say("child", f"I found {item}. I want to keep it beside my pillow")
    world.say("sibling", "I want to see it too. Maybe it can make our dreams bright")
    world.narrate(
        "tension",
        f"{c} held {item} close, while {s} watched from the other side of the bed. "
        f"Then {c}'s nose began to wiggle. It smelled something sweet near the open window.",
        question="Why did the children stop arguing about the treasure?",
        cause=f"{c}'s nose noticed a sweet scent near the window.",
        result="The scent gave them a reason to investigate together.",
    )
    world.entities["nose"].meters["scent"] = 1
    world.entities["child"].meters["scent"] = 1
    world.entities["sibling"].meters["scent"] = 1

    world.say("child", "My nose smells something. Will you come and check it with me")
    world.say("sibling", "Yes. I will bring the basket, and you can lead with your nose")
    world.narrate(
        "foreshadowing",
        f"They followed the scent across the moonlit room and out to the garden. "
        f"Behind a pot, {animal} {sound} beside a tiny empty bowl.",
        question="What clue led the children to the garden?",
        cause=f"Their noses followed the sweet scent from the window.",
        result=f"They found {animal} beside an empty bowl.",
    )

    world.say("child", f"It looks hungry. I think {item} should not stay only with me")
    world.say("sibling", "Then let us share it with our new friend, and with each other")
    world.entities["treasure"].meters["portions"] = 2
    world.entities["basket"].meters["contents"] = 2

    world.narrate(
        "turn",
        f"{c} carefully split {item} into two portions. One went into the bowl for "
        f"{animal}; the other rested in the basket between the children. "
        f"The little nose of the visitor twitched happily.",
        question="How did the children help the hungry animal?",
        cause=f"They divided {item} instead of keeping it for one child.",
        result=f"One portion went into the animal's bowl, and the other stayed for sharing.",
    )

    world.say("child", "You may have the first bite")
    world.say("sibling", "Only if you have the first bite with me")
    world.share()
    world.narrate(
        "resolution",
        f"They ate the remaining portion together. The garden grew quiet, and {animal} "
        f"curled beside the bowl. The scent of {treat} drifted through the soft night air.",
        question="What changed when the children shared?",
        cause="They gave one portion away and invited each other to enjoy the other portion.",
        result="The animal was fed, and both children felt happy instead of worried about ownership.",
    )
    world.say("child", "Your nose found a friend for us tonight")
    world.say("sibling", "And sharing found room for everyone")
    world.narrate(
        "ending",
        f"Back in bed, the children placed the empty basket between their pillows. "
        f"Outside, {animal} slept safely in {nest}. The two little noses pointed toward "
        "the same quiet dream.",
        question="What was the bedtime lesson?",
        cause="The children listened to a clue and chose to share what they had.",
        result="Their small treasure became a kindness that included everyone.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if not world.entities["basket"].meters.get("shared"):
        raise StoryError("The treasure must be shared.")
    if world.entities["animal"].location != "garden":
        raise StoryError("The animal must remain in the garden.")
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 8:
        raise StoryError("The bedtime story needs a sustained exchange.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs grounded questions and answers.")
    if not any("nose" in e.text.lower() for e in world.history):
        raise StoryError("The nose must matter to the story.")


PROBLEMS = {"hunger": "share_treasure", "lonely": "share_treasure"}
SOLUTIONS = {"share": "share_treasure"}

ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("problem", key, value) for key, value in PROBLEMS.items()]
        + [fact("solution", key, value) for key, value in SOLUTIONS.items()]
    )


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p, need in PROBLEMS.items()
            for s, capability in SOLUTIONS.items() if need == capability]


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--sibling")
    parser.add_argument("--animal", choices=tuple(ANIMALS))
    parser.add_argument("--treasure", choices=tuple(TREASURES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    sibling = args.sibling or rng.choice([n for n in NAMES if n != child])
    params = StoryParams(
        child=child,
        sibling=sibling,
        animal=args.animal or rng.choice(tuple(ANIMALS)),
        treasure=args.treasure or rng.choice(tuple(TREASURES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree.")
    tested = 0
    for animal in ANIMALS:
        for treasure in TREASURES:
            sample = generate(StoryParams(animal=animal, treasure=treasure))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} compatible pairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + ASP_RULES)
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
            for animal in ANIMALS:
                for treasure in TREASURES:
                    samples.append(generate(StoryParams(
                        child=args.child or "Mara",
                        sibling=args.sibling or "Pip",
                        animal=animal,
                        treasure=treasure,
                        seed=args.seed,
                    )))
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
