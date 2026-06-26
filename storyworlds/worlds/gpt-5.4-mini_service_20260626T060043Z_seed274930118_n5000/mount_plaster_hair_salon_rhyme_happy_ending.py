#!/usr/bin/env python3
"""
storyworlds/worlds/mount_plaster_hair_salon_rhyme_happy_ending.py
===================================================================

A small animal-story world set in a hair salon, built from the seed words
"mount" and "plaster" with rhyme and a happy ending.

Premise:
- A little animal visits a hair salon for a trim or wash.
- The animal wants to climb onto a salon mount or sit near the mirrors.
- A plaster/bandage on a paw or ear can get wet or snagged.

Story shape:
- Setup: introduce the animal, the salon, and the beloved thing or reason for
  visiting.
- Tension: the animal wants to try something that would bother the plaster.
- Turn: the stylist offers a safe helper.
- Resolution: the animal gets the salon fun without ruining the plaster.

The prose aims to feel like a gentle Animal Story with a light rhyme beat and a
clear happy ending image.
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "cat": {"subject": "it", "object": "it", "possessive": "its"},
            "dog": {"subject": "it", "object": "it", "possessive": "its"},
            "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
            "fox": {"subject": "it", "object": "it", "possessive": "its"},
            "stylist": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Salon:
    place: str = "the hair salon"
    affords: set[str] = field(default_factory=lambda: {"wash", "trim", "blowdry"})


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
    rhyme1: str = ""
    rhyme2: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"animal"})


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
    def __init__(self, setting: Salon) -> None:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.id}'s {item.label} got wet and messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["conflict"] < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"{actor.id} worried about the plaster.")
    return out


def _r_joy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["love"] < THRESHOLD:
            continue
        sig = ("joy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} felt happy again.")
    return out


CAUSAL_RULES = [_r_soak, _r_worry, _r_joy]


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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    propagate(world, narrate=narrate)


def rhyme_line(activity: Activity) -> str:
    return f"{activity.rhyme1} {activity.rhyme2}"


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Little {hero.id} was a {hero.type} who loved bright places and gentle brushes."
    )


def setting_line(world: World) -> None:
    world.say(
        "The hair salon smelled like shampoo, and the mirrors shone like water."
    )


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {rhyme_line(activity)}."
    )
    world.say(
        f"But {hero.id} still wore {hero.pronoun('possessive')} {prize.label}, and that made the day a little tricky."
    )


def warn(world: World, stylist: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you {activity.verb}, your {prize.label} might get {activity.soil}," '
        f"{stylist.id} said. \"Let's find a safer way.\""
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} hopped toward the {activity.keyword} spot anyway.")
    world.say(f"{hero.id} tried to {activity.rush}.")


def offer_fix(world: World, stylist: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=stylist.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(
        f"{stylist.id} smiled and said, \"How about we {gear_def.prep}?\""
    )


def accept(world: World, hero: Entity, stylist: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} nodded, and soon the plan fit like a song."
    )
    world.say(
        f"They {gear_def.tail}. Then {hero.id} could {activity.verb}, while {prize.label} stayed neat and dry."
    )
    world.say(
        f"{hero.id} looked in the mirror with a shiny smile, and the salon felt warm and bright."
    )


def tell(setting: Salon, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "rabbit") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    stylist = world.add(Entity(id="Stylist", kind="character", type="stylist", label="the stylist"))
    prize = world.add(Entity(
        id="plaster",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=stylist.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    setting_line(world)
    world.say(f"{hero.id} came to {world.setting.place} for a little trim and a little treat.")
    wants(world, hero, activity, prize)

    world.para()
    warn(world, stylist, hero, activity, prize)
    defy(world, hero, activity)

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def:
        offer_fix(world, stylist, hero, prize, gear_def)
        accept(world, hero, stylist, activity, prize, gear_def)

    world.facts.update(hero=hero, stylist=stylist, prize=prize, activity=activity, gear=gear_def)
    return world


SETTINGS = {
    "salon": Salon(),
}

ACTIVITIES = {
    "wash": Activity(
        id="wash",
        verb="hop up for a wash",
        gerund="hopping up for a wash",
        rush="jump into the wash bowl",
        mess="wet",
        soil="soggy",
        zone={"paws", "head"},
        keyword="wash",
        rhyme1="Plip and plop",
        rhyme2="never want to stop",
    ),
    "chair": Activity(
        id="chair",
        verb="mount the salon chair",
        gerund="climbing the salon chair",
        rush="climb the chair in a flash",
        mess="dirty",
        soil="dusty",
        zone={"paws"},
        keyword="mount",
        rhyme1="Up the chair",
        rhyme2="with a happy flair",
    ),
    "dryer": Activity(
        id="dryer",
        verb="dance by the dryer",
        gerund="dancing by the dryer",
        rush="spin near the warm air",
        mess="wet",
        soil="damp",
        zone={"head", "ears"},
        keyword="dry",
        rhyme1="Whirr and breeze",
        rhyme2="gentle as you please",
    ),
}

PRIZES = {
    "paw_plaster": Prize(
        label="plaster",
        phrase="a little plaster on the paw",
        type="plaster",
        region="paws",
    ),
    "ear_plaster": Prize(
        label="plaster",
        phrase="a tiny plaster on the ear",
        type="plaster",
        region="ears",
    ),
}

GEAR = [
    Gear(
        id="towel_wrap",
        label="a soft towel wrap",
        covers={"paws"},
        guards={"wet", "dirty"},
        prep="wrap a soft towel around your paws",
        tail="wrapped the soft towel around the little paws",
    ),
    Gear(
        id="plastic_cap",
        label="a clear plastic cap",
        covers={"ears"},
        guards={"wet"},
        prep="put on a clear plastic cap first",
        tail="put on the clear plastic cap",
    ),
    Gear(
        id="salon_cushion",
        label="a tiny cushion",
        covers={"paws"},
        guards={"dirty"},
        prep="set you on a tiny cushion",
        tail="set the rabbit on the tiny cushion",
    ),
]

ANIMAL_NAMES = ["Milo", "Nina", "Pip", "Toto", "Luna", "Benny", "Mimi", "Remy"]
ANIMAL_TYPES = ["rabbit", "cat", "dog", "fox"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    seed: Optional[int] = None


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short Animal Story about {hero.id}, a {hero.type}, who wants to {act.verb} in a hair salon.',
        f'Write a gentle story with rhyme about a {hero.type} named {hero.id}, a {prize.label}, and a happy ending.',
        f'Create a child-friendly tale set in a hair salon where {hero.id} almost makes {prize.label} messy, then finds a safer way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who went to the hair salon in the story?",
            answer=f"{hero.id}, the little {hero.type}, went to the hair salon.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the stylist worry?",
            answer=f"The stylist worried because {hero.id}'s {prize.label} could get {act.soil}.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"What helped {hero.id} stay safe and happy?",
                answer=f"{gear.label} helped {hero.id} do the salon activity without ruining the {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hair salon?",
            answer="A hair salon is a place where people or animals can get their hair brushed, trimmed, washed, or styled.",
        ),
        QAItem(
            question="What is a plaster?",
            answer="A plaster is a small bandage that covers a sore spot so it can heal.",
        ),
        QAItem(
            question="Why do people use a towel after washing?",
            answer="A towel helps soak up water so hair and paws dry faster.",
        ),
    ]


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
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="salon", activity="chair", prize="paw_plaster", name="Milo", animal="rabbit"),
    StoryParams(place="salon", activity="wash", prize="ear_plaster", name="Luna", animal="cat"),
    StoryParams(place="salon", activity="dryer", prize="ear_plaster", name="Pip", animal="fox"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (pr.region in act.zone and select_gear(act, pr)):
            raise StoryError("No valid story matches the chosen activity and plaster.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(ANIMAL_NAMES)
    animal = args.animal or rng.choice(ANIMAL_TYPES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, animal=animal)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.animal)
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
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
        for r in g.covers:
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: hair salon, mount, plaster, rhyme, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
