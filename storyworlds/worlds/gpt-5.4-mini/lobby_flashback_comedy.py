#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py
==========================================================

A standalone storyworld for a small comedy domain: a child gets embarrassed in a
lobby, remembers an earlier mistake in a flashback, and uses that memory to fix
the present with a silly but sensible move.

Domain sketch
-------------
The lobby is a bright public place with a desk, a couch, a shiny floor, and a
help desk bell. A child wants to do something funny to get attention, but that
goes awkwardly wrong. The flashback shows an earlier moment of embarrassment that
teaches the child what *not* to do. A kind adult helps with a calmer plan, and
the ending proves the child can laugh at the mistake and still do better.

This world keeps the style close to comedy:
- the prose is child-facing and concrete,
- the turn comes from a memory, not a random swap of nouns,
- the ending is an image of changed behavior,
- the humor stays gentle.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/lobby_flashback_comedy.py --verify
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
EMOTION_TURN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Setting:
    id: str
    lobby_name: str
    desk: str
    floor: str
    vibe: str
    public: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Antic:
    id: str
    label: str
    verb: str
    result: str
    mess: str
    comedy: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Memory:
    id: str
    label: str
    old_mistake: str
    lesson: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Remedy:
    id: str
    sense: int
    help_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World(self.setting)
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
            value = defaultdict(float)
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


def _r_embarrass(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["embarrass"] < THRESHOLD:
            continue
        sig = ("embarrass", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["sheepish"] += 1
        e.memes["laughing_at_self"] += 1
        out.append("__embarrass__")
    return out


def _r_announce(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes["sheepish"] < THRESHOLD:
            continue
        sig = ("announce", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "adult" in world.entities:
            world.get("adult").memes["helpful"] += 1
        out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule("embarrass", "social", _r_embarrass),
    Rule("announce", "social", _r_announce),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict_awkwardness(world: World, antic_id: str) -> dict:
    sim = world.copy()
    _do_antic(sim, sim.get("child"), ANTICS[antic_id], narrate=False)
    child = sim.get("child")
    return {
        "embarrassed": child.meters["embarrass"] >= THRESHOLD,
        "sheepish": child.memes["sheepish"] >= THRESHOLD,
    }


def _do_antic(world: World, child: Entity, antic: Antic, narrate: bool = True) -> None:
    child.meters["embarrass"] += 1
    child.meters["noise"] += 1
    child.memes["bold"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"On a busy afternoon, {child.id} and {adult.label_word} stepped into the "
        f"{setting.lobby_name}. {setting.vibe}."
    )
    world.say(
        f"{child.id} loved the lobby because it had a desk, a couch, and a shiny "
        f"floor that made shoes squeak like tiny birds."
    )


def want_attention(world: World, child: Entity, antic: Antic) -> None:
    world.say(
        f'{child.id} wanted to {antic.verb} and make everybody look up. '
        f'That seemed funny right up until it was not.'
    )


def flashback(world: World, child: Entity, memory: Memory, antic: Antic) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Then {child.id} remembered something from before. Once, in a different "
        f"lobby, {memory.old_mistake}."
    )
    world.say(
        f'The memory popped up like a bubble and whispered, "{memory.lesson}"'
    )
    world.say(
        f"That was the sort of mistake that can turn a joke into a face-plant."
    )


def do_antic(world: World, child: Entity, antic: Antic) -> None:
    child.meters["embarrass"] += 1
    child.memes["bold"] += 1
    world.say(
        f"{child.id} tried to {antic.verb}, and {antic.comedy}. "
        f"Instead, {antic.result}."
    )


def adult_help(world: World, adult: Entity, remedy: Remedy, antic: Antic) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came over with a calm grin and said, "
        f'"How about we do the silly part the safe way?"'
    )
    world.say(
        f"Then {adult.label_word} used {remedy.help_text}."
    )


def recover(world: World, child: Entity, adult: Entity, remedy: Remedy) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    adult.memes["joy"] += 1
    world.say(
        f"{child.id} snorted a laugh, because the fix was even funnier than the plan. "
        f"{remedy.qa_text}."
    )
    world.say(
        f"By the end, {child.id} was smiling beside the lobby couch, and the shiny "
        f"floor stayed clean."
    )


def tell(setting: Setting, antic: Antic, memory: Memory, remedy: Remedy,
         child_name: str = "Nora", child_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["funny", "restless"]))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender,
                             role="adult", label="the grown-up"))
    world.add(Entity(id="lobby", type="place", label=setting.lobby_name))
    world.add(Entity(id="desk", type="thing", label=setting.desk))
    world.add(Entity(id="floor", type="thing", label=setting.floor))

    intro(world, child, adult, setting)
    world.para()
    want_attention(world, child, antic)
    pred = predict_awkwardness(world, antic.id)
    if pred["embarrassed"]:
        flashback(world, child, memory, antic)
    world.para()
    do_antic(world, child, antic)
    adult_help(world, adult, remedy, antic)
    world.para()
    recover(world, child, adult, remedy)

    world.facts.update(
        child=child, adult=adult, setting=setting, antic=antic, memory=memory,
        remedy=remedy, embarrassed=pred["embarrassed"],
    )
    return world


