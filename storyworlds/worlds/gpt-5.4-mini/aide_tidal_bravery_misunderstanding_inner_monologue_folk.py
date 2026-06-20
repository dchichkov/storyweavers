#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aide_tidal_bravery_misunderstanding_inner_monologue_folk.py
===========================================================================================

A standalone storyworld for a small folk-tale coastal domain: a child, a village
aide, a tidal path, a brave misunderstanding, and an inner monologue that turns
fear into action.

The seed imagery is a little seaside tale: someone hears the tide "calling" and
thinks a helper is in trouble. In the end, bravery is not the loud kind; it is
the kind that crosses the wet sand, asks a careful question, and discovers that
the "call" was only the tide bells and the wind in the reeds.

This world keeps the simulation small:
- typed entities with physical meters and emotional memes
- a reasonableness gate over valid scene combinations
- a forward-chained causal model
- a Python gate with an inline ASP twin
- story-grounded QA generated from world state, not from parsing prose
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    tide_kind: str
    safe_when_low: bool
    risky_when_high: bool
    poem: str
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
class Misunderstanding:
    id: str
    phrase: str
    meaning: str
    wrong_guess: str
    clear_answer: str
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
class Action:
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


def _r_tide_reaches(world: World) -> list[str]:
    out: list[str] = []
    tide = world.get("tide")
    if tide.meters["high"] < THRESHOLD:
        return out
    sig = ("tide_reaches",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("causeway").meters["wet"] += 1
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["unease"] += 1
    out.append("__tide__")
    return out


def _r_brave_but_worried(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.memes["unease"] < THRESHOLD or e.memes["bravery"] < THRESHOLD:
            continue
        sig = ("inner", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["inner_monologue"] += 1
        out.append(f"__inner_{e.id}__")
    return out


CAUSAL_RULES = [
    Rule("tide_reaches", "physical", _r_tide_reaches),
    Rule("inner", "social", _r_brave_but_worried),
]


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


def tide_at_risk(place: Place) -> bool:
    return place.risky_when_high


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def best_action() -> Action:
    return max(ACTIONS.values(), key=lambda a: a.sense)


def would_affect(place: Place, misunderstanding: Misunderstanding) -> bool:
    return place.risky_when_high and misunderstanding.id in {"call", "bells"}


def tide_level_for(delay: int) -> int:
    return 1 + delay


def action_works(action: Action, delay: int) -> bool:
    return action.power >= tide_level_for(delay)


def _do_watch(world: World, narrator: Entity, aide: Entity, place: Place) -> None:
    if place.safe_when_low:
        world.say(
            f"At dusk, {narrator.id} and {aide.id} walked to {place.name}, where "
            f"{place.poem}"
        )
    else:
        world.say(
            f"At dusk, {narrator.id} and {aide.id} stood by {place.name}, where "
            f"{place.poem}"
        )


def perceive_call(world: World, child: Entity, mis: Misunderstanding, aide: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'The wind went hush-hush through the reeds, and {child.id} heard what '
        f'sounded like a call. "{mis.phrase}," {child.id} thought. '
        f'"Someone is asking for help."'
    )


def inner_monologue(world: World, child: Entity, mis: Misunderstanding) -> None:
    child.memes["bravery"] += 1
    child.memes["fear"] += 1
    world.say(
        f"Inside {child.id}'s chest, a small voice whispered, 'What if the tide "
        f"takes the path before you get there?' But another voice answered, "
        f"'Brave feet can still ask a careful question.'"
    )


def warn(world: World, aide: Entity, child: Entity, place: Place, mis: Misunderstanding) -> None:
    world.say(
        f'{aide.id} lifted a lantern and said, "{mis.clear_answer}. The tide is '
        f"only speaking with the water and the stones. Wait for the right moment, "
        f"and do not rush the causeway."
    )


def defy(world: World, child: Entity, aide: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} swallowed hard. The child did not mean to be rude, only brave, '
        f'and so {child.id} took one step onto the wet stones.'
    )


def ask_again(world: World, child: Entity, aide: Entity, mis: Misunderstanding) -> None:
    world.say(
        f"Then {child.id} stopped, listened again, and asked, 'Do you hear it too?' "
        f"{aide.id} nodded, and together they saw that {mis.wrong_guess} had been a mistake."
    )


def resolve(world: World, child: Entity, aide: Entity, place: Place, act: Action) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    aide.memes["joy"] += 1
    world.say(
        f"{aide.id} smiled and opened {act.text}. The light showed the path, and "
        f"the tide stayed on the far side of the stones."
    )
    world.say(
        f"Together they crossed at the safe time, and by the shore they found a "
        f"little lost lamb tucked beneath a driftwood arch, safe and waiting."
    )


def tell(place: Place, mis: Misunderstanding, act: Action,
         child_name: str = "Mara", child_gender: str = "girl",
         aide_name: str = "Eamon", aide_gender: str = "boy",
         helper_name: str = "Nan", helper_gender: str = "woman",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    aide = world.add(Entity(id=aide_name, kind="character", type=aide_gender, role="aide"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="elder"))
    tide = world.add(Entity(id="tide", type="tide", label="the tide"))
    causeway = world.add(Entity(id="causeway", type="place", label="the causeway"))
    tide.meters["high"] = float(tide_level_for(delay))
    child.memes["bravery"] = 1.0
    aide.memes["trust"] = 1.0
    world.facts["helper"] = helper
    world.facts["delay"] = delay

    _do_watch(world, child, aide, place)
    world.say(f"{child.id} remembered {helper.id}'s warning about the sea path.")
    perceive_call(world, child, mis, aide)
    world.para()
    inner_monologue(world, child, mis)
    warn(world, aide, child, place, mis)

    if would_affect(place, mis):
        defy(world, child, aide)
        world.para()
        ask_again(world, child, aide, mis)
        if action_works(act, delay):
            resolve(world, child, aide, place, act)
            outcome = "settled"
        else:
            world.say(
                f"But the tide was already too strong for that plan. The water "
                f"came over the stones, and the lantern light shivered on the wet dark."
            )
            world.say(
                f"{helper.id} called them back to the shore, where they waited "
                f"until the sea drew away again."
            )
            outcome = "delayed"
    else:
        world.say(
            f"{child.id} listened, and the mistaken thought drifted away like a "
            f"feather on the wind."
        )
        resolve(world, child, aide, place, act)
        outcome = "settled"

    world.facts.update(
        child=child, aide=aide, place=place, misunderstanding=mis,
        action=act, outcome=outcome, guided=outcome == "settled",
        brave=child.memes["bravery"] >= THRESHOLD,
    )
    return world


PLACES = {
    "tidal_path": Place(
        "tidal_path",
        "the tidal path",
        "tide path",
        True,
        True,
        "the stones were dry at low tide but slick and shining when the water came up",
        tags={"tidal", "tide", "folk"},
    ),
    "harbor_steps": Place(
        "harbor_steps",
        "the harbor steps",
        "harbor steps",
        True,
        True,
        "the little steps looked like a stair for gulls and boots, until the sea licked them clean",
        tags={"tidal", "harbor", "folk"},
    ),
    "salt_meadow": Place(
        "salt_meadow",
        "the salt meadow",
        "salt meadow",
        True,
        False,
        "the reeds bowed and whispered, while the water stayed far away",
        tags={"folk", "meadow"},
    ),
}

MISUNDERSTANDINGS = {
    "call": Misunderstanding(
        "call",
        "Someone is calling",
        "the sound of a tide bell and wind in the reeds",
        "a person in trouble",
        "the tide bells and the wind in the reeds",
        tags={"misunderstanding", "tidal"},
    ),
    "song": Misunderstanding(
        "song",
        "A song is coming from the water",
        "the chiming of shell bells on a post",
        "a sea sprite singing",
        "the shell bells tapping together",
        tags={"misunderstanding", "folk"},
    ),
}

ACTIONS = {
    "lantern": Action(
        "lantern", 3, 4,
        "a little lantern bright as a gold coin",
        "the lantern, but the tide was too bold",
        "held up the lantern and made the way clear",
        tags={"light", "folk"},
    ),
    "rope": Action(
        "rope", 2, 3,
        "a braided rope handhold",
        "the rope, but the water lapped too high",
        "tied a braided rope to the post and steadied the crossing",
        tags={"rope", "folk"},
    ),
    "bell": Action(
        "bell", 2, 2,
        "the old warning bell",
        "the bell, but the sea was quicker",
        "rang the old warning bell so everyone could wait",
        tags={"bell", "folk"},
    ),
    "smoke": Action(
        "smoke", 1, 1,
        "a smoky torch",
        "the torch, but smoke could not out-walk the tide",
        "held a smoky torch to the dark",
        tags={"torch"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MISUNDERSTANDINGS:
            for a in ACTIONS:
                if tide_at_risk(PLACES[p]) and would_affect(PLACES[p], MISUNDERSTANDINGS[m]):
                    combos.append((p, m, a))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    action: str
    child: str
    child_gender: str
    aide: str
    aide_gender: str
    helper: str
    helper_gender: str
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


KNOWLEDGE = {
    "tidal": [("What does tidal mean?",
               "Tidal means it has to do with the sea's rise and fall. When the tide is high, water can reach places that are usually dry.")],
    "tide": [("What is a tide?",
              "A tide is the sea moving in and out again. In some places, the water comes up over the shore and later goes back down.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light you can carry. It helps people see without needing to shout or rush.")],
    "rope": [("What is a rope handhold for?",
              "A rope handhold helps someone keep balance and hold on safely while crossing a slippery place.")],
    "bell": [("Why do people use warning bells?",
               "People use warning bells to tell others that something is changing or that they should wait and be careful.")],
    "misunderstanding": [("What is a misunderstanding?",
                          "A misunderstanding happens when someone thinks something means one thing, but it really means something else.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing the careful thing even when you feel worried. It does not mean never feeling afraid.")],
    "inner_monologue": [("What is an inner monologue?",
                         "An inner monologue is the little voice in your mind that helps you think through a choice.")],
    "aide": [("What is an aide?",
              "An aide is a helper. An aide often helps someone stay safe, learn something, or get a job done.")],
}
KNOWLEDGE_ORDER = ["tidal", "tide", "lantern", "rope", "bell", "misunderstanding", "bravery", "inner_monologue", "aide"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the words "aide" and "tidal" and shows a child misunderstanding a sound by the sea.',
        f"Tell a seaside folk story where {f['child'].id} thinks someone is calling, but {f['aide'].id} helps {f['child'].pronoun('object')} understand the tidal sound.",
        f"Write a gentle tale with bravery and an inner monologue, ending in a safe crossing at the tidal path.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    aide = f["aide"]
    place = f["place"]
    mis = f["misunderstanding"]
    act = f["action"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {aide.id}, and the old helper {f['helper'].id}. They are all part of a seaside folk tale about the tidal path."),
        ("What did {0} think at first?".format(child.id),
         f"{child.id} first thought {mis.wrong_guess}. {mis.phrase} sounded like a person in trouble, even though it was really {mis.clear_answer}."),
        ("What changed the child's mind?",
         f"{child.id}'s inner voice and {aide.id}'s calm words changed the plan. The mistake became clear when they listened again and heard the real sound."),
        ("How did they cross safely?",
         f"{aide.id} used {act.qa_text}. That helped them wait for the right moment and cross when the tide had not reached the stones."),
    ]
    if f["outcome"] == "settled":
        qa.append((
            "How did the story end?",
            f"It ended safely, with {child.id} brave enough to ask again and with {aide.id} helping. The tide stayed where it belonged, and the path led them onward."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a delay. They had to wait on the shore until the water drew back, and then they crossed after the tide passed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["misunderstanding"].tags) | set(world.facts["action"].tags)
    if world.facts["outcome"] == "settled":
        tags.add("bravery")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("tidal_path", "call", "lantern", "Mara", "girl", "Eamon", "boy", "Nan", "woman", 0),
    StoryParams("harbor_steps", "song", "rope", "Pip", "boy", "Aide", "girl", "Gran", "woman", 1),
    StoryParams("tidal_path", "call", "bell", "Lina", "girl", "Tomas", "boy", "Aunt", "woman", 0),
]


def explain_rejection(place: Place, mis: Misunderstanding) -> str:
    if not would_affect(place, mis):
        return "(No story: this scene does not create a real misunderstanding worth solving.)"
    return "(No story: this combination does not fit the tidal folk-tale premise.)"


def explain_action(rid: str) -> str:
    r = ACTIONS[rid]
    options = " / ".join(sorted(a.id for a in sensible_actions()))
    return f"(Refusing action '{rid}': it is too weak for the tide story. Try: {options}.)"


ASP_RULES = r"""
risk(P,M) :- place(P), tidal(P), misunderstanding(M).
sensible(A) :- action(A), sense(A,S), sense_min(M), S >= M.
valid(P,M,A) :- risk(P,M), action(A).

outcome(settled) :- chosen(P,M,A), risk(P,M), action(A), power(A, Pow), delay(D), tide_level(D, L), Pow >= L.
outcome(delayed) :- chosen(P,M,A), risk(P,M), action(A), power(A, Pow), delay(D), tide_level(D, L), Pow < L.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "tidal" in p.tags:
            lines.append(asp.fact("tidal", pid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    for d in range(4):
        lines.append(asp.fact("tide_level", d, tide_level_for(d)))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen", params.place, params.misunderstanding, params.action),
                        asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {a.id for a in sensible_actions()}:
        print("OK: sensible actions match.")
    else:
        rc = 1
        print("MISMATCH in sensible actions.")
    samples = list(CURATED)
    for s in range(20):
        try:
            samples.append(resolve_params(argparse.Namespace(place=None, misunderstanding=None, action=None, child=None, child_gender=None, aide=None, aide_gender=None, helper=None, helper_gender=None, delay=None), random.Random(s)))
        except Exception:
            pass
    if all(asp_outcome(p) in {"settled", "delayed"} for p in samples):
        print("OK: ASP outcome model runs on sample scenarios.")
    else:
        rc = 1
        print("MISMATCH in ASP outcome model.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = format_qa(sample)
        print("OK: generate smoke test passed.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small seaside folk-tale storyworld with tide, aid, bravery, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--aide")
    ap.add_argument("--aide-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3])
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


def _pick(rng: random.Random, seq: list[str], avoid: str = "") -> str:
    pool = [x for x in seq if x != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.misunderstanding:
        place, mis = PLACES[args.place], MISUNDERSTANDINGS[args.misunderstanding]
        if not would_affect(place, mis):
            raise StoryError(explain_rejection(place, mis))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_action(args.action))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mis, action = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    aide_gender = args.aide_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(["Mara", "Pip", "Lina", "Toby", "Nell", "Oren"])
    aide = args.aide or rng.choice(["Eamon", "Tamsin", "Ivo", "Rhea", "Hollis"])
    helper = args.helper or rng.choice(["Nan", "Gran", "Auntie", "Uncle Rook"])
    delay = args.delay if args.delay is not None else rng.randint(0, 3)
    return StoryParams(place, mis, action, child, child_gender, aide, aide_gender, helper, helper_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MISUNDERSTANDINGS[params.misunderstanding], ACTIONS[params.action],
                 params.child, params.child_gender, params.aide, params.aide_gender,
                 params.helper, params.helper_gender, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible actions: {', '.join(asp_sensible())}\n")
        for p, m, a in asp_valid_combos():
            print(f"  {p:14} {m:12} {a}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child} and {p.aide} ({p.place}, {p.misunderstanding}, {p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
