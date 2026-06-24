#!/usr/bin/env python3
"""
A small comedy storyworld about an episcopal misunderstanding.

A bishop, a choir, and a very earnest helper misread one another's plans,
creating a harmless, funny mix-up that resolves through clarification and a
better idea.
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
    wears: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"woman", "girl", "mother", "sister"}
        masculine = {"man", "boy", "father", "brother", "bishop", "deacon"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name(self) -> str:
        return self.label or self.id

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    style: str
    genders: set[str] = field(default_factory=lambda: {"woman", "man"})
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
    ceremonial: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


PLACES = {
    "hall": Place("hall", "the parish hall", True, {"singing", "baking"}),
    "garden": Place("garden", "the church garden", False, {"flowers", "picnic"}),
    "chapel": Place("chapel", "the small chapel", True, {"singing"}),
}

ACTIONS = {
    "singing": Activity(
        id="singing",
        verb="lead the choir",
        gerund="leading the choir",
        rush="hurry to the front",
        mess="loud",
        effect="made the echo bounce off the walls",
        keyword="choir",
        tags={"choir", "music"},
    ),
    "flowers": Activity(
        id="flowers",
        verb="arrange the flowers",
        gerund="arranging flowers",
        rush="dash to the flower buckets",
        mess="pollen",
        effect="made the petals drift onto every sleeve",
        keyword="flowers",
        tags={"flowers", "garden"},
    ),
    "baking": Activity(
        id="baking",
        verb="serve the buns",
        gerund="serving warm buns",
        rush="hurry to the oven",
        mess="crumbs",
        effect="made crumbs appear like tiny confetti",
        keyword="buns",
        tags={"buns", "kitchen"},
    ),
}

PROPS = {
    "robe": Prop("robe", "a white robe", "a white robe with shiny buttons", "torso", "ceremonial"),
    "hat": Prop("hat", "a tall hat", "a tall hat with a purple ribbon", "head", "ceremonial"),
    "apron": Prop("apron", "an apron", "an apron with floury pockets", "torso", "ordinary"),
    "gloves": Prop("gloves", "gloves", "a pair of gardening gloves", "hands", "ordinary", plural=True),
}

FIXES = [
    Fix("wash", "a clean towel", "wipe the mishap away with a clean towel", "wiped away the mess", {"torso", "hands"}, {"crumbs", "pollen", "loud"}),
    Fix("change", "a spare robe", "put on a spare robe", "changed into the spare robe", {"torso"}, {"crumbs", "pollen"}),
    Fix("mute", "a softer plan", "use a softer plan and speak one at a time", "used a softer plan", {"head", "torso", "hands"}, {"loud"}),
]

NAMES = {
    "bishop": ["Bishop Ada", "Bishop Ruth", "Bishop Nora", "Bishop Helen"],
    "deacon": ["Deacon Milo", "Deacon Jonah", "Deacon Felix", "Deacon Eli"],
    "helper": ["Mina", "Toby", "Jasper", "Lena"],
    "choir": ["the choir", "the children’s choir", "the parish choir"],
}


@dataclass
class StoryParams:
    place: str
    activity: str
    robe: str
    bishop_name: str
    helper_name: str
    seed: Optional[int] = None


def apply_mess(world: World, actor: Entity, act: Activity) -> None:
    actor.meters[act.mess] = actor.meters.get(act.mess, 0) + 1
    actor.memes["excited"] = actor.memes.get("excited", 0) + 1
    for e in world.entities.values():
        if e.wears and e.wears in {world.facts["prop"].id}:
            pass


def predict(world: World, act: Activity, prop: Prop) -> dict:
    sim = world.copy()
    singer = sim.get("bishop")
    singer.meters[act.mess] = singer.meters.get(act.mess, 0) + 1
    ruined = prop.region == "torso" and act.mess in {"crumbs", "pollen"} and sim.place.indoors
    return {"ruined": ruined}


def choose_fix(act: Activity, prop: Prop) -> Optional[Fix]:
    for fx in FIXES:
        if prop.region in fx.covers and act.mess in fx.guards:
            return fx
    return None


def tell(place: Place, act: Activity, prop: Prop, bishop_name: str, helper_name: str) -> World:
    world = World(place)
    bishop = world.add(Entity("bishop", "character", "bishop", bishop_name))
    helper = world.add(Entity("helper", "character", "helper", helper_name))
    choir = world.add(Entity("choir", "character", "group", "the choir", plural=True))
    robe = world.add(Entity("robe", "thing", "robe", prop.label, prop.phrase, owner="bishop", plural=prop.plural))
    robe.wears = bishop.id

    world.facts.update(bishop=bishop, helper=helper, choir=choir, prop=prop, act=act, place=place, robe=robe)
    world.say(f"{bishop.name()} was an episcopal visitor with a kind smile and a very serious robe.")
    world.say(f"{helper.name()} liked helping at {place.label}, especially when {bishop.name()} was there.")
    world.say(f"The day began with {bishop.name()} wanting to {act.verb}, because {act.effect}.")

    world.para()
    if place.indoors:
        world.say(f"Inside {place.label}, everyone heard a whisper that sounded like a plan.")
    else:
        world.say(f"Outside {place.label}, the breeze carried every word a little too far.")
    world.say(f"{helper.name()} thought {bishop.name()} said to {act.rush}, so {helper.name()} rushed off to be useful.")
    world.say(f"But {bishop.name()} only meant to get ready, not to start in a hurry.")

    world.para()
    apply_mess(world, bishop, act)
    world.say(f"When {bishop.name()} got to work, {act.effect}.")
    if act.mess == "crumbs":
        world.say(f"The crumbs landed on {prop.label}, which made {helper.name()} blink twice and look worried.")
    elif act.mess == "pollen":
        world.say(f"The pollen drifted over {prop.label}, and {helper.name()} sneezed so politely that it was funny.")
    else:
        world.say(f"The noise made the room wobble with comic importance.")

    fix = choose_fix(act, prop)
    if fix is None:
        raise StoryError("No reasonable comic fix exists for this combination.")
    world.facts["fix"] = fix

    world.para()
    world.say(f"Then {helper.name()} laughed softly and said, \"Oh! I heard that wrong.\"")
    if fix.id == "mute":
        world.say(f"{bishop.name()} nodded. \"That is a much better idea,\" {bishop.pronoun('subject')} said.")
    else:
        world.say(f"{bishop.name()} pointed to {fix.label} and smiled as if the whole mix-up had been planned.")
    world.say(f"They {fix.prep}, and soon the whole place felt tidy again.")

    world.para()
    world.say(f"After that, {bishop.name()} could {act.verb} without any trouble.")
    if fix.id == "change":
        world.say(f"The spare robe stayed clean, and {helper.name()} looked proud of the rescue.")
    elif fix.id == "wash":
        world.say(f"The towel did its job, and the joke of the day was how serious everyone had looked.")
    else:
        world.say(f"The softer plan kept the laughter gentle, and the choir started in the right key.")
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bishop: Entity = f["bishop"]
    helper: Entity = f["helper"]
    act: Activity = f["act"]
    prop: Prop = f["prop"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"What did {bishop.name()} want to do at {world.place.label}?",
            answer=f"{bishop.name()} wanted to {act.verb}, and that is what the story was building toward.",
        ),
        QAItem(
            question=f"Why did {helper.name()} get mixed up?",
            answer=f"{helper.name()} heard the wrong part of the plan and thought {bishop.name()} meant to {act.rush}. That misunderstanding made the day funny instead of serious.",
        ),
        QAItem(
            question=f"What got messy during the story?",
            answer=f"{prop.label} got caught in the mess when the action started, so everyone had to pause and sort it out.",
        ),
        QAItem(
            question=f"How did they fix the misunderstanding?",
            answer=f"They chose {fix.label} and followed the plan to {fix.tail}, which cleared up the confusion and let the story end happily.",
        ),
    ]


def knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bishop?",
            answer="A bishop is a church leader who helps guide worship and take care of the congregation.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people hear or think about the same thing in different ways.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy can be funny because people make mistakes, get mixed up, and then solve the problem in a cheerful way.",
        ),
    ]


def prompts(world: World) -> list[str]:
    f = world.facts
    act: Activity = f["act"]
    return [
        f"Write a short comedy story about an episcopal misunderstanding involving the word '{act.keyword}'.",
        f"Tell a gentle story where a bishop tries to {act.verb} but someone hears it wrong and everyone laughs kindly.",
        f"Write a child-friendly story about church helpers, a mix-up, and a funny fix.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes} wears={e.wears}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hall). place(garden). place(chapel).
indoors(hall). indoors(chapel).
affords(hall,singing). affords(hall,baking).
affords(garden,flowers). affords(garden,picnic).
affords(chapel,singing).

activity(singing). mess_of(singing,loud). splashes(singing,torso).
activity(flowers). mess_of(flowers,pollen). splashes(flowers,torso).
activity(baking). mess_of(baking,crumbs). splashes(baking,torso).

prop(robe). worn_on(robe,torso).
prop(hat). worn_on(hat,head).
prop(apron). worn_on(apron,torso).
prop(gloves). worn_on(gloves,hands).

fix(wash). guards(wash,crumbs). guards(wash,pollen). covers(wash,torso). covers(wash,hands).
fix(change). guards(change,crumbs). guards(change,pollen). covers(change,torso).
fix(mute). guards(mute,loud). covers(mute,head). covers(mute,torso). covers(mute,hands).

at_risk(A,P) :- splashes(A,R), worn_on(P,R).
compatible(F,A,P) :- fix(F), at_risk(A,P), guards(F,M), mess_of(A,M), covers(F,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), at_risk(A,P), compatible(_,A,P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.indoors:
            lines.append(asp.fact("indoors", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for a in ACTIONS.values():
        lines.append(asp.fact("activity", a.id))
        lines.append(asp.fact("mess_of", a.id, a.mess))
        for r in {"torso"}:
            lines.append(asp.fact("splashes", a.id, r))
    for pr in PROPS.values():
        lines.append(asp.fact("prop", pr.id))
        lines.append(asp.fact("worn_on", pr.id, pr.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for act in ACTIONS.values():
            for prop in PROPS.values():
                if act.id in place.affords and prop.region == "torso":
                    out.append((place.id, act.id, prop.id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with an episcopal misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--bishop-name")
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prop:
        combos = [c for c in combos if c[2] == args.prop]
    if not combos:
        raise StoryError("No valid comedy combination matches the given options.")
    place, activity, prop = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        robe=prop,
        bishop_name=args.bishop_name or rng.choice(NAMES["bishop"]),
        helper_name=args.helper_name or rng.choice(NAMES["helper"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIONS[params.activity],
        PROPS[params.robe],
        params.bishop_name,
        params.helper_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=knowledge_qa(world),
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


CURATED = [
    StoryParams("hall", "baking", "robe", "Bishop Ada", "Mina"),
    StoryParams("garden", "flowers", "robe", "Bishop Ruth", "Toby"),
    StoryParams("chapel", "singing", "robe", "Bishop Nora", "Jasper"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
