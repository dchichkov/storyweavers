#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/breathe_conflict_cautionary_suspense_slice_of_life.py
=====================================================================================

A small storyworld built from the seed words:
- breathe
- Conflict
- Cautionary
- Suspense
- Slice of Life

Premise:
A child is helping in a normal home routine, notices something that feels urgent,
and a calm adult guides the situation toward safety. The story stays grounded in
ordinary details: a kitchen, a shared task, a small conflict, a cautious warning,
and a suspenseful moment that resolves into a quieter ending.

The world model tracks typed entities with physical meters and emotional memes.
The prose is driven by simulated state, not by swapping nouns in a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SAFETY_MIN = 2
WORRY_LIMIT = 1.0
STARTLED_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    routine: str
    mood: str
    afford: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    trigger: str
    object_word: str
    object_phrase: str
    danger: str
    cue: str
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
    action: str
    fail: str
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
    response: str
    child: str = "Mina"
    child_gender: str = "girl"
    parent: str = "mother"
    parent_gender: str = "girl"
    helper: str = "Theo"
    helper_gender: str = "boy"
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            attrs=dict(v.attrs), meters=defaultdict(float, dict(v.meters)),
            memes=defaultdict(float, dict(v.memes))
        ) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        routine="a normal after-school snack",
        mood="quiet and busy",
        afford={"tea", "snack"},
    ),
    "balcony": Setting(
        id="balcony",
        place="the balcony",
        routine="watering the plants",
        mood="bright and breezy",
        afford={"tea", "plants"},
    ),
    "laundry": Setting(
        id="laundry",
        place="the laundry room",
        routine="folding warm towels",
        mood="soft and humming",
        afford={"folding", "tea"},
    ),
}

PROBLEMS = {
    "steam": Problem(
        id="steam",
        trigger="the kettle hissed",
        object_word="kettle",
        object_phrase="the kettle",
        danger="the steam could sting a face",
        cue="a white puff",
        tags={"steam", "hot"},
    ),
    "spills": Problem(
        id="spills",
        trigger="the tray wobbled",
        object_word="tray",
        object_phrase="the tray of mugs",
        danger="the hot drinks could spill onto hands",
        cue="a shaky edge",
        tags={"spills", "hot"},
    ),
    "window": Problem(
        id="window",
        trigger="the window stuck",
        object_word="window",
        object_phrase="the sticky window",
        danger="the room could get stuffy and hard to breathe in",
        cue="thin air",
        tags={"window", "air"},
    ),
}

RESPONSES = {
    "step_back": Response(
        id="step_back",
        sense=3,
        power=3,
        action="stepped back and let the hot steam drift away",
        fail="stepped back, but the steam kept curling into the room",
        tags={"safe", "space"},
    ),
    "open_window": Response(
        id="open_window",
        sense=3,
        power=2,
        action="opened the window and let in fresh air",
        fail="opened the window, but the air still felt trapped",
        tags={"air", "safe"},
    ),
    "call_adult": Response(
        id="call_adult",
        sense=3,
        power=4,
        action="called a grown-up right away and waited still",
        fail="called a grown-up, but the delay let the trouble grow",
        tags={"safe", "help"},
    ),
    "hold_breath": Response(
        id="hold_breath",
        sense=1,
        power=0,
        action="held their breath and hoped for the best",
        fail="held their breath, but that did not solve anything",
        tags={"unsafe"},
    ),
}

