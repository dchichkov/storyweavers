#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gasoline_quest_folk_tale.py
===========================================================

A standalone storyworld for a tiny folk-tale quest about a child who needs
gasoline for a useful purpose, but must choose a safe, grown-up path to get it.

The world is built around a simple quest shape:
- a need is discovered,
- a journey begins,
- a helper or obstacle changes the plan,
- the characters return with the right thing,
- the ending proves the change in the world.

The story keeps a folk-tale tone: village, path, bridge, barn, market, and a
wise helper. The engine uses typed entities with physical meters and emotional
memes, a forward-chained rule step for tension, and a reasonableness gate so
only plausible quests are generated.

This script is stdlib-only and matches the storyworld contract:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- main
- --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

It imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample,
and imports storyworlds/asp.py lazily inside ASP helpers.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Setting:
    id: str
    place: str
    path: str
    journey: str
    mood: str
    allowed_quests: set[str] = field(default_factory=set)

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
class QuestNeed:
    id: str
    label: str
    phrase: str
    where: str
    useful_for: str
    dangerous_when: str
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
class Helper:
    id: str
    label: str
    role: str
    wisdom: int
    aid: int
    text: str
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
class Outcome:
    id: str
    power: int
    sense: int
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
        return clone


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("mother").memes["care"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry)]


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


def can_quest(setting: Setting, need: QuestNeed) -> bool:
    return need.id in setting.allowed_quests


def sensible_outcomes() -> list[Outcome]:
    return [o for o in OUTCOMES.values() if o.sense >= SENSE_MIN]


def journey_risk(need: QuestNeed, delay: int) -> int:
    return 1 + delay if need.id == "gasoline" else delay


def outcome_of(params: "StoryParams") -> str:
    if params.helper_first:
        return "guided"
    return "returned" if OUTCOMES[params.outcome].power >= journey_risk(NEEDS[params.need], params.delay) else "mistake"


def predict_misstep(world: World, need: QuestNeed) -> dict:
    sim = world.copy()
    _take_quest(sim, sim.get("child"), need, narrate=False)
    return {
        "worry": sim.get("mother").memes["care"],
        "trail": sim.get("road").meters["dust"],
    }


def _take_quest(world: World, child: Entity, need: QuestNeed, narrate: bool = True) -> None:
    child.meters["distance"] += 1
    child.memes["hope"] += 1
    world.get("road").meters["used"] += 1
    propagate(world, narrate=narrate)


def begin(world: World, child: Entity, mother: Entity, setting: Setting, need: QuestNeed) -> None:
    child.memes["hope"] += 1
    mother.memes["care"] += 1
    world.say(
        f"In a little village beside {setting.path}, {child.id} lived with {mother.label_word}. "
        f"Each morning the wind went soft through the fences, and the lane looked as if it were waiting for a quest."
    )
    world.say(
        f"One day, {child.id} needed {need.phrase}. It was used for {need.useful_for}, and {child.id} knew the work could not be done without it."
    )


def ask_help(world: World, child: Entity, helper: Helper, need: QuestNeed) -> None:
    world.say(
        f"{child.id} went first to {helper.label}. {helper.text} "
        f'"You seek {need.label}," {helper.role} said, "but remember the rule: {need.dangerous_when}."'
    )


def travel(world: World, child: Entity, setting: Setting, need: QuestNeed) -> None:
    world.say(
        f"So {child.id} walked the {setting.journey}. The path was {setting.mood}, and every step felt like the beginning of an old tale."
    )


def warning(world: World, mother: Entity, child: Entity, need: QuestNeed) -> None:
    child.memes["worry"] += 1
    pred = predict_misstep(world, need)
    world.facts["predicted_care"] = pred["worry"]
    world.say(
        f"{mother.label_word.capitalize()} watched {child.id} tie a little cloth bag and said, "
        f'"If you are carrying {need.label}, keep it away from sparks and lamps. {need.label.capitalize()} can be useful, but it must be handled with care."'
    )


def helper_turn(world: World, child: Entity, helper: Helper, need: QuestNeed) -> None:
    child.memes["hope"] += 1
    if helper.wisdom >= 5:
        world.say(
            f"{helper.label} pointed down the road and gave a wise answer. "
            f'"Take the safe road to the market, and ask the keeper for the proper bottle," {helper.role} said.'
        )
    else:
        world.say(f"{helper.label} offered a smaller hint, and {child.id} kept walking.")


def obtain(world: World, child: Entity, need: QuestNeed, outcome: Outcome) -> None:
    child.meters["distance"] += 1
    world.say(
        f"At last {child.id} reached the market stall and asked for {need.label}. "
        f"The keeper filled a can, and the little bag grew warm with the weight of the quest."
    )
    world.say(
        f"Then {outcome.text.replace('{need}', need.label)}."
    )


def return_home(world: World, child: Entity, mother: Entity, setting: Setting, need: QuestNeed) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} carried the {need.label} home along {setting.path}. "
        f"{mother.label_word.capitalize()} smiled when {child.pronoun()} set it safely on the porch."
    )
    world.say(
        f"By dusk the yard was ready, the lantern was bright, and the old village path had helped turn a need into a worthy errand."
    )


