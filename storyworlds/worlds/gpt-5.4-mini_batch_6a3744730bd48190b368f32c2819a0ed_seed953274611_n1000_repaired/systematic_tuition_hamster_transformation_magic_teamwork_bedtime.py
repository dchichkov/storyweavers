#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/systematic_tuition_hamster_transformation_magic_teamwork_bedtime.py
===================================================================================================

A small bedtime-story world about a child, a hamster, a careful tuition-saving
plan, and a little bit of magic teamwork that transforms a bedtime worry into a
gentle new routine.

The world is deliberately tiny: one child wants a hamster at bedtime, the parent
worries about tuition money, and the story turns on whether the child and parent
work together, make a systematic plan, and use magic only in the storybook sense
of warm, cozy imagination. The transformation is physical and emotional: a
plain bedtime becomes a calm shared routine, and if the chosen route allows it,
the hamster becomes part of the home in a safe, realistic way.

This file is standalone and uses only the standard library plus the shared
storyworld result containers. ASP is imported lazily inside helper functions.
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
    can_transform: bool = False
    magical: bool = False
    cooperative: bool = False

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
    bedtime: str
    quiet: str
    cozy: str
    bed: str
    table: str
    shelf: str
    window: str
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
class Desire:
    id: str
    want: str
    keyword: str
    bedtime_need: str
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
class Plan:
    id: str
    title: str
    steps: list[str] = field(default_factory=list)
    power: int = 0
    sense: int = 0
    magic: bool = False
    teamwork: bool = False
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
class Transformation:
    id: str
    from_state: str
    to_state: str
    text: str
    proof: str
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
        c.facts = dict(self.facts)
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


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["worry"] >= THRESHOLD and parent.memes["worry"] >= THRESHOLD:
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["settled"] += 1
            parent.memes["settled"] += 1
            out.append("__settle__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hamster = world.get("hamster")
    if child.memes["care"] >= THRESHOLD and hamster.meters["safe_home"] >= THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            hamster.can_transform = True
            hamster.meters["changed"] += 1
            child.memes["joy"] += 1
            out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("settle", _r_settle), Rule("transform", _r_transform)]


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


def reasonableness_ok(desire: Desire, plan: Plan, transformation: Transformation) -> bool:
    return desire.keyword in desire.tags and plan.sense >= SENSE_MIN and (
        (plan.magic and transformation.id == "soft_light") or transformation.id == "hamster_home"
    )


def applicable_plan(plan: Plan) -> bool:
    return plan.sense >= SENSE_MIN


def resolve_home(desire: Desire, plan: Plan) -> bool:
    return desire.keyword == "hamster" and plan.magic and plan.teamwork


def predict_transition(world: World) -> dict:
    sim = world.copy()
    _do_bedtime_story(sim, narrate=False)
    return {
        "settled": sim.get("child").memes["settled"] >= THRESHOLD,
        "changed": sim.get("hamster").meters["changed"] >= THRESHOLD,
    }


