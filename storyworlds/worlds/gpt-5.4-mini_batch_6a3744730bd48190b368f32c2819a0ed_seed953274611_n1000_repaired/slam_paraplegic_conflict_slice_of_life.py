#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slam_paraplegic_conflict_slice_of_life.py
==========================================================================

A small slice-of-life storyworld about a minor household conflict: a noisy,
hurried moment, a slammed door or cabinet, a hurt feeling, and a calm repair.

Seed words:
- slam
- paraplegic

Style:
- Slice of Life

Feature:
- Conflict

The world generates short, child-facing stories with state-driven turns.
It includes typed entities with physical meters and emotional memes, a Python
reasonableness gate, and an inline ASP twin for parity checks.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TENSION_LIMIT = 2.0


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
    loud: bool = False
    wheel_support: bool = False

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
    name: str
    quiet_need: bool = False
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
class NoisyThing:
    id: str
    label: str
    action: str
    volume: int
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
class Repair:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    noisy: str
    repair: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    paraplegic_name: str
    paraplegic_gender: str
    parent: str
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


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", quiet_need=True, tags={"home", "quiet"}),
    "hallway": Place("hallway", "the hallway", quiet_need=True, tags={"home", "quiet"}),
    "living_room": Place("living_room", "the living room", quiet_need=True, tags={"home", "quiet"}),
}

NOISY = {
    "cabinet": NoisyThing("cabinet", "the cabinet door", "slam it shut", 2, tags={"slam"}),
    "screen_door": NoisyThing("screen_door", "the screen door", "slam it shut", 2, tags={"slam"}),
    "drawer": NoisyThing("drawer", "the drawer", "slam it shut", 1, tags={"slam"}),
}

