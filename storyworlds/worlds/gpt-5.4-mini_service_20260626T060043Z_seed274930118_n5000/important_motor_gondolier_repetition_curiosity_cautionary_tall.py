#!/usr/bin/env python3
"""
storyworlds/worlds/important_motor_gondolier_repetition_curiosity_cautionary_tall.py
====================================================================================

A small tall-tale storyworld about an important delivery, a motorized gondola,
repetition, curiosity, and caution.

Seed image:
- A gondolier carries something important across a winding waterway.
- A curious helper keeps asking why the rules matter.
- A cautionary warning prevents a mishap with the motor.
- Repetition gives the tale its tall, rhythmic feel.

The world is intentionally compact and constraint-checked:
- if the chosen delivery is not actually at risk, the story is rejected
- if no reasonable caution can fix the problem, the story is rejected
- the ASP twin mirrors the Python reasonableness gate
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
            self.meters = {"wet": 0.0, "damage": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "curiosity": 0.0, "caution": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle", "gondolier"}
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
    tag: str
    affords: set[str]


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
    keyword: str
    refrain: str
    tags: set[str]


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    importance: str = "important"
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_splash(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mission_key in world.facts.get("mission_tags", set()):
            if actor.meters["wet"] < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.worn_by != actor.id:
                    continue
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("splash", item.id, mission_key)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["wet"] += 1
                item.meters["damage"] += 1
                out.append(f"{actor.id}'s {item.label} got soaked by the water.")
    return out


def _r_work(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["damage"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["work"] += 1
        out.append(f"That would mean extra work for {carer.id}.")
    return out


CAUSAL_RULES = [Rule("splash", _r_splash), Rule("work", _r_work)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(mission: Mission, cargo: Cargo) -> bool:
    return cargo.region in mission.zone


def select_gear(mission: Mission, cargo: Cargo) -> Optional[Gear]:
    for g in GEAR:
        if mission.risk in g.guards and cargo.region in g.covers:
            return g
    return None


def predict_risk(world: World, hero: Entity, mission: Mission, cargo_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), mission, narrate=False)
    cargo = sim.entities[cargo_id]
    return {"damaged": cargo.meters["damage"] >= THRESHOLD, "work": sim.get(world.facts["helper"].id).meters["work"] if "helper" in world.facts else 0}


def _do_mission(world: World, hero: Entity, mission: Mission, narrate: bool = True) -> None:
    world.zone = set(mission.zone)
    hero.meters["wet"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=narrate)


def story_intro(world: World, hero: Entity) -> None:
    world.say(f"In the river town of {world.setting.place}, {hero.id} was a {hero.type} gondolier with a heart as wide as the water.")


def story_repetition(world: World, mission: Mission) -> None:
    world.say(f"{mission.refrain}, the old folks said, and they said it twice more for luck: {mission.refrain}, {mission.refrain}.")


def story_curiosity(world: World, helper: Entity) -> None:
    helper.memes["curiosity"] += 1
    world.say(f"{helper.id}, a curious little helper, kept asking why the motor had to be watched so carefully.")


def story_caution(world: World, hero: Entity, helper: Entity, mission: Mission, cargo: Cargo) -> None:
    helper.memes["caution"] += 1
    world.say(f"{hero.id} answered, \"Because the water is a sneaky thing, and a motor never likes a rope in the wrong place.\"")
    world.say(f"\"Easy now,\" {hero.id} said. \"Slow hands make safe trips, and safe trips carry important things home.\"")


def story_warning(world: World, hero: Entity, cargo: Cargo, mission: Mission) -> bool:
    pred = predict_risk(world, hero, mission, cargo.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(f"\"If we rush, {cargo.label} may get {mission.risk},\" {hero.id} warned, \"and that would be a sorry thing indeed.\"")
    return True


def story_fix(world: World, hero: Entity, helper: Entity, mission: Mission, cargo: Cargo) -> Optional[Gear]:
    gear_def = select_gear(mission, cargo)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_risk(world, hero, mission, cargo.id)["damaged"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{helper.id} fetched {gear.label}, and {hero.id} set it in place before the motor could start its grumble.")
    return gear


def story_finish(world: World, hero: Entity, helper: Entity, mission: Mission, cargo: Cargo, gear: Gear) -> None:
    hero.memes["worry"] = 0
    hero.memes["joy"] += 1
    world.say(f"Then, slow as a hymn and steady as a saint's promise, they went on.")
    world.say(f"{hero.id} kept the boat true, {helper.id} kept watch, and {cargo.label} stayed dry and important all the way across.")
    world.say(f"When they arrived, the whole town said the trip was tall enough to tell twice, and they did.")


def tell(setting: Setting, mission: Mission, cargo_cfg: Cargo, hero_name: str = "Gino", helper_name: str = "Mina") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="gondolier"))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl"))
    cargo = world.add(Entity(id="cargo", type=cargo_cfg.type, label=cargo_cfg.label, phrase=cargo_cfg.phrase, caretaker=hero.id, region=cargo_cfg.region, plural=cargo_cfg.plural))
    world.facts.update(hero=hero, helper=helper, cargo=cargo, mission=mission, mission_tags=set(mission.tags))

    story_intro(world, hero)
    world.say(f"Today he had one job and one job only: carry {cargo.importance} {cargo.label} across {setting.place}.")
    story_repetition(world, mission)
    world.para()
    story_curiosity(world, helper)
    world.say(f"{helper.id} wanted to know how a little motorboat could seem so grand, but {hero.id} only grinned and patted the rail.")
    world.say(f"\"It is not size that matters,\" he said, \"it is the way a boat keeps its promise.\"")
    world.para()
    world.say(f"At the water's edge, the wind worried the ropes and the motor gave a low, warning hum.")
    story_warning(world, hero, cargo, mission)
    world.say(f"{hero.id} pointed to the {mission.keyword} and told {helper.id} not to lean near the spinning part.")
    story_caution(world, hero, helper, mission, cargo)
    gear = story_fix(world, hero, helper, mission, cargo)
    if gear is None:
        raise StoryError("No reasonable caution could keep the cargo safe.")
    world.para()
    story_finish(world, hero, helper, mission, cargo, gear)
    world.facts["gear"] = gear
    return world


SETTINGS = {
    "canal_town": Setting(place="the canal town", tag="canal", affords={"delivery", "crossing"}),
    "river_bend": Setting(place="the river bend", tag="river", affords={"delivery", "crossing"}),
    "harbor_lane": Setting(place="the harbor lane", tag="harbor", affords={"delivery", "crossing"}),
}

MISSIONS = {
    "delivery": Mission(
        id="delivery",
        verb="deliver the parcel",
        gerund="delivering parcels",
        rush="dash through the water",
        risk="wet",
        zone={"torso"},
        weather="windy",
        keyword="motor",
        refrain="Slow the motor and mind the rope",
        tags={"important", "motor"},
    ),
    "crossing": Mission(
        id="crossing",
        verb="carry the note",
        gerund="crossing the water",
        rush="rush across the channel",
        risk="damage",
        zone={"torso"},
        weather="foggy",
        keyword="motor",
        refrain="Easy hands and a careful motor",
        tags={"important", "motor"},
    ),
}

CARGOES = {
    "parcel": Cargo(id="parcel", label="an important parcel", phrase="an important parcel wrapped in wax paper", type="parcel", region="torso"),
    "ledger": Cargo(id="ledger", label="an important ledger", phrase="an important ledger tied with twine", type="ledger", region="torso"),
    "lantern": Cargo(id="lantern", label="an important lantern", phrase="an important lantern with a glass belly", type="lantern", region="torso"),
}

GEAR = [
    Gear(id="cover", label="a canvas cover", covers={"torso"}, guards={"wet", "damage"}, prep="spread a canvas cover over the cargo", tail="kept the cargo under the canvas cover"),
    Gear(id="shield", label="a wind shield", covers={"torso"}, guards={"wet"}, prep="raise the wind shield first", tail="glided on with the wind shield set tight"),
]

HERO_NAMES = ["Gino", "Nico", "Piero", "Rocco", "Timo"]
HELPER_NAMES = ["Mina", "Lola", "Pia", "Tessa", "Nora"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    cargo: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for m, mission in MISSIONS.items():
            for c, cargo in CARGOES.items():
                if prize_at_risk(mission, cargo) and select_gear(mission, cargo):
                    out.append((s, m, c))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale about an important motor gondolier, repetition, curiosity, and caution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    if args.mission and args.cargo:
        if not (prize_at_risk(MISSIONS[args.mission], CARGOES[args.cargo]) and select_gear(MISSIONS[args.mission], CARGOES[args.cargo])):
            raise StoryError("No story: that cargo and mission do not create a reasonable cautionary problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mission is None or c[1] == args.mission)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, mission, cargo = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        mission=mission,
        cargo=cargo,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale for young children about a gondolier named {f['hero'].id}, an important {f['cargo'].label}, and a motor that must be handled with care.",
        f"Tell a story with repetition, curiosity, and caution where {f['helper'].id} keeps asking questions while {f['hero'].id} delivers {f['cargo'].phrase}.",
        f"Write a small river adventure that says {f['mission'].refrain']}? No, {f['mission'].refrain']}! and ends safely with the cargo dry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, cargo, mission = f["hero"], f["helper"], f["cargo"], f["mission"]
    return [
        QAItem(
            question=f"Who was carrying the important cargo across {world.setting.place}?",
            answer=f"{hero.id} the gondolier was carrying {cargo.label} across {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {helper.id} keep asking questions about the motor?",
            answer=f"{helper.id} was curious, and {hero.id} kept warning that a motor needs careful hands.",
        ),
        QAItem(
            question=f"What made the story feel like a tall tale?",
            answer=f"The repeated refrain and the grand, rhythmic way {hero.id} spoke made it feel like a tall tale.",
        ),
        QAItem(
            question=f"How did they keep {cargo.label} safe?",
            answer=f"They used {f['gear'].label} and moved slowly, so the cargo stayed dry and important all the way across.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gondolier?",
            answer="A gondolier is a person who rows or steers a gondola or similar boat, often on narrow water.",
        ),
        QAItem(
            question="Why should people be careful around a motor on a boat?",
            answer="A motor has moving parts and can splash or tangle things, so careful hands help keep people and cargo safe.",
        ),
        QAItem(
            question="What does repetition do in a story?",
            answer="Repetition repeats words or phrases on purpose, so a story can sound memorable, musical, or extra grand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(M, C) :- mission(M), cargo(C), cargo_region(C, R), mission_zone(M, R).
protects(G, M, C) :- gear(G), prize_at_risk(M, C), mission_risk(M, R), guards(G, R), cargo_region(C, Z), covers(G, Z).
has_fix(M, C) :- protects(_, M, C).
valid(S, M, C) :- setting(S), mission(M), cargo(C), affords(S, M), prize_at_risk(M, C), has_fix(M, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", sid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_risk", mid, m.risk))
        for r in sorted(m.zone):
            lines.append(asp.fact("mission_zone", mid, r))
    for cid, c in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_region", cid, c.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
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
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(p - a))
    print("only in clingo:", sorted(a - p))
    return 1


def explain_rejection(mission: Mission, cargo: Cargo) -> str:
    if not prize_at_risk(mission, cargo):
        return f"(No story: {cargo.label} is not at risk in this mission.)"
    return f"(No story: no gear in this world can safely protect {cargo.label} from that risk.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISSIONS[params.mission], CARGOES[params.cargo], params.hero_name, params.helper_name)
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s, m, c in sorted(valid_combos()):
            params = StoryParams(s, m, c, random.choice(HERO_NAMES), random.choice(HELPER_NAMES), seed=base_seed)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
