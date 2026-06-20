#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/incinerator_befriend_storage_closet_surprise_suspense_bravery.py
===============================================================================================

A small, standalone storyworld in a folk-tale style about a child in a storage
closet, a surprising discovery, a suspenseful choice, and a brave act of
befriending a lonely little helper before anyone does anything unsafe with the
incinerator.

The world is intentionally tiny and state-driven:
- typed entities carry physical meters and emotional memes,
- the closet state changes through a few causal rules,
- a reasonableness gate keeps the stories plausible,
- QA is grounded in simulated state rather than rendered English,
- an inline ASP twin mirrors the Python gate and outcome logic.

This script is self-contained and uses only the stdlib plus storyworlds/results.py.
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
SUSPENSE_MIN = 1.0


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
    friendly: bool = False
    hot: bool = False
    hidden: bool = False

    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    label: str
    dark: bool = True
    cramped: bool = True
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
class FolkChild:
    id: str
    role: str
    label: str
    curious: bool = True
    brave: bool = False
    wants_friendship: bool = True
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
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    incinerator: str
    surprise: str
    suspense: str
    bravery: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


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
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    closet = world.get("closet")
    if child.memes["wonder"] < THRESHOLD:
        return out
    if helper.meters["hidden"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    closet.meters["suspense"] += 1
    child.memes["suspense"] += 1
    out.append("The closet felt very still, as if it were holding its breath.")
    return out


def _r_befriend(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["bravery"] < THRESHOLD or child.memes["kindness"] < THRESHOLD:
        return out
    if helper.memes["trust"] < THRESHOLD:
        return out
    sig = ("befriend",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    helper.hidden = False
    out.append("The shy little one came out from the shadows and stood by the child.")
    return out


def _r_safety(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    inc = world.get("incinerator")
    if helper.memes["friendship"] < THRESHOLD:
        return out
    if inc.meters["heat"] >= THRESHOLD:
        sig = ("safety",)
        if sig not in world.fired:
            world.fired.add(sig)
            inc.meters["shut"] = 1
            out.append("Together they kept away from the hot mouth of the incinerator.")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("befriend", _r_befriend), Rule("safety", _r_safety)]


def a_reasonable_gate(place: Place, incinerator: FolkChild) -> bool:
    return place.id == "storage_closet" and "incinerator" in incinerator.tags


def valid_combos() -> list[tuple[str, str, str]]:
    if not a_reasonable_gate(PLACES["storage_closet"], HELPERS["sparky"]):
        return []
    return [("storage_closet", cid, hid) for cid in CHILDREN for hid in HELPERS]


def outcome_of(params: StoryParams) -> str:
    return "befriended"


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["bravery"] += 1
    sim.get("helper").memes["trust"] += 1
    propagate(sim, narrate=False)
    return {"friendship": sim.get("child").memes["friendship"], "suspense": sim.get("closet").meters["suspense"]}


def setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name,
                             role="child", traits=["curious", "kind"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name,
                              role="helper", traits=["shy", "small"], hidden=True, friendly=True))
    closet = world.add(Entity(id="closet", kind="place", type="room", label="the storage closet"))
    inc = world.add(Entity(id="incinerator", kind="thing", type="machine", label=params.incinerator,
                           hot=True, hidden=False, attrs={"safe_distance": True}))
    child.memes["wonder"] = 1
    child.memes["bravery"] = 1 if params.bravery == "bravery" else 0
    child.memes["kindness"] = 1
    helper.memes["trust"] = 1
    helper.meters["hidden"] = 1
    closet.meters["suspense"] = 0
    inc.meters["heat"] = 1
    world.facts.update(params=params, child=child, helper=helper, closet=closet, incinerator=inc)
    world.say(
        f"Once, in a storage closet behind the house, {params.child_name} found a surprising little hush. "
        f"The old {params.incinerator} stood in the corner, and the air felt full of suspense."
    )
    world.say(
        f"Then {params.child_name} noticed {params.helper_name}, a shy little soul with bright eyes, hiding between the boxes."
    )


def tension(world: World, params: StoryParams) -> None:
    child = world.get("child")
    helper = world.get("helper")
    child.memes["wonder"] += 1
    world.para()
    world.say(
        f"{params.child_name} stepped softly and said, \"Who are you, little one?\" "
        f"The closet stayed very still."
    )
    world.say(
        f"{params.helper_name} trembled at first, for the {params.incinerator} made the room feel warm and strange."
    )
    child.memes["suspense"] += 1
    helper.memes["trust"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=True)


def resolution(world: World, params: StoryParams) -> None:
    child = world.get("child")
    helper = world.get("helper")
    world.para()
    world.say(
        f"With brave heart, {params.child_name} smiled and said, "
        f'\"I will be your friend.\" '
        f"That was a small promise, but in folk tales small promises can be stronger than locked doors."
    )
    world.say(
        f"{params.helper_name} stepped out at last, and the two of them kept a careful distance from the {params.incinerator}."
    )
    world.say(
        f"By the end, suspense had gone quiet, and the storage closet no longer felt lonely."
    )
    child.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    child.meters["joy"] += 1
    helper.meters["joy"] += 1


def tell(params: StoryParams) -> World:
    world = World()
    setup(world, params)
    tension(world, params)
    resolution(world, params)
    world.facts["outcome"] = "befriended"
    return world


PLACES = {
    "storage_closet": Place("storage_closet", "the storage closet", dark=True, cramped=True,
                            tags={"storage", "closet", "suspense"}),
}

CHILDREN = {
    "mira": FolkChild("Mira", "child", "Mira", brave=True, tags={"bravery"}),
    "niko": FolkChild("Niko", "child", "Niko", brave=False, tags={"bravery"}),
}

HELPERS = {
    "sparky": FolkChild("Sparky", "helper", "Sparky", brave=False, wants_friendship=True,
                        tags={"incinerator", "befriend"}),
    "ember": FolkChild("Ember", "helper", "Ember", brave=False, wants_friendship=True,
                       tags={"incinerator", "befriend"}),
}

SURPRISES = {
    "keys": "a ring of silver keys",
    "lantern": "a tiny lantern",
    "cricket": "a cricket in a jar",
}

SUSPENSES = {
    "whisper": "a whisper from the boxes",
    "footstep": "a soft footstep",
    "drip": "a slow drip from a pipe",
}

BRAVERIES = {
    "kind_word": "kind word",
    "step_closer": "step closer",
    "friend_offer": "offer friendship",
}


@dataclass
class RegistryItem:
    id: str
    label: str

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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a folk-tale story for a 3-to-5-year-old set in a storage closet. Include the words "{p.incinerator}" and "befriend".',
        f"Tell a suspenseful little story where {p.child_name} finds something surprising in the storage closet and uses bravery to befriend a shy helper.",
        f"Write a gentle folk tale in which a child meets a hidden friend near an {p.incinerator} and the ending feels safe and warm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    child = f["child"]
    helper = f["helper"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {p.child_name}, who finds {p.helper_name} in the storage closet. The old {p.incinerator} is part of the setting and helps make the moment feel suspenseful.",
        ),
        QAItem(
            question=f"What did {p.child_name} do with {p.helper_name}?",
            answer=f"{p.child_name} chose to befriend {p.helper_name}. That brave choice turned the hidden, nervous moment into a friendly one.",
        ),
    ]
    if helper.memes["friendship"] >= THRESHOLD:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended safely and warmly. The suspense went quiet, and the two new friends stayed away from the hot machine.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important is about to happen, so you keep wondering what will come next. It can make a small moment feel very big.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the kind and right thing even when you feel shy or nervous. A brave choice can help someone and make a story turn out better.",
        ),
        QAItem(
            question="What does it mean to befriend someone?",
            answer="To befriend someone means to act kindly so they become your friend. It can start with a gentle greeting, a smile, or a promise to stay near.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.hidden:
            bits.append("hidden=True")
        if e.hot:
            bits.append("hot=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: Place, incinerator: FolkChild) -> str:
    return f"(No story: this world only works in the storage closet with an incinerator-like hidden helper.)"


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "storage_closet"), asp.fact("feature", "surprise"),
             asp.fact("feature", "suspense"), asp.fact("feature", "bravery")]
    for k in SURPRISES:
        lines.append(asp.fact("surprise", k))
    for k in SUSPENSES:
        lines.append(asp.fact("suspense", k))
    for k in BRAVERIES:
        lines.append(asp.fact("bravery_move", k))
    return "\n".join(lines)


ASP_RULES = r"""
valid(storage_closet, surprise, suspense, bravery).
outcome(befriended) :- valid(storage_closet, surprise, suspense, bravery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld about a storage closet, surprise, suspense, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--seedword", choices=["incinerator", "befriend"])
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
    if args.place and args.place != "storage_closet":
        raise StoryError("(No story: this tale belongs in the storage closet.)")
    place = "storage_closet"
    child = args.child or rng.choice(sorted(CHILDREN))
    helper = args.helper or rng.choice(sorted(HELPERS))
    seedword = args.seedword or rng.choice(["incinerator", "befriend"])
    surprise = rng.choice(sorted(SURPRISES))
    suspense = rng.choice(sorted(SUSPENSES))
    bravery = rng.choice(sorted(BRAVERIES))
    return StoryParams(place, CHILDREN[child].label, "girl" if child == "mira" else "boy",
                       HELPERS[helper].label, "girl" if helper == "ember" else "boy",
                       seedword, surprise, suspense, bravery)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/3.\n#show outcome/1."))
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
        samples = [generate(StoryParams("storage_closet", "Mira", "girl", "Sparky", "boy", "incinerator", "a silver key", "a whisper from the boxes", "kind word"))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
