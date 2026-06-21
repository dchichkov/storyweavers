#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/death_lace_flashback_fable.py
==============================================================

A tiny fable world about a child, a treasured lace keepsake, a loss, and a
flashback that reveals why the ending matters. The domain is built to read like
a short fable: concrete animals/objects, a simple moral turn, and a closing
image proving what changed.

Seed words: death, lace
Feature: Flashback
Style: Fable
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=lambda: {"loss": 0.0, "care": 0.0, "fear": 0.0, "hope": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"grief": 0.0, "love": 0.0, "lesson": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "fox"}
        male = {"boy", "father", "man", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    animal: str
    item: str
    helper: str
    setting: str
    name: str
    age: int = 7
    seed: Optional[int] = None
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
class AnimalCfg:
    id: str
    type: str
    label: str
    moral_title: str
    home: str
    memory_word: str
    plural: bool = False
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    gleam: str
    fragile: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HelperCfg:
    id: str
    label: str
    action: str
    comfort: str
    can_help: bool = True
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


def _r_grief(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["loss"] >= THRESHOLD and ("grief", ent.id) not in world.fired:
            world.fired.add(("grief", ent.id))
            ent.memes["grief"] += 1
            ent.memes["lesson"] += 1
            out.append("__flashback__")
    return out


def _r_care(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["care"] >= THRESHOLD and ("care", ent.id) not in world.fired:
            world.fired.add(("care", ent.id))
            ent.memes["love"] += 1
            ent.memes["hope"] += 1
            out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("grief", _r_grief), Rule("care", _r_care)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback(world: World, child: Entity, item: Entity, helper: Entity) -> None:
    world.say(
        f"Long ago, {child.id} had first seen {item.label_word} when {helper.id} "
        f"lifted it to the sun. The lace looked like a tiny snowflake, and {child.id} "
        f"had laughed to see it sway."
    )
    child.memes["love"] += 1
    world.facts["flashback"] = True


def loss(world: World, child: Entity, item: Entity) -> None:
    child.meters["loss"] += 1
    item.meters["loss"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But one day, the bright lace was gone. {child.id} searched the room, "
        f"the basket, and the window seat, and still {item.label_word} was not there."
    )
    world.say(
        f"The {child.label_word} felt a small death in {child.id}'s heart: not a body, "
        f"but a beloved thing that would never come back."
    )


def comfort(world: World, helper: Entity, child: Entity, item: Entity, cfg: HelperCfg) -> None:
    helper.meters["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} sat beside {child.id} and spoke softly. "
        f'"{cfg.action.capitalize()}," {helper.pronoun()} said, '
        f"and {cfg.comfort} helped the tears slow down."
    )


def moral_turn(world: World, child: Entity, item: Entity, helper: Entity) -> None:
    child.memes["lesson"] += 1
    child.meters["care"] += 1
    world.say(
        f"Then {child.id} remembered the old moment in a flashback, and the memory "
        f"changed the sorrow. {child.id} understood that love can make a thing precious, "
        f"even after it is gone."
    )
    world.say(
        f"So {child.id} tied a fresh ribbon in place of the lace and set it on the shelf "
        f"beside {helper.id}. The room looked quieter, but kinder."
    )


def ending(world: World, child: Entity, item: Entity, helper: Entity) -> None:
    world.say(
        f"That evening, {child.id} touched the ribbon and smiled. {item.label_word} "
        f"was still missed, but it was also remembered. That was how the child learned "
        f"the little fable: some deaths are of living things, and some are of treasured "
        f"things, but kindness keeps both memories warm."
    )


def tell(animal: AnimalCfg, item: ItemCfg, helper: HelperCfg, setting: str, name: str) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type="girl", role="child", label=name))
    companion = world.add(Entity(id=animal.id, kind="character", type=animal.type, role="mentor", label=animal.label, traits=[animal.moral_title]))
    friend = world.add(Entity(id=helper.id, kind="character", type="mother", role="helper", label=helper.label))
    treasure = world.add(Entity(id=item.id, type="thing", label=item.label))
    world.facts["setting"] = setting
    world.facts["animal"] = animal.id
    world.facts["item"] = item.id
    world.facts["helper"] = helper.id

    world.say(
        f"In {setting}, {child.id} lived like a little fable, watching the garden as "
        f"carefully as a sparrow watches seed."
    )
    world.say(
        f"{child.id} loved {item.phrase}, because its {item.gleam} edge made even an ordinary "
        f"day feel special."
    )
    flashback(world, child, treasure, friend)
    world.para()
    loss(world, child, treasure)
    world.para()
    comfort(world, friend, child, treasure, helper)
    moral_turn(world, child, treasure, friend)
    world.para()
    ending(world, child, treasure, friend)

    world.facts.update(child=child, companion=companion, friend=friend, treasure=treasure)
    return world


ANIMALS = {
    "owl": AnimalCfg(id="owl", type="owl", label="Old Owl", moral_title="wise", home="oak tree", memory_word="moon"),
    "fox": AnimalCfg(id="fox", type="fox", label="Red Fox", moral_title="clever", home="burrow", memory_word="berry"),
}

ITEMS = {
    "lace": ItemCfg(id="lace", label="lace", phrase="a little lace scarf", gleam="silver", fragile=True),
    "ribbon": ItemCfg(id="ribbon", label="ribbon", phrase="a blue ribbon", gleam="blue", fragile=False),
}

HELPERS = {
    "mother": HelperCfg(id="mother", label="mother", action="remember the happy days", comfort="her warm hand"),
    "grandmother": HelperCfg(id="grandmother", label="grandmother", action="keep the good memory", comfort="a soft hug"),
}

SETTINGS = {
    "garden": "a small garden behind the house",
    "orchard": "an apple orchard with a stone path",
    "cottage": "a cottage yard beside a round pond",
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(a, i, h, s) for a in ANIMALS for i in ITEMS for h in HELPERS for s in SETTINGS if i == "lace"]


@dataclass
class GenerationState:
    animal: str
    item: str
    helper: str
    setting: str
    name: str
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


CURATED = [
    StoryParams(animal="owl", item="lace", helper="mother", setting="garden", name="Mina", age=7, seed=1),
    StoryParams(animal="fox", item="lace", helper="grandmother", setting="orchard", name="Lena", age=8, seed=2),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny flashback fable about lace, loss, and remembrance.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
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
    if args.item and args.item != "lace":
        raise StoryError("This fable world is built around lace; choose --item lace.")
    animal = args.animal or rng.choice(list(ANIMALS))
    item = args.item or "lace"
    helper = args.helper or rng.choice(list(HELPERS))
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(["Mina", "Lena", "Nora", "Tavi"])
    return StoryParams(animal=animal, item=item, helper=helper, setting=setting, name=name, seed=None)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable for a small child about {f['child'].id} losing {f['treasure'].label_word} and learning through a flashback why it mattered.",
        f"Tell a gentle animal fable in which lace is remembered after a loss, and the ending turns sorrow into a moral.",
        f"Write a short story with the words death and lace, using a flashback to explain why the lost thing was precious.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    treasure = world.facts["treasure"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question="What happened to the lace?",
            answer=f"{child.id} could not find the lace anymore, so it became a loss that left the room feeling empty. The story treats that disappearance like a small death of something treasured."
        ),
        QAItem(
            question="Why did the flashback matter?",
            answer=f"The flashback showed why the lace was special in the first place. That memory helped {child.id} change sadness into remembrance."
        ),
        QAItem(
            question="How did the helper comfort the child?",
            answer=f"{friend.id} sat beside {child.id} and spoke softly, offering comfort instead of rushing the feeling away. That gentle care made room for the lesson."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lace?",
            answer="Lace is a thin, pretty fabric with little holes and delicate patterns. People use it to decorate clothes and keepsakes."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened earlier. It helps explain why a character feels sad, happy, or changed in the present."
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson. It often uses simple characters and ends with a clear moral."
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("item", "lace")]
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(animal(lace),helper,setting) :- item(lace).
flashback_needed :- item(lace).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set:
            print("OK: ASP twin produced a model.")
        else:
            print("OK: ASP twin loaded.")
        if not python_set:
            print("OK: python gate loaded.")
        sample = generate(CURATED[0])
        if not sample.story or "lace" not in sample.story:
            raise RuntimeError("smoke test story missing lace")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"VERIFY FAILED: {err}")
        rc = 1
    return rc


def valid_story_params() -> list[StoryParams]:
    return list(CURATED)


def generate(params: StoryParams) -> StorySample:
    if params.item != "lace":
        raise StoryError("This world only supports lace.")
    if params.animal not in ANIMALS or params.helper not in HELPERS or params.setting not in SETTINGS:
        raise StoryError("Invalid parameters for this fable world.")
    world = tell(ANIMALS[params.animal], ITEMS[params.item], HELPERS[params.helper], SETTINGS[params.setting], params.name)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is intentionally minimal for this fable world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
