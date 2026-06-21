#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/invincible_scribble_clank_cautionary_ghost_story.py
===================================================================================

A tiny cautionary ghost-story world built from the seed words
"invincible", "scribble", and "clank".

Premise:
- A child sneaks into a quiet old room to "prove" they are invincible.
- A scribble on an old paper opens a risky ghostly game.
- A clank in the dark reveals the danger and brings help.
- The ending teaches caution: some dares are not brave.

The world is intentionally small, state-driven, and child-facing. It supports
ordinary text output, JSON, QA sets, trace, and a tiny ASP twin for parity
checks.
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mood:
    id: str
    place: str
    dark_spot: str
    title: str
    ending_image: str
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
class Forbidden:
    id: str
    label: str
    phrase: str
    warning: str
    makes_ghosts: bool = True
    sense: int = 3
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
class Target:
    id: str
    label: str
    phrase: str
    risky: bool = True
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
    mood: str
    forbidden: str
    target: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    delay: int = 0
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
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
    for e in list(world.entities.values()):
        if e.meters["ghostly"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            for kid in [x for x in world.entities.values() if x.role in {"hero", "helper"}]:
                kid.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clank_heard") and ("warning",) not in world.fired:
        world.fired.add(("warning",))
        out.append("The clank sounded like a warning in the dark.")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("warning", "social", _r_warning)]


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


MOODS = {
    "hall": Mood(
        id="hall",
        place="the old hall",
        dark_spot="the shadow under the staircase",
        title="an old hall",
        ending_image="the lantern glow and the chalk dust on the floor",
    ),
    "attic": Mood(
        id="attic",
        place="the attic",
        dark_spot="the corner behind the trunk",
        title="a dusty attic",
        ending_image="the window light and the quiet trunk",
    ),
}

FORBIDDEN = {
    "scrawl": Forbidden(
        id="scrawl",
        label="the old warning page",
        phrase="a scrap of paper with a scribble on it",
        warning="The page said, 'Do not wake the ghost.'",
        tags={"scribble", "ghost"},
    ),
}

TARGETS = {
    "bell": Target(
        id="bell",
        label="the brass bell",
        phrase="the brass bell hanging by a rope",
        risky=True,
        tags={"clank"},
    ),
    "box": Target(
        id="box",
        label="the metal box",
        phrase="the metal box on the shelf",
        risky=True,
        tags={"clank"},
    ),
}

