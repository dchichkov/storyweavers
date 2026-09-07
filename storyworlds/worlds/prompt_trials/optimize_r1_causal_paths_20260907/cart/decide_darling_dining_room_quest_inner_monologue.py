#!/usr/bin/env python3
"""Decide, Darling: a small dining-room quest about choosing with care."""

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
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Nora"
    helper: str = "Aunt June"
    problem: str = "missing_guest"
    solution: str = "follow_clue"
    resource: str = "lantern"
    mood: str = "tender"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lena", "Owen", "Pia", "Sam")
HELPERS = ("Aunt June", "Grandpa Eli", "Uncle Tom")
PROBLEMS = {
    "missing_guest": "find_guest",
    "cold_soup": "warm_soup",
    "dark_table": "light_table",
    "empty_place": "make_place",
}
SOLUTIONS = {
    "follow_clue": "find_guest",
    "ask_neighbor": "find_guest",
    "stove": "warm_soup",
    "shared_candle": "light_table",
    "borrow_place": "make_place",
}
RESOURCES = ("lantern", "candle", "red_ribbon")
MOODS = ("tender", "hopeful", "bright")

ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "dining room",
                           memes={"courage": 0.5, "worry": 1.0}),
            "helper": Entity("helper", params.helper, "character", "dining room",
                             memes={"patience": 1.0, "trust": 0.5}),
            "table": Entity("table", "the dining table", "furniture", "dining room",
                            meters={"places": 4, "set_places": 3}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {k: asdict(v) for k, v in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, who: str, text: str, *, to=""):
        speaker = self.entities[who].label
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {speaker} {tag}.',
                                  speaker=who, listener=to, state=self.snapshot()))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(e.text for e in self.history),
            prompts=[PROMPT],
            story_qa=[QAItem(e.question, f"{e.cause} {e.result}")
                      for e in self.history if e.question],
            world_qa=[
                QAItem("Where did the quest take place?",
                       "It took place in the dining room."),
                QAItem("What helped the characters decide?",
                       "They listened to one another and used a concrete clue."),
            ],
            world=self,
        )


PROMPT = ("Write a heartwarming children's story set in a dining room. Include a "
          "quest, suspense, inner monologue, and a spoken conversation in which "
          "someone must decide what to do.")
