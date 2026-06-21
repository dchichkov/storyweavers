#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hoo_tavern_realize_surprise_fable.py
=====================================================================

A tiny standalone storyworld in a fable style: an evening in a tavern, a
surprising "hoo" from the rafters, and a child who comes to realize what the
sound means. The world is intentionally small and state-driven: the same few
entities accumulate physical meters and emotional memes, and the prose is
rendered from that evolving state rather than from a frozen template.

Theme note:
- Seed words: hoo, tavern, realize
- Feature: Surprise
- Style: Fable

This script supports:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

It imports storyworlds/results.py eagerly and storyworlds/asp.py lazily inside
ASP helper functions.
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
MORAL_MIN = 2.0


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
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    id: str
    place: str
    smell: str
    sound: str
    mood: str
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
class Surprise:
    id: str
    source: str
    sound: str
    revealed: str
    effect: str
    lesson: str
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
    setting: str
    surprise: str
    response: str
    child_name: str
    child_type: str
    elder_name: str
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").meters["startle"] >= THRESHOLD and ("fear",) not in world.fired:
        world.fired.add(("fear",))
        world.get("child").memes["fear"] += 1
        out.append("__startle__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").meters["understanding"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        world.get("child").memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("relief", _r_relief)]


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


def reasonableness_gate(setting: Setting, surprise: Surprise, response: Response) -> bool:
    return setting.id == "tavern" and surprise.source == "owl" and response.sense >= MORAL_MIN


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= MORAL_MIN]


def incident_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= incident_severity(delay)


def predict(world: World, surprise: Surprise) -> dict:
    sim = world.copy()
    sim.get("child").meters["startle"] += 1
    sim.get("child").meters["understanding"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "relief": sim.get("child").memes["relief"],
    }


def setup(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    elder.memes["care"] += 1
    world.say(
        f"At dusk, {child.id} sat in the {setting.place}, where the air smelled of "
        f"{setting.smell} and the room hummed with {setting.sound}."
    )
    world.say(
        f"{elder.id} poured warm soup and told {child.id} to listen well, for the "
        f"{setting.place} had old beams and old stories."
    )


def desire(world: World, child: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} looked up at the rafters and thought the night would be only "
        f"quiet crumbs, firelight, and songs."
    )


def surprise_beat(world: World, surprise: Surprise, child: Entity) -> None:
    child.meters["startle"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"Then came a soft, sudden {surprise.sound} from above. {child.id} froze "
        f"and stared at the dark beams."
    )
    world.say(
        f"For a breath, {child.id} thought the sound meant trouble. That was the "
        f"surprise of the hour."
    )
    propagate(world, narrate=True)


def realize_beat(world: World, child: Entity, elder: Entity, surprise: Surprise) -> None:
    child.meters["understanding"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} listened harder and then {child.id} began to realize: the "
        f"sound was not a ghost at all."
    )
    world.say(
        f"It was {surprise.revealed}, and {elder.id} had already guessed it from the "
        f"way the rafters rustled."
    )
    propagate(world, narrate=True)


def rescue(world: World, elder: Entity, response: Response, surprise: Surprise) -> None:
    body = response.text.replace("{surprise}", surprise.source)
    elder.memes["calm"] += 1
    world.say(f"{elder.id} smiled, stood up, and {body}.")
    world.say(
        f"The {surprise.source} settled again, and the room's worry grew smaller than "
        f"a spoon."
    )


def rescue_fail(world: World, elder: Entity, response: Response, surprise: Surprise) -> None:
    elder.memes["alarm"] += 1
    body = response.fail.replace("{surprise}", surprise.source)
    world.say(f"{elder.id} tried, but {body}.")
    world.say(
        f"The old tavern shook with more noise, and everyone had to step back until "
        f"the moment passed."
    )


def lesson(world: World, child: Entity, elder: Entity, surprise: Surprise) -> None:
    child.memes["lesson"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"After that, {elder.id} told a fable-like truth: not every sudden sound is "
        f"bad, and wise eyes should look before they jump."
    )
    world.say(
        f"{child.id} nodded and remembered the lesson: if a thing surprises you, "
        f"pause, look, and realize what it really is."
    )
    world.say(
        f"And so the {surprise.lesson} stayed with {child.id} long after the cups "
        f"were cleared."
    )


