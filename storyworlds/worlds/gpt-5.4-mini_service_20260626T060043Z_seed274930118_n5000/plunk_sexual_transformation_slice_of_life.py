#!/usr/bin/env python3
"""
storyworlds/worlds/plunk_sexual_transformation_slice_of_life.py
===============================================================

A small slice-of-life story world about a gentle plunk, a practical worry,
and a transformation that makes the day feel a little brighter.

Seed image:
---
A child likes the soft plunk of little things dropped into a jar, but the
piece of clothing they are wearing is meant for a special outing. When a spill
would ruin the look, a parent helps turn the moment into a tidy transformation
instead of a messy problem.

World idea:
---
The domain centers on a child doing a quiet indoor activity with a small
sound-making object. The child is attached to one outfit or accessory, and the
parent notices that the activity could stain or scuff it. The resolution is a
simple transformation: either the child changes into play clothes, or the
object being decorated transforms into something safe to use. The ending image
should show the new form and the child's calmer mood.

Narrative instruments:
---
- plunk: a small, audible drop or tap that marks the beginning of the activity
- transformation: a state change from plain to useful, or from risky to safe
- slice_of_life: short, domestic, concrete, and causal

This script follows the Storyweavers contract:
- standalone stdlib script
- typed entities with meters and memes
- Python reasonableness gate plus inline ASP twin
- story, QA, trace, JSON, and verification support
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "clean": 0.0, "calm": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hope": 0.0, "patience": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    noun: str
    verb: str
    gerund: str
    plunk: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Transformation:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little messy.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] += 1
        out.append(f"{actor.id} took a breath and waited.")
    return out


RULES = [Rule("mess", _r_mess), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_transform(activity: Activity, prize: Prize) -> Optional[Transformation]:
    for t in TRANSFORMS:
        if activity.mess in t.guards and prize.region in t.covers:
            return t
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["mess"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved quiet things that made a soft plunk.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} liked {activity.gerund}, because each {activity.noun} made a tiny, happy {activity.plunk}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That morning, {parent.id} bought {hero.pronoun('object')} {prize.phrase} for the day.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["hope"] += 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} carefully.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The room was calm and still, just right for a small {activity.noun} project.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 0.0
    world.say(f"{hero.id} wanted to {activity.verb}, right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f"\"You'll get your {prize.label} {activity.soil},\" {parent.id} said softly.")
    return True


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} looked down and held still for a moment.")


def offer_transformation(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Transformation]:
    t = select_transform(activity, prize)
    if t is None:
        return None
    thing = world.add(Entity(
        id=t.id, type="thing", label=t.label, owner=hero.id, protective=True,
        covers=set(t.covers), plural=t.plural
    ))
    thing.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["soiled"]:
        thing.worn_by = None
        del world.entities[thing.id]
        return None
    world.say(f"{parent.id} smiled and suggested a small transformation: {t.prep}.")
    return t


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, t: Transformation) -> None:
    hero.memes["joy"] += 1
    hero.memes["hope"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"{hero.id} nodded, and their face brightened.")
    world.say(f"They {t.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed clean.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["prize"] = prize
    world.facts["activity"] = activity
    world.facts["setting"] = setting
    intro(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    hesitate(world, hero)
    world.para()
    t = offer_transformation(world, parent, hero, activity, prize)
    if t is not None:
        accept(world, hero, parent, activity, prize, t)
    world.facts["transform"] = t
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"beads", "colors"}),
    "laundry": Setting(place="the laundry room", indoor=True, affords={"beads", "colors"}),
    "table": Setting(place="the little table by the window", indoor=True, affords={"beads", "colors"}),
}

ACTIVITIES = {
    "beads": Activity(
        id="beads",
        noun="beads",
        verb="drop beads into a jar",
        gerund="sorting beads into a jar",
        plunk="plunk",
        mess="scattered",
        soil="scattered across the floor",
        zone={"torso", "hands"},
        keyword="beads",
        tags={"beads", "plunk"},
    ),
    "colors": Activity(
        id="colors",
        noun="paint",
        verb="mix colors in a tray",
        gerund="mixing colors in a tray",
        plunk="plunk",
        mess="smeared",
        soil="smudged with color",
        zone={"torso", "hands"},
        keyword="colors",
        tags={"colors", "plunk"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "dress": Prize(label="dress", phrase="a pretty little dress", type="dress", region="torso"),
    "apron": Prize(label="apron", phrase="a bright apron", type="apron", region="torso"),
}

TRANSFORMS = [
    Transformation(
        id="apron_cover",
        label="a bright apron",
        prep="put on a bright apron first",
        tail="put on the apron and set the beads back in place",
        covers={"torso"},
        guards={"scattered", "smeared"},
    ),
    Transformation(
        id="smock_cover",
        label="an old smock",
        prep="change into an old smock first",
        tail="changed into the smock and kept working",
        covers={"torso"},
        guards={"smeared"},
    ),
]

NAMES = ["Mia", "Noah", "Lena", "Owen", "Ivy", "Theo", "Ruby", "Eli"]
TRAITS = ["quiet", "curious", "gentle", "patient", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a slice-of-life story about a child named {hero.id} and the word "{activity.plunk}".',
        f"Tell a gentle story where {hero.id} wants to {activity.verb} but worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Write a short story that includes a small transformation and ends with {prize.label} staying clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    t: Optional[Transformation] = f.get("transform")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a child named {hero.id} and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {activity.verb}. The little {activity.plunk} sound made the job feel fun.",
        ),
        QAItem(
            question=f"Why did the parent speak up about the {prize.label}?",
            answer=f"The parent worried that {prize.label} would end up {activity.soil} if the activity got underway.",
        ),
    ]
    if t is not None:
        qa.append(
            QAItem(
                question="What helped make the day work out safely?",
                answer=f"They used {t.label} as a small transformation, so the child could keep playing while the {prize.label} stayed clean.",
            )
        )
        qa.append(
            QAItem(
                question="How did the child feel at the end?",
                answer=f"{hero.id} felt happy and calmer after the transformation, and the room stayed tidy.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "plunk": [
        (
            "What does plunk mean?",
            "Plunk is a soft, round sound you hear when something small drops into water, a jar, or a bowl.",
        )
    ],
    "beads": [
        (
            "What are beads?",
            "Beads are tiny, often colorful pieces with holes in them. People string them together or drop them into patterns.",
        )
    ],
    "colors": [
        (
            "Why can mixing colors be fun?",
            "Mixing colors can be fun because new shades appear, and the changes are easy to see right away.",
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is when something changes into a new form or a new use.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("transform"):
        tags.add("transformation")
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="beads", prize="shirt", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="table", activity="colors", prize="dress", name="Owen", gender="boy", parent="father", trait="patient"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the parent would have no honest reason to worry.)"
    return f"(No story: there is no simple transformation in this world that can keep a {prize.label} safe from {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: plunk, a worry, and a transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_transform(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_transform(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
has_transform(A, P) :- prize_at_risk(A, P), transform(T), guards(T, M), mess_of(A, M), covers(T, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_transform(A, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t.id))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, m))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
