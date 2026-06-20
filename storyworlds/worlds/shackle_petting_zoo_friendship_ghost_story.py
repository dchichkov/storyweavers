#!/usr/bin/env python3
"""A child-friendly ghost story about friendship at a petting zoo gate."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "At closing time in a petting zoo, a child hears a shackle rattle on an animal gate. "
    "The small ghost near the pen is not hunting anyone; the ghost is trying to keep one animal "
    "safe through the night. The child notices what the gate and the animal physically need, uses "
    "a kind gesture that fits the shackle, and turns the haunting into a friendship."
)


@dataclass(frozen=True)
class Pen:
    id: str
    name: str
    animal_name: str
    animal_kind: str
    spooky_detail: str
    risk_text: str
    closing_image: str
    needed_tags: tuple[str, ...]


@dataclass(frozen=True)
class Ghost:
    id: str
    name: str
    role: str
    worry: str
    request: str
    whisper: str
    accepted_gestures: tuple[str, ...]
    needed_tags: tuple[str, ...]


@dataclass(frozen=True)
class Shackle:
    id: str
    label: str
    sound: str
    texture: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Gesture:
    id: str
    action: str
    promise: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class StoryParams:
    pen: str
    ghost: str
    shackle: str
    gesture: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    location: str
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    delta: dict[str, int] = field(default_factory=dict)


@dataclass
class PettingZooWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
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
            bucket, metric = key.split(":", 1)
            self.entities[bucket].meters[metric] = self.entities[bucket].meters.get(metric, 0) + value


PENS = {
    "goat_yard": Pen(
        "goat_yard",
        "the moonlit goat yard",
        "Button",
        "goat",
        "tin feed cups clicked whenever the wind slipped through the fence",
        "Button kept nosing the gate as if one more cold rattle might send him wandering toward the dark tool shed.",
        "Button curled beside the gate and chewed slowly while the quiet shackle shone like a moon coin.",
        ("sturdy",),
    ),
    "rabbit_green": Pen(
        "rabbit_green",
        "the rabbit green",
        "Clover",
        "rabbit",
        "the hutches threw long shadows that looked like little doorways into the grass",
        "Clover thumped once and pressed low, frightened that one sharp clang would make the whole row of hutches jump.",
        "Clover lifted his nose to the latch, and the gate answered with only the softest whisper.",
        ("gentle",),
    ),
    "pony_ring": Pen(
        "pony_ring",
        "the pony ring by the red barn",
        "Pebble",
        "pony",
        "practice poles leaned against the fence like pale bones in the dusk",
        "Pebble kept shifting near the rail, and the loose gate looked too weak for one more startled bump.",
        "Pebble lowered her head against the top rail, and the gate stayed still under the friendly night sound.",
        ("sturdy",),
    ),
}

GHOSTS = {
    "ellis": Ghost(
        "ellis",
        "Ellis",
        "an old goat helper",
        "that the latch would keep snapping and let a sleepy animal wander into the dark",
        "quiet the gate and show that the animals will still be cared for",
        '"I only wanted the gate to stop sounding scared," whispered Ellis.',
        ("polish", "bell"),
        ("quiet", "care"),
    ),
    "mae": Ghost(
        "mae",
        "Mae",
        "a shy rabbit tender",
        "that sudden noise would frighten the smallest animal all night long",
        "make the shackle gentle enough for a timid friend",
        '"The little ones do not need a loud night," whispered Mae.',
        ("polish", "ribbon"),
        ("gentle", "care"),
    ),
    "benji": Ghost(
        "benji",
        "Benji",
        "a pony groom from long ago",
        "that the gate would not guide the pony home once the yard turned dark",
        "give the gate a strong hold and a friendly guiding sound",
        '"If the gate can speak kindly, Pebble will choose home," whispered Benji.',
        ("bell",),
        ("sturdy", "guide"),
    ),
}

SHACKLES = {
    "brass": Shackle(
        "brass",
        "a brass shackle",
        "a careful little clink",
        "warm from many hands even in the evening chill",
        ("sturdy", "quiet", "care"),
    ),
    "iron": Shackle(
        "iron",
        "an iron shackle",
        "a scrape like a spoon across a winter plate",
        "cold and rough with old barn dust",
        ("sturdy",),
    ),
    "ribboned": Shackle(
        "ribboned",
        "a ribbon-wrapped shackle",
        "a soft jingle under cloth",
        "threaded with fading blue ribbon from a fair day long ago",
        ("gentle", "care"),
    ),
}

GESTURES = {
    "polish": Gesture(
        "polish",
        "rub the shackle clean with a feed towel",
        "treat the latch as something worth caring for, not something cursed",
        ("quiet", "care"),
    ),
    "ribbon": Gesture(
        "ribbon",
        "tie a fresh ribbon through the shackle",
        "make the gate feel gentle enough for a shy friend",
        ("gentle", "care"),
    ),
    "bell": Gesture(
        "bell",
        "hang the lost night bell from the shackle",
        "give the gate a sound that calls a friend home instead of driving one away",
        ("guide", "care"),
    ),
}


ASP_RULES = r"""
combined_tag(S, A, T) :- shackle(S), gesture(A), shackle_tag(S, T).
combined_tag(S, A, T) :- shackle(S), gesture(A), gesture_tag(A, T).

