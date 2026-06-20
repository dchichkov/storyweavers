#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jaw_linguini_tiresome_flashback_moral_value_fable.py
====================================================================================

A small, standalone storyworld in fable form.

Domain:
- A young hare and an older tortoise share a kitchen-garden lunch.
- The hare's jaw gets sore from bragging and nibbling too fast.
- The lunch is linguini, which is slippery and easy to spill.
- A flashback reminds the hare of an earlier tiresome mess.
- The ending teaches a clear moral value: patience and care save the meal.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- a Python reasonableness gate plus inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify, --show-asp, --asp, --all, -n, --seed, --trace, --qa, --json
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class FableSetting:
    id: str
    place: str
    mood: str
    table: str
    flashback_trigger: str

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
class Ingredient:
    id: str
    label: str
    phrase: str
    slippery: bool = False
    chewy: bool = False
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
class Action:
    id: str
    verb: str
    consequence: str
    mess: str
    sense: int
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
class Moral:
    id: str
    line: str
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
    def __init__(self, setting: FableSetting) -> None:
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_jaw_ache(world: World) -> list[str]:
    out: list[str] = []
    hare = world.entities.get("hare")
    if not hare or hare.meters["chewing"] < THRESHOLD:
        return out
    sig = ("jaw_ache", "hare")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hare.meters["jaw_ache"] += 1
    hare.memes["irritation"] += 1
    out.append("__jaw__")
    return out