def ending(world: World, child: Entity, elder: Entity, surprise: Surprise) -> None:
    child.memes["peace"] += 1
    elder.memes["peace"] += 1
    world.say(
        f"At last, {child.id} laughed softly and watched the little owl go quiet in "
        f"the rafters, while the tavern lanterns glowed like patient stars."
    )
    world.say(
        f"Before sleep, {child.id} could still hear a gentle hoo in memory, but now "
        f"it sounded friendly."
    )


def tell(setting: Setting, surprise: Surprise, response: Response,
         child_name: str = "Pip", child_type: str = "boy",
         elder_name: str = "Mara", elder_type: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    owl = world.add(Entity(id="owl", kind="character", type="owl", role="surprise",
                           label="the owl"))

    world.facts.update(setting=setting, surprise=surprise, response=response,
                       child=child, elder=elder, owl=owl)

    setup(world, child, elder, setting)
    world.para()
    desire(world, child)
    surprise_beat(world, surprise, child)
    world.para()
    realize_beat(world, child, elder, surprise)
    if is_contained(response, delay=0):
        rescue(world, elder, response, surprise)
        lesson(world, child, elder, surprise)
        world.para()
        ending(world, child, elder, surprise)
        outcome = "calm"
    else:
        rescue_fail(world, elder, response, surprise)
        lesson(world, child, elder, surprise)
        world.para()
        ending(world, child, elder, surprise)
        outcome = "noisy"
    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "tavern": Setting(
        id="tavern",
        place="tavern",
        smell="warm bread and wood smoke",
        sound="murmuring voices and clinking cups",
        mood="cozy",
    ),
    "inn": Setting(
        id="inn",
        place="inn",
        smell="stew and fresh straw",
        sound="low laughter and ticking mugs",
        mood="gentle",
    ),
    "hall": Setting(
        id="hall",
        place="hall",
        smell="apple cider and old beams",
        sound="boots, spoons, and a fiddle",
        mood="bright",
    ),
}

SURPRISES = {
    "owl": Surprise(
        id="owl",
        source="owl",
        sound="hoo",
        revealed="a little owl with bright gold eyes",
        effect="a flap of feathers and a surprise",
        lesson="owl in the rafters",
        tags={"owl", "hoo", "surprise"},
    ),
    "cat": Surprise(
        id="cat",
        source="cat",
        sound="mrrp",
        revealed="a sleepy cat on the beam",
        effect="a tiny pounce of surprise",
        lesson="cat on the beam",
        tags={"cat", "surprise"},
    ),
    "loose_sign": Surprise(
        id="loose_sign",
        source="sign",
        sound="clack",
        revealed="a hanging sign swinging in the draft",
        effect="a surprising clack from above",
        lesson="sign in the draft",
        tags={"sign", "surprise"},
    ),
}

RESPONSES = {
    "calm_lookup": Response(
        id="calm_lookup",
        sense=3,
        power=3,
        text="looked up and checked the rafters until the truth was clear",
        fail="looked up, but the noise kept hiding in the dark beams",
        qa_text="looked up and checked the rafters until the truth was clear",
        tags={"look", "owl"},
    ),
    "lamp_raise": Response(
        id="lamp_raise",
        sense=2,
        power=2,
        text="held the lamp high so everyone could see the little shape above",
        fail="held the lamp high, but the beams were still too dark",
        qa_text="held the lamp high so everyone could see the little shape above",
        tags={"light", "owl"},
    ),
    "shoo": Response(
        id="shoo",
        sense=1,
        power=1,
        text="shooed at the sound and made a bigger fuss",
        fail="shooed at the sound, but that only made a bigger fuss",
        qa_text="shooed at the sound and made a bigger fuss",
        tags={"noise"},
    ),
}

