#!/usr/bin/env python3
"""One Cart, Two Plans: a disagreement becomes an agreement they actually carry out.

Track each load and completed delivery. Hearing a proposal is not consent;
both friends must accept it before the cart moves. Promises alone earn no QA.
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
    hero: str = "Mia"
    friend: str = "Ben"
    problem: str = "order"
    solution: str = "turns"
    approach: str = "ask"
    item: str = "beans"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(id="hero", label=params.hero, kind="character",
                           memes={"frustration": 1.0, "trust": 0.5}),
            "friend": Entity(id="friend", label=params.friend, kind="character",
                             memes={"frustration": 0.5, "trust": 0.5}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind=kind, text=text, question=question,
                                  cause=cause, result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, to="", reveal="", tag="said"):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot pass on information they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        if text.endswith("."):
            text = text[:-1] + ","
        self.history.append(Event(kind="speech", text=f'"{text}" {actor.label} {tag}.',
                                  speaker=speaker, listener=to, revealed=reveal,
                                  state=self.snapshot()))

    def agree(self):
        for key in ("hero", "friend"):
            self.entities[key].memes.update(frustration=0.0, trust=1.0)

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params, story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[QAItem(question=event.question, answer=f"{event.cause} {event.result}")
                      for event in self.history if event.question],
            world_qa=[], world=self,
        )


NAMES = ("Mia", "Ben", "Noor", "Sam", "Lily", "Theo")
APPROACHES = ("ask", "guess")

PROMPT = "Write a dialogue-rich children's story in which two friends negotiate a practical plan for sharing one garden cart."
PROBLEMS = {"order": "fair_order", "gate": "narrow_passage", "heavy": "reduce_load"}
SOLUTIONS = {"turns": "fair_order", "carry": "narrow_passage", "split": "reduce_load"}
ITEMS = {"beans": ("bean", "red"), "peas": ("pea", "blue"), "sunflowers": ("sunflower", "yellow")}


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    plant, color = ITEMS[params.item]
    world.entities["cart"] = Entity(id="cart", label=f"the {color} cart", location="shed",
                                    meters={"capacity": 2, "load": 0, "width": 2, "trips": 0})
    world.entities["gate"] = Entity(id="gate", label="the garden gate", location="path",
                                    meters={"width": 1 if params.problem == "gate" else 3})
    world.entities["plants"] = Entity(id="plants", label=f"{plant} seedlings", location="shed",
                                      meters={"units": 1, "delivered": 0})
    world.entities["blocks"] = Entity(id="blocks", label="wooden blocks", location="shed",
                                      meters={"units": 4 if params.problem == "heavy" else 1, "delivered": 0})
    return world


def accept_plan(world: World):
    hero, friend = world.entities["hero"], world.entities["friend"]
    if hero.beliefs.get("proposal") != world.params.solution or friend.beliefs.get("proposal") != world.params.solution:
        raise StoryError("Both friends must have heard the proposed plan before agreeing.")
    hero.beliefs["accepted_plan"] = world.params.solution
    friend.beliefs["accepted_plan"] = world.params.solution
    world.agree()


def move_load(world: World, key: str, units: int, destination: str, *, by_hand=False):
    cart, gate, cargo = (world.entities[name] for name in ("cart", "gate", key))
    if any(world.entities[name].beliefs.get("accepted_plan") != world.params.solution for name in ("hero", "friend")):
        raise StoryError("Moving the shared load requires both friends' agreement.")
    if units <= 0 or units > cargo.meters["units"] - cargo.meters["delivered"]:
        raise StoryError("Cannot deliver nonexistent cargo.")
    if not by_hand and (units > cart.meters["capacity"] or cart.meters["width"] > gate.meters["width"]):
        raise StoryError("That cart trip is too heavy or too wide for the gate.")
    if by_hand and units > 1:
        raise StoryError("Carry small loads together, not the whole heavy box.")
    cargo.meters["delivered"] += units
    if cargo.meters["delivered"] == cargo.meters["units"]:
        cargo.location = destination
    if not by_hand:
        cart.location = destination
        cart.meters["trips"] += 1
    cart.meters["load"] = 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, friend, cart = (world.entities[key] for key in ("hero", "friend", "cart"))
    h, f = hero.label, friend.label
    plant, color = ITEMS[params.item]
    world.narrate("beginning", f"{h} held a tray of {plant} seedlings. {f} had a box of wooden blocks. "
                  f"Between them stood the only cart in the garden, with one shiny {color} handle.")
    world.say("hero", "I need the cart.")
    world.say("friend", "So do I. One handle, two hands wanting it.")
    world.say("hero", "The plants need the shady bench.")
    world.say("friend", "The blocks need the play mat. We're going different ways.")

    if params.problem == "order":
        friend.beliefs["waiting"] = "the blocks can wait"
        world.say("hero", "Then my job goes first.")
        world.say("friend", "You went first yesterday. I remember doing all the lifting.")
        if params.approach == "guess":
            hero.memes["frustration"] += 1
            world.say("hero", "I'll only be a minute.")
            world.narrate("pulled_handle", f"{h} pulled the handle. {f} kept a hand on it, and the cart stayed between them.")
            world.say("friend", "That's what you said yesterday. Could we make an actual plan?")
        else:
            world.say("hero", "You're right. What would make this feel fair to you?")
            world.say("friend", "A turn driving, not another whole afternoon lifting.")
        world.say("hero", "Can the blocks wait in the shed while we move the plants?")
        world.say("friend", "They can wait. Blocks don't wilt.", to="hero", reveal="waiting")
        world.say("hero", "These leaves are starting to droop. I'll load the plants if you drive.")
        world.say("friend", "And the blocks?")
        world.say("hero", "I'll bring them while you build. Then we've both done a trip.")
        hero.beliefs["proposal"] = "turns"
        world.say("hero", "Plants first, with you driving. Blocks next, with me driving. Does that work?",
                  to="friend", reveal="proposal")
        world.say("friend", "Yes. And this time I get to hold the shiny end.")
        accept_plan(world)
        world.narrate("agreement", f"{h} let go of the handle and lifted the seedling tray onto the cart.",
            question="Why did they agree to move the plants first?",
            cause="The plants were drooping, but the blocks could wait safely in the shed.",
            result=f"{f} would drive the first trip, and {h} would bring the blocks afterward.")
        move_load(world, "plants", 1, "shady_bench")
        world.narrate("plants_delivered", f"{f} wheeled the seedlings to the shady bench. Together they lifted the tray off.")
        world.say("friend", "There. Your plants are out of the sun.")
        world.say("hero", "Now it's the blocks' turn. I'll bring the cart back to the shed.")
        move_load(world, "blocks", 1, "play_mat")
        world.narrate("blocks_delivered", f"{h} returned to the shed, loaded the blocks, and rolled them to {f}'s play mat.",
            question="Did the second friend actually get a turn?",
            cause=f"{f} drove the seedlings to the bench.",
            result=f"{h} then delivered the blocks while {f} began arranging the toy town.")
        world.say("friend", "A bridge needs two sides. Will you build the other one?")
        world.say("hero", "Yes. We can both go first on that.")
        world.narrate("ending", f"Two rows of blocks met in the middle of the mat. Behind them, the seedlings rested in the shade and the empty cart stood still.",
            question="How could they tell that both jobs were finished?",
            cause="The seedling tray had reached the shady bench, and all the blocks were on the play mat.",
            result="Neither load was left waiting beside the shed.")

    elif params.problem == "gate":
        friend.beliefs["gate"] = "the cart is wider than the opening"
        world.say("hero", "Let's load both things. One trip, then we're finished.")
        world.say("friend", "Have you looked at the little gate?")
        if params.approach == "guess":
            hero.memes["frustration"] += 1
            cart.location = "gate"
            world.say("hero", "The cart will fit. It's only a small cart.")
            world.narrate("blocked_cart", f"{h} rolled the empty cart up to the gate. Its wheels stopped against the posts.")
            world.say("friend", "Small cart. Smaller gate.")
        else:
            world.say("hero", "Do you think the wheels are wider than the opening?")
            world.narrate("measured_gate", f"They held a stick across the cart's wheels, then across the gate. The stick reached past both posts.")
        world.say("friend", "The cart is wider than the opening. Loading it won't change that.",
                  to="hero", reveal="gate")
        world.say("hero", "Could we turn it sideways?")
        world.say("friend", "Then the tray would tip. I'd rather keep the plants inside their pots.")
        world.say("hero", "I wanted to solve this with the cart.")
        world.say("friend", "Do we need the cart, or do we need the things on the other side?")
        world.say("hero", "The things. I suppose the cart hasn't asked to come.")
        world.say("friend", "We can carry the tray together. Then we can bring the blocks.")
        hero.beliefs["proposal"] = "carry"
        world.say("hero", "Let's park the cart and carry one small load at a time, together.",
                  to="friend", reveal="proposal")
        world.say("friend", "Agreed. You take that handle; I'll take this one.")
        accept_plan(world)
        cart.location = "gate"
        world.narrate("agreement", f"They parked the cart beside the gate and stood at opposite ends of the tray.",
            question="Why did they stop trying to use the cart?",
            cause="The cart's wheels were wider than the gate opening.",
            result="The friends agreed to carry the loads through instead of tipping or forcing the cart.")
        move_load(world, "plants", 1, "shady_bench", by_hand=True)
        world.narrate("plants_carried", "They carried the tray level through the gate and set it on the shady bench.")
        world.say("hero", "Not a single pot tipped.")
        world.say("friend", "Now the box. Same team, different handles.")
        move_load(world, "blocks", 1, "play_mat", by_hand=True)
        world.narrate("blocks_carried", f"Together they brought the small block box through and lowered it onto the play mat.",
            question="How did both loads get through the narrow gate?",
            cause="The friends carried the tray together, keeping it level.",
            result="They then returned for the block box and carried that through together too.")
        world.say("hero", "The cart can watch us build.")
        world.say("friend", "It's very good at staying on its own side of the gate.")
        world.narrate("ending", "The cart waited outside. Inside, a green tray and a wooden town stood on opposite sides of two dusty footprints.",
            question="Where was the cart when they finished?",
            cause="They parked the cart beside the gate because it could not fit through.",
            result="It stayed there while the friends carried both loads into the garden.")

    else:
        friend.beliefs["capacity"] = "two small baskets per trip"
        world.say("hero", "Plants underneath, all the blocks on top. Easy.")
        world.say("friend", "Not on the plants. And that box holds four little baskets of blocks.")
        world.say("hero", "The cart looks big enough.")
        if params.approach == "guess":
            hero.memes["frustration"] += 1
            cart.meters["load"] = 4
            world.say("hero", "I'll try the blocks first.")
            world.narrate("overloaded", f"{h} emptied the four baskets into the cart. The wheels sank into the soft path.")
            world.say("friend", "Stop pulling. Listen to those wheels asking for less.")
            cart.meters["load"] = 0
            world.narrate("unloaded", "They put the blocks back into their four little baskets.")
        else:
            world.say("hero", "How much did it carry last time without sinking?")
            world.say("friend", "Two little baskets. Not four and not a tray underneath.")
        world.say("friend", "Two small baskets per trip kept the wheels moving.", to="hero", reveal="capacity")
        world.say("hero", "Two trips sounds slower.")
        world.say("friend", "Slower than a cart that doesn't move at all?")
        world.say("hero", "All right. First the plants by themselves.")
        world.say("friend", "Then two baskets of blocks. Then the other two.")
        hero.beliefs["proposal"] = "split"
        world.say("hero", "Three light trips. We can swap driving each time.", to="friend", reveal="proposal")
        world.say("friend", "Deal. I'll count baskets; you tell me when the cart is empty.")
        accept_plan(world)
        world.narrate("agreement", "They set the four baskets in two pairs and put the seedling tray alone on the cart.",
            question="Why did they divide the load into smaller trips?",
            cause="The cart could carry two small baskets of blocks, but the box held four.",
            result="They planned one trip for the plants and two lighter trips for the blocks.")
        move_load(world, "plants", 1, "shady_bench")
        world.narrate("plants_delivered", f"{h} drove the seedlings to the shady bench, and {f} lifted the tray off.")
        world.say("hero", "Empty cart. Ready for the first pair.")
        move_load(world, "blocks", 2, "play_mat")
        world.narrate("first_half", f"{f} brought two baskets to the play mat while {h} cleared a space.")
        world.say("friend", "Two baskets here. Two still at the shed.")
        world.say("hero", "Then we aren't finished. My turn to fetch the rest.")
        move_load(world, "blocks", 2, "play_mat")
        world.narrate("second_half", f"{h} brought the last two baskets. {f} counted all four beside the mat.",
            question="How many trips did they actually make?",
            cause="They carried the plants on one trip and two baskets of blocks on each of two more trips.",
            result="All four baskets reached the play mat, making three cart trips in total.")
        world.say("friend", "Four baskets. No missing half of a town.")
        world.say("hero", "And no plants underneath it.")
        world.narrate("ending", "The four empty baskets nested together beside the cart. Across the mat, the first little street reached all the way to the shady bench.",
            question="What showed that they had kept the whole agreement?",
            cause="The seedlings reached the bench, and both pairs of block baskets reached the mat.",
            result="They did not stop after delivering only the first half of the blocks.")
    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(world: World):
    for key, destination in (("plants", "shady_bench"), ("blocks", "play_mat")):
        item = world.entities[key]
        if item.location != destination or item.meters["delivered"] != item.meters["units"]:
            raise StoryError("Every promised load must actually reach its destination.")
    if world.entities["cart"].meters["load"] != 0:
        raise StoryError("The cart must be unloaded at the end.")
    expected = {"order": 2, "gate": 0, "heavy": 3}[world.params.problem]
    if world.entities["cart"].meters["trips"] != expected:
        raise StoryError("The ending must account for the trips actually made.")

ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [(problem, solution) for problem, need in PROBLEMS.items()
            for solution, capability in SOLUTIONS.items() if need == capability]


def asp_facts() -> str:
    from asp import fact
    return "\n".join([fact("problem", key, value) for key, value in PROBLEMS.items()]
                     + [fact("solution", key, value) for key, value in SOLUTIONS.items()])


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(f"{params.solution!r} cannot solve {params.problem!r}; choose a compatible action.")
    if params.approach not in APPROACHES or params.item not in ITEMS:
        raise StoryError("Unknown approach or story item.")
    if params.hero == params.friend:
        raise StoryError("The two speakers must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.friend)):
        raise StoryError("Use simple capitalized names, such as Mia and Ben.")


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    turns = [event for event in world.history if event.kind == "speech"]
    if len(turns) < 14 or any(sum(event.speaker == key for event in turns) < 5 for key in ("hero", "friend")):
        raise StoryError("Both characters need sustained speaking turns.")
    if not any(event.revealed for event in turns):
        raise StoryError("The conversation must pass on useful information.")
    if len(sample.story_qa) < 3 or any(not event.cause or not event.result for event in world.history if event.question):
        raise StoryError("Grounded QA needs causes and consequences.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")):
        raise StoryError("The final agreement has not happened.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--item", choices=tuple(ITEMS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [(p, s) for p, s in valid_combos()
                  if (args.problem is None or p == args.problem)
                  and (args.solution is None or s == args.solution)]
    if not candidates:
        raise StoryError("That solution does not address the selected problem.")
    problem, solution = rng.choice(candidates)
    hero = args.hero or rng.choice([name for name in NAMES if name != args.friend])
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(hero=hero, friend=friend, problem=problem, solution=solution,
                         approach=args.approach or rng.choice(APPROACHES),
                         item=args.item or rng.choice(tuple(ITEMS)), seed=args.seed)
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree on compatible problem/solution pairs.")
    tested = 0
    for problem, solution in valid_combos():
        for approach in APPROACHES:
            for item in ITEMS:
                sample = generate(StoryParams(problem=problem, solution=solution,
                                               approach=approach, item=item))
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} Python/ASP-compatible pairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for pair in sample.story_qa:
            print(f"\nQ: {pair.question}\nA: {pair.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(dict(entities=sample.world.snapshot(),
                              history=[asdict(event) for event in sample.world.history]), indent=2))


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
            choices = [(p, s, a) for p, s in valid_combos() for a in APPROACHES
                       if (args.problem is None or p == args.problem)
                       and (args.solution is None or s == args.solution)
                       and (args.approach is None or a == args.approach)]
            if not choices:
                raise StoryError("No compatible combinations match these options.")
            params_list = []
            for problem, solution, approach in choices:
                fields = vars(args) | dict(problem=problem, solution=solution, approach=approach)
                params_list.append(resolve_params(argparse.Namespace(**fields), rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(params) for params in params_list]
        if args.json:
            payloads = [sample.to_dict() for sample in samples]
            print(json.dumps(payloads[0] if len(payloads) == 1 else payloads, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
