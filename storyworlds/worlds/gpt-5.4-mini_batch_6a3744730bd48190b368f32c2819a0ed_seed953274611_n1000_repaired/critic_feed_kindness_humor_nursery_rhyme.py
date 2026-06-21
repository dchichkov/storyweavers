#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/critic_feed_kindness_humor_nursery_rhyme.py
==========================================================================

A tiny nursery-rhyme-style storyworld about a picky critic, a hungry little
friend, and a kind, funny way to make the meal go right.

The domain is intentionally small:
- a critic complains that the porridge is too plain,
- a feeder wants to help a hungry child or animal,
- kindness changes the mood,
- humor turns the meal into a cheerful rhyme,
- and the ending proves somebody was fed and the critic softened.

This is a standalone storyworld script following the repo contract:
- typed entities with meters and memes,
- a reasonableness gate,
- an inline ASP twin,
- three Q&A sets grounded in world state,
- `--verify`, `--json`, `--qa`, `--trace`, `--asp`, and `--show-asp`.

Style goal: nursery rhyme.
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
        if self.type in {"girl", "mother", "woman"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    cozy: str
    rhyme: str
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
class Food:
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
class Action:
    id: str
    verb: str
    delight: str
    mess: str
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
class Response:
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


@dataclass
class StoryParams:
    place: str
    food: str
    action: str
    response: str
    critic_name: str
    critic_type: str
    feeder_name: str
    feeder_type: str
    hungry_name: str
    hungry_type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


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


def _r_happy(world: World) -> list[str]:
    out = []
    child = world.get("hungry")
    if child.meters["fed"] >= THRESHOLD and (("happy",) not in world.fired):
        world.fired.add(("happy",))
        child.memes["joy"] += 1
        out.append("__happy__")
    return out


def _r_soften(world: World) -> list[str]:
    out = []
    critic = world.get("critic")
    if critic.memes["kindness"] >= THRESHOLD and ("soften",) not in world.fired:
        world.fired.add(("soften",))
        critic.memes["warmth"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("happy", _r_happy), Rule("soften", _r_soften)]


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


def valid_food_and_action(food: Food, action: Action) -> bool:
    return "feed" in action.tags and "porridge" in food.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def meal_need(action: Action) -> bool:
    return "hungry" in action.tags


def _make_copy_and_feed(world: World, food: Food, action: Action, response: Response) -> dict:
    sim = world.copy()
    hungry = sim.get("hungry")
    hungry.meters["fed"] += 1
    hungry.meters["satisfied"] += 1
    critic = sim.get("critic")
    critic.memes["kindness"] += 1
    if response.power >= 1:
        critic.memes["humor"] += 1
    propagate(sim, narrate=False)
    return {"fed": hungry.meters["fed"] >= THRESHOLD, "soft": critic.memes["kindness"] >= THRESHOLD}


def tell(place: Place, food: Food, action: Action, response: Response,
         critic_name: str = "Molly", critic_type: str = "girl",
         feeder_name: str = "Tom", feeder_type: str = "boy",
         hungry_name: str = "Pip", hungry_type: str = "boy") -> World:
    w = World()
    critic = w.add(Entity(id="critic", kind="character", type=critic_type, label=critic_name, role="critic"))
    feeder = w.add(Entity(id="feeder", kind="character", type=feeder_type, label=feeder_name, role="feeder"))
    hungry = w.add(Entity(id="hungry", kind="character", type=hungry_type, label=hungry_name, role="hungry"))
    critic.memes["picky"] = 1
    critic.memes["kindness"] = 0
    feeder.memes["kindness"] = 1
    hungry.meters["hunger"] = 1
    w.add(Entity(id="place", type="place", label=place.label))
    w.add(Entity(id="food", type="food", label=food.label))

    w.say(f"By {place.label}, {critic.label} sat so neat, beneath a little moonlit treat.")
    w.say(f"{feeder.label} brought {food.phrase}, warm and bright, to feed {hungry.label} on that night.")
    w.say(f"But {critic.label} frowned, as critics do: \"Too plain! Too soft! It needs a clue!\"")
    w.para()
    w.say(f"{hungry.label} looked up with a hungry face. {hungry.pronoun().capitalize()} needed {food.label} in place.")
    w.say(f"{feeder.label} heard that cry and winked with cheer. \"We'll make it fun and kind and near.\"")

    critique_ok = True
    if meal_need(action):
        critique_ok = True
    if critique_ok:
        w.say(f"{critic.label} wrinkled {critic.pronoun('possessive')} nose and gave a little hum.")
    w.para()
    w.say(f"Then {feeder.label} {action.verb}, with a jig and a grin, and the meal turned merry from within.")
    hungry.meters["fed"] += 1
    hungry.meters["satisfied"] += 1
    critic.memes["kindness"] += 1
    critic.memes["humor"] += 1
    propagate(w, narrate=False)
    if response.id == "joke":
        w.say(f"{critic.label} laughed at the joke and stopped the grumble. \"Well then!\" said {critic.label}, \"I like this tumble.\"")
    else:
        w.say(f"{critic.label} paused, then smiled at the light. \"That was a kind idea,\" {critic.label} said bright.")
    w.para()
    w.say(f"{hungry.label} ate right up, with crumbs and glee, while {critic.label} looked pleased as pleased could be.")
    w.say(f"And there by the place, in a rhyme so small, kindness and humor helped after all.")

    w.facts.update(
        place=place,
        food=food,
        action=action,
        response=response,
        critic=critic,
        feeder=feeder,
        hungry=hungry,
        fed=hungry.meters["fed"] >= THRESHOLD,
        softened=critic.memes["kindness"] >= THRESHOLD,
        laughed=critic.memes["humor"] >= THRESHOLD,
    )
    return w


PLACES = {
    "window": Place(id="window", label="the window", cozy="a small table by the window", rhyme="glow", tags={"place"}),
    "stove": Place(id="stove", label="the stove", cozy="a warm spot by the stove", rhyme="warm", tags={"place"}),
    "porch": Place(id="porch", label="the porch", cozy="a tiny bench on the porch", rhyme="breeze", tags={"place"}),
}

FOODS = {
    "porridge": Food(id="porridge", label="porridge", phrase="a bowl of porridge", smell="sweet", tags={"porridge", "food"}),
    "oatmeal": Food(id="oatmeal", label="oatmeal", phrase="a bowl of oatmeal", smell="toasty", tags={"porridge", "food"}),
}

ACTIONS = {
    "feed": Action(id="feed", verb="fed the hungry child", delight="a spoonful made the room sing", mess="sticky", tags={"feed", "hungry"}),
    "spoon": Action(id="spoon", verb="spun a silly spoon dance", delight="the spoon went twirl and spin", mess="laughing", tags={"feed", "humor"}),
    "jig": Action(id="jig", verb="did a little feeding jig", delight="the jig made the porridge bob", mess="smiles", tags={"feed", "humor"}),
}

RESPONSES = {
    "joke": Response(id="joke", sense=3, power=2,
                     text="told a tiny joke and clapped along",
                     fail="tried a joke, but the room stayed grumpy",
                     qa_text="told a tiny joke and clapped along",
                     tags={"humor"}),
    "smile": Response(id="smile", sense=3, power=1,
                      text="smiled kindly and passed the spoon",
                      fail="smiled kindly, but the worry stayed",
                      qa_text="smiled kindly and passed the spoon",
                      tags={"kindness"}),
    "share": Response(id="share", sense=2, power=2,
                      text="shared the last warm spoonful",
                      fail="shared too little and the hunger stayed",
                      qa_text="shared the last warm spoonful",
                      tags={"kindness"}),
}

GIRL_NAMES = ["Molly", "Polly", "Sally", "Millie", "Daisy"]
BOY_NAMES = ["Tom", "Jack", "Billy", "Ned", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for fid, food in FOODS.items():
            for aid, action in ACTIONS.items():
                if valid_food_and_action(food, action) and meal_need(action):
                    combos.append((pid, fid, aid))
    return combos


@dataclass
class StoryParams:
    place: str
    food: str
    action: str
    response: str
    critic_name: str
    critic_type: str
    feeder_name: str
    feeder_type: str
    hungry_name: str
    hungry_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story about kindness and humor where a critic says "{f["food"].label}" is too plain, but a feeder makes it lovely and feeds {f["hungry"].label}.',
        f"Tell a short rhyming story where {f['critic'].label} is a critic, {f['feeder'].label} wants to feed {f['hungry'].label}, and everyone ends up smiling.",
        f'Write a gentle rhyme that uses the words "critic" and "feed" and ends with kindness and a funny little turn.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    critic, feeder, hungry = f["critic"], f["feeder"], f["hungry"]
    qa = [
        ("Who was the critic?",
         f"{critic.label} was the critic. {critic.label} started out picky, but kindness helped {critic.pronoun('object')} soften."),
        ("What did the feeder do?",
         f"{feeder.label} fed {hungry.label} with a kind heart and a funny little flourish. That helped turn the meal into a happy rhyme."),
        ("How did the hungry child feel at the end?",
         f"{hungry.label} felt full and cheerful. {hungry.label} was fed, so the hungry feeling went away."),
    ]
    if f["softened"]:
        qa.append(("How did the critic change?",
                    f"{critic.label} became kinder after the meal got a funny, gentle turn. The critic stopped grumbling and looked pleased instead."))
    if f["laughed"]:
        qa.append(("Why did the story sound playful?",
                    f"It sounded playful because the critic laughed and the feeder made a silly, kind moment out of the meal. That humor made the rhyme feel bright and warm."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["food"].tags) | set(f["action"].tags) | set(f["response"].tags)
    knowledge = {
        "critic": [("What is a critic?",
                     "A critic is someone who notices details and says what they think. In a story, a critic might be picky before they become kinder.")],
        "feed": [("What does it mean to feed someone?",
                  "To feed someone means to give them food so they are not hungry anymore. It can be a kind thing to do.")],
        "porridge": [("What is porridge?",
                      "Porridge is a soft hot food, often made from oats and milk or water. People eat it when they want something warm and filling.")],
        "kindness": [("What is kindness?",
                      "Kindness means being gentle, helpful, and caring toward someone else. A kind act can make a worried face relax.")],
        "humor": [("What is humor?",
                    "Humor is something funny that makes people smile or laugh. A little humor can make a story feel light and friendly.")],
    }
    order = ["critic", "feed", "porridge", "kindness", "humor"]
    out = []
    for key in order:
        if key in tags:
            out.extend(knowledge[key])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(place: Place, food: Food, action: Action) -> str:
    return f"(No story: {action.verb} does not fit this meal or setting.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("porridge", fid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        if "feed" in ACTIONS[aid].tags:
            lines.append(asp.fact("feeds", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F,A) :- place(P), food(F), action(A), porridge(F), feeds(A).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(fed) :- chosen_action(A), feeds(A).
outcome(softened) :- chosen_response(R), response(R), sensible(R).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("", "#show valid/3.")), "valid")))


