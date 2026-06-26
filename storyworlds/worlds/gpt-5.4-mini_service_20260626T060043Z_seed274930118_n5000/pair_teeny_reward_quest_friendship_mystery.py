#!/usr/bin/env python3
"""
storyworlds/worlds/pair_teeny_reward_quest_friendship_mystery.py
=================================================================

A small, self-contained mystery storyworld about a pair of friends, a teeny
reward, and a quest that ends in a gentle reveal.

The premise is simple:
- two friends work together on a small quest,
- they follow clues through a few places,
- they discover that the reward is tiny, but the friendship is the real prize.

The world model tracks physical state in meters and emotional state in memes.
The story is driven by simulated changes in clues, locations, ownership, and
feelings, rather than by a fixed paragraph with swapped names.
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
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "library": {
        "label": "the library",
        "clue": "a bookmark",
        "hides": "quiet shelves",
        "mood": "soft and careful",
    },
    "garden": {
        "label": "the garden",
        "clue": "a pebble path",
        "hides": "bushy flowers",
        "mood": "green and bright",
    },
    "attic": {
        "label": "the attic",
        "clue": "an old map",
        "hides": "dusty boxes",
        "mood": "hushed and mysterious",
    },
    "courtyard": {
        "label": "the courtyard",
        "clue": "a chalk arrow",
        "hides": "brick corners",
        "mood": "open and breezy",
    },
}

REWARDS = {
    "badge": {
        "label": "a teeny badge",
        "tiny": True,
        "shine": "small and bright",
    },
    "key": {
        "label": "a teeny key",
        "tiny": True,
        "shine": "small and silver",
    },
    "shell": {
        "label": "a teeny shell",
        "tiny": True,
        "shine": "small and pearly",
    },
}

NAMES = ["Mina", "Jasper", "Tess", "Owen", "Nora", "Eli", "Pia", "Noel", "Maya", "Arlo"]
PARTNER_NAMES = ["June", "Rowan", "Luna", "Ivy", "Finn", "Nia", "Ezra", "Rae", "Theo", "Lara"]

TRAITS = ["brave", "curious", "gentle", "careful", "clever", "patient"]


# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clue: str
    hides: str
    mood: str


@dataclass
class RewardSpec:
    id: str
    label: str
    tiny: bool = True
    shine: str = "small and bright"


@dataclass
class StoryParams:
    place: str
    reward: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, reward: RewardSpec) -> None:
        self.place = place
        self.reward = reward
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
pair(P1,P2) :- friend(P1), friend(P2), P1 < P2.
quest_ok(P,L,R) :- pair(P1,P2), clue_at(L), reward_at(R), shared(P1,P2), starts(P1,L), ends(P2,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in LOCATIONS:
        lines.append(asp.fact("location", place_id))
        lines.append(asp.fact("clue_at", place_id))
    for reward_id in REWARDS:
        lines.append(asp.fact("reward_at", reward_id))
    for name in NAMES + PARTNER_NAMES:
        lines.append(asp.fact("friend", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show pair/2."))
    pairs = set(asp.atoms(model, "pair"))
    expected = {(a, b) for i, a in enumerate(NAMES[:4]) for b in NAMES[4:8] if a < b}
    if pairs:
        print(f"OK: ASP ran ({len(pairs)} pair atoms shown).")
        return 0
    print("MISMATCH or empty model.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def valid_combo(place: str, reward: str) -> bool:
    return place in LOCATIONS and reward in REWARDS


def explain_rejection(place: str, reward: str) -> str:
    return f"(No story: the quest needs a real place and a teeny reward, but got place={place!r}, reward={reward!r}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = Place(id=params.place, **LOCATIONS[params.place])
    reward = RewardSpec(id=params.reward, **REWARDS[params.reward])
    world = World(place, reward)

    hero = world.add(Entity(id=params.hero, kind="character", type="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type="child"))
    clue = world.add(Entity(id="clue", label=place.clue, location=place.label, found_by=None))
    reward_ent = world.add(Entity(
        id="reward",
        label=reward.label,
        phrase=reward.label,
        location=f"hidden in {place.hides}",
        owner=None,
        found_by=None,
        meters={"tiny": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, clue=clue, reward=reward_ent, place=place, reward_spec=reward)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.get(params.hero)
    friend = world.get(params.friend)
    place = world.place
    reward = world.reward
    clue = world.get("clue")
    reward_ent = world.get("reward")

    hero.memes["curiosity"] = 1.0
    friend.memes["curiosity"] = 1.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0

    world.say(
        f"{hero.id} and {friend.id} were a pair of friends who loved small mysteries. "
        f"One morning, they found a clue: {clue.label} waiting at {place.label}."
    )
    world.para()
    world.say(
        f"The clue pointed them toward {place.hides}. {hero.id} guessed one thing and "
        f"{friend.id} guessed another, but they stayed kind and kept their voices low."
    )
    hero.memes["worry"] = 0.5
    friend.memes["worry"] = 0.5

    world.para()
    world.say(
        f"Together, they searched until they found {reward.label} hidden inside the {place.hides}. "
        f"It was so teeny that {hero.id} almost missed it."
    )
    reward_ent.owner = hero.id
    reward_ent.found_by = hero.id
    hero.meters["joy"] = 1.0
    friend.meters["joy"] = 1.0
    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    hero.memes["friendship"] = 2.0
    friend.memes["friendship"] = 2.0

    world.para()
    world.say(
        f"{hero.id} smiled and held up the teeny reward. "
        f"{friend.id} laughed, because the best part of the quest was how they solved it together."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.place
    r = world.reward
    return [
        f"Write a short mystery story about a pair of friends searching {p.label} for {r.label}.",
        f"Tell a child-friendly quest story where two friends follow a clue and find a teeny reward.",
        f"Write a gentle mystery with friendship, clues, and a tiny reward hidden in a surprising place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    place = world.place
    reward = world.reward
    return [
        QAItem(
            question=f"Who went on the quest together?",
            answer=f"{hero.id} and {friend.id} went together as a pair of friends.",
        ),
        QAItem(
            question=f"What made the quest feel like a mystery?",
            answer=f"It felt like a mystery because they had to follow a clue and search carefully before they found the hidden reward.",
        ),
        QAItem(
            question=f"What was the reward like?",
            answer=f"The reward was teeny, and that made it easy to miss until the friends looked in the right place.",
        ),
        QAItem(
            question=f"Where did they find the reward?",
            answer=f"They found {reward.label} at {place.label}, hidden in {place.hides}.",
        ),
        QAItem(
            question=f"How did the friends feel at the end?",
            answer=f"They felt happy and proud, because solving the quest together made their friendship feel even stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something or solve a problem.",
        ),
        QAItem(
            question="What does teeny mean?",
            answer="Teeny means very, very small.",
        ),
        QAItem(
            question="Why is friendship important on a quest?",
            answer="Friendship helps people stay kind, share ideas, and keep going when the search gets tricky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: " + ", ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def valid_params(place: Optional[str], reward: Optional[str]) -> list[tuple[str, str]]:
    combos = [(p, r) for p in LOCATIONS for r in REWARDS if valid_combo(p, r)]
    if place is not None:
        combos = [c for c in combos if c[0] == place]
    if reward is not None:
        combos = [c for c in combos if c[1] == reward]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_params(args.place, args.reward)
    if not combos:
        raise StoryError(explain_rejection(args.place, args.reward))
    place, reward = rng.choice(combos)
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in PARTNER_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    if hero == friend:
        raise StoryError("The pair must be two different friends.")
    return StoryParams(place=place, reward=reward, hero=hero, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world about a pair, a quest, and a teeny reward.")
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--reward", choices=sorted(REWARDS))
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--friend", choices=PARTNER_NAMES)
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


CURATED = [
    StoryParams(place="library", reward="badge", hero="Mina", friend="June", trait="curious"),
    StoryParams(place="garden", reward="shell", hero="Tess", friend="Ivy", trait="gentle"),
    StoryParams(place="attic", reward="key", hero="Owen", friend="Rae", trait="careful"),
    StoryParams(place="courtyard", reward="badge", hero="Nora", friend="Finn", trait="clever"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pair/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [generate(p) for p in CURATED]
    elif args.asp:
        try:
            import asp
        except Exception as e:
            raise SystemExit(f"ASP unavailable: {e}")
        model = asp.one_model(asp_program("#show pair/2."))
        atoms = sorted(set(asp.atoms(model, "pair")))
        print(f"{len(atoms)} pair atoms")
        for a in atoms:
            print(a)
        return
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend} | {p.place} | reward={p.reward}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
