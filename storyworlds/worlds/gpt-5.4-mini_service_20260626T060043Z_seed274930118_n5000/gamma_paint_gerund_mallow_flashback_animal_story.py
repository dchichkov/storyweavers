#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gamma_paint_gerund_mallow_flashback_animal_story.py
==============================================================================================================================

A small animal-story world built from the seed words: gamma, paint-gerund, mallow.
It includes a Flashback beat and a gentle compromise structure in the style of an
Animal Story: a young animal wants to paint, worries about a messy outcome, and
finds a safer way to continue.

The premise is deliberately tiny and state-driven:
- a young animal loves a paint activity
- a cherished item is at risk from paint
- a flashback explains the animal's worry
- a helpful gear choice prevents the mess
- the ending image shows what changed

The domain is intentionally narrow so that the simulated state, the prose, and
the QA all stay closely aligned.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe", "hen"}
        male = {"boy", "father", "dad", "man", "buck", "stag", "rooster"}
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
    weather: str
    keyword: str = "paint-gerund"
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
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes), covers=set(v.covers), traits=list(v.traits))
                          for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


MESS_KINDS = {"painted"}
REGIONS = {"torso", "head", "legs", "feet"}


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("painted", 0.0) < THRESHOLD:
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
            item.meters["painted"] = item.meters.get("painted", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.id}'s {item.label} got paint on it.")
    return out


def _r_workload(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_flashback(world: World) -> list[str]:
    actor = world.facts.get("hero")
    if not actor:
        return []
    if world.facts.get("flashback_shown"):
        return []
    if world.facts.get("memory_ping", 0.0) < THRESHOLD:
        return []
    world.facts["flashback_shown"] = True
    return ["__flashback__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soak, _r_workload, _r_flashback):
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__flashback__":
                        produced.append(s)
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
    prize = sim.entities[prize_id]
    return {"soiled": bool(prize.meters.get("dirty", 0.0) >= THRESHOLD),
            "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This place does not support that activity.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def flashback(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"Flashback: once, {hero.id} had tried to {activity.verb} without help, "
        f"and {hero.pronoun('possessive')} {prize.label} had ended up sticky."
    )
    world.say(
        f"That memory made {hero.id} pause, because {hero.pronoun('possessive')} "
        f"{prize.label} still mattered to {hero.pronoun('object')}."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Gamma", hero_type: str = "goat",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "gentle"])
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="Mama"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)

    hero.memes["love_paint"] = 1
    world.say(f"{hero.id} was a little {hero.type} who loved {activity.gerund}.")
    world.say(f"{hero.id} liked the soft look of {activity.keyword} and the bright smell of mallow petals.")
    world.say(f"{hero.id}'s {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} on every happy walk.")

    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} lifted a careful hand.")
    pred = predict_mess(world, hero, activity, prize.id)
    world.facts["memory_ping"] = 1.0 if pred["soiled"] else 0.0
    world.facts["predicted_workload"] = pred["workload"]
    if pred["soiled"]:
        flashback(world, hero, activity, prize)
    if pred["soiled"]:
        world.say(f'"You will get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.label} said.')
    world.say(f"{hero.id} looked at the paint again and tried to {activity.rush}.")
    world.say(f"{hero.pronoun().capitalize()} wanted the fun, but not the mess.")

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No safe gear matches this story.")
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        raise StoryError("Chosen gear did not actually prevent the mess.")
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled and said, "
        f'"How about we {gear_def.prep} and then {activity.verb} together?"'
    )
    world.say(f"{hero.id} nodded, and soon {hero.pronoun('subject')} was {activity.gerund} in the {setting.place}.")
    world.say(
        f"The {gear_def.label} kept {hero.pronoun('possessive')} {prize.label} clean, "
        f"and the paint made a bright picture instead of a stain."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.facts["gear"] = gear_def
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, affords={"paint"}),
    "barnyard": Setting(place="the barnyard", indoor=False, affords={"paint"}),
    "porch": Setting(place="the porch", indoor=False, affords={"paint"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting pictures",
        rush="dash to the paint pots",
        mess="painted",
        soil="all painted",
        zone={"torso", "head", "legs"},
        weather="sunny",
        keyword="paint-gerund",
        tags={"paint", "mallow"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean little shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a neat apron", type="apron", region="torso"),
    "cap": Prize(label="cap", phrase="a bright cap", type="cap", region="head"),
}

GEAR = [
    Gear(id="smock", label="a smock", covers={"torso", "head", "legs"}, guards={"painted"},
         prep="put on a smock first", tail="put on the smock"),
    Gear(id="apron", label="an apron", covers={"torso"}, guards={"painted"},
         prep="put on an apron first", tail="put on the apron"),
]

GIRL_NAMES = ["Gamma", "Mina", "Lila", "Poppy", "Nora"]
BOY_NAMES = ["Buddy", "Toby", "Milo", "Ollie", "Sunny"]
TRAITS = ["curious", "gentle", "brave", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "paint": [("What is paint?", "Paint is a colored liquid or paste that people use to cover surfaces and make pictures.")],
    "mallow": [("What is a mallow?", "A mallow is a soft plant with pretty blossoms; some people also know marshmallow treats as sweet and fluffy.")],
    "smock": [("What is a smock?", "A smock is a loose cover you wear over clothes so paint does not get on them.")],
    "apron": [("What is an apron for?", "An apron helps keep clothes clean while you cook, craft, or paint.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short animal story for a small child about {hero.id} and "{act.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Include a Flashback moment and end with a safe compromise in the meadow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves {act.gerund}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {hero.id} wanted to {act.verb}, and paint could leave {hero.pronoun('possessive')} {prize.label} all painted.",
        ),
        QAItem(
            question=f"What happened in the Flashback?",
            answer=f"In the Flashback, {hero.id} remembered a time when {hero.pronoun('possessive')} {prize.label} got sticky from paint, so {hero.id} paused before rushing ahead.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} wearing {gear.label} and {act.gerund} safely while {prize.label} stayed clean.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in ["paint", "mallow", "smock", "apron"]:
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
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
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


CURATED = [
    StoryParams(place="meadow", activity="paint", prize="shirt", name="Gamma", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="barnyard", activity="paint", prize="cap", name="Buddy", gender="boy", parent="father", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: nothing in the gear catalog safely protects a {prize.label} from {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: Gamma, paint-gerund, mallow, and a Flashback.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:8} {prize:8}")
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