RESPONSES = {
    "call_help": Response(
        id="call_help",
        sense=3,
        power=3,
        text="called for a grown-up and held the lantern steady until help came",
        fail="called, but the dark was too thick and the clank kept echoing",
        qa_text="called for a grown-up and kept the lantern steady until help came",
        tags={"help", "lantern"},
    ),
    "back_away": Response(
        id="back_away",
        sense=3,
        power=2,
        text="backed away, shut the door, and waited for a grown-up",
        fail="backed away, but the noise was already too wild",
        qa_text="backed away, shut the door, and waited for a grown-up",
        tags={"help"},
    ),
    "ignore": Response(
        id="ignore",
        sense=1,
        power=0,
        text="ignored the warning and kept playing",
        fail="ignored the warning and kept playing",
        qa_text="ignored the warning and kept playing",
        tags={"reckless"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lila", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for m in MOODS:
        for f in FORBIDDEN:
            for t in TARGETS:
                if TARGETS[t].risky and FORBIDDEN[f].makes_ghosts:
                    combos.append((m, f, t))
    return combos


def reasonableness_gate() -> set[str]:
    return {rid for rid, r in RESPONSES.items() if r.sense >= SENSE_MIN}


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def ghost_risk(forbidden: Forbidden, target: Target) -> bool:
    return forbidden.makes_ghosts and target.risky


def fire_like_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_like_severity(delay)


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_scare(sim, sim.get(target_id), narrate=False)
    return {"ghostly": sim.get(target_id).meters["ghostly"] >= THRESHOLD}


def _do_scare(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["ghostly"] += 1
    propagate(world, narrate=narrate)


def tell(mood: Mood, forbidden: Forbidden, target: Target, response: Response,
         hero: str = "Mia", hero_gender: str = "girl",
         helper: str = "Theo", helper_gender: str = "boy",
         delay: int = 0) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    x = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    grown = world.add(Entity(id="Adult", kind="character", type="mother", role="adult", label="the grown-up"))
    page = world.add(Entity(id="page", label=forbidden.label, tags=forbidden.tags))
    tgt = world.add(Entity(id="target", label=target.label, tags=target.tags))

    h.memes["bravery"] = 6
    x.memes["caution"] = 5

    world.say(f"On a moonless night, {hero} and {helper} explored {mood.title}.")
    world.say(f"They had a lantern, but the dark spot at {mood.dark_spot} felt like it was listening.")
    world.para()

    world.say(f'{hero} found {forbidden.phrase}. {forbidden.warning}')
    h.memes["curiosity"] += 1
    world.say(f'{hero} whispered, "I am invincible." But the room answered with a tiny chill.')

    world.para()
    world.say(f'{helper} frowned. "That scribble is not a game," {helper} said, pointing at the page.')
    world.say(f'"If something clanks, we should call for help."')
    pred = predict(world, "target")
    world.facts["predicted_ghostly"] = pred["ghostly"]

    if response.id == "ignore":
        world.say(f'But {hero} did not listen. {hero} reached for the {target.label} anyway.')
        _do_scare(world, tgt)
        world.para()
        world.say(f'{target.label_word.capitalize()} gave a loud clank, and the shadows seemed to jump.')
        world.say(f'{grown.label_word.capitalize()} rushed in and {response.fail}.')
        world.say("The lesson was clear: being brave does not mean being careless.")
    else:
        world.say(f'{helper} was right, and {hero} backed away from the page and the clanking thing.')
        world.say(f'They used the lantern instead, so the dark stayed only dark, not scary.')
        world.para()
        world.say(f'{grown.label_word.capitalize()} smiled and {response.text}.')
        world.say(f'After that, the old hall looked gentle again, with {mood.ending_image}.')
        world.say("They learned that caution can be the bravest choice.")

    world.facts.update(
        hero=h, helper=x, adult=grown, forbidden=forbidden, target_cfg=target,
        target=tgt, response=response, mood=mood, outcome="contained" if response.id != "ignore" else "warned",
        clank_heard=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary ghost story for a young child that includes "invincible", '
        f'"scribble", and "clank".',
        f"Tell a spooky-but-gentle story where {f['hero'].id} thinks {f['hero'].pronoun()} is invincible, "
        f"but a scribble on an old page and a clank in the dark teach caution.",
        f"Write a short ghost story with a warning, a clank, and a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    resp = f["response"]
    mood = f["mood"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, who were exploring {mood.title}."),
        ("Why was the story cautionary?",
         f"It warned that being bold is not the same as being careful. {helper.id} noticed the danger first, and that helped keep everyone safe."),
    ]
    if f["response"].id != "ignore":
        qa.append((
            "What did they do instead of chasing the clank?",
            f"They chose a safer response: they {resp.qa_text}. That kept the ghostly scare from turning into a bigger problem."
        ))
    else:
        qa.append((
            "What happened when they did not listen?",
            f"The {f['target'].label_word} made a loud clank and the room grew much scarier. Then the grown-up came running."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["forbidden"].tags) | set(world.facts["target_cfg"].tags)
    if "scribble" in tags:
        out.append(("What is a scribble?",
                     "A scribble is a messy line or mark made by writing or drawing quickly. In a ghost story, it can look mysterious and a little spooky."))
    if "clank" in tags:
        out.append(("What does clank mean?",
                     "Clank is a loud metal sound. It can make a quiet room feel eerie because it stands out so much."))
    if "ghost" in tags:
        out.append(("Are ghosts real in stories like this?",
                     "In stories, ghosts are part of the pretend spooky world. They help make the warning feel mysterious without needing real danger."))
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
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mood="hall",
        forbidden="scrawl",
        target="bell",
        response="call_help",
        hero="Mia",
        hero_gender="girl",
        helper="Theo",
        helper_gender="boy",
        delay=0,
    ),
    StoryParams(
        mood="attic",
        forbidden="scrawl",
        target="box",
        response="back_away",
        hero="Owen",
        hero_gender="boy",
        helper="Ava",
        helper_gender="girl",
        delay=1,
    ),
    StoryParams(
        mood="hall",
        forbidden="scrawl",
        target="bell",
        response="ignore",
        hero="Nora",
        hero_gender="girl",
        helper="Eli",
        helper_gender="boy",
        delay=1,
    ),
]


def explain_rejection(forbidden: Forbidden, target: Target) -> str:
    if not ghost_risk(forbidden, target):
        return "(No story: that combination is too harmless for a ghost warning.)"
    return "(No story: this setup does not support the cautionary ghost-story turn.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    options = ", ".join(sorted(reasonableness_gate()))
    return f"(Refusing response '{rid}': sense={r.sense} < {SENSE_MIN}. Try: {options}.)"


ASP_RULES = r"""
valid(M, F, T) :- mood(M), forbidden(F), target(T), ghost_risk(F, T).
reasonable(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% Outcome twin:
ghosty :- chosen_target(T), delay(D), target_risk(T), severity(D, V), V > 0.
contained :- chosen_response(R), response(R), power(R, P), delay(D), severity(D, V), P >= V.
warned :- not ghosty.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MOODS:
        lines.append(asp.fact("mood", mid))
    for fid in FORBIDDEN:
        lines.append(asp.fact("forbidden", fid))
        lines.append(asp.fact("ghost_risk", fid, "bell"))
        lines.append(asp.fact("ghost_risk", fid, "box"))
    for tid in TARGETS:
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("target_risk", tid))
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
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/1."))
    return sorted(x for (x,) in asp.atoms(model, "reasonable"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scen = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scen, "#show contained/0.\n#show warned/0."))
    atoms = {s.name for s in model}
    return "contained" if "contained" in atoms else "warned"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    py_resp = reasonableness_gate()
    cl_resp = set(asp_reasonable())
    if py_resp == cl_resp:
        print(f"OK: reasonable responses match ({sorted(py_resp)}).")
    else:
        rc = 1
        print("MISMATCH in responses.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(
            mood=None, forbidden=None, target=None, response=None,
            hero=None, hero_gender=None, helper=None, helper_gender=None,
            seed=None, delay=None, n=1, all=False, trace=False, qa=False,
            json=False, asp=False, verify=False, show_asp=False
        ), random.Random(7)))
        assert sample.story
        assert sample.prompts
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary ghost-story world using the words invincible, scribble, and clank."
    )
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.forbidden and args.target:
        if not ghost_risk(FORBIDDEN[args.forbidden], TARGETS[args.target]):
            raise StoryError(explain_rejection(FORBIDDEN[args.forbidden], TARGETS[args.target]))

    combos = [c for c in valid_combos()
              if (args.mood is None or c[0] == args.mood)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mood, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(reasonableness_gate()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_choices = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero]
    helper = args.helper or rng.choice(helper_choices)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        mood=mood,
        forbidden=forbidden,
        target=target,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mood not in MOODS or params.forbidden not in FORBIDDEN or params.target not in TARGETS or params.response not in RESPONSES:
        raise StoryError("(Invalid params for this story world.)")
    world = tell(
        MOODS[params.mood],
        FORBIDDEN[params.forbidden],
        TARGETS[params.target],
        RESPONSES[params.response],
        hero=params.hero,
        hero_gender=params.hero_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        delay=params.delay,
    )
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
        print(asp_program("", "#show valid/3.\n#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"reasonable responses: {', '.join(asp_reasonable())}\n")
        for m, f, t in asp_valid_combos():
            print(f"{m:6} {f:8} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
