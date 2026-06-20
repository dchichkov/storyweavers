#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sliver_humor_cautionary_repetition_bedtime_story.py
===================================================================================

A standalone story world for a small bedtime tale: a child notices a sliver of
moonlight, keeps wanting one more peek, and a calm parent turns the repeated
poking into a gentle, funny, sleep-friendly ending.

The world is built from a tiny simulation with typed entities, physical meters,
and emotional memes. The story is not a frozen paragraph: the world state moves
from bedtime setup, to repeated temptation, to a cautious turn, to a restful
resolution.

This world supports the shared Storyweavers contract:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- main
- --n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

It also includes:
- a Python reasonableness gate
- inline ASP_RULES twin
- asp_facts()
- verify parity between Python and ASP
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
class Room:
    id: str
    name: str
    quiet: bool
    dim: bool
    smell: str
    comforts: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Temptation:
    id: str
    noun: str
    phrase: str
    repetition: str
    risk: str
    safe_rule: str
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
class Comfort:
    id: str
    noun: str
    phrase: str
    glow: str
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
class Response:
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
        self.room = Room("room", "the bedroom", quiet=True, dim=True, smell="lavender", comforts=["blanket"])

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
        clone.room = copy.deepcopy(self.room)
        clone.paragraphs = [[]]
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