CHILD_NAMES = ["Pip", "Nia", "Milo", "Ada", "Ben", "Tess", "Oli", "Lena"]
ELDER_NAMES = ["Mara", "Hugo", "Iris", "Jeb", "Rosa", "Otto"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for s in SETTINGS:
        for sp in SURPRISES:
            for r in sensible_responses():
                if reasonableness_gate(SETTINGS[s], SURPRISES[sp], r):
                    combos.append((s, sp))
    return combos


def explain_rejection(setting: Setting, surprise: Surprise) -> str:
    if setting.id != "tavern":
        return "(No story: this fable needs a tavern, with beams and lantern light."
    if surprise.source != "owl":
        return "(No story: the surprise should be an owl for the seed word hoo."
    return "(No story: no sensible response is available."


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return (
        f"(Refusing response '{rid}': it is too plain or noisy for a gentle fable "
        f"(sense={r.sense} < {MORAL_MIN}). Try calm_lookup or lamp_raise.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    surprise: Surprise = f["surprise"]
    return [
        f"Write a short fable set in a {setting.place} that includes the word '{surprise.sound}'.",
        f"Tell a child-friendly surprise story in a {setting.place} where someone hears hoo and realizes what it means.",
        f"Write a gentle fable about an owl in a tavern, and let the child realize the truth before the ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    surprise: Surprise = f["surprise"]
    setting: Setting = f["setting"]
    resp: Response = f["response"]
    return [
        ("Where does the story take place?",
         f"It takes place in a {setting.place}. The warm room and its beams make the surprise feel like part of a fable."),
        (f"What sound does the child hear?",
         f"{child.id} hears '{surprise.sound}'. At first it sounds mysterious, but the story shows it is only the owl making a call."),
        (f"What does {child.id} realize?",
         f"{child.id} realizes that the sound comes from {surprise.revealed}. That matters because the surprise turns into understanding instead of fear."),
        (f"How did {elder.id} help?",
         f"{elder.id} helped by using {resp.qa_text}. That calm response gave {child.id} time to look carefully and realize the truth."),
        ("How did the story end?",
         f"It ended peacefully, with the tavern quiet again and the owl safe in the rafters. The surprise became a lesson instead of a worry."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tavern?",
         "A tavern is a place where people gather to eat, drink, and talk together. In old stories, taverns often feel warm and busy."),
        ("What does hoo sound like?",
         "Hoo is a soft owl call. It can sound mysterious at night, especially when it comes from above."),
        ("Why can a surprise make someone freeze for a moment?",
         "A surprise can make the body pause because the mind is trying to understand what just happened. A calm look helps turn surprise into knowledge."),
        ("What does it mean to realize something?",
         "To realize something means to understand it clearly after not knowing it before. Often, you notice a clue and the truth suddenly makes sense."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="tavern", surprise="owl", response="calm_lookup",
                child_name="Pip", child_type="boy", elder_name="Mara", elder_type="woman"),
    StoryParams(setting="tavern", surprise="owl", response="lamp_raise",
                child_name="Nia", child_type="girl", elder_name="Hugo", elder_type="man"),
]


ASP_RULES = r"""
valid(S, P) :- setting(S), surprise(P), is_reasonable(S, P).
is_reasonable("tavern", "owl").
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in SURPRISES:
        lines.append(asp.fact("surprise", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", int(MORAL_MIN)))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in asp:", sorted(a - b))
        print("  only in py :", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tavern fable of hoo and realize.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--elder")
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
    if args.response and RESPONSES[args.response].sense < MORAL_MIN:
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(list(SETTINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    if not reasonableness_gate(SETTINGS[setting], SURPRISES[surprise], RESPONSES[response]):
        raise StoryError("(No valid combination matches the given options.)")
    child_name = args.child or rng.choice(CHILD_NAMES)
    elder_name = args.elder or rng.choice([n for n in ELDER_NAMES if n != child_name])
    child_type = rng.choice(["boy", "girl"])
    elder_type = "woman" if child_type == "boy" else "man"
    return StoryParams(setting=setting, surprise=surprise, response=response,
                       child_name=child_name, child_type=child_type,
                       elder_name=elder_name, elder_type=elder_type)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("invalid setting")
    if params.surprise not in SURPRISES:
        raise StoryError("invalid surprise")
    if params.response not in RESPONSES:
        raise StoryError("invalid response")
    world = tell(SETTINGS[params.setting], SURPRISES[params.surprise], RESPONSES[params.response],
                 params.child_name, params.child_type, params.elder_name, params.elder_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for s, p in combos:
            print(f"  {s} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.child_name} in the {p.setting} ({p.surprise}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
