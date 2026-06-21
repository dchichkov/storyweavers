#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/famous_tripod_teamwork_twist_slice_of_life.py
=============================================================================

A small slice-of-life storyworld about two children helping a neighborhood
photo day go right, with a famous tripod, a teamwork turn, and a gentle twist:
the "famous" tripod is not famous because it is fancy, but because everyone in
the room has used it for the best community pictures.

The world is built as a tiny causal simulation:
- typed entities with meters and memes
- a forward-chained rule engine
- a reasonableness gate
- a Python/ASP twin
- three Q&A sets grounded in world state

The story premise:
A child wants to use a famous tripod for a photo, but the tripod is wobbly and
the camera bag is heavy. A helper notices the problem, they work together to
stabilize the setup, and the twist is that the "famous" tripod turns out to be
famous because it has been in all the neighborhood memory photos. The ending is
a calm, warm slice-of-life image showing that teamwork changed the scene.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    is_object: bool = False
    is_tool: bool = False
    is_famous: bool = False
    unstable: bool = False
    heavy: bool = False
    supports_weight: bool = False

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
    scene: str
    time_word: str
    tone: str
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
    cause: str
    fix: str
    twist_line: str
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
class SupportAction:
    id: str
    label: str
    power: int
    text: str
    result: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    tripod = world.entities.get("tripod")
    camera = world.entities.get("camera")
    if not tripod or not camera:
        return out
    if tripod.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    camera.memes["nervous"] += 1
    for kid in world.characters():
        kid.memes["focus"] += 1
    out.append("__wobble__")
    return out


def _r_teamwork(world: World) -> list[str]:
    helper = world.entities.get("helper")
    photographer = world.entities.get("photographer")
    tripod = world.entities.get("tripod")
    if not helper or not photographer or not tripod:
        return []
    if helper.memes["help"] < THRESHOLD or photographer.memes["ask"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tripod.meters["stable"] += 1.5
    tripod.meters["wobble"] = max(0.0, tripod.meters["wobble"] - 1.5)
    photographer.memes["relief"] += 1
    helper.memes["pride"] += 1
    return ["__teamwork__"]


CAUSAL_RULES = [
    Rule("wobble", "physical", _r_wobble),
    Rule("teamwork", "social", _r_teamwork),
]


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


def need_is_reasonable(problem: Problem, setting: Setting) -> bool:
    return "tripod" in setting.tags and "photo" in problem.tags


def fix_is_reasonable(action: SupportAction, problem: Problem) -> bool:
    return action.power >= 2 and "stability" in action.tags and "photo" in problem.tags


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for aid, action in ACTIONS.items():
                if need_is_reasonable(problem, setting) and fix_is_reasonable(action, problem):
                    out.append((sid, pid, aid))
    return out


def predict_tripod(world: World) -> dict:
    sim = world.copy()
    if "tripod" in sim.entities:
        sim.get("tripod").meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("tripod").meters["wobble"] if "tripod" in sim.entities else 0.0,
        "relief": sim.get("photographer").memes["relief"] if "photographer" in sim.entities else 0.0,
    }


def setup(world: World, setting: Setting, child: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"On a slow afternoon at {setting.place}, {child.id} and {helper.id} "
        f"were helping set up for the neighborhood photo."
    )
    world.say(
        f"The room felt {setting.tone}, with {setting.scene} and the easy hum of "
        f"people waiting for their turn."
    )
    world.say(
        f"{child.id} had brought a famous tripod. Everyone said it was famous "
        f"because it had been in so many happy pictures."
    )


def notice(world: World, photographer: Entity, problem: Problem) -> None:
    photographer.memes["ask"] += 1
    world.say(
        f"{photographer.id} looked at the famous tripod and noticed a small wobble. "
        f"The camera tilted a little each time someone brushed past the table."
    )
    world.say(
        f'"{problem.cause}," {photographer.id} said softly. '
        f'"We need to keep it steady before we start."'
    )


def offer_help(world: World, helper: Entity, photographer: Entity, action: SupportAction) -> None:
    helper.memes["help"] += 1
    world.say(
        f'{helper.id} smiled and said, "{action.text}." '
        f"{photographer.id} nodded, glad not to handle it alone."
    )


def do_teamwork(world: World, helper: Entity, photographer: Entity, action: SupportAction, problem: Problem) -> None:
    world.get("tripod").meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they did it slowly: {action.result}. {action.label.capitalize()} "
        f"turned a shaky moment into a calmer one."
    )


