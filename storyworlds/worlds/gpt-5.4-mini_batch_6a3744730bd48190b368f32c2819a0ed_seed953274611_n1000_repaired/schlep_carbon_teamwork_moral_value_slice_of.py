#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/schlep_carbon_teamwork_moral_value_slice_of.py
================================================================================

A small slice-of-life storyworld about a child, a heavy carbon delivery, and a
teamwork-and-moral-value turn: one person starts to schlep a too-heavy box, a
second person notices, helps share the load, and the group chooses kindness over
showing off.

The world is intentionally modest: it models physical load in meters and social
feelings in memes, lets those state changes drive the prose, and provides a
reasonableness gate plus an inline ASP twin.
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
LOAD_LIMIT = 2.0
HELP_THRESHOLD = 1.0


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
    scene: str
    detail: str
    supports: set[str] = field(default_factory=set)
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
class CarbonThing:
    id: str
    label: str
    phrase: str
    heavy: bool = True
    dirty: bool = False
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
class HelpOption:
    id: str
    label: str
    shares: bool = True
    power: int = 2
    text: str = ""
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["load"] < LOAD_LIMIT:
            continue
        sig = ("tired", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tired"] += 1
        out.append(f"{e.id} slowed down.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["helped"] < HELP_THRESHOLD:
            continue
        sig = ("helped", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["pride"] += 1
        out.append("__help__")
    return out


CAUSAL_RULES = [Rule("tired", _r_tired), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def heavy_enough(carbon: CarbonThing) -> bool:
    return carbon.heavy


def reasonable_help(option: HelpOption) -> bool:
    return option.shares and option.power >= 2


def too_heavy_to_schlep(carbon: CarbonThing) -> bool:
    return carbon.heavy


def predict(world: World, carbon_id: str, helper_id: str = "") -> dict:
    sim = world.copy()
    carbon = sim.get(carbon_id)
    carrier = sim.get("carrier")
    carrier.meters["load"] += 2
    carbon_ent = sim.get(carbon_id)
    if helper_id:
        helper = sim.get(helper_id)
        helper.memes["helped"] += 1
        carrier.meters["load"] -= 1
        helper.meters["load"] += 1
    propagate(sim, narrate=False)
    return {"tired": carrier.memes["tired"] >= THRESHOLD, "shared": helper_id != ""}


def setup(world: World, carrier: Entity, friend: Entity, place: Place, carbon: CarbonThing) -> None:
    carrier.memes["want"] += 1
    world.say(
        f"After breakfast, {carrier.id} and {friend.id} were at {place.scene}. "
        f"{place.detail}"
    )
    world.say(
        f"They had to move {carbon.phrase}, and {carrier.id} said {carrier.pronoun().capitalize()} would schlep it alone if needed."
    )


def strain(world: World, carrier: Entity, carbon: CarbonThing) -> None:
    carrier.meters["load"] += 2
    carrier.memes["determination"] += 1
    world.say(
        f"{carrier.id} grabbed the box and started to schlep {carbon.label} across the room."
    )


def notice(world: World, friend: Entity, carrier: Entity, carbon: CarbonThing, option: HelpOption) -> None:
    pred = predict(world, carbon.id)
    world.facts["predicted_tired"] = pred["tired"]
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} saw the wobble and frowned. "
        f'"That looks too heavy to schlep by yourself," {friend.id} said. '
        f'"Let me help carry the {carbon.label}."'
    )
    if reason_for_help(option):
        friend.memes["helped"] += 1


def reason_for_help(option: HelpOption) -> bool:
    return reasonable_help(option)


def accept_help(world: World, carrier: Entity, friend: Entity, carbon: CarbonThing, option: HelpOption) -> None:
    carrier.meters["load"] = 1
    friend.meters["load"] = 1
    carrier.memes["relief"] += 1
    friend.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{carrier.id} nodded, and together they used {option.label}. "
        f"{option.text} The load felt smaller right away."
    )
    world.say(
        f"Side by side, they finished the schlep without dropping anything."
    )


def moral_turn(world: World, carrier: Entity, friend: Entity) -> None:
    carrier.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"At the end, {carrier.id} said the nicest part was not looking strong; it was being kind enough to share the work."
    )
    world.say(
        f"{friend.id} smiled, because helping had turned the chore into teamwork."
    )


def ending(world: World, place: Place, carbon: CarbonThing) -> None:
    world.say(
        f"By afternoon, the {carbon.label} was where it needed to be, and the kitchen smelled faintly of warm carbon and toast."
    )
    world.say(
        f"{place.detail} now felt calm again, with the heavy box gone and two friends grinning at their clean hands."
    )