NAME_POOL = ["Mina", "Luca", "Sana", "Jules", "Noah", "Ivy", "Tia", "Owen"]
TRAITS = ["careful", "curious", "gentle", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if not setting.afford:
                continue
            for rid, resp in RESPONSES.items():
                if resp.sense >= SAFETY_MIN:
                    combos.append((sid, pid, rid))
    return combos


def reason_bad_response(rid: str) -> str:
    resp = RESPONSES[rid]
    return f"(No story: response '{rid}' is too unwise for a cautionary slice-of-life story.)"


def reason_bad_combo(problem: Problem, setting: Setting) -> str:
    return f"(No story: {problem.id} does not fit {setting.place} in a grounded, plausible way.)"


def fire_response_gate(problem: Problem, response: Response) -> bool:
    if problem.id == "window":
        return response.id in {"open_window", "call_adult"}
    return response.id in {"step_back", "call_adult"}


def predict(world: World, response: Response) -> dict:
    sim = world.copy()
    child = sim.get("child")
    parent = sim.get("parent")
    problem = sim.facts["problem"]
    child.memes["worry"] += 1
    if response.id == "call_adult":
        parent.memes["alert"] += 1
    if problem.id == "window" and response.id == "hold_breath":
        sim.get("room").meters["stuffy"] += 1
    return {"stuffy": sim.get("room").meters["stuffy"], "worry": child.memes["worry"]}


def setup(world: World, child: Entity, helper: Entity, parent: Entity, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"It was a small ordinary afternoon in {world.setting.place}, the kind with "
        f"{world.setting.routine}. {world.setting.mood.capitalize()}."
    )
    world.say(
        f"{child.id} and {helper.id} were helping {parent.label_word} with a little chore "
        f"when {problem.trigger}."
    )


def conflict(world: World, child: Entity, problem: Problem) -> None:
    child.memes["stubborn"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{problem.cue} showed that something was off. {child.id} wanted to keep going, "
        f"but {problem.danger}."
    )


def caution(world: World, helper: Entity, child: Entity, parent: Entity, problem: Problem, response: Response) -> None:
    helper.memes["caution"] += 1
    pred = predict(world, response)
    world.facts["predicted"] = pred
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip and said, "
        f"'{child.id}, breathe slowly. {problem.danger.capitalize()}. We should not rush.'"
    )
    world.say(
        f"{parent.label_word.capitalize()} listened too, because {parent.pronoun()} could see "
        f"the trouble had a real edge to it."
    )


def turn(world: World, child: Entity, helper: Entity, response: Response, problem: Problem) -> bool:
    if not fire_response_gate(problem, response):
        return False
    child.memes["startled"] += 1
    world.say(
        f"{child.id} hesitated, then {response.action}."
    )
    if response.id == "hold_breath":
        world.say("That only made the moment feel tighter.")
    return True


def resolve(world: World, parent: Entity, response: Response, child: Entity) -> bool:
    if response.sense < SAFETY_MIN:
        return False
    if response.id == "call_adult":
        parent.memes["calm"] += 1
    if response.id == "open_window":
        world.get("room").meters["fresh_air"] += 1
    if response.id == "step_back":
        world.get("room").meters["space"] += 1
    world.say(
        f"{parent.label_word.capitalize()} took the safer part of the plan and the room settled down."
    )
    return True


def ending(world: World, child: Entity, helper: Entity, parent: Entity, problem: Problem, response: Response) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    parent.memes["relief"] += 1
    if problem.id == "window" and response.id == "open_window":
        world.say(
            f"Soon fresh air moved through the room. {child.id} could breathe again, and the "
            f"afternoon felt normal once more."
        )
    elif response.id == "call_adult":
        world.say(
            f"By the time everything was calm, {parent.label_word} had handled it without any fuss, "
            f"and {child.id} stood quietly beside {helper.id}."
        )
    else:
        world.say(
            f"After that, {child.id} and {helper.id} went back to their little chore, a bit more careful "
            f"than before."
        )


