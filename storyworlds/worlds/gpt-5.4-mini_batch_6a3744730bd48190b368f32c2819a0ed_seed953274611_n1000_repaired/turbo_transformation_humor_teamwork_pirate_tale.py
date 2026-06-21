#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/turbo_transformation_humor_teamwork_pirate_tale.py
==================================================================================

A small standalone storyworld about a pirate crew, a turbo gadget, a surprising
transformation, and a teamwork fix with a comic payoff.

Premise:
- A pirate crew wants to reach a tiny island cave before sunset.
- Their boat is slow, and a goofy "turbo" contraption is supposed to help.
- The contraption accidentally transforms one crew member into an octopus-like
  helper for a short while.
- The crew must cooperate to steer, laugh, and use the transformed helper's
  new abilities to finish the voyage.
- The ending proves what changed: the crew gets the treasure, and the helper
  returns to normal with a better trick for later.

The domain is intentionally tiny and state-driven. The prose is generated from
simulated meters and memes rather than from a frozen template swap.
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
DELTA_STEP = 1.0
SENSE_MIN = 2

NAMES = ["Pip", "Mara", "Jett", "Nell", "Bo", "Kira", "Sail", "Rook"]
TRAITS = ["brave", "nimble", "sly", "cheerful", "careful", "lively"]


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    detail: str
    weather: str
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
    phrase: str
    effect: str
    kind: str = "gadget"
    makes_noise: bool = False
    makes_transformation: bool = False
    safe: bool = True
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
class Transformation:
    id: str
    label: str
    body: str
    method: str
    benefit: str
    reverses: str
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
    setting: Setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
class StoryParams:
    setting: str
    crew1: str
    crew2: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    device: str
    transform: str
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


