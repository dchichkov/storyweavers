#!/usr/bin/env python3
"""A detective story about a wobbly bush, a loud window, and a repeated clue."""

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
class Yard:
    id: str
    name: str
    setting: str
    clutter: int


@dataclass(frozen=True)
class Bush:
    id: str
    name: str
    wobble: str
    repeats: int


@dataclass(frozen=True)
class Window:
    id: str
    name: str
    noise: str
    lesson_need: str


@dataclass(frozen=True)
class Suspect:
    id: str
    name: str
    excuse: str
    pressure: int


@dataclass(frozen=True)
class Test:
    id: str
    name: str
    action: str
    checks: str
    insight: int


@dataclass(frozen=True)
class Params:
    yard: str
    bush: str
    window: str
    suspect: str
    test: str


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
class WindowWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)
    meters: dict[str, int] = field(
        default_factory=lambda: {"noise": 0, "repeats": 0, "insight": 0, "lesson": 0, "trust": 0}
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


YARDS = {
    "school": Yard("school", "the schoolyard", "chalk dust lay in loops around the fence", 1),
    "library": Yard("library", "the library garden", "fallen labels hid among the leaves", 2),
    "station": Yard("station", "the old train-yard", "ticket stubs skittered under every bench", 3),
}

BUSHES = {
    "rose": Bush("rose", "wobbly rose bush", "shook three times whenever anyone said 'missing'", 3),
    "mint": Bush("mint", "wobbly mint bush", "leaned left, straightened, then leaned left again", 2),
    "holly": Bush("holly", "wobbly holly bush", "rattled as if something tiny knocked inside it", 2),
}

WINDOWS = {
    "attic": Window("attic", "loud attic window", "banged once for every repeated clue", "listen"),
    "kitchen": Window("kitchen", "loud kitchen window", "whistled whenever someone guessed too fast", "patience"),
    "ticket": Window("ticket", "loud ticket-window", "clacked open and shut like a nervous mouth", "ask"),
}

SUSPECTS = {
    "janitor": Suspect("janitor", "Mr. Broom", "claimed the bush was only windy", 1),
    "cat": Suspect("cat", "Button the cat", "sat too neatly beside the loud window", 2),
    "clerk": Suspect("clerk", "Nima the clerk", "kept repeating the same wrong time", 1),
}

TESTS = {
    "repeat": Test("repeat", "repeat the clue aloud", "say the bush's pattern back exactly", "listen", 3),
    "wait": Test("wait", "wait through the noise", "let the loud window finish before judging", "patience", 3),
    "ask": Test("ask", "ask the quiet witness", "ask who benefited from the racket", "ask", 2),
}


def lesson_phrase(lesson: str) -> str:
    return {
        "listen": "listen",
        "patience": "be patient",
        "ask": "ask a better question",
    }.get(lesson, lesson)


def valid_params(params: Params) -> tuple[bool, str]:
    if params.yard not in YARDS:
        return False, f"unknown yard: {params.yard}"
    if params.bush not in BUSHES:
        return False, f"unknown bush: {params.bush}"
    if params.window not in WINDOWS:
        return False, f"unknown window: {params.window}"
    if params.suspect not in SUSPECTS:
        return False, f"unknown suspect: {params.suspect}"
    if params.test not in TESTS:
        return False, f"unknown test: {params.test}"
    if params.yard == "station" and params.bush == "rose":
        return False, "the rose bush cannot grow in the old train-yard"
    if params.window == "ticket" and params.test == "wait":
        return False, "waiting at the ticket-window only repeats the same noise"
    if params.suspect == "cat" and params.test == "ask":
        return False, "Button the cat cannot answer the quiet-witness question"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(yard, bush, window, suspect, test)
        for yard in YARDS
        for bush in BUSHES
        for window in WINDOWS
        for suspect in SUSPECTS
        for test in TESTS
        if valid_params(Params(yard, bush, window, suspect, test))[0]
    ]


