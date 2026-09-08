#!/usr/bin/env python3
"""Luna's Lard Cart: curiosity needs a careful hand.

A small tall tale about lard, a shiny cart, and the moral that testing a
mystery is wise only when you first make it safe.
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
    helper: str = "Pip"
    mystery: str = "whistling"
    method: str = "test"
    seed: int = 20260907


NAMES = ("Luna", "Pip", "Mara", "Toby", "Nia", "Finn")
MYSTERIES = {
    "whistling": "the lard cart whistles whenever its wheel turns",
    "sliding": "the lard tin slides farther than any tin should",
    "glowing": "the lard tin shines like a small moon at dusk",
}
METHODS = ("test", "rush")

PROMPT = (
    "Write a dialogue-rich children's tall tale about Luna, a curious child, "
    "a cart of lard, a cautionary mistake, and the moral that curiosity needs care."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", memes={"curiosity": 1.0, "care": 0.5}
            ),
            "helper": Entity(
                "helper", params.helper, "character", memes={"wisdom": 1.0, "trust": 0.5}
            ),
            "cart": Entity(
                "cart", "the lard cart", "vehicle", "barn",
                meters={"load": 0, "speed": 0, "distance": 0, "safe": 0},
            ),
            "lard": Entity(
                "lard", "a barrel of lard", "food", "barn",
                meters={"weight": 3, "spill": 0, "delivered": 0},
            ),
            "hill": Entity(
                "hill", "the blue hill", "landmark", "road",
                meters={"slope": 8, "roughness": 3},
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

    def say(self, speaker: str, text: str, *, to: str = "", reveal: str = ""):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a fact they have not learned.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
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


def validate_params(params: StoryParams):
    if params.mystery not in MYSTERIES:
        raise StoryError("Choose a registered cart mystery.")
    if params.method not in METHODS:
        raise StoryError("Choose either a careful test or a reckless rush.")
    if params.hero == params.helper:
        raise StoryError("The two speakers must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Names must be simple capitalized names, such as Luna and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def make_safe(world: World):
    cart = world.entities["cart"]
    lard = world.entities["lard"]
    if world.entities["hero"].beliefs.get("safe_plan") != "rope_and_brake":
        raise StoryError("The cart needs a shared safety plan before it moves.")
    cart.meters["safe"] = 1
    cart.meters["speed"] = 0
    lard.meters["spill"] = 0


def roll_cart(world: World, *, distance: float, downhill: bool = False):
    cart = world.entities["cart"]
    lard = world.entities["lard"]
    if cart.meters["safe"] != 1:
        raise StoryError("The lard cart cannot roll before its brake and rope are secured.")
    if cart.meters["load"] != 1:
        raise StoryError("The cart must carry the lard before it can make the delivery.")
    if downhill:
        cart.meters["speed"] = 1
        cart.meters["distance"] += distance
        lard.meters["spill"] += 1
        raise StoryError("A safe cart was sent downhill without a hand on its brake.")
    cart.meters["speed"] = 1
    cart.meters["distance"] += distance
    cart.meters["speed"] = 0
    lard.meters["delivered"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, helper = world.entities["hero"], world.entities["helper"]
    cart, lard, hill = world.entities["cart"], world.entities["lard"], world.entities["hill"]
    h, p = hero.label, helper.label

    world.narrate(
        "beginning",
        f"At the foot of {hill.label}, {h} found a little cart holding a barrel of lard. "
        f"The barrel was ordinary, but the cart had a brass bell that rang without being touched."
    )
    world.say("hero", "Why does this cart ring when nobody pulls it?")
    world.say("helper", "That is a fine question. It is not yet a fine reason to push it downhill.")
    world.say("hero", "Perhaps the bell knows where the lard wants to go.")
    world.say("helper", "Perhaps the hill knows where the cart wants to go.")

    if params.mystery == "whistling":
        hero.beliefs["mystery"] = MYSTERIES[params.mystery]
        world.say("hero", "Listen. The wheel is whistling.")
        world.say("helper", "I hear it too. A loose axle can sing.", to="hero", reveal="mystery")
    elif params.mystery == "sliding":
        hero.beliefs["mystery"] = MYSTERIES[params.mystery]
        world.say("hero", "The tin slid across the cart by itself.")
        world.say("helper", "A greasy board can make a tin slide.", to="hero", reveal="mystery")
    else:
        hero.beliefs["mystery"] = MYSTERIES[params.mystery]
        world.say("hero", "The lard is shining like a moon.")
        world.say("helper", "Sunlight on a smooth lid can make a bright trick.", to="hero", reveal="mystery")

    if params.method == "rush":
        hero.memes["curiosity"] += 1
        world.say("hero", "There is only one way to find out. I will give it a mighty shove.")
        world.narrate(
            "warning",
            f"{h} put both hands on the cart. The barrel of lard wobbled, the brass bell trembled, "
            f"and the long blue hill waited below.",
            question="Why was the cart dangerous to push at once?",
            cause="The hill was steep and the heavy barrel was not tied down.",
            result="A sudden shove could send the cart and its lard racing away.",
        )
        world.say("helper", "Wait! A mystery is worth testing, but not by risking a runaway barrel.")
        world.say("hero", "Then tell me how to test it without letting the hill decide.")
    else:
        world.say("hero", "I want to know the answer, but I do not want the lard rolling into town.")
        world.narrate(
            "warning",
            f"{p} examined the cart. Its brake was loose, and the barrel of lard had no rope around it.",
            question="What made the first test unsafe?",
            cause="The cart's brake was loose and the heavy barrel was untied.",
            result="The friends needed to secure both cart and cargo before investigating.",
        )
        world.say("helper", "Curiosity can wear an apron. Tie the barrel first, then test one wheel.")
        world.say("hero", "And keep a hand on the brake. I can do that.")

    helper.beliefs["safety"] = "tie the barrel and hold the brake"
    world.say("helper", "I know a safe plan: rope the barrel, tighten the brake, and test on level ground.",
              to="hero", reveal="safety")
    hero.beliefs["safe_plan"] = "rope_and_brake"
    world.say("hero", "Rope the lard, tighten the brake, and test the bell before the hill. Agreed?")
    world.say("helper", "Agreed. Questions should open doors, not send carts through them.")

    lard.location = "cart"
    cart.meters["load"] = 1
    cart.meters["safe"] = 0
    world.narrate(
        "careful_setup",
        f"They tied the barrel of lard with three stout loops, tightened the brake, and placed a wedge behind a wheel.",
        question="How did Luna turn curiosity into a safe plan?",
        cause="She learned that the hill and loose cart could cause trouble.",
        result="She secured the lard, tightened the brake, and chose level ground for the test.",
    )
    make_safe(world)

    world.narrate(
        "test",
        f"On the flat yard, {h} lifted the brake one finger while {p} held the rope. "
        f"The wheel turned, the brass bell rang, and the cart moved no farther than a pumpkin seed.",
        question="What did the careful test reveal?",
        cause="They tested the cart slowly while the rope and brake were ready.",
        result=f"They discovered that the ringing came from the turning wheel, not from magic inside the lard."
    )
    world.say("hero", "The bell rings when the wheel turns!")
    world.say("helper", "And it stops when the brake stops the wheel.")
    world.say("hero", "So the lard was innocent all along.")
    world.say("helper", "Most mysteries are less wild after a careful look.")

    world.narrate(
        "delivery",
        f"With the barrel tied and the brake held, they guided the cart around the hill instead of down it. "
        f"They delivered the lard to the village kitchen, where the cook needed it for warm bread.",
        question="Why did they go around the hill?",
        cause="The steep slope could turn a curious test into a runaway cart.",
        result="The friends chose the longer safe path and delivered the lard without spilling it.",
    )
    roll_cart(world, distance=12)

    world.say("hero", "I still have questions about the bell.")
    world.say("helper", "Good. What will you do before the next experiment?")
    world.say("hero", "Check the danger, make a plan, and ask someone to help.")
    world.say("helper", "That is how a small question grows into a wise adventure.")

    world.narrate(
        "ending",
        f"That evening, the empty cart rested beside the kitchen, its brass bell quiet and its rope neatly coiled. "
        f"{h} wrote three words on the barn door: Ask, Prepare, Test.",
        question="What moral did Luna learn?",
        cause="Her curiosity was useful, but an untied barrel and steep hill could have caused harm.",
        result="She learned to investigate bravely only after making the experiment safe.",
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
                "What is lard?",
                "Lard is a cooking fat made from pork that can be used in foods such as bread.",
            ),
            QAItem(
                "Why should a heavy cart be secured before testing it?",
                "A secured cart is less likely to roll away, spill its load, or hurt someone.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["lard"].meters["delivered"] != 1:
        raise StoryError("The lard must reach the village kitchen.")
    if world.entities["lard"].meters["spill"] != 0:
        raise StoryError("The cautionary story cannot end with spilled lard.")
    if world.entities["cart"].meters["safe"] != 1:
        raise StoryError("The cart must remain secured.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 14:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if sum(event.speaker == "hero" for event in speech) < 6:
        raise StoryError("The curious hero needs enough spoken turns.")
    if sum(event.speaker == "helper" for event in speech) < 6:
        raise StoryError("The helper needs enough spoken turns.")
    if not any(event.revealed for event in speech):
        raise StoryError("Dialogue must pass useful knowledge between characters.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several grounded questions and answers.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every grounded question needs a natural answer.")


ASP_RULES = """
safe_method(test) :- method(test).
safe_method(rush) :- method(rush), has_warning(rush).
valid(M) :- safe_method(M), method(M).
#show valid/1.
"""


def asp_facts() -> str:
    from asp import fact

    facts = [fact("method", method) for method in METHODS]
    facts.append(fact("has_warning", "rush"))
    return "\n".join(facts)


def asp_methods() -> set[str]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return {row[0] for row in atoms(symbols, "valid")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--mystery", choices=tuple(MYSTERIES))
    parser.add_argument("--method", choices=METHODS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        mystery=args.mystery or rng.choice(tuple(MYSTERIES)),
        method=args.method or rng.choice(METHODS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_methods() != set(METHODS):
        raise StoryError("Python and ASP disagree about registered methods.")
    count = 0
    for mystery in MYSTERIES:
        for method in METHODS:
            sample = generate(
                StoryParams(
                    hero="Luna",
                    helper="Pip",
                    mystery=mystery,
                    method=method,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; {len(METHODS)} ASP-compatible methods.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
            print(json.dumps(sorted(asp_methods())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    helper=args.helper or "Pip",
                    mystery=mystery,
                    method=method,
                    seed=args.seed,
                )
                for mystery in MYSTERIES
                for method in METHODS
                if (args.mystery is None or args.mystery == mystery)
                and (args.method is None or args.method == method)
            ]
            if not params_list:
                raise StoryError("No combinations match the selected options.")
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
