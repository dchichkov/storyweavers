#!/usr/bin/env python3
"""A nursery-rhyme bridge tale about a poor bouquet, a mistaken assumption, and a remembered fix."""

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
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Pip"
    flower: str = "poppy"
    repair: str = "reed"
    approach: str = "remember"
    seed: int = 777


NAMES = ("Luna", "Mira", "Nell", "Tessa", "Poppy", "Wren")
HELPERS = ("Pip", "Tom", "Bo", "Finn", "Kit", "Sol")
FLOWERS = {
    "poppy": "a red poppy",
    "daisy": "a white daisy",
    "bluebell": "a bluebell",
}
REPAIRS = {
    "reed": "a reed rail",
    "ribbon": "a ribbon rail",
    "twig": "a twig rail",
}
APPROACHES = ("remember", "guess")

PROMPT = (
    "Write a nursery-rhyme children's story about Luna carrying a poor bouquet "
    "across a tiny bridge, making a wrong assumption, remembering an earlier lesson, "
    "and repairing the bridge before the bouquet is lost."
)

ASP_RULES = """
valid_repair(R) :- repair(R).
#show valid_repair/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", memes={"hope": 0.6, "care": 0.8}
            ),
            "helper": Entity(
                "helper", params.helper, "character", memes={"patience": 0.8, "trust": 0.6}
            ),
            "bridge": Entity(
                "bridge",
                "the little plank bridge",
                "structure",
                "brook_bank",
                meters={"width": 2, "strength": 1, "safe": 0, "tested": 0},
            ),
            "bouquet": Entity(
                "bouquet",
                f"{FLOWERS[params.flower]} bouquet",
                "bundle",
                "hero_hand",
                meters={"stems": 3, "dry": 0, "saved": 0},
                memes={"importance": 1.0},
            ),
            "supplies": Entity(
                "supplies",
                "the grassy basket",
                "tools",
                "brook_bank",
                meters={"reed": 1, "ribbon": 1, "twig": 1},
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

    def say(self, speaker: str, text: str, *, listener: str = ""):
        if speaker not in self.entities:
            raise StoryError("A story speaker must be a known character.")
        actor = self.entities[speaker]
        verb = "asked" if text.rstrip().endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {verb}.',
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
                    "What makes a bridge safer for a light bouquet?",
                    "A rail can keep the bouquet from slipping while the bridge is crossed carefully.",
                )
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.flower not in FLOWERS:
        raise StoryError("Choose a flower from the flower registry.")
    if params.repair not in REPAIRS:
        raise StoryError("Choose a repair from the repair registry.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either remember or guess.")
    if params.hero == params.helper:
        raise StoryError("The child and helper need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def inspect_bridge(world: World) -> str:
    bridge = world.entities["bridge"]
    return "weak" if bridge.meters["strength"] < 2 else ""


def cross_bridge(world: World) -> bool:
    bridge = world.entities["bridge"]
    bouquet = world.entities["bouquet"]
    bridge.meters["tested"] += 1
    if inspect_bridge(world):
        bouquet.location = "brook"
        bouquet.meters["dry"] = 1
        return False
    bridge.meters["safe"] = 1
    bouquet.location = "far_bank"
    bouquet.meters["saved"] = 1
    return True


def repair_bridge(world: World):
    supplies = world.entities["supplies"]
    bridge = world.entities["bridge"]
    repair = world.params.repair
    if supplies.meters[repair] < 1:
        raise StoryError(f"The basket has no {repair} left for the repair.")
    supplies.meters[repair] = 0
    bridge.meters["strength"] = 2
    bridge.meters["safe"] = 0


def check_ending(world: World):
    bouquet = world.entities["bouquet"]
    bridge = world.entities["bridge"]
    if not bouquet.meters["saved"] or bouquet.location != "far_bank":
        raise StoryError("The repaired story must save the bouquet on the far bank.")
    if bridge.meters["safe"] != 1:
        raise StoryError("The final bridge must be safe.")
    if bridge.meters["tested"] != 2:
        raise StoryError("The story must show one bad test and one careful test.")


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 10:
        raise StoryError("The tale needs a real back-and-forth conversation.")
    if {event.speaker for event in speeches} != {"hero", "helper"}:
        raise StoryError("Both characters must speak.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs questions grounded in causes and results.")
    if not any(event.kind == "flashback" for event in world.history):
        raise StoryError("The story must contain a state-changing flashback.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    bouquet = world.entities["bouquet"].label
    repair = REPAIRS[params.repair]

    world.narrate(
        "beginning",
        f"{hero} had a poor little bouquet, three flowers tied with a grass-green string. "
        f"Over the brook stood the garden gate, and the little plank bridge lay between, "
        f"thin as a rhyme and pale as a moonbeam.",
    )
    world.say("hero", f"I'll carry this {bouquet} across before the sun goes down.", listener="helper")
    world.say(
        "helper",
        "Mind the bridge, dear Luna. It looks brave, but it may not be strong.",
        listener="hero",
    )
    world.say(
        "hero",
        "It held my wooden cart yesterday, so it will hold a few flowers today.",
        listener="helper",
    )
    world.narrate(
        "assumption",
        f"{hero} made a quick assumption: if the bridge held a cart, it must hold the {bouquet}. "
        "But a cart has wheels, while a bouquet can slide, tip, and tumble.",
        question="What assumption did Luna make?",
        cause="She thought a bridge that held her wooden cart would automatically hold flowers.",
        result="She did not yet check whether a loose bouquet could stay balanced.",
    )

    world.say("helper", "The flowers are lighter, but they are slipperier.", listener="hero")
    world.say("hero", "I will step lightly. Tap, tap, and over we go.", listener="helper")
    if not cross_bridge(world):
        world.narrate(
            "bad_ending",
            f"Tap went {hero}'s shoe, and snap went the plank. The {bouquet} slid into the brook. "
            "The red bloom bobbed away, the white bloom hid beneath a leaf, and the blue string came untied. "
            "Poor flowers, poor bridge, poor plan!",
            question="What went wrong on the first crossing?",
            cause="The bridge was too weak, and the bouquet was not secured.",
            result="The plank bent and the poor bouquet fell into the brook.",
        )
    else:
        raise StoryError("The weak bridge must fail before the repair.")

    world.say("hero", "Oh, poor bouquet! I thought the old bridge was enough.", listener="helper")
    world.say(
        "helper",
        "You remembered the cart, but forgot what the flowers needed.",
        listener="hero",
    )
    world.narrate(
        "flashback",
        "Then Luna remembered yesterday: the cart had rolled over the middle rail, "
        "and Pip had tied a ribbon beside it. The rail had stopped the cart from slipping.",
        question="What did Luna remember from yesterday?",
        cause="The cart had crossed safely because a rail guided it and a tie stopped slipping.",
        result="She understood that the bouquet needed both a stronger plank and a side rail.",
    )
    world.say("hero", "A bridge is not safe just because it held one thing.", listener="helper")
    world.say("helper", "That is the lesson. What can we use from the basket?", listener="hero")
    world.say("hero", f"One {repair} for a rail, and careful hands for the stems.", listener="helper")
    repair_bridge(world)
    world.narrate(
        "repair",
        f"Together they braced the plank and fixed the {repair} along its edge. "
        f"{hero} tied the {bouquet} snugly, while {helper} held the rail straight.",
        question="How did Luna and Pip repair the crossing?",
        cause=f"They used {repair} to make a side rail and strengthened the weak plank.",
        result="The bridge could guide the bouquet instead of letting it slip into the brook.",
    )
    world.say("helper", "Now we test with patience, not a guess.", listener="hero")
    world.say("hero", "Step, pause, breathe, and carry the flowers close.", listener="helper")
    if not cross_bridge(world):
        raise StoryError("The repaired bridge must carry the bouquet.")
    world.narrate(
        "ending",
        f"Step, pause, breathe—across went {hero}. The {bouquet} reached the garden gate, "
        f"dry and bright. {helper} smiled, the brook sang below, and the poor bouquet became "
        "a small bright gift beside the gate.",
        question="How did the second crossing prove the repair worked?",
        cause="Luna tied the bouquet and crossed the strengthened bridge slowly beside its new rail.",
        result="The bouquet reached the far bank dry and safe.",
    )
    world.say("hero", "The bridge taught me to look before I leap.", listener="helper")
    world.say("helper", "And a poor bouquet can still have a happy ending.", listener="hero")
    sample = world.sample()
    check_sample(sample)
    return sample


def valid_repairs() -> list[str]:
    return list(REPAIRS)


def asp_facts() -> str:
    from asp import fact

    return "\n".join(fact("repair", key) for key in REPAIRS)


def asp_repairs() -> set[tuple[str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid_repair"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--flower", choices=tuple(FLOWERS))
    parser.add_argument("--repair", choices=tuple(REPAIRS))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in HELPERS if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        flower=args.flower or rng.choice(tuple(FLOWERS)),
        repair=args.repair or rng.choice(tuple(REPAIRS)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_repairs() != {(item,) for item in valid_repairs()}:
        raise StoryError("Python and ASP disagree about available repairs.")
    tested = 0
    for flower in FLOWERS:
        for repair in REPAIRS:
            sample = generate(
                StoryParams(
                    hero="Luna",
                    helper="Pip",
                    flower=flower,
                    repair=repair,
                    approach="remember",
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP agrees on {len(valid_repairs())} repairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print(
            "\nTRACE\n"
            + json.dumps(
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
            print(json.dumps(sorted(asp_repairs())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for flower in FLOWERS:
                for repair in REPAIRS:
                    params = StoryParams(
                        hero=args.hero or "Luna",
                        helper=args.helper or "Pip",
                        flower=flower,
                        repair=repair,
                        approach=args.approach or "remember",
                        seed=args.seed,
                    )
                    samples.append(generate(params))
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
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
