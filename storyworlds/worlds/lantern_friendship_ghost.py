#!/usr/bin/env python3
"""A state-driven ghost story about a lantern and earned friendship."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    mood: str
    risk: int


@dataclass(frozen=True)
class Ghost:
    id: str
    name: str
    grief: str
    need: str


@dataclass(frozen=True)
class Lantern:
    id: str
    name: str
    light: str
    calm_bonus: int


@dataclass(frozen=True)
class Gesture:
    id: str
    name: str
    promise: str
    trust_gain: int
    fear_cost: int


@dataclass(frozen=True)
class Params:
    place: str
    ghost: str
    lantern: str
    gesture: str


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
class GhostWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)
    meters: dict[str, int] = field(
        default_factory=lambda: {"fear": 0, "trust": 0, "friendship": 0, "lantern": 0}
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


PLACES = {
    "attic": Place("attic", "the locked attic", "dust breathed like a sleeping thing", 2),
    "pier": Place("pier", "the foggy pier", "black water knocked under the boards", 3),
    "orchard": Place("orchard", "the moonlit orchard", "bare branches clicked like teeth", 1),
}

GHOSTS = {
    "elias": Ghost("elias", "Elias", "loneliness", "someone to remember his name"),
    "mina": Ghost("mina", "Mina", "betrayal", "someone to return a borrowed keepsake"),
    "ori": Ghost("ori", "Ori", "silence", "someone to carry a final message"),
}

LANTERNS = {
    "blue": Lantern("blue", "blue lantern", "a patient blue flame", 2),
    "brass": Lantern("brass", "brass lantern", "a warm amber flame", 1),
    "cracked": Lantern("cracked", "cracked lantern", "a nervous green flame", 0),
}

GESTURES = {
    "listen": Gesture("listen", "listen without interrupting", "hear the whole sorrow", 3, -1),
    "offer": Gesture("offer", "offer the lantern handle", "share the light instead of owning it", 2, -2),
    "name": Gesture("name", "speak the ghost's name", "treat the haunting as a person", 3, 0),
}


def need_sentence(ghost: Ghost) -> str:
    return f"{ghost.name} needed {ghost.need}"


def choices() -> list[Params]:
    return [
        Params(place=place, ghost=ghost, lantern=lantern, gesture=gesture)
        for place in PLACES
        for ghost in GHOSTS
        for lantern in LANTERNS
        for gesture in GESTURES
        if valid_params(Params(place, ghost, lantern, gesture))[0]
    ]


def valid_params(params: Params) -> tuple[bool, str]:
    if params.place not in PLACES:
        return False, f"unknown place: {params.place}"
    if params.ghost not in GHOSTS:
        return False, f"unknown ghost: {params.ghost}"
    if params.lantern not in LANTERNS:
        return False, f"unknown lantern: {params.lantern}"
    if params.gesture not in GESTURES:
        return False, f"unknown gesture: {params.gesture}"
    if params.place == "pier" and params.lantern == "cracked":
        return False, "the cracked lantern cannot hold its flame on the foggy pier"
    if params.ghost == "mina" and params.gesture == "name":
        return False, "Mina cannot be won by a name alone; she needs a returned trust"
    if params.place == "attic" and params.gesture == "offer":
        return False, "the locked attic is too narrow to safely offer the lantern handle"
    return True, ""


def resolve_params(args: argparse.Namespace) -> Params:
    rng = random.Random(args.seed)
    supplied = {
        "place": args.place,
        "ghost": args.ghost,
        "lantern": args.lantern,
        "gesture": args.gesture,
    }
    if any(value is not None for value in supplied.values()):
        params = Params(
            place=args.place or rng.choice(list(PLACES)),
            ghost=args.ghost or rng.choice(list(GHOSTS)),
            lantern=args.lantern or rng.choice(list(LANTERNS)),
            gesture=args.gesture or rng.choice(list(GESTURES)),
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    return rng.choice(choices())


def make_world(params: Params) -> GhostWorld:
    place = PLACES[params.place]
    ghost = GHOSTS[params.ghost]
    lantern = LANTERNS[params.lantern]
    world = GhostWorld(params)
    world.add_entity(Entity("child", "Nora", "child", {"Courage": 1, "Friendship": 0}))
    world.add_entity(Entity("ghost", ghost.name, "ghost", {"Grief": 3, "Friendship": 0}))
    world.add_entity(Entity("lantern", lantern.name, "physical", {"Light": 1}))
    world.add_entity(Entity("place", place.name, "place", {"Fear": place.risk}))
    world.facts["need"] = ghost.need
    world.facts["mood"] = place.mood
    return world


def enter_haunted_place(world: GhostWorld) -> None:
    place = PLACES[world.params.place]
    lantern = LANTERNS[world.params.lantern]
    fear = max(0, place.risk - lantern.calm_bonus)
    world.record(
        "enter",
        f"Nora carried the {lantern.name} into {place.name}, where {place.mood}.",
        "child",
        "place",
        fear=fear,
        lantern=1,
    )
    world.facts["entered"] = True


def reveal_ghost(world: GhostWorld) -> None:
    ghost = GHOSTS[world.params.ghost]
    lantern = LANTERNS[world.params.lantern]
    world.record(
        "reveal",
        f"In {lantern.light}, the ghost of {ghost.name} appeared with {ghost.grief} in every edge of the air.",
        "ghost",
        "child",
        fear=1,
    )
    world.facts["ghost_visible"] = True


def predict_friendship(world: GhostWorld) -> str:
    imagined = copy.deepcopy(world)
    apply_gesture(imagined, predicted=True)
    if imagined.meters["trust"] >= 3:
        return "If Nora answered gently, the haunting would loosen instead of harden."
    return "If Nora kept too much of the light for herself, the ghost would remain near but wary."


def apply_gesture(world: GhostWorld, predicted: bool = False) -> None:
    ghost = GHOSTS[world.params.ghost]
    gesture = GESTURES[world.params.gesture]
    trust_gain = gesture.trust_gain
    if world.params.lantern == "blue" and gesture.id in {"listen", "name"}:
        trust_gain += 1
    if world.params.ghost == "ori" and gesture.id == "listen":
        trust_gain += 1
    if predicted:
        world.meters["trust"] += trust_gain
        world.meters["fear"] = max(0, world.meters["fear"] + gesture.fear_cost)
        return
    world.record(
        "gesture",
        f"Nora chose to {gesture.name}, promising to {gesture.promise}.",
        "child",
        "ghost",
        trust=trust_gain,
        fear=gesture.fear_cost,
    )
    world.facts["promise"] = gesture.promise


def settle_haunting(world: GhostWorld) -> None:
    ghost = GHOSTS[world.params.ghost]
    place = PLACES[world.params.place]
    friendship = 1 if world.meters["trust"] >= 3 and world.meters["fear"] <= 3 else 0
    if friendship:
        world.record(
            "settle",
            f"{ghost.name} lowered the cold around {place.name} because Nora had treated the haunting as a friend.",
            "ghost",
            "child",
            friendship=1,
        )
        world.facts["ending"] = "friendship"
    else:
        world.record(
            "settle",
            f"{ghost.name} faded only halfway; Nora understood that {need_sentence(ghost)}, but had not answered it fully yet.",
            "ghost",
            "child",
        )
        world.facts["ending"] = "unfinished"
    world.entities["child"].memes["Friendship"] = world.meters["friendship"]
    world.entities["ghost"].memes["Friendship"] = world.meters["friendship"]


def render_story(world: GhostWorld, prediction: str) -> str:
    lines = [
        "Nora did not believe a lantern could make a friend until the night the dark answered back.",
        *[event.text for event in world.history[:2]],
        prediction,
        *[event.text for event in world.history[2:]],
    ]
    if world.facts["ending"] == "friendship":
        lines.append(f"After that, the lantern shone softer whenever Nora passed a lonely place, and {world.entities['ghost'].name} no longer had to haunt it alone.")
    else:
        lines.append("After that, Nora kept the lantern ready, knowing friendship sometimes needed a second brave visit.")
    return "\n".join(lines)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    enter_haunted_place(world)
    reveal_ghost(world)
    prediction = predict_friendship(world)
    world.facts["prediction"] = prediction
    apply_gesture(world)
    settle_haunting(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a ghost story about a lantern.",
        "Use friendship as the way the haunting changes.",
        "Let the answer come from the simulated world state, not a narrator's guess.",
    ]
    story_qa = [
        QAItem(
            "What made the ghost story turn toward friendship?",
            (
                "Nora treated the ghost as someone with a need rather than as a monster. "
                f"Her promise was to {world.facts['promise']}, which raised trust enough to change the haunting."
                if world.facts["ending"] == "friendship"
                else "Nora tried to treat the ghost as someone with a need rather than as a monster. "
                f"Her promise was to {world.facts['promise']}, but the ghost still needed another brave visit before full friendship."
            ),
        ),
        QAItem(
            "Why was the lantern important?",
            f"The {LANTERNS[params.lantern].name} made the ghost visible and reduced Nora's fear. "
            "It also became the physical carrier for the friendship in the ending.",
        ),
    ]
    world_qa = [
        QAItem(
            "Did Nora and the ghost become friends?",
            (
                f"Yes. Nora earned enough trust for {world.entities['ghost'].name} to lower the cold and accept the lantern as a shared light."
                if world.facts["ending"] == "friendship"
                else f"Not yet. Nora lowered the fear, but {world.entities['ghost'].name} still needed more trust before the haunting could become friendship."
            ),
        ),
        QAItem(
            "Which entity held the ghost's need?",
            f"{world.entities['ghost'].name} held the need: {world.facts['need']}. "
            "That need explains why the lantern scene had to become a gesture of care, not a chase.",
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


def asp_program() -> str:
    facts = []
    for key in PLACES:
        facts.append(f"place({asp_atom(key)}).")
    for key in GHOSTS:
        facts.append(f"ghost({asp_atom(key)}).")
    for key in LANTERNS:
        facts.append(f"lantern({asp_atom(key)}).")
    for key in GESTURES:
        facts.append(f"gesture({asp_atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(P,G,L,A) :- P=pier, L=cracked, place(P), ghost(G), lantern(L), gesture(A).",
            "invalid(P,G,L,A) :- G=mina, A=name, place(P), ghost(G), lantern(L), gesture(A).",
            "invalid(P,G,L,A) :- P=attic, A=offer, place(P), ghost(G), lantern(L), gesture(A).",
            "valid(P,G,L,A) :- place(P), ghost(G), lantern(L), gesture(A), not invalid(P,G,L,A).",
            "#show valid/4.",
        ]
    )


def asp_atom(value: str) -> str:
    return value.replace("-", "_")


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    atoms = set(asp.atoms(model, "valid"))
    asp_valid = {tuple(str(part) for part in atom) for atom in atoms}
    py_valid = {
        (params.place, params.ghost, params.lantern, params.gesture)
        for params in [
            Params(place, ghost, lantern, gesture)
            for place in PLACES
            for ghost in GHOSTS
            for lantern in LANTERNS
            for gesture in GESTURES
        ]
        if valid_params(params)[0]
    }
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid lantern ghost stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--ghost", choices=sorted(GHOSTS))
    parser.add_argument("--lantern", choices=sorted(LANTERNS))
    parser.add_argument("--gesture", choices=sorted(GESTURES))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in choices():
            yield generate(params)
        return
    rng = random.Random(args.seed)
    explicit = any(
        value is not None
        for value in (args.place, args.ghost, args.lantern, args.gesture)
    )
    for _ in range(max(1, args.n)):
        if explicit:
            params = resolve_params(args)
        else:
            params = rng.choice(choices())
        yield generate(params)


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
