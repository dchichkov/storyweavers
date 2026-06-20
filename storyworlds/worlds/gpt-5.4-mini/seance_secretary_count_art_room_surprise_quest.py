#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/seance_secretary_count_art_room_surprise_quest.py
===================================================================================

A small, self-contained storyworld for a folk-tale style art-room adventure.

Seed words:
- seance
- secretary
- count

Seed features:
- Surprise
- Quest
- Conflict

Domain:
An art room where children conduct a gentle "seance" to ask the old paint-lady
for a missing piece, while a careful secretary counts clues and a proud count
tries to hurry the search. The tale turns on the choice between rushing and
counting, ends with a surprising discovery, and leaves the art room changed.

This script follows the Storyweavers contract:
- stdlib only
- imports shared result containers eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, --seed, -n, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness gates and an inline ASP twin
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "lady"}
        male = {"boy", "man", "father", "count", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    hall: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.objects = copy.deepcopy(self.objects)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["hurry"] < THRESHOLD or e.meters["steadiness"] >= THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["confidence"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("calm", "social", _r_calm)]


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


def reasonableness_gate(charm: Charm, target: ObjectThing) -> bool:
    return charm.sense >= SENSE_MIN and target.kind in {"missing_piece", "clue", "keystone"}


def choose_objects() -> list[tuple[str, str]]:
    out = []
    for c in CHARMS.values():
        for t in OBJECTS.values():
            if reasonableness_gate(c, t):
                out.append((c.id, t.id))
    return out


def _count_words(world: World) -> int:
    return sum(1 for obj in world.objects.values() if obj.meters["counted"] >= THRESHOLD)


def seance(world: World, seeker: Entity, secretary: Entity, count: Entity, obj: ObjectThing, charm: Charm) -> None:
    seeker.memes["wonder"] += 1
    secretary.memes["duty"] += 1
    count.memes["pride"] += 1
    world.say(
        f"In the old art room, with jars of paint like bright little moons, "
        f"{seeker.id}, {secretary.id}, and {count.id} began a quiet seance."
    )
    world.say(
        f'Their candle was only a lamp, and {secretary.id} sat like a true secretary, '
        f"ready to count the clues one by one."
    )
    world.say(
        f'They called, "Kind spirit of the art room, tell us where the {obj.label} has gone."'
    )
    world.facts["quest"] = obj.label
    world.facts["charm"] = charm.id


def conflict(world: World, seeker: Entity, secretary: Entity, count: Entity, charm: Charm) -> None:
    seeker.meters["hurry"] += 1
    count.meters["hurry"] += 1
    secretary.meters["steadiness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {count.id}, a proud count in velvet sleeves, wanted to rush the answer. '
        f'"No more waiting," {count.id} said. "We should open every drawer at once."'
    )
    world.say(
        f'{secretary.id} raised a hand. "Not yet," {secretary.id} said. '
        f'"If we count the signs, we will not lose the path."'
    )
    if seeker.memes["wonder"] >= THRESHOLD:
        world.say(f"{seeker.id} listened, and the room grew very still.")


def surprise(world: World, seeker: Entity, secretary: Entity, count: Entity, obj: ObjectThing) -> None:
    obj.meters["found"] = 1
    count.meters["hurry"] = 0
    seeker.memes["joy"] += 1
    secretary.memes["joy"] += 1
    world.say(
        f"Then came the surprise: behind a canvas of gold fish, they found the {obj.label} "
        f"tucked inside a paint basket."
    )
    world.say(
        f"It had not been stolen at all. A ribbon had hidden it, like a shy mouse in a flower pot."
    )


def quest_end(world: World, seeker: Entity, secretary: Entity, count: Entity, obj: ObjectThing) -> None:
    obj.meters["returned"] = 1
    secretary.meters["steadiness"] += 1
    count.memes["humility"] += 1
    world.say(
        f"{secretary.id} counted the clues again, and the answer was plain. "
        f"{seeker.id} carried the {obj.label} back to the easel table."
    )
    world.say(
        f"{count.id} bowed to {secretary.id} and laughed softly. "
        f'"A good count is worth more than a hurried one," said {count.id}.'
    )
    world.say(
        f"By candle-bright lamp light, the art room felt warm and kind, and the quest was done."
    )


def tell(place: Place, charm: Charm, missing: ObjectThing,
         seeker_name: str = "Mina", seeker_gender: str = "girl",
         secretary_name: str = "Pip", secretary_gender: str = "boy",
         count_name: str = "Count Alaric", count_gender: str = "boy") -> World:
    world = World(place)
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    secretary = world.add(Entity(id=secretary_name, kind="character", type=secretary_gender, role="secretary"))
    count = world.add(Entity(id=count_name, kind="character", type=count_gender, role="count"))
    obj = world.add_object(missing)

    seance(world, seeker, secretary, count, obj, charm)
    world.para()
    conflict(world, seeker, secretary, count, charm)
    world.para()
    surprise(world, seeker, secretary, count, obj)
    quest_end(world, seeker, secretary, count, obj)

    world.facts.update(
        seeker=seeker, secretary=secretary, count=count, object=obj,
        place=place, charm=charm, outcome="found", counted=_count_words(world),
    )
    return world


PLACES = {
    "art_room": Place("art_room", "the art room", "an art room", "paint-sweet and bright", {"art", "room"}),
}

OBJECTS = {
    "star_piece": ObjectThing("star_piece", "star piece", "a little star piece from the mural", "missing_piece", {"quest", "art"}),
    "blue_tile": ObjectThing("blue_tile", "blue tile", "a blue tile from the mosaic", "missing_piece", {"quest", "art"}),
    "gold_leaf": ObjectThing("gold_leaf", "gold leaf", "a scrap of gold leaf from the frame", "missing_piece", {"quest", "art"}),
    "glove": ObjectThing("glove", "glove", "a paint glove", "tool", {"art"}),
}

CHARMS = {
    "gentle_seance": Charm("gentle_seance", "gentle seance", "a gentle seance", 3, 3, {"seance", "quest"}),
    "lamp_seance": Charm("lamp_seance", "lamp seance", "a lamp-lit seance", 4, 3, {"seance", "quest"}),
    "whisper_seance": Charm("whisper_seance", "whisper seance", "a whispering seance", 2, 2, {"seance", "quest"}),
}

GENTLE_NAMES = ["Mina", "Lina", "Nora", "Pia", "Tessa", "Elin"]
BOY_NAMES = ["Pip", "Milo", "Ned", "Jasper", "Owen", "Theo"]


@dataclass
class StoryParams:
    place: str
    object: str
    charm: str
    seeker: str
    seeker_gender: str
    secretary: str
    secretary_gender: str
    count: str
    count_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, o) for p in PLACES for c in CHARMS for o in OBJECTS if reasonableness_gate(CHARMS[c], OBJECTS[o])]


