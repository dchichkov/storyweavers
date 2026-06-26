#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/radio_lesson_learned_suspense_bravery_nursery_rhyme.py
==================================================================================================

A small nursery-rhyme style storyworld about a beloved radio, a brave child,
a suspenseful rainy moment, and a lesson learned at the end.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "bravery": 0.0, "conflict": 0.0, "lesson": 0.0}

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


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
            actor.memes["worry"] += 1
            out.append(f"The rain kissed the {item.label}, and now it was wet.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["bravery"] < THRESHOLD:
            continue
        if actor.memes["lesson"] >= THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson"] += 1
        out.append("The little heart learned a careful lesson.")
    return out


CAUSAL_RULES = [Rule("soak", _r_soak), Rule("lesson", _r_lesson)]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["wet"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little brave child who loved to sing along with the radio.")


def loves_radio(world: World, hero: Entity, radio: Entity) -> None:
    hero.memes["joy"] += 1
    radio.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {radio.label} and carried it as if it were a tiny treasure.")


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One rainy day, " if world.weather else "One day, "
    go = "went to" if not world.setting.indoor else "were in"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} {go} {world.setting.place}.")
    world.say("The clouds were gray, and the air felt hush-hush and still.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 0.0
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} looked at the sky.")
    world.say(f'"If the {activity.keyword} gets too wild, the radio might get wet," said the parent.')


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["bravery"] += 1
    world.say(f"But {hero.id} took a brave breath and tried to {activity.rush}.")


def guide(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} came close and held up a lantern.")
    world.say(f'"Brave does not mean hasty," said the parent. "Let us choose the safe way."')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="thing", label=gear_def.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear_def.covers),
        plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"So {hero.id} and {hero.pronoun('possessive')} {parent.label} chose {gear.label} first.")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"With {gear_def.label}, {hero.id} could {activity.verb} and keep the radio dry.")
    world.say(f"{hero.id} smiled, and the rain became only a soft drum on the roof.")
    world.say(f"At the end, the radio stayed safe, and the little one had learned to pause, listen, and be brave.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pippa", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "brave") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["bravery"] = 0.0
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mother"))
    prize = world.add(Entity(
        id="radio", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    intro(world, hero)
    loves_radio(world, hero, prize)
    world.para()
    arrives(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    defies(world, hero, activity)
    guide(world, parent, hero, activity)
    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity,
                       setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "porch": Setting(place="the porch", indoor=False, affords={"listen"}),
    "garden": Setting(place="the garden", indoor=False, affords={"listen"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"listen"}),
}

ACTIVITIES = {
    "listen": Activity(
        id="listen",
        verb="listen to the radio",
        gerund="listening to the radio",
        rush="dash into the rain with the radio",
        mess="wet",
        soil="soaked",
        zone={"torso", "hands"},
        weather="rainy",
        keyword="radio",
        tags={"radio", "wet", "lesson", "suspense", "bravery"},
    )
}

PRIZES = {
    "radio": Prize(
        label="radio",
        phrase="a little red radio with a bright dial",
        type="radio",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="raincoat",
        label="a raincoat",
        covers={"torso", "hands"},
        guards={"wet"},
        prep="put on a raincoat first",
        tail="put on a raincoat first",
    ),
    Gear(
        id="umbrella",
        label="an umbrella",
        covers={"torso"},
        guards={"wet"},
        prep="carry an umbrella",
        tail="carry an umbrella",
    ),
]

NAMES = ["Pippa", "Milo", "Nina", "Toby", "Luna", "Rory"]
TRAITS = ["brave", "gentle", "curious", "shy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short nursery-rhyme story about {hero.id}, a {prize.label}, and a rainy day at {f["setting"].place}.',
        f"Tell a suspenseful, gentle story where {hero.id} wants to {act.verb} but must be brave and listen to {hero.pronoun('possessive')} {parent.label}.",
        f'Write a child-friendly story that includes the word "{act.keyword}" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} with the radio?",
            answer=f"{hero.id} wanted to {act.verb} with {hero.pronoun('possessive')} little {prize.label}.",
        ),
        QAItem(
            question="Why did the parent worry in the rainy part of the story?",
            answer="The parent worried because the rain could make the radio wet and stop it from sounding bright and merry.",
        ),
        QAItem(
            question="What did the brave child learn by the end?",
            answer="The child learned to pause, listen, and choose the safe way before hurrying into the rain.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a radio?",
            answer="A radio is a machine that plays voices, music, and sounds so people can listen to them.",
        ),
        QAItem(
            question="Why can rain be a problem for a radio?",
            answer="Rain can make a radio wet, and water can stop it from working properly.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means feeling afraid or unsure and still doing the careful, good thing.",
        ),
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
    return "\n".join(lines)


CURATED = [
    StoryParams(place="porch", activity="listen", prize="radio", name="Pippa", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="garden", activity="listen", prize="radio", name="Milo", gender="boy", parent="father", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the radio would not be in real danger there.)"
    return "(No story: no gear in this world can both cover the radio and keep it safe from the chosen rain.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with radio, suspense, bravery, and a lesson learned.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
