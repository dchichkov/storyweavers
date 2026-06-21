#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/care_rhyme_ghost_story.py
=========================================================

A tiny storyworld for a ghost-story rhyme about care:
a child hears a bump in a dim room, follows a careful rhythm,
finds the "ghost" is only a worried pet or a loose thing, and
chooses a kinder, safer ending. The prose is child-facing and
the world model drives the beats.

This script is standalone and uses only stdlib plus the shared
result containers. The ASP twin is inline and imported lazily.
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
    spooky: bool = False
    noisy: bool = False
    fragile: bool = False

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
    dark_nook: str
    sound_word: str
    weather: str = ""
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
class Cause:
    id: str
    label: str
    phrase: str
    noise: str
    reveal: str
    safe_note: str
    makes_bump: bool = False
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
    out = []
    for e in list(world.entities.values()):
        if e.meters["bump"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    if world.get("cause").meters["spotted"] < THRESHOLD:
        return out
    sig = ("reveal", "cause")
    if sig not in world.fired:
        world.fired.add(sig)
        world.get("child").memes["relief"] += 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, cause in CAUSES.items():
            if cause.makes_bump:
                combos.append((sid, cid))
    return combos


def bump_hazard(cause: Cause) -> bool:
    return cause.makes_bump


def _do_bump(world: World, cause_ent: Entity, narrate: bool = True) -> None:
    cause_ent.meters["bump"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, cause_id: str) -> dict:
    sim = world.copy()
    _do_bump(sim, sim.get(cause_id), narrate=False)
    return {
        "bumped": sim.get(cause_id).meters["bump"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def opening(world: World, child: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a hush-hush night, {child.id} went to {setting.place}, where even the air seemed to care and stare."
    )
    world.say(
        f"Down by {setting.dark_nook}, a little hush made a spooky push, and the shadows swayed in a sleepy way."
    )


def hear_bump(world: World, child: Entity, cause: Cause) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then came a soft little thump, a bump, a bump, a bump; {child.id} held still and listened with care and dare."
    )


def suspect(world: World, child: Entity, cause: Cause) -> None:
    child.memes["fear"] += 1
    world.say(
        f'"Is that a ghost?" {child.id} wondered, all fluttery and slight, in the candleless dark of the night.'
    )


def reveal_safe(world: World, child: Entity, cause: Cause, setting: Setting) -> None:
    cause.meters["spotted"] += 1
    world.say(
        f"With a careful peek and a tiny brave squeak, {child.id} found the truth in the gloom: it was only {cause.reveal}."
    )
    world.say(
        f"{cause.safe_note.capitalize()}, and the room felt less like a fright and more like a light."
    )


def response_text(resp: Response, cause: Cause) -> str:
    return resp.text.replace("{cause}", cause.label)


def fail_text(resp: Response, cause: Cause) -> str:
    return resp.fail.replace("{cause}", cause.label)


def resolve(world: World, child: Entity, parent: Entity, resp: Response, cause: Cause) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    world.say(
        f"Then {parent.label_word} came near, calm as a star, and {response_text(resp, cause)}."
    )
    world.say(
        f"The bumping stopped, the shadows lost their bark, and the night grew soft in the dark."
    )


def resolve_fail(world: World, child: Entity, parent: Entity, resp: Response, cause: Cause) -> None:
    world.say(
        f"Then {parent.label_word} came near, but {fail_text(resp, cause)}."
    )
    world.say(
        f"So the house stayed loud for a while, until the truth was found and the fright was unbound."
    )


def ending(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"After that, {child.id} was kinder to the night: a little more careful, a little more bright."
    )
    world.say(
        f"And {setting.place} was just {setting.place} again, with no ghost in sight, only peace in the light."
    )


SETTINGS = {
    "attic": Setting(id="attic", place="the attic", dark_nook="the old trunk by the wall", sound_word="creak", weather="windy", tags={"dark"}),
    "hall": Setting(id="hall", place="the long hall", dark_nook="the coat rack corner", sound_word="tap", weather="rainy", tags={"dark"}),
    "cellar": Setting(id="cellar", place="the cellar", dark_nook="the shelf behind the jars", sound_word="thud", weather="quiet", tags={"dark"}),
}

CAUSES = {
    "cat": Cause(id="cat", label="a cat", phrase="a little cat", noise="mew", reveal="a sleepy cat with a shiny eye", safe_note="just a cat wanted care", makes_bump=True, tags={"animal"}),
    "branch": Cause(id="branch", label="a branch", phrase="a branch by the window", noise="scrape", reveal="a branch tapping the glass", safe_note="the wind was brushing it", makes_bump=True, tags={"object"}),
    "toy": Cause(id="toy", label="a toy", phrase="a toy on a string", noise="clack", reveal="a toy that had slipped loose", safe_note="it had only rolled and rung", makes_bump=True, tags={"object"}),
}

RESPONSES = {
    "lamp": Response(id="lamp", sense=3, power=3, text="turned on the lamp and showed {cause} resting where it should", fail="fumbled with the lamp and still could not see {cause}", qa_text="turned on the lamp and showed the thing resting where it should", tags={"light"}),
    "hug": Response(id="hug", sense=3, power=2, text="gave {cause} a careful nudge and a warm look", fail="gave {cause} a nudge, but the dark stayed stubborn", qa_text="gave it a careful nudge and a warm look", tags={"kindness"}),
    "listen": Response(id="listen", sense=2, power=2, text="held still and listened until the answer came clear", fail="held still, but the answer did not come clear yet", qa_text="held still and listened until the answer came clear", tags={"care"}),
    "water_bucket": Response(id="water_bucket", sense=1, power=1, text="hurried in with a bucket of water, which was not the right care at all", fail="hurried in with a bucket of water, but it only made a mess", qa_text="used a bucket of water", tags={"weak"}),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Theo", "Max", "Finn", "Ben"]


@dataclass
class StoryParams:
    setting: str
    cause: str
    response: str
    child: str
    child_gender: str
    parent: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhymey ghost-story world about care.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection(cause: Cause) -> str:
    return f"(No story: the chosen thing would not make a bump, so there is no ghostly riddle to solve.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} is too low. Try one of: {good}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and not bump_hazard(CAUSES[args.cause]):
        raise StoryError(explain_rejection(CAUSES[args.cause]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.cause is None or c[1] == args.cause)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, cause = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, cause=cause, response=response, child=child, child_gender=gender, parent=parent)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    resp = RESPONSES[params.response]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    cause_ent = world.add(Entity(id="cause", kind="thing", type="thing", label=cause.label, spooky=True, noisy=True))
    world.facts.update(setting=setting, cause=cause, response=resp, child=child, parent=parent, cause_ent=cause_ent)

    opening(world, child, setting)
    world.para()
    hear_bump(world, child, cause)
    suspect(world, child, cause)
    child.memes["care"] += 1

    pred = predict(world, "cause")
    world.facts["pred"] = pred
    if pred["bumped"]:
        _do_bump(world, cause_ent, narrate=False)
    world.para()
    reveal_safe(world, child, cause, setting)
    if resp.sense >= SENSE_MIN:
        resolve(world, child, parent, resp, cause)
    else:
        resolve_fail(world, child, parent, resp, cause)
    world.para()
    ending(world, child, setting)

    world.facts["outcome"] = "safe"
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost-story rhyme for a child that includes the word "care" and ends with a safe reveal.',
        f"Tell a spooky-but-kind story where {f['child'].id} hears a bump in {f['setting'].place} and uses care to find out what it is.",
        f'Write a rhyming story about a supposed ghost that turns out to be something ordinary, with a calm ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    cause = f["cause"]
    resp = f["response"]
    parent = f["parent"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who heard a spooky little sound and tried to be careful. {child.id}'s {parent.label_word} helped at the end."),
        ("What did {0} hear?".format(child.id),
         f"{child.id} heard a bump in {setting.place}. That sound made the room feel ghostly, so {child.id} listened with care."),
        ("What was the ghost really?".format(child.id),
         f"It was really {cause.reveal}. The story turns from a fright into a simple, ordinary thing once it is seen clearly."),
    ]
    if resp.sense >= SENSE_MIN:
        qa.append((
            "How did the parent help?",
            f"{parent.label_word.capitalize()} came near and {resp.qa_text}. That calm help made the dark feel safe again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cause"].tags)
    tags |= {"care", "light"}
    out = []
    if "animal" in tags:
        out.append(("Why might a cat make a small bump at night?",
                    "A cat can move quietly, but its feet, tail, or collar can still make little taps and bumps in a dark room."))
    if "object" in tags:
        out.append(("Why can a loose object sound spooky in the dark?",
                    "A loose object can scrape, tap, or clack when it moves, and the sound can seem scarier when you cannot see it yet."))
    out.append(("What does care mean in a spooky story?",
                "Care means moving slowly, listening first, and choosing a calm way to find out the truth instead of jumping at a fright."))
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.spooky:
            bits.append("spooky")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
bump_hazard(C) :- cause(C), makes_bump(C).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(safe) :- sensible(R).
outcome(uncertain) :- response(R), not sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if c.makes_bump:
            lines.append(asp.fact("makes_bump", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show bump_hazard/1."))
    return sorted(set(asp.atoms(model, "bump_hazard")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != {(cid,) for cid, c in CAUSES.items() if c.makes_bump}:
        print("MISMATCH in ASP hazard gate.")
        rc = 1
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in ASP sensible responses.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming ghost story world about care.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    StoryParams(setting="attic", cause="cat", response="lamp", child="Mia", child_gender="girl", parent="mother"),
    StoryParams(setting="hall", cause="branch", response="listen", child="Leo", child_gender="boy", parent="father"),
    StoryParams(setting="cellar", cause="toy", response="hug", child="Nora", child_gender="girl", parent="mother"),
]


def asp_verify_and_exit() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show bump_hazard/1.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify_and_exit())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        print(f"{len(asp_valid_combos())} bump-making causes:")
        for (cid,) in asp_valid_combos():
            print(f"  {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
