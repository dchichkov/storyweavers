#!/usr/bin/env python3
"""
A small comedy storyworld about an ointment jar, garden soil, and a surprising stone.

Seed image:
- A child has a sore spot and a tiny jar of ointment.
- The child also wants to play in the soil and collect stones.
- A careful parent worries that the ointment will get dirty.
- A surprise stone changes the plan, and the ending lands in a light, silly way.

The world is intentionally tiny, constraint-checked, and state-driven.
"""

from __future__ import annotations

import argparse
import dataclasses
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0, "soiled": 0.0, "stuck": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "surprise": 0.0, "amusement": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
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


@dataclass
class SurpriseItem:
    id: str
    label: str
    reveal: str
    helps: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.world_notes: list[str] = []

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
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("soil", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["soiled"] += 1
            out.append(f"{actor.label_word.capitalize()}'s {item.label_word} got dusty and a little grubby.")
    return out


def _r_ointment_smear(world: World) -> list[str]:
    out: list[str] = []
    oint = world.entities.get("ointment")
    if not oint:
        return out
    if oint.worn_by and oint.meters.get("soiled", 0.0) >= THRESHOLD:
        sig = ("smear", oint.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get(oint.worn_by).memes["worry"] += 1
            out.append("That made the ointment look less like medicine and more like a pastry mistake.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("stone_revealed") and ("surprise",) not in world.fired:
        world.fired.add(("surprise",))
        actor = world.facts["hero"]
        actor.memes["surprise"] += 1
        actor.memes["amusement"] += 1
        out.append("The stone turned out to be hiding something silly.")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_ointment_smear,
    _r_surprise,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("soiled", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.label_word.capitalize()} was a little {hero.type} who loved curious little discoveries.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, especially when the day felt like a joke waiting to happen.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {parent.label_word} bought {hero.pronoun('object')} {prize.phrase} for the sore spot on {hero.pronoun('possessive')} arm.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One afternoon, {hero.label_word} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}.")
    world.say(f"The ground was ready for {activity.keyword}, and the air felt like a funny surprise might pop out next.")


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["worry"] += 0.25
    world.say(f"{hero.label_word} wanted to {activity.verb}, but {hero.pronoun('possessive')} {prize.label} was still sitting nearby like a tiny bossy cloud.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.label_word} said.')
    world.say('"' + "And then we'll both be doing laundry, which is nobody's favorite hobby." + '"')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["amusement"] += 0.5
    world.say(f"{hero.label_word} tried to {activity.rush}, because the adventure sounded too funny to skip.")


def reveal_surprise(world: World, hero: Entity, surprise: SurpriseItem) -> None:
    world.facts["stone_revealed"] = True
    hero.memes["surprise"] += 1
    world.say(f"Then {hero.label_word} found {surprise.reveal}.")


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"{parent.label_word} smiled and handed over {gear.label}.")
    world.say(f'"How about we {gear.prep} and still {activity.verb}?" {parent.label_word} asked.')
    world.say(f"{hero.label_word} grinned, and soon {hero.pronoun('subject')} was {activity.gerund} while {prize.label} stayed clean.")
    world.say(f"They {gear.tail}, and the stone surprise made the whole plan feel extra silly.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(id="ointment", type="ointment", label="ointment", phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region))
    hero.meters["clean"] = 1.0
    prize.worn_by = hero.id

    introduce(world, hero)
    loves(world, hero, activity)
    buys(world, parent, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    surprise = SURPRISES["stone"]
    reveal_surprise(world, hero, surprise)
    gear = select_gear(activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, surprise=surprise)
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"soil"}),
    "backyard": Setting(place="the backyard", indoors=False, affords={"soil"}),
    "potting_bench": Setting(place="the potting bench", indoors=False, affords={"soil"}),
}

ACTIVITIES = {
    "soil": Activity(
        id="soil",
        verb="dig in the soil",
        gerund="digging in the soil",
        rush="dash into the soil patch",
        mess="soil",
        soil="all smeared with soil",
        zone={"hands", "arms"},
        keyword="soil",
        tags={"soil", "garden"},
    )
}

PRIZES = {
    "ointment": Prize(
        label="ointment",
        phrase="a little jar of cooling ointment",
        type="ointment",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="gloves",
        label="garden gloves",
        covers={"hands"},
        guards={"soil"},
        prep="put on the garden gloves first",
        tail="walked back to the bench for the gloves",
        plural=True,
    )
]

SURPRISES = {
    "stone": SurpriseItem(
        id="stone",
        label="stone",
        reveal="a stone with a silly face painted on it, tucked under the soil like it was trying very hard not to laugh",
        helps=True,
    )
}

TRAITS = ["curious", "cheerful", "silly", "spirited"]
GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Leo"]


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
    "ointment": [
        QAItem(question="What is ointment?", answer="Ointment is a soft medicine you spread on skin to help it feel better."),
    ],
    "soil": [
        QAItem(question="What is soil?", answer="Soil is the loose brown stuff on the ground where plants can grow."),
    ],
    "stone": [
        QAItem(question="What is a stone?", answer="A stone is a hard piece of rock, and some stones are small enough to fit in a child's hand."),
    ],
    "garden": [
        QAItem(question="Why do people wear gloves in a garden?", answer="People wear gloves in a garden to keep their hands cleaner and help protect them from dirt."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy story for a young child about {hero.label_word}, {prize.label}, and a surprise stone in the {act.keyword}.',
        f"Tell a funny story where {hero.label_word} wants to {act.verb} but {parent.label_word} worries about {prize.phrase}.",
        f'Write a gentle humorous story set in {world.setting.place} that uses the words "ointment", "soil", and "stone".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.label_word} want to do in {world.setting.place}?",
            answer=f"{hero.label_word} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} warn {hero.label_word} about the {prize.label}?",
            answer=f"{parent.label_word} warned {hero.label_word} because the {prize.label} would get {act.soil} if {hero.label_word} kept playing in the soil.",
        ),
        QAItem(
            question="What surprise did the child find?",
            answer="The child found a stone with a silly painted face hiding under the soil.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the {gear.label} help?",
                answer=f"The {gear.label} covered {act.zone.pop() if len(act.zone)==1 else 'the hands'} so {hero.label_word} could play without dirtying the ointment.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["ointment", "soil", "stone", "garden"]:
        out.extend(KNOWLEDGE.get(key, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R), splashes(A, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
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
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy world about ointment, soil, and a surprise stone.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations available.")
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.activity is None or c[1] == args.activity) and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combinations:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(place=p, activity=a, prize=pr, name="Mina", gender="girl", parent="mother", trait="curious") for p, a, pr in valid_combos()]:
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