def _do_bedtime_story(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    parent = world.get("parent")
    hamster = world.get("hamster")
    setting = world.facts["setting"]
    desire = world.facts["desire"]
    plan = world.facts["plan"]
    transform = world.facts["transformation"]

    child.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.say(f"It was bedtime in {setting.place}, and the room was quiet as a whisper.")
    world.say(
        f"{child.id} tucked {child.pronoun('possessive')} chin into the blanket and said, "
        f'"I want a hamster," because {desire.bedtime_need}.'
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled softly, but {parent.pronoun()} reminded "
        f"{child.pronoun('object')} that tuition came first, and the money had to be handled systematically."
    )
    world.para()
    child.memes["want"] += 1
    parent.memes["concern"] += 1
    world.say(
        f"Then they made a plan together: {', '.join(plan.steps)}. "
        f"It felt like magic to make a hard thing simple."
    )
    child.memes["care"] += 1
    parent.memes["care"] += 1
    parent.meters["tuition_savings"] += 1
    if resolve_home(desire, plan):
        hamster.meters["safe_home"] += 1
        world.say(
            f"The tiny idea changed shape. Instead of a rushed wish, it became a gentle promise: "
            f"save carefully, share the chores, and bring a hamster home only when the timing was right."
        )
        world.say(
            f"{transform.text} {transform.proof}."
        )
    else:
        world.say(
            f"The wish stayed a wish for now, but it no longer felt sad. "
            f"They kept the note on the lamp, and bedtime ended with a calm plan for tomorrow."
        )
    propagate(world, narrate=narrate)
    world.say(
        f"At the end, the blanket was still warm, the room was still quiet, and {child.id} "
        f"fell asleep thinking about the little future that teamwork could build."
    )


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        bedtime="bedtime",
        quiet="soft",
        cozy="cozy",
        bed="the little bed",
        table="the nightstand",
        shelf="the toy shelf",
        window="the moonlit window",
    ),
    "attic_room": Setting(
        id="attic_room",
        place="the attic room",
        bedtime="bedtime",
        quiet="hushed",
        cozy="snug",
        bed="the pillow nest",
        table="the small desk",
        shelf="the book shelf",
        window="the round window",
    ),
    "tiny_apartment": Setting(
        id="tiny_apartment",
        place="the tiny apartment",
        bedtime="bedtime",
        quiet="gentle",
        cozy="warm",
        bed="the sofa bed",
        table="the lamp table",
        shelf="the basket shelf",
        window="the narrow window",
    ),
}

DESIRES = {
    "hamster": Desire(
        id="hamster",
        want="a hamster",
        keyword="hamster",
        bedtime_need="it would be fluffy and tiny and could ride in a little wheel",
        tags={"hamster", "bedtime"},
    ),
    "soft_toy": Desire(
        id="soft_toy",
        want="a soft toy",
        keyword="hamster",
        bedtime_need="it would feel new and special under the blanket",
        tags={"hamster", "bedtime"},
    ),
}

PLANS = {
    "systematic_piggy_bank": Plan(
        id="systematic_piggy_bank",
        title="a systematic saving plan",
        steps=["make a list of chores", "put coins in a jar each day", "count the savings together"],
        power=3,
        sense=3,
        magic=False,
        teamwork=True,
        tags={"systematic", "tuition", "teamwork"},
    ),
    "magic_stars": Plan(
        id="magic_stars",
        title="a magic star map",
        steps=["draw a star map", "wish kindly together", "save a little each week"],
        power=2,
        sense=2,
        magic=True,
        teamwork=True,
        tags={"magic", "teamwork", "systematic"},
    ),
    "quiet_note": Plan(
        id="quiet_note",
        title="a quiet bedtime note",
        steps=["write the tuition reminder", "promise to help", "sleep on the idea"],
        power=2,
        sense=2,
        magic=False,
        teamwork=True,
        tags={"tuition", "teamwork"},
    ),
}