def make_world(params: Params) -> WindowWorld:
    yard = YARDS[params.yard]
    bush = BUSHES[params.bush]
    window = WINDOWS[params.window]
    suspect = SUSPECTS[params.suspect]
    world = WindowWorld(params)
    world.add_entity(Entity("detective", "Pip", "child detective", {"Curiosity": 2, "Patience": 1}))
    world.add_entity(Entity("bush", bush.name, "physical", {"Wobble": bush.repeats}))
    world.add_entity(Entity("window", window.name, "physical", {"Noise": 2}))
    world.add_entity(Entity("yard", yard.name, "place", {"Clutter": yard.clutter}))
    world.add_entity(Entity("suspect", suspect.name, "suspect", {"Pressure": suspect.pressure}))
    world.facts["setting"] = yard.setting
    world.facts["wobble"] = bush.wobble
    world.facts["noise"] = window.noise
    world.facts["lesson_need"] = window.lesson_need
    world.facts["excuse"] = suspect.excuse
    return world


def enter_case(world: WindowWorld) -> None:
    yard = YARDS[world.params.yard]
    window = WINDOWS[world.params.window]
    world.record(
        "enter",
        f"Pip entered {yard.name}, where {yard.setting}, and heard the {window.name} start its noisy warning.",
        "detective",
        "yard",
        noise=yard.clutter,
    )


def observe_repetition(world: WindowWorld) -> None:
    bush = BUSHES[world.params.bush]
    window = WINDOWS[world.params.window]
    world.record(
        "repeat_one",
        f"The {bush.name} {bush.wobble}; then the {window.name} {window.noise}.",
        "bush",
        "window",
        repeats=bush.repeats,
        noise=1,
    )


def repeat_observation(world: WindowWorld) -> None:
    bush = BUSHES[world.params.bush]
    world.record(
        "repeat_two",
        f"It happened again: the {bush.name} repeated its wobble before anyone touched the latch.",
        "bush",
        "detective",
        repeats=1,
        insight=1,
    )


def hear_excuse(world: WindowWorld) -> None:
    suspect = SUSPECTS[world.params.suspect]
    world.record(
        "suspect",
        f"{suspect.name} {suspect.excuse}.",
        "suspect",
        "detective",
        trust=max(0, 2 - suspect.pressure),
    )


def predict_lesson(world: WindowWorld) -> str:
    imagined = copy.deepcopy(world)
    test = TESTS[imagined.params.test]
    aligned = test.checks == imagined.facts["lesson_need"]
    imagined.meters["insight"] += test.insight + (1 if aligned else -1)
    if imagined.meters["insight"] >= imagined.meters["noise"] and aligned:
        return "Pip realized the surprise would appear only if he learned the lesson before naming the culprit."
    return "Pip realized that solving too quickly would make the loud window repeat the warning again."


def run_test(world: WindowWorld) -> None:
    test = TESTS[world.params.test]
    aligned = test.checks == world.facts["lesson_need"]
    insight = test.insight + (1 if aligned else -1)
    world.record(
        "test",
        f"Pip chose to {test.name}: he would {test.action}.",
        "detective",
        "window",
        insight=insight,
        lesson=1 if aligned else 0,
    )
    world.facts["test_action"] = test.action
    world.facts["aligned"] = aligned


def reveal_surprise(world: WindowWorld) -> None:
    solved = (
        world.meters["insight"] >= 4
        and world.meters["lesson"] >= 1
        and world.meters["repeats"] >= 3
        and bool(world.facts["aligned"])
    )
    if solved:
        world.record(
            "surprise",
            f"The surprise was that the loud window was repeating the {world.facts['lesson_need']} lesson, not accusing anyone.",
            "window",
            "detective",
            trust=1,
        )
        world.facts["ending"] = "solved"
    else:
        world.record(
            "not_yet",
            "The window quieted for a moment, but the wobbly bush began its pattern once more.",
            "window",
            "bush",
        )
        world.facts["ending"] = "partial"
    world.entities["detective"].memes["Lesson"] = world.meters["lesson"]
    world.entities["window"].memes["Noise"] = 0 if solved else 2


