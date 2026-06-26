#!/usr/bin/env python3
"""
A tiny superhero-style story world set in a toy library.

Premise:
A young superhero loves helping in a toy library. On the ninetieth day of
story hour, a slippery shampoo spill and a marshmallow-soft toy cause a small
conflict. The hero learns to solve the problem by using calm teamwork and a
careful cleanup, saving the library day.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["mess", "clean", "stuck", "sparkle"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "conflict", "pride", "worry", "calm", "teamwork"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the toy library"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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


THRESHOLD = 1.0
MESS_KINDS = {"wet", "foamy", "slippery"}

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the toy library", affords={"shelf", "wash", "train"}),
}

ACTIVITIES = {
    "wash": Activity(
        id="wash",
        verb="wash the toy cape",
        gerund="washing the toy cape",
        rush="rush to the sink",
        mess="foamy",
        soil="all foamy",
        zone={"hands", "torso"},
        keyword="shampoo",
        tags={"shampoo", "clean"},
    ),
    "train": Activity(
        id="train",
        verb="train the rescue bot",
        gerund="training the rescue bot",
        rush="dash to the practice mat",
        mess="slippery",
        soil="slippery and messy",
        zone={"hands", "feet"},
        keyword="mallow",
        tags={"mallow", "toy"},
    ),
    "shelf": Activity(
        id="shelf",
        verb="sort the storybooks",
        gerund="sorting storybooks",
        rush="hurry to the shelves",
        mess="wet",
        soil="damp",
        zone={"hands"},
        keyword="ninetieth",
        tags={"library", "ninetieth"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a bright red cape",
        type="cape",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="little blue boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "gloves": Prize(
        label="gloves",
        phrase="soft hero gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a clean apron",
        covers={"torso"},
        guards={"foamy"},
        prep="put on a clean apron",
        tail="put on the apron and came back",
    ),
    Gear(
        id="slipboots",
        label="grippy slip boots",
        covers={"feet"},
        guards={"slippery", "wet"},
        prep="wear grippy slip boots",
        tail="wore the slip boots and returned",
        plural=True,
    ),
    Gear(
        id="drygloves",
        label="dry rescue gloves",
        covers={"hands"},
        guards={"foamy", "wet"},
        prep="wear dry rescue gloves",
        tail="slid on the rescue gloves and came back",
        plural=True,
    ),
]

HERO_NAMES = ["Maya", "Leo", "Nora", "Jett", "Ari", "Zoe"]
VILLAIN_NAMES = ["Mop Mask", "Captain Spill", "Foam Fog"]
TRAITS = ["brave", "kind", "curious", "quick", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid_story(S,A,P) :- affords(S,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize) is not None:
                    out.append((place, act_id, prize_id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate.")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by,
        "protective": v.protective, "covers": set(v.covers), "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["mess"] >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        if activity.mess in MESS_KINDS:
            sig = ("mess", item.id, activity.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            item.meters["clean"] = 0
            if narrate:
                world.say(f"{actor.id}'s {item.label} got messy.")
    for e in world.entities.values():
        if e.caretaker and e.meters["mess"] >= THRESHOLD:
            e.memes["worry"] += 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         parent_type: str = "parent") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the librarian"))
    rival = world.add(Entity(id="Rival", kind="character", type="villain", label="Mop Mask"))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, worn_by=hero.id, plural=prize_cfg.plural
    ))

    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a {random.choice(TRAITS)} superhero in {setting.place}.")
    world.say(f"On the ninetieth story hour, {hero.id} loved the shiny toy library and {activity.gerund}.")
    world.say(f"{hero.id} wore {prize.phrase} like a cape and promised to help the shelves sparkle.")

    world.para()
    world.say(f"Then {rival.label} swooped in with a bottle of shampoo and made a foamy splash.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the shampoo spill made everything tense.")
    world.say(f"{hero.id} saw that {prize.label} could get messy and felt a small conflict in {hero.pronoun('possessive')} chest.")

    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        hero.memes["conflict"] += 1
        hero.memes["worry"] += 1
        world.say(f'"This could ruin my {prize.label}!" {hero.id} said.')
        world.say(f"The librarian held up a calm hand and said, 'We need a safer hero plan.'")
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No reasonable heroic fix exists for this combo.")
        g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers)))
        g.worn_by = hero.id
        world.para()
        world.say(f"{hero.id} nodded, put on {gear.label}, and smiled again.")
        world.say(f"Together they {gear.tail}, and {hero.id} could {activity.gerund} without ruining {prize.label}.")
        hero.memes["conflict"] = 0
        hero.memes["calm"] += 1
        hero.memes["teamwork"] += 1
    else:
        raise StoryError("This story world only tells conflicts that lead to a real fix.")

    world.para()
    world.say(f"In the end, the toy library was neat, the shampoo was gone, and the {prize.label} stayed bright.")
    world.say(f"{hero.id} stood tall like a tiny superhero, ready for the next mission.")

    world.facts.update(hero=hero, parent=parent, rival=rival, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA and narration
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short superhero story set in a toy library that uses the word "{activity.keyword}".',
        f"Tell a gentle conflict story about {hero.id} and a shampoo spill in the toy library.",
        f"Write a child-friendly story where a hero solves a messy problem and keeps {prize.label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, activity, prize, parent = f["hero"], f["activity"], f["prize"], f["parent"]
    return [
        QAItem(
            question=f"Who was the superhero in the toy library story?",
            answer=f"The superhero was {hero.id}, who helped in the toy library and kept trying to do the right thing.",
        ),
        QAItem(
            question=f"What caused the conflict during story hour?",
            answer=f"The conflict started when shampoo made a foamy spill, and {hero.id} worried that {prize.label} would get messy.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} put on {f['gear'].label} and worked with the librarian so {activity.gerund} could happen safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is shampoo for?",
            answer="Shampoo is used to wash hair and help clean out dirt and oil.",
        ),
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where children can borrow toys and play with them carefully.",
        ),
        QAItem(
            question="What does ninetieth mean?",
            answer="Ninetieth means number ninety in order, like the 90th day or the 90th turn.",
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict is a problem or disagreement that makes the characters stop and figure out what to do next.",
        ),
        QAItem(
            question="What is mallow?",
            answer="Mallow is a soft, marshmallow-like treat that can feel squishy and sweet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="library", activity="wash", prize="cape", name="Maya"),
    StoryParams(place="library", activity="train", prize="boots", name="Leo"),
    StoryParams(place="library", activity="shelf", prize="gloves", name="Nora"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world in a toy library.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], hero_name=params.name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
