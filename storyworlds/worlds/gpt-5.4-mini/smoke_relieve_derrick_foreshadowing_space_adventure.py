#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smoke_relieve_derrick_foreshadowing_space_adventure.py
======================================================================================

A standalone story world for a small Space Adventure tale: a ship's scanner
foreshadows a smoky engine problem, Derrick and a helper relieve the pressure,
and the crew ends with a bright, safe launch.

This world keeps the Storyweavers contract shape:
- typed entities with physical meters and emotional memes
- a state-driven story engine
- prompt/story QA/world-knowledge QA
- Python reasonableness checks plus an inline ASP twin
- `--verify`, `--asp`, `--show-asp`, `--json`, `--qa`, `--trace`, `-n`, `--all`

The seed words are woven into the world model:
- smoke
- relieve
- derrick
- foreshadowing
- space adventure
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "captain": "captain"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    scene: str
    sky: str
    launch: str
    dark_spot: str
    clue: str
    finale: str

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
class Hazard:
    id: str
    label: str
    source: str
    cue: str
    where: str
    ominous: str
    causes_smoke: bool = True

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
    tags: set[str] = field(default_factory=set)

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


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["smoke"] < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ship" in world.entities:
            world.get("ship").meters["risk"] += 1
        for person in list(world.entities.values()):
            if person.kind == "character":
                person.memes["worry"] += 1
        out.append("__smoke__")
    return out


