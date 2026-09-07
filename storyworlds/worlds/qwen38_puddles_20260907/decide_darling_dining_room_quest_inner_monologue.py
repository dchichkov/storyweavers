#!/usr/bin/env python3
"""A child, a treasured plate, and the quiet choice to share or keep.

Build the physics first: hunger demands food, and the dining room is where
that need becomes visible. The tension is not about breaking things, but about
allocation: the child loves the plate too much to use it for everyday soup, yet
the soup is hot and ready. 

The "Quest" is the internal decision to find a way to honor both love and
generosity. The "Inner Monologue" drives the suspense as the child weighs the
options, and the "Heartwarming" resolution comes when a creative, gentle
compromise allows the plate to remain safe while the soup is enjoyed. 

Names and wording are not the source of plot variation; the state of the
plate (safe vs. at-risk) and the soup (hot vs. eaten) drives the prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

# The example must run directly as well as through the exporter.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys that count as a "risk" to the treasured object.
RISK_KINDS = {"broken", "dirty", "moved"}

# Emotional meme keys for the hero.
MEME_KINDS = {"love", "suspense", "joy", "conflict", "kindness"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, plate, bowl, soup ...
    label: str = ""                # short reference, e.g. "plate", "bowl"
    phrase: str = ""               # full noun phrase, e.g. "a blue plate with stars"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""             # "shelf", "table", "bag", "hand"
    status: str = ""               # "safe", "at_risk", "compromised", "clean"
    plural: bool = False              # "bowls" -> them, "plate" -> it
    # Two numeric dimensions, treated uniformly:
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the dining room"
    affords: set[str] = field(default_factory=set)   # which food items this place supports
    atmosphere: str = "cozy"


@dataclass
class Food:
    """The hot meal that creates the need."""
    id: str
    label: str
    verb: str            # "drink", "eat", "share"
    warmth: str          # "hot", "warm"
    sound: str           # "slosh", "steam", "slurp"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The thing the child loves, that is at risk of being used for the food."""
    label: str
    phrase: str
    type: str
    location: str        # "shelf", "table" -- where it starts
    plural: bool = False
    fragility: str       # "delicate", "heavy"
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})  # who plausibly owns it


@dataclass
class Helper:
    """The parent figure who observes and supports the decision."""
    id: str
    label: str
    type: str
    role: str            # "chef", "guardian"


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.turn = 0
        self.history: list[tuple] = []  # (kind, actor, target, text, cause, result)
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def record(self, kind: str, text: str, *, cause: str = "", result: str = "",
               actor: str = "", target: str = "prize") -> None:
        self.history.append((kind, actor or self.facts["hero"].id, target, text, cause, result))
        self.say(text)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.turn = self.turn
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_risk(world: World) -> list[str]:
    """If the prize is on the table and food is present, it is at risk."""
    out: list[str] = []
    prize = world.facts.get("prize")
    if not prize or prize.status == "safe":
        return out
    if prize.location == "table" and world.facts.get("food_present", False):
        sig = ("risk", prize.id, world.turn)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["exposure"] += 1
            if prize.meters["exposure"] >= THRESHOLD:
                prize.status = "at_risk"
                hero = world.facts["hero"]
                hero.memes["suspense"] += 1
                out.append(f"The {prize.label} looked right in the path of the steam.")
    return out


def _r_comfort(world: World) -> list[str]:
    """If the hero is calm, suspense decreases."""
    out: list[str] = []
    hero = world.facts.get("hero")
    if hero and hero.memes["suspense"] > 0 and world.facts.get("decision_made", False):
        sig = ("calm", hero.id, world.turn)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["suspense"] -= 1
            hero.memes["joy"] += 1
            out.append("")  # silent state change
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="comfort", tag="emotional", apply=_r_comfort),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* concern and a *reasonable* fix.
# ---------------------------------------------------------------------------
def prize_at_risk(food: Food, prize: Prize) -> bool:
    """Would this food actually risk this prize if served on it or near it?"""
    # In this world, hot liquid foods risk delicate plates.
    return food.warmth == "hot" and prize.fragility == "delicate"


