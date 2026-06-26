#!/usr/bin/env python3
"""
A storyworld about a tiny nursery-rhyme protest, a shining shard, and a
friendship puzzle that feels a little suspenseful and a little magical.

Premise:
- A small group of childlike characters want to hold a gentle protest.
- They discover a magic shard that can show who needs a friend.
- One friend must calculate a safe, fair way to share the shard's glow.

The story always moves through:
setup -> tension -> calculation/choice -> friendship resolution
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
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    role: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    broken: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.role in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    shard: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registry: setting, characters, shard types
# ---------------------------------------------------------------------------

SETTINGS = {
    "green": Setting(place="the green", outdoors=True, affords={"protest", "magic", "calculate"}),
    "square": Setting(place="the old square", outdoors=True, affords={"protest", "magic", "calculate"}),
    "nursery": Setting(place="the nursery room", outdoors=False, affords={"protest", "magic", "calculate"}),
}

HEROES = [
    ("Pippa", "girl"),
    ("Toby", "boy"),
    ("Mina", "girl"),
    ("Ned", "boy"),
]

FRIENDS = [
    ("Luna", "girl"),
    ("Robin", "child"),
    ("Milo", "boy"),
    ("Sage", "child"),
]

SHARDS = {
    "glass": "a bright glass shard",
    "rainbow": "a rainbow shard",
    "moon": "a moonlit shard",
}


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is compatible if the place supports all three core actions.
valid_story(P,H,F,S) :- place(P), hero(H), friend(F), shard(S),
                       affords(P, protest), affords(P, magic), affords(P, calculate).

% The shard is safe if it is a shard and not broken.
safe_shard(S) :- shard(S), not broken(S).

% Friendship resolves suspense when the hero and friend share the glow fairly.
resolved(H,F,S) :- valid_story(_,H,F,S), safe_shard(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, s in SETTINGS.items():
        lines.append(asp.fact("place", key))
        if s.outdoors:
            lines.append(asp.fact("outdoors", key))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", key, a))
    for hid, role in HEROES:
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("role", hid, role))
    for fid, role in FRIENDS:
        lines.append(asp.fact("friend", fid))
        lines.append(asp.fact("role", fid, role))
    for sid in SHARDS:
        lines.append(asp.fact("shard", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate.")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero, _ in HEROES:
            for friend, _ in FRIENDS:
                for shard in SHARDS:
                    combos.append((place, hero, friend, shard))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    friend = args.friend or rng.choice([f for f, _ in FRIENDS if f != hero])
    shard = args.shard or rng.choice(list(SHARDS))
    return StoryParams(place=place, hero=hero, friend=friend, shard=shard)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    w = World(setting)
    hero_role = dict(HEROES)[params.hero]
    friend_role = dict(FRIENDS)[params.friend]

    hero = w.add(Entity(id=params.hero, kind="character", role=hero_role))
    friend = w.add(Entity(id=params.friend, kind="character", role=friend_role))
    shard = w.add(Entity(
        id=params.shard,
        kind="thing",
        label=SHARDS[params.shard],
        protective=True,
    ))

    w.facts.update(hero=hero, friend=friend, shard=shard)
    return w


def calculate_plan(world: World, hero: Entity, friend: Entity, shard: Entity) -> int:
    """A tiny in-world calculation: how many children can share the glow fairly."""
    base = 2
    if world.setting.outdoors:
        base += 1
    if shard.id == "rainbow":
        base += 1
    if hero.role == "child" or friend.role == "child":
        base += 1
    return base


def tell(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    shard = world.facts["shard"]

    world.say(
        f"On {world.setting.place}, {hero.id} stood up with a tiny protest sign and a brave little frown."
    )
    world.say(
        f"{hero.id} did not want a loud fuss; {hero.pronoun('subject')} only wanted the rules to be fair."
    )
    world.say(
        f"Then {friend.id} found {shard.label}, and it shone like a sleepy star in a pocket."
    )

    world.para()
    world.say(
        f"The little light made the air feel hushed, and everyone paused with a bit of suspense."
    )
    world.say(
        f"{hero.id} wondered if the shard would crack, or if it would help the protest turn kind."
    )

    count = calculate_plan(world, hero, friend, shard)
    world.say(
        f"So {hero.id} began to calculate: if {count} friends shared the glow, nobody would be left alone."
    )
    world.say(
        f"{friend.id} nodded, and together they counted by twos and then by smiles."
    )

    world.para()
    world.say(
        f"In the end, {hero.id} let {friend.id} hold the shard high, and the protest became a friendship parade."
    )
    world.say(
        f"The bright magic did not break anything at all; it only made a soft path of light for every child to follow."
    )
    world.say(
        f"And so the nursery rhyme ended with a cheer: fair is fair, and friends should care."
    )

    world.facts["calculated"] = count
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short nursery-rhyme story about a protest on {world.setting.place}, a magic shard, and a careful calculation.",
        f"Tell a gentle story where {world.facts['hero'].id} and {world.facts['friend'].id} discover {world.facts['shard'].label} during a protest.",
        "Write a suspenseful but friendly children's rhyme that ends with friendship and fairness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    shard = world.facts["shard"]
    count = world.facts["calculated"]
    return [
        QAItem(
            question=f"What did {hero.id} want to be fair about on {world.setting.place}?",
            answer=f"{hero.id} wanted the protest to be fair, not loud or mean. {hero.pronoun('subject').capitalize()} wanted everyone to listen and share kindly."
        ),
        QAItem(
            question=f"What did {friend.id} find during the story?",
            answer=f"{friend.id} found {shard.label}. It shone like a small magic star and made the scene feel suspenseful for a moment."
        ),
        QAItem(
            question=f"What did {hero.id} calculate before the ending?",
            answer=f"{hero.id} calculated that {count} friends could share the glow fairly. That helped turn the protest into a friendly, peaceful parade."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a protest?",
            answer="A protest is when people gather to show they want something to change, usually by speaking up together."
        ),
        QAItem(
            question="What is a shard?",
            answer="A shard is a small broken piece of something hard, like glass or stone."
        ),
        QAItem(
            question="What does calculate mean?",
            answer="To calculate means to work out an answer by counting, adding, or thinking carefully about numbers."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising and impossible in real life, like a light that shines because of a special charm."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind}, role={e.role}, label={e.label}")
    lines.append(f"calculated={world.facts.get('calculated')}")
    lines.append(f"resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme protest world with a magic shard and suspense.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(h for h, _ in HEROES))
    ap.add_argument("--friend", choices=sorted(f for f, _ in FRIENDS))
    ap.add_argument("--shard", choices=sorted(SHARDS))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="green", hero="Pippa", friend="Luna", shard="glass"),
            StoryParams(place="square", hero="Toby", friend="Robin", shard="moon"),
            StoryParams(place="nursery", hero="Mina", friend="Sage", shard="rainbow"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50:
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
