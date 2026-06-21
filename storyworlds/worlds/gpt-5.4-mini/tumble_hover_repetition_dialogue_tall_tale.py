#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tumble_hover_repetition_dialogue_tall_tale.py
===============================================================================

A standalone story world sketch for a tall-tale style kid story about a tiny
crew, a tumble, and a hovering rescue. The domain is deliberately small:
children, a precarious object, a breezy hazard, and a surprisingly grand,
repeated, dialogue-filled solution.

This world keeps the contract for Storyweavers scripts:
- typed entities with meters and memes
- state-driven narration
- a Python reasonableness gate plus inline ASP twin
- three QA sets grounded in the world model
- standard CLI modes including --verify, --asp, --show-asp, --qa, --json

The seed words are honored by the core premise:
- tumble: the risky drop
- hover: the strange tall-tale rescue
- repetition: a repeated refrain in the dialogue and narration
- dialogue: direct speech from the characters
- tall tale: a grand, slightly larger-than-life style

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/tumble_hover_repetition_dialogue_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/tumble_hover_repetition_dialogue_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/tumble_hover_repetition_dialogue_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/tumble_hover_repetition_dialogue_tall_tale.py --verify
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    can_hover: bool = False
    can_tumble: bool = False
    fragile: bool = False
    heavy: bool = False

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
class Prop:
    id: str
    label: str
    phrase: str
    can_tumble: bool = True
    fragile: bool = False
    can_hover: bool = False

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
class Move:
    id: str
    title: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_tumble(world: World) -> list[str]:
    out: list[str] = []
    for prop in list(world.entities.values()):
        if prop.meters["tumbling"] < THRESHOLD:
            continue
        sig = ("tumble", prop.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["alarm"] += 1
        out.append("__tumble__")
    return out


def _r_hover(world: World) -> list[str]:
    out: list[str] = []
    if not ("rescue" in world.facts and world.facts["rescue"]):
        return out
    for kid in world.characters():
        if kid.meters["hovering"] < THRESHOLD:
            continue
        sig = ("hover", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["wonder"] += 1
        out.append("__hover__")
    return out


CAUSAL_RULES = [Rule("tumble", "physical", _r_tumble), Rule("hover", "magical", _r_hover)]


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


def hazard_at_risk(prop: Prop) -> bool:
    return prop.can_tumble and prop.fragile


def sensible_moves() -> list[Move]:
    return [m for m in MOVES.values() if m.sense >= SENSE_MIN]


def fire_power(prop: Prop, delay: int) -> int:
    return 2 + delay if prop.fragile else 1 + delay


def move_beats(prop: Prop, delay: int, move: Move) -> bool:
    return move.power >= fire_power(prop, delay)


def predict(world: World, prop_id: str, move_id: str, delay: int) -> dict:
    sim = world.copy()
    prop = sim.get(prop_id)
    prop.meters["tumbling"] += 1
    sim.facts["rescue"] = move_beats(PROPS[prop_id], delay, MOVES[move_id])
    if sim.facts["rescue"]:
        sim.get("hero").meters["hovering"] += 1
    propagate(sim, narrate=False)
    return {"alarm": sim.get("hero").memes["alarm"], "rescue": sim.facts["rescue"]}


def setup(world: World, hero: Entity, friend: Entity, prop: Prop, place: Entity) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"On a wind-stacked afternoon, {hero.id} and {friend.id} climbed up by {place.label} "
        f"to admire {prop.phrase}."
    )
    world.say(
        f"{hero.id} said, \"Look high, look wide, and look again!\" and {friend.id} said, "
        f"\"High and wide, high and wide!\""
    )


def wind_up(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"The wind kept whispering, \"Hurry now, hurry now,\" and the whole place felt as "
        f"wobbly as a spoon on a saddle."
    )
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1


def tumble_beat(world: World, prop_ent: Entity, prop: Prop) -> None:
    prop_ent.meters["tumbling"] += 1
    world.say(
        f"Then the {prop.label} gave a lurch, a wobble, and a tumble. "
        f"It slipped, it dipped, and it went to the edge."
    )


def warn(world: World, friend: Entity, hero: Entity, prop: Prop) -> None:
    friend.memes["worry"] += 1
    world.say(
        f'{friend.id} cried, "{hero.id}, hold fast! Hold fast!"'
    )
    world.say(
        f'{hero.id} answered, "Hold fast, hold fast? I am trying!"'
    )


def act_tumble(world: World, hero: Entity, friend: Entity, prop: Prop, move: Move, delay: int) -> None:
    predicted = predict(world, "bundle", move.id, delay)
    world.facts["predicted_alarm"] = predicted["alarm"]
    world.facts["rescue"] = move_beats(prop, delay, move)
    if world.facts["rescue"]:
        world.say(
            f'"{friend.id}," said {hero.id}, "if the bundle tumbles, then we hover."'
        )
    else:
        world.say(
            f'"{friend.id}," said {hero.id}, "if the bundle tumbles, then we run."'
        )


def rescue(world: World, hero: Entity, friend: Entity, move: Move, prop: Prop) -> None:
    hero.meters["hovering"] += 1
    friend.meters["hovering"] += 1
    prop_ent = world.get("bundle")
    prop_ent.meters["tumbling"] = 0.0
    world.say(
        f"{friend.label_word.capitalize()} came booming up the path and {move.text.replace('{prop}', prop.label)}."
    )
    world.say(
        f"The bundle stopped its tumble, and the children were laughing so hard they almost hovered themselves."
    )
    world.say(
        f'"We hovered! We hovered!" they kept saying, as if the words were balloons.'
    )


def lesson(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"For a moment nobody spoke, and then {friend.id} grinned and said, "
        f"\"A tall thing can tumble, and a small clever thing can hover.\""
    )
    world.say(
        f'{hero.id} nodded and said, "A tumble can scare us, but a hover can save us."'
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"In the end the wind kept on singing, but the bundle stayed put, and {hero.id} and "
        f"{friend.id} went home with their hats on straight and their eyes as bright as lanterns."
    )


def tell(params: "StoryParams") -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="helper"))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian, role="guardian"))
    prop_ent = world.add(Entity(id="bundle", type="thing", label=PROPS[params.prop].label))
    place = world.add(Entity(id="ridge", kind="place", type="place", label=PLACES[params.place].label))
    world.facts["prop"] = PROPS[params.prop]
    world.facts["place"] = PLACES[params.place]
    world.facts["move"] = MOVES[params.move]

    setup(world, hero, friend, PROPS[params.prop], place)
    world.para()
    wind_up(world, hero, friend)
    warn(world, friend, hero, PROPS[params.prop])
    act_tumble(world, hero, friend, PROPS[params.prop], MOVES[params.move], params.delay)
    world.para()
    tumble_beat(world, prop_ent, PROPS[params.prop])
    if move_beats(PROPS[params.prop], params.delay, MOVES[params.move]):
        rescue(world, guardian, friend, MOVES[params.move], PROPS[params.prop])
        lesson(world, hero, friend)
        world.para()
        ending(world, hero, friend)
        outcome = "contained"
    else:
        world.say(
            f"{guardian.label_word.capitalize()} came late, and the bundle rolled and rolled until the hill looked like a river of dust."
        )
        world.say(
            f"{hero.id} and {friend.id} chased after it, but the wind won the race."
        )
        outcome = "burned"
    world.facts["outcome"] = outcome
    return world


