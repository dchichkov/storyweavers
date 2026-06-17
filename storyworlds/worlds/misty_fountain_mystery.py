#!/usr/bin/env python3
"""A stateful mystery about solving the trouble at a misty fountain."""

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
class Fountain:
    id: str
    name: str
    symptom: str
    fog: int


@dataclass(frozen=True)
class Clue:
    id: str
    name: str
    reveals: str
    clarity: int


@dataclass(frozen=True)
class Suspect:
    id: str
    name: str
    motive: str
    pressure: int


@dataclass(frozen=True)
class Fix:
    id: str
    name: str
    targets: str
    repair: int


@dataclass(frozen=True)
class Params:
    fountain: str
    clue: str
    suspect: str
    fix: str


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
class FountainWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, int] = field(
        default_factory=lambda: {"mist": 0, "clarity": 0, "repair": 0, "trust": 0}
    )
    facts: dict[str, str | int | bool] = field(default_factory=dict)

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


FOUNTAINS = {
    "lion": Fountain("lion", "the lion-mouth fountain", "mist poured from the stone teeth instead of water", 2),
    "moon": Fountain("moon", "the moon-basin fountain", "the reflection stayed cloudy even under noon sun", 3),
    "shell": Fountain("shell", "the shell fountain", "each splash sounded like a whispered accusation", 1),
}

CLUES = {
    "coin": Clue("coin", "bent silver coin", "a jammed wish-slot", 2),
    "petal": Clue("petal", "blue glass petal", "a hidden valve below the basin", 3),
    "thread": Clue("thread", "red silk thread", "a tied-off pump chain", 2),
}

SUSPECTS = {
    "gardener": Suspect("gardener", "Mara the gardener", "wanted the dry roses blamed on the fountain", 1),
    "mayor": Suspect("mayor", "Mayor Pell", "wanted the old fountain replaced", 2),
    "vendor": Suspect("vendor", "Tobin the tea vendor", "wanted the square quiet before dawn", 1),
}

FIXES = {
    "filter": Fix("filter", "clear the bronze filter", "slot", 2),
    "valve": Fix("valve", "turn the hidden valve", "valve", 3),
    "untie": Fix("untie", "untie the pump chain", "chain", 3),
}


def valid_params(params: Params) -> tuple[bool, str]:
    if params.fountain not in FOUNTAINS:
        return False, f"unknown fountain: {params.fountain}"
    if params.clue not in CLUES:
        return False, f"unknown clue: {params.clue}"
    if params.suspect not in SUSPECTS:
        return False, f"unknown suspect: {params.suspect}"
    if params.fix not in FIXES:
        return False, f"unknown fix: {params.fix}"
    if params.fountain == "moon" and params.clue == "coin":
        return False, "the moon-basin fountain is too deep for the bent coin clue"
    if params.suspect == "mayor" and params.fix == "untie":
        return False, "the mayor's scheme leaves documents, not a tied pump chain"
    if params.clue == "petal" and params.fix == "filter":
        return False, "the blue glass petal points below the basin, not into the filter"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(fountain, clue, suspect, fix)
        for fountain in FOUNTAINS
        for clue in CLUES
        for suspect in SUSPECTS
        for fix in FIXES
        if valid_params(Params(fountain, clue, suspect, fix))[0]
    ]


def make_world(params: Params) -> FountainWorld:
    fountain = FOUNTAINS[params.fountain]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    world = FountainWorld(params)
    world.add_entity(Entity("detective", "Lina", "child detective", {"Curiosity": 3}))
    world.add_entity(Entity("fountain", fountain.name, "physical", {"Mist": fountain.fog}))
    world.add_entity(Entity("clue", clue.name, "physical", {"Clue": clue.clarity}))
    world.add_entity(Entity("suspect", suspect.name, "person", {"Motive": suspect.pressure}))
    world.facts["problem"] = fountain.symptom
    world.facts["answer"] = clue.reveals
    world.facts["motive"] = suspect.motive
    return world


def observe_problem(world: FountainWorld) -> None:
    fountain = FOUNTAINS[world.params.fountain]
    world.record(
        "observe",
        f"Lina found {fountain.name} in trouble: {fountain.symptom}.",
        "detective",
        "fountain",
        mist=fountain.fog,
    )


def collect_clue(world: FountainWorld) -> None:
    clue = CLUES[world.params.clue]
    world.record(
        "clue",
        f"Inside the mist she noticed a {clue.name}, which suggested {clue.reveals}.",
        "detective",
        "clue",
        clarity=clue.clarity,
    )
    world.facts["clue_seen"] = clue.name


def question_suspect(world: FountainWorld) -> None:
    suspect = SUSPECTS[world.params.suspect]
    world.record(
        "question",
        f"{suspect.name} admitted they {suspect.motive}.",
        "detective",
        "suspect",
        clarity=1,
        trust=max(0, 2 - suspect.pressure),
    )


def predict_fix(world: FountainWorld) -> str:
    imagined = copy.deepcopy(world)
    fix = FIXES[imagined.params.fix]
    aligned = fix.targets in imagined.facts["answer"]
    imagined.meters["repair"] += fix.repair + (1 if aligned else -1)
    if imagined.meters["repair"] >= 3:
        return "Lina reasoned that the right repair would thin the mist before the square filled with rumors."
    return "Lina saw that a careless repair would move the mist, but not the hidden cause."


