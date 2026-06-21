#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/repetition_stew_rain_flashback_adventure.py
===========================================================================

A standalone story world for a small Adventure-style tale about repetition,
stew, and rain, with a flashback as the narrative instrument.

Premise:
- Two kids are on a little adventure.
- They are making stew outdoors or at a campsite.
- Rain threatens the meal.
- A flashback reminds them of a useful earlier lesson.
- Repetition matters: they repeat a careful action until the stew becomes right.

The world is state-driven: physical meters track stew warmth, wateriness, rain
soak, and fire/cover effects; emotional memes track worry, confidence, relief,
and memory. The story text is rendered from world state, not from a frozen
template swap.

This module supports:
- default story generation
- -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp

It imports storyworlds/results.py eagerly and storyworlds/asp.py lazily only
inside ASP helpers.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REASONABLE_MIN = 2

GIRL_NAMES = ["Mina", "Nora", "Lina", "Tess", "Zoe", "Ivy"]
BOY_NAMES = ["Arlo", "Theo", "Finn", "Jasper", "Noel", "Owen"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
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
    adventure: str
    shelter: str
    rain_risk: int
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
class Pot:
    id: str
    label: str
    material: str
    lid: bool
    portable: bool
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
    sense: int
    flood: int
    text: str
    repair: str
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
class Helper:
    id: str
    label: str
    action: str
    repeat_action: str
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


def _r_cool(world: World) -> list[str]:
    out: list[str] = []
    stew = world.entities.get("stew")
    if not stew or stew.meters["hot"] < THRESHOLD:
        return out
    sig = ("cool",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.entities.get("rain"):
        stew.meters["watery"] += 1
    if stew.meters["watery"] >= THRESHOLD:
        for e in list(world.entities.values()):
            if e.role in {"child1", "child2"}:
                e.memes["worry"] += 1
    out.append("__cool__")
    return out


def _r_repetition(world: World) -> list[str]:
    stew = world.entities.get("stew")
    if not stew or stew.meters["watery"] < THRESHOLD:
        return []
    sig = ("repeat",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stew.meters["good"] += 1
    for e in list(world.entities.values()):
        if e.role in {"child1", "child2"}:
            e.memes["confidence"] += 1
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_cool, _r_repetition):
            s = fn(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rain_problem(problem: Problem) -> bool:
    return problem.sense >= REASONABLE_MIN


def stew_at_risk(setting: Setting, pot: Pot) -> bool:
    return setting.rain_risk > 0 and pot.portable


def best_problem() -> Problem:
    return max(PROBLEMS.values(), key=lambda p: p.sense)


def predict(world: World, rain_on: bool) -> dict:
    sim = world.copy()
    sim.get("rain").meters["falling"] = 1 if rain_on else 0
    if rain_on:
        sim.get("stew").meters["hot"] += 0.5
        sim.get("stew").meters["watery"] += 1
    propagate(sim, narrate=False)
    return {"watery": sim.get("stew").meters["watery"], "good": sim.get("stew").meters["good"]}


def setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"On a bright adventure day, {a.id} and {b.id} set out for {setting.place}. "
        f"{setting.adventure}"
    )


def cook(world: World, a: Entity, b: Entity, pot: Pot) -> None:
    stew = world.get("stew")
    stew.meters["hot"] += 1
    stew.meters["tasty"] += 0.5
    world.say(
        f"They built a little fire and stirred the {pot.label} until the stew began to smell good."
    )


def rain_turns(world: World, setting: Setting, pot: Pot, problem: Problem) -> None:
    rain = world.get("rain")
    rain.meters["falling"] += 1
    world.get("stew").meters["watery"] += 1
    world.get("stew").meters["hot"] -= 0.2
    for e in list(world.entities.values()):
        if e.role in {"child1", "child2"}:
            e.memes["worry"] += 1
    world.say(
        f"Then rain started tapping the leaves and the pot. The {pot.label} looked a little too thin."
    )
    world.say(
        f"{a_name(world)} frowned. \"We need to fix the stew,\" {b_name(world)} said, because the rain was making trouble."
    )


def a_name(world: World) -> str:
    return world.get("child1").id


def b_name(world: World) -> str:
    return world.get("child2").id


def flashback(world: World, helper: Helper, parent: Entity) -> None:
    child = world.get("child1")
    child.memes["memory"] += 1
    world.say(
        f"{child.id} paused, and for a moment the campsite felt very still. Then {child.pronoun()} remembered a flashback: "
        f"back home, {parent.label_word} had once shown {child.pronoun('object')} how to {helper.action}."
    )


def repeat_fix(world: World, helper: Helper, pot: Pot) -> None:
    stew = world.get("stew")
    world.say(
        f"So they did it again and again: {helper.repeat_action}, then tasting, then stirring, then tasting again."
    )
    stew.meters["watery"] = max(0.0, stew.meters["watery"] - 1.0)
    stew.meters["good"] += 1.5
    for e in list(world.entities.values()):
        if e.role in {"child1", "child2"}:
            e.memes["confidence"] += 1


def end(world: World, setting: Setting, pot: Pot) -> None:
    stew = world.get("stew")
    world.say(
        f"At last the rain softened, the stew turned thick and warm, and the two adventurers ate beside the shelter, "
        f"happy that repetition had made the meal right."
    )


def tell(setting: Setting, pot: Pot, problem: Problem, helper: Helper,
         child1: str = "Mina", child1_gender: str = "girl",
         child2: str = "Arlo", child2_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id="child1", kind="character", type=child1_gender, role="child1"))
    a.id = child1
    b = world.add(Entity(id="child2", kind="character", type=child2_gender, role="child2"))
    b.id = child2
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="rain", type="weather", label="rain"))
    world.add(Entity(id="stew", type="food", label="stew"))
    setup(world, a, b, setting)
    cook(world, a, b, pot)
    world.para()
    rain_turns(world, setting, pot, problem)
    flashback(world, helper, parent)
    repeat_fix(world, helper, pot)
    end(world, setting, pot)
    world.facts.update(setting=setting, pot=pot, problem=problem, helper=helper, parent=parent, a=a, b=b)
    return world