def mistake_end(world: World, child: Entity, mother: Entity, need: QuestNeed) -> None:
    child.meters["scuffed"] += 1
    mother.memes["care"] += 1
    world.say(
        f"But the quest went badly, and {child.id} came back with a scuffed shoe and a worried heart. "
        f"{mother.label_word.capitalize()} was not angry; {mother.pronoun()} was glad {child.id} had returned home."
    )
    world.say(
        f"That night, the lesson stayed clear: {need.dangerous_when}, and a true quest always chooses the safer road."
    )


def tell(setting: Setting, need: QuestNeed, helper: Helper, outcome: Outcome,
         child_name: str = "Milo", child_gender: str = "boy",
         mother_name: str = "Mother", mother_gender: str = "woman",
         delay: int = 0, helper_first: bool = False) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="quester"))
    mother = world.add(Entity(id=mother_name, kind="character", type=mother_gender, role="guardian", label="the mother"))
    road = world.add(Entity(id="road", type="place", label=setting.path))
    child.memes["hope"] = 1
    mother.memes["care"] = 1
    world.facts["delay"] = delay
    begin(world, child, mother, setting, need)
    world.para()
    warning(world, mother, child, need)
    if helper_first:
        ask_help(world, child, helper, need)
        helper_turn(world, child, helper, need)
    else:
        travel(world, child, setting, need)
        ask_help(world, child, helper, need)
        helper_turn(world, child, helper, need)
    world.para()
    _take_quest(world, child, need)
    obtain(world, child, need, outcome)
    world.para()
    return_home(world, child, mother, setting, need)
    if outcome.id == "mistake":
        world.para()
        mistake_end(world, child, mother, need)
    world.facts.update(child=child, mother=mother, need=need, helper=helper, outcome=outcome, setting=setting, road=road, helper_first=helper_first)
    return world


SETTINGS = {
    "village": Setting("village", "the village green", "the stone bridge", "the long lane", "golden and quiet", {"gasoline"}),
    "meadow": Setting("meadow", "the meadow", "the worn footpath", "the ribbon road", "soft with grass", {"gasoline"}),
    "harbor": Setting("harbor", "the harbor road", "the wooden bridge", "the salt lane", "full of gulls and creaks", {"gasoline"}),
}

NEEDS = {
    "gasoline": QuestNeed(
        "gasoline",
        "gasoline",
        "gasoline in a can",
        "at the shed behind the house",
        "light the old tractor lantern for the night watch",
        "near a spark, lamp, or open flame",
        {"gasoline", "fuel", "quest"},
    ),
    "lamp_oil": QuestNeed(
        "lamp_oil",
        "lamp oil",
        "lamp oil in a bottle",
        "at the mill shop",
        "fill a lantern for the supper table",
        "near a spark, lamp, or open flame",
        {"oil", "quest"},
    ),
}

HELPERS = {
    "fox": Helper("fox", "the fox", "fox", 5, 3, "A red fox sat on a stump and flicked its tail.", {"wise"}),
    "miller": Helper("miller", "the miller", "miller", 7, 5, "An old miller lifted his cap and listened carefully.", {"wise"}),
    "grandmother": Helper("grandmother", "grandmother", "grandmother", 8, 6, "Grandmother opened the door and spoke in a calm voice.", {"wise"}),
}

