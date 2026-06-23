#!/usr/bin/env python3
"""
storyworlds/worlds/dynamic_valuable_quest_lesson_learned_moral_value.py
=======================================================================

A small standalone storyworld about a space quest, a valuable find, and a
lesson learned along the way. The world keeps track of physical meters and
emotional memes, generates a complete child-facing story, and provides three
Q&A sets grounded in the simulated state.

Premise:
- A child astronaut and a helper drone go on a quest through a tiny space
  setting.
- They want a valuable object or place.
- A wrong shortcut creates tension.
- A wiser choice resolves the quest and leaves behind a moral value.

Style:
- Space Adventure
- Child-facing, concrete, and state-driven
- Includes the words "dynamic" and "valuable"
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    helper: Optional[str] = None
    location: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain-girl"}
        male = {"boy", "father", "dad", "man", "captain-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


@dataclass
class Setting:
    id: str
    place: str
    kind: str
    features: set[str] = field(default_factory=set)
    details: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Quest:
    id: str
    goal: str
    verb: str
    lure: str
    at_risk: str
    turn: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Item:
    id: str
    label: str
    phrase: str
    value: str
    weight: int = 0
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Guide:
    id: str
    label: str
    role: str
    wisdom: str
    fix: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
        self.events: list[str] = []

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
            self.events.append(text)

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
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


def _r_glitch(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    quest = world.facts["quest"]
    if hero.memes["shortcut"] < THRESHOLD:
        return out
    sig = ("glitch", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").meters["wobble"] += 1
    hero.memes["worry"] += 1
    out.append(f"The ship gave a small wobble, and the quest felt harder.")
    out.append(f"{hero.id} noticed that the quick way was not the safe way.")
    return out


def _r_value(world: World) -> list[str]:
    out: list[str] = []
    relic = world.get("relic")
    guide = world.get("guide")
    if relic.meters["found"] < THRESHOLD:
        return out
    sig = ("value", relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide.memes["pride"] += 1
    out.append(f"The valuable {relic.label} glimmered like a tiny star.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    guide = world.get("guide")
    if hero.memes["lesson"] < THRESHOLD:
        return out
    sig = ("lesson", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] += 1
    guide.memes["trust"] += 1
    out.append("The lesson settled in like a bright beacon.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_glitch, _r_value, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def quest_at_risk(quest: Quest, setting: Setting, item: Item) -> bool:
    return "space" in setting.features and "valuable" in item.tags


def select_fix(quest: Quest, item: Item) -> bool:
    return quest.id in {"quest1", "quest2"} and item.value in {"map-core", "star-gem"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for iid, item in ITEMS.items():
                if quest_at_risk(quest, setting, item) and select_fix(quest, item):
                    combos.append((sid, qid, iid))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    item: str
    hero_name: str
    hero_gender: str
    guide_name: str
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


SETTINGS = {
    "orbital_hub": Setting(
        id="orbital_hub",
        place="the orbital hub",
        kind="station",
        features={"space", "metal", "lights"},
        details="The windows showed a deep black sky and a line of distant stars.",
    ),
    "moon_port": Setting(
        id="moon_port",
        place="the moon port",
        kind="base",
        features={"space", "dust", "ramp"},
        details="Gray dust curled over the landing pad whenever the hatch opened.",
    ),
    "asteroid_room": Setting(
        id="asteroid_room",
        place="the asteroid room",
        kind="cavern",
        features={"space", "rocks", "tunnels"},
        details="Tiny rocks floated near the walls like sleepy crumbs.",
    ),
}

QUESTS = {
    "quest1": Quest(
        id="quest1",
        goal="find the map-core",
        verb="scan the old tunnel",
        lure="a blinking shortcut door",
        at_risk="the wrong door could scatter their path",
        turn="the tunnel light flickered, and the shortcut looked tricky",
        ending="the map-core was safe in their hands",
        tags={"quest", "lesson", "moral"},
    ),
    "quest2": Quest(
        id="quest2",
        goal="fetch the star-gem",
        verb="cross the quiet dock",
        lure="a shiny lift rail",
        at_risk="the rail might send them into a cold drift",
        turn="the dock hummed softly, and the shiny rail looked tempting",
        ending="the star-gem came home without a scratch",
        tags={"quest", "lesson", "moral"},
    ),
    "quest3": Quest(
        id="quest3",
        goal="bring back the beacon coin",
        verb="follow the blinking panels",
        lure="a fast side hatch",
        at_risk="the hatch could lose their way",
        turn="the panels blinked in a dynamic pattern",
        ending="the beacon coin ended up shining in the basket",
        tags={"quest", "lesson", "moral"},
    ),
}

ITEMS = {
    "map_core": Item(
        id="map_core",
        label="map-core",
        phrase="a valuable map-core",
        value="map-core",
        weight=2,
        tags={"valuable"},
    ),
    "star_gem": Item(
        id="star_gem",
        label="star-gem",
        phrase="a valuable star-gem",
        value="star-gem",
        weight=3,
        tags={"valuable"},
    ),
    "beacon_coin": Item(
        id="beacon_coin",
        label="beacon coin",
        phrase="a valuable beacon coin",
        value="beacon-coin",
        weight=1,
        tags={"valuable"},
    ),
}

GUIDES = {
    "guide1": Guide(
        id="guide1",
        label="Captain Mira",
        role="guide",
        wisdom="slow hands make steady space trips",
        fix="a calm route is better than a fast guess",
        tags={"lesson", "moral"},
    ),
    "guide2": Guide(
        id="guide2",
        label="Pilot Jace",
        role="guide",
        wisdom="good crews check their path twice",
        fix="a careful plan keeps valuable things safe",
        tags={"lesson", "moral"},
    ),
}

GIRL_NAMES = ["Luna", "Mina", "Aria", "Tia", "Nina", "Iris"]
BOY_NAMES = ["Kai", "Oren", "Leo", "Milo", "Noah", "Ezra"]


def _choose_hero(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(setting.features):
            lines.append(asp.fact("feature", sid, feat))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in sorted(quest.tags):
            lines.append(asp.fact("quest_tag", qid, tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if "valuable" in item.tags:
            lines.append(asp.fact("valuable", iid))
        lines.append(asp.fact("value", iid, item.value))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, I) :- setting(S), quest(Q), item(I), feature(S, space), valuable(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a quest and a lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
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
              and (args.quest is None or c[1] == args.quest)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, item = rng.choice(sorted(combos))
    name, gender = (_choose_hero(rng) if args.name is None or args.gender is None
                    else (args.name, args.gender))
    if args.gender is not None and args.name is None:
        name, _ = _choose_hero(rng)
        gender = args.gender
    guide = args.guide or rng.choice(sorted(GUIDES))
    return StoryParams(setting=setting, quest=quest, item=item, hero_name=name, hero_gender=gender, guide_name=guide)


def _introduce(world: World, hero: Entity, guide: Entity, quest: Quest, item: Entity) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["energy"] += 1
    guide.memes["warmth"] += 1
    world.say(f"{hero.id} was a young space traveler at {world.setting.place}. The place felt dynamic under the starlight.")
    world.say(f"{hero.id} and {guide.label_word} were on a quest to {quest.goal}, because {item.phrase} was valuable.")
    world.say(world.setting.details)


def _turn(world: World, hero: Entity, guide: Entity, quest: Quest, item: Entity) -> None:
    hero.memes["shortcut"] += 1
    world.say(f"They moved toward {quest.verb}, but a shortcut door looked tempting.")
    world.say(f'"{guide.label_word}," {hero.id} said, "that door looks fast."')
    world.say(f'"It does," said {guide.label_word}, "but {quest.at_risk}."')
    propagate(world)


def _resolution(world: World, hero: Entity, guide: Entity, quest: Quest, item: Entity) -> None:
    hero.memes["lesson"] += 1
    guide.memes["lesson"] += 1
    item.meters["found"] += 1
    propagate(world)
    world.say(f"They chose the slower path instead.")
    world.say(f"{hero.id} found {item.phrase} at the end of the trail, and the quest was complete.")
    world.say(f"{quest.ending.capitalize()}. The moral value was simple: careful choices keep valuable things safe.")


def tell(setting: Setting, quest: Quest, item: Item, hero_name: str, hero_gender: str, guide_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    guide = world.add(Entity(id=GUIDES[guide_name].label, kind="character", type="adult"))
    relic = world.add(Entity(id="relic", type="relic", label=item.label, phrase=item.phrase, tags=set(item.tags)))
    ship = world.add(Entity(id="ship", type="ship", label="their small ship"))
    world.add(Entity(id="guide", type="guide", label=GUIDES[guide_name].label))
    world.add(Entity(id="quest", type="quest", label=quest.goal))
    world.add(Entity(id="item", type="item", label=item.label))

    world.facts["quest"] = quest
    world.facts["item"] = item
    world.facts["guide"] = guide
    world.facts["hero"] = hero

    _introduce(world, hero, guide, quest, relic)
    world.para()
    _turn(world, hero, guide, quest, relic)
    world.para()
    _resolution(world, hero, guide, quest, relic)

    world.facts.update(hero=hero, guide=guide, relic=relic, ship=ship, quest=quest, item=item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure for a child that includes the words "dynamic" and "valuable" and ends with a lesson learned.',
        f"Tell a short story where {f['hero'].id} and a guide go on a quest for {f['item'].phrase} and choose the safer path.",
        f"Write a gentle quest story set at {world.setting.place} with a moral value at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    quest = f["quest"]
    item = f["item"]
    qa = [
        QAItem(
            question=f"Who went on the quest in the story?",
            answer=f"{hero.id} went on the quest with {guide.label_word}. They traveled through space to bring back {item.phrase}.",
        ),
        QAItem(
            question=f"Why was the quest important?",
            answer=f"It mattered because {item.phrase} was valuable. The trip was not just for fun; it was about bringing something special home safely.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the safer choice?",
            answer=f"{hero.id} wanted to take the shortcut door. That choice looked quick, but it could have scattered their path and made the quest harder.",
        ),
        QAItem(
            question=f"What lesson did the story teach?",
            answer=f"It taught that careful choices matter. A steady route can be the best moral value when something valuable has to stay safe.",
        ),
    ]
    if world.get("relic").meters["found"] >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What happened at the end of the quest?",
                answer=f"{item.phrase} was found and brought home. The ending showed that the slower path still won, and it proved the quest had a happy finish.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal. Someone goes looking for something or trying to solve a problem.",
        ),
        QAItem(
            question="What does valuable mean?",
            answer="Valuable means something is important, special, or worth a lot. People try to protect valuable things.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is an idea someone understands after something happens. It helps them make better choices next time.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for how to act, like being careful, kind, or honest.",
        ),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.item not in ITEMS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], ITEMS[params.item], params.hero_name, params.hero_gender, params.guide_name)
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


CURATED = [
    StoryParams(setting="orbital_hub", quest="quest1", item="map_core", hero_name="Luna", hero_gender="girl", guide_name="guide1"),
    StoryParams(setting="moon_port", quest="quest2", item="star_gem", hero_name="Kai", hero_gender="boy", guide_name="guide2"),
    StoryParams(setting="asteroid_room", quest="quest3", item="beacon_coin", hero_name="Mina", hero_gender="girl", guide_name="guide1"),
]


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between ASP and Python:")
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos) and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, quest, item) combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.hero_name}: {p.quest} at {p.setting} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
