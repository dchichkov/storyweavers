#!/usr/bin/env python3
"""
A standalone storyworld for a tiny mythic tale about three friends, eerie sound
effects, foreshadowing, and a kind friendship that saves the day.

Seed premise:
- In an old, legend-like place, three companions travel together.
- Strange sounds in the dark foreshadow trouble.
- Their friendship helps them cooperate, face the omen, and finish the quest.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAME_POOL = [
    "Ari", "Bela", "Ciro", "Dara", "Eli", "Fae", "Galen", "Hera", "Ivo", "Juna"
]

SETTING_POOL = {
    "cave": "a moonlit cave",
    "forest": "an ancient forest",
    "bridge": "a stone bridge over a black river",
    "hill": "a windy hill of old grass",
}

SOUND_EFFECTS = {
    "drip": {
        "word": "drip-drip",
        "description": "water tapping from the stone like tiny fingers",
        "omen": "a hidden leak or a crack above",
    },
    "rumble": {
        "word": "rumble-rumble",
        "description": "the earth talking in a low, sleepy voice",
        "omen": "a shift under the path",
    },
    "whoosh": {
        "word": "whoosh",
        "description": "a wind that slipped through the dark with a long sigh",
        "omen": "a sudden gust or a door of air opening somewhere ahead",
    },
    "clang": {
        "word": "clang-clang",
        "description": "metal singing against stone",
        "omen": "a gate, chain, or guardian stirring nearby",
    },
}

GIFTS = {
    "lamp": "a little bronze lamp",
    "rope": "a woven rope",
    "flute": "a reed flute",
    "bread": "a round loaf of travel bread",
}

MITHIC_ACTIONS = {
    "crossing": "cross the old place",
    "seeking": "seek the hidden shrine",
    "listening": "listen for the path home",
}

MYTH_BEATS = [
    "the old world had a voice",
    "every sound could carry a warning",
    "friendship was stronger than fear",
    "the bravest step was the one taken together",
]

KNOWLEDGE = {
    "threesome": [
        ("What is a threesome?", "A threesome is a group of three people or things together."),
    ],
    "friendship": [
        ("What is friendship?", "Friendship is when people care for one another, help one another, and enjoy being together."),
    ],
    "foreshadowing": [
        ("What is foreshadowing?", "Foreshadowing is a clue in a story that hints something important may happen later."),
    ],
    "sound": [
        ("What is a sound effect?", "A sound effect is a word that helps readers imagine a noise, like drip-drip or clang."),
    ],
    "myth": [
        ("What is a myth?", "A myth is an old story that often includes heroes, strange places, and magical or legendary events."),
    ],
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    phrase: str
    sound: str
    omen: str
    affords: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    sound: str
    gift: str
    names: list[str]
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Three friends form a threesome.
trio(A,B,C) :- friend(A,B), friend(B,C), friend(A,C), A < B, B < C.

% A sound effect can foreshadow an omen for the place.
foreshadows(P,S) :- place(P), sound(S), omen(P,O), hint(S,O).

% The story is valid when the trio and the omen both exist.
valid_story(P,S) :- trio(A,B,C), place(P), sound(S), foreshadows(P,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, place in PLACES.items():
        lines.append(asp.fact("place", key))
        lines.append(asp.fact("omen", key, place.omen))
        for snd in place.affords:
            lines.append(asp.fact("hint", snd, place.omen))
    for snd in SOUNDS:
        lines.append(asp.fact("sound", snd))
    for name in NAME_POOL:
        lines.append(asp.fact("person", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pkey, place in PLACES.items():
        for skey in place.affords:
            combos.append((pkey, skey))
    return combos


def trio_names(rng: random.Random) -> list[str]:
    names = rng.sample(NAME_POOL, 3)
    return sorted(names)


def choose_gift(rng: random.Random) -> str:
    return rng.choice(sorted(GIFTS))


def reasonableness_check(place: str, sound: str) -> None:
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if sound not in SOUNDS:
        raise StoryError("Unknown sound effect.")
    if sound not in PLACES[place].affords:
        raise StoryError(
            f"(No story: {SOUNDS[sound]['word']} does not fit {PLACES[place].phrase}; "
            f"that omen would feel forced.)"
        )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    a, b, c = params.names
    hero = world.add(Entity(id=a, kind="character", type="friend", label=a))
    friend_b = world.add(Entity(id=b, kind="character", type="friend", label=b))
    friend_c = world.add(Entity(id=c, kind="character", type="friend", label=c))
    relic = world.add(Entity(
        id="relic",
        type="thing",
        label=GIFTS[params.gift],
        phrase=GIFTS[params.gift],
        owner=a,
    ))

    # setup
    world.say(
        f"In the old tales, {hero.id}, {friend_b.id}, and {friend_c.id} walked as one "
        f"through {place.phrase}."
    )
    world.say(
        f"They carried {relic.phrase}, because the journey was meant to end in a small "
        f"gift for the shrine."
    )
    world.say(
        f"Their friendship was easy and bright; if one grew tired, the others slowed down."
    )

    # foreshadowing
    world.para()
    effect = SOUNDS[params.sound]
    world.say(
        f"Then, from the dark, came {effect['word']}. It sounded like {effect['description']}."
    )
    world.say(
        f"The sound felt like a clue. In a myth, such a sign can mean {effect['omen']}."
    )
    world.say(
        f"{hero.id} listened carefully, and {friend_b.id} and {friend_c.id} listened too."
    )

    # tension
    world.para()
    world.say(
        f"Still, the path ahead narrowed. The {effect['word']} came again, and this time "
        f"the air seemed to push back."
    )
    world.say(
        f"{friend_c.id} wanted to hurry, but {hero.id} remembered that friendship means "
        f"not leaving anyone behind."
    )
    world.say(
        f"So the threesome joined hands and chose a slower way."
    )

    # resolution
    world.para()
    world.say(
        f"Together they used {relic.phrase} as a careful token: {hero.id} held it high, "
        f"{friend_b.id} steadied the light, and {friend_c.id} sang softly to keep their courage."
    )
    world.say(
        f"The warning had been true, and because they had listened, the hidden danger passed "
        f"without breaking their steps."
    )
    world.say(
        f"By dawn, the three friends stood safely beyond {place.phrase}, and the old place "
        f"felt less lonely for having been understood."
    )

    world.facts.update(
        trio=(a, b, c),
        place=params.place,
        sound=params.sound,
        gift=params.gift,
        effect=effect["word"],
        omen=effect["omen"],
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = PLACES[f["place"]].phrase
    sound = SOUNDS[f["sound"]]["word"]
    return [
        f'Write a short myth about a threesome of friends in {place} where the sound "{sound}" foreshadows danger.',
        f"Tell a child-friendly legend about three companions who hear {sound} and stay close because of friendship.",
        f"Write a tiny myth that uses foreshadowing, sound effects, and a trio of friends crossing {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b, c = world.facts["trio"]
    place = PLACES[world.facts["place"]].phrase
    sound = SOUNDS[world.facts["sound"]]["word"]
    omen = SOUNDS[world.facts["sound"]]["omen"]
    gift = GIFTS[world.facts["gift"]]

    return [
        QAItem(
            question=f"Who made up the threesome in the story?",
            answer=f"The threesome was {a}, {b}, and {c}. They traveled together through {place}.",
        ),
        QAItem(
            question=f"What sound effect foreshadowed trouble?",
            answer=f"The sound effect was {sound}. It hinted at {omen}.",
        ),
        QAItem(
            question=f"What did the friends carry on their journey?",
            answer=f"They carried {gift} as a small gift for the shrine, and they protected it by staying together.",
        ),
        QAItem(
            question=f"Why did the friends slow down instead of rushing ahead?",
            answer=(
                f"They slowed down because the {sound} was a foreshadowing clue, and the friends "
                f"trusted one another enough to listen before the danger reached them."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, the threesome had crossed {place} safely. Their friendship stayed strong, "
                f"and the old place felt less lonely."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("threesome", "friendship", "foreshadowing", "sound", "myth"):
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries / settings
# ---------------------------------------------------------------------------

PLACES = {
    "cave": Place(key="cave", phrase=SETTING_POOL["cave"], sound="drip", omen="a hidden leak or a crack above", affords={"drip"}),
    "forest": Place(key="forest", phrase=SETTING_POOL["forest"], sound="whoosh", omen="a sudden gust or a door of air opening somewhere ahead", affords={"whoosh"}),
    "bridge": Place(key="bridge", phrase=SETTING_POOL["bridge"], sound="clang", omen="a gate, chain, or guardian stirring nearby", affords={"clang"}),
    "hill": Place(key="hill", phrase=SETTING_POOL["hill"], sound="rumble", omen="a shift under the path", affords={"rumble"}),
}

SOUNDS = SOUND_EFFECTS


CURATED = [
    StoryParams(place="cave", sound="drip", gift="lamp", names=["Ari", "Bela", "Ciro"]),
    StoryParams(place="forest", sound="whoosh", gift="rope", names=["Dara", "Eli", "Fae"]),
    StoryParams(place="bridge", sound="clang", gift="flute", names=["Galen", "Hera", "Ivo"]),
    StoryParams(place="hill", sound="rumble", gift="bread", names=["Juna", "Ari", "Bela"]),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: threesome, sound effects, friendship, foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    sound = args.sound or rng.choice(sorted(PLACES[place].affords))
    reasonableness_check(place, sound)
    gift = args.gift or rng.choice(list(GIFTS))
    names = [args.name] if args.name else trio_names(rng)
    if len(names) != 3:
        names = trio_names(rng)
    return StoryParams(place=place, sound=sound, gift=gift, names=names)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, s in combos:
            print(f"  {p:8} {s}")
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
            header = f"### {p.place} / {p.sound} / {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
