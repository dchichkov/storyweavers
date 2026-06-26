#!/usr/bin/env python3
"""
storyworlds/worlds/press_repetition_cautionary_sound_effects_heartwarming.py
============================================================================

A small story world about a child, a press, a careful warning, repeating
motions, sound effects, and a warm, happy ending.

Premise seed:
---
A child wants to use a berry press in the kitchen. The grown-up worries the
press will splash juice onto a clean shirt, so they pause, add an apron, and
work together. The child repeats the motion, the press makes cheerful sounds,
and the finished juice becomes a shared treat.

Story shape:
---
- Setup: a child loves the press and the fruit.
- Tension: pressing too fast can stain clothes and make a mess.
- Turn: the grown-up gives a safer method and a simple helper.
- Resolution: they press slowly together, keep things clean, and enjoy the
  warm, fresh result.
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
    kind: str = "thing"  # "character" | "thing"
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
            self.meters = {"mess": 0.0, "clean": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "comfort": 0.0, "patience": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
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
    sound: str
    caution: str
    keyword: str = "press"
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            item.memes["worry"] += 1
            out.append(f"{item.label.capitalize()} got sticky.")
    return out


def _comfort(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.protective and item.worn_by and item.meters["safe"] >= THRESHOLD:
            sig = ("comfort", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The careful helper made the work feel easier.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_soak, _comfort):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by, "region": v.region,
        "protective": v.protective, "covers": set(v.covers), "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["mess"] += 1
    propagate(sim, narrate=False)
    return sim.get(prize_id).meters["mess"] >= THRESHOLD


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved the word press, because "
        f"press, press, press made things change."
    )
    world.say(
        f"{hero.id} loved {activity.gerund}, and the kitchen felt cozy whenever the "
        f"bright fruit waited in a bowl."
    )
    world.say(
        f"One afternoon, {hero.id}'s {parent.label} brought home {prize.phrase}, and "
        f"{hero.id} smiled at it like it was a tiny treasure."
    )

    world.para()
    world.say(f"At the kitchen counter, {hero.id} wanted to {activity.verb}.")
    world.say(f"The press answered with a soft {activity.sound}.")
    world.say(
        f"{hero.id} leaned closer and tried to {activity.rush}, but {activity.caution}."
    )
    hero.memes["joy"] += 1
    hero.memes["patience"] += 0.2
    world.zone = set(activity.zone)
    if predict_mess(world, hero, activity, prize.id):
        hero.memes["worry"] += 1
        world.say(
            f'"Careful," {hero.pronoun("possessive")} {parent.label} said. '
            f'"If you press too fast, {prize.label} will get {activity.soil}."'
        )
        world.say(
            f"{hero.id} paused, listened, and repeated, \"press, press, press,\" but this time "
            f"slower and smaller."
        )
        world.say(
            f'The press went "creak, creak, plip," and the fruit gave up its juice without a splash.'
        )
        gear_def = choose_gear(activity, prize)
        if gear_def is None:
            raise StoryError("(No safe helper exists for this press story.)")
        gear = world.add(Entity(
            id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
            caretaker=parent.id, protective=True, covers=set(gear_def.covers),
            plural=gear_def.plural, worn_by=hero.id
        ))
        gear.meters["safe"] += 1
        world.say(
            f'{hero.pronoun("possessive").capitalize()} {parent.label} put on {gear.label}, '
            f'and suddenly the work felt calm and snug.'
        )
        world.say(
            f"{hero.id} pressed, pressed, pressed in a patient rhythm. "
            f'"Squish, drip-drip," said the fruit, and the bowl filled up with bright juice.'
        )
        world.say(
            f"Then {hero.id} and {hero.pronoun('possessive')} {parent.label} shared the fresh treat, "
            f"and the clean {prize.label} stayed bright."
        )
        hero.memes["worry"] = 0.0
        hero.memes["comfort"] += 1
        hero.memes["joy"] += 1
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, resolved=True)
    else:
        world.say(
            f"The press made a happy {activity.sound}, and nothing spilled at all."
        )
        world.say(
            f"{hero.id} smiled, {hero.pronoun('possessive')} {parent.label} smiled back, and the kitchen stayed neat."
        )
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=None, resolved=True)

    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"berry_press", "apple_press"}),
    "pantry": Setting(place="the pantry", affords={"berry_press"}),
}

ACTIVITIES = {
    "berry_press": Activity(
        id="berry_press",
        verb="press the berries",
        gerund="pressing berries",
        rush="push the handle again and again",
        mess="sticky",
        soil="sticky and purple",
        zone={"torso", "hands"},
        sound="creak",
        caution="the juice can splash onto a shirt",
        keyword="press",
        tags={"press", "berries", "sticky"},
    ),
    "apple_press": Activity(
        id="apple_press",
        verb="press the apples",
        gerund="pressing apples",
        rush="push the handle a little too hard",
        mess="wet",
        soil="wet and shiny",
        zone={"torso", "hands"},
        sound="thump",
        caution="the cider can splish out if the handle moves too fast",
        keyword="press",
        tags={"press", "apples", "wet"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "dress": Prize(label="dress", phrase="a soft blue dress", type="dress", region="torso", genders={"girl"}),
}

GEAR = [
    Gear(id="apron", label="an apron", covers={"torso"}, guards={"sticky", "wet"},
         prep="tie on an apron", tail="tied on the apron"),
    Gear(id="towel", label="a kitchen towel", covers={"hands"}, guards={"sticky", "wet"},
         prep="wrap a towel around the handle", tail="wrapped a towel around the handle"),
]

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Finn", "Theo"]
TRAITS = ["gentle", "curious", "cheerful", "patient", "brave"]


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
                if prize.region in act.zone and choose_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming press story world.")
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
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short heartwarming story for a small child that includes the word "press" and a careful warning.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Make a cozy story with repeated sound words like {act.sound}, and end with sharing a fresh treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the kitchen?",
            answer=f"{hero.id} wanted to {act.verb}, and the press made a soft {act.sound}.",
        ),
        QAItem(
            question=f"Why did {parent.label} tell {hero.id} to be careful?",
            answer=f"{parent.label} worried that if {hero.id} pressed too fast, {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep the {prize.label} clean?",
            answer=f"An apron helped, and {hero.id} learned to press slowly, with press, press, press turning into a careful rhythm.",
        ),
        QAItem(
            question=f"What sound did the press make in the story?",
            answer=f"The press made a soft {act.sound}, and later it also went creak, creak, plip or thump, thump, drip as the fruit gave up its juice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = f["activity"]
    out = [
        QAItem(
            question="What does a press do?",
            answer="A press squeezes something with steady force, like fruit or flowers, to change its shape or take out juice.",
        ),
        QAItem(
            question="Why should someone press carefully?",
            answer="Careful pressing helps keep juice from splashing, so clothes and counters stay cleaner.",
        ),
    ]
    if "berries" in act.tags:
        out.append(QAItem(
            question="Why can berry juice stain clothes?",
            answer="Berry juice is colorful and wet, so it can leave purple or red marks on fabric.",
        ))
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
    lines.append("== (3) World questions ==")
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), guards(G,M), mess_of(A,M).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), fix(A,P).
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
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("only in clingo:", sorted(a - p))
    if p - a:
        print("only in python:", sorted(p - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:12} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(place="kitchen", activity="berry_press", prize="shirt", name="Mia", gender="girl", parent="mother", trait="gentle")),
            generate(StoryParams(place="kitchen", activity="apple_press", prize="shirt", name="Leo", gender="boy", parent="father", trait="patient")),
            generate(StoryParams(place="pantry", activity="berry_press", prize="dress", name="Nora", gender="girl", parent="mother", trait="curious")),
        ]
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
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
