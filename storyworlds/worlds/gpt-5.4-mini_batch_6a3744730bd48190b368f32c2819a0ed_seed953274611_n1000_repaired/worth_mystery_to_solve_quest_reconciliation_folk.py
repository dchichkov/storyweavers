#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/worth_mystery_to_solve_quest_reconciliation_folk.py
===================================================================================

A small story world in a folk-tale style: a child or two discover a village
mystery, go on a quest to solve it, and end in reconciliation when the missing
thing is found and everyone remembers what is truly worth keeping.

This world is built to be:
- standalone and stdlib-only
- state-driven, with meters and memes
- reasonableness-checked in Python and mirrored in inline ASP
- able to produce three QA sets from simulated world state
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
SENSE_MIN = 2


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
    carries: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Place:
    id: str
    label: str
    mood: str
    holds: set[str] = field(default_factory=set)
    mystery_sign: str = ""
    quest_sign: str = ""
    worth_sign: str = ""
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
class Mystery:
    id: str
    label: str
    clue: str
    missing: str
    location_hint: str
    risk: str
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
class Quest:
    id: str
    label: str
    verb: str
    route: str
    helper: str
    tool: str
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
class Resolution:
    id: str
    label: str
    action: str
    reassurance: str
    lesson: str
    worth_line: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_worry(world: World) -> list[str]:
    out = []
    for eid in ["village", "child", "elder"]:
        if eid in world.entities:
            e = world.get(eid)
            if e.meters["worry"] >= THRESHOLD and ("worry", eid) not in world.fired:
                world.fired.add(("worry", eid))
                out.append("__worry__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    if "child" in world.entities and "elder" in world.entities:
        c = world.get("child")
        e = world.get("elder")
        sig = ("reconcile", c.id)
        if c.memes["kindness"] >= THRESHOLD and e.memes["relief"] >= THRESHOLD and sig not in world.fired:
            world.fired.add(sig)
            c.memes["peace"] += 1
            e.memes["peace"] += 1
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("reconcile", _r_reconcile)]


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


def reasonableness_gate(place: Place, mystery: Mystery, quest: Quest, resolution: Resolution) -> bool:
    return (
        mystery.missing in place.holds
        and quest.tool in {"lantern", "thread", "map", "bread_crumbs"}
        and resolution.id in {"kind_return", "shared_truth"}
    )


def sensible_quests() -> list[Quest]:
    return [q for q in QUESTS.values() if q.tool in {"lantern", "thread", "map", "bread_crumbs"}]


def best_resolution() -> Resolution:
    return RESOLUTIONS["kind_return"]


def predict_mystery(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    if "child" in sim.entities:
        sim.get("child").meters["search"] += 1
        sim.get("child").memes["hope"] += 1
    if "village" in sim.entities:
        sim.get("village").meters["worry"] += 1
    return {
        "worry": sim.get("village").meters["worry"] if "village" in sim.entities else 0,
        "hope": sim.get("child").memes["hope"] if "child" in sim.entities else 0,
        "missing": mystery.missing,
    }


def gather(world: World, child: Entity, quest: Quest, mystery: Mystery) -> None:
    child.meters["steps"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} set out on {quest.label}, following {quest.route} to find the answer to the mystery."
    )


def ask_around(world: World, child: Entity, elder: Entity, mystery: Mystery) -> None:
    child.meters["search"] += 1
    elder.memes["memory"] += 1
    world.say(
        f"At the cottage door, {child.id} asked {elder.id} about the missing thing. "
        f'"{mystery.clue}," {elder.id} said, "and that is why the village grew quiet."'
    )


def seek(world: World, child: Entity, quest: Quest, place: Place, mystery: Mystery) -> None:
    child.meters["search"] += 1
    child.memes["hope"] += 1
    world.say(
        f"{child.id} went along {quest.route}, past {place.label}, listening for a sign of {mystery.missing}."
    )


def find(world: World, child: Entity, mystery: Mystery, place: Place) -> None:
    child.meters["found"] += 1
    world.get("village").meters["worry"] += 1
    world.say(
        f"Near {place.label}, {child.id} found the lost {mystery.missing}, hidden where the reeds bent low."
    )


def reconcile(world: World, child: Entity, elder: Entity, res: Resolution, mystery: Mystery) -> None:
    child.memes["kindness"] += 1
    elder.memes["relief"] += 1
    world.get("village").meters["worry"] = 0
    world.say(
        f"{elder.id} smiled with tears in {elder.pronoun('possessive')} eyes and thanked {child.id} for bringing it back."
    )
    world.say(
        f'Then {child.id} heard {res.worth_line} "{mystery.missing}" and the hurt feeling between them softened.'
    )
    world.say(
        f"{res.reassurance} {res.lesson}"
    )


