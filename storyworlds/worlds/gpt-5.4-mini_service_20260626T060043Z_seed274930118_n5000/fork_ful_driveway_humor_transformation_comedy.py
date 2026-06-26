#!/usr/bin/env python3
"""
storyworlds/worlds/forkful_driveway_comedy.py
==============================================

A small comedy storyworld set in a driveway, with a gentle transformation beat
and a fork-ful seed image.

Premise:
- A child wants to carry a fork-ful of something delicious or silly across the
  driveway.
- A careful parent worries about a clean prize item.
- A tiny accident turns into a funny transformation.
- The ending proves what changed in the world.

The domain is intentionally narrow so the generated stories stay complete and
grounded.
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
MESS_KINDS = {"sticky", "splashy", "smeary"}


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
            self.meters = {"sticky": 0.0, "splashy": 0.0, "smeary": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "surprise": 0.0, "humor": 0.0, "worry": 0.0, "pride": 0.0}

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
    place: str = "the driveway"
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
    keyword: str = "fork-ful"
    funny_twist: str = ""


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


SETTING = Setting(place="the driveway", affords={"spill", "paint", "sprinkle"})

ACTIVITIES = {
    "spill": Activity(
        id="spill",
        verb="carry the fork-ful across the driveway",
        gerund="carrying a fork-ful across the driveway",
        rush="dash to the chalk square",
        mess="sticky",
        soil="sticky and silly",
        zone={"hands", "torso"},
        funny_twist="the fork started to look bigger than the snack",
    ),
    "paint": Activity(
        id="paint",
        verb="decorate the driveway with a fork-ful of paint",
        gerund="painting with a fork-ful",
        rush="swirl the fork toward the puddle",
        mess="smeary",
        soil="smeary and bright",
        zone={"hands", "torso"},
        funny_twist="the driveway turned into a wiggly picture",
    ),
    "sprinkle": Activity(
        id="sprinkle",
        verb="sprinkle the fork-ful of crumbs for birds",
        gerund="sprinkling a fork-ful of crumbs",
        rush="toss the crumbs in a hurry",
        mess="splashy",
        soil="dusty and scattered",
        zone={"hands"},
        funny_twist="the birds arrived like tiny, hungry judges",
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "cap": Prize(label="cap", phrase="a bright blue cap", type="cap", region="head"),
    "sneakers": Prize(label="sneakers", phrase="new red sneakers", type="sneakers", region="feet", plural=True),
    "jacket": Prize(label="jacket", phrase="a neat yellow jacket", type="jacket", region="torso"),
}

GEAR = [
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"sticky", "smeary"},
        prep="put on an apron first",
        tail="went back inside to fetch the apron",
    ),
    Gear(
        id="cap-cover",
        label="a cap with a brim",
        covers={"head"},
        guards={"splashy"},
        prep="put on a cap with a brim first",
        tail="came back wearing the cap with a brim",
    ),
    Gear(
        id="old-clothes",
        label="old play clothes",
        covers={"torso", "hands"},
        guards={"sticky", "smeary", "splashy"},
        prep="change into old play clothes",
        tail="returned in old play clothes",
        plural=True,
    ),
]

NAMES = ["Mina", "Leo", "June", "Toby", "Nora", "Pip", "Maya", "Ben"]
TRAITS = ["funny", "curious", "cheerful", "silly", "playful", "bouncy"]


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


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_dirty(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("dirty", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                actor.memes["humor"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


RULES = [Rule("dirty", _r_dirty), Rule("worry", _r_worry)]


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


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        **e.__dict__,
        "meters": dict(e.meters),
        "memes": dict(e.memes),
        "covers": set(e.covers),
    }) for k, e in world.entities.items()}
    sim.zone = set(world.zone)
    sim.fired = set(world.fired)
    sim_actor = sim.get(actor.id)
    sim_actor.meters[activity.mess] += 1
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.pronoun('possessive')} {hero.type} who loved jokes and surprises.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, and {hero.pronoun('possessive')} {parent.type} "
        f"had just handed over {prize.phrase}."
    )
    world.say(f"It looked so tidy that even the driveway seemed to be waiting for a laugh.")


def arrival(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say(f"{hero.id} saw a small {activity.keyword} idea and grinned at the silly plan.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["humor"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but the fork-ful looked wobbly in {hero.pronoun('possessive')} hands.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"Careful," {parent.pronoun("possessive")} {parent.type} said. '
        f'"That fork-ful could make your {prize.label} {activity.soil}."'
    )
    return True


def wobble(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] += 1
    hero.memes["surprise"] += 1
    world.say(f"{hero.id} tried to {activity.rush}, but the fork-ful wobbled like a tiny see-saw.")


def funny_turn(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["humor"] += 1
    world.say(f"Then the {activity.keyword} made a funny mess, and {activity.funny_twist}.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.pronoun("possessive").capitalize()} {parent.type} smiled. '
        f'"How about we {gear_def.prep} and try again?"'
    )
    return gear_def


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} laughed, because the plan sounded as funny as the mess.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed clean."
    )
    world.say(
        f"The driveway even looked transformed: one side was neat, and the other side had a goofy little {activity.keyword} pattern."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
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

    introduce(world, hero)
    setup(world, hero, parent, prize, activity)
    world.para()
    arrival(world, hero, parent, activity)
    wants(world, hero, activity)
    if warn(world, parent, hero, activity, prize):
        wobble(world, hero, activity)
        funny_turn(world, hero, activity)
    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        resolve(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"driveway": SETTING}.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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
    "fork-ful": [
        (
            "What is a fork-ful?",
            "A fork-ful is the amount of food or stuff that fits on a fork at one time."
        )
    ],
    "sticky": [
        (
            "Why is sticky stuff funny sometimes?",
            "Sticky stuff can make a silly mess, and people often laugh when it clings to fingers, shoes, or clothes."
        )
    ],
    "apron": [
        (
            "What is an apron for?",
            "An apron helps keep clothes clean while cooking, painting, or making a mess."
        )
    ],
    "driveway": [
        (
            "What is a driveway?",
            "A driveway is the path where cars can drive up to a house."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    prize = f["prize"]
    hero = f["hero"]
    return [
        f'Write a short comedy story for a young child that includes the phrase "fork-ful" and takes place in the driveway.',
        f"Tell a funny story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {prize.label} might get messy.",
        f'Write a gentle transformation story about a driveway, a fork-ful, and a clean item that stays safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to carry in the driveway?",
            answer=f"{hero.id} wanted to carry a fork-ful across the driveway."
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the {prize.label}?",
            answer=f"{parent.label} warned {hero.id} because the fork-ful could make the {prize.label} {act.soil}."
        ),
        QAItem(
            question=f"What happened to the driveway in the end?",
            answer=f"The driveway got transformed into a funny, messy little scene, but the clean item stayed safe."
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"What helped {hero.id} keep the {prize.label} clean?",
                answer=f"{gear.label} helped {hero.id} finish the job without ruining the {prize.label}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"fork-ful", "driveway"}
    if world.facts["activity"].mess == "sticky":
        tags.add("sticky")
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid_story("driveway",A,P) :- affords("driveway",A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "driveway"))
    for a in sorted(SETTING.affords):
        lines.append(asp.fact("affords", "driveway", a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [("driveway", a, p) for (_, a, p) in asp_valid_stories()]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy driveway storyworld with a fork-ful and a small transformation.")
    ap.add_argument("--place", choices=["driveway"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put the {prize.label} at risk.)"
    return f"(No story: there is no suitable fix for a {prize.label} during {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="driveway",
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="driveway", activity="spill", prize="shirt", name="Mina", gender="girl", parent="mother", trait="funny"),
    StoryParams(place="driveway", activity="paint", prize="jacket", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="driveway", activity="sprinkle", prize="cap", name="June", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible driveway stories:\n")
        for _, act, prize in stories:
            print(f"  driveway  {act:10} {prize}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} with a fork-ful in the driveway"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