def twist(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then came the twist. A neighbor pointed to a frame on the wall and said "
        f"the tripod was famous because it had stood in the very first photo of the "
        f"street fair, years ago."
    )
    world.say(
        f"{child.id} laughed, because the famous part was not about being fancy at all; "
        f"it was about helping people remember one another."
    )


def ending(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"At last, the camera stood straight. {child.id} and {helper.id} lined up "
        f"the chairs, and the next family smiled for the picture."
    )
    world.say(
        f"By the time the sun slid lower, the famous tripod sat steady and proud, "
        f"while the little room at {setting.place} felt warm with ordinary, good work."
    )


def tell(setting: Setting, problem: Problem, action: SupportAction,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Owen", helper_gender: str = "boy",
         photographer_name: str = "Rae", photographer_gender: str = "adult",
         seed_label: str = "") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        traits=["kind"], attrs={"seed": seed_label}
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=["patient"], attrs={"seed": seed_label}
    ))
    photographer = world.add(Entity(
        id=photographer_name, kind="character", type=photographer_gender, role="photographer",
        traits=["careful"], attrs={"seed": seed_label}
    ))
    tripod = world.add(Entity(
        id="tripod", type="tool", label="tripod", is_tool=True, is_object=True,
        is_famous=True, unstable=True
    ))
    camera = world.add(Entity(
        id="camera", type="tool", label="camera", is_tool=True, is_object=True
    ))
    tripod.meters["wobble"] = 1.0
    child.memes["care"] += 1
    helper.memes["care"] += 1

    setup(world, setting, child, helper, problem)
    world.para()
    notice(world, photographer, problem)
    offer_help(world, helper, photographer, action)
    do_teamwork(world, helper, photographer, action, problem)
    world.para()
    twist(world, child, helper, problem)
    ending(world, child, helper, setting)

    world.facts.update(
        setting=setting, problem=problem, action=action,
        child=child, helper=helper, photographer=photographer,
        tripod=tripod, camera=camera,
        resolved=tripod.meters["wobble"] < 1.0,
        famous=True,
        teamwork=True,
        twist=True,
    )
    return world


SETTINGS = {
    "community_center": Setting(
        id="community_center",
        place="the community center",
        scene="folding chairs, a paper banner, and a tray of orange slices",
        time_word="afternoon",
        tone="quiet and cheerful",
        tags={"tripod", "photo", "slice"},
    ),
    "bookstore": Setting(
        id="bookstore",
        place="the little bookstore",
        scene="rows of books, a poster board, and a table by the window",
        time_word="morning",
        tone="soft and busy",
        tags={"tripod", "photo", "slice"},
    ),
    "apartment_hall": Setting(
        id="apartment_hall",
        place="the apartment hall",
        scene="shoes by the wall, a borrowed lamp, and a small table of cookies",
        time_word="late afternoon",
        tone="warm and close",
        tags={"tripod", "photo", "slice"},
    ),
}

PROBLEMS = {
    "wobble": Problem(
        id="wobble",
        label="small wobble",
        cause="the tripod kept wobbling when people walked by",
        fix="steady hands and a careful pause",
        twist_line="famous because it helped families remember one another",
        tags={"photo", "tripod", "twist"},
    ),
}

ACTIONS = {
    "brace": SupportAction(
        id="brace",
        label="teamwork",
        power=2,
        text="Let's hold the legs together for a second",
        result="one child held the tripod while the other tightened the latch",
        tags={"stability", "photo"},
    ),
    "sandbag": SupportAction(
        id="sandbag",
        label="teamwork",
        power=3,
        text="I can put this heavy bag near the base",
        result="they set a weighted bag at the base and checked each corner",
        tags={"stability", "photo"},
    ),
}

