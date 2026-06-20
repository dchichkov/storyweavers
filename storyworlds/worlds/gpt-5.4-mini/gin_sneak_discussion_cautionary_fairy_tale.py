#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gin_sneak_discussion_cautionary_fairy_tale.py
=============================================================================

A small, self-contained fairy-tale storyworld built from the seed words
"gin", "sneak", and "discussion".

Premise
-------
A child in a fairy-tale household is tempted to sneak a forbidden bottle of
gin from a cellar or cabinet, but a cautious friend or elder notices, a calm
discussion happens, and the child learns a safe replacement choice.

This is a cautionary fairy-tale world:
- there is a forbidden object that can make trouble,
- there is a moment of sneaking,
- there is a discussion that redirects the choice,
- the ending proves what changed.

The script follows the Storyweavers contract:
- typed entities with meters and memes,
- a forward-chained causal model,
- Python reasonableness gates and an inline ASP twin,
- three QA sets derived from world state,
- standard CLI modes: --all, -n, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp.
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
        female = {"girl", "mother", "mom", "woman", "queen", "witch"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen",
                "king": "king", "witch": "witch"}.get(self.type, self.type)



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
    mood: str
    detail: str

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
class Forbidden:
    id: str
    label: str
    phrase: str
    where: str
    danger: str
    makes_trouble: bool = True

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
class SafeChoice:
    id: str
    label: str
    phrase: str
    glow: str

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


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["trouble"] < THRESHOLD:
            continue
        sig = ("trouble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            if kid.role in {"child", "friend"}:
                kid.memes["fear"] += 1
        out.append("__trouble__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["understanding"] < THRESHOLD:
            continue
        sig = ("relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("trouble", "physical", _r_trouble),
    Rule("relief", "social", _r_relief),
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


def child_names() -> list[str]:
    return ["Mina", "Lina", "Rosie", "Elsa", "Nell", "Ivy", "Tara", "Mira"]


def helper_names() -> list[str]:
    return ["Bram", "Dora", "Alin", "Wren", "Hazel", "Gwen", "Cedric"]


SETTINGS = {
    "forest": Setting("forest", "an old forest cottage", "golden and hush-soft",
                      "ivy climbed the door and moonlight pooled on the stones"),
    "castle": Setting("castle", "a little castle hall", "bright and echoing",
                      "the tapestries swayed like sleeping birds"),
    "village": Setting("village", "a baker's cottage", "warm and chimney-bright",
                       "the windows shone like tiny lanterns"),
}

FORBIDDEN = {
    "gin": Forbidden("gin", "gin", "a bottle of gin", "in the pantry",
                     "it is a grown-up drink and can make a child dizzy"),
}

SAFE = {
    "tea": SafeChoice("tea", "herbal tea", "a cup of herbal tea", "steamed softly"),
    "juice": SafeChoice("juice", "sweet berry juice", "a cup of berry juice", "shone ruby-red"),
    "water": SafeChoice("water", "cool well water", "a cup of well water", "glittered clear"),
}

RESPONSES = {
    "safekeep": Response("safekeep", 3, 3,
                         "set the bottle high on the shelf and shut the pantry door",
                         "tried to hide the bottle again, but the trouble had already begun",
                         "set the bottle aside and shut the pantry door"),
    "call_help": Response("call_help", 3, 4,
                          "called for a grown-up and told the truth at once",
                          "called too late, after the child had already taken a sip",
                          "called for a grown-up right away"),
    "discussion": Response("discussion", 4, 2,
                           "sat down for a calm discussion, and the child agreed to stop",
                           "tried to talk, but the child had already run off with the bottle",
                           "held a calm discussion and agreed on a safer choice"),
}

TRAITS = ["cautious", "kind", "careful", "gentle", "thoughtful", "brave"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    forbidden: str
    response: str
    safe_choice: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    trait: str
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


def unsafe_combo(forbidden: Forbidden) -> bool:
    return forbidden.makes_trouble


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid, fb in FORBIDDEN.items():
            if unsafe_combo(fb):
                combos.append((sid, fid))
    return combos


def reasonableness_gate(forbidden: Forbidden, response: Response) -> bool:
    return forbidden.makes_trouble and response.sense >= 3


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def outcome_of(params: StoryParams) -> str:
    if params.response == "discussion":
        return "averted"
    if params.response == "safekeep":
        return "contained"
    return "contained"


def predict_trouble(world: World, child_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.meters["trouble"] += 1
    propagate(sim, narrate=False)
    return {"trouble": child.meters["trouble"] >= THRESHOLD}


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Once in {setting.place}, {child.id} was a little {child.type} with "
        f"{child.pronoun('possessive')} heart full of wonder. {setting.detail}."
    )
    world.say(
        f"{helper.id} came near like a friend from a song, and the two of them "
        f"shared a quiet afternoon."
    )


def tempt(world: World, child: Entity, forbidden: Forbidden) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But in the pantry stood {forbidden.phrase}. {child.id} looked at it and "
        f"wondered if a tiny taste would feel clever."
    )
    world.say(
        f"{child.id} wanted to sneak inside and take the bottle, just to see "
        f"what secrets it held."
    )


def warn(world: World, helper: Entity, child: Entity, forbidden: Forbidden) -> None:
    pred = predict_trouble(world, child.id)
    helper.memes["care"] += 1
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{helper.id} noticed and shook {helper.pronoun("possessive")} head. '
        f'"That is not for children," {helper.id} said. "A sip could make you '
        f"dizzy and unsteady."
    )


def sneak(world: World, child: Entity, forbidden: Forbidden) -> None:
    child.memes["defiance"] += 1
    child.meters["trouble"] += 1
    world.say(
        f'"I can be quick," {child.id} whispered, and tried to sneak past the '
        f"door to the pantry."
    )


def discuss(world: World, helper: Entity, child: Entity, response: Response) -> None:
    child.memes["understanding"] += 1
    world.say(
        f"Then {helper.id} sat beside {child.id} and began a calm discussion. "
        f'Together they chose to be wise instead of hasty, and {response.qa_text}.'
    )


def resolve(world: World, child: Entity, helper: Entity, safe_choice: SafeChoice) -> None:
    child.memes["joy"] += 1
    child.meters["trouble"] = 0.0
    world.say(
        f"{child.id} nodded and chose {safe_choice.phrase} instead. "
        f"{safe_choice.glow.capitalize()}, and the room felt safe again."
    )
    world.say(
        f"By the hearth, {child.id} sipped the {safe_choice.label} while "
        f"{helper.id} smiled, and the bottle of gin stayed where it belonged."
    )


def lesson(world: World, child: Entity, helper: Entity) -> None:
    child.memes["lesson"] += 1
    helper.memes["relief"] += 1
    world.say(
        "From then on, they remembered that some shiny things are meant for "
        "grown-ups, and a good discussion can save the day."
    )


def tell(setting: Setting, forbidden: Forbidden, response: Response, safe_choice: SafeChoice,
         child_name: str = "Mina", child_type: str = "girl",
         helper_name: str = "Dora", helper_type: str = "woman",
         trait: str = "cautious") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type,
                             role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type,
                              role="helper", traits=["kind", "steady"]))
    world.add(Entity(id="gin", type="thing", label="gin bottle"))
    introduce(world, child, helper, setting)
    world.para()
    tempt(world, child, forbidden)
    warn(world, helper, child, forbidden)
    sneak(world, child, forbidden)
    world.para()
    discuss(world, helper, child, response)
    resolve(world, child, helper, safe_choice)
    lesson(world, child, helper)
    world.facts.update(child=child, helper=helper, setting=setting,
                       forbidden=forbidden, response=response, safe_choice=safe_choice,
                       outcome=outcome_of(StoryParams(setting.id, forbidden.id, response.id,
                                                       safe_choice.id, child_name, child_type,
                                                       helper_name, helper_type, trait)))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a cautionary fairy tale that includes the words "gin", "sneak", and "discussion".',
        f"Tell a small fairy tale where {f['child'].id} tries to sneak toward gin, "
        f"but a kind helper turns it into a discussion and a safer ending.",
        "Write a child-facing cautionary story about a forbidden bottle, a brief "
        "sneak, and a calm discussion that helps the child choose wisely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, forbidden, safe_choice = f["child"], f["helper"], f["forbidden"], f["safe_choice"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who spend a fairy-tale afternoon together."),
        ("What did the child want to do?",
         f"{child.id} wanted to sneak to the pantry and take the bottle of gin. "
         f"{helper.id} stopped that plan before it could turn foolish."),
        ("What changed the ending?",
         f"A calm discussion changed the ending. The child listened, chose {safe_choice.label}, "
         f"and left the gin bottle untouched."),
    ]
    if f.get("outcome") == "averted":
        qa.append((
            "How did they solve the problem?",
            f"They solved it with a discussion and a safer drink. That let the child "
            f"feel heard without touching the gin."
        ))
    else:
        qa.append((
            "How did the helper keep everyone safe?",
            f"The helper called the child back, spoke kindly, and made sure the gin "
            f"stayed closed away in the pantry. The calm talk was the safer choice."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is gin?",
         "Gin is an alcoholic drink for grown-ups. Children should never taste it."),
        ("What does sneak mean?",
         "To sneak means to move quietly so other people do not notice right away. "
         "It is often used when someone is trying to do something secretly."),
        ("What is a discussion?",
         "A discussion is a calm talk where people share ideas and listen to each other. "
         "Good discussions can help solve problems without fighting."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "gin", "discussion", "tea", "Mina", "girl", "Dora", "woman", "cautious"),
    StoryParams("castle", "gin", "safekeep", "juice", "Lina", "girl", "Wren", "man", "kind"),
    StoryParams("village", "gin", "call_help", "water", "Rosie", "girl", "Hazel", "woman", "thoughtful"),
]


