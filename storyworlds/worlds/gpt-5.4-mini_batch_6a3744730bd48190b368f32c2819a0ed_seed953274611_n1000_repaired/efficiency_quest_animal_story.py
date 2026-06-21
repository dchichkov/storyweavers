#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/efficiency_quest_animal_story.py
================================================================

A standalone storyworld for a small Animal Story quest about *efficiency*.

Premise
-------
A little animal sets out on a quest to fetch something useful for the den.
The route has a few choices, and only a more efficient path keeps the pack
from wasting time and energy. The story turns on planning, a helper, and a
small change in method that makes the journey smoother.

The world keeps physical meters and emotional memes, drives the prose from
state, and includes an ASP twin for the reasonableness gate and outcome model.
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
EFFICIENCY_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "they", "object": "them", "possessive": "their"}
        if self.type in {"fox", "wolf", "dog", "cat", "bear", "mouse", "rabbit"}:
            if self.attrs.get("gender") == "female":
                mapping = {"subject": "she", "object": "her", "possessive": "her"}
            elif self.attrs.get("gender") == "male":
                mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

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
class Place:
    id: str
    label: str
    terrain: str
    shortcut: str
    danger: int
    affords: set[str] = field(default_factory=set)
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
class QuestItem:
    id: str
    label: str
    phrase: str
    needed_for: str
    weight: int = 1
    bulky: bool = False
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
class Route:
    id: str
    label: str
    effort: int
    time: int
    scenic: bool
    safe: bool
    phrase: str
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
class Trick:
    id: str
    label: str
    sense: int
    save_time: int
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


@dataclass
class StoryParams:
    place: str
    quest_item: str
    route: str
    trick: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_exhaustion(world: World) -> list[str]:
    out: list[str] = []
    h = world.get("hero")
    if h.meters["tired"] < THRESHOLD:
        return out
    sig = ("tired",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    h.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_efficiency(world: World) -> list[str]:
    out: list[str] = []
    if world.get("route").meters["efficiency"] < THRESHOLD:
        return out
    sig = ("efficiency",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["hope"] += 1
    out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("exhaustion", _r_exhaustion), Rule("efficiency", _r_efficiency)]


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


def route_cost(route: Route) -> int:
    return route.effort + route.time


def route_is_reasonable(route: Route) -> bool:
    return route.safe and route.effort <= 5


def trick_is_reasonable(trick: Trick) -> bool:
    return trick.sense >= EFFICIENCY_MIN


def best_trick() -> Trick:
    return max(TRICKS.values(), key=lambda t: t.sense)


def predict_trip(world: World, route_id: str) -> dict:
    sim = world.copy()
    _take_route(sim, sim.get("hero"), ROUTES[route_id], narrate=False)
    return {
        "time": sim.get("route").meters["spent_time"],
        "tired": sim.get("hero").meters["tired"],
    }


def _take_route(world: World, hero: Entity, route: Route, narrate: bool = True) -> None:
    hero.meters["tired"] += route.effort
    world.get("route").meters["spent_time"] += route.time
    world.get("route").meters["efficiency"] += route.effort * 0.5
    propagate(world, narrate=narrate)


def start(world: World, hero: Entity, helper: Entity, elder: Entity, place: Place, item: QuestItem) -> None:
    hero.memes["adventure"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"In the {place.label}, {hero.id} the {hero.type} was given a quest: bring back {item.phrase} for the den."
    )
    world.say(
        f"{helper.id} went too, because every good quest needs a friend, and the path through the {place.terrain} was long."
    )


def worry(world: World, elder: Entity, hero: Entity, item: QuestItem, route: Route) -> None:
    pred = predict_trip(world, route.id)
    world.facts["predicted_time"] = pred["time"]
    world.facts["predicted_tired"] = pred["tired"]
    world.say(
        f"{elder.id} peered at the trail and said, \"If you take {route.label}, it will waste time and leave you too tired to carry {item.label}.\""
    )


def choose_path(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    world.say(
        f"{hero.id} looked at the trail, then at {helper.id}, and chose {route.phrase}."
    )
    _take_route(world, hero, route)


def idea(world: World, elder: Entity, hero: Entity, trick: Trick, route: Route) -> None:
    world.say(
        f"{elder.id} smiled and offered a smarter plan: {trick.text}."
    )
    hero.meters["efficiency"] += trick.save_time
    world.get("route").meters["efficiency"] += trick.save_time


def finish(world: World, hero: Entity, helper: Entity, elder: Entity, item: QuestItem) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"By the time the sun slid low, {hero.id} came home with {item.phrase}, and everyone in the den cheered."
    )
    world.say(
        f"The clever plan made the quest feel easy, and {hero.id} tucked the prize safely beside the warm nest."
    )


def tell(place: Place, item: QuestItem, route: Route, trick: Trick,
         hero: str = "Milo", hero_gender: str = "fox",
         helper: str = "Pip", helper_gender: str = "rabbit",
         elder: str = "Aunt Nia", elder_gender: str = "fox") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    h.attrs["gender"] = "male" if hero_gender in {"fox"} else "female"
    he = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    he.attrs["gender"] = "male" if helper_gender in {"fox"} else "female"
    e = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder"))
    e.attrs["gender"] = "female"
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="route", type="route", label=route.label))
    world.add(Entity(id="item", type="item", label=item.label))

    start(world, h, he, e, place, item)
    world.para()
    worry(world, e, h, item, route)
    choose_path(world, h, he, route)
    world.para()
    idea(world, e, h, trick, route)
    world.para()
    finish(world, h, he, e, item)

    world.facts.update(hero=h, helper=he, elder=e, place=place, item_cfg=item,
                       route_cfg=route, trick_cfg=trick, outcome="efficient",
                       route_cost=route_cost(route), used_trick=trick.id)
    return world