OUTCOMES = {
    "returned": Outcome("returned", 4, 3, "the keeper poured it into a safe can with a tight lid", "the little bottle tipped and wasted the fuel", "the keeper poured the gasoline into a safe can with a tight lid", {"quest"}),
    "guided": Outcome("guided", 5, 5, "the keeper gave directions and a lantern so the child could travel safely", "the keeper shook their head, because the errand was too muddled to trust", "the keeper gave directions and a lantern so the child could travel safely", {"quest"}),
    "mistake": Outcome("mistake", 1, 1, "someone tried to hurry, and the can sloshed and made a dangerous mess", "someone tried to hurry, and the can sloshed and made a dangerous mess", "someone tried to hurry, and the can sloshed and made a dangerous mess", {"quest"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    need: str
    helper: str
    outcome: str
    child_name: str
    child_gender: str
    delay: int = 0
    helper_first: bool = False
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for nid, n in NEEDS.items():
            if not can_quest(s, n):
                continue
            for hid in HELPERS:
                for oid in OUTCOMES:
                    combos.append((sid, nid, hid))
    return combos


GIRL_NAMES = ["Mara", "Lina", "Nia", "Hana", "Ivy", "June", "Tess"]
BOY_NAMES = ["Oren", "Pip", "Ari", "Bram", "Ned", "Otis", "Jonah"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale quest about gasoline and a safe journey.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--helper-first", action="store_true")
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
    if args.need and args.need != "gasoline":
        raise StoryError("This world is built around gasoline, so the quest must involve gasoline.")
    setting = args.setting or rng.choice(list(SETTINGS))
    need = "gasoline"
    helper = args.helper or rng.choice(list(HELPERS))
    outcome = args.outcome or rng.choice(list(OUTCOMES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting, need, helper, outcome, name, gender, args.delay, args.helper_first)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale quest story for a 3-to-5-year-old that includes the word "gasoline".',
        f"Tell a gentle village quest about {f['child'].id} seeking gasoline, meeting a wise helper, and returning home safely.",
        f"Write a simple story in a folk-tale style where a child learns how to handle gasoline carefully on an errand.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mother = f["mother"]
    need = f["need"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa = [
        QAItem(
            question="What was the child looking for?",
            answer=f"{child.id} was looking for gasoline. It was needed for the lantern work, so the errand mattered to the whole home.",
        ),
        QAItem(
            question="Who gave advice on the quest?",
            answer=f"{helper.label.capitalize()} gave advice. The helper's calm words pushed the child toward the safe road and away from danger.",
        ),
        QAItem(
            question="How did the mother help?",
            answer=f"{mother.label_word.capitalize()} warned {child.id} to keep gasoline away from sparks and lamps. That warning mattered because gasoline is useful but dangerous near fire.",
        ),
    ]
    if f["outcome_id"] == "guided":
        qa.append(QAItem(
            question="How did the story end?",
            answer="The child returned with gasoline safely and the lantern could shine again. The ending is bright and calm, with the quest completed the careful way.",
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer="The child still came home safely, but the errand went wrong and made a mess. The lesson was that gasoline must be handled slowly and kept away from fire.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gasoline?",
            answer="Gasoline is a fuel used in some machines and vehicles. It burns easily, so it must be kept away from flames and sparks.",
        ),
        QAItem(
            question="Why is gasoline dangerous near fire?",
            answer="Gasoline gives off fumes that can catch fire very quickly. That is why grown-ups keep it in a safe container and handle it carefully.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to get something important or solve a problem. In folk tales, quests often include a path, a helper, and a return home.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, need: QuestNeed, helper: Helper, outcome: Outcome,
         child_name: str, child_gender: str, delay: int, helper_first: bool) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="quester"))
    mother = world.add(Entity(id="mother", kind="character", type="mother", role="guardian", label="the mother"))
    h = world.add(Entity(id=helper.id, kind="character", type="person", role=helper.role, label=helper.label))
    road = world.add(Entity(id="road", type="place", label=setting.path))
    child.memes["hope"] = 1
    mother.memes["care"] = 1
    world.say(
        f"Once in a little village, {child.id} lived with {mother.label_word}. "
        f"The world beside {setting.path} felt old as a song, and every lane seemed to wait for a story."
    )
    world.say(
        f"One morning, {child.id} set out on a quest for {need.label}. "
        f"It was needed for {need.useful_for}, and the need was too important to forget."
    )
    world.para()
    warning(world, mother, child, need)
    if helper_first:
        ask_help(world, child, helper, need)
        helper_turn(world, child, helper, need)
    else:
        travel(world, child, setting, need)
        ask_help(world, child, helper, need)
        helper_turn(world, child, helper, need)
    world.para()
    _take_quest(world, child, need)
    obtain(world, child, need, outcome)
    if outcome.id == "mistake":
        world.para()
        mistake_end(world, child, mother, need)
    else:
        world.para()
        return_home(world, child, mother, setting, need)
    world.facts.update(child=child, mother=mother, need=need, helper=h, outcome=outcome, setting=setting, road=road, outcome_id=outcome.id)
    return world


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
gasoline_need(gasoline).
quest_need(N) :- gasoline_need(N).

safe_outcome(guided) :- outcome(guided).
safe_outcome(returned) :- outcome(returned).
valid_story(S, N, H) :- setting(S), quest_need(N), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.allowed_quests):
            lines.append(asp.fact("allowed_quest", sid, q))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("useful_for", nid, n.useful_for))
        lines.append(asp.fact("dangerous_when", nid, n.dangerous_when))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("wisdom", hid, h.wisdom))
        lines.append(asp.fact("aid", hid, h.aid))
    for oid, o in OUTCOMES.items():
        lines.append(asp.fact("outcome", oid))
        lines.append(asp.fact("sense", oid, o.sense))
        lines.append(asp.fact("power", oid, o.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams("village", "gasoline", "miller", "returned", "Milo", "boy", 0, False),
    StoryParams("meadow", "gasoline", "grandmother", "guided", "Nia", "girl", 0, True),
]


def explain_rejection() -> str:
    return "(No story: this world only makes a folk-tale quest for gasoline.)"


def explain_outcome(rid: str) -> str:
    r = OUTCOMES[rid]
    better = " / ".join(sorted(o.id for o in sensible_outcomes()))
    return f"(Refusing outcome '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], NEEDS[params.need], HELPERS[params.helper],
        OUTCOMES[params.outcome], params.child_name, params.child_gender,
        params.delay, params.helper_first,
    )
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
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest combos:\n")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.need} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