def select_helper_action(prize: Prize) -> str:
    """Determine the best helper response based on the prize type."""
    if prize.type == "plate":
        return "offer_bowl"
    return "offer_towel"


# ---------------------------------------------------------------------------
# Prediction: the child runs the world model forward on a copy to foresee the
# risk before deciding.
# ---------------------------------------------------------------------------
def predict_risk(world: World, actor: Entity, food: Food, prize_id: str) -> dict:
    """Simulate the scenario silently and report whether the prize is at risk."""
    sim = world.copy()
    # In the simulation, assume the child wants to use the prize.
    prize = sim.entities.get(prize_id)
    if prize:
        prize.location = "table"
        sim.facts["food_present"] = True
        propagate(sim, narrate=False)
    return {
        "at_risk": bool(prize and prize.status == "at_risk"),
        "suspense": actor.memes["suspense"],
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting, food: Food) -> str:
    if setting.atmosphere == "cozy":
        return f"The {setting.place.removeprefix('the ')} was warm, and the table was set for dinner."
    return f"The {setting.place.removeprefix('the ')} was quiet, waiting for dinner."


def food_sound(food: Food) -> str:
    return {
        "soup": "softly sloshing",
        "stew": "gently bubbling",
        "tea": "quietly steaming",
    }.get(food.id, "silently waiting")


def begin_quest(world: World) -> None:
    f = world.facts
    hero, helper, prize, food = (f[k] for k in ("hero", "helper", "prize", "food"))
    name, pos = hero.id, hero.pronoun("possessive")
    risk = predict_risk(world, hero, food, prize.id)
    if not risk["at_risk"]:
        raise StoryError("The story needs a real concern about these items.")
    
    f["predicted_risk"] = True
    world.para()
    
    hero.memes["suspense"] += 1
    hero.memes["love"] += 1
    
    cause = f"{name} wanted to eat {food.label}, but {pos} favorite {prize.label} was right there."
    result = f"{name} paused, feeling a tug in {hero.pronoun()} chest."
    
    inner = {
        "plate": f'Could I use it? No, it\'s too pretty for {food.label}. But I am so hungry.',
        "cup": f'Could I use it? It\'s so smooth. But what if I drop it?',
    }.get(prize.type, f'Is it safe to use? I want to enjoy my {food.label}.')
    
    text = (f'{cause} {result} {inner} '
            f'The {food.label} was {food_sound(food)}, and the {prize.label} caught the light.')
    
    world.record("quest_begin", text, cause=cause, result=result)


def choose_solution(world: World) -> None:
    f = world.facts
    hero, helper, prize, food = (f[k] for k in ("hero", "helper", "prize", "food"))
    name, pos = hero.id, hero.pronoun("possessive")
    solution = f["solution"]
    world.para()
    
    if solution == "find_alt":
        hero.memes["curiosity"] += 1
        cause = f"{name} decided to find a different bowl that could hold the {food.label} safely."
        result = f"{name} looked under the table and found a sturdy, plain bowl."
        text = (f'{cause} {result} "This one is strong," {name} said, holding it up. '
                f'The {prize.label} stayed on the shelf, safe and shining.')
        world.record("find_alt", text, cause=cause, result=result)
        
    elif solution == "wait":
        hero.memes["patience"] += 1
        cause = f"{name} decided to wait until the {prize.label} could be used for something special."
        result = f"{name} carefully moved the {prize.label} to a high shelf."
        text = (f'{cause} {result} '
                f'"I will save it for my birthday," {name} whispered. '
                f'{helper.label} smiled and brought a simple bowl for the dinner.')
        world.record("wait", text, cause=cause, result=result)
        
    elif solution == "ask_help":
        hero.memes["kindness"] += 1
        cause = f"{name} was not sure what to do, so {name} asked for help."
        result = f'{helper.label} offered a gentle solution: a clean, matching bowl for the food.'
        text = (f'{cause} {result} '
                f'"We can keep your {prize.label} safe and still eat," {helper.label} said. '
                f'{name} felt a warm glow of relief.')
        world.record("ask_help", text, cause=cause, result=result)

