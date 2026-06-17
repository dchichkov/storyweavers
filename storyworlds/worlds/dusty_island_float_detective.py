#!/usr/bin/env python3
"""A detective story about honesty, a dusty island, and what should float."""

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
class Island:
    id: str
    name: str
    oddity: str
    dust: int


@dataclass(frozen=True)
class Evidence:
    id: str
    name: str
    clue: str
    points_to: str
    clarity: int


@dataclass(frozen=True)
class Witness:
    id: str
    name: str
    secret: str
    honesty: int


@dataclass(frozen=True)
class Method:
    id: str
    name: str
    action: str
    tests: str
    solve: int


@dataclass(frozen=True)
class Params:
    island: str
    evidence: str
    witness: str
    method: str


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
class IslandWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)
    meters: dict[str, int] = field(
        default_factory=lambda: {"dust": 0, "clarity": 0, "honesty": 0, "solve": 0, "trust": 0}
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


ISLANDS = {
    "mesa": Island("mesa", "Mesa Moth Island", "the island left no wake although it crossed the bay", 3),
    "salt": Island("salt", "Saltcoat Island", "dust blew upward from the beach instead of down", 2),
    "bell": Island("bell", "Bellroot Island", "a buried bell rang whenever the island drifted east", 1),
}

EVIDENCE = {
    "feather": Evidence("feather", "glass feather", "it floated above the dust instead of falling", "float", 3),
    "ledger": Evidence("ledger", "honest ledger", "every erased line returned when read aloud", "honest", 2),
    "rope": Evidence("rope", "dusty rope", "one end was tied to air and the other to the dock", "anchor", 2),
}

WITNESSES = {
    "fisher": Witness("fisher", "Nell the fisher", "saw the island float before sunrise", 2),
    "mayor": Witness("mayor", "Mayor Quill", "hid the fact that the map had moved", 0),
    "keeper": Witness("keeper", "Old Faro", "kept an honest tide log no one believed", 3),
}

METHODS = {
    "weigh": Method("weigh", "weigh the dust", "compare ordinary dust with floating dust", "float", 3),
    "confess": Method("confess", "ask for an honest account", "let the witness correct the official story", "honest", 3),
    "untie": Method("untie", "untie the invisible anchor", "follow the rope until the island stops drifting", "anchor", 2),
}


def truth_clause(secret: str) -> str:
    if secret.startswith("saw "):
        return "someone " + secret
    if secret.startswith("kept "):
        return "someone " + secret
    if secret.startswith("hid the fact that "):
        return "someone hid the fact that " + secret.removeprefix("hid the fact that ")
    return secret


def valid_params(params: Params) -> tuple[bool, str]:
    if params.island not in ISLANDS:
        return False, f"unknown island: {params.island}"
    if params.evidence not in EVIDENCE:
        return False, f"unknown evidence: {params.evidence}"
    if params.witness not in WITNESSES:
        return False, f"unknown witness: {params.witness}"
    if params.method not in METHODS:
        return False, f"unknown method: {params.method}"
    if params.island == "mesa" and params.method == "untie":
        return False, "Mesa Moth Island is moving freely; there is no anchor to untie"
    if params.witness == "mayor" and params.method == "confess":
        return False, "Mayor Quill will not give an honest account without another clue first"
    if params.evidence == "ledger" and params.method == "weigh":
        return False, "the honest ledger cannot be solved by weighing dust"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(island, evidence, witness, method)
        for island in ISLANDS
        for evidence in EVIDENCE
        for witness in WITNESSES
        for method in METHODS
        if valid_params(Params(island, evidence, witness, method))[0]
    ]


def make_world(params: Params) -> IslandWorld:
    island = ISLANDS[params.island]
    evidence = EVIDENCE[params.evidence]
    witness = WITNESSES[params.witness]
    world = IslandWorld(params)
    world.add_entity(Entity("detective", "Detective Mira", "detective", {"Honesty": 2, "Curiosity": 2}))
    world.add_entity(Entity("island", island.name, "place", {"Dust": island.dust, "Float": 1}))
    world.add_entity(Entity("evidence", evidence.name, "physical", {"Clue": evidence.clarity}))
    world.add_entity(Entity("witness", witness.name, "person", {"Honesty": witness.honesty}))
    world.facts["oddity"] = island.oddity
    world.facts["clue"] = evidence.clue
    world.facts["answer"] = evidence.points_to
    world.facts["secret"] = witness.secret
    return world


def arrive(world: IslandWorld) -> None:
    island = ISLANDS[world.params.island]
    world.record(
        "arrive",
        f"Detective Mira reached {island.name}, where {island.oddity}.",
        "detective",
        "island",
        dust=island.dust,
    )


def collect_evidence(world: IslandWorld) -> None:
    evidence = EVIDENCE[world.params.evidence]
    world.record(
        "evidence",
        f"She found the {evidence.name}: {evidence.clue}.",
        "detective",
        "evidence",
        clarity=evidence.clarity,
    )


def hear_witness(world: IslandWorld) -> None:
    witness = WITNESSES[world.params.witness]
    world.record(
        "witness",
        f"{witness.name} admitted they {witness.secret}.",
        "witness",
        "detective",
        honesty=witness.honesty,
        trust=1 if witness.honesty else 0,
    )


