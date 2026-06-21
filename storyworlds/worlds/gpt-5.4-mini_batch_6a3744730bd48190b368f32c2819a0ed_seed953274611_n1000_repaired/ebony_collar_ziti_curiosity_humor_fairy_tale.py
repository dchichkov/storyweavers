#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ebony_collar_ziti_curiosity_humor_fairy_tale.py
================================================================================

A tiny fairy-tale storyworld about curiosity, a little humor, and three seed
words: ebony, collar, ziti.

Premise
-------
A child or small creature notices an ebony collar, wonders about a bowl of ziti,
and must choose whether to poke, taste, or ask. The turn comes from curiosity:
the wrong choice makes a silly mess, while the wise choice leads to a warm,
funny ending with shared food and a bright lesson.

This world keeps the story child-facing, state-driven, and complete:
- the beginning establishes the odd object and the tempting food,
- the middle turns on a curious choice and its consequence,
- the ending proves what changed through repaired state and a final image.

It supports:
- default run
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

The inline ASP twin mirrors the Python reasonableness gate and outcome model.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOUS_MIN = 2.0
HUMOR_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    edible: bool = False
    shiny: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    detail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    material: str
    sparkle: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class FoodConfig:
    id: str
    label: str
    phrase: str
    smell: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ChoiceConfig:
    id: str
    verb: str
    result: str
    note: str
    sense: int
    humor: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    spoon = world.entities.get("spoon")
    bowl = world.entities.get("bowl")
    for e in list(world.entities.values()):
        if e.meters["messy"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if bowl:
            bowl.meters["tipped"] += 1
        if spoon:
            spoon.meters["sticky"] += 1
        out.append("__silly__")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for o_id, obj in OBJECTS.items():
            for f_id, food in FOODS.items():
                for c_id, choice in CHOICES.items():
                    if reasonableness_gate(obj, food, choice):
                        combos.append((s_id, o_id, f_id))
    return combos


def reasonableness_gate(obj: ObjectConfig, food: FoodConfig, choice: ChoiceConfig) -> bool:
    return choice.sense >= 2 and choice.humor >= 1 and obj.material == "ebony" and food.id == "ziti"


def best_choice() -> ChoiceConfig:
    return max(CHOICES.values(), key=lambda c: (c.sense, c.humor))


def outcome_of(params: "StoryParams") -> str:
    choice = CHOICES[params.choice]
    return "silly" if choice.id == "poke" else "warm"


def predicts_mess(choice: ChoiceConfig) -> bool:
    return choice.id == "poke"


def predict_world(world: World, choice: ChoiceConfig) -> dict:
    sim = world.copy()
    if predicts_mess(choice):
        sim.get("hero").meters["messy"] += 1
        propagate(sim, narrate=False)
    return {"messy": sim.get("hero").meters["messy"] >= THRESHOLD,
            "tipped": sim.get("bowl").meters["tipped"] >= THRESHOLD}


def setup(world: World, hero: Entity, obj: ObjectConfig, food: FoodConfig) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Once in a fairy village by a silver stream, {hero.id} found an ebony collar "
        f"beside a window, and a warm bowl of ziti waited nearby."
    )
    world.say(
        f"{hero.id} blinked at the ebony collar. It gleamed like moonlight on a raven's wing."
    )
    world.say(
        f"The ziti smelled buttery and brave, as if it had a secret to tell."
    )


def question(world: World, hero: Entity, obj: ObjectConfig, food: FoodConfig) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"What are you for?" {hero.id} asked the ebony collar, and then peered at the ziti. '
        f'"Do you wear a collar, or eat one?"'
    )
    world.say("That was a funny question, even for a fairy tale, and it made the kitchen grin.")


def warn(world: World, caretaker: Entity, hero: Entity, obj: ObjectConfig, food: FoodConfig) -> bool:
    pred = predict_world(world, CHOICES[world.facts["choice"]])
    if not pred["messy"]:
        return False
    caretaker.memes["care"] += 1
    world.say(
        f'{caretaker.id} laughed and said, "The ebony collar is not a noodle, dear one. '
        f"And the ziti is for supper, not for poking."'
    )
    return True


