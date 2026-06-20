#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/beep_defective_misunderstanding_twist_rhyming_story.py
======================================================================================

A standalone storyworld for a tiny rhyming tale about a strange beep,
a defective device, a misunderstanding, and a twist that turns worry into joy.

The seed idea:
- A child hears a beep from a small gadget.
- The gadget seems defective.
- Everyone misunderstands what the beep means.
- The twist reveals the beep was a helpful signal, and the ending is warm.

This world keeps the domain small on purpose: one child, one helper, one device,
and one house setting. The simulated state drives the prose, including the
misunderstanding beat and the final twist.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/beep_defective_misunderstanding_twist_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/beep_defective_misunderstanding_twist_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/beep_defective_misunderstanding_twist_rhyming_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"broken": 0.0, "fixed": 0.0, "glow": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "confusion": 0.0, "relief": 0.0}

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Device:
    id: str
    label: str
    phrase: str
    beep_word: str
    defect: str
    sign: str
    fix: str
    truth: str
    safe_use: str
    defective: bool = True
    makes_beep: bool = True
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
class Setting:
    id: str
    place: str
    rhyme_a: str
    rhyme_b: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


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
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    device = world.get("device")
    if device.meters["broken"] >= THRESHOLD and "confused" not in world.fired:
        world.fired.add("confused")
        child.memes["confusion"] += 1
        out.append("The beep made the child think something had gone wrong.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    device = world.get("device")
    if device.meters["fixed"] >= THRESHOLD and "relief" not in world.fired:
        world.fired.add("relief")
        child.memes["relief"] += 1
        child.memes["worry"] = 0.0
        out.append("The soft beep soon brought sweet relief.")
    return out


RULES = [Rule("confusion", _r_confusion), Rule("relief", _r_relief)]


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    trigger_fault(sim, narrate=False)
    return {
        "confused": sim.get("child").memes["confusion"] >= THRESHOLD,
        "broken": sim.get("device").meters["broken"] >= THRESHOLD,
    }


def trigger_fault(world: World, narrate: bool = True) -> None:
    device = world.get("device")
    device.meters["broken"] += 1
    propagate(world, narrate=narrate)


def fix_device(world: World, helper: Entity, device: Entity, setting: Setting) -> None:
    device.meters["broken"] = 0.0
    device.meters["fixed"] = 1.0
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} checked the little {device.label}, found the tiny snag, and gave it a careful tap."
    )
    world.say(
        f"Then the {device.label} gave one bright beep, neat as could be, in {setting.place} by the sleepy tree."
    )
    propagate(world, narrate=False)


def misunderstanding(world: World, child: Entity, helper: Entity, device: Device) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} heard the beep and frowned in a heap. "
        f'"Oh no," {child.pronoun()} cried, "my {device.label} is defective and cheap!"'
    )
    world.say(
        f"But {helper.id} laughed soft and said, " 
        f'"Let us look; there may be a different book."'
    )


def twist(world: World, child: Entity, helper: Entity, device: Device) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then came the twist in the little breeze: the beep was a signal, a message to please."
    )
    world.say(
        f"The {device.label} was not broken beyond repair; it had beeped to say, 'I need a little care.'"
    )
    world.say(
        f"{helper.id} smiled wide and showed {child.id} the clue, and the room felt bright and new."
    )


def ending(world: World, child: Entity, helper: Entity, device: Device, setting: Setting) -> None:
    world.say(
        f"So {child.id} kept the {device.label} near, and the beep became music instead of fear."
    )
    world.say(
        f"In {setting.place}, under {setting.rhyme_a}, they laughed together beneath {setting.rhyme_b}."
    )


def tell(setting: Setting, device: Device, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    gadget = world.add(Entity(id="device", kind="thing", type="device", label=device.label))
    world.facts.update(setting=setting, device=device, child=child, helper=helper)

    world.say(
        f"In {setting.place}, where the day could sway, {child.id} and {helper.id} went out to play."
    )
    world.say(
        f"They found a small {device.label} with a shiny face, a bit {device.defect}, in a quiet place."
    )
    world.say(
        f"It gave a beep, a peep, a squeak in the air, and {child.id} wondered why it was there."
    )
    world.para()
    misunderstanding(world, child, helper, device)
    if predict_misunderstanding(world)["confused"]:
        world.say(
            f"{child.id} thought the beep meant doom and gloom, and the small room grew tense in the room."
        )
    world.para()
    twist(world, child, helper, device)
    fix_device(world, helper, gadget, setting)
    world.para()
    ending(world, child, helper, device, setting)
    world.facts["outcome"] = "fixed"
    world.facts["device_entity"] = gadget
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "the green grass", "the pink-red roses", {"outdoor"}),
    "porch": Setting("porch", "the porch", "the wooden boards", "the evening stars", {"outdoor"}),
    "kitchen": Setting("kitchen", "the kitchen", "the warm blue chair", "the bright white tile", {"indoor"}),
}

