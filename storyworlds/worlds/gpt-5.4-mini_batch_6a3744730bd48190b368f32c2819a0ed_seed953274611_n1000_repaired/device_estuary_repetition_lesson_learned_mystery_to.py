#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/device_estuary_repetition_lesson_learned_mystery_to.py
======================================================================================

A small heartwarming storyworld about a child, a curious device, and a mystery at
the estuary. The story leans on repetition, a lesson learned, and a gentle
mystery-to-solve structure: something keeps happening, the characters investigate
it, learn what it means, and end with a warm, changed closing image.

The estuary is a place where a river meets the sea. In this world, a child finds
a simple device there: a little marker device that flashes, clicks, or beeps when
the tide changes. The repeated signal becomes the mystery. The answer is not
scary: the device is simply trying to warn that the water is rising, and once the
child understands it, they use the clue to help someone safe and calm.

The story is generated from a simulated world state rather than from a frozen
paragraph with swapped nouns. Emotional state and physical state both matter.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Place:
    id: str
    label: str
    waterline: str
    detail: str
    safe_spot: str
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
class Device:
    id: str
    label: str
    phrase: str
    signal: str
    purpose: str
    wear: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Clue:
    id: str
    label: str
    message: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_signal(world: World) -> list[str]:
    out: list[str] = []
    device = world.entities.get("device")
    if not device or device.meters["active"] < THRESHOLD:
        return out
    sig = ("signal", device.id, int(device.meters["ticks"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    device.meters["ticks"] += 1
    out.append("__repeat__")
    if device.meters["ticks"] >= 2:
        world.get("child").memes["curious"] += 1
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    device = world.entities.get("device")
    if not device:
        return out
    if device.meters["ticks"] < 2 or world.facts.get("solved"):
        return out
    sig = ("worry", device.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("parent").memes["concern"] += 1
    out.append("__worry__")
    return out


RULES = [Rule("signal", _r_signal), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    sent: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                sent.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for s in sent:
            world.say(s)
    return sent


def explain_repetition(world: World, device: Device) -> str:
    return f"The {device.label} kept repeating its {device.signal.lower()} because it was trying to help."


def predict_solution(world: World, device_id: str) -> dict:
    sim = world.copy()
    solve_mystery(sim, narrate=False)
    return {"solved": sim.facts.get("solved", False), "signal": sim.get(device_id).meters["ticks"]}


def build_scene(place: Place, device: Device, clue: Clue) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="girl", role="observer", traits=["gentle"]))
    parent = world.add(Entity(id="parent", kind="character", type="mother", role="helper", traits=["calm"]))
    world.add(Entity(id="device", kind="thing", type="device", label=device.label, attrs={"purpose": device.purpose}))
    world.add(Entity(id="estuary", kind="place", type="place", label=place.label, attrs={"waterline": place.waterline}))
    world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label))

    child.memes["curious"] = 1.0
    parent.memes["love"] = 1.0
    world.facts.update(place=place, device=device, clue=clue, child=child, parent=parent)
    return world


def introduce(world: World, child: Entity, place: Place, device: Device) -> None:
    world.say(
        f"At the {place.label}, where the river met the sea, {child.id} found a little {device.label}."
    )
    world.say(
        f"It was a simple {device.id}, and {device.signal.lower()}! it went again and again."
    )


def repeat_beat(world: World, device: Device, clue: Clue) -> None:
    device.meters["active"] = 1.0
    world.say(
        f"{device.signal}! Then a pause. Then {device.signal.lower()}! again."
    )
    world.say(
        f"{clue.message}"
    )
    propagate(world, narrate=False)


def investigate(world: World, child: Entity, parent: Entity, place: Place, device: Device) -> None:
    child.memes["curious"] += 1
    world.say(
        f"{child.id} listened carefully and looked at the {device.label}."
    )
    world.say(
        f"{child.id} looked at the water, then at the {device.label}, then at the water again."
    )
    if device.meters["ticks"] >= 2:
        world.say(
            f"Each time the little light blinked, the answer felt closer."
        )


def solve_mystery(world: World, narrate: bool = True) -> None:
    place: Place = world.facts["place"]
    device: Device = world.facts["device"]
    clue: Clue = world.facts["clue"]
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]

    if narrate:
        introduce(world, child, place, device)
        world.para()
    repeat_beat(world, device, clue)
    investigate(world, child, parent, place, device)

    if device.meters["ticks"] >= 2:
        if narrate:
            world.para()
        world.facts["solved"] = True
        world.say(
            f"Then {child.id} understood: the {device.label} was not broken at all. It was warning that the water was rising."
        )
        world.say(
            f"{parent.id} smiled, and together they moved the picnic basket to {place.safe_spot}."
        )
        world.say(
            f"The {device.label} clicked one last time, and this time the sound felt kind."
        )
        world.say(
            f"By evening, the path stayed dry, the basket stayed safe, and {child.id} kept the {device.label} close like a small friend."
        )
    else:
        world.facts["solved"] = False
        if narrate:
            world.para()
        world.say(
            f"{child.id} was still not sure what the repeating sound meant, so {parent.id} listened too."
        )
        world.say(
            f"Together they waited, watched the tide, and the answer arrived in time."
        )


PLACE_REGISTRY = {
    "rivermouth": Place(
        id="rivermouth",
        label="river mouth estuary",
        waterline="the tide comes and goes",
        detail="the salty edge where reeds lean over the water",
        safe_spot="the high bench above the reeds",
        tags={"estuary", "water", "tide"},
    ),
    "boardwalk": Place(
        id="boardwalk",
        label="boardwalk by the estuary",
        waterline="the tide brushes the pilings",
        detail="a wooden path with gulls resting nearby",
        safe_spot="the steps up by the café",
        tags={"estuary", "water", "tide"},
    ),
    "marsh": Place(
        id="marsh",
        label="quiet marsh estuary",
        waterline="the water slips in and out of the grass",
        detail="soft mud, reeds, and shining little channels",
        safe_spot="the stone wall above the marsh",
        tags={"estuary", "water", "tide"},
    ),
}

