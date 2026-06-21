#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/taffy_crab_bravery_sharing_folk_tale.py
=======================================================================

A small folk-tale storyworld about a brave child, a crab on the shore, and a
sweet piece of taffy that is shared at just the right moment.

Premise
-------
A child walks to the tide pools with a wrapper of taffy. The wind is strong,
the path is tricky, and a crab needs help getting back to the water. The child
must choose whether to keep the treat, share it, or use the sweetness and
bravery of the moment to help the crab and a smaller companion.

This world keeps the simulation small but real:
- entities have physical meters and emotional memes,
- a forward rule engine drives the middle turn,
- the ending is different depending on whether the child shares well and acts
  bravely,
- the prose is authored from world state rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/taffy_crab_bravery_sharing_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/taffy_crab_bravery_sharing_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/taffy_crab_bravery_sharing_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/taffy_crab_bravery_sharing_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/taffy_crab_bravery_sharing_folk_tale.py --verify
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
BRAVERY_START = 5.0
SHARING_START = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
class Shore:
    id: str
    label: str
    tide: str
    wind: str
    path: str
    dark_place: str
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
class Sweet:
    id: str
    label: str
    phrase: str
    crumb: str
    shiny: str
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
class Creature:
    id: str
    label: str
    phrase: str
    pinch: str
    shell: str
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
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters["shared"] < THRESHOLD:
            continue
        sig = ("share", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["warmth"] += 1
        companion = world.entities.get("companion")
        if companion is not None:
            companion.memes["comfort"] += 1
        crab = world.entities.get("crab")
        if crab is not None:
            crab.meters["fed"] += 1
            crab.memes["trust"] += 1
        out.append("__share__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None or hero.meters["courage"] < THRESHOLD:
        return out
    sig = ("brave", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("share", _r_share), Rule("bravery", _r_bravery)]


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


def reasonableness_gate(shares: bool, help_needs_bravery: bool) -> bool:
    return shares and help_needs_bravery


def best_help() -> HelpAction:
    return max(HELP_ACTIONS.values(), key=lambda h: h.sense)


def required_power(distance: int, wind: int) -> int:
    return distance + wind


def can_help(action: HelpAction, distance: int, wind: int) -> bool:
    return action.power >= required_power(distance, wind)


def predict_world(world: World) -> dict:
    sim = world.copy()
    _help_crab(sim, narrate=False)
    return {
        "shared": sim.get("hero").meters["shared"] >= THRESHOLD,
        "courage": sim.get("hero").meters["courage"] >= THRESHOLD,
        "crab_trust": sim.get("crab").meters["fed"] >= THRESHOLD,
    }


def _help_crab(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    companion = world.entities.get("companion")
    crab = world.get("crab")
    hero.meters["courage"] += 1
    hero.meters["shared"] += 1
    hero.meters["shared_sweet"] += 1
    if companion is not None:
        companion.memes["hope"] += 1
    crab.meters["fed"] += 1
    crab.memes["trust"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, companion: Entity, shore: Shore, sweet: Sweet, crab: Creature) -> None:
    hero.memes["curiosity"] += 1
    companion.memes["curiosity"] += 1
    world.say(
        f"On a bright morning by {shore.label}, {hero.id} and {companion.id} walked "
        f"where the tide left little pools that glimmered like glass."
    )
    world.say(
        f"{hero.id} carried {sweet.phrase} in a little wrapper, and {companion.id} "
        f"kept peeking toward the water."
    )
    world.say(
        f"Near {shore.dark_place}, a {crab.label} was stuck between a rock and the foam, "
        f"its {crab.shell} shining after the spray."
    )


def need(world: World, hero: Entity, shore: Shore) -> None:
    world.say(
        f"But the path was narrow, and the {shore.wind} wind kept tugging at sleeves "
        f"and turning the puddles silver."
    )
    world.say(
        f'{hero.id} looked at the crab and whispered, "I can help, but I need a brave way to do it."'
    )


def tempt(world: World, hero: Entity, sweet: Sweet) -> None:
    hero.memes["wanting"] += 1
    world.say(
        f"{hero.id} glanced at {sweet.phrase}. Its {sweet.shiny} shine made the treat look too good to lose."
    )
    world.say(
        f'For a moment, {hero.id} wanted to keep the whole sweet piece to {hero.pronoun("object")}self.'
    )


def choose_share(world: World, hero: Entity, companion: Entity, sweet: Sweet) -> None:
    hero.meters["shared"] += 1
    companion.meters["kindness"] += 1
    world.say(
        f"Then {hero.id} broke the taffy into two sticky pieces and handed one to {companion.id}."
    )
    world.say(
        f'Together they held the sweet crumbs out like a tiny feast, and the crab waved its claws toward them.'
    )


def show_bravery(world: World, hero: Entity, crab: Creature) -> None:
    hero.meters["courage"] += 1
    world.say(
        f"{hero.id} took a breath, stepped over the wet stone, and reached toward the crab instead of stepping back."
    )
    world.say(
        f"That brave little move calmed the crab long enough for it to scuttle to a safer pool."
    )


def rescue(world: World, action: HelpAction, shore: Shore, sweet: Sweet, crab: Creature) -> None:
    body = action.text.replace("{target}", crab.label)
    world.say(
        f"With a steady hand, {body}."
    )
    world.say(
        f"The crab clicked happily into the tide, and the taffy crumbs glowed in the sun like little gold coins."
    )


def lesson(world: World, hero: Entity, companion: Entity, sweet: Sweet, crab: Creature) -> None:
    hero.memes["pride"] += 1
    companion.memes["pride"] += 1
    world.say(
        f"For a moment nobody spoke. Then {companion.id} smiled and said that sharing had made the sweet feel larger, not smaller."
    )
    world.say(
        f"{hero.id} nodded, because the brave thing had been to give away the {sweet.label} and the kind thing had been to save the {crab.label}."
    )


def ending(world: World, hero: Entity, companion: Entity, sweet: Sweet, shore: Shore, crab: Creature) -> None:
    world.say(
        f"By sunset the water was calm again, {companion.id} had sticky fingers, and {hero.id} walked home with an empty wrapper and a warm heart."
    )
    world.say(
        f"Behind them, the little {crab.label} chattered in the shallows, safe at last."
    )


def failed_help(world: World, action: HelpAction, shore: Shore, crab: Creature) -> None:
    world.say(
        f"{action.fail.replace('{target}', crab.label)}"
    )
    world.say(
        f"The wind kept pushing spray across the stones, and the crab stayed trapped until the tide changed."
    )


def sad_end(world: World, hero: Entity, companion: Entity, sweet: Sweet, crab: Creature) -> None:
    world.say(
        f"Even so, {hero.id} learned that bravery without sharing was only half a song."
    )
    world.say(
        f"They went home with the last of the taffy untouched, wishing they had used it to help sooner."
    )


def tell(params: "StoryParams") -> World:
    if params.shore not in SHORE_REGISTRY or params.sweet not in SWEET_REGISTRY or params.crab not in CRAB_REGISTRY or params.help_action not in HELP_ACTIONS:
        raise StoryError("Unknown story parameters.")
    world = World()
    shore = SHORE_REGISTRY[params.shore]
    sweet = SWEET_REGISTRY[params.sweet]
    crab = CRAB_REGISTRY[params.crab]
    action = HELP_ACTIONS[params.help_action]
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, role="hero"))
    companion = world.add(Entity(id=params.companion_name, kind="character", type=params.companion_type, role="companion"))
    world.add(Entity(id="shore", type="place", label=shore.label))
    world.add(Entity(id="sweet", type="thing", label=sweet.label))
    world.add(Entity(id="crab", type="creature", label=crab.label))
    hero.memes["sharing"] = SHARING_START
    hero.memes["bravery"] = BRAVERY_START
    companion.memes["sharing"] = 2.0
    world.facts["shore"] = shore
    world.facts["sweet"] = sweet
    world.facts["crab"] = crab
    world.facts["action"] = action
    opening(world, hero, companion, shore, sweet, crab)
    world.para()
    need(world, hero, shore)
    tempt(world, hero, sweet)
    if params.share_first:
        choose_share(world, hero, companion, sweet)
    if params.brave_step:
        show_bravery(world, hero, crab)
    world.para()
    if can_help(action, shore.distance, shore.wind_strength) and reasonableness_gate(params.share_first, params.brave_step):
        _help_crab(world)
        rescue(world, action, shore, sweet, crab)
        lesson(world, hero, companion, sweet, crab)
        world.para()
        ending(world, hero, companion, sweet, shore, crab)
        outcome = "shared"
    else:
        failed_help(world, action, shore, crab)
        sad_end(world, hero, companion, sweet, crab)
        outcome = "unshared"
    world.facts["outcome"] = outcome
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    shore = f["shore"]
    sweet = f["sweet"]
    crab = f["crab"]
    return [
        f'Write a folk-tale style story for a 3-to-5-year-old that includes "{sweet.label}" and a {crab.label}.',
        f"Tell a brave sharing story by the shore where a child uses {sweet.label} to help a {crab.label}.",
        f'Write a gentle folk tale about {shore.label}, bravery, and sharing, ending with {sweet.label} and a safe crab.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    sweet = f["sweet"]
    crab = f["crab"]
    action = f["action"]
    outcome = f["outcome"]
    items = [
        QAItem(
            question="Who are the story about?",
            answer=f"It is about {hero.id} and {companion.id}, who went to the shore and met a little {crab.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry?",
            answer=f"{hero.id} carried {sweet.phrase}. The sweet mattered because it could be shared instead of kept only for one child.",
        ),
    ]
    if outcome == "shared":
        items.append(
            QAItem(
                question="How did the children help the crab?",
                answer=f"They shared the taffy, then used a brave little step to guide the {crab.label} back toward the water. Sharing made the help kinder, and bravery made it possible to reach the crab.",
            )
        )
        items.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended happily: the crab was safe, the taffy was shared, and {hero.id} went home with a warm heart and an empty wrapper.",
            )
        )
    else:
        items.append(
            QAItem(
                question="Why did the help not work well?",
                answer=f"{hero.id} did not share or act bravely enough at the right time, so {action.fail.replace('{target}', crab.label).lower()} The crab stayed stuck until the tide changed.",
            )
        )
        items.append(
            QAItem(
                question="What did {hero.id} learn?",
                answer=f"{hero.id} learned that bravery needs sharing too. A sweet kept alone could not become the kind of help the crab needed.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a crab?",
            answer="A crab is a sea creature with a hard shell and sideways steps. It lives near water and uses its claws to pinch and hold things.",
        ),
        QAItem(
            question="What is taffy?",
            answer="Taffy is a chewy sweet that can be pulled and broken into pieces. People often share it because it comes apart in sticky strands.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else have some of what you have. It helps two people enjoy one thing together instead of only one person enjoying it.",
        ),
    ]
    if world.facts.get("outcome") == "shared":
        out.append(
            QAItem(
                question="Why was bravery important in this story?",
                answer="Bravery was important because the child had to step close enough to help the crab. The shore was slippery and the wind was strong, so a brave choice made the rescue possible.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    shore: str
    sweet: str
    crab: str
    help_action: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    share_first: bool = True
    brave_step: bool = True
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


SHORE_REGISTRY = {
    "tidal_path": Shore(
        id="tidal_path",
        label="the tidal path",
        tide="tide",
        wind="salt",
        path="stone path",
        dark_place="the little rock-shadow",
        tags={"shore", "tide"},
        ),
    "shell_bay": Shore(
        id="shell_bay",
        label="Shell Bay",
        tide="tide",
        wind="sea",
        path="beach path",
        dark_place="the barnacled bend",
        tags={"shore", "bay"},
    ),
    "moon_cove": Shore(
        id="moon_cove",
        label="Moon Cove",
        tide="tide",
        wind="brisk",
        path="moonlit stones",
        dark_place="the narrow cove mouth",
        tags={"shore", "cove"},
    ),
}

SWEET_REGISTRY = {
    "taffy": Sweet(
        id="taffy",
        label="taffy",
        phrase="a ribbon of taffy",
        crumb="sticky crumbs",
        shiny="golden",
        tags={"taffy", "sweet"},
    ),
    "honey_taffy": Sweet(
        id="honey_taffy",
        label="honey taffy",
        phrase="a twist of honey taffy",
        crumb="sweet crumbs",
        shiny="amber",
        tags={"taffy", "sweet"},
    ),
}

CRAB_REGISTRY = {
    "crab": Creature(
        id="crab",
        label="crab",
        phrase="a small crab",
        pinch="pinchy claws",
        shell="red shell",
        tags={"crab"},
    ),
    "hermit_crab": Creature(
        id="hermit_crab",
        label="hermit crab",
        phrase="a tiny hermit crab",
        pinch="little claws",
        shell="striped shell",
        tags={"crab"},
    ),
}

HELP_ACTIONS = {
    "carry_to_water": HelpAction(
        id="carry_to_water",
        sense=3,
        power=3,
        text="carried the crab in a little shell boat to the water",
        fail="tried to carry the crab, but the waves were too tricky",
        qa_text="carried the crab in a little shell boat to the water",
        tags={"help"},
    ),
    "guide_along_stones": HelpAction(
        id="guide_along_stones",
        sense=4,
        power=4,
        text="guided the crab along the stones until it reached the shallows",
        fail="guided the crab along the stones, but the wind pushed it back",
        qa_text="guided the crab along the stones until it reached the shallows",
        tags={"help"},
    ),
}

CURATED = [
    StoryParams(
        shore="tidal_path",
        sweet="taffy",
        crab="crab",
        help_action="guide_along_stones",
        hero_name="Mara",
        hero_type="girl",
        companion_name="Pip",
        companion_type="boy",
        share_first=True,
        brave_step=True,
    ),
    StoryParams(
        shore="shell_bay",
        sweet="honey_taffy",
        crab="hermit_crab",
        help_action="carry_to_water",
        hero_name="Nell",
        hero_type="girl",
        companion_name="Rook",
        companion_type="boy",
        share_first=True,
        brave_step=True,
    ),
    StoryParams(
        shore="moon_cove",
        sweet="taffy",
        crab="hermit_crab",
        help_action="guide_along_stones",
        hero_name="Ivo",
        hero_type="boy",
        companion_name="Lina",
        companion_type="girl",
        share_first=False,
        brave_step=False,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sh in SHORE_REGISTRY:
        for sw in SWEET_REGISTRY:
            for cr in CRAB_REGISTRY:
                for ha in HELP_ACTIONS:
                    combos.append((sh, sw, cr, ha))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about taffy, a crab, bravery, and sharing.")
    ap.add_argument("--shore", choices=SHORE_REGISTRY)
    ap.add_argument("--sweet", choices=SWEET_REGISTRY)
    ap.add_argument("--crab", choices=CRAB_REGISTRY)
    ap.add_argument("--help-action", choices=HELP_ACTIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("--share-first", action="store_true")
    ap.add_argument("--no-share-first", action="store_true")
    ap.add_argument("--brave-step", action="store_true")
    ap.add_argument("--no-brave-step", action="store_true")
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
    if args.share_first and args.no_share_first:
        raise StoryError("Choose only one of --share-first or --no-share-first.")
    if args.brave_step and args.no_brave_step:
        raise StoryError("Choose only one of --brave-step or --no-brave-step.")
    combos = valid_combos()
    sh = args.shore or rng.choice(list(SHORE_REGISTRY))
    sw = args.sweet or rng.choice(list(SWEET_REGISTRY))
    cr = args.crab or rng.choice(list(CRAB_REGISTRY))
    ha = args.help_action or rng.choice(list(HELP_ACTIONS))
    if (sh, sw, cr, ha) not in combos:
        raise StoryError("That shore, sweet, crab, and help-action do not fit this tale.")
    share_first = True if args.share_first else False if args.no_share_first else rng.choice([True, True, False])
    brave_step = True if args.brave_step else False if args.no_brave_step else rng.choice([True, True, False])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(["Mara", "Nell", "Ivo", "Pip", "Sana", "Tobin"])
    companion_name = args.companion_name or rng.choice([n for n in ["Pip", "Lina", "Rook", "Joss", "Tia", "Bram"] if n != hero_name])
    return StoryParams(
        shore=sh,
        sweet=sw,
        crab=cr,
        help_action=ha,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        share_first=share_first,
        brave_step=brave_step,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
shared(H) :- share_first(H).
brave(H) :- brave_step(H).
happy(H) :- shared(H), brave(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHORE_REGISTRY:
        lines.append(asp.fact("shore", sid))
    for sid in SWEET_REGISTRY:
        lines.append(asp.fact("sweet", sid))
    for cid in CRAB_REGISTRY:
        lines.append(asp.fact("crab", cid))
    for aid in HELP_ACTIONS:
        lines.append(asp.fact("help_action", aid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show happy/1."))
        _ = model
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    sample = generate(CURATED[0])
    if not sample.story or "taffy" not in sample.story or "crab" not in sample.story:
        print("Generate smoke test failed.")
        return 1
    print("OK: ASP smoke test and story generation succeeded.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show happy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            i += 1
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
