#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/anticipate_handsome_friend_s_backyard_quest_humor.py
=====================================================================================================

A tiny fairy-tale story world about a child, a handsome friend, and a backyard
quest with humor and suspense.

The seed premise:
- A child eagerly anticipates a visit to a handsome friend.
- The friend's backyard hides a quest object.
- A little misunderstanding adds suspense.
- A humorous turn reveals the object was near the picnic bench all along.

The world model keeps track of:
- physical meters: search progress, tidy/messy, hidden/revealed, worry, delight
- emotional memes: anticipation, pride, suspense, humor, relief, friendship

The story is rendered from live state changes, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "mom", "sister"}
        male = {"boy", "prince", "king", "father", "dad", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "a friend's backyard"
    weather: str = "sunny"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    object_label: str
    object_phrase: str
    clue: str
    misread: str
    reveal: str
    hiding_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Friend:
    name: str
    type: str
    label: str
    handsome: bool = True
    trait: str = "bright"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    quest: str
    seed: Optional[int] = None


SETTINGS = {
    "backyard": Setting(place="a friend's backyard", weather="sunny", affords={"quest"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="find the silver lantern",
        object_label="lantern",
        object_phrase="a tiny silver lantern",
        clue="a ribbon tied to the rose bush",
        misread="the ribbon looked like a worm from far away",
        reveal="the lantern had been resting beside the picnic bench",
        hiding_spot="beside the picnic bench",
        tags={"light", "quest", "humor", "suspense"},
    ),
    "crown": Quest(
        id="crown",
        goal="find the toy crown",
        object_label="crown",
        object_phrase="a toy crown with blue stones",
        clue="a sparkle near the watering can",
        misread="the sparkle winked like a dragon eye for one silly moment",
        reveal="the crown had slipped behind the watering can",
        hiding_spot="behind the watering can",
        tags={"crown", "quest", "humor", "suspense"},
    ),
    "key": Quest(
        id="key",
        goal="find the brass key",
        object_label="key",
        object_phrase="a brass key with a heart-shaped handle",
        clue="a little patch of dirt shaped like a bootprint",
        misread="the bootprint looked like a giant mouse had tiptoed there",
        reveal="the key was tucked under the garden glove",
        hiding_spot="under the garden glove",
        tags={"key", "quest", "humor", "suspense"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Lily", "Ava", "Esme", "Iris", "Mina"]
BOY_NAMES = ["Theo", "Nico", "Eli", "Owen", "Finn", "Jasper", "Levi", "Hugo"]
TRAITS = ["curious", "cheerful", "brave", "gentle", "sprightly", "thoughtful"]


def sibling_pronoun(kind: str) -> str:
    return "her" if kind == "girl" else "his" if kind == "boy" else "their"


def valid_combos() -> list[tuple[str, str]]:
    return [("backyard", qid) for qid in QUESTS]


def quest_at_risk(quest: Quest) -> bool:
    return True


ASP_RULES = r"""
quest_goal(Q) :- quest(Q).
at_risk(Q) :- quest_goal(Q).
compatible(backyard, Q) :- quest(Q), at_risk(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.weather:
            lines.append(asp.fact("weather", place, setting.weather))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale backyard quest with humor and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place and args.place != "backyard":
        raise StoryError("This world only supports a friend's backyard.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    quest = args.quest or rng.choice(list(QUESTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        quest=quest,
    )


def _do_search(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    hero.memes["anticipation"] = hero.memes.get("anticipation", 0.0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    if narrate:
        world.say(
            f"{hero.id} looked here and there, expecting the next clue to sparkle."
        )


def _misread_clue(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.say(
        f"Then {hero.id} saw {quest.clue}, but {quest.misread}; for a breath, the yard felt full of mystery."
    )


def _reveal(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0.0) + 1
    quest_ent = world.get("quest")
    quest_ent.hidden = False
    quest_ent.location = quest.hiding_spot
    world.say(
        f"At last, {quest.reveal}, and everyone laughed because the treasure had been near all along."
    )
    world.say(
        f"{hero.id} and {friend.id} shared a grin, and the little quest was done."
    )


def tell(setting: Setting, quest: Quest, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name))
    qent = world.add(Entity(
        id="quest",
        kind="thing",
        type="thing",
        label=quest.object_label,
        phrase=quest.object_phrase,
        hidden=True,
        location="somewhere in the backyard",
    ))

    hero.memes["anticipation"] = 1
    friend.memes["pride"] = 1

    world.say(
        f"Once in a {setting.place}, {hero.id} grew more and more eager to visit {friend.id}, a handsome friend with a bright smile."
    )
    world.say(
        f"{hero.id} came with a small heart full of hope, because today there would be a quest."
    )
    world.para()
    world.say(
        f"In the sunny backyard, the two friends bowed to the beans and roses, and began to {quest.goal}."
    )
    _do_search(world, hero, quest)
    _misread_clue(world, hero, quest)
    world.say(
        f"The clue seemed almost secret, and for a tiny moment even the birds sounded as if they were whispering."
    )
    world.para()
    _do_search(world, hero, quest)
    _reveal(world, hero, friend, quest)

    world.facts.update(
        hero=hero,
        friend=friend,
        quest=quest,
        quest_ent=qent,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    return [
        f"Write a fairy tale about {hero.id} who anticipates a visit to a handsome friend in a backyard and goes on a quest.",
        f"Tell a humorous story with suspense where {hero.id} and {friend.id} search for {quest.object_phrase} in a friend's backyard.",
        f"Write a gentle fairy tale scene where the clue is confusing at first, then the hidden treasure is found with laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    qa = [
        QAItem(
            question=f"Who was {hero.id} excited to visit?",
            answer=f"{hero.id} was excited to visit {friend.id}, a handsome friend in a friend's backyard.",
        ),
        QAItem(
            question=f"What was the quest looking for?",
            answer=f"The quest was looking for {quest.object_phrase}.",
        ),
        QAItem(
            question=f"Why did the yard feel suspenseful for a little while?",
            answer=f"It felt suspenseful because the clue was hard to read at first, so {hero.id} had to keep searching.",
        ),
        QAItem(
            question=f"What made the story funny too?",
            answer=f"The clue was misread in a silly way, and then the treasure was found close by, which made everyone laugh.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} laughing after the hidden treasure was revealed.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    out = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like a treasure, a friend, or a lost object.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny and makes people smile or laugh.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
    ]
    if "light" in q.tags:
        out.append(QAItem(
            question="What is a lantern used for?",
            answer="A lantern gives light, so people can see in the dark or in shadowy places.",
        ))
    if "crown" in q.tags:
        out.append(QAItem(
            question="What is a crown?",
            answer="A crown is a special headpiece, often worn by a king, queen, or in a game of pretend.",
        ))
    if "key" in q.tags:
        out.append(QAItem(
            question="What does a key do?",
            answer="A key can open a lock when it fits the right shape.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero_name="Mina", hero_type="girl", friend_name="Hugo", friend_type="boy", quest="lantern"),
    StoryParams(hero_name="Theo", hero_type="boy", friend_name="Lina", friend_type="girl", quest="crown"),
    StoryParams(hero_name="Iris", hero_type="girl", friend_name="Owen", friend_type="boy", quest="key"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS["backyard"],
        QUESTS[params.quest],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
    )
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

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, quest in combos:
            print(f"  {place:10} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.quest} in the backyard"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
