#!/usr/bin/env python3
"""
storyworlds/worlds/print_protect_rink_transformation_rhyming_story.py
=====================================================================

A small Storyweavers world for a rhyming tale about a rink, a print, and a
protective transformation.

Seed-tale idea:
---
At the rink, a child wants to print bright signs and pictures for a tiny show.
The printing can splash ink, so a parent worries about a white shirt getting
stained. They choose a sensible protective layer, print together, and the plain
paper transforms into a bright banner that makes the rink feel new.

World model:
- Physical meters track ink, clean/dirty, bright/plain, and protective coverage.
- Emotional memes track desire, worry, delight, pride, and calm.
- The story turns on a transformation: plain paper becomes a bright rink banner.
- The compromise is protective gear that keeps the shirt clean while printing.

Style:
- Child-facing, concrete, lightly rhyming prose.
- State-driven narration, not a frozen paragraph.
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
MESS_KINDS = {"ink"}
REGIONS = {"torso"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
    keyword: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.m("ink") < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["ink"] = item.m("ink") + 1
            item.meters["dirty"] = item.m("dirty") + 1
            out.append(f"{actor.id}'s {item.label} got inky and dirty.")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    banner = world.entities.get("banner")
    if not banner:
        return out
    if world.facts.get("printed") and banner.m("bright") < THRESHOLD:
        sig = ("bright", banner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            banner.meters["bright"] = 1
            banner.meters["plain"] = 0
            out.append("The plain banner turned bright and merry.")
    return out


CAUSAL_RULES = [Rule("soak", _r_soak), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.m("dirty") >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} does not support {activity.id}.)")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.m(activity.mess) + 1
    actor.memes["joy"] = actor.e("joy") + 1
    world.facts["printed"] = True
    propagate(world, narrate=narrate)


def rhyming_open(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"At the rink with a twinkly blink, {hero.id} had a plan to think and think. "
        f"{hero.id} loved bright signs and a happy line, and {hero.id}'s {prize.label} looked neat and fine."
    )
    world.say(
        f"{hero.id} wanted to print and make things shine, but {hero.pronoun('possessive')} "
        f"{parent.label} gave a worried sign: the ink could spatter, the shirt could smatter, "
        f"and that would be a messy matter."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Prize) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you print too fast, your {prize.label} may get {activity.soil}," '
        f"{parent.label} said with a careful grin. "
        f'"Let us protect you first, then print with cheer, so the rink stays tidy and clear."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.e("defiance") + 1
    world.say(
        f"{hero.id} huffed at first, then gave a little squint, "
        f"and tried to dash right in to print."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            gear = g
            break
    if gear is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        return None
    obj = world.add(
        Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
        )
    )
    obj.worn_by = hero.id
    world.say(
        f"Then {parent.label} smiled and said, 'Let's not fight; let's do this right. "
        f"We can put on {gear.label} with a handy sway, and print on the sign in a softer way.'"
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Prize, gear: Gear) -> None:
    hero.memes["joy"] = hero.e("joy") + 1
    hero.memes["calm"] = hero.e("calm") + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} wore {gear.label}, and the worry fell light. "
        f"{hero.id} smiled so wide, the whole rink felt bright."
    )
    world.say(
        f"Together they printed a sign that gleamed, and the plain page changed like a lovely dream. "
        f"At the rink the banner shone, and {hero.id} felt proud to the bone."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Lena",
         hero_type: str = "girl", parent_type: str = "mother", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(
        Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["cheery", "curious"]))
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(
        Entity(
            id="shirt",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )
    banner = world.add(Entity(id="banner", type="thing", label="banner", meters={"plain": 1.0, "bright": 0.0}))

    rhyming_open(world, hero, parent, prize)

    world.para()
    world.say(
        f"They went to the rink with inks and a wink, where paper and pictures could gently think. "
        f"{hero.id} wanted to print a banner so neat, while {parent.label} watched for a splatter or streak."
    )
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        _do_activity(world, hero, activity, narrate=False)
        accept(world, hero, parent, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, banner=banner, gear=gear)
    return world


SETTINGS = {
    "rink": Setting(place="the rink", affords={"print"}),
}

ACTIVITIES = {
    "print": Activity(
        id="print",
        verb="print a bright sign",
        gerund="printing bright signs",
        rush="rush to the table and print",
        mess="ink",
        soil="ink-spattered",
        zone={"torso"},
        keyword="print",
        tags={"print", "ink", "transform"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean white shirt",
        type="shirt",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a blue apron",
        covers={"torso"},
        guards={"ink"},
        prep="put on a blue apron first",
        tail="put on the blue apron first",
    ),
]

GIRL_NAMES = ["Lena", "Mina", "Rosa", "Tia", "Nina"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Eli", "Theo"]
TRAITS = ["cheery", "curious", "brave", "spry", "gentle"]


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


KNOWLEDGE = {
    "print": [("What does it mean to print?", "To print means to make words or pictures appear on paper or another surface.")],
    "ink": [("What is ink?", "Ink is a colored liquid used for writing and printing.")],
    "transform": [("What is a transformation?", "A transformation is a change that turns something into something different.")],
    "apron": [("What is an apron for?", "An apron helps protect your clothes from spills and splashes.")],
    "rink": [("What is a rink?", "A rink is a smooth place for skating, rolling, or special games.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [("rink", "print", "shirt")]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        'Write a short rhyming story for a little child about print, protect, and rink.',
        f"Tell a gentle rhyming story where {hero.id} wants to {act.verb} at {world.setting.place} "
        f"but {parent.label} worries about {prize.phrase}.",
        "Write a child-friendly story that begins at a rink, includes a print, and ends with a happy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} at the rink?",
            answer=f"{hero.id} wanted to {act.verb} at the rink while {parent.label} watched carefully.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried that the ink would get on {hero.id}'s {prize.label} and leave it messy.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The plain banner turned bright, and the rink moment felt like a little transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    tags.add("rink")
    out = []
    for key in ["print", "ink", "transform", "apron", "rink"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.id} at the rink is not a reasonable setup for {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming rink story of print, protect, and transformation.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    place = args.place or "rink"
    activity = args.activity or "print"
    prize = args.prize or "shirt"
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, [params.trait, "stubborn"])
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


CURATED = [
    StoryParams(place="rink", activity="print", prize="shirt", name="Lena", gender="girl", parent="mother", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:8} {prize:8}")
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


if __name__ == "__main__":
    main()