def tell(setting: Setting, problem: Problem, response: Response,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         parent_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent", label="the parent"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    world.facts["problem"] = problem
    world.facts["response"] = response

    setup(world, child, helper, parent, problem)
    world.para()
    conflict(world, child, problem)
    caution(world, helper, child, parent, problem, response)
    world.para()
    if turn(world, child, helper, response, problem):
        resolve(world, parent, response, child)
    ending(world, child, helper, parent, problem, response)
    world.facts.update(
        child=child, helper=helper, parent=parent, room=room,
        outcome="resolved" if response.sense >= SAFETY_MIN else "unwise",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the word "breathe" and a small '
        f'cautionary moment in {world.setting.place}.',
        f"Tell a quiet story where {f['child'].id} and {f['helper'].id} notice a problem, "
        f"pause, and choose a safer response instead of rushing.",
        f'Write a short story with conflict and suspense that ends calmly, using the word '
        f'"breathe" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    problem = f["problem"]
    response = f["response"]
    pred = f.get("predicted", {})
    qa = [
        QAItem(
            question=f"What was happening at the start of the story?",
            answer=(
                f"{child.id} and {helper.id} were helping with an ordinary chore in {world.setting.place}. "
                f"Then {problem.trigger}, which made the moment feel suddenly different."
            ),
        ),
        QAItem(
            question=f"Why did {helper.id} tell {child.id} to be careful?",
            answer=(
                f"{helper.id} could tell that {problem.danger}. {helper.id} wanted {child.id} to breathe "
                f"slowly and not make the trouble worse."
            ),
        ),
    ]
    if response.id == "open_window":
        qa.append(
            QAItem(
                question="How did the room change by the end?",
                answer=(
                    f"The room got fresher because the window was opened. That gave everyone space "
                    f"to breathe, and the uneasy feeling eased away."
                ),
            )
        )
    elif response.id == "call_adult":
        qa.append(
            QAItem(
                question="Why was calling a grown-up a good choice?",
                answer=(
                    f"Calling a grown-up brought someone who could handle the situation calmly. "
                    f"That kept the small problem from turning into a bigger one."
                ),
            )
        )
    else:
        qa.append(
            QAItem(
                question="What did the story show about the risky choice?",
                answer=(
                    f"It showed that holding a breath and hoping would not solve the problem. "
                    f"The warning was there for a reason, and the safer choice mattered."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | set(world.facts["response"].tags)
    items = []
    if "air" in tags:
        items.append(QAItem(
            question="Why do people need fresh air sometimes?",
            answer="Fresh air helps a room feel less stuffy, and breathing can feel easier when air can move around."
        ))
    if "steam" in tags:
        items.append(QAItem(
            question="What is steam?",
            answer="Steam is warm water vapor that floats up from something hot, like a kettle or a pot."
        ))
    if "safe" in tags:
        items.append(QAItem(
            question="What does a cautious person do?",
            answer="A cautious person slows down, notices danger, and chooses a safer way to handle the moment."
        ))
    items.append(QAItem(
        question="What should you do if something feels suddenly unsafe?",
        answer="Stop, breathe, and get help from a grown-up right away."
    ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def reason_valid_combo(setting: Setting, problem: Problem, response: Response) -> bool:
    return response.sense >= SAFETY_MIN and fire_response_gate(problem, response)


def explain_rejection(problem: Problem, response: Response) -> str:
    if response.sense < SAFETY_MIN:
        return reason_bad_response(response.id)
    return f"(No story: response '{response.id}' does not fit problem '{problem.id}' well enough.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SAFETY_MIN:
        raise StoryError(reason_bad_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, response = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        problem=problem,
        response=response,
        child=args.child or rng.choice(NAME_POOL),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        parent_gender=args.parent_gender or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice([n for n in NAME_POOL if n != (args.child or "")]),
        helper_gender=args.helper_gender or rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    response = RESPONSES[params.response]
    if not reason_valid_combo(setting, problem, response):
        raise StoryError(explain_rejection(problem, response))
    world = tell(
        setting=setting,
        problem=problem,
        response=response,
        child_name=params.child,
        child_gender=params.child_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_gender=params.parent_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S,P,R) :- setting(S), problem(P), response(R), sense(R,N), min_sense(M), N >= M.
helpful(R) :- response(R), sense(R,N), min_sense(M), N >= M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("min_sense", SAFETY_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, problem=None, response=None, child=None, child_gender=None,
            parent=None, parent_gender=None, helper=None, helper_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="kitchen", problem="steam", response="step_back", child="Mina", child_gender="girl", parent="mother", parent_gender="girl", helper="Theo", helper_gender="boy"),
    StoryParams(setting="balcony", problem="window", response="open_window", child="Luca", child_gender="boy", parent="father", parent_gender="boy", helper="Sana", helper_gender="girl"),
    StoryParams(setting="laundry", problem="spills", response="call_adult", child="Ivy", child_gender="girl", parent="mother", parent_gender="girl", helper="Owen", helper_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life cautionary storyworld with a breath, a conflict, and a safe turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--parent-gender", dest="parent_gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["girl", "boy"])
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
        print(asp_program("#show valid/3.\n#show helpful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