invalid(P, G, S, A) :- pen_need(P, T), not combined_tag(S, A, T), pen(P), ghost(G), shackle(S), gesture(A).
invalid(P, G, S, A) :- ghost_need(G, T), not combined_tag(S, A, T), pen(P), ghost(G), shackle(S), gesture(A).
invalid(P, G, S, A) :- ghost(G), gesture(A), not ghost_accepts(G, A), pen(P), shackle(S).

valid(P, G, S, A) :- pen(P), ghost(G), shackle(S), gesture(A), not invalid(P, G, S, A).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pen", choices=sorted(PENS))
    parser.add_argument("--ghost", choices=sorted(GHOSTS))
    parser.add_argument("--shackle", choices=sorted(SHACKLES))
    parser.add_argument("--gesture", choices=sorted(GESTURES))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def combined_tags(params: StoryParams) -> set[str]:
    return set(SHACKLES[params.shackle].tags) | set(GESTURES[params.gesture].tags)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.pen not in PENS:
        return False, f"unknown pen: {params.pen}"
    if params.ghost not in GHOSTS:
        return False, f"unknown ghost: {params.ghost}"
    if params.shackle not in SHACKLES:
        return False, f"unknown shackle: {params.shackle}"
    if params.gesture not in GESTURES:
        return False, f"unknown gesture: {params.gesture}"

    ghost = GHOSTS[params.ghost]
    tags = combined_tags(params)

    if params.gesture not in ghost.accepted_gestures:
        return False, f"{ghost.name} would not trust the {params.gesture} gesture in this haunting"
    for tag in PENS[params.pen].needed_tags:
        if tag not in tags:
            return False, f"{PENS[params.pen].name} needs a {tag} fix before the story can resolve well"
    for tag in ghost.needed_tags:
        if tag not in tags:
            return False, f"{ghost.name} needs a {tag} answer before friendship can happen"
    return True, ""


def all_params() -> list[StoryParams]:
    options: list[StoryParams] = []
    for pen in PENS:
        for ghost in GHOSTS:
            for shackle in SHACKLES:
                for gesture in GESTURES:
                    params = StoryParams(pen=pen, ghost=ghost, shackle=shackle, gesture=gesture)
                    if valid_params(params)[0]:
                        options.append(params)
    return options


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    chooser = rng or random.Random(args.seed)
    candidates = [
        params
        for params in all_params()
        if (args.pen is None or params.pen == args.pen)
        and (args.ghost is None or params.ghost == args.ghost)
        and (args.shackle is None or params.shackle == args.shackle)
        and (args.gesture is None or params.gesture == args.gesture)
    ]
    if not candidates:
        probe = StoryParams(
            pen=args.pen or sorted(PENS)[0],
            ghost=args.ghost or sorted(GHOSTS)[0],
            shackle=args.shackle or sorted(SHACKLES)[0],
            gesture=args.gesture or sorted(GESTURES)[0],
            seed=args.seed,
        )
        ok, reason = valid_params(probe)
        raise StoryError(reason if not ok else "no valid story matches the requested partial choices")
    picked = chooser.choice(candidates)
    return StoryParams(
        pen=picked.pen,
        ghost=picked.ghost,
        shackle=picked.shackle,
        gesture=picked.gesture,
        seed=args.seed,
    )


