#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eruption_tug_jersey_quest_rhyme_friendship_superhero.py
==============================================================================================================

A small superhero storyworld about a quest, a rhyme, and a friendship that
helps carry a jersey safely through an eruption.

The seed idea:
- A young hero wants to tug on a special jersey for a quest.
- A nearby eruption makes the trip risky.
- A friend offers a rhyme and a better plan.
- The hero learns that teamwork is stronger than rushing alone.

This script keeps the world tiny and classical:
- a hero
- a friend
- a quest
- a prized jersey
- an eruption risk
- a turn from stubbornness to friendship

It supports the shared Storyweavers interface, plus an inline ASP twin and a
reasonableness gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine"}
        male = {"boy", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    route: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Jersey:
    label: str
    phrase: str
    region: str = "torso"
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Ally:
    id: str
    label: str
    rhyme: str
    help_line: str
    fix_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "city": Setting(place="the city rooftops", affords={"quest", "rhyme"}),
    "harbor": Setting(place="the harbor", affords={"quest", "rhyme"}),
    "canyon": Setting(place="the canyon bridge", affords={"quest", "rhyme"}),
}

QUESTS = {
    "rescue": Quest(
        id="rescue",
        goal="rescue the comet map",
        route="race across the rooftop path",
        danger="ashes could blur the map",
        keyword="quest",
        tags={"quest"},
    ),
    "signal": Quest(
        id="signal",
        goal="deliver the signal flare",
        route="sprint to the tower gate",
        danger="heat could snuff the flare",
        keyword="quest",
        tags={"quest"},
    ),
    "bridge": Quest(
        id="bridge",
        goal="bring the bridge key",
        route="dash across the bridge stones",
        danger="lava sparks could singe the key",
        keyword="quest",
        tags={"quest", "eruption"},
    ),
}

JERSEYS = {
    "team": Jersey(label="team jersey", phrase="a bright blue team jersey"),
    "star": Jersey(label="star jersey", phrase="a red star jersey"),
    "capejersey": Jersey(label="cape jersey", phrase="a stretchy jersey cape"),
}

ALLIES = {
    "piper": Ally(
        id="Piper",
        label="Piper",
        rhyme="When lava huffs and ash goes high, we move with care and let it sigh.",
        help_line="I can help you keep the jersey steady.",
        fix_line="We can use a softer tug and a safer path.",
        tags={"rhyme", "friendship"},
    ),
    "milo": Ally(
        id="Milo",
        label="Milo",
        rhyme="A friend who waits and counts to three can help a brave plan come to be.",
        help_line="I know a calmer way to go.",
        fix_line="Let's slow down and share the load.",
        tags={"rhyme", "friendship"},
    ),
}

HERO_NAMES = ["Nova", "Sky", "Jett", "Ruby", "Zane", "Luna", "Theo", "Mina"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "bouncy", "quick", "curious", "spirited"]