def predict_method(world: IslandWorld) -> str:
    imagined = copy.deepcopy(world)
    method = METHODS[imagined.params.method]
    aligned = method.tests == imagined.facts["answer"]
    imagined.meters["solve"] += method.solve + (1 if aligned else -1)
    if imagined.meters["solve"] + imagined.meters["honesty"] >= imagined.meters["dust"] + 3:
        return "Mira saw the twist forming: the island was not hiding a crime so much as floating away from a lie."
    return "Mira saw that a clever test without honesty would leave the island dusty and drifting."


def test_case(world: IslandWorld) -> None:
    method = METHODS[world.params.method]
    aligned = method.tests == world.facts["answer"]
    solve = method.solve + (1 if aligned else -1)
    world.record(
        "test",
        f"Mira chose to {method.name}: she would {method.action}.",
        "detective",
        "island",
        solve=solve,
        clarity=1 if aligned else 0,
    )
    world.facts["method_action"] = method.action
    world.facts["aligned"] = aligned


def reveal_twist(world: IslandWorld) -> None:
    solved = (
        world.meters["solve"] >= 3
        and world.meters["clarity"] >= 3
        and world.meters["honesty"] >= 2
        and bool(world.facts["aligned"])
    )
    if solved:
        truth = truth_clause(str(world.facts["secret"]))
        world.record(
            "twist",
            f"The twist was that the dusty island could float only while people denied that {truth}.",
            "island",
            "detective",
            trust=1,
        )
        world.facts["ending"] = "solved"
    else:
        world.record(
            "partial",
            "The island dipped lower, but a dusty gust showed that one honest fact was still missing.",
            "island",
            "detective",
        )
        world.facts["ending"] = "partial"
    world.entities["detective"].memes["Honesty"] = world.meters["honesty"]
    world.entities["island"].memes["Float"] = 0 if solved else 1


def render_story(world: IslandWorld, prediction: str) -> str:
    lines = [
        "Detective Mira believed every mystery deserved one honest sentence before any accusation.",
        world.history[0].text,
        world.history[1].text,
        world.history[2].text,
        prediction,
        world.history[3].text,
        world.history[4].text,
    ]
    if world.facts["ending"] == "solved":
        lines.append("When the truth was spoken, the island stopped trying to float away from the town.")
    else:
        lines.append("Mira closed her notebook gently, knowing the case would solve itself only when someone chose honesty.")
    return "\n".join(lines)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    arrive(world)
    collect_evidence(world)
    hear_witness(world)
    prediction = predict_method(world)
    world.facts["prediction"] = prediction
    test_case(world)
    reveal_twist(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a detective story with a dusty island and the word honest.",
        "Include a twist involving something that can float.",
        "Make problem solving depend on evidence, honesty, and state.",
    ]
    story_qa = [
        QAItem(
            "What was the twist in the case?",
            (
                f"The twist was that the dusty island could float while people denied that {truth_clause(str(world.facts['secret']))}. "
                "That answer came from the witness secret and the final island state."
                if world.facts["ending"] == "solved"
                else "The story only partly revealed the twist. "
                f"The world still showed a floating island because honesty reached {world.meters['honesty']} and the final state was partial."
            ),
        ),
        QAItem(
            "How did Mira use problem solving?",
            f"Mira used the clue that {world.facts['clue']} and chose to {world.facts['method_action']}. "
            f"The solve meter ended at {world.meters['solve']}.",
        ),
    ]
    world_qa = [
        QAItem(
            "Was the dusty island case solved?",
            f"The ending state is {world.facts['ending']}. "
            f"Clarity ended at {world.meters['clarity']}, honesty at {world.meters['honesty']}, and solve at {world.meters['solve']}.",
        ),
        QAItem(
            "Which evidence pointed to the answer?",
            f"The evidence was {world.entities['evidence'].name}. "
            f"It pointed to {world.facts['answer']}, and the method was {'aligned' if world.facts['aligned'] else 'not aligned'} with it.",
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
    for key in ISLANDS:
        facts.append(f"island({atom(key)}).")
    for key in EVIDENCE:
        facts.append(f"evidence({atom(key)}).")
    for key in WITNESSES:
        facts.append(f"witness({atom(key)}).")
    for key in METHODS:
        facts.append(f"method({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(I,E,W,M) :- I=mesa, M=untie, island(I), evidence(E), witness(W), method(M).",
            "invalid(I,E,W,M) :- W=mayor, M=confess, island(I), evidence(E), witness(W), method(M).",
            "invalid(I,E,W,M) :- E=ledger, M=weigh, island(I), evidence(E), witness(W), method(M).",
            "valid(I,E,W,M) :- island(I), evidence(E), witness(W), method(M), not invalid(I,E,W,M).",
            "#show valid/4.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in item) for item in asp.atoms(model, "valid")}
    py_valid = {(p.island, p.evidence, p.witness, p.method) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid dusty-island detective stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--island", choices=sorted(ISLANDS))
    parser.add_argument("--evidence", choices=sorted(EVIDENCE))
    parser.add_argument("--witness", choices=sorted(WITNESSES))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--seed", type=int, default=23)
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
    explicit = any(value is not None for value in (args.island, args.evidence, args.witness, args.method))
    if explicit:
        params = Params(
            island=args.island or rng.choice(list(ISLANDS)),
            evidence=args.evidence or rng.choice(list(EVIDENCE)),
            witness=args.witness or rng.choice(list(WITNESSES)),
            method=args.method or rng.choice(list(METHODS)),
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