def poke(world: World, hero: Entity, food: FoodConfig) -> None:
    hero.memes["humor"] += 1
    hero.meters["messy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} poked the ziti with a spoon, and one curly noodle leaped onto the floor "
        f"like a tiny ribbon dancer."
    )


def taste(world: World, hero: Entity, food: FoodConfig) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} took a careful bite of the ziti instead, and the room filled with a cozy "
        f"smile."
    )


def laugh_fix(world: World, caretaker: Entity, hero: Entity) -> None:
    caretaker.memes["humor"] += 1
    hero.memes["humor"] += 1
    world.say(
        f"{caretaker.id} wiped the noodle away and chuckled, and even the ebony collar seemed "
        f"to sparkle harder at the joke."
    )


def ending(world: World, hero: Entity, caretaker: Entity, food: FoodConfig, choice: ChoiceConfig) -> None:
    if hero.meters["messy"] >= THRESHOLD:
        world.say(
            f"In the end, {hero.id} washed {hero.pronoun('possessive')} hands, and the ziti stayed "
            f"in the bowl where it belonged."
        )
    else:
        world.say(
            f"In the end, {hero.id} sat up straight, smiling with a ziti crumb on {hero.pronoun('possessive')} chin."
        )
    world.say(
        f"{caretaker.id} smiled, the ebony collar gleamed, and the little fairy kitchen felt wise and merry."
    )


@dataclass
class StoryParams:
    setting: str
    object: str
    food: str
    choice: str
    hero_name: str = "Nell"
    hero_type: str = "girl"
    caretaker_name: str = "Aunt Rose"
    caretaker_type: str = "woman"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def tell(setting: Setting, obj: ObjectConfig, food: FoodConfig, choice: ChoiceConfig,
         hero_name: str = "Nell", hero_type: str = "girl",
         caretaker_name: str = "Aunt Rose", caretaker_type: str = "woman") -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=caretaker_type, label=caretaker_name))
    collar = world.add(Entity(id="collar", type="thing", label=obj.label, phrase=obj.phrase, shiny=True))
    bowl = world.add(Entity(id="bowl", type="thing", label=food.label, phrase=food.phrase, edible=True))
    spoon = world.add(Entity(id="spoon", type="thing", label="spoon"))

    world.facts.update(choice=choice.id, object=obj, food=food, setting=setting)
    setup(world, hero, obj, food)
    world.para()
    question(world, hero, obj, food)
    warn(world, caretaker, hero, obj, food)
    world.para()
    if choice.id == "poke":
        poke(world, hero, food)
        laugh_fix(world, caretaker, hero)
    else:
        taste(world, hero, food)
    ending(world, hero, caretaker, food, choice)
    world.facts.update(hero=hero, caretaker=caretaker, collar=collar, bowl=bowl, spoon=spoon,
                       outcome=outcome_of(StoryParams(setting=setting.id, object=obj.id, food=food.id, choice=choice.id)))
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="a fairy kitchen", mood="warm", detail="golden light danced on the walls"),
    "garden": Setting(id="garden", place="a moonlit garden", mood="bright", detail="tiny lanterns winked in the hedges"),
}

OBJECTS = {
    "ebony": ObjectConfig(id="ebony", label="ebony collar", phrase="an ebony collar with a silver clasp", material="ebony", sparkle="moon-bright", tags={"ebony"}),
}

FOODS = {
    "ziti": FoodConfig(id="ziti", label="ziti", phrase="a bowl of ziti", smell="buttery", tags={"ziti"}),
}

CHOICES = {
    "poke": ChoiceConfig(id="poke", verb="poke", result="mess", note="curious and funny", sense=2, humor=3, tags={"curiosity", "humor"}),
    "taste": ChoiceConfig(id="taste", verb="taste", result="warm", note="curious and kind", sense=3, humor=2, tags={"curiosity", "humor"}),
}

CURATED = [
    None,
]


