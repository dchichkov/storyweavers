#!/usr/bin/env python3
"""Bridge Builders: questions, tests and replies change a toy bridge before a delivery.

Different faults need different repairs. Observe before explaining; share the
observation before revising; test the real bridge before narrating success.
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
    problem: str = "sag"
    solution: str = "fold"
    approach: str = "ask"
    item: str = "bus"
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

PROMPT = "Write a dialogue-rich children's story about two friends testing and revising a small bridge for a toy vehicle."
PROBLEMS = {"sag": "stiffen", "short": "extend", "steep": "level"}
SOLUTIONS = {"fold": "stiffen", "join": "extend", "lower": "level"}
ITEMS = {"bus": "red bus", "van": "blue van", "truck": "green truck"}


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["bridge"] = Entity(
        id="bridge", label="the cardboard bridge", location="between_boxes",
        meters={"span": 2 if params.problem == "short" else 4, "gap": 3,
                "capacity": 1 if params.problem == "sag" else 3,
                "slope": 2 if params.problem == "steep" else 0, "tested": 0})
    world.entities["vehicle"] = Entity(id="vehicle", label=ITEMS[params.item], location="near_box",
                                       meters={"weight": 2, "crossed": 0})
    world.entities["parcel"] = Entity(id="parcel", label="the tiny paper parcel", location="vehicle",
                                      meters={"delivered": 0}, beliefs={"message": "We make a good bridge team."})
    world.entities["supplies"] = Entity(id="supplies", label="the supply tray", location="floor",
                                        meters={"spare_strip": 1, "tape": 1, "support_block": 1})
    return world


def obstacle(world: World) -> str:
    bridge, vehicle = world.entities["bridge"], world.entities["vehicle"]
    if bridge.meters["span"] < bridge.meters["gap"]:
        return "short"
    if bridge.meters["slope"] > 1:
        return "steep"
    if bridge.meters["capacity"] < vehicle.meters["weight"]:
        return "sag"
    return ""


def cross(world: World) -> str:
    bridge = world.entities["bridge"]
    bridge.meters["tested"] += 1
    problem = obstacle(world)
    if not problem:
        world.entities["vehicle"].location = "far_box"
        world.entities["vehicle"].meters["crossed"] = 1
        world.entities["parcel"].location = "station"
        world.entities["parcel"].meters["delivered"] = 1
    return problem


def revise(world: World):
    if world.entities["hero"].beliefs.get("obstacle") != obstacle(world):
        raise StoryError("Listen to the observed problem before choosing a repair.")
    bridge, supplies = world.entities["bridge"], world.entities["supplies"]
    solution = world.params.solution
    if solution == "fold":
        bridge.meters["capacity"] = 3
        bridge.meters["folded_edges"] = 1
    elif solution == "join":
        if min(supplies.meters.values()) < 1:
            raise StoryError("Extending the bridge needs a second strip, tape and a middle support.")
        supplies.meters.update(spare_strip=0, tape=0, support_block=0)
        bridge.meters.update(span=4, supported_join=1)
    else:
        bridge.meters.update(slope=0, upper_block_removed=1)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, friend = world.entities["hero"], world.entities["friend"]
    h, f = hero.label, friend.label
    vehicle = world.entities["vehicle"].label
    world.narrate("beginning", f"{h} balanced a tiny paper parcel on a {vehicle}. "
                  f"{f} had built a station on a box across a pretend river. Their cardboard bridge was the last piece of the route.")
    world.say("hero", "One delivery for your station. Is the road ready?")
    world.say("friend", "It looks like a bridge. I'm not sure it works like one yet.")
    if params.approach == "guess":
        world.say("hero", "I'll give it a good push.")
        problem = cross(world)
        hero.memes["frustration"] += 1
        failure_text = {
            "sag": f"The cardboard dipped beneath the {vehicle}. {f} steadied it, and {h} pulled the vehicle back.",
            "short": f"The front wheels reached the end of the strip before reaching the far box. {h} held the {vehicle} still.",
            "steep": f"The {vehicle} climbed a little way, then rolled back into {h}'s waiting hand.",
        }[problem]
        world.narrate("failed_" + problem, failure_text)
        world.say("friend", "Stop a moment. A bigger push won't tell us what's wrong.")
        world.say("hero", "I wanted the first delivery to be the first try.")
    else:
        world.say("hero", "What should we check before I let it go?")
        world.say("friend", "The gap, the slope, and whether the middle can hold it.")
        problem = obstacle(world)
        inspection = {
            "sag": f"{f} pressed the center of the strip with a finger. The flat cardboard bowed.",
            "short": f"They laid the strip across the boxes. A gap of air remained under its far end.",
            "steep": "They looked along the road to the extra block propping up its far end. The cardboard made a steep hill.",
        }[problem]
        world.narrate("inspected_" + problem, inspection)
    friend.beliefs["obstacle"] = problem

    if problem == "sag":
        world.say("friend", "The middle bends down. It isn't strong enough for the wheels.",
                  to="hero", reveal="obstacle")
        world.say("hero", "But I used the whole piece.")
        world.say("friend", "A whole flat piece. Could we give it sides?")
        world.say("hero", "Sides like a little tray?")
        world.say("friend", "Yes. Fold both long edges up. I'll hold one while you fold the other.")
        world.say("hero", "Will that make the river smaller?")
        world.say("friend", "No. Same river, different shape for the cardboard.")
        world.say("hero", "All right. Tell me if my fold goes crooked.")
        revise(world)
        world.narrate("fold", f"They raised two straight edges along the bridge. {f} held one fold while {h} pressed the other flat at its base.",
            question="What problem did their conversation identify?",
            cause="The flat bridge bowed under a small load.",
            result="They chose to fold up its long edges instead of pushing the vehicle harder.")
        world.say("friend", "Those edges look like tiny walls.")
        world.say("hero", "Tiny walls with an important job. Shall we try it slowly?")
        world.narrate("repair_ready", "They set the folded bridge across the same gap.",
            question="How did they change the bridge?",
            cause="The bridge needed more support against bending.",
            result="They folded both long edges upward while leaving the river gap unchanged.")

    elif problem == "short":
        world.say("friend", "The end doesn't reach the other box. There's air under the last bit.",
                  to="hero", reveal="obstacle")
        world.say("hero", "What if I fold it, like the bridge we made yesterday?")
        world.say("friend", "Folding won't make this piece longer.")
        world.say("hero", "Then could the wheels jump?")
        world.say("friend", "This is a delivery, not a flying lesson.")
        world.say("hero", "I have another strip in the tray. Could we join them?")
        world.say("friend", "Yes, but I don't want the join hanging over the river.")
        world.say("hero", "A block underneath the join?")
        world.say("friend", "Exactly. You hold the strips still; I'll put the block in place.")
        revise(world)
        world.narrate("join", f"{h} overlapped the two strips and taped them. {f} slid the spare block under the join.",
            question="Why did they need a second strip?",
            cause="The original bridge ended before reaching the far box.",
            result="A second strip lengthened the road, and a block supported the place where the strips met.")
        world.say("hero", "Now both ends have somewhere to rest.")
        world.say("friend", "And the middle has somewhere too. No road floating on wishes.")
        world.say("hero", "A slow delivery, then. No flying.")
        world.narrate("repair_ready", "The taped road rested on the two boxes and its new middle support.",
            question="Why was tape alone not their whole plan?",
            cause="The joined strips would meet above the pretend river.",
            result="They put a block directly beneath that join rather than leaving it unsupported.")

    else:
        world.say("friend", "The far end is much higher. The road is too steep for this little vehicle.",
                  to="hero", reveal="obstacle")
        world.say("hero", "I added that extra block to make a grand entrance.")
        world.say("friend", "I like grand. I like getting my parcel more.")
        world.say("hero", "Do you mind if we change your side?")
        world.say("friend", "Ask me which part. I don't want the station to disappear.")
        world.say("hero", "Just the extra block under the road. The station can stay on its box.")
        world.say("friend", "That works. I'll lift the road while you slide the block out.")
        world.say("hero", "Ready?")
        world.say("friend", "Ready. And thank you for asking before moving my things.")
        revise(world)
        world.narrate("lower", f"{f} lifted the high end. {h} removed the extra block, and they lowered the road until both ends were level.",
            question="Why did they lower one end of the bridge?",
            cause="The road climbed too steeply toward the station.",
            result="They agreed to remove only the extra support block, leaving the station itself in place.")
        world.say("hero", "Your station is still there.")
        world.say("friend", "And now the road comes to it instead of climbing a mountain.")
        world.say("hero", "I'll try again, gently." if params.approach == "guess" else "I'll try the delivery gently.")
        world.narrate("repair_ready", "The spare block sat beside the route. The bridge no longer tilted uphill.",
            question="What permission did one builder ask for?",
            cause=f"{h} wanted to alter the support on {f}'s side.",
            result=f"{f} agreed to moving the extra block, but not to removing the station.")

    if cross(world):
        raise StoryError("The revised bridge still does not support this delivery.")
    world.narrate("crossed", f"{h} rolled the {vehicle} across. {f} lifted the paper parcel from its roof onto the station.",
        question="How did they check that the repair worked?",
        cause=f"They rolled the {vehicle} across the repaired bridge without a running start.",
        result=f"It reached the far box, and {f} unloaded the parcel at the station.")
    world.say("friend", "Delivered. Your driver didn't even lose a corner of the parcel.")
    world.say("hero", "What did I bring you?")
    friend.beliefs["message"] = world.entities["parcel"].beliefs["message"]
    world.say("friend", "A very small thank-you note. It says we make a good bridge team.",
              to="hero", reveal="message")
    world.say("hero", "Then the next delivery is yours. I'll be the station.")
    world.agree()
    world.narrate("ending", f"The little parcel rested at the station. {f} turned the {vehicle} around while {h} opened a hand beside the other end of the bridge.")
    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(world: World):
    if obstacle(world) or not world.entities["vehicle"].meters["crossed"]:
        raise StoryError("The vehicle must really cross a compatible bridge.")
    if not world.entities["parcel"].meters["delivered"] or world.entities["parcel"].location != "station":
        raise StoryError("The promised delivery must be unloaded at the station.")
    expected = 2 if world.params.approach == "guess" else 1
    if world.entities["bridge"].meters["tested"] != expected:
        raise StoryError("The trace must distinguish a failed attempt from an inspection.")

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
