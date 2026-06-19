#!/usr/bin/env python3
"""A ghost-story mystery about a feast whose clues foreshadow the answer."""

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
class Room:
    id: str
    name: str
    omen: str
    fear: int


@dataclass(frozen=True)
class Dish:
    id: str
    name: str
    clue: str
    memory: str


@dataclass(frozen=True)
class Suspect:
    id: str
    name: str
    role: str
    secret: str


@dataclass(frozen=True)
class Method:
    id: str
    name: str
    solves: str
    insight: int


@dataclass(frozen=True)
class Params:
    room: str
    dish: str
    suspect: str
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
    subject: str
    target: str | None = None
    delta: dict[str, int] = field(default_factory=dict)


@dataclass
class FeastWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, int] = field(
        default_factory=lambda: {"fear": 0, "clues": 0, "insight": 0, "peace": 0}
    )
    facts: dict[str, str | int | bool] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(
        self,
        event_id: str,
        text: str,
        subject: str,
        target: str | None = None,
        **delta: int,
    ) -> None:
        self.history.append(Event(event_id, text, subject, target, dict(delta)))
        for key, value in delta.items():
            self.meters[key] = self.meters.get(key, 0) + value


ROOMS = {
    "hall": Room("hall", "the candlelit banquet hall", "every empty chair faced the same locked plate", 1),
    "kitchen": Room("kitchen", "the abandoned kitchen", "cold steam curled upward with no fire beneath it", 2),
    "cellar": Room("cellar", "the wine-dark cellar", "the old barrels tapped in the rhythm of a warning", 3),
}

DISHES = {
    "pie": Dish("pie", "blackberry pie", "a silver button baked under the crust", "a vanished servant's coat"),
    "soup": Dish("soup", "midnight soup", "three salt rings floating in the stirred soup", "a promise broken before supper"),
    "bread": Dish("bread", "braided bread", "one braid tied into a tiny noose", "a guest who never reached the table"),
}

SUSPECTS = {
    "butler": Suspect("butler", "Mr. Vale", "butler", "hid the last invitation"),
    "aunt": Suspect("aunt", "Aunt Rowan", "host", "changed the seating chart"),
    "piper": Suspect("piper", "the window piper", "stranger", "played the tune that summoned the dead"),
}

METHODS = {
    "match": Method("match", "match the clue to the place setting", "dish", 2),
    "question": Method("question", "question the living suspect gently", "suspect", 2),
    "toast": Method("toast", "raise a toast to the missing guest", "ghost", 3),
}


def secret_sentence(suspect: Suspect) -> str:
    name = sentence_start(suspect.name)
    return {
        "hid the last invitation": f"{name} had hidden the last invitation.",
        "changed the seating chart": f"{name} had moved a name card before the first bell rang.",
        "played the tune that summoned the dead": f"{name} had played the tune that called the dead to supper.",
    }.get(suspect.secret, f"{suspect.name} knew that {suspect.secret}.")


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def method_sentence(method: Method, suspect: Suspect) -> str:
    if method.id == "match":
        return (
            "Iris set the clue beside the empty place and watched the pattern answer her. "
            f"{secret_sentence(suspect)}"
        )
    if method.id == "question":
        return (
            f"Iris asked {suspect.name} one soft question, then another, until the room itself seemed to listen. "
            f"{secret_sentence(suspect)}"
        )
    return (
        "Iris lifted her glass to the chair no one had claimed and spoke the secret into the candlelight. "
        f"{secret_sentence(suspect)}"
    )


def memory_sentence(memory: str) -> str:
    return {
        "a vanished servant's coat": "the vanished servant whose coat had been left behind",
        "a promise broken before supper": "the promise broken before supper",
        "a guest who never reached the table": "the guest who never reached the table",
    }.get(memory, memory)


def restored_detail(memory: str) -> str:
    return {
        "a vanished servant's coat": "a neat coat hung beside the servant's old chair",
        "a promise broken before supper": "the broken promise was spoken aloud and forgiven",
        "a guest who never reached the table": "the empty chair was finally drawn close to the table",
    }.get(memory, "the old wrong was named and set right")


def opening_sentence(room: Room) -> str:
    return (
        "Iris came to the old house because, once each year, it laid supper for someone no one remembered. "
        f"This year the whispers led her to {room.name}."
    )