KNOWLEDGE = {
    "ebony": [("What is ebony?", "Ebony is a very dark, hard wood. It can look black and shiny, like a little piece of night.")],
    "ziti": [("What is ziti?", "Ziti is a kind of pasta with tube-shaped noodles. People often serve it with sauce and cheese.")],
    "curiosity": [("What is curiosity?", "Curiosity is the wish to know more. It makes someone ask questions and look closely at the world.")],
    "humor": [("What is humor?", "Humor is what makes a story or moment funny. It helps people smile and laugh together.")],
}


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fairy-tale story that includes the words ebony, collar, and ziti, and has a curious, funny mood.',
        'Tell a small fairy story where a child wonders about an ebony collar and a bowl of ziti, then makes a choice that leads to a gentle ending.',
        'Write a child-friendly tale with curiosity and humor, where ebony and ziti both matter to the ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    choice = CHOICES[f["choice"]]
    qas = [
        ("What did the child find?",
         f"The child found an ebony collar and noticed a bowl of ziti nearby. The shiny collar and the warm pasta both caught {hero.id}'s eye."),
        ("Why did the child ask questions?",
         f"{hero.id} was curious, so {hero.id} asked what the ebony collar was for. The ziti made the question a little funny, which gave the story humor."),
    ]
    if choice.id == "poke":
        qas.append((
            "What happened after the child poked the ziti?",
            f"A noodle jumped onto the floor like a ribbon dancer, and everyone laughed. The caretaker cleaned it up, so the silliness stayed harmless."
        ))
    else:
        qas.append((
            "How did the child end the story?",
            f"{hero.id} tasted the ziti and chose the gentle path, so the evening stayed cozy. The ebony collar kept shining while the supper stayed neat."
        ))
    qas.append((
        "How did the story end?",
        f"The story ended with a calm, merry fairy-tale image: the child, the caretaker, and the ebony collar all stayed part of the warm little scene."
    ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ebony", "ziti", "curiosity", "humor"}
    out: list[tuple[str, str]] = []
    for key in ["curiosity", "humor", "ebony", "ziti"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.plural:
            bits.append("plural=True")
        if e.edible:
            bits.append("edible=True")
        if e.shiny:
            bits.append("shiny=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(_: ObjectConfig, __: FoodConfig, choice: ChoiceConfig) -> str:
    return f"(No story: choice '{choice.id}' is not reasonable enough for this fairy-tale world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with ebony, collar, and ziti.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--caretaker")
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
    obj = args.object or "ebony"
    food = args.food or "ziti"
    choice = args.choice or rng.choice(list(CHOICES))
    if not reasonableness_gate(OBJECTS[obj], FOODS[food], CHOICES[choice]):
        raise StoryError(explain_rejection(OBJECTS[obj], FOODS[food], CHOICES[choice]))
    name = args.name or rng.choice(["Nell", "Mira", "Pip", "Ivy"])
    caretaker = args.caretaker or rng.choice(["Aunt Rose", "Grandma Fern", "The Queen", "A kindly baker"])
    return StoryParams(setting=setting, object=obj, food=food, choice=choice, hero_name=name, caretaker_name=caretaker)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("object", OBJECTS), ("food", FOODS), ("choice", CHOICES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], FOODS[params.food], CHOICES[params.choice], params.hero_name, params.hero_type, params.caretaker_name, params.caretaker_type)
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


ASP_RULES = r"""
reasonable(choice(poke)) :- sense(poke,S), S >= 2, humor(poke,H), H >= 1.
reasonable(choice(taste)) :- sense(taste,S), S >= 2, humor(taste,H), H >= 1.
outcome(silly) :- chosen_choice(poke).
outcome(warm) :- chosen_choice(taste).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("material", oid, o.material))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("humor", cid, c.humor))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/1."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import random as _r
    rc = 0
    if set(asp_valid_combos()) != {("choice", "poke"), ("choice", "taste")}:
        rc = 1
        print("MISMATCH: ASP gate unexpected.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object=None, food=None, choice=None, name=None, caretaker=None), _r.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    else:
        print("OK: smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible choices:", ", ".join(f"{t[1]}" for t in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, object="ebony", food="ziti", choice=c, seed=0)) for s in SETTINGS for c in CHOICES]
    else:
        i = 0
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
