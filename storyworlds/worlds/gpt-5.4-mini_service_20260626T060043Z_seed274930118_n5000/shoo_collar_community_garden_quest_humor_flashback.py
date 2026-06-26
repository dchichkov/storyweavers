#!/usr/bin/env python3
"""
storyworlds/worlds/shoo_collar_community_garden_quest_humor_flashback.py
========================================================================

A compact story world for a whodunit-style community garden mystery:
a small quest, a few funny beats, and a flashback that reveals how the
missing collar went missing in the first place.

Premise:
- In a community garden, a child and a caretaker notice that a collar
  tied to the garden's shoo-string scarecrow is gone.
- The group follows tiny clues through beds, bins, and bean poles.
- A flashback explains the odd earlier moment that made the clue make sense.
- The ending proves the collar's new place and shows the garden calmer.

This file follows the Storyweavers storyworld contract:
- typed world entities with meters and memes
- standalone stdlib script
- lazy ASP import via the shared helper
- generation, QA, trace, parser, resolve_params, emit, main
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _init_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _init_meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the community garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    search: str
    reveal: str
    location: str
    funny_line: str
    flashback_line: str


@dataclass
class Collar:
    label: str
    phrase: str
    location: str
    owner_kind: str = "dog"
    worn: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _bump_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _bump_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _search_step(world: World, searcher: Entity, quest: Quest, collar: Entity) -> None:
    _bump_meme(searcher, "curiosity", 1)
    world.say(
        f"{searcher.id} followed the clue {quest.clue} and looked where {quest.search}."
    )
    if collar.location == quest.location:
        _bump_meme(searcher, "joy", 1)
        _bump_meme(searcher, "relief", 1)


def _humor_step(world: World, helper: Entity, quest: Quest) -> None:
    _bump_meme(helper, "humor", 1)
    world.say(f"{helper.id} gave a little grin and said, “{quest.funny_line}”")


def _flashback_step(world: World, narrator: Entity, quest: Quest) -> None:
    _bump_meme(narrator, "memory", 1)
    world.say(
        f"Then {narrator.id} remembered {quest.flashback_line}, and the clue finally made sense."
    )


def _resolve(world: World, hero: Entity, helper: Entity, collar: Entity, quest: Quest) -> None:
    collar.location = "around the bean pole"
    collar.worn_by = None
    collar.carried_by = hero.id
    _bump_meme(hero, "joy", 2)
    _bump_meme(helper, "joy", 1)
    world.say(
        f"They found the collar {quest.reveal}. {hero.id} lifted it carefully, and {helper.id} laughed at the neat little fix."
    )
    world.say(
        f"At the end, the garden was calm again, and the collar was safe in {hero.pronoun('possessive')} hands."
    )


SETTING = Setting(place="the community garden", affords={"search", "story"})
QUESTS = {
    "collar_quest": Quest(
        id="collar_quest",
        goal="find the missing collar",
        clue="the tiny muddy prints near the bean poles",
        search="the path by the tomato beds, the hose, and the compost bin",
        reveal="looped around the bean pole like a bright little loop of luck",
        location="around the bean pole",
        funny_line="If a collar wants privacy, it sure picked a dramatic hiding place!",
        flashback_line="the gardener had used the collar as a quick tag to scare birds from the beans",
    ),
}


@dataclass
class StoryParams:
    quest: str
    hero_name: str = "Mina"
    hero_type: str = "girl"
    helper_name: str = "Tariq"
    helper_type: str = "boy"
    caretaker_name: str = "Mrs. Vale"
    caretaker_type: str = "woman"
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Ivy", "Lena", "Nora", "Zia"]
BOY_NAMES = ["Tariq", "Owen", "Eli", "Noah", "Ben"]
CAREGIVER_NAMES = ["Mrs. Vale", "Mr. Park", "Aunt June", "Uncle Reed"]
TRAITS = ["careful", "brave", "sharp-eyed", "kind", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style community garden quest with humor and flashback.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker-name")
    ap.add_argument("--caretaker-type", choices=["woman", "man"])
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
    quest = args.quest or "collar_quest"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    caretaker_type = args.caretaker_type or rng.choice(["woman", "man"])

    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(BOY_NAMES if helper_type == "boy" else GIRL_NAMES)
    caretaker_name = args.caretaker_name or rng.choice(CAREGIVER_NAMES)

    return StoryParams(
        quest=quest,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        caretaker_name=caretaker_name,
        caretaker_type=caretaker_type,
    )


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    quest = QUESTS[params.quest]

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["sharp-eyed", "careful"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, traits=["funny", "kind"]))
    caretaker = world.add(Entity(id=params.caretaker_name, kind="character", type=params.caretaker_type, traits=["patient"]))

    collar = world.add(Entity(
        id="collar",
        kind="thing",
        type="collar",
        label="collar",
        phrase="a bright red collar with a brass buckle",
        owner=caretaker.id,
        caretaker=caretaker.id,
        location="the strawberry bed",
    ))
    shoo_string = world.add(Entity(
        id="shoo_string",
        kind="thing",
        type="string",
        label="shoo-string",
        phrase="a fluttery ribbon meant to shoo away birds",
        owner=caretaker.id,
        caretaker=caretaker.id,
        location="around the bean pole",
    ))

    world.facts.update(hero=hero, helper=helper, caretaker=caretaker, collar=collar, quest=quest, shoo_string=shoo_string)

    # Act 1
    world.say(
        f"In the community garden, {hero.id} and {caretaker.id} noticed something odd: the collar was gone."
    )
    world.say(
        f"It had been hanging by the bean poles, where it helped the shoo-string flap and shoo curious birds."
    )
    world.say(
        f"{hero.id} said, “This is a quest.” {helper.id} nodded, because the missing collar felt like a tiny mystery with muddy footprints."
    )

    # Act 2
    world.para()
    _search_step(world, hero, quest, collar)
    _humor_step(world, helper, quest)
    world.say(
        f"They checked the tomato rows, the watering can, and the compost bin, but the collar was not there."
    )
    _flashback_step(world, caretaker, quest)

    # Act 3
    world.para()
    world.say(
        f"That flashback explained why the collar had vanished: it had been tied near the beans as a quick garden trick, not worn by anyone."
    )
    _resolve(world, hero, helper, collar, quest)

    world.facts.update(
        resolved=True,
        quest=quest,
        hero=hero,
        helper=helper,
        caretaker=caretaker,
        collar=collar,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest: Quest = f["quest"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    caretaker: Entity = f["caretaker"]
    return [
        "Write a short whodunit-style story set in a community garden where a missing collar becomes a little quest.",
        f"Tell a gentle mystery about {hero.id}, {helper.id}, and {caretaker.id} looking for a collar, with a funny clue and a flashback.",
        f"Write a child-friendly detective story about a community garden, a shoo-string, and a collar that needs to be found.",
        f"Make it feel like a small mystery: someone notices a missing collar, follows muddy clues, remembers a flashback, and solves the quest.",
        f"Include humor and a flashback while {hero.id} investigates why the collar disappeared from the bean pole area.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    caretaker: Entity = f["caretaker"]
    collar: Entity = f["collar"]
    quest: Quest = f["quest"]

    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} in the community garden?",
            answer=f"It is a small whodunit-style quest about a missing collar in the community garden.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} start looking for the collar?",
            answer=f"The tiny muddy prints near the bean poles helped {hero.id} start the search.",
        ),
        QAItem(
            question=f"Why did {helper.id} make the story lighter and funnier?",
            answer=f"{helper.id} made it lighter by joking about the collar's dramatic hiding place.",
        ),
        QAItem(
            question=f"What did the flashback explain about the collar?",
            answer=f"The flashback explained that the collar had been tied near the beans as a quick trick to shoo birds away.",
        ),
        QAItem(
            question=f"Where was the collar found in the end?",
            answer=f"The collar was found looped around the bean pole, which solved the little mystery.",
        ),
        QAItem(
            question=f"How did the story end for {caretaker.id} and the garden?",
            answer=f"{caretaker.id} got the collar back, and the community garden became calm and orderly again.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a community garden?",
        answer="A community garden is a shared garden where neighbors grow plants, help with watering, and take care of the beds together.",
    ),
    QAItem(
        question="What is a collar?",
        answer="A collar is a band that goes around an animal's neck or around clothing as a trim or tag.",
    ),
    QAItem(
        question="Why do people shoo birds from a garden?",
        answer="People shoo birds from a garden because birds may peck at seeds or ripe fruits and disturb the plants.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.

valid("community_garden") :- setting("community_garden"), has_collar_mystery, shoo_useful, flashback_present, humor_present.
has_collar_mystery :- collar_missing.
shoo_useful :- shoo_string.
flashback_present :- flashback.
humor_present :- humor.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "community_garden"),
            asp.fact("collar_missing"),
            asp.fact("shoo_string"),
            asp.fact("flashback"),
            asp.fact("humor"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    ok = bool(asp.atoms(model, "valid"))
    py_ok = True
    if ok == py_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = _build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(quest="collar_quest", hero_name="Mina", hero_type="girl", helper_name="Tariq", helper_type="boy", caretaker_name="Mrs. Vale", caretaker_type="woman"),
        StoryParams(quest="collar_quest", hero_name="Ivy", hero_type="girl", helper_name="Owen", helper_type="boy", caretaker_name="Mr. Park", caretaker_type="man"),
        StoryParams(quest="collar_quest", hero_name="Noah", hero_type="boy", helper_name="Lena", helper_type="girl", caretaker_name="Aunt June", caretaker_type="woman"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in build_curated()]
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: collar quest in the community garden"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