REPAIRS = {
    "apology": Repair(
        "apology", 2, 2,
        "took a breath, knocked softly, and apologized with a careful voice",
        "tried to apologize, but the hurt feeling was still too big",
        "said sorry, knocked softly, and made things feel calm again",
        tags={"kindness", "talk"},
    ),
    "soft_close": Repair(
        "soft_close", 3, 3,
        "closed it gently this time and added a folded towel so it would not bang again",
        "tried to close it gently, but the noise had already upset everyone",
        "closed it gently and stopped the noise from coming back",
        tags={"quiet", "fix"},
    ),
    "tea": Repair(
        "tea", 2, 2,
        "put a mug of warm tea on the table and sat down to listen",
        "made tea, but the mood was still too sharp to settle",
        "made tea and let everybody breathe for a minute",
        tags={"quiet", "care"},
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Sara", "Nora", "Ava"]
NAMES_BOY = ["Owen", "Milo", "Ben", "Eli", "Noah"]
REASONABLE_REPAIRS = {"apology", "soft_close", "tea"}


def hazard_at_risk(place: Place, noisy: NoisyThing) -> bool:
    return place.quiet_need and noisy.volume >= 1


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for nid, noisy in NOISY.items():
            if hazard_at_risk(place, noisy):
                out.append((pid, nid))
    return out


def repair_ok(rid: str) -> bool:
    return rid in REASONABLE_REPAIRS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and not repair_ok(args.repair):
        raise StoryError("That repair would not make sense for a small slice-of-life conflict.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.noisy is None or c[1] == args.noisy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, noisy = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(REASONABLE_REPAIRS))
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(NAMES_GIRL if g1 == "girl" else NAMES_BOY)
    name2 = args.name2 or rng.choice([n for n in (NAMES_GIRL if g2 == "girl" else NAMES_BOY) if n != name1])
    paraplegic_name = args.paraplegic_name or rng.choice(NAMES_GIRL + NAMES_BOY)
    paraplegic_gender = args.paraplegic_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place, noisy=noisy, repair=repair,
        name1=name1, gender1=g1, name2=name2, gender2=g2,
        paraplegic_name=paraplegic_name, paraplegic_gender=paraplegic_gender,
        parent=parent,
    )


def _smash(world: World, actor: Entity, noisy: NoisyThing) -> None:
    actor.meters["noise"] += noisy.volume
    actor.memes["tension"] += 1
    for e in world.characters():
        if e.id != actor.id:
            e.memes["startled"] += 1


def predict_tension(world: World, actor: Entity, noisy: NoisyThing) -> dict:
    sim = world.copy()
    _smash(sim, sim.get(actor.id), noisy)
    return {"noise": sim.get(actor.id).meters["noise"], "conflict": sim.facts.get("conflict", 0)}


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.name1, kind="character", type=params.gender1, role="instigator"))
    b = world.add(Entity(id=params.name2, kind="character", type=params.gender2, role="witness"))
    p = world.add(Entity(id=params.paraplegic_name, kind="character", type=params.paraplegic_gender, role="mediator",
                         traits=["paraplegic"], attrs={"paraplegic": True}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))

    place = PLACES[params.place]
    noisy = NOISY[params.noisy]
    repair = REPAIRS[params.repair]

    a.memes["impatience"] += 1
    b.memes["calm"] += 1
    p.memes["calm"] += 1

    world.say(f"On an ordinary afternoon, {a.id}, {b.id}, and {p.id} were in {place.name}.")
    world.say(f"{p.id} was paraplegic, so they moved carefully and liked a tidy room where nothing got in the way.")
    world.say(f"{a.id} wanted to reach for {noisy.label}, and {b.id} was nearby with a quiet little stack of books.")

    world.para()
    pred = predict_tension(world, a, noisy)
    if pred["noise"] >= TENSION_LIMIT:
        world.say(f"{b.id} frowned. \"Please don't {noisy.action}; the noise is too much in here,\" {b.pronoun()} said.")
    world.say(f'"It is just one quick move," {a.id} said, and then {a.id} let the {noisy.label} {noisy.action}.')

    _smash(world, a, noisy)
    world.facts["conflict"] = 1

    world.para()
    world.say(f"The {noisy.label} went with a hard slam, and the sharp sound bounced around {place.name}.")
    world.say(f"{p.id} flinched, and {b.id} looked over with a worried face. The room suddenly felt tense.")

    if params.repair == "soft_close":
        outcome = True
    elif params.repair == "apology":
        outcome = True
    else:
        outcome = True

    world.para()
    if outcome:
        a.memes["regret"] += 1
        b.memes["relief"] += 1
        p.memes["relief"] += 1
        world.say(f"After a pause, {a.id} took a breath and {repair.text}.")
        world.say(f"{p.id} nodded, and {b.id} helped by speaking gently so nobody had to keep feeling upset.")
        world.say(f"By the end, the noise was settled, the face were calm again, and {place.name} felt peaceful.")
        world.say(f"That evening, {a.id} remembered to close the {noisy.label} softly instead of making it slam.")
    world.facts.update(
        instigator=a, witness=b, mediator=p, parent=parent, place=place, noisy=noisy, repair=repair,
        resolved=True, conflict=True, paraplegic=True,
    )
    return world


PROMPT_TEMPLATES = [
    "Write a slice-of-life story about a small household conflict that includes the word 'slam' and a paraplegic family member.",
    "Tell a gentle everyday story where one child makes a noisy {noisy} and another child helps calm things down.",
    "Write a story about a quiet room, a sudden slam, and a calm repair that ends peacefully.",
]

STORY_QA = {
    "who": "It is about three people in an ordinary home moment: two children and a paraplegic family member. The conflict is small, but it changes the mood of the room.",
    "why": "The problem started because the noisy thing was slammed too hard. That sharp sound upset the paraplegic character and made the others stop and notice the tension.",
    "resolution": "The conflict was repaired when the child slowed down, apologized, and used a gentler way to close the thing. That quiet choice changed the ending from tense to calm.",
    "ending": "The story ends peacefully, with the noisy thing closed softly and the room feeling settled again. The last image shows that the people learned from the moment.",
}

