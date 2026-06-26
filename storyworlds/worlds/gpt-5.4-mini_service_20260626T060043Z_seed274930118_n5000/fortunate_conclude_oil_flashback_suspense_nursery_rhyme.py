#!/usr/bin/env python3
"""
A tiny storyworld in nursery-rhyme style: a child, a little oil trouble, a
flashback to a helpful lesson, a suspenseful pause, and a fortunate ending.

The seed words are folded into the world model and narration:
- fortunate
- conclude
- oil

The story beats:
- setup: a child loves a small task
- flashback: a remembered lesson about oil
- suspense: a risky moment and a pause
- resolution: a careful choice and a fortunate conclude
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False


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


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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


THRESHOLD = 1.0
MESS_KINDS = {"oil", "wet"}


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("oil", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["oil"] = item.meters.get("oil", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got oily and dirty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["work"] = caretaker.memes.get("work", 0.0) + 1
        out.append(f"That would mean more work for {caretaker.label}.")
    return out


CAUSAL_RULES = [(_r_soil), (_r_worry)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting("the kitchen", indoors=True),
    "workbench": Setting("the workbench corner", indoors=True),
    "yard": Setting("the little yard", indoors=False),
}

ACTIVITIES = {
    "fix_wheel": Activity(
        id="fix_wheel",
        verb="fix the squeaky wheel",
        gerund="fixing the squeaky wheel",
        rush="run to the bike",
        mess="oil",
        soil="oily and dirty",
        zone={"hands", "torso"},
        keyword="oil",
        tags={"oil", "tool"},
    ),
    "polish_lamp": Activity(
        id="polish_lamp",
        verb="polish the lamp",
        gerund="polishing the lamp",
        rush="reach for the lamp",
        mess="oil",
        soil="slick with oil",
        zone={"hands"},
        keyword="oil",
        tags={"oil", "light"},
    ),
    "grease_gate": Activity(
        id="grease_gate",
        verb="grease the gate hinge",
        gerund="greasing the gate hinge",
        rush="hurry to the gate",
        mess="oil",
        soil="smudged with oil",
        zone={"hands", "torso"},
        keyword="oil",
        tags={"oil", "metal"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean little shirt", "shirt", "torso"),
    "apron": Prize("apron", "a bright apron", "apron", "torso"),
    "mittens": Prize("mittens", "warm mittens", "mittens", "hands", plural=True),
}

GEAR = [
    Gear(
        id="old_apron",
        label="an old apron",
        covers={"torso"},
        guards={"oil"},
        prep="put on the old apron first",
        tail="went to fetch the old apron",
    ),
    Gear(
        id="work_gloves",
        label="work gloves",
        covers={"hands"},
        guards={"oil"},
        prep="pull on the work gloves first",
        tail="came back with the work gloves",
        plural=True,
    ),
]

GIRL_NAMES = ["Ada", "Mina", "Lila", "Nora", "Pia"]
BOY_NAMES = ["Ben", "Finn", "Toby", "Leo", "Sam"]
TRAITS = ["cheery", "curious", "gentle", "spry", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting, s in SETTINGS.items():
        for act_id in ACTIVITIES:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and any(prize.region in g.covers and act.mess in g.guards for g in GEAR):
                    combos.append((setting, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not put {prize.label} at honest risk, "
        f"or the world has no sensible gear for that pair.)"
    )


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_soil(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["oil"] = 1
    for item in sim.worn_items(sim.get(actor.id)):
        if item.protective or item.region not in sim.zone:
            continue
        if not sim.covered(sim.get(actor.id), item.region):
            return True
    return False


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.memes if False) if False else hero.type} who loved bright little chores.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero_trait = (hero_traits or ["bright"])[0]
    world.say(f"{hero.id} was a little {hero_trait} {hero.type} who liked to help and hum.")
    world.say(f"On a day in {setting.place}, {hero.id} wore {prize.phrase} and smiled so sunny and sweet.")
    world.say(f"{hero.id} loved to {activity.verb}, for the work felt tidy and neat.")

    world.para()
    world.say(f"Then came a flashback, soft as a chime: once, {parent.label} had said,")
    world.say(f'"A drop of oil can slip and slide, so keep your little hands ahead."')
    world.say(f"{hero.id} remembered that lesson and nodded slow, as if hearing a tune long ago.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} wanted to {activity.verb}, but the old oil can tipped and swayed.")
    world.say(f"One splash could smudge {prize.it()} at once, and the room grew still in the shade.")
    world.say(f"Suspense hung close like a spider's thread; {hero.id} held very still.")
    world.say(f"{parent.label.capitalize()} asked, 'Will you choose the careful way?' and waited with patient will.")

    if predict_soil(world, hero, activity, prize.id):
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError(explain_rejection(activity, prize))
        if gear.label.startswith("an "):
            gear_label = gear.label
        else:
            gear_label = gear.label
        world.say(f"Then {parent.label} said, 'Let's {gear.prep}.'")
        gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True,
                                    owner=hero.id, caretaker=parent.id, plural=gear.plural,
                                    worn_by=hero.id))
        hero.meters["oil"] = 1
        world.zone = set(activity.zone)
        world.say(f"So they {gear.tail}, and {hero.id} could still {activity.verb}.")
        world.say(f"The tricky oil stayed off {prize.it()}, and the little day went gentle again.")
        world.say(f"In the end, the story came to a fortunate conclude: {hero.id} finished the chore with a grin.")
        world.say(f"{parent.label.capitalize()} laughed, and {hero.id} was merry, with a clean {prize.label} shining bright within.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_ent, setting=setting)
        return world

    raise StoryError(explain_rejection(activity, prize))


KNOWLEDGE = {
    "oil": [
        ("What is oil?", "Oil is a slippery liquid that can help things move smoothly, but it can also make a floor or cloth messy."),
        ("Why do people use oil on moving parts?", "People use oil on moving parts because it helps them slide more easily and makes squeaks quieter."),
    ],
    "tool": [
        ("What is a tool?", "A tool is something people use to help them do work, like turning, fixing, or building."),
    ],
    "light": [
        ("Why can a lamp be useful?", "A lamp can make a dark place bright enough to see small details."),
    ],
    "metal": [
        ("What is metal?", "Metal is a hard material that can be strong and shiny, and it is often used for hinges and wheels."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short nursery-rhyme style story with the word "{activity.keyword}" and a soft flashback.',
        f"Tell a suspenseful little tale about {hero.id} who wants to {activity.verb} without making {prize.label} messy.",
        "Make the ending fortunate, and let the child conclude the problem with a careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the little one in the story?",
            answer=f"It was {hero.id}, a little {hero.type} who liked helpful chores and bright little rhymes.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}, but {parent.label} worried that oil might make {prize.label} messy.",
        ),
        QAItem(
            question=f"What helped the story end well?",
            answer=f"{gear.label} helped keep the oil off {prize.label}, so the story could conclude in a fortunate way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", activity="fix_wheel", prize="shirt", name="Mina", gender="girl", parent="mother", trait="cheery"),
    StoryParams(setting="workbench", activity="polish_lamp", prize="mittens", name="Ben", gender="boy", parent="father", trait="curious"),
    StoryParams(setting="yard", activity="grease_gate", prize="apron", name="Ada", gender="girl", parent="mother", trait="gentle"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Setting,A,P) :- affords(Setting,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in ACTIVITIES:
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
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple[str, str, str]]:
    res = []
    for setting, act_id, prize_id in valid_combos():
        res.append((setting, act_id, prize_id))
    return sorted(res)


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - asp_set))
    print("clingo only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about oil, flashback, and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(vals)
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
