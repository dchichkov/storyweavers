#!/usr/bin/env python3
"""
storyworlds/worlds/uncle_twist_humor_moral_value_rhyming_story.py
===================================================================

A small standalone story world about an uncle, a child, a funny twist, and a
moral-value turn told in a light rhyming-story style.

Source tale premise:
- A child wants to do a playful, messy activity.
- The uncle notices a treasured item is at risk.
- A humorous twist leads to a kind compromise.
- The ending proves the change: the child gets to play, the treasured item
  stays safe, and the moral lands gently.

The world model tracks:
- physical meters: mess, dirt, sparkle, readiness, cleanup
- emotional memes: delight, worry, tease, trust, pride, shame, gratitude

The prose is driven by state transitions rather than a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"painted", "muddy", "sticky", "splashy"}


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "dirty", "sparkle", "ready", "cleanup"]:
            self.meters.setdefault(k, 0.0)
        for k in ["delight", "worry", "tease", "trust", "pride", "shame", "gratitude"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    humor: str
    moral: str
    keyword: str = ""


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def activity_line(activity: Activity) -> str:
    return {
        "paint": "The paint was bright as jam, and it made the whole day hum.",
        "mud": "The mud went splat and pat, like a beat from a tap-tap drum.",
        "snack": "The snack smelled sweet and neat, and it made their tummies cheer.",
    }.get(activity.id, "The little game felt lively and bright, with laughter near.")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["delight"] += 1
    actor.memes["tease"] += 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        item.meters[activity.mess] += 1
        item.meters["dirty"] += 1
    if narrate:
        world.say(f"{actor.id} gave it a try, and the room rang with glee.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD}


def resolve_mess(world: World) -> None:
    for item in world.entities.values():
        if item.meters["dirty"] >= THRESHOLD and item.caretaker:
            carer = world.get(item.caretaker)
            carer.meters["cleanup"] += 1


def introduce(world: World, child: Entity, uncle: Entity, prize: Entity, activity: Activity) -> None:
    child.memes["trust"] += 1
    uncle.memes["pride"] += 1
    world.say(f"{child.id} was a bright little {child.type} with a grin that could start a song.")
    world.say(f"{child.id} loved to {activity.verb}, and {uncle.id} loved to make the day less long.")
    world.say(f"{uncle.id} had {prize.phrase}, kept safe and neat, the sort of thing that could not meet {activity.mess}.")


def warn(world: World, uncle: Entity, child: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, child, activity, prize.id)
    if not pred["soiled"]:
        return False
    uncle.memes["worry"] += 1
    world.say(f'"If you {activity.verb}, that {prize.label} might get {activity.soil}," said {uncle.id} with a wink and a smile.')
    return True


def joke(world: World, uncle: Entity, child: Entity, activity: Activity) -> None:
    uncle.memes["tease"] += 1
    world.say(f'"I am an uncle, not a pickle," {uncle.id} said. "I do not like a {activity.mess} trickle!"')
    world.say(f"{child.id} laughed at the rhyme, then tapped one toe; the tension got lighter, and the worry did go.")


def propose(world: World, uncle: Entity, child: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=child.id,
        caretaker=uncle.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = child.id
    if predict_mess(world, child, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{uncle.id} laughed, then said, "Let us use {gear_def.label} and keep the fun in view."')
    return gear


def accept(world: World, child: Entity, uncle: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    child.memes["trust"] += 1
    child.memes["delight"] += 1
    child.memes["shame"] = max(0.0, child.memes["shame"] - 1.0)
    uncle.memes["gratitude"] += 1
    world.say(f"{child.id} nodded quick, then smiled so wide it seemed to light the room.")
    world.say(
        f"They chose {gear_def.label}, and off they went with a hop and a shimmy and a cheerful zoom."
    )
    world.say(
        f"By the end, {child.id} was {activity.gerund}, {prize.label} stayed clean, and {uncle.id} had a grin that could beam."
    )


def moral_line(world: World, child: Entity, uncle: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"The moral was simple and easy to keep: ask first, use care, and the best play runs deep."
    )
    world.say(
        f"When you choose a kind fix, you can still have your fun, and the good little ending shines brighter than sun."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str = "Milo", child_type: str = "boy",
         uncle_name: str = "Uncle Pip") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, traits=["little", "curious"]))
    uncle = world.add(Entity(id=uncle_name, kind="character", type="uncle", traits=["funny", "kind"]))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=uncle.id,
        caretaker=uncle.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = uncle.id

    introduce(world, child, uncle, prize, activity)
    world.para()
    world.say(activity_line(activity))
    warn(world, uncle, child, activity, prize)
    joke(world, uncle, child, activity)
    gear_def = propose(world, uncle, child, activity, prize)
    world.para()
    if gear_def is None:
        raise StoryError("No reasonable compromise exists for this activity and prize.")
    accept(world, child, uncle, activity, prize, gear_def)
    moral_line(world, child, uncle, activity, prize)
    resolve_mess(world)

    world.facts.update(
        child=child,
        uncle=uncle,
        prize=prize,
        activity=activity,
        gear=gear_def,
        setting=setting,
        resolved=True,
        conflict=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"paint", "snack"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"paint", "mud"}),
    "porch": Setting(place="the porch", indoor=False, affords={"paint", "snack"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a big picture",
        gerund="painting bright stars",
        rush="dash for the paint pots",
        mess="painted",
        soil="painted and streaky",
        zone={"torso", "arms"},
        humor="He painted a silly line and gave his nose a grin.",
        moral="A good plan keeps the play kind and clean.",
        keyword="paint",
    ),
    "mud": Activity(
        id="mud",
        verb="play in the mud",
        gerund="splashing in the mud",
        rush="rush to the muddy patch",
        mess="muddy",
        soil="muddy and brown",
        zone={"feet", "legs"},
        humor="He stomped one boot so hard a worm seemed to laugh.",
        moral="It is wise to ask before a messy blast.",
        keyword="mud",
    ),
    "snack": Activity(
        id="snack",
        verb="make a sticky snack",
        gerund="stirring sweet treats",
        rush="reach for the sticky bowl",
        mess="sticky",
        soil="sticky with syrup",
        zone={"hands", "arms", "torso"},
        humor="The spoon wore more syrup than the cake wore a crown.",
        moral="Sharing and cleaning up make a happy ending.",
        keyword="snack",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a striped apron",
        covers={"torso", "arms"},
        guards={"painted", "sticky"},
        prep="put on a striped apron first",
        tail="slipped on the striped apron and came back ready",
    ),
    Gear(
        id="boots",
        label="mud boots",
        covers={"feet", "legs"},
        guards={"muddy"},
        prep="wear mud boots first",
        tail="pulled on the mud boots and stomped back",
        plural=True,
    ),
    Gear(
        id="smock",
        label="a little smock",
        covers={"torso", "arms"},
        guards={"painted", "sticky"},
        prep="tie on a little smock first",
        tail="tied on the little smock and skipped back",
    ),
]

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean blue shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a neat white apron", type="apron", region="torso"),
    "shoes": Prize(label="shoes", phrase="shiny little shoes", type="shoes", region="feet", plural=True),
    "hat": Prize(label="hat", phrase="a round yellow hat", type="hat", region="head"),
}

NAMES = ["Milo", "Nia", "Owen", "Zara", "Theo", "Luna", "Ivy", "Eli"]
UNCLE_NAMES = ["Uncle Pip", "Uncle Jo", "Uncle Sam", "Uncle Lou"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    child_name: str
    child_type: str
    uncle_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "paint": [("Why do people wear an apron when they paint?", "An apron helps keep paint off clothes so they stay cleaner.")],
    "mud": [("What does mud do to shoes?", "Mud sticks to shoes and makes them dirty, brown, and messy.")],
    "sticky": [("Why is syrup sticky?", "Syrup is thick and sweet, so it clings to spoons and fingers.")],
    "uncle": [("Who is an uncle?", "An uncle is a family member who is the brother of one of your parents, or married to one.")],
    "shirt": [("What is a shirt for?", "A shirt is clothing that covers the body and helps keep you comfy.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act: Activity = f["activity"]
    prize: Prize = f["prize"]
    child: Entity = f["child"]
    uncle: Entity = f["uncle"]
    return [
        f'Write a short rhyming story about {child.id} and {uncle.id} where the word "{act.keyword}" appears and a funny twist helps fix a mess.',
        f"Tell a gentle story in rhyme about an uncle who worries that a {prize.label} will get {act.soil} when a child wants to {act.verb}.",
        f"Write a child-friendly tale with humor, a moral, and a happy ending where {child.id} learns a safer way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    uncle: Entity = f["uncle"]
    prize: Entity = f["prize"]
    act: Activity = f["activity"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{child.id} wanted to {act.verb}, and {uncle.id} listened before making a kind plan.",
        ),
        QAItem(
            question=f"Why did {uncle.id} worry about the {prize.label}?",
            answer=f"{uncle.id} worried because {act.verb} could leave {prize.label} {act.soil}.",
        ),
        QAItem(
            question=f"What funny thing helped the child laugh before the compromise?",
            answer=f"{uncle.id} told a silly rhyme about the mess, and that made the worry feel smaller.",
        ),
        QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} covered the risky parts, so {child.id} could {act.verb} without ruining the {prize.label}.",
        ),
        QAItem(
            question="What moral did the ending teach?",
            answer="The story taught that asking first, using care, and choosing a safe fix can keep both fun and kindness in the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["activity"].keyword, world.facts["activity"].id, "uncle", world.facts["prize"].label}
    out: list[QAItem] = []
    for tag in ["uncle", "paint", "mud", "sticky", "shirt"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="paint", prize="shirt", child_name="Milo", child_type="boy", uncle_name="Uncle Pip"),
    StoryParams(place="backyard", activity="mud", prize="shoes", child_name="Luna", child_type="girl", uncle_name="Uncle Jo"),
    StoryParams(place="porch", activity="snack", prize="apron", child_name="Eli", child_type="boy", uncle_name="Uncle Lou"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, aid, pid))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the {prize.label} would stay safe.)"
    return f"(No story: there is no reasonable gear to protect the {prize.label} from {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(["boy", "girl"])
    uncle_name = args.uncle_name or rng.choice(UNCLE_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, child_name=child_name, child_type=child_type, uncle_name=uncle_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.child_name, params.child_type, params.uncle_name)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming uncle story world with humor, twist, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--uncle-name")
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            header = f"### {p.child_name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
