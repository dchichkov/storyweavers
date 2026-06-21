#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/specimen_rat_consume_suspense_foreshadowing_sharing_detective.py
================================================================================================

A tiny detective storyworld about a missing specimen, a rat, and the danger of
letting curiosity consume a clue. The domain is built to support suspense,
foreshadowing, and sharing: a careful detective notices hints, tests a theory,
shares evidence with a helper, and restores the case with a clear ending image.

Seed words:
- specimen
- rat
- consume

Narrative instruments:
- Suspense
- Foreshadowing
- Sharing

Style:
- Detective Story
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        female = {"girl", "mother", "woman", "female"}
        male = {"boy", "father", "man", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    shadowy: bool = False
    quiet: bool = False
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
class Specimen:
    id: str
    label: str
    fragile: bool = True
    edible: bool = False
    scent: str = "odd"
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
class Rat:
    id: str
    label: str
    sly: bool = True
    hungry: bool = True
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
class SharingTool:
    id: str
    label: str
    phrase: str
    gives: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(place=copy.deepcopy(self.place))
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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
    place: str
    detective: str
    detective_gender: str
    partner: str
    partner_gender: str
    specimen: str
    rat: str
    sharing: str
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
    "lab": Place(id="lab", label="the old lab", shadowy=True, quiet=True),
    "archive": Place(id="archive", label="the archive room", shadowy=True, quiet=False),
    "basement": Place(id="basement", label="the basement corridor", shadowy=True, quiet=True),
}

SPECIMENS = {
    "amber": Specimen(id="amber", label="an amber specimen", fragile=True, edible=False, scent="sweet"),
    "seed": Specimen(id="seed", label="a rare seed specimen", fragile=True, edible=True, scent="earthy"),
    "shell": Specimen(id="shell", label="a bright shell specimen", fragile=True, edible=False, scent="salty"),
}

RATS = {
    "rat": Rat(id="rat", label="a rat", sly=True, hungry=True),
}

SHARING = {
    "crumbs": SharingTool(id="crumbs", label="crumbs", phrase="a little plate of crumbs", gives="crumbs"),
    "cheese": SharingTool(id="cheese", label="cheese", phrase="a tiny bit of cheese", gives="cheese"),
    "water": SharingTool(id="water", label="water", phrase="a dish of water", gives="water"),
}

DETECTIVE_NAMES = ["Mina", "Ivy", "June", "Ada", "Nora", "Tess"]
PARTNER_NAMES = ["Ben", "Owen", "Leo", "Milo", "Eli", "Finn"]

