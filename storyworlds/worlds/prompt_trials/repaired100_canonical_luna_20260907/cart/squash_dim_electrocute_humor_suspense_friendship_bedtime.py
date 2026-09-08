#!/usr/bin/env python3
"""The Sleepy Cart and the Squash-Dim Lantern.

A bedtime story about friendship, a dark garden path, and a cart that learns
not to tickle an electric wire.
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


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    revealed: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Pip"
    problem: str = "squash_dim"
    solution: str = "wooden_handle"
    approach: str = "listen"
    seed: int = 777


NAMES = ("Luna", "Pip", "Milo", "Nora", "Tess", "Ollie")
APPROACHES = ("listen", "guess")
PROBLEMS = ("squash_dim", "electrocute")
SOLUTIONS = ("wooden_handle", "unplug_first")
PROMPT = (
    "Write a gentle bedtime story about two friends moving a sleepy garden cart "
    "through a dim path without touching a dangerous electric wire."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", memes={"bravery": 0.5, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", memes={"bravery": 0.5, "trust": 0.5}),
            "cart": Entity("cart", "the little moon cart", "vehicle", "shed",
                          {"wheels": 2, "lantern": 1, "moving": 0},
                          {"sleepiness": 0.7}),
            "lantern": Entity("lantern", "the squash-dim lantern", "light", "cart",
                              {"brightness": 0.2, "battery": 1},
                              {"coziness": 0.4}),
            "wire": Entity("wire", "the humming electric wire", "hazard", "path",
                           {"voltage": 1, "safe": 0}, {"danger": 1.0}),
            "handle": Entity("handle", "the dry wooden handle", "tool", "shed",
                             {"insulation": 1, "length": 1}, {"safety": 1.0}),
            "blanket": Entity("blanket", "the blue blanket", "cargo", "shed",
                              {"delivered": 0}, {"warmth": 1.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, listener: str = "",
            reveal: str = ""):
        if reveal:
            if speaker == "hero":
                self.entities["friend"].memes[reveal] = 1.0
            else:
                self.entities["hero"].memes[reveal] = 1.0
        verb = "asked" if text.endswith("?") else "said"
        name = self.entities[speaker].label
        self.history.append(Event("speech", f'"{text}" {name} {verb}.',
                                  speaker=speaker, listener=listener,
                                  revealed=reveal, state=self.snapshot()))

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
                QAItem(
                    "Why should someone avoid touching an electric wire?",
                    "An electric wire can hurt a person, so it should be switched off or kept away from safely.",
                )
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Unknown solution.")
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(f"{params.solution!r} does not solve {params.problem!r}.")
    if params.approach not in APPROACHES:
        raise StoryError("Unknown approach.")
    if params.hero == params.friend:
        raise StoryError("The friends must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def unplug(world: World):
    wire = world.entities["wire"]
    if wire.meters["safe"] != 0:
        raise StoryError("The electric wire has already been made safe.")
    wire.meters["safe"] = 1
    wire.meters["voltage"] = 0


def move_cart(world: World):
    cart = world.entities["cart"]
    wire = world.entities["wire"]
    handle = world.entities["handle"]
    if wire.meters["safe"] != 1:
        raise StoryError("The cart cannot pass the electric wire before it is made safe.")
    if handle.meters["insulation"] != 1:
        raise StoryError("The cart needs a dry wooden handle.")
    cart.location = "moon_garden"
    cart.meters["moving"] = 1


def deliver_blanket(world: World):
    blanket = world.entities["blanket"]
    if world.entities["cart"].location != "moon_garden":
        raise StoryError("The cart must reach the moon garden first.")
    blanket.location = "moon_garden"
    blanket.meters["delivered"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.friend

    world.narrate(
        "beginning",
        f"At bedtime, {h} and {f} found a blue blanket beside the little moon cart. "
        "They promised to carry it to the sleepy garden before the stars grew tired."
    )
    world.say("hero", "The lantern is glowing only a squash-dim orange.")
    world.say("friend", "That sounds less like a lantern and more like a sleepy pumpkin.")
    world.say("hero", "The path is dark, but we can go slowly.")
    world.say("friend", "Slowly is good. Especially if the path has surprises.")

    if params.problem == "squash_dim":
        world.say("hero", "I will pull the cart quickly, before the light gets dimmer.")
        if params.approach == "guess":
            world.entities["hero"].memes["bravery"] += 0.2
            world.narrate(
                "wobble",
                f"{h} tugged the cart. It wobbled three inches, bumped a pebble, "
                "and made the lantern blink like a nervous firefly."
            )
            world.say("friend", "That firefly looks nervous. Maybe we should listen before we hurry.")
        else:
            world.say("hero", "Let's listen to the cart before we pull it.")
            world.narrate(
                "listen",
                "They leaned close. The cart gave a tiny squeak, and the lantern flickered toward the path."
            )
        world.say("friend", "The wooden handle is dry, and the wire is humming ahead.", listener="hero",
                  reveal="hazard")
        world.say("hero", "Then we need the handle, not a brave yank.")
        world.say("friend", "And we should switch off the wire before crossing.")
        world.say("hero", "You watch the wire. I will fetch the wooden handle.")
        world.say("friend", "Together, we can make the dark path safe.")
        unplug(world)
        world.entities["hero"].memes["bravery"] = 1.0
        world.entities["friend"].memes["bravery"] = 1.0
        world.narrate(
            "turn",
            f"{h} brought the dry wooden handle while {f} kept everyone away from the wire.",
            question="Why did the friends stop pulling the cart quickly?",
            cause="The lantern was squash-dim, and a humming electric wire crossed the path.",
            result="They chose a dry wooden handle and made the wire safe before moving."
        )
    else:
        world.say("hero", "I can touch the wire switch. It is only a little wire.")
        world.say("friend", "Little wires can still make a very big surprise.")
        if params.approach == "guess":
            world.narrate(
                "near_miss",
                f"{h} reached toward the wire, but {f} caught the cart handle first. "
                "A blue spark snapped far away, and both friends froze."
            )
            world.say("friend", "Please do not touch it. I do not want bedtime to become electrocute-time.")
        else:
            world.say("hero", "How can we cross without touching the wire?")
            world.say("friend", "We can switch it off, then use the dry wooden handle.")
        world.say("hero", "You are right. We need an adult-safe plan, not a guessing plan.")
        world.say("friend", "I will stand back while you use the safe switch.")
        world.say("hero", "Then we both check that the humming has stopped.", listener="friend",
                  reveal="hazard")
        unplug(world)
        world.narrate(
            "turn",
            f"They stood well away from the wire and switched it off before touching the cart.",
            question="How did the friends avoid being hurt by the electric wire?",
            cause="They understood that even a small wire could be dangerous.",
            result="They kept back, switched it off, and used a dry wooden handle."
        )

    world.entities["handle"].location = "cart"
    move_cart(world)
    world.narrate(
        "crossing",
        f"With the dry handle in place, {h} pulled and {f} guided. "
        "The cart rolled past the quiet wire while the squash-dim lantern painted a small golden puddle."
    )
    world.say("hero", "We crossed!")
    world.say("friend", "And the cart did not tickle the wire.")
    world.say("hero", "That is the best kind of cart joke.")
    deliver_blanket(world)
    world.narrate(
        "ending",
        f"In the moon garden, they spread the blue blanket beneath the pear tree. "
        f"{h} and {f} curled up beside it while the lantern glowed softly, no longer dim with worry.",
        question="What showed that their plan worked?",
        cause="The wire was quiet, the cart reached the moon garden, and the blanket was delivered safely.",
        result="The friends could rest beneath the pear tree with a gentle light beside them."
    )
    world.entities["hero"].memes["trust"] = 1.0
    world.entities["friend"].memes["trust"] = 1.0
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["wire"].meters["safe"] != 1:
        raise StoryError("The electric wire must be safe at the ending.")
    if world.entities["blanket"].meters["delivered"] != 1:
        raise StoryError("The blanket must reach the moon garden.")
    if world.entities["cart"].location != "moon_garden":
        raise StoryError("The cart must reach the moon garden.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 12:
        raise StoryError("The story needs a sustained back-and-forth exchange.")
    if any(sum(event.speaker == key for event in speeches) < 4
           for key in ("hero", "friend")):
        raise StoryError("Both friends need several speaking turns.")
    if not any(event.revealed for event in speeches):
        raise StoryError("Dialogue must pass on useful information.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if "electrocute" not in sample.story.lower():
        raise StoryError("The story must include the word electrocute.")


ASP_RULES = """
safe_solution(S,P) :- solution(S,P).
#show safe_solution/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [("squash_dim", "wooden_handle"), ("electrocute", "unplug_first")]


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        fact("solution", solution, problem)
        for problem, solution in valid_combos()
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "safe_solution"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if (args.problem is None or pair[0] == args.problem)
        and (args.solution is None or pair[1] == args.solution)
    ]
    if not choices:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about valid solutions.")
    count = 0
    for problem, solution in valid_combos():
        for approach in APPROACHES:
            generate(StoryParams(problem=problem, solution=solution,
                                 approach=approach))
            count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible pairs.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = ""):
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
            params_list = []
            for problem, solution in valid_combos():
                if args.problem and problem != args.problem:
                    continue
                if args.solution and solution != args.solution:
                    continue
                for approach in APPROACHES:
                    if args.approach and approach != args.approach:
                        continue
                    params_list.append(resolve_params(argparse.Namespace(
                        problem=problem, solution=solution, approach=approach,
                        hero=args.hero, friend=args.friend,
                    ), rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n"
                     if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
