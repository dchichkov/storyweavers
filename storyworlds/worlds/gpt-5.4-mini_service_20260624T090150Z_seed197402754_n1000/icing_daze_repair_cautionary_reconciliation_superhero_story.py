#!/usr/bin/env python3
"""
storyworlds/worlds/icing_daze_repair_cautionary_reconciliation_superhero_story.py
=================================================================================

A small superhero-style story world about caution, a surprising daze, and a
repair that ends in reconciliation.

Seed tale:
---
Once upon a time, a young superhero loved helping at the city bake hall.
One afternoon, they carried a cake with bright icing up a tall stairway to
the rooftop celebration. Their mentor warned them to move slowly because the
icing was slippery and the cake box could tip.

The hero hurried anyway. The box wobbled, the icing smudged across the cape,
and the sudden splash left the hero dazed for a moment. The celebration
stopped. The mentor showed the hero how to repair the frosting with a small
spatula and how to steady the box with both hands.

After the repair, the hero apologized. The mentor smiled, and they carried the
cake together. The rooftop lights shone on the fixed icing, and the hero felt
proud to have learned a safer way.

Story instruments:
---
- Cautionary: a warning about a risky action, with a foreseeable mess.
- Reconciliation: after the mistake, a repair and apology restore trust.
- Superhero Story style: capes, rooftop flights, helper mentor, bright rescue
  energy, but grounded in a small, child-facing problem.
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
METER_KEYS = {"messy", "broken", "tired", "steady"}
MEME_KEYS = {"joy", "worry", "caution", "daze", "shame", "repair_pride", "trust"}


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METER_KEYS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEME_KEYS})

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
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    risk_zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairGear:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.activity: Optional[Activity] = None
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.activity = copy.deepcopy(self.activity)
        return w


def _warnable(activity: Activity) -> bool:
    return "cautionary" in activity.tags or activity.mess == "messy"


def risk_hits_prize(activity: Activity, prize: Entity) -> bool:
    return prize.id in {"cape", "cake", "mask"} and "torso" in activity.risk_zone


def select_repair(activity: Activity, prize: Entity) -> Optional[RepairGear]:
    for gear in REPAIR_GEAR:
        if activity.mess in gear.helps:
            return gear
    return None


def predict_daze(world: World, hero: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return {
        "messy": sim.get(prize.id).meters["messy"] >= THRESHOLD,
        "daze": sim.get(hero.id).memes["daze"] >= THRESHOLD,
    }


def _do_activity(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.activity = activity
    hero.meters[activity.mess] += 1
    hero.memes["joy"] += 1
    if narrate:
        world.say(f"{hero.id} {activity.gerund}.")


def _soak_gear(world: World) -> list[str]:
    out: list[str] = []
    act = world.activity
    if not act:
        return out
    for hero in world.chars():
        if hero.meters[act.mess] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != hero.id:
                continue
            sig = ("soak", hero.id, item.id, act.mess)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if item.protective:
                continue
            item.meters["messy"] += 1
            item.meters["broken"] += 1
            out.append(f"{hero.pronoun('possessive').capitalize()} {item.label} got smeared.")
    return out


def _daze_rule(world: World) -> list[str]:
    out: list[str] = []
    act = world.activity
    if not act:
        return out
    for hero in world.chars():
        if hero.meters[act.mess] < THRESHOLD or hero.memes["caution"] >= THRESHOLD:
            continue
        sig = ("daze", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["daze"] += 1
        out.append(f"{hero.id} looked dazed for a moment.")
    return out


CAUSAL_RULES = [_soak_gear, _daze_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} glittered with bright windows and a rooftop ladder."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little superhero who loved helping people at {world.setting.place}.")


def setup_activity(world: World, hero: Entity, mentor: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} loved {activity.gerund} and especially loved the shiny {prize.label}."
    )
    world.say(
        f"{mentor.id} showed {hero.pronoun('object')} the {prize.label} and said it was for the rooftop celebration."
    )


def caution(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["caution"] += 1
    world.say(
        f"{mentor.id} lifted a hand and warned, \"Slow steps, please. The {activity.keyword} can slip and smear the {prize.label}.\""
    )
    world.say(setting_detail(world.setting))


def rush(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"But {hero.id} wanted to go faster, so {hero.pronoun()} tried to {activity.rush}."
    )


def spill_and_daze(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] += 1
    prize.meters["messy"] += 1
    hero.memes["daze"] += 1
    propagate(world, narrate=True)
    world.say(
        f"The {activity.keyword} splashed across {hero.pronoun('possessive')} cape and left {hero.id} dazed."
    )


def repair(world: World, mentor: Entity, hero: Entity, prize: Entity, gear: RepairGear) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{mentor.id} came close, spoke gently, and said, \"We can repair this together.\""
    )
    world.say(
        f"They used the {gear.label} to fix the {prize.label}, and {gear.tail}."
    )
    prize.meters["broken"] = 0.0
    prize.meters["messy"] = 0.0
    hero.memes["repair_pride"] += 1
    hero.memes["trust"] += 1
    hero.memes["daze"] = 0.0


def reconcile(world: World, mentor: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["shame"] = max(0.0, hero.memes["shame"] - 1.0)
    world.say(
        f"{hero.id} apologized, and {mentor.id} smiled. They carried the {prize.label} together again."
    )
    world.say(
        f"At the end, the fixed icing shone like a tiny superhero badge in the light."
    )


def tell(setting: Setting, activity: Activity, hero_name: str = "Nova") -> World:
    world = World(setting)
    world.activity = activity
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    mentor = world.add(Entity(id="Mentor", kind="character", type="woman", label="the mentor"))
    prize = world.add(Entity(id="cake", type="cake", label="cake", phrase="a cake with bright icing", caretaker=mentor.id))
    cape = world.add(Entity(id="cape", type="cape", label="cape", caretaker=mentor.id))
    world.add(cape)
    cape.worn_by = hero.id

    introduce(world, hero)
    setup_activity(world, hero, mentor, prize, activity)
    world.para()
    caution(world, mentor, hero, activity, prize)
    rush(world, hero, activity)
    spill_and_daze(world, hero, prize, activity)
    world.para()
    gear = select_repair(activity, prize)
    if gear is None:
        raise StoryError("No repair gear fits this story.")
    repair(world, mentor, hero, prize, gear)
    reconcile(world, mentor, hero, prize)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, cape=cape, activity=activity, gear=gear)
    return world


SETTINGS = {
    "bake_hall": Setting(place="the city bake hall", affords={"icing"}),
    "rooftop": Setting(place="the rooftop celebration", affords={"icing"}),
    "kitchen": Setting(place="the rescue kitchen", affords={"icing"}),
}

ACTIVITIES = {
    "icing": Activity(
        id="icing",
        verb="spread the icing",
        gerund="spreading the icing",
        rush="dash up the stairs with the frosting tray",
        mess="messy",
        soil="smeared with icing",
        keyword="icing",
        risk_zone={"torso"},
        tags={"cautionary", "reconciliation", "superhero"},
    ),
    "daze": Activity(
        id="daze",
        verb="hurry the job",
        gerund="hurrying too fast",
        rush="race ahead without watching the tray",
        mess="messy",
        soil="smudged and dazed",
        keyword="daze",
        risk_zone={"torso"},
        tags={"cautionary", "reconciliation", "superhero"},
    ),
    "repair": Activity(
        id="repair",
        verb="repair the icing",
        gerund="carefully repairing the icing",
        rush="rush into a quick fix",
        mess="messy",
        soil="neatly repaired",
        keyword="repair",
        risk_zone={"torso"},
        tags={"cautionary", "reconciliation", "superhero"},
    ),
}

REPAIR_GEAR = [
    RepairGear(
        id="spatula",
        label="small spatula",
        helps={"messy"},
        prep="use a small spatula",
        tail="the icing was smooth again",
    ),
    RepairGear(
        id="cloth",
        label="clean cloth",
        helps={"messy"},
        prep="wipe carefully with a clean cloth",
        tail="the cape looked neat once more",
    ),
]

HERO_NAMES = ["Nova", "Mira", "Zane", "Ari", "Pip", "Luna", "Tess"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about icing, daze, and repair.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            combos.append((sid, aid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if not combos:
        raise StoryError("No valid setting/activity combination matches the options.")
    setting, activity = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(setting=setting, activity=activity, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "{f["activity"].keyword}".',
        f"Tell a gentle cautionary story where {f['hero'].id} wants to {f['activity'].verb} but must slow down to protect the cake.",
        "Write a story about a superhero who makes a mistake, then repairs it and makes up with a helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a little hero who wants to help at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {mentor.id} warn {hero.id} about?",
            answer=f"{mentor.id} warned {hero.id} that the {act.keyword} could slip and smear the {prize.label}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} rushed ahead?",
            answer=f"The {act.keyword} splashed across the cape, {hero.id} looked dazed, and the cake got messy.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used the {gear.label} to repair the {prize.label}, then {hero.id} apologized and they carried it together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is icing?",
            answer="Icing is a sweet, soft topping spread on cakes and cupcakes to make them look and taste special.",
        ),
        QAItem(
            question="What does dazed mean?",
            answer="If someone is dazed, they feel mixed up or stunned for a moment, as if their head needs a second to catch up.",
        ),
        QAItem(
            question="What is repair?",
            answer="Repair means fixing something that is damaged so it can work or look good again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(S, A) :- setting(S), affords(S, A), activity(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for aid in SETTINGS[sid].affords:
            lines.append(asp.fact("affords", sid, aid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], params.name)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(setting=s, activity=a, name="Nova")) for s, a in valid_combos()]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