SETTINGS = {
    "hotel": Setting("hotel", "hotel lobby", "front desk", "polished floor", "It was quiet except for a bell ding and a suitcase roll."),
    "museum": Setting("museum", "museum lobby", "welcome desk", "waxed floor", "It was echoey, like the room was listening."),
    "school": Setting("school", "school lobby", "sign-in desk", "shiny floor", "It was bright and busy, with backpacks bumping knees."),
}

ANTICS = {
    "bell": Antic(
        "bell", "ring the desk bell three times", "ring the desk bell three times",
        "the bell dinged so hard that even the posters seemed surprised",
        "a very loud ding bounced off the walls and made the line jump",
        "the lobby sounded like a parade in a teacup",
        tags={"bell", "noise", "lobby"},
    ),
    "twirl": Antic(
        "twirl", "spin like a tiny tornado", "spin like a tiny tornado",
        "the child got so dizzy that the couch looked like a boat",
        "the twirl went crooked and became a wobble",
        "the lobby looked briefly like a dancing classroom",
        tags={"spin", "lobby"},
    ),
    "echo": Antic(
        "echo", "shout hello to the ceiling", "shout hello to the ceiling",
        "the ceiling shouted back in a wiggly echo that sounded silly and awkward",
        "the echo came back too big and too proud",
        "the lobby turned into a voice soup",
        tags={"echo", "lobby"},
    ),
}

MEMORIES = {
    "bell": Memory(
        "bell", "the time the child rang the bell too many times",
        "the child rang the bell so many times that a tired receptionist laughed",
        "don't make a joke louder than the room can hold",
        tags={"bell", "memory"},
    ),
    "twirl": Memory(
        "twirl", "the time the child spun until the backpack caught on a chair",
        "the child spun so fast that a backpack slid right off a chair",
        "funny moves need a little space",
        tags={"spin", "memory"},
    ),
    "echo": Memory(
        "echo", "the time the child yelled in a hallway and startled a janitor",
        "the child yelled in a hallway and startled a janitor carrying cups of water",
        "kind jokes are quieter than surprise",
        tags={"echo", "memory"},
    ),
}

REMEDIES = {
    "whisper": Remedy(
        "whisper", 3,
        "showed how to whisper the joke into a paper cup instead of into the whole lobby",
        "tried to whisper, but the joke stayed too loud and still made a scene",
        "Now the joke fit in one hand and one giggle",
        tags={"quiet", "comedy"},
    ),
    "mime": Remedy(
        "mime", 3,
        "taught a silly mime with wide eyes, big eyebrows, and a tiny bow",
        "made a face that was funny in the wrong way and did not help at all",
        "the tiny bow was the best part",
        tags={"mime", "comedy"},
    ),
    "wave": Remedy(
        "wave", 2,
        "gave a dramatic little wave and a thumbs-up toward the couch",
        "waved, but the moment was still too bumpy to fix",
        "the wave looked like a duck saying hello",
        tags={"wave", "comedy"},
    ),
}



def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, r) for s in SETTINGS for a in ANTICS for r in REMEDIES]


