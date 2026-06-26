#!/usr/bin/env python3
"""
storyworlds/worlds/crumb_kindness_lesson_learned_superhero_story.py
===================================================================

A small superhero storyworld about crumbs, kindness, and a lesson learned.

Seed tale premise:
A young superhero loves crunchy snacks after patrol, but crumbs can fall onto
their costume and make a mess. When a hungry little helper appears, the hero
must choose between keeping the snack to themself or sharing kindly. The story
turns on a simple, state-driven lesson: kindness can be the strongest superpower.

This world keeps the prose child-facing and concrete while modeling a tiny
simulation of physical mess and emotional change.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny rooftop"
    indoor: bool = False
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
    weather: str
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
        self.weather: str = ""
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("crumbs", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("crumb_soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["crumbs"] = item.meters.get("crumbs", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"Crumbs dusted {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type in {"boy", "girl"}), None)
    helper = next((e for e in world.characters() if e.id.startswith("Helper")), None)
    if not hero or not helper:
        return out
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("share", hero.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hope"] = helper.memes.get("hope", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    out.append("The shared snack made the whole roof feel warmer.")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_kindness,
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


def setting_detail(setting: Setting) -> str:
    return "The rooftop was bright and windy, with a little chair and a cereal box nearby."


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["crumbs"] = sim.get(actor.id).meters.get("crumbs", 0.0) + 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["crumbs"] = actor.meters.get("crumbs", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little superhero who loved helping on windy days.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because every patrol felt like an adventure.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That afternoon, {hero.pronoun('possessive')} {parent.label} gave {hero.pronoun('object')} {prize.phrase} for the rooftop break.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.it()} proudly, as if {prize.it()} could help save the whole city.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One sunny afternoon,"
    world.say(f"{day} {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label} pointed to the snack box.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {hero.pronoun("possessive")} {parent.label} said.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} still rushed to {activity.rush}, and little crumbs began to tumble onto the bench.")


def helper_arrives(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["need"] = helper.memes.get("need", 0.0) + 1
    world.say(f"Then a tiny helper appeared below the roof and looked up with hopeful eyes.")


def kindness_turn(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    helper.memes["gratitude"] = helper.memes.get("gratitude", 0.0) + 1
    world.say(f"{hero.id} remembered that a real hero also notices who is hungry.")
    world.say(f"With a smile, {hero.id} shared the snack and passed down the biggest crumb.")
    world.say(f"The little helper cheered, and the roof felt peaceful again.")


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0.0) + 1
    world.say(f"{hero.id} used {gear_def.label} first, so the crumbs stayed away from {hero.pronoun('possessive')} {prize.label}.")
    world.say(f"After that, {hero.id} could {activity.verb} kindly, and the helper got a fair share too.")
    world.say(f"That was the lesson learned: kindness could be a superhero power all by itself.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Captain Nova", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label="hero", meters={}, memes={}
    ))
    parent = world.add(Entity(id="Mom", kind="character", type=parent_type, label="mom"))
    helper = world.add(Entity(id="Helper Pip", kind="character", type="boy", label="small helper"))
    prize = world.add(Entity(
        id="cape", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    helper_arrives(world, helper, hero)

    world.para()
    kindness_turn(world, hero, helper)
    gear_def = select_gear(activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, helper=helper, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "rooftop": Setting(place="the sunny rooftop", indoor=False, affords={"snack"}),
    "balcony": Setting(place="the apartment balcony", indoor=False, affords={"snack"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"snack"}),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="eat the crunchy snack",
        gerund="snacking after patrol",
        rush="dash for the snack box",
        mess="crumbs",
        soil="full of crumbs",
        zone={"bench", "cape"},
        weather="sunny",
        keyword="crumb",
        tags={"crumb", "kindness"},
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a crumb tray",
        covers={"bench", "cape"},
        guards={"crumbs"},
        prep="place a crumb tray under the snack",
        tail="shared the snack over a crumb tray",
    ),
    Gear(
        id="napkin",
        label="a big napkin",
        covers={"cape"},
        guards={"crumbs"},
        prep="put a big napkin over the cape",
        tail="ate carefully on a big napkin",
    ),
]

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a bright red cape",
        type="cape",
        region="cape",
    )
}

NAMES = ["Captain Nova", "Starling", "Comet Kid", "Ruby Bolt", "Hero Mae", "Sky Finn"]


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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p, s in SETTINGS.items() for a in s.affords if prize_at_risk(ACTIVITIES[a], PRIZES["cape"]) and select_gear(ACTIVITIES[a], PRIZES["cape"])]


KNOWLEDGE = {
    "crumb": [("What is a crumb?", "A crumb is a tiny piece that breaks off from bread, cookies, or crackers.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring toward someone else.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is a good idea someone remembers after something happens.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        'Write a short superhero story for a young child about crumbs and kindness.',
        f"Tell a gentle story where {f['hero'].id} wants to {act.verb} but learns to share kindly.",
        f'Write a story that uses the word "{act.keyword}" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, helper, prize, act = f["hero"], f["parent"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little superhero who wanted to {act.verb} and also learn to be kind.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the snack?",
            answer=f"{parent.label} warned {hero.id} because the snack would leave {act.soil} on the {prize.label}.",
        ),
        QAItem(
            question=f"What changed when {hero.id} shared the snack with the helper?",
            answer=f"{hero.id} became kinder, the helper felt happy, and the story ended with a lesson learned about sharing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["crumb", "kindness", "lesson"]:
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
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
    py = set((p, a, "cape") for p, a in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero crumb storyworld about kindness and a lesson learned.")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the snack would not reach the cape, so there is no real problem to solve.)"
    return "(No story: no gear in this world can protect the cape from this snack.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = "brave"
    return StoryParams(place=place, activity=activity, prize="cape", name=name, gender=gender, parent=parent, trait=trait)


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


CURATED = [
    StoryParams(place="rooftop", activity="snack", prize="cape", name="Captain Nova", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:8} {prize:8}")
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
