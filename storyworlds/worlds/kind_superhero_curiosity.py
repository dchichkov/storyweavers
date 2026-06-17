#!/usr/bin/env python3
"""A superhero story where curiosity and kindness solve the crisis."""

from __future__ import annotations

import argparse
import copy
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Crisis:
    id: str
    name: str
    surface: str
    hidden_need: str
    danger: int


@dataclass(frozen=True)
class Power:
    id: str
    name: str
    question: str
    curiosity: int


@dataclass(frozen=True)
class Ally:
    id: str
    name: str
    doubt: str
    trust_gain: int


@dataclass(frozen=True)
class Response:
    id: str
    name: str
    kind_act: str
    matches: str
    kindness: int


@dataclass(frozen=True)
class Params:
    crisis: str
    power: str
    ally: str
    response: str


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    delta: dict[str, int] = field(default_factory=dict)


@dataclass
class HeroWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)
    meters: dict[str, int] = field(
        default_factory=lambda: {"danger": 0, "curiosity": 0, "kindness": 0, "trust": 0, "resolve": 0}
    )

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        **delta: int,
    ) -> None:
        self.history.append(Event(event_id, text, actor, target, dict(delta)))
        for key, value in delta.items():
            self.meters[key] = self.meters.get(key, 0) + value


CRISES = {
    "bridge": Crisis(
        "bridge",
        "the humming bridge",
        "cars froze while the railings glowed blue",
        "the bridge was frightened by its own new power grid",
        3,
    ),
    "museum": Crisis(
        "museum",
        "the floating museum",
        "paintings drifted toward the skylight",
        "a lonely gravity engine wanted someone to notice its song",
        2,
    ),
    "tower": Crisis(
        "tower",
        "the glass tower",
        "windows flashed warnings no adult could read",
        "a trapped maintenance drone was asking for help",
        2,
    ),
}

POWERS = {
    "xray": Power("xray", "x-ray listening", "What is the machine really trying to say?", 3),
    "wind": Power("wind", "gentle wind-shaping", "Where is the panic moving fastest?", 2),
    "spark": Power("spark", "blue spark-jumping", "Which circuit is scared, not broken?", 3),
}

ALLIES = {
    "rookie": Ally("rookie", "Rook", "thought speed mattered more than questions", 1),
    "captain": Ally("captain", "Captain Vale", "wanted a dramatic rescue for the cameras", 0),
    "robot": Ally("robot", "Unit Pebble", "could calculate danger but not comfort", 2),
}

RESPONSES = {
    "ask": Response("ask", "ask the frightened system what hurt", "listen before lifting", "need", 3),
    "shield": Response("shield", "shield the crowd while speaking softly", "protect without blaming", "danger", 2),
    "share": Response("share", "share a small kindness with the hidden helper", "offer companionship", "lonely", 3),
}


def valid_params(params: Params) -> tuple[bool, str]:
    if params.crisis not in CRISES:
        return False, f"unknown crisis: {params.crisis}"
    if params.power not in POWERS:
        return False, f"unknown power: {params.power}"
    if params.ally not in ALLIES:
        return False, f"unknown ally: {params.ally}"
    if params.response not in RESPONSES:
        return False, f"unknown response: {params.response}"
    if params.crisis == "bridge" and params.power == "spark":
        return False, "blue spark-jumping would make the humming bridge more dangerous"
    if params.ally == "captain" and params.response == "share":
        return False, "Captain Vale will not pause long enough for a shared quiet kindness"
    if params.crisis == "tower" and params.response == "shield":
        return False, "shielding the crowd does not reach the trapped tower drone"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(crisis, power, ally, response)
        for crisis in CRISES
        for power in POWERS
        for ally in ALLIES
        for response in RESPONSES
        if valid_params(Params(crisis, power, ally, response))[0]
    ]


def make_world(params: Params) -> HeroWorld:
    crisis = CRISES[params.crisis]
    power = POWERS[params.power]
    ally = ALLIES[params.ally]
    world = HeroWorld(params)
    world.add_entity(Entity("hero", "Kind Comet", "superhero", {"Curiosity": 1, "Kindness": 2}))
    world.add_entity(Entity("crisis", crisis.name, "physical", {"Danger": crisis.danger, "Need": 1}))
    world.add_entity(Entity("power", power.name, "concept", {"Curiosity": power.curiosity}))
    world.add_entity(Entity("ally", ally.name, "sidekick", {"Trust": ally.trust_gain}))
    world.facts["hidden_need"] = crisis.hidden_need
    world.facts["ally_doubt"] = ally.doubt
    world.facts["question"] = power.question
    return world


def notice_crisis(world: HeroWorld) -> None:
    crisis = CRISES[world.params.crisis]
    world.record(
        "notice",
        f"Kind Comet arrived at {crisis.name}, where {crisis.surface}.",
        "hero",
        "crisis",
        danger=crisis.danger,
    )


def inner_monologue(world: HeroWorld) -> None:
    power = POWERS[world.params.power]
    thought = f"I could punch the problem, Kind Comet thought, but {power.question.lower()}"
    world.record(
        "thought",
        thought,
        "hero",
        "power",
        curiosity=power.curiosity,
    )
    world.facts["inner_monologue"] = thought


def consult_ally(world: HeroWorld) -> None:
    ally = ALLIES[world.params.ally]
    world.record(
        "ally",
        f"{ally.name} hesitated because they {ally.doubt}.",
        "ally",
        "hero",
        trust=ally.trust_gain,
    )


