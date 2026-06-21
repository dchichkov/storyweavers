#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pound_inference_refraction_curiosity_myth.py
=============================================================================

A standalone story world in a mythic key: a curious child approaches an old
shrine, notices how moonlight bends through water and crystal, makes an
inference, acts on it, and changes the scene with a small, concrete discovery.

The seed words are woven into the simulated world:
- pound: the heart or drum beats loudly when wonder or worry rises
- inference: the child reasons from observed signs
- refraction: light bends through water and crystal
- curiosity: the motivating emotional meme
- myth: the tone, setting, and ending image

The simulation keeps the narrative state-driven rather than swapping nouns in a
fixed paragraph. It includes a Python reasonableness gate and an inline ASP twin
for parity checks.
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
SENSE_MIN = 2

CURIOUS_TRAITS = {"curious", "watchful", "wise", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    glowing: bool = False
    holds_water: bool = False
    bends_light: bool = False
    reflects: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "priestess"}
        male = {"boy", "father", "dad", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "priest": "priest",
                "priestess": "priestess"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Temple:
    id: str
    name: str
    dark_place: str
    shrine_phrase: str
    wonder_phrase: str
    ending_image: str

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
class Beacon:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = True
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
class PrismPool:
    id: str
    label: str
    phrase: str
    near: str
    refracts: bool = True
    holds_water: bool = True
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


def _r_heartbeat(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["awe"] >= THRESHOLD and ("heartbeat", ent.id) not in world.fired:
            world.fired.add(("heartbeat", ent.id))
            ent.meters["pound"] += 1
            out.append("__pound__")
    return out


def _r_refraction(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if not ent.bends_light:
            continue
        if ent.meters["filled"] < THRESHOLD:
            continue
        sig = ("refraction", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("lamp").meters["seen"] += 1
        out.append("__refraction__")
    return out


CAUSAL_RULES = [
    Rule("heartbeat", "social", _r_heartbeat),
    Rule("refraction", "physical", _r_refraction),
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


def reason_gate(artifact: PrismPool, beacon: Beacon) -> bool:
    return artifact.refracts and beacon.safe


def should_infer(world: World) -> bool:
    child = world.get("child")
    return child.memes["curiosity"] >= THRESHOLD and child.memes["doubt"] >= THRESHOLD


def infer_truth(world: World, beacon: Beacon, pool: PrismPool) -> bool:
    sim = world.copy()
    sim.get("child").memes["curiosity"] += 1
    sim.get("pool").meters["filled"] += 1
    propagate(sim, narrate=False)
    return sim.get("lamp").meters["seen"] >= THRESHOLD and beacon.safe and pool.refracts


def tell_temple(world: World, child: Entity, elder: Entity, temple: Temple,
                beacon: Beacon, pool: PrismPool, response: Response) -> None:
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    child.memes["awe"] += 1
    child.memes["doubt"] += 1
    world.say(
        f"Long ago, beneath the high stones of {temple.name}, {child.id} and "
        f"{elder.id} found {temple.shrine_phrase}. {temple.wonder_phrase}"
    )
    world.say(
        f"{child.id}'s heart began to pound with curiosity. {child.id} peered into "
        f"{temple.dark_place} and whispered that the dark held a secret."
    )


def wonder_turn(world: World, child: Entity, elder: Entity, beacon: Beacon,
                pool: PrismPool) -> None:
    world.say(
        f"In the hollow, a {beacon.label} waited beside {pool.phrase}. {child.id} "
        f"noticed that the water could bend the light, and {child.pronoun()} made "
        f"an inference before speaking."
    )
    world.say(
        f'"If the moonbeam is straight here, but looks broken there, then the '
        f'{pool.label} must be changing it," {child.id} said.'
    )


def warn(world: World, elder: Entity, child: Entity, beacon: Beacon, pool: PrismPool) -> None:
    elder.memes["care"] += 1
    world.say(
        f"{elder.id} listened closely and smiled. \"Your thought is good,\" "
        f"{elder.id} said. \"But we should test it gently, without losing the lamp.\""
    )


def test_theory(world: World, child: Entity, beacon: Beacon, pool: PrismPool) -> None:
    child.meters["steps"] += 1
    pool.meters["filled"] += 1
    world.say(
        f"{child.id} poured a little water into the bowl, and at once the clear "
        f"surface brightened. The moonlight bent inside it, a silver road curving "
        f"through the dark."
    )
    propagate(world, narrate=False)
    if world.get("lamp").meters["seen"] >= THRESHOLD:
        world.say(
            f"The beam split and shone where it had not shone before, as if the "
            f"water had taught it a new path."
        )


def reveal(world: World, child: Entity, temple: Temple, beacon: Beacon, pool: PrismPool) -> None:
    child.memes["joy"] += 1
    child.memes["awe"] += 1
    world.say(
        f"{child.id} laughed softly. \"It was refraction,\" {child.id} said, and "
        f"the word felt as old as the stones and as new as the dawn."
    )
    world.say(
        f"Together they followed the bright curve to the hidden latch, and the "
        f"shrine answered by opening with a low, kind sigh."
    )


def ending(world: World, child: Entity, elder: Entity, temple: Temple) -> None:
    child.memes["peace"] += 1
    elder.memes["peace"] += 1
    world.say(
        f"In the end, {temple.ending_image}, and {child.id} carried that wisdom "
        f"home: wonder can be measured, and an inference can lead a traveler to "
        f"the truth."
    )


def tell(temple: Temple, beacon: Beacon, pool: PrismPool, response: Response,
         child_name: str = "Nia", child_gender: str = "girl",
         elder_name: str = "Aster", elder_gender: str = "woman",
         elder_role: str = "priestess", trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                              role="child", traits=[trait]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender,
                             role="elder", traits=["wise"]))
    shrine = world.add(Entity(id="shrine", type="thing", label="the shrine"))
    lamp = world.add(Entity(id="lamp", type="thing", label="the lamp"))
    water = world.add(Entity(id="pool", type="thing", label=pool.label,
                             bends_light=pool.refracts, holds_water=True))
    world.facts["shrine"] = shrine
    world.facts["lamp"] = lamp
    world.facts["pool"] = water

    tell_temple(world, child, elder, temple, beacon, pool, response)
    world.para()
    wonder_turn(world, child, elder, beacon, pool)
    warn(world, elder, child, beacon, pool)
    if should_infer(world) and reason_gate(pool, beacon) and infer_truth(world, beacon, pool):
        world.para()
        test_theory(world, child, beacon, pool)
        reveal(world, child, temple, beacon, pool)
    else:
        world.para()
        world.say(
            f"The sign stayed hidden, and the pair waited for clearer moonlight "
            f"before making a guess."
        )
    world.para()
    ending(world, child, elder, temple)
    world.facts.update(child=child, elder=elder, temple=temple, beacon=beacon,
                       pool=pool, outcome="revealed" if infer_truth(world, beacon, pool) else "quiet")
    return world


TEMPLE = {
    "moonwell": Temple(
        "moonwell",
        "the Moonwell",
        "a blue-black hollow in the stones",
        "a lamp of polished bronze and a pool as still as sleep",
        "Above them, the old walls held their breath.",
        "the pool was bright, the lamp was lit, and the dark had become a path"),
    "cliff": Temple(
        "cliff",
        "the cliff shrine",
        "a narrow chamber of stone",
        "a glass lamp and a basin of water",
        "Far above, gulls called like distant flutes.",
        "the basin shimmered, the lamp glowed, and the sea wind seemed to bow"),
}

BEACONS = {
    "lamp": Beacon("lamp", "lamp", "a small lamp", "glowed soft as emberlight", safe=True, tags={"light"}),
    "torch": Beacon("torch", "torch", "a torch", "burned bright and loud", safe=False, tags={"fire"}),
}

POOLS = {
    "pool": PrismPool("pool", "pool", "a shallow pool", "beside the lamp", True, True, tags={"water", "refraction"}),
    "basin": PrismPool("basin", "basin", "a clear basin", "near the shrine wall", True, True, tags={"water", "refraction"}),
}

RESPONSES = {
    "study": Response("study", 3, 3, "studied the light until the pattern became clear",
                      "looked too quickly and missed the hidden curve",
                      "studied the light and found the hidden curve", tags={"refraction"}),
    "lift": Response("lift", 2, 2, "lifted the lamp higher and watched the beam move",
                     "lifted the lamp, but the darkness kept the answer",
                     "lifted the lamp and followed the moving beam", tags={"light"}),
}

GIRL_NAMES = ["Nia", "Mara", "Ira", "Lina", "Tala", "Sera"]
BOY_NAMES = ["Orin", "Kian", "Pavo", "Eren", "Milo", "Tavi"]
TRAITS = ["curious", "watchful", "wise", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TEMPLE:
        for b in BEACONS:
            for p in POOLS:
                if reason_gate(POOLS[p], BEACONS[b]):
                    combos.append((t, b, p))
    return combos


@dataclass
@dataclass
class StoryParams:
    temple: str
    beacon: str
    pool: str
    response: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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
    "refraction": [("What is refraction?",
                    "Refraction is when light bends as it moves through water, glass, or another clear material.")],
    "inference": [("What is an inference?",
                  "An inference is a smart guess you make from clues you can see.")],
    "curiosity": [("What is curiosity?",
                   "Curiosity is the feeling that makes you want to look, ask, and learn more.")],
    "pound": [("What can it mean when your heart pounds?",
                "When your heart pounds, it is beating fast because you feel excited, nervous, or afraid.")],
    "moon": [("Why does moonlight look soft?",
               "Moonlight looks soft because the moon only reflects sunlight, so it is gentle and pale.")],
    "water": [("How does clear water help you see light paths?",
                "Clear water can bend light and make it easy to notice bright lines and reflections.")],
}
KNOWLEDGE_ORDER = ["curiosity", "inference", "refraction", "pound", "moon", "water"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the words "pound", '
        f'"inference", and "refraction".',
        f"Tell a small legend where {f['child'].id} follows curiosity in an old shrine, "
        f"makes an inference from light in water, and learns why the beam bends.",
        f"Write a gentle myth about a child and a wise elder discovering that refraction "
        f"can reveal a hidden path.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, elder, temple, pool, beacon = f["child"], f["elder"], f["temple"], f["pool"], f["beacon"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id}, who went to an old shrine together."),
        ("Why did {0} stay in the dark place?".format(child.id),
         f"{child.id} stayed because curiosity pulled {child.pronoun('object')} closer to the hidden place. The child wanted to understand the strange light instead of turning away."),
        ("What did the child figure out?",
         f"{child.id} made an inference that the water was changing the moonlight. That was true because the pool bent the beam through refraction."),
    ] + ([
        ("How did they find the hidden path?",
         f"They poured water into the pool, watched the light bend, and followed the bright curve to the latch. The changing line showed the way to the secret opening."),
        ("How did the story end?",
         f"It ended with the shrine opening and {child.id} carrying the lesson home. The old place became understandable instead of mysterious.")
    ] if f.get("outcome") == "revealed" else [
        ("How did the story end?",
         f"It ended quietly, with the pair waiting for clearer moonlight before guessing again. Even so, curiosity stayed alive in {child.id}'s heart.")
    ])


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "inference", "refraction", "pound", "moon", "water"}
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
        flags = [n for n, on in (("glowing", e.glowing), ("holds_water", e.holds_water),
                                 ("bends_light", e.bends_light), ("reflects", e.reflects)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moonwell", "lamp", "pool", "study", "Nia", "girl", "Aster", "woman"),
    StoryParams("cliff", "lamp", "basin", "lift", "Orin", "boy", "Mira", "woman"),
]


def explain_rejection(beacon: Beacon, pool: PrismPool) -> str:
    if not reason_gate(pool, beacon):
        return "(No story: this pair cannot show refraction clearly enough for a child-sized legend.)"
    return "(No story: the requested choices do not form a reasonable myth.)"


def outcome_of(params: StoryParams) -> str:
    return "revealed"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TEMPLE:
        lines.append(asp.fact("temple", tid))
    for bid, b in BEACONS.items():
        lines.append(asp.fact("beacon", bid))
        if b.safe:
            lines.append(asp.fact("safe", bid))
    for pid, p in POOLS.items():
        lines.append(asp.fact("pool", pid))
        if p.refracts:
            lines.append(asp.fact("refracts", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, B, P) :- temple(T), beacon(B), pool(P), safe(B), refracts(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            temple=None, beacon=None, pool=None, response=None, child=None,
            child_gender=None, elder=None, elder_gender=None, seed=None
        ), _random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic curiosity/refraction story world.")
    ap.add_argument("--temple", choices=TEMPLE)
    ap.add_argument("--beacon", choices=BEACONS)
    ap.add_argument("--pool", choices=POOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
              if (args.temple is None or c[0] == args.temple)
              and (args.beacon is None or c[1] == args.beacon)
              and (args.pool is None or c[2] == args.pool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    temple, beacon, pool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(["Aster", "Mira", "Sage", "Ivo"])
    return StoryParams(temple, beacon, pool, response, child, child_gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(TEMPLE[params.temple], BEACONS[params.beacon], POOLS[params.pool],
                 RESPONSES[params.response], params.child, params.child_gender,
                 params.elder, params.elder_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