def _r_wakefulness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["awake"] < THRESHOLD:
            continue
        sig = ("awake", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fidgety"] += 1
        out.append("__awake__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    kid = world.facts.get("child")
    if not kid:
        return out
    if kid.memes["fidgety"] < THRESHOLD:
        return out
    sig = ("repeat", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["repeat"] += 1
    out.append("__repeat__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    kid = world.facts.get("child")
    if not kid:
        return out
    if kid.memes["settled"] < THRESHOLD:
        return out
    sig = ("settle", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.memes["quiet"] += 1
    out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("wakefulness", "social", _r_wakefulness),
                Rule("repeat", "social", _r_repeat),
                Rule("settle", "social", _r_settle)]


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


def reasonable_choice(temptation: Temptation, comfort: Comfort) -> bool:
    return temptation.id in {"moon_sliver", "blanket_tag"} and comfort.id in {"night_light", "storybook"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def bedtime_pressure(delay: int) -> int:
    return 1 + delay


def is_still_awake(response: Response, delay: int) -> bool:
    return response.power < bedtime_pressure(delay)


def _do_temptation(world: World, child: Entity, temp: Temptation, narrate: bool = True) -> None:
    child.meters["awake"] += 1
    child.memes["curious"] += 1
    child.memes["fidgety"] += 1
    propagate(world, narrate=narrate)


def predict_bedtime(world: World, temp_id: str) -> dict:
    sim = world.copy()
    _do_temptation(sim, sim.get("child"), TEMPTATIONS[temp_id], narrate=False)
    child = sim.get("child")
    return {"repeat": child.memes["repeat"], "quiet": sim.room.memes["quiet"]}


def bedtime_setup(world: World, child: Entity, parent: Entity, room: Room, temp: Temptation) -> None:
    child.memes["love"] += 1
    child.memes["cozy"] += 1
    world.say(
        f"At bedtime, {child.id} snuggled under the blanket in {room.name}, where the air was soft and sleepy."
    )
    world.say(
        f"A tiny sliver of moonlight lay across the floor like a silver ribbon, and {child.id} noticed it at once."
    )


def tempt(world: World, child: Entity, temp: Temptation) -> None:
    world.say(
        f'{child.id} pointed at the sliver and whispered, "{temp.repetition}"'
    )
    world.say(
        f'It sounded funny, because {temp.phrase} was only a little thing, but {child.id} wanted it anyway.'
    )


def warn(world: World, parent: Entity, child: Entity, temp: Temptation, comfort: Comfort) -> None:
    pred = predict_bedtime(world, temp.id)
    child.memes["warning"] += 1
    world.facts["predicted_repeat"] = pred["repeat"]
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "{temp.safe_rule}, {child.id}. We do not chase slivers at bedtime."'
    )
    if pred["repeat"] >= THRESHOLD:
        world.say(
            f'"If we start chasing it, we might be up and up and up," {parent.label_word} added, "and that would make morning feel far away."'
        )


def repeat_trip(world: World, child: Entity, temp: Temptation) -> None:
    child.memes["repeat"] += 1
    world.say(
        f'{child.id} tried once, then twice, then a tiny third time, tiptoeing after the moon sliver.'
    )
    world.say(
        f'Each time, the sliver stayed just ahead, as if it were a shy cat with a very serious schedule.'
    )


def soothe(world: World, parent: Entity, child: Entity, comfort: Comfort) -> None:
    child.memes["settled"] += 1
    child.memes["curious"] = 0
    child.memes["fidgety"] = 0
    world.say(
        f'Then {parent.label_word} opened the little lamp and turned on {comfort.phrase}, which {comfort.glow}.'
    )
    world.say(
        f'"The moon can keep its sliver," {parent.label_word} said. "You can keep your blanket and your dreams."'
    )


def bedtime_end(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f'{child.id} tucked {child.pronoun("possessive")} chin into the blanket, yawned a huge yawn, and the silly sliver of moonlight became nothing more than a quiet stripe on the carpet.'
    )
    world.say(
        f'{parent.label_word.capitalize()} kissed {child.pronoun("possessive")} forehead, and the room grew still, small, and safe.'
    )


def tell(temp: Temptation, comfort: Comfort, response: Response,
         child_name: str = "Milo", child_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    world.add(Entity(id="sliver", type="thing", label="sliver of moonlight"))
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["temptation"] = temp
    world.facts["comfort"] = comfort
    world.facts["response"] = response
    world.facts["delay"] = delay

    bedtime_setup(world, child, parent, world.room, temp)
    world.para()
    tempt(world, child, temp)
    warn(world, parent, child, temp, comfort)

    if not is_still_awake(response, delay):
        repeat_trip(world, child, temp)
        world.para()
        soothe(world, parent, child, comfort)
        bedtime_end(world, child, parent, comfort)
        outcome = "settled"
    else:
        child.memes["defiance"] += 1
        world.say(f'{child.id} tried to keep going, but the bedtime feeling was stronger than the game.')
        world.para()
        world.say(f'{parent.label_word.capitalize()} had to carry the story to its ending and tuck {child.id} in firmly.')
        bedtime_end(world, child, parent, comfort)
        outcome = "too_late"

    world.facts["outcome"] = outcome
    world.facts["promised"] = child.memes["settled"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    temp = f["temptation"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that repeats the phrase "{temp.repetition}" and ends sleepy and safe.',
        f"Tell a gentle, cautionary bedtime story where {child.id} keeps noticing a sliver and a grown-up helps {child.pronoun('object')} stop chasing it.",
        f'Write a cozy story with humor and repetition about a sliver of moonlight, a bedtime warning, and a calm ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    temp = f["temptation"]
    comfort = f["comfort"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word.capitalize()}, who are trying to get ready for sleep."),
        ("What did {0} keep noticing?".format(child.id),
         f"{child.id} kept noticing a sliver of moonlight. It looked small and funny, so it kept pulling {child.pronoun('object')} back to the window."),
        ("Why did the parent warn {0}?".format(child.id),
         f"{parent.label_word.capitalize()} warned {child.id} because chasing the sliver would keep {child.id} awake. Bedtime needs stillness, not more and more peeking."),
    ]
    if f["outcome"] == "settled":
        qa.append((
            f"What helped {child.id} calm down?",
            f"{parent.label_word.capitalize()} turned on {comfort.phrase} and reminded {child.id} that the moon could keep its sliver. That gave {child.id} something cozy to look at instead of wandering around."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {child.id} tucked in, sleepy and safe, while the tiny sliver of moonlight stayed on the floor. The room became quiet again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["temptation"].tags) | set(world.facts["comfort"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  room     (room   ) quiet={world.room.quiet} dim={world.room.dim} smell={world.room.smell}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


TEMPTATIONS = {
    "moon_sliver": Temptation(
        "moon_sliver",
        "sliver",
        "a sliver of moonlight",
        "just a sliver, just a sliver",
        "stay in bed",
        "keep the blanket over your shoulders",
        tags={"sliver", "moonlight", "bedtime"},
    ),
    "curtain_gap": Temptation(
        "curtain_gap",
        "sliver",
        "a sliver of light between the curtains",
        "only peeking once, only peeking once",
        "stay in bed",
        "keep the blanket over your shoulders",
        tags={"sliver", "light", "bedtime"},
    ),
}

COMFORTS = {
    "night_light": Comfort(
        "night_light",
        "lamp",
        "a little night-light",
        "glowed like a tiny breakfast sun",
        tags={"night_light", "light", "bedtime"},
    ),
    "storybook": Comfort(
        "storybook",
        "book",
        "a bedtime storybook",
        "opened like a soft little door",
        tags={"storybook", "bedtime"},
    ),
}

RESPONSES = {
    "gentle": Response(
        "gentle",
        3,
        3,
        "turned on the night-light and read one calm page until the room felt sleepy",
        "turned on the night-light, but the sliver kept stealing every thought",
        "turned on the night-light and made bedtime calm again",
        tags={"night_light", "bedtime"},
    ),
    "story": Response(
        "story",
        3,
        2,
        "opened the storybook and told one silly page after another until the eyes grew heavy",
        "opened the storybook, but the room was still too wiggly to settle",
        "opened the storybook and helped the eyes grow heavy",
        tags={"storybook", "bedtime"},
    ),
    "too_tired": Response(
        "too_tired",
        1,
        1,
        "yawned and tried to wing it with a shrug",
        "yawned, but the bedtime battle was already too lively",
        "yawned and tried to wing it",
        tags={"bedtime"},
    ),
}

GIRL_NAMES = ["Luna", "Nina", "Mira", "June", "Pia", "Ada"]
BOY_NAMES = ["Milo", "Theo", "Noah", "Finn", "Owen", "Ezra"]
TRAITS = ["curious", "silly", "gentle", "sleepy", "thoughtful"]

KNOWLEDGE = {
    "sliver": [("What is a sliver?",
                "A sliver is a very tiny thin piece of something. It can look small and shiny, like a little strip of light.")],
    "moonlight": [("Where does moonlight come from?",
                   "Moonlight is light from the sun that bounces off the moon and reaches Earth at night.")],
    "night_light": [("What is a night-light?",
                     "A night-light is a small lamp that gives a soft glow in the dark. It helps a room feel less scary at bedtime.")],
    "storybook": [("Why can a storybook help at bedtime?",
                   "A storybook gives your mind a calm thing to follow, so it is easier to settle down and get sleepy.")],
    "bedtime": [("Why do people need bedtime?",
                 "Bedtime gives the body and brain time to rest. Sleep helps people feel ready for a new day.")],
}
KNOWLEDGE_ORDER = ["sliver", "moonlight", "night_light", "storybook", "bedtime"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for temp in TEMPTATIONS:
        for resp in RESPONSES.values():
            if resp.sense >= SENSE_MIN:
                combos.append((temp, resp.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    temptation: str
    comfort: str
    response: str
    child: str
    child_gender: str
    parent: str
    trait: str
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


def explain_rejection(temptation: Temptation, response: Response) -> str:
    return f"(No story: response '{response.id}' is too weak for a calm bedtime ending.)"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, R) :- temptation(T), response(R), sensible(R).
outcome(settled) :- chosen_response(R), chosen_delay(D), pressure(P), power(R, X), X >= P.
outcome(too_late) :- chosen_response(R), chosen_delay(D), pressure(P), power(R, X), X < P.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_delay", params.delay),
        asp.fact("pressure", bedtime_pressure(params.delay)),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    cases = [StoryParams("moon_sliver", "night_light", "gentle", "Milo", "boy", "mother", "curious", delay=d) for d in range(3)]
    bad = sum(1 for p in cases if asp_outcome(p) != ("too_late" if is_still_awake(RESPONSES[p.response], p.delay) else "settled"))
    if bad == 0:
        print("OK: outcome model matches Python logic.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome differences.")
    try:
        _ = generate(resolve_params(argparse.Namespace(temptation=None, comfort=None, response=None, child=None, child_gender=None, parent=None, trait=None, delay=None), random.Random(1)))  # type: ignore[arg-type]
    except Exception:
        pass
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
    _ = sample.story
    print("OK: smoke test story generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a sliver, humor, caution, and repetition.")
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_rejection(TEMPTATIONS["moon_sliver"], RESPONSES[args.response]))
    combos = [c for c in valid_combos() if (args.temptation is None or c[0] == args.temptation) and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    temptation, response = rng.choice(sorted(combos))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(temptation, comfort, response, child, gender, parent, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(TEMPTATIONS[params.temptation], COMFORTS[params.comfort], RESPONSES[params.response], params.child, params.child_gender, params.parent, params.trait, params.delay)
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(r.id for r in sensible_responses())}\n")
        for t, r in asp_valid_combos():
            print(f"  {t:12} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("moon_sliver", "night_light", "gentle", "Milo", "boy", "mother", "curious", 0),
            StoryParams("curtain_gap", "storybook", "story", "Luna", "girl", "father", "silly", 1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