WORLD_QA = [
    QAItem(question="What does a paraplegic person usually need in daily life?", answer="A paraplegic person may use a wheelchair or another way to move around, and a clear, calm space can make everyday life easier."),
    QAItem(question="Why can a slam be upsetting in a small home?", answer="A slam is sudden and loud, so it can startle people and make a peaceful room feel tense very quickly."),
    QAItem(question="What is a gentle way to fix a small conflict?", answer="A gentle way to fix it is to apologize, speak softly, and change the noisy action so it does not happen again."),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    noisy = f["noisy"]
    return [t.format(noisy=noisy.label) for t in PROMPT_TEMPLATES]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, p, noisy = f["instigator"], f["witness"], f["mediator"], f["noisy"]
    return [
        ("Who is the story about?", f"It is about {a.id}, {b.id}, and {p.id}, who is paraplegic. They are all in one ordinary home scene, and the conflict stays small."),
        ("What caused the conflict?", f"The conflict started when {a.id} made {noisy.label} slam. The noise upset the room and made {p.id} flinch."),
        ("How did the people fix the problem?", f"{a.id} apologized and then used a gentler way to close {noisy.label}. That turned the moment from tense to calm."),
        ("How did the story end?", f"It ended with the noisy thing closed softly and everyone feeling better. The ending image proves the conflict was repaired."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, N) :- place(P), noisy(N).
valid(P, N) :- hazard(P, N).
sensible(R) :- repair(R), sense(R, S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for nid, n in NOISY.items():
        lines.append(asp.fact("noisy", nid))
        lines.append(asp.fact("volume", nid, n.volume))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    if set(asp_sensible_repairs()) == {r.id for r in sensible_repairs()}:
        print("OK: ASP sensible repairs match.")
    else:
        rc = 1
        print("MISMATCH: ASP sensible repairs differ.")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: normal generation produced empty story.")
    else:
        print("OK: normal generation smoke test passed.")
    return rc


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= 2]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.noisy not in NOISY or params.repair not in REPAIRS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a small conflict and a calm repair.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--noisy", choices=NOISY)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--paraplegic-name")
    ap.add_argument("--paraplegic-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


CURATED = [
    StoryParams(place="kitchen", noisy="cabinet", repair="apology", name1="Mia", gender1="girl", name2="Owen", gender2="boy", paraplegic_name="Lena", paraplegic_gender="girl", parent="mother"),
    StoryParams(place="hallway", noisy="screen_door", repair="soft_close", name1="Ben", gender1="boy", name2="Ava", gender2="girl", paraplegic_name="Noah", paraplegic_gender="boy", parent="father"),
    StoryParams(place="living_room", noisy="drawer", repair="tea", name1="Nora", gender1="girl", name2="Eli", gender2="boy", paraplegic_name="Milo", paraplegic_gender="boy", parent="mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and not repair_ok(args.repair):
        raise StoryError("That repair is not reasonable for this slice-of-life conflict.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.noisy is None or c[1] == args.noisy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, noisy = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(REASONABLE_REPAIRS))
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or ("boy" if gender1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(NAMES_GIRL if gender1 == "girl" else NAMES_BOY)
    name2 = args.name2 or rng.choice(NAMES_GIRL if gender2 == "girl" else NAMES_BOY)
    paraplegic_gender = args.paraplegic_gender or rng.choice(["girl", "boy"])
    paraplegic_name = args.paraplegic_name or rng.choice(NAMES_GIRL if paraplegic_gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place, noisy=noisy, repair=repair,
        name1=name1, gender1=gender1, name2=name2, gender2=gender2,
        paraplegic_name=paraplegic_name, paraplegic_gender=paraplegic_gender,
        parent=parent,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        for p, n in asp_valid_combos():
            print(f"{p:12} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
