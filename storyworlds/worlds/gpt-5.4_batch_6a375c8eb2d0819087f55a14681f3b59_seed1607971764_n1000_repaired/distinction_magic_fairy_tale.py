#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py
==========================================================

A standalone story world for a small fairy-tale domain about a child who longs
for distinction, takes a selfish magical shortcut, and learns that the brightest
kind of distinction is the kind that helps everyone.

The world model tracks magical glow as a physical meter and pride, worry, guilt,
and relief as emotional memes. A helper fairy can predict the consequence of a
draining spell before it is cast. The story then branches into a restored ending
or a faded cautionary ending depending on whether the chosen repair is strong
enough to undo the harm in time.

Run it
------
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py --trace --seed 11
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/distinction_magic_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    attrs: dict = field(default_factory=dict)
    luminous: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "queen", "mother", "woman"}
        male = {"boy", "fairy_boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
    path: str
    gathering: str
    image: str
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
class Craft:
    id: str
    label: str
    phrase: str
    finish: str
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
class Source:
    id: str
    label: str
    phrase: str
    kind: str
    shared_use: str
    dim_image: str
    restore_image: str
    fragility: int
    luminous: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"
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
class Spell:
    id: str
    label: str
    incantation: str
    pull_text: str
    power: int
    sense: int
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
class Repair:
    id: str
    label: str
    text: str
    fail_text: str
    qa_text: str
    supports: set[str] = field(default_factory=set)
    power: int = 0
    sense: int = 0
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


def _r_dimness(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    place = world.entities.get("place")
    helper = world.entities.get("helper")
    hero = world.entities.get("hero")
    if source is None or place is None or helper is None or hero is None:
        return out
    if source.meters["glow"] >= THRESHOLD:
        return out
    sig = ("dimness", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["dimness"] += 1
    helper.memes["worry"] += 1
    hero.memes["guilt_seed"] += 1
    out.append("__dim__")
    return out


def _r_overbright(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    hero = world.entities.get("hero")
    source = world.entities.get("source")
    if craft is None or hero is None or source is None:
        return out
    if craft.meters["glow"] < 2 or source.meters["glow"] >= THRESHOLD:
        return out
    sig = ("overbright", craft.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["guilt"] += 1
    out.append("__guilt__")
    return out


CAUSAL_RULES = [
    Rule(name="dimness", tag="physical", apply=_r_dimness),
    Rule(name="overbright", tag="emotional", apply=_r_overbright),
]


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


def source_at_risk(spell: Spell, source: Source) -> bool:
    return spell.power > 0 and source.luminous


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_supports(source: Source, repair: Repair) -> bool:
    return source.kind in repair.supports


def drain_severity(source: Source, delay: int) -> int:
    return source.fragility + delay


def is_restored(source: Source, repair: Repair, delay: int) -> bool:
    return repair.power >= drain_severity(source, delay)


def best_repair() -> Repair:
    return max(REPAIRS.values(), key=lambda r: (r.sense, r.power))


def predict_dimness(world: World) -> dict:
    sim = world.copy()
    cast_distinction(sim, narrate=False)
    return {
        "source_dim": sim.get("source").meters["glow"] < THRESHOLD,
        "place_dim": sim.get("place").meters["dimness"],
    }


def introduce(world: World, hero: Entity, helper: Entity, queen: Entity,
              craft_cfg: Craft) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once, in {world.setting.place}, a young fairy named {hero.id} was helping "
        f"prepare {world.setting.gathering}. {world.setting.image}"
    )
    world.say(
        f"{hero.id} was making {craft_cfg.phrase}, and more than anything, "
        f"{hero.pronoun()} wished it might win a little distinction."
    )
    world.say(
        f"{helper.id}, {hero.pronoun('possessive')} dear friend, sorted ribbons nearby, "
        f"while Queen {queen.id} walked the meadow to see that every light was kind."
    )


def show_source(world: World, source: Source) -> None:
    world.say(
        f"At the edge of {world.setting.path} shone {source.phrase}, whose magic "
        f"guided everyone on the way to the feast."
    )


def temptation(world: World, hero: Entity, spell: Spell, craft_cfg: Craft, source: Source) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"Then {hero.id} noticed that {source.the} glimmered more sweetly than "
        f"{hero.pronoun('possessive')} own work. A bold thought fluttered into "
        f"{hero.pronoun('possessive')} mind."
    )
    world.say(
        f'"If I whisper {spell.incantation}," {hero.pronoun()} thought, '
        f'"my {craft_cfg.label} may shine enough for everyone to notice."'
    )


def warning(world: World, helper: Entity, hero: Entity, source: Source) -> None:
    pred = predict_dimness(world)
    helper.memes["worry"] += 1
    world.facts["predicted_dimness"] = pred["place_dim"]
    world.say(
        f'{helper.id} saw where {hero.id} was looking and shook {helper.pronoun("possessive")} '
        f'head. "{source.The} lights {source.shared_use}," {helper.pronoun()} said.'
    )
    if pred["source_dim"]:
        world.say(
            f'"If you pull its glow away, {world.setting.path} will grow dim, and '
            f'other fairies will lose the gentle light that leads them in."'
        )


def defy(world: World, hero: Entity, helper: Entity, spell: Spell) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But the wish for distinction tugged harder than the warning. '
        f'"Only a little," {hero.id} whispered, and {hero.pronoun()} lifted '
        f"{hero.pronoun('possessive')} wand."
    )
    world.say(f"{helper.id} reached out, but the spell had already begun.")


def cast_distinction(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    craft = world.get("craft")
    source = world.get("source")
    spell = world.facts["spell"]
    source.meters["glow"] -= 1
    craft.meters["glow"] += spell.power
    hero.memes["pride"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{spell.pull_text} A silver thread of brightness slipped from "
            f"{source.the} into {hero.id}'s {world.facts['craft_cfg'].label}."
        )


def consequence(world: World, hero: Entity, helper: Entity, source: Source, craft_cfg: Craft) -> None:
    world.say(
        f"For one breath, {hero.id}'s {craft_cfg.label} blazed like a tiny star. "
        f"Then {source.dim_image}"
    )
    world.say(
        f"The path grew uncertain, and the fairies hurrying to the feast slowed and "
        f"looked around. {helper.id}'s face fell."
    )
    if hero.memes["guilt"] >= THRESHOLD:
        world.say(
            f"{hero.id} saw the dim place {hero.pronoun()} had made and felt the bright "
            f"shine on {hero.pronoun('possessive')} own work turn heavy in "
            f"{hero.pronoun('possessive')} hands."
        )


def queen_arrives(world: World, queen: Entity, hero: Entity) -> None:
    world.say(
        f"Queen {queen.id} came on soft wings and understood the trouble at once. "
        f'She did not speak sharply. "Little one," she said, "distinction that steals '
        f"light grows dull very quickly."
    )
    world.say(
        f'"True distinction helps the whole circle shine. Now we must mend what was '
        f'taken."'
    )
    hero.memes["guilt"] += 1


def restore(world: World, hero: Entity, helper: Entity, queen: Entity,
            source: Source, repair: Repair, craft_cfg: Craft) -> None:
    world.get("source").meters["glow"] = 1.0
    world.get("place").meters["dimness"] = 0.0
    world.get("craft").meters["glow"] = 1.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Together they {repair.text.format(source=source.label)}."
    )
    world.say(
        f"Soon {source.restore_image}, and the winding way shone clear again. "
        f"{hero.id}'s {craft_cfg.label} still glowed, but now it glowed gently, as if it "
        f"were happy to belong among the rest."
    )
    world.say(
        f'At the feast, Queen {queen.id} touched {hero.id} on the brow and said, '
        f'"You earned your distinction after all -- not for taking the most light, '
        f'but for returning it."'
    )
    world.say(
        f"{hero.id} smiled at {helper.id}, and the two friends carried the "
        f"{craft_cfg.label} beside the bright path together."
    )


def fail_restore(world: World, hero: Entity, helper: Entity, queen: Entity,
                 source: Source, repair: Repair) -> None:
    world.get("place").meters["dimness"] += 1.0
    hero.memes["lesson"] += 1
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"Together they {repair.fail_text.format(source=source.label)}, but the lost glow "
        f"would not wholly come back before the feast began."
    )
    world.say(
        f"{world.setting.path.capitalize()} stayed dusky, and the dancers moved carefully "
        f"in the half-light. Queen {queen.id} kept everyone safe, but the merriest sparkle "
        f"never quite returned that night."
    )
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} wand close and whispered an apology "
        f"to {helper.id} and to {source.the}. From then on, {hero.pronoun()} would rather "
        f"be known for a steady kindness than for a stolen gleam."
    )