def finish(world: World) -> None:
    f = world.facts
    hero, helper, prize, food = (f[k] for k in ("hero", "helper", "prize", "food"))
    name, pos = hero.id, hero.pronoun("possessive")
    world.para()
    
    if f["solution"] == "find_alt":
        image = f"{name} sat at the table, and the {food.label} looked even better in the sturdy bowl."
    elif f["solution"] == "wait":
        image = f"The {prize.label} sat on the high shelf, watching over the dinner like a little king."
    else:
        image = f"The {prize.label} stayed safe, and the table was set with care."
    
    cause = f"The decision was made, and the {food.label} was ready."
    result = f"{name} took the first bite, and it tasted even sweeter."
    
    text = (f'{result} {image} {cause} '
            f'{helper.label} touched {hero.pronoun("object")} shoulder. '
            f'"That was a good choice, darling," {helper.label} said. '
            f'{name} smiled, feeling proud and happy.')
    
    world.record("finish", text, cause=cause, result=result)
    
    hero.memes["suspense"] = 0
    hero.memes["joy"] += 1
    f["resolved"] = True


def tell(setting: Setting, food_cfg: Food, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, helper_type: str = "mother",
         *, problem: str = "temptation", solution: str = "find_alt") -> World:
    if problem not in {"temptation"} or solution not in {"find_alt", "wait", "ask_help"}:
        raise StoryError("This response does not fit the problem.")
    
    world = World(setting)
    
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["thoughtful", "gentle"]),
    ))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, location=prize_cfg.location,
        status="safe", plural=prize_cfg.plural,
    ))
    food_ent = world.add(Entity(
        id="food", type="food", label=food_cfg.label, location="pot",
    ))
    
    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg,
                       food=food_cfg, food_ent=food_ent, setting=setting,
                       problem=problem, solution=solution, resolved=False,
                       food_present=True, decision_made=False)
    
    hero.memes.update(love=1, desire=1)
    
    opening = f"{hero.id} was in {setting.place}, waiting for dinner."
    world.record("arrive", f'{opening} {setting_detail(setting, food_cfg)} '
                 f'{hero.id}, a {hero.traits[1]} child, loved {prize.phrase}. '
                 f'{food.sound.capitalize()} in the pot, and {name} smelled the aroma.'
                 .replace("{name}", hero_name), cause="dinner_time", result="hunger")
    
    begin_quest(world)
    world.facts["decision_made"] = True
    choose_solution(world)
    finish(world)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "dining_room": Setting(place="the dining room", indoor=True, affords={"soup", "stew", "tea"}, atmosphere="cozy"),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"soup", "stew"}, atmosphere="warm"),
}

FOODS = {
    "soup": Food(
        id="soup",
        label="soup",
        verb="drink",
        warmth="hot",
        sound="slosh",
        tags={"soup", "hot"},
    ),
    "stew": Food(
        id="stew",
        label="stew",
        verb="eat",
        warmth="hot",
        sound="bubble",
        tags={"stew", "hot"},
    ),
    "tea": Food(
        id="tea",
        label="tea",
        verb="drink",
        warmth="warm",
        sound="steam",
        tags={"tea", "warm"},
    ),
}

