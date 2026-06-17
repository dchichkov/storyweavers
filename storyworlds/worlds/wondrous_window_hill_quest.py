#!/usr/bin/env python3
"""A heartwarming quest across a dusty hill to a wondrous window."""

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
class Hill:
    id: str
    name: str
    hardship: str
    dust: int


@dataclass(frozen=True)
class Window:
    id: str
    name: str
    wonder: str
    need: str


@dataclass(frozen=True)
class Memory:
    id: str
    name: str
    flashback: str
    warmth: int


@dataclass(frozen=True)
class Conflict:
    id: str
    name: str
    pressure: str
    damage: int


@dataclass(frozen=True)
class Choice:
    id: str
    name: str
    action: str
    helps: str
    repair: int


@dataclass(frozen=True)
class Params:
    hill: str
    window: str
    memory: str
    conflict: str
    choice: str


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
class QuestWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)
    meters: dict[str, int] = field(
        default_factory=lambda: {"dust": 0, "warmth": 0, "repair": 0, "conflict": 0, "hope": 0}
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


HILLS = {
    "chalk": Hill("chalk", "the chalky dusty hill", "white dust turned every footprint into a question", 2),
    "thorn": Hill("thorn", "the thorn-dust hill", "dry brambles tugged at sleeves and tempers", 3),
    "sunset": Hill("sunset", "the sunset dusty hill", "gold dust made the long road look gentler than it felt", 1),
}

WINDOWS = {
    "kitchen": Window("kitchen", "the kitchen's wondrous window", "showed every lonely supper becoming shared", "family"),
    "school": Window("school", "the schoolhouse wondrous window", "showed shy voices turning into a chorus", "courage"),
    "barn": Window("barn", "the barn's wondrous window", "showed lost animals finding their way home", "home"),
}

MEMORIES = {
    "grandma": Memory("grandma", "Grandma's ribbon", "Grandma once tied a red ribbon on the sill and said, 'Bring wonder back kindly.'", 3),
    "friend": Memory("friend", "Milo's promise", "Milo once promised to wait at the hilltop no matter how dusty the day became.", 2),
    "song": Memory("song", "the window song", "A little song from last winter remembered how the glass brightened when people forgave each other.", 3),
}

CONFLICTS = {
    "storm": Conflict("storm", "dust storm", "a dust storm tried to bury the path before anyone could apologize", 3),
    "rival": Conflict("rival", "jealous rival", "a jealous rival wanted the window hidden from everyone else", 2),
    "crack": Conflict("crack", "growing crack", "a crack spread through the glass whenever anger was spoken near it", 3),
}

CHOICES = {
    "share": Choice("share", "share the memory", "tell the remembered promise aloud", "family", 3),
    "guide": Choice("guide", "guide the rival", "help the rival climb instead of racing ahead", "courage", 2),
    "mend": Choice("mend", "mend the frame", "patch the window frame with ribbon and patience", "home", 3),
}


def valid_params(params: Params) -> tuple[bool, str]:
    if params.hill not in HILLS:
        return False, f"unknown hill: {params.hill}"
    if params.window not in WINDOWS:
        return False, f"unknown window: {params.window}"
    if params.memory not in MEMORIES:
        return False, f"unknown memory: {params.memory}"
    if params.conflict not in CONFLICTS:
        return False, f"unknown conflict: {params.conflict}"
    if params.choice not in CHOICES:
        return False, f"unknown choice: {params.choice}"
    if params.hill == "thorn" and params.choice == "guide":
        return False, "the thorn-dust hill is too narrow for guiding another climber safely"
    if params.window == "school" and params.conflict == "storm":
        return False, "the schoolhouse window cannot be reached during the full dust storm"
    if params.memory == "friend" and params.choice == "mend":
        return False, "Milo's promise helps people, not a broken wooden frame"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(hill, window, memory, conflict, choice)
        for hill in HILLS
        for window in WINDOWS
        for memory in MEMORIES
        for conflict in CONFLICTS
        for choice in CHOICES
        if valid_params(Params(hill, window, memory, conflict, choice))[0]
    ]