def valid_params(params: Params) -> tuple[bool, str]:
    if params.room not in ROOMS:
        return False, f"unknown room: {params.room}"
    if params.dish not in DISHES:
        return False, f"unknown dish: {params.dish}"
    if params.suspect not in SUSPECTS:
        return False, f"unknown suspect: {params.suspect}"
    if params.method not in METHODS:
        return False, f"unknown method: {params.method}"
    if params.room == "cellar" and params.dish == "soup":
        return False, "midnight soup cannot keep its clue intact in the wine-dark cellar"
    if params.suspect == "piper" and params.method == "question":
        return False, "the window piper will not stay long enough to be questioned"
    if params.dish == "bread" and params.method == "toast":
        return False, "the braided bread clue needs inspection before any toast can help"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(room, dish, suspect, method)
        for room in ROOMS
        for dish in DISHES
        for suspect in SUSPECTS
        for method in METHODS
        if valid_params(Params(room, dish, suspect, method))[0]
    ]


def make_world(params: Params) -> FeastWorld:
    room = ROOMS[params.room]
    dish = DISHES[params.dish]
    suspect = SUSPECTS[params.suspect]
    world = FeastWorld(params)
    world.add_entity(Entity("sleuth", "Iris", "child detective", {"Curiosity": 2, "Courage": 1}))
    world.add_entity(Entity("ghost", "the missing guest", "ghost", {"Grief": 3, "Peace": 0}))
    world.add_entity(Entity("feast", "the ghost feast", "physical", {"Mystery": 3}))
    world.add_entity(Entity("dish", dish.name, "physical", {"Clue": 1}))
    world.add_entity(Entity("suspect", suspect.name, suspect.role, {"Secret": 1}))
    world.add_entity(Entity("room", room.name, "place", {"Fear": room.fear}))
    world.facts["answer"] = dish.memory
    world.facts["secret"] = suspect.secret
    return world


def foreshadow(world: FeastWorld) -> None:
    room = ROOMS[world.params.room]
    world.record(
        "foreshadow",
        f"Long before midnight, {room.omen}.",
        "room",
        "sleuth",
        fear=room.fear,
    )
    world.facts["omen_seen"] = True


def reveal_feast(world: FeastWorld) -> None:
    dish = DISHES[world.params.dish]
    suspect = SUSPECTS[world.params.suspect]
    world.record(
        "feast",
        f"When midnight opened like a door, the ghost feast set out {dish.name}; across the table, {suspect.name} went still.",
        "feast",
        "suspect",
        clues=1,
    )
    world.facts["dish_clue"] = dish.clue


def inspect_clue(world: FeastWorld) -> None:
    dish = DISHES[world.params.dish]
    clue_pronoun = "They" if dish.id == "soup" else "It"
    world.record(
        "clue",
        f"Iris found {dish.clue}. {clue_pronoun} pointed toward {memory_sentence(dish.memory)}.",
        "sleuth",
        "dish",
        clues=1,
        insight=1,
    )


def predict_if_wrong(world: FeastWorld) -> str:
    imagined = copy.deepcopy(world)
    imagined.meters["insight"] += METHODS[imagined.params.method].insight
    if imagined.meters["insight"] >= 3:
        return "Iris felt the room waiting for one true memory, not a clever guess."
    return "Iris knew that if she guessed too soon, every covered plate would whisper a different lie."


def solve_mystery(world: FeastWorld) -> None:
    method = METHODS[world.params.method]
    suspect = SUSPECTS[world.params.suspect]
    insight = method.insight
    if method.solves == "dish":
        insight += 1
    if method.solves == "suspect" and suspect.id in {"butler", "aunt"}:
        insight += 1
    world.record(
        "solve",
        method_sentence(method, suspect),
        "sleuth",
        "suspect",
        insight=insight,
    )
    world.facts["method"] = method.name


def settle_ghost(world: FeastWorld) -> None:
    solved = world.meters["insight"] >= 3 and world.meters["clues"] >= 2
    if solved:
        world.record(
            "peace",
            f"The missing guest heard the truth about {memory_sentence(str(world.facts['answer']))}. One by one, the whispering plates fell silent.",
            "ghost",
            "feast",
            peace=1,
        )
        world.facts["ending"] = "solved"
    else:
        world.record(
            "unsettled",
            "The ghost feast folded itself away, but one spoon kept knocking for a better answer.",
            "ghost",
            "feast",
        )
        world.facts["ending"] = "unsettled"
    world.entities["ghost"].memes["Peace"] = world.meters["peace"]
    world.entities["feast"].memes["Mystery"] = 0 if solved else 2


