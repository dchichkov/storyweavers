#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/breaking_incense_pine_conflict_foreshadowing_surprise_adventure.py
===================================================================================================

A small standalone storyworld about an adventure in a pine cabin where a fragile
incense tray breaks, a warning turns into conflict, and a surprise solves the
quest.

Seed words:
- breaking
- incense
- pine

Features:
- Conflict
- Foreshadowing
- Surprise

Style:
- Adventure
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
MEME_GOAL = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Setting:
    id: str
    place: str
    pine_detail: str
    path_detail: str
    hidden_spot: str
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
class ObjectCfg:
    id: str
    label: str
    fragile: bool = False
    scented: bool = False
    pine_related: bool = False
    secret: bool = False
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


@dataclass
class ActionCfg:
    id: str
    verb: str
    clue: str
    risk: str
    surprise_noun: str
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
        return [e for e in self.entities.values() if e.kind == "character"]

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
    tag: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    pair = world.facts.get("pair")
    if not pair:
        return out
    a = world.get(pair[0])
    b = world.get(pair[1])
    if a.memes["defiance"] >= THRESHOLD and b.memes["warning"] >= THRESHOLD:
        sig = ("conflict", a.id, b.id)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["conflict"] += 1
            b.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("foreshadowed"):
        return out
    if world.facts.get("broken") and world.facts.get("pine_clue"):
        sig = ("foreshadow",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["foreshadowed"] = True
            out.append("__foreshadow__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("opened_secret"):
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("foreshadow", "story", _r_foreshadow), Rule("conflict", "story", _r_conflict), Rule("surprise", "story", _r_surprise)]


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


def predict_break(world: World, obj: Entity) -> dict:
    sim = world.copy()
    sim.get(obj.id).meters["broken"] += 1
    propagate(sim, narrate=False)
    return {"broken": sim.get(obj.id).meters["broken"] >= THRESHOLD}


def tell(setting: Setting, action: ActionCfg, obj: ObjectCfg, surprise: ObjectCfg,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         parent_name: str, parent_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["bold"], attrs={"setting": setting.id}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["careful"], attrs={"setting": setting.id}))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label="the guide"))
    item = world.add(Entity(id=obj.id, type="thing", label=obj.label))
    hidden = world.add(Entity(id=surprise.id, type="thing", label=surprise.label, attrs={"secret": True}))
    world.facts["pair"] = (hero.id, helper.id)
    world.facts["setting"] = setting
    world.facts["action"] = action
    world.facts["object"] = obj
    world.facts["surprise"] = surprise
    world.facts["parent"] = parent
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["item"] = item
    world.facts["hidden"] = hidden

    hero.memes["curiosity"] += 1
    helper.memes["warning"] += 1
    world.say(f"In the pine cabin, {hero.id} and {helper.id} followed a trail of needles and old board creaks. {setting.pine_detail} {setting.path_detail}")
    world.say(f"They were searching for the {action.clue}, because the map said it would lead to a hidden door.")

    world.para()
    world.say(f"But near the window sat {obj.label}, and the incense smell made the room feel like a ship's cabin. The little tray was so fragile it looked ready for breaking.")
    world.say(f'{helper.id} bit {helper.pronoun("possessive")} lip. "{obj.label} could break if we rush," {helper.id} said. "And if it breaks, the smoke will get everywhere."')
    world.say(f'{hero.id} shrugged. "A fast adventure needs fast hands," {hero.id} said, and reached for it.')
    hero.memes["defiance"] += 1
    if predict_break(world, item)["broken"]:
        world.facts["broken"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(f'{parent.id} turned at the sound of the scrape and said, "{action.risk}!"')
    world.say(f"{hero.id} frowned back. {helper.id} frowned too, because neither wanted the quest to stop, but the room was already tense with conflict.")

    if world.facts.get("broken"):
        item.meters["broken"] += 1
        item.meters["scattered"] += 1
        world.say(f"Then came the accident: a tiny slip, a sharp crack, and the incense tray broke open on the floor.")
        world.say(f"A sweet pine scent and a ribbon of smoke curled up together, exactly like the clue they had seen earlier.")
        world.facts["pine_clue"] = True
        propagate(world, narrate=False)
        world.para()
        world.say(f"The helper pointed to a small knot in the pine boards that the smoke had made visible. Behind it was a secret latch.")
        world.facts["opened_secret"] = True
        propagate(world, narrate=False)
        world.para()
        world.say(f"{parent.id} lifted the latch, and the surprise was waiting there all along: a tiny brass compass wrapped in pine twine.")
        world.say(f'Inside the lid was a note that said, "Follow the pine smell where the floor sings."')
        world.say(f"{hero.id} and {helper.id} laughed, because the broken thing had become the very thing that showed the way.")
        world.say(f"With the compass shining in {hero.id}'s hand, the adventure could continue without fear.")
    else:
        world.say(f"Instead of breaking, the tray stayed whole, and the day moved on with a quieter clue.")

    world.facts.update(outcome="broken" if world.facts.get("broken") else "safe")
    return world


SETTING_REGISTRY = {
    "pine_cabin": Setting(
        id="pine_cabin",
        place="a pine cabin",
        pine_detail="The whole room smelled like pine sap and old wood.",
        path_detail="A narrow path of pine needles led past the hearth.",
        hidden_spot="behind the pine boards",
    ),
    "pine_trail": Setting(
        id="pine_trail",
        place="a pine trail",
        pine_detail="The trees leaned over them like a green tunnel.",
        path_detail="A crooked trail of cones and needles pointed deeper uphill.",
        hidden_spot="under a root",
    ),
}

OBJECT_REGISTRY = {
    "incense_tray": ObjectCfg(
        id="incense_tray",
        label="the incense tray",
        fragile=True,
        scented=True,
        pine_related=False,
        secret=False,
        tags={"incense", "breaking"},
    ),
    "pine_box": ObjectCfg(
        id="pine_box",
        label="the pine box",
        fragile=True,
        scented=True,
        pine_related=True,
        secret=False,
        tags={"pine"},
    ),
}

SURPRISE_REGISTRY = {
    "compass": ObjectCfg(
        id="compass",
        label="a brass compass",
        secret=True,
        tags={"surprise"},
    ),
    "key": ObjectCfg(
        id="key",
        label="a silver key",
        secret=True,
        tags={"surprise"},
    ),
}

ACTION_REGISTRY = {
    "search": ActionCfg(
        id="search",
        verb="search for the clue",
        clue="a hidden clue",
        risk="Careful hands first",
        surprise_noun="compass",
        tags={"foreshadowing"},
    ),
    "follow": ActionCfg(
        id="follow",
        verb="follow the pine trail",
        clue="a pine-scented clue",
        risk="Slow down and look",
        surprise_noun="key",
        tags={"foreshadowing"},
    ),
}


@dataclass
class StoryParams:
    setting: str = "pine_cabin"
    action: str = "search"
    object: str = "incense_tray"
    surprise: str = "compass"
    hero: str = "Mina"
    hero_gender: str = "girl"
    helper: str = "Owen"
    helper_gender: str = "boy"
    parent: str = "Rae"
    parent_gender: str = "woman"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTING_REGISTRY:
        for aid in ACTION_REGISTRY:
            for oid in OBJECT_REGISTRY:
                if "incense" in OBJECT_REGISTRY[oid].tags and "pine" not in OBJECT_REGISTRY[oid].tags:
                    combos.append((sid, aid, oid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with breaking, incense, pine, conflict, foreshadowing, and surprise.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--action", choices=ACTION_REGISTRY)
    ap.add_argument("--object", choices=OBJECT_REGISTRY)
    ap.add_argument("--surprise", choices=SURPRISE_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent")
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
    if args.object and args.object not in OBJECT_REGISTRY:
        raise StoryError("Unknown object.")
    if args.surprise and args.surprise not in SURPRISE_REGISTRY:
        raise StoryError("Unknown surprise.")
    if args.object and "incense" not in OBJECT_REGISTRY[args.object].tags:
        raise StoryError("This story needs an incense object.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, obj = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISE_REGISTRY))
    hero = args.hero or rng.choice(["Mina", "Tess", "Lio", "Iris"])
    helper = args.helper or rng.choice([n for n in ["Owen", "Sage", "Noah", "Rin"] if n != hero])
    parent = args.parent or rng.choice(["Rae", "Mara", "Jon", "Tara"])
    return StoryParams(setting=setting, action=action, object=obj, surprise=surprise, hero=hero, helper=helper, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Setting = f["setting"]
    a: ActionCfg = f["action"]
    return [
        f'Write an adventure story that includes the words "breaking", "incense", and "pine" in a pine setting.',
        f"Tell a child-sized adventure where {f['hero'].id} and {f['helper'].id} follow a clue in {s.place}, conflict over a fragile incense object, and end with a surprise.",
        f"Write a foreshadowing story where a pine smell hints at a hidden discovery after the breaking of an incense tray.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    setting: Setting = f["setting"]
    items = [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} and {helper.id} went together, with {parent.id} keeping watch nearby. They were the brave pair in the pine cabin.",
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"The conflict started when {hero.id} reached for the incense tray too fast. {helper.id} warned that it could break and make smoke everywhere, but {hero.id} wanted to hurry.",
        ),
        QAItem(
            question="What was foreshadowed earlier in the story?",
            answer=f"The pine smell and the clue about a singing floor hinted that something hidden was nearby. That earlier detail mattered because it pointed to the secret latch before the surprise appeared.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was a brass compass hidden behind the latch. It gave the children a new way to keep exploring after the broken tray revealed the way forward.",
        ),
    ]
    if f.get("broken"):
        items.append(QAItem(
            question="What happened when the incense tray broke?",
            answer=f"It cracked open on the floor and a sweet pine-scented smoke rose up. The broken tray exposed the hidden latch, so the accident turned into part of the adventure.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is incense?",
            answer="Incense is something that gives off a strong smell when it is used. It can also make smoke, so people handle it carefully.",
        ),
        QAItem(
            question="What does pine smell like?",
            answer="Pine usually smells fresh, green, and a little sharp, like trees and forest air. That smell can remind you of a cabin or a trail in the woods.",
        ),
        QAItem(
            question="Why can breaking something be important in a story?",
            answer="Breaking something can change the plan and create a new problem to solve. It can also reveal a hidden clue or lead the characters to a surprise.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.setting]
    action = ACTION_REGISTRY[params.action]
    obj = OBJECT_REGISTRY[params.object]
    surprise = SURPRISE_REGISTRY[params.surprise]
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent_gender, role="parent", label="the guide"))
    incense_item = world.add(Entity(id=obj.id, type="thing", label="the incense tray"))
    hidden = world.add(Entity(id=surprise.id, type="thing", label=surprise.label, attrs={"secret": True}))
    world.facts.update(setting=setting, action=action, object=obj, surprise=surprise, hero=hero, helper=helper, parent=parent, incense=incense_item, hidden=hidden, opened_secret=False)

    hero.memes["curiosity"] += 1
    helper.memes["warning"] += 1

    world.say(f"It was an adventure day in {setting.place}. {setting.pine_detail} {setting.path_detail}")
    world.say(f"{hero.id} and {helper.id} followed the clue because they were sure it would lead somewhere secret.")

    world.para()
    world.say(f"Near the window, the incense tray sat by itself, and the air smelled of pine and warm wood.")
    world.say(f'"Careful," {helper.id} said. "If that tray starts {action.id}{"ing" if not action.id.endswith("e") else "ing"}, it could crack."')
    world.say(f"{hero.id} wanted to hurry anyway. {hero.id} reached out, and the tray slipped from {hero.pronoun('possessive')} fingers.')
    hero.memes["defiance"] += 1
    if obj.fragile:
        incense_item.meters["broken"] += 1
        world.facts["broken"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(f"{parent.id} stepped in at once. '{action.risk}!' {parent.id} said, and the room went quiet except for the rustle of pine needles outside.")
    world.say(f"{helper.id} and {hero.id} stood in a tense little conflict, until the broken pieces made the smell even stronger.")
    world.facts["pine_clue"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(f"Then the surprise appeared: the smoke had shown a hidden latch in the pine boards.")
    world.say(f"{parent.id} opened it, and inside was {surprise.label}, shining like a tiny moon for the trail.")
    world.facts["opened_secret"] = True
    propagate(world, narrate=False)
    world.say(f"{hero.id} grinned, because the broken incense tray had not ruined the adventure after all. It had pointed the way to the next step.")
    world.facts["outcome"] = "surprise"
    return world


CURATED = [
    StoryParams(setting="pine_cabin", action="search", object="incense_tray", surprise="compass", hero="Mina", hero_gender="girl", helper="Owen", helper_gender="boy", parent="Rae", parent_gender="woman"),
    StoryParams(setting="pine_trail", action="follow", object="incense_tray", surprise="key", hero="Tess", hero_gender="girl", helper="Noah", helper_gender="boy", parent="Jon", parent_gender="man"),
]


def explain_rejection() -> str:
    return "(No story: this world needs an incense object that can break, plus a pine setting and a surprise discovery.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for aid in ACTION_REGISTRY:
        lines.append(asp.fact("action", aid))
    for oid, o in OBJECT_REGISTRY.items():
        lines.append(asp.fact("object", oid))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
        if "incense" in o.tags:
            lines.append(asp.fact("incense", oid))
    for sid in SURPRISE_REGISTRY:
        lines.append(asp.fact("surprise", sid))
    lines.append(asp.fact("needs_pine", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,O) :- setting(S), action(A), object(O), fragile(O), incense(O).
conflict :- fragile(O), incense(O).
foreshadowing :- setting(S).
surprise :- surprise(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, action=None, object=None, surprise=None, hero=None, helper=None, parent=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY or params.action not in ACTION_REGISTRY or params.object not in OBJECT_REGISTRY or params.surprise not in SURPRISE_REGISTRY:
        raise StoryError("Invalid parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write an adventure story that includes the words breaking, incense, and pine.',
        f"Tell a story where {f['hero'].id} and {f['helper'].id} explore {f['setting'].place}, get into conflict over incense, and discover a surprise.",
        "Write a foreshadowing-and-surprise adventure with a pine smell hinting at a hidden path.",
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, action, obj = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISE_REGISTRY))
    hero = args.hero or rng.choice(["Mina", "Tess", "Lio", "Iris"])
    helper = args.helper or rng.choice([n for n in ["Owen", "Sage", "Noah", "Rin"] if n != hero])
    parent = args.parent or rng.choice(["Rae", "Mara", "Jon", "Tara"])
    return StoryParams(setting=setting, action=action, object=obj, surprise=surprise, hero=hero, helper=helper, parent=parent)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--action", choices=ACTION_REGISTRY)
    ap.add_argument("--object", choices=OBJECT_REGISTRY)
    ap.add_argument("--surprise", choices=SURPRISE_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