@dataclass
class StoryParams:
    setting: str
    craft: str
    spell: str
    source: str
    repair: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    queen_name: str
    delay: int = 0
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


KNOWLEDGE = {
    "distinction": [(
        "What does distinction mean?",
        "Distinction means being noticed in a special way. The best kind of distinction comes from doing something truly good or beautiful."
    )],
    "magic": [(
        "What is magic in a fairy tale?",
        "Magic in a fairy tale is a special power that can change how things look or act. It often shows what is in a character's heart, too."
    )],
    "sharing": [(
        "Why is sharing important?",
        "Sharing lets good things help more than one person. When everyone has enough, a happy place feels brighter for all."
    )],
    "dew": [(
        "What is dew?",
        "Dew is tiny drops of water that gather on grass and petals when the air turns cool. In fairy tales, dew is often treated like gentle morning treasure."
    )],
    "song": [(
        "Why do fairy tales use songs as magic?",
        "Songs are gentle ways to guide magic because they can calm, gather, or invite. A song can feel kinder than a command."
    )],
    "flower": [(
        "Why do flowers matter in fairy tales?",
        "Flowers often stand for beauty, growth, and care. When a flower closes or opens, it can show how the whole place is feeling."
    )],
    "firefly": [(
        "Why do fireflies glow?",
        "Fireflies make light in their bodies. Their glow helps them signal in the dark, and in stories it can feel like living lantern-light."
    )],
    "water": [(
        "Why can water reflect light?",
        "Still water can act a little like a mirror, sending light back to your eyes. That is why moonlight can look silver on a pond."
    )],
}
KNOWLEDGE_ORDER = ["distinction", "magic", "sharing", "dew", "song", "flower", "firefly", "water"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    craft = f["craft_kind"]
    source = f["source_kind"]
    if f["outcome"] == "restored":
        return [
            'Write a short fairy tale about a young fairy who longs for distinction and borrows magic the wrong way, then learns to set it right.',
            f"Tell a gentle fairy-tale story where {hero.id} steals glow from {source.label} to brighten a {craft.label}, but learns that true distinction means helping everyone shine.",
            f'Write a magical bedtime story that includes the word "distinction" and ends with a bright path, a repaired mistake, and a lesson about sharing light.',
        ]
    return [
        'Write a cautionary fairy tale about a young fairy who longs for distinction and uses magic selfishly.',
        f"Tell a fairy-tale story where {hero.id} drains glow from {source.label} to brighten a {craft.label}, but cannot mend the harm before the feast begins.",
        f'Write a magical story that includes the word "distinction" and teaches that stolen brightness never feels as lovely as kindness.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    queen = f["queen"]
    craft = f["craft_kind"]
    source = f["source_kind"]
    repair = f["repair_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young fairy named {hero.id}, {hero.pronoun('possessive')} friend {helper.id}, and Queen {queen.id}. They are preparing a feast in a magical place."
        ),
        (
            f"Why did {hero.id} use magic on the {craft.label}?",
            f"{hero.id} wanted the {craft.label} to win a little distinction and be noticed by everyone. That wish made the selfish shortcut feel tempting."
        ),
        (
            f"Why did {helper.id} warn {hero.id} not to take glow from {source.label}?",
            f"{helper.id} knew {source.label} was lighting {source.shared_use}. If its glow was pulled away, the path to the feast would grow dim for other fairies."
        ),
    ]
    if f["outcome"] == "restored":
        qa.extend([
            (
                "How did they fix the problem?",
                f"They used {repair.label}, and the borrowed glow was guided back where it belonged. Because they mended the shared light, the path shone safely again."
            ),
            (
                f"What did Queen {queen.id} teach about distinction?",
                f'She taught that true distinction does not come from stealing the brightest glow for yourself. It comes from making the whole circle brighter and kinder.'
            ),
            (
                "How did the story end?",
                f"It ended with the path bright again and {hero.id}'s {craft.label} shining gently among the other lights. The ending shows that {hero.id} changed from wanting attention alone to caring for everyone."
            ),
        ])
    else:
        qa.extend([
            (
                "Were they able to fix everything before the feast?",
                f"No. They tried {repair.label}, but the lost glow did not fully return in time. Because the repair was too weak for the harm, the feast began in a dimmer light."
            ),
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned that a stolen gleam is not worth the trouble it causes others. The lesson stayed strong because {hero.pronoun()} had to see the whole feast grow quieter and darker."
            ),
            (
                "How did the story end?",
                f"It ended with everyone safe but the celebration less bright than it should have been. That sad ending proves that selfish magic can leave a mark even after an apology."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"distinction", "magic"}
    if f["repair_cfg"].id == "sharing_spell":
        tags.add("sharing")
    if f["repair_cfg"].id == "dew_cup":
        tags.add("dew")
    if f["repair_cfg"].id == "lullaby_call":
        tags.add("song")
    tags |= set(f["source_kind"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.luminous:
            bits.append("luminous=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_meadow",
        craft="lantern",
        spell="distinction_whisper",
        source="moonflowers",
        repair="sharing_spell",
        hero_name="Liora",
        hero_type="fairy_girl",
        helper_name="Pip",
        helper_type="fairy_boy",
        queen_name="Mab",
        delay=0,
    ),
    StoryParams(
        setting="lily_pond",
        craft="garland",
        spell="proud_spark",
        source="fireflies",
        repair="lullaby_call",
        hero_name="Tansy",
        hero_type="fairy_girl",
        helper_name="Rowan",
        helper_type="fairy_boy",
        queen_name="Iris",
        delay=0,
    ),
    StoryParams(
        setting="crystal_glen",
        craft="crown",
        spell="royal_glitter",
        source="wishing_pool",
        repair="dew_cup",
        hero_name="Mira",
        hero_type="fairy_girl",
        helper_name="Alder",
        helper_type="fairy_boy",
        queen_name="Selka",
        delay=1,
    ),
    StoryParams(
        setting="moon_meadow",
        craft="crown",
        spell="royal_glitter",
        source="moonflowers",
        repair="lullaby_call",
        hero_name="Elowen",
        hero_type="fairy_girl",
        helper_name="Finn",
        helper_type="fairy_boy",
        queen_name="Mab",
        delay=2,
    ),
    StoryParams(
        setting="lily_pond",
        craft="lantern",
        spell="distinction_whisper",
        source="wishing_pool",
        repair="sharing_spell",
        hero_name="Nessa",
        hero_type="fairy_girl",
        helper_name="Bram",
        helper_type="fairy_boy",
        queen_name="Iris",
        delay=1,
    ),
]


def explain_rejection(source: Source, spell: Spell) -> str:
    if not source.luminous:
        return (
            f"(No story: {source.phrase} does not hold shareable glow, so {spell.label} "
            f"cannot honestly drain any light from it. Pick moonflowers, fireflies, or the wishing pool.)"
        )
    return "(No story: this spell and source do not make a reasonable magical problem.)"


def explain_repair(source: Source, repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    if repair.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_repairs() if repair_supports(source, r)))
        return (
            f"(Refusing repair '{repair_id}': it is too weak-minded for this world "
            f"(sense={repair.sense} < {SENSE_MIN}). Try one that actually restores the lost glow: {better}.)"
        )
    if not repair_supports(source, repair):
        choices = ", ".join(sorted(r.id for r in sensible_repairs() if repair_supports(source, r)))
        return (
            f"(No story: {repair.label} does not fit {source.label}. Pick a repair that works for "
            f"{source.kind}: {choices}.)"
        )
    return "(No story: that repair does not fit this source.)"


def outcome_of(params: StoryParams) -> str:
    source = SOURCES[params.source]
    repair = REPAIRS[params.repair]
    return "restored" if is_restored(source, repair, params.delay) else "faded"


ASP_RULES = r"""
hazard(Sp, So) :- spell(Sp), source(So), drains(Sp), luminous(So).
sensible_repair(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
supports_source(R, So) :- repair_support(R, K), source_kind(So, K).
valid(St, Cr, Sp, So) :- setting(St), craft(Cr), hazard(Sp, So), source(So),
                         exists_fix(So).
exists_fix(So) :- sensible_repair(R), supports_source(R, So).

severity(F + D) :- chosen_source(So), fragility(So, F), delay(D).
restored :- chosen_repair(R), sensible_repair(R), chosen_source(So),
            supports_source(R, So), repair_power(R, P), severity(V), P >= V.
outcome(restored) :- restored.
outcome(faded) :- not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for craft_id in CRAFTS:
        lines.append(asp.fact("craft", craft_id))
    for spell_id, spell in SPELLS.items():
        lines.append(asp.fact("spell", spell_id))
        if spell.power > 0:
            lines.append(asp.fact("drains", spell_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_kind", source_id, source.kind))
        lines.append(asp.fact("fragility", source_id, source.fragility))
        if source.luminous:
            lines.append(asp.fact("luminous", source_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
        for kind in sorted(repair.supports):
            lines.append(asp.fact("repair_support", repair_id, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_repair", params.repair),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible_repairs())
    p_sens = {r.id for r in sensible_repairs()}
    if c_sens == p_sens:
        print(f"OK: sensible repairs match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a magical shortcut, a dim path, and a lesson about true distinction."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the glow stays missing before the repair is tried")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = FAIRY_GIRL_NAMES if gender == "fairy_girl" else FAIRY_BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.spell:
        source = SOURCES[args.source]
        spell = SPELLS[args.spell]
        if not source_at_risk(spell, source):
            raise StoryError(explain_rejection(source, spell))
    if args.source and args.repair:
        source = SOURCES[args.source]
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN or not repair_supports(source, repair):
            raise StoryError(explain_repair(source, args.repair))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN and args.source is None:
        source = next(s for s in SOURCES.values() if s.luminous)
        raise StoryError(explain_repair(source, args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.craft is None or combo[1] == args.craft)
        and (args.spell is None or combo[2] == args.spell)
        and (args.source is None or combo[3] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, craft_id, spell_id, source_id = rng.choice(sorted(combos))
    source = SOURCES[source_id]

    repair_choices = [
        r.id for r in sensible_repairs()
        if repair_supports(source, r)
        and (args.repair is None or r.id == args.repair)
    ]
    if not repair_choices:
        raise StoryError("(No valid repair matches the given options.)")
    repair_id = rng.choice(sorted(repair_choices))

    hero_type = "fairy_girl"
    helper_type = "fairy_boy"
    hero_name = _pick_name(rng, hero_type)
    helper_name = _pick_name(rng, helper_type, avoid=hero_name)
    queen_name = rng.choice(QUEEN_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        craft=craft_id,
        spell=spell_id,
        source=source_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        queen_name=queen_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.craft not in CRAFTS:
        raise StoryError(f"(Unknown craft: {params.craft})")
    if params.spell not in SPELLS:
        raise StoryError(f"(Unknown spell: {params.spell})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    source = SOURCES[params.source]
    spell = SPELLS[params.spell]
    repair = REPAIRS[params.repair]

    if not source_at_risk(spell, source):
        raise StoryError(explain_rejection(source, spell))
    if repair.sense < SENSE_MIN or not repair_supports(source, repair):
        raise StoryError(explain_repair(source, params.repair))

    world = tell(
        setting=SETTINGS[params.setting],
        craft_cfg=CRAFTS[params.craft],
        spell=spell,
        source_cfg=source,
        repair=repair,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        queen_name=params.queen_name,
        delay=params.delay,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible_repair/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        print(f"{len(combos)} compatible (setting, craft, spell, source) combos:\n")
        for setting_id, craft_id, spell_id, source_id in combos:
            print(f"  {setting_id:13} {craft_id:8} {spell_id:20} {source_id}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = (
                f"### {p.hero_name}: {p.craft} with {p.spell} from {p.source} "
                f"({outcome_of(p)}, repair={p.repair})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(setting: Setting, craft_cfg: Craft, spell: Spell, source_cfg: Source,
         repair: Repair, hero_name: str = "Liora", hero_type: str = "fairy_girl",
         helper_name: str = "Pip", helper_type: str = "fairy_boy",
         queen_name: str = "Mab", delay: int = 0) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            label=hero_name, attrs={}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper",
                              label=helper_name, attrs={}))
    queen = world.add(Entity(id=queen_name, kind="character", type="queen", role="queen",
                             label=queen_name, attrs={}))
    place = world.add(Entity(id="place", kind="thing", type="path", label=setting.path,
                             attrs={}))
    source = world.add(Entity(id="source", kind="thing", type="magic_source", label=source_cfg.label,
                              luminous=source_cfg.luminous, attrs={}))
    craft = world.add(Entity(id="craft", kind="thing", type="craft", label=craft_cfg.label,
                             attrs={}))

    source.meters["glow"] = 1.0
    craft.meters["glow"] = 0.0
    place.meters["dimness"] = 0.0
    hero.memes["guilt"] = 0.0
    helper.memes["worry"] = 0.0

    world.facts["spell"] = spell
    world.facts["craft_cfg"] = craft_cfg
    world.facts["source_cfg"] = source_cfg
    world.facts["repair"] = repair
    world.facts["delay"] = delay

    introduce(world, hero, helper, queen, craft_cfg)
    show_source(world, source_cfg)

    world.para()
    temptation(world, hero, spell, craft_cfg, source_cfg)
    warning(world, helper, hero, source_cfg)
    defy(world, hero, helper, spell)

    world.para()
    cast_distinction(world, narrate=True)
    consequence(world, hero, helper, source_cfg, craft_cfg)

    world.para()
    queen_arrives(world, queen, hero)

    restored = is_restored(source_cfg, repair, delay)
    if restored:
        restore(world, hero, helper, queen, source_cfg, repair, craft_cfg)
        outcome = "restored"
    else:
        fail_restore(world, hero, helper, queen, source_cfg, repair)
        outcome = "faded"

    world.facts.update(
        hero=hero,
        helper=helper,
        queen=queen,
        place=place,
        source=source,
        craft=craft,
        setting=setting,
        craft_kind=craft_cfg,
        source_kind=source_cfg,
        spell_cfg=spell,
        repair_cfg=repair,
        outcome=outcome,
        severity=drain_severity(source_cfg, delay),
        dimmed=place.meters["dimness"] >= THRESHOLD or outcome == "faded",
    )
    return world


SETTINGS = {
    "moon_meadow": Setting(
        id="moon_meadow",
        place="a moonlit meadow beyond the reeds",
        path="the clover path",
        gathering="the Night Blossom Feast",
        image="Blue bells nodded, and every blade of grass wore a little pearl of dew.",
        tags={"meadow", "feast"},
    ),
    "lily_pond": Setting(
        id="lily_pond",
        place="a silver pond ringed with lilies",
        path="the petal bridge",
        gathering="the Moon Dance",
        image="The water held the sky so still that stars seemed to be floating under the leaves.",
        tags={"pond", "dance"},
    ),
    "crystal_glen": Setting(
        id="crystal_glen",
        place="a crystal glen hidden inside the hill",
        path="the glassy stair",
        gathering="the Dew Lantern Supper",
        image="The stones in the bank gleamed faintly, as if they remembered old songs.",
        tags={"glen", "lantern"},
    ),
}

CRAFTS = {
    "lantern": Craft(
        id="lantern",
        label="lantern",
        phrase="a tiny lantern of woven reeds and pearl-thread",
        finish="hung it by the path",
        tags={"lantern"},
    ),
    "garland": Craft(
        id="garland",
        label="garland",
        phrase="a flower garland braided with star-grass",
        finish="laid it on the feast table",
        tags={"garland"},
    ),
    "crown": Craft(
        id="crown",
        label="crown",
        phrase="a moonleaf crown with a satin ribbon",
        finish="set it upon a velvet cushion",
        tags={"crown"},
    ),
}

SOURCES = {
    "moonflowers": Source(
        id="moonflowers",
        label="moonflowers",
        phrase="a bank of moonflowers",
        kind="bloom",
        shared_use="the way for the smallest guests",
        dim_image="the moonflowers folded their pale faces, and their path-light thinned to a hush",
        restore_image="the moonflowers opened wide again, spilling soft milk-white light over the grass",
        fragility=2,
        luminous=True,
        tags={"flower", "light"},
    ),
    "fireflies": Source(
        id="fireflies",
        label="fireflies",
        phrase="a swirl of fireflies in the fern shadows",
        kind="swarm",
        shared_use="the dancing ring",
        dim_image="the fireflies drifted apart like sleepy embers, leaving dark pockets among the ferns",
        restore_image="the fireflies gathered close again, blinking in merry green-gold loops",
        fragility=1,
        luminous=True,
        tags={"firefly", "light"},
    ),
    "wishing_pool": Source(
        id="wishing_pool",
        label="wishing pool",
        phrase="a wishing pool full of moon-reflections",
        kind="reflection",
        shared_use="the little bridge over the water",
        dim_image="the moon-reflections shattered into gray ripples, and the bridge lost its silver edge",
        restore_image="the water calmed, and the moon returned to it in one bright unbroken ribbon",
        fragility=2,
        luminous=True,
        tags={"water", "light"},
    ),
    "stone_bench": Source(
        id="stone_bench",
        label="stone bench",
        phrase="an old stone bench under ivy",
        kind="stone",
        shared_use="nothing at all",
        dim_image="nothing happened",
        restore_image="nothing changed",
        fragility=0,
        luminous=False,
        tags={"stone"},
    ),
}

SPELLS = {
    "distinction_whisper": Spell(
        id="distinction_whisper",
        label="distinction whisper",
        incantation="the distinction whisper",
        pull_text="The air rang like a spoon against crystal.",
        power=1,
        sense=2,
        tags={"distinction", "magic"},
    ),
    "proud_spark": Spell(
        id="proud_spark",
        label="proud spark",
        incantation="the proud spark",
        pull_text="A sharp little note flew out and twined around the glow like silk thread.",
        power=1,
        sense=2,
        tags={"magic"},
    ),
    "royal_glitter": Spell(
        id="royal_glitter",
        label="royal glitter",
        incantation="royal glitter",
        pull_text="Golden dust spun in a fast bright ring.",
        power=2,
        sense=2,
        tags={"magic", "glitter"},
    ),
}

REPAIRS = {
    "sharing_spell": Repair(
        id="sharing_spell",
        label="sharing spell",
        text="joined hands and sang the sharing spell until the borrowed shine flowed back into the {source}",
        fail_text="joined hands and sang the sharing spell over the {source}",
        qa_text="They sang a sharing spell that sent the borrowed light back where it belonged.",
        supports={"bloom", "swarm", "reflection"},
        power=3,
        sense=3,
        tags={"sharing", "magic"},
    ),
    "dew_cup": Repair(
        id="dew_cup",
        label="dew-cup blessing",
        text="tipped a dew-cup blessing over the {source} and let moon-dew gather the lost glow",
        fail_text="tipped a dew-cup blessing over the {source}",
        qa_text="They used a dew-cup blessing to gather glow and pour it back.",
        supports={"bloom", "reflection"},
        power=2,
        sense=3,
        tags={"dew", "magic"},
    ),
    "lullaby_call": Repair(
        id="lullaby_call",
        label="lullaby call",
        text="sang a lullaby call that coaxed the {source} home to its own merry brightness",
        fail_text="sang a lullaby call toward the {source}",
        qa_text="They sang a lullaby call to coax the light back.",
        supports={"swarm"},
        power=1,
        sense=2,
        tags={"song", "magic"},
    ),
    "extra_glitter": Repair(
        id="extra_glitter",
        label="extra glitter",
        text="threw extra glitter at the {source}",
        fail_text="threw extra glitter at the {source}",
        qa_text="They only threw extra glitter over it.",
        supports=set(),
        power=0,
        sense=1,
        tags={"glitter"},
    ),
}

FAIRY_GIRL_NAMES = ["Liora", "Tansy", "Mira", "Elowen", "Nessa", "Briony"]
FAIRY_BOY_NAMES = ["Pip", "Rowan", "Alder", "Finn", "Moss", "Bram"]
QUEEN_NAMES = ["Mab", "Iris", "Selka"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    repairs = sensible_repairs()
    for setting_id in SETTINGS:
        for craft_id in CRAFTS:
            for spell_id, spell in SPELLS.items():
                for source_id, source in SOURCES.items():
                    if not source_at_risk(spell, source):
                        continue
                    if any(repair_supports(source, r) for r in repairs):
                        combos.append((setting_id, craft_id, spell_id, source_id))
    return combos

if __name__ == "__main__":
    main()