OPENINGS = (
    "The dining room glowed softly as {hero} counted the spoons.",
    "Rain tapped the dining-room window while {hero} prepared the table.",
    "In the dining room, {hero} smoothed the cloth and listened to the quiet house.",
)
INNER = (
    "{hero} thought, *If I choose badly, someone may wait alone.*",
    "{hero} wondered, *A brave decision can begin with one small question.*",
    "{hero} thought, *The room feels safer when everyone has a place.*",
)
ENDINGS = (
    "The dining room filled with warm voices, and the once-empty chair no longer looked lonely.",
    "Candlelight danced across the table as every place held a bowl, a spoon, and a welcome.",
    "When supper began, {hero} smiled at the table because the right choice had made room for everyone.",
)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p, need in PROBLEMS.items()
            for s, solves in SOLUTIONS.items() if need == solves]


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(f"{params.solution!r} cannot solve {params.problem!r}.")
    if params.resource not in RESOURCES or params.mood not in MOODS:
        raise StoryError("Unknown resource or mood.")
    if params.hero == params.helper:
        raise StoryError("The two characters need different names.")
    if not re.fullmatch(r"[A-Z][a-z]+", params.hero):
        raise StoryError("The hero name must be a simple capitalized name.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["resource"] = Entity("resource", f"the {params.resource}",
                                        "tool", "dining room",
                                        meters={"brightness": 0.2 if params.resource == "candle" else 0.8})
    world.entities["guest"] = Entity("guest", "Grandma Rose", "character", "garden",
                                     memes={"belonging": 0.2})
    world.entities["soup"] = Entity("soup", "the soup", "food", "dining room",
                                    meters={"temperature": 0.3})
    world.entities["spare_place"] = Entity("spare_place", "a folded chair", "furniture",
                                           "hall", meters={"available": 1})
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    rng = random.Random(params.seed)
    h = params.hero
    helper = params.helper
    world.narrate("beginning", rng.choice(OPENINGS).format(hero=h) +
                  f" Tonight was {params.mood}, but one detail was not ready.")
    world.say("hero", "I want everyone to feel welcome.")
    world.say("helper", "Then we must notice what the table is telling us.")
    world.narrate("inner_monologue", rng.choice(INNER).format(hero=h))

    if params.problem == "missing_guest":
        world.say("hero", "Grandma Rose has not come in. Should I keep setting her place?")
        world.say("helper", "Decide, darling, but first look for a clue.")
        world.narrate("suspense", f"{h} found a damp red ribbon beneath the dining-room window.",
                      question="Why did they look for a clue before deciding?",
                      cause="Grandma Rose was missing, and the damp ribbon suggested she had gone outside.",
                      result=f"{h} chose to search instead of assuming the guest had stayed away.")
        world.say("hero", "The ribbon is wet. She may be in the garden.")
        world.say("helper", "Take the lantern. I will keep the soup warm.")
        world.entities["hero"].location = "garden"
        world.entities["guest"].location = "garden"
        world.entities["guest"].memes["belonging"] = 1.0
        world.narrate("quest", f"{h} carried the {params.resource} through the back door and found Grandma Rose beside the pear tree.",
                      question="How did the quest find Grandma Rose?",
                      cause="A damp ribbon led the search from the dining-room window to the garden.",
                      result=f"{h} found Grandma Rose and brought her safely to supper.")
        world.say("hero", "Grandma, we saved your chair.")
        world.say("helper", "And you found the person who belonged in it.")
        world.entities["hero"].location = "dining room"

    elif params.problem == "cold_soup":
        world.say("hero", "The soup is cold. Should I serve it anyway?")
        world.say("helper", "Decide, darling, but ask what the guests need.")
        world.say("hero", "Would everyone rather wait a little for warm soup?")
        world.say("helper", "Yes. The bread can keep us company.")
        world.narrate("quest", f"{h} carried the pot to the stove and stirred it slowly.",
                      question="Why did they wait before serving supper?",
                      cause="The soup was cold, so the guests agreed that warmth mattered more than speed.",
                      result="They warmed the soup while sharing bread.")
        world.entities["soup"].meters["temperature"] = 1.0
        world.say("hero", "Now it is steaming.")
        world.say("helper", "A patient choice can make a small meal feel grand.")
        world.narrate("turn", "The soup sent a fragrant cloud above the stove, and hungry smiles followed it.")

    elif params.problem == "dark_table":
        world.say("hero", "The room is dark. Should we eat in the kitchen?")
        world.say("helper", "Decide, darling, but see whether the table can share one light.")
        world.say("hero", "We can place the candle in the middle and sit close.")
        world.say("helper", "Then nobody will be left in a shadow.")
        world.narrate("quest", f"They moved the {params.resource} to the center of the table.",
                      question="How did they make the dining room bright enough?",
                      cause="The room was dim, but one shared light could reach everyone from the table's center.",
                      result="They gathered close and used the light together.")
        world.entities["resource"].meters["brightness"] = 1.0
        world.say("hero", "Look. The spoons are shining.")
        world.say("helper", "So are the faces around them.")
        world.narrate("turn", "The little flame trembled, then steadied as the family drew their chairs nearer.")

    else:
        world.say("hero", "There is one chair too few. Should I eat standing?")
        world.say("helper", "Decide, darling, but remember that a welcome can be built.")
        world.say("hero", "I will borrow the folded chair from the hall.")
        world.say("helper", "And I will carry it with you.")
        world.narrate("quest", f"Together they carried the folded chair from the hall into the dining room.",
                      question="Why did they fetch the folded chair?",
                      cause="There was not enough seating for every person at supper.",
                      result="They borrowed a chair so nobody had to stand or eat alone.")
        world.entities["table"].meters["set_places"] = 4
        world.entities["spare_place"].meters["available"] = 0
        world.say("hero", "Now every guest has a place.")
        world.say("helper", "That is a decision worth making.")
        world.narrate("turn", "The borrowed chair tucked neatly beneath the table, beside a waiting blue bowl.")

    world.entities["hero"].memes["courage"] = 1.0
    world.entities["hero"].memes["worry"] = 0.0
    world.narrate("ending", rng.choice(ENDINGS).format(hero=h),
                  question="What showed that the decision had worked?",
                  cause="The characters used a clue, listened to one another, and changed the dining room.",
                  result="The final table showed a practical welcome rather than an unfinished worry.")
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if len([e for e in world.history if e.kind == "speech"]) < 8:
        raise StoryError("The story needs a sustained spoken exchange.")
    speakers = {e.speaker for e in world.history if e.kind == "speech"}
    if speakers != {"hero", "helper"}:
        raise StoryError("Both characters must speak.")
    if not any(e.kind == "inner_monologue" for e in world.history):
        raise StoryError("The story needs an inner-monologue beat.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded questions and answers.")


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("problem", p, n) for p, n in PROBLEMS.items()] +
        [fact("solution", s, n) for s, n in SOLUTIONS.items()]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--resource", choices=RESOURCES)
    parser.add_argument("--mood", choices=MOODS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    combos = [(p, s) for p, s in valid_combos()
              if args.problem is None or p == args.problem
              if args.solution is None or s == args.solution]
    if not combos:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(combos)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(hero, helper, problem, solution,
                       args.resource or rng.choice(RESOURCES),
                       args.mood or rng.choice(MOODS), args.seed)


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree.")
    count = 0
    for problem, solution in valid_combos():
        for resource in RESOURCES:
            for mood in MOODS:
                generate(StoryParams(problem=problem, solution=solution,
                                     resource=resource, mood=mood))
                count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible paths.")


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
            "history": [asdict(e) for e in sample.world.history],
        }, indent=2))


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
            params = []
            for problem, solution in valid_combos():
                if args.problem and args.problem != problem:
                    continue
                if args.solution and args.solution != solution:
                    continue
                local = argparse.Namespace(**vars(args))
                local.problem, local.solution = problem, solution
                params.append(resolve_params(local, rng))
        else:
            params = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            data = [s.to_dict() for s in samples]
            print(json.dumps(data[0] if len(data) == 1 else data,
                             ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