DEVICES = {
    "beeper": Device(
        "beeper",
        "beeper",
        "a little beeper",
        "beep",
        "defective",
        "a faint beep",
        "fix the tiny wire",
        "it was only asking for care",
        "listening close",
        True,
        True,
        {"beep", "defective", "device"},
    ),
    "toy": Device(
        "toy",
        "toy robot",
        "a toy robot",
        "beep",
        "defective",
        "a puzzled beep",
        "replace the tiny battery",
        "it was only a loose battery",
        "gentle tapping",
        True,
        True,
        {"beep", "defective", "toy"},
    ),
}

CHILDREN = [("Mia", "girl"), ("Noah", "boy"), ("Lily", "girl"), ("Eli", "boy")]
HELPERS = [("Mom", "girl"), ("Dad", "boy"), ("Aunt May", "girl"), ("Uncle Ben", "boy")]


@dataclass
@dataclass
class StoryParams:
    setting: str
    device: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, d) for s in SETTINGS for d in DEVICES if DEVICES[d].defective and DEVICES[d].makes_beep]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming beep-and-twist storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--child")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.device is None or c[1] == args.device)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, device = rng.choice(sorted(combos))
    child_name, child_gender = rng.choice(CHILDREN)
    helper_name, helper_gender = rng.choice([x for x in HELPERS if x[0] != child_name])
    if args.child:
        child_name = args.child
    if args.helper:
        helper_name = args.helper
    return StoryParams(setting, device, child_name, child_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming story where {f['child'].id} hears a beep from a defective {f['device'].label}.",
        f"Tell a gentle misunderstanding story that includes the words beep and defective and ends with a twist.",
        f"Write a child-friendly rhyme about a strange beep that turns out to mean something helpful, not scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    device = world.facts["device"]
    setting = world.facts["setting"]
    return [
        QAItem(
            question="What did the child hear?",
            answer=f"The child heard a beep from the {device.label}. It sounded strange at first, so {child.id} worried.",
        ),
        QAItem(
            question="Why was there a misunderstanding?",
            answer=f"{child.id} thought the beep meant the {device.label} was defective in a bad way. {helper.id} checked it and found it only needed care.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the beep was a helpful signal, not a disaster. The device was safe once {helper.id} fixed the tiny problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with relief and a happy beep in {setting.place}. {child.id} learned that a strange sound can have a kind reason.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beep?",
            answer="A beep is a short sound made by a machine or device. It can be a warning, a signal, or a tiny notice that something needs attention.",
        ),
        QAItem(
            question="What does defective mean?",
            answer="Defective means something is not working the right way. It may need fixing, even if it still does a little bit of its job.",
        ),
        QAItem(
            question="What should you do when a device seems broken?",
            answer="You should tell a grown-up and check it carefully instead of guessing. A calm look can turn worry into a simple fix.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,D) :- setting(S), device(D), defective(D), makes_beep(D).
outcome(fixed) :- valid(_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        if d.defective:
            lines.append(asp.fact("defective", did))
        if d.makes_beep:
            lines.append(asp.fact("makes_beep", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import contextlib
    import io
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    try:
        sample = generate(StoryParams("kitchen", "beeper", "Mia", "girl", "Mom", "girl"))
        _ = sample.story
    except Exception as exc:
        print(f"MISMATCH: generate() failed: {exc}")
        return 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True)
    except Exception as exc:
        print(f"MISMATCH: emit() failed: {exc}")
        return 1
    print("OK: verify passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DEVICES[params.device], params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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


CURATED = [
    StoryParams("garden", "beeper", "Mia", "girl", "Mom", "girl"),
    StoryParams("porch", "toy", "Noah", "boy", "Dad", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