def _r_tiresome(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["boredom"] < THRESHOLD:
            continue
        sig = ("tiresome", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["weariness"] += 1
        out.append("__tiresome__")
    return out


def _r_shared_pause(world: World) -> list[str]:
    out: list[str] = []
    hare = world.entities.get("hare")
    tortoise = world.entities.get("tortoise")
    if not hare or not tortoise:
        return out
    if hare.memes["regret"] < THRESHOLD or tortoise.memes["kindness"] < THRESHOLD:
        return out
    sig = ("pause",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tortoise.memes["calm"] += 1
    hare.memes["calm"] += 1
    out.append("__pause__")
    return out


CAUSAL_RULES = [
    Rule("jaw_ache", "physical", _r_jaw_ache),
    Rule("tiresome", "social", _r_tiresome),
    Rule("shared_pause", "social", _r_shared_pause),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: FableSetting, ingredient: Ingredient, action: Action) -> bool:
    return ingredient.slippery and action.sense >= SENSE_MIN and setting.id in {"garden", "table"}


def should_flashback(world: World) -> bool:
    hare = world.entities.get("hare")
    return bool(hare and hare.meters["jaw_ache"] >= THRESHOLD and hare.memes["regret"] >= THRESHOLD)


def setup_flashback(world: World, hare: Entity) -> None:
    hare.memes["flashback"] += 1
    world.say(
        f"As they waited, {hare.id} remembered an older afternoon."
    )
    world.say(
        f"Back then, {hare.id} had spoken with a full mouth, laughed too hard, "
        f"and bitten {hare.pronoun('possessive')} own jaw while trying to finish lunch first."
    )


def scene_open(world: World, hare: Entity, tortoise: Entity, setting: FableSetting, ingredient: Ingredient) -> None:
    world.say(
        f"On a bright day in {setting.place}, {hare.id} and {tortoise.id} sat beside {setting.table}."
    )
    world.say(
        f"A bowl of {ingredient.phrase} waited between them, and the air smelled warm and honest."
    )
    world.say(
        f"{hare.id} had a quick jaw and a faster tongue, while {tortoise.id} moved with patient care."
    )


def want_and_warn(world: World, hare: Entity, tortoise: Entity, ingredient: Ingredient) -> None:
    hare.memes["want"] += 1
    world.say(
        f'"I can eat it all at once," {hare.id} boasted, though {hare.pronoun("possessive")} jaw was already tiring.'
    )
    world.say(
        f'{tortoise.id} tipped {tortoise.pronoun("possessive")} head. "Slow bites are kinder to the jaw," {tortoise.pronoun()} said.'
    )


def act(world: World, hare: Entity, ingredient: Ingredient, action: Action) -> None:
    hare.meters["chewing"] += 1
    hare.meters["mess"] += 1
    hare.memes["boredom"] += 1
    world.say(
        f"{hare.id} tried to {action.verb}, but the {ingredient.label} slipped from {hare.pronoun('possessive')} paws."
    )
    world.say(
        f"{ingredient.label.capitalize()} {action.consequence} and made the lunch feel {action.mess}."
    )
    propagate(world, narrate=False)


def flashback(world: World, hare: Entity) -> None:
    if should_flashback(world):
        setup_flashback(world, hare)
        world.say(
            f"That memory was tiresome, and it made {hare.id} stop rushing."
        )


def resolve(world: World, hare: Entity, tortoise: Entity, ingredient: Ingredient, moral: Moral) -> None:
    hare.memes["regret"] += 1
    hare.memes["kindness"] += 1
    tortoise.memes["kindness"] += 1
    world.say(
        f"{hare.id} lowered {hare.pronoun('possessive')} eyes and asked for a smaller bite."
    )
    world.say(
        f'{tortoise.id} smiled and pushed the bowl closer. "A gentle meal leaves room for joy," {tortoise.pronoun()} said.'
    )
    world.say(
        f"Together they ate the {ingredient.label} slowly, and the dish stayed neat."
    )
    world.say(
        f"By the end, {hare.id}'s jaw felt better, {tortoise.id}'s patience had warmed the table, and the old trouble was gone."
    )
    world.say(f"The moral was clear: {moral.line}")


def tell(setting: FableSetting, ingredient: Ingredient, action: Action, moral: Moral,
         hare_name: str = "Hare", tortoise_name: str = "Tortoise") -> World:
    world = World(setting)
    hare = world.add(Entity(id=hare_name, kind="character", type="boy", role="learned"))
    tortoise = world.add(Entity(id=tortoise_name, kind="character", type="thing", role="guide"))
    hare.memes["pride"] = 1
    tortoise.memes["kindness"] = 1

    scene_open(world, hare, tortoise, setting, ingredient)
    world.para()
    want_and_warn(world, hare, tortoise, ingredient)
    act(world, hare, ingredient, action)
    flashback(world, hare)
    world.para()
    resolve(world, hare, tortoise, ingredient, moral)

    world.facts.update(
        hare=hare,
        tortoise=tortoise,
        setting=setting,
        ingredient=ingredient,
        action=action,
        moral=moral,
        flashback=hare.memes["flashback"] >= THRESHOLD,
        jaw=hare.meters["jaw_ache"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": FableSetting("garden", "the garden", "sunny", "the low stone table", "an old memory"),
    "orchard": FableSetting("orchard", "the orchard", "quiet", "the round stump table", "the earlier lunch"),
}

INGREDIENTS = {
    "linguini": Ingredient("linguini", "linguini", "a bowl of linguini", slippery=True, chewy=True, tags={"food", "flashback"}),
    "noodles": Ingredient("noodles", "noodles", "a bowl of soft noodles", slippery=True, chewy=True, tags={"food"}),
}

ACTIONS = {
    "gulp": Action("gulp", "gulp it down", "spilled onto the cloth", "tiresome", 3, tags={"rush"}),
    "twirl": Action("twirl", "twirl the fork too fast", "flew from the fork", "tiresome", 2, tags={"rush"}),
}

MORALS = {
    "patience": Moral("patience", "patience makes a meal kinder and cleaner", tags={"moral"}),
    "sharing": Moral("sharing", "sharing a meal is better than racing for the first bite", tags={"moral"}),
}

TRAITS = ["careful", "quick", "thoughtful", "gentle"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    ingredient: str
    action: str
    moral: str
    hare_name: str = "Hare"
    tortoise_name: str = "Tortoise"
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


KNOWLEDGE = {
    "linguini": [("What is linguini?", "Linguini is a kind of long, thin pasta. It is soft when cooked and easy to twirl on a fork.")],
    "jaw": [("What is a jaw?", "A jaw is the part of your face that helps you chew food and talk.")],
    "patience": [("What is patience?", "Patience means waiting calmly and not rushing. It helps you do things more carefully.")],
    "moral": [("What is a moral in a fable?", "A moral is the lesson at the end of a fable. It tells what the story teaches.")],
    "flashback": [("What is a flashback?", "A flashback is when a story briefly remembers something that happened earlier.")],
    "tiresome": [("What does tiresome mean?", "Tiresome means boring or tiring because it takes too long or feels hard to keep doing.")],
}
KNOWLEDGE_ORDER = ["linguini", "jaw", "patience", "moral", "flashback", "tiresome"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in INGREDIENTS:
            for a in ACTIONS:
                for m in MORALS:
                    if reasonableness_gate(SETTINGS[s], INGREDIENTS[i], ACTIONS[a]):
                        combos.append((s, i, a, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a small child that includes the words "{f["ingredient"].label}", "jaw", and "tiresome".',
        f"Tell a short animal story in which a hare rushes lunch, remembers an earlier mistake in a flashback, and learns a moral value.",
        f'Write a calm fable with a flashback and a moral at the end, using the word "{f["ingredient"].label}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hare = f["hare"]
    tortoise = f["tortoise"]
    ing = f["ingredient"]
    moral = f["moral"]
    qa = [
        ("Who is the story about?", f"It is about {hare.id} and {tortoise.id}, who shared a meal and a lesson."),
        ("What did the hare want to do?", f"{hare.id} wanted to rush the {ing.label} and finish before anyone else. That hurried choice made {hare.id}'s jaw tired."),
        ("Why did the hare remember the older afternoon?", f"The flashback came because the jaw pain and the busy, tiresome lunch made {hare.id} think of an earlier mistake. The memory helped {hare.id} slow down."),
        ("How did the story end?", f"It ended with a quiet meal, a calmer jaw, and the moral that {moral.line}."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["ingredient"].tags) | set(world.facts["action"].tags) | set(world.facts["moral"].tags) | {"flashback", "jaw"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
slippery(I) :- ingredient(I), slippery_ing(I).
reasonable(S, I, A) :- setting(S), ingredient(I), action(A), slippery(I), sense(A, X), sense_min(M), X >= M.
jaw_ache(hare) :- chewing(hare), jawsore(hare).
flashback_needed(hare) :- jaw_ache(hare), regret(hare).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for iid, i in INGREDIENTS.items():
        lines.append(asp.fact("ingredient", iid))
        if i.slippery:
            lines.append(asp.fact("slippery_ing", iid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if a - b:
            print("  only in ASP:", sorted(a - b))
        if b - a:
            print("  only in Python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams("garden", "linguini", "gulp", "patience", "Hare", "Tortoise"),
    StoryParams("orchard", "noodles", "twirl", "sharing", "Hare", "Tortoise"),
]


def explain_rejection(setting: FableSetting, ingredient: Ingredient, action: Action) -> str:
    return (
        f"(No story: the chosen move is not reasonable for this little fable. "
        f"{ingredient.label.capitalize()} is not slippery enough for that turn, or the action is too weak to support the moral.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: jaw, linguini, tiresome, flashback, moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--hare-name")
    ap.add_argument("--tortoise-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.ingredient is None or c[1] == args.ingredient)
              and (args.action is None or c[2] == args.action)
              and (args.moral is None or c[3] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ingredient, action, moral = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        ingredient=ingredient,
        action=action,
        moral=moral,
        hare_name=args.hare_name or rng.choice(["Hare", "Pip", "Nim"]),
        tortoise_name=args.tortoise_name or rng.choice(["Tortoise", "Toby", "Tessa"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], INGREDIENTS[params.ingredient], ACTIONS[params.action], MORALS[params.moral], params.hare_name, params.tortoise_name)
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
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
