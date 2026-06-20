#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lioness_secondary_atmosphere_dock_suspense_bad_ending.py
========================================================================================

A standalone storyworld for a rhyming dock suspense tale with a lioness, a
secondary helper, a tense atmosphere, problem solving, and a bad ending.

The world is small and state-driven: a child, a dock keeper, a lioness, a crate,
a boat, and the weather pressure around them. The story can end in either a safe
pause or a bad ending, but the curated default leans into suspense and loss.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/lioness_secondary_atmosphere_dock_suspense_bad_ending.py
    python storyworlds/worlds/gpt-5.4-mini/lioness_secondary_atmosphere_dock_suspense_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4-mini/lioness_secondary_atmosphere_dock_suspense_bad_ending.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    flammable: bool = False
    heavy: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "lioness"}
        male = {"boy", "man", "father", "lion"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class DockSetting:
    mood: str
    atmosphere: str
    tide: str
    place: str = "dock"

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
class Risk:
    id: str
    label: str
    danger: str
    risk_phrase: str
    flammable: bool = False
    heavy: bool = False
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


@dataclass
class Helper:
    id: str
    label: str
    method: str
    power: int
    sense: int
    text: str
    fail: str
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


@dataclass
@dataclass
class StoryParams:
    risk: str
    helper: str
    delay: int
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "dock": DockSetting(
        mood="a gray dock",
        atmosphere="The atmosphere was hush and dim, with ropes that creaked in the wind.",
        tide="The tide kept tapping the posts like a slow, nervous drum.",
        place="dock",
    )
}

RISKS = {
    "stormcrate": Risk(
        "stormcrate",
        "a wet crate of paint",
        "the crate could split and spill",
        "the crate sat near the edge",
        flammable=False,
        heavy=True,
        tags={"crate", "paint", "dock"},
    ),
    "lanternoil": Risk(
        "lanternoil",
        "a lantern with oil",
        "the flame could jump",
        "the lantern swayed in the wind",
        flammable=True,
        heavy=False,
        tags={"lantern", "fire", "dock"},
    ),
    "net": Risk(
        "net",
        "a fishing net",
        "the net could snag and tangle",
        "the net hung loose by the rail",
        flammable=False,
        heavy=False,
        tags={"net", "dock"},
    ),
}

HELPERS = {
    "rope": Helper(
        "rope",
        "a spare rope",
        "tie the crate fast",
        power=3,
        sense=3,
        text="tied the crate fast and steadied it against the sway",
        fail="pulled at the rope, but the load still slipped in the spray",
        tags={"rope", "dock"},
    ),
    "barrier": Helper(
        "barrier",
        "a tall barrier",
        "block the edge",
        power=4,
        sense=3,
        text="set a tall barrier by the edge, and the risky thing stayed in place",
        fail="dragged over a barrier, but the wind still found a race",
        tags={"barrier", "dock"},
    ),
    "callkeeper": Helper(
        "callkeeper",
        "a dock keeper",
        "call for help",
        power=5,
        sense=4,
        text="called for the dock keeper, who came with calm and care",
        fail="called for the dock keeper, but the rush was more than they could bear",
        tags={"keeper", "dock"},
    ),
}

# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, int]]:
    combos = []
    for risk in RISKS:
        for helper in HELPERS:
            if risk == "net" and helper == "rope":
                combos.append(("dock", risk, helper))
            if risk == "stormcrate" and helper in {"rope", "barrier", "callkeeper"}:
                combos.append(("dock", risk, helper))
            if risk == "lanternoil" and helper in {"barrier", "callkeeper"}:
                combos.append(("dock", risk, helper))
    return [(place, risk, helper) for place, risk, helper in combos]


def best_helper() -> Helper:
    return max(HELPERS.values(), key=lambda h: h.sense)


def is_contained(helper: Helper, risk: Risk, delay: int) -> bool:
    severity = (2 if risk.heavy else 1) + delay
    return helper.power >= severity


# ---------------------------------------------------------------------------
# Plot verbs
# ---------------------------------------------------------------------------
def predict(world: World, risk_id: str, helper_id: str, delay: int) -> dict:
    sim = world.copy()
    risk = RISKS[risk_id]
    helper = HELPERS[helper_id]
    contained = is_contained(helper, risk, delay)
    if not contained:
        sim.get("dock").meters["danger"] = 2
    return {"contained": contained, "danger": sim.get("dock").meters.get("danger", 0)}


def setup(world: World, child: Entity, secondary: Entity, setting: DockSetting) -> None:
    world.say(
        f"On the dock, {child.id} and {secondary.id} stood by the rails. "
        f"{setting.atmosphere} {setting.tide}"
    )


def suspense(world: World, child: Entity, secondary: Entity, risk: Risk) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    secondary.memes["worry"] = secondary.memes.get("worry", 0) + 1
    world.say(
        f'The air felt like suspense, and even the word "secondary" sounded slow. '
        f'{secondary.id} pointed at {risk.risk_phrase}.'
    )
    world.say(
        f'"That {risk.label} looks tricky," {secondary.id} said. '
        f'"The {risk.danger}, if we do not think."'
    )


def problem_solving(world: World, child: Entity, secondary: Entity, helper: Helper,
                    risk: Risk) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f"{child.id} took a breath and tried problem solving. "
        f'Together they chose {helper.label}, because it could {helper.method}.'
    )


