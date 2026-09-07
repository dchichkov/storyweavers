#!/usr/bin/env python3
"""A child, a cold bath, and the quiet courage to face a tricky moment with a friend.

Build the physics first: cold water chills the body and creates a shiver.
Predict on a copy before choosing to dive; execute on the real world afterward.
Different problems permit different actions: wait, encourage, distract, or
join in. Record each turn after changing state, then derive QA from those
events. The 'naked' state is a physical condition, not a plot device for
shame, but a condition that makes bravery necessary.
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

# Body regions, used for the cold-sensitivity constraint.
REGIONS = {"body"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "character"         # child, friend, tub, towel ...
    label: str = ""                # short reference, e.g. "tub", "towel"
    phrase: str = ""               # full noun phrase, e.g. "a big blue tub"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    present: bool = True           # is this entity in the room?
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "daughter"}
        male = {"boy", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the bathroom"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)   # which actions this place supports


@dataclass
class Action:
    """A brave or cautious choice involving water."""
    id: str
    verb: str            # after "wanted to ..."             : "get in the tub"
    gerund: str          # after "loved playing ... and ..." : "washing"
    chill: str           # mess kind key, one of COLD_KINDS  : "chill"
    state: str           # physical state: "naked", "drying"
    zone: set[str]       # body regions exposed to cold
    keyword: str = ""    # topic word for generation prompts : "bath"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    """A comfort item reduces chill."""
    id: str
    label: str
    covers: set[str]     # regions it warms
    warms: set[str]      # mess kinds it neutralizes
    plural: bool = False
    replaces: bool = False


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # splash zone of the activity in play
        self.activity: Optional[Action] = None
        self.active_actor: str = ""
        self.turn = 0
        self.history: list[Event] = []
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def covered(self, actor: Entity, region: str, mess: str) -> bool:
        """Is `region` shielded by some protective gear the actor is wearing?"""
        return any(g.protective and region in g.covers and mess in g.warms
                   for g in self.worn_items(actor))

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
               actor: str = "", target: str = "hero") -> None:
        self.history.append(Event(
            kind=kind, actor=actor or self.facts["hero"].id, target=target, text=text,
            cause=cause, result=result,
        ))
        self.say(text)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.activity = self.activity
        clone.active_actor = self.active_actor
        clone.turn = self.turn
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


def _r_chill(world: World) -> list[str]:
    """actor naked + wet -> cold + shiver."""
    out: list[str] = []
    if world.activity is None:
        return out
    actor = world.get(world.active_actor)
    mess = world.activity.chill
    if actor.meters["wet"] >= THRESHOLD and not world.covered(actor, "body", mess):
        if ("chill", actor.id, world.turn) not in world.fired:
            world.fired.add(("chill", actor.id, world.turn))
            actor.meters[mess] += 1
            actor.meters["shiver"] += 1
            out.append(f"{actor.id} felt the cold start to tingle.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="chill", tag="physical", apply=_r_chill),
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
def action_at_risk(action: Action, state: str) -> bool:
    """Would this action actually cause chill in this state?"""
    return state in action.zone or action.state == state


def select_gear(action: Action, state: str) -> Optional[Gear]:
    """Match the mess and region, or replace the at-risk clothes entirely."""
    for gear in GEAR:
        if "body" in gear.covers and (gear.replaces or action.chill in gear.warms):
            return gear
    return None


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        raise StoryError("This place does not support that action.")
    world.turn += 1
    world.activity = action
    world.active_actor = actor.id
    world.zone = set(action.zone)
    actor.meters["wet"] += 1
    actor.meters["courage"] += 1
    propagate(world, narrate=narrate)

SOLUTIONS = {
    "fear": ("comfort", "distraction"),
    "shiver": ("warmth", "friend"),
    "hesitation": ("example", "support"),
    "cold_start": ("gradual", "play")
}


def begin_problem(world: World) -> None:
    f = world.facts
    hero, friend, tub = (f[k] for k in ("hero", "friend", "tub"))
    name, pos = hero.id, hero.pronoun("possessive")
    risk = predict_mess(world, hero, f["action"], "body")
    if not risk["chilled"]:
        raise StoryError("The story needs a real concern about the cold.")
    f["predicted_chill"] = True
    world.para()
    if f["problem"] == "fear":
        hero.memes["fear"] += 1
        cause = f"{name} looked at the water and saw their own reflection, but it looked wobbly."
        result = f"{name} pulled {pos} knees to {pos} chest, waiting."
        text = (f'{cause} "It looks deep," {name} whispered. '
                f'{result} {friend.id} waited patiently nearby, holding a duck.')
    elif f["problem"] == "shiver":
        _do_action(world, hero, f["action"], narrate=False)
        hero.memes["discomfort"] += 1
        cause = f"{name} jumped in before the water got warm."
        result = f"{name}'s toes curled up tight."
        text = (f'{cause} {result} "Brrr!" {name} said, '
                f'and the little toes tried to walk on the bottom of the tub.')
    elif f["problem"] == "hesitation":
        hero.memes["doubt"] += 1
        cause = f"{name} stood at the edge of the tub, one foot in, one foot out."
        result = f"{name} wasn't sure if {pos} toes should go first."
        text = (f'{cause} {result} "Which foot comes first?" {name} asked. '
                f'{friend.id} smiled and held out a rubber duck.')
    else:
        hero.memes["anxiety"] += 1
        cause = "The air in the bathroom was crisp, and the towel felt thin."
        result = f"{name} wrapped the towel tight, but it didn't hide the shiver."
        text = (f'{cause} {result} {name} looked at {friend.id}. '
                f'"Do you think I can do it?" {name} asked quietly.')
    world.record(f["problem"], text, cause=cause, result=result)


def choose_solution(world: World) -> None:
    f = world.facts
    hero, friend, tub = (f[k] for k in ("hero", "friend", "tub"))
    name, pos = hero.id, hero.pronoun("possessive")
    solution = f["solution"]
    world.para()
    if solution == "comfort":
        friend.memes["care"] += 1
        cause = f"{friend.id} knew that {name} needed a friend closer than a towel."
        result = f"{friend.id} sat on the floor and started a song."
        world.record("comfort", f'{cause} "Shake, rattle, and roll," {friend.id} sang. '
                     f'{result} {name} started to sway to the beat.')
        return
    if solution == "distraction":
        friend.memes["joy"] += 1
        cause = f"{friend.id} decided that bubbles would be more interesting than the dark water."
        result = f"{friend.id} squirted a big cloud of foam onto the water."
        world.record("distraction", f'{cause} {result} '
                     f'Now the water looked like a white, fluffy sheep pasture.')
    if solution == "warmth":
        # Washing settles the actual cleaning debt; the next play can soil it again.
        hero.meters["wet"] = 0
        hero.meters["warm"] = 1
        hero.memes["comfort"] += 1
        cause = f"The cold would not go away just because {name} stopped moving."
        result = f"{friend.id} handed over a warm cup of cocoa, and the steam curled up."
        world.record("warmth", f'{cause} {result} '
                     f'{name} took a sip, and the warmth spread to the toes.')
    if solution == "friend":
        _do_action(world, friend, f["action"], narrate=False)
        friend.memes["courage"] += 1
        cause = f"{friend.id} decided to show that the water wasn't scary by getting in too."
        result = f"{friend.id} splashed gently, making a soft 'plip'."
        world.record("friend", f'{cause} {result} '
                     f'"See? It\'s fun," {friend.id} said, holding a duck aloft.')
        return
    if solution == "example":
        friend.memes["calm"] += 1
        cause = f"{friend.id} didn't rush, but moved slowly to show the way."
        result = f"{friend.id} lifted one toe, then the other, into the air."
        world.record("example", f'{cause} {result} '
                     f'"One, two, three," {friend.id} counted softly.')
    if solution == "support":
        friend.memes["strength"] += 1
        cause = f"{friend.id} held onto {name}'s hand to make the tub feel like a boat."
        result = f"{name} felt steady, like a leaf on a gentle stream."
        world.record("support", f'{cause} {result} '
                     f'"I\'m right here," {friend.id} promised.')
    if solution == "gradual":
        hero.memes["patience"] += 1
        cause = f"{name} decided to go in by inches, not all at once."
        result = f"{name} dipped a toe, then a heel, feeling the water's temperature."
        world.record("gradual", f'{cause} {result} '
                     f'"It\'s just cool," {name} realized, and took a deep breath.')
    if solution == "play":
        hero.memes["joy"] += 1
        cause = f"{name} looked at the duck and saw a game instead of a chore."
        result = f"{name} grabbed the duck and started to paddle."
        world.record("play", f'{cause} {result} '
                     f'Paddle, splash, wiggle -- the duck went round and round.')
    hero.memes["fear"] = 0
    hero.memes["anxiety"] = 0
    hero.memes["discomfort"] = 0
    f["resolved"] = True


def finish(world: World) -> None:
    f = world.facts
    hero, friend, tub = (f[k] for k in ("hero", "friend", "tub"))
    name, pos = hero.id, hero.pronoun("possessive")
    world.para()
    if f["solution"] == "comfort":
        result = f"{name} smiled, and the wobbly reflection looked happy too."
        image = f"{name} and {friend.id} sat together, the song still humming in the air."
        world.record("end", f'{result} {image}', cause="", result=result, target=hero.id)
    else:
        _do_action(world, hero, f["action"], narrate=False)
        f["played"] = True
        result = f"{name} finished washing, and the water sparkled."
        image = {
            "bath": f"{name} wrapped in a dry towel, looking like a little cloud.",
            "shower": f"{name} stepping out, steam rising around them like a halo.",
            "pool": f"{name} floating on their back, eyes closed in peace."
        }[f["action"].id]
        world.record("play", f'{result} {image}', cause="", result=result)
    hero.memes["courage"] += 1
    friend.memes["friendship"] += 1


def tell(setting: Setting, action: Action,
         hero_name: str = "Lily", hero_type: str = "girl",
         friend_name: str = "Ben", friend_type: str = "boy",
         *, problem: str = "fear", solution: str = "comfort") -> World:
    if problem not in SOLUTIONS or solution not in SOLUTIONS[problem]:
        raise StoryError("This response does not fit the problem.")
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["brave", "sensitive"],
    ))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label="friend"))
    tub = world.add(Entity(id="tub", type="tub", label="tub", phrase="a big blue tub"))
    towel = world.add(Entity(id="towel", type="towel", label="towel", phrase="a soft pink towel"))
    duck = world.add(Entity(id="duck", type="duck", label="duck", phrase="a yellow rubber duck"))
    world.facts.update(hero=hero, friend=friend, tub=tub, towel=towel, duck=duck,
                       action=action, setting=setting,
                       problem=problem, solution=solution, played=False, resolved=False)
    hero.memes.update(desire=1, curiosity=1)
    friend.memes.update(care=1, support=1)
    pos = hero.pronoun("possessive")
    openings = {
        "fear": f"{hero_name} stood in front of the tub, holding the towel tight.",
        "shiver": f"{hero_name} was ready for the bath, but the water was just starting to fill.",
        "hesitation": f"{hero_name} looked at the duck, then at the water, then at {friend_name}.",
        "cold_start": f"The room was bright, but the air felt cool against {hero_name}'s back."
    }
    world.record("arrive", f'{openings[problem]} The water was clear and still. '
                 f'{hero_name} was naked, just as the bath required, and '
                 f'{action_delight(action)}.')
    begin_problem(world)
    choose_solution(world)
    finish(world)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "bathroom": Setting(place="the bathroom", indoor=True, affords={"bath", "shower"}),
    "pool": Setting(place="the pool", indoor=False, affords={"pool"}),
}

ACTIONS = {
    "bath": Action(
        id="bath",
        verb="get in the tub",
        gerund="washing",
        chill="chill",
        state="naked",
        zone={"body"},
        keyword="bath",
        tags={"water", "cold"},
    ),
    "shower": Action(
        id="shower",
        verb="stand in the shower",
        gerund="washing",
        chill="chill",
        state="naked",
        zone={"body"},
        keyword="shower",
        tags={"water", "cold"},
    ),
    "pool": Action(
        id="pool",
        verb="swim in the pool",
        gerund="swimming",
        chill="chill",
        state="swimsuit",
        zone={"body"},
        keyword="pool",
        tags={"water", "cold"},
    ),
}

GEAR = [
    Gear(
        id="towel",
        label="a warm towel",
        covers={"body"},
        warms={"chill"},
        plural=False,
    ),
    Gear(
        id="robe",
        label="a fluffy robe",
        covers={"body"},
        warms={"chill"},
        plural=False,
        replaces=True,
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "shy", "curious", "cheerful", "gentle", "determined"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, hero_type) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in sorted(setting.affords):
            act = ACTIONS[act_id]
            for hero_type in ["girl", "boy"]:
                if action_at_risk(act, "naked") or act.state == "swimsuit":
                    if select_gear(act, "body"):
                        combos.append((place, act_id, hero_type))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    action: str
    hero_type: str
    name: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None
    problem: str = "fear"
    solution: str = "comfort"


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.
KNOWLEDGE = {
    "water": [("Why does water feel cold?",
               "Water feels cold when it is below the temperature of your skin, "
               "because it takes heat from your body to warm up.")],
    "cold": [("What happens when you get cold?",
              "When you get cold, your body shivers to make heat, and your skin "
              "may turn pale or blue.")],
    "towel": [("What is a towel for?",
               "A towel is a piece of soft fabric used to dry your body after "
               "a bath or shower, helping to keep you warm.")],
    "duck": [("Why do children like rubber ducks?",
              "Rubber ducks are fun to bathe with because they float and don't "
              "sink, making bath time feel like a game.")],
    "bravery": [("What is bravery?",
                 "Bravery is doing something even when you are scared. It is "
                 "about feeling the fear but moving forward anyway.")],
    "friendship": [("How can a friend help?",
                    "A friend can help by being there, listening, or joining in "
                    "with you, which makes scary things feel less scary.")],
}
KNOWLEDGE_ORDER = ["water", "cold", "towel", "duck", "bravery", "friendship"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, friend, act = f["hero"], f["friend"], f["action"]
    kw = act.keyword
    premise = {
        "fear": "feels scared of the water",
        "shiver": "feels a sudden shiver",
        "hesitation": "hesitates at the edge",
        "cold_start": "feels the cold air"
    }[f["problem"]]
    response = {
        "comfort": "is comforted by a friend's song",
        "distraction": "is distracted by bubbles",
        "warmth": "is warmed by a drink",
        "friend": "is encouraged by a friend joining in",
        "example": "sees a friend's gentle example",
        "support": "feels supported by a friend's hand",
        "gradual": "enters the water gradually",
        "play": "turns the moment into play"
    }[f["solution"]]
    return [
        f'Write a short nursery rhyme story about "{kw}" where a child {premise}, '
        f'and a friend helps them {response}.',
        f"Tell a gentle story about {hero.id}, {friend.id}, and a {act.keyword} "
        f"at {world.setting.place}. The child {premise}, and {response}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """Explain recorded causes and outcomes, without smuggling answers into questions."""
    questions = {
        "fear": "Why did the child hesitate?",
        "shiver": "What made the child shiver?",
        "hesitation": "What was the child unsure about?",
        "cold_start": "Why did the child feel anxious?",
        "comfort": "How did the friend help the child feel better?",
        "distraction": "What did the friend do to change the mood?",
        "warmth": "What made the child feel warm?",
        "friend": "How did the friend show bravery?",
        "example": "How did the friend show the way?",
        "support": "How did the friend provide support?",
        "gradual": "How did the child decide to enter the water?",
        "play": "What turned the moment into fun?",
        "end": "How did the story end?",
        "play": "What happened in the end?",
    }
    return [QAItem(question=questions[e.kind], answer=f"{e.cause} {e.result}")
            for e in world.history if e.kind in questions]


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["action"].tags)
    tags.add("bravery")
    tags.add("friendship")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.actor} -> {event.target}: {event.text}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="bathroom",
        action="bath",
        hero_type="girl",
        name="Lily",
        friend_name="Ben",
        friend_type="boy",
        trait="brave",
    ),
    StoryParams(
        place="bathroom",
        action="shower",
        hero_type="boy",
        name="Tim",
        friend_name="Mia",
        friend_type="girl",
        trait="curious",
        problem="shiver",
        solution="warmth",
    ),
    StoryParams(
        place="pool",
        action="pool",
        hero_type="girl",
        name="Mia",
        friend_name="Leo",
        friend_type="boy",
        trait="gentle",
        problem="hesitation",
        solution="example",
    ),
    StoryParams(
        place="bathroom",
        action="bath",
        hero_type="boy",
        name="Max",
        friend_name="Ava",
        friend_type="girl",
        trait="cheerful",
        problem="cold_start",
        solution="play",
    ),
]
CURATED.extend([
    replace(CURATED[0], problem="fear", solution="distraction"),
    replace(CURATED[2], problem="hesitation", solution="support"),
    replace(CURATED[3], problem="cold_start", solution="gradual"),
])


def explain_rejection(action: Action, hero_type: str) -> str:
    verb = "feel" if action.plural else "feels"
    if not action_at_risk(action, "naked"):
        return (f"(No story: {action.gerund} doesn't expose the body to cold "
                f"in a way that requires this gear. Try a different action.)")
    return (f"(No story: no gear can protect from {action.gerund} in this "
            f"manner. The compromise must actually cover the at-risk body, "
            f"so this argument is rejected.)")


def explain_gender(hero_type: str) -> str:
    ok = " / ".join(["girl", "boy"])
    return (f"(No story: the hero type must be {ok}; try --hero_type {hero_type}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (action_at_risk / select_gear / valid_combos).
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An action is at risk when it exposes the body to cold.
action_at_risk(A, State) :- action_state(A, S), state_exposes(S).
exposes("naked").
exposes("swimsuit").

% Gear is a compatible fix only when it warms the body.
protects(G, A) :- gear(G), warms(G, "chill"), covers(G, "body").
has_fix(A) :- protects(_, A).

valid(Place, A, HeroType) :- affords(Place, A), action_at_risk(A, "naked"), has_fix(A).
valid_story(Place, A, HeroType) :- valid(Place, A, HeroType).
valid_plan(Place, A, HeroType, Problem, Solution) :- valid(Place, A, HeroType), response(Problem, Solution).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_state", aid, a.state))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        if g.replaces:
            lines.append(asp.fact("changes_clothes", g.id))
        for m in sorted(g.warms):
            lines.append(asp.fact("warms", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    for problem, solutions in SOLUTIONS.items():
        for solution in solutions:
            lines.append(asp.fact("response", problem, solution))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, activity, hero_type) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, hero_type) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def check_sample(sample: StorySample) -> None:
    """Check outcomes, not just the fact that generation returned some text."""
    world = sample.world
    f = world.facts
    hero, act = (f[k] for k in ("hero", "action"))
    played = f["solution"] not in ("comfort", "warmth", "distraction")
    steps = int(f["problem"] == "shiver") + int(played)
    assert hero.meters["wet"] == steps
    assert f["played"] == played and f["resolved"]
    assert len(world.paragraphs) >= 4 and 3 <= len(sample.story_qa) <= 4
    assert len({q.question for q in sample.story_qa}) == len(sample.story_qa)
    for event in world.history:
        assert event.actor in world.entities and event.target in world.entities
        assert event.text in sample.story
        if event.result:
            assert event.result in event.text
    assert all(q.answer.endswith(".") and len(q.answer.split()) >= 12 for q in sample.story_qa)
    assert not any(marker in sample.story for marker in ("{", "}", "__", "meters=", "memes="))


def asp_verify() -> int:
    """The static twin checks choices; executable checks prove their consequences."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    import asp
    plans = set(asp.atoms(asp.one_model(asp_program("#show valid_plan/5.")), "valid_plan"))
    expected = {(*combo, problem, solution) for combo in python_set
                for problem, solutions in SOLUTIONS.items() for solution in solutions}
    if clingo_set != python_set or plans != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    signatures = set()
    checked = 0
    for place, action, hero_type, problem, solution in sorted(expected):
        params = StoryParams(place=place, action=action, hero_type=hero_type,
                             name="Robin", friend_name="Sally",
                             friend_type="girl", trait="curious", problem=problem, solution=solution)
        sample = generate(params)
        check_sample(sample)
        assert sample.to_dict() == generate(params).to_dict()
        signatures.add(tuple(event.kind for event in sample.world.history))
        checked += 1
    assert len(signatures) == sum(map(len, SOLUTIONS.values()))
    print(f"OK: {len(python_set)} ASP/Python combinations, {len(plans)} plans; "
          f"{checked} story/state/QA/replay checks and {len(signatures)} event paths.")
    return 0


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a bath, a brave moment. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero_type", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend_name")
    ap.add_argument("--friend_type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--problem", choices=SOLUTIONS)
    ap.add_argument("--solution", choices=sorted({s for choices in SOLUTIONS.values() for s in choices}))
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
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.action and args.hero_type:
        act = ACTIONS[args.action]
        if not action_at_risk(act, "naked"):
            raise StoryError(explain_rejection(act, args.hero_type))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.hero_type is None or c[2] == args.hero_type)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, action, hero_type = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    problems = [p for p, choices in SOLUTIONS.items()
                if (args.problem is None or p == args.problem)
                and (args.solution is None or args.solution in choices)]
    if not problems:
        raise StoryError("That solution does not fit the requested problem.")
    problem = rng.choice(problems)
    solution = args.solution or rng.choice(SOLUTIONS[problem])
    return StoryParams(
        place=place,
        action=action,
        hero_type=hero_type,
        name=name,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
        problem=problem,
        solution=solution,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    if (params.place, params.action, params.hero_type) not in valid_combos():
        raise StoryError("The place, action, and hero type do not form a valid combination.")
    if params.hero_type not in ["girl", "boy"]:
        raise StoryError("The hero type must be girl or boy.")
    if params.name in {"tub", "towel", "duck", "friend"}:
        raise StoryError("The character name must not collide with an object id.")
    world = tell(SETTINGS[params.place], ACTIONS[params.action],
                 params.name, params.hero_type,
                 params.friend_name, params.friend_type,
                 problem=params.problem, solution=params.solution)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, action, hero_type) combos "
              f"({len(stories)} with type):\n")
        for place, act, h_type in triples:
            print(f"  {place:9} {act:8} {h_type:8}")
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
            header = f"### {p.name}: {p.action} at {p.place} (hero: {p.hero_type})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
