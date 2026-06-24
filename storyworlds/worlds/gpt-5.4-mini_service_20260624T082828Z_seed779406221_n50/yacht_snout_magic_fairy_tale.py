#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/yacht_snout_magic_fairy_tale.py
============================================================================================================

A small fairy-tale story world about a magic yacht, a child with a snout,
and a careful compromise that keeps a treasured prize safe.

The seed image behind this world:
---
A little pig prince stood on a moonlit dock beside a magic yacht. His snout
tipped up to the stars while he begged to sail at once. But his golden crown
could be blown into the sea spray, so a grown-up suggested a clever magical
covering. The prince agreed, and the yacht sailed on with laughter and sparks.
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
REGIONS = {"head", "torso", "feet"}
MESS_KINDS = {"spray", "sparkles"}


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
        for k in ["spray", "sparkles", "dirty", "windy", "spark"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "desire", "conflict", "love", "worry", "defiance", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man", "pig", "piglet"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit harbor"
    indoors: bool = False
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["spray"] < THRESHOLD and actor.meters["sparkles"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            if ("soak", item.id) in world.fired:
                continue
            world.fired.add(("soak", item.id))
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got splashed.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would make more work for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("soak", _r_soak), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} shone softly under the stars."


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.zone = set(world.zone)
    sim.fired = set(world.fired)
    sim.get(actor.id).meters[activity.mess] += 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["dirty"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    desc = "little " + ", ".join([t for t in hero.traits if t]) if hero.traits else "little"
    world.say(f"{hero.id} was a {desc} {hero.type} with a bright snout and a brave heart.")


def loves_magic_yacht(world: World, hero: Entity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved the magic yacht because it glittered like a dream on the water.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One evening, {hero.pronoun('possessive')} {parent.label} brought home {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting))
    world.say(f"The magic yacht waited there, rocking like a sleepy swan.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} at once, and {hero.pronoun('possessive')} snout wrinkled with excitement.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"You will get your {prize.label} {activity.soil}," {parent.label} said softly. "We should think of a safer way."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} frowned and tried to {activity.rush} anyway.")


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            gear = g
            break
    if gear is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear = None
        return None
    item = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True,
                            covers=set(gear.covers), plural=gear.plural,
                            owner=hero.id, caretaker=parent.id))
    item.worn_by = hero.id
    world.say(f"Then {parent.label} smiled. \"How about we {gear.prep}?\"")
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(f"{hero.id} smiled wide and hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} safe, and the magic yacht sparkled on the dark water.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip",
         hero_type: str = "pig", parent_type: str = "queen", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["curious", "cheerful"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the queen"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves_magic_yacht(world, hero)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear = offer_gear(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear,
                       conflict=hero.memes["defiance"] >= THRESHOLD, resolved=gear is not None)
    return world


SETTINGS = {
    "harbor": Setting(place="the moonlit harbor", affords={"sail"}),
    "cove": Setting(place="the silver cove", affords={"sail", "glow"}),
    "dock": Setting(place="the royal dock", affords={"sail"}),
}

ACTIVITIES = {
    "sail": Activity(
        id="sail",
        verb="ride the magic yacht",
        gerund="riding the magic yacht",
        rush="dash onto the magic yacht",
        mess="spray",
        soil="sprayed wet",
        zone={"head", "torso"},
        keyword="magic",
        tags={"magic", "yacht"},
    ),
    "glow": Activity(
        id="glow",
        verb="cast a glowing spell on the mast",
        gerund="casting a glowing spell",
        rush="run to the bow and wave the wand",
        mess="sparkles",
        soil="full of sparkles",
        zone={"head", "torso"},
        keyword="magic",
        tags={"magic", "yacht"},
    ),
}

PRIZES = {
    "crown": Prize(label="crown", phrase="a tiny golden crown", type="crown", region="head"),
    "cloak": Prize(label="cloak", phrase="a velvet cloak with silver stars", type="cloak", region="torso"),
}

GEAR = [
    Gear(id="hood", label="a moon-hood", covers={"head"}, guards={"spray", "sparkles"},
         prep="put on the moon-hood first", tail="sailed with the moon-hood tied snugly under the chin"),
    Gear(id="cloakwrap", label="a charm-wrap cloak", covers={"torso"}, guards={"spray", "sparkles"},
         prep="wrap the charm-cloak around your shoulders", tail="went along wrapped in the charm-cloak"),
]

GIRL_NAMES = ["Luna", "Mina", "Elsa", "Nora", "Ivy"]
BOY_NAMES = ["Pip", "Finn", "Theo", "Milo", "Owen"]
TRAITS = ["brave", "gentle", "curious", "cheerful"]


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
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    out.append((place, act_id, prize_id))
    return out


KNOWLEDGE = {
    "yacht": [("What is a yacht?", "A yacht is a boat for sailing on water, often smooth and fancy.")],
    "snout": [("What is a snout?", "A snout is the nose and mouth part of an animal like a pig.")],
    "magic": [("What is magic in a fairy tale?", "Magic is a special power that can make wonderful things happen.")],
    "crown": [("What is a crown?", "A crown is a special hat for a king or queen.")],
    "cloak": [("What is a cloak?", "A cloak is a loose covering you wear over your clothes.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a small child about a {f["hero"].type} with a snout, a magic yacht, and a careful promise.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} but must protect {f['prize'].label}.",
        f'Write a magical bedtime story that includes the words "yacht" and "snout" and ends happily on the water.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    out = [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, a little {hero.type} with a snout, and the queen who cares for {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the magic yacht?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the queen worry about {prize.label}?",
            answer=f"She worried because the magic yacht would leave {prize.label} {act.soil}.",
        ),
    ]
    if f.get("resolved") and gear:
        out.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"It covered the part of {hero.id} that held {prize.label}, so {hero.id} could enjoy the boat without ruining it.",
        ))
    return out


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | {"yacht", "snout", "magic"}
    out: list[QAItem] = []
    for tag in ["yacht", "snout", "magic", "crown", "cloak"]:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world: a magic yacht, a snout, and a careful promise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["queen", "king"])
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
    place, act, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, "pig", params.parent, [params.trait, "gentle"])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


CURATED = [
    StoryParams(place="harbor", activity="sail", prize="crown", name="Pip", gender="boy", parent="queen", trait="curious")
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
