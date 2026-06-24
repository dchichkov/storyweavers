#!/usr/bin/env python3
"""
A small mythic shopping-mall storyworld about a magical bulb that can interfere
with the bright order of the mall, and the gentle fix that restores harmony.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the shopping mall"


@dataclass
class Bulb:
    label: str
    phrase: str
    glow: str
    interference: str
    shelter: str
    calm: str


@dataclass
class Ward:
    id: str
    label: str
    covers: set[str]
    dims: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    bulb: str
    name: str
    role: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.fault: bool = False

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


BULBS = {
    "moonbulb": Bulb(
        label="moon bulb",
        phrase="a small moon bulb wrapped in silver thread",
        glow="its pale light spilled like milk across the floor",
        interference="it interfered with the mall's signs and made them blink like startled stars",
        shelter="a velvet pouch",
        calm="it slept quietly inside the pouch",
    ),
    "sunbulb": Bulb(
        label="sun bulb",
        phrase="a warm sun bulb with a round golden heart",
        glow="its golden glow danced on the shiny tiles",
        interference="it interfered with the escalator lights and made them flicker",
        shelter="a woven cloth bag",
        calm="it rested softly inside the cloth bag",
    ),
}

WARDS = {
    "cloth": Ward(
        id="cloth",
        label="a soft cloth wrap",
        covers={"light"},
        dims={"bright"},
        prep="wrap the bulb in a soft cloth wrap",
        tail="carefully wrapped the bulb and carried it like a tiny treasure",
    ),
    "pouch": Ward(
        id="pouch",
        label="a velvet pouch",
        covers={"light"},
        dims={"bright", "glow"},
        prep="place the bulb in a velvet pouch",
        tail="lifted the pouch closed and held it close",
    ),
}

ROLES = {
    "child": "child",
    "sprite": "sprite",
    "seeker": "seeker",
    "prince": "prince",
    "princess": "princess",
}

GUIDES = {
    "aunt": "aunt",
    "elder": "elder",
    "mother": "mother",
    "father": "father",
    "guardian": "guardian",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic mall storyworld: bulb, interfere, and harmony.")
    ap.add_argument("--place", choices=["shopping mall"], default="shopping mall")
    ap.add_argument("--bulb", choices=list(BULBS), default=None)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=list(ROLES), default=None)
    ap.add_argument("--guide", choices=list(GUIDES), default=None)
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
    bulb = args.bulb or rng.choice(list(BULBS))
    role = args.role or rng.choice(list(ROLES))
    guide = args.guide or rng.choice(list(GUIDES))
    name = args.name or rng.choice(["Lina", "Mara", "Kian", "Sora", "Ari", "Nico"])
    return StoryParams(place="shopping mall", bulb=bulb, name=name, role=role, guide=guide)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "shopping mall":
        raise StoryError("This world only tells stories in a shopping mall.")
    if params.bulb not in BULBS:
        raise StoryError("Unknown bulb.")
    if params.role not in ROLES:
        raise StoryError("Unknown role.")
    if params.guide not in GUIDES:
        raise StoryError("Unknown guide.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(Setting(place=params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, traits=["small", "wonder-struck"]))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=f"the {params.guide}"))
    bulb = world.add(Entity(
        id="Bulb",
        type="thing",
        label=BULBS[params.bulb].label,
        phrase=BULBS[params.bulb].phrase,
        owner=hero.id,
    ))
    ward = world.add(Entity(
        id="Ward",
        type="thing",
        label=WARDS["pouch"].label,
        phrase="a velvet pouch for holy things",
        owner=guide.id,
        caretaker=guide.id,
        plural=WARDS["pouch"].plural,
    ))

    hero.memes["wonder"] = 1
    bulb.meters["glow"] = 1
    world.say(
        f"In {world.setting.place}, {hero.id} carried {bulb.phrase} as if it were a gift from the old sky."
    )
    world.say(
        f"{BULBS[params.bulb].glow.capitalize()}, and {hero.pronoun('possessive')} heart grew bright with wonder."
    )

    world.para()
    world.say(
        f"Then {hero.id} lifted the bulb a little too high, and {BULBS[params.bulb].interference}."
    )
    hero.meters["interfere"] = 1
    world.fault = True
    hero.memes["trouble"] = 1
    world.say(
        f"The shining crowd paused, and the mall seemed to hold its breath."
    )

    world.para()
    world.say(
        f"The {params.guide} did not scold {hero.id}. Instead, {guide.pronoun().capitalize()} smiled and said, "
        f"\"A bright thing can be powerful, but power needs a gentle hand.\""
    )
    world.say(
        f"{WARDS['pouch'].prep.capitalize()}, {guide.pronoun('subject')} said, and the two of them listened to the quiet."
    )
    bulb.worn_by = None
    world.say(
        f"Together they {WARDS['pouch'].tail}. Soon {BULBS[params.bulb].calm}, and the signs shone true again."
    )
    hero.memes["peace"] = 1
    hero.memes["wonder"] = 2
    hero.meters["interfere"] = 0
    world.facts.update(hero=hero, guide=guide, bulb=bulb, ward=ward, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    params: StoryParams = f["params"]
    return [
        f'Write a short myth-like story for a young child set in a {params.place} about a magical bulb that can interfere with the bright order of the world.',
        f'Tell a gentle legend about {hero.id}, a {params.role}, who carries a bulb and learns how to keep its magic from causing trouble in the mall.',
        f'Write a simple story using the words "bulb" and "interfere" that ends with a wise helper restoring harmony.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    bulb: Entity = f["bulb"]
    params: StoryParams = f["params"]
    q = [
        QAItem(
            question=f"Who is the story about in the shopping mall?",
            answer=f"It is about {hero.id}, a little {hero.type}, who carried {bulb.phrase} through the shopping mall.",
        ),
        QAItem(
            question=f"What happened when {hero.id} lifted the bulb too high?",
            answer=f"The bulb began to interfere with the mall's bright order, and the signs started to blink and flicker.",
        ),
        QAItem(
            question=f"Who helped {hero.id} keep the bulb calm?",
            answer=f"The {params.guide} helped by choosing a gentle way to hold and cover the bulb.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the bulb wrapped safely away, the mall shining true again, and {hero.id} feeling peaceful.",
        ),
    ]
    return q


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shopping mall?",
            answer="A shopping mall is a big indoor place with many stores, bright lights, and walking paths for people to visit.",
        ),
        QAItem(
            question="What does interfere mean?",
            answer="To interfere means to get in the way of something and make it work badly or feel mixed up.",
        ),
        QAItem(
            question="What is a bulb?",
            answer="A bulb is a round thing that can glow with light, like a lamp bulb or a magical glowing bulb in a story.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "character":
            bits.append(f"role={e.type}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "shopping_mall"),
        asp.fact("bulb", "moonbulb"),
        asp.fact("bulb", "sunbulb"),
        asp.fact("can_interfere", "moonbulb"),
        asp.fact("can_interfere", "sunbulb"),
        asp.fact("ward", "cloth"),
        asp.fact("ward", "pouch"),
        asp.fact("dims", "cloth", "bright"),
        asp.fact("dims", "pouch", "bright"),
        asp.fact("dims", "pouch", "glow"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
good_story(B) :- bulb(B), can_interfere(B), ward(W), dims(W, bright).
#show good_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/1."))
    atoms = asp.atoms(model, "good_story")
    if atoms:
        print("OK: ASP rules recognize a bulb story with a gentle ward.")
        return 0
    print("Mismatch in ASP verification.")
    return 1


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
        for i, item in enumerate(sample.prompts, 1):
            pass
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="shopping mall", bulb="moonbulb", name="Lina", role="child", guide="aunt"),
    StoryParams(place="shopping mall", bulb="sunbulb", name="Mara", role="sprite", guide="elder"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
