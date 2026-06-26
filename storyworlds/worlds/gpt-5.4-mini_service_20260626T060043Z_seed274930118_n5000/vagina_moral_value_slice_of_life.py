#!/usr/bin/env python3
"""
storyworlds/worlds/vagina_moral_value_slice_of_life.py
======================================================

A small slice-of-life story world about learning the proper name for a body part
and how to treat private matters with respect.

Seed tale:
---
A child hears the word "vagina" at home and feels a little embarrassed.
A parent calmly explains that it is a normal body part, like an elbow or a knee,
and that using correct words is kind and honest. Later, the child sees a friend
who needs help buttoning a coat and notices that helping quietly and respectfully
can make an ordinary day feel warmer and safer.
---

Core turn:
- Curiosity -> embarrassment -> calm explanation -> respectful action -> relief

The world models:
- meters: clean, messy, prepared, helped
- memes: curiosity, embarrassment, calm, respect, kindness, relief

This is intended to stay child-facing, concrete, and non-explicit.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("clean", "messy", "prepared", "helped"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "embarrassment", "calm", "respect", "kindness", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Topic:
    id: str
    word: str
    concern: str
    explanation: str
    kindness: str


@dataclass
class SceneObject:
    id: str
    label: str
    phrase: str
    used_for: str


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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    topic: str
    name: str
    gender: str
    parent: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "home": Setting(place="home", indoor=True, affords={"talk", "help"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"talk", "help"}),
    "porch": Setting(place="the porch", indoor=False, affords={"help", "talk"}),
}

TOPICS = {
    "vagina": Topic(
        id="vagina",
        word="vagina",
        concern="felt shy about saying the word out loud",
        explanation="It is a normal body part with a proper name, and using the proper name is respectful.",
        kindness="speaking calmly and using the right word",
    )
}

OBJECTS = {
    "coat": SceneObject(
        id="coat",
        label="coat",
        phrase="a warm blue coat",
        used_for="keeping warm on a cool day",
    ),
    "stool": SceneObject(
        id="stool",
        label="stool",
        phrase="a little stool by the counter",
        used_for="reaching a shelf",
    ),
}

GIRL_NAMES = ["Mina", "Ella", "Ruby", "Nora", "Lena", "Ivy"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Theo", "Milo", "Finn"]
FRIEND_NAMES = ["Pip", "June", "Tessa", "Luca", "Bea", "Rowan"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story about respectful language and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--friend")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TOPICS]


def explain_rejection() -> str:
    return "(No story: this world only tells a respectful, non-explicit slice-of-life story about the body and kindness.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.topic is None or c[1] == args.topic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, topic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(setting=place, topic=topic, name=name, gender=gender, parent=parent, friend=friend)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "thoughtful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", traits=["helpful"]))
    object_ = world.add(Entity(id="coat", type="thing", label="coat", phrase=OBJECTS["coat"].phrase))
    world.facts.update(hero=hero, parent=parent, friend=friend, object=object_, topic=TOPICS[params.topic], params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    friend: Entity = f["friend"]
    topic: Topic = f["topic"]
    coat: Entity = f["object"]

    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} was a little {hero.type} who liked asking honest questions.")
    world.say(f"One ordinary day at {world.setting.place}, {hero.id} heard the word “{topic.word}” and went quiet for a moment.")
    hero.memes["embarrassment"] += 1
    world.say(f"It felt like a private word, and {hero.id} worried it might be rude to say it.")

    world.para()
    parent.memes["calm"] += 1
    parent.memes["respect"] += 1
    world.say(f"{parent.id} noticed the shy look and spoke in a calm voice.")
    world.say(f'“That is a normal body part,” {parent.pronoun("subject")} said. “{topic.word.capitalize()} is the proper word, and using proper words is respectful.”')
    world.say(topic.explanation)
    hero.memes["calm"] += 1
    hero.memes["respect"] += 1

    world.para()
    world.say(f"Later, {hero.id} saw {friend.id} tugging on {friend.pronoun('possessive')} coat and looking stuck.")
    world.say(f"{hero.id} walked over, buttoned the coat carefully, and did not make a big fuss about it.")
    friend.meters["helped"] += 1
    hero.meters["helped"] += 1
    hero.memes["kindness"] += 1
    world.say(f"That small kindness made the afternoon feel softer, like a warm blanket on a cool day.")

    world.para()
    hero.memes["relief"] += 1
    world.say(f"By the time they went back inside, {hero.id} felt relieved.")
    world.say(f"{hero.id} could say {topic.word} without whispering, and {topic.kindness} felt like the right way to move through an ordinary day.")

    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    friend: Entity = f["friend"]
    topic: Topic = f["topic"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel shy after hearing the word {topic.word}?",
            answer=f"{hero.id} felt shy because the word sounded private at first, and {hero.id} worried about saying it the wrong way.",
        ),
        QAItem(
            question=f"What did {parent.id} explain about the word {topic.word}?",
            answer=f"{parent.id} explained that {topic.word} is a normal body part and that using the proper word is respectful.",
        ),
        QAItem(
            question=f"What kind thing did {hero.id} do for {friend.id}?",
            answer=f"{hero.id} quietly helped {friend.id} button the coat, which was a small and careful kindness.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does respectful language mean?",
            answer="Respectful language means using honest, polite words and not teasing or saying things carelessly.",
        ),
        QAItem(
            question="Why is it helpful to use the correct name for a body part?",
            answer="Using the correct name is helpful because it is clear, honest, and lets people talk about bodies safely.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    topic: Topic = f["topic"]
    return [
        f'Write a gentle slice-of-life story for a young child that includes the word "{topic.word}".',
        f"Tell a story about {hero.id} learning that {topic.word} is a normal word and that kindness matters.",
        f"Write a calm everyday story where a child feels shy, gets a respectful explanation, and then helps a friend.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,T) :- place(P), topic(T).
"""


def asp_facts() -> str:
    import asp
    out = []
    for p in SETTINGS:
        out.append(asp.fact("place", p))
    for t in TOPICS:
        out.append(asp.fact("topic", t))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="home", topic="vagina", name="Mina", gender="girl", parent="mother", friend="Pip"),
    StoryParams(setting="kitchen", topic="vagina", name="Owen", gender="boy", parent="father", friend="June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for p, t in asp_valid_combos():
            print(f"  {p:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.topic} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
