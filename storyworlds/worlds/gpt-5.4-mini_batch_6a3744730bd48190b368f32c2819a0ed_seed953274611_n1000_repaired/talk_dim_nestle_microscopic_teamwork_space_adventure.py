#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/talk_dim_nestle_microscopic_teamwork_space_adventure.py
======================================================================================

A tiny space-adventure storyworld about a repair team inside a ship's
microscopic maintenance bay. The seed words are folded into the world model:

- talk-dim: the comms are too quiet to rely on
- nestle: a tiny part must be seated into a snug socket
- microscopic: the problem is very small but important
- teamwork: two helpers must cooperate to solve it

The simulation is built from typed entities with physical meters and emotional
memes, a forward causal model, a reasonableness gate, and an inline ASP twin.
Stories are child-facing, state-driven, and end with a clear changed image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"focus": 0.0, "damage": 0.0, "brightness": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "worry": 0.0, "trust": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
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


@dataclass
class CrewRole:
    id: str
    title: str
    gender: str
    traits: set[str] = field(default_factory=set)
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
class Device:
    id: str
    label: str
    kind: str
    needs: set[str] = field(default_factory=set)
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
    tiny: bool
    risky: bool
    fixable: bool
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
    ship: str
    crew1: str
    crew1_gender: str
    crew2: str
    crew2_gender: str
    captain: str
    device: str
    problem: str
    response: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("damage", 0.0) < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("bay").meters["dust"] += 1
        for eid in ("crew1", "crew2"):
            if eid in world.entities:
                world.get(eid).memes["worry"] += 1
        out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


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


def hazard_at_risk(problem: Problem, device: Device) -> bool:
    return problem.fixable and "nestle" in device.needs


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(problem: Problem) -> int:
    return 2 if problem.risky else 1


def is_contained(response: Response, problem: Problem) -> bool:
    return response.power >= fire_severity(problem)


SENSE_MIN = 2


SHIP_TYPES = {
    "skylark": "the Skylark",
    "comet": "the Comet",
    "orbit": "the Orbit",
}

CREW = {
    "mina": CrewRole("mina", "navigator", "girl", {"careful", "brave"}),
    "taro": CrewRole("taro", "engineer", "boy", {"gentle", "clever"}),
    "zoe": CrewRole("zoe", "pilot", "girl", {"quick", "kind"}),
    "pax": CrewRole("pax", "technician", "boy", {"patient", "steady"}),
}

DEVICES = {
    "microchip": Device("microchip", "microscopic control chip", "part", needs={"nestle"}, tags={"microscopic", "nestle"}),
    "lens": Device("lens", "tiny lens", "part", needs={"nestle"}, tags={"microscopic"}),
    "bolt": Device("bolt", "little bolt", "part", needs={"nestle"}, tags={"microscopic"}),
}

PROBLEMS = {
    "loose_chip": Problem("loose_chip", "a microscopic chip that had slipped loose", tiny=True, risky=True, fixable=True, tags={"microscopic"}),
    "dim_comms": Problem("dim_comms", "the talk-dim comms panel that blinked too softly", tiny=True, risky=True, fixable=True, tags={"talk-dim"}),
    "dusty_slot": Problem("dusty_slot", "a microscopic dusty slot near the map screen", tiny=True, risky=False, fixable=True, tags={"microscopic"}),
}

RESPONSES = {
    "steady_hands": Response("steady_hands", 3, 3,
                             "used steady hands to guide the part into its snug little socket",
                             "tried to guide the part in, but it wobbled right back out",
                             "guided the part into its snug little socket",
                             tags={"nestle", "teamwork"}),
    "glove_pair": Response("glove_pair", 3, 2,
                           "worked together with soft gloves to nestle the part in place",
                           "worked with the gloves, but the fix was too weak and the part slipped",
                           "worked together and nestle'd the part in place",
                           tags={"nestle", "teamwork"}),
    "signal_boost": Response("signal_boost", 2, 2,
                             "boosted the signal with a spare relay while one crewmate held the part steady",
                             "boosted the signal, but the panel stayed too dim to trust",
                             "boosted the signal while holding the part steady",
                             tags={"talk-dim", "teamwork"}),
}

SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Zoe", "Aria", "Nia", "Lina", "Ivy"]
BOY_NAMES = ["Taro", "Pax", "Leo", "Milo", "Eli", "Oren"]
TRAITS = ["careful", "gentle", "patient", "clever", "steady", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIP_TYPES:
        for device in DEVICES:
            for problem in PROBLEMS:
                if hazard_at_risk(PROBLEMS[problem], DEVICES[device]):
                    combos.append((ship, device, problem))
    return combos


def explain_rejection(problem: Problem, device: Device) -> str:
    if not problem.fixable:
        return "(No story: that problem cannot be fixed in this tiny world.)"
    return f"(No story: {device.label} does not need to nestle into anything, so it cannot solve this problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def predict_fix(world: World, response: Response, problem: Problem) -> dict:
    sim = world.copy()
    sim.get("problem").meters["damage"] += 1
    return {"contained": is_contained(response, problem), "dust": sim.get("bay").meters["dust"]}


def setup(world: World, ship: str, crew1: Entity, crew2: Entity, captain: Entity) -> None:
    crew1.memes["trust"] += 1
    crew2.memes["trust"] += 1
    world.say(f"On the {SHIP_TYPES[ship]}, {crew1.id} and {crew2.id} worked under the soft blue lights of the maintenance bay.")
    world.say("It was a microscopic job, but the ship still needed it done.")


def describe_problem(world: World, problem: Problem, device: Device) -> None:
    world.say(f"The trouble was {problem.label}, and the talk-dim comms made the little warning beep hard to hear.")
    world.say(f"{device.label.capitalize()} was the thing that had to nestle back into place.")


def teamwork_move(world: World, crew1: Entity, crew2: Entity, response: Response, device: Device) -> None:
    crew1.memes["calm"] += 1
    crew2.memes["calm"] += 1
    world.say(f'"Let me hold it," {crew1.id} said, and {crew2.id} nodded at once.')
    world.say(f'Together they {response.text.replace("{device}", device.label)}.')


def damage_start(world: World, problem: Problem) -> None:
    world.get("problem").meters["damage"] += 1
    propagate(world, narrate=False)
    world.say(f"The tiny part slipped and the panel flickered.")
    world.say("A little warning light blinked red across the bay.")


def rescue(world: World, captain: Entity, response: Response, device: Device, problem: Problem) -> None:
    world.get("problem").meters["damage"] = 0.0
    world.get("bay").meters["dust"] = 0.0
    world.say(f"The captain came in fast and {response.text.replace('{device}', device.label)}.")
    world.say(f"After that, the {problem.label} was quiet again, and the ship's lights shone steady.")


def rescue_fail(world: World, captain: Entity, response: Response, device: Device, problem: Problem) -> None:
    world.get("bay").meters["dust"] += 1
    world.say(f"The captain tried to help, but {response.fail.replace('{device}', device.label)}.")
    world.say("The bay stayed dim, and the tiny repair had to be abandoned for the moment.")


def ending(world: World, crew1: Entity, crew2: Entity) -> None:
    crew1.memes["joy"] += 1
    crew2.memes["joy"] += 1
    world.say(f"In the end, {crew1.id} and {crew2.id} smiled at the tiny, fixed panel.")
    world.say("The microscopic repair had taken teamwork, and the ship glowed brighter for it.")


def tell(params: StoryParams) -> World:
    world = World()
    crew1 = world.add(Entity(id=params.crew1, kind="character", type=params.crew1_gender, role="helper"))
    crew2 = world.add(Entity(id=params.crew2, kind="character", type=params.crew2_gender, role="helper"))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain, role="leader"))
    bay = world.add(Entity(id="bay", type="room", label="maintenance bay"))
    problem = world.add(Entity(id="problem", type="problem", label=PROBLEMS[params.problem].label))
    device = DEVICES[params.device]

    setup(world, params.ship, crew1, crew2, captain)
    world.para()
    describe_problem(world, PROBLEMS[params.problem], device)
    teamwork_move(world, crew1, crew2, RESPONSES[params.response], device)
    damage_start(world, PROBLEMS[params.problem])

    if is_contained(RESPONSES[params.response], PROBLEMS[params.problem]):
        world.para()
        rescue(world, captain, RESPONSES[params.response], device, PROBLEMS[params.problem])
        ending(world, crew1, crew2)
        outcome = "contained"
    else:
        world.para()
        rescue_fail(world, captain, RESPONSES[params.response], device, PROBLEMS[params.problem])
        world.say("They promised to return with better tools and try again together.")
        outcome = "failed"

    world.facts.update(
        ship=params.ship,
        crew1=crew1,
        crew2=crew2,
        captain=captain,
        device=device,
        problem_cfg=PROBLEMS[params.problem],
        problem=problem,
        response=RESPONSES[params.response],
        outcome=outcome,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tiny space-adventure story for a child that uses the words "talk-dim", "nestle", and "microscopic".',
        f"Tell a teamwork story on the {SHIP_TYPES[f['ship']]} where {f['crew1'].id} and {f['crew2'].id} fix a {f['problem_cfg'].label} with a calm helper.",
        "Write a child-facing repair story where two crewmates cooperate to fit one tiny part into its place and make the ship brighter again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1, c2 = f["crew1"], f["crew2"]
    problem = f["problem_cfg"]
    device = f["device"]
    qa = [
        ("Who worked together in the story?", f"{c1.id} and {c2.id} worked together, and the captain watched them fix the ship."),
        ("What made the job hard to hear or see?", "The talk-dim comms were very soft, so the crew could not rely on them much. That is why they had to use teamwork and pay close attention to the tiny repair."),
        ("What had to be put back in place?", f"{device.label.capitalize()} had to nestle back into its snug socket. It was microscopic, so the crew needed careful hands."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the crew solve the problem?",
            f"They held the part steady and used teamwork until it fit. That let the {problem.label} settle down, and the ship's lights became bright again."
        ))
        qa.append((
            "How did the ending show the change?",
            "The bay went from blinking red to shining steady. The final image proves the tiny repair worked."
        ))
    else:
        qa.append((
            "Did the repair work?",
            "No. They tried hard, but the fix was not strong enough, so the part slipped again. The crew had to leave the bay dim for a while."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["device"].tags) | set(world.facts["problem_cfg"].tags)
    tags |= {"teamwork"}
    out: list[tuple[str, str]] = []
    if "microscopic" in tags:
        out.append(("What does microscopic mean?", "Microscopic means very, very small, almost too small to see without care. Tiny things like that still matter if they help a ship work right."))
    if "nestle" in tags:
        out.append(("What does nestle mean?", "To nestle means to fit something snugly into a safe, close place. The object feels settled and supported when it nestles in."))
    if "talk-dim" in tags:
        out.append(("What does talk-dim mean in this story?", "Talk-dim means the communication was too quiet and weak to depend on. The crew had to use their own eyes, hands, and teamwork instead."))
    if "teamwork" in tags:
        out.append(("Why is teamwork helpful?", "Teamwork is helpful because different helpers can do different jobs at once. One can hold steady while another fits the tiny part into place."))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, D) :- problem(P), device(D), fixable(P), needs(D, nestle).
valid(S, D, P) :- ship(S), device(D), problem(P), hazard(P, D).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
outcome(contained) :- chosen_problem(P), chosen_response(R), response(R), problem(P), fixable(P), power(R, Pow), severity(P, Sev), Pow >= Sev.
outcome(failed) :- chosen_problem(P), chosen_response(R), response(R), problem(P), fixable(P), power(R, Pow), severity(P, Sev), Pow < Sev.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHIP_TYPES:
        lines.append(asp.fact("ship", sid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        for n in sorted(d.needs):
            lines.append(asp.fact("needs", did, n))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("fixable", pid))
        lines.append(asp.fact("severity", pid, fire_severity(p)))
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


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
        sample = generate(resolve_params(argparse.Namespace(ship=None, crew1=None, crew1_gender=None, crew2=None, crew2_gender=None, captain=None, device=None, problem=None, response=None), random.Random(777)))  # type: ignore[arg-type]
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space-adventure teamwork storyworld.")
    ap.add_argument("--ship", choices=SHIP_TYPES)
    ap.add_argument("--crew1", choices=sorted(CREW))
    ap.add_argument("--crew1-gender", choices=["girl", "boy"])
    ap.add_argument("--crew2", choices=sorted(CREW))
    ap.add_argument("--crew2-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["Nova", "Orion", "Sky", "Rhea"])
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.device and args.problem:
        if not hazard_at_risk(PROBLEMS[args.problem], DEVICES[args.device]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], DEVICES[args.device]))
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.device is None or c[1] == args.device)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, device, problem = rng.choice(sorted(combos))
    crew1 = args.crew1 or rng.choice(sorted(CREW))
    crew2 = args.crew2 or rng.choice([c for c in sorted(CREW) if c != crew1])
    c1g = args.crew1_gender or CREW[crew1].gender
    c2g = args.crew2_gender or CREW[crew2].gender
    captain = args.captain or rng.choice(["Nova", "Orion", "Sky", "Rhea"])
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(ship=ship, crew1=crew1, crew1_gender=c1g, crew2=crew2, crew2_gender=c2g, captain=captain, device=device, problem=problem, response=response)


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIP_TYPES or params.device not in DEVICES or params.problem not in PROBLEMS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(params)
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


CURATED = [
    StoryParams(ship="skylark", crew1="mina", crew1_gender="girl", crew2="taro", crew2_gender="boy", captain="Nova", device="microchip", problem="loose_chip", response="steady_hands"),
    StoryParams(ship="comet", crew1="zoe", crew1_gender="girl", crew2="pax", crew2_gender="boy", captain="Orion", device="lens", problem="dim_comms", response="signal_boost"),
    StoryParams(ship="orbit", crew1="taro", crew1_gender="boy", crew2="mina", crew2_gender="girl", captain="Sky", device="bolt", problem="loose_chip", response="glove_pair"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for ship, device, problem in asp_valid_combos():
            print(f"{ship:8} {device:12} {problem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