def _r_noise(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["turbo"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ship").memes["alarm"] += 1
        out.append("__noise__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["transformed"] < THRESHOLD:
            continue
        sig = ("transformed", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["extra_arms"] += 1
        e.memes["pride"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def best_device() -> Device:
    return max(DEVICES.values(), key=lambda d: d.safe + int(d.makes_transformation))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for did, dev in DEVICES.items():
            for tid, tr in TRANSFORMS.items():
                if dev.safe and dev.makes_transformation and tid in tr.tags:
                    combos.append((sid, did, tid))
    return combos


def no_story_reason(device: Device) -> str:
    return f"(No story: {device.label} is not a sensible turbo tool for a pirate tale.)"


def predict(world: World, actor: Entity, device: Device, transform: Transformation) -> dict:
    sim = world.copy()
    _do_turbo(sim, actor.id, device, transform, narrate=False)
    return {"transformed": sim.get(actor.id).meters["transformed"] >= THRESHOLD,
            "teamwork": sim.get("crew").memes["teamwork"]}


def _do_turbo(world: World, actor_id: str, device: Device, transform: Transformation, narrate: bool = True) -> None:
    actor = world.get(actor_id)
    actor.meters["turbo"] += 1
    actor.meters["transformed"] += 1
    actor.attrs["form"] = transform.body
    propagate(world, narrate=narrate)


def set_sail(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["excited"] += 1
    b.memes["excited"] += 1
    world.say(f"On {setting.place}, {a.id} and {b.id} found a little pirate boat with a squeaky mast.")
    world.say(f"The deck was {setting.detail}, and the tide was too sleepy for a fast escape.")


def need_help(world: World, a: Entity, device: Device) -> None:
    world.say(f'"We need more speed," {a.id} said. "Maybe the {device.label} will help."')


def joke(world: World, b: Entity, device: Device) -> None:
    b.memes["humor"] += 1
    world.say(f'{b.id} pointed at the {device.label} and grinned. "That thing looks like a teapot with ambition!"')


def activate(world: World, a: Entity, b: Entity, device: Device, transform: Transformation) -> None:
    world.say(f"{a.id} pulled the cord. The {device.label} went {device.effect}!")
    world.say(f"With a puff and a wobble, {a.id} felt {transform.method}.")


def transform_scene(world: World, a: Entity, b: Entity, transform: Transformation) -> None:
    a.memes["surprise"] += 1
    a.meters["extra_arms"] += 4
    world.say(f"One blink later, {a.id} had {transform.body}.")
    world.say(f'"Shiver me timbers," {b.id} laughed, "now you can {transform.benefit}!"')


def teamwork(world: World, a: Entity, b: Entity, transform: Transformation) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.get("ship").memes["teamwork"] += 1
    world.say(f"Together they worked the ropes, the sail, and the wheel.")
    world.say(f"{a.id} used {transform.benefit}, while {b.id} steered around the reef.")


def finish(world: World, a: Entity, b: Entity, transform: Transformation) -> None:
    a.meters["transformed"] = 0.0
    a.attrs["form"] = "pirate"
    world.say(f"At last the ship slipped into the cave, and the treasure chest was waiting with a tiny bow.")
    world.say(f"After the job was done, {a.id} popped back to normal, but everyone kept laughing about the turbo trick.")


def tell(setting: Setting, device: Device, transform: Transformation, captain: str = "Pip",
         captain_gender: str = "boy", mate: str = "Mara", mate_gender: str = "girl") -> World:
    world = World(setting)
    crew = world.add(Entity(id="crew", kind="group", type="crew", label="the crew"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    a = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    b = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    world.facts.update(crew=crew, ship=ship, a=a, b=b, device=device, transform=transform)

    set_sail(world, a, b, setting)
    world.para()
    need_help(world, a, device)
    joke(world, b, device)
    activate(world, a, b, device, transform)
    _do_turbo(world, a.id, device, transform)
    world.para()
    transform_scene(world, a, b, transform)
    teamwork(world, a, b, transform)
    world.para()
    finish(world, a, b, transform)
    world.facts.update(outcome="transformed", got_treasure=True)
    return world


SETTINGS = {
    "docks": Setting(id="docks", place="the moonlit docks", detail="sticky with tar and salt", weather="calm"),
    "island": Setting(id="island", place="a tiny island cove", detail="ringed by foamy waves", weather="windy"),
    "reef": Setting(id="reef", place="the reef edge", detail="bright with barnacles", weather="breezy"),
}

DEVICES = {
    "turbo_shell": Device(id="turbo_shell", label="turbo shell", phrase="a shiny turbo shell", effect="BRRRM", makes_noise=True, makes_transformation=True, tags={"turbo"}),
    "turbo_pump": Device(id="turbo_pump", label="turbo pump", phrase="a brass turbo pump", effect="WHOOF", makes_noise=True, makes_transformation=True, tags={"turbo"}),
    "turbo_wheel": Device(id="turbo_wheel", label="turbo wheel", phrase="a spinning turbo wheel", effect="VROOP", makes_noise=True, makes_transformation=True, tags={"turbo"}),
}

TRANSFORMS = {
    "octo_help": Transformation(id="octo_help", label="octopus help", body="eight wiggly helper arms", method="a squishy tickle", benefit="tie knots and lift crates at once", reverses="the tide calmed", tags={"turbo"}),
    "sail_fins": Transformation(id="sail_fins", label="sail fins", body="two finny arms and a very proud tail", method="a funny stretch", benefit="swim the rope across the water", reverses="the spell wore off", tags={"turbo"}),
    "parrot_hat": Transformation(id="parrot_hat", label="parrot hat", body="a feathered crest and a silly squawk", method="a puff of glitter", benefit="keep watch from the mast", reverses="the feathers fell back", tags={"turbo"}),
}


KNOWLEDGE = {
    "turbo": [("What does turbo mean?", "Turbo means extra fast or extra powerful. In stories, it can make a machine or idea go zoom.")],
    "octopus": [("What is an octopus?", "An octopus is a sea animal with eight arms. It can grab, carry, and squeeze into small places.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and share the job. Together, they can do more than one person could do alone.")],
    "humor": [("Why is a funny mistake helpful in a story?", "A funny mistake can make characters laugh, stay calm, and keep trying. That helps the story feel warm instead of scary.")],
    "pirate": [("What does a pirate crew do?", "A pirate crew sails together, watches for danger, and shares the work on the ship.")],
    "transformation": [("What is a transformation?", "A transformation is when something changes into a different form. In a story, that change can create a new problem and a new way to solve it.")],
}

KNOWLEDGE_ORDER = ["pirate", "teamwork", "humor", "turbo", "octopus", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["device"]
    t = f["transform"]
    return [
        f'Write a pirate tale for a young child that includes the word "turbo" and a funny transformation.',
        f"Tell a short story where {f['a'].id} uses the {d.label} and changes into {t.label}, then the crew works together.",
        f"Write a humorous pirate adventure about teamwork, a turbo gadget, and a surprising change into {t.body}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["a"], f["b"]
    d, t = f["device"], f["transform"]
    qa = [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, two pirates who try to help their ship move faster."),
        ("What problem did they face?", f"The boat was too slow, so they needed a turbo idea to reach the cave before sunset."),
        ("What funny thing happened when they used the device?", f"The turbo device changed {a.id} into {t.body}. That made the scene silly, but it also gave the crew a useful new way to work."),
        ("How did they solve the problem?", f"They laughed, shared the work, and used teamwork. {b.id} steered while {a.id} used the new helper arms to tie knots and lift crates."),
        ("How did the story end?", f"They reached the cave and found the treasure, and {a.id} changed back to normal afterward. The ending shows that the turbo mishap became a helpful trick instead of a disaster."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set()
    tags.update(world.facts["device"].tags)
    tags.update(world.facts["transform"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="docks", crew1="Pip", crew2="Mara", captain="Pip", captain_gender="boy", mate="Mara", mate_gender="girl", device="turbo_shell", transform="octo_help"),
    StoryParams(setting="island", crew1="Nell", crew2="Bo", captain="Nell", captain_gender="girl", mate="Bo", mate_gender="boy", device="turbo_pump", transform="sail_fins"),
    StoryParams(setting="reef", crew1="Kira", crew2="Rook", captain="Kira", captain_gender="girl", mate="Rook", mate_gender="boy", device="turbo_wheel", transform="parrot_hat"),
]


ASP_RULES = r"""
turbo_device(D) :- device(D), turbo_tag(D).
transformed(A) :- chosen_device(D), makes_transformation(D), actor(A).
teamwork :- transformed(A), mate(B), actor(A), actor(B).
funny :- transformed(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        if d.makes_transformation:
            lines.append(asp.fact("makes_transformation", did))
        if "turbo" in d.tags:
            lines.append(asp.fact("turbo_tag", did))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        if "turbo" in t.tags:
            lines.append(asp.fact("turbo_tag_transform", tid))
    return "\n".join(lines)

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import asp
    # simple parity gate
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos parity")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # pragma: no cover
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with turbo transformation and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy", "woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(list(DEVICES))
    transform = args.transform or rng.choice(list(TRANSFORMS))
    if device not in DEVICES or transform not in TRANSFORMS:
        raise StoryError("Invalid device or transform.")
    if args.captain_gender and args.captain_gender not in {"girl", "boy", "woman", "man"}:
        raise StoryError("Invalid captain gender.")
    captain_gender = args.captain_gender or rng.choice(["boy", "girl"])
    mate_gender = args.mate_gender or ("girl" if captain_gender == "boy" else "boy")
    captain = args.captain or rng.choice(NAMES)
    mate = args.mate or rng.choice([n for n in NAMES if n != captain])
    if not DEVICES[device].safe:
        raise StoryError(no_story_reason(DEVICES[device]))
    return StoryParams(setting=setting, crew1=captain, crew2=mate, captain=captain, captain_gender=captain_gender, mate=mate, mate_gender=mate_gender, device=device, transform=transform)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.device not in DEVICES:
        raise StoryError("Unknown device.")
    if params.transform not in TRANSFORMS:
        raise StoryError("Unknown transform.")
    world = tell(SETTINGS[params.setting], DEVICES[params.device], TRANSFORMS[params.transform], params.captain, params.captain_gender, params.mate, params.mate_gender)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos:")
        for c in valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