PLACES = {
    "meadow": Place(id="meadow", label="sunny meadow", terrain="long grass", shortcut="stone bridge", danger=2, affords={"leaf", "berry"}),
    "riverbank": Place(id="riverbank", label="muddy riverbank", terrain="winding reeds", shortcut="log crossing", danger=3, affords={"berry", "shell"}),
}

ITEMS = {
    "berries": QuestItem(id="berries", label="berries", phrase="a basket of ripe berries", needed_for="supper", tags={"food"}),
    "honey": QuestItem(id="honey", label="honey", phrase="a jar of honey", needed_for="tea", tags={"food"}),
    "feather": QuestItem(id="feather", label="feather", phrase="a bright blue feather", needed_for="nest", tags={"nest"}),
}

ROUTES = {
    "long_way": Route(id="long_way", label="the long way around", effort=4, time=4, scenic=True, safe=True, phrase="the long way around the hill", tags={"long"}),
    "shortcut": Route(id="shortcut", label="the shortcut", effort=2, time=1, scenic=False, safe=True, phrase="the quick shortcut by the stones", tags={"short"}),
    "winding": Route(id="winding", label="the winding path", effort=3, time=3, scenic=True, safe=True, phrase="the winding path through the reeds", tags={"winding"}),
}

TRICKS = {
    "split": Trick(id="split", label="split the job", sense=3, save_time=2, text="split the load so each animal carried a smaller bundle", fail="split the load, but it still took too long", qa_text="split the load so the trip took less time"),
    "rest": Trick(id="rest", label="rest once", sense=2, save_time=1, text="rest once at a shady rock and then hurry on", fail="rest once, but the pause did not help much", qa_text="rested once to save a little energy"),
    "skip": Trick(id="skip", label="skip the backtrack", sense=4, save_time=3, text="skip the backtrack and return by the shorter trail", fail="skip the backtrack, but the path was blocked", qa_text="skipped the backtrack and saved time"),
}

