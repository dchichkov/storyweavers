#!/usr/bin/env python3
"""
storyworlds/worlds/discourage_slag_dialogue_comedy.py
======================================================

A small comedy storyworld about a child who wants to poke at slag, gets
discouraged with a funny warning, and then finds a safer, sillier way to do it
through dialogue.

Seed tale idea:
---
A child spots a sparkly pile of slag near a small forge and wants to grab it.
A grown-up says no, because the slag is hot and dusty. The child groans, makes
a joke, and tries anyway. Then the grown-up offers a pair of tongs and thick
gloves, and they laugh while moving the slag into a bucket without getting
burned or dirty.

Core dynamics:
---
- wanting the slag pile raises desire
- touching/approaching hot slag risks dirtying or warming the child's clothes
- the grown-up discourages the unsafe choice
- the child responds in dialogue, then accepts safer gear
- the ending proves the change: the slag is handled safely and the child's
  prize stays clean
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
    warning: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "forge": Setting(place="the little forge", indoor=True, affords={"poke", "sort"}),
    "yard": Setting(place="the back yard", indoor=False, affords={"sort"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"poke", "show"}),
}

ACTIVITIES = {
    "poke": Activity(
        id="poke",
        verb="poke the slag",
        gerund="poking the slag",
        rush="run to the slag pile",
        mess="dusty",
        soil="dusty and warm",
        zone={"hands", "torso"},
        warning="hot",
        keyword="slag",
        tags={"slag", "hot", "dust"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the slag",
        gerund="sorting the slag",
        rush="dash to the buckets",
        mess="dusty",
        soil="dusty",
        zone={"hands", "torso", "feet"},
        warning="dusty",
        keyword="slag",
        tags={"slag", "dust"},
    ),
    "show": Activity(
        id="show",
        verb="show the slag to everyone",
        gerund="showing the slag",
        rush="rush to the door with the slag",
        mess="dusty",
        soil="dusty",
        zone={"hands"},
        warning="sparkly",
        keyword="slag",
        tags={"slag", "comedy"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean yellow shirt", "shirt", "torso"),
    "shoes": Prize("shoes", "new blue shoes", "shoes", "feet", plural=True),
    "apron": Prize("apron", "a neat apron", "apron", "torso"),
}

GEAR = [
    Gear(
        id="tongs",
        label="long tongs",
        covers={"hands"},
        guards={"hot", "dusty"},
        prep="use long tongs and keep our hands back",
        tail="used the long tongs like a pair of metal chopsticks",
    ),
    Gear(
        id="gloves",
        label="thick gloves",
        covers={"hands"},
        guards={"hot", "dusty"},
        prep="put on thick gloves first",
        tail="put on the thick gloves and grinned",
    ),
    Gear(
        id="aprongear",
        label="a heavy apron",
        covers={"torso"},
        guards={"dusty"},
        prep="tie on a heavy apron first",
        tail="tied on the heavy apron and laughed",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ada", "Zoe", "Lily"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Noah", "Theo"]
TRAITS = ["curious", "silly", "cheerful", "playful", "brave"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        sig = ("mess", item.id, activity.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1
        item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
        if narrate:
            world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty.")

def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    hero.memes["curiosity"] = 1
    hero.memes["love_slag"] = 1
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} {hero_type} who loved shiny things and funny noises.")
    world.say(f"{hero.id} kept pointing at {prize.phrase} and the sparkly pile of slag beside the forge.")

    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} frowned.")
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"No," {parent.pronoun("subject")} said. "That slag is {activity.warning} and {activity.soil}."')
        world.say(f'"{What if it\'s only a little bit hot?" {hero.id} asked. "I can be tiny and dramatic."')
        hero.memes["discouraged"] = hero.memes.get("discouraged", 0.0) + 1
        hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
        world.say(f'{hero.id} tried to {activity.rush}, but {parent.pronoun("possessive")} hand stopped {hero.pronoun("object")}.')
        world.say(f'"We can still play," {parent.pronoun("subject")} said, "just not with bare hands."')

    world.para()
    gear_def = select_gear(activity, prize)
    gear = None
    if gear_def is not None:
        gear = world.add(Entity(
            id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
            caretaker=parent.id, protective=True, covers=set(gear_def.covers),
            plural=gear_def.plural
        ))
        gear.worn_by = hero.id
        world.say(f'"How about we {gear_def.prep}?" {parent.pronoun("subject")} asked.')
        world.say(f'"That sounds less like a disaster and more like a plan," {hero.id} said.')
        world.say(f'{hero.id} {gear_def.tail} while {parent.pronoun("subject")} held out a bucket.')

    if gear is not None:
        _do_activity(world, hero, activity, narrate=False)
        world.say(f"Together they moved the slag into the bucket.")
        world.say(f"{hero.id} laughed, because the slag looked like treasure and behaved like a loaf of rocks.")
        world.say(f"In the end, {hero.pronoun('possessive')} {prize.label} stayed clean and the forge stayed tidy.")
        hero.memes["joy"] += 1
        hero.memes["discouraged"] = 0.0

    world.facts.update(
        hero=hero, parent=parent, prize=prize, activity=activity, setting=setting,
        gear=gear, resolved=gear is not None, conflict=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a funny story for a child where "{act.keyword}" appears near a forge and a grown-up says no at first.',
        f"Tell a comedy story in dialogue where {hero.id} wants to {act.verb} but {parent.pronoun('subject')} discourages {hero.pronoun('object')} for safety.",
        f"Write a short, child-friendly scene about slag, a warning, and a safer plan with dialogue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    out = [
        QAItem(
            question=f"What did {hero.id} want to do with the slag?",
            answer=f"{hero.id} wanted to {act.verb}, because the slag looked sparkly and funny."
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} discourage {hero.id} at first?",
            answer=f"{parent.pronoun('subject').capitalize()} discouraged {hero.id} because the slag was {act.warning} and could make {prize.label} {act.soil}."
        ),
        QAItem(
            question=f"What did they use so {hero.id} could play safely?",
            answer=f"They used {f['gear'].label} so {hero.id} could handle the slag without getting too close."
        ),
    ]
    if f.get("resolved"):
        out.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"{hero.id} and {parent.pronoun('subject')} laughed, moved the slag into a bucket, and {prize.label} stayed clean."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    if f["activity"].id == "poke":
        out.append(QAItem(
            question="What are tongs for?",
            answer="Tongs are long tools that help you pick up hot or messy things without touching them."
        ))
    out.append(QAItem(
        question="Why do grown-ups sometimes discourage a child from touching hot things?",
        answer="Grown-ups discourage that because hot things can burn skin or make clothes dirty, so they want the child to stay safe."
    ))
    out.append(QAItem(
        question="What is slag?",
        answer="Slag is the rocky leftover that can form when metal is melted and cleaned."
    ))
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
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
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about discouraging a child from touching slag.")
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
    place, activity, prize = rng.choice(sorted(combos))
    prize_cfg = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_cfg.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, "girl" if params.gender == "girl" else "boy",
                 params.parent, params.trait)
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
    StoryParams(place="forge", activity="poke", prize="shirt", name="Mia", gender="girl", parent="mother", trait="silly"),
    StoryParams(place="forge", activity="sort", prize="shoes", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="workshop", activity="show", prize="apron", name="Nora", gender="girl", parent="mother", trait="playful"),
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
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
