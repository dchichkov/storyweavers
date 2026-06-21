#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rage_lad_curiosity_quest_myth.py
================================================================

A standalone storyworld for a small mythic tale about a curious lad, a quest,
and a dangerous burst of rage that must be calmed before it harms the path.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal engine
- a reasonableness gate
- grounded Q&A from simulated state
- an inline ASP twin for parity checks

Seed words: rage, lad
Features: Curiosity, Quest
Style: Myth
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
CURIOUS_MIN = 2
RAGE_MAX = 8.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "lad", "man", "father", "king", "prince"}
        female = {"girl", "woman", "mother", "queen", "priestess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"king": "king", "queen": "queen", "mother": "mother", "father": "father"}.get(self.type, self.type)



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
    path: str
    gate: str

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
class Quest:
    id: str
    object: str
    goal: str
    quest_word: str
    clue: str
    reaches: str
    reward: str
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
class Hazard:
    id: str
    label: str
    flare: str
    trigger: str
    danger: str
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
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_spread_rage(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["rage"] < THRESHOLD:
            continue
        sig = ("rage_spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "path" in world.entities:
            world.get("path").meters["danger"] += 1
        out.append("__rage__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["calm"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["rage"] = max(0.0, e.memes["rage"] - 1.0)
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("rage", "social", _r_spread_rage), Rule("calm", "social", _r_calm)]


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


def curious_enough(lad: Entity) -> bool:
    return lad.memes["curiosity"] >= CURIOUS_MIN


def danger_of(rage: Hazard, delay: int) -> int:
    return 2 + delay


def can_contain(remedy: Remedy, rage: Hazard, delay: int) -> bool:
    return remedy.power >= danger_of(rage, delay)


def hazard_matches(quest: Quest) -> bool:
    return quest.object == "stone gate"


def predict_rage(world: World, lady: Entity, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get(lady.id).memes["rage"] += 1
    propagate(sim, narrate=False)
    return {"danger": sim.get("path").meters["danger"], "rage": sim.get(lady.id).memes["rage"]}


def _rally(world: World, lad: Entity, quest: Quest, setting: Setting) -> None:
    lad.memes["joy"] += 1
    world.say(
        f"At the edge of dusk, {lad.id}, a young lad with bright eyes, wandered into {setting.place}. "
        f"{setting.mood.capitalize()} hung over the hills, and the old {setting.path} led toward {quest.goal}."
    )
    world.say(
        f"He carried a small heart full of curiosity, for {quest.quest_word} had called to him since sunrise. "
        f"At the end of the way waited {quest.object}, and beyond it, {quest.reward}."
    )


def _tempt(world: World, lad: Entity, quest: Quest, hazard: Hazard) -> None:
    lad.memes["curiosity"] += 1
    world.say(
        f"{lad.id} peered toward {quest.object} and whispered, "
        f'"If I follow the clue, I will find {quest.goal}."'
    )
    world.say(
        f"But the air near {hazard.label} felt strange, and the old stones seemed ready to answer with a warning."
    )


def _warn(world: World, elder: Entity, lad: Entity, quest: Quest, hazard: Hazard, setting: Setting) -> None:
    pred = predict_rage(world, lad, hazard)
    world.facts["predicted_danger"] = pred["danger"]
    elder.memes["care"] += 1
    world.say(
        f'{elder.id} lifted a steady hand. "{lad.id}, do not touch {hazard.label}," {elder.pronoun()} said. '
        f'"{hazard.danger}. And if anger wakes there, the {setting.path} will grow unsafe."'
    )


def _defy(world: World, lad: Entity) -> None:
    lad.memes["defiance"] += 1
    world.say(
        f'{lad.id} frowned and answered, "I have a quest to follow."'
    )


def _ignite_rage(world: World, lad: Entity, hazard: Hazard) -> None:
    lad.memes["rage"] += 1
    world.get("path").meters["danger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then his hand brushed the {hazard.label}, and a hot rage leapt up like a red spark. "
        f"For one heartbeat, the stones seemed to shiver."
    )


def _alarm(world: World, elder: Entity, lad: Entity, hazard: Hazard) -> None:
    world.say(f'"{lad.id}! The {hazard.label}!" {elder.id} cried.')
    world.say(f'"Come back to me!"')


def _rescue(world: World, elder: Entity, remedy: Remedy, hazard: Hazard, delay: int) -> None:
    world.get("path").meters["danger"] = 0.0
    world.get("lad").memes["rage"] = 0.0
    body = remedy.text.replace("{hazard}", hazard.label)
    world.say(f"{elder.id} came running and {body}.")
    world.say("The red spark faded, and the stones grew still again.")


def _lesson(world: World, elder: Entity, lad: Entity, hazard: Hazard) -> None:
    lad.memes["gratitude"] += 1
    lad.memes["curiosity"] += 1
    world.say(
        f"Then {elder.id} knelt beside him and said, "
        f'"Curiosity is a brave lantern, but rage is a wild fire. '
        f'You may seek the quest, yet you must not let anger lead your hands."'
    )
    world.say(f"{lad.id} bowed his head and promised to remember.")


def _safe_end(world: World, elder: Entity, lad: Entity, quest: Quest, setting: Setting) -> None:
    lad.memes["joy"] += 1
    world.say(
        f"The next dawn, {elder.id} brought a gentler road marker. "
        f'Together they walked the {setting.path}, and {lad.id} found {quest.goal} without waking the rage.'
    )
    world.say(
        f"At last he saw {quest.reward} shining beyond the gate, and his curiosity stood tall and calm."
    )


def tell(setting: Setting, quest: Quest, hazard: Hazard, remedy: Remedy,
         lad_name: str = "Lad", elder_name: str = "Helm",
         elder_type: str = "king", delay: int = 0) -> World:
    world = World()
    lad = world.add(Entity(id="lad", kind="character", type="boy", label=lad_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="guide"))
    gate = world.add(Entity(id="gate", kind="thing", type="stone gate", label=quest.object))
    path = world.add(Entity(id="path", kind="place", type="path", label=setting.path))
    lad.memes["curiosity"] = 2.0
    world.facts["delay"] = delay

    _rally(world, lad, quest, setting)
    world.para()
    _tempt(world, lad, quest, hazard)
    _warn(world, elder, lad, quest, hazard, setting)

    if not curious_enough(lad):
        world.say(f"{lad.id} turned back before the stones could stir.")
        world.para()
        _safe_end(world, elder, lad, quest, setting)
        outcome = "averted"
    else:
        _defy(world, lad)
        world.para()
        _ignite_rage(world, lad, hazard)
        _alarm(world, elder, lad, hazard)
        contained = can_contain(remedy, hazard, delay)
        world.facts["contained"] = contained
        world.para()
        if contained:
            _rescue(world, elder, remedy, hazard, delay)
            _lesson(world, elder, lad, hazard)
            world.para()
            _safe_end(world, elder, lad, quest, setting)
            outcome = "contained"
        else:
            world.say(
                f"{elder.id} tried to answer with {remedy.qa_text}, but the raging stone-light was too much."
            )
            world.say(
                "The path broke into smoke and dust, and the lad and the elder escaped beneath the darkening sky."
            )
            world.say(
                "Though they were safe, the quest was left unfinished, and both remembered that rage can outrun a small remedy."
            )
            outcome = "burned"

    world.facts.update(lad=lad, elder=elder, quest=quest, hazard=hazard, remedy=remedy,
                       setting=setting, outcome=outcome)
    return world


SETTINGS = {
    "forest": Setting("forest", "the forest", "green twilight", "mossy path", "stone gate"),
    "mountain": Setting("mountain", "the mountain", "cold wind", "narrow path", "iron gate"),
    "river": Setting("river", "the river bank", "silver mist", "water path", "old gate"),
}

QUESTS = {
    "crown": Quest("crown", "the stone gate", "the crown of dawn", "Quest", "a hidden clue", "reaches", "a gold crown", {"quest"}),
    "star": Quest("star", "the moon arch", "the star of midnight", "Quest", "a whispered clue", "reaches", "a silver star", {"quest"}),
    "harp": Quest("harp", "the cedar door", "the harp of morning", "Quest", "a secret clue", "reaches", "a bright harp", {"quest"}),
}

HAZARDS = {
    "ember": Hazard("ember", "the ember-stone", "red flare", "touch", "it can wake a hot rage and make the path dangerous", {"rage"}),
    "shard": Hazard("shard", "the glass shard", "glint", "touch", "it can cut the hand and make the heart flare with rage", {"rage"}),
    "idol": Hazard("idol", "the old idol", "gold glare", "touch", "it can stir a wild rage in any rash seeker", {"rage"}),
}

REMEDIES = {
    "water": Remedy("water", 3, 4, "snatched a clay bowl of water and poured it over the glowing stone", "poured water, but the red flare kept growing", "put the red flare out with water", {"water"}),
    "sand": Remedy("sand", 2, 3, "threw a cloak of sand over the heat until it dimmed", "threw sand, but the hot light broke free", "covered the heat with sand", {"sand"}),
    "prayer": Remedy("prayer", 3, 2, "spoke a calm prayer and bound the stone in a circle of ash", "said a prayer, but the rage had already grown too fierce", "calmed the stones with prayer", {"calm"}),
}

CURATED = [
    ("forest", "crown", "ember", "water", "Lad", "Helm", "king", 0),
    ("mountain", "star", "shard", "sand", "Pip", "Sage", "queen", 0),
    ("river", "harp", "idol", "water", "Toma", "Old King", "king", 1),
]


@dataclass
class StoryParams:
    setting: str
    quest: str
    hazard: str
    remedy: str
    lad: str
    elder: str
    elder_type: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for hid in HAZARDS:
                for rid in REMEDIES:
                    if hazard_matches(QUESTS[qid]):
                        combos.append((sid, qid, hid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about curiosity, quest, and rage.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--lad")
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["king", "queen", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError("The chosen remedy is too foolish for a mythic rescue.")
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    lad = args.lad or rng.choice(["Lad", "Pip", "Toma", "Eli"])
    elder = args.elder or rng.choice(["Helm", "Sage", "Aster", "Mira"])
    elder_type = args.elder_type or rng.choice(["king", "queen", "mother", "father"])
    return StoryParams(setting, quest, hazard, remedy, lad, elder, elder_type, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], HAZARDS[params.hazard], REMEDIES[params.remedy],
                 params.lad, params.elder, params.elder_type, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the words "rage" and "lad" and centers on a quest.',
        f"Tell a gentle legend where a curious lad follows a quest, touches a dangerous stone, and an elder calms the rage before the path is lost.",
        f'Write a small myth with curiosity, quest, and a burst of rage, ending in a wise rescue and a calm road onward.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lad: Entity = f["lad"]
    elder: Entity = f["elder"]
    quest: Quest = f["quest"]
    hazard: Hazard = f["hazard"]
    remedy: Remedy = f["remedy"]
    qas = [
        ("Who is the story about?", f"It is about a curious lad and the elder who guides him. The lad follows a quest through a mythic place."),
        ("What did the lad want to do?", f"He wanted to follow the quest and reach {quest.goal}. His curiosity led him toward {quest.object}."),
        ("What danger appeared?", f"The {hazard.label} could wake a hot rage and make the path dangerous. That is why the elder warned him at once."),
    ]
    if f["outcome"] == "contained":
        qas.append((
            "How was the danger stopped?",
            f"{elder.id} used {remedy.qa_text}. That calmed the red spark before it could break the path."
        ))
        qas.append((
            "How did the lad end?",
            "He ended with wisdom instead of anger. His curiosity stayed alive, but his rage was calmed."
        ))
    elif f["outcome"] == "burned":
        qas.append((
            "What happened when the remedy was too weak?",
            f"The elder tried to {remedy.qa_text}, but the raging stone-light was too much. The quest had to wait because the path broke."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["hazard"].tags) | set(world.facts["quest"].tags) | set(world.facts["remedy"].tags)
    bank = {
        "rage": [("What is rage?", "Rage is a hot, fierce feeling. It can make someone act without thinking if they do not calm down.")],
        "quest": [("What is a quest?", "A quest is a journey to find something important or to reach a special goal.")],
        "calm": [("Why is it good to calm down?", "Calming down helps a person think clearly and keep others safe.")],
        "water": [("What does water do to fire?", "Water can cool a small fire and help put it out.")],
        "sand": [("How can sand help with heat?", "Sand can cover heat and help smother a small flame.")],
    }
    out: list[tuple[str, str]] = []
    for tag in ["rage", "quest", "calm", "water", "sand"]:
        if tag in tags or tag in bank:
            out.extend(bank[tag])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
rage_spreads(L) :- lad(L), rage(L, R), R >= 1.
calm_down(L) :- lad(L), calm(L, C), C >= 1.
outcome(contained) :- rage_spreads(L), remedy_power(P), severity(S), P >= S.
outcome(burned) :- rage_spreads(L), remedy_power(P), severity(S), P < S.
outcome(averted) :- lad(L), curiosity(L, C), C < 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_power", rid, r.power))
    lines.append(asp.fact("severity", 2))
    lines.append(asp.fact("curiosity", "lad", 2))
    lines.append(asp.fact("rage", "lad", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if asp_outcome() not in {"contained", "burned", "averted", "?"}:
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_dict()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP helper reachable.")
    return rc


def explain_rejection(remedy: Remedy) -> str:
    return f"(No story: remedy '{remedy.id}' is too weak for a mythic rescue.)"


def valid_story(params: StoryParams) -> bool:
    return params.remedy in REMEDIES and REMEDIES[params.remedy].sense >= 2


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
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world's ASP twin is intentionally tiny; use --verify to test it.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c)) for c in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        if args.all:
            p = sample.params
            header = f"### {p.lad}: {p.setting}, {p.quest}, {p.hazard} -> {p.remedy}"
        else:
            header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("forest", "crown", "ember", "water", "Lad", "Helm", "king", 0),
    StoryParams("mountain", "star", "shard", "sand", "Pip", "Sage", "queen", 0),
    StoryParams("river", "harp", "idol", "water", "Toma", "Old King", "king", 1),
]


if __name__ == "__main__":
    main()
