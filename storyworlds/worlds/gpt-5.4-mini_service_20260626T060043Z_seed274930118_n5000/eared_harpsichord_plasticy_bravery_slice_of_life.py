#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eared_harpsichord_plasticy_bravery_slice_of_life.py
======================================================================================================

A small slice-of-life storyworld about a child, a delicate harpsichord,
and the quiet bravery it takes to keep practicing when a tiny spill could
ruin something lovely.

Seed-imagined source tale:
---
A child named Tessa loved the old harpsichord in the front room. It had tiny
eared carvings on the music stand and a warm, golden sound. Before an afternoon
visit, Tessa wanted cocoa, but her mother worried the plasticy cup would tip near
the keys. Tessa felt shy about playing while anyone watched. Then her mother
set down a tray, Tessa took a breath, put the cup safely away, and played a
small song bravely while the room felt calm again.

Causal state updates:
---
    carrying a wet cup near the instrument -> spill risk rises
    spill onto the harpsichord -> instrument gets wet and needs careful wiping
    child chooses the tray and moves the cup -> risk falls, bravery rises
    brave performance after a small pause -> joy and pride rise
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"wet", "sticky"}
REGIONS = {"keys", "lid", "bench"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the front room"
    indoor: bool = True
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.worn_by == actor.id:
                continue
            if item.region not in world.zone:
                continue
            if item.protective or world.covered(actor, item.region):
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{item.label.capitalize()} got wet.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    if hero.memes["chosen_calm"] >= THRESHOLD and hero.memes["shy"] >= THRESHOLD:
        sig = ("bravery", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["bravery"] += 1
            hero.memes["shy"] = 0
            out.append(f"{hero.id} found a brave breath.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("bravery", "social", _r_bravery),
]


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
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["shy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved the old harpsichord in the front room.")


def loves_instrument(world: World, hero: Entity, instrument: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} liked the way the {instrument.label} sounded soft and bright at the same time, "
        f"as if the room had tiny gold raindrops in it."
    )


def arrives(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} came into the front room together.")
    world.say("The eared carving on the harpsichord lid looked like it was listening too.")


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["shy"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} hands felt a little fluttery near the {prize.label}.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"If the {activity.keyword} tips," {parent.pronoun("possessive")} {parent.label} said, "the {prize.label} could get {activity.soil}."')
    return True


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="thing",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.id} set down {gear_def.label} and said they could put the drink there instead of by the keys.")
    return gear_def


def choose_bravery(world: World, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["chosen_calm"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a breath, moved the cup to {gear_def.label}, and sat a little straighter on the bench."
    )
    world.say(
        f"Then {hero.id} played {activity.gerund}, and the {prize.label} stayed dry while the room filled with a gentle tune."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Tessa",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["quiet", "careful"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="instrument",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_instrument(world, hero, prize)
    world.para()
    arrives(world, hero, parent)
    wants(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    world.say(f"{hero.id} looked at the eared carving and nodded.")
    gear_def = offer(world, parent, hero, activity, prize)
    world.para()
    if gear_def:
        choose_bravery(world, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "front_room": Setting(place="the front room", indoor=True, affords={"cocoa"}),
    "music_room": Setting(place="the music room", indoor=True, affords={"cocoa"}),
}

ACTIVITIES = {
    "cocoa": Activity(
        id="cocoa",
        verb="sip cocoa near the harpsichord",
        gerund="sipping cocoa near the harpsichord",
        rush="reach for the cup too fast",
        mess="wet",
        soil="spilled on",
        zone={"keys", "lid"},
        weather="",
        keyword="cocoa",
        tags={"harpsichord", "wet", "slice_of_life", "bravery"},
    ),
}

PRIZES = {
    "harpsichord": Prize(
        label="harpsichord",
        phrase="the old family harpsichord",
        type="harpsichord",
        region="keys",
    )
}

GEAR = [
    Gear(
        id="tray",
        label="a plasticy tray",
        covers={"keys", "lid"},
        guards={"wet"},
        prep="put the cup on a plasticy tray",
        tail="set the drink on the tray",
    ),
]

NAMES = ["Tessa", "Mina", "June", "Iris", "Nell"]
TRAITS = ["brave", "gentle", "quiet", "careful", "curious"]


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


KNOWLEDGE = {
    "harpsichord": [("What is a harpsichord?", "A harpsichord is a keyboard instrument that makes a bright, plucked sound when the keys are pressed.")],
    "cocoa": [("What is cocoa?", "Cocoa is a warm chocolate drink that some people like to sip slowly.")],
    "tray": [("What is a tray for?", "A tray is a flat board or plate that helps carry cups and snacks more safely.")],
    "bravery": [("What does bravery mean?", "Bravery means doing something even when you feel a little scared or shy.")],
    "eared": [("What does eared mean?", "Eared means having ears or ear-like parts, like a rabbit with long ears.")],
    "plasticy": [("What does plasticy mean?", "Plasticy means shiny or hard like plastic, which is a material many everyday things are made from.")],
}
KNOWLEDGE_ORDER = ["eared", "harpsichord", "plasticy", "cocoa", "tray", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a small slice-of-life story for a child named {hero.id} about a {prize.label} and the word "bravery".',
        f"Tell a gentle story where {hero.id} wants to {act.verb}, but {parent.label} worries about the {prize.label}, and they solve it with a plasticy tray.",
        f'Write a cozy story that includes the words "eared", "harpsichord", and "plasticy" and ends with a brave musical moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who was the story about in the front room with the {prize.label}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question="Why did the parent worry about the cup near the instrument?",
            answer=f"The parent worried that if the cup tipped, the {prize.label} could get {f.get('predicted_soil', 'wet and messy')}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the child keep the harpsichord safe?",
            answer=f"{hero.id} put the cup on a plasticy tray, so the drink stayed away from the keys.",
        ))
        qa.append(QAItem(
            question="How did the child feel at the end?",
            answer=f"{hero.id} felt brave and calm, and then played while the room stayed tidy and quiet.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("tray")
        tags.add("plasticy")
    tags.add("eared")
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="front_room", activity="cocoa", prize="harpsichord", name="Tessa", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="music_room", activity="cocoa", prize="harpsichord", name="Mina", gender="girl", parent="mother", trait="quiet"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not really reach the {prize.label}, so there is no honest worry to solve.)"
    return f"(No story: nothing in the gear catalog safely protects the {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: eared details, a harpsichord, a plasticy tray, and bravery."
    )
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
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "thoughtful"], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:10} {prize:12}  [{', '.join(genders)}]")
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
