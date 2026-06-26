#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thyme_teller_bad_ending_transformation_folk_tale.py
============================================================================================================================

A small folk-tale storyworld about a teller, thyme, and a transformation that
does not end well.

Premise:
- A village teller carries a little thyme sprig because thyme is said to steady
  a shaking voice and sweeten a story.
- A hungry or frightened listener asks for the thyme, or for the story magic
  it seems to hold.
- The teller tries a folk remedy or a rhyme.
- The remedy works, but not the way anyone hoped: someone changes shape, and the
  ending leaves a loss behind.

The domain is intentionally small and classical: a few entities, a few physical
meters, a few emotional memes, and a single causal turn with a bad ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "witch"}
        male = {"boy", "man", "father", "grandfather", "teller"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    action: str
    result: str
    risk: str
    tag: str


@dataclass
class StoryParams:
    place: str
    charm: str
    listener: str
    listener_type: str
    teller_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "village": Place(name="the village green", tags={"folk", "outdoor"}),
    "cottage": Place(name="the old cottage", indoors=True, tags={"folk", "indoor"}),
    "well": Place(name="the stone well", tags={"folk", "outdoor", "water"}),
}

CHARTS = {
    "healing": Charm(
        id="healing",
        label="thyme tea",
        action="brew thyme tea",
        result="steady a trembling voice",
        risk="too much magic",
        tag="thyme",
    ),
    "rhyme": Charm(
        id="rhyme",
        label="thyme rhyme",
        action="whisper a thyme rhyme",
        result="wake the green old power in the herb",
        risk="the rhyme answers back",
        tag="thyme",
    ),
    "pouch": Charm(
        id="pouch",
        label="a thyme pouch",
        action="tie thyme into a pouch",
        result="keep the teller's words from shaking",
        risk="the pouch may call roots to grow",
        tag="thyme",
    ),
}

GIRL_NAMES = ["Mina", "Elsa", "Tara", "Nia", "Lina"]
BOY_NAMES = ["Jory", "Evan", "Milo", "Soren", "Pavel"]
LISTENER_TYPES = ["girl", "boy", "old woman", "old man"]
TALES = ["gentle", "bright", "careful", "wary", "lonely"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about thyme, a teller, and a bad transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARTS)
    ap.add_argument("--listener")
    ap.add_argument("--listener-type", choices=LISTENER_TYPES)
    ap.add_argument("--teller-name")
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
    place = args.place or rng.choice(list(PLACES))
    charm = args.charm or rng.choice(list(CHARTS))
    listener_type = args.listener_type or rng.choice(LISTENER_TYPES)
    if args.listener:
        listener = args.listener
    else:
        listener = rng.choice(GIRL_NAMES if listener_type in {"girl", "old woman"} else BOY_NAMES)
    teller_name = args.teller_name or rng.choice(["Marta", "Ivo", "Edda", "Borin", "Tilda"])
    return StoryParams(place=place, charm=charm, listener=listener, listener_type=listener_type, teller_name=teller_name)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Charm]:
    place = PLACES[params.place]
    charm = CHARTS[params.charm]
    world = World(place)
    teller = world.add(Entity(id="teller", kind="character", type="teller", label=params.teller_name, meters={}, memes={"pride": 0.0, "worry": 0.0, "hope": 0.0}))
    listener = world.add(Entity(id="listener", kind="character", type=params.listener_type, label=params.listener, meters={}, memes={"hunger": 0.0, "curiosity": 0.0, "fear": 0.0}))
    thyme = world.add(Entity(id="thyme", kind="thing", type="thyme", label="thyme", phrase="a little bunch of thyme", owner=teller.id, carried_by=teller.id, meters={"green": 1.0, "magic": 1.0}, memes={"quiet": 1.0}))
    return world, teller, listener, thyme, charm


