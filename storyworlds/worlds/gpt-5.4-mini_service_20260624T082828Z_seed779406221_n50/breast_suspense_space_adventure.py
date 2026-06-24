#!/usr/bin/env python3
"""
A small storyworld about a space walk with suspense: a tiny crew sees a
mysterious signal, crosses a dark stretch of space, and discovers that a
breast-shaped emblem on a chest plate was the key to the rescue beacon.

The world is intentionally simple:
- one setting: a moon base
- one main activity: follow a blinking signal
- one prize: a chest patch / badge worn on the breast
- one gear fix: a lamp or tether that makes the trip safe

The story is driven by state changes: fear rises in the dark, then falls when
the crew uses the right tool and the signal is found.
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

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
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
    outer_space: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    hazard: str
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
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_shadow_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("dark", 0.0) < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
        out.append(f"The dark made {actor.id} feel small.")
    return out


def _r_signal_found(world: World) -> list[str]:
    out: list[str] = []
    beacon = world.entities.get("beacon")
    if not beacon:
        return out
    for actor in world.characters():
        if actor.meters.get("signal", 0.0) < THRESHOLD:
            continue
        sig = ("signal_found", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if beacon.meters.get("lost", 0.0) >= THRESHOLD:
            beacon.meters["lost"] = 0.0
            beacon.meters["found"] = 1.0
            out.append(f"A bright beep answered back from the rock.")
    return out


CAUSAL_RULES = [
    _r_shadow_fear,
    _r_signal_found,
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


def signal_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.risk in gear.protects and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "fear": sim.get(actor.id).memes.get("fear", 0.0),
        "signal": sim.get(actor.id).meters.get("signal", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters["signal"] = actor.meters.get("signal", 0.0) + 1.0
    actor.meters["dark"] = actor.meters.get("dark", 0.0) + 1.0
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little space pilot who loved quiet missions and bright stars."
    )


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"On the moon base, {hero.id} wore {hero.pronoun('possessive')} "
        f"{prize.label} close to {hero.pronoun('possessive')} {prize.region}, "
        f"and {parent.label} said it was the most important badge on the suit."
    )
    world.say(
        f"{hero.id} loved to {activity.verb}, because {activity.keyword} lights made the dark feel like a game."
    )


def warning(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> bool:
    pred = predict(world, hero, activity)
    if pred["fear"] < THRESHOLD:
        return False
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"If you go too far, your {prize.label} could get lost in the dark," {parent.id} said.'
    )
    return True


def tension(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} wanted to go anyway, so {hero.pronoun()} took one careful step after another."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, and the shadows stretched long.")


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    world.say(
        f"{parent.label} pointed to a small lamp and smiled. "
        f'"Use {gear_def.label} first, and the path will not feel so scary."'
    )
    if predict(world, hero, activity)["fear"] < THRESHOLD:
        return gear_def
    gear.worn_by = None
    del world.entities[gear.id]
    return None


def resolve(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity, gear_def: Gear) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1.0
    world.say(
        f"{hero.id} nodded, clipped on the lamp, and the path turned gold in the dark."
    )
    world.say(
        f"Soon {hero.id} found the blinking beacon, and {hero.pronoun('possessive')} {prize.label} stayed safe on {hero.pronoun('possessive')} breast."
    )
    world.say(
        f"{parent.id} laughed in relief as they {gear_def.tail}, and the moon base felt warm again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="badge",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    beacon = world.add(Entity(id="beacon", type="thing", label="beacon"))
    beacon.meters["lost"] = 1.0

    intro(world, hero)
    setup(world, hero, parent, prize, activity)
    world.para()
    world.say(f"One night, the base lights blinked low, and a tiny signal flickered past the window.")
    warning(world, parent, hero, prize, activity)
    tension(world, hero, activity)
    world.para()
    gear_def = offer_gear(world, parent, hero, activity, prize)
    if gear_def:
        resolve(world, hero, parent, prize, activity, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        beacon=beacon,
        trait=trait,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "moon_base": Setting(place="the moon base", outer_space=True, affords={"signal"}),
    "space_dock": Setting(place="the space dock", outer_space=True, affords={"signal"}),
    "cargo_hold": Setting(place="the cargo hold", outer_space=False, affords={"signal"}),
}

ACTIVITIES = {
    "signal": Activity(
        id="signal",
        verb="follow the blinking signal",
        gerund="following the blinking signal",
        rush="run toward the dark tunnel",
        risk="dark",
        hazard="the shadowy gap",
        zone={"torso"},
        keyword="signal",
        tags={"space", "signal", "dark"},
    )
}

PRIZES = {
    "breast_patch": Prize(
        label="breast patch",
        phrase="a tiny silver patch for the breast of the suit",
        type="patch",
        region="torso",
    )
}

GEAR = [
    Gear(
        id="lamp",
        label="a helmet lamp",
        covers={"torso"},
        protects={"dark"},
        prep="turn on the helmet lamp",
        tail="walked back under the bright lamp",
    )
]

NAMES = ["Mina", "Tara", "Pico", "Lio", "Nell"]
TRAITS = ["curious", "brave", "careful", "quiet"]


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
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if signal_at_risk(ACTIVITIES[act_id], prize) and select_gear(ACTIVITIES[act_id], prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space adventure for a child that includes the word "breast".',
        f"Tell a suspenseful story where {f['hero'].id} must {f['activity'].verb} at {f['setting'].place}.",
        f"Write a gentle moon-base story about a child whose {f['prize'].label} stays safe on the breast of a spacesuit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do on the moon base?",
            answer=f"{hero.id} was trying to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the {prize.label} could get lost in the dark during the trip.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel safe in the end?",
            answer=f"A helmet lamp helped {hero.id} see the path, and the {prize.label} stayed safe on the breast of the suit.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moon base?",
            answer="A moon base is a place where people can live and work on the Moon.",
        ),
        QAItem(
            question="What does a helmet lamp do?",
            answer="A helmet lamp shines light forward so you can see in the dark.",
        ),
        QAItem(
            question="What does breast mean in a suit?",
            answer="Breast means the front of the chest on a person or suit.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), protects(G,M), risk_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with suspense and a breast patch.")
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
        raise StoryError("No valid story matches the requested options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
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
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
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
        for p in [StoryParams(place="moon_base", activity="signal", prize="breast_patch", name="Mina", gender="girl", parent="mother", trait="curious")]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
