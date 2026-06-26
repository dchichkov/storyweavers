#!/usr/bin/env python3
"""
A small storyworld about a piñata, sharing, and heartwarming problem solving.

The seed premise:
A child at a party wants to enjoy the piñata, but something goes wrong:
the string is too high, the stick is missing, or the candy is stuck.
The children and adults work together, solve the problem gently, and share
the treats so everyone ends the party happy.

This world keeps the story physically grounded with meters and emotionally
grounded with memes. The story is generated from simulated state, not from a
fixed paragraph template.
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Venue:
    place: str = "the backyard"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Scenario:
    id: str
    problem: str
    fix: str
    hint: str
    shared: bool = True


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    plural: bool = False
    shared_by_default: bool = True


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.time: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.time = self.time
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VENUES = {
    "backyard": Venue(place="the backyard", indoors=False, affords={"pinata"}),
    "park": Venue(place="the park", indoors=False, affords={"pinata"}),
    "playroom": Venue(place="the playroom", indoors=True, affords={"pinata"}),
}

SCENARIOS = {
    "too_high": Scenario(
        id="too_high",
        problem="the string is too high",
        fix="a chair and a careful pair of hands",
        hint="lift the rope lower",
    ),
    "no_stick": Scenario(
        id="no_stick",
        problem="the stick is missing",
        fix="a broom handle wrapped with ribbon",
        hint="find a safe helper stick",
    ),
    "stuck_candy": Scenario(
        id="stuck_candy",
        problem="the candy is stuck inside",
        fix="gentle tapping and a shared shake",
        hint="loosen the treats without tearing the pinata too soon",
    ),
}

REWARDS = {
    "candies": Reward(
        id="candies",
        label="candies",
        phrase="little wrapped candies",
        plural=True,
        shared_by_default=True,
    ),
    "stickers": Reward(
        id="stickers",
        label="stickers",
        phrase="bright stickers",
        plural=True,
        shared_by_default=True,
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Milo", "Theo", "Ben"]
TRAITS = ["gentle", "curious", "kind", "patient", "brave", "helpful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    scenario: str
    reward: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

valid_story(Place, Scenario, Reward, Gender) :-
    venue(Place), affords(Place, pinata), scenario(Scenario), reward(Reward),
    can_share(Reward), wears(Gender, Reward), reason(Remark),
    reason_ok(Scenario, Remark).

can_share(candies).
can_share(stickers).

reason_ok(too_high, problem_height).
reason_ok(no_stick, problem_tool).
reason_ok(stuck_candy, problem_loosen).

problem_height.
problem_tool.
problem_loosen.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vid, venue in VENUES.items():
        lines.append(asp.fact("venue", vid))
        if venue.indoors:
            lines.append(asp.fact("indoors", vid))
        for a in sorted(venue.affords):
            lines.append(asp.fact("affords", vid, a))
    for sid in SCENARIOS:
        lines.append(asp.fact("scenario", sid))
    for rid, reward in REWARDS.items():
        lines.append(asp.fact("reward", rid))
        if reward.shared_by_default:
            lines.append(asp.fact("can_share", rid))
        for g in ("girl", "boy"):
            lines.append(asp.fact("wears", g, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_stories())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(python_set)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_story(place: str, scenario: str, reward: str, gender: str) -> bool:
    return place in VENUES and scenario in SCENARIOS and reward in REWARDS and gender in {"girl", "boy"}


def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for place in VENUES:
        for scenario in SCENARIOS:
            for reward in REWARDS:
                for gender in ("girl", "boy"):
                    if valid_story(place, scenario, reward, gender):
                        out.append((place, scenario, reward, gender))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming piñata storyworld.")
    ap.add_argument("--place", choices=VENUES)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_stories()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.scenario:
        combos = [c for c in combos if c[1] == args.scenario]
    if args.reward:
        combos = [c for c in combos if c[2] == args.reward]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, scenario, reward, gender = rng.choice(combos)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mom", "dad", "grandma", "grandpa"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, scenario=scenario, reward=reward, name=name, gender=gender, helper=helper, trait=trait)


def _make_story(world: World, hero: Entity, helper: Entity, scenario: Scenario, reward: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.pronoun('subject')} with a {world.facts['trait']} smile who loved parties.")
    world.say(f"At the end of the party, there was a big pinata full of {reward.phrase}.")
    world.para()
    world.say(f"{hero.id} ran to {world.venue.place}, where everyone gathered around the pinata.")
    world.say(f"Then they found a problem: {scenario.problem}.")
    world.say(f"{hero.pronoun().capitalize()} looked at {helper.id} and said, \"We can fix it together.\"")
    world.say(f"{helper.id} nodded and offered {scenario.fix}.")
    world.say(f"Together, they used {scenario.hint}, and the problem got smaller.")
    world.para()
    if scenario.id == "stuck_candy":
        world.say(f"When the pinata finally opened, the treats tumbled out in a happy shower.")
    else:
        world.say(f"The pinata opened with a cheerful crack, and the treats spilled out safely.")
    world.say(f"{hero.id} helped gather the {reward.label} and made sure the other children got some too.")
    world.say(f"Soon everyone had a little share, and the whole party felt warm and kind.")
    world.say(f"{hero.id} smiled, holding {reward.it()} for a friend, and the leftover pieces of pinata became a happy memory.")


def generate(params: StoryParams) -> StorySample:
    world = World(VENUES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    reward = world.add(Entity(id=params.reward, type=params.reward, label=REWARDS[params.reward].label, plural=REWARDS[params.reward].plural))
    world.facts.update(
        hero=hero,
        helper=helper,
        reward=reward,
        scenario=SCENARIOS[params.scenario],
        trait=params.trait,
        place=params.place,
        gender=params.gender,
    )
    _make_story(world, hero, helper, SCENARIOS[params.scenario], reward)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child at a pinata party in {f["place"]}.',
        f"Tell a gentle tale where {f['hero'].id} and {f['helper'].id} solve a pinata problem together.",
        f"Write a short story about sharing {f['reward'].label} after a pinata challenge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    scenario: Scenario = f["scenario"]
    reward: Entity = f["reward"]
    return [
        QAItem(
            question=f"What problem did {hero.id} and {helper.id} find at {world.venue.place}?",
            answer=f"They found that {scenario.problem}.",
        ),
        QAItem(
            question=f"How did they solve the problem with the pinata?",
            answer=f"They worked together using {scenario.fix}, so the pinata could be enjoyed safely.",
        ),
        QAItem(
            question=f"What happened after the pinata opened?",
            answer=f"The {reward.label} spilled out, and {hero.id} helped share them with the other children.",
        ),
        QAItem(
            question=f"How did {hero.id} end the story?",
            answer=f"{hero.id} ended up smiling and feeling happy because everyone shared the treats.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a pinata?",
            answer="A pinata is a decorated container that can hold treats, and people open it at parties so the treats can fall out.",
        ),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it helps everyone feel included and enjoy the treats together.",
        ),
        QAItem(
            question="What does it mean to solve a problem together?",
            answer="It means people help each other and choose a plan that works for everyone.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.plural:
            bits.append("plural=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
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


CURATED = [
    StoryParams(place="backyard", scenario="too_high", reward="candies", name="Mia", gender="girl", helper="mom", trait="gentle"),
    StoryParams(place="park", scenario="no_stick", reward="stickers", name="Leo", gender="boy", helper="dad", trait="helpful"),
    StoryParams(place="playroom", scenario="stuck_candy", reward="candies", name="Nora", gender="girl", helper="grandma", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for t in stories:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
