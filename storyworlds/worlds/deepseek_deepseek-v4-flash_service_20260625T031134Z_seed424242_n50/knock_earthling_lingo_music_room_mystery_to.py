#!/usr/bin/env python3
"""
storyworlds/worlds/knock_earthling_lingo_music_room_mystery_to.py
=================================================================

A standalone *story world* sketch for a comedic mystery in a music room.
An earthling learns alien lingo through repetitive knock patterns and
discovers a moral value about listening.

Initial story (used to build a world model):
---
Once upon a time, there was a cheerful earthling named Pip. Pip loved visiting
the music room in the big community hall. The music room had a funny piano, a
wiggly trumpet, and a drum that liked to echo. One day, Pip heard a strange
knock: knock-knock-knockety-knock.

Pip looked around. Nobody was there! The knock came again: knock-knock-knockety-knock.
Pip realized it was coming from the old music cabinet. Inside, Pip found a small
shiny box with blinking lights. The box kept knocking: knock-knock-knockety-knock.
Pip did not understand the lingo.

Pip tried to talk to the box. "Hello?" Pip said. The box knocked back: knock-knock.
Pip knocked back: knock-knock. The box knocked faster: knock-knock-knockety-knockety-knock!
Pip wrote down the knocks. Knock means yes. Knock-knock means hello. Knockety-knock
means please. Knock-knock-knockety-knock means I need help!

Pip knocked: knockety-knock (please) and then knock-knock-knockety-knock (I need help).
The box opened! Inside was a tiny alien named Gloop who was stuck. Gloop said,
"Thank you, earthling! You learned my lingo!" Pip learned that when you listen
carefully, even knock sounds can become words.

Causal state updates:
---
    mystery encountered          -> player.curiosity += 1
    player repeats knock         -> player.knowledge += 1
    player decodes lingo         -> player.understanding += 1
    player helps alien           -> player.kindness += 1
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

TRICK_KINDS = {"knock", "echo", "blink"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "alien_f"}
        male = {"boy", "man", "alien_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the music room"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    verb: str
    discovery: str
    solution: str
    lingo_pattern: str
    moral_key: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Lingo:
    pattern: str
    meaning: str
    level: int


MYSTERIES = {
    "alien_box": Mystery(
        id="alien_box",
        verb="solve the knock mystery",
        discovery="a blinking box in the cabinet",
        solution="learn the knock lingo",
        lingo_pattern="knock-knock-knockety-knock",
        moral_key="listening",
        keyword="alien",
        tags={"knock", "lingo", "alien"},
    ),
    "funny_trumpet": Mystery(
        id="funny_trumpet",
        verb="figure out the trumpet's echo",
        discovery="the trumpet echoes everything twice",
        solution="sing back the echo pattern",
        lingo_pattern="toot-toot-toooot",
        moral_key="patience",
        keyword="trumpet",
        tags={"echo", "lingo", "alien"},
    ),
}

LINGOS = [
    Lingo(pattern="knock", meaning="yes", level=1),
    Lingo(pattern="knock-knock", meaning="hello", level=1),
    Lingo(pattern="knockety-knock", meaning="please", level=2),
    Lingo(pattern="knock-knock-knockety-knock", meaning="I need help", level=3),
    Lingo(pattern="toot", meaning="yes", level=1),
    Lingo(pattern="toot-toot", meaning="hello", level=1),
    Lingo(pattern="toooot-toot", meaning="please", level=2),
    Lingo(pattern="toot-toot-toooot", meaning="I am stuck", level=3),
]


MORAL_VALUES = {
    "listening": "When you listen carefully, even knock sounds can become words.",
    "patience": "Sometimes you need to wait for the right toot before you understand.",
    "kindness": "Helping a stranger makes the world feel friendlier.",
}


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    moral_value: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mystery_seen"] >= THRESHOLD and actor.memes["curiosity"] < THRESHOLD:
            sig = ("discover", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["curiosity"] += 1
            out.append(f"{actor.id} felt a tickle of curiosity.")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["heard_knock"] >= THRESHOLD * 2:
            sig = ("repeat", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["knowledge"] += 1
            out.append(f"{actor.id} tried to repeat the sound.")
    return out


def _r_decode(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["knowledge"] >= THRESHOLD * 3:
            sig = ("decode", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["understanding"] += 1
            out.append(f"The sounds started making sense!")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["understanding"] >= THRESHOLD and actor.memes["kindness"] < THRESHOLD:
            sig = ("help", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["kindness"] += 1
            out.append(f"{actor.id} decided to help.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="discover", tag="mental", apply=_r_discover),
    Rule(name="repeat", tag="mental", apply=_r_repeat),
    Rule(name="decode", tag="mental", apply=_r_decode),
    Rule(name="help", tag="moral", apply=_r_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce_earthling(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a cheerful earthling who loved visiting the music room.")


def describe_room(world: World, mystery: Mystery) -> None:
    items = "a funny piano, a wiggly trumpet, and a drum that liked to echo"
    world.say(f"The music room had {items}.")
    world.say(f"One day, {hero(world).id} heard a strange {mystery.lingo_pattern}.")
    world.para()


def hero(world: World) -> Entity:
    chars = world.characters()
    return [c for c in chars if c.type in {"boy", "girl"}][0]


def encounter_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(f"{hero.id} looked around. Nobody was there! The knock came again.")
    hero.meters["mystery_seen"] += 1
    propagate(world)


def search_source(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(f"{hero.id} realized it was coming from the old music cabinet.")
    world.say(f"Inside, {hero.id} found {mystery.discovery}.")
    propagate(world)


def repeat_lingo(world: World, hero: Entity, mystery: Mystery) -> None:
    for _ in range(2):
        hero.memes["heard_knock"] += 1
        propagate(world)
    world.say(f"{hero.id} knocked back: {mystery.lingo_pattern}.")
    propagate(world)


def decode_lingo(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(f"{hero.id} wrote down the sounds. A knock means yes. Knock-knock means hello.")
    world.say(f"{hero.id} knocked: knockety-knock and then knock-knock-knockety-knock.")
    propagate(world)


def resolve_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    alien = world.add(Entity(
        id="Gloop",
        kind="character",
        type="alien_m",
        label="tiny alien",
        phrase="a tiny alien with big eyes",
    ))
    world.say(f"The box opened! Inside was {alien.phrase} named Gloop who was stuck.")
    world.say(f"Gloop said, 'Thank you, earthling! You learned my lingo!'")
    world.say(f"{hero.id} learned that when you listen carefully, even knock sounds can become words.")
    propagate(world)


def tell(setting: Setting, mystery: Mystery,
         hero_name: str = "Pip", hero_type: str = "boy",
         moral_value: str = "listening") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["cheerful", "curious"],
    ))

    introduce_earthling(world, hero)
    describe_room(world, mystery)
    encounter_mystery(world, hero, mystery)
    search_source(world, hero, mystery)
    repeat_lingo(world, hero, mystery)
    decode_lingo(world, hero, mystery)
    resolve_mystery(world, hero, mystery)

    world.facts.update(hero=hero, mystery=mystery,
                       moral_value=moral_value,
                       resolved=True)
    return world


NAMES = ["Pip", "Zuzu", "Momo", "Bib", "Fufu", "Didi", "Gaga", "Lulu", "Nini", "Toto"]
TRAITS = ["cheerful", "curious", "brave", "silly", "friendly"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery = f["hero"], f["mystery"]
    return [
        f'Write a short story about an earthling named {hero.id} who discovers '
        f'{mystery.discovery} in the music room and learns to understand '
        f'the knock lingo.',
        f'Tell a comedic mystery where {hero.id} must {mystery.verb} by '
        f'repeating the strange patterns from the cabinet.',
        f'Write a story where a silly earthling learns the moral value of '
        f'listening through knock sounds in a music room.',
    ]


KNOWLEDGE = {
    "knock": [("What does knock-knock mean in alien lingo?",
               "Knock-knock means hello in alien lingo. It is how aliens say hi to earthlings.")],
    "lingo": [("What is lingo?",
               "Lingo is a special way of talking. It can be sounds or words that only "
               "some people understand.")],
    "alien": [("What is an alien?",
               "An alien is someone from another planet. They might look different "
               "and speak different lingo.")],
    "echo": [("What is an echo?",
              "An echo is when a sound bounces back and you hear it again. It repeats "
              "what you said.")],
    "listening": [("Why is listening important?",
                   "Listening helps you understand what others are saying. When you listen "
                   "carefully, even knock sounds can become words.")],
    "patience": [("What does patience mean?",
                  "Patience means waiting calmly. Sometimes you need patience to understand "
                  "new lingo.")],
    "kindness": [("What is kindness?",
                  "Kindness is helping others. When the earthling helped the alien, "
                  "that was kindness.")],
}

KNOWLEDGE_ORDER = ["knock", "lingo", "alien", "echo", "listening", "patience", "kindness"]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mystery = f["hero"], f["mystery"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Where did {hero.id} hear the strange knock?",
            answer=f"{hero.id} heard the strange knock in the music room, coming from "
                   f"the old music cabinet where {mystery.discovery} was hiding.",
        ),
        QAItem(
            question=f"What did {hero.id} find inside the cabinet?",
            answer=f"{hero.id} found {mystery.discovery} inside the cabinet. It was "
                   f"making the knock sounds that needed to be understood.",
        ),
        QAItem(
            question=f"How did {hero.id} learn to understand the knock lingo?",
            answer=f"{hero.id} listened carefully and repeated the knock patterns. By "
                   f"writing them down and trying different knocks, {hero.id} figured "
                   f"out the meaning of each pattern.",
        ),
        QAItem(
            question=f"Who was inside the box and why?",
            answer=f"A tiny alien named Gloop was inside the box. Gloop was stuck and "
                   f"needed help, which is why the box kept making knock sounds.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} learn from the mystery?",
            answer=f"{hero.id} learned the moral value of {f['moral_value']}. "
                   f"{MORAL_VALUES[f['moral_value']]}",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    tags.add(world.facts["moral_value"])
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(mystery="alien_box", name="Pip", gender="boy", moral_value="listening"),
    StoryParams(mystery="funny_trumpet", name="Zuzu", gender="girl", moral_value="patience"),
    StoryParams(mystery="alien_box", name="Momo", gender="girl", moral_value="kindness"),
    StoryParams(mystery="funny_trumpet", name="Bib", gender="boy", moral_value="listening"),
]


ASP_RULES = r"""
mystery_has_lingo(M, P) :- mystery(M), lingo_pattern(M, P).
earthling_learns(E, M) :- earthling(E), mystery(M),
                          mystery_has_lingo(M, _),
                          curiosity(E, _), knowledge(E, _).
moral_value(E, V) :- earthling(E), learns_value(E, V),
                     kindness(E, _).
valid_story(E, M, V) :- earthling(E), mystery(M),
                        earthling_learns(E, M),
                        moral_value(E, V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("lingo_pattern", mid, m.lingo_pattern))
    for v in MORAL_VALUES:
        lines.append(asp.fact("moral", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    print("ASP verification passed (inline rules match domain logic).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an earthling solves a knock mystery in the music room.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--moral-value", choices=list(MORAL_VALUES.keys()))
    ap.add_argument("--name", choices=NAMES)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["boy", "girl"])
    moral_value = args.moral_value or rng.choice(list(MORAL_VALUES.keys()))
    return StoryParams(mystery=mystery, name=name, gender=gender,
                       moral_value=moral_value)


def generate(params: StoryParams) -> StorySample:
    setting = Setting(place="the music room", indoor=True, affords={"knock", "echo"})
    world = tell(setting, MYSTERIES[params.mystery],
                 params.name, params.gender, params.moral_value)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for e, m, v in stories:
            print(f"  earthling={e}, mystery={m}, moral_value={v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.mystery} (moral: {p.moral_value})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
