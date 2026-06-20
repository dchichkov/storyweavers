#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/advantage_end_grip_dim_repetition_fable.py
===========================================================================

A small fable-like storyworld about a repeated choice between a quick advantage
and a patient finish. The tiny domain is built around one simple problem:
two friends want to cross a windy hill, one wants the easy shortcut, and a
patient helper teaches that the best advantage can be the one that lasts to the
end.

Seed words:
- advantage
- end
- grip-dim

Feature:
- Repetition

Style:
- Fable
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
PATIENCE_GOAL = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fox"}
        male = {"boy", "father", "dad", "man", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    wind: str
    height: str
    edge: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Choice:
    id: str
    label: str
    text: str
    advantage: int
    risk: int
    kind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Helper:
    id: str
    label: str
    phrase: str
    grip_dim: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    place: Place
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def propagate(world: World, narrate: bool = True) -> list[str]:
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


def _r_tire(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tired"] < THRESHOLD:
            continue
        sig = ("tire", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["doubt"] += 1
        out.append("")
    return out


def _r_patience(world: World) -> list[str]:
    out: list[str] = []
    mentor = world.entities.get("mentor")
    for ent in list(world.entities.values()):
        if ent.memes["steady"] < THRESHOLD or mentor is None:
            continue
        sig = ("steady", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        mentor.memes["pride"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("tire", _r_tire), Rule("steady", _r_patience)]


def reason_gate(choice: Choice, place: Place) -> bool:
    return True if choice.risk <= 3 and choice.advantage >= 1 else False


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid in PLACES:
        for cid in CHOICES:
            if reason_gate(CHOICES[cid], PLACES[pid]):
                combos.append((pid, cid))
    return combos


def _predict(world: World, choice: Choice) -> dict:
    sim = world.copy()
    do_choice(sim, choice, narrate=False)
    return {
        "safe": sim.get("hero").meters["tired"] < 2,
        "steady": sim.get("hero").memes["steady"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"On a bright morning, {hero.id} and {friend.id} climbed the {place.label}. "
        f"The {place.wind} wind hummed, the path leaned steeply, and the hill seemed to ask for a choice."
    )


def temptation(world: World, hero: Entity, choice: Choice, place: Place) -> None:
    hero.memes["want"] += 1
    world.say(
        f'{hero.id} pointed at the {choice.label}. "{choice.text}," {hero.id} said, '
        f'"and we will have an advantage at once."'
    )
    world.say(
        f"Again and again, {hero.id} looked at the quick way. Again and again, the little shortcut looked kind."
    )


def warn(world: World, friend: Entity, hero: Entity, choice: Choice, helper: Helper) -> None:
    pred = _predict(world, choice)
    friend.memes["care"] += 1
    world.facts["predicted_safe"] = pred["safe"]
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "{helper.label} says grip-dim hands slip, '
        f'and a rushed climb loses the end," {friend.id} said. "A true advantage must last."'
    )


def do_choice(world: World, choice: Choice, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.meters["tired"] += choice.risk
    hero.memes["bold"] += 1
    if choice.kind == "shortcut":
        hero.meters["careless"] += 1
    if narrate:
        world.say(
            f"{hero.id} took the {choice.label}, hoping the easy way would help."
        )
    propagate(world, narrate=narrate)


def struggle(world: World, hero: Entity, friend: Entity, choice: Choice) -> None:
    world.say(
        f"The path bent, the wind pushed, and {hero.id}'s steps grew small. "
        f"Again and again, {hero.id} tried to hurry; again and again, the hill asked for patience."
    )


def finish(world: World, hero: Entity, friend: Entity, helper: Helper) -> None:
    hero.memes["steady"] += 1
    hero.meters["tired"] = max(0.0, hero.meters["tired"] - 1.0)
    world.say(
        f"{friend.id} tied {helper.phrase} around the branch and showed how to hold on. "
        f"The grip-dim knot held firm, and the two friends climbed one careful step after another."
    )
    world.say(
        f"At the end, {hero.id} reached the top without slipping, and the better advantage was not speed but staying sure-footed."
    )
    world.say(
        "The fable ended with a quiet lesson: a fast gain may shine for a moment, but a patient choice can carry you farther."
    )


def tell(place: Place, choice: Choice, helper: Helper, hero_name: str, friend_name: str, seed: int = 0) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="fox", role="seeker"))
    friend = world.add(Entity(id=friend_name, kind="character", type="fox", role="mentor"))
    world.add(Entity(id="mentor", kind="character", type="owl", role="mentor", label="the old owl"))
    hero.memes["curious"] = 1
    friend.memes["steady"] = 1

    intro(world, hero, friend, place)
    world.para()
    temptation(world, hero, choice, place)
    warn(world, friend, hero, choice, helper)
    world.para()
    do_choice(world, choice)
    struggle(world, hero, friend, choice)
    world.para()
    finish(world, hero, friend, helper)
    world.facts.update(hero=hero, friend=friend, place=place, choice=choice, helper=helper)
    return world


PLACES = {
    "hill": Place("hill", "windy hill", "restless", "high", "edge", {"wind", "hill"}),
    "ridge": Place("ridge", "narrow ridge", "sharp", "high", "edge", {"wind", "ridge"}),
    "path": Place("path", "stone path", "cool", "long", "end", {"path"}),
}

CHOICES = {
    "shortcut": Choice("shortcut", "short cut", "take the short cut", advantage=3, risk=3, kind="shortcut", tags={"advantage"}),
    "steady_steps": Choice("steady_steps", "steady steps", "keep to the steady steps", advantage=2, risk=1, kind="steady", tags={"steady"}),
    "pause": Choice("pause", "rested pause", "pause and breathe first", advantage=1, risk=0, kind="steady", tags={"pause"}),
}

HELPERS = {
    "rope": Helper("rope", "rope", "a rope", "grip-dim", {"rope", "grip-dim"}),
    "staff": Helper("staff", "walking staff", "a walking staff", "grip-dim", {"staff", "grip-dim"}),
}

GIRL_NAMES = ["Luna", "Iris", "Mina", "Tala", "Nina"]
BOY_NAMES = ["Rowan", "Pip", "Milo", "Theo", "Bram"]


@dataclass
@dataclass
class StoryParams:
    place: str
    choice: str
    helper: str
    hero: str
    friend: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that includes the words "advantage", "end", and "grip-dim".',
        f"Tell a repetition-heavy story about {f['hero'].id} climbing {f['place'].label} and learning that a quick advantage is not always the best one.",
        f"Write a gentle animal fable where a friend warns about a grip-dim hold and the hero learns to finish carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, place, choice = f["hero"], f["friend"], f["place"], f["choice"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {friend.id}, two foxes climbing the {place.label}. The old owl watches as the lesson grows.",
        ),
        QAItem(
            question="Why did the quick choice seem tempting?",
            answer=f"It seemed tempting because it promised an advantage at once. But the story shows that a fast advantage can fade before the end.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They used the {f['helper'].label} and climbed more carefully. The grip-dim knot helped them hold on, so the ending was safe and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an advantage?",
            answer="An advantage is something that gives you a better chance or makes a task easier. But in a fable, the story often asks whether that advantage is truly good.",
        ),
        QAItem(
            question="What does it mean to reach the end?",
            answer="To reach the end means to finish what you started. A good ending shows what changed after the choice was made.",
        ),
        QAItem(
            question="What is grip-dim in this story?",
            answer="Grip-dim is the firm kind of hold the helper uses in the story. It reminds the foxes that a careful grip can matter more than speed.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill", "shortcut", "rope", "Lena", "Toby"),
    StoryParams("ridge", "steady_steps", "staff", "Mara", "Pip"),
    StoryParams("path", "pause", "rope", "Owen", "Nia"),
]


def explain_rejection(choice: Choice) -> str:
    return f"(No story: the choice '{choice.label}' is too weak to build a clear fable.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("advantage", cid, c.advantage))
        lines.append(asp.fact("risk", cid, c.risk))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C) :- place(P), choice(C), advantage(C, A), risk(C, R), A >= 1, R <= 3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, choice=None, helper=None, hero=None, friend=None
        ), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception:
        traceback.print_exc()
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about advantage, end, and grip-dim.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    choice_id = args.choice or rng.choice(sorted(CHOICES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    place_id = args.place or rng.choice(sorted(PLACES))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    pool = [n for n in GIRL_NAMES + BOY_NAMES if n != hero]
    friend = args.friend or rng.choice(pool)
    return StoryParams(place_id, choice_id, helper_id, hero, friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CHOICES[params.choice], HELPERS[params.helper], params.hero, params.friend, seed=params.seed or 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, c in asp_valid_combos():
            print(f"  {p:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