def _r_relieve(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["pressure"] < THRESHOLD or e.meters["relieved"] >= THRESHOLD:
            continue
        sig = ("relieve", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["relieved"] += 1
        e.meters["pressure"] = max(0.0, e.meters["pressure"] - 1.0)
        out.append("__relieve__")
    return out


CAUSAL_RULES = [
    Rule("smoke", "physical", _r_smoke),
    Rule("relieve", "physical", _r_relieve),
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


def valid_hazard(hazard: Hazard, setting: Setting) -> bool:
    return hazard.causes_smoke and "ship" in setting.id


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= (2 + delay)


def predict_smoke(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    ship = sim.get("ship")
    ship.meters["smoke"] += 1
    ship.meters["pressure"] += 1
    propagate(sim, narrate=False)
    return {"risk": sim.get("ship").meters["risk"], "smoke": ship.meters["smoke"]}


def start(world: World, setting: Setting, derrick: Entity, helper: Entity) -> None:
    derrick.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On the {setting.label}, {derrick.id} and {helper.id} prepared for a space adventure. "
        f"{setting.scene}"
    )
    world.say(
        f"{setting.sky} above them, the ship {setting.launch} and the stars looked like tiny white seeds."
    )


def foreshadow(world: World, setting: Setting, hazard: Hazard, derrick: Entity, helper: Entity) -> None:
    pred = predict_smoke(world, hazard)
    world.facts["foreshadow_risk"] = pred["risk"]
    world.say(
        f"Then a small clue appeared: {hazard.cue}. {setting.clue} made {derrick.id} pause."
    )
    world.say(
        f'{helper.id} frowned. "{derrick.id}, that is not ordinary space dust. It smells like {hazard.label}."'
    )
    helper.memes["foreshadow"] += 1


def choose(world: World, derrick: Entity, hazard: Hazard) -> None:
    derrick.memes["boldness"] += 1
    world.say(
        f'"We can fix it," {derrick.id} said. "Let\'s check {hazard.where} before it gets worse."'
    )


def warn(world: World, helper: Entity, derrick: Entity, hazard: Hazard) -> None:
    helper.memes["warning"] += 1
    world.say(
        f'{helper.id} pointed at {hazard.ominous}. "If we ignore that, smoke could fill the deck."'
    )


def trigger_smoke(world: World, hazard: Hazard, setting: Setting) -> None:
    ship = world.get("ship")
    engine = world.get("engine")
    ship.meters["smoke"] += 1
    ship.meters["pressure"] += 1
    engine.meters["smoke"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Sure enough, {hazard.source} started to smoke. A gray ribbon curled out through the {setting.dark_spot}."
    )


def alarm(world: World, derrick: Entity, helper: Entity) -> None:
    derrick.memes["fear"] += 1
    helper.memes["fear"] += 1
    world.say(f'"Smoke!" {derrick.id} shouted. "The ship is filling up with smoke!"')


def relieve(world: World, helper: Entity, response: Response, hazard: Hazard, setting: Setting) -> None:
    ship = world.get("ship")
    engine = world.get("engine")
    body = response.text.replace("{hazard}", hazard.label)
    ship.meters["smoke"] = 0.0
    engine.meters["smoke"] = 0.0
    ship.meters["risk"] = 0.0
    world.say(f"{helper.id} came fast and {body}.")
    world.say(f"The smoke thinned, and the ship steadied above {setting.label}.")


def relieve_fail(world: World, helper: Entity, response: Response, hazard: Hazard) -> None:
    ship = world.get("ship")
    ship.meters["risk"] += 1
    body = response.fail.replace("{hazard}", hazard.label)
    world.say(f"{helper.id} tried to help, but {body}.")
    world.say("The smoke kept spreading, and the crew had to back away from the engine hatch.")


def ending(world: World, setting: Setting, derrick: Entity, helper: Entity) -> None:
    derrick.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, {derrick.id} remembered the clue before the trouble, and {helper.id} kept watch beside {derrick.pronoun('object')}."
    )
    world.say(
        f"At last the ship {setting.finale}, bright and safe, with no smoke left in the air."
    )


def tell(setting: Setting, hazard: Hazard, response: Response, delay: int = 0,
         derrick_name: str = "Derrick", helper_name: str = "Mara",
         helper_gender: str = "girl", derrick_gender: str = "boy") -> World:
    world = World()
    derrick = world.add(Entity(id=derrick_name, kind="character", type=derrick_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="ship", type="ship", label="the ship"))
    world.add(Entity(id="engine", type="engine", label="the engine room"))

    start(world, setting, derrick, helper)
    world.para()
    foreshadow(world, setting, hazard, derrick, helper)
    choose(world, derrick, hazard)
    warn(world, helper, derrick, hazard)
    world.para()

    trigger_smoke(world, hazard, setting)
    alarm(world, derrick, helper)

    contained = is_contained(response, hazard, delay)
    world.facts["contained"] = contained
    world.facts["delay"] = delay

    world.para()
    if contained:
        relieve(world, helper, response, hazard, setting)
        ending(world, setting, derrick, helper)
    else:
        relieve_fail(world, helper, response, hazard)
        world.say(
            "They backed out, called the captain, and watched the rescue lights flash over the hull."
        )
        world.say(
            f"The lesson was clear: when a clue foreshadows danger, ask for help before the smoke grows."
        )

    world.facts.update(
        derrick=derrick,
        helper=helper,
        setting=setting,
        hazard=hazard,
        response=response,
        smoke=world.get("engine").meters["smoke"] >= THRESHOLD,
        outcome="contained" if contained else "failed",
    )
    return world


SETTINGS = {
    "orbit": Setting(
        "orbit",
        "the ring of the space station",
        "The station windows flashed like silver cards, and the little rover waited by the airlock.",
        "Far below, Earth glowed blue and gold",
        "the station hummed",
        "the shadowed maintenance corridor",
        "the blinking warning light",
        "the crew waved from the dome",
    ),
    "moonbase": Setting(
        "moonbase",
        "the moon base",
        "The habitat domes made round white hills, and a rover rolled past the crates.",
        "Under the black sky, the moon looked calm and close",
        "the base breathed softly",
        "the service tunnel",
        "the tiny crackle from the panel",
        "the launch bay opened to the stars",
    ),
    "asteroid": Setting(
        "asteroid",
        "the asteroid outpost",
        "The outpost clung to the rock like a bright tin shell, and tools floated in tidy loops.",
        "The stars seemed near enough to touch",
        "the outpost thrummed",
        "the vent shaft",
        "the flicker on the dashboard",
        "the shuttle slipped away into open space",
    ),
}

HAZARDS = {
    "smoke-vent": Hazard("smoke-vent", "smoke", "the vent fan", "a faint smell of hot metal", "the vent shaft", "a gray curl near the panel"),
    "smoke-engine": Hazard("smoke-engine", "smoke", "the engine core", "a warning blink on the console", "the engine hatch", "a warm cough of air"),
    "smoke-panel": Hazard("smoke-panel", "smoke", "the power panel", "a tiny hiss behind the lights", "the service tunnel", "a blackened seam"),
}

RESPONSES = {
    "cooling": Response("cooling", 3, 4, "shut the hatch, cooled the panel, and worked until the smoke stopped", "shut the hatch too late, and the smoke kept pouring out", "shut the hatch and cooled the panel until the smoke stopped", {"cool"}),
    "seal": Response("seal", 3, 3, "sealed the leak with a patch and helped the engine breathe easier", "sealed the leak too weakly, and the smoke slipped through again", "sealed the leak with a patch", {"seal"}),
    "fan": Response("fan", 2, 2, "switched on the spare fan and cleared the smoke from the corridor", "turned on the fan, but it could not push the smoke away", "switched on the spare fan and cleared the smoke", {"fan"}),
    "bucket": Response("bucket", 1, 1, "splashed a bucket of water at the panel", "splashed water at the panel, but that did almost nothing", "splashed water at the panel", {"weak"}),
}

NAMES = ["Derrick", "Mara", "Nova", "Iris", "Juno", "Pax", "Leo", "Tala"]
TRAITS = ["curious", "steady", "brave", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for hid, hazard in HAZARDS.items():
            for rid, resp in RESPONSES.items():
                if valid_hazard(hazard, setting) and resp.sense >= SENSE_MIN:
                    out.append((sid, hid, rid))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    response: str
    delay: int = 0
    derrick_name: str = "Derrick"
    helper_name: str = "Mara"
    derrick_gender: str = "boy"
    helper_gender: str = "girl"
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


KNOWLEDGE = {
    "smoke": [("Why is smoke a warning sign?", "Smoke often means something is getting too hot or burning. If you see smoke, you should tell a grown-up or crew leader right away.")],
    "space": [("Why do astronauts check things carefully?", "In space, small problems can become big problems quickly. Checking early helps keep everyone safe.")],
    "engine": [("What does an engine do on a ship?", "An engine gives the ship power to move. If the engine is damaged, the ship may not be able to travel safely.")],
    "hatch": [("What is a hatch?", "A hatch is a door or opening that can be sealed closed on a ship or station.")],
    "warning": [("What is a warning light for?", "A warning light tells people that something needs attention before it gets worse.")],
    "fan": [("What does a fan do?", "A fan moves air. It can help push smoke away from a room or corridor.")],
    "seal": [("What does it mean to seal a leak?", "To seal a leak means to cover the opening so air or water cannot get through.")],
    "cool": [("Why cool something hot?", "Cooling something hot can keep it from getting worse and can help stop smoke or fire.")],
}
KNOWLEDGE_ORDER = ["smoke", "space", "engine", "hatch", "warning", "fan", "seal", "cool"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    hazard = f["hazard"]
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that uses the word "{hazard.label}" and includes a hint before the big problem.',
        f"Tell a story where Derrick notices a clue first, then smoke appears, and a helper relieves the danger on {setting.label}.",
        f'Write a child-friendly space adventure with foreshadowing, a smoky surprise, and a calm ending that proves the crew learned to watch for clues.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    derrick: Entity = f["derrick"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    hazard: Hazard = f["hazard"]
    response: Response = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {derrick.id} and {helper.id} on {setting.label}. They are the little crew at the center of the space adventure."),
        ("What clue warned them first?",
         f"{hazard.cue} warned them first. That clue foreshadowed the smoky trouble before the ship started to fill with it."),
        ("What did Derrick want to do?",
         f"Derrick wanted to check {hazard.where} and fix the problem quickly. That was the brave choice once the clue appeared."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the helper relieve the danger?",
            f"{helper.id} {response.qa_text} so the smoke could leave the ship. That relieved the pressure and let the crew feel safe again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the ship safe and bright again, and no smoke left in the air. The crew kept going because they had noticed the clue early."
        ))
    else:
        qa.append((
            "What happened when the helper could not fix it fast enough?",
            f"The smoke kept spreading, so they backed away and called the captain for help. The story still taught them to act early when a clue appears."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"smoke", "space", "engine", "warning"}
    if world.facts["outcome"] == "contained":
        tags |= set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbit", "smoke-vent", "cooling", 0, "Derrick", "Mara", "boy", "girl"),
    StoryParams("moonbase", "smoke-engine", "seal", 0, "Derrick", "Iris", "boy", "girl"),
    StoryParams("asteroid", "smoke-panel", "fan", 1, "Derrick", "Nova", "boy", "girl"),
]


def explain_rejection(hazard: Hazard, setting: Setting) -> str:
    return f"(No story: this setting and hazard do not make a convincing smoke problem for a space adventure.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too weak on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
hazard(H, S) :- hazard_id(H), setting(S), smoke_hazard(H).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(S, H, R) :- hazard(H, S), sensible(R).
contained :- chosen_response(R), power(R, P), delay(D), needed(N), P >= N + D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard_id", hid))
        lines.append(asp.fact("smoke_hazard", hid))
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
    extra = "\n".join([asp.fact("chosen_response", params.response), asp.fact("delay", params.delay), asp.fact("needed", 2)])
    model = asp.one_model(asp_program(extra, "#show contained/0."))
    return "contained" if asp.atoms(model, "contained") else "failed"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, response=None, delay=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with smoke, foreshadowing, and relief.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--derrick", dest="derrick_name")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for hid in HAZARDS:
            for rid in RESPONSES:
                if valid_hazard(HAZARDS[hid], SETTINGS[sid]) and RESPONSES[rid].sense >= SENSE_MIN:
                    out.append((sid, hid, rid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, response = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    derrick = args.derrick_name or "Derrick"
    helper = args.helper or rng.choice([n for n in NAMES if n != derrick])
    return StoryParams(setting, hazard, response, delay, derrick, helper, "boy", "girl")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], RESPONSES[params.response],
                 params.delay, params.derrick_name, params.helper, params.helper_gender, params.derrick_gender)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for s, h, r in asp_valid_combos():
            print(f"{s:10} {h:12} {r}")
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
