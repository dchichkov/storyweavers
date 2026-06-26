#!/usr/bin/env python3
"""
A standalone storyworld for a tiny comedy about photography, a twit, and an aster.

The premise:
- A child photographer wants a picture of a prized aster.
- A rude little twit keeps interrupting the shot.
- Kindness and a small transformation turn the trouble into a silly helper.

The world model tracks:
- physical meters: ready, tangled, bright, muddy, moved, snapped
- emotional memes: joy, annoyance, worry, kindness, shame, pride, laughter

The story is generated from a simulated causal world so the prose reflects
what changed, not a fixed template with swapped nouns.
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

ENTITY_HUMAN = "human"
ENTITY_ANIMAL = "animal"
ENTITY_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str = ENTITY_OBJECT
    type: str = ENTITY_OBJECT
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == ENTITY_HUMAN:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == ENTITY_ANIMAL:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    twit: str
    aster: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": "the garden",
    "greenhouse": "the greenhouse",
    "park": "the park",
    "backyard": "the backyard",
}

HERO_NAMES = ["Mina", "Lola", "Nia", "Poppy", "Tia", "June", "Ivy"]
TWIT_NAMES = ["Tib", "Nip", "Zip", "Murm", "Wren"]
ASTER_NAMES = ["aster", "purple aster", "starry aster", "blue aster"]

ASP_RULES = r"""
% A shot is spoiled when the twit is meddling and the aster is not protected.
spoiled(S) :- setting(S), meddles(twit), near(twit, aster), no_protection(aster).

% Kindness can transform the twit into a helper.
helpful(twit) :- kind_action(hero), transformed(twit).

