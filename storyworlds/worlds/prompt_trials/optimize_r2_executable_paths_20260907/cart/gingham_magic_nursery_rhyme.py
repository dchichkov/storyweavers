#!/usr/bin/env python3
"""Gingham Magic Cart: a nursery-rhyme story about choosing the right path."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve()
for parent in (_HERE.parents[3], _HERE.parents[4], _HERE.parents[5]):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
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
    hero: str = "Mabel"
    helper: str = "Pip"
    problem: str = "mud"
    solution: str = "moonstones"
    verse: str = "bells"
    seed: int = 777


NAMES = ("Mabel", "Pip", "Nell", "Tom", "Daisy", "Bram")
PROBLEMS = {
    "mud": "lift",
    "thorn": "cut",
    "dark": "light",
    "river": "float",
}
SOLUTIONS = {
    "moonstones": "lift",
    "silver_shears": "cut",
    "glow_ribbon": "light",
    "bubble_wheels": "float",
}
VERSES = {
    "bells": ("Ting-a-ling", "the bells rang bright"),
    "claps": ("Clap-clap", "small hands clapped twice"),
    "hums": ("Hummity-hum", "the hedges hummed low"),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p, need in PROBLEMS.items()
            for s, gift in SOLUTIONS.items() if need == gift]


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character",
                           memes={"courage": 0.4, "wonder": 0.5}),
            "helper": Entity("helper", params.helper, "character",
                             memes={"courage": 0.6, "trust": 0.5}),
            "cart": Entity("cart", "the gingham cart", "vehicle", "cottage",
                           meters={"wheels": 2, "load": 0, "magic": 1}),
            "path": Entity("path", "the little path", "place", "garden"),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, who: str, text: str, *, to=""):
        actor = self.entities[who]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {actor.label} {tag}.',
                                  speaker=who, listener=to, state=self.snapshot()))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(e.text for e in self.history),
            prompts=[PROMPT],
            story_qa=[QAItem(e.question, f"{e.cause} {e.result}")
                      for e in self.history if e.question],
            world_qa=[
                QAItem("What made the cart special?",
                       "Its magic could respond to the right helpful object."),
                QAItem("What cloth covered the cart?",
                       "A bright gingham cloth covered the cart."),
            ],
            world=self,
        )


PROMPT = ("Write a gentle nursery-rhyme story about a gingham cart whose magic "
          "helps two children solve a path problem by listening to one another.")


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError("That magical solution does not fit the chosen path problem.")
    if params.verse not in VERSES:
        raise StoryError("Unknown nursery-rhyme verse.")
    if params.hero == params.helper:
        raise StoryError("The two speakers need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.helper)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    problem = params.problem
    details = {
        "mud": ("a puddle of brown mud", "garden gate", 2),
        "thorn": ("a thorny hedge", "berry hill", 3),
        "dark": ("a dark tunnel", "moon meadow", 4),
        "river": ("a singing stream", "daisy field", 5),
    }
    obstacle, destination, measure = details[problem]
    world.entities["path"].label = obstacle
    world.entities["path"].location = "between cottage and " + destination
    world.entities["path"].meters = {"difficulty": measure, "cleared": 0}
    return world


def perform_solution(world: World):
    p = world.params
    cart = world.entities["cart"]
    path = world.entities["path"]
    if p.solution == "moonstones":
        world.narrate("action", f"{p.hero} placed three moonstones beneath the gingham cart.")
        cart.meters["load"] = 3
        path.meters["cleared"] = 2
        path.location = "garden gate"
        world.narrate("change", "The cart rose on a silver moonbeam and floated over the muddy puddle.",
                      question="How did the cart cross the mud?",
                      cause="Moonstones lifted the magic gingham cart.",
                      result="It floated over the puddle without sinking.")
    elif p.solution == "silver_shears":
        world.narrate("action", f"{p.helper} opened the silver shears beside the gingham cart.")
        path.meters["cleared"] = 3
        path.location = "berry hill"
        world.narrate("change", "Snip-snap! The shears trimmed a safe arch through the thorny hedge.",
                      question="How did the children pass the hedge?",
                      cause="The silver shears cut a safe arch through the thorns.",
                      result="The gingham cart rolled beneath the arch.")
    elif p.solution == "glow_ribbon":
        world.narrate("action", f"{p.hero} tied the glow ribbon to the gingham cart's handle.")
        cart.meters["load"] = 1
        path.meters["cleared"] = 4
        path.location = "moon meadow"
        world.narrate("change", "The ribbon shone like a tiny dawn and lit the dark tunnel.",
                      question="What made the tunnel safe to cross?",
                      cause="The glow ribbon turned the cart into a bright moving lantern.",
                      result="Both children could see the tunnel walls and walk through.")
    else:
        world.narrate("action", f"{p.helper} fastened bubble wheels to the gingham cart.")
        cart.meters["load"] = 2
        path.meters["cleared"] = 5
        path.location = "daisy field"
        world.narrate("change", "Round bubble wheels bounced the cart across the singing stream.",
                      question="How did the cart cross the stream?",
                      cause="Bubble wheels lifted it above the rushing water.",
                      result="The cart bobbed safely to the daisy field.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    p = params
    h, f = p.hero, p.helper
    verse, verse_tail = VERSES[p.verse]
    world.narrate("beginning",
                  f"{h} and {f} found a little gingham cart by the cottage door. "
                  f"{verse}, {verse_tail}; its magic handle shone like a star.")
    world.say("hero", "The cart can carry our picnic to the far garden.")
    world.say("helper", "But the path has a problem today.")
    world.narrate("problem",
                  f"Before them lay {world.entities['path'].label}. "
                  f"The gingham cart stopped with a tiny magical shiver.")
    world.say("hero", "I know a way. We can push very hard.")
    world.say("helper", "Hard pushing may not be the right magic. What do we know?")
    clue_text = {
        "mud": "Moonstones lift things that are stuck.",
        "thorn": "Silver shears cut only what is safe to cut.",
        "dark": "A glow ribbon shows a kindly path.",
        "river": "Bubble wheels float over singing water.",
    }[p.problem]
    world.say("helper", clue_text)
    world.say("hero", "Then let us try the helpful thing, not the biggest thing.")
    world.entities["hero"].beliefs["clue"] = p.solution
    world.entities["helper"].beliefs["clue"] = p.solution
    world.narrate("decision",
                  f"They listened to the clue and chose the {p.solution.replace('_', ' ')}.",
                  question="Why did the children change their first plan?",
                  cause=f"{f} knew that the {p.solution.replace('_', ' ')} matched the path's problem.",
                  result=f"{h} agreed to use that gentle magic instead of pushing the cart.")
    perform_solution(world)
    world.say("helper", f"{verse}! It worked just as the clue said.")
    world.say("hero", "Your knowing made my doing wiser.")
    world.narrate("ending",
                  f"At the far garden, {h} and {f} shared the picnic. "
                  f"The gingham cart rested beside them, its magic handle glowing softly. "
                  f"{verse}, {verse_tail}, and the safe path curled home like a ribbon.",
                  question="What showed that their plan succeeded?",
                  cause=f"The {p.solution.replace('_', ' ')} solved the {p.problem} problem.",
                  result="The cart reached the far garden, and both children arrived safely.")
    check_sample(world.sample())
    return world.sample()


def check_sample(sample: StorySample):
    world = sample.world
    p = world.params
    if world.entities["path"].meters.get("cleared", 0) <= 0:
        raise StoryError("The chosen action must change the path.")
    if world.entities["path"].location not in ("garden gate", "berry hill",
                                                "moon meadow", "daisy field"):
        raise StoryError("The cart must reach its destination.")
    speech = [e for e in world.history if e.kind == "speech"]
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "helper" for e in speech):
        raise StoryError("Both characters must speak.")
    if not any("?" in e.text for e in speech):
        raise StoryError("The story needs a spoken question.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if re.search(r"\{[^}]+\}", sample.story):
        raise StoryError("Unresolved template text found.")


ASP_RULES = """
compatible(P,S) :- problem(P,Need), solution(S,Need).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("problem", p, need) for p, need in PROBLEMS.items()] +
        [fact("solution", s, gift) for s, gift in SOLUTIONS.items()]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "compatible"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--verse", choices=tuple(VERSES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    choices = [(p, s) for p, s in valid_combos()
               if args.problem is None or p == args.problem
               if args.solution is None or s == args.solution]
    if not choices:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(hero, helper, problem, solution,
                         args.verse or rng.choice(tuple(VERSES)), args.seed)
    validate_params(params)
    return params


def verify():
    if asp_combos() != set(valid_combos()):
        raise StoryError("Python and ASP compatibility facts disagree.")
    count = 0
    for problem, solution in valid_combos():
        for verse in VERSES:
            sample = generate(StoryParams(problem=problem, solution=solution, verse=verse))
            check_sample(sample)
            count += 1
    print(f"OK: {count} executable paths checked.")


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
            params_list = [
                StoryParams(hero=args.hero or NAMES[0],
                            helper=args.helper or NAMES[1],
                            problem=p, solution=s,
                            verse=args.verse or v, seed=args.seed)
                for p, s in valid_combos()
                for v in VERSES
            ]
            for item in params_list:
                validate_params(item)
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(p) for p in params_list]
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
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
