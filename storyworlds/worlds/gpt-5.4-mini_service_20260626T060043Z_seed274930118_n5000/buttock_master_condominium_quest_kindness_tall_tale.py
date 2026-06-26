#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about a master, a condominium, a quest, and kindness.

The seed image:
A mighty master lives in a towering condominium where a grand quest goes wrong.
A forgotten key, a stubborn elevator, and a bruised pride lead to trouble.
Kindness turns the tale: the master helps a neighbor, the neighbor helps back,
and the quest ends with the whole building humming like a happy hive.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "master"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str = "condominium"
    floors: int = 20
    has_lift: bool = True
    has_stairs: bool = True
    has_roof: bool = True


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    trouble: str
    risk: str
    reward: str
    keyword: str = "quest"


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


PLACES = {
    "ivory_tower": Place(name="the Ivory Tower Condominium", floors=30),
    "copper_spire": Place(name="the Copper Spire Condominium", floors=18),
    "blue_lantern": Place(name="the Blue Lantern Condominium", floors=24),
}

QUESTS = {
    "lost_key": Quest(
        id="lost_key",
        verb="find the lost key",
        gerund="searching for the lost key",
        trouble="the elevator jammed between floors",
        risk="the master would miss the evening meeting",
        reward="the rooftop bell would ring at last",
        keyword="quest",
    ),
    "storm_lantern": Quest(
        id="storm_lantern",
        verb="carry a lantern to the roof",
        gerund="climbing toward the roof with a lantern",
        trouble="the hallway lights blinked out",
        risk="the steps would turn the hero shy and slow",
        reward="the whole building would glow like a firefly jar",
        keyword="quest",
    ),
    "kindness_basket": Quest(
        id="kindness_basket",
        verb="deliver a kindness basket",
        gerund="walking room to room with a kindness basket",
        trouble="the front doors stuck tight as a drum",
        risk="the neighbors would wait too long for help",
        reward="every door would open with a smile",
        keyword="kindness",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale condominium quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["woman", "man"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    hero_type = args.gender or rng.choice(["woman", "man"])
    helper_type = args.helper_gender or rng.choice(["woman", "man"])
    hero_name = args.name or rng.choice(["Mabel", "Clive", "Rosie", "Hank", "Nora", "Bram"])
    helper_name = args.helper or rng.choice(["Tilda", "Earl", "June", "Otis", "Pearl", "Wes"])
    return StoryParams(
        place=place,
        quest=quest,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def _talk_tall(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"In {world.place.name}, {hero.id} was a great {hero.type} with a voice "
        f"like a brass trumpet and a heart big as a barn."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had a mighty fondness for a good {world.quest.keyword}, "
        f"and {hero.pronoun('subject')} promised to {world.quest.verb} before supper."
    )
    world.say(
        f"{helper.id} lived two doors down, quick as a whip and kind as rain, "
        f"always ready to lend a hand in the tall condominium."
    )


def _begin_quest(world: World, hero: Entity) -> None:
    hero.memes["determination"] = hero.memes.get("determination", 0.0) + 1
    world.say(
        f"So {hero.id} set out {world.quest.gerund}, while the condominium "
        f"stood taller than a stack of storybooks."
    )


def _trouble(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    hero.meters["stuck"] = hero.meters.get("stuck", 0.0) + 1
    world.say(
        f"But up came trouble: {world.quest.trouble}. "
        f"{hero.id} stamped {hero.pronoun('possessive')} foot and said, "
        f'"Well, butter my boots, that is a tall pinch indeed!"'
    )
    world.say(
        f"Down the hall, {helper.id} heard the ruckus and came trotting over, "
        f"kindness shining brighter than a lantern."
    )


def _kindness_turn(world: World, hero: Entity, helper: Entity) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{helper.id} did not laugh. Instead, {helper.pronoun('subject')} said, "
        f'"Let’s take the stairs together, one brave step at a time."'
    )
    world.say(
        f"That was kindness plain and true. Together they climbed, "
        f"and the condominium seemed to straighten its shoulders to cheer them on."
    )


def _resolution(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["stuck"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"At last they reached the top, and {hero.id} found the missing piece "
        f"right where the wind had tucked it."
    )
    world.say(
        f"{world.quest.reward.capitalize()}, and the whole building hummed with relief."
    )
    world.say(
        f"{hero.id} thanked {helper.id}, and the master of the quest learned "
        f"that kindness can lift a heavy day better than a crane."
    )


def tell(place: Place, quest: Quest, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place, quest)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    world.facts.update(hero=hero, helper=helper, quest=quest, place=place)

    _talk_tall(world, hero, helper)
    world.para()
    _begin_quest(world, hero)
    _trouble(world, hero, helper)
    world.para()
    _kindness_turn(world, hero, helper)
    _resolution(world, hero, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a tall tale about a {world.facts['hero'].type} named {world.facts['hero'].id} "
        f"who has a grand {world.quest.keyword} in {world.place.name}.",
        f"Tell a child-friendly story where {world.facts['helper'].id} helps with "
        f"{world.quest.gerund} and kindness saves the day.",
        f"Make a playful tall tale set in a condominium with a heroic quest and a kind helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    quest: Quest = world.facts["quest"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who is the story about in {place.name}?",
            answer=f"It is about {hero.id}, a {hero.type} with a mighty heart, and {helper.id}, who helps with the quest.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do?",
            answer=f"{hero.id} was trying to {quest.verb}. The tale starts with a bold promise and then a problem in the condominium.",
        ),
        QAItem(
            question=f"How did the trouble get solved?",
            answer=f"{helper.id} showed kindness, walked with {hero.id}, and helped finish the quest so the building could cheer.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"At the end, the quest was done, the worry was gone, and the condominium felt bright and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condominium?",
            answer="A condominium is a building with many homes inside it, usually stacked up on different floors.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, caring, and being gentle with someone else.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find, carry, or do something important.",
        ),
        QAItem(
            question="What is a buttock?",
            answer="A buttock is one of the soft round parts at the back of the body where a person sits.",
        ),
        QAItem(
            question="Why do people use stairs when the lift is stuck?",
            answer="People use stairs because they can still go up and down even when the lift does not work.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_quest(Q) :- quest(Q).
story_ok(P,Q) :- valid_place(P), valid_quest(Q).
#show story_ok/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show story_ok/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "story_ok"))
    py = {(p, q) for p in PLACES for q in QUESTS}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(atoms - py))
    print("only in python:", sorted(py - atoms))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        QUESTS[params.quest],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(place="ivory_tower", quest="lost_key", hero_name="Mabel", hero_type="woman", helper_name="Tilda", helper_type="woman"),
    StoryParams(place="copper_spire", quest="storm_lantern", hero_name="Hank", hero_type="man", helper_name="June", helper_type="woman"),
    StoryParams(place="blue_lantern", quest="kindness_basket", hero_name="Rosie", hero_type="woman", helper_name="Earl", helper_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        print(sorted(asp.atoms(model, "story_ok")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
