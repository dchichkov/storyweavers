#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py
=================================================================================

A small, standalone story world about animal friends noticing a health problem,
using friendship, a little rhyme, and a careful grown-up check to *detect
diabetes* early.

The world is designed as a TinyStories-style domain: a pet or forest animal
shows a few concrete signs, a friend notices a pattern, they rhyme a clue aloud,
and a trusted adult takes a sensible next step. The story ends with a clearer,
safer plan and an image proving what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/detect_diabetes_friendship_rhyme_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Animal:
    id: str
    kind: str
    type: str
    label: str
    sound: str
    place: str
    sign1: str
    sign2: str
    rhyme: str
    risk: str
    safe_step: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class FriendTone:
    id: str
    line: str
    rhyme: str
    comfort: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["noticed"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("checked"):
        for ent in world.characters():
            if ent.role == "friend":
                ent.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("comfort", "social", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def detect_pattern(animal: Animal) -> bool:
    return animal.sign1 and animal.sign2 and animal.risk == "diabetes"


def is_reasonable(animal: Animal, tone: FriendTone) -> bool:
    return animal.risk == "diabetes" and "detect" in tone.tags


def detect_step(world: World, friend: Entity, animal: Animal, tone: FriendTone) -> None:
    friend.meters["noticed"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} watched {animal.label} and noticed two small clues: "
        f"{animal.sign1} and {animal.sign2}. "
        f'"{tone.line}," {friend.id} said, because {animal.rhyme}.'
    )
    world.say(
        f"The little rhyme stuck in {friend.id}'s head: {tone.rhyme}. "
    )


def warn_and_share(world: World, friend: Entity, other: Entity, animal: Animal) -> None:
    friend.memes["friendship"] += 1
    other.memes["friendship"] += 1
    world.say(
        f'{friend.id} told {other.id}, "Let\'s help {animal.label} and ask a grown-up." '
        f"They stayed close together instead of guessing."
    )


def adult_check(world: World, adult: Entity, animal: Animal) -> None:
    world.facts["checked"] = True
    adult.meters["help"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over, listened carefully, and said "
        f"they would check to detect diabetes sooner rather than later."
    )
    world.say(
        f"{adult.label_word.capitalize()} thanked the friends for speaking up. "
        f"That kind of noticing can keep an animal safer."
    )


def ending(world: World, animal: Animal) -> None:
    if animal.safe_step:
        world.say(
            f"After that, {animal.label} got {animal.safe_step}, and the friends "
            f"sat beside {animal.label} under a sunny branch."
        )
    world.say(
        f"Their friendship felt brighter, and the rhyme helped the clue stay remembered."
    )


ANIMALS = {
    "rabbit": Animal(
        "rabbit", "animal", "rabbit", "rabbit", "soft hop", "garden",
        "very thirsty", "kept visiting the water bowl", "Sugar, sugar, take a test later",
        "diabetes", "a gentle check from the vet", tags={"animal", "detect", "diabetes", "friendship", "rhyme"},
    ),
    "bear": Animal(
        "bear", "animal", "bear", "bear", "slow lumber", "forest",
        "so sleepy after snacks", "seemed extra hungry", "When clues rhyme, it's help time",
        "diabetes", "a calm doctor visit", tags={"animal", "detect", "diabetes", "friendship", "rhyme"},
    ),
    "fox": Animal(
        "fox", "animal", "fox", "fox", "quick step", "hill",
        "kept asking for water", "looked tired by noon", "Small signs can lead us right",
        "diabetes", "a careful check at the clinic", tags={"animal", "detect", "diabetes", "friendship", "rhyme"},
    ),
}

FRIEND_TONES = {
    "gentle": FriendTone("gentle", "I think we should tell someone kind", "Clue by clue, we can help too", "gentle"),
    "steady": FriendTone("steady", "Let's not wait; let's ask for help", "When we notice, we can cope", "steady"),
    "bright": FriendTone("bright", "This pattern matters; let's share it", "Say it clear, then bring help near", "bright"),
}


@dataclass
@dataclass
class StoryParams:
    animal: str
    tone: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for a in ANIMALS:
        for t in FRIEND_TONES:
            combos.append((a, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship story about noticing clues and detecting diabetes.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--tone", choices=FRIEND_TONES)
    ap.add_argument("--helper", choices=["parent", "vet", "teacher"])
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
    combos = [c for c in valid_combos()
              if (args.animal is None or c[0] == args.animal) and (args.tone is None or c[1] == args.tone)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    animal, tone = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(["parent", "vet", "teacher"])
    return StoryParams(animal, tone, helper)


def tell(animal: Animal, tone: FriendTone, helper: str) -> World:
    world = World()
    a = world.add(Entity(id="Milo", kind="character", type="boy", role="friend"))
    b = world.add(Entity(id="Pip", kind="character", type="animal", role="friend"))
    adult = world.add(Entity(id=helper.capitalize(), kind="character", type="parent", label=f"the {helper}"))
    world.say(
        f"In the green garden, Milo and Pip were best friends. Pip the {animal.label} lived near a sunny path."
    )
    world.say(
        f"One day Milo noticed Pip's {animal.sign1} and {animal.sign2}. "
        f"Milo remembered a tiny rhyme about how friends can detect diabetes clues."
    )
    world.para()
    detect_step(world, a, animal, tone)
    warn_and_share(world, a, b, animal)
    adult_check(world, adult, animal)
    world.para()
    ending(world, animal)
    world.facts.update(animal=animal, tone=tone, helper=adult, friend=a, buddy=b, checked=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal: Animal = f["animal"]
    tone: FriendTone = f["tone"]
    return [
        f'Write an animal friendship story that includes the word "detect" and the word "diabetes".',
        f"Tell a rhyme-filled story where a friend notices that a {animal.label} has two clues and decides to ask for help.",
        f'Write a gentle animal story about friendship, rhyme, and how people can detect diabetes early by noticing signs.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    animal: Animal = world.facts["animal"]
    helper: Entity = world.facts["helper"]
    return [
        ("What did the friends notice?", f"They noticed {animal.sign1} and {animal.sign2}. Those two clues made the pattern feel important."),
        ("Why did they ask a grown-up?", f"They asked because the signs might point to diabetes. A grown-up could help detect diabetes safely and decide what to do next."),
        ("What did the helper do?", f"{helper.label_word.capitalize()} listened carefully and checked the clues. That was a calm way to help the animal and the friends."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    animal: Animal = world.facts["animal"]
    return [
        ("What does detect mean?", "To detect something means to notice it or find it by looking carefully for signs."),
        ("What is diabetes?", "Diabetes is a health problem that affects how the body uses sugar. A doctor or vet can help detect diabetes and treat it."),
        ("Why do friends help each other?", "Friends help each other because they care, they listen, and they work together when something seems wrong."),
        ("Why can a rhyme help?", "A rhyme is easy to remember, so it can help keep an important clue in your mind."),
        ("Why should an animal with worrying signs see a doctor or vet?", "Because a doctor or vet can check the animal carefully and decide the safest next step."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rabbit", "gentle", "vet"),
    StoryParams("bear", "steady", "parent"),
    StoryParams("fox", "bright", "teacher"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("risk", aid, a.risk))
    for tid in FRIEND_TONES:
        lines.append(asp.fact("tone", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,T) :- animal(A), tone(T).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(ANIMALS[params.animal], FRIEND_TONES[params.tone], params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (animal, tone) combos:")
        for a, t in asp_valid_combos():
            print(f"  {a:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