def predict_response(world: HeroWorld) -> str:
    imagined = copy.deepcopy(world)
    response = RESPONSES[imagined.params.response]
    imagined.meters["kindness"] += response.kindness
    if response.matches in imagined.facts["hidden_need"]:
        imagined.meters["resolve"] += 2
    else:
        imagined.meters["resolve"] += 1
    if imagined.meters["curiosity"] + imagined.meters["kindness"] + imagined.meters["resolve"] >= 7:
        return "The thought showed her that a kind question could become stronger than a punch."
    return "The thought warned her that kindness without the right question would only slow the danger."


def answer_kindly(world: HeroWorld) -> None:
    response = RESPONSES[world.params.response]
    aligned = response.matches in world.facts["hidden_need"]
    resolve = 2 if aligned else 1
    world.record(
        "kind_response",
        f"Kind Comet chose to {response.name}: she would {response.kind_act}.",
        "hero",
        "crisis",
        kindness=response.kindness,
        resolve=resolve,
        danger=-resolve,
    )
    world.facts["kind_act"] = response.kind_act
    world.facts["aligned"] = aligned


def settle_city(world: HeroWorld) -> None:
    solved = (
        world.meters["danger"] <= 1
        and world.meters["curiosity"] >= 2
        and world.meters["kindness"] >= 2
        and bool(world.facts["aligned"])
    )
    if solved:
        world.record(
            "saved",
            f"The crisis calmed because Kind Comet understood that {world.facts['hidden_need']}.",
            "crisis",
            "hero",
            trust=1,
        )
        world.facts["ending"] = "saved"
    else:
        world.record(
            "unfinished",
            "The city was safer, but Kind Comet knew the real worry still needed another gentle question.",
            "hero",
            "crisis",
        )
        world.facts["ending"] = "unfinished"
    world.entities["hero"].memes["Curiosity"] = world.meters["curiosity"]
    world.entities["hero"].memes["Kindness"] = world.meters["kindness"]
    world.entities["crisis"].memes["Danger"] = world.meters["danger"]


def render_story(world: HeroWorld, prediction: str) -> str:
    lines = [
        "The city called her Kind Comet because she rescued people without making them feel small.",
        world.history[0].text,
        world.history[1].text,
        world.history[2].text,
        prediction,
        world.history[3].text,
        world.history[4].text,
    ]
    if world.facts["ending"] == "saved":
        lines.append("Afterward, even the sirens sounded softer, as if the city had learned to ask before shouting.")
    else:
        lines.append("Afterward, Kind Comet stayed nearby, curious enough to keep listening and kind enough not to rush.")
    return "\n".join(lines)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    notice_crisis(world)
    inner_monologue(world)
    consult_ally(world)
    prediction = predict_response(world)
    world.facts["prediction"] = prediction
    answer_kindly(world)
    settle_city(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a superhero story that includes the word kind.",
        "Use inner monologue to expose the hero's problem solving.",
        "Make curiosity and kindness change the simulated world state.",
    ]
    story_qa = [
        QAItem(
            "What did Kind Comet think before acting?",
            f"Kind Comet's inner monologue was: {world.facts['inner_monologue']}. "
            "That thought shifted the scene from force toward curiosity.",
        ),
        QAItem(
            "How was the hero kind?",
            f"Kind Comet chose to {world.facts['kind_act']}. "
            f"The kindness meter became {world.meters['kindness']}, and the ending was {world.facts['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            "Was the superhero crisis solved?",
            f"The ending state is {world.facts['ending']}. "
            f"Danger ended at {world.meters['danger']}, curiosity at {world.meters['curiosity']}, and resolve at {world.meters['resolve']}.",
        ),
        QAItem(
            "What hidden need drove the crisis?",
            f"The hidden need was that {world.facts['hidden_need']}. "
            "That need was stored in the crisis entity before the response was chosen.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def atom(value: str) -> str:
    return value.replace("-", "_")


def asp_program() -> str:
    facts = []
    for key in CRISES:
        facts.append(f"crisis({atom(key)}).")
    for key in POWERS:
        facts.append(f"power({atom(key)}).")
    for key in ALLIES:
        facts.append(f"ally({atom(key)}).")
    for key in RESPONSES:
        facts.append(f"response({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(C,P,A,R) :- C=bridge, P=spark, crisis(C), power(P), ally(A), response(R).",
            "invalid(C,P,A,R) :- A=captain, R=share, crisis(C), power(P), ally(A), response(R).",
            "invalid(C,P,A,R) :- C=tower, R=shield, crisis(C), power(P), ally(A), response(R).",
            "valid(C,P,A,R) :- crisis(C), power(P), ally(A), response(R), not invalid(C,P,A,R).",
            "#show valid/4.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in item) for item in asp.atoms(model, "valid")}
    py_valid = {(p.crisis, p.power, p.ally, p.response) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid kind superhero stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crisis", choices=sorted(CRISES))
    parser.add_argument("--power", choices=sorted(POWERS))
    parser.add_argument("--ally", choices=sorted(ALLIES))
    parser.add_argument("--response", choices=sorted(RESPONSES))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> Params:
    rng = rng or random.Random(args.seed)
    explicit = any(value is not None for value in (args.crisis, args.power, args.ally, args.response))
    if explicit:
        params = Params(
            crisis=args.crisis or rng.choice(list(CRISES)),
            power=args.power or rng.choice(list(POWERS)),
            ally=args.ally or rng.choice(list(ALLIES)),
            response=args.response or rng.choice(list(RESPONSES)),
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    return rng.choice(all_params())


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    rng = random.Random(args.seed)
    for _ in range(max(1, args.n)):
        yield generate(resolve_params(args, rng))


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        for event in sample.world.history:
            print(f"- {event.id}: {event.text} {event.delta}")
    if args.qa:
        print("\nStory QA:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\nWorld QA:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify_asp())
            return 0
        if args.asp:
            import asp

            print(asp.solve(asp_program()))
            return 0
        for index, sample in enumerate(iter_samples(args)):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