DEVICE_REGISTRY = {
    "tide_lamp": Device(
        id="tide_lamp",
        label="tide lamp",
        phrase="a tide lamp",
        signal="Blink",
        purpose="to warn when the tide rises",
        wear="a bright shell-shaped case",
        tags={"device", "signal", "tide"},
    ),
    "beacon_box": Device(
        id="beacon_box",
        label="beacon box",
        phrase="a little beacon box",
        signal="Beep",
        purpose="to call attention when water changes",
        wear="a clipped-on strap",
        tags={"device", "signal", "tide"},
    ),
    "marker_device": Device(
        id="marker_device",
        label="marker device",
        phrase="a small marker device",
        signal="Click",
        purpose="to show where the safe line should be",
        wear="a blue ribbon",
        tags={"device", "signal", "tide"},
    ),
}

CLUE_REGISTRY = {
    "blink": Clue(id="blink", label="blink clue", message="It blinked near the waterline, as if asking to be noticed.", tags={"mystery"}),
    "beep": Clue(id="beep", label="beep clue", message="It beeped in a patient rhythm, like a whisper that would not give up.", tags={"mystery"}),
    "click": Clue(id="click", label="click clue", message="It clicked, clicked, clicked, and each click seemed to point at the tide.", tags={"mystery"}),
}


@dataclass
class StoryParams:
    place: str
    device: str
    clue: str
    child_name: str
    child_gender: str
    parent_name: str
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
    combos = []
    for p in PLACE_REGISTRY:
        for d in DEVICE_REGISTRY:
            for c in CLUE_REGISTRY:
                combos.append((p, d, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming estuary mystery storyworld.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--device", choices=DEVICE_REGISTRY)
    ap.add_argument("--clue", choices=CLUE_REGISTRY)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
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
              if (args.place is None or c[0] == args.place)
              and (args.device is None or c[1] == args.device)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, device, clue = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mina", "Lena", "Toby", "Noah", "Iris", "Ezra"])
    parent_name = args.parent_name or rng.choice(["Mom", "Dad"])
    return StoryParams(place=place, device=device, clue=clue, child_name=child_name,
                       child_gender=child_gender, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACE_REGISTRY[params.place]
        device = DEVICE_REGISTRY[params.device]
        clue = CLUE_REGISTRY[params.clue]
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc.args[0]}") from exc
    world = build_scene(place, device, clue)
    # customize names into entities
    child = world.get("child")
    parent = world.get("parent")
    child.id = params.child_name
    child.type = params.child_gender
    parent.id = params.parent_name
    parent.type = "mother" if params.parent_name == "Mom" else "father"
    world.entities[params.child_name] = world.entities.pop("child")
    world.entities[params.parent_name] = world.entities.pop("parent")
    world.facts["child"] = world.get(params.child_name)
    world.facts["parent"] = world.get(params.parent_name)

    solve_mystery(world, narrate=True)
    story = world.render()

    prompts = [
        f"Write a heartwarming mystery story that includes the words device and estuary.",
        f"Tell a gentle story where {params.child_name} hears a repeating signal from a device at the estuary and learns what it means.",
        f"Write a small child-friendly mystery where a device keeps clicking or beeping by an estuary until the child solves it kindly.",
    ]

    child_ent = world.get(params.child_name)
    parent_ent = world.get(params.parent_name)
    story_qa = [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was what the repeating signal from the device meant. It turned out to be a tide warning, so the sound was helpful, not scary.",
        ),
        QAItem(
            question=f"How did {params.child_name} solve the mystery?",
            answer=f"{params.child_name} listened, looked at the estuary, and noticed the signal repeating near the waterline. Then {child_ent.pronoun()} understood that the tide was rising and helped move the picnic basket to the safe spot.",
        ),
        QAItem(
            question=f"What lesson did {params.child_name} learn?",
            answer=f"{params.child_name} learned to pay attention to repeated clues instead of ignoring them. The device kept repeating because it was trying to help, and careful listening led to the answer.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an estuary?",
            answer="An estuary is a place where a river meets the sea. The water there changes with the tide, so it can rise and fall in a noticeable way.",
        ),
        QAItem(
            question="Why might a device repeat a signal?",
            answer="A device might repeat a signal so people will notice it. Repetition can be a way to warn, guide, or ask for attention.",
        ),
        QAItem(
            question="Why is it kind to solve a mystery calmly?",
            answer="Calmly solving a mystery helps everyone think clearly and stay safe. It also makes it easier to notice clues and understand what they mean.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- place_fact(P).
device(D) :- device_fact(D).
clue(C) :- clue_fact(C).
valid(P,D,C) :- place(P), device(D), clue(C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place_fact", p))
    for d in DEVICE_REGISTRY:
        lines.append(asp.fact("device_fact", d))
    for c in CLUE_REGISTRY:
        lines.append(asp.fact("clue_fact", c))
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
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: ASP matches Python and generation smoke test passed.")
    return rc


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
    StoryParams(place="rivermouth", device="tide_lamp", clue="blink", child_name="Mina", child_gender="girl", parent_name="Mom"),
    StoryParams(place="boardwalk", device="beacon_box", clue="beep", child_name="Toby", child_gender="boy", parent_name="Dad"),
    StoryParams(place="marsh", device="marker_device", clue="click", child_name="Iris", child_gender="girl", parent_name="Mom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
