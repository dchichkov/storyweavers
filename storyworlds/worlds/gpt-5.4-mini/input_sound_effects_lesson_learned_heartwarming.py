#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/input_sound_effects_lesson_learned_heartwarming.py
===================================================================================

A small, standalone storyworld about a child, a friendly helper, and the
difference between a noisy, mistaken input and a thoughtful one.

Domain
------
A child is helping a little kitchen robot or toy machine start a gentle task.
The machine has an input slot that can take a card, button code, or voice cue.
The child first uses the wrong input and gets a silly sound effect, then a kind
helper shows the right input and the machine works. The ending is warm and
heartwarming: the child learns to ask, listen, and try again.

This world supports:
- sound effects in narration
- a lesson learned ending
- complete, state-driven story arcs
- generated prompts, story QA, and world knowledge QA
- a Python reasonableness gate plus an inline ASP twin
- verify smoke tests

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/input_sound_effects_lesson_learned_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/input_sound_effects_lesson_learned_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/input_sound_effects_lesson_learned_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/input_sound_effects_lesson_learned_heartwarming.py --verify
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
    input_kind: str
    sound_on_wrong: str
    sound_on_right: str
    helpful_result: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    sense: int = 3

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
class InputItem:
    id: str
    label: str
    kind: str
    wrong_fit: bool
    right_fit: bool
    sound: str
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
    type: str
    kind_words: str = ""
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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_mistake(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["confused"] < THRESHOLD:
            continue
        sig = ("confused", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__sound__")
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    if world.facts.get("resolved"):
        for e in world.characters():
            if e.memes["relief"] < THRESHOLD:
                e.memes["relief"] += 1
                out.append("__warm__")
    return out


CAUSAL_RULES = [Rule("mistake", "social", _r_mistake), Rule("fix", "social", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def good_combo(inp: InputItem, device: Device) -> bool:
    return (not inp.wrong_fit) and inp.right_fit and device.input_kind == inp.kind


def sensible_devices() -> list[Device]:
    return [d for d in DEVICES.values() if d.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    inp = INPUTS[params.input_item]
    dev = DEVICES[params.device]
    return "resolved" if good_combo(inp, dev) else "repaired"


def predict_resolution(world: World, device: Device, inp: InputItem) -> dict:
    sim = world.copy()
    _use_input(sim, sim.get("child"), sim.get("helper"), device, inp, narrate=False)
    return {"resolved": sim.facts.get("resolved", False)}


def _use_input(world: World, child: Entity, helper: Entity, device: Device, inp: InputItem, narrate: bool = True) -> None:
    child.meters["confused"] += 1
    world.say(f'{child.id} pressed the {inp.label}.')
    if inp.wrong_fit:
        world.say(f"{inp.sound} The machine blinked, coughed, and stayed quiet.")
    else:
        world.say(f"{inp.sound} The machine woke up gently and began to {device.helpful_result}.")
    world.facts["resolved"] = good_combo(inp, device)
    if world.facts["resolved"]:
        propagate(world, narrate=narrate)


def story_open(world: World, child: Entity, helper: Entity, device: Device) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a cozy afternoon, {child.id} and {helper.id} stood beside the little {device.label}. "
        f"It had a slot for an input, and {child.id} wanted to make it work."
    )


def tempt(world: World, child: Entity, inp: InputItem) -> None:
    world.say(
        f'{child.id} tried the {inp.label} first. {inp.sound} '
        f'For a moment, {child.pronoun()} looked surprised.'
    )


def guide(world: World, helper: Entity, child: Entity, device: Device, inp: InputItem) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} knelt down and pointed to the little sign. '
        f'"This machine needs a {device.input_kind} input," {helper.pronoun()} said softly. '
        f'"The {inp.label} is not the right one."'
    )


def listen_again(world: World, child: Entity, helper: Entity, device: Device, inp: InputItem) -> None:
    child.memes["trust"] += 1
    world.say(
        f'{child.id} took a breath, nodded, and tried again the careful way. '
        f'{inp.sound} The room felt calmer right away.'
    )


def warm_finish(world: World, child: Entity, helper: Entity, device: Device, inp: InputItem) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then the {device.label} hummed happily and began to {device.helpful_result}. "
        f"{child.id} smiled up at {helper.id}. "
        f'"I learned that the right input matters," {child.pronoun()} said. '
        f'"And it helps to ask for help."'
    )
    world.say(
        f"{helper.id} hugged {child.id} and smiled. "
        f'"That is exactly right," {helper.pronoun()} said. '
        f"The little machine kept working, and the cozy room felt bright and safe."
    )


def repair_finish(world: World, child: Entity, helper: Entity, device: Device, inp: InputItem) -> None:
    world.say(
        f"{helper.id} showed {child.id} the right slot and the right {device.input_kind}. "
        f"After one more try, the machine finally {device.helpful_result}."
    )
    world.say(
        f'{child.id} grinned. "Now I know," {child.pronoun()} whispered, '
        f"and {helper.id} smiled back."
    )


def tell(device: Device, inp: InputItem, helper_cfg: Helper, child_name: str, child_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type=helper_cfg.type, role="helper", label=helper_cfg.label))
    machine = world.add(Entity(id="machine", type="thing", label=device.label))
    story_open(world, child, helper, device)
    world.para()
    guide(world, helper, child, device, inp)
    tempt(world, child, inp)
    world.para()
    _use_input(world, child, helper, device, inp)
    if world.facts.get("resolved"):
        listen_again(world, child, helper, device, inp)
        world.para()
        warm_finish(world, child, helper, device, inp)
    else:
        world.say(f"The wrong input did not break anything, but it did make a soft, silly mess of noise.")
        world.para()
        repair_finish(world, child, helper, device, inp)
    world.facts.update(child=child, helper=helper, device=device, input_cfg=inp, machine=machine,
                       outcome="resolved" if world.facts.get("resolved") else "repaired")
    return world


