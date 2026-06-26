#!/usr/bin/env python3
"""
storyworlds/worlds/tiny_naughty_repetition_cautionary_space_adventure.py
========================================================================

A tiny, cautionary space-adventure storyworld about a small crew, a tempting
control panel, and a repeated naughty choice that creates a problem before a
safer ending fixes it.

Seed tale:
---
A tiny helper on a little starship loved buttons. The captain warned not to
press the red one, because it repeated the engine alarm and could make the ship
drift. But the helper pressed it again and again anyway. The ship beeped,
lights flashed, and everyone had to slow down and fix the problem. At last the
helper stopped, apologized, and used the safe blue button to guide the ship
home.

This file turns that premise into a stateful simulation with physical meters and
emotional memes, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Small domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
REPETITION_LIMIT = 2
TINY_LIMIT = 0.5


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def __post_init__(self):
        if not self.meters:
            self.meters = {"fuel": 0.0, "drift": 0.0, "noise": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "naughty": 0.0, "careful": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "captain"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    helper_type: str
    captain_type: str
    ship_name: str
    beacon: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HELPERS = {
    "tiny_robot": {
        "type": "robot",
        "label": "tiny robot",
        "phrase": "a tiny, curious robot",
        "traits": ["tiny", "curious", "naughty"],
    },
    "tiny_pilot": {
        "type": "boy",
        "label": "tiny pilot",
        "phrase": "a tiny, eager pilot",
        "traits": ["tiny", "eager", "naughty"],
    },
    "tiny_cadet": {
        "type": "girl",
        "label": "tiny cadet",
        "phrase": "a tiny, bright cadet",
        "traits": ["tiny", "bright", "naughty"],
    },
}

CAPTAINS = {
    "captain": {"type": "captain", "label": "captain", "phrase": "the ship captain"},
    "mother": {"type": "mother", "label": "mom captain", "phrase": "the captain mom"},
    "father": {"type": "father", "label": "dad captain", "phrase": "the captain dad"},
}

BEACONS = {
    "red_button": {
        "label": "red button",
        "phrase": "a big red button",
        "risk": "alarm",
        "safe": "blue button",
        "safe_phrase": "the blue button",
    },
    "lever": {
        "label": "silver lever",
        "phrase": "a shiny silver lever",
        "risk": "drift",
        "safe": "green dial",
        "safe_phrase": "the green dial",
    },
}

SHIP_NAMES = ["Star Dot", "Moon Shoe", "Little Comet", "Tiny Orbit", "Spark Boat"]

LOCATIONS = ["near a glowing moon", "past a ring of ice", "beside a sleepy asteroid", "between two bright stars"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(helper_type: str, beacon: str) -> None:
    if helper_type not in HELPERS:
        raise StoryError("Unknown helper type.")
    if beacon not in BEACONS:
        raise StoryError("Unknown ship control.")
    if beacon == "lever" and helper_type == "tiny_robot":
        return
    if beacon == "red_button":
        return
    raise StoryError("This story needs a control that can be pressed more than once and still cause a cautionary problem.")


def build_world(params: StoryParams) -> Ship:
    reasonableness_gate(params.helper_type, params.beacon)
    ship = Ship(name=params.ship_name, place=random.choice(LOCATIONS))
    helper_cfg = HELPERS[params.helper_type]
    captain_cfg = CAPTAINS[params.captain_type]
    beacon_cfg = BEACONS[params.beacon]

    helper = ship.add(Entity(
        id=params.name,
        kind="character",
        type=helper_cfg["type"],
        label=helper_cfg["label"],
        phrase=helper_cfg["phrase"],
        traits=list(helper_cfg["traits"]),
    ))
    captain = ship.add(Entity(
        id="Captain",
        kind="character",
        type=captain_cfg["type"],
        label=captain_cfg["label"],
        phrase=captain_cfg["phrase"],
        traits=["wise", "careful"],
    ))
    control = ship.add(Entity(
        id="Control",
        type="thing",
        label=beacon_cfg["label"],
        phrase=beacon_cfg["phrase"],
        owner=ship.name,
    ))
    safe = ship.add(Entity(
        id="Safe",
        type="thing",
        label=beacon_cfg["safe"],
        phrase=beacon_cfg["safe_phrase"],
        owner=ship.name,
    ))

    ship.facts.update(helper=helper, captain=captain, control=control, safe=safe, beacon_cfg=beacon_cfg)
    return ship


def apply_press(ship: Ship, actor: Entity, control: Entity, caution: bool = True) -> None:
    beacon = ship.facts["beacon_cfg"]
    actor.meters["noise"] += 1
    actor.memes["naughty"] += 1
    control.meters["noise"] += 1
    sig = ("press", actor.id, control.id, int(actor.meters["noise"]))
    if sig in ship.fired:
        return
    ship.fired.add(sig)

    ship.say(f"{actor.id} pressed the {control.label} again.")
    if actor.meters["noise"] >= REPETITION_LIMIT:
        ship.say("The same wrong tap happened over and over, and the ship began to beep loudly.")
        ship.facts["repetition"] = True

    if caution and control.id == "Control":
        actor.memes["worry"] += 0.5
        ship.get("Captain").memes["worry"] += 1
        ship.say(f"The captain frowned because the {beacon['risk']} alarm could make the ship drift.")


def propagate(ship: Ship) -> None:
    helper = ship.facts["helper"]
    captain = ship.facts["captain"]
    control = ship.facts["control"]

    if helper.meters["noise"] >= REPETITION_LIMIT and "drift" not in ship.fired:
        ship.fired.add(("drift",))
        ship.get(helper.id).meters["drift"] += 1
        ship.get(captain.id).memes["worry"] += 1
        ship.say("The ship drifted a little farther from the safe path.")

    if helper.meters["drift"] >= THRESHOLD and ("fix",) not in ship.fired:
        ship.fired.add(("fix",))
        captain.memes["careful"] += 1
        ship.say("The captain slowed everything down so they could fix the problem safely.")

    if helper.memes["naughty"] >= THRESHOLD and helper.meters["drift"] >= THRESHOLD:
        ship.facts["problem"] = True

    if helper.memes["careful"] >= THRESHOLD and ship.facts.get("resolved"):
        ship.say("The ship steadied, and the lights went back to a calm blue.")


def tell(params: StoryParams) -> Ship:
    ship = build_world(params)
    helper = ship.facts["helper"]
    captain = ship.facts["captain"]
    control = ship.facts["control"]
    safe = ship.facts["safe"]
    beacon = ship.facts["beacon_cfg"]

    ship.say(f"{helper.phrase} lived aboard the little ship {ship.name}.")
    ship.say(f"{helper.id} liked bright controls and dreamed about the stars.")
    ship.say(f"One day, {helper.id} and {captain.id} floated {ship.place}.")

    ship.para()
    ship.say(f"{helper.id} wanted to press the {control.label}, but {captain.id} warned, “Do not press it.”")
    ship.say("The warning was important, because the same naughty choice could happen again and again.")

    apply_press(ship, helper, control)
    apply_press(ship, helper, control)
    propagate(ship)

    ship.para()
    ship.say(f"{helper.id} made the naughty choice one more time.")
    apply_press(ship, helper, control)
    propagate(ship)

    ship.para()
    ship.say(f"Then {captain.id} pointed to {safe.label} and showed a safer way.")
    helper.memes["careful"] += 1
    helper.memes["naughty"] = 0
    ship.facts["resolved"] = True
    ship.say(f'{helper.id} stopped, said sorry, and used {safe.phrase} to guide the ship home.')
    ship.say(f"At last, {helper.id} was tiny no longer in trouble, and the ship glided steadily under the stars.")
    propagate(ship)

    ship.facts.update(
        ship=ship,
        helper=helper,
        captain=captain,
        control=control,
        safe=safe,
        beacon_cfg=beacon,
        place=ship.place,
    )
    return ship


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(ship: Ship) -> list[str]:
    f = ship.facts
    helper = f["helper"]
    beacon = f["beacon_cfg"]
    return [
        f"Write a tiny space adventure about {helper.id} and a naughty repeated mistake with the {f['control'].label}.",
        f"Tell a cautionary story where a small ship crew learns not to keep pressing the {f['control'].label}.",
        f"Write a child-friendly story about repetition, warning, and a safer choice using the {beacon['safe_phrase']}.",
    ]


def story_qa(ship: Ship) -> list[QAItem]:
    f = ship.facts
    helper = f["helper"]
    captain = f["captain"]
    control = f["control"]
    safe = f["safe"]
    qa = [
        QAItem(
            question=f"What did {helper.id} keep doing that caused trouble?",
            answer=f"{helper.id} kept pressing the {control.label} again and again, even after being warned.",
        ),
        QAItem(
            question=f"Why was the captain worried about the {control.label}?",
            answer=f"The captain was worried because pressing it could repeat the alarm and make the ship drift away from the safe path.",
        ),
        QAItem(
            question=f"How did the story end for {helper.id}?",
            answer=f"{helper.id} stopped the naughty repetition, said sorry, and used {safe.phrase} to guide the ship home safely.",
        ),
    ]
    if ship.facts.get("repetition"):
        qa.append(
            QAItem(
                question=f"What happened because the same mistake happened more than once?",
                answer="The ship beeped loudly, drifted a little, and the crew had to slow down and fix the problem.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "button": [
        ("What is a button on a spaceship for?", "A spaceship button is a control you press to make a machine do something."),
    ],
    "alarm": [
        ("What is an alarm?", "An alarm is a loud warning sound that tells people something needs attention."),
    ],
    "drift": [
        ("What does drift mean in space?", "To drift means to move slowly without a strong push or careful steering."),
    ],
    "safe": [
        ("Why should you choose the safe control?", "A safe control helps you avoid trouble and keep things working the right way."),
    ],
}


def world_knowledge_qa(ship: Ship) -> list[QAItem]:
    tags = {"button", "alarm", "drift", "safe"}
    out: list[QAItem] = []
    for tag in tags:
        if tag in WORLD_KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(ship: Ship) -> str:
    lines = ["--- world model state ---"]
    for e in ship.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(str(x) for x in ship.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A helper repeatedly presses a control.
pressed(H, C) :- helper(H), control(C), repeat_press(H, C).

% Repetition means the same action happens more than once.
repetition(H, C) :- pressed(H, C), pressed(H, C).

% Cautionary result: the captain worries when repetition can cause drift.
worry(Captain, H) :- captain(Captain), helper(H), repetition(H, _), risky_control(_).

% Resolution: the helper can choose the safe control.
resolved(H) :- helper(H), safe_control(_), stop_naughty(H).

#show repetition/2.
#show worry/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("captain", "captain"))
    lines.append(asp.fact("control", "control"))
    lines.append(asp.fact("safe_control", "safe"))
    lines.append(asp.fact("risky_control", "control"))
    lines.append(asp.fact("repeat_press", "helper", "control"))
    lines.append(asp.fact("repeat_press", "helper", "control"))
    lines.append(asp.fact("stop_naughty", "helper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repetition/2. #show worry/2. #show resolved/1."))
    reps = set(asp.atoms(model, "repetition"))
    worries = set(asp.atoms(model, "worry"))
    resolved = set(asp.atoms(model, "resolved"))

    py_reps = {("helper", "control")}
    py_worries = {("captain", "helper")}
    py_resolved = {("helper",)}

    if reps == py_reps and worries == py_worries and resolved == py_resolved:
        print("OK: ASP and Python gates agree.")
        return 0

    print("MISMATCH between ASP and Python gate.")
    print("ASP repetition:", sorted(reps))
    print("PY  repetition:", sorted(py_reps))
    print("ASP worry:", sorted(worries))
    print("PY  worry:", sorted(py_worries))
    print("ASP resolved:", sorted(resolved))
    print("PY  resolved:", sorted(py_resolved))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny cautionary space adventure storyworld.")
    ap.add_argument("--name", choices=["Milo", "Nia", "Pip"])
    ap.add_argument("--helper-type", choices=list(HELPERS))
    ap.add_argument("--captain-type", choices=list(CAPTAINS))
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
    ap.add_argument("--beacon", choices=list(BEACONS))
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
    helper_type = args.helper_type or rng.choice(list(HELPERS))
    captain_type = args.captain_type or rng.choice(list(CAPTAINS))
    beacon = args.beacon or rng.choice(list(BEACONS))
    name = args.name or rng.choice(["Milo", "Nia", "Pip"])
    ship_name = args.ship_name or rng.choice(SHIP_NAMES)
    if helper_type == "tiny_robot" and beacon == "lever":
        pass
    return StoryParams(
        name=name,
        helper_type=helper_type,
        captain_type=captain_type,
        ship_name=ship_name,
        beacon=beacon,
    )


def generate(params: StoryParams) -> StorySample:
    ship = tell(params)
    return StorySample(
        params=params,
        story=ship.render(),
        prompts=generation_prompts(ship),
        story_qa=story_qa(ship),
        world_qa=world_knowledge_qa(ship),
        world=ship,
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
    StoryParams(name="Milo", helper_type="tiny_robot", captain_type="captain", ship_name="Little Comet", beacon="red_button"),
    StoryParams(name="Pip", helper_type="tiny_cadet", captain_type="mother", ship_name="Tiny Orbit", beacon="lever"),
    StoryParams(name="Nia", helper_type="tiny_pilot", captain_type="father", ship_name="Star Dot", beacon="red_button"),
]


def asp_valids() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show repetition/2. #show worry/2. #show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show repetition/2. #show worry/2. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valids())
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
