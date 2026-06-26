#!/usr/bin/env python3
"""
storyworlds/worlds/orbit_transformation_moral_value_curiosity_myth.py
====================================================================

A tiny mythic storyworld about a curious wanderer, a bright object in orbit,
and a transformation that teaches a moral value.

Seed tale:
---
Long ago, in a sky older than names, a small curious fox-child named Nia lived
on the edge of a moonlit grove. Every night she watched a silver lantern circle
the mountain like a faithful star. The village elders said the lantern had once
been a selfish ember, but it learned to share its light after a great silence.
Nia wanted to know the lantern's secret, so she climbed the path and asked the
moon why it never fell.

The moon answered only with a riddle: "What changes shape without breaking its
promise?" Nia waited, listened, and saw that the lantern was not fixed at all.
It was turning, shining, and becoming something gentler in its orbit. When dawn
came, Nia carried the riddle home and shared her bread with the youngest child.
Then the sky seemed to circle a little closer, as if kindness itself had found
its place.

Core causal model:
---
    curiosity about a sacred thing -> approach + questions + discovery
    discovery of a true pattern     -> wonder + respect
    selfishness or hoarding         -> shame + imbalance
    chosen sharing / honesty        -> moral value rises, tension resolves
    transformation in orbit         -> object changes state while remaining in
                                       a stable path; the change is visible

Narrative instruments:
---
    orbit                 -> a visible sky-path around a host
    transformation        -> an entity changes its form/state
    moral value           -> the story rewards generosity, honesty, patience
    curiosity             -> the hero asks, watches, and learns
    myth style            -> ancient, symbolic, gentle, concrete
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    orbiting: Optional[str] = None
    transformed: bool = False
    plural: bool = False
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
class Realm:
    sky: str = "the old sky"
    grove: str = "the moonlit grove"
    host: str = "moon"
    old_path: str = "a silver orbit"
    place_name: str = "the mountain"
    mythic: bool = True


@dataclass
class Transformation:
    id: str
    before: str
    after: str
    trigger: str
    visible_change: str
    moral_gain: str


@dataclass
class World:
    realm: Realm
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        return World(self.realm, copy.deepcopy(self.entities), [[]], set(self.fired), copy.deepcopy(self.facts))


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    host: str
    orbiting: str
    transformation: str
    moral: str
    curiosity: str
    seed: Optional[int] = None


HEROES = [
    ("Nia", "girl"),
    ("Ivo", "boy"),
    ("Lina", "girl"),
    ("Taro", "boy"),
    ("Sera", "girl"),
]

HOSTS = {
    "moon": Realm(host="moon", sky="the old sky", grove="the moonlit grove", old_path="a silver orbit", place_name="the mountain"),
    "star": Realm(host="star", sky="the deep sky", grove="the dark field", old_path="a bright orbit", place_name="the hill"),
    "sun": Realm(host="sun", sky="the gold sky", grove="the dawn meadow", old_path="a wide orbit", place_name="the world"),
}

ORBITING = {
    "lantern": "silver lantern",
    "comet": "small comet",
    "stone": "glowing stone",
    "spindle": "fire spindle",
}

TRANSFORMATIONS = {
    "ember_to_lantern": Transformation(
        id="ember_to_lantern",
        before="a selfish ember",
        after="a gentle lantern",
        trigger="shared warmth",
        visible_change="its red core turns bright and steady",
        moral_gain="sharing",
    ),
    "seed_to_tree": Transformation(
        id="seed_to_tree",
        before="a sleeping seed",
        after="a young tree",
        trigger="patient care",
        visible_change="a green shoot rises from the earth",
        moral_gain="patience",
    ),
    "stone_to_swan": Transformation(
        id="stone_to_swan",
        before="a cold stone",
        after="a white swan",
        trigger="a truthful name",
        visible_change="its shell cracks and feathers shine through",
        moral_gain="honesty",
    ),
}

MORALS = {
    "sharing": "share what you have",
    "patience": "wait kindly for what grows slowly",
    "honesty": "speak the truth even when it is small",
}

CURIOSITIES = {
    "secret": "why the sky-thing kept circling and never fell",
    "name": "what the shining thing was called",
    "path": "how the bright path stayed in the same ring",
}

ASP_RULES = r"""
curious(H) :- curiosity(H).
approaches(H, O) :- curious(H), wonders_about(H, O).
discovers(H, O) :- approaches(H, O), truth_visible(O).
transforms(O) :- before(O, _), after(O, _), trigger_met(O).
moral_rises(H) :- shares(H) ; honest(H) ; patient(H).
valid_story(H, O, T, M, C) :- curious(H), orbiting(O), transforms(T), moral(M), curiosity(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for oid in ORBITING:
        lines.append(asp.fact("orbiting", oid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    for cid in CURIOSITIES:
        lines.append(asp.fact("curiosity", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def choose(rng: random.Random, seq):
    return rng.choice(list(seq))


def build_world(params: StoryParams) -> World:
    realm = HOSTS[params.host]
    world = World(realm)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    orb = world.add(Entity(
        id="orb",
        kind="thing",
        type=params.orbiting,
        label=params.orbiting,
        phrase=ORBITING[params.orbiting],
        orbiting=params.host,
    ))
    trans = TRANSFORMATIONS[params.transformation]
    world.facts.update(hero=hero, orb=orb, transformation=trans, moral=params.moral, curiosity=params.curiosity)
    return world


def simulate(world: World) -> World:
    hero: Entity = world.facts["hero"]
    orb: Entity = world.facts["orb"]
    trans: Transformation = world.facts["transformation"]
    moral = world.facts["moral"]
    curiosity = world.facts["curiosity"]

    hero.memes["curiosity"] = 1.0
    world.say(f"Long ago, in {world.realm.sky}, there lived {hero.id}, who was young and full of curiosity.")
    world.say(f"Each night {hero.id} watched {orb.phrase} move in {world.realm.old_path} around {world.realm.host}.")
    world.say(f"{hero.id} wanted to know {curiosity}, so {hero.pronoun().capitalize()} climbed toward {world.realm.place_name} and asked old questions to the wind.")

    world.para()
    world.say(f"The moon-like host did not answer at once. Instead, the light showed a secret: {orb.phrase} was not only circling, it was changing.")
    world.say(f"At the heart of it, {trans.before} was becoming {trans.after}, and {trans.visible_change}.")
    hero.memes["wonder"] = 1.0
    hero.memes["respect"] = 1.0

    world.para()
    world.say(f"{hero.id} saw that every true thing has a path, and every path has a lesson.")
    if moral == "sharing":
        world.say(f"So {hero.id} carried bread back to the grove and gave it to a hungry child.")
    elif moral == "patience":
        world.say(f"So {hero.id} watered the ground and waited, day after day, without complaint.")
    else:
        world.say(f"So {hero.id} told the villagers the whole truth, even though the truth was small.")

    hero.memes[moral] = 1.0
    orb.transformed = True
    orb.label = f"the {trans.after}"
    orb.phrase = trans.after
    world.facts["resolved"] = True

    world.say(f"Then the sky seemed kinder, as if it had remembered {MORALS[moral]}.")
    world.say(f"And the bright thing kept its orbit, but it was no longer the same thing that had begun the tale.")
    return world


def tell(params: StoryParams) -> World:
    return simulate(build_world(params))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trans = f["transformation"]
    return [
        f"Write a mythic story for a child named {hero.id} who notices an object in orbit and asks what it means.",
        f"Tell a gentle myth about {hero.id}, a changing sky-light, and a lesson about {MORALS[world.facts['moral']]}.",
        f"Write a short old-sounding story in which {trans.before} becomes {trans.after} while keeping its orbit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    orb = f["orb"]
    trans = f["transformation"]
    moral = f["moral"]
    curiosity = f["curiosity"]
    return [
        QAItem(
            question=f"What made {hero.id} climb toward the mountain and ask questions?",
            answer=f"{hero.id} was full of curiosity and wanted to know {curiosity}. That is why {hero.pronoun()} went to watch the bright thing in orbit.",
        ),
        QAItem(
            question=f"What was changing about {orb.phrase} in the story?",
            answer=f"It was transforming from {trans.before} into {trans.after}. The change could be seen because {trans.visible_change}.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to {MORALS[moral]}. The story ends with that value making the sky feel kinder.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orbit?",
            answer="An orbit is a path one thing follows around another thing in a steady circle or curve.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more by looking, asking, and wondering.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or state.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of acting, like sharing, honesty, or patience.",
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
        bits = []
        if e.orbiting:
            bits.append(f"orbiting={e.orbiting}")
        if e.transformed:
            bits.append("transformed=True")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for hname, htype in HEROES:
        for host in HOSTS:
            for orb in ORBITING:
                for tr in TRANSFORMATIONS:
                    for moral in MORALS:
                        for cur in CURIOSITIES:
                            out.append((hname, host, orb, tr, moral, cur))
    return out


def explain_rejection() -> str:
    return "(No story: the requested myth must include a clear curiosity, an orbiting thing, a transformation, and a moral lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic orbit story world with curiosity, transformation, and moral value."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--host", choices=sorted(HOSTS))
    ap.add_argument("--orbiting", choices=sorted(ORBITING))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--moral", choices=sorted(MORALS))
    ap.add_argument("--curiosity", choices=sorted(CURIOSITIES))
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
    host = args.host or choose(rng, HOSTS)
    orbiting = args.orbiting or choose(rng, ORBITING)
    transformation = args.transformation or choose(rng, TRANSFORMATIONS)
    moral = args.moral or choose(rng, MORALS)
    curiosity = args.curiosity or choose(rng, CURIOSITIES)
    gender = args.gender or choose(rng, ["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = choose(rng, [n for n, g in HEROES if g == gender])
    return StoryParams(
        hero_name=name,
        hero_type=gender,
        host=host,
        orbiting=orbiting,
        transformation=transformation,
        moral=moral,
        curiosity=curiosity,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((h, o, t, m, c) for h, o, t, m, c in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for row in combos[:200]:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, (name, gender) in enumerate(HEROES):
            params = StoryParams(
                hero_name=name,
                hero_type=gender,
                host=list(HOSTS)[i % len(HOSTS)],
                orbiting=list(ORBITING)[i % len(ORBITING)],
                transformation=list(TRANSFORMATIONS)[i % len(TRANSFORMATIONS)],
                moral=list(MORALS)[i % len(MORALS)],
                curiosity=list(CURIOSITIES)[i % len(CURIOSITIES)],
            )
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
