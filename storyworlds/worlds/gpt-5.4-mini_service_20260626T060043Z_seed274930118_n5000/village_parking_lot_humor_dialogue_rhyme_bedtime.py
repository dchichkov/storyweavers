#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/village_parking_lot_humor_dialogue_rhyme_bedtime.py
=========================================================================================================================

A small bedtime-story world set in a village parking lot, with humor, dialogue,
and a little rhyme. The child wants to do a noisy, dusty bit of play after dark;
the guardian worries about a favorite shirt; a simple protective smock makes the
plan gentle again.

The world model tracks both physical meters and emotional memes, and the story is
assembled from simulated state rather than from a frozen template.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village parking lot"
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("dusty", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dusty"] = item.meters.get("dusty", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["work_worry"] = carer.memes.get("work_worry", 0.0) + 1
        out.append(f"That would mean more laundry for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("work", _r_work)]


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
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes), "covers": set(v.covers)}) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters[activity.mess] = sim.get(actor.id).meters.get(activity.mess, 0.0) + 1
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def bedtime_tone() -> str:
    return "The stars were blinking like sleepy buttons in the sky."


def rhyme_line() -> str:
    return "Soft feet, neat feet, tiptoe on the ground; quiet little circles make a sleepy, lovely sound."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"In a village parking lot, {hero.id} was a little {hero.type} who loved quiet night games.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, and {bedtime_tone()}")


def prize_scene(world: World, hero: Entity, prize: Entity, parent: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{parent.label.capitalize()} had bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} loved {prize.it()} very much.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One calm night, {hero.id} and {hero.pronoun('possessive')} {parent.label} walked to {world.setting.place}.")
    world.say("The lot was empty, except for a sleepy cart and one little bicycle leaning like a yawning horse.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"'{hero.id} wanted to {activity.verb},' {hero.pronoun('subject')} whispered. 'Just a tiny circle, then bed.'")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f"'{parent.label.capitalize()} worried that {hero.pronoun('possessive')} {prize.label} would get {activity.soil},' {parent.pronoun('subject')} said.")
    world.say("'And dusty shirts are funny only until laundry time,' {0} added.".format(parent.pronoun('subject')))
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["gumption"] = hero.memes.get("gumption", 0.0) + 1
    world.say(f"{hero.id} gave a tiny grin. 'But the chalk makes a moon road!' {hero.pronoun('subject')} said.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id, caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f"'{parent.label.capitalize()} smiled. \"How about we {gear_def.prep}?\"' {parent.pronoun('subject')} asked.")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["gumption"] = 0.0
    world.say(f"'{hero.id} nodded and hugged {hero.pronoun('possessive')} {parent.label}.'")
    world.say(f"Then they {gear_def.tail}, and {hero.id} drew a tiny chalk crescent while {prize.label} stayed clean.")
    world.say(rhyme_line())
    world.say("Soon the moon was high, the parking lot was still, and bedtime felt like a blanket folded just right.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    prize_scene(world, hero, prize, parent)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def, conflict=True, resolved=gear_def is not None)
    return world


SETTINGS = {
    "parking_lot": Setting(place="the village parking lot", affords={"chalk"}),
}

ACTIVITIES = {
    "chalk": Activity(
        id="chalk",
        verb="draw moon roads with chalk",
        gerund="drawing moon roads with chalk",
        rush="dash around the chalk stars",
        mess="dusty",
        soil="dusty",
        zone={"torso"},
        weather="night",
        keyword="village",
        tags={"village", "chalk", "dusty"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean striped shirt", type="shirt", region="torso"),
    "jacket": Prize(label="jacket", phrase="a soft bedtime jacket", type="jacket", region="torso"),
}

GEAR = [
    Gear(id="smock", label="a little smock", covers={"torso"}, guards={"dusty"}, prep="put on a little smock first", tail="walked back for the little smock"),
    Gear(id="night_cloak", label="a night cloak", covers={"torso"}, guards={"dusty"}, prep="wrap on a night cloak first", tail="came back for the night cloak"),
]

GIRL_NAMES = ["Mina", "Luna", "Sara", "Nia", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Milo", "Noah"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story set in a village parking lot that includes the word "{f["activity"].keyword}".',
        f"Tell a gentle, funny story where {f['hero'].id} wants to {f['activity'].verb} but {f['parent'].label} worries about {f['prize'].phrase}.",
        "Make the ending feel sleepy, kind, and a little rhyming.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Where did {hero.id} want to play?",
            answer=f"{hero.id} wanted to play in the village parking lot, where the night was quiet and the ground was smooth.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do there?",
            answer=f"{hero.id} wanted to {act.verb}, which made a tiny dusty trail of chalk fun instead of noisy trouble.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because {prize.phrase} could get {act.soil} if {hero.id} played without protection.",
        ),
        QAItem(
            question=f"What helped {hero.id} play safely?",
            answer=f"They used {gear.label}, so {hero.id} could keep drawing while {prize.label} stayed clean.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} calm, {parent.label} smiling, and the parking lot feeling as sleepy as a tucked-in pillow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parking lot?",
            answer="A parking lot is a place where people leave cars for a while.",
        ),
        QAItem(
            question="What is a smock for?",
            answer="A smock is a loose cover that helps keep clothes clean when something dusty or messy is happening.",
        ),
        QAItem(
            question="Why do bedtime stories often sound gentle?",
            answer="Bedtime stories are often gentle because they help children feel calm and ready to sleep.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="parking_lot", activity="chalk", prize="shirt", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="parking_lot", activity="chalk", prize="jacket", name="Owen", gender="boy", parent="father"),
]


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
    ap = argparse.ArgumentParser(description="Bedtime story world in a village parking lot, with humor, dialogue, and rhyme.")
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
    prize_obj = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_obj.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        combos = asp_valid_combos()
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
