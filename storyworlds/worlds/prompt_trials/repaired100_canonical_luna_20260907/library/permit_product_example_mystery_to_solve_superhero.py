#!/usr/bin/env python3
"""A superhero solves a small permit mystery by checking a product example."""

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
    hero: str = "Luna"
    helper: str = "Pip"
    product: str = "glow-lantern"
    example: str = "paper lantern"
    approach: str = "inspect"
    seed: int = 777


PRODUCTS = {
    "glow-lantern": {
        "label": "Glow Lantern",
        "example": "paper lantern",
        "power": "a gentle blue beam",
        "place": "Moonbeam Market",
        "clue": "a blue thumbprint",
    },
    "rescue-kite": {
        "label": "Rescue Kite",
        "example": "red kite",
        "power": "a strong lifting breeze",
        "place": "Cloudside Fair",
        "clue": "a red thread",
    },
    "echo-badge": {
        "label": "Echo Badge",
        "example": "silver badge",
        "power": "a brave ringing call",
        "place": "Starbridge Square",
        "clue": "a silver button",
    },
}

APPROACHES = ("inspect", "guess")
NAMES = ("Luna", "Pip", "Nova", "Milo", "Zara", "Theo")

PROMPT = (
    "Write a dialogue-rich superhero story in which a hero solves a mystery "
    "about a permit, a product, and an example."
)

