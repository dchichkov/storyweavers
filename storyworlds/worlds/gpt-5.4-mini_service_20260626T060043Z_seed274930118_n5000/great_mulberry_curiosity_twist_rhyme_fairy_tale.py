#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/great_mulberry_curiosity_twist_rhyme_fairy_tale.py
===============================================================================================================

A small fairy-tale story world about the Great Mulberry and three magical
companions: Curiosity, Twist, and Rhyme.

Seed tale shape:
- A child loves the Great Mulberry tree and wants to gather berries.
- The berries are wonderfully sweet, but their juice stains clothes and hands.
- Curiosity wants to hurry up the climb, Twist helps with a clever method,
  and Rhyme steadies the mood with a song.
- A caregiver warns about the stain, and a sensible berry-apron compromise
  lets the child gather fruit safely.

The world is constraint-checked: the risky activity must plausibly threaten a
worn prize, and the compromise must genuinely cover the at-risk region.
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
            self.meters = {"stain": 0.0, "mud": 0.0, "spark": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "queen", "woman"}
        male = {"boy", "prince", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the Great Mulberry Garden"
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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["stain"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("stain", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stain"] += 1
            out.append(f"{actor.noun()}'s {item.label} picked up berry stains.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["stain"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caregiver = world.get(item.caretaker)
        caregiver.memes["worry"] += 1
        out.append(f"That would mean more washing for {caregiver.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_stain,
    _r_worry,
    _r_conflict,
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_at_risk(activity: Activity, prize: Prize) -> bool:
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
    return {
        "soiled": bool(prize and prize.meters["stain"] >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"In the days of the Great Mulberry, {hero.id} was a little {hero.type} with a bright heart.")


def love_tree(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the Great Mulberry tree, where the branches leaned low "
        f"and the berries shone like tiny purple lamps. {hero.pronoun().capitalize()} especially loved to {activity.gerund}."
    )


def gift_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One morning, {hero.pronoun('possessive')} {parent.noun()} gave {hero.pronoun('object')} {prize.phrase} "
        f"for the berry-gathering."
    )
    prize.worn_by = hero.id


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One bright day, {hero.id} and {hero.pronoun('possessive')} {parent.noun()} went to {world.setting.place}. "
        f"The air smelled sweet, and the mulberries waited overhead."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} at once, because the berries looked so tempting."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you hurry without care, your {prize.label} will get {activity.soil}," '
        f"{hero.pronoun('possessive')} {parent.noun()} said. \"We should be wise, not merely quick.\""
    )
    return True


def twist_and_rhyme(world: World, hero: Entity, activity: Activity) -> None:
    twist = world.get("Twist")
    rhyme = world.get("Rhyme")
    curiosity = world.get("Curiosity")
    twist.memes["spark"] += 1
    rhyme.memes["joy"] += 1
    curiosity.memes["curiosity"] += 1
    world.say(
        "Curiosity peered at the shiny berries, Twist found a neat way to reach them, "
        "and Rhyme hummed, 'Softly, softly, berry by berry, keep your sleeves and apron merry.'"
    )
    world.say(
        f"{hero.id} listened, but still leaned forward to {activity.rush}."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.noun()} smiled and said, "
        f"\"How about we {gear_def.prep} before you {activity.verb}?\""
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} beamed, for {hero.pronoun('possessive')} {parent.noun()} had found a kind answer."
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed clean under the {gear_def.label}. "
        f"The Great Mulberry tree rustled above them like a green crown."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the mother"))
    world.add(Entity(id="Curiosity", kind="character", type="sprite", label="Curiosity"))
    world.add(Entity(id="Twist", kind="character", type="sprite", label="Twist"))
    world.add(Entity(id="Rhyme", kind="character", type="sprite", label="Rhyme"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    love_tree(world, hero, activity)
    gift_prize(world, parent, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    twist_and_rhyme(world, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity,
                       setting=setting, gear=gear_def, conflict=True, resolved=gear_def is not None)
    return world


SETTINGS = {
    "great_mulberry_grove": Setting(place="the Great Mulberry Grove", affords={"pick_mulberries", "climb_branch"}),
    "orchard_path": Setting(place="the orchard path beside the Great Mulberry", affords={"pick_mulberries"}),
}

ACTIVITIES = {
    "pick_mulberries": Activity(
        id="pick_mulberries",
        verb="pick the mulberries",
        gerund="picking mulberries",
        rush="reach for the ripest cluster",
        mess="stain",
        soil="stained purple",
        zone={"hands", "torso"},
        keyword="mulberry",
        tags={"mulberry", "stain", "berry"},
    ),
    "climb_branch": Activity(
        id="climb_branch",
        verb="climb the low branch",
        gerund="climbing the low branch",
        rush="scramble up the twisting limb",
        mess="mud",
        soil="muddy",
        zone={"feet", "hands"},
        keyword="twist",
        tags={"twist", "branch"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a pale little cloak", type="cloak", region="torso"),
    "dress": Prize(label="dress", phrase="a bright new dress", type="dress", region="torso", genders={"girl"}),
    "gloves": Prize(label="gloves", phrase="white gloves for a feast day", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(
        id="berry_apron",
        label="a berry apron",
        covers={"torso", "hands"},
        guards={"stain"},
        prep="put on a berry apron",
        tail="tied on the berry apron",
    ),
    Gear(
        id="garden_gloves",
        label="garden gloves",
        covers={"hands"},
        guards={"stain", "mud"},
        prep="put on garden gloves",
        tail="pulled on the garden gloves",
        plural=True,
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Edda", "Nora", "Ivy"]
BOY_NAMES = ["Bram", "Pip", "Oren", "Finn", "Toby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_at_risk(act, prize) and select_gear(act, prize):
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
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a fairy-tale story about the Great Mulberry where {hero.id} wants to {act.verb}.',
        f'Tell a gentle story in which {hero.id} and {hero.pronoun("possessive")} {parent.noun()} visit {world.setting.place} and protect {prize.phrase}.',
        f'Write a short fairy tale that includes Curiosity, Twist, and Rhyme, and ends with a safe berry-gathering plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who went to the Great Mulberry Grove to {act.verb}?",
            answer=f"{hero.id} went with {hero.pronoun('possessive')} {parent.noun()} to gather berries near the Great Mulberry tree.",
        ),
        QAItem(
            question=f"Why did the {parent.noun()} warn {hero.id} about the {prize.label}?",
            answer=f"Because the mulberries could stain {hero.pronoun('possessive')} {prize.label} purple if {hero.id} hurried too carelessly.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay safe while {act.gerund}?",
            answer=f"A {f['gear'].label} helped {hero.id} gather the mulberries without ruining the {prize.label}.",
        ),
        QAItem(
            question="Who were Curiosity, Twist, and Rhyme?",
            answer="They were three small magical companions in the tale: Curiosity peered, Twist helped find a clever way, and Rhyme sang a steadying song.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} ended up {act.gerund} happily, and the {prize.label} stayed clean under the {f['gear'].label}.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "mulberry": [
        QAItem(
            question="What is a mulberry?",
            answer="A mulberry is a small sweet berry that grows on a tree and can stain fingers purple.",
        )
    ],
    "stain": [
        QAItem(
            question="Why do berry stains spread so easily?",
            answer="Berry juice is wet and colorful, so it can smudge onto cloth, skin, and sleeves very quickly.",
        )
    ],
    "berry": [
        QAItem(
            question="Why do people pick berries carefully?",
            answer="People pick berries carefully so they do not crush the fruit or get juice all over their clothes.",
        )
    ],
    "twist": [
        QAItem(
            question="What does it mean to twist a branch?",
            answer="To twist a branch means to turn it gently so you can help guide it or move it a little without breaking it.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a sound pattern in words, like when the endings of two words sound alike in a song or poem.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to find out more, ask questions, and see what is hidden or new.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["curiosity", "twist", "rhyme", "mulberry", "berry", "stain"]:
        if tag in tags or tag in {"curiosity", "twist", "rhyme"}:
            out.extend(WORLD_KNOWLEDGE.get(tag, []))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


CURATED = [
    StoryParams(place="great_mulberry_grove", activity="pick_mulberries", prize="dress", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="orchard_path", activity="pick_mulberries", prize="cloak", name="Bram", gender="boy", parent="father"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not activity_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not actually threaten {noun}.)"
    return f"(No story: nothing in the gear catalog truly protects {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world of the Great Mulberry, Curiosity, Twist, and Rhyme.")
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
        if not (activity_at_risk(act, pr) and select_gear(act, pr)):
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

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 hero_name=params.name, hero_type=params.gender, parent_type=params.parent)
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
            print(f"  {place:24} {act:18} {prize:10}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
