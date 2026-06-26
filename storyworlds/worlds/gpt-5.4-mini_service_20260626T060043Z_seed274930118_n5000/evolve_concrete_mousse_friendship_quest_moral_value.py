#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/evolve_concrete_mousse_friendship_quest_moral_value.py
==============================================================================================================================

A tiny nursery-rhyme storyworld about friendship, a quest, and moral value.

Seed tale imagined from the prompt:
---
On a bright little lane of concrete, Pip the mouse found a bowl of mousse
that was meant for the village feast. Pip and his friend Dot the sparrow
wanted to carry it to the hilltop basket. But the path had a crack, the wind
was wiggly, and the mousse could wobble and spill. Pip wanted to rush, Dot
wanted to help, and both learned that kindness and patience make a better
quest than speed.
---

World model:
- concrete path, a mousse bowl, two friends, and a small quest
- physical meters: distance, balance, wobble, spill, repair, carried
- emotional memes: friendship, worry, patience, pride, help, moral value

The story is generated from state changes, not a frozen template: a quest
creates tension, a small mistake raises wobble, friends choose a gentle repair,
and the ending proves what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "sparrow"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the concrete lane"
    affords: set[str] = field(default_factory=lambda: {"quest", "carry", "repair"})


@dataclass
class Quest:
    id: str
    verb: str
    noun: str
    goal: str
    risk: str
    moral: str
    topic: str = "friendship"


@dataclass
class Bowl:
    label: str
    phrase: str
    fragility: str
    region: str = "hands"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    quest: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


QUESTS = {
    "mousse": Quest(
        id="mousse",
        verb="carry the mousse",
        noun="mousse",
        goal="bring the bowl to the feast basket",
        risk="the mousse may wobble and spill on the concrete",
        moral="kindness and patience help friends finish a quest",
        topic="friendship",
    ),
}

SETTINGS = {
    "lane": Setting(place="the concrete lane"),
    "courtyard": Setting(place="the concrete courtyard"),
    "path": Setting(place="the concrete path"),
}

HEROES = [
    ("Pip", "mouse", "little mouse"),
    ("Mina", "girl", "little girl"),
    ("Toby", "boy", "little boy"),
]

