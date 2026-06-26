#!/usr/bin/env python3
"""
farm_quest_ghost_story.py
=========================

A tiny storyworld for a farm quest with a ghost-story mood.

Premise:
A child on a farm hears of a small quest: find the missing lantern key
before the barn goes dark. The farm is a little eerie at dusk, and a
ghostly helper may be honest, tricky, or both.

The world simulates:
- a farm with places and objects
- a quest with a target and a reason it matters
- a ghostly presence with emotional pressure
- concrete meters/memes that drive the story turn and ending

The story should feel like a complete, child-facing ghost story:
beginning, uneasy middle, turn, and a resolved ending image.
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
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class FarmSetting:
    place: str = "the farm"
    twilight: bool = True
    has_barn: bool = True
    has_field: bool = True
    has_well: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    thing: str
    danger: str
    reward: str
    location: str
    ghost_topic: str
    keyword: str = "farm"


@dataclass
class Ghost:
    id: str
    label: str
    type: str = "ghost"
    place: str = "barn"
    is_friend: bool = False
    tricky: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: FarmSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.ghost: Optional[Ghost] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.night: bool = False
        self.mist: bool = True

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.ghost = _copy.deepcopy(self.ghost)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.night = self.night
        clone.mist = self.mist
        clone.facts = dict(self.facts)
        return clone


QUESTS = {
    "lantern_key": Quest(
        id="lantern_key",
        goal="find the lantern key",
        clue="a cold rattle near the hay bales",
        thing="lantern key",
        danger="the barn will stay dark",
        reward="light in the barn",
        location="barn loft",
        ghost_topic="lantern",
    ),
    "lost_lamb": Quest(
        id="lost_lamb",
        goal="find the lost lamb",
        clue="tiny prints near the wet fence",
        thing="little lamb",
        danger="the lamb may shiver alone",
        reward="a warm pen and a happy bleat",
        location="field edge",
        ghost_topic="lamb",
    ),
    "silver_egg": Quest(
        id="silver_egg",
        goal="find the silver egg",
        clue="a shiny flash by the old well",
        thing="silver egg",
        danger="the hen will not settle",
        reward="a calm nest at dawn",
        location="well path",
        ghost_topic="egg",
    ),
}

CHARACTER_NAMES = ["Mina", "Leo", "Nora", "Owen", "Elsie", "Theo"]
TRAITS = ["brave", "quiet", "curious", "careful", "gentle", "steady"]


def quest_endangers(quest: Quest) -> bool:
    return True


def select_quest(rng: random.Random) -> Quest:
    return QUESTS[rng.choice(sorted(QUESTS))]


def valid_story(quest: Quest, name: str, ghost_friend: bool) -> bool:
    if not quest_endangers(quest):
        return False
    if quest.id == "silver_egg" and ghost_friend is False:
        return True
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Farm quest ghost story world.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--ghost-friend", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random):
    quest = QUESTS[args.quest] if args.quest else select_quest(rng)
    name = args.name or rng.choice(CHARACTER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    ghost_friend = bool(args.ghost_friend)
    if not valid_story(quest, name, ghost_friend):
        raise StoryError("The requested farm quest cannot make a coherent story.")
    return StoryParams(quest=quest.id, name=name, trait=trait, ghost_friend=ghost_friend)


@dataclass
class StoryParams:
    quest: str
    name: str
    trait: str
    ghost_friend: bool = False
    seed: Optional[int] = None


def _build_world(params: StoryParams) -> World:
    setting = FarmSetting()
    world = World(setting)
    quest = QUESTS[params.quest]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Nora", "Elsie"} else "boy",
        label=params.name,
        meters={"courage": 0.0, "tired": 0.0},
        memes={"wonder": 0.0, "fear": 0.0, "hope": 0.0},
    ))
    parent = world.add(Entity(
        id="farmer",
        kind="character",
        type="farmer",
        label="the farmer",
        meters={"work": 0.0},
        memes={"worry": 0.0},
    ))
    target = world.add(Entity(
        id=quest.id,
        type="thing",
        label=quest.thing,
        phrase=quest.thing,
        caretaker="farmer",
        place=quest.location,
        meters={"hidden": 1.0},
    ))
    ghost = Ghost(
        id="ghost",
        label="a pale barn ghost",
        place="barn",
        is_friend=params.ghost_friend,
        tricky=not params.ghost_friend,
        meters={"seen": 0.0},
        memes={"mystery": 1.0, "kindness": 0.5 if params.ghost_friend else 0.0},
    )
    world.ghost = ghost

    world.say(f"{hero.id} lived on {world.setting.place}, where the fields rustled at dusk.")
    world.say(f"{hero.id} was a {params.trait} child who loved looking for hidden things.")
    world.say(f"One evening, {hero.id} heard about a quest: {quest.goal}.")
    world.say(f"The clue was {quest.clue}, and the reward would be {quest.reward}.")

    world.para()
    hero.memes["wonder"] += 1
    hero.meters["courage"] += 0.5
    world.say(f"The sky turned dim, and the barn looked bigger than before.")
    world.say(f"{hero.id} went toward the {quest.location} with a small lantern in one hand.")
    hero.memes["fear"] += 0.5
    parent.memes["worry"] += 0.5
    world.say(f"The farmer frowned and said, \"Be careful. {quest.danger}.\"")

    if params.ghost_friend:
        world.para()
        ghost.seen = 1.0
        hero.memes["fear"] += 0.25
        world.say("A soft glow floated out of the barn shadows.")
        world.say(f"It was {ghost.label}, who whispered that the clue was real.")
        world.say(f"The ghost pointed toward the hay and nodded at the cold rattle.")
        hero.meters["courage"] += 0.75
        hero.memes["hope"] += 1.0
    else:
        world.para()
        ghost.seen = 1.0
        hero.memes["fear"] += 0.75
        world.say("Then the wind made the boards creak, and something pale drifted by the barn.")
        world.say(f"{hero.id} froze for a moment, because the farm felt haunted.")
        world.say(f"But the pale shape only floated ahead, as if it wanted to lead the way.")
        hero.meters["courage"] += 0.5
        hero.memes["hope"] += 0.5

    world.para()
    world.say(f"{hero.id} followed the clue to the {quest.location}.")
    world.say(f"Under the hay and near the old tools, {hero.id} found the {quest.thing}.")
    target.meters["hidden"] = 0.0
    target.meters["found"] = 1.0
    hero.memes["hope"] += 1.0
    hero.meters["courage"] += 0.5

    world.para()
    if params.ghost_friend:
        world.say(f"The ghost smiled, and the barn key shimmered in {hero.id}'s palm.")
        world.say(f"{hero.id} carried it back to the barn, and warm light poured out at once.")
    else:
        world.say(f"The pale ghost vanished like mist, but it had led {hero.id} straight to the answer.")
        world.say(f"{hero.id} ran back to the barn, and the farmer opened the way to light the lantern.")
    parent.meters["work"] += 1.0
    parent.memes["worry"] = 0.0
    hero.memes["fear"] = 0.0

    world.facts.update(hero=hero, parent=parent, quest=quest, target=target, ghost=ghost)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    return [
        f'Write a short ghost story for children about a farm quest involving "{q.goal}".',
        f"Tell a gentle eerie story where {hero.id} explores the farm at dusk and a ghost helps with {q.thing}.",
        f'Write a farm story with a haunted feeling, a small quest, and an ending where the barn becomes safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    parent = world.facts["parent"]
    qa = [
        QAItem(
            question=f"What quest did {hero.id} hear about on the farm?",
            answer=f"{hero.id} heard about a quest to {q.goal}. The clue was {q.clue}, and that is what sent the child out at dusk.",
        ),
        QAItem(
            question=f"Why did the farmer warn {hero.id}?",
            answer=f"The farmer warned {hero.id} because {q.danger}. The warning made the farm feel more spooky, but it also gave the story its tension.",
        ),
        QAItem(
            question=f"Where did {hero.id} finally find {q.thing}?",
            answer=f"{hero.id} found {q.thing} at the {q.location}. That is where the clue led after the shadowy search.",
        ),
    ]
    if ghost.is_friend:
        qa.append(QAItem(
            question=f"How did the ghost help {hero.id}?",
            answer=f"The ghost gave a soft clue and pointed the way instead of scaring {hero.id} away. That made the quest feel eerie, but kind.",
        ))
    else:
        qa.append(QAItem(
            question=f"Why did the ghost make the farm feel scary?",
            answer=f"The ghost drifted through the barn like mist, so {hero.id} felt a shiver of fear. Even so, the ghost still led the child toward the answer.",
        ))
    qa.append(QAItem(
        question=f"What changed at the end of the story?",
        answer=f"At the end, the missing thing was found and the farm felt safe again. The barn could have light, and the child's fear faded away.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    return [
        QAItem(
            question="What is a farm?",
            answer="A farm is a place where people grow crops and care for animals, often with barns, fields, and tools.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky, floating figure that can make a place feel mysterious or haunted.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. In stories, a quest usually means going somewhere, following clues, and solving a problem.",
        ),
        QAItem(
            question=f"Why might a lantern be useful on a farm at night?",
            answer="A lantern gives light in the dark, so you can see paths, doors, tools, and animals when the farm gets shadowy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} place={e.place} meters={e.meters} memes={e.memes}")
    if world.ghost is not None:
        lines.append(f"ghost: {world.ghost}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(quest(lantern_key)).
quest(quest(lost_lamb)).
quest(quest(silver_egg)).

ghost_mode(friend) :- friend_flag.
ghost_mode(tricky) :- not friend_flag.

valid_story(Q) :- quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_quests() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest/1."))
    return sorted(set(asp.atoms(model, "quest")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_quests())
    py_set = {(qid,) for qid in QUESTS}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches QUESTS ({len(clingo_set)} quests).")
        return 0
    print("MISMATCH between clingo and QUESTS:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


CURATED = [
    StoryParams(quest="lantern_key", name="Mina", trait="curious", ghost_friend=True),
    StoryParams(quest="lost_lamb", name="Leo", trait="brave", ghost_friend=False),
    StoryParams(quest="silver_egg", name="Nora", trait="careful", ghost_friend=True),
]


def build_quest_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show quest/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest/1."))
        print(sorted(set(asp.atoms(model, "quest"))))
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
