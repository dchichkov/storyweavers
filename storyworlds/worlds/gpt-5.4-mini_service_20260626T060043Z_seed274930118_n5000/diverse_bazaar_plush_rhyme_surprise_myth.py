#!/usr/bin/env python3
"""
A tiny mythic bazaar world where plush gifts, rhyme, and surprise
shape a short child-facing story.

The premise:
- A small bazaar opens in a bright square.
- A child wants a plush treasure.
- A keeper of stalls warns that the treasure should be chosen with care.
- The story turns on rhyme as a way to test charms and reveals a surprise.

This script is self-contained and follows the Storyworld contract.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bazaar"
    night: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Plush:
    id: str
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    verse: str
    rhyme_key: str
    reveals: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bazaar": Setting(place="the bazaar", night=False, affords={"browse", "buy"}),
    "night_bazaar": Setting(place="the moonlit bazaar", night=True, affords={"browse", "buy"}),
    "river_bazaar": Setting(place="the river bazaar", night=False, affords={"browse", "buy"}),
}

PLUSHES = {
    "lion": Plush(
        id="lion",
        label="plush lion",
        phrase="a plush lion with a golden mane",
        type="lion",
        tags={"plush", "myth", "lion"},
    ),
    "bird": Plush(
        id="bird",
        label="plush bird",
        phrase="a plush bird with stitched blue wings",
        type="bird",
        tags={"plush", "myth", "bird"},
    ),
    "fox": Plush(
        id="fox",
        label="plush fox",
        phrase="a plush fox with bright ears",
        type="fox",
        tags={"plush", "myth", "fox"},
    ),
    "whale": Plush(
        id="whale",
        label="plush whale",
        phrase="a plush whale with a silver smile",
        type="whale",
        tags={"plush", "myth", "sea"},
    ),
}

CHARMS = {
    "ember": Charm(
        id="ember",
        label="ember charm",
        phrase="an ember charm on a cord",
        verse="ember and timber, shimmer and glimmer",
        rhyme_key="ember",
        reveals="the charm was warm but harmless",
        tags={"rhyme", "surprise", "myth"},
    ),
    "river": Charm(
        id="river",
        label="river charm",
        phrase="a river charm wrapped in reed",
        verse="river and silver, giver and shiver",
        rhyme_key="river",
        reveals="the charm was only a story-token, not magic to fear",
        tags={"rhyme", "surprise", "myth"},
    ),
    "crown": Charm(
        id="crown",
        label="crown charm",
        phrase="a tiny crown charm",
        verse="crown and dawn, frown and shone",
        rhyme_key="crown",
        reveals="the charm belonged to the stallkeeper's child",
        tags={"rhyme", "surprise", "myth"},
    ),
}

GROUNDS = [
    "a bright square",
    "a lane of cloth awnings",
    "a stone path beside the fountain",
]

NAMES = {
    "girl": ["Mira", "Lina", "Nora", "Sana", "Tala"],
    "boy": ["Ari", "Bram", "Kian", "Rafi", "Oren"],
}
TRAITS = ["curious", "gentle", "brave", "hopeful", "lively"]
PARENTS = ["mother", "father", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    plush: str
    charm: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.plush not in PLUSHES:
        raise StoryError("unknown plush choice")
    if params.charm not in CHARMS:
        raise StoryError("unknown charm choice")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("gender must be girl or boy")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"hope": 1.0},
        memes={"curiosity": 1.0},
    ))
    guardian = world.add(Entity(
        id="Guardian",
        kind="character",
        type=params.guardian,
        label=f"the {params.guardian}",
        meters={"care": 1.0},
    ))
    plush = PLUSHES[params.plush]
    charm = CHARMS[params.charm]

    toy = world.add(Entity(
        id="toy",
        type=plush.type,
        label=plush.label,
        phrase=plush.phrase,
        owner=hero.id,
    ))
    token = world.add(Entity(
        id="token",
        type="charm",
        label=charm.label,
        phrase=charm.phrase,
        owner=guardian.id,
    ))

    world.facts.update(hero=hero, guardian=guardian, toy=toy, token=token,
                       plush=plush, charm=charm, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    guardian: Entity = f["guardian"]
    toy: Entity = f["toy"]
    plush: Plush = f["plush"]
    charm: Charm = f["charm"]
    params: StoryParams = f["params"]

    world.say(
        f"Long ago, in {world.setting.place}, there lived a {params.trait} {params.gender} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved the bazaar because every stall had colors, bells, and tiny wonders."
    )
    world.say(
        f"One day, {guardian.label} brought {hero.id} {plush.phrase}, and {hero.id} hugged {toy.label} close."
    )

    world.para()
    world.say(
        f"Near the fountain, a keeper showed {hero.id} {charm.phrase} and sang, "
        f"'{charm.verse}.'"
    )
    world.say(
        f"{hero.id} asked if the charm was a treasure from a far-off king, a river spirit, or a hidden star."
    )
    world.say(
        f"The keeper only smiled, because the bazaar loved riddles and surprise."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to buy the charm and carry {toy.label} home too, but {guardian.label} said, "
        f'\"First, listen for the rhyme. The bazaar never gives up its secrets all at once.\"'
    )
    world.say(
        f"{hero.id} repeated the verse, and the words rang together like little bells."
    )
    world.say(
        f"At the last rhyme, the keeper bowed and revealed that {charm.reveals}."
    )

    world.para()
    world.say(
        f"{hero.id} laughed in surprise, because the wonder was not a dragon or a storm, but a kind story."
    )
    world.say(
        f"{guardian.label} bought the charm beside {toy.label}, and {hero.id} walked home with {toy.label} in one hand and the secret in the other."
    )
    world.say(
        f"That night, {hero.id} whispered the rhyme to {toy.label}, and the plush lion, bird, fox, or whale seemed to smile in the moonlight."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- bazaar(S).
hero(H) :- name(H).
plush(P) :- plush_kind(P).
charm(C) :- charm_kind(C).

desire(H, P) :- hero(H), plush(P).
surprise(C) :- charm(C), reveal(C, _).
rhyme(C) :- charm(C), rhyme_key(C, _).

mythic_story(S, H, P, C) :- setting(S), hero(H), plush(P), charm(C),
                            desire(H, P), surprise(C), rhyme(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("bazaar", sid))
    for pid in PLUSHES:
        lines.append(asp.fact("plush_kind", pid))
    for cid in CHARMS:
        lines.append(asp.fact("charm_kind", cid))
        lines.append(asp.fact("rhyme_key", cid, CHARMS[cid].rhyme_key))
        lines.append(asp.fact("reveal", cid, CHARMS[cid].reveals))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show mythic_story/4.")
    model = asp.one_model(program)
    tuples = asp.atoms(model, "mythic_story")
    ok = len(tuples) == len(SETTINGS) * len(PLUSHES) * len(CHARMS)
    if ok:
        print(f"OK: ASP produced {len(tuples)} mythic_story atoms.")
        return 0
    print("MISMATCH: ASP twin did not enumerate the expected story space.")
    print(sorted(tuples))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a short mythic story for a child about a bazaar, a {params.plush}, and a rhyme that ends in surprise.',
        f'Tell a gentle tale set in {world.setting.place} where {params.name} hears a rhyme and discovers a secret charm.',
        f'Write a child-friendly myth about a bazaar seller, a plush treasure, and a surprising reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    charm: Charm = f["charm"]
    plush: Plush = f["plush"]
    return [
        QAItem(
            question=f"Who walked through the bazaar with {plush.label}?",
            answer=f"It was {params.name}, a {params.trait} {params.gender}, who walked through the bazaar with {plush.label}.",
        ),
        QAItem(
            question=f"What did the keeper sing to make the story feel magical?",
            answer=f"The keeper sang, '{charm.verse}.' The rhyme made the moment feel special and old as a myth.",
        ),
        QAItem(
            question=f"What was surprising about the charm?",
            answer=f"The surprise was that {charm.reveals}. It sounded mysterious at first, but it turned out kind and small.",
        ),
        QAItem(
            question=f"What did {params.name} take home at the end?",
            answer=f"{params.name} went home with {plush.label} and the charm, holding the secret like a little treasure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bazaar?",
            answer="A bazaar is a market where people sell many different things in little stalls.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when the ends of words sound alike, like bell and tell.",
        ),
        QAItem(
            question="Why can surprise make a story exciting?",
            answer="Surprise makes a story exciting because it gives the listener something new to wonder about.",
        ),
        QAItem(
            question="What is plush?",
            answer="Plush is soft fabric that feels cozy, like the stuffing and fur on a stuffed toy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    plush = args.plush or rng.choice(list(PLUSHES))
    charm = args.charm or rng.choice(list(CHARMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    guardian = args.guardian or rng.choice(PARENTS)
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(setting=setting, plush=plush, charm=charm, name=name,
                         gender=gender, guardian=guardian, trait=trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
CURATED = [
    StoryParams(setting="bazaar", plush="lion", charm="ember", name="Mira", gender="girl", guardian="mother", trait="curious"),
    StoryParams(setting="night_bazaar", plush="bird", charm="river", name="Ari", gender="boy", guardian="father", trait="brave"),
    StoryParams(setting="river_bazaar", plush="fox", charm="crown", name="Tala", gender="girl", guardian="aunt", trait="hopeful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic bazaar storyworld with plush toys, rhyme, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plush", choices=PLUSHES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
        print(asp_program("#show mythic_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mythic_story/4."))
        print(f"mythic_story atoms: {sorted(set(asp.atoms(model, 'mythic_story')))}")
        return

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.plush} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
