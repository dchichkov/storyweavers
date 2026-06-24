#!/usr/bin/env python3
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = False
    sacred: bool = False


@dataclass
class StoryParams:
    place: str
    artifact: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


SETTINGS = {
    "grove": Setting(place="the mossy grove", mood="ancient", affords={"approach", "observe", "pick"}),
    "hill": Setting(place="the windy hill", mood="bright", affords={"approach", "observe"}),
    "temple": Setting(place="the hill shrine", mood="solemn", affords={"approach", "observe", "pick"}),
    "spring": Setting(place="the spring meadow", mood="gentle", affords={"approach", "observe", "pick"}),
}

ARTIFACTS = {
    "crocus": Artifact(
        id="crocus",
        label="crocus",
        phrase="a purple crocus with a gold heart",
        location="ground",
        fragile=True,
        sacred=True,
    ),
    "seeds": Artifact(
        id="seeds",
        label="seed-pouch",
        phrase="a tiny pouch of old seeds",
        location="palm",
        fragile=False,
        sacred=False,
    ),
    "stone": Artifact(
        id="stone",
        label="river stone",
        phrase="a smooth river stone",
        location="altar",
        fragile=False,
        sacred=False,
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Iris", "Nora", "Sera", "Ayla"]
BOY_NAMES = ["Eli", "Tomas", "Robin", "Noel", "Arin", "Levi"]
GUIDES = ["grandmother", "father", "mother", "old keeper", "village elder"]
TRAITS = ["curious", "gentle", "bold", "thoughtful", "restless", "kind"]

KNOWLEDGE = {
    "crocus": [
        ("What is a crocus?",
         "A crocus is a small flower that often blooms early, sometimes while the air is still chilly."),
        ("Why do flowers bloom?",
         "Flowers bloom to make seeds and help new plants grow later."),
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the wish to learn, look closer, and ask questions about something new."),
    ],
    "moral": [
        ("What does it mean to keep a promise?",
         "Keeping a promise means doing what you said you would do, because your word matters."),
        ("Why should people be kind?",
         "Kindness helps other people feel safe and cared for, and it makes a community stronger."),
    ],
}


def reasonableness_gate(setting: Setting, artifact: Artifact) -> bool:
    return "observe" in setting.affords and artifact.id == "crocus"


ASP_RULES = r"""
setting(grove). setting(hill). setting(temple). setting(spring).
affords(grove,observe). affords(grove,approach). affords(grove,pick).
affords(hill,observe). affords(hill,approach).
affords(temple,observe). affords(temple,approach). affords(temple,pick).
affords(spring,observe). affords(spring,approach). affords(spring,pick).

artifact(crocus). fragile(crocus). sacred(crocus).
desire_to(keen). virtue(curiosity). virtue(kindness).
can_story(Place, crocus) :- affords(Place, observe), artifact(crocus).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.fragile:
            lines.append(asp.fact("fragile", aid))
        if a.sacred:
            lines.append(asp.fact("sacred", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/2."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = {(p, a) for p in SETTINGS for a in ARTIFACTS if reasonableness_gate(SETTINGS[p], ARTIFACTS[a])}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} cases).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic crocus storyworld driven by curiosity and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
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
    place = args.place or rng.choice(list(SETTINGS))
    artifact = args.artifact or "crocus"
    if not reasonableness_gate(SETTINGS[place], ARTIFACTS[artifact]):
        raise StoryError("This myth only works where the crocus can be found and observed.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(GUIDES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, artifact=artifact, name=name, gender=gender, guide=guide, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    art = ARTIFACTS[params.artifact]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"steps": 0}, memes={"curiosity": 0, "moral_value": 0}))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide, label=f"the {params.guide}", memes={"duty": 0}))
    crocus = world.add(Entity(id="crocus", kind="thing", type="flower", label="crocus", phrase=art.phrase, owner="earth", meters={"bloom": 1}))
    world.facts.update(hero=hero, guide=guide, crocus=crocus, artifact=art, setting=setting, params=params)

    world.say(f"Long ago, in {setting.place}, there lived a {params.trait} child named {params.name}.")
    world.say(f"{params.name} was known for curiosity; whenever a new thing shimmered by the path, {hero.pronoun().capitalize()} wanted to know its story.")
    world.say(f"One dawn, {params.name} found {art.phrase} lifting its face from the earth.")
    hero.memes["curiosity"] += 1
    hero.meters["steps"] += 1
    world.say(f"The little flower seemed almost sacred, and {params.name} leaned closer, listening as if the wind might speak.")
    world.say(f"Then {guide.label} came quietly and said, 'Some beautiful things are not ours to take. We may look, and we may learn, but we must keep faith with what grows here.'")
    guide.memes["duty"] += 1
    hero.memes["moral_value"] += 1
    world.say(f"{params.name} thought about that old rule of the road. Curiosity could pull forward, but moral value asked for care.")
    if params.place in {"grove", "temple"}:
        world.say(f"So {params.name} knelt by the crocus instead of plucking it, and the flower stayed rooted where spring had placed it.")
    else:
        world.say(f"So {params.name} did not tear the crocus free. {hero.pronoun('subject').capitalize()} only watched until the gold heart of the flower brightened in the sun.")
    world.say(f"At last, {params.name} whispered the flower's color and shape into memory, then walked home with a gentler heart than before.")
    world.say(f"That evening, the crocus still stood in {setting.place}, and the child carried a story instead of a stolen bloom.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    art = world.facts["artifact"]
    return [
        f"Write a short myth about a curious child named {p.name} who finds a {art.label} in {world.setting.place}.",
        f"Tell a gentle story where curiosity is strong, but moral value helps {p.name} choose the right thing to do.",
        f"Write an old-fashioned, child-friendly myth about a crocus that is admired, not taken.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who is the myth about?",
            answer=f"It is about a {p.trait} child named {p.name} who is very curious in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} find in {world.setting.place}?",
            answer=f"{p.name} found a crocus, a small flower with a gold heart, growing from the earth.",
        ),
        QAItem(
            question=f"What helped {p.name} choose not to take the flower?",
            answer=f"Curiosity made {p.name} want to look closely, but moral value and the guide's words helped {p.name} keep the crocus where it was.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["crocus", "curiosity", "moral"]:
        for q, a in KNOWLEDGE[key]:
            out.append(QAItem(question=q, answer=a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


CURATED = [
    StoryParams(place="grove", artifact="crocus", name="Mira", gender="girl", guide="grandmother", trait="curious"),
    StoryParams(place="spring", artifact="crocus", name="Eli", gender="boy", guide="village elder", trait="thoughtful"),
    StoryParams(place="temple", artifact="crocus", name="Iris", gender="girl", guide="old keeper", trait="gentle"),
]


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
        print(asp_program("#show can_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid myth settings:")
        for place, art in vals:
            print(f"  {place}: {art}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