@dataclass
@dataclass
class StoryParams:
    place: str
    prop: str
    move: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    guardian: str
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


PLACES = {
    "hill": Entity(id="hill", kind="place", type="place", label="the hill"),
    "dock": Entity(id="dock", kind="place", type="place", label="the dock"),
    "roof": Entity(id="roof", kind="place", type="place", label="the roof"),
}

PROPS = {
    "balloon": Prop("balloon", "balloon", "a red balloon as big as a pumpkin", True, False, True),
    "hat": Prop("hat", "hat", "a shiny hat perched on a box", True, True, False),
    "lantern": Prop("lantern", "lantern", "a glass lantern on a crate", True, True, False),
}

MOVES = {
    "rope": Move("rope", "rope", 3, 4, "lashed a rope around the bundle and held it fast", "could not hold the bundle fast", "lashed a rope around the bundle and held it fast"),
    "net": Move("net", "net", 3, 3, "dropped a net over the bundle and pinned it down", "could not pin the bundle down", "dropped a net over the bundle and pinned it down"),
    "kite": Move("kite", "kite", 2, 2, "ran with a kite string and tugged the bundle back", "could not tug the bundle back", "ran with a kite string and tugged the bundle back"),
    "whistle": Move("whistle", "whistle", 1, 1, "blew a whistle and hoped for the best", "could not do much with a whistle", "blew a whistle and hoped for the best"),
}

SENSE_MIN = 2

