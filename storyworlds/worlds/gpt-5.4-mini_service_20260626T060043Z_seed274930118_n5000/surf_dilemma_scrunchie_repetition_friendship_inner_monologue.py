#!/usr/bin/env python3
"""
storyworlds/worlds/surf_dilemma_scrunchie_repetition_friendship_inner_monologue.py
=================================================================================

A tall-tale storyworld about a seaside day, a thorny little dilemma, a scrunchie,
and the kind of friendship that can turn a wobble into a wave.

Premise:
- A child loves surfing on a windy, bright beach.
- A favorite scrunchie keeps hair tidy, but it can slip off in the surf.
- A friend wants to surf together, while the hero must choose between vanity,
  safety, and loyalty.
- Repetition and inner monologue shape the rhythm of the tale: a repeated
  refrain, a repeated worry, and a repeated kind thought.

The story model tracks:
- physical meters: wind, wet, salt, tide, grip, distance
- emotional memes: excitement, worry, pride, loyalty, friendship, shame, relief

The resolution is always a plausible compromise:
- the hero secures the scrunchie, remembers the friend, and rides the wave.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Beach:
    place: str = "the beach"
    wind: str = "windy"
    tide: str = "high"
    surfable: bool = True


@dataclass
class Scrunchie:
    label: str = "scrunchie"
    phrase: str = "a bright red scrunchie"
    color: str = "red"
    keeps_hair_tidy: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    friend_name: str
    place: str = "beach"
    seed: Optional[int] = None


class World:
    def __init__(self, beach: Beach) -> None:
        self.beach = beach
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.refrain_count: int = 0

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


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def _inner_monologue(hero: Entity, scrunchie: Entity) -> str:
    return (
        f"{hero.pronoun().capitalize()} looked at the surf and thought, "
        f'"My {scrunchie.label} is lucky, but the sea is mighty. '
        f'If I lose it, will I still feel like me?"'
    )


def _refrain(world: World, hero: Entity, scrunchie: Entity) -> str:
    world.refrain_count += 1
    if world.refrain_count == 1:
        return f"{hero.id} kept whispering, \"Hold tight, little {scrunchie.label}, hold tight.\""
    if world.refrain_count == 2:
        return f"Again {hero.id} whispered, \"Hold tight, little {scrunchie.label}, hold tight.\""
    return f"Once more, {hero.id} whispered, \"Hold tight, little {scrunchie.label}, hold tight.\""


def _tall_tale_setup(world: World, hero: Entity, friend: Entity, scrunchie: Entity) -> None:
    world.say(
        f"{hero.id} was a brave little surfer who could spot a wave the way a crow spots corn."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the beach, loved the salt wind, and loved "
        f"{hero.pronoun('possessive')} {scrunchie.label} because it kept {hero.pronoun('possessive')} hair "
        f"from flying like a banner in a storm."
    )
    world.say(
        f"{friend.id} loved surfing too, and the two of them were friends so close they could share a shadow."
    )
    world.say(_inner_monologue(hero, scrunchie))
    world.say(_refrain(world, hero, scrunchie))


def _dilemma(world: World, hero: Entity, friend: Entity, scrunchie: Entity) -> None:
    hero.memes["worry"] = hero.meme("worry") + 1
    hero.memes["pride"] = hero.meme("pride") + 1
    hero.memes["friendship"] = hero.meme("friendship") + 1
    world.para()
    world.say(
        f"Then a dilemma blew in with the wind: {hero.id} wanted to surf at once, "
        f"but {hero.pronoun('possessive')} {scrunchie.label} might fly off in the waves."
    )
    world.say(
        f"{friend.id} called, \"The wave is waiting!\" and {hero.id} felt the whole sky pull one way "
        f"and the whole heart pull another."
    )
    world.say(
        f"{hero.pronoun().capitalize()} thought, \"If I go now, I may lose my {scrunchie.label}; "
        f"if I wait too long, the wave may be gone.\""
    )


def _compromise(world: World, hero: Entity, friend: Entity, scrunchie: Entity) -> None:
    world.para()
    hero.memes["relief"] = hero.meme("relief") + 1
    hero.memes["friendship"] = hero.meme("friendship") + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"At last {hero.id} tucked the {scrunchie.label} in twice, tied it once more, "
        f"and nodded to {friend.id}."
    )
    world.say(
        f'"We can surf together," {hero.id} said, "and I can keep my scrunchie safe too."'
    )
    world.say(
        f"That was the kind of fine, featherlight plan that fits a tall tale: simple enough for a child, "
        f"strong enough for a storm."
    )
    world.say(
        f"So the two friends ran for the board, laughed at the spray, and caught the wave together."
    )
    world.say(
        f"The {scrunchie.label} stayed bright, the friendship stayed bright, and the sea rolled on like a blue drum."
    )


def tell_story(params: StoryParams) -> World:
    beach = Beach()
    world = World(beach)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"distance": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "friendship": 1.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="child",
        meters={"distance": 0.0},
        memes={"friendship": 1.0},
    ))
    scrunchie = world.add(Entity(
        id="scrunchie",
        kind="thing",
        type="accessory",
        label="scrunchie",
        phrase="a bright red scrunchie",
        owner=hero.id,
        worn_by=hero.id,
        meters={"grip": 1.0, "wet": 0.0, "salt": 0.0},
        memes={"value": 1.0},
    ))
    board = world.add(Entity(
        id="board",
        kind="thing",
        type="board",
        label="surfboard",
        phrase="a long surfboard with a blue stripe",
        owner=hero.id,
        meters={"distance": 0.0},
    ))

    _tall_tale_setup(world, hero, friend, scrunchie)
    _dilemma(world, hero, friend, scrunchie)
    _compromise(world, hero, friend, scrunchie)

    hero.meters["distance"] += 1.0
    friend.meters["distance"] += 1.0
    board.meters["distance"] += 1.0
    scrunchie.meters["wet"] = 0.0
    scrunchie.meters["salt"] = 0.0

    world.facts.update(
        hero=hero,
        friend=friend,
        scrunchie=scrunchie,
        board=board,
        beach=beach,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Maya", "Nina", "Luna", "Ivy", "Ada", "Zoe"]
BOY_NAMES = ["Finn", "Owen", "Kai", "Levi", "Noah", "Jude"]
FRIEND_NAMES = ["Pip", "June", "Milo", "Sunny", "Rae", "Tess"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        "Write a tall tale about a child, a scrunchie, and a surfboard on a windy beach.",
        f"Tell a story where {hero.id} and {friend.id} face a dilemma about surfing and a scrunchie.",
        "Use repetition and an inner monologue to make a beach friendship adventure feel grand.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    scrunchie = f["scrunchie"]
    return [
        QAItem(
            question=f"Why did {hero.id} worry before surfing?",
            answer=(
                f"{hero.id} worried that the {scrunchie.label} might fly off in the surf. "
                f"{hero.pronoun().capitalize()} wanted to surf right away, but {hero.pronoun('possessive')} "
                f"little scrunchie mattered to {hero.pronoun('object')}."
            ),
        ),
        QAItem(
            question=f"What did {friend.id} want {hero.id} to do?",
            answer=(
                f"{friend.id} wanted {hero.id} to surf with {friend.pronoun('object')} right away, "
                f"because the wave was waiting and friends like that do not like to leave a good wave behind."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} solve the dilemma?",
            answer=(
                f"{hero.id} tucked the {scrunchie.label} in twice, tied it once more, and surfed with {friend.id}. "
                f"The choice kept the friendship strong and the {scrunchie.label} safe."
            ),
        ),
        QAItem(
            question=f"What repeated words did {hero.id} keep saying?",
            answer=(
                f"{hero.id} kept saying, \"Hold tight, little scrunchie, hold tight,\" over and over. "
                f"That repetition showed the worry and the careful hope in {hero.pronoun('possessive')} mind."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surfboard?",
            answer="A surfboard is a board a person stands or lies on to ride waves on the water.",
        ),
        QAItem(
            question="What is a dilemma?",
            answer="A dilemma is a hard choice where each option has something good and something risky about it.",
        ),
        QAItem(
            question="What is a scrunchie?",
            answer="A scrunchie is a soft hair tie that holds hair together and is easier on hair than a tight band.",
        ),
        QAItem(
            question="Why do friends help each other?",
            answer="Friends help each other because they care about one another and want to share good things and hard moments.",
        ),
    ]


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  refrain_count={world.refrain_count}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
scrunchie(S) :- scrunchie_name(S).

dilemma(H,S) :- worry_about_losing(H,S), wants_to_surf(H).
needs_fix(H,S) :- dilemma(H,S), can_secure(S).
resolved(H,S) :- needs_fix(H,S), secures(H,S), surfs_together(H).

compatible_story(H,F,S) :- hero(H), friend(F), scrunchie(S),
                            wants_to_surf(H), wants_friendship(H,F),
                            worry_about_losing(H,S), can_secure(S).

#show compatible_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", name))
    lines.append(asp.fact("scrunchie_name", "scrunchie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    combos = asp_valid_combos()
    expected = sorted(
        (h, f, "scrunchie")
        for h in GIRL_NAMES + BOY_NAMES
        for f in FRIEND_NAMES
    )
    if combos == expected:
        print(f"OK: ASP gate matches expected compatibility ({len(combos)} combos).")
        return 0
    print("MISMATCH between ASP and expected compatibility:")
    print("  ASP:", combos)
    print("  PY :", expected)
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    friend_name: str
    place: str = "beach"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale beach storyworld with surf, dilemma, scrunchie, friendship, and repetition."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--place", choices=["beach"], default="beach")
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
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    if friend_name == name:
        raise StoryError("The friend must be a different child so the friendship can matter.")
    return StoryParams(name=name, gender=gender, friend_name=friend_name, place=args.place, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(name="Maya", gender="girl", friend_name="Pip"),
    StoryParams(name="Kai", gender="boy", friend_name="June"),
    StoryParams(name="Luna", gender="girl", friend_name="Milo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} with {p.friend_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