FRIENDS = [
    ("Dot", "sparrow", "bright sparrow"),
    ("Nell", "girl", "kind friend"),
    ("Bram", "boy", "steady friend"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world about friendship, a quest, and moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or "mousse"
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    friend = args.friend or rng.choice([f[0] for f in FRIENDS])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(place=place, quest=quest, hero=hero, friend=friend)


def _hero_entity(name: str) -> Entity:
    for hname, htype, label in HEROES:
        if hname == name:
            return Entity(id=hname, kind="character", type=htype, label=label)
    return Entity(id=name, kind="character", type="mouse", label="little mouse")


def _friend_entity(name: str) -> Entity:
    for fname, ftype, label in FRIENDS:
        if fname == name:
            return Entity(id=fname, kind="character", type=ftype, label=label)
    return Entity(id=name, kind="character", type="sparrow", label="bright friend")


def introduce(world: World, hero: Entity, friend: Entity, quest: Quest, bowl: Entity) -> None:
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    world.say(
        f"{hero.id} was a {hero.label} who loved a small rhyme and a good deed."
    )
    world.say(
        f"{friend.id} was a {friend.label} who liked to help, and together they heard of a quest."
    )
    world.say(
        f"They must carry the {bowl.label} to the feast, for the little lane was waiting."
    )


def begin_quest(world: World, hero: Entity, friend: Entity, quest: Quest, bowl: Entity) -> None:
    hero.memes["want"] = 1
    friend.memes["want"] = 1
    world.say(
        f"On {world.setting.place}, {hero.id} said, \"Come along now; let us {quest.verb}.\""
    )
    world.say(
        f"{friend.id} nodded, for the {quest.noun} gleamed like a moon-white spoon."
    )


def worry(world: World, hero: Entity, friend: Entity, bowl: Entity, quest: Quest) -> None:
    hero.memes["worry"] = 1
    friend.memes["worry"] = 1
    bowl.meters["balance"] = 1
    bowl.meters["wobble"] = 1
    world.say(
        f"But the bowl was a wobbly thing, and the concrete path had a cracky edge."
    )
    world.say(
        f"{hero.id} hurried a bit too much, and the mousse trembled in a little white hill."
    )


def test_spill(world: World, bowl: Entity) -> None:
    if bowl.meters.get("wobble", 0) >= THRESHOLD:
        bowl.meters["spill"] = 1
        world.say(
            f"A tiny dab of mousse slid near the rim, and both friends stopped at once."
        )


def repair_and_help(world: World, hero: Entity, friend: Entity, bowl: Entity) -> None:
    hero.memes["patience"] = 1
    friend.memes["help"] = 1
    bowl.meters["spill"] = 0
    bowl.meters["carried"] = 1
    hero.meters["care"] = 1
    friend.meters["care"] = 1
    world.say(
        f"{friend.id} said, \"Slow paws, soft steps,\" and {hero.id} listened."
    )
    world.say(
        f"They steadied the bowl together, wiped the rim, and walked like a gentle rhyme."
    )


def resolution(world: World, hero: Entity, friend: Entity, quest: Quest, bowl: Entity) -> None:
    hero.memes["moral_value"] = 1
    friend.memes["moral_value"] = 1
    world.say(
        f"At last the {quest.noun} reached the feast basket, safe and bright."
    )
    world.say(
        f"{hero.id} smiled at {friend.id}, for a kind heart had made the quest go right."
    )
    world.say(
        f"And that was the moral value of the tale: friends who help each other carry more than mousse."
    )


def tell(setting: Setting, quest: Quest, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(_hero_entity(hero_name))
    friend = world.add(_friend_entity(friend_name))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="bowl",
        label="bowl of mousse",
        phrase="a bowl of mousse",
        owner=hero.id,
        meters={"balance": 1},
    ))

    world.facts.update(hero=hero, friend=friend, bowl=bowl, quest=quest, setting=setting)

    introduce(world, hero, friend, quest, bowl)
    world.para()
    begin_quest(world, hero, friend, quest, bowl)
    worry(world, hero, friend, bowl, quest)
    test_spill(world, bowl)
    world.para()
    repair_and_help(world, hero, friend, bowl)
    resolution(world, hero, friend, quest, bowl)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        f'Write a nursery-rhyme style story about {q.noun}, friendship, and a small quest on concrete.',
        f"Tell a gentle story where two friends try to {q.verb} without spilling the mousse.",
        f"Write a child-friendly rhyme about patience, help, and a bowl of mousse on a concrete path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    quest: Quest = f["quest"]
    bowl: Entity = f["bowl"]
    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} trying to do?",
            answer=f"They were trying to {quest.verb} and bring the {bowl.label} to the feast basket.",
        ),
        QAItem(
            question=f"Why did the friends slow down on {world.setting.place}?",
            answer="They slowed down because the mousse was wobbling, and the concrete path had a crack that made the bowl shaky.",
        ),
        QAItem(
            question=f"What helped the quest succeed in the end?",
            answer=f"Patience and friendship helped. {friend.id} reminded {hero.id} to take soft steps, and they carried the bowl together.",
        ),
        QAItem(
            question="What moral value did the story teach?",
            answer=f"It taught that {quest.moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is concrete?",
            answer="Concrete is a hard material used for paths, roads, and floors.",
        ),
        QAItem(
            question="What is mousse?",
            answer="Mousse is a soft, fluffy food that can wobble if it is carried carelessly.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, helping each other, and caring about what your friend feels.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(herb).
friend(friendy).
quest(moussequest).
moral_value(friendship).
setting(concrete_lane).
supports(concrete_lane, quest).
supports(concrete_lane, carry).
supports(concrete_lane, repair).

good_story(P) :- setting(P), supports(P, quest), supports(P, carry), supports(P, repair).
compatible(Setting, Quest, Moral) :- setting(Setting), quest(Quest), moral_value(Moral), good_story(Setting).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", sid) for sid in SETTINGS
        ]
        + [asp.fact("quest", qid) for qid in QUESTS]
        + [asp.fact("moral_value", "friendship")]
        + [asp.fact("supports", sid, "quest") for sid in SETTINGS]
        + [asp.fact("supports", sid, "carry") for sid in SETTINGS]
        + [asp.fact("supports", sid, "repair") for sid in SETTINGS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {(p,) for p in SETTINGS}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: ASP parity matches Python gate ({len(cl)} settings).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params.hero, params.friend)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(place=pid, quest="mousse", hero="Pip", friend="Dot")
            for pid in SETTINGS
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
