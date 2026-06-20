#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mixture_handle_magic_friendship_conflict_myth.py
================================================================================

A standalone storyworld for a small mythic tale about a magical mixture,
a handle on a vessel, friendship, conflict, and a gentle resolution.

Premise:
- Two friends prepare a magic mixture in a sacred bowl with a carved handle.
- A quarrel rises when one friend wants to use the mixture for boastful magic.
- The wiser friend notices the danger, a mentor intervenes, and the friends choose
  to use the mixture for healing and a lantern blessing instead.

This world stays tiny and classical: typed entities, physical meters and emotional
memes, a short forward-chained causal model, grounded QA, and an inline ASP twin.
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
    sacred: bool = False
    fragile: bool = False
    useful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return {"mother": "mom", "father": "dad", "priestess": "priestess", "priest": "priest"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    name: str
    sacred: bool = False
    light: str = ""
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
class Vessel:
    id: str
    label: str
    phrase: str
    handle: str
    fragile: bool = False
    useful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Mixture:
    id: str
    label: str
    phrase: str
    magic: bool = False
    healing: bool = False
    bright: bool = False
    volatile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Guide:
    id: str
    type: str
    label: str
    phrase: str
    wisdom: int
    calm: int
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for mix in list(world.entities.values()):
        if mix.meters["unbalanced"] < THRESHOLD:
            continue
        sig = ("spill", mix.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in world.characters():
            char.memes["fear"] += 1
        out.append("__spill__")
    return out


def _r_harmony(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes["reconciled"] < THRESHOLD:
            continue
        sig = ("harmony", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["joy"] += 1
        out.append("__harmony__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("harmony", "social", _r_harmony)]


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


def handle_risk(vessel: Vessel, place: Place) -> bool:
    return vessel.fragile and place.sacred


def sensible_fixes() -> list[str]:
    return [k for k, v in FIXES.items() if v.wisdom >= 2]


def fix_can_help(fix: "Fix", vessel: Vessel, mix: Mixture, place: Place) -> bool:
    return fix.power >= (1 + int(mix.volatile) + int(place.sacred))


def predict_spill(world: World, vessel_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(vessel_id), narrate=False)
    return {"spilled": sim.get(vessel_id).meters["spilled"] >= THRESHOLD}


def _do_magic(world: World, vessel: Entity, narrate: bool = True) -> None:
    vessel.meters["handled"] += 1
    vessel.meters["unbalanced"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, place: Place, vessel: Vessel, mix: Mixture) -> None:
    world.say(
        f"Long ago, at {place.name}, {a.id} and {b.id} were friends who kept a sacred task. "
        f"They carried {vessel.phrase}, and inside it rested {mix.phrase}."
    )
    world.say(
        f"The bowl had a carved handle, so it could be lifted with care, and the old priests said the {mix.label} should never be wasted."
    )
    a.memes["trust"] += 1
    b.memes["trust"] += 1


def urge(world: World, a: Entity, mix: Mixture) -> None:
    a.memes["desire"] += 1
    world.say(f"{a.id} leaned close and whispered, \"If the {mix.label} is magic, we should use it for something grand.\"")


def warn(world: World, b: Entity, a: Entity, mix: Mixture, guide: Entity, place: Place) -> None:
    pred = predict_spill(world, "vessel")
    b.memes["care"] += 1
    world.facts["predicted_spill"] = pred["spilled"]
    world.say(
        f"{b.id} shook {b.pronoun('possessive')} head. \"No, {a.id}. Not for boasting. "
        f"The handle is for steady hands, and a sacred place asks for a gentle heart.\""
    )
    if pred["spilled"]:
        world.say(f"{guide.label_word.capitalize()} watched them from the doorway, already worried about the {mix.label}.")


def quarrel(world: World, a: Entity, b: Entity) -> None:
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(f"The friends frowned at each other, and for a little while their friendship felt tight like a knot.")


def guide_step(world: World, guide: Entity, a: Entity, b: Entity, place: Place, mix: Mixture) -> None:
    guide.memes["calm"] += 1
    world.say(
        f"Then {guide.id} came with slow feet and a quiet voice. \"A true wonder is not made by showing off,\" {guide.pronoun()} said. "
        f"\"Use the {mix.label} to mend what is hurt, and let the handle help you carry it safely.\""
    )
    a.memes["reconsider"] += 1
    b.memes["hope"] += 1


def choose_good_use(world: World, a: Entity, b: Entity, mix: Mixture, place: Place) -> None:
    a.memes["reconciled"] += 1
    b.memes["reconciled"] += 1
    world.say(
        f"{a.id} looked down, then nodded. {b.id} nodded too. Together they lifted the bowl by its handle and walked to the sleeping herbs at the shrine."
    )


def heal(world: World, mix: Mixture, place: Place) -> None:
    world.say(
        f"They poured the {mix.label} into a clay lamp. The glow rose like dawn, soft and gold, and the old stones warmed as if they remembered summer."
    )
    if mix.healing:
        world.say(f"The mixture soothed the cracked roots and made the little garden breathe easier.")
    if mix.bright:
        world.say(f"One bright ribbon of light climbed from the lamp and hung under the temple roof.")


def resolve(world: World, a: Entity, b: Entity, mix: Mixture) -> None:
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f"For a moment nobody spoke. Then the friends smiled at last, because the strongest magic was the one that kept them together."
    )


def tell(place: Place, vessel: Vessel, mix: Mixture, fix: "Fix",
         hero_a: str = "Mira", hero_b: str = "Kellan", guide_name: str = "Orin",
         a_gender: str = "girl", b_gender: str = "boy", guide_gender: str = "priest") -> World:
    world = World(place)
    a = world.add(Entity(id=hero_a, kind="character", type=a_gender, role="friend", traits=["curious"]))
    b = world.add(Entity(id=hero_b, kind="character", type=b_gender, role="friend", traits=["proud"]))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide", traits=["wise"]))
    bowl = world.add(Entity(id="vessel", type="thing", label=vessel.label, fragile=vessel.fragile, useful=vessel.useful))
    bowl.meters["handled"] = 0.0
    bowl.meters["unbalanced"] = 0.0

    opening(world, a, b, place, vessel, mix)
    world.para()
    urge(world, a, mix)
    warn(world, b, a, mix, guide, place)
    quarrel(world, a, b)
    world.para()
    guide_step(world, guide, a, b, place, mix)
    choose_good_use(world, a, b, mix, place)
    heal(world, mix, place)
    resolve(world, a, b, mix)

    world.facts.update(
        place=place, vessel=vessel, mix=mix, fix=fix, a=a, b=b, guide=guide,
        outcome="reconciled", handle=bowl, story_tone="myth",
    )
    return world


@dataclass
class Fix:
    id: str
    label: str
    wisdom: int
    power: int
    phrase: str
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


PLACES = {
    "temple": Place("temple", "the moon temple", sacred=True, light="moonlight", tags={"sacred", "myth"}),
    "grove": Place("grove", "the old grove", sacred=True, light="starlight", tags={"sacred", "myth"}),
    "village": Place("village", "the hill village", sacred=False, light="sunlight", tags={"myth"}),
}

VESSELS = {
    "bowl": Vessel("bowl", "bowl", "a silver bowl with a carved handle", "handle", fragile=True, useful=True, tags={"handle"}),
    "urn": Vessel("urn", "urn", "a clay urn with a bronze handle", "handle", fragile=True, useful=True, tags={"handle"}),
}

MIXTURES = {
    "healing": Mixture("healing", "mixture", "a healing mixture of herbs and honey", magic=True, healing=True, bright=False, volatile=False, tags={"mixture", "magic"}),
    "dawn": Mixture("dawn", "mixture", "a bright mixture of ash and moonflowers", magic=True, healing=False, bright=True, volatile=False, tags={"mixture", "magic"}),
    "wild": Mixture("wild", "mixture", "a wild mixture of sparks and sap", magic=True, healing=False, bright=True, volatile=True, tags={"mixture", "magic"}),
}

FIXES = {
    "prayer": Fix("prayer", "a quiet prayer", 3, 3, "spoke a quiet prayer and steadied the bowl", {"calm"}),
    "sharing": Fix("sharing", "a shared vow", 2, 2, "made a shared vow to use the magic only together", {"friendship"}),
}

GIRL_NAMES = ["Mira", "Lysa", "Nema", "Sora", "Iria", "Tala"]
BOY_NAMES = ["Kellan", "Rui", "Tovin", "Daren", "Pavel", "Aren"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for v in VESSELS.values():
            for m in MIXTURES.values():
                if handle_risk(v, p):
                    combos.append((p.id, v.id, m.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    vessel: str
    mix: str
    fix: str
    hero_a: str
    a_gender: str
    hero_b: str
    b_gender: str
    guide: str
    guide_gender: str
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
    "mixture": [("What is a mixture?", "A mixture is something made by combining different things together. In a myth, a mixture can be magical and carry power.")],
    "handle": [("What is a handle for?", "A handle is the part you hold so you can carry a bowl, pot, or jar more safely.")],
    "magic": [("What is magic in a story?", "Magic is special power that can do unusual things in a story, like glow, heal, or bless something.")],
    "friendship": [("What is friendship?", "Friendship means caring about someone, listening to them, and helping them when they need it.")],
    "conflict": [("What is conflict in a story?", "Conflict is when characters want different things or feel upset, and the story has to find a way to solve that.")],
    "myth": [("What is a myth?", "A myth is an old story about special people, gods, spirits, or magical events that explains or celebrates something important.")],
}

KNOWLEDGE_ORDER = ["myth", "magic", "mixture", "handle", "friendship", "conflict"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the words "{f["mix"].label}" and "handle".',
        f"Tell a gentle myth about two friends at {f['place'].name} who argue over a magical {f['mix'].label} and then make peace.",
        f"Write a story with friendship, conflict, and magic where a carved handle helps keep a special mixture safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, guide = f["a"], f["b"], f["guide"]
    mix, place = f["mix"], f["place"]
    qa = [
        ("Who are the story's main characters?",
         f"The story is about {a.id} and {b.id}, two friends, and {guide.id}, the wise guide who helps them."),
        ("Why did the friends quarrel?",
         f"{a.id} wanted to use the {mix.label} for a grand display, but {b.id} feared it would be careless. That disagreement turned their friendship into a conflict for a little while."),
        ("What did the guide teach them?",
         f"{guide.id} taught them that the best magic is used with care and friendship. The guide showed them that the handle was for safe carrying, not showing off."),
        ("How did the story end?",
         f"The friends used the {mix.label} to heal the shrine and light a lamp, and their conflict softened into friendship again. They ended the tale working together at {place.name}."),
    ]
    if world.facts.get("handled"):
        qa.append((
            "What did the handle do in the story?",
            f"The handle let them lift the bowl safely and carry the {mix.label} without spilling it. That small detail helped turn the conflict into a careful, shared task."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mix"].tags) | {"myth", "handle", "friendship", "conflict"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("temple", "bowl", "healing", "prayer", "Mira", "girl", "Kellan", "boy", "Orin", "priest"),
    StoryParams("grove", "urn", "dawn", "sharing", "Lysa", "girl", "Tovin", "boy", "Edda", "priestess"),
]


def explain_rejection(vessel: Vessel, place: Place) -> str:
    return f"(No story: {vessel.label} and {place.name} do not make a meaningful handle-and-magic conflict here.)"


def valid_fix(fix_id: str) -> bool:
    return fix_id in FIXES and FIXES[fix_id].wisdom >= 2


def outcome_of(params: StoryParams) -> str:
    return "reconciled"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.sacred:
            lines.append(asp.fact("sacred", pid))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if v.fragile:
            lines.append(asp.fact("fragile", vid))
        lines.append(asp.fact("handle", vid, v.handle))
    for mid, m in MIXTURES.items():
        lines.append(asp.fact("mixture", mid))
        if m.magic:
            lines.append(asp.fact("magic", mid))
        if m.healing:
            lines.append(asp.fact("healing", mid))
        if m.bright:
            lines.append(asp.fact("bright", mid))
        if m.volatile:
            lines.append(asp.fact("volatile", mid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("wisdom", fid, f.wisdom))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


ASP_RULES = r"""
risk(V, P) :- fragile(V), sacred(P).
valid(P, V, M) :- place(P), vessel(V), mixture(M), risk(V, P).
reconcile(F) :- fix(F), wisdom(F, W), W >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reconcile() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show reconcile/1."))
    return sorted(x for (x,) in asp.atoms(model, "reconcile"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_reconcile()) == set(sensible_fixes()):
        print("OK: fix wisdom matches.")
    else:
        rc = 1
        print("MISMATCH in fixes.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, vessel=None, mix=None, fix=None, hero_a=None, a_gender=None, hero_b=None, b_gender=None, guide=None, guide_gender=None), random.Random(1)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: magic, friendship, conflict, and a handled mixture.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--mix", choices=MIXTURES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-a")
    ap.add_argument("--a-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-b")
    ap.add_argument("--b-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["priest", "priestess"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.vessel is None or c[1] == args.vessel)
              and (args.mix is None or c[2] == args.mix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, vessel, mix = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(sensible_fixes()))
    a_gender = args.a_gender or rng.choice(["girl", "boy"])
    b_gender = args.b_gender or ("boy" if a_gender == "girl" else "girl")
    guide_gender = args.guide_gender or rng.choice(["priest", "priestess"])
    hero_a = args.hero_a or _pick_name(rng, a_gender)
    hero_b = args.hero_b or _pick_name(rng, b_gender, avoid=hero_a)
    guide = args.guide or ("Orin" if guide_gender == "priest" else "Edda")
    return StoryParams(place, vessel, mix, fix, hero_a, a_gender, hero_b, b_gender, guide, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], VESSELS[params.vessel], MIXTURES[params.mix], FIXES[params.fix],
                 params.hero_a, params.hero_b, params.guide, params.a_gender, params.b_gender, params.guide_gender)
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
        print(asp_program("", "#show valid/3.\n#show reconcile/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
