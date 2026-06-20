#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/avoid_repetition_sharing_animal_story.py
========================================================================

A standalone storyworld for a small animal tale about sharing, repeating a
safe choice, and avoiding a trouble spot.

Seed idea
---------
A little animal wants a treat, but the forest has a place to avoid. A helpful
friend suggests sharing the snack instead of taking turns the noisy way, and
the animals repeat the safer plan until the job is done.

This world keeps the story small:
- one animal wants something shiny or sweet
- another animal notices a place or behavior to avoid
- they repeat a safe routine
- they share, and the ending image proves the change

The prose is state-driven: physical meters and emotional memes accumulate into
a turn and a resolution.
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
SENSE_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "hen"}
        male = {"boy", "father", "dad", "man", "brother", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    avoid_spot: str
    repeat_routine: str
    share_table: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    plural: bool = False
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Caution:
    id: str
    label: str
    avoid_phrase: str
    reason: str
    repeated_action: str
    success_phrase: str
    sense: int
    tags: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_avoid(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("avoid_triggered") and "hazard" in world.entities:
        haz = world.get("hazard")
        if haz.meters["crowded"] < THRESHOLD:
            sig = ("avoid", haz.id)
            if sig not in world.fired:
                world.fired.add(sig)
                haz.meters["crowded"] += 1
                out.append("__avoid__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["repeat"] < THRESHOLD:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["confidence"] += 1
        out.append(f"{e.id} kept the same safe rhythm.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared") and "treat" in world.entities:
        treat = world.get("treat")
        if treat.meters["shared"] < THRESHOLD:
            sig = ("share", treat.id)
            if sig not in world.fired:
                world.fired.add(sig)
                treat.meters["shared"] += 1
                out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule("avoid", "social", _r_avoid),
    Rule("repeat", "social", _r_repeat),
    Rule("share", "social", _r_share),
]


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


def hazard_at_risk(place: Place, treat: Treat, caution: Caution) -> bool:
    return bool(place.avoid_spot and treat.shareable and caution.sense >= SENSE_MIN)


def sensible_cautions() -> list[Caution]:
    return [c for c in CAUTIONS.values() if c.sense >= SENSE_MIN]


def best_caution() -> Caution:
    return max(CAUTIONS.values(), key=lambda c: c.sense)


def tell(place: Place, treat: Treat, caution: Caution,
         seeker_name: str = "Milo", seeker_type: str = "rabbit",
         friend_name: str = "Pip", friend_type: str = "fox") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type,
                              role="seeker", traits=["eager"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type,
                              role="friend", traits=["kind", "careful"]))
    hazard = world.add(Entity(id="hazard", type="thing", label=place.avoid_spot))
    treat_ent = world.add(Entity(id="treat", type="thing", label=treat.label))
    seeker.memes["want"] += 1
    friend.memes["care"] += 1

    world.say(
        f"In {place.name}, {seeker.id} and {friend.id} found {place.detail}. "
        f"{seeker.id} wanted {treat.phrase} by {place.share_table}."
    )
    world.say(
        f'But {friend.id} pointed at {place.avoid_spot} and said, '
        f'"We should avoid that place. {caution.reason}"'
    )

    world.para()
    seeker.memes["repetition"] += 1
    world.facts["avoid_triggered"] = True
    world.say(
        f"{seeker.id} nodded and tried the safer way once. Then {seeker.id} tried "
        f"it again, using the same careful steps."
    )
    propagate(world, narrate=True)

    world.para()
    world.facts["shared"] = True
    treat_ent.meters["shared"] += 0.0
    if caution.sense >= SENSE_MIN:
        world.say(
            f"{friend.id} slid {treat.phrase} between them, and they shared it one "
            f"small bite at a time."
        )
        world.say(
            f"At the end, {place.share_table} was still neat, {place.avoid_spot} "
            f"was left alone, and {seeker.id} and {friend.id} smiled with full bellies."
        )
        seeker.memes["joy"] += 1
        friend.memes["joy"] += 1
        treat_ent.meters["shared"] += 1
    else:
        world.say(
            f"They never quite settled on the plan, and the snack stayed in the basket."
        )

    world.facts.update(
        place=place, treat=treat, caution=caution,
        seeker=seeker, friend=friend, hazard=hazard, treat_ent=treat_ent,
        repeated=seeker.memes["repetition"] >= THRESHOLD,
        shared=treat_ent.meters["shared"] >= THRESHOLD,
    )
    return world


PLACES = {
    "meadow": Place("meadow", "the meadow", "the ant hill",
                    "step the same safe path", "the picnic log",
                    "The grass was soft, and little flowers nodded in the breeze.",
                    tags={"outdoor", "avoid"}),
    "pond": Place("pond", "the pond bank", "the slippery reeds",
                  "walk the same careful loop", "the flat rock",
                  "The water shone like glass, and dragonflies zipped overhead.",
                  tags={"outdoor", "avoid"}),
    "orchard": Place("orchard", "the orchard", "the bee nest",
                     "take the same quiet trail", "the wooden crate",
                     "Apples hung low, and the trees made cool shade.",
                     tags={"outdoor", "avoid"}),
}

TREATS = {
    "berries": Treat("berries", "berries", "a little bowl of berries", False, True, {"share"}),
    "crumbs": Treat("crumbs", "crumbs", "a tiny pile of seed crumbs", True, True, {"share"}),
    "cubes": Treat("cubes", "apple cubes", "a plate of apple cubes", False, True, {"share"}),
}

CAUTIONS = {
    "gentle": Caution("gentle", "gentle", "avoid that place",
                      "It could make a messy tumble, so a careful path is better.",
                      "take the same careful steps", "They chose the careful path again.",
                      3, tags={"avoid", "repetition"}),
    "careful": Caution("careful", "careful", "avoid the bees",
                       "A loud rush could wake the bees, so the quiet trail is smarter.",
                       "move the same quiet way", "They kept the quiet way.",
                       4, tags={"avoid", "repetition"}),
    "patient": Caution("patient", "patient", "avoid the mud patch",
                       "Mud sticks to paws, so slow steps keep the snack clean.",
                       "step the same slow way", "They stayed slow and steady.",
                       5, tags={"avoid", "repetition"}),
}

SEEKER_NAMES = ["Milo", "Nina", "Toby", "Luna", "Pip", "Ruby", "Poppy", "Bram"]
FRIEND_NAMES = ["Pip", "Fern", "Otis", "Rory", "Tara", "Benny", "Wren", "Maisie"]
SEEKER_TYPES = ["rabbit", "mouse", "squirrel", "badger", "deer", "hedgehog"]
FRIEND_TYPES = ["fox", "owl", "rabbit", "beaver", "deer", "cat"]


@dataclass
class StoryParams:
    place: str
    treat: str
    caution: str
    seeker: str
    seeker_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TREATS:
            for c in CAUTIONS:
                if hazard_at_risk(PLACES[p], TREATS[t], CAUTIONS[c]):
                    combos.append((p, t, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about avoiding a place, repeating a safe path, and sharing a treat.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--caution", choices=CAUTIONS)
    ap.add_argument("--seeker")
    ap.add_argument("--friend")
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
              and (args.treat is None or c[1] == args.treat)
              and (args.caution is None or c[2] == args.caution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treat, caution = rng.choice(sorted(combos))
    seeker = args.seeker or rng.choice(SEEKER_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != seeker])
    seeker_type = rng.choice(SEEKER_TYPES)
    friend_type = rng.choice(FRIEND_TYPES)
    return StoryParams(place, treat, caution, seeker, seeker_type, friend, friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, treat, caution = f["place"], f["treat"], f["caution"]
    return [
        f'Write an animal story for a 3-to-5-year-old that uses the word "avoid".',
        f"Tell a small forest story where {f['seeker'].id} and {f['friend'].id} "
        f"share {treat.phrase}, repeat a safe route, and avoid {place.avoid_spot}.",
        f"Write a gentle animal story where friends solve a snack problem by "
        f"sharing and repeating the same careful steps.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p: Place = f["place"]
    t: Treat = f["treat"]
    c: Caution = f["caution"]
    s: Entity = f["seeker"]
    fr: Entity = f["friend"]
    qa = [
        ("Who is the story about?",
         f"It is about {s.id} and {fr.id}, two little animals sharing a snack in {p.name}."),
        ("What did they need to avoid?",
         f"They needed to avoid {p.avoid_spot}. {c.reason}"),
        ("What did they do instead?",
         f"They repeated {c.repeated_action} and then shared {t.phrase} together."),
        ("Why did the friend speak up?",
         f"{fr.id} saw a place to avoid and wanted the snack time to stay safe. "
         f"That is why {fr.id} suggested the careful path right away."),
        ("How did the story end?",
         f"It ended with sharing, a safe path, and a neat table. The animals stayed away from {p.avoid_spot} and finished the treat together."),
    ]
    return qa


KNOWLEDGE = {
    "avoid": [("What does avoid mean?",
               "Avoid means to stay away from something on purpose so you do not run into it or use it.")],
    "share": [("What does share mean?",
               "Share means to let someone else have some of what you have, or to use something together.")],
    "repeat": [("What does repeat mean?",
                "Repeat means to do the same thing again, like saying a word again or taking the same safe step again.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["treat"].tags) | set(world.facts["caution"].tags)
    tags |= {"avoid", "share", "repetition"}
    out = []
    for tag in ["avoid", "repeat", "share"]:
        out.extend(KNOWLEDGE.get(tag, []))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
avoid_needed(P, T, C) :- place(P), treat(T), caution(C), shareable(T), sense(C, S), sense_min(M), S >= M.
repeated(P) :- place(P), caution(C), avoid_needed(P, _, C).
shared(P, T) :- place(P), treat(T), avoid_needed(P, T, _).
valid(P, T, C) :- avoid_needed(P, T, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for cid, c in CAUTIONS.items():
        lines.append(asp.fact("caution", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH in the gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams("meadow", "berries", "gentle", "Milo", "rabbit", "Pip", "fox"),
    StoryParams("pond", "crumbs", "careful", "Nina", "mouse", "Fern", "owl"),
    StoryParams("orchard", "cubes", "patient", "Toby", "squirrel", "Wren", "deer"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TREATS[params.treat], CAUTIONS[params.caution],
                 params.seeker, params.seeker_type, params.friend, params.friend_type)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, t, c in combos:
            print(f"  {p:8} {t:8} {c}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker} & {p.friend}: avoid {p.place} / share {p.treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
