#!/usr/bin/env python3
"""A small fable about teamwork, a seed, and the care hidden underground."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def change(self, key: str, amount: float) -> None:
        self.meters[key] = self.meter(key) + amount

    def feel(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    place: str
    treasure: str
    child: str
    animal: str
    partner: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    label: str
    detail: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    lesson: str


SETTINGS = {
    "meadow": Setting("meadow", "the meadow", "where clover nodded beside a sunny path"),
    "orchard": Setting("orchard", "the orchard", "where apples hung like red lanterns"),
    "garden": Setting("garden", "the garden", "where soft soil waited beneath the beans"),
    "hill": Setting("hill", "the hill", "where the wind combed the tall grass"),
}

TREASURES = {
    "acorn": Treasure("acorn", "acorn", "a plump acorn", "small beginnings can grow into something grand"),
    "seed": Treasure("seed", "seed", "a bright sunflower seed", "patient care helps a hidden hope rise"),
    "marble": Treasure("marble", "marble", "a blue glass marble", "a gift matters because it is remembered"),
    "bell": Treasure("bell", "bell", "a tiny brass bell", "a gentle sound can bring friends together"),
}

ANIMALS = {
    "badger": ("badger", "a careful digger"),
    "rabbit": ("rabbit", "a quick-footed helper"),
    "mole": ("mole", "a quiet tunnel-maker"),
    "squirrel": ("squirrel", "a nimble climber"),
}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Owen", "Iris", "Sam"]
TRAITS = ["curious", "patient", "eager", "kind", "hopeful"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def entity_name(world: World, eid: str) -> str:
    return world.entities[eid].label


def valid_combo(place: str, treasure: str) -> bool:
    return place in SETTINGS and treasure in TREASURES


def tell(params: StoryParams) -> World:
    if not valid_combo(params.place, params.treasure):
        raise StoryError("The chosen place and treasure do not form a sensible story.")
    if params.animal not in ANIMALS:
        raise StoryError("The helper must be a known woodland animal.")
    if params.trait not in TRAITS:
        raise StoryError("The child's trait is not in the story registry.")

    setting = SETTINGS[params.place]
    treasure = TREASURES[params.treasure]
    animal_label, animal_role = ANIMALS[params.animal]
    world = World(setting)

    child = world.add(Entity(params.child, "character", params.child))
    helper = world.add(Entity(params.animal, "animal", f"the {animal_label}"))
    prize = world.add(Entity("treasure", "thing", treasure.label))
    place = world.add(Entity("place", "setting", setting.label))

    child.feel("hope", 1)
    child.feel("loneliness", 1)
    helper.feel("willingness", 1)
    prize.change("hidden", 0)

    world.facts.update(
        child=child,
        helper=helper,
        treasure=treasure,
        child_name=params.child,
        animal_label=animal_label,
        animal_role=animal_role,
        buried=False,
        found=False,
        teamwork=False,
    )

    world.record(
        "arrive",
        f"{params.child} walked into {setting.label}, {setting.detail}. "
        f"{params.child} carried {treasure.phrase}, a little treasure that "
        f"{treasure.lesson}.",
        actor=child.id,
        target=place.id,
        cause=f"{params.child} wanted to keep {treasure.label} safe",
        result=f"{params.child} brought {treasure.phrase} to {setting.label}",
    )

    world.para()
    world.record(
        "problem",
        f"At the end of the path, {params.child} found a deep crack in the earth. "
        f"The wind was growing strong, and {params.child} worried that the "
        f"{treasure.label} might roll away. "
        f'"I can bury it," {params.child} said, but the ground was hard and the '
        f"little spade bent against a root.",
        actor=child.id,
        target=prize.id,
        cause=f"The wind could carry away {treasure.phrase}",
        result=f"The first attempt to bury it did not work",
    )
    child.feel("worry", 1)
    child.change("failed_attempts", 1)

    world.para()
    world.record(
        "helper",
        f"A {animal_label} listened from beneath a nearby bush. "
        f'"I know the earth," said the {animal_label}. '
        f'"You bring the seed-sized stones, and I will loosen the soil." '
        f"{params.child} looked at the {animal_label}. "
        f"The work seemed less frightening when there were two sets of paws and hands.",
        actor=helper.id,
        target=child.id,
        cause=f"The {animal_label} noticed that {params.child} needed help",
        result=f"They divided the work according to what each could do",
    )
    helper.feel("trust", 1)
    child.feel("trust", 1)
    world.facts["teamwork"] = True

    world.para()
    child.change("stones_carried", 3)
    helper.change("soil_loosened", 3)
    world.record(
        "teamwork",
        f"{params.child} carried three smooth stones from the path while the "
        f"{animal_label} loosened the hard soil. "
        f"Together they made a small, safe hollow. "
        f"{params.child} placed {treasure.phrase} inside, and the "
        f"{animal_label} nudged warm earth over it.",
        actor=child.id,
        target=prize.id,
        cause=f"{params.child} and the {animal_label} used different strengths",
        result=f"They made a hollow and buried {treasure.label} safely",
    )
    prize.change("hidden", 1)
    world.facts["buried"] = True
    child.feel("pride", 1)
    helper.feel("pride", 1)

    world.para()
    child.change("marker_placed", 1)
    world.record(
        "marker",
        f"Before leaving, {params.child} placed a white pebble above the spot, "
        f"and the {animal_label} pressed two twigs into the soil. "
        f"They had made a mark that both friends could recognize.",
        actor=child.id,
        target=prize.id,
        cause="A hidden treasure needs a shared way to be remembered",
        result="The pebble and twigs marked the burial place",
    )

    world.para()
    prize.change("future", 1)
    child.feel("loneliness", -1)
    child.feel("joy", 1)
    helper.feel("joy", 1)
    world.facts["found"] = True
    world.record(
        "ending",
        f"Then the wind swept over the meadow, orchard, garden, or hill, but the "
        f"{treasure.label} stayed beneath the earth. "
        f"{params.child} and the {animal_label} went home side by side, planning "
        f"to visit the mark when the right day came. "
        f"Under the soil, something precious waited. Above it, friendship had "
        f"already begun to grow.",
        actor=child.id,
        target=helper.id,
        cause=f"Teamwork made the hiding place strong and gave the friends a shared plan",
        result="The treasure stayed safe and the friends left together",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child_name"]
    treasure: Treasure = f["treasure"]  # type: ignore[assignment]
    animal = f["animal_label"]
    return [
        f"Write a gentle fable about {child} who wants to bury {treasure.phrase}, "
        f"then learns teamwork with a {animal}.",
        f"Tell a child-friendly story in which {child} cannot bury a treasure alone, "
        f"but a {animal} helps by using a different strength.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "problem": "Why did the child want to bury the treasure?",
        "helper": "How did the animal help?",
        "teamwork": "What did the child and the animal do together?",
        "marker": "How would the friends remember where the treasure was?",
        "ending": "What changed by the end of the story?",
    }
    return [
        QAItem(question=questions[event.kind], answer=f"{event.cause}. {event.result}.")
        for event in world.history
        if event.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    animal = world.facts["animal_label"]
    return [
        QAItem(
            "Why might someone bury a treasure?",
            "Someone might bury a treasure to keep it safe for later and remember where it is hidden.",
        ),
        QAItem(
            "What does teamwork mean?",
            "Teamwork means people or animals share a job and use their different strengths to reach a goal.",
        ),
        QAItem(
            f"How can a {animal} help in a forest?",
            f"A {animal} can help by using its natural strength, such as digging, carrying, climbing, or finding a safe path.",
        ),
        QAItem(
            "Why is a marker useful?",
            "A marker helps friends find a hidden place again without having to search everywhere.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
burial_safe :- teamwork, marker.
goal_reached :- burial_safe.
teamwork :- child_carries, helper_digs.
marker :- pebble, twigs.
#show goal_reached/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child_carries"),
            asp.fact("helper_digs"),
            asp.fact("teamwork"),
            asp.fact("pebble"),
            asp.fact("twigs"),
            asp.fact("marker"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    goals = asp.atoms(model, "goal_reached")
    if not goals:
        print("MISMATCH: ASP did not derive a safe burial.")
        return 1
    for params in curated():
        sample = generate(params)
        check_sample(sample)
    print(f"OK: ASP derived a safe burial; {len(curated())} stories checked.")
    return 0


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    child = world.facts["child"]
    helper = world.facts["helper"]
    assert world.facts["teamwork"]
    assert world.facts["buried"]
    assert child.meter("stones_carried") == 3
    assert helper.meter("soil_loosened") == 3
    assert child.meter("marker_placed") == 1
    assert world.facts["found"]
    assert len(sample.story.split()) > 100
    assert len(sample.story_qa) == 5
    assert not any(x in sample.story for x in ("{", "}", "meters=", "memes="))
    for event in world.history:
        assert event.text in sample.story
        assert event.actor in world.entities
        assert event.target in world.entities
        assert event.result in event.text


def curated() -> list[StoryParams]:
    return [
        StoryParams("meadow", "acorn", "Luna", "badger", "Milo", "curious"),
        StoryParams("orchard", "seed", "Theo", "rabbit", "Pia", "patient"),
        StoryParams("garden", "marble", "Nia", "mole", "Owen", "hopeful"),
        StoryParams("hill", "bell", "Iris", "squirrel", "Sam", "kind"),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable about burying a treasure through teamwork.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--treasure", choices=sorted(TREASURES))
    parser.add_argument("--child")
    parser.add_argument("--animal", choices=sorted(ANIMALS))
    parser.add_argument("--partner")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    child = args.child or rng.choice(NAMES)
    animal = args.animal or rng.choice(sorted(ANIMALS))
    partner = args.partner or rng.choice([n for n in NAMES if n != child])
    trait = args.trait or rng.choice(TRAITS)
    if not valid_combo(place, treasure):
        raise StoryError("That place and treasure cannot make a complete story.")
    if child.lower() == ANIMALS[animal][0]:
        raise StoryError("The child's name must differ from the helper animal.")
    return StoryParams(place, treasure, child, animal, partner, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP goal:", bool(asp.atoms(model, "goal_reached")))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