INPUTS = {
    "voice": InputItem("voice", "voice prompt", "voice", False, True, "Beep-beep!", {"voice"}),
    "button": InputItem("button", "button code", "button", False, True, "Click!", {"button"}),
    "card": InputItem("card", "picture card", "card", False, True, "Tap-tap!", {"card"}),
    "spoon": InputItem("spoon", "metal spoon", "spoon", True, False, "Clang!", {"spoon"}),
}

DEVICES = {
    "toast": Device("toast", "toast maker", "button", "Clunk!", "toast crisp and golden", "make breakfast toast", "The toast maker liked a clear button code.", {"breakfast"}, 3),
    "lamp": Device("lamp", "night lamp", "voice", "Buzz!", "shine warmly", "glow a soft light", "The night lamp listened to a calm voice prompt.", {"light"}, 3),
    "musicbox": Device("musicbox", "music box", "card", "Pop!", "play a cheerful tune", "play a cheerful tune", "The music box wanted a picture card input.", {"music"}, 3),
    "plant": Device("plant", "watering helper", "card", "Plip!", "water the flowers gently", "water the flowers gently", "The watering helper expected a picture card input.", {"garden"}, 2),
}

HELPERS = {
    "mom": Helper("mom", "mom", "mother", "kind words", {"family"}),
    "dad": Helper("dad", "dad", "father", "kind words", {"family"}),
    "grandma": Helper("grandma", "grandma", "woman", "kind words", {"family"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for iid, inp in INPUTS.items():
        for did, dev in DEVICES.items():
            if good_combo(inp, dev):
                combos.append((iid, did))
    return combos


@dataclass
@dataclass
class StoryParams:
    device: str
    input_item: str
    helper: str
    child: str
    gender: str
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


KNOWLEDGE = {
    "input": [("What is an input?",
               "An input is the signal or thing you give a machine so it knows what to do. It can be a button, a voice cue, or a card.")],
    "voice": [("What is a voice prompt?",
               "A voice prompt is when a machine listens to your words and uses them as the input.")],
    "button": [("What is a button code?",
                "A button code is a button or set of buttons that you press to tell a machine what to do.")],
    "card": [("What is a picture card?",
              "A picture card can show a machine what you want, so it can choose the right action.")],
    "spoon": [("Why is a spoon not a good machine input?",
                "A spoon is a kitchen tool, not a proper signal for a machine, so it can make noise but not help.")],
    "lesson": [("What does it mean to learn a lesson?",
                "It means you understand something better after trying, making a mistake, or being helped.")],
    "sound": [("Why do machines make sound effects?",
               "Sound effects can show that a machine started, stopped, or made a mistake, so people know what happened.")],
}
KNOWLEDGE_ORDER = ["input", "voice", "button", "card", "spoon", "lesson", "sound"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the word "input" and a gentle sound effect.',
        f"Tell a child-friendly story where {f['child'].id} tries the wrong input on a little machine, then learns the right one with help from {f['helper'].id}.",
        f'Write a cozy story about a machine, a mistaken input, and a lesson learned, with a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, device, inp = f["child"], f["helper"], f["device"], f["input_cfg"]
    items = [
        QAItem("What did the child want to do?", f"{child.id} wanted to make the {device.label} work by giving it the right input."),
        QAItem("What happened first?", f"{child.id} tried the {inp.label} first, and it made a silly sound before the machine settled down."),
        QAItem("How did the helper respond?", f"{helper.id} explained the correct kind of input kindly and showed {child.id} a better way to try again."),
    ]
    if f["outcome"] == "resolved":
        items.append(QAItem("How did the story end?", f"It ended happily, with the {device.label} working and {child.id} learning that the right input matters."))
        items.append(QAItem("What lesson did the child learn?", f"{child.id} learned to ask for help and to listen for the right input before trying again."))
    else:
        items.append(QAItem("How did the story end?", f"It ended warmly after a correction, with the helper showing the right input and the machine finally working."))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["device"].tags) | set(world.facts["input_cfg"].tags) | {"input", "lesson", "sound"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
    lines.append("== (3) World knowledge ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("toast", "button", "mom", "Maya", "girl"),
    StoryParams("lamp", "voice", "dad", "Leo", "boy"),
    StoryParams("musicbox", "card", "grandma", "Zoe", "girl"),
]


def explain_rejection(inp: InputItem, device: Device) -> str:
    if not good_combo(inp, device):
        return f"(No story: {inp.label} is not the right input for the {device.label}. The world wants a real, sensible match.)"
    return "(No story: invalid combination.)"


def asp_facts() -> str:
    import asp
    lines = []
    for iid, inp in INPUTS.items():
        lines.append(asp.fact("input", iid))
        if inp.wrong_fit:
            lines.append(asp.fact("wrong_fit", iid))
        if inp.right_fit:
            lines.append(asp.fact("right_fit", iid))
    for did, dev in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("input_kind", did, dev.input_kind))
        lines.append(asp.fact("sense", did, dev.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
good(I,D) :- input(I), device(D), input_kind(D,K), fits(I,K), right_fit(I), not wrong_fit(I).
sensible(D) :- device(D), sense(D,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good/2."))
    return sorted(set(asp.atoms(model, "good")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid combos")
        rc = 1
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    if set(asp_sensible()) != {d.id for d in sensible_devices()}:
        print("MISMATCH in sensible devices")
        rc = 1
    else:
        print("OK: sensible devices match.")
    try:
        sample = generate(resolve_params(argparse.Namespace(device=None, input_item=None, helper=None, child=None, gender=None, seed=None), random.Random(7)))
        assert sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming input-and-sound-effect storyworld.")
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--input", dest="input_item", choices=INPUTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.device and args.input_item:
        if (args.input_item, args.device) not in combos:
            raise StoryError(explain_rejection(INPUTS[args.input_item], DEVICES[args.device]))
    valid = [c for c in combos if (args.device is None or c[1] == args.device) and (args.input_item is None or c[0] == args.input_item)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    inp, dev = rng.choice(sorted(valid))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(dev, inp, helper, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(DEVICES[params.device], INPUTS[params.input_item], HELPERS[params.helper], params.child, params.gender)
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
        print(asp_program("", "#show good/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible devices: {', '.join(asp_sensible())}\n")
        print("valid combos:")
        for inp, dev in asp_valid_combos():
            print(f"  {inp} -> {dev}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