def make_world(params: StoryParams) -> PettingZooWorld:
    pen = PENS[params.pen]
    ghost = GHOSTS[params.ghost]
    shackle = SHACKLES[params.shackle]
    world = PettingZooWorld(params=params)
    world.add(
        Entity(
            "child",
            "Lila",
            "child",
            pen.name,
            meters={"steady_hands": 1},
            memes={"fear": 1, "friendship": 0, "care": 1},
        )
    )
    world.add(
        Entity(
            "ghost",
            ghost.name,
            "ghost",
            pen.name,
            meters={"visible": 0},
            memes={"loneliness": 2, "trust": 0, "friendship": 0},
        )
    )
    world.add(
        Entity(
            "animal",
            pen.animal_name,
            pen.animal_kind,
            pen.name,
            meters={"calm": 0, "wander_risk": 1},
            memes={"trust": 0},
        )
    )
    world.add(
        Entity(
            "gate",
            "the gate",
            "gate",
            pen.name,
            meters={"secure": 0, "noise": 1},
            memes={},
        )
    )
    world.add(
        Entity(
            "shackle",
            shackle.label,
            "shackle",
            pen.name,
            meters={"quiet": 1 if "quiet" in shackle.tags else 0, "gentle": 1 if "gentle" in shackle.tags else 0},
            memes={"memory": 1},
        )
    )
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["combined_tags"] = sorted(combined_tags(params))
    world.facts["promise"] = GESTURES[params.gesture].promise
    world.facts["ending"] = "unresolved"
    return world


