#!/usr/bin/env python3
"""
A small fable-style storyworld about a nation, a promise, and a quest.

Premise:
A tiny nation depends on a promissory ribbon that keeps a fair trade vow.
When the ribbon goes missing, a young messenger with cheeks that grow dim
from worry must go on a quest to bring it home before the market bell.

This script models the story as a stateful simulation:
- physical meters track carrying, distance, loss, and recovery
- emotional memes track worry, hope, pride, and trust
- a quest advances through locations and changes the world
- the ending reflects what has changed in the model
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def thing(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    neighbors: list[str] = field(default_factory=list)
    promise_holds: bool = False
    note: str = ""


@dataclass
class Quest:
    id: str
    start: str
    goal: str
    route: list[str]
    prize: str
    risk: str
    turn: str
    return_clause: str


@dataclass
class StoryParams:
    nation: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    quest: str
    seed: Optional[int] = None


class World:
    def __init__(self, nation: str) -> None:
        self.nation = nation
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_place(self, p: Place) -> Place:
        self.places[p.id] = p
        return p

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    world = World(params.nation)
    world.add_place(Place("square", "the market square", neighbors=["gate"], note="The bell is heard here."))
    world.add_place(Place("gate", "the stone gate", neighbors=["square", "hill"]))
    world.add_place(Place("hill", "the windy hill", neighbors=["gate", "well"]))
    world.add_place(Place("well", "the old well", neighbors=["hill"], promise_holds=True, note="A loose box can hide here."))

    hero = world.add_entity(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        location="square",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "pride": 0.0, "trust": 1.0},
    ))
    helper = world.add_entity(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        location="square",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "pride": 0.0, "trust": 1.0},
    ))
    ribbon = world.add_entity(Entity(
        id="promissory_ribbon",
        kind="thing",
        type="ribbon",
        label="promissory ribbon",
        phrase="a bright promissory ribbon sealed with blue wax",
        owner=params.nation,
        location="well",
        meters={"lost": 1.0},
    ))
    chest = world.add_entity(Entity(
        id="promise_chest",
        kind="thing",
        type="chest",
        label="promise chest",
        phrase="a little cedar chest",
        location="well",
        meters={"closed": 1.0},
    ))
    hero.meters["cheek_dim"] = 0.0
    helper.meters["cheek_dim"] = 0.0
    world.facts.update(hero=hero, helper=helper, ribbon=ribbon, chest=chest)
    return world


def dim_cheeks(world: World, hero: Entity) -> None:
    hero.meters["cheek_dim"] += 1.0
    hero.memes["worry"] += 1.0


def brighten_cheeks(world: World, hero: Entity) -> None:
    hero.meters["cheek_dim"] = max(0.0, hero.meters["cheek_dim"] - 1.0)
    hero.memes["hope"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)


def travel(world: World, hero: Entity, dest: str) -> None:
    hero.location = dest
    hero.meters["distance"] += 1.0


def find_ribbon(world: World, hero: Entity) -> bool:
    ribbon = world.get("promissory_ribbon")
    if hero.location == ribbon.location:
        ribbon.carried_by = hero.id
        ribbon.location = None
        hero.meters["carried_ribbon"] = 1.0
        hero.memes["pride"] += 1.0
        return True
    return False


def return_ribbon(world: World, hero: Entity) -> None:
    ribbon = world.get("promissory_ribbon")
    ribbon.carried_by = None
    ribbon.location = "square"
    hero.meters["carried_ribbon"] = 0.0


def narrate_opening(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    world.say(
        f"In the small nation of {world.nation}, the people prized a promissory ribbon "
        f"that kept their market vows as neat as sewn thread."
    )
    world.say(
        f"{hero.id} was a kind {hero.type} who often ran messages for the town, and "
        f"{helper.id} was a steady {helper.type} who never laughed at a worried face."
    )
    world.say(
        f"One morning, the ribbon was gone from the square, and {hero.id}'s cheeks grew dim "
        f"with worry."
    )


def narrate_quest(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    quest: Quest = world.facts["quest"]
    world.para()
    world.say(
        f"{helper.id} pointed toward the stone gate and said the ribbon might be hidden "
        f"along the old path."
    )
    world.say(
        f"So {hero.id} began the quest from {world.places[quest.start].label} to "
        f"{world.places[quest.goal].label}, with the wind tugging at {hero.pronoun('possessive')} cloak."
    )
    for step in quest.route:
        travel(world, hero, step)
        if step == "gate":
            world.say(f"At {world.places[step].label}, {hero.id} found no ribbon, only a cold latch and a long shadow.")
            dim_cheeks(world, hero)
        elif step == "hill":
            world.say(f"At {world.places[step].label}, {hero.id} saw footprints and felt hope wake up again.")
            brighten_cheeks(world, hero)
        elif step == "well":
            world.say(f"At {world.places[step].label}, {hero.id} lifted a loose box and found the promissory ribbon tucked beneath it.")
            if find_ribbon(world, hero):
                world.say(f"The wax seal still shone, and {hero.id} knew the nation could keep its word.")
        else:
            world.say(f"{hero.id} hurried on toward {world.places[step].label}.")
    world.para()
    world.say(
        f"On the way back, {helper.id} met {hero.id} at the hill and carried the little chest, "
        f"so the return was lighter than the going."
    )
    brighten_cheeks(world, hero)
    world.say(
        f"By sunset, {hero.id} came home to the square with the ribbon safe again, "
        f"and {hero.pronoun('possessive')} cheeks were bright instead of dim."
    )
    world.say(
        f"The market bell rang, the vow was honored, and the nation slept easy."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero_name)
    helper = world.get(params.helper_name)
    quest = Quest(
        id=params.quest,
        start="square",
        goal="well",
        route=["gate", "hill", "well", "hill", "square"],
        prize="promissory ribbon",
        risk="cheek-dim worry",
        turn="find the ribbon hidden by the old well",
        return_clause="carry it home before the bell",
    )
    world.facts["quest"] = quest
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    narrate_opening(world)
    narrate_quest(world)
    return world


def make_story_params(seed: int, args: argparse.Namespace) -> StoryParams:
    rng = random.Random(seed)
    nation = args.nation or rng.choice(["Aster Vale", "Brindle Cove", "Clovermark"])
    hero_name = args.hero_name or rng.choice(["Mina", "Taro", "Lena", "Pip"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(["Old Bram", "Nina", "Soren", "Aunt Sia"])
    helper_type = args.helper_type or rng.choice(["man", "woman"])
    return StoryParams(
        nation=nation,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        quest="the ribbon quest",
        seed=seed,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    quest: Quest = world.facts["quest"]
    return [
        f"Write a fable about a small nation and a quest to recover a promissory ribbon.",
        f"Tell a child-friendly story where {hero.id} crosses {world.places[quest.goal].label} to find what the nation lost.",
        f"Write a short fable in which {helper.id} helps {hero.id} bring back a promise before the market bell."
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    ribbon = world.facts["ribbon"]
    quest: Quest = world.facts["quest"]
    return [
        QAItem(
            question=f"Why did {hero.id}'s cheeks grow dim at the start of the story?",
            answer=f"{hero.id} felt worried because the nation had lost the {ribbon.label}, and keeping the promise mattered."
        ),
        QAItem(
            question=f"Where did {hero.id} find the promissory ribbon?",
            answer=f"{hero.id} found it near the old well, tucked beneath a loose box at the end of the quest."
        ),
        QAItem(
            question=f"How did {helper.id} help with the quest?",
            answer=f"{helper.id} guided {hero.id} toward the right path and carried the little chest on the way home."
        ),
        QAItem(
            question=f"What changed for the nation at the end?",
            answer=f"The ribbon was brought back to the square, the vow was kept, and the nation could rest peacefully again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a promise?",
            answer="A promise is a pledge that someone says they will keep or do later."
        ),
        QAItem(
            question="What is a nation?",
            answer="A nation is a group of people who live together and share rules, stories, and a place they call home."
        ),
        QAItem(
            question="What can make cheeks look dim?",
            answer="Cheeks can look dim when a person feels tired, worried, or very sad."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a purpose, like finding something lost or doing something important."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:16} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A ribbon is at risk if it is lost and the quest reaches its hiding place.
at_risk(R) :- ribbon(R), lost(R), hidden_at(R, P), reached(P).

% A quest succeeds when the hero reaches the goal and the ribbon is recovered.
recovered(R) :- at_risk(R), carried(R).

quest_success(Q) :- quest(Q), target(Q, R), recovered(R).

% Cheeks dim when worry is present, and brighten when hope is present.
dim_cheeks(H) :- hero(H), worry(H).
bright_cheeks(H) :- hero(H), hope(H).
"""