% A reasonable story is one where the twit can be soothed and the aster can still be photographed.
valid_story(S) :- setting(S), spoiled(S), transformed(twit).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("meddles", "twit"))
    lines.append(asp.fact("near", "twit", "aster"))
    lines.append(asp.fact("no_protection", "aster"))
    lines.append(asp.fact("kind_action", "hero"))
    lines.append(asp.fact("transformed", "twit"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(SETTINGS.keys())
    cl = set(s for (s,) in asp_valid())
    if py == cl:
        print(f"OK: ASP model covers {len(py)} story settings.")
        return 0
    print("MISMATCH between Python and ASP setting coverage.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Photography, twit, and aster comedy storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--twit")
    ap.add_argument("--aster")
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
    hero = args.hero or rng.choice(HERO_NAMES)
    twit = args.twit or rng.choice(TWIT_NAMES)
    aster = args.aster or rng.choice(ASTER_NAMES)
    return StoryParams(setting=setting, hero=hero, twit=twit, aster=aster)


def _should_reject(params: StoryParams) -> Optional[str]:
    if params.hero.lower() == params.twit.lower():
        return "The hero and the twit need different names so the comedy can clearly land."
    return None


def build_world(params: StoryParams) -> World:
    err = _should_reject(params)
    if err:
        raise StoryError(err)

    world = World(SETTINGS[params.setting])

    hero = world.add(Entity(
        id="hero",
        kind=ENTITY_HUMAN,
        type="child",
        label=params.hero,
        phrase=f"the child photographer {params.hero}",
        memes={"joy": 1.0, "kindness": 0.0, "worry": 0.0, "laughter": 0.0},
    ))
    twit = world.add(Entity(
        id="twit",
        kind=ENTITY_ANIMAL,
        type="twit",
        label=params.twit,
        phrase=f"a little twit named {params.twit}",
        meters={"mess": 0.0, "moved": 0.0, "bright": 0.0},
        memes={"annoyance": 1.0, "shame": 0.0, "pride": 0.0},
        location="bushes",
    ))
    aster = world.add(Entity(
        id="aster",
        kind=ENTITY_OBJECT,
        type="flower",
        label=params.aster,
        phrase=f"a bright {params.aster}",
        meters={"bright": 1.0, "ready": 1.0, "snapped": 0.0},
        location="sunny patch",
    ))
    camera = world.add(Entity(
        id="camera",
        kind=ENTITY_OBJECT,
        type="camera",
        label="camera",
        phrase="a small camera",
        owner=hero.id,
        meters={"ready": 1.0},
    ))

    world.facts.update(params=params, hero=hero, twit=twit, aster=aster, camera=camera)
    return world


def predict_shot(world: World) -> dict:
    sim = world.copy()
    twit = sim.get("twit")
    aster = sim.get("aster")
    spoiled = twit.location == "beside the aster" and twit.meters.get("mess", 0.0) >= 1.0
    if spoiled:
        aster.meters["ready"] = 0.0
    return {"spoiled": spoiled, "bright": aster.meters.get("bright", 0.0)}


def act_setup(world: World) -> None:
    hero = world.get("hero")
    aster = world.get("aster")
    world.say(
        f"{hero.label} loved photography and carried a small camera everywhere."
    )
    world.say(
        f"One day {hero.pronoun('subject')} saw {aster.phrase} in {world.setting} and wanted a perfect picture."
    )


def act_twit_interrupts(world: World) -> None:
    twit = world.get("twit")
    aster = world.get("aster")
    hero = world.get("hero")
    twit.location = "beside the aster"
    twit.meters["mess"] = 1.0
    world.say(
        f"Then {twit.label} bounced into the frame with a silly little twit-hop and made faces at the camera."
    )
    world.say(
        f"{hero.label} frowned, because the twit was blocking {hero.pronoun('possessive')} view of {aster.label}."
    )


def act_kindness(world: World) -> None:
    hero = world.get("hero")
    twit = world.get("twit")
    aster = world.get("aster")
    hero.memes["kindness"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"Instead of shooing {twit.label} away, {hero.label} knelt down and spoke kindly."
    )
    world.say(
        f'{hero.label} said, "You can help. Hold still like a tiny star, and I will take your picture too."'
    )
    if predict_shot(world)["spoiled"]:
        world.say(
            f"That gentle idea changed the whole scene, because the twit stopped bouncing and looked very proud."
        )


def transform_twit(world: World) -> None:
    twit = world.get("twit")
    hero = world.get("hero")
    twit.memes["shame"] = 0.0
    twit.memes["pride"] = 1.0
    twit.meters["mess"] = 0.0
    twit.location = "beside the aster"
    world.say(
        f"At the sound of the kind words, {twit.label} transformed from a rude little twit into a helpful pose-model."
    )
    world.say(
        f"{twit.label} stood very still, puffed up with pride, and even pointed one wing toward {world.get('aster').label}."
    )


def act_shot(world: World) -> None:
    hero = world.get("hero")
    twit = world.get("twit")
    aster = world.get("aster")
    camera = world.get("camera")
    aster.meters["snapped"] = 1.0
    aster.meters["ready"] = 1.0
    hero.memes["joy"] = 2.0
    hero.memes["laughter"] = 1.0
    world.say(
        f"{hero.label} clicked the camera, and the picture caught both {aster.label} and the newly helpful twit together."
    )
    world.say(
        f"The result was delightfully funny: {twit.label} looked grand, {aster.label} looked bright, and the camera did its job."
    )
    world.say(
        f"{hero.label} laughed so hard {hero.pronoun('subject')} had to wipe a tear from {hero.pronoun('possessive')} cheek."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_setup(world)
    world.para()
    act_twit_interrupts(world)
    act_kindness(world)
    transform_twit(world)
    world.para()
    act_shot(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short comedy story about photography, a twit, and an aster in {world.setting}.',
        f"Tell a gentle story where {p.hero} uses kindness to transform a rude twit into a helpful friend.",
        f"Write a funny child-friendly story that ends with a bright aster and a silly photo.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.get("hero")
    twit = world.get("twit")
    aster = world.get("aster")
    return [
        QAItem(
            question=f"Who wanted to take the picture in {world.setting}?",
            answer=f"{hero.label} wanted to take the picture, because {hero.pronoun('subject')} loved photography.",
        ),
        QAItem(
            question=f"What was the twit doing before kindness changed the scene?",
            answer=f"{twit.label} was bouncing into the frame and blocking the view of {aster.label}.",
        ),
        QAItem(
            question=f"How did {hero.label} respond to the rude twit?",
            answer=f"{hero.label} responded with kindness, spoke gently, and offered {twit.label} a chance to help.",
        ),
        QAItem(
            question=f"What changed after the kindness?",
            answer=f"The twit transformed into a helpful pose-model, and the camera captured a funny picture of {aster.label} and the twit together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} laughing, the {aster.label} looking bright, and the twit proudly posing instead of misbehaving.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is photography?",
            answer="Photography is the art of making pictures with a camera.",
        ),
        QAItem(
            question="What is an aster?",
            answer="An aster is a flower with petals that often looks like a little star.",
        ),
        QAItem(
            question="What does kindness do?",
            answer="Kindness helps people and creatures feel safe, calm, and willing to cooperate.",
        ),
        QAItem(
            question="What is a twit in this story world?",
            answer="A twit is a silly, rude little character who can become helpful after being treated kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.location:
            bits.append(f"location={ent.location}")
        lines.append(f"{ent.id}: {ent.label} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="garden", hero="Mina", twit="Tib", aster="purple aster"),
    StoryParams(setting="park", hero="Lola", twit="Zip", aster="blue aster"),
    StoryParams(setting="backyard", hero="June", twit="Nip", aster="starry aster"),
    StoryParams(setting="greenhouse", hero="Ivy", twit="Wren", aster="aster"),
]


def resolve_valid(params: StoryParams) -> None:
    if params.hero.lower() == params.twit.lower():
        raise StoryError("The hero and the twit need different names.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible ASP story settings:")
        for (sid,) in asp_valid():
            print(f"  {sid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            resolve_valid(p)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            try:
                resolve_valid(params)
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
            header = f"### {p.hero} / {p.twit} / {p.aster} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