@dataclass
class StoryParams:
    place: str
    quest: str
    jersey: str
    hero_name: str
    hero_type: str
    ally: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    quest = QUESTS[params.quest]
    jersey = JERSEYS[params.jersey]
    if jersey.region != "torso":
        raise StoryError("This world only supports a torso jersey.")
    if "quest" not in quest.tags:
        raise StoryError("The story needs a quest.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("Unknown hero type.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: eruption, tug, jersey, quest, rhyme, friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--jersey", choices=JERSEYS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--ally", choices=ALLIES)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    jersey = args.jersey or rng.choice(list(JERSEYS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    ally = args.ally or rng.choice(list(ALLIES))
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, quest=quest, jersey=jersey, hero_name=hero_name, hero_type=hero_type, ally=ally, trait=trait)
    reasonableness_gate(params)
    return params


def _do_eruption(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["ash"] = hero.meters.get("ash", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(f"Far away, an eruption puffed ash into the sky, and {hero.id} felt the path get harder.")


def _do_tug(world: World, hero: Entity, jersey: Entity) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1.0
    world.say(f"{hero.id} reached for {jersey.phrase} and gave it a tug, hoping to start the quest at once.")


def _do_friendship(world: World, ally: Entity, hero: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    world.say(f"{ally.id} stepped beside {hero.id} like a true friend and offered a steady smile.")


def _do_rhyme(world: World, ally: Entity) -> None:
    world.say(f'{ally.id} said a rhyme: "{ALLIES[ally.id.lower()].rhyme}"')


def _resolve(world: World, hero: Entity, ally: Entity, quest: Quest, jersey: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{ally.id} helped {hero.id} slow down, carry the jersey safely, and choose the smarter route."
    )
    world.say(
        f"Together they finished the {quest.keyword} quest: {hero.id} could wear {jersey.label}, and the team stayed proud."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    ally_cfg = ALLIES[params.ally]
    ally = world.add(Entity(id=ally_cfg.id, kind="character", type="friend", label=ally_cfg.label))
    quest = QUESTS[params.quest]
    jersey_cfg = JERSEYS[params.jersey]
    jersey = world.add(Entity(id="Jersey", type="jersey", label=jersey_cfg.label, phrase=jersey_cfg.phrase, owner=hero.id))
    jersey.worn_by = hero.id

    world.say(f"{hero.id} was a {params.trait} young hero with a big {quest.keyword} ahead of {world.setting.place}.")
    world.say(f"{hero.id} loved {jersey.phrase} because it made every mission feel official.")

    world.para()
    world.say(f"One day, {hero.id} had to {quest.route} to {quest.goal}.")
    _do_eruption(world, hero, quest)
    _do_tug(world, hero, jersey)
    world.say(f"But the eruption danger was real: {quest.danger}.")
    _do_rhyme(world, ally)
    _do_friendship(world, ally, hero)

    world.para()
    world.say(f"{hero.id} stopped tugging so hard and listened to {ally.id}.")
    _resolve(world, hero, ally, quest, jersey)

    world.facts = {
        "hero": hero,
        "ally": ally,
        "quest": quest,
        "jersey": jersey,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    quest = f["quest"]
    jersey = f["jersey"]
    return [
        f'Write a short superhero story for a young child about an eruption, a tug, and a {jersey.label}.',
        f"Tell a gentle quest story where {hero.id} wants to keep {jersey.phrase} safe while an eruption makes the journey tricky.",
        f"Write a story with friendship and a rhyme in which {ally.id} helps {hero.id} finish a {quest.keyword} quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    quest = f["quest"]
    jersey = f["jersey"]
    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id}, a {hero.pronoun('subject')} who wants to finish a {quest.keyword} quest.",
        ),
        QAItem(
            question=f"What did {hero.id} tug on?",
            answer=f"{hero.id} tugged on {jersey.phrase}, because {hero.pronoun('subject')} wanted to start the mission right away.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm during the eruption?",
            answer=f"{ally.id} helped {hero.id} stay calm with a rhyme and friendly advice.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {ally.id} working together so the jersey stayed safe and the quest was finished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a special goal or mission that someone tries hard to complete.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short line or song where the sounds at the ends of words match or sound alike.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and being a good teammate.",
        ),
        QAItem(
            question="What is an eruption?",
            answer="An eruption is when hot material, ash, or lava bursts out from a volcano.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            mems = {k: v for k, v in e.memes.items() if v}
            mets = {k: v for k, v in e.meters.items() if v}
            if mems:
                bits.append(f"memes={mems}")
            if mets:
                bits.append(f"meters={mets}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_story/4.
valid_story(Place,Quest,Jersey,Ally) :- setting(Place), quest(Quest), jersey(Jersey), ally(Ally).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for j in JERSEYS:
        lines.append(asp.fact("jersey", j))
    for a in ALLIES:
        lines.append(asp.fact("ally", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, q, j, a) for p in SETTINGS for q in QUESTS for j in JERSEYS for a in ALLIES)
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - py_set:
        print(" only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in Python:", sorted(py_set - asp_set))
    return 1


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
    StoryParams(place="city", quest="rescue", jersey="team", hero_name="Nova", hero_type="girl", ally="piper", trait="brave"),
    StoryParams(place="harbor", quest="signal", jersey="star", hero_name="Jett", hero_type="boy", ally="milo", trait="curious"),
    StoryParams(place="canyon", quest="bridge", jersey="capejersey", hero_name="Ruby", hero_type="girl", ally="piper", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