KNOWLEDGE = {
    "seance": [("What is a seance?", "A seance is a quiet gathering where people try to speak with spirits or ask for a sign. In a folk tale, it is often done with whispers, lamps, and brave hearts.")],
    "secretary": [("What does a secretary do?", "A secretary keeps records, writes things down, and helps make order from a pile of clues. In stories, a secretary is often calm and careful.")],
    "count": [("What is a count?", "A count is a noble title for a ruler or lord in some old tales. In a folk tale, a count may wear proud clothes and speak with a grand voice.")],
    "art": [("Why is an art room special?", "An art room is special because it holds paints, brushes, papers, and the things children use to make pictures.")],
    "quest": [("What is a quest?", "A quest is a journey or search for something important. The seeker keeps going even when the path is tricky.")],
    "conflict": [("What is a conflict in a story?", "A conflict is the trouble or disagreement that makes the story move. It can be between people who want different things.")],
    "surprise": [("What is a surprise?", "A surprise is something unexpected that changes what the characters thought was happening.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obj = f["object"]
    return [
        f'Write a folk-tale story for a young child set in an art room, and include the words "seance", "secretary", and "count".',
        f"Tell a gentle quest story where {f['seeker'].id}, {f['secretary'].id}, and {f['count'].id} hold a seance to find {obj.label}.",
        f"Write a story with a surprise, a quest, and a conflict, all inside the art room, where a secretary counts clues and a count wants to hurry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker, secretary, count, obj = f["seeker"], f["secretary"], f["count"], f["object"]
    qa = [
        QAItem(
            question="Who went on the quest?",
            answer=f"{seeker.id}, {secretary.id}, and {count.id} all joined the quest in the art room. Each of them had a different part to play, and that helped the search feel like a true story."
        ),
        QAItem(
            question="What was the seance for?",
            answer=f"It was for finding {obj.phrase}. They asked the quiet spirit of the art room for a sign, because the missing piece mattered to their work."
        ),
        QAItem(
            question="What was the conflict?",
            answer=f"{count.id} wanted to rush and open everything at once, but {secretary.id} wanted to count the clues first. That disagreement made the search tense until they chose the careful way."
        ),
        QAItem(
            question="What was surprising about the ending?",
            answer=f"The missing thing was not lost forever at all. It was hiding in a paint basket behind a canvas, so the quest ended in an unexpected but happy way."
        ),
        QAItem(
            question="How did the secretary help?",
            answer=f"{secretary.id} kept the search steady by counting clues one by one. That careful work helped the others see where the trail really led."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["place"].tags) | set(world.facts["charm"].tags) | set(world.facts["object"].tags)
    out = []
    for key in ["art", "seance", "secretary", "count", "quest", "conflict", "surprise"]:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    for o in world.objects.values():
        meters = {k: v for k, v in o.meters.items() if v}
        lines.append(f"  {o.id:12} (object  ) meters={dict(meters)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("art_room", "star_piece", "gentle_seance", "Mina", "girl", "Pip", "boy", "Count Alaric", "boy"),
    StoryParams("art_room", "blue_tile", "lamp_seance", "Lina", "girl", "Ned", "boy", "Count Orin", "boy"),
    StoryParams("art_room", "gold_leaf", "whisper_seance", "Tessa", "girl", "Theo", "boy", "Count Marrow", "boy"),
]


def explain_rejection(charm: Charm, obj: ObjectThing) -> str:
    return f"(No story: the quest charm is not reasonable for the missing thing.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_kind", oid, o.kind))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C,O) :- charm(C), object(O), object_kind(O, missing_piece), sense(C,S), sense_min(M), S >= M.
valid(P,C,O) :- place(P), reasonable(C,O).
"""


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
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    if rc == 0:
        print("OK: verification passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale art-room storyworld with seance, secretary, count.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--secretary")
    ap.add_argument("--secretary-gender", choices=["girl", "boy"])
    ap.add_argument("--count")
    ap.add_argument("--count-gender", choices=["girl", "boy"])
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
    if args.object_ and args.charm:
        if not reasonableness_gate(CHARMS[args.charm], OBJECTS[args.object_]):
            raise StoryError(explain_rejection(CHARMS[args.charm], OBJECTS[args.object_]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.charm is None or c[1] == args.charm)
              and (args.object_ is None or c[2] == args.object_)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, charm, obj = rng.choice(sorted(combos))
    obj_cfg = OBJECTS[obj]
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    secretary_gender = args.secretary_gender or rng.choice(["girl", "boy"])
    count_gender = args.count_gender or "boy"
    seeker = args.seeker or rng.choice(GENTLE_NAMES if seeker_gender == "girl" else BOY_NAMES)
    secretary = args.secretary or rng.choice(GENTLE_NAMES if secretary_gender == "girl" else BOY_NAMES)
    count = args.count or "Count " + rng.choice(["Alaric", "Bram", "Cedric", "Dorian"])
    return StoryParams(place, obj, charm, seeker, seeker_gender, secretary, secretary_gender, count, count_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CHARMS[params.charm], OBJECTS[params.object],
                 params.seeker, params.seeker_gender,
                 params.secretary, params.secretary_gender,
                 params.count, params.count_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c, o in combos:
            print(f"  {p:10} {c:16} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