def render_story(world: WindowWorld, prediction: str) -> str:
    lines = [
        "Pip liked detective cases best when they taught him something before they named a culprit, so he tried to listen even when the clues were loud.",
        world.history[0].text,
        world.history[1].text,
        world.history[2].text,
        world.history[3].text,
        prediction,
        world.history[4].text,
        world.history[5].text,
    ]
    if world.facts["ending"] == "solved":
        lines.append(f"After that, Pip wrote the lesson twice: {lesson_phrase(str(world.facts['lesson_need']))} before chasing surprise.")
    else:
        lines.append("After that, Pip stayed beside the bush, ready to learn the pattern instead of outrunning it.")
    return "\n".join(lines)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    enter_case(world)
    observe_repetition(world)
    repeat_observation(world)
    hear_excuse(world)
    prediction = predict_lesson(world)
    world.facts["prediction"] = prediction
    run_test(world)
    reveal_surprise(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a detective story with a wobbly bush and a loud window.",
        "Use repetition as evidence, not filler.",
        "Make the surprise and lesson come from simulated state.",
    ]
    story_qa = [
        QAItem(
            "What repeated clue mattered?",
            f"The bush {world.facts['wobble']} before the loud window made its noise. "
            "Because the pattern came first, Pip knew the window was warning him rather than accusing someone.",
        ),
        QAItem(
            "What lesson did Pip learn?",
            (
                f"Pip learned to {lesson_phrase(str(world.facts['lesson_need']))} before accusing anyone. "
                f"He tested that by choosing to {world.facts['test_action']}."
                if world.facts["ending"] == "solved"
                else f"Pip had not fully learned to {lesson_phrase(str(world.facts['lesson_need']))} yet. "
                f"He tried to {world.facts['test_action']}, but the ending stayed partial."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            "Was the loud-window case solved?",
            (
                "Yes. Pip matched the test to the window's lesson, so the repeated clue became an answer."
                if world.facts["ending"] == "solved"
                else "Not fully. Pip noticed the repeated pattern, but his test did not match the lesson the loud window was repeating."
            ),
        ),
        QAItem(
            "Which suspect excuse was recorded?",
            f"The suspect was {world.entities['suspect'].name}. "
            f"The recorded excuse was that they {world.facts['excuse']}.",
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
    for key in YARDS:
        facts.append(f"yard({atom(key)}).")
    for key in BUSHES:
        facts.append(f"bush({atom(key)}).")
    for key in WINDOWS:
        facts.append(f"window({atom(key)}).")
    for key in SUSPECTS:
        facts.append(f"suspect({atom(key)}).")
    for key in TESTS:
        facts.append(f"test({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(Y,B,W,S,T) :- Y=station, B=rose, yard(Y), bush(B), window(W), suspect(S), test(T).",
            "invalid(Y,B,W,S,T) :- W=ticket, T=wait, yard(Y), bush(B), window(W), suspect(S), test(T).",
            "invalid(Y,B,W,S,T) :- S=cat, T=ask, yard(Y), bush(B), window(W), suspect(S), test(T).",
            "valid(Y,B,W,S,T) :- yard(Y), bush(B), window(W), suspect(S), test(T), not invalid(Y,B,W,S,T).",
            "#show valid/5.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in item) for item in asp.atoms(model, "valid")}
    py_valid = {(p.yard, p.bush, p.window, p.suspect, p.test) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid wobbly-bush detective stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yard", choices=sorted(YARDS))
    parser.add_argument("--bush", choices=sorted(BUSHES))
    parser.add_argument("--window", choices=sorted(WINDOWS))
    parser.add_argument("--suspect", choices=sorted(SUSPECTS))
    parser.add_argument("--test", choices=sorted(TESTS))
    parser.add_argument("--seed", type=int, default=29)
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
    explicit = any(value is not None for value in (args.yard, args.bush, args.window, args.suspect, args.test))
    if explicit:
        params = Params(
            yard=args.yard or rng.choice(list(YARDS)),
            bush=args.bush or rng.choice(list(BUSHES)),
            window=args.window or rng.choice(list(WINDOWS)),
            suspect=args.suspect or rng.choice(list(SUSPECTS)),
            test=args.test or rng.choice(list(TESTS)),
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