ASP_RULES = """
approved(P,E) :- product(P,E), permit(P).
#show approved/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                "hero", params.hero, "character",
                memes={"courage": 1.0, "confidence": 0.6},
            ),
            "helper": Entity(
                "helper", params.helper, "character",
                memes={"trust": 0.7, "attention": 0.8},
            ),
            "permit": Entity(
                "permit", "the market permit", "document",
                location="notice_board",
                meters={"valid": 1, "found": 0},
            ),
            "product": Entity(
                "product", PRODUCTS[params.product]["label"], "product",
                location="display_cart",
                meters={"tested": 0, "safe": 1},
            ),
            "example": Entity(
                "example", f"the {params.example}", "example",
                location="sample_table",
                meters={"matches_product": 1},
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
    ) -> None:
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

    def say(self, speaker: str, text: str, *, listener: str = "") -> None:
        label = self.entities[speaker].label
        if text.endswith("?"):
            ending = "asked"
        else:
            ending = "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {label} {ending}.',
                state=self.snapshot(),
            )
        )


def validate_params(params: StoryParams) -> None:
    if params.product not in PRODUCTS:
        raise StoryError("Choose a known superhero product.")
    if params.example != PRODUCTS[params.product]["example"]:
        raise StoryError("That example does not demonstrate the selected product.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either inspect or guess.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper need different names.")
    for name in (params.hero, params.helper):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def solve_mystery(world: World) -> None:
    permit = world.entities["permit"]
    product = world.entities["product"]
    example = world.entities["example"]
    if permit.location != "notice_board":
        raise StoryError("The permit must be found on the notice board.")
    if not permit.meters["valid"]:
        raise StoryError("The permit is not valid.")
    if example.meters["matches_product"] != 1:
        raise StoryError("The example must match the product.")
    permit.meters["found"] = 1
    product.meters["tested"] = 1
    example.location = "display_cart"


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    product = PRODUCTS[params.product]
    product_label = product["label"]
    example = params.example
    place = product["place"]
    power = product["power"]
    clue = product["clue"]

    world.narrate(
        "beginning",
        f"{hero}, the Moonlight Hero, arrived at {place} with {helper}, "
        f"just as the {product_label} was ready for its first rescue demonstration.",
    )
    world.say("hero", f"Is the {product_label} ready to shine?")
    world.say("helper", "It is, but the town guard says the demonstration has no permit.")
    world.narrate(
        "mystery",
        f"The {product_label} rested safely on a cart, but the permit pouch beside it was empty. "
        f"A tiny {clue} marked the edge of the cart.",
        question="Why could the superhero not begin the demonstration?",
        cause=f"The permit for the {product_label} was missing from its pouch.",
        result="The rescue demonstration had to wait.",
    )

    if params.approach == "guess":
        world.entities["hero"].memes["confidence"] -= 0.2
        world.say("hero", "Perhaps the wind carried the permit to the clock tower.")
        world.say("helper", "That is a guess. What clue can we check first?")
        world.narrate(
            "wrong_turn",
            f"{hero} looked toward the clock tower, but the {clue} still glittered beside the cart.",
            question="Why did looking at the clock tower fail?",
            cause=f"{hero} guessed a destination instead of following the {clue}.",
            result=f"The cart remained the only place connected to the missing permit.",
        )
    else:
        world.say("hero", "We need a clue, not a guess. What does the cart tell us?")
        world.say("helper", f"The {clue} points toward the sample table.")

    world.say("hero", f"Could the {example} show us what the product needs?")
    world.say(
        "helper",
        f"Yes. The {example} is the approved example for this {product_label}.",
    )
    world.narrate(
        "example",
        f"At the sample table, {hero} compared the {product_label} with the {example}. "
        f"The same {clue} appeared on a folded card beneath the example.",
        question="How did the example help solve the mystery?",
        cause=f"The {example} matched the {product_label} and led to a folded card.",
        result="The card gave the heroes a safe path back to the permit.",
    )
    world.say("hero", "The card says, 'Check the notice board before every demonstration.'")
    world.say("helper", "Then the permit may be waiting there.")
    world.narrate(
        "discovery",
        f"Behind the sample table, {hero} and {helper} hurried to the notice board. "
        "The valid permit was pinned behind a bright safety poster.",
        question="Where did the heroes find the permit?",
        cause="The card directed them to check the notice board.",
        result="They found the valid permit behind the safety poster.",
    )
    world.say("hero", "Here it is! The permit belongs with the product.")
    world.say("helper", "And the example proves which product the permit covers.")
    solve_mystery(world)
    world.narrate(
        "turn",
        f"{hero} placed the permit beside the {product_label}, then tested it with the {example}. "
        f"The product answered with {power}.",
        question="What did the heroes do before using the product?",
        cause="They found the valid permit and compared the product with its approved example.",
        result="They tested the product safely and confirmed that it matched the permit.",
    )
    world.say("hero", "Now the rescue signal can begin.")
    world.say("helper", "And everyone knows why it is safe.")
    world.narrate(
        "ending",
        f"The {product_label} filled {place} with {power}. "
        f"{hero} pinned the permit above the cart, while the {example} rested beside it as a clear guide.",
        question="What changed at the end of the story?",
        cause="The permit was found, and the example confirmed the product was approved.",
        result="The heroes began a safe demonstration with the permit displayed.",
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
                "What is a permit?",
                "A permit is permission that allows an activity to happen safely and properly.",
            ),
            QAItem(
                "Why is an example useful?",
                "An example shows what a product should look like or how it should work.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise StoryError("The generated sample needs its live world.")
    if world.entities["permit"].meters["found"] != 1:
        raise StoryError("The story must actually find the permit.")
    if world.entities["product"].meters["tested"] != 1:
        raise StoryError("The product must be tested after the permit is found.")
    if world.entities["example"].location != "display_cart":
        raise StoryError("The example must be used beside the product.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 8:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if not any("permit" in event.text.lower() for event in speeches):
        raise StoryError("The dialogue must discuss the permit.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several grounded questions and answers.")


def asp_facts() -> str:
    from asp import fact

    rows = []
    for key, data in PRODUCTS.items():
        rows.append(fact("product", key, data["example"]))
        rows.append(fact("permit", key))
    return "\n".join(rows)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(symbols, "approved"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--product", choices=tuple(PRODUCTS))
    parser.add_argument("--example")
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    product_key = args.product or rng.choice(tuple(PRODUCTS))
    expected_example = PRODUCTS[product_key]["example"]
    if args.example is not None and args.example != expected_example:
        raise StoryError("The selected example does not match the selected product.")
    hero = args.hero or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    params = StoryParams(
        hero=hero,
        helper=helper,
        product=product_key,
        example=expected_example,
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    expected = {
        (key, data["example"]) for key, data in PRODUCTS.items()
    }
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about approved products.")
    tested = 0
    for product_key, data in PRODUCTS.items():
        for approach in APPROACHES:
            sample = generate(
                StoryParams(
                    product=product_key,
                    example=data["example"],
                    approach=approach,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(expected)} approved product examples.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace and sample.world is not None:
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
            print(json.dumps(sorted(asp_combos()), ensure_ascii=False))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for product_key, data in PRODUCTS.items():
                if args.product and args.product != product_key:
                    continue
                for approach in APPROACHES:
                    if args.approach and args.approach != approach:
                        continue
                    params_list.append(
                        resolve_params(
                            argparse.Namespace(
                                product=product_key,
                                example=data["example"],
                                approach=approach,
                                hero=args.hero,
                                helper=args.helper,
                            ),
                            rng,
                        )
                    )
            if not params_list:
                raise StoryError("No combinations match these options.")
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
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
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
