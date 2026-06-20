#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/speech_mar_lesson_learned_kindness_sharing_folk.py
===================================================================================

A tiny folk-tale story world about a marsh, a speech, a quarrel, and a lesson
learned: a child wants to keep a special thing all to themselves, a wise elder
offers a kind speech, the child sees the trouble, and sharing makes the day
bright again.

The world is deliberately small and classical: typed entities, physical meters,
emotional memes, a forward-chained causal model, grounded QA, and an ASP twin
for parity checking.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "elder"}
        male = {"boy", "father", "dad", "man", "son"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    mood: str
    water: bool = False
    home: bool = False

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind_word: str
    shareable: bool = True
    precious: bool = False
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
class Reaction:
    id: str
    sense: int
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["lonely"] < THRESHOLD:
            continue
        sig = ("lonely", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["worry"] += 1
        out.append("__lonely__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["shared"] < THRESHOLD:
            continue
        sig = ("soften", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["joy"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("lonely", "social", _r_lonely), Rule("soften", "social", _r_soften)]


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


def shareable_with(obj: ObjectThing, p: Place) -> bool:
    return obj.shareable and p.home


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for obj_id, obj in OBJECTS.items():
            if shareable_with(obj, place):
                combos.append((place_id, obj_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    object: str
    reaction: str
    child: str
    elder: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale about a speech, a marsh, kindness, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--elder")
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
    if args.reaction and REACTIONS[args.reaction].sense < SENSE_MIN:
        raise StoryError(f"(Refusing reaction '{args.reaction}': it is too weak for this tale.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    reaction = args.reaction or rng.choice(sorted(r.id for r in sensible_reactions()))
    child = args.child or rng.choice(NAMES_CHILD)
    elder = args.elder or rng.choice(NAMES_ELDER)
    return StoryParams(place, obj, reaction, child, elder)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    obj = OBJECTS[params.object]
    react = REACTIONS[params.reaction]

    child = world.add(Entity(id=params.child, kind="character", type="child", role="child"))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder", role="elder"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="object", type="object", label=obj.label))

    child.memes["want"] += 1
    child.memes["love"] += 1

    world.say(
        f"Long ago, by the {place.label}, {child.id} found {obj.phrase}. "
        f"The little thing seemed to glow in the morning air."
    )
    world.say(
        f"{child.id} made a small speech to {them_name(child)}: "
        f'"This is mine, and I shall keep it all day."'
    )

    world.para()
    if place.water:
        world.say(f"The {place.label_word()} wind came soft over the water, and the day grew quiet.")
    else:
        world.say(f"The path beside the {place.label} was busy with children and birds.")

    child.meters["hold"] += 1
    if obj.precious:
        child.memes["stingy"] += 1
    world.say(
        f"{elder.id} heard the speech and gave a kind speech in return: "
        f'"Kind hands make kind days. Sharing does not make a treasure smaller; '
        f'it makes the heart bigger."'
    )

    world.para()
    child.meters["lonely"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} looked at the {place.label}. The marsh reeds bent and murmured, "
        f"and the day suddenly felt much lonelier."
    )
    world.say(
        f"At last, {child.id} held out {obj.phrase} to {elder.id}, and {elder.id} smiled."
    )
    child.meters["shared"] += 1
    child.memes["stingy"] = 0.0
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"They shared the {obj.label} beside the {place.label}, and even the water "
        f"seemed to shine brighter."
    )
    world.say(
        f"{child.id} learned that a kind speech and a shared thing can turn a lonely "
        f"day into a warm one."
    )

    world.facts.update(
        place=place, object=obj, reaction=react, child=child, elder=elder,
        shared=True, lonely=child.meters["lonely"] >= THRESHOLD,
    )
    return world


def them_name(e: Entity) -> str:
    return "them" if e.pronoun() == "they" else e.pronoun("object")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a small child that includes the words "speech" and "mar".',
        f"Tell a gentle story where {f['child'].id} learns kindness and sharing after a wise speech near the {f['place'].label}.",
        f'Write a short tale with a marshy setting, a small treasure, and a lesson learned about sharing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, elder, place, obj = f["child"], f["elder"], f["place"], f["object"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id}, who meet beside the {place.label} in a folk-tale way."),
        ("What did {0} want to do first?".format(child.id),
         f"{child.id} wanted to keep {obj.phrase} all to {child.pronoun('possessive')} self."),
        ("What did the elder say?".format(child.id),
         f"The elder gave a kind speech about how sharing does not make a treasure smaller. The words were gentle, and they helped {child.id} think again."),
        ("How did the story end?",
         f"{child.id} shared {obj.phrase}, and the day felt warm and bright by the {place.label}. That is the lesson learned: kindness grows when people share."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["object"].tags)
    if f["place"].water:
        tags.add("mar")
    out = []
    for tag in ["mar", "sharing", "kindness"]:
        if tag == "mar" and "mar" in tags:
            out.extend(KNOWLEDGE["mar"])
        elif tag == "sharing":
            out.extend(KNOWLEDGE["sharing"])
        elif tag == "kindness":
            out.extend(KNOWLEDGE["kindness"])
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "marsh": Place("marsh", "the marsh", "soft", water=True, home=True),
    "village_green": Place("village_green", "the village green", "bright", home=True),
    "cottage_yard": Place("cottage_yard", "the cottage yard", "warm", home=True),
}

OBJECTS = {
    "bread": ObjectThing("bread", "a loaf of bread", "a fresh loaf of bread", "bread", precious=True, tags={"sharing"}),
    "berries": ObjectThing("berries", "a small basket of berries", "a small basket of berries", "berries", precious=True, tags={"sharing"}),
    "flute": ObjectThing("flute", "a little flute", "a little flute", "flute", precious=False, tags={"sharing"}),
}

REACTIONS = {
    "share": Reaction("share", 3, "shared the treasure kindly", "tried to keep the treasure, but the child stayed stubborn", "shared the treasure kindly", tags={"sharing", "kindness"}),
    "split": Reaction("split", 2, "split the treasure between them", "could not quite divide it fairly", "split the treasure between them", tags={"sharing"}),
    "hoard": Reaction("hoard", 1, "kept it all and learned nothing", "kept it all and learned nothing", "kept it all and learned nothing", tags={"stingy"}),
}

NAMES_CHILD = ["Mara", "Tobin", "Iris", "Luca", "Nell"]
NAMES_ELDER = ["Old Brin", "Aunt Wren", "Grand Vale", "Elder Moss", "Nana Roa"]

KNOWLEDGE = {
    "mar": [("What is a marsh?",
             "A marsh is wet land with reeds, shallow water, and soft ground. It can feel quiet and a little magical.")],
    "sharing": [("What is sharing?",
                 "Sharing means letting someone else use or enjoy part of something too. It is a kind way to help everyone feel included.")],
    "kindness": [("What is kindness?",
                  "Kindness means being gentle, helpful, and caring with other people. Kind words and fair actions are both part of it.")],
}

CURATED = [
    StoryParams("marsh", "berries", "share", "Mara", "Old Brin"),
    StoryParams("village_green", "bread", "split", "Tobin", "Aunt Wren"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].home:
            lines.append(asp.fact("home", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.shareable:
            lines.append(asp.fact("shareable", oid))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, O) :- place(P), object(O), home(P), shareable(O).
sensible(R) :- reaction(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_reactions()}:
        rc = 1
        print("MISMATCH in sensible reactions")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, object=None, reaction=None, child=None, elder=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible reactions: {', '.join(asp_sensible())}\n")
        for p, o in asp_valid_combos():
            print(f"  {p:12} {o}")
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
