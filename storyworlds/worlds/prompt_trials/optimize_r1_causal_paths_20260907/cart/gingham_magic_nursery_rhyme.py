#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme tale of a little cart and a changing path."""

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
    hero: str = "Nell"
    helper: str = "Pip"
    problem: str = "bridge"
    solution: str = "ribbon"
    charm: str = "moon"
    weather: str = "rain"
    seed: int = 777


NAMES = ("Nell", "Pip", "Tess", "Bram", "Mina", "Roo")
PROBLEMS = {
    "bridge": "cross",
    "hill": "pull",
    "dark": "light",
    "wind": "anchor",
}
SOLUTIONS = {
    "ribbon": "cross",
    "bell": "cross",
    "feather": "pull",
    "song": "pull",
    "lantern": "light",
    "star": "light",
    "stone": "anchor",
    "knot": "anchor",
}
CHARMS = ("moon", "sun", "star")
WEATHERS = ("rain", "breeze", "mist")
PROMPT = (
    "Write a child-facing nursery-rhyme story about two friends using a magical "
    "gingham cart to solve a practical problem."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", memes={"courage": 0.6}),
            "helper": Entity("helper", params.helper, "character", memes={"courage": 0.7}),
            "cart": Entity(
                "cart",
                "the gingham cart",
                "vehicle",
                "yard",
                meters={"wheels": 2, "magic": 1, "load": 0},
                memes={"cheer": 0.5},
            ),
            "charm": Entity(
                "charm",
                f"the {params.charm} charm",
                "magic",
                "cart",
                memes={"glow": 0.5},
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

    def say(self, who: str, text: str, *, to: str = ""):
        if who not in self.entities:
            raise StoryError("A story speaker is missing from the world.")
        if not text.endswith((".", "?", "!")):
            raise StoryError("Spoken lines need punctuation.")
        verb = "asked" if text.endswith("?") else "cried" if text.endswith("!") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {self.entities[who].label} {verb}.',
                speaker=who,
                listener=to,
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
                    "What made the cart special?",
                    "Its gingham cloth carried a small magic that answered a kind, useful plan.",
                )
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("Unknown problem or magical solution.")
    if PROBLEMS[params.problem] != SOLUTIONS[params.solution]:
        raise StoryError(
            f"The {params.solution} charm cannot solve the {params.problem} problem."
        )
    if params.charm not in CHARMS or params.weather not in WEATHERS:
        raise StoryError("Unknown charm or weather.")
    if params.hero == params.helper:
        raise StoryError("The two friends must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Use simple capitalized names for the friends.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["cart"].meters["load"] = 1
    if params.problem == "bridge":
        world.entities["path"] = Entity(
            "path", "the brook path", "place", "yard", meters={"gap": 2}
        )
    elif params.problem == "hill":
        world.entities["path"] = Entity(
            "path", "the steep hill", "place", "yard", meters={"slope": 3}
        )
    elif params.problem == "dark":
        world.entities["path"] = Entity(
            "path", "the moonless lane", "place", "yard", meters={"light": 0}
        )
    else:
        world.entities["path"] = Entity(
            "path", "the windy meadow", "place", "yard", meters={"gust": 4}
        )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.helper
    cart = world.entities["cart"]
    charm = world.entities["charm"]

    openings = [
        f"{h} and {f} found a gingham cart at dawn, with a {params.charm} charm bright as a silver spoon.",
        f"By the nursery gate stood a little magic gingham cart, humming a tune for {h} and {f}.",
        f"{h} wore a red cap, {f} wore blue, and between them rolled a gingham cart with magic to do.",
    ]
    world.narrate(
        "beginning",
        random.Random(params.seed).choice(openings)
        + f" Inside lay one basket of warm buns for the children beyond the {world.entities['path'].label}.",
    )
    world.say("hero", "The buns must reach the nursery before noon.")
    world.say("helper", "Then we shall roll, and sing, and see what the cart can do.")

    if params.problem == "bridge":
        world.say("hero", "The brook has swallowed the little bridge.")
        world.say("helper", "A cart cannot leap water, however bright its wheels.")
        world.narrate(
            "obstacle",
            f"The {params.weather} had filled the brook until the path showed a gap of two skipping stones.",
            question="Why could the cart not take the usual path?",
            cause="Rain had widened the brook and broken the bridge.",
            result="The friends needed another way to cross with the buns.",
        )
        if params.solution == "ribbon":
            world.say("hero", "Could the gingham ribbon stretch from bank to bank?")
            world.say("helper", "Only if we tie it to a strong willow root.")
            world.say("hero", "I know a root beneath the bent willow.")
            charm.beliefs["method"] = "ribbon"
            world.say("helper", "Tie it there, and I will guide the cart along the bright line.")
            world.narrate(
                "turn",
                "They tied the gingham ribbon to the willow root. Magic shimmered through its checks, and it became a firm, shining rail.",
                question="What did the friends discover about the ribbon?",
                cause="They tied it to a strong willow root.",
                result="Its magic made a safe rail across the brook.",
            )
            cart.location = "far_bank"
            cart.meters["load"] = 0
            world.say("hero", "The wheels are over!")
            world.say("helper", "And the buns are dry!")
            world.narrate(
                "ending",
                "Across the brook the cart rolled, its gingham ribbon glowing from bank to bank like a striped rainbow.",
            )
        else:
            world.say("hero", "The bell may call the stepping stones awake.")
            world.say("helper", "Let us ring it softly, not loudly.")
            charm.beliefs["method"] = "bell"
            world.narrate(
                "turn",
                "Pip rang the little bell three times. Three broad stones rose from the brook, bobbing in a neat row.",
                question="How did the bell help them cross?",
                cause="Pip rang the magic bell softly three times.",
                result="Three stepping stones rose from the water for the cart.",
            )
            cart.location = "far_bank"
            cart.meters["load"] = 0
            world.say("hero", "One stone, two stones, three!")
            world.say("helper", "The nursery buns have crossed with us.")
            world.narrate(
                "ending",
                "The cart rested on the far bank, and three wet stones winked behind it beneath the gingham wheels.",
            )

    elif params.problem == "hill":
        world.say("hero", "The hill is steep, and the cart is full.")
        world.say("helper", "My arms are small. Your arms are small too.")
        world.narrate(
            "obstacle",
            "The road rose sharply, and the cart's wheels slipped backward on the damp grass.",
            question="Why did pulling harder fail?",
            cause="The hill was steep and the damp grass made the wheels slip.",
            result="The friends needed a lighter, kinder way to move the cart.",
        )
        if params.solution == "feather":
            world.say("hero", "The silver feather could make the cart light.")
            world.say("helper", "Then we must remove the basket before we lift it.")
            world.narrate(
                "turn",
                "They placed the feather beneath the cart, but kept the buns in the basket. The cart rose as light as a cloud.",
                question="What careful choice made the feather safe to use?",
                cause="They put the feather under the cart while keeping the buns steady in their basket.",
                result="The empty-looking cart floated uphill without spilling the buns.",
            )
            cart.location = "hilltop"
            cart.meters["load"] = 0
            world.say("hero", "Up it floats, with nary a crumb astray!")
            world.say("helper", "A light cart and careful friends make a fine parade.")
            world.narrate(
                "ending",
                "At the hilltop, the gingham cart settled softly, and its wheels made four tiny cloud-shaped prints.",
            )
        else:
            world.say("hero", "Perhaps the song can teach the wheels a marching beat.")
            world.say("helper", "I will sing the high notes; you sing the low.")
            world.narrate(
                "turn",
                "Together they sang, 'Trundle and tumble, turn and climb!' The cart's wheels found the beat and gripped the earth.",
                question="What did the friends learn about the magic song?",
                cause="They sang together in a steady marching rhythm.",
                result="The wheels followed the beat and climbed instead of slipping.",
            )
            cart.location = "hilltop"
            cart.meters["load"] = 0
            world.say("hero", "The hill has heard our nursery rhyme.")
            world.say("helper", "And the buns have heard it too.")
            world.narrate(
                "ending",
                "At the top, the cart hummed the last note, while the gingham cloth rippled like a little flag.",
            )

    elif params.problem == "dark":
        world.say("hero", "The lane is black as a closed-up room.")
        world.say("helper", "The buns cannot guide us if we cannot see them.")
        world.narrate(
            "obstacle",
            "Even the stars hid behind clouds, and the cart's two wheels bumped against a root.",
            question="What made the lane unsafe?",
            cause="Clouds hid the stars and a root lay across the dark path.",
            result="The friends needed a light before they could roll onward.",
        )
        if params.solution == "lantern":
            world.say("hero", "Let us hang the lantern from the cart's tall handle.")
            world.say("helper", "Then its light will show the road and the roots.")
            charm.beliefs["method"] = "lantern"
            world.narrate(
                "turn",
                "The lantern sprang awake when hung from the handle. Its golden circle showed every root and puddle.",
                question="Where did they place the lantern?",
                cause="They hung it from the cart's tall handle.",
                result="Its golden light shone ahead over the whole lane.",
            )
            cart.location = "nursery"
            cart.meters["load"] = 0
            world.say("hero", "Now I can see the nursery gate.")
            world.say("helper", "And I can see the bun basket, safe and snug.")
            world.narrate(
                "ending",
                "The nursery windows glowed beside the cart, whose lantern made a warm gold moon on the gingham cloth.",
            )
        else:
            world.say("hero", "The star charm may call one friendly star down.")
            world.say("helper", "Ask it to shine on the road, not on our noses.")
            charm.beliefs["method"] = "star"
            world.narrate(
                "turn",
                "They asked politely. A small star slipped through the clouds and floated before the cart, lighting the lane.",
                question="What did the star do?",
                cause="The friends asked it politely to shine on the road.",
                result="It floated ahead and revealed the safe path to the nursery.",
            )
            cart.location = "nursery"
            cart.meters["load"] = 0
            world.say("hero", "The road is bright as a spoon.")
            world.say("helper", "Then let the nursery supper begin.")
            world.narrate(
                "ending",
                "The star twinkled above the nursery gate, and the gingham cart rolled beneath it with every bun in place.")

    else:
        world.say("hero", "The meadow wind is tugging the cart toward the pond.")
        world.say("helper", "If it goes, the buns will bob away.")
        world.narrate(
            "obstacle",
            "A gust lifted the cart's front wheels and shook the gingham cloth like a sail.",
            question="Why did the cart need anchoring?",
            cause="A strong gust was lifting its front wheels toward the pond.",
            result="The friends had to hold it still before moving the buns.",
        )
        if params.solution == "stone":
            world.say("hero", "The round stone can sit in the empty lower tray.")
            world.say("helper", "Good. Low and steady, then we can push together.")
            world.narrate(
                "turn",
                "They placed the heavy stone in the lower tray. The cart sat firmly, and the wind could no longer lift it.",
                question="Where did they put the stone?",
                cause="They wanted the weight low in the cart.",
                result="The lower tray held the cart steady against the gust.",
            )
            cart.location = "nursery"
            cart.meters["load"] = 0
            world.say("hero", "The wheels stay down!")
            world.say("helper", "And now the buns can travel safely.")
            world.narrate(
                "ending",
                "The stone waited beneath the cart at the nursery, while the gingham cloth fluttered harmlessly in the quiet yard.",
            )
        else:
            world.say("hero", "A sailor's knot may hold the handle to that old fence.")
            world.say("helper", "I know a knot that will not pinch or slip.")
            world.narrate(
                "turn",
                "They tied the handle to the fence with a broad sailor's knot. The cart stayed put until the gust passed.",
                question="How did the knot help?",
                cause="They tied the cart handle securely to the old fence.",
                result="The cart stayed in place until the dangerous gust was gone.",
            )
            cart.location = "nursery"
            cart.meters["load"] = 0
            world.say("hero", "The wind has lost its tug.")
            world.say("helper", "Then onward to the nursery, snug as a bug.")
            world.narrate(
                "ending",
                "At the nursery, the loosened knot curled like a sleeping snake beside the gingham wheel.",
            )

    check_sample(world)
    return world.sample()


def check_sample(world: World):
    if world.entities["cart"].location not in {"far_bank", "hilltop", "nursery"}:
        raise StoryError("The cart must reach the nursery route's safe ending.")
    if world.entities["cart"].meters["load"] != 0:
        raise StoryError("The buns must be delivered before the story ends.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 8:
        raise StoryError("The story needs a sustained exchange between both friends.")
    if not any(event.speaker == "hero" for event in speech) or not any(
        event.speaker == "helper" for event in speech
    ):
        raise StoryError("Both friends must speak.")
    if len([event for event in world.history if event.question]) < 2:
        raise StoryError("The story needs causal grounded questions.")
    if not any("magic" in event.text.lower() or "charm" in event.text.lower() for event in world.history):
        raise StoryError("The magical feature must appear in the story.")


ASP_RULES = """
works(P,S) :- solution(S,N), problem(P,N).
#show works/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, need in PROBLEMS.items()
        for solution, capability in SOLUTIONS.items()
        if need == capability
    ]


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [fact("problem", key, value) for key, value in PROBLEMS.items()]
        + [fact("solution", key, value) for key, value in SOLUTIONS.items()]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "works"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--charm", choices=CHARMS)
    parser.add_argument("--weather", choices=WEATHERS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        pair
        for pair in valid_combos()
        if (args.problem is None or pair[0] == args.problem)
        and (args.solution is None or pair[1] == args.solution)
    ]
    if not candidates:
        raise StoryError("That magical solution does not fit the selected problem.")
    problem, solution = rng.choice(candidates)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        problem=problem,
        solution=solution,
        charm=args.charm or rng.choice(CHARMS),
        weather=args.weather or rng.choice(WEATHERS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about magical paths.")
    tested = 0
    for problem, solution in valid_combos():
        for charm in CHARMS:
            for weather in WEATHERS:
                sample = generate(
                    StoryParams(
                        problem=problem,
                        solution=solution,
                        charm=charm,
                        weather=weather,
                        seed=tested,
                    )
                )
                check_sample(sample.world)
                tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} compatible magical paths.")


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
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            choices = [
                (problem, solution)
                for problem, solution in valid_combos()
                if (args.problem is None or problem == args.problem)
                and (args.solution is None or solution == args.solution)
            ]
            if not choices:
                raise StoryError("No compatible paths match these options.")
            params_list = []
            for problem, solution in choices:
                copied = argparse.Namespace(**vars(args))
                copied.problem = problem
                copied.solution = solution
                params_list.append(resolve_params(copied, rng))
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
