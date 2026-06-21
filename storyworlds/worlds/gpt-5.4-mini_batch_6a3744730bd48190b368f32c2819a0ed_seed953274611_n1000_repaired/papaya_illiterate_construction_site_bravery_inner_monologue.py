#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/papaya_illiterate_construction_site_bravery_inner_monologue.py
==============================================================================================

A standalone storyworld for a tiny superhero-style construction-site tale:
a brave helper faces a problem, listens to an inner monologue, and turns
confusion into a safe rescue. The seed words are woven into the world:
papaya and illiterate.

Premise:
- At a construction site, a child helper or small hero wants to solve a simple
  problem.
- An illiterate foreman or worker cannot read a warning sign or list.
- The hero's bravery is useful, but the inner monologue keeps that bravery
  careful rather than reckless.
- The ending proves what changed in the world: a barrier is secured, a plan is
  chosen, or a mistake is corrected.

This file follows the Storyweavers contract:
- stdlib-only script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports --verify, --show-asp, --asp, --json, --qa, --trace, --all, -n, --seed
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
BRAVERY_BASE = 4.0


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
    detail: str
    mood: str
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
class Problem:
    id: str
    label: str
    phrase: str
    danger: str
    makes_confusion: bool = False
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
class Challenge:
    id: str
    label: str
    phrase: str
    risk: str
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
class Aid:
    id: str
    label: str
    phrase: str
    use: str
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
    setting: str
    problem: str
    challenge: str
    aid: str
    response: str
    hero: str
    hero_gender: str
    worker: str
    worker_gender: str
    supervisor: str
    trait: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_confuse(world: World) -> list[str]:
    out: list[str] = []
    worker = world.get("worker")
    if worker.memes["confusion"] < THRESHOLD:
        return out
    sig = ("confusion", worker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    worker.memes["fear"] += 1
    out.append("__silent__")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["bravery"] < THRESHOLD or hero.memes["monologue"] < THRESHOLD:
        return out
    sig = ("brave", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["focus"] += 1
    out.append("__silent__")
    return out


CAUSAL_RULES = [Rule("confuse", _r_confuse), Rule("brave", _r_brave)]


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


def danger_exists(problem: Problem, challenge: Challenge) -> bool:
    return problem.makes_confusion and challenge.id in {"sign", "rope", "gate"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def is_contained(response: Response, challenge: Challenge) -> bool:
    return response.power >= challenge_risk(challenge)


def challenge_risk(challenge: Challenge) -> int:
    return {"sign": 2, "rope": 1, "gate": 3}.get(challenge.id, 2)


def hero_bravery(trait: str) -> float:
    return BRAVERY_BASE + (1.5 if trait in {"brave", "bold", "steady"} else 0.5)


def inner_voice(hero: Entity, problem: Problem, setting: Setting) -> str:
    if problem.id == "sign":
        return (
            f"{hero.id} thought, I can be brave without being careless. "
            f"If that sign stays unread, someone could walk where the floor is not safe."
        )
    return (
        f"{hero.id} thought, I should look twice. "
        f"Being brave means helping at the right moment, not rushing past the danger."
    )


def predict_problem(world: World, challenge_id: str) -> dict:
    sim = world.copy()
    _create_confusion(sim, narrate=False)
    _act_help(sim, sim.get(challenge_id), narrate=False)
    return {
        "confusion": sim.get("worker").memes["confusion"],
        "risk": sim.get("site").meters["risk"],
    }


def _create_confusion(world: World, narrate: bool = True) -> None:
    worker = world.get("worker")
    worker.memes["confusion"] += 1
    world.get("site").meters["risk"] += 1
    propagate(world, narrate=narrate)


def _act_help(world: World, challenge: Entity, narrate: bool = True) -> None:
    if challenge.id == "sign":
        world.get("site").meters["risk"] = max(0.0, world.get("site").meters["risk"] - 1)
        world.get("worker").memes["relief"] += 1
    elif challenge.id == "rope":
        world.get("rope").meters["tension"] = 0.0
    elif challenge.id == "gate":
        world.get("gate").meters["blocked"] = 0.0
    propagate(world, narrate=narrate)


def tell(setting: Setting, problem: Problem, challenge: Challenge, aid: Aid,
         response: Response, hero_name: str, hero_gender: str, worker_name: str,
         worker_gender: str, supervisor: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    worker = world.add(Entity(id="worker", kind="character", type=worker_gender, label=worker_name, role="worker", traits=["illiterate"]))
    boss = world.add(Entity(id="supervisor", kind="character", type="adult", label=supervisor, role="supervisor"))
    site = world.add(Entity(id="site", type="place", label=setting.place))
    world.add(Entity(id="rope", type="thing", label="the rope"))
    world.add(Entity(id="gate", type="thing", label="the gate"))
    world.add(Entity(id="sign", type="thing", label=problem.label))
    world.add(Entity(id="aid", type="thing", label=aid.label))

    hero.memes["bravery"] = hero_bravery(trait)
    hero.memes["monologue"] = 1.0
    worker.memes["confusion"] = 1.0

    world.say(
        f"At {setting.place}, {hero_name} and {worker_name} worked under the bright sky. "
        f"{setting.detail} A little snack break even smelled like papaya from a lunch box nearby."
    )
    world.say(
        f"{worker_name} squinted at {problem.phrase} and frowned. {worker_name} was illiterate, "
        f"so the words on the sign were only a blur. That made the whole site feel jumpy."
    )
    world.para()
    world.say(
        f"{hero_name} lifted {aid.phrase} and took a deep breath. "
        f"Bravery bubbled up, but the inner monologue stayed close and gentle."
    )
    world.say(inner_voice(hero, problem, setting))
    world.say(
        f'"{supervisor}!" {hero_name} called. "{worker_name} cannot read that sign, and it may hide a danger."'
    )

    danger = danger_exists(problem, challenge)
    if danger:
        _create_confusion(world, narrate=False)

    world.para()
    if response.id == "guide":
        _act_help(world, world.get(challenge.id), narrate=False)
        world.say(
            f"{supervisor} hurried over, and {response.text.replace('{challenge}', challenge.label)}."
        )
        world.say(
            f"The danger settled down. {worker_name} could stay safe, and {hero_name} stood a little taller."
        )
        world.say(
            f"By the end, the papaya lunch was still fresh, the sign was fixed, and the site was calm again."
        )
        outcome = "contained"
    else:
        world.say(
            f"{supervisor} came, but {response.fail.replace('{challenge}', challenge.label)}."
        )
        world.say(
            f"The mistake spread fast enough to scare everyone, and the site had to stop for a while."
        )
        world.say(
            f"Even then, {hero_name} kept {hero.pronoun('possessive')} chin up and promised to ask for help sooner next time."
        )
        outcome = "failed"

    world.facts.update(
        setting=setting,
        problem=problem,
        challenge=challenge,
        aid=aid,
        response=response,
        hero=hero,
        worker=worker,
        boss=boss,
        outcome=outcome,
    )
    return world


SETTINGS = {
    "construction_site": Setting(
        id="construction_site",
        place="the construction site",
        detail="Cranes stood high, the fence rattled, and hard hats bobbed between piles of bricks.",
        mood="noisy",
        tags={"construction", "site"},
    ),
}

PROBLEMS = {
    "sign": Problem(
        id="sign",
        label="the warning sign",
        phrase="a warning sign with big letters",
        danger="it says where the floor is unsafe",
        makes_confusion=True,
        tags={"sign", "read"},
    ),
}

CHALLENGES = {
    "gate": Challenge(
        id="gate",
        label="the swinging gate",
        phrase="the swinging gate near the trench",
        risk="it can open into the wrong place",
        tags={"gate"},
    ),
    "rope": Challenge(
        id="rope",
        label="the hanging rope",
        phrase="a loose rope by the scaffold",
        risk="it can knock things loose",
        tags={"rope"},
    ),
    "sign": Challenge(
        id="sign",
        label="the warning sign",
        phrase="the warning sign with big letters",
        risk="it hides a dangerous spot",
        tags={"sign"},
    ),
}

AIDS = {
    "radio": Aid(
        id="radio",
        label="the radio",
        phrase="a walkie-talkie radio",
        use="call for help",
        tags={"radio"},
    ),
    "flashlight": Aid(
        id="flashlight",
        label="the flashlight",
        phrase="a flashlight clipped to a belt",
        use="look closely",
        tags={"light"},
    ),
    "clipboard": Aid(
        id="clipboard",
        label="the clipboard",
        phrase="a clipboard with a plan",
        use="check the list",
        tags={"paper"},
    ),
}

RESPONSES = {
    "guide": Response(
        id="guide",
        sense=3,
        power=3,
        text="read the sign aloud and guided everyone to the safe path",
        fail="tried to read the sign aloud, but the words were still too muddled",
        qa_text="read the sign aloud and guided everyone to the safe path",
        tags={"safe", "help"},
    ),
    "secure": Response(
        id="secure",
        sense=3,
        power=2,
        text="blocked the open edge and tied the loose rope tight",
        fail="blocked the edge, but the rope was still loose and the plan was not enough",
        qa_text="blocked the open edge and tied the loose rope tight",
        tags={"safe", "help"},
    ),
    "mark": Response(
        id="mark",
        sense=2,
        power=2,
        text="marked the safe route with bright tape",
        fail="marked the route, but the tape could not solve the whole problem",
        qa_text="marked the safe route with bright tape",
        tags={"safe", "help"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        power=1,
        text="shouted, but no one understood the message in time",
        fail="shouted, but no one understood the message in time",
        qa_text="shouted, but no one understood the message in time",
        tags={"unsafe"},
    ),
}

HERO_NAMES = ["Nova", "Maya", "Iris", "Theo", "Ari", "Zane", "Lena", "Kai"]
WORKER_NAMES = ["Rico", "Milo", "Ana", "Bo", "Nia", "Luz"]
TRAITS = ["brave", "bold", "steady", "quick", "kind"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    challenge: str
    aid: str
    response: str
    hero: str
    hero_gender: str
    worker: str
    worker_gender: str
    supervisor: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, problem in PROBLEMS.items():
            for cid in CHALLENGES:
                if danger_exists(problem, CHALLENGES[cid]):
                    combos.append((sid, pid, cid))
    return combos


def explain_rejection(problem: Problem, challenge: Challenge) -> str:
    return (
        f"(No story: {problem.label} only works here if it can actually create a problem, "
        f"and {challenge.label} must be something the hero can meaningfully fix. "
        f"Try the warning sign with the gate or rope.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too weak or too unsafe for this story "
        f"(sense={r.sense}). Try one of: {better}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style construction site storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--worker")
    ap.add_argument("--worker-gender", choices=["girl", "boy"])
    ap.add_argument("--supervisor", choices=["Foreman", "Boss", "Captain"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    if args.problem and args.challenge:
        if not danger_exists(PROBLEMS[args.problem], CHALLENGES[args.challenge]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], CHALLENGES[args.challenge]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.challenge is None or c[2] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, challenge = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    worker_gender = args.worker_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    worker = args.worker or rng.choice([n for n in WORKER_NAMES if n != hero])
    supervisor = args.supervisor or rng.choice(["Foreman", "Boss", "Captain"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        problem=problem,
        challenge=challenge,
        aid=aid,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        worker=worker,
        worker_gender=worker_gender,
        supervisor=supervisor,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.problem not in PROBLEMS or params.challenge not in CHALLENGES:
        raise StoryError("Unknown problem or challenge.")
    if params.aid not in AIDS or params.response not in RESPONSES:
        raise StoryError("Unknown aid or response.")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        CHALLENGES[params.challenge],
        AIDS[params.aid],
        RESPONSES[params.response],
        params.hero,
        params.hero_gender,
        params.worker,
        params.worker_gender,
        params.supervisor,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words '
        f'"papaya" and "illiterate" and takes place at {f["setting"].place}.',
        f"Tell a short rescue story where {f['hero'].id} stays brave, listens to "
        f"an inner monologue, and helps {f['worker'].id} at a construction site.",
        f"Write a gentle action story where a warning sign matters, someone is illiterate, "
        f"and a brave helper makes the safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    worker: Entity = f["worker"]
    problem: Problem = f["problem"]
    challenge: Challenge = f["challenge"]
    response: Response = f["response"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, a brave helper, and {worker.id}, who could not read the sign. "
                   f"Together they faced a small danger at the construction site."
        ),
        QAItem(
            question=f"Why was {worker.id} confused?",
            answer=f"{worker.id} was illiterate, so the warning sign looked like a blur of shapes instead of clear words. "
                   f"That is why {hero.id} knew to step in and help."
        ),
        QAItem(
            question="How did bravery and the inner monologue help?",
            answer=f"Bravery pushed {hero.id} to act, but the inner monologue kept the help careful and smart. "
                   f"It helped {hero.id} choose a safe response instead of rushing."
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            QAItem(
                question=f"What did {hero.id} do at the end?",
                answer=f"{hero.id} used the {response.label} to {response.qa_text}. "
                       f"That fixed the problem and made the site calm again."
            )
        )
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the warning sign handled, the danger contained, and the papaya snack still waiting nearby. "
                       f"The construction site felt safe again, and the hero stood proud."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    items = [
        QAItem("What is papaya?", "Papaya is a soft tropical fruit with sweet orange flesh. People can cut it open and eat it with a spoon."),
        QAItem("What does illiterate mean?", "Illiterate means a person cannot read words on a page or sign. That person may need help with written messages."),
        QAItem("Why can a construction site be dangerous?", "Construction sites can be dangerous because there are heavy tools, open edges, machines, and signs that tell people where to stay safe."),
        QAItem("What is bravery?", "Bravery means doing the helpful thing even when you feel nervous. Brave people can still think carefully and ask for help."),
        QAItem("What is an inner monologue?", "An inner monologue is the voice in your head that thinks things through. It can remind you to pause, notice danger, and make a wise choice."),
    ]
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="construction_site",
        problem="sign",
        challenge="gate",
        aid="radio",
        response="guide",
        hero="Nova",
        hero_gender="girl",
        worker="Rico",
        worker_gender="boy",
        supervisor="Foreman",
        trait="brave",
    ),
    StoryParams(
        setting="construction_site",
        problem="sign",
        challenge="rope",
        aid="flashlight",
        response="mark",
        hero="Theo",
        hero_gender="boy",
        worker="Ana",
        worker_gender="girl",
        supervisor="Boss",
        trait="steady",
    ),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.makes_confusion:
            lines.append(asp.fact("confusing", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk", cid, challenge_risk(CHALLENGES[cid])))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
safe_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
danger(P, C) :- confusing(P), challenge(C).
valid(S, P, C) :- setting(S), problem(P), challenge(C), danger(P, C).
contained(R, C) :- response(R), power(R, P), risk(C, V), P >= V.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show safe_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe_response"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_story(sample: StorySample) -> str:
    return sample.story


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    if args.problem and args.challenge:
        if not danger_exists(PROBLEMS[args.problem], CHALLENGES[args.challenge]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], CHALLENGES[args.challenge]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.challenge is None or c[2] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, challenge = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    worker_gender = args.worker_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    worker = args.worker or rng.choice([n for n in WORKER_NAMES if n != hero])
    supervisor = args.supervisor or rng.choice(["Foreman", "Boss", "Captain"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        problem=problem,
        challenge=challenge,
        aid=aid,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        worker=worker,
        worker_gender=worker_gender,
        supervisor=supervisor,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS.get(params.setting, SETTINGS["construction_site"]),
        PROBLEMS.get(params.problem, PROBLEMS["sign"]),
        CHALLENGES.get(params.challenge, CHALLENGES["gate"]),
        AIDS.get(params.aid, AIDS["radio"]),
        RESPONSES.get(params.response, RESPONSES["guide"]),
        params.hero,
        params.hero_gender,
        params.worker,
        params.worker_gender,
        params.supervisor,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show safe_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