def arrive_after_closing(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    shackle = SHACKLES[world.params.shackle]
    world.record(
        "arrival",
        f"After the last children went home, Lila carried the empty feed cups past {pen.name}, where {pen.spooky_detail}. "
        f"On the gate hung {shackle.label}, {shackle.texture}.",
        "child",
        "shackle",
    )


def rattle_and_reveal(world: PettingZooWorld) -> None:
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    world.entities["ghost"].meters["visible"] = 1
    world.entities["child"].memes["fear"] += 1
    world.record(
        "reveal",
        f"Then {shackle.label} gave {shackle.sound}, and the pale shape of {ghost.name}, {ghost.role}, rose beside the latch. "
        f"{ghost.whisper} {ghost.name} wanted Lila to {ghost.request}.",
        "ghost",
        "child",
    )


def show_risk(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    world.entities["animal"].meters["wander_risk"] += 1
    world.record(
        "risk",
        pen.risk_text,
        "animal",
        "gate",
    )


def understanding_sentence(world: PettingZooWorld) -> str:
    ghost = GHOSTS[world.params.ghost]
    tags = set(world.facts["combined_tags"])
    if "guide" in tags:
        return f"That was when Lila understood that {ghost.name} was trying to guide a friend, not frighten one."
    if "gentle" in tags:
        return f"That was when Lila understood that the haunting wanted softness more than silence."
    return f"That was when Lila understood that the cold little ghost was guarding the gate the way a friend would."


def apply_gesture(world: PettingZooWorld) -> None:
    gesture = GESTURES[world.params.gesture]
    tags = set(world.facts["combined_tags"])
    world.entities["child"].memes["care"] += 1
    world.entities["ghost"].memes["trust"] += 1
    if "quiet" in tags:
        world.entities["gate"].meters["noise"] = 0
        world.entities["shackle"].meters["quiet"] = 2
        world.entities["child"].memes["fear"] = max(0, world.entities["child"].memes["fear"] - 1)
    if "gentle" in tags:
        world.entities["animal"].meters["calm"] += 1
        world.entities["shackle"].meters["gentle"] = 2
    if "guide" in tags:
        world.entities["animal"].memes["trust"] += 1
        world.entities["animal"].meters["calm"] += 1
    if "sturdy" in tags:
        world.entities["gate"].meters["secure"] = 2
        world.entities["animal"].meters["wander_risk"] = 0

    world.record(
        "gesture",
        f"Lila chose to {gesture.action}. She wanted to {gesture.promise}.",
        "child",
        "shackle",
    )


def settle_scene(world: PettingZooWorld) -> None:
    ghost = GHOSTS[world.params.ghost]
    animal = world.entities["animal"]
    gate = world.entities["gate"]
    tags = set(world.facts["combined_tags"])
    if "guide" in tags:
        text = f"{animal.name} followed the new sound back to the gate instead of edging toward the dark."
    elif "gentle" in tags:
        text = f"{animal.name} stopped trembling and came close enough to touch the latch with a calm nose."
    else:
        text = f"The hard little echo left the gate, and {animal.name} no longer looked ready to bolt."
    world.record("turn", text, "animal", "gate")

    if gate.meters["secure"] < 1:
        gate.meters["secure"] = 1
    if animal.meters["calm"] < 1:
        animal.meters["calm"] = 1
    world.entities["ghost"].memes["trust"] += 1
    world.entities["ghost"].memes["loneliness"] = max(0, world.entities["ghost"].memes["loneliness"] - 1)
    world.record(
        "friendship",
        f"{ghost.name} touched the gate with transparent fingers and smiled when it held. "
        f'"You heard what I was trying to protect," {ghost.name} said.',
        "ghost",
        "child",
    )


def resolve_friendship(world: PettingZooWorld) -> None:
    child = world.entities["child"]
    ghost = world.entities["ghost"]
    animal = world.entities["animal"]
    gate = world.entities["gate"]
    if gate.meters["secure"] < 1 or animal.meters["calm"] < 1 or ghost.memes["trust"] < 2:
        raise StoryError("world state did not reach a complete friendship ending")
    child.memes["friendship"] = 1
    ghost.memes["friendship"] = 1
    animal.memes["trust"] = max(1, animal.memes["trust"])
    world.facts["ending"] = "friendship"


def render_story(world: PettingZooWorld) -> str:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    intro = "The petting zoo was supposed to be asleep, but one small sound refused to rest."
    first = " ".join(event.text for event in world.history[:3])
    second = " ".join(
        [
            understanding_sentence(world),
            *[event.text for event in world.history[3:]],
        ]
    )
    ending = (
        f"Before Lila left, {pen.closing_image} {ghost.name} stayed beside her instead of hiding in the cold, "
        f"and {shackle.label} no longer sounded lonely. From then on, Lila thought of the haunting as a friendship "
        f"fastened to the gate."
    )
    return "\n\n".join([f"{intro} {first}", second, ending])


def build_story_qa(world: PettingZooWorld) -> list[QAItem]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    gesture = GESTURES[world.params.gesture]
    return [
        QAItem(
            "Why did the ghost care so much about the shackle?",
            f"{ghost.name} cared because {ghost.worry}. The shackle was the part of the gate that could either keep {pen.animal_name} safe or let the whole night feel dangerous.",
        ),
        QAItem(
            "What turned the haunting into a friendship?",
            f"Lila answered the ghost with a fitting act of care when she chose to {gesture.action}. That physical change showed {ghost.name} that she understood the job of the gate, so trust replaced the cold fear.",
        ),
        QAItem(
            "How does the ending prove that the problem was really solved?",
            f"The ending shows the problem is solved because {pen.closing_image.lower()} The gate is steady, the animal is calm, and the ghost stays near Lila like a friend instead of a warning.",
        ),
    ]


def build_world_qa(world: PettingZooWorld) -> list[QAItem]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    return [
        QAItem(
            "Which object carried the main change in this story world?",
            f"The main physical carrier was {SHACKLES[world.params.shackle].label}. It held the fix on the gate and also held the new friendship because the ghost stopped rattling it in fear.",
        ),
        QAItem(
            "Who became friends in this world?",
            f"Lila and {ghost.name} became friends. Their friendship mattered because it also made {pen.animal_name} feel safe enough to settle for the night.",
        ),
        QAItem(
            "Why is the setting important in this ghost story?",
            f"The petting zoo matters because the haunting grows out of caring for a real animal gate after closing time. The problem is not abstract; it lives in the pen, the shackle, and the animal that needs a safe night.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    world = make_world(params)
    arrive_after_closing(world)
    rattle_and_reveal(world)
    show_risk(world)
    apply_gesture(world)
    settle_scene(world)
    resolve_friendship(world)
    story = render_story(world)
    prompts = [
        "Write a ghost story set in a petting zoo.",
        "Include the word shackle as a physical object that changes the action.",
        "Use friendship as the force that resolves the haunting.",
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for pen in PENS.values():
        facts.append(asp.fact("pen", pen.id))
        for tag in pen.needed_tags:
            facts.append(asp.fact("pen_need", pen.id, tag))
    for ghost in GHOSTS.values():
        facts.append(asp.fact("ghost", ghost.id))
        for gesture in ghost.accepted_gestures:
            facts.append(asp.fact("ghost_accepts", ghost.id, gesture))
        for tag in ghost.needed_tags:
            facts.append(asp.fact("ghost_need", ghost.id, tag))
    for shackle in SHACKLES.values():
        facts.append(asp.fact("shackle", shackle.id))
        for tag in shackle.tags:
            facts.append(asp.fact("shackle_tag", shackle.id, tag))
    for gesture in GESTURES.values():
        facts.append(asp.fact("gesture", gesture.id))
        for tag in gesture.tags:
            facts.append(asp.fact("gesture_tag", gesture.id, tag))
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/4.\n"


def verify_asp_and_world() -> str:
    import asp

    py_valid = {
        (params.pen, params.ghost, params.shackle, params.gesture)
        for params in all_params()
    }
    model = asp.one_model(asp_program())
    asp_valid = {
        tuple(str(piece) for piece in atom)
        for atom in asp.atoms(model, "valid")
    }
    if py_valid != asp_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")

    exercised = 0
    for params in all_params():
        sample = generate(params)
        exercised += 1
        if "shackle" not in sample.story.lower():
            raise StoryError("generated story failed to include the seed word 'shackle'")
        if len(sample.story_qa) != 3 or len(sample.world_qa) != 3:
            raise StoryError("generated story did not emit the required QA sets")
        if sample.world.facts.get("ending") != "friendship":
            raise StoryError("generated story did not reach the intended friendship ending")
    return f"OK: Python and ASP agree on {len(py_valid)} valid petting-zoo ghost stories; exercised {exercised} renders."


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return

    rng = random.Random(args.seed)
    explicit = any((args.pen, args.ghost, args.shackle, args.gesture))
    for _ in range(max(1, args.n)):
        if explicit:
            yield generate(resolve_params(args, rng))
        else:
            chosen = rng.choice(all_params())
            yield generate(
                StoryParams(
                    pen=chosen.pen,
                    ghost=chosen.ghost,
                    shackle=chosen.shackle,
                    gesture=chosen.gesture,
                    seed=args.seed,
                )
            )


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        for event in sample.world.history:
            print(f"- {event.id}: {event.text}")
        print("\nState:")
        for entity in sample.world.entities.values():
            print(f"- {entity.id}: meters={entity.meters} memes={entity.memes}")
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
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
        if args.asp:
            import asp

            model = asp.one_model(asp_program())
            print(sorted(tuple(str(piece) for piece in atom) for atom in asp.atoms(model, "valid")))
            return 0
        if args.verify:
            print(verify_asp_and_world())
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