def make_world(params: Params) -> QuestWorld:
    hill = HILLS[params.hill]
    window = WINDOWS[params.window]
    memory = MEMORIES[params.memory]
    conflict = CONFLICTS[params.conflict]
    world = QuestWorld(params)
    world.add_entity(Entity("hero", "Anya", "child", {"Kindness": 2, "Hope": 1}))
    world.add_entity(Entity("hill", hill.name, "place", {"Dust": hill.dust}))
    world.add_entity(Entity("window", window.name, "physical", {"Wonder": 3, "Need": 1}))
    world.add_entity(Entity("memory", memory.name, "memory", {"Warmth": memory.warmth}))
    world.add_entity(Entity("conflict", conflict.name, "force", {"Conflict": conflict.damage}))
    world.facts["window_need"] = window.need
    world.facts["hardship"] = hill.hardship
    world.facts["pressure"] = conflict.pressure
    return world


def begin_quest(world: QuestWorld) -> None:
    hill = HILLS[world.params.hill]
    window = WINDOWS[world.params.window]
    world.record(
        "quest",
        f"Anya began her quest over {hill.name} because {window.name} had gone dim.",
        "hero",
        "window",
        dust=hill.dust,
        hope=1,
    )


def cross_hill(world: QuestWorld) -> None:
    hill = HILLS[world.params.hill]
    world.record(
        "hill",
        f"On the climb, {hill.hardship}.",
        "hill",
        "hero",
        dust=1,
    )


def flashback(world: QuestWorld) -> None:
    memory = MEMORIES[world.params.memory]
    world.record(
        "flashback",
        f"Then Anya remembered: {memory.flashback}",
        "memory",
        "hero",
        warmth=memory.warmth,
    )
    world.facts["flashback"] = memory.flashback


def raise_conflict(world: QuestWorld) -> None:
    conflict = CONFLICTS[world.params.conflict]
    world.record(
        "conflict",
        f"Near the top, {conflict.pressure}.",
        "conflict",
        "hero",
        conflict=conflict.damage,
        hope=-1,
    )


def predict_choice(world: QuestWorld) -> str:
    imagined = copy.deepcopy(world)
    choice = CHOICES[imagined.params.choice]
    aligned = choice.helps == imagined.facts["window_need"]
    imagined.meters["repair"] += choice.repair + (1 if aligned else -1)
    if imagined.meters["warmth"] + imagined.meters["repair"] > imagined.meters["dust"] + imagined.meters["conflict"]:
        return "Anya could almost see that a warm choice would clear more than dust from the glass."
    return "Anya sensed that a useful choice made without warmth would leave the window cloudy."


def make_choice(world: QuestWorld) -> None:
    choice = CHOICES[world.params.choice]
    aligned = choice.helps == world.facts["window_need"]
    repair = choice.repair + (1 if aligned else -1)
    world.record(
        "choice",
        f"Anya chose to {choice.name}: she would {choice.action}.",
        "hero",
        "window",
        repair=repair,
        hope=1 if aligned else 0,
    )
    world.facts["choice_action"] = choice.action
    world.facts["aligned"] = aligned


def resolve_window(world: QuestWorld) -> None:
    success = (
        world.meters["repair"] >= 3
        and world.meters["warmth"] >= 2
        and world.meters["hope"] >= 1
        and bool(world.facts["aligned"])
    )
    if success:
        world.record(
            "homecoming",
            f"The wondrous window brightened because it needed {world.facts['window_need']}, not victory.",
            "window",
            "hero",
            hope=2,
        )
        world.facts["ending"] = "restored"
    else:
        world.record(
            "still_cloudy",
            "The window glimmered, but a cloudy corner remained for another gentler try.",
            "window",
            "hero",
        )
        world.facts["ending"] = "partial"
    world.entities["hero"].memes["Hope"] = world.meters["hope"]
    world.entities["window"].memes["Wonder"] = 3 if success else 1


