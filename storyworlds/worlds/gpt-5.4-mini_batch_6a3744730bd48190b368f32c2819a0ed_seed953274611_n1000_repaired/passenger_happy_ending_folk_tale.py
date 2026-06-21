#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/passenger_happy_ending_folk_tale.py
====================================================================

A small folk-tale storyworld about a river crossing, a stranded passenger,
a kindly ferryman, and a happy ending reached through a simple, state-driven
turn: the boat is stuck, a helper chooses a sensible means, and everyone reaches
the far bank before night.

The world keeps a typed simulation with physical meters and emotional memes.
Stories are generated from world state, not from a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MIN_SENSE = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    setting: str
    current: str
    far_bank: str
    if_stuck: str
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
class Hazard:
    id: str
    label: str
    cause: str
    makes_stuck: bool = True
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
class Rescue:
    id: str
    label: str
    action: str
    power: int
    sense: int
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
        self.fired: set[str] = set()
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACE = Place(
    id="riverbank",
    label="the river bank",
    setting="a little riverside",
    current="the current",
    far_bank="the far bank",
    if_stuck="the boat could not budge",
    tags={"river", "bank"},
)

HAZARDS = {
    "mud": Hazard(
        id="mud",
        label="thick mud",
        cause="the wheels sank into thick mud",
        makes_stuck=True,
        tags={"mud"},
    ),
    "reed": Hazard(
        id="reed",
        label="tangled reeds",
        cause="tangled reeds wrapped the keel",
        makes_stuck=True,
        tags={"reed"},
    ),
}

RESCUES = {
    "pole": Rescue(
        id="pole",
        label="a long pole",
        action="push the boat free with a long pole",
        power=2,
        sense=3,
        tags={"pole"},
    ),
    "horse": Rescue(
        id="horse",
        label="a borrowed horse",
        action="pull the boat with a borrowed horse and a rope",
        power=3,
        sense=2,
        tags={"horse"},
    ),
    "wheel": Rescue(
        id="wheel",
        label="a cart wheel",
        action="roll the boat from the soft mud with a cart wheel",
        power=1,
        sense=1,
        tags={"wheel"},
    ),
}

PEOPLE = {
    "passenger": {"boy": ["Pavel", "Milo", "Theo"], "girl": ["Mina", "Lina", "Anya"]},
    "ferryman": {"boy": ["Jon", "Rurik", "Bram"], "girl": ["Sela", "Nora", "Marta"]},
}

TALKS = ["kind", "steady", "brave", "patient"]


@dataclass
class StoryParams:
    passenger_name: str
    passenger_gender: str
    ferryman_name: str
    ferryman_gender: str
    hazard: str
    rescue: str
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


def hazard_risk(place: Place, hazard: Hazard) -> bool:
    return hazard.makes_stuck and place.id == "riverbank"


