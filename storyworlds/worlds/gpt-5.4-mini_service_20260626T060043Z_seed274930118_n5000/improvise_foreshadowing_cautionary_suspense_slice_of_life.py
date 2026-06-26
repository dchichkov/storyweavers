#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/improvise_foreshadowing_cautionary_suspense_slice_of_life.py
====================================================================================================

A small slice-of-life story world about improvising a little performance at home.

Premise:
- A child wants to improvise something cheerful in an ordinary room.
- A parent notices a fragile object nearby and gives a cautionary warning.
- The child feels suspense, then finds a safer way to keep the fun going.

The world is intentionally modest: one household scene, a few typed entities,
stateful physical and emotional meters, and a single causal turn that resolves
cleanly.
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
REGIONS = {"floor", "table", "shelf"}
MESS_KINDS = {"wobble", "spill", "scuff"}


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
        for k in ["wobble", "spill", "scuff", "fragile", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "suspense", "caution", "relief", "care", "resolve"]:
            self.memes.setdefault(k, 0.0)

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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.kind == "thing" and item.region in world.zone and not item.protective:
                    sig = ("mess", actor.id, item.id, mess)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters[mess] += 1
                    if mess == "wobble":
                        item.meters["fragile"] += 1
                    out.append(f"{item.label.capitalize()} looked less steady.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["caution"] < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append("A careful warning hung in the air.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_mess, _r_worry):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "wobbled": prize.meters["fragile"] >= THRESHOLD or prize.meters["wobble"] >= THRESHOLD,
        "stress": sum(e.memes["worry"] + e.memes["suspense"] for e in sim.characters()),
    }


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked making ordinary afternoons feel special.")


def loves_improvise(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to improvise, especially {activity.gerund}, "
        f"because small ideas could turn into a whole game."
    )


def scene_setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} noticed {hero.pronoun('possessive')} {prize.label} near the action, "
        f"and that made the plan feel a little more exciting."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.id.lower()} gave a glance toward the {prize.label} and the open floor."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the room already held one fragile thing to think about."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_risk(world, hero, activity, prize.id)
    if not pred["wobbled"]:
        return False
    parent.memes["caution"] += 1
    world.facts["predicted_stress"] = pred["stress"]
    world.say(
        f'"Easy," {parent.id.lower()} said. "If you start {activity.gerund}, {prize.label} could wobble."'
    )
    return True


def suspense(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"{hero.id} paused for a moment, listening to the tiny hush after the warning."
    )
    world.say(
        f"Then {hero.pronoun().capitalize()} took a breath and tried to {activity.rush}."
    )


def improvise_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_risk(world, hero, activity, prize.id)["wobbled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{parent.id.lower()} smiled and said, "
        f"\"Let's improvise safely. We can use {gear_def.label} first.\""
    )
    return gear_def


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["suspense"] = 0.0
    world.say(
        f"{hero.id} nodded, and the tense little pause turned into a plan."
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"the room stayed calm, and {prize.label} stayed steady."
    )
    world.say(
        f"It ended as a small, happy home moment: nothing grand, just a safe bit of music and a clean, warm room."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "gentle"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    loves_improvise(world, hero, activity)
    scene_setup(world, hero, parent, prize, activity)

    world.para()
    warn(world, parent, hero, activity, prize)
    suspense(world, hero, activity)

    world.para()
    gear_def = improvise_fix(world, parent, hero, activity, prize)
    if gear_def:
        resolve(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "living_room": Setting(place="the living room", affords={"dance", "show"}),
    "kitchen": Setting(place="the kitchen", affords={"dance", "show"}),
    "hallway": Setting(place="the hallway", affords={"dance"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="improvise a little dance",
        gerund="improvising a little dance",
        rush="step onto the open floor",
        mess="wobble",
        soil="a bit shaky",
        zone={"floor"},
        keyword="improvise",
        tags={"improvise", "music", "dance"},
    ),
    "show": Activity(
        id="show",
        verb="improvise a tiny show",
        gerund="improvising a tiny show",
        rush="set up a tiny stage",
        mess="scuff",
        soil="scuffed",
        zone={"floor", "table"},
        keyword="improvise",
        tags={"improvise", "show", "stage"},
    ),
}

PRIZES = {
    "lamp": Prize(
        label="lamp",
        phrase="a small glass lamp",
        type="lamp",
        region="floor",
    ),
    "vase": Prize(
        label="vase",
        phrase="a narrow vase",
        type="vase",
        region="table",
    ),
    "stack": Prize(
        label="stack of books",
        phrase="a neat stack of books",
        type="books",
        region="table",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="rug",
        label="the soft rug",
        covers={"floor"},
        guards={"wobble", "scuff"},
        prep="slide the rug into the middle",
        tail="slid the rug into the middle",
    ),
    Gear(
        id="tray",
        label="the serving tray",
        covers={"table"},
        guards={"scuff"},
        prep="move the fragile things onto the serving tray",
        tail="moved the fragile things onto the serving tray",
    ),
]

GIRL_NAMES = ["Mina", "Nora", "Tia", "Lena", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Milo", "Jonah"]
TRAITS = ["playful", "curious", "patient", "thoughtful", "cheerful"]


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


KNOWLEDGE = {
    "improvise": [
        ("What does it mean to improvise?",
         "To improvise means to make something up as you go, using the things and ideas you have right then."),
    ],
    "music": [
        ("What is a rhythm?",
         "A rhythm is a pattern of beats that you can clap, tap, or dance to."),
    ],
    "dance": [
        ("Why do people dance?",
         "People dance to enjoy music, move their bodies, and have fun."),
    ],
    "glass": [
        ("Why should glass things be handled carefully?",
         "Glass can break if it is bumped or dropped, so people often handle it gently."),
    ],
    "rug": [
        ("What does a rug do on the floor?",
         "A rug makes the floor softer to stand on and can help keep footsteps from slipping."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a child who wants to improvise, using the word "{act.keyword}".',
        f"Tell a gentle home story where {hero.id} wants to {act.verb}, but {parent.label} worries about the {prize.label}.",
        f"Write a small suspenseful-but-kind story about a child, a fragile object, and a safe way to keep playing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.pronoun('subject').capitalize()} loved improvising small things at home.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the {prize.label}?",
            answer=f"{parent.label} warned {hero.id} because the {prize.label} was fragile and could wobble if {hero.id} started {act.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the warning?",
            answer=f"{hero.id} paused, felt a little suspense, and then kept going in a safer way once the room was ready.",
        ),
        QAItem(
            question=f"What helped make the ending safer?",
            answer=f"The soft rug helped because it made the floor safer for {hero.id} to keep {act.gerund}.",
        ),
    ]
    if f.get("gear"):
        qa.append(QAItem(
            question=f"How did the {f['gear'].label} help?",
            answer=f"The {f['gear'].label} gave {hero.id} a safer setup, so the fun could continue without troubling the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="living_room", activity="dance", prize="lamp", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="kitchen", activity="show", prize="vase", name="Owen", gender="boy", parent="father", trait="playful"),
    StoryParams(place="living_room", activity="show", prize="stack", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach {noun} in a way that would make the parent honestly worry.)"
    return f"(No story: there is no safe fix for {noun} in this setup.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't pinned to {gender} here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a child improvises, a parent cautions, and the room stays safe.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for place, act, prize in triples:
            print(f"  {place:12} {act:8} {prize}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
