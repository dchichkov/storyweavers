#!/usr/bin/env python3
"""Toggle County: Luna and a dull magic superhero repair a dark town sign."""

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
    speaker: str = ""
    listener: str = ""
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    partner: str = "Milo"
    problem: str = "dull"
    magic: str = "lantern"
    method: str = "listen"
    seed: int = 777


NAMES = ("Luna", "Milo", "Nia", "Theo", "Pip", "Zara")
PROBLEMS = {"dull": "polish", "dim": "toggle", "crooked": "straighten"}
MAGICS = {
    "lantern": "the moon-lantern",
    "cape": "the silver cape",
    "bell": "the star bell",
}
METHODS = ("listen", "rush")
PROMPT = (
    "Write a dialogue-rich children's superhero story about Luna helping a county "
    "repair a dull magic signal by listening before using her power."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "county_square",
                memes={"courage": 1.0, "patience": 0.4, "trust": 0.5},
            ),
            "partner": Entity(
                "partner", params.partner, "character", "county_square",
                memes={"worry": 0.7, "trust": 0.5},
            ),
            "county": Entity(
                "county", "Toggle County", "place", "hill",
                meters={"safe": 0, "lights": 0},
            ),
            "signal": Entity(
                "signal", "the magic signal", "device", "clock_tower",
                meters={"brightness": 0, "toggle": 0, "aligned": 0},
                memes={"hope": 0.2},
                beliefs={"message": "Kindness makes a bright signal."},
            ),
            "magic": Entity(
                "magic", MAGICS[params.magic], "magic", "hero",
                meters={"charge": 1, "uses": 0},
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
        to: str = "",
        reveal: str = "",
        tag: str = "said",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a secret they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        if text.endswith("."):
            text = text[:-1] + ","
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {tag}.',
                speaker=speaker,
                listener=to,
                revealed=reveal,
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
                    "What kind of place is Toggle County?",
                    "Toggle County is a small county whose town lights depend on a magic signal.",
                ),
                QAItem(
                    "What makes Luna a superhero?",
                    f"Luna uses {MAGICS[self.params.magic]} to help people, but she also listens before acting.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS:
        raise StoryError("The selected county problem is unknown.")
    if params.magic not in MAGICS:
        raise StoryError("Choose a known kind of Magic.")
    if params.method not in METHODS:
        raise StoryError("Choose either listening or rushing.")
    if params.hero == params.partner:
        raise StoryError("The superhero and partner need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.partner)):
        raise StoryError("Use simple capitalized names, such as Luna and Milo.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    signal = world.entities["signal"]
    if params.problem == "dull":
        signal.meters.update(brightness=1, toggle=0, aligned=1)
    elif params.problem == "dim":
        signal.meters.update(brightness=0, toggle=0, aligned=1)
    else:
        signal.meters.update(brightness=1, toggle=1, aligned=0)
    return world


def diagnose(world: World) -> str:
    signal = world.entities["signal"]
    if signal.meters["aligned"] == 0:
        return "crooked"
    if signal.meters["toggle"] == 0:
        return "dim"
    if signal.meters["brightness"] < 3:
        return "dull"
    return ""


def repair(world: World):
    signal = world.entities["signal"]
    magic = world.entities["magic"]
    problem = diagnose(world)
    if problem != world.entities["hero"].beliefs.get("problem"):
        raise StoryError("Luna must use the county's observed problem before repairing it.")
    if magic.meters["charge"] < 1:
        raise StoryError("The Magic has already been spent.")
    if problem == "dull":
        signal.meters["brightness"] = 3
    elif problem == "dim":
        signal.meters["toggle"] = 1
        signal.meters["brightness"] = 3
    else:
        signal.meters["aligned"] = 1
        signal.meters["brightness"] = 3
    magic.meters["charge"] = 0
    magic.meters["uses"] += 1
    signal.memes["hope"] = 1.0


def activate(world: World) -> bool:
    signal = world.entities["signal"]
    if diagnose(world):
        return False
    signal.meters["toggle"] += 1
    if signal.meters["toggle"] < 2:
        return False
    world.entities["county"].meters.update(safe=1, lights=1)
    return True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    partner = world.entities["partner"].label
    magic = MAGICS[params.magic]
    problem = diagnose(world)

    world.narrate(
        "beginning",
        f"In Toggle County, every porch lamp listened to the magic signal on the clock tower. "
        f"One evening the signal looked {problem}, and the county streets began to lose their glow. "
        f"{hero}, the county's young superhero, arrived with {magic}.",
    )
    world.say("hero", "I can save the county before the last light fades.")
    world.say("partner", "Please look closely first. The signal may be telling us what it needs.")

    if params.method == "rush":
        world.say("hero", "There is no time for looking. I will pour Magic into it now.")
        world.entities["magic"].meters["charge"] = 0
        world.narrate(
            "misfire",
            f"{hero} waved {magic}, but the tower answered with a tired puff of blue dust. "
            f"The signal stayed {problem}, and two more porch lamps went dark.",
        )
        world.say("partner", "Your power is strong, but power cannot fix a mystery.")
        world.say("hero", "Then tell me what I missed.")
        world.entities["magic"].meters["charge"] = 1
    else:
        world.say("hero", "What do you notice at the tower?")
        world.say("partner", "The light is not broken everywhere. Its little toggle is stuck halfway.")
        world.narrate(
            "inspection",
            f"{hero} and {partner} climbed the clock tower steps. They watched the county signal "
            f"blink once, pause, and fade instead of changing cleanly.",
        )

    world.entities["partner"].beliefs["problem"] = problem
    world.say(
        "partner",
        {
            "dull": "The glow is dull because the signal has forgotten how to gather its shine.",
            "dim": "The signal is dim because its toggle is stuck on one side.",
            "crooked": "The signal is crooked, so its magic points at the clouds instead of the county.",
        }[problem],
        to="hero",
        reveal="problem",
    )
    world.entities["hero"].beliefs["problem"] = problem

    if problem == "dull":
        world.say("hero", "Should I make it brighter by making the spell bigger?")
        world.say("partner", "No. Use a small shine and polish the cloudy glass.")
        world.say("hero", "You want Magic with a gentle hand.")
        world.say("partner", "Exactly. The county needs a clear signal, not a loud one.")
        repair(world)
        world.narrate(
            "repair",
            f"{hero} touched {magic} to the signal's cloudy glass. A soft silver spark polished "
            f"the dull surface until the hidden star inside could be seen.",
            question="Why did Luna use a small spell?",
            cause="The signal was dull because its cloudy surface hid its star.",
            result="She used a gentle Magic spark to polish the glass instead of making a louder spell.",
        )
    elif problem == "dim":
        world.say("hero", "May I move the toggle?")
        world.say("partner", "Yes, but move it once to the mark, not back and forth.")
        world.say("hero", "One careful click can help a whole county.")
        world.say("partner", "That is the kind of superhero lesson I like.")
        repair(world)
        world.narrate(
            "repair",
            f"{hero} placed {magic} beside the tiny toggle. The Magic nudged it to the bright mark "
            f"with one neat click.",
            question="What did Luna learn about the toggle?",
            cause="The signal was dim because its toggle was stuck halfway.",
            result="She moved the toggle once to the bright mark instead of shaking it back and forth.",
        )
    else:
        world.say("hero", "The tower points upward. Shall I turn it toward the county?")
        world.say("partner", "Yes, but hold the base while I read the arrow.")
        world.say("hero", "You guide the aim, and I will make the turn.")
        world.say("partner", "Together, the signal can point where it belongs.")
        repair(world)
        world.narrate(
            "repair",
            f"{partner} read the faded arrow while {hero} used {magic} to turn the signal's ring. "
            f"They aimed the beam down toward the homes of Toggle County.",
            question="How did the heroes aim the signal?",
            cause="The signal was crooked and pointed its Magic at the clouds.",
            result="Milo read the arrow while Luna turned the ring toward the county.",
        )

    world.say("partner", "Now test it with the county's real lights.")
    world.say("hero", "I will press the town toggle once, then wait.")
    if not activate(world):
        raise StoryError("The repaired signal did not activate the county.")
    world.narrate(
        "test",
        f"{hero} pressed the brass town toggle. The signal answered with two clear flashes, "
        f"and every porch lamp in Toggle County woke in the same warm color.",
        question="How did Luna test the repair?",
        cause="The repair needed to work with the county's actual light system.",
        result="She pressed the brass town toggle and watched two clear flashes wake every porch lamp.",
    )
    world.say("partner", "The county is bright again.")
    world.say("hero", "You saw the clue before I saw the answer.")
    world.say("partner", "And you listened when the clue changed your plan.")
    world.narrate(
        "ending",
        f"The dull tower now shone above Toggle County. {hero} clipped {magic} to a belt loop, "
        f"while {partner} painted a small listening ear beside the town toggle.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(world: World):
    county = world.entities["county"]
    signal = world.entities["signal"]
    if not county.meters["safe"] or not county.meters["lights"]:
        raise StoryError("The county must be safe and lit at the ending.")
    if signal.meters["brightness"] < 3 or signal.meters["toggle"] < 2:
        raise StoryError("The repaired signal must be bright and successfully tested.")
    if world.entities["magic"].meters["uses"] != 1:
        raise StoryError("Magic must be used once for the repair.")


ASP_RULES = """
repairable(P,S) :- problem(P,S).
#show repairable/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("problem", problem, solution) for problem, solution in PROBLEMS.items())


def asp_pairs() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "repairable"))


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speech = [event for event in sample.world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The superhero story needs a sustained back-and-forth exchange.")
    if not any(event.revealed for event in speech):
        raise StoryError("The dialogue must pass useful information between characters.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded questions and causal answers.")
    if any(not item.answer or "." not in item.answer for item in sample.story_qa):
        raise StoryError("Story answers must be full natural-language explanations.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--magic", choices=tuple(MAGICS))
    parser.add_argument("--method", choices=METHODS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    partner = args.partner or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        partner=partner,
        problem=args.problem or rng.choice(tuple(PROBLEMS)),
        magic=args.magic or rng.choice(tuple(MAGICS)),
        method=args.method or rng.choice(METHODS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_pairs() != set(PROBLEMS.items()):
        raise StoryError("Python and ASP disagree about repairable county problems.")
    tested = 0
    for problem in PROBLEMS:
        for magic in MAGICS:
            for method in METHODS:
                sample = generate(
                    StoryParams(problem=problem, magic=magic, method=method)
                )
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} superhero stories; {len(PROBLEMS)} ASP-compatible repairs.")


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
            print(json.dumps(sorted(asp_pairs())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            problems = (args.problem,) if args.problem else tuple(PROBLEMS)
            methods = (args.method,) if args.method else METHODS
            params_list = [
                resolve_params(
                    argparse.Namespace(
                        hero=args.hero,
                        partner=args.partner,
                        problem=problem,
                        magic=magic,
                        method=method,
                    ),
                    rng,
                )
                for problem in problems
                for magic in ((args.magic,) if args.magic else tuple(MAGICS))
                for method in methods
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
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