@dataclass
class StoryParams:
    setting: str
    antic: str
    memory: str
    remedy: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    ("hotel", "bell", "bell", "whisper"),
    ("museum", "twirl", "twirl", "mime"),
    ("school", "echo", "echo", "wave"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old set in a {f["setting"].lobby_name} with the word "lobby".',
        f"Tell a comedy story where {f['child'].id} gets the urge to make a scene in the lobby, remembers an old mistake, and chooses a calmer joke.",
        f"Write a flashback-comedy story with a lobby, an embarrassing memory, and a grown-up who helps turn the joke into something kinder.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, setting = f["child"], f["adult"], f["setting"]
    antic, memory, remedy = f["antic"], f["memory"], f["remedy"]
    qa = [
        ("Where does the story happen?",
         f"It happens in the {setting.lobby_name}. The lobby matters because the child wants attention in a public place."),
        ("What did {0} want to do?".format(child.id),
         f"{child.id} wanted to {antic.verb}. It started as a joke, but it was the kind of joke that could become a mess."),
        ("What did the child remember?",
         f"{child.id} remembered that {memory.old_mistake}. The flashback helped {child.id} notice that the same kind of joke had gone wrong before."),
        ("How did the grown-up help?",
         f"{adult.label_word.capitalize()} helped by {remedy.help_text}. That turned the joke into something gentler and easier for everyone to laugh at."),
    ]
    if f["embarrassed"]:
        qa.append((
            "Why did the child feel embarrassed?",
            f"{child.id} felt embarrassed because the first plan made too much noise and got awkward in the lobby. The memory made {child.id} stop and choose a better way."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {child.id} smiling near the lobby couch, after the silly idea got a calmer shape. The final image shows the child laughing without making a bigger mess."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["antic"].tags) | set(f["memory"].tags) | set(f["remedy"].tags) | {"lobby"}
    out = []
    if "lobby" in tags:
        out.append(("What is a lobby?",
                    "A lobby is the front room of a building where people come in, wait, or ask for help. It is usually a public place with a desk or couch."))
    if "bell" in tags:
        out.append(("What does a desk bell do?",
                    "A desk bell makes a little ding so someone at the desk knows a person needs help. It is for attention, not for being noisy on purpose."))
    if "echo" in tags:
        out.append(("What is an echo?",
                    "An echo is a sound that bounces back so you hear it again. It can make a voice sound bigger or sillier."))
    if "quiet" in tags:
        out.append(("Why can whispering be a good idea indoors?",
                    "Whispering keeps sound small. That helps other people stay calm in a shared room."))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
embarrassed(C) :- child(C), meter(C, embarrass, V), V >= 1.
help_needed(C) :- embarrassed(C), memory(C, _).
resolved(C) :- help_needed(C), remedy(R), sense(R, S), sense_min(M), S >= M.
outcome(embarrassed) :- embarrassed(C), not resolved(C).
outcome(resolved) :- resolved(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ANTICS.items():
        lines.append(asp.fact("antic", aid))
    for mid, m in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    outcomes = set(asp.atoms(model, "outcome"))
    py = {"resolved"}
    if outcomes != {("resolved",)}:
        print("MISMATCH: ASP outcome did not resolve")
        return 1
    sample = generate(resolve_params(argparse.Namespace(setting=None, antic=None, memory=None, remedy=None, child=None, child_gender=None, adult=None, adult_gender=None), random.Random(7)))
    if not sample.story:
        print("MISMATCH: story generation failed")
        return 1
    print("OK: ASP and normal generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny lobby flashback comedy storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--antic", choices=ANTICS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    antic = args.antic or rng.choice(list(ANTICS))
    memory = args.memory or antic
    remedy = args.remedy or rng.choice(list(REMEDIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or (rng.choice(["Mina", "Toby", "Lila", "Noah", "June"]) if child_gender == "girl" else rng.choice(["Ben", "Otto", "Finn", "Max", "Eli"]))
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult = args.adult or ("Mom" if adult_gender == "mother" else "Dad")
    if memory not in MEMORIES:
        raise StoryError("Unknown memory choice.")
    if remedy not in REMEDIES:
        raise StoryError("Unknown remedy choice.")
    return StoryParams(setting, antic, memory, remedy, child, child_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANTICS[params.antic], MEMORIES[params.memory],
                 REMEDIES[params.remedy], params.child, params.child_gender,
                 params.adult, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def valid_combo_filter(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.antic in ANTICS and params.memory in MEMORIES and params.remedy in REMEDIES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatibility is broad in this comedy world")
        for s in SETTINGS:
            for a in ANTICS:
                for r in REMEDIES:
                    print(f"  {s} {a} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, a, m, r, "Nora", "girl", "Mom", "mother"))
                   for s, a, m, r in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
