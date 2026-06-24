#!/usr/bin/env python3
"""
Standalone storyworld: defensive friend in a backyard, with repetition.

A small animal-story domain in which a gentle backyard scene turns tense
when one animal becomes defensive about a shared object, then resolves
through a repeated warning and a safer plan.

The world model tracks physical meters and emotional memes. The repeated
pattern is part of the story shape: a newcomer tries the same thing twice,
the defensive friend says "no" twice, and the ending proves the change.
"""

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


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "animal"  # animal | thing
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "friend's backyard"
    afford: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    vulnerable_to: str
    owner_kind: str = "animal"


@dataclass
class Scenario:
    id: str
    verb: str
    repeated_verb: str
    nuisance: str
    consequence: str
    token: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    animals: dict[str, Entity] = field(default_factory=dict)
    things: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        if ent.kind == "thing":
            self.things[ent.id] = ent
        else:
            self.animals[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.animals.get(eid) or self.things[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        return World(
            setting=self.setting,
            animals=_copy.deepcopy(self.animals),
            things=_copy.deepcopy(self.things),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="friend's backyard", afford={"share", "run", "snack"}),
}

SCENARIOS = {
    "ball": Scenario(
        id="ball",
        verb="roll the red ball",
        repeated_verb="roll the red ball again",
        nuisance="the ball might bump the flowers",
        consequence="nudge the flower pot",
        token="ball",
        tags={"play", "red"},
    ),
    "berries": Scenario(
        id="berries",
        verb="taste the berries",
        repeated_verb="taste another berry",
        nuisance="the berries were saved for a snack",
        consequence="take the snack bowl",
        token="berries",
        tags={"snack", "food"},
    ),
    "sprinkler": Scenario(
        id="sprinkler",
        verb="race through the sprinkler",
        repeated_verb="dash through the sprinkler again",
        nuisance="the wet splashes might reach the nest",
        consequence="soak the nest",
        token="sprinkler",
        tags={"water", "play"},
    ),
}

ITEMS = {
    "nest": Item(
        id="nest",
        label="nest",
        phrase="a soft little nest",
        region="ground",
        vulnerable_to="wet",
    ),
    "snackbowl": Item(
        id="snackbowl",
        label="snack bowl",
        phrase="a small bowl of berries",
        region="table",
        vulnerable_to="food",
    ),
    "flowers": Item(
        id="flowers",
        label="flowers",
        phrase="the garden flowers",
        region="ground",
        vulnerable_to="play",
    ),
}

ANIMAL_NAMES = ["Milo", "Pip", "Luna", "Tia", "Ned", "Gus", "Rory", "Mimi"]
KINDS = ["rabbit", "fox", "mouse", "bird", "cat", "dog", "squirrel", "chipmunk"]
DEFENSIVE_NAMES = ["Pip", "Gus", "Milo", "Tia"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
scenario_valid(S) :- scenario(S), can_fit(S).
needs_defense(S, I) :- scenario_valid(S), target(S, I).

can_fit(ball).
can_fit(berries).
can_fit(sprinkler).

"""
def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, sc in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("token", sid, sc.token))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("vulnerable_to", iid, item.vulnerable_to))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def reasonableness_gate(scenario: Scenario, item: Item) -> bool:
    return (
        (scenario.id == "ball" and item.id == "flowers")
        or (scenario.id == "berries" and item.id == "snackbowl")
        or (scenario.id == "sprinkler" and item.id == "nest")
    )


def choose_restriction(scenario: Scenario, item: Item) -> str:
    if scenario.id == "ball":
        return "the flowers"
    if scenario.id == "berries":
        return "the snack bowl"
    return "the nest"


def predict_damage(world: World, actor: Entity, scenario: Scenario, item: Entity) -> bool:
    sim = world.copy()
    _perform_action(sim, sim.animals[actor.id], scenario, narrate=False)
    return bool(sim.things[item.id].meters.get("damaged", 0) >= THRESHOLD)


def _perform_action(world: World, actor: Entity, scenario: Scenario, narrate: bool = True) -> None:
    actor.meters[scenario.token] = actor.meters.get(scenario.token, 0) + 1
    if scenario.id == "sprinkler":
        world.things["nest"].meters["wet"] = world.things["nest"].meters.get("wet", 0) + 1
    elif scenario.id == "ball":
        world.things["flowers"].meters["bumped"] = world.things["flowers"].meters.get("bumped", 0) + 1
    else:
        world.things["snackbowl"].meters["taken"] = world.things["snackbowl"].meters.get("taken", 0) + 1
    if narrate:
        pass


def introduce(world: World, defender: Entity, friend: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {defender.id} was a small {defender.type} who loved quiet play. "
        f"{friend.id} was a curious {friend.type} visiting the backyard."
    )


def setup(world: World, defender: Entity, friend: Entity, scenario: Scenario, item: Entity) -> None:
    world.say(
        f"They found {world.facts['item_phrase']} under the sun, and {friend.id} wanted to {scenario.verb}."
    )
    world.say(
        f"But {defender.id} watched the {item.label} closely, because {world.facts['nuisance']}."
    )


def warning(world: World, defender: Entity, friend: Entity, scenario: Scenario, item: Entity) -> None:
    defender.memes["defensive"] = defender.memes.get("defensive", 0) + 1
    world.say(
        f'"No, no," said {defender.id}. "Not near the {item.label}." '
        f'{defender.id} said it once, then said it again.'
    )


def repeat_attempt(world: World, friend: Entity, scenario: Scenario) -> None:
    friend.memes["want"] = friend.memes.get("want", 0) + 1
    world.say(
        f"{friend.id} tried to {scenario.repeated_verb}, because the idea still felt fun."
    )


def second_warning(world: World, defender: Entity, friend: Entity, item: Entity) -> None:
    defender.memes["defensive"] = defender.memes.get("defensive", 0) + 1
    world.say(
        f'"No, no," said {defender.id} again. "We can play, but not in the same way."'
    )


def resolve(world: World, defender: Entity, friend: Entity, scenario: Scenario, item: Entity) -> None:
    defender.memes["calm"] = defender.memes.get("calm", 0) + 1
    friend.memes["calm"] = friend.memes.get("calm", 0) + 1
    world.say(
        f"Then {defender.id} pointed to a safer spot by the fence and showed a gentler game."
    )
    world.say(
        f"{friend.id} nodded, and soon they were {scenario.verb} there instead. "
        f"The {item.label} stayed safe, and the backyard felt happy again."
    )


def build_world(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)
    defender = world.add(Entity(id=params.defender, kind="animal", type=params.defender_kind))
    friend = world.add(Entity(id=params.friend, kind="animal", type=params.friend_kind))
    scenario = SCENARIOS[params.scenario]
    item = world.add(Entity(id=params.item, kind="thing", type="thing", label=ITEMS[params.item].label))
    world.facts.update(
        defender=defender,
        friend=friend,
        scenario=scenario,
        item=item,
        item_phrase=ITEMS[params.item].phrase,
        nuisance=choose_restriction(scenario, ITEMS[params.item]),
    )

    introduce(world, defender, friend)
    world.para()
    setup(world, defender, friend, scenario, item)
    warning(world, defender, friend, scenario, item)
    repeat_attempt(world, friend, scenario)
    second_warning(world, defender, friend, item)
    world.para()
    resolve(world, defender, friend, scenario, item)
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    scenario: str
    item: str
    defender: str
    defender_kind: str
    friend: str
    friend_kind: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="backyard",
        scenario="ball",
        item="flowers",
        defender="Pip",
        defender_kind="rabbit",
        friend="Milo",
        friend_kind="fox",
    ),
    StoryParams(
        place="backyard",
        scenario="berries",
        item="snackbowl",
        defender="Gus",
        defender_kind="mouse",
        friend="Luna",
        friend_kind="cat",
    ),
    StoryParams(
        place="backyard",
        scenario="sprinkler",
        item="nest",
        defender="Tia",
        defender_kind="bird",
        friend="Rory",
        friend_kind="dog",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sc: Scenario = f["scenario"]
    return [
        f'Write a short Animal Story about a defensive friend in a backyard with repetition, using "{sc.token}".',
        f"Tell a gentle story where {f['defender'].id} says 'no' twice and then finds a safer game.",
        f"Write a backyard story for little kids in which one animal wants to {sc.verb} but must stop and change plans.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["defender"]
    fr: Entity = f["friend"]
    sc: Scenario = f["scenario"]
    it: Entity = f["item"]
    return [
        QAItem(
            question=f"Who was the defensive friend in the backyard story?",
            answer=f"{d.id} was the defensive friend, because {d.id} wanted to keep the {it.label} safe.",
        ),
        QAItem(
            question=f"What did {fr.id} want to do twice before changing plans?",
            answer=f"{fr.id} wanted to {sc.verb} and then tried to {sc.repeated_verb}.",
        ),
        QAItem(
            question=f"What stayed safe by the end of the story?",
            answer=f"The {it.label} stayed safe, and the two animals played in a gentler way instead.",
        ),
        QAItem(
            question=f"Why did {d.id} keep saying no?",
            answer=f"{d.id} kept saying no because {world.facts['nuisance']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does defensive mean?",
            answer="Defensive means you protect something carefully and do not want it to be hurt or taken.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again. In stories, repetition can make a moment feel strong and easy to remember.",
        ),
        QAItem(
            question="What is a backyard?",
            answer="A backyard is the open space behind a house where children and animals can play.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show scenario_valid/1."))
    return sorted(set(asp.atoms(model, "scenario_valid")))


def asp_verify() -> int:
    py = {(sid,) for sid in SCENARIOS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} scenarios).")
        return 0
    print("Mismatch between Python and clingo:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with defensive repetition in a friend's backyard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--defender")
    ap.add_argument("--defender-kind", choices=["rabbit", "fox", "mouse", "bird", "cat", "dog", "squirrel", "chipmunk"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-kind", choices=["rabbit", "fox", "mouse", "bird", "cat", "dog", "squirrel", "chipmunk"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for sc in SCENARIOS:
        for item in ITEMS:
            if reasonableness_gate(SCENARIOS[sc], ITEMS[item]):
                combos.append((sc, item))
    combos = [
        (sc, item)
        for sc, item in combos
        if (args.scenario is None or sc == args.scenario)
        and (args.item is None or item == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sc, item = rng.choice(sorted(combos))
    if args.defender_kind:
        defender_kind = args.defender_kind
    else:
        defender_kind = rng.choice(["rabbit", "mouse", "bird"])
    friend_kind = args.friend_kind or rng.choice([k for k in KINDS if k != defender_kind])
    defender = args.defender or rng.choice(DEFENSIVE_NAMES)
    friend = args.friend or rng.choice([n for n in ANIMAL_NAMES if n != defender])
    return StoryParams(
        place=args.place or "backyard",
        scenario=sc,
        item=item,
        defender=defender,
        defender_kind=defender_kind,
        friend=friend,
        friend_kind=friend_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.animals.values()) + list(world.things.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
    if args.show_asp:
        print(asp_program("#show scenario_valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show scenario_valid/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