def asp_facts() -> str:
    import asp
    world_nations = ["aster_vale", "brindle_cove", "clovermark"]
    lines = []
    for n in world_nations:
        lines.append(asp.fact("nation", n))
    lines.append(asp.fact("quest", "ribbon_quest"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("ribbon", "promissory_ribbon"))
    lines.append(asp.fact("lost", "promissory_ribbon"))
    lines.append(asp.fact("hidden_at", "promissory_ribbon", "well"))
    lines.append(asp.fact("target", "ribbon_quest", "promissory_ribbon"))
    lines.append(asp.fact("reached", "well"))
    lines.append(asp.fact("carried", "promissory_ribbon"))
    lines.append(asp.fact("worry", "hero"))
    lines.append(asp.fact("hope", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_success() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_success/1."))
    return sorted(set(asp.atoms(model, "quest_success")))


def asp_reasonable() -> bool:
    return len(asp_story_success()) > 0


def asp_verify() -> int:
    if asp_reasonable():
        print("OK: ASP twin recognizes the quest as successful.")
        return 0
    print("MISMATCH: ASP twin failed to derive quest success.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld about a nation and a quest.")
    ap.add_argument("--nation")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
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
    return make_story_params(rng.randrange(2**31) if args.seed is None else args.seed, args)


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
    StoryParams(nation="Aster Vale", hero_name="Mina", hero_type="girl", helper_name="Old Bram", helper_type="man", quest="the ribbon quest", seed=1),
    StoryParams(nation="Brindle Cove", hero_name="Taro", hero_type="boy", helper_name="Nina", helper_type="woman", quest="the ribbon quest", seed=2),
    StoryParams(nation="Clovermark", hero_name="Lena", hero_type="girl", helper_name="Soren", helper_type="man", quest="the ribbon quest", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_success/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("quest_success", asp_story_success())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = make_story_params(base_seed + i, args)
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.nation} / {p.hero_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
