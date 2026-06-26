#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/blame_sanitize_costume_sound_effects_pirate_tale.py
===============================================================================================================================

A standalone story world for a tiny pirate-tale domain.

Premise:
- A young pirate loves a special costume.
- A lively, noisy pirate activity threatens to make the costume dirty.
- A careful grown-up spots the problem, names the risk, and offers a safer
  way that still feels like pirate play.

This world is intentionally small and constraint-checked.  It models both
physical state (meters) and emotional state (memes), and it includes an ASP
twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
        for k in ("dirty", "soot", "wet", "sticky", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "love", "desire", "defiance", "conflict", "blame", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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
    sound: str
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def validity_gate(activity: Activity, prize: Prize) -> bool:
    return prize_at_risk(activity, prize) and select_gear(activity, prize) is not None


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "sticky", "soot", "dirty"):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{item.label} got {mess} and dirty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for {caretaker.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["blame"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soak, _r_workload, _r_conflict):
            msgs = rule(world)
            if msgs:
                changed = True
                produced.extend(m for m in msgs if m != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD, "workload": sum(e.meters["workload"] for e in sim.characters())}


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little pirate who loved every bright thing on the ship.")


def loves_costume(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.phrase} "
        f"like {hero.pronoun('possessive')} own treasure."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved {activity.gerund}; "
        f'"{activity.sound}" went the ship toys, and "{activity.sound}" answered the deck.'
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One breezy day, {hero.id} and {hero.pronoun('possessive')} {parent.label} were on {world.setting.place}."
    )
    world.say(f"The salty air hummed, and {activity.sound} sounded even louder beside the ropes.")


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {prize.label} was too fine to ruin."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you do that, your {prize.label} will get {activity.soil}," '
        f"{parent.label} said. \"Don't blame the deck if the paint splashes!\""
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} stamped {hero.pronoun('possessive')} foot and reached for the brush.")
    world.say(f'"{activity.sound}!" went the pot as the paint started to wobble.')


