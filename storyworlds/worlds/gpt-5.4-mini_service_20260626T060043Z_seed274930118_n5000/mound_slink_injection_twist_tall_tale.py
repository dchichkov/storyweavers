#!/usr/bin/env python3
"""
storyworlds/worlds/mound_slink_injection_twist_tall_tale.py
===========================================================

A tiny tall-tale story world about a child, a towering mound, a slinky wish,
and a jam injection that calls for a sensible twist.

The seed image:
- A child wants to slink up near a giant mound in a bakery.
- A parent worries the child's clean shirt will get dusty.
- A clever compromise uses an apron, and a jam injection adds a playful twist.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.meters.setdefault("dusty", 0.0)
        self.meters.setdefault("sticky", 0.0)
        self.meters.setdefault("workload", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("desire", 0.0)
        self.memes.setdefault("conflict", 0.0)
        self.memes.setdefault("grabbed_by", 0.0)

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the bakery"
    indoor: bool = True
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
    twist: str
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
        self.zone: set[str] = set()
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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dusty"] < THRESHOLD and actor.meters["sticky"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            if item.meters["dusty"] >= THRESHOLD and item.meters["sticky"] >= THRESHOLD:
                continue
            item.meters["dusty"] += actor.meters["dusty"]
            item.meters["sticky"] += actor.meters["sticky"]
            out.append(f"{actor.id}'s {item.label} got dusty and sticky.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if (item.meters["dusty"] < THRESHOLD and item.meters["sticky"] < THRESHOLD) or not item.caretaker:
            continue
        carer = world.get(item.caretaker)
        if carer.meters["workload"] >= THRESHOLD:
            continue
        carer.meters["workload"] += 1
        out.append(f"That would mean more washing for {carer.label_word}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        if actor.memes["conflict"] >= THRESHOLD:
            continue
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soil, _r_workload, _r_conflict):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters[activity.mess] += 1
    sim.get(actor.id).memes["joy"] += 1
    prize = sim.entities[prize_id]
    if prize.region in activity.zone:
        prize.meters[activity.mess] += 1
        prize.meters["sticky"] += 1 if activity.mess == "sticky" else 0
    return {"soiled": bool(prize.meters["dusty"] >= THRESHOLD or prize.meters["sticky"] >= THRESHOLD)}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


SETTINGS = {
    "bakery": Setting(place="the bakery", indoor=True, affords={"mound"}),
}

ACTIVITIES = {
    "mound": Activity(
        id="mound",
        verb="slink around the mound",
        gerund="slinking around the mound",
        rush="slink up to the mound",
        mess="dusty",
        soil="dusty as a biscuit tin",
        zone={"torso"},
        keyword="mound",
        twist="injection",
        tags={"mound", "slink", "injection"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean white shirt",
        type="shirt",
        region="torso",
    ),
    "vest": Prize(
        label="vest",
        phrase="a bright red vest",
        type="vest",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"dusty", "sticky"},
        prep="put on an apron first",
        tail="slipped on the apron",
    ),
]

GIRL_NAMES = ["Mabel", "Nora", "Pearl", "Sadie", "Tilly"]
BOY_NAMES = ["Bram", "Milo", "Otis", "Rudy", "Wes"]
TRAITS = ["curious", "bright-eyed", "lively", "stubborn", "cheerful"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale about a mound, a slink, and an injection.")
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
            raise StoryError("That combination does not make a reasonable tall tale.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} with a nose for big surprises.")


def _set_scene(world: World, hero: Entity, parent: Entity, act: Activity) -> None:
    world.say(f"In {world.setting.place}, there stood a mound so tall it looked like a hill that had learned to stand on a spoon.")
    world.say(f"{hero.id} loved to {act.verb}, because the whole place felt like a secret made of flour and sunshine.")


def _warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, act, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = act.soil
    world.say(
        f'"If you go near that mound, you may get your {prize.label} {act.soil}," '
        f"{parent.label_word} said. \"Then I'd have to wash it.\""
    )
    return True


def _compromise(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(act, prize)
    if gear is None:
        return None
    g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    g.worn_by = hero.id
    if predict_mess(world, hero, act, prize.id)["soiled"]:
        g.worn_by = None
        del world.entities[g.id]
        return None
    world.say(f'{parent.label_word} had a better idea: "{gear.prep}, and then you can play."')
    return gear


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    act = ACTIVITIES[params.activity]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait, "stubborn"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    prize = world.add(Entity(id="Prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=parent.id, region=PRIZES[params.prize].region))
    _introduce(world, hero)
    _set_scene(world, hero, parent, act)
    world.say(f"{hero.id} had {hero.pronoun('possessive')} {prize.label}, and {hero.id} liked it brighter than a parade flag.")
    world.para()
    world.say(f"One day, {hero.id} wanted to slink nearer and nearer to the mound, where a baker was readying an {act.twist} to fill buns with jam.")
    _warn(world, parent, hero, act, prize)
    hero.memes["worry"] += 1
    hero.memes["desire"] += 1
    hero.memes["grabbed_by"] += 1
    propagate(world)
    world.say(f"{hero.id} tried to {act.rush}, but {parent.label_word} took hold and kept that bright shirt out of the dust.")
    world.para()
    gear = _compromise(world, parent, hero, act, prize)
    if gear is not None:
        hero.memes["joy"] += 1
        hero.memes["conflict"] = 0
        world.say(f"{hero.id} smiled wide, {hero.id} {gear.tail}, and the two of them watched the baker make the great {act.twist}.")
        world.say(f"At last, the baker gave the jam a tiny twist, and the mound became a sweet hill full of wonder.")
        world.say(f"{hero.id} kept {hero.pronoun('possessive')} {prize.label} clean and came away feeling tall as a tale.")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a tall-tale story for a young child about a mound, a slink, and an {act.twist}.',
        f"Tell a story where {hero.id} wants to {act.verb} but {parent.label_word} worries about {prize.phrase}.",
        f'Write a gentle tale that includes the words "{act.keyword}", "{act.gerund}", and "{act.twist}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do near the mound?",
            answer=f"{hero.id} wanted to {act.verb} near the mound at the bakery.",
        ),
        QAItem(
            question=f"Why was {parent.label_word} worried about {hero.id}'s {prize.label}?",
            answer=f"{parent.label_word} worried that the {prize.label} would get {act.soil} near the mound.",
        ),
        QAItem(
            question=f"What helped {hero.id} play without ruining the {prize.label}?",
            answer="An apron helped keep the shirt clean while the child stayed near the mound.",
        ),
    ]
    if f.get("gear"):
        qa.append(QAItem(
            question="What was the clever twist in the ending?",
            answer=f"The baker used an {act.twist} to fill the buns with jam, turning the mound into something sweet instead of messy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mound?", answer="A mound is a lump or hill of something piled up in one place."),
        QAItem(question="What does it mean to slink?", answer="To slink means to move quietly and sneakingly, like trying not to be noticed."),
        QAItem(question="What is an injection?", answer="An injection can mean putting a small amount of something into another thing with a tool or nozzle."),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
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


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(place="bakery", activity="mound", prize="shirt", name="Mabel", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bakery", activity="mound", prize="vest", name="Bram", gender="boy", parent="father", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
