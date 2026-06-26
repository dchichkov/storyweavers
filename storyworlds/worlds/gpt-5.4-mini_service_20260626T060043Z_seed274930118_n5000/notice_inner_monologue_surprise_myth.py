#!/usr/bin/env python3
"""
A standalone storyworld for a myth-style tale built around noticing an omen,
an inner monologue, and a surprise turn.

The world model tracks a small cast in a sacred place. The hero notices a sign,
argues with themself in inner monologue, and then meets a surprising outcome
that changes the ending image.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    sacred: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    light: str
    sound: str
    smell: str
    sacred_image: str


@dataclass
class Omen:
    label: str
    kind: str
    message: str
    sign_word: str
    appears_in: set[str] = field(default_factory=set)
    reveals: str = ""


@dataclass
class Gift:
    label: str
    phrase: str
    kind: str
    owner_kind: str
    hidden_truth: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "temple": Place(
        name="the temple hill",
        light="golden",
        sound="drums",
        smell="cedar smoke",
        sacred_image="a circle of lanterns around an ancient stone",
    ),
    "river": Place(
        name="the river shrine",
        light="silver",
        sound="water",
        smell="wet reeds",
        sacred_image="a moon-bright river touching the altar steps",
    ),
    "mountain": Place(
        name="the mountain pass",
        light="thin and cold",
        sound="wind",
        smell="pine and frost",
        sacred_image="a high cairn with snow on every edge",
    ),
}

OMENS = {
    "bird": Omen(
        label="a black bird",
        kind="bird",
        message="the gods were watching",
        sign_word="notice",
        appears_in={"temple", "river", "mountain"},
        reveals="a hidden path",
    ),
    "star": Omen(
        label="a falling star",
        kind="star",
        message="something old was about to change",
        sign_word="notice",
        appears_in={"temple", "mountain"},
        reveals="a buried door",
    ),
    "shell": Omen(
        label="a bright shell",
        kind="shell",
        message="the sea had sent a promise",
        sign_word="notice",
        appears_in={"river", "temple"},
        reveals="a secret gift",
    ),
    "flame": Omen(
        label="a blue flame",
        kind="flame",
        message="the sacred fire had woken",
        sign_word="notice",
        appears_in={"temple", "mountain"},
        reveals="a living crown",
    ),
}

GIFTS = {
    "crown": Gift(
        label="crown",
        phrase="a small bronze crown",
        kind="crown",
        owner_kind="leader",
        hidden_truth="it had been waiting for the humblest heart",
    ),
    "stone": Gift(
        label="stone",
        phrase="a smooth white stone",
        kind="stone",
        owner_kind="child",
        hidden_truth="it held the river's memory",
    ),
    "key": Gift(
        label="key",
        phrase="an iron key wrapped in cloth",
        kind="key",
        owner_kind="guardian",
        hidden_truth="it opened a door beneath the altar",
    ),
}

HEROES = [
    ("Ari", "boy"),
    ("Mira", "girl"),
    ("Niko", "boy"),
    ("Lena", "girl"),
]
TRAITS = ["quiet", "brave", "curious", "gentle", "restless", "thoughtful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    omen: str
    gift: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def hero_pronouns(hero: Entity) -> tuple[str, str, str]:
    return hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, pl in PLACES.items():
        for omen_id, omen in OMENS.items():
            if place not in omen.appears_in:
                continue
            for gift_id in GIFTS:
                combos.append((place, omen_id, gift_id))
    return combos


def reasonableness_gate(place: str, omen: str, gift: str) -> bool:
    return place in OMENS[omen].appears_in and gift in GIFTS


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    omen = OMENS[params.omen]
    gift = GIFTS[params.gift]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"a {params.trait} {params.gender}",
        meters={"hope": 1.0},
        memes={"wonder": 1.0, "unease": 0.0},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type="priestess",
        label="the keeper",
        phrase="the keeper of the shrine",
        meters={"care": 1.0},
        memes={"serenity": 1.0},
    ))
    sacred_item = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift.kind,
        label=gift.label,
        phrase=gift.phrase,
        owner=keeper.id,
        sacred=True,
        meters={"hidden": 1.0},
    ))

    world.facts.update(hero=hero, keeper=keeper, omen=omen, gift=sacred_item)

    sub, obj, pos = hero_pronouns(hero)

    # Act 1: setup
    world.say(
        f"At {place.name}, {hero.label} was a {params.trait} child who came to listen for signs."
    )
    world.say(
        f"{sub.capitalize()} loved the hush there, where {place.light} light rested on the stones and {place.sound} echoed between the pillars."
    )
    world.say(
        f"That day, {hero.label} carried {pos} thoughts like a little lantern and kept looking for meaning."
    )

    # Act 2: noticing the omen and inner monologue
    world.para()
    world.say(
        f"Then {hero.label} saw {omen.label} and {hero.pronoun('subject')} stopped short."
    )
    world.say(
        f"{sub.capitalize()} noticed it because {omen.message}; even the air felt different."
    )
    hero.memes["unease"] += 1.0
    hero.memes["wonder"] += 1.0

    world.say(
        f"Inside {obj}'s head, a soft inner monologue began: "
        f'"Should I speak? Should I wait? Maybe this is only wind. '
        f'No, I saw it too clearly to pretend otherwise."'
    )

    # Surprise turn
    world.para()
    world.say(
        f"{keeper.label} smiled as if {hero.label} had arrived on purpose."
    )
    world.say(
        f'With a surprising bow, {keeper.label} lifted the cloth and revealed {gift.phrase}.'
    )
    world.say(
        f"It was not a treasure for a king at all; {gift.hidden_truth}."
    )
    world.say(
        f"The omen had not warned of ruin. It had been a doorway, and {hero.label} was the one meant to walk through it."
    )

    # Resolution
    hero.meters["hope"] += 1.0
    hero.memes["unease"] = 0.0
    hero.memes["joy"] = 1.0
    sacred_item.carried_by = hero.id
    world.say(
        f"{hero.label} took {obj} in both hands, and the weight felt like a blessing."
    )
    world.say(
        f"By dusk, {sub} stood beneath {place.sacred_image}, holding {gift.phrase}, and the old hill seemed to answer with quiet light."
    )

    world.facts.update(
        resolved=True,
        ending_image=f"{hero.label} beneath {place.sacred_image} with {gift.phrase}",
    )
    return world


# ---------------------------------------------------------------------------
# Narration and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    omen: Omen = f["omen"]
    gift: Entity = f["gift"]
    return [
        f'Write a short myth for a child who notices {omen.label} at {world.place.name}.',
        f"Tell a gentle myth where {hero.label} has an inner monologue after seeing a sign and then meets a surprising truth.",
        f"Write a story about noticing, fear, and wonder that ends with {gift.phrase} becoming a blessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    omen: Omen = f["omen"]
    gift: Entity = f["gift"]
    place = world.place.name
    sub, obj, pos = hero_pronouns(hero)
    return [
        QAItem(
            question=f"What did {hero.label} notice first at {place}?",
            answer=f"{hero.label} first noticed {omen.label}. That was the sign that made {obj} stop and think.",
        ),
        QAItem(
            question=f"What was {hero.label} thinking about in {pos} inner monologue?",
            answer=(
                f"{sub.capitalize()} wondered whether to speak, wait, or trust what {obj} had seen. "
                f"The little inner monologue showed {obj}'s doubt and courage at the same time."
            ),
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=(
                f"The surprise was that {f['keeper'].label} revealed {gift.phrase} instead of a danger. "
                f"The sign was a doorway to a blessing."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {hero.label} holding {gift.phrase} beneath {world.place.sacred_image}, "
                f"which showed that the omen led to a true gift."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an omen?",
            answer="An omen is a sign that people think points to something important that may happen.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talk a person has inside their own mind.",
        ),
        QAItem(
            question="Why can a surprise change a story?",
            answer="A surprise can change a story because it makes the character learn something new and respond in a different way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.name}")
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
omen_ok(P,O) :- place(P), omen(O), appears_in(O,P).
valid_story(P,O,G) :- omen_ok(P,O), gift(G).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        for p in sorted(omen.appears_in):
            lines.append(asp.fact("appears_in", oid, p))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth storyworld with noticing, inner monologue, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.omen:
        combos = [c for c in combos if c[1] == args.omen]
    if args.gift:
        combos = [c for c in combos if c[2] == args.gift]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, omen, gift = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice([n for n, g in HEROES if g == gender])
    trait = args.trait or rng.choice(TRAITS)
    if args.gender and args.name is None:
        candidates = [n for n, g in HEROES if g == gender]
        if not candidates:
            raise StoryError("No hero names available for that gender.")
    return StoryParams(place=place, omen=omen, gift=gift, name=name, gender=gender, trait=trait)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, omen, gift in valid_combos():
            params = StoryParams(
                place=place,
                omen=omen,
                gift=gift,
                name="Ari",
                gender="boy",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