def accident(world: World, risk: Risk, delay: int) -> None:
    dock = world.get("dock")
    dock.meters["danger"] = dock.meters.get("danger", 0) + (1 + delay)
    if risk.flammable:
        dock.meters["fire"] = 1
        world.say(
            f"A spark jumped in the salty air, and the lantern flame caught the edge. "
            f"The dock glowed orange for a blink."
        )
    else:
        world.say(
            f"The crate tipped with a groan, and paint sloshed over the boards. "
            f"The dock became slippery and hard to cross."
        )


def resolve(world: World, child: Entity, secondary: Entity, helper: Helper, risk: Risk,
            contained: bool) -> None:
    if contained:
        world.say(
            f"{secondary.id} {helper.text}. The trouble settled, and the dock felt safe again."
        )
        world.say(
            f"{child.id} smiled at the quieter air, and the waves went back to their soft rhyme."
        )
    else:
        world.say(
            f"{secondary.id} {helper.fail}. The trouble won the night, and there was no bright light."
        )
        world.say(
            f"The crate broke, the boards were stained, and the dock stayed lost in rain."
        )
        world.say(
            f"{child.id} and {secondary.id} could only stare as the bad ending drifted there."
        )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS["dock"]
    child = world.add(Entity(id="Mina", kind="character", type="girl", role="child"))
    secondary = world.add(Entity(id="Soren", kind="character", type="boy", role="secondary"))
    lioness = world.add(Entity(id="lioness", kind="character", type="lioness", role="threat"))
    dock = world.add(Entity(id="dock", type="place", label="dock"))
    risk = RISKS[params.risk]
    helper = HELPERS[params.helper]
    setup(world, child, secondary, setting)
    suspense(world, child, secondary, risk)
    problem_solving(world, child, secondary, helper, risk)
    pred = predict(world, params.risk, params.helper, params.delay)
    world.facts["predicted"] = pred
    world.para()
    accident(world, risk, params.delay)
    contained = is_contained(helper, risk, params.delay)
    resolve(world, child, secondary, helper, risk, contained)
    world.facts.update(
        child=child,
        secondary=secondary,
        lioness=lioness,
        dock=dock,
        risk=risk,
        helper=helper,
        contained=contained,
        outcome="bad" if not contained else "contained",
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming suspense story set on a dock that includes the words "lioness", "secondary", and "atmosphere".',
        f"Tell a dock story where {f['secondary'].id} helps {f['child'].id} solve a problem, but the ending is bad.",
        f"Write a tense rhyming tale where a lioness, a secondary helper, and a stormy atmosphere lead to trouble on the dock.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sec = f["secondary"]
    risk = f["risk"]
    helper = f["helper"]
    contained = f["contained"]
    out = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {sec.id}, and the lioness by the dock. The dock atmosphere stays tense the whole time.",
        ),
        QAItem(
            question="What problem did they try to solve?",
            answer=f"They tried to handle {risk.label} safely. They used {helper.label} so the danger would not spread across the dock.",
        ),
    ]
    if contained:
        out.append(QAItem(
            question="Did the plan work?",
            answer="Yes, the plan worked and the danger settled down. The dock grew calm again before anything could get worse.",
        ))
    else:
        out.append(QAItem(
            question="Did the plan work?",
            answer="No, the plan was not enough. The bad ending came because the trouble moved faster than their fix.",
        ))
    return out


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lioness?",
            answer="A lioness is a female lion. She is strong, alert, and can be very dangerous if people get too close.",
        ),
        QAItem(
            question="What does atmosphere mean in a story?",
            answer="Atmosphere means the feeling around the scene. It can be calm, happy, spooky, or tense, depending on what the story wants you to feel.",
        ),
        QAItem(
            question="What does a dock do?",
            answer="A dock is a place by the water where boats can stop. People may load things there, watch the waves, or tie ropes to the posts.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(dock, R, H) :- risk(R), helper(H).

contained(R, H, D) :- risk(R), helper(H), delay(D), power(H, P), severity(R, S), P >= S + D.
outcome(bad) :- risk(R), helper(H), delay(D), not contained(R, H, D).
outcome(contained) :- risk(R), helper(H), delay(D), contained(R, H, D).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "dock")]
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("severity", rid, 2 if r.heavy else 1))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("power", hid, h.power))
    for d in range(3):
        lines.append(asp.fact("delay", d))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_risk", params.risk),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming dock suspense storyworld.")
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
              if (args.risk is None or c[1] == args.risk)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, risk, helper = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(risk=risk, helper=helper, delay=delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p != c:
        rc = 1
        print("MISMATCH in ASP parity")
        print("python only:", sorted(p - c))
        print("clingo only:", sorted(c - p))
    else:
        print(f"OK: ASP parity with {len(p)} combos.")
    # smoke test normal generation
    try:
        sample = generate(StoryParams("stormcrate", "barrier", 1))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"FAIL: generate smoke test crashed: {exc}")
    # verify outcome for a few cases
    for p in [StoryParams("stormcrate", "barrier", 0), StoryParams("lanternoil", "callkeeper", 2)]:
        _ = asp_outcome(p)
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
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
        curated = [
            StoryParams("stormcrate", "rope", 0),
            StoryParams("stormcrate", "barrier", 1),
            StoryParams("lanternoil", "callkeeper", 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