NAMES_GIRL = ["Mina", "Nia", "Lena", "Tess", "Maya", "Rosa"]
NAMES_BOY = ["Owen", "Eli", "Noah", "Theo", "Finn", "Jace"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    action: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    photographer_name: str
    photographer_gender: str
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
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a famous tripod and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--photographer-name")
    ap.add_argument("--photographer-gender", choices=["girl", "boy", "adult"])
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


def reasonable_problem(setting: Setting, problem: Problem) -> bool:
    return "tripod" in setting.tags and "photo" in problem.tags


def reasonable_action(action: SupportAction, problem: Problem) -> bool:
    return action.power >= 2 and "stability" in action.tags and "photo" in problem.tags


def explain_rejection(setting: Setting, problem: Problem, action: SupportAction) -> str:
    if not reasonable_problem(setting, problem):
        return "(No story: the setting and problem do not naturally support a tripod photo scene.)"
    if not reasonable_action(action, problem):
        return "(No story: that action does not really steady a wobbly tripod.)"
    return "(No story: this combination is not reasonable.)"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return [(s, p, a) for s in SETTINGS for p in PROBLEMS for a in ACTIONS
            if reasonable_problem(SETTINGS[s], PROBLEMS[p]) and reasonable_action(ACTIONS[a], PROBLEMS[p])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "famous" and "tripod" and shows teamwork.',
        f"Tell a calm community story where {f['child'].id} and {f['helper'].id} help steady a famous tripod.",
        f"Write a gentle story with a small twist: the tripod is famous for memory and kindness, not for glamour.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, photographer = f["child"], f["helper"], f["photographer"]
    action, setting, problem = f["action"], f["setting"], f["problem"]
    qa = [
        ("Who helped with the tripod?",
         f"{child.id} and {helper.id} helped {photographer.id}, and they worked together to steady the famous tripod."),
        ("What was the problem?",
         f"The tripod had a small wobble, so the camera tilted when people walked by. They needed steady hands and a careful fix."),
        ("Why was the tripod famous?",
         f"It was famous because it had been in so many neighborhood photos. The twist was that people loved it for the memories it held."),
        ("How did teamwork help?",
         f"{action.result.capitalize()}. That teamwork made the tripod steady enough for the next picture."),
    ]
    if f.get("resolved"):
        qa.append(("How did the story end?",
                   f"It ended calmly, with the tripod steady and the next family ready for their photo. The room felt warm and ordinary again."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a tripod?",
         "A tripod is a three-legged stand that helps hold a camera still. It keeps pictures from looking shaky."),
        ("What does teamwork mean?",
         "Teamwork means people help each other and do a job together. Each person does a small part so the whole thing works better."),
        ("What is a twist in a story?",
         "A twist is a surprise turn that changes how you understand something. It makes the story feel a little unexpected."),
    ]
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
        if e.is_famous:
            bits.append("famous=True")
        if e.unstable:
            bits.append("unstable=True")
        if e.is_tool:
            bits.append("tool=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
wobble_needed :- problem(wobble).
teamwork_fix :- action(brace).
teamwork_fix :- action(sandbag).
valid(S,P,A) :- setting(S), problem(P), action(A), wobble_needed, teamwork_fix.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_story_combos()):
        print(f"OK: ASP matches valid_story_combos() ({len(valid_story_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, action=None, child_name=None, child_gender=None, helper_name=None, helper_gender=None, photographer_name=None, photographer_gender=None, n=1, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    action = args.action or rng.choice(sorted(ACTIONS))
    if not reasonable_problem(SETTINGS[setting], PROBLEMS[problem]) or not reasonable_action(ACTIONS[action], PROBLEMS[problem]):
        raise StoryError(explain_rejection(SETTINGS[setting], PROBLEMS[problem], ACTIONS[action]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    photographer_gender = args.photographer_gender or "adult"
    child_name = args.child_name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice([n for n in (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY) if n != child_name])
    photographer_name = args.photographer_name or "Rae"
    return StoryParams(
        setting=setting,
        problem=problem,
        action=action,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        photographer_name=photographer_name,
        photographer_gender=photographer_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key in ("setting", "problem", "action"):
        if key not in params.__dict__:
            raise StoryError(f"Invalid params: missing {key}.")
    setting = SETTINGS.get(params.setting)
    problem = PROBLEMS.get(params.problem)
    action = ACTIONS.get(params.action)
    if setting is None or problem is None or action is None:
        raise StoryError("Invalid params: unknown setting, problem, or action.")
    world = tell(setting, problem, action,
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 photographer_name=params.photographer_name, photographer_gender=params.photographer_gender,
                 seed_label=str(params.seed or ""))
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, p, a in combos:
            print(f"  {s:16} {p:8} {a}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="community_center", problem="wobble", action="brace",
                        child_name="Mina", child_gender="girl", helper_name="Owen", helper_gender="boy",
                        photographer_name="Rae", photographer_gender="adult"),
            StoryParams(setting="bookstore", problem="wobble", action="sandbag",
                        child_name="Lena", child_gender="girl", helper_name="Theo", helper_gender="boy",
                        photographer_name="Rae", photographer_gender="adult"),
        ]
        samples = [generate(p) for p in curated]
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