def apply_fix(world: FountainWorld) -> None:
    fix = FIXES[world.params.fix]
    aligned = fix.targets in world.facts["answer"]
    repair = fix.repair + (1 if aligned else -1)
    world.record(
        "fix",
        f"Lina decided to {fix.name}, testing the clue against the fountain instead of guessing.",
        "detective",
        "fountain",
        repair=repair,
        mist=-min(world.meters["mist"], repair),
    )
    world.facts["fix"] = fix.name


def resolve_mystery(world: FountainWorld) -> None:
    solved = (
        world.meters["clarity"] >= 3
        and world.meters["repair"] >= 3
        and world.meters["mist"] <= 1
        and FIXES[world.params.fix].targets in world.facts["answer"]
    )
    if solved:
        world.record(
            "clear",
            f"The mist lifted, proving the real problem was {world.facts['answer']}.",
            "fountain",
            "detective",
            trust=1,
        )
        world.facts["ending"] = "solved"
    else:
        world.record(
            "haze",
            "The fountain cleared for one breath, then folded the answer back into mist.",
            "fountain",
            "detective",
        )
        world.facts["ending"] = "partial"
    world.entities["fountain"].memes["Mist"] = world.meters["mist"]
    world.entities["detective"].memes["Trust"] = world.meters["trust"]


def render_story(world: FountainWorld, prediction: str) -> str:
    parts = [
        "The town square had one mystery left after sunset: why the misty fountain would not run clear.",
        world.history[0].text,
        world.history[1].text,
        world.history[2].text,
        prediction,
        world.history[3].text,
        world.history[4].text,
    ]
    if world.facts["ending"] == "solved":
        parts.append("By morning, people made wishes again, and Lina wrote the solution before the mist could steal it.")
    else:
        parts.append("By morning, Lina had narrowed the mystery, but the fountain still kept one wet secret.")
    return "\n".join(parts)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    observe_problem(world)
    collect_clue(world)
    question_suspect(world)
    prediction = predict_fix(world)
    world.facts["prediction"] = prediction
    apply_fix(world)
    resolve_mystery(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a mystery about a misty fountain.",
        "Use problem solving instead of luck.",
        "Ground the answer in clues, repair state, and suspect motive.",
    ]
    story_qa = [
        QAItem(
            "What was wrong with the misty fountain?",
            f"The fountain's visible problem was that {world.facts['problem']}. "
            f"The actual cause was {world.facts['answer']}, which Lina inferred from the clue.",
        ),
        QAItem(
            "How did Lina solve the problem?",
            (
                f"Lina used the {world.facts['clue_seen']} and then chose to {world.facts['fix']}. "
                f"That repair changed the repair meter to {world.meters['repair']} and the mist meter to {world.meters['mist']}."
                if world.facts["ending"] == "solved"
                else f"Lina used the {world.facts['clue_seen']} and tried to {world.facts['fix']}. "
                f"The repair meter reached {world.meters['repair']}, but the world state stayed partial because the fix did not match the cause."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            "Was the fountain mystery solved?",
            f"The ending state is {world.facts['ending']}. "
            f"The world had clarity {world.meters['clarity']}, repair {world.meters['repair']}, and mist {world.meters['mist']}.",
        ),
        QAItem(
            "Which suspect motive was recorded?",
            f"The suspect was {world.entities['suspect'].name}. "
            f"The recorded motive was that they {world.facts['motive']}.",
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
    for key in FOUNTAINS:
        facts.append(f"fountain({atom(key)}).")
    for key in CLUES:
        facts.append(f"clue({atom(key)}).")
    for key in SUSPECTS:
        facts.append(f"suspect({atom(key)}).")
    for key in FIXES:
        facts.append(f"fix({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(F,C,S,X) :- F=moon, C=coin, fountain(F), clue(C), suspect(S), fix(X).",
            "invalid(F,C,S,X) :- S=mayor, X=untie, fountain(F), clue(C), suspect(S), fix(X).",
            "invalid(F,C,S,X) :- C=petal, X=filter, fountain(F), clue(C), suspect(S), fix(X).",
            "valid(F,C,S,X) :- fountain(F), clue(C), suspect(S), fix(X), not invalid(F,C,S,X).",
            "#show valid/4.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in item) for item in asp.atoms(model, "valid")}
    py_valid = {(p.fountain, p.clue, p.suspect, p.fix) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid misty-fountain mysteries."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fountain", choices=sorted(FOUNTAINS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--suspect", choices=sorted(SUSPECTS))
    parser.add_argument("--fix", choices=sorted(FIXES))
    parser.add_argument("--seed", type=int, default=13)
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
    explicit = any(value is not None for value in (args.fountain, args.clue, args.suspect, args.fix))
    if explicit:
        params = Params(
            fountain=args.fountain or rng.choice(list(FOUNTAINS)),
            clue=args.clue or rng.choice(list(CLUES)),
            suspect=args.suspect or rng.choice(list(SUSPECTS)),
            fix=args.fix or rng.choice(list(FIXES)),
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