def good_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= MIN_SENSE]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    if not good_rescues():
        return out
    for hid in HAZARDS:
        for rid, rescue in RESCUES.items():
            if rescue.sense >= MIN_SENSE and hazard_risk(PLACE, HAZARDS[hid]):
                out.append((hid, rid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld with a passenger and a happy ending.")
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--passenger-name")
    ap.add_argument("--passenger-gender", choices=["girl", "boy"])
    ap.add_argument("--ferryman-name")
    ap.add_argument("--ferryman-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rescue and RESCUES[args.rescue].sense < MIN_SENSE:
        raise StoryError(f"(Refusing rescue '{args.rescue}': it is too weak and not sensible enough.)")
    combos = [c for c in valid_combos()
              if args.hazard is None or c[0] == args.hazard
              if args.rescue is None or c[1] == args.rescue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hazard, rescue = rng.choice(sorted(combos))
    pg = args.passenger_gender or rng.choice(["girl", "boy"])
    fg = args.ferryman_gender or rng.choice(["girl", "boy"])
    pname = args.passenger_name or rng.choice(PEOPLE["passenger"][pg])
    fname = args.ferryman_name or rng.choice(PEOPLE["ferryman"][fg])
    return StoryParams(pname, pg, fname, fg, hazard, rescue)


def _story_setup(world: World, p: Entity, f: Entity, place: Place) -> None:
    p.memes["hope"] = 1
    f.memes["kindness"] = 1
    world.say(f"By the river bank, {p.id} met {f.id}, who kept a small ferry for travelers.")
    world.say(f"The day was calm, but the water ran quick below {place.label}.")
    world.say(f"{p.id} had a bag of bread and a heart full of travel, and wanted to cross before dark.")


def _temptation(world: World, p: Entity, hazard: Hazard) -> None:
    p.memes["worry"] = 1
    world.para()
    world.say(f"Yet {hazard.cause}, and the boat gave a lonely creak.")
    world.say(f'"{hazard.label.capitalize()}," {p.id} murmured. "What if we cannot go on?"')


def _helper_thinks(world: World, f: Entity, rescue: Rescue, hazard: Hazard) -> None:
    f.memes["calm"] = 1
    world.say(f"{f.id} looked at the shore, then at the boat, and stayed as steady as a tree.")
    world.say(f'"No need to fear," {f.id} said. "I know how to {rescue.action}."')
    world.facts["helper_saw_hazard"] = hazard.label


def _rescue(world: World, f: Entity, rescue: Rescue) -> None:
    world.para()
    world.say(f"{f.id} took {rescue.label} and got to work.")
    world.say(f"In a few hard pushes and a little laughter, {rescue.action}.")
    world.say(f"The boat rocked, slipped free, and floated back into the current.")


def _happy_crossing(world: World, p: Entity, f: Entity, place: Place) -> None:
    p.memes["joy"] += 1
    f.memes["joy"] += 1
    world.para()
    world.say(f"{p.id} climbed aboard again, and together they crossed to {place.far_bank}.")
    world.say(f"On the far bank the reeds bent in the wind, and the sunset made the river shine like gold.")
    world.say(f"{p.id} thanked {f.id}, and both of them smiled as the little ferry went on with its song.")


def tell(params: StoryParams) -> World:
    world = World()
    p = world.add(Entity(id=params.passenger_name, kind="character", type=params.passenger_gender, role="passenger"))
    f = world.add(Entity(id=params.ferryman_name, kind="character", type=params.ferryman_gender, role="ferryman"))
    hazard = HAZARDS[params.hazard]
    rescue = RESCUES[params.rescue]
    _story_setup(world, p, f, PLACE)
    _temptation(world, p, hazard)
    _helper_thinks(world, f, rescue, hazard)
    _rescue(world, f, rescue)
    _happy_crossing(world, p, f, PLACE)
    world.facts.update(passenger=p, ferryman=f, hazard=hazard, rescue=rescue, place=PLACE, outcome="happy")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p, h, r = f["passenger"], f["hazard"], f["rescue"]
    return [
        f'Write a folk-tale story for a small child about a passenger named {p.id} who gets stuck because of {h.label}, and a kind ferryman who helps. Include the word "passenger".',
        f"Tell a happy ending river story where {p.id} trusts {f['ferryman'].id} and the boat becomes unstuck.",
        f"Write a gentle folk tale with a river crossing, a stranded passenger, and a helper who knows how to {r.action}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p, ferr, hazard, rescue = f["passenger"], f["ferryman"], f["hazard"], f["rescue"]
    return [
        QAItem(
            question="Who was the passenger?",
            answer=f"The passenger was {p.id}, who wanted to cross the river on the ferry. {p.id} was worried at first because {hazard.cause}.",
        ),
        QAItem(
            question="How did the ferryman help?",
            answer=f"{ferr.id} stayed calm and used {rescue.label} to solve the problem. That helped the boat get free, and it let the trip continue safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. {p.id} reached the far bank, thanked {ferr.id}, and the ferry went on under the evening sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a passenger?", "A passenger is someone who rides in a boat, car, train, or other vehicle. They travel instead of steering."),
        QAItem("What does a ferryman do?", "A ferryman carries people across water in a boat. They help travelers reach the other side."),
        QAItem("Why can mud stop a boat?", "Mud can hold the boat in place and keep it from moving. If the bottom sinks in, the boat may need help to free itself."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(passenger_name="Mina", passenger_gender="girl", ferryman_name="Bram", ferryman_gender="boy", hazard="mud", rescue="pole"),
    StoryParams(passenger_name="Theo", passenger_gender="boy", ferryman_name="Sela", ferryman_gender="girl", hazard="reed", rescue="horse"),
]


def explain_response(rid: str) -> str:
    r = RESCUES[rid]
    return f"(Refusing rescue '{rid}': it is too weak for a happy ending tale; sense={r.sense} < {MIN_SENSE}.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


ASP_RULES = r"""
rescue_ok(R) :- rescue(R), sense(R,S), min_sense(M), S >= M.
hazard_ok(H) :- hazard(H), risky(H).
story_ok(H,R) :- hazard_ok(H), rescue_ok(R).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("min_sense", MIN_SENSE)]
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_stuck:
            lines.append(asp.fact("risky", hid))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((h, r) for h, r in valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.hazard not in HAZARDS or params.rescue not in RESCUES:
        raise StoryError("Invalid params.")
    if RESCUES[params.rescue].sense < MIN_SENSE:
        raise StoryError(explain_response(params.rescue))
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
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for item in asp_valid_combos():
            print(item)
        return

    rng0 = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random((args.seed or 0) + i if args.seed is not None else rng0.randrange(2**31))
            params = resolve_params(args, rng)
            params.seed = args.seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