def ending(world: World, child: Entity, elder: Entity, mystery: Mystery, place: Place, res: Resolution) -> None:
    child.memes["peace"] += 1
    elder.memes["peace"] += 1
    world.say(
        f"In the end, the village was bright again, and {child.id} and {elder.id} walked home under the lantern glow."
    )
    world.say(
        f"{res.worth_line.capitalize()} was not in gold or applause, but in bringing back {mystery.missing} and making things right."
    )


def tell(place: Place, mystery: Mystery, quest: Quest, resolution: Resolution,
         child_name: str = "Pip", child_type: str = "boy",
         elder_name: str = "Gran", elder_type: str = "woman") -> World:
    world = World()
    village = world.add(Entity(id="village", kind="place", type="place", label=place.label))
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="seeker"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="guide"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="thing", label="lantern"))
    world.facts["place"] = place
    world.facts["mystery"] = mystery
    world.facts["quest"] = quest
    world.facts["resolution"] = resolution

    child.memes["curiosity"] = 1
    elder.memes["care"] = 1
    village.meters["worry"] = 1

    world.say(
        f"In the old village of {place.label}, there was a small mystery to solve: {mystery.label}."
    )
    world.say(
        f"The people worried because {mystery.clue} and no one knew where {mystery.missing} had gone."
    )
    world.say(
        f"{child.name if hasattr(child, 'name') else child.id} knew the answer might be worth finding, so {child.id} promised to look."
    )

    world.para()
    ask_around(world, child, elder, mystery)
    gather(world, child, quest, mystery)
    seek(world, child, quest, place, mystery)
    world.say(f"{child.id} carried a {quest.tool} and a little lantern for the dark path.")

    world.para()
    find(world, child, mystery, place)
    reconcile(world, child, elder, resolution, mystery)
    ending(world, child, elder, mystery, place, resolution)

    world.facts.update(
        village=village,
        child=child,
        elder=elder,
        lantern=lantern,
        resolved=True,
        found=True,
        worth=mystery.missing,
    )
    return world


PLACES = {
    "green_hollow": Place(
        id="green_hollow",
        label="Green Hollow",
        mood="gentle",
        holds={"silver_key", "songstone", "lantern"},
        mystery_sign="the well had gone silent",
        quest_sign="the path by the alder trees",
        worth_sign="what is worth keeping",
    ),
    "millbrook": Place(
        id="millbrook",
        label="Millbrook",
        mood="busy",
        holds={"bridge_bell", "bread_crumbs", "lantern"},
        mystery_sign="the bell stopped ringing at dawn",
        quest_sign="the lane by the mill",
        worth_sign="what was worth the journey",
    ),
    "bramble_ford": Place(
        id="bramble_ford",
        label="Bramble Ford",
        mood="wild",
        holds={"river_pearl", "thread", "lantern"},
        mystery_sign="the river had lost its sparkle",
        quest_sign="the ford under the willows",
        worth_sign="what is worth a brave heart",
    ),
}

MYSTERIES = {
    "silver_key": Mystery(
        id="silver_key", label="the missing silver key",
        clue="the old chest would not open",
        missing="silver_key",
        location_hint="the mossy bridge",
        risk="the village could not enter the store room",
        tags={"key", "missing", "mystery"},
    ),
    "bridge_bell": Mystery(
        id="bridge_bell", label="the stolen bridge bell",
        clue="the morning bell stayed silent",
        missing="bridge_bell",
        location_hint="near the river reeds",
        risk="the villagers had no call to gather",
        tags={"bell", "missing", "mystery"},
    ),
    "river_pearl": Mystery(
        id="river_pearl", label="the lost river pearl",
        clue="the river shimmer had dimmed",
        missing="river_pearl",
        location_hint="under the willow roots",
        risk="the old song would not be sung",
        tags={"pearl", "missing", "mystery"},
    ),
}

QUESTS = {
    "lantern_path": Quest(
        id="lantern_path", label="the lantern path", verb="seek the trail",
        route="the lantern path", helper="lantern", tool="lantern", tags={"lantern", "quest"},
    ),
    "thread_map": Quest(
        id="thread_map", label="the thread-and-map quest", verb="follow the thread",
        route="a thread tied to the alder trees", helper="thread", tool="thread", tags={"thread", "quest"},
    ),
    "bread_crumbs": Quest(
        id="bread_crumbs", label="the bread-crumb quest", verb="walk the trail",
        route="a trail of bread crumbs", helper="bread crumbs", tool="bread_crumbs", tags={"bread", "quest"},
    ),
    "river_map": Quest(
        id="river_map", label="the river map quest", verb="follow the map",
        route="a hand-drawn map by the river", helper="map", tool="map", tags={"map", "quest"},
    ),
}

