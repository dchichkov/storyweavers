#!/usr/bin/env python3
"""
A small Tall Tale storyworld about clambering, ramen, kindness, inner monologue,
and sharing.

The seed idea:
A large-hearted kid has a giant bowl of ramen, but the noodles and broth must
reach a hungry friend up high. The hero clambers through a tiny, exaggerated
landscape, listens to an inner monologue about being generous, and ends by
sharing the ramen in a way that feels bigger than the hill itself.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    with_actor: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    ramen_style: str
    seed: Optional[int] = None


PLACES = {
    "hill": "the big hill",
    "stair": "the long stairway",
    "tower": "the leaning tower",
    "dock": "the windy dock",
    "garden": "the rooftop garden",
}

RAMEN_STYLES = {
    "simple": "a steaming bowl of ramen",
    "giant": "a giant bowl of ramen with shining noodles",
    "noisy": "a slurpy bowl of ramen with bright broth",
    "golden": "a golden bowl of ramen that smelled like a feast",
}

HERO_NAMES = ["Milo", "June", "Ari", "Nia", "Toby", "Lena", "Pip", "Sora"]
FRIEND_NAMES = ["Bea", "Omar", "Ivy", "Jax", "Mina", "Noor", "Ezra", "Mara"]

TYPES = ["girl", "boy"]
PLACES_ORDER = list(PLACES)


# ---------------------------------------------------------------------------
# ASP twin and registry facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- site(P).
ramen(R) :- bowl(R).
has_friend(H,F) :- hero(H), friend(F).
can_share(H,R) :- hero(H), ramen(R), kindness(H,K), K >= 1.
needs_clamber(H,P) :- hero(H), site(P), tall(P), at(H,P), climbable(P).
good_story(H,F,R,P) :- can_share(H,R), has_friend(H,F), needs_clamber(H,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in PLACES:
        lines.append(asp.fact("site", key))
    for key in RAMEN_STYLES:
        lines.append(asp.fact("bowl", key))
    lines.append(asp.fact("tall", "hill"))
    lines.append(asp.fact("tall", "stair"))
    lines.append(asp.fact("tall", "tower"))
    lines.append(asp.fact("climbable", "hill"))
    lines.append(asp.fact("climbable", "stair"))
    lines.append(asp.fact("climbable", "tower"))
    lines.append(asp.fact("climbable", "dock"))
    lines.append(asp.fact("climbable", "garden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = set()
    for p in valid_combos():
        py_set.add(p)
    # Compare only projection to the same abstract shape.
    py_proj = {(h, f, r, p) for (h, f, r, p) in py_set}
    if asp_set == py_proj:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_proj:
        print("  only in clingo:", sorted(asp_set - py_proj))
    if py_proj - asp_set:
        print("  only in python:", sorted(py_proj - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for hero_name in HERO_NAMES:
            for friend_name in FRIEND_NAMES:
                if hero_name == friend_name:
                    continue
                for ramen in RAMEN_STYLES:
                    combos.append((hero_name, friend_name, ramen, place))
    return combos


def explain_rejection() -> str:
    return "(No story: this world needs a hero, a friend, a ramen bowl, and a place to clamber.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"height": 2.0, "hope": 1.0},
        memes={"kindness": 1.0, "hunger": 0.2, "resolve": 0.5, "monologue": 0.5},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        meters={"height": 1.0, "hope": 0.8},
        memes={"kindness": 0.4, "hunger": 1.0, "waiting": 1.0},
    ))
    ramen = world.add(Entity(
        id="ramen",
        kind="thing",
        type="ramen",
        label="ramen",
        phrase=RAMEN_STYLES[params.ramen_style],
        owner=hero.id,
        with_actor=hero.id,
        meters={"steam": 1.0, "warmth": 1.0, "fullness": 1.0},
        memes={"delight": 1.0},
        plural=False,
    ))
    world.facts.update(hero=hero, friend=friend, ramen=ramen, params=params)
    return world


def inner_monologue(world: World, hero: Entity, friend: Entity, ramen: Entity) -> None:
    hero.memes["monologue"] += 1.0
    hero.memes["kindness"] += 0.5
    world.say(
        f"{hero.label} looked at the {ramen.phrase} and thought, "
        f'"If I keep this all to myself, {friend.label} will still be hungry."'
    )
    world.say(
        f"Then {hero.label} thought again, quieter and braver: "
        f'"A warm bowl tastes better when it helps somebody else."'
    )


def clamber(world: World, hero: Entity) -> None:
    hero.meters["effort"] = hero.meters.get("effort", 0.0) + 1.0
    hero.meters["clamber"] = hero.meters.get("clamber", 0.0) + 1.0
    world.say(
        f"{hero.label} clambered up {world.place} step by step, "
        f"like a determined sparrow climbing a fence."
    )


def reveal_need(world: World, friend: Entity) -> None:
    friend.memes["waiting"] += 0.5
    world.say(
        f"At the top, {friend.label} sat with a small sigh, watching the road "
        f"as if supper might roll up on wheels."
    )


def share_ramen(world: World, hero: Entity, friend: Entity, ramen: Entity) -> None:
    hero.memes["sharing"] = 1.0
    friend.memes["sharing"] = 1.0
    friend.memes["hunger"] = 0.0
    friend.meters["fullness"] = friend.meters.get("fullness", 0.0) + 1.0
    ramen.meters["steam"] = 0.5
    ramen.meters["fullness"] = 0.4
    world.say(
        f"{hero.label} held out the bowl and said, "
        f'"I brought us ramen. Let\'s share it so nobody is left out."'
    )
    world.say(
        f"{friend.label} smiled so wide it looked like dawn. "
        f"Together they shared the noodles, the broth, and the last little mushroom."
    )


def ending_image(world: World, hero: Entity, friend: Entity, ramen: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(
        f"By the time the bowl was nearly empty, {world.place} seemed smaller, "
        f"but their kindness seemed bigger."
    )
    world.say(
        f"{hero.label} and {friend.label} sat shoulder to shoulder, warm with ramen "
        f"and warm with sharing, while the wind above them forgot how to be bossy."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    ramen = world.get("ramen")

    world.say(
        f"{hero.label} was a {params.hero_type} with a heart big enough to "
        f"carry soup, songs, and sunshine."
    )
    world.say(
        f"One day {hero.label} had {ramen.phrase}, and {friend.label} was waiting "
        f"way up {world.place}."
    )
    world.para()
    clamber(world, hero)
    reveal_need(world, friend)
    inner_monologue(world, hero, friend, ramen)
    share_ramen(world, hero, friend, ramen)
    world.para()
    ending_image(world, hero, friend, ramen)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    ramen = world.facts["ramen"]
    return [
        f'Write a tall tale for a small child about "{hero.label}" who must clamber up {world.place} with {ramen.phrase}.',
        f"Tell a gentle story where {hero.label} thinks to themself, then chooses kindness and sharing with {friend.label}.",
        f'Write a short, big-hearted story that includes clamber, ramen, kindness, inner monologue, and sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    ramen: Entity = world.facts["ramen"]
    params: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Who was climbing up {world.place} with the ramen?",
            answer=f"{hero.label} was climbing up {world.place} with {ramen.phrase}."
        ),
        QAItem(
            question=f"What did {hero.label} think about before sharing?",
            answer=(
                f"{hero.label} thought that keeping the ramen all to themself would leave "
                f"{friend.label} hungry, so sharing would be kinder."
            ),
        ),
        QAItem(
            question=f"What did the two friends do at the end?",
            answer=(
                f"They shared the ramen together, and that turned the meal into a warm "
                f"happy moment instead of a lonely one."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ramen?",
            answer="Ramen is a noodle soup with broth, noodles, and toppings like eggs or vegetables."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or care about someone else."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in someone's head when they are thinking."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: clamber, ramen, kindness, inner monologue, sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--friend-type", choices=TYPES)
    ap.add_argument("--ramen-style", choices=RAMEN_STYLES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())

    filtered = []
    for hero_name, friend_name, ramen, place in combos:
        if args.place and place != args.place:
            continue
        if args.hero_name and hero_name != args.hero_name:
            continue
        if args.friend_name and friend_name != args.friend_name:
            continue
        if args.ramen_style and ramen != args.ramen_style:
            continue
        filtered.append((hero_name, friend_name, ramen, place))

    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    hero_name, friend_name, ramen, place = rng.choice(filtered)
    hero_type = args.hero_type or rng.choice(TYPES)
    friend_type = args.friend_type or rng.choice(TYPES)
    if hero_name == friend_name:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        ramen_style=ramen,
    )


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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            print(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hill", hero_name="Milo", hero_type="boy", friend_name="Bea", friend_type="girl", ramen_style="giant"),
            StoryParams(place="tower", hero_name="June", hero_type="girl", friend_name="Omar", friend_type="boy", ramen_style="golden"),
            StoryParams(place="stair", hero_name="Ari", hero_type="boy", friend_name="Mina", friend_type="girl", ramen_style="noisy"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