def render_story(world: QuestWorld, prediction: str) -> str:
    lines = [
        "Everyone said the wondrous window only opened for people who came back with a softer heart.",
        world.history[0].text,
        world.history[1].text,
        world.history[2].text,
        world.history[3].text,
        prediction,
        world.history[4].text,
        world.history[5].text,
    ]
    if world.facts["ending"] == "restored":
        lines.append("When Anya looked through it, she saw the dusty hill shining like a road home.")
    else:
        lines.append("Anya sat beside the sill anyway, warm enough to try again before sunset.")
    return "\n".join(lines)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    begin_quest(world)
    cross_hill(world)
    flashback(world)
    raise_conflict(world)
    prediction = predict_choice(world)
    world.facts["prediction"] = prediction
    make_choice(world)
    resolve_window(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a heartwarming quest with a wondrous window and a dusty hill.",
        "Use a flashback to carry emotional state into the present conflict.",
        "Make the window's outcome depend on simulated warmth, repair, and alignment.",
    ]
    story_qa = [
        QAItem(
            "What flashback helped Anya?",
            f"The flashback was: {world.facts['flashback']} "
            f"It raised warmth to {world.meters['warmth']}, which helped determine the window's outcome.",
        ),
        QAItem(
            "What conflict stood in the way?",
            f"The conflict was that {world.facts['pressure']}. "
            f"Anya answered by choosing to {world.facts['choice_action']}.",
        ),
    ]
    world_qa = [
        QAItem(
            "Was the wondrous window restored?",
            f"The ending state is {world.facts['ending']}. "
            f"Repair ended at {world.meters['repair']}, warmth at {world.meters['warmth']}, and hope at {world.meters['hope']}.",
        ),
        QAItem(
            "What did the window need?",
            f"The window needed {world.facts['window_need']}. "
            f"The chosen action was {'aligned' if world.facts['aligned'] else 'not aligned'} with that need.",
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
    for key in HILLS:
        facts.append(f"hill({atom(key)}).")
    for key in WINDOWS:
        facts.append(f"window({atom(key)}).")
    for key in MEMORIES:
        facts.append(f"memory({atom(key)}).")
    for key in CONFLICTS:
        facts.append(f"conflict({atom(key)}).")
    for key in CHOICES:
        facts.append(f"choice({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(H,W,M,F,C) :- H=thorn, C=guide, hill(H), window(W), memory(M), conflict(F), choice(C).",
            "invalid(H,W,M,F,C) :- W=school, F=storm, hill(H), window(W), memory(M), conflict(F), choice(C).",
            "invalid(H,W,M,F,C) :- M=friend, C=mend, hill(H), window(W), memory(M), conflict(F), choice(C).",
            "valid(H,W,M,F,C) :- hill(H), window(W), memory(M), conflict(F), choice(C), not invalid(H,W,M,F,C).",
            "#show valid/5.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in item) for item in asp.atoms(model, "valid")}
    py_valid = {(p.hill, p.window, p.memory, p.conflict, p.choice) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid wondrous-window quests."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hill", choices=sorted(HILLS))
    parser.add_argument("--window", choices=sorted(WINDOWS))
    parser.add_argument("--memory", choices=sorted(MEMORIES))
    parser.add_argument("--conflict", choices=sorted(CONFLICTS))
    parser.add_argument("--choice", choices=sorted(CHOICES))
    parser.add_argument("--seed", type=int, default=19)
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
    explicit = any(
        value is not None
        for value in (args.hill, args.window, args.memory, args.conflict, args.choice)
    )
    if explicit:
        params = Params(
            hill=args.hill or rng.choice(list(HILLS)),
            window=args.window or rng.choice(list(WINDOWS)),
            memory=args.memory or rng.choice(list(MEMORIES)),
            conflict=args.conflict or rng.choice(list(CONFLICTS)),
            choice=args.choice or rng.choice(list(CHOICES)),
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