PRIZES = {
    "plate": Prize(
        label="plate",
        phrase="a delicate blue plate with stars",
        type="plate",
        location="shelf",
        plural=False,
        fragility="delicate",
    ),
    "cup": Prize(
        label="cup",
        phrase="a tiny pink cup",
        type="cup",
        location="table",
        plural=False,
        fragility="delicate",
    ),
    "spoon": Prize(
        label="spoon",
        phrase="a shiny silver spoon",
        type="spoon",
        location="drawer",
        plural=False,
        fragility="heavy",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["thoughtful", "gentle", "curious", "careful", "patient", "sweet"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, food, prize) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for food_id in sorted(setting.affords):
            food = FOODS[food_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(food, prize):
                    combos.append((place, food_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    food: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None
    problem: str = "temptation"
    solution: str = "find_alt"


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.
KNOWLEDGE = {
    "soup": [("What is soup?",
              "Soup is a hot dish made from broth, vegetables, meat, or beans. "
              "It is usually served in a bowl.")],
    "hot": [("Why do we need to be careful with hot food?",
             "Hot food can burn our tongues if we eat it too quickly, so we blow on "
             "it or wait for it to cool down a little.")],
    "plate": [("What is a plate for?",
               "A plate is a flat dish we use to serve food like pasta, salad, or "
               "dessert. Some plates are pretty and used only for special days.")],
    "bowl": [("What is a bowl for?",
              "A bowl is a deep dish with a rounded bottom, perfect for soups, "
              "cereal, or rice.")],
    "shelf": [("Where do we put pretty dishes?",
               "We often put pretty or delicate dishes on a high shelf where they "
               "cannot be easily knocked over or broken.")],
    "decision": [("Why is it good to think before you act?",
                  "Thinking before you act helps you make good choices, like keeping "
                  "something safe or being kind to others.")],
}
KNOWLEDGE_ORDER = ["soup", "hot", "plate", "bowl", "shelf", "decision"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, helper, food, prize = f["hero"], f["helper"], f["food"], f["prize_cfg"]
    premise = "wants to use a treasured item for everyday food"
    response = {
        "find_alt": "finds a sturdy alternative to keep the item safe",
        "wait": "decides to save the item for a special occasion",
        "ask_help": "asks a parent for a gentle solution",
    }[f["solution"]]
    return [
        f'Write a short story for a 3-to-5-year-old about eating {food.label}. '
        f'A child {premise}, then {response}.',
        f"Tell a gentle story about {hero.id}, {hero.pronoun('possessive')} "
        f"{helper.label_word}, and {prize.phrase} in {world.setting.place}. "
        f"The child wants to {food.verb} {food.label}, but {premise} and {response}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """Explain recorded causes and outcomes, without smuggling answers into questions."""
    questions = {
        "quest_begin": "What made the child hesitate?",
        "find_alt": "How did the child solve the problem?",
        "wait": "Why did the child decide to wait?",
        "ask_help": "How did the parent help?",
        "finish": "How did the child feel at the end?",
    }
    return [QAItem(question=questions[kind], answer=f"{cause} {result}")
            for kind, _, _, _, cause, result in world.history if kind in questions]


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["food"].tags)
    if f.get("prize"):
        tags.add(f["prize"].type)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.status:
            bits.append(f"status={e.status}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append("--- events ---")
    for kind, actor, target, text, cause, result in world.history:
        lines.append(f"  {kind}: {actor} -> {target}: {text}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="dining_room",
        food="soup",
        prize="plate",
        name="Lily",
        gender="girl",
        helper="mother",
        trait="thoughtful",
        solution="find_alt",
    ),
    StoryParams(
        place="dining_room",
        food="stew",
        prize="cup",
        name="Tim",
        gender="boy",
        helper="father",
        trait="gentle",
        solution="ask_help",
    ),
    StoryParams(
        place="kitchen",
        food="tea",
        prize="plate",
        name="Mia",
        gender="girl",
        helper="mother",
        trait="patient",
        solution="wait",
    ),
]


def explain_rejection(food: Food, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(food, prize):
        return (f"(No story: {food.label} is {food.warmth}, but {noun} is "
                f"{prize.fragility} or not at risk. Try a delicate item with hot food.)")
    return "(No story: no suitable alternative is available for this combination.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the food is hot and the prize is delicate.
prize_at_risk(F, P) :- food(F), prize(P), warm(F, hot), fragility(P, delicate).

valid(Place, F, P) :- affords(Place, F), prize_at_risk(F, P).
valid_story(Place, F, P, Gender) :- valid(Place, F, P), wears(Gender, P).
valid_plan(Place, F, P, Solution) :- valid(Place, F, P), response(Solution).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("warm", fid, f.warmth))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("fragility", pid, pr.fragility))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for solution in {"find_alt", "wait", "ask_help"}:
        lines.append(asp.fact("response", solution))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, food, prize) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, food, prize, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def check_sample(sample: StorySample) -> None:
    """Check outcomes, not just the fact that generation returned some text."""
    world = sample.world
    f = world.facts
    hero, prize = (f[k] for k in ("hero", "prize"))
    assert f["resolved"]
    assert hero.memes["suspense"] == 0
    assert hero.memes["joy"] >= 1
    assert len(world.paragraphs) >= 3
    assert 3 <= len(sample.story_qa) <= 4
    assert len({q.question for q in sample.story_qa}) == len(sample.story_qa)
    for kind, actor, target, text, cause, result in world.history:
        assert actor in world.entities and target in world.entities
        assert text in sample.story
        if result:
            assert result in text
    assert all(q.answer.endswith(".") and len(q.answer.split()) >= 12 for q in sample.story_qa)
    assert not any(marker in sample.story for marker in ("{", "}", "__", "meters=", "memes="))


def asp_verify() -> int:
    """The static twin checks choices; executable checks prove their consequences."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    import asp
    plans = set(asp.atoms(asp.one_model(asp_program("#show valid_plan/4.")), "valid_plan"))
    expected = {(*combo, solution) for combo in python_set for solution in {"find_alt", "wait", "ask_help"}}
    if clingo_set != python_set or plans != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    signatures = set()
    checked = 0
    for place, food, prize, solution in sorted(expected):
        for gender in sorted(PRIZES[prize].genders):
            params = StoryParams(place=place, food=food, prize=prize,
                                 name="Robin", gender=gender, helper="mother",
                                 trait="curious", solution=solution)
            sample = generate(params)
            check_sample(sample)
            assert sample.to_dict() == generate(params).to_dict()
            signatures.add(tuple(kind for kind, _, _, _, _, _ in sample.world.history))
            checked += 1
    assert len(signatures) == 3
    print(f"OK: {len(python_set)} ASP/Python combinations, {len(plans)} plans; "
          f"{checked} story/state/QA/replay checks and {len(signatures)} event paths.")
    return 0


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a choice, a safe object. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--solution", choices=["find_alt", "wait", "ask_help"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    if args.food and args.prize:
        food, pr = FOODS[args.food], PRIZES[args.prize]
        if not prize_at_risk(food, pr):
            raise StoryError(explain_rejection(food, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.food is None or c[1] == args.food)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, food, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    solution = args.solution or rng.choice(["find_alt", "wait", "ask_help"])
    return StoryParams(
        place=place,
        food=food,
        prize=prize_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        solution=solution,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    if (params.place, params.food, params.prize) not in valid_combos():
        raise StoryError("The place, food, and item do not form a valid combination.")
    if params.gender not in PRIZES[params.prize].genders:
        raise StoryError(explain_gender(params.prize, params.gender))
    if params.name in {"Helper", "prize", "food"}:
        raise StoryError("The character name must not collide with an object id.")
    
    world = tell(SETTINGS[params.place], FOODS[params.food],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.helper, problem="temptation", solution=params.solution)
    
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, food, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, food, prize in triples:
            genders = sorted(g for (pl, f, pr, g) in stories
                             if (pl, f, pr) == (place, food, prize))
            print(f"  {place:9} {food:8} {prize:8}  [{', '.join(genders)}]")
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
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                raise SystemExit(str(err)) from err
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
            header = f"### {p.name}: {p.food} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
