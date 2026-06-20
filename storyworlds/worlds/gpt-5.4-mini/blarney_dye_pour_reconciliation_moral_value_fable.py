#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blarney_dye_pour_reconciliation_moral_value_fable.py
====================================================================================

A small fable-like storyworld about a boastful trickster, a spilled dye pot,
and a repaired friendship. The domain is tuned for the seed words
"blarney", "dye", and "pour", with reconciliation and a moral value ending.

The world is intentionally simple:
- two animal characters with typed physical meters and emotional memes
- a dye pot, a cloth, and a shared stream-side setting
- a causal accident (pouring dye) that stains the cloth
- a repair act (washing, apology, and sharing the work) that restores calm
- an explicit moral value rendered as the closing lesson

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports results eagerly
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "vixen", "girl", "mother", "woman"}
        male = {"he", "boy", "male", "father", "man", "rooster", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str

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
class Dye:
    id: str
    label: str
    color: str
    source: str
    makes_stain: bool = True
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
class Cloth:
    id: str
    label: str
    phrase: str
    can_stain: bool = True
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
class Repair:
    id: str
    label: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    pourer = world.entities.get("pourer")
    cloth = world.entities.get("cloth")
    dye_pot = world.entities.get("dye_pot")
    if not pourer or not cloth or not dye_pot:
        return out
    if pourer.meters["pouring"] < THRESHOLD:
        return out
    sig = ("stain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cloth.meters["stained"] += 1
    cloth.meters["dye"] += 1
    cloth.memes["sadness"] += 1
    world.entities["stream"].meters["colored"] += 1
    out.append("__stain__")
    return out


def _r_mend(world: World) -> list[str]:
    cloth = world.entities.get("cloth")
    mender = world.entities.get("mender")
    if not cloth or not mender:
        return []
    if cloth.meters["stained"] < THRESHOLD or cloth.meters["washed"] >= THRESHOLD:
        return []
    sig = ("mend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cloth.meters["washed"] += 1
    cloth.meters["stained"] = 0.0
    cloth.memes["relief"] += 1
    mender.memes["kindness"] += 1
    return ["__mend__"]


CAUSAL_RULES = [Rule("stain", "physical", _r_stain), Rule("mend", "social", _r_mend)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def reasonableness_ok(dye: Dye, cloth: Cloth) -> bool:
    return dye.makes_stain and cloth.can_stain


def stain_severity(delay: int) -> int:
    return 1 + delay


def can_reconcile(repair: Repair, delay: int) -> bool:
    return repair.power >= stain_severity(delay)


def predict(world: World) -> dict:
    sim = world.copy()
    dye_it(sim, narrate=False)
    return {
        "stained": sim.get("cloth").meters["stained"] >= THRESHOLD,
        "stream_colored": sim.get("stream").meters["colored"] >= THRESHOLD,
    }


def dye_it(world: World, narrate: bool = True) -> None:
    pourer = world.get("pourer")
    cloth = world.get("cloth")
    pourer.meters["pouring"] += 1
    cloth.meters["in_path"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, trickster: Entity, friend: Entity, setting: Setting) -> None:
    trickster.memes["confidence"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"At {setting.place}, under {setting.scene}, {trickster.id} and {friend.id} worked by a little table."
    )
    world.say(
        f"{trickster.id} loved a clever bit of blarney, and {friend.id} loved honest work more than talk."
    )


def conflict(world: World, trickster: Entity, friend: Entity, dye: Dye, cloth: Cloth) -> None:
    friend.memes["worry"] += 1
    world.say(
        f"{trickster.id} began with blarney, saying the dye would make the cloth splendid, "
        f"but the pot wobbled near the {cloth.label}."
    )
    world.say(
        f'"Let me just pour it," {trickster.id} said, and the idea sounded quick and easy.'
    )


def spill(world: World, dye: Dye, cloth: Cloth) -> None:
    world.say(
        f"The dye tipped at once. {dye.label.capitalize()} spilled in a bright rush and stained the {cloth.label}."
    )
    world.say("A little blue trail ran along the stones and into the stream.")


def reconcile(world: World, trickster: Entity, friend: Entity, repair: Repair, cloth: Cloth) -> None:
    trickster.memes["shame"] += 1
    friend.memes["mercy"] += 1
    world.say(
        f"Then {trickster.id} bowed their head and spoke plain truth. {friend.id} answered with a calm nod."
    )
    world.say(
        f"{friend.id} came with warm water and {repair.text.replace('{cloth}', cloth.label)}."
    )
    world.say("The two friends worked side by side until the stain faded.")


def lesson(world: World, trickster: Entity, friend: Entity, dye: Dye, cloth: Cloth) -> None:
    trickster.memes["peace"] += 1
    friend.memes["peace"] += 1
    world.say("At last, they smiled at one another again.")
    world.say(
        f"The moral was clear: blarney may glitter, but truth and patience mend what careless pouring can harm."
    )
    if cloth.meters["washed"] >= THRESHOLD:
        world.say(f"In the end, the {cloth.label} was clean once more, and the stream ran clear.")


def tell(setting: Setting, dye: Dye, cloth: Cloth, repair: Repair,
         trickster_name: str = "Fox", friend_name: str = "Heron",
         trickster_type: str = "fox", friend_type: str = "heron",
         delay: int = 0) -> World:
    world = World()
    trickster = world.add(Entity(id="trickster", kind="character", type=trickster_type, label=trickster_name, role="trickster"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    world.add(Entity(id="stream", type="place", label="stream"))
    world.add(Entity(id="dye_pot", type="thing", label=dye.label))
    world.add(Entity(id="cloth", type="thing", label=cloth.label))
    world.add(Entity(id="mender", kind="character", type=friend_type, label=friend_name, role="mender"))

    setup(world, trickster, friend, setting)
    world.para()
    conflict(world, trickster, friend, dye, cloth)

    if delay < 0:
        raise StoryError("delay must be nonnegative")
    if can_reconcile(repair, delay):
        dye_it(world)
        world.para()
        spill(world, dye, cloth)
        world.para()
        reconcile(world, trickster, friend, repair, cloth)
        world.para()
        lesson(world, trickster, friend, dye, cloth)
        outcome = "reconciled"
    else:
        dye_it(world)
        world.para()
        spill(world, dye, cloth)
        world.para()
        world.say(
            f"The stain spread too far, and the friends could only watch the water darken."
        )
        world.say("Even so, they promised to tell the truth next time and begin again more gently.")
        outcome = "stained"

    world.facts.update(
        setting=setting, dye=dye, cloth=cloth, repair=repair,
        trickster=trickster, friend=friend, delay=delay, outcome=outcome
    )
    return world


SETTINGS = {
    "riverbank": Setting("riverbank", "the riverbank", "the willow shade"),
    "courtyard": Setting("courtyard", "the courtyard", "the sunlit wall"),
    "garden": Setting("garden", "the garden", "the bee-buzzing hedge"),
}

DYES = {
    "blue": Dye("blue", "blue dye", "blue", "berries", tags={"dye", "blue"}),
    "red": Dye("red", "red dye", "red", "roots", tags={"dye", "red"}),
    "gold": Dye("gold", "gold dye", "gold", "flowers", tags={"dye", "gold"}),
}

CLOTHS = {
    "cloth": Cloth("cloth", "cloth", "a clean cloth", tags={"cloth"}),
    "banner": Cloth("banner", "banner", "a bright banner", tags={"cloth"}),
    "apron": Cloth("apron", "apron", "a work apron", tags={"cloth"}),
}

REPAIRS = {
    "wash": Repair("wash", "wash", 2, 2, "washed the cloth in warm water", "could not wash the stain away", "washed the cloth clean"),
    "rinse": Repair("rinse", "rinse", 3, 3, "rinsed the cloth and rubbed the stain out gently", "could not rinse the stain away", "rinsed the cloth clean"),
    "share": Repair("share", "share", 2, 2, "shared the scrubbing and apologized at once", "could not set things right", "shared the work and apologized"),
}

TRAITS = ["clever", "kind", "proud", "patient", "careful"]
NAMES = ["Fox", "Hare", "Robin", "Mole", "Stork"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    dye: str
    cloth: str
    repair: str
    trickster_name: str
    friend_name: str
    seed: Optional[int] = None
    delay: int = 0

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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DYES:
            for c in CLOTHS:
                if reasonableness_ok(DYES[d], CLOTHS[c]):
                    combos.append((s, d, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that includes the words "blarney", "dye", and "pour".',
        f"Tell a short moral tale where {f['trickster'].label} uses blarney, then pours dye and must make amends.",
        f"Write a gentle reconciliation story with a clear moral value about telling the truth after a spill.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trickster = f["trickster"]
    friend = f["friend"]
    cloth = f["cloth"]
    repair = f["repair"]
    items = [
        QAItem(
            question="What did the trickster do first?",
            answer=f"{trickster.label} began with blarney and tried to make the plan sound harmless. That talk came before the dye was poured.",
        ),
        QAItem(
            question="What happened when the dye was poured?",
            answer=f"The dye spilled onto the {cloth.label} and left it stained. The stream also picked up some color, which showed why the spill mattered.",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"They spoke honestly, apologized, and used the {repair.label} plan to wash the cloth together. Working side by side helped their friendship settle again.",
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is blarney?", "Blarney is flattering or smooth talk that may sound charming, but it can hide what someone really means."),
        QAItem("What is dye?", "Dye is a colored liquid or powder used to change the color of cloth or other materials."),
        QAItem("What does pour mean?", "To pour is to tip a liquid so it flows from one place to another."),
        QAItem("Why should people be careful with dye?", "Dye can stain cloth and surfaces, so it is best used carefully and with clean hands."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("riverbank", "blue", "cloth", "wash", "Fox", "Heron", delay=0),
    StoryParams("garden", "red", "banner", "share", "Fox", "Stork", delay=0),
    StoryParams("courtyard", "gold", "apron", "rinse", "Robin", "Mole", delay=1),
]


def explain_rejection(dye: Dye, cloth: Cloth) -> str:
    if not reasonableness_ok(dye, cloth):
        return f"(No story: {dye.label} can stain, but {cloth.label} cannot reasonably be repaired in this fable setup.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "reconciled" if can_reconcile(REPAIRS[params.repair], params.delay) else "stained"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DYES.items():
        lines.append(asp.fact("dye", did))
        if d.makes_stain:
            lines.append(asp.fact("makes_stain", did))
    for cid, c in CLOTHS.items():
        lines.append(asp.fact("cloth", cid))
        if c.can_stain:
            lines.append(asp.fact("can_stain", cid))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
stain(D,C) :- dye(D), cloth(C), makes_stain(D), can_stain(C).
sensible(R) :- repair(R), sense(R,S), sense_min(M), S >= M.
valid(S,D,C) :- setting(S), stain(D,C).
reconciled(R) :- sensible(R), power(R,P), delay(D), need(N), P >= N.
need(N) :- delay(D), N = 1 + D.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("delay", params.delay),
        asp.fact("need", 1 + params.delay),
        asp.fact("power", params.repair, REPAIRS[params.repair].power),
    ])
    model = asp.one_model(asp_program(scenario, "#show reconciled/1."))
    return "reconciled" if asp.atoms(model, "reconciled") else "stained"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {r.id for r in sensible_repairs()}:
        rc = 1
        print("MISMATCH in sensible repairs.")
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p)
            break
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    if rc == 0:
        print("OK: ASP parity and story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about blarney, dye, pour, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dye", choices=DYES)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--trickster-name")
    ap.add_argument("--friend-name")
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
    if args.dye and args.cloth and not reasonableness_ok(DYES[args.dye], CLOTHS[args.cloth]):
        raise StoryError(explain_rejection(DYES[args.dye], CLOTHS[args.cloth]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.dye is None or c[1] == args.dye)
              and (args.cloth is None or c[2] == args.cloth)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, dye, cloth = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(REPAIRS))
    return StoryParams(
        setting=setting, dye=dye, cloth=cloth, repair=repair,
        trickster_name=args.trickster_name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice([n for n in NAMES if n != (args.trickster_name or "")]),
        seed=None, delay=args.delay if args.delay is not None else rng.randint(0, 2)
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DYES[params.dye], CLOTHS[params.cloth], REPAIRS[params.repair],
                 params.trickster_name, params.friend_name, delay=params.delay)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.trickster_name} and {p.friend_name}: {p.dye} over {p.cloth} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