SETTINGS = {
    "campsite": Setting(id="campsite", place="the campsite", adventure="They were following a narrow trail to the old lookout."),
    "forest": Setting(id="forest", place="the forest camp", adventure="They were looking for a stone bridge and a hidden map."),
}
POTS = {
    "tinpot": Pot(id="tinpot", label="tin pot", material="tin", lid=False, portable=True, tags={"portable"}),
    "kettle": Pot(id="kettle", label="kettle", material="iron", lid=True, portable=True, tags={"portable", "lid"}),
}
PROBLEMS = {
    "rain_thins": Problem(id="rain_thins", sense=3, flood=2, text="the rain thinned the stew", repair="cover it and simmer it again", tags={"rain", "stew"}),
    "rain_dilutes": Problem(id="rain_dilutes", sense=2, flood=1, text="rain splashed into the pot", repair="stir it again and again", tags={"rain", "repetition"}),
}
HELPERS = {
    "stir": Helper(id="stir", label="stirring", action="stir the pot slowly", repeat_action="stirring the pot slowly", tags={"repetition"}),
    "cover": Helper(id="cover", label="covering", action="cover the pot with the lid", repeat_action="covering the pot with the lid", tags={"repetition"}),
}


@dataclass
class StoryParams:
    setting: str
    pot: str
    problem: str
    helper: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in POTS:
            for prob in PROBLEMS:
                if stew_at_risk(SETTINGS[s], POTS[p]) and rain_problem(PROBLEMS[prob]):
                    out.append((s, p, prob))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pot", choices=POTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pot is None or c[1] == args.pot)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, p, prob = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=s, pot=p, problem=prob, helper=helper,
                       child1=rng.choice(GIRL_NAMES), child1_gender="girl",
                       child2=rng.choice(BOY_NAMES), child2_gender="boy",
                       parent="mother")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], POTS[params.pot], PROBLEMS[params.problem], HELPERS[params.helper],
                 params.child1, params.child1_gender, params.child2, params.child2_gender, params.parent)
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
        f'Write an Adventure story that includes repetition, stew, rain, and a flashback at {f["setting"].place}.',
        f"Tell a child-friendly adventure where rain threatens the stew and a flashback helps the children fix it by repeating the right action.",
        f'Write a short story with the words "repetition", "stew", and "rain" and a flashback that changes what the kids do next.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, setting, helper = f["a"], f["b"], f["setting"], f["helper"]
    return [
        ("What was the story about?",
         f"It was about {a.id} and {b.id} on an adventure at {setting.place}. They were trying to make the stew turn out right even while rain caused trouble."),
        ("What helped them fix the stew?",
         f"A flashback reminded {a.id} of how to {helper.action}. After that, they repeated the careful steps until the stew thickened."),
        ("How did the story end?",
         "The rain softened, the stew became warm and thick again, and the children ate happily by the shelter. Repetition turned the problem into a good meal."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is stew?",
         "Stew is food cooked slowly in a pot. It is usually warm, thick, and made from several ingredients mixed together."),
        ("Why can rain be a problem outside?",
         "Rain can wet things and make them colder or thinner. It can also make it harder to keep food and fire under control."),
        ("What is a flashback?",
         "A flashback is when a story briefly shows something that happened earlier. It helps a character remember an important lesson."),
        ("What does repetition mean?",
         "Repetition means doing something again and again. In a story, repetition can help a character get better at a task."),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in POTS:
        lines.append(asp.fact("pot", pid))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.id))
        lines.append(asp.fact("sense", pr.id, pr.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,R) :- setting(S), pot(P), problem(R), sense(R,N), N >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"FAIL: normal generation crashed: {e}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
        return 1
    print("OK: verification passed.")
    return 0


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [
            generate(StoryParams(setting="campsite", pot="kettle", problem="rain_thins", helper="cover",
                                 child1="Mina", child1_gender="girl", child2="Arlo", child2_gender="boy",
                                 parent="mother")),
            generate(StoryParams(setting="forest", pot="tinpot", problem="rain_dilutes", helper="stir",
                                 child1="Nora", child1_gender="girl", child2="Theo", child2_gender="boy",
                                 parent="father")),
        ]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