TRANSFORMATIONS = {
    "hamster_home": Transformation(
        id="hamster_home",
        from_state="plain bedtime",
        to_state="shared bedtime",
        text="The plain bedtime turned into a shared one",
        proof="because the child and parent built a careful home for the hamster",
        tags={"hamster", "teamwork", "systematic"},
    ),
    "soft_light": Transformation(
        id="soft_light",
        from_state="worry",
        to_state="calm",
        text="The worry turned into a soft calm",
        proof="because the plan was small, kind, and easy to keep",
        tags={"magic", "tuition", "teamwork"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    desire: str
    plan: str
    transformation: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
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


CURATED = [
    StoryParams(
        setting="nursery",
        desire="hamster",
        plan="systematic_piggy_bank",
        transformation="hamster_home",
        child_name="Mina",
        child_gender="girl",
        parent_name="Mom",
        parent_gender="mother",
    ),
    StoryParams(
        setting="attic_room",
        desire="hamster",
        plan="magic_stars",
        transformation="soft_light",
        child_name="Theo",
        child_gender="boy",
        parent_name="Dad",
        parent_gender="father",
    ),
    StoryParams(
        setting="tiny_apartment",
        desire="soft_toy",
        plan="quiet_note",
        transformation="hamster_home",
        child_name="Luna",
        child_gender="girl",
        parent_name="Mom",
        parent_gender="mother",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DESIRES:
            for p in PLANS:
                for t in TRANSFORMATIONS:
                    if reasonableness_ok(DESIRES[d], PLANS[p], TRANSFORMATIONS[t]):
                        combos.append((s, d, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: hamster, tuition, teamwork, and a little magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--desire", choices=DESIRES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError("The chosen plan is too weak for this bedtime world.")
    choices = [c for c in valid_combos()
               if args.setting in (None, c[0])
               and args.desire in (None, c[1])
               and args.plan in (None, c[2])]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, desire, plan = rng.choice(sorted(choices))
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    return StoryParams(
        setting=setting,
        desire=desire,
        plan=plan,
        transformation=transformation,
        child_name=args.child_name or rng.choice(["Mina", "Theo", "Luna", "Kai", "Nora", "Eli"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        parent_name=args.parent_name or rng.choice(["Mom", "Dad"]),
        parent_gender=args.parent_gender or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.desire not in DESIRES or params.plan not in PLANS or params.transformation not in TRANSFORMATIONS:
        raise StoryError("Invalid params for this storyworld.")
    if not reasonableness_ok(DESIRES[params.desire], PLANS[params.plan], TRANSFORMATIONS[params.transformation]):
        raise StoryError("The chosen combination does not make a reasonable bedtime story.")
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent"))
    hamster = world.add(Entity(id="hamster", kind="character", type="thing", label="hamster", role="pet", magical=True))
    world.facts["setting"] = SETTINGS[params.setting]
    world.facts["desire"] = DESIRES[params.desire]
    world.facts["plan"] = PLANS[params.plan]
    world.facts["transformation"] = TRANSFORMATIONS[params.transformation]
    _do_bedtime_story(world, narrate=True)
    story = world.render()
    prompts = generation_prompts(world)
    story_qa = [QAItem(question=q, answer=a) for q, a in story_qa_items(world)]
    world_qa = [QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story about a child who wants a hamster, but tuition comes first and the family makes a systematic plan.",
        f"Tell a gentle story where {f['setting'].place} is quiet, a child asks for a hamster, and teamwork turns worry into calm.",
        f"Write a cozy story with the words systematic, tuition, and hamster, ending with a magical-feeling family plan.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s = f["setting"]
    d = f["desire"]
    p = f["plan"]
    t = f["transformation"]
    child = world.get("child")
    parent = world.get("parent")
    hamster = world.get("hamster")
    return [
        ("What did the child want at bedtime?",
         f"{child.id} wanted {d.want}. The wish came out in the quiet of bedtime, when everything felt bigger and softer."),
        ("Why did the parent mention tuition?",
         f"{parent.id} wanted to keep tuition money safe first. The parent explained that the family needed a systematic plan before bringing a hamster home."),
        ("How did the child and parent solve the problem?",
         f"They worked together and followed {p.title}. That teamwork made the wish feel possible without being rushed."),
        ("What changed by the end of the story?",
         f"{t.text} {t.proof}. The hamster was no longer just a wish; it belonged in a safe, shared home."),
        ("Why did the story feel magical?",
         f"The magic was in how the room and the feelings changed. A worry turned gentle because the child and parent made a kind plan together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is tuition?",
         "Tuition is money paid for school or lessons. Families usually save for it carefully."),
        ("What is a hamster?",
         "A hamster is a small furry pet that likes wheels, nests, and tiny snacks."),
        ("What does systematic mean?",
         "Systematic means done in a careful order, step by step, so nothing is forgotten."),
        ("What does teamwork mean?",
         "Teamwork means people work together and help each other. It is easier to do hard things that way."),
        ("What is a transformation?",
         "A transformation is when something changes into a new form or feeling."),
        ("What is magic in a bedtime story?",
         "Magic can mean a wonderful change that feels bright and surprising, like a wish becoming calm and real."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(P) :- plan(P), sense(P,S), sense_min(M), S >= M.
valid(S,D,P) :- setting(S), desire(D), plan(P), sensible(P).
happy(S,D,P) :- valid(S,D,P), desire_keyword(D,"hamster").
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DESIRES.items():
        lines.append(asp.fact("desire", did))
        lines.append(asp.fact("desire_keyword", did, d.keyword))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def explain_rejection() -> str:
    return "(No story: this bedtime world needs a reasonable hamster plan with teamwork and enough sense.)"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, desire, plan) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
