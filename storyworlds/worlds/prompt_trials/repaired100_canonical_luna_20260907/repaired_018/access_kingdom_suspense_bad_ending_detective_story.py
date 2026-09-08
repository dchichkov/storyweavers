#!/usr/bin/env python3
"""
A child-friendly detective storyworld about access to a secret kingdom, where
suspense grows around a locked gate and careful clues prevent a bad ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


GATES = ["the moon gate", "the ivy gate", "the silver gate", "the stone gate"]
KINGDOMS = ["the kingdom of Lanterns", "the kingdom of Blue Bells", "the kingdom of Little Stars"]
HEROES = ["Luna", "Mira", "Theo", "Nell", "Pip", "Ari"]
HELPERS = ["Inspector Moss", "Aunt Rowan", "Keeper Bea", "Detective Fox"]
CLUES = ["a muddy key print", "three silver feathers", "a torn blue ribbon", "a line of golden dust"]


@dataclass
class StoryParams:
    hero: str
    helper: str
    gate: str
    kingdom: str
    clue: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Case:
    mission: str
    trouble: str
    suspicion: str
    clue_detail: str
    test: str
    truth: str
    child_action: str
    helper_action: str
    solution: str
    ending: str
    bad_ending: str
    opening_exchange: str
    detective_exchange: str


CASES = [
    Case(
        mission="deliver a welcome lantern to the kingdom council",
        trouble="the gate slammed shut, and the welcome lantern vanished from the path",
        suspicion="someone inside the kingdom had stolen the lantern",
        clue_detail="the muddy key print pointed away from the gate instead of toward it",
        test="placed a fresh lantern beside the print and compared their shapes",
        truth="a sleepy cart pony had dragged the lantern toward the garden pond",
        child_action="followed the muddy wheel tracks around the wall",
        helper_action="held the gate lantern high so every mark could be seen",
        solution="they found the lantern beside the pond and used its light to reveal the real latch",
        ending="the council welcomed them beneath a warm golden glow",
        bad_ending="the kingdom would have begun its festival in darkness while everyone blamed the wrong visitor",
        opening_exchange="'The kingdom is waiting,' said Luna. 'Then let us examine every clue,' said Inspector Moss.",
        detective_exchange="'The print faces outward,' Luna said. 'So the lantern went away from the gate.'",
    ),
    Case(
        mission="return a small crown to the young ruler",
        trouble="the crown disappeared just before the gate's bell rang",
        suspicion="the gatekeeper had hidden it to stop the royal visit",
        clue_detail="three silver feathers rested in a neat trail beneath the welcome bench",
        test="used a hand lens to see that the feathers were caught in a crown's velvet lining",
        truth="a gust had carried the crown into the bell tower",
        child_action="climbed only as far as the safe viewing step and pointed to the tower window",
        helper_action="lowered a ribbon loop from the tower stairs",
        solution="they pulled the crown down gently and checked the gate bell before entering",
        ending="the young ruler placed the crown on their head and thanked the careful detective",
        bad_ending="the kingdom would have crowned the wrong object and laughed through a very confusing ceremony",
        opening_exchange="'A crown should not wander,' said Luna. 'That is why we follow where it went,' said Inspector Moss.",
        detective_exchange="'The feathers are caught in velvet,' Luna said. 'The crown passed this way,' said the inspector.",
    ),
    Case(
        mission="ask the kingdom for shelter before a storm",
        trouble="the access bell would not ring, and dark clouds folded over the road",
        suspicion="the kingdom had refused to let strangers enter",
        clue_detail="a torn blue ribbon was wedged between the bell and its wooden post",
        test="pulled the ribbon free with a pencil instead of forcing the bell",
        truth="a delivery bundle had snagged the bell rope",
        child_action="read the bundle's label and carried it to the side porch",
        helper_action="tested the bell with one gentle tug",
        solution="they cleared the rope, rang twice, and received shelter before the rain arrived",
        ending="the storm drummed on the roof while warm soup steamed inside",
        bad_ending="they would have stood outside in the cold because of a trapped ribbon",
        opening_exchange="'The clouds look worried,' said Luna. 'We will solve the quiet bell first,' said Inspector Moss.",
        detective_exchange="'The bell is not refusing us,' Luna said. 'Its rope is caught,' replied the inspector.",
    ),
    Case(
        mission="return a map showing the safest path through the kingdom",
        trouble="the map case was locked, and a line of golden dust led under the gate",
        suspicion="a secret thief had taken the map to seal the kingdom away",
        clue_detail="the dust sparkled on both sides of the case's tiny keyhole",
        test="shook the case gently and heard the map roll inside",
        truth="the map was safe, but the key had slipped beneath the gate's welcome mat",
        child_action="lifted the mat by its corner and spotted the brass key",
        helper_action="kept the map case steady while the key turned",
        solution="they opened the case, checked the map, and marked a safer route for everyone",
        ending="the kingdom opened its paths, and no traveler had to guess at the crossing",
        bad_ending="the safe map would have stayed locked while travelers wandered toward the marsh",
        opening_exchange="'A locked case makes a serious mystery,' said Luna. 'A serious mystery needs patient eyes,' said Inspector Moss.",
        detective_exchange="'The map is still inside,' Luna said. 'Then the missing key is our next suspect,' said the inspector.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detective storyworld about access to a secret kingdom.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--gate", choices=GATES)
    parser.add_argument("--kingdom", choices=KINGDOMS)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        gate=args.gate or rng.choice(GATES),
        kingdom=args.kingdom or rng.choice(KINGDOMS),
        clue=args.clue or rng.choice(CLUES),
    )


def build_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")
    world = World(params)
    world.add(Entity("hero", "character", params.hero, "detective", memes={"curiosity": 1.0}))
    world.add(Entity("helper", "character", params.helper, "helper", memes={"patience": 1.0}))
    world.add(Entity("gate", "place", params.gate, "gate", meters={"distance": 0.0}))
    world.add(Entity("kingdom", "place", params.kingdom, "kingdom", memes={"welcome": 0.0}))
    world.add(Entity("clue", "thing", params.clue, "clue", meters={"visibility": 0.0}))
    return world


def choose_case(params: StoryParams) -> Case:
    if params.seed is not None:
        index = params.seed % len(CASES)
    else:
        index = sum(ord(ch) for ch in "|".join(vars(params).values()) if isinstance(ch, str)) % len(CASES)
    return CASES[index]


def generate_story(world: World) -> None:
    p = world.params
    case = choose_case(p)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    gate = world.entities["gate"]
    kingdom = world.entities["kingdom"]
    clue = world.entities["clue"]

    world.say(
        f"{p.hero} was a young detective who had permission to seek access through {p.gate}, "
        f"the guarded entrance to {p.kingdom}."
    )
    world.say(case.opening_exchange)
    world.say(f"Their mission was to {case.mission}.")

    world.para()
    world.say(f"When they reached {p.gate}, {case.trouble}.")
    gate.meters["suspense"] = 1.0
    hero.memes["worry"] = 1.0
    kingdom.memes["welcome"] = 0.0
    world.say(f"For a moment, Luna feared that {case.suspicion}.")
    world.say(f"{p.helper} pointed to {p.clue}: {case.clue_detail}.")
    world.say(case.detective_exchange)
    world.facts["suspicion"] = case.suspicion
    world.facts["clue_detail"] = case.clue_detail

    world.para()
    world.say(f"Instead of guessing, {p.hero} {case.test}.")
    clue.meters["visibility"] = 1.0
    hero.memes["curiosity"] = 2.0
    world.say(f"The clue revealed the truth: {case.truth}.")
    world.say(
        f"If they had trusted the first suspicion, {case.bad_ending}; that would have been a bad ending."
    )
    world.facts["truth"] = case.truth
    world.facts["bad_ending"] = case.bad_ending
    world.facts["suspense_resolved"] = True

    world.para()
    world.say(f"{p.hero} {case.child_action}, while {p.helper} {case.helper_action}.")
    world.say(f"Together, {case.solution}.")
    kingdom.memes["welcome"] = 1.0
    hero.memes["pride"] = 1.0
    helper.memes["relief"] = 1.0
    world.say(f"At last, access was safe, and {case.ending}.")
    world.say(
        f"{p.hero} wrote the case in a little notebook: a good detective follows the clue before choosing a culprit."
    )
    world.facts.update(
        {
            "mission": case.mission,
            "trouble": case.trouble,
            "child_action": case.child_action,
            "helper_action": case.helper_action,
            "solution": case.solution,
            "ending": case.ending,
            "kingdom_open": True,
            "bad_ending_avoided": True,
        }
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    p = params
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a suspenseful detective story for children about {p.hero} finding access to {p.kingdom}.",
            f"Tell a mystery at {p.gate} where {p.hero} follows {p.clue} and avoids a bad ending.",
            "Create a child-facing detective tale in which careful evidence solves a kingdom mystery.",
        ],
        story_qa=[
            QAItem(
                f"What was {p.hero}'s mission at {p.gate}?",
                f"{p.hero}'s mission was to {facts['mission']}.",
            ),
            QAItem(
                f"What clue helped solve the mystery at {p.gate}?",
                f"The important clue was {p.clue}: {facts['clue_detail']}.",
            ),
            QAItem(
                f"What was the real cause of the trouble?",
                f"The real cause was that {facts['truth']}.",
            ),
            QAItem(
                f"How did {p.hero} avoid a bad ending?",
                f"{p.hero} avoided a bad ending by investigating instead of trusting the first suspicion. {facts['solution']}.",
            ),
            QAItem(
                f"What happened when access to {p.kingdom} became safe?",
                f"Access became safe, and {facts['ending']}.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is access?",
                "Access is the ability or permission to enter or use a place.",
            ),
            QAItem(
                "What is a kingdom?",
                "A kingdom is a land ruled by a king, queen, or other ruler.",
            ),
            QAItem(
                "Why should a detective check clues?",
                "A detective checks clues to learn what really happened instead of blaming someone too quickly.",
            ),
        ],
        world=world,
    )


def asp_facts() -> str:
    import asp
    lines = []
    for gate in GATES:
        lines.append(asp.fact("gate", gate))
    for kingdom in KINGDOMS:
        lines.append(asp.fact("kingdom", kingdom))
    lines.extend(
        [
            asp.fact("feature", "access"),
            asp.fact("feature", "suspense"),
            asp.fact("feature", "bad_ending_avoided"),
            asp.fact("style", "detective_story"),
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
mystery(G,K) :- gate(G), kingdom(K).
access_case(G,K) :- mystery(G,K).
suspense(G) :- gate(G).
bad_ending_avoided(G,K) :- access_case(G,K).
detective_story(G,K) :- access_case(G,K).
#show mystery/2.
#show access_case/2.
#show suspense/1.
#show bad_ending_avoided/2.
#show detective_story/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    mysteries = set(asp.atoms(model, "mystery"))
    accesses = set(asp.atoms(model, "access_case"))
    suspense = set(asp.atoms(model, "suspense"))
    avoided = set(asp.atoms(model, "bad_ending_avoided"))
    detective = set(asp.atoms(model, "detective_story"))
    wanted_pairs = {(g, k) for g in GATES for k in KINGDOMS}
    wanted_gates = {(g,) for g in GATES}
    ok = (
        mysteries == wanted_pairs
        and accesses == wanted_pairs
        and suspense == wanted_gates
        and avoided == wanted_pairs
        and detective == wanted_pairs
    )
    if not ok:
        print("Mismatch between ASP and Python registries.")
        return 1
    for seed in range(5):
        params = StoryParams(
            hero=HEROES[seed % len(HEROES)],
            helper=HELPERS[seed % len(HELPERS)],
            gate=GATES[seed % len(GATES)],
            kingdom=KINGDOMS[seed % len(KINGDOMS)],
            clue=CLUES[seed % len(CLUES)],
            seed=seed,
        )
        sample = generate(params)
        if "bad ending" not in sample.story or "access" not in sample.story:
            print("Generated story failed feature check.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for prompt in sample.prompts:
            print(f"P: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams("Luna", "Inspector Moss", "the moon gate", "the kingdom of Lanterns", "a muddy key print", 0),
    StoryParams("Mira", "Aunt Rowan", "the ivy gate", "the kingdom of Blue Bells", "three silver feathers", 1),
    StoryParams("Theo", "Keeper Bea", "the silver gate", "the kingdom of Little Stars", "a torn blue ribbon", 2),
    StoryParams("Nell", "Detective Fox", "the stone gate", "the kingdom of Lanterns", "a line of golden dust", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print(f"mysteries={len(asp.atoms(model, 'mystery'))}")
            print(f"access_cases={len(asp.atoms(model, 'access_case'))}")
            print(f"suspense_gates={len(asp.atoms(model, 'suspense'))}")
            print(f"bad_endings_avoided={len(asp.atoms(model, 'bad_ending_avoided'))}")
            print(f"detective_stories={len(asp.atoms(model, 'detective_story'))}")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(args.n):
            seed = base_seed + index
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} investigates {sample.params.kingdom}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
