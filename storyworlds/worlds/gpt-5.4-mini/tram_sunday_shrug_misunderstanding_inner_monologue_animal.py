#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tram_sunday_shrug_misunderstanding_inner_monologue_animal.py
=============================================================================================

A small animal-story world about a Sunday tram ride, a shrug that gets
misread, and the quiet relief that comes when the animals say what they mean.

Seed words:
- tram
- sunday
- shrug

Features:
- Misunderstanding
- Inner Monologue

Style:
- Animal Story

The simulation keeps a tiny causal model:
- animals have bodies (meters) and feelings (memes)
- a Sunday tram ride can be crowded or calm
- one animal's shrug can be misread as refusal
- inner monologue reveals the truth
- a gentle clarification turns the ride into a happy ending image
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "squirrel", "badger", "bear", "fox"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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
class Rule:
    name: str
    apply: callable

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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for eid, e in world.entities.items():
        if e.memes["misread"] < THRESHOLD:
            continue
        sig = ("misunderstanding", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        other = world.entities.get(e.attrs.get("about", ""))
        if other:
            other.memes["hurt"] += 1
        out.append("__misunderstanding__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["clarified"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] += 1
        e.memes["hurt"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    emitted: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                emitted.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in emitted:
            world.say(s)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    crowd: str

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
class Animal:
    id: str
    species: str
    adjective: str
    vibe: str
    small: bool = True

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
class Tram:
    id: str
    label: str
    sound: str
    window: str

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


SETTINGS = {
    "sunny": Setting("sunny", "the tram stop by the park", "bright", "not too crowded"),
    "rainy": Setting("rainy", "the tram stop under the awning", "soft and gray", "quite crowded"),
}

ANIMALS = {
    "mouse": Animal("mouse", "mouse", "tiny", "nervous"),
    "rabbit": Animal("rabbit", "rabbit", "fluffy", "curious"),
    "squirrel": Animal("squirrel", "squirrel", "quick", "thoughtful"),
    "badger": Animal("badger", "badger", "calm", "careful"),
}

TRAMS = {
    "green": Tram("green", "the green tram", "clang-clang", "wide windows"),
    "red": Tram("red", "the red tram", "ding-ding", "round windows"),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal1: str
    animal2: str
    tram: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a Sunday tram ride and a shrug misunderstood.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--tram", choices=TRAMS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a1, a2) for s in SETTINGS for a1 in ANIMALS for a2 in ANIMALS if a1 != a2]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for t in TRAMS:
        lines.append(asp.fact("tram", t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A1, A2) :- setting(S), animal(A1), animal(A2), A1 != A2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def tell(setting: Setting, a1: Animal, a2: Animal, tram: Tram) -> World:
    w = World()
    hero = w.add(Entity(id="Mika", kind="character", type=a1.species, label="Mika", role="observer", traits=[a1.adjective, a1.vibe]))
    friend = w.add(Entity(id="Pip", kind="character", type=a2.species, label="Pip", role="shrubber", traits=[a2.adjective, a2.vibe]))
    vehicle = w.add(Entity(id="tram", kind="thing", type="tram", label=tram.label))
    stop = w.add(Entity(id="stop", kind="thing", type="place", label=setting.place))

    hero.memes["want"] += 1
    friend.memes["want"] += 1
    w.say(f"On a {setting.id} Sunday, Mika and Pip waited at {setting.place} for {tram.label}.")
    w.say(f"The {tram.label} went {tram.sound}, and its {tram.window} flashed in the light.")

    w.para()
    w.say("Mika wanted to sit by the window and watch the city go by.")
    friend.memes["misread"] += 1
    friend.attrs["about"] = "Mika"
    w.say(f"Pip gave a small shrug.")
    w.say("Mika's whiskers twitched. That shrug looked like a no.")
    w.say('Mika thought, "Oh no, maybe Pip does not want to ride with me."')
    w.say('Inside, Pip thought, "I do want to ride. I just do not want to shout over the tram."')
    propagate(w, narrate=False)

    w.para()
    if friend.memes["misread"] >= THRESHOLD:
        w.say("Mika scooted back and looked a little sad.")
        w.say("Pip saw that Mika had gone quiet and quickly leaned closer.")
        friend.memes["clarified"] += 1
        w.say('Pip said softly, "I was not saying no. I only shrugged because I was thinking."')
        w.say('Mika blinked, then smiled. "Oh! I thought you meant the window seat was for someone else."')
        w.say("Pip shook their head and moved over to make room.")
        w.say("Soon the two animals sat side by side, sharing the warm bench and the view.")
        w.say("The tram rattled on, and the little Sunday ride felt easy again.")
    else:
        w.say("Pip simply pointed at the open seat, and Mika climbed up happily.")
        w.say("The tram rolled on through Sunday morning light.")

    w.facts.update(setting=setting, animal1=hero, animal2=friend, tram=vehicle, outcome="clarified")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a small child that includes the words "tram", "sunday", and "shrug".',
        f"Tell a gentle Sunday story about {f['animal1'].id} and {f['animal2'].id} riding a tram, where one shrug causes a misunderstanding that gets fixed.",
        "Write a short animal story with an inner monologue that shows what one character really meant after a shrug.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["animal1"].id
    b = world.facts["animal2"].id
    return [
        QAItem(
            question="What happened on the Sunday tram ride?",
            answer=f"{a} and {b} rode the tram together, but a shrug was first misunderstood as a refusal. Then they talked it through and sat side by side again."
        ),
        QAItem(
            question="What did Pip really mean by the shrug?",
            answer="Pip did not mean no. Pip was only thinking and did not want to shout over the tram, so the shrug was a quiet thinking gesture."
        ),
        QAItem(
            question="How did the misunderstanding get fixed?",
            answer="Pip explained the shrug in words, and Mika understood right away. After that, the two animals made room for each other and the ride felt friendly again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tram?",
            answer="A tram is a vehicle that rides on tracks and carries people through a town or city."
        ),
        QAItem(
            question="What does a shrug often mean?",
            answer="A shrug can mean that someone is unsure, thinking, or does not know what to say."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in a character's head that tells the reader what the character really thinks."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sunny", "mouse", "squirrel", "green"),
    StoryParams("rainy", "rabbit", "badger", "red"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal1 and args.animal2 and args.animal1 == args.animal2:
        raise StoryError("The two animals must be different.")
    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)]
    combos = [c for c in combos if (args.animal1 is None or c[1] == args.animal1)]
    combos = [c for c in combos if (args.animal2 is None or c[2] == args.animal2)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal1, animal2 = rng.choice(sorted(combos))
    tram = args.tram or rng.choice(sorted(TRAMS))
    return StoryParams(setting, animal1, animal2, tram)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal1], ANIMALS[params.animal2], TRAMS[params.tram])
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
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        print("MISMATCH in valid combos")
        return 1
    # smoke test normal generation
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("Generation failed")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