RESOLUTIONS = {
    "kind_return": Resolution(
        id="kind_return", label="kind return", action="gave the missing thing back",
        reassurance="The elder’s face softened.",
        lesson="They learned that a mystery can be solved best when people work together and speak kindly.",
        worth_line="What was worth most",
        tags={"reconciliation", "worth"},
    ),
    "shared_truth": Resolution(
        id="shared_truth", label="shared truth", action="told the whole story",
        reassurance="The village listened closely.",
        lesson="They learned that the truth can mend a hurt place and bring people back together.",
        worth_line="What is worth most",
        tags={"reconciliation", "truth"},
    ),
}

NAMES_BOY = ["Pip", "Oren", "Toby", "Milo", "Finn", "Joss"]
NAMES_GIRL = ["Nia", "Bryn", "Lina", "Mara", "Etta", "Rosa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.missing not in place.holds:
                continue
            for quest_id, quest in QUESTS.items():
                if quest.tool not in {"lantern", "thread", "map", "bread_crumbs"}:
                    continue
                for res_id, res in RESOLUTIONS.items():
                    if reasonableness_gate(place, mystery, quest, res):
                        combos.append((place_id, mystery_id, quest_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    quest: str
    resolution: str
    child: str
    child_type: str
    elder: str
    elder_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a mystery, a quest, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.place:
        pl = PLACES[args.place]
        my = MYSTERIES[args.mystery]
        if my.missing not in pl.holds:
            raise StoryError("No story: that place does not hold the missing thing, so there is no real mystery to solve there.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("No story: unknown quest.")
    if args.resolution and args.resolution not in RESOLUTIONS:
        raise StoryError("No story: unknown resolution.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, quest = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(list(RESOLUTIONS))
    child_type = args.child_type or rng.choice(["boy", "girl"])
    child = args.name or rng.choice(NAMES_BOY if child_type == "boy" else NAMES_GIRL)
    elder_type = args.elder_type or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(["Gran", "Old Tom", "Aunt May", "Uncle Reed"])
    return StoryParams(place=place, mystery=mystery, quest=quest, resolution=resolution,
                       child=child, child_type=child_type, elder=elder, elder_type=elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a 3-to-5-year-old about {f["mystery"].label} in {f["place"].label}.',
        f"Tell a small quest story where {f['child'].id} goes looking for {f['mystery'].missing} and reconciles with {f['elder'].id} at the end.",
        f'Write a gentle mystery tale that includes the word "worth" and ends with everyone glad the missing thing came home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, mystery, place, quest, res = f["child"], f["elder"], f["mystery"], f["place"], f["quest"], f["resolution"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"The mystery was {mystery.label}. People were worried because {mystery.clue}, and they did not know where it had gone."
        ),
        QAItem(
            question="What did the child do?",
            answer=f"{child.id} went on {quest.label}, asking questions, following the route, and looking for {mystery.missing}. The quest turned the worry into a search."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended in reconciliation. {elder.id} thanked {child.id}, and the village remembered that {res.worth_line.lower()} was bringing back {mystery.missing} and speaking kindly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something people do not understand yet. They look for clues until the missing or hidden thing becomes clear."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey made to find or fix something important. In folk tales, a quest often begins with a problem and ends with a lesson."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were hurt or upset come back together peacefully. They listen, forgive, and make room for kindness again."
        ),
        QAItem(
            question="What does worth mean in this story?",
            answer="Worth means something is important or valuable. In this story, the missing thing is worth bringing home because it helps the village and mends hearts."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place(P), mystery(M), quest(Q)) :- place(P), mystery(M), quest(Q), holds(P, M), usable(Q).
reconciliation(R) :- resolution(R), good(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(p.holds):
            lines.append(asp.fact("holds", pid, h))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.tool in {"lantern", "thread", "map", "bread_crumbs"}:
            lines.append(asp.fact("usable", qid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    lines.append(asp.fact("good", "kind_return"))
    lines.append(asp.fact("good", "shared_truth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate vs Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: generate smoke test crashed: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.quest not in QUESTS or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid parameters for this story world.")
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    quest = QUESTS[params.quest]
    resolution = RESOLUTIONS[params.resolution]
    if not reasonableness_gate(place, mystery, quest, resolution):
        raise StoryError("No story: the chosen parts do not fit this mystery quest.")
    world = tell(place, mystery, quest, resolution, params.child, params.child_type, params.elder, params.elder_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show reconciliation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="green_hollow", mystery="silver_key", quest="lantern_path", resolution="kind_return",
                        child="Pip", child_type="boy", elder="Gran", elder_type="woman"),
            StoryParams(place="millbrook", mystery="bridge_bell", quest="river_map", resolution="shared_truth",
                        child="Nia", child_type="girl", elder="Old Tom", elder_type="man"),
            StoryParams(place="bramble_ford", mystery="river_pearl", quest="thread_map", resolution="kind_return",
                        child="Mara", child_type="girl", elder="Aunt May", elder_type="woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
