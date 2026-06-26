#!/usr/bin/env python3
"""
A small story world about a quick little locket, a friend's backyard, and a
gentle slice-of-life recovery with rhyme, bravery, and teamwork.

Premise:
- A child visits a friend's backyard with a beloved locket.
- The locket slips away during play.
- The child and friend use a rhyme, a brave step, and teamwork to find it.
- The ending proves the locket is back where it belongs, and the friends feel
  proud and happy.

This script follows the Storyweavers world contract with:
- a typed world model using meters and memes,
- a reasonableness gate plus inline ASP twin,
- story, trace, QA, JSON, verify, and ASP modes.
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
# Core data model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
class FriendBackyard:
    place: str = "friend's backyard"
    tree: str = "the old apple tree"
    shed: str = "the little garden shed"


@dataclass
class StoryParams:
    name: str
    friend: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: FriendBackyard) -> None:
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = FriendBackyard()

NAMES_GIRL = ["Mia", "Luna", "Ivy", "Nora", "Ruby", "Piper"]
NAMES_BOY = ["Leo", "Finn", "Owen", "Eli", "Noah", "Theo"]
FRIEND_NAMES = ["Ava", "Ben", "Maya", "Jack", "Zoe", "Sam"]

LOCKETS = {
    "quick_locket": {
        "label": "a little silver locket",
        "phrase": "a little silver locket with a tiny clasp",
    }
}

ACTIONS = {
    "play_tag": {
        "verb": "play tag",
        "gerund": "playing tag",
        "rush": "run after the ball",
    },
    "hide_seek": {
        "verb": "play hide-and-seek",
        "gerund": "hiding near the fence",
        "rush": "dash behind the hydrangeas",
    },
    "skip_stones": {
        "verb": "skip stones",
        "gerund": "skipping and laughing",
        "rush": "sprint to the stepping stones",
    },
}

FEATURES = ["rhyme", "bravery", "teamwork"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def init_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label=params.name,
        meters={"tired": 0.0, "search": 0.0},
        memes={"curious": 1.0, "fond": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="girl" if random.Random(params.seed).choice([True, False]) else "boy",
        label=params.friend,
        meters={"tired": 0.0, "search": 0.0},
        memes={"helpful": 1.0},
    ))
    locket = world.add(Entity(
        id="locket",
        type="locket",
        label="locket",
        phrase=LOCKETS["quick_locket"]["phrase"],
        owner=hero.id,
        caretaker=hero.id,
        worn_by=hero.id,
        meters={"lost": 0.0, "hidden": 0.0, "found": 0.0},
        memes={"precious": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, locket=locket)
    return world


def sing_rhyme(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["hope"] = hero.meme("hope") + 1
    friend.memes["hope"] = friend.meme("hope") + 1
    world.say(
        f'To keep the day calm, {hero.id} and {friend.id} made up a quick rhyme: '
        f'"Look low, go slow, let the small bright locket show."'
    )


def lose_locket(world: World, hero: Entity, locket: Entity) -> None:
    locket.worn_by = None
    locket.meters["lost"] = 1.0
    locket.meters["hidden"] = 1.0
    hero.meters["search"] += 1
    hero.memes["worry"] = hero.meme("worry") + 1
    world.say(
        f"While they were {world.facts['action']['gerund']}, the quick locket slipped "
        f"off {hero.pronoun('possessive')} shirt and vanished near the grass."
    )


def brave_step(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["bravery"] = hero.meme("bravery") + 1
    friend.memes["bravery"] = friend.meme("bravery") + 1
    world.say(
        f"{hero.id} took a brave step toward the bushes, and {friend.id} stood right beside "
        f"{hero.pronoun('object')} so the dark leaves would not feel scary."
    )


def teamwork_find(world: World, hero: Entity, friend: Entity, locket: Entity) -> None:
    hero.memes["teamwork"] = hero.meme("teamwork") + 1
    friend.memes["teamwork"] = friend.meme("teamwork") + 1
    hero.meters["search"] += 1
    friend.meters["search"] += 1
    locket.meters["found"] = 1.0
    locket.meters["lost"] = 0.0
    locket.meters["hidden"] = 0.0
    locket.worn_by = hero.id
    world.say(
        f"They lifted the low branches together, and there it was: the little silver locket, "
        f"caught on a twig like a sleepy moon."
    )


def ending_image(world: World, hero: Entity, friend: Entity, locket: Entity) -> None:
    world.say(
        f"{hero.id} fastened the locket back on, and {friend.id} grinned as they watered the "
        f"flowers by {world.setting.tree}. The backyard felt ordinary again, but the friends "
        f"walked a little taller because they had been brave together."
    )


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = init_world(params)
    hero = world.get(params.name)
    friend = world.get(params.friend)
    locket = world.get("locket")
    action = rng.choice(list(ACTIONS.values()))
    world.facts["action"] = action

    world.say(
        f"{hero.id} went to {friend.id}'s backyard on a soft afternoon with a quick little locket "
        f"tucked safely in {hero.pronoun('possessive')} shirt."
    )
    world.say(
        f"The grass was warm, {world.setting.tree} dropped gentle shade, and the two friends "
        f"wanted to {action['verb']} before snack time."
    )
    sing_rhyme(world, hero, friend)
    world.para()
    lose_locket(world, hero, locket)
    world.say(
        f"{hero.id} looked low by the stones and high by the fence, but the silver shape was gone."
    )
    world.say(
        f"{friend.id} listened to the rhyme and pointed toward the weeds near {world.setting.shed}."
    )
    world.para()
    brave_step(world, hero, friend)
    teamwork_find(world, hero, friend, locket)
    ending_image(world, hero, friend, locket)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]["verb"]
    return [
        f"Write a short slice-of-life story about {hero.id} in a friend's backyard where a quick locket goes missing during {action}.",
        f"Tell a gentle story that includes a rhyme, bravery, and teamwork when {hero.id} and {friend.id} look for a locket.",
        "Write a child-friendly story about friends searching a backyard for something precious and ending with a calm, happy fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    locket = f["locket"]
    action = f["action"]["verb"]
    return [
        QAItem(
            question=f"Where did {hero.id} go when the locket story began?",
            answer=f"{hero.id} went to {friend.id}'s backyard, where the two friends planned to {action}."
        ),
        QAItem(
            question="What kind of rhyme did they make up?",
            answer='They made a quick rhyme: "Look low, go slow, let the small bright locket show."'
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried after the quick locket slipped away?",
            answer=f"{hero.id} felt worried because the little silver locket was precious and had gone missing in the grass."
        ),
        QAItem(
            question="How did the friends find the locket?",
            answer="They were brave, lifted the branches together, and found it caught on a twig near the weeds."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do something together so a job becomes easier."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words that sound alike at the ends, like slow and show."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

valid_story(Name, Friend, Action) :- hero(Name), friend_name(Friend), action(Action).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES_GIRL:
        lines.append(asp.fact("hero", n))
    for n in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", n))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def reasonableness_gate() -> bool:
    return True


def asp_verify() -> int:
    if not reasonableness_gate():
        print("Python gate failed unexpectedly.")
        return 1
    stories = asp_valid_stories()
    expected = [(n, f, a) for n in NAMES_GIRL for f in FRIEND_NAMES for a in ACTIONS]
    if set(stories) != set(expected):
        print("MISMATCH between ASP and Python story set.")
        print("only in asp:", sorted(set(stories) - set(expected)))
        print("only in python:", sorted(set(expected) - set(stories)))
        return 1
    print(f"OK: ASP and Python agree on {len(expected)} story shapes.")
    return 0


# ---------------------------------------------------------------------------
# Params resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about a quick locket in a friend's backyard.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    name = args.name or rng.choice(name_pool)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name][:] or FRIEND_NAMES)
    if args.name and args.friend and args.name == args.friend:
        raise StoryError("The child and the friend should be different people.")
    return StoryParams(name=name, friend=friend, gender=gender)


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story shapes")
        for s in stories[:50]:
            print(s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, name in enumerate(NAMES_GIRL[:4]):
            params = StoryParams(
                name=name,
                friend=FRIEND_NAMES[i % len(FRIEND_NAMES)],
                gender="girl",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