def grab_and_blame(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["blame"] += 1
    world.say(
        f"Then {parent.label} gently held up a hand and said, "
        f"\"No, little pirate. We can do this the clean way.\""
    )
    world.say(f"{hero.id} felt a bit blamed, and the tug-of-war in {hero.pronoun('possessive')} chest grew hot.")


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
        del world.entities[gear.id]
        return None
    world.say(
        f'Then {parent.label} smiled. "How about we {gear_def.prep} and still make our pirate sounds?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["blame"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id}'s face lit up. {hero.id} hugged {hero.pronoun('possessive')} {parent.label} and shouted, "
        f"\"Aye-aye!\""
    )
    world.say(
        f"They {gear_def.tail}, and soon {hero.id} was {activity.gerund}, "
        f"{hero.pronoun('possessive')} {prize.label} still clean, while "
        f"{gear_def.label} kept the mess off the costume."
    )
    world.say(
        f'"{activity.sound}!" went the brushes, "clink-clink!" went the toys, and the little pirate grinned from ear to ear.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"love": 0.0, "joy": 0.0, "desire": 0.0, "defiance": 0.0, "conflict": 0.0, "blame": 0.0, "relief": 0.0}, meters={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain parent", memes={}, meters={}))
    prize = world.add(Entity(
        id="costume",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_activity(world, hero, activity)
    loves_costume(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_and_blame(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        gear=gear_def,
        setting=setting,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "ship_deck": Setting(place="the deck of the Laughing Gull", indoor=False, affords={"paint_flag", "drum_roll"}),
    "harbor_stage": Setting(place="the harbor stage", indoor=False, affords={"paint_flag"}),
    "cove": Setting(place="the bright cove", indoor=False, affords={"drum_roll"}),
}

ACTIVITIES = {
    "paint_flag": Activity(
        id="paint_flag",
        verb="paint the pirate flag",
        gerund="painting the pirate flag",
        rush="grab the paint pot",
        mess="sticky",
        soil="spotted with paint",
        zone={"torso"},
        sound="Splat-swash!",
        keyword="paint",
        tags={"paint", "costume", "sanitize"},
    ),
    "drum_roll": Activity(
        id="drum_roll",
        verb="beat the drum",
        gerund="beating the drum",
        rush="lift the drumsticks",
        mess="soot",
        soil="smudged with soot",
        zone={"torso", "head"},
        sound="Boom-bam!",
        keyword="boom",
        tags={"sound", "costume"},
    ),
}

PRIZES = {
    "costume": Prize(
        label="costume",
        phrase="a sparkly pirate costume",
        type="costume",
        region="torso",
    ),
    "hat": Prize(
        label="hat",
        phrase="a feathered pirate hat",
        type="hat",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a clean apron",
        covers={"torso"},
        guards={"sticky", "soot"},
        prep="put on a clean apron first",
        tail="walked back to the paint table with the apron on",
    ),
    Gear(
        id="cloth",
        label="a sanitizing cloth",
        covers={"torso", "head"},
        guards={"sticky", "soot"},
        prep="sanitize the costume with a soft cloth first",
        tail="used the sanitizing cloth before the next splash",
    ),
]

GIRL_NAMES = ["Mina", "Ruby", "Luna", "Nell", "Pia", "Ivy"]
BOY_NAMES = ["Finn", "Jasper", "Owen", "Toby", "Pip", "Cai"]
TRAITS = ["brave", "cheerful", "curious", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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
    "paint": [("What is paint?", "Paint is a colored liquid used to cover things with color.")],
    "sanitize": [("What does sanitize mean?", "To sanitize something means to clean it carefully so it is safer and less messy.")],
    "costume": [("What is a costume?", "A costume is special clothes someone wears to look like a character in a story or play.")],
    "sound": [("What is a sound effect?", "A sound effect is a made-up or added sound, like boom or clang, that makes a story feel lively.")],
    "boom": [("What does boom sound like?", "Boom sounds loud and deep, like a drum or cannon in a story.")],
    "dirty": [("Why do dirty clothes need washing?", "Dirty clothes need washing so the stains and mess can come out.")],
}
KNOWLEDGE_ORDER = ["paint", "sanitize", "costume", "sound", "boom", "dirty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a small pirate tale for a child that includes "{act.keyword}" and the word "costume".',
        f"Tell a gentle pirate story where {f['hero'].id} wants to {act.verb} but the costume might get messy, then someone offers a safer plan.",
        f'Write a story with sound effects like "{act.sound}" and a happy cleanup or sanitize moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    act: Activity = f["activity"]
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.id} was the little pirate wearing the costume.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the costume?",
            answer=f"{parent.label} worried because the costume could get {act.soil} if {hero.id} painted or drummed without protection.",
        ),
        QAItem(
            question=f"What sound made the pirate play feel lively?",
            answer=f'The story used "{act.sound}" as a sound effect, along with "clink-clink!" to make the pirate scene feel busy and fun.',
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} covered the costume, so {hero.id} could still {act.verb} without ruining {prize.label}.",
        ))
        qa.append(QAItem(
            question="What changed by the end?",
            answer=f"By the end, {hero.id} felt happy again, the costume stayed clean, and the pirate play could continue safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship_deck", activity="paint_flag", prize="costume", name="Pip", gender="boy", parent="mother", trait="brave"),
    StoryParams(place="harbor_stage", activity="paint_flag", prize="hat", name="Mina", gender="girl", parent="father", trait="cheerful"),
    StoryParams(place="cove", activity="drum_roll", prize="costume", name="Finn", gender="boy", parent="mother", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the chosen costume would not actually get messy in this scene.)"
    return "(No story: no gear in this world can safely protect that prize for this activity.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this prize does not fit the requested gendered setup; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    ap = argparse.ArgumentParser(description="A small pirate tale story world with sound effects.")
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
        if not validity_gate(act, pr):
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
    gender = args.gender or rng.choice(sorted(PRIZES[prize_id].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