CURATED = [
    StoryParams(place="lab", detective="Mina", detective_gender="girl", partner="Ben", partner_gender="boy",
                specimen="amber", rat="rat", sharing="crumbs", seed=101),
    StoryParams(place="archive", detective="Ada", detective_gender="girl", partner="Eli", partner_gender="boy",
                specimen="seed", rat="rat", sharing="cheese", seed=102),
    StoryParams(place="basement", detective="Nora", detective_gender="girl", partner="Ivy", partner_gender="girl",
                specimen="shell", rat="rat", sharing="water", seed=103),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for specimen in SPECIMENS:
            for rat in RATS:
                if PLACES[place].shadowy and SPECIMENS[specimen].fragile:
                    out.append((place, specimen, rat))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective storyworld: a specimen, a rat, and a shared clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--specimen", choices=SPECIMENS)
    ap.add_argument("--rat", choices=RATS)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.specimen is None or c[1] == args.specimen)
              and (args.rat is None or c[2] == args.rat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, specimen, rat = rng.choice(sorted(combos))
    sharing = args.sharing or rng.choice(sorted(SHARING))
    gender = args.gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    partner = args.partner or rng.choice([n for n in PARTNER_NAMES if n != detective])
    return StoryParams(place=place, detective=detective, detective_gender=gender,
                       partner=partner, partner_gender=rng.choice(["girl", "boy"]),
                       specimen=specimen, rat=rat, sharing=sharing)


def _scene_open(world: World, det: Entity, partner: Entity, specimen: Entity) -> None:
    det.memes["focus"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"In {world.place.label}, {det.id} and {partner.id} found {specimen.label} on a long table."
    )
    world.say(
        f"{det.id} knew the room was quiet in a suspicious way, like it was holding its breath."
    )


def _foreshadow(world: World, det: Entity, specimen: Entity) -> None:
    det.memes["suspense"] += 1
    world.say(
        f"Near the shelf, there was a small trail of dust and a nibble mark that seemed to point nowhere."
    )
    world.say(
        f"{det.id} noticed one more clue: the lid beside the specimen was half-open, as if someone had been there first."
    )


def _rat_moves(world: World, rat: Entity, specimen: Entity) -> None:
    rat.memes["hunger"] += 1
    rat.meters["near_specimen"] += 1
    world.say(
        f"Then a rat slipped from the shadows, its whiskers twitching toward the specimen."
    )
    if specimen.edible:
        world.say(
            f"It looked ready to consume anything soft enough to chew, and that made the room feel even smaller."
        )
    else:
        world.say(
            f"It did not care what the specimen meant; it only cared that it might consume the crumbs of the case."
        )


def _share(world: World, det: Entity, partner: Entity, share: SharingTool) -> None:
    det.memes["trust"] += 1
    partner.memes["helpfulness"] += 1
    world.say(
        f'{det.id} lowered {det.pronoun("possessive")} voice and shared the clue with {partner.id}.'
    )
    world.say(
        f'Together they set out {share.phrase}, because a patient rat can be guided more gently than chased.'
    )


def _solve(world: World, det: Entity, partner: Entity, specimen: Entity, rat: Entity, share: SharingTool) -> None:
    rat.meters["fed"] += 1
    rat.memes["calm"] += 1
    world.say(
        f"The rat sniffed the offering, took {share.gives}, and backed away from the specimen."
    )
    world.say(
        f"{partner.id} lifted the specimen carefully while {det.id} checked the floor for any last tiny footprints."
    )
    world.say(
        f"By the end, the specimen was safe again, the rat was busy with its share, and the case had an answer."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.specimen not in SPECIMENS:
        raise StoryError(f"Unknown specimen: {params.specimen}")
    if params.rat not in RATS:
        raise StoryError(f"Unknown rat: {params.rat}")
    if params.sharing not in SHARING:
        raise StoryError(f"Unknown sharing tool: {params.sharing}")

    world = World(place=PLACES[params.place])
    det = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="partner"))
    specimen = world.add(Entity(id="specimen", kind="thing", type="specimen", label=SPECIMENS[params.specimen].label,
                                attrs={"edible": SPECIMENS[params.specimen].edible}))
    rat = world.add(Entity(id="rat", kind="character", type="rat", role="intruder"))
    share = SHARING[params.sharing]

    _scene_open(world, det, partner, specimen)
    world.para()
    _foreshadow(world, det, specimen)
    _rat_moves(world, rat, SPECIMENS[params.specimen])
    world.para()
    _share(world, det, partner, share)
    _solve(world, det, partner, specimen, rat, share)

    world.facts.update(
        detective=det,
        partner=partner,
        specimen=SPECIMENS[params.specimen],
        rat=rat,
        share=share,
        place=PLACES[params.place],
        outcome="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child that uses the words "specimen" and "rat".',
        f"Tell a suspenseful story where {f['detective'].id} notices clues, suspects a rat, and shares evidence with {f['partner'].id}.",
        f'Write a foreshadowing-heavy detective tale where a specimen is in danger of being consumed, but sharing saves the day.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    partner = f["partner"]
    specimen = f["specimen"]
    share = f["share"]
    return [
        ("Who was the story about?",
         f"It was about {det.id} and {partner.id}, two detectives who worked together in a quiet room."),
        ("What was in danger?",
         f"The specimen was in danger because a hungry rat had gotten close to it. The clue was safe only after the detectives shared the right food with the rat."),
        ("How did they solve the case?",
         f"{det.id} shared the clue with {partner.id}, and they offered {share.phrase} to the rat. That gentle choice gave the rat something else to consume and kept the specimen safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a specimen?",
         "A specimen is something kept or studied because it is special, unusual, or useful for learning."),
        ("What is a rat?",
         "A rat is a small animal with sharp teeth and whiskers. It can be curious, quick, and sometimes sneaky."),
        ("What does consume mean?",
         "To consume means to eat, drink, or use something up. If an animal consumes food, it eats it."),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, S, R) :- place(P), specimen(S), rat(R), shadowy(P), fragile(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.shadowy:
            lines.append(asp.fact("shadowy", pid))
    for sid, s in SPECIMENS.items():
        lines.append(asp.fact("specimen", sid))
        if s.fragile:
            lines.append(asp.fact("fragile", sid))
    for rid in RATS:
        lines.append(asp.fact("rat", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # smoke test ordinary generation first
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, specimen=None, rat=None, sharing=None,
                                                            detective=None, partner=None, gender=None),
                                       random.Random(777)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid combos:")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
        return 1
    print(f"OK: verify passed with {len(py)} valid combos and a generation smoke test.")
    return 0


def explain_rejection() -> str:
    return "(No story: this combination does not leave room for a believable detective suspense scene.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
