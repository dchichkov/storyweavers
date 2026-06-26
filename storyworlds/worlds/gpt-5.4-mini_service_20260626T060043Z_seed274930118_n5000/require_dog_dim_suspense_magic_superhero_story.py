#!/usr/bin/env python3
"""
Storyworld: require_dog_dim_suspense_magic_superhero_story
===========================================================

A small superhero-style storyworld with suspense and magic:
a young hero, a loyal dog, a strange dog-dim doorway, and a
problem that can only be solved with a sensible magical choice.

Seed premise:
---
A little hero has a brave dog and a magic gadget. When a shadowy
problem appears, the hero wants to rush in alone, but the dog and
the gadget reveal a safer, kinder path through the dog-dim.
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
    companion: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    magical: bool = False
    dimensions: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "heroine"}
        male = {"boy", "man", "father", "dad", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city rooftops"
    mood: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class HeroSpec:
    name: str
    type: str
    trait: str


@dataclass
class DogSpec:
    name: str
    breed: str
    trait: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    reveals: set[str] = field(default_factory=set)
    can_open: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "rooftops": Setting(place="the city rooftops", mood="moonlit", affords={"run", "glide", "search"}),
    "museum": Setting(place="the museum hall", mood="quiet", affords={"search", "hide", "open"}),
    "alley": Setting(place="the lantern alley", mood="rainy", affords={"run", "search", "hide"}),
}

HEROES = [
    HeroSpec(name="Nova", type="girl", trait="brave"),
    HeroSpec(name="Bolt", type="boy", trait="quick"),
    HeroSpec(name="Mira", type="girl", trait="sharp-eyed"),
    HeroSpec(name="Jett", type="boy", trait="bold"),
]

DOGS = [
    DogSpec(name="Pip", breed="small dog", trait="loyal"),
    DogSpec(name="Comet", breed="dog", trait="bouncy"),
    DogSpec(name="Scout", breed="dog", trait="clever"),
]

ARTIFACTS = {
    "mask": Artifact(
        id="mask",
        label="magic mask",
        phrase="a magic mask with a silver star",
        protects={"fear"},
        reveals={"shadow"},
        can_open={"dog_dim"},
    ),
    "cape": Artifact(
        id="cape",
        label="magic cape",
        phrase="a magic cape stitched with moon thread",
        protects={"wind"},
        reveals={"trail"},
        can_open={"dog_dim"},
    ),
    "lantern": Artifact(
        id="lantern",
        label="spell lantern",
        phrase="a spell lantern that glowed blue",
        protects={"dark"},
        reveals={"hidden"},
        can_open={"dog_dim"},
    ),
}

THREATS = {
    "shadow_thief": "a sneaky shadow thief",
    "fog_wall": "a thick fog wall",
    "lost_gate": "a locked gate of light",
}

DIMENSIONS = {
    "city": "the city",
    "dog_dim": "the dog-dim",
}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    dog: str
    artifact: str
    threat: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the chosen setting affords suspenseful movement.
valid_story(P, H, D, A, T) :- place(P), hero(H), dog(D), artifact(A), threat(T), afford(P, search).

% The dog-dim is only sensible if the artifact can open it.
valid_story(P, H, D, A, T) :- place(P), hero(H), dog(D), artifact(A), threat(T), opens(A, dog_dim).

% A threat must be something the magic item can reveal or push back.
valid_story(P, H, D, A, T) :- place(P), hero(H), dog(D), artifact(A), threat(T), useful(A, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for hid in sorted(HEROES, key=lambda x: x.name):
        lines.append(asp.fact("hero", hid.name))
    for did in sorted(DOGS, key=lambda x: x.name):
        lines.append(asp.fact("dog", did.name))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        for x in sorted(a.can_open):
            lines.append(asp.fact("opens", aid, x))
        for x in sorted(a.reveals):
            lines.append(asp.fact("useful", aid, x))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    valid = set(valid_stories())
    clingo = set(asp_valid_stories())
    if valid == clingo:
        print(f"OK: clingo gate matches python gate ({len(valid)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if valid - clingo:
        print("  only in python:", sorted(valid - clingo))
    if clingo - valid:
        print("  only in clingo:", sorted(clingo - valid))
    return 1


def valid_stories() -> list[tuple]:
    out = []
    for p in SETTINGS:
        for h in HEROES:
            for d in DOGS:
                for a in ARTIFACTS:
                    for t in THREATS:
                        if can_story(p, h.name, d.name, a, t):
                            out.append((p, h.name, d.name, a, t))
    return out


def can_story(place: str, hero: str, dog: str, artifact: str, threat: str) -> bool:
    if place not in SETTINGS or artifact not in ARTIFACTS or threat not in THREATS:
        return False
    art = ARTIFACTS[artifact]
    return ("search" in SETTINGS[place].affords) and ("dog_dim" in art.can_open) and bool(art.reveals)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def choose_artifact(hero: Entity, dog: Entity, artifact: Entity) -> str:
    return (
        f"{hero.id} wore {hero.pronoun('possessive')} {artifact.label}, "
        f"and {dog.id} trotted close at {hero.pronoun('possessive')} side."
    )


def predict(world: World, hero: Entity, artifact: Entity, threat: str) -> dict[str, bool]:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] = 1
    sim.get(artifact.id).memes["glow"] = 1
    return {"revealed": threat in artifact.meters.get("reveals", set())}


def tell(hero_spec: HeroSpec, dog_spec: DogSpec, artifact_key: str, threat_key: str, place: str) -> World:
    setting = SETTINGS[place]
    world = World(setting)
    hero = world.add(Entity(id=hero_spec.name, kind="character", type=hero_spec.type, traits=[hero_spec.trait, "heroic"]))
    dog = world.add(Entity(id=dog_spec.name, kind="character", type="dog", traits=[dog_spec.trait, "loyal"]))
    artifact = ARTIFACTS[artifact_key]
    item = world.add(Entity(
        id=artifact.id,
        type="thing",
        label=artifact.label,
        phrase=artifact.phrase,
        owner=hero.id,
        magical=True,
        dimensions={"dog_dim"},
    ))

    threat_text = THREATS[threat_key]

    hero.memes["resolve"] = 1
    dog.memes["trust"] = 1
    item.meters["glow"] = 1

    world.say(f"On a {setting.mood} night, {hero.id} and {dog.id} watched {setting.place} from above.")
    world.say(f"{hero.id} was a {hero_spec.trait} young hero, and {dog.id} was a {dog_spec.trait} helper who never barked at the wrong time.")
    world.say(f"Then {threat_text} slipped between the lights, and the whole street felt suddenly smaller.")

    world.para()
    hero.memes["suspense"] = 1
    world.say(f"{hero.id} wanted to rush in alone, but {dog.id} pressed close and nudged {hero.pronoun('possessive')} hand.")
    world.say(f'At the edge of a hidden stair, {hero.id} held up {hero.pronoun("possessive")} {artifact.label} and whispered, "I require the dog-dim."')
    world.say(f"The {artifact.label} shivered, and a blue doorway opened like a tiny star-shaped door for a brave pause.")

    world.para()
    hero.memes["fear"] = 1
    dog.meters["scent"] = 1
    world.say(f"{dog.id} led the way into the dog-dim, where everything looked a little sideways and much more magic than before.")
    if artifact.can_open and "dog_dim" in artifact.can_open:
        world.say(f"The {artifact.label} lit the path, revealing the hidden shape of {threat_text}.")
    world.say(f"Together they found that {threat_text} was not a monster at all, but a drifting shadow snagged on a broken sign.")

    world.para()
    hero.memes["joy"] = 1
    hero.memes["fear"] = 0
    world.say(f"{hero.id} used the {artifact.label} to shine the shadow loose, and {dog.id} barked once, just enough to scare the dark away.")
    world.say(f"The sign clicked back into place, the doorway faded, and {setting.place} grew bright again.")
    world.say(f"In the last quiet moment, {hero.id} smiled at {dog.id}, and the two of them stood like a tiny team that knew exactly how to be brave together.")

    world.facts = {
        "hero": hero,
        "dog": dog,
        "artifact": item,
        "threat_key": threat_key,
        "threat_text": threat_text,
        "place": place,
        "setting": setting,
        "artifact_key": artifact_key,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    dog: Entity = f["dog"]
    artifact: Entity = f["artifact"]
    return [
        f'Write a short superhero story for children that includes the words "require" and "dog-dim".',
        f"Tell a suspenseful magic story where {hero.id} and {dog.id} need {artifact.label} to cross the dog-dim and solve a problem.",
        f"Write a simple hero tale with a loyal dog, a glowing magical object, and a suspenseful hidden threat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    dog: Entity = f["dog"]
    artifact: Entity = f["artifact"]
    threat_text: str = f["threat_text"]
    place: str = f["place"]
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {hero.id}, a {hero.traits[0]} hero, and {dog.id}, a {dog.traits[0]} dog who stayed close through the suspense.",
        ),
        QAItem(
            question=f"What did {hero.id} require to open the dog-dim?",
            answer=f"{hero.id} required {artifact.phrase} to open the dog-dim and follow the trail safely.",
        ),
        QAItem(
            question=f"What was the problem the team had to solve?",
            answer=f"They had to solve the problem of {threat_text}, which turned out to be a broken, drifting shadow instead of a true monster.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {dog.id} standing together after the shadow was set free and {place} became bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dog?",
            answer="A dog is a loyal animal that can help people by staying close, listening, and following a scent.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special power in a story that can glow, open doors, reveal hidden things, or change what is possible.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next when something scary or important is not finished yet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.magical:
            bits.append("magical=True")
        if e.dimensions:
            bits.append(f"dimensions={sorted(e.dimensions)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation / CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="rooftops", hero="Nova", dog="Pip", artifact="mask", threat="shadow_thief"),
    StoryParams(place="museum", hero="Mira", dog="Scout", artifact="lantern", threat="lost_gate"),
    StoryParams(place="alley", hero="Bolt", dog="Comet", artifact="cape", threat="fog_wall"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with suspense, magic, and the dog-dim.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=[h.name for h in HEROES])
    ap.add_argument("--dog", choices=[d.name for d in DOGS])
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--threat", choices=THREATS)
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
    combos = valid_stories()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hero:
        combos = [c for c in combos if c[1] == args.hero]
    if args.dog:
        combos = [c for c in combos if c[2] == args.dog]
    if args.artifact:
        combos = [c for c in combos if c[3] == args.artifact]
    if args.threat:
        combos = [c for c in combos if c[4] == args.threat]
    if not combos:
        raise StoryError("No valid superhero story matches the given options.")
    place, hero, dog, artifact, threat = rng.choice(sorted(combos))
    return StoryParams(place=place, hero=hero, dog=dog, artifact=artifact, threat=threat)


def generate(params: StoryParams) -> StorySample:
    hero = next(h for h in HEROES if h.name == params.hero)
    dog = next(d for d in DOGS if d.name == params.dog)
    world = tell(hero, dog, params.artifact, params.threat, params.place)
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} + {p.dog} at {p.place} ({p.artifact} / {p.threat})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