GIRL_NAMES = ["Ada", "June", "Mina", "Ruby", "Nell", "Ivy"]
BOY_NAMES = ["Owen", "Basil", "Eli", "Poe", "Rex", "Toby"]
TRAITS = ["brave", "curious", "loud", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for prop_id, prop in PROPS.items():
            if not hazard_at_risk(prop):
                continue
            for move_id, move in MOVES.items():
                if move.sense >= SENSE_MIN and move_beats(prop, 0, move):
                    combos.append((place, prop_id, move_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a small child using the words "tumble" and "hover".',
        f"Tell a lively story where {f['hero'].id} sees {f['prop'].label} tumble and a grown-up helps the children hover it safely.",
        f'Write a dialogue-filled story with repetition, a tumble, and a hover ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prop = f["prop"]
    move = f["move"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {friend.id}, and their grown-up helper. They are the ones who watch the big bundle tumble."),
        ("What happened first?",
         f"The bundle began to tumble near the edge, and the children warned each other right away. The danger came from the bundle being fragile and the wind being strong."),
        ("What did the grown-up do?",
         f"The grown-up {move.qa_text.replace('{prop}', prop.label)}. That stopped the tumble and let the children hover in relief."),
    ]
    if f.get("outcome") == "contained":
        qa.append((
            "How did the children feel at the end?",
            f"They felt amazed and happy. They kept saying they hovered the bundle to safety, which is a tall-tale way of saying the rescue worked."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to tumble?",
         "To tumble means to tip, roll, or fall over in a sudden way."),
        ("What does hover mean?",
         "To hover means to stay up in the air or hold still over one place for a little while."),
        ("Why do people use repetition in stories?",
         "Repetition helps listeners remember the important words and makes the story feel lively."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)




def explain_rejection(prop: Prop) -> str:
    return f"(No story: {prop.label} needs a taller, windier rescue to make a real tumble-and-hover tale.)"


def explain_move(move_id: str) -> str:
    m = MOVES[move_id]
    return f"(Refusing move '{move_id}': it is too small-minded for the tall-tale rescue. Try a braver, smarter move.)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if move_beats(PROPS[params.prop], params.delay, MOVES[params.move]) else "burned"


ASP_RULES = r"""
hazard(P) :- prop(P), fragile(P).
sensible(M) :- move(M), sense(M, S), min_sense(N), S >= N.
valid(Pl, P, M) :- place(Pl), prop(P), move(M), hazard(P), sensible(M).

contained :- chosen_prop(P), chosen_move(M), chosen_delay(D), power(M, PW), prop_power(P, PP), PP + D =< PW.
outcome(contained) :- contained.
outcome(burned) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
        lines.append(asp.fact("prop_power", pid, 2 if p.fragile else 1))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_prop", params.prop), asp.fact("chosen_move", params.move), asp.fact("chosen_delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    smoke = [generate(CURATED[0]), generate(CURATED[1])]
    for s in smoke:
        if not s.story.strip():
            rc = 1
            print("MISMATCH: empty story in smoke test.")
    if asp_outcome(CURATED[0]) != outcome_of(CURATED[0]):
        rc = 1
        print("MISMATCH: ASP outcome differs.")
    else:
        print("OK: smoke generation and outcome parity passed.")
    return rc


@dataclass
class StoryParams:
    place: str
    prop: str
    move: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    guardian: str
    delay: int = 0
    seed: Optional[int] = None

CURATED = [
    StoryParams("hill", "balloon", "rope", "Mina", "girl", "Owen", "boy", "Captain June", 0),
    StoryParams("dock", "hat", "net", "Eli", "boy", "Ruby", "girl", "Uncle Sam", 0),
    StoryParams("roof", "lantern", "kite", "Ada", "girl", "Toby", "boy", "Grandpa", 1),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale story world about a tumble and a hover.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--guardian")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (["Ada", "June", "Mina", "Ruby", "Nell", "Ivy"] if gender == "girl" else ["Owen", "Basil", "Eli", "Poe", "Rex", "Toby"]) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.move and MOVES[args.move].sense < SENSE_MIN:
        raise StoryError(explain_move(args.move))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prop is None or c[1] == args.prop)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prop, move = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    hero = args.name or _pick_name(rng, gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    guardian = args.guardian or rng.choice(["Mom", "Dad", "Grandma", "Grandpa", "Aunt May"])
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(place, prop, move, hero, gender, friend, friend_gender, guardian, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero} and {p.friend}: {p.prop} on the {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