def explain_rejection(forbidden: Forbidden, response: Response) -> str:
    if not reasonableness_gate(forbidden, response):
        return "(No story: this choice is not cautious enough for a fairy-tale warning.)"
    return "(No story: the combination does not fit the cautionary pattern.)"


def valid_combo_world(setting_id: str, forbidden_id: str) -> bool:
    return setting_id in SETTINGS and forbidden_id in FORBIDDEN and FORBIDDEN[forbidden_id].makes_trouble


def valid_combos_all() -> list[tuple[str, str]]:
    return [(sid, fid) for sid in SETTINGS for fid in FORBIDDEN if valid_combo_world(sid, fid)]


ASP_RULES = r"""
valid(S, F) :- setting(S), forbidden(F), makes_trouble(F).
sensible(R) :- response(R), sense(R, X), sense_min(M), X >= M.
outcome(averted) :- chosen_response("discussion").
outcome(contained) :- chosen_response("safekeep").
outcome(contained) :- chosen_response("call_help").
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, f in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if f.makes_trouble:
            lines.append(asp.fact("makes_trouble", fid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen_response", params.response)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos_all())
    if cset == pset:
        print(f"OK: gate matches valid_combos_all() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    params = CURATED[0]
    try:
        sample = generate(params)
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if asp_outcome(params) != outcome_of(params):
        rc = 1
        print("MISMATCH in outcome model.")
    else:
        print("OK: outcome model matches.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary fairy-tale storyworld about gin, sneak, and discussion."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--safe-choice", choices=SAFE)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("(Unknown response.)")
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    if RESPONSES[response].sense < 3:
        raise StoryError("(No story: the chosen response is too careless.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    forbidden = "gin"
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    child = args.child or rng.choice(child_names())
    helper = args.helper or rng.choice(helper_names())
    safe_choice = args.safe_choice or rng.choice(list(SAFE))
    trait = args.trait or rng.choice(TRAITS)
    if not valid_combo_world(setting, forbidden):
        raise StoryError("(No story: the setting does not fit the cautionary pattern.)")
    return StoryParams(setting, forbidden, response, safe_choice, child, child_type, helper, helper_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FORBIDDEN[params.forbidden],
                 RESPONSES[params.response], SAFE[params.safe_choice],
                 params.child, params.child_type, params.helper, params.helper_type,
                 params.trait)
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for setting, forbidden in asp_valid_combos():
            print(f"  {setting:8} {forbidden}")
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
            header = f"### {p.child}: {p.setting}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