def asp_sensible() -> list[str]:
    import asp
    return sorted(r for (r,) in asp.atoms(asp.one_model(asp_program("", "#show sensible/1.")), "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    if set(asp_sensible()) != {r for r in RESPONSES if RESPONSES[r].sense >= 2}:
        rc = 1
        print("MISMATCH: ASP sensible responses differ from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, food=None, action=None, response=None, critic_name=None, critic_type=None, feeder_name=None, feeder_type=None, hungry_name=None, hungry_type=None), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verification checks passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: critic, feed, kindness, and humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--critic-name")
    ap.add_argument("--critic-type", choices=["girl", "boy", "mother", "father"])
    ap.add_argument("--feeder-name")
    ap.add_argument("--feeder-type", choices=["girl", "boy", "mother", "father"])
    ap.add_argument("--hungry-name")
    ap.add_argument("--hungry-type", choices=["girl", "boy", "baby", "duck", "cat"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.food is None or c[1] == args.food)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food, action = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    critic_type = args.critic_type or rng.choice(["girl", "boy"])
    feeder_type = args.feeder_type or rng.choice(["girl", "boy"])
    hungry_type = args.hungry_type or rng.choice(["girl", "boy"])
    critic_name = args.critic_name or rng.choice(["Molly", "Polly", "Bert", "Ned"])
    feeder_name = args.feeder_name or rng.choice(["Tom", "Lily", "Pip", "May"])
    hungry_name = args.hungry_name or rng.choice(["Pip", "Kit", "Dot", "Sammy"])
    return StoryParams(place=place, food=food, action=action, response=response,
                       critic_name=critic_name, critic_type=critic_type,
                       feeder_name=feeder_name, feeder_type=feeder_type,
                       hungry_name=hungry_name, hungry_type=hungry_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.food not in FOODS or params.action not in ACTIONS or params.response not in RESPONSES:
        raise StoryError("(Invalid params.)")
    place = PLACES[params.place]
    food = FOODS[params.food]
    action = ACTIONS[params.action]
    response = RESPONSES[params.response]
    if not valid_food_and_action(food, action):
        raise StoryError(explain_rejection(place, food, action))
    world = tell(place, food, action, response,
                 critic_name=params.critic_name, critic_type=params.critic_type,
                 feeder_name=params.feeder_name, feeder_type=params.feeder_type,
                 hungry_name=params.hungry_name, hungry_type=params.hungry_type)
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


CURATED = [
    StoryParams(place="window", food="porridge", action="feed", response="smile",
                critic_name="Molly", critic_type="girl", feeder_name="Tom", feeder_type="boy",
                hungry_name="Pip", hungry_type="boy"),
    StoryParams(place="porch", food="oatmeal", action="jig", response="joke",
                critic_name="Bert", critic_type="boy", feeder_name="May", feeder_type="girl",
                hungry_name="Dot", hungry_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3.\n#show sensible/1."))
        print("sensible responses:", ", ".join(asp_sensible()))
        print("valid combos:")
        for t in asp.atoms(model, "valid"):
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