def tell(place: Place, carbon: CarbonThing, helpopt: HelpOption,
         carrier_name: str = "Mina", carrier_gender: str = "girl",
         friend_name: str = "Jo", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    carrier = world.add(Entity(id=carrier_name, kind="character", type=carrier_gender, role="carrier"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))

    setup(world, carrier, friend, place, carbon)
    world.para()
    strain(world, carrier, carbon)
    notice(world, friend, carrier, carbon, helpopt)

    world.para()
    if reason_for_help(helpopt):
        accept_help(world, carrier, friend, carbon, helpopt)
        moral_turn(world, carrier, friend)
    else:
        world.say(f"{friend.id} offered something that did not really help, so {carrier.id} kept struggling alone.")
        carrier.meters["load"] += 1
        carrier.memes["tired"] += 1
        world.say(f"{parent.label_word.capitalize()} came over, saw the wobble, and asked them to stop and try again together.")

    ending(world, place, carbon)

    world.facts.update(
        carrier=carrier,
        friend=friend,
        parent=parent,
        place=place,
        carbon=carbon,
        helpopt=helpopt,
        teamwork=reason_for_help(helpopt),
        moral=carrier.memes["lesson"] >= THRESHOLD,
        load=int(carrier.meters["load"]),
    )
    return world


PLACES = {
    "kitchen": Place(id="kitchen", scene="the kitchen", detail="The counter was crowded with groceries and a little radio hummed softly.", supports={"move"}),
    "backyard": Place(id="backyard", scene="the backyard", detail="The back gate stood open, and the sun made the stepping stones warm.", supports={"move"}),
    "basement": Place(id="basement", scene="the basement", detail="The basement was cool and echoey, with a neat shelf waiting nearby.", supports={"move"}),
}

CARBONS = {
    "charcoal": CarbonThing(id="charcoal", label="charcoal briquettes", phrase="a heavy bag of carbon briquettes", heavy=True, tags={"carbon", "schlep"}),
    "filter": CarbonThing(id="filter", label="carbon filter", phrase="a boxed carbon filter", heavy=True, tags={"carbon"}),
    "pencil": CarbonThing(id="pencil", label="carbon paper", phrase="a pack of carbon paper", heavy=False, tags={"carbon"}),
}

HELPS = {
    "carry": HelpOption(id="carry", label="a second pair of hands", shares=True, power=2, text="They split the weight between them. "),
    "cart": HelpOption(id="cart", label="a little cart", shares=True, power=3, text="They rolled the box on a little cart. "),
    "wrong": HelpOption(id="wrong", label="a tiny towel", shares=False, power=0, text="It was far too small to matter. "),
}

@dataclass
class StoryParams:
    place: str
    carbon: str
    helpopt: str
    carrier_name: str
    carrier_gender: str
    friend_name: str
    friend_gender: str
    parent_type: str = "mother"
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


CURATED = [
    StoryParams(place="kitchen", carbon="charcoal", helpopt="carry", carrier_name="Mina", carrier_gender="girl", friend_name="Jo", friend_gender="boy", parent_type="mother"),
    StoryParams(place="backyard", carbon="filter", helpopt="cart", carrier_name="Leo", carrier_gender="boy", friend_name="Nia", friend_gender="girl", parent_type="father"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CARBONS:
            for h in HELPS:
                if heavy_enough(CARBONS[c]) and reasonable_help(HELPS[h]):
                    combos.append((p, c, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about schlep, carbon, teamwork, and a moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--carbon", choices=CARBONS)
    ap.add_argument("--helpopt", choices=HELPS)
    ap.add_argument("--carrier-name")
    ap.add_argument("--carrier-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.carbon is None or c[1] == args.carbon)
              and (args.helpopt is None or c[2] == args.helpopt)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, carbon, helpopt = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        carbon=carbon,
        helpopt=helpopt,
        carrier_name=args.carrier_name or rng.choice(["Mina", "Tess", "Lena", "Ivy", "Nora"]),
        carrier_gender=args.carrier_gender or rng.choice(["girl", "boy"]),
        friend_name=args.friend_name or rng.choice(["Jo", "Sam", "Owen", "Kai", "Milo"]),
        friend_gender=args.friend_gender or rng.choice(["boy", "girl"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.carbon not in CARBONS or params.helpopt not in HELPS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        place=PLACES[params.place],
        carbon=CARBONS[params.carbon],
        helpopt=HELPS[params.helpopt],
        carrier_name=params.carrier_name,
        carrier_gender=params.carrier_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "schlep" and "carbon" and ends with teamwork.',
        f"Tell a gentle story about {f['carrier'].id} trying to schlep {f['carbon'].label} and learning to share the load.",
        f"Write a small moral story where a friend notices someone carrying carbon and helps in a practical, kind way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier, friend, carbon, place, helpopt = f["carrier"], f["friend"], f["carbon"], f["place"], f["helpopt"]
    return [
        ("What was the heavy thing?",
         f"It was {carbon.phrase}. The box was heavy enough that one person could not schlep it comfortably alone."),
        ("Why did {0} need help?".format(carrier.id),
         f"{carrier.id} needed help because the load was too heavy to carry by {carrier.pronoun('object')}self. "
         f"Sharing the work kept the trip safe and steady."),
        ("What did the friend do?",
         f"{friend.id} offered {helpopt.label} and helped carry the carbon. That turned the chore into teamwork."),
        ("What moral value did the story show?",
         "It showed kindness and teamwork. The friends did not try to look impressive; they chose to help each other instead."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does teamwork mean?",
         "Teamwork means people work together and share the job. When they help each other, hard things can feel easier."),
        ("What is carbon?",
         "Carbon is a kind of material found in things like charcoal and filters. In this story, it is part of the heavy thing they had to move."),
        ("What does schlep mean?",
         "To schlep something means to carry it along, usually when it is heavy or awkward. It sounds a little tired, just like the job can feel."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,H) :- place(P), carbon(C), help(H), heavy(C), helpful(H).
heavy(C) :- carbon(C), heavy_fact(C).
helpful(H) :- helpopt(H), shares(H), power(H, P), P >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c, obj in CARBONS.items():
        lines.append(asp.fact("carbon", c))
        if obj.heavy:
            lines.append(asp.fact("heavy_fact", c))
    for h, obj in HELPS.items():
        lines.append(asp.fact("helpopt", h))
        if obj.shares:
            lines.append(asp.fact("shares", h))
        lines.append(asp.fact("power", h, obj.power))
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
        rc = 1
        print("MISMATCH: ASP and Python valid_combos disagree.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: ASP parity and generation smoke test passed.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