GENDERED_NAMES = {
    "fox": ["Milo", "Junie", "Tavi", "Nell"],
    "rabbit": ["Pip", "Bun", "Luna", "Mira"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for r in ROUTES:
            for i in ITEMS:
                combos.append((p, i, r))
    return combos


def _name(rng: random.Random, kind: str) -> str:
    return rng.choice(GENDERED_NAMES[kind])


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal quest story that includes the word "efficiency" and shows a clever way to save time.',
        f"Tell a small animal adventure where {f['hero'].id} and {f['helper'].id} go on a quest for {f['item_cfg'].phrase} and learn about efficiency.",
        f"Write a child-friendly quest story where an elder animal gives a wiser plan instead of a slower one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, elder = f["hero"], f["helper"], f["elder"]
    item, route, trick = f["item_cfg"], f["route_cfg"], f["trick_cfg"]
    answers = [
        QAItem(question="Who went on the quest?", answer=f"{hero.id} went with {helper.id}, and {elder.id} helped them get started."),
        QAItem(question="What was the animal quest for?", answer=f"They were trying to bring home {item.phrase} for the den."),
        QAItem(question="What changed the trip most?", answer=f"{elder.id}'s idea made the biggest difference. The new plan used efficiency to save time and keep the quest from feeling too hard."),
        QAItem(question="How did the story end?", answer=f"It ended happily with {hero.id} bringing home {item.phrase} and everyone cheering in the den."),
    ]
    if f.get("used_trick"):
        answers.append(QAItem(question="What did the clever plan do?", answer=f"It let the animals save time by {trick.qa_text}. That made the quest feel smoother and more efficient."))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is efficiency?", answer="Efficiency means doing something in a smart way that saves time or energy. It helps a job feel easier without wasting effort."),
        QAItem(question="Why is a shortcut sometimes helpful?", answer="A shortcut can help when it is safe and truly shorter. Then the traveler gets where they need to go with less time and less tiredness."),
        QAItem(question="Why do quests often have helpers?", answer="Helpers can carry, notice things, and think of better plans. That makes hard trips easier for everyone."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", quest_item="berries", route="shortcut", trick="skip", hero="Milo", hero_gender="fox", helper="Pip", helper_gender="rabbit", elder="Aunt Nia", elder_gender="fox"),
    StoryParams(place="riverbank", quest_item="honey", route="long_way", trick="split", hero="Junie", hero_gender="fox", helper="Bun", helper_gender="rabbit", elder="Grandma Fae", elder_gender="fox"),
]


def explain_rejection(route: Route, trick: Trick) -> str:
    if not route.safe:
        return f"(No story: {route.label} is not safe enough for a quest.)"
    if not trick_is_reasonable(trick):
        return f"(No story: the plan '{trick.label}' is not efficient enough.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "efficient" if trick_is_reasonable(TRICKS[params.trick]) else "slow"


ASP_RULES = r"""
route_ok(R) :- route(R), safe(R), effort(R,E), E <= 5.
good_trick(T) :- trick(T), sense(T,S), sense_min(M), S >= M.
quest_ok(P,I,R,T) :- place(P), item(I), route(R), trick(T), route_ok(R), good_trick(T).
outcome(efficient) :- quest_ok(_,_,_,_).
outcome(slow) :- not outcome(efficient).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("danger", pid, p.danger))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("safe", rid))
        lines.append(asp.fact("effort", rid, r.effort))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", EFFICIENCY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show quest_ok/4."))
    return sorted(set(asp.atoms(model, "quest_ok")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    program = asp_program(
        "\n".join([asp.fact("chosen", params.place), asp.fact("chosen2", params.quest_item)]),
        "#show outcome/1."
    )
    model = asp.one_model(program)
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()):
        print(f"OK: ASP found {len(asp_valid_combos())} quest combinations.")
    else:
        rc = 1
        print("MISMATCH: ASP found no combinations.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story quest about efficiency.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest-item", dest="quest_item", choices=ITEMS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    combos = valid_combos()
    place, item, route = rng.choice(combos)
    trick = args.trick or rng.choice(list(TRICKS))
    if args.place:
        place = args.place
    if args.quest_item:
        item = args.quest_item
    if args.route:
        route = args.route
    if args.trick:
        trick = args.trick
    if not route_is_reasonable(ROUTES[route]) or not trick_is_reasonable(TRICKS[trick]):
        raise StoryError(explain_rejection(ROUTES[route], TRICKS[trick]))
    hero = args.hero or _name(rng, "fox")
    helper = args.helper or _name(rng, "rabbit")
    elder = args.elder or ("Aunt Nia" if rng.random() < 0.5 else "Grandma Fae")
    return StoryParams(
        place=place, quest_item=item, route=route, trick=trick,
        hero=hero, hero_gender="fox", helper=helper, helper_gender="rabbit",
        elder=elder, elder_gender="fox",
    )


def generate(params: StoryParams) -> StorySample:
    missing = [k for k in ("place", "quest_item", "route", "trick") if getattr(params, k) not in globals()[k.upper()+"S"]]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)}.)")
    world = tell(PLACES[params.place], ITEMS[params.quest_item], ROUTES[params.route], TRICKS[params.trick], params.hero, params.hero_gender, params.helper, params.helper_gender, params.elder, params.elder_gender)
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
        print(asp_program("", "#show quest_ok/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("quest combinations:")
        for t in asp_valid_combos():
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
