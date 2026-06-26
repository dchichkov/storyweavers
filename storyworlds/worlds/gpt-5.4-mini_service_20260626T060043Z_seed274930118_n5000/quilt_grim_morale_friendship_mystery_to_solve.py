#!/usr/bin/env python3
"""
A small nursery-rhyme-style story world about a quilt, a grim mood, and a mystery
that gets solved by friendship.

The world model tracks:
- physical meters: who has what, where the quilt is, what is missing, and how
  far the search has gone
- emotional memes: grimness, morale, care, worry, and delight

The premise is simple:
A child and a friend find a quilt that has lost a patch or ribbon. The room feels
grim. They look together, follow clues, and solve the mystery. The ending image
shows the quilt mended and morale lifted by friendship.
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
    with_: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage"
    cozy: bool = True
    clues: tuple[str, ...] = ("under the chair", "beside the hearth", "near the toy box")


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage": Setting(place="the cottage", cozy=True, clues=("under the chair", "beside the hearth", "near the toy box")),
    "attic": Setting(place="the attic", cozy=False, clues=("under the rafters", "behind the trunk", "by the dusty ladder")),
    "garden room": Setting(place="the garden room", cozy=True, clues=("on the bench", "under the window", "by the teacups")),
}

HEROES = {
    "lily": ("Lily", "girl", "bright"),
    "tom": ("Tom", "boy", "gentle"),
    "mabel": ("Mabel", "girl", "spry"),
    "ben": ("Ben", "boy", "cheery"),
}

FRIENDS = {
    "pip": ("Pip", "boy", "kind"),
    "rose": ("Rose", "girl", "kind"),
    "nina": ("Nina", "girl", "brave"),
    "oscar": ("Oscar", "boy", "steady"),
}

QUILT_NAMES = [
    "patchwork quilt",
    "little quilt",
    "starry quilt",
    "soft quilt",
]

MYSTERIES = [
    ("missing patch", "a bright patch had gone astray", "patch"),
    ("lost ribbon", "a ribbon was nowhere to be seen", "ribbon"),
    ("torn corner", "one corner had snagged", "thread"),
]

TRAITS = ["kind", "gentle", "cheery", "brave", "patient"]


@dataclass
class Mystery:
    kind: str
    description: str
    clue_item: str


@dataclass
class Quilt:
    label: str
    phrase: str
    mystery: Mystery


def make_quilt(rng: random.Random) -> Quilt:
    label = rng.choice(QUILT_NAMES)
    m = Mystery(*rng.choice(MYSTERIES))
    phrase = f"a {label} with a {m.kind}"
    return Quilt(label=label, phrase=phrase, mystery=m)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, quilt: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a {hero.memes.get('trait', 'kind')} heart, "
        f"and {friend.id} was {friend.memes.get('trait', 'kind')} too."
    )
    world.say(
        f"They loved the {quilt.label}, for it was {quilt.phrase}, snug and close as a song."
    )


def set_grim(world: World, hero: Entity, friend: Entity, quilt: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    quilt.meters["missing"] = 1
    hero.memes["morale"] -= 1
    friend.memes["morale"] -= 1
    world.say(
        f"One day the room felt grim, for {quilt.label} had a mystery: {quilt.mystery.description}."
    )
    world.say(
        f"{hero.id} looked low, and {friend.id} did too; their little voices went soft and small."
    )


def search_step(world: World, seeker: Entity, clue: str) -> None:
    seeker.meters["search"] = seeker.meters.get("search", 0) + 1
    seeker.memes["hope"] = seeker.memes.get("hope", 0) + 1
    world.say(f"{seeker.id} searched {clue}, with eyes like beads and feet like taps.")


def friendship_turn(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    hero.memes["morale"] += 1
    friend.memes["morale"] += 1
    world.say(
        f"Then friendship came softly in, and {hero.id} said, \"We can look together.\""
    )
    world.say(
        f"{friend.id} smiled back, and that smile was a small warm lantern in the dim."
    )


def solve_mystery(world: World, hero: Entity, friend: Entity, quilt: Entity, clue: str) -> None:
    quilt.meters["missing"] = 0
    quilt.meters["mended"] = 1
    hero.memes["morale"] += 2
    friend.memes["morale"] += 2
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At last they found the {quilt.mystery.clue_item} {clue}, tucked neat as a pea."
    )
    world.say(
        f"They fixed the {quilt.label} with careful hands, and the little mystery was set free."
    )


def ending(world: World, hero: Entity, friend: Entity, quilt: Entity) -> None:
    world.say(
        f"So the {quilt.label} lay smooth and bright, and the room was no longer grim."
    )
    world.say(
        f"{hero.id} and {friend.id} sat side by side, with high morale and happy trim."
    )


def tell(setting: Setting, hero_name: str, friend_name: str, rng: random.Random) -> World:
    world = World(setting)
    quilt = make_quilt(rng)

    hero_type = HEROES[hero_name][1]
    friend_type = FRIENDS[friend_name][1]

    hero = world.add(Entity(id=HEROES[hero_name][0], kind="character", type=hero_type))
    friend = world.add(Entity(id=FRIENDS[friend_name][0], kind="character", type=friend_type))
    q = world.add(Entity(id="quilt", kind="thing", type="quilt", label=quilt.label, phrase=quilt.phrase))

    hero.memes["trait"] = HEROES[hero_name][2]
    friend.memes["trait"] = FRIENDS[friend_name][2]
    hero.memes["morale"] = 1
    friend.memes["morale"] = 1
    q.place = setting.place

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["quilt"] = q
    world.facts["mystery"] = quilt.mystery
    world.facts["setting"] = setting

    introduce(world, hero, friend, q)
    world.para()
    set_grim(world, hero, friend, q)

    world.para()
    friendship_turn(world, hero, friend)
    for clue in setting.clues:
        search_step(world, hero, clue)
        search_step(world, friend, clue)
    solve_mystery(world, hero, friend, q, setting.clues[-1])

    world.para()
    ending(world, hero, friend, q)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    h = world.facts["hero"]
    f = world.facts["friend"]
    q = world.facts["quilt"]
    m = world.facts["mystery"]
    s = world.facts["setting"]
    return [
        f"Write a nursery-rhyme-style story about {h.id}, {f.id}, and a {q.label} in {s.place}.",
        f"Tell a gentle tale where friendship helps solve the mystery of {m.kind}.",
        f"Write a short story with a grim feeling that brightens when two friends fix a quilt.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    f = world.facts["friend"]
    q = world.facts["quilt"]
    m = world.facts["mystery"]
    s = world.facts["setting"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {h.id} and {f.id}, two little friends who worked together in {s.place}.",
        ),
        QAItem(
            question=f"What made the room feel grim at first?",
            answer=f"It felt grim because {q.label} had a mystery: {m.description}.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They searched together, found the {m.clue_item}, and mended the {q.label} with careful hands.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The {q.label} was smooth and bright again, and {h.id} and {f.id} ended with high morale.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quilt?",
            answer="A quilt is a warm blanket made from pieces of cloth sewn together.",
        ),
        QAItem(
            question="What does morale mean?",
            answer="Morale is how hopeful and cheerful someone feels inside.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care for each other, help each other, and stay kind together.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzle or problem that needs clues and careful thinking.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(cottage).
setting(attic).
setting(garden_room).

kind(quality).
kind(clue).

friendship(ally).

mystery_to_solve(missing_patch).
mystery_to_solve(lost_ribbon).
mystery_to_solve(torn_corner).

cozy(cottage).
cozy(garden_room).

good_story(S) :- setting(S), friendship(ally), mystery_to_solve(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        const = key.replace(" ", "_")
        lines.append(asp.fact("setting", const))
        if SETTINGS[key].cozy:
            lines.append(asp.fact("cozy", const))
    lines.append(asp.fact("friendship", "ally"))
    for _, kind, _ in MYSTERIES:
        lines.append(asp.fact("mystery_to_solve", kind.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {k.replace(" ", "_") for k, v in SETTINGS.items() if v.cozy}
    cl = {a[0] for a in asp_good_settings()}
    if py == cl:
        print(f"OK: clingo gate matches Python settings ({len(py)} cozy settings).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a quilt, grimness, morale, friendship, and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=HEROES.keys())
    ap.add_argument("--friend", choices=FRIENDS.keys())
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice(list(FRIENDS))
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(setting=setting, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = tell(SETTINGS[params.setting], params.hero, params.friend, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Good cozy settings:", ", ".join(k for k, v in SETTINGS.items() if v.cozy))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        combos = [
            StoryParams(setting=s, hero=h, friend=f)
            for s in SETTINGS
            for h in HEROES
            for f in FRIENDS
            if h != f
        ]
        samples = [generate(p) for p in combos]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