def tell_story(world: World, teller: Entity, listener: Entity, thyme: Entity, charm: Charm) -> None:
    world.say(f"Long ago, in {world.place.name}, there lived {teller.label} the teller, who kept a little bunch of thyme tucked close to {teller.pronoun('possessive')} sleeve.")
    world.say(f"{teller.label} said thyme could {charm.result}, and the villagers liked to listen when {teller.pronoun().capitalize()} spoke in a soft, steady voice.")
    world.para()
    world.say(f"One evening, {listener.label} came close and asked for the thyme, because {listener.pronoun('subject')} had {charm.risk} in {listener.pronoun('possessive')} heart and wanted the old folk help.")
    teller.memes["hope"] += 1
    listener.memes["curiosity"] += 1
    world.say(f"{teller.label} wanted to help, but {teller.pronoun('possessive')} hand tightened around the herb, for the thyme was the last green thing left from {teller.pronoun('possessive')} mother’s garden.")
    world.para()
    world.say(f"Still, {teller.label} chose a charm. {teller.pronoun().capitalize()} whispered, '{charm.action}, little thyme, and carry the worry away.'")
    thyme.meters["magic"] += 1
    listener.memes["fear"] += 1
    world.say(f"The air grew sharp and sweet. The thyme answered too well, and green light climbed from the sprigs to {listener.label}'s hands.")
    world.para()
    listener.transformed = True
    listener.type = "thyme bush"
    listener.label = f"{listener.label} the thyme bush"
    world.say(f"When the light went out, {listener.label} was no longer a child at all, but a small thyme bush trembling by the well.")
    teller.memes["worry"] += 2
    teller.meters["loss"] = 1.0
    world.say(f"{teller.label} sat down in silence, because the good story had turned into a bad ending, and the thyme scent would not bring the child back.")
    world.facts.update(teller=teller, listener=listener, thyme=thyme, charm=charm, place=world.place)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short folk tale about a teller, a little thyme sprig, and a charm that changes someone in a sad way.",
        f"Tell a story in a village where {f['teller'].label} uses thyme to help {f['listener'].label}, but the help goes wrong.",
        "Write a gentle but eerie tale with thyme, a teller, and an ending where something is transformed and not recovered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teller: Entity = f["teller"]
    listener: Entity = f["listener"]
    charm: Charm = f["charm"]
    qa = [
        QAItem(
            question=f"Who was the story about in {world.place.name}?",
            answer=f"It was about {teller.label}, a teller who carried thyme, and {listener.label}, who came asking for help.",
        ),
        QAItem(
            question=f"What did {teller.label} try to do with the thyme?",
            answer=f"{teller.label} tried to {charm.action} so {listener.pronoun('subject')} could feel better.",
        ),
        QAItem(
            question=f"What happened to {listener.label} at the end?",
            answer=f"{listener.label} was transformed into a thyme bush, so the ending stayed sad and the loss remained.",
        ),
        QAItem(
            question=f"Why did {teller.label} feel bad after the charm?",
            answer=f"The charm worked too strongly, and {listener.label} changed in a way that {teller.label} could not undo.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is thyme?", answer="Thyme is a small herb with tiny leaves and a strong smell. People use it in cooking and sometimes in little folk remedies."),
        QAItem(question="What is a teller in a folk tale?", answer="A teller is someone who tells stories to other people, often by speaking aloud in a village or by a hearth."),
        QAItem(question="What does transformation mean?", answer="Transformation means something changes into a different shape, form, or kind of being."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions ==",]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
thyme(t).
teller(x).
listener(y).
bad_ending :- transformed(y), loss(x).
transformed(y) :- charm(c), uses(x,c), thyme(t), helper(t), risk(c).
helper(t) :- thyme(t).
risk(c) :- charm(c).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("thyme", "t"),
        asp.fact("teller", "x"),
        asp.fact("listener", "y"),
        asp.fact("charm", "c"),
        asp.fact("uses", "x", "c"),
        asp.fact("helper", "t"),
        asp.fact("risk", "c"),
        asp.fact("loss", "x"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show bad_ending/0."))
    ok = any(sym.name == "bad_ending" for sym in model)
    if ok:
        print("OK: ASP twin derives a bad ending.")
        return 0
    print("MISMATCH: ASP twin failed to derive bad ending.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world, teller, listener, thyme, charm = _setup_world(params)
    tell_story(world, teller, listener, thyme, charm)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="village", charm="healing", listener="Mira", listener_type="girl", teller_name="Edda"),
            StoryParams(place="cottage", charm="rhyme", listener="Oren", listener_type="boy", teller_name="Borin"),
            StoryParams(place="well", charm="pouch", listener="Hilda", listener_type="old woman", teller_name="Tilda"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