def render_story(world: FeastWorld, prediction: str) -> str:
    room = ROOMS[world.params.room]
    suspect = SUSPECTS[world.params.suspect]
    answer = str(world.facts["answer"])
    parts = [
        opening_sentence(room),
        f"She arrived with a notebook in her coat pocket and found one extra place set at the table, though {suspect.name} would not say who it was for.",
        world.history[0].text,
        world.history[1].text,
        prediction,
        world.history[2].text,
        world.history[3].text,
        world.history[4].text,
    ]
    if world.facts["ending"] == "solved":
        parts.append(
            f"By dawn, {restored_detail(answer)}. Iris stepped out into the pale morning, "
            "and behind her the house kept only enough silence for the living."
        )
    else:
        parts.append(
            "By dawn, Iris had named only part of the truth. She left a candle burning and promised to return before the next midnight feast."
        )
    return "\n".join(parts)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    foreshadow(world)
    reveal_feast(world)
    prediction = predict_if_wrong(world)
    world.facts["prediction"] = prediction
    inspect_clue(world)
    solve_mystery(world)
    settle_ghost(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a ghost story about a feast.",
        "Use foreshadowing before the main clue is explained.",
        "Make the mystery answer come from simulated clues and state.",
    ]
    story_qa = [
        QAItem(
            "Why did Iris come to the old house?",
            f"Iris came because the old house was said to set supper for a forgotten guest once each year. This year's haunting led her to {ROOMS[params.room].name}, where the extra place setting began the mystery.",
        ),
        QAItem(
            "What clue helped solve the ghost feast?",
            f"The important clue was {world.facts['dish_clue']}. "
            f"It pointed Iris toward {memory_sentence(str(world.facts['answer']))}, which is why the ghost could respond to the solution.",
        ),
        QAItem(
            "How did the story foreshadow the mystery?",
            f"The omen appeared before the feast: {ROOMS[params.room].omen}. "
            "That early sign warned Iris that the room itself was trying to identify the right memory.",
        ),
    ]
    world_qa = [
        QAItem(
            "Did Iris truly solve the mystery?",
            f"Yes. Iris gathered enough clues and insight for the feast to quiet, so the ending is {world.facts['ending']} rather than merely postponed.",
        ),
        QAItem(
            "Which suspect secret mattered?",
            f"{secret_sentence(SUSPECTS[params.suspect])} "
            "That secret mattered because Iris used it to connect the clue to the missing guest instead of making a lucky guess.",
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
    for key in ROOMS:
        facts.append(f"room({atom(key)}).")
    for key in DISHES:
        facts.append(f"dish({atom(key)}).")
    for key in SUSPECTS:
        facts.append(f"suspect({atom(key)}).")
    for key in METHODS:
        facts.append(f"method({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(R,D,S,M) :- R=cellar, D=soup, room(R), dish(D), suspect(S), method(M).",
            "invalid(R,D,S,M) :- S=piper, M=question, room(R), dish(D), suspect(S), method(M).",
            "invalid(R,D,S,M) :- D=bread, M=toast, room(R), dish(D), suspect(S), method(M).",
            "valid(R,D,S,M) :- room(R), dish(D), suspect(S), method(M), not invalid(R,D,S,M).",
            "#show valid/4.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in valid) for valid in asp.atoms(model, "valid")}
    py_valid = {(p.room, p.dish, p.suspect, p.method) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid haunted-feast mysteries."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--dish", choices=sorted(DISHES))
    parser.add_argument("--suspect", choices=sorted(SUSPECTS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--seed", type=int, default=11)
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
    explicit = any(value is not None for value in (args.room, args.dish, args.suspect, args.method))
    if explicit:
        params = Params(
            room=args.room or rng.choice(list(ROOMS)),
            dish=args.dish or rng.choice(list(DISHES)),
            suspect=args.suspect or rng.choice(list(SUSPECTS)),
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
