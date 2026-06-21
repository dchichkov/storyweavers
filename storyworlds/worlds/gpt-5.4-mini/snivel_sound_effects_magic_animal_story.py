#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snivel_sound_effects_magic_animal_story.py
===========================================================================

A standalone story world for a small animal tale with magic and sound effects.

Premise:
- A shy animal wants to join a noisy magic show.
- The animal keeps sniveling because it feels too small or too nervous.
- Sound effects and a little magic help the animal solve the problem.
- The ending proves the change with a concrete image and a new sound.

This world is intentionally tiny and classical: one character-driven problem,
one magical turn, one satisfying ending, and question/answer sets grounded in
simulated state rather than rendered text.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_MIN = 1
MAGIC_MIN = 1


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
    noisy: bool = False
    magical: bool = False
    animal: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "ewe", "doe", "cat"}
        male = {"boy", "father", "dad", "man", "rooster", "buck", "dog", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    stage: str
    magical: bool = False

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
    type: str
    label: str
    sound: str
    movement: str
    small: str
    brave: str
    snivel_sound: str
    noisy: bool = False
    animal: bool = True

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
class Trick:
    id: str
    label: str
    effect: str
    sound: str
    sparkle: str
    source: str
    magical: bool = True

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
class Remedy:
    id: str
    label: str
    action: str
    sound: str
    effect: str
    power: int
    magical: bool = True

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


def _r_calm(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["snivel"] < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__snivel__")
    return out


def _r_magic_brighten(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["sparkle"] < THRESHOLD:
            continue
        sig = ("brighten", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__sparkle__")
    return out


CAUSAL_RULES = [
    Rule("calm", "social", _r_calm),
    Rule("brighten", "magical", _r_magic_brighten),
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


def reasonableness_gate(animal: Animal, trick: Trick, remedy: Remedy) -> bool:
    return animal.noisy and trick.magical and remedy.magical and remedy.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid, a in ANIMALS.items():
            for tid, t in TRICKS.items():
                for rid, r in REMEDIES.items():
                    if reasonableness_gate(a, t, r):
                        combos.append((sid, aid, tid))
    return combos


def quiet_predict(world: World, animal_id: str, trick_id: str) -> dict:
    sim = world.copy()
    a = sim.get(animal_id)
    t = sim.get(trick_id)
    a.meters["snivel"] += 1
    t.meters["sparkle"] += 1
    propagate(sim, narrate=False)
    return {"snivel": a.meters["snivel"], "sparkle": t.meters["sparkle"]}


def do_snivel(world: World, animal: Entity) -> None:
    animal.meters["snivel"] += 1
    animal.memes["worry"] += 1
    propagate(world, narrate=False)


def cast_trick(world: World, animal: Entity, trick: Trick) -> None:
    world.get("stage").meters["sparkle"] += 1
    animal.meters["sparkle"] += 1
    world.say(f"{trick.sound} went the spell, and {trick.sparkle} filled the air.")


def animal_noise_line(animal: Animal) -> str:
    return f"{animal.sound} went the {animal.label} sound, soft at first, then brighter."


def setup(world: World, setting: Setting, animal: Animal, trick: Trick) -> None:
    world.say(
        f"In {setting.place}, the air felt {setting.mood}, and the little {animal.label} "
        f"waited beside the {setting.stage}."
    )
    world.say(
        f"{animal.id} wanted to join the magic show, but {animal.id} kept a tiny {animal.small} "
        f"snivel whenever the crowd looked over."
    )
    world.say(animal_noise_line(animal))


def tension(world: World, animal: Entity, trick: Trick) -> None:
    animal.memes["shy"] += 1
    world.say(
        f'The wand tipped, the bells chimed, and the spell was almost ready. '
        f'"I can do this," {animal.id} whispered, sniffling once more.'
    )


def warn(world: World, helper: Entity, animal: Entity, trick: Trick) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} nudged close and said, "No need to rush. Magic likes a slow breath '
        f'and a brave heart."'
    )


def resolution(world: World, animal: Entity, trick: Trick, remedy: Remedy) -> None:
    animal.memes["brave"] += 1
    world.say(
        f'Then {animal.id} tried again. {trick.sound} popped, and {remedy.sound} answered back, '
        f'like the room itself was cheering.'
    )
    world.say(
        f"The little snivel turned into a clear little laugh, and {animal.id} stood taller."
    )
    world.say(
        f"{remedy.action.capitalize()}, {animal.id} felt {animal.brave}, and the spell made a "
        f"{remedy.effect} glow on the {world.setting.stage}."
    )


def ending(world: World, animal: Entity) -> None:
    world.say(
        f"At the end, {animal.id} bowed, ears up and eyes bright, while the last sparkle drifted down "
        f"like gold dust."
    )
    world.say(
        f"This time the only sound left was {animal.sound} -- happy, not sniveling -- and everyone smiled."
    )


def tell(setting: Setting, animal_cfg: Animal, trick: Trick, remedy: Remedy,
         helper_name: str = "Milo", helper_type: str = "dog",
         helper_label: str = "dog", seed_note: str = "") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=animal_cfg.id, kind="character", type=animal_cfg.type, label=animal_cfg.label,
        traits=["small", "shy"], role="hero", noisy=True, magical=False, animal=True,
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type, label=helper_label,
        role="helper", traits=["kind"], noisy=False, magical=False, animal=True,
    ))
    stage = world.add(Entity(id="stage", type="stage", label=setting.stage))
    trick_ent = world.add(Entity(id=trick.id, type="trick", label=trick.label, magical=True))
    remedy_ent = world.add(Entity(id=remedy.id, type="remedy", label=remedy.label, magical=True))

    setup(world, setting, animal_cfg, trick)
    world.para()
    tension(world, hero, trick)
    do_snivel(world, hero)
    warn(world, helper, hero, trick)
    cast_trick(world, hero, trick)
    world.para()
    resolution(world, hero, trick, remedy)
    ending(world, hero)

    world.facts.update(
        hero=hero, helper=helper, stage=stage, trick=trick_ent, remedy=remedy_ent,
        setting=setting, animal_cfg=animal_cfg, seed_note=seed_note,
        sniveled=hero.meters["snivel"] >= THRESHOLD,
        sparkle=stage.meters["sparkle"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonlit_stage": Setting("moonlit_stage", "a moonlit glade", "soft and twinkly", "little wooden stage", True),
    "forest_ring": Setting("forest_ring", "the forest ring", "quiet and mossy", "mossy stump stage", True),
    "barn_corner": Setting("barn_corner", "the barn corner", "warm and echoey", "painted crate stage", True),
}

ANIMALS = {
    "bunny": Animal("Pip", "rabbit", "rabbit", "boing", "hop", "small hop", "brave hop", "sniveling"),
    "kitten": Animal("Mimi", "cat", "cat", "mew", "pounce", "tiny purr", "brave purr", "sniffling"),
    "fox": Animal("Fenn", "fox", "fox", "yip", "dart", "tiny tail tuck", "brave grin", "snuffling"),
}

TRICKS = {
    "bells": Trick("bells", "ringing bells", "A ring of bells", "Ding-a-ding!", "silver sparks", "wand"),
    "bubbles": Trick("bubbles", "bubble magic", "Pop-pop!", "bubble stars", "wand"),
    "glow_leaf": Trick("glow_leaf", "glow-leaf charm", "Shimmer-shim!", "leaf lights", "palm spell"),
}

REMEDIES = {
    "hum": Remedy("hum", "a humming charm", "hummed", "hummy warmth", 1),
    "spark_hat": Remedy("spark_hat", "a sparkle hat", "put on", "fizz-fizz", "sparkling", 1),
    "clap": Remedy("clap", "a clap spell", "clapped", "bright merriment", 1),
}



@dataclass
class StoryParams:
    setting: str
    animal: str
    trick: str
    remedy: str
    helper_name: str
    helper_type: str
    helper_label: str
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

CURATED = [
    StoryParams("moonlit_stage", "bunny", "bells", "hum", "Pip", "rabbit", "rabbit"),
    StoryParams("forest_ring", "kitten", "bubbles", "spark_hat", "Mimi", "cat", "cat"),
    StoryParams("barn_corner", "fox", "glow_leaf", "clap", "Fenn", "fox", "fox"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["animal_cfg"]
    trick = f["trick"]
    return [
        f'Write a tiny animal story for preschoolers that includes the word "snivel" and the sound {trick.sound!r}.',
        f"Tell a magical animal story where {hero.id} is shy at first, then gets brave with help and a little sparkle.",
        f"Write a child-friendly story about an animal who snivels, hears a magical sound effect, and ends up smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trick = f["trick"]
    remedy = f["remedy"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small {hero.label}, and {helper.id}, who helped with the magic."
        ),
        QAItem(
            question=f"Why did {hero.id} snivel at first?",
            answer=(
                f"{hero.id} sniveled because the show felt big and the crowd made {hero.id} shy. "
                f"The worry made the first try feel hard, so {hero.id} needed a kind helper."
            )
        ),
        QAItem(
            question=f"What helped {hero.id} become brave?",
            answer=(
                f"{helper.id}'s calm words, plus the magical {trick.label}, helped {hero.id} try again. "
                f"Then the {remedy.label} added a bright finish, and the sniveling turned into a laugh."
            )
        ),
    ]
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {hero.id} bowing on the stage and sounding happy instead of sniveling. "
                f"The magic made the little animal look proud and bright."
            )
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does sniveling mean?",
            answer="Sniveling means making small sniffly sounds because you feel upset, nervous, or close to crying."
        ),
        QAItem(
            question="What do sound effects do in a story?",
            answer="Sound effects help readers hear the action in their minds. They can make magic, footsteps, or surprises feel lively."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in real life that can still happen in a story. It can make light, sparkles, or helpful changes appear."
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs a noisy animal, a magical trick, and a magical remedy.)"


ASP_RULES = r"""
noisy_animal(A) :- animal(A), noisy(A).
good_story(S, A, T, R) :- setting(S), animal(A), trick(T), remedy(R),
                          noisy_animal(A), magical_trick(T), magical_remedy(R).
outcome(snivels) :- good_story(S, A, T, R), setting(S), animal(A), trick(T), remedy(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        if a.noisy:
            lines.append(asp.fact("noisy", aid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("magical_trick", tid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("magical_remedy", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1

    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(generate(CURATED[0]), qa=True)
        print("OK: emit smoke test passed.")
    except Exception as exc:
        print(f"EMIT SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny animal magic story world with snivel and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["dog", "cat", "bird", "rabbit", "fox"])
    ap.add_argument("--helper-label")
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
    if args.animal is None:
        animal = rng.choice(sorted(ANIMALS))
    else:
        animal = args.animal
    if args.trick is None:
        trick = rng.choice(sorted(TRICKS))
    else:
        trick = args.trick
    if args.remedy is None:
        remedy = rng.choice(sorted(REMEDIES))
    else:
        remedy = args.remedy
    if not reasonableness_gate(ANIMALS[animal], TRICKS[trick], REMEDIES[remedy]):
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(sorted(SETTINGS))
    helper_name = args.helper_name or rng.choice(["Milo", "Poppy", "Ned", "Ruby"])
    helper_type = args.helper_type or rng.choice(["dog", "cat", "bird", "rabbit", "fox"])
    helper_label = args.helper_label or helper_type
    return StoryParams(setting, animal, trick, remedy, helper_name, helper_type, helper_label)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ANIMALS[params.animal],
        TRICKS[params.trick],
        REMEDIES[params.remedy],
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_label=params.helper_label,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
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
            header = f"### {p.animal} + {p.trick} + {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
