#!/usr/bin/env python3
"""
A standalone story world for a tall-tale quest about friendship, reason, and a downward journey.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Quest:
    place: str
    goal: str
    reason: str
    downward: bool
    difficulty: str
    keyword: str = "reason"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    hero: str
    friend: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks = []
        current = []
        for line in self.lines:
            if line == "":
                if current:
                    chunks.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            chunks.append(" ".join(current))
        return "\n\n".join(chunks)


PLACES = {
    "hill": {
        "label": "the steep story-hill",
        "downward": True,
        "quirk": "its path curled like a ribbon down to the valley",
    },
    "well": {
        "label": "the whispering well",
        "downward": True,
        "quirk": "its stone steps slid down and down like a ladder to the dark water",
    },
    "canyon": {
        "label": "the red canyon",
        "downward": True,
        "quirk": "its trail dropped lower than a pocket watch on a runaway string",
    },
    "tower": {
        "label": "the clock tower",
        "downward": False,
        "quirk": "its stairway wound round and round instead of down",
    },
}

QUESTS = {
    "map": Quest(
        place="hill",
        goal="bring back the lost map",
        reason="the village gardener had no idea where the secret spring was",
        downward=True,
        difficulty="long",
        keyword="reason",
        tags={"quest", "reason", "downward", "friendship"},
    ),
    "bell": Quest(
        place="well",
        goal="find the silver bell",
        reason="the bell's ringing was said to wake the sleeping goose that guarded the orchard gate",
        downward=True,
        difficulty="deep",
        keyword="downward",
        tags={"quest", "reason", "downward", "friendship"},
    ),
    "key": Quest(
        place="canyon",
        goal="recover the gate key",
        reason="without it, the bakery wagon could not roll into town by morning",
        downward=True,
        difficulty="steep",
        keyword="reason",
        tags={"quest", "reason", "downward", "friendship"},
    ),
    "kite": Quest(
        place="tower",
        goal="rescue the gold kite",
        reason="a storm had lifted it up into the clock hands and the town children missed it terribly",
        downward=False,
        difficulty="high",
        keyword="reason",
        tags={"quest", "reason", "friendship"},
    ),
}

HEROES = [
    ("Mara", "girl", "quick"),
    ("Jeb", "boy", "kind"),
    ("Tilda", "girl", "brave"),
    ("Otis", "boy", "spry"),
    ("Nell", "girl", "clever"),
]
FRIENDS = [
    ("Bram", "boy"),
    ("Pip", "boy"),
    ("June", "girl"),
    ("Rose", "girl"),
    ("Finn", "boy"),
]


ASP_RULES = r"""
quest_ok(P,Q) :- place(P), quest(Q), needs_downward(Q), downward_place(P).
friendship_ok(H,F) :- hero(H), friend(F), allies(H,F).
valid_story(P,Q,H,F) :- quest_ok(P,Q), friendship_ok(H,F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p]["downward"]:
            lines.append(asp.fact("downward_place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        if QUESTS[q].downward:
            lines.append(asp.fact("needs_downward", q))
    for h, _, _ in HEROES:
        lines.append(asp.fact("hero", h))
    for f, _ in FRIENDS:
        lines.append(asp.fact("friend", f))
    for h, _, _ in HEROES:
        for f, _ in FRIENDS:
            if h[0] != f[0]:
                lines.append(asp.fact("allies", h, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(place_key: str, quest_key: str, hero_name: str, friend_name: str) -> World:
    q = QUESTS[quest_key]
    p = PLACES[place_key]
    world = World(setting=p["label"])
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mara", "Tilda", "Nell"} else "boy", traits=["tall-tale", "stubborn"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl" if friend_name in {"June", "Rose"} else "boy", traits=["loyal", "steady"]))
    hero.memes["courage"] = 1
    friend.memes["trust"] = 1
    world.facts.update(hero=hero, friend=friend, quest=q, place=p)

    world.say(f"Folks said {hero.name if hasattr(hero, 'name') else hero_name} was a {hero.traits[0]} sort who could stare a thundercloud in the eye and still ask it for directions.")
    world.say(f"That was the day {hero.id} and {friend.id} set out for {p['label']}, because {q.reason}.")
    world.para()
    world.say(f"The road went { 'downward' if q.downward else 'upward' } so sharply that even the crows seemed to slide on the air.")
    world.say(f"{p['quirk'].capitalize()}.")
    hero.meters["distance"] = 1
    friend.meters["distance"] = 1
    hero.memes["need"] = 1
    friend.memes["care"] = 1
    world.say(f"{hero.id} wanted the answer for {q.goal}, but {hero.id} also wanted to be wise about it, because a quick foot is good and a good reason is better.")
    world.say(f"{friend.id} said, 'If the path gets tricky, I will stay beside you.'")
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    world.para()
    world.say(f"Halfway there, the trail dipped into a hollow where the wind could snatch a hat clean off a head and call it a toy.")
    world.say(f"{hero.id} nearly rushed ahead, but {friend.id} reminded {hero.pronoun('object')} of the reason for the quest: {q.reason}.")
    world.say(f"That calmed the hurry right out of {hero.pronoun('possessive')} boots.")
    hero.memes["calm"] = 1
    hero.meters["downward"] = 1 if q.downward else 0
    friend.meters["downward"] = 1 if q.downward else 0
    world.para()
    world.say(f"At last they reached the place where the lost thing waited, and together they pulled, climbed, and tugged like two mice hauling a moonbeam.")
    world.say(f"They brought back the {q.goal.split()[-1]} and set it where it belonged.")
    world.say(f"The village cheered, and {hero.id} laughed so hard {hero.pronoun('possessive')} hat tilted sideways.")
    world.say(f"{friend.id} grinned, because the best part of a quest was not the cleverness alone, but the friend who walked the whole long way with you.")
    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        f"Write a tall-tale story about a friendship-powered quest where the road goes downward and someone needs a good reason to keep going.",
        f"Tell a child-friendly adventure about {world.facts['hero'].id} and {world.facts['friend'].id} traveling downward to {q.goal}.",
        f"Write a big-hearted story that includes the words reason and downward and ends with two friends finishing a quest together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    h = world.facts["hero"]
    f = world.facts["friend"]
    return [
        QAItem(
            question=f"Why did {h.id} and {f.id} go to {world.setting}?",
            answer=f"They went there because {q.reason}, and the quest depended on a good reason instead of a wild guess.",
        ),
        QAItem(
            question=f"What made the trip feel so big and strange?",
            answer=f"The path went downward so sharply, and the place itself felt tall-tale huge, like the world was leaning to listen.",
        ),
        QAItem(
            question=f"How did {f.id} help {h.id} on the quest?",
            answer=f"{f.id} stayed beside {h.id}, reminded {h.pronoun('object')} of the reason for the quest, and helped carry the lost thing home.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The missing {q.goal.split()[-1]} was returned, the town was happy, and the friends finished the quest together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something, fix something, or help someone.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and staying with them when things get hard.",
        ),
        QAItem(
            question="What does downward mean?",
            answer="Downward means going toward a lower place, like walking down a hill or into a valley.",
        ),
        QAItem(
            question="Why do people use reason?",
            answer="People use reason to think carefully before they act so they can make a good choice.",
        ),
    ]
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} type={e.type:5} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest storyworld about friendship, reason, and a downward journey.")
    ap.add_argument("--place", choices=PLACES)
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
    if args.quest:
        q = QUESTS[args.quest]
        if args.place and args.place != q.place:
            raise StoryError("That quest does not fit that place.")
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice([k for k, v in PLACES.items() if v["downward"]])
    if not PLACES[place]["downward"] and args.quest and QUESTS[args.quest].downward:
        raise StoryError("That quest needs a downward place.")
    quest = args.quest or rng.choice([k for k, q in QUESTS.items() if q.place == place or q.downward == PLACES[place]["downward"]])
    hero = args.hero or rng.choice([h for h, _, _ in HEROES])
    friend = args.friend or rng.choice([f for f, _ in FRIENDS if f != hero])
    return StoryParams(place=place, quest=quest, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.quest, params.hero, params.friend)
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


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set()
    for p, pdata in PLACES.items():
        if not pdata["downward"]:
            continue
        for q, qd in QUESTS.items():
            if qd.downward:
                for h, _, _ in HEROES:
                    for f, _ in FRIENDS:
                        python_set.add((p, q, h, f))
    asp_set = set(asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: ASP gate matches Python ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - python_set:
        print(" only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print(" only in Python:", sorted(python_set - asp_set))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hill", quest="map", hero="Mara", friend="Bram"),
            StoryParams(place="well", quest="bell", hero="Jeb", friend="June"),
            StoryParams(place="canyon", quest="key", hero="Nell", friend="Finn"),
            StoryParams(place="tower", quest="kite", hero="Tilda", friend="Rose"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
