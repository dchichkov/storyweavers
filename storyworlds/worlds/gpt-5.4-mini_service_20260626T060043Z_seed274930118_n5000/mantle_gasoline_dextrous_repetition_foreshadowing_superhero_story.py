#!/usr/bin/env python3
"""
storyworlds/worlds/mantle_gasoline_dextrous_repetition_foreshadowing_superhero_story.py
======================================================================================

A small superhero story world about a young hero, a precious mantle, a gasoline
hazard, and a dextrous rescue.

The story premise is built from a tiny source tale:
- a child hero proudly wears a mantle
- a gasoline spill threatens the city during a rescue
- repeated warnings foreshadow that sparks would make the danger worse
- a dextrous helper and a careful plan turn the problem into a safe save

This script keeps the world classical and simulation-driven:
physical meters track fire, spill, damage, and safety;
emotional memes track pride, worry, courage, and trust.

It also includes an inline ASP twin and a Python reasonableness gate so the
compatible stories are checked twice.
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    omen: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


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
        self.facts: dict = {}
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
        return any(e.protective and region in getattr(e, "covers", set()) for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def clone_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.paragraphs = [[]]
    clone.zone = set(world.zone)
    return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            outs = rule.apply(world)
            if outs:
                changed = True
                produced.extend(outs)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Rule:
    name: str
    apply: callable


def _r_heat_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Hero")
    spill = world.entities.get("Spill")
    if not hero or not spill:
        return out
    if hero.meters.get("near_spill", 0) < THRESHOLD:
        return out
    if spill.meters.get("gasoline", 0) < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append("A sharp gasoline smell drifted through the alley, and that made the air feel dangerous.")
    return out


def _r_spark_threat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Hero")
    spark = world.entities.get("Spark")
    spill = world.entities.get("Spill")
    if not hero or not spark or not spill:
        return out
    if hero.meters.get("near_spill", 0) < THRESHOLD:
        return out
    if spark.meters.get("lit", 0) < THRESHOLD:
        return out
    if spill.meters.get("gasoline", 0) < THRESHOLD:
        return out
    sig = ("threat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    out.append("A tiny spark near the gasoline could have made a terrible blaze.")
    return out


def _r_hide_mantle(world: World) -> list[str]:
    out: list[str] = []
    mantle = world.entities.get("Mantle")
    hero = world.entities.get("Hero")
    if not mantle or not hero:
        return out
    if mantle.worn_by != hero.id:
        return out
    if world.zone and hero.meters.get("near_spill", 0) >= THRESHOLD:
        sig = ("mantle_safe",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The mantle fluttered behind the hero like a bright promise.")
    return out


CAUSAL_RULES = [
    Rule("heat_risk", _r_heat_risk),
    Rule("spark_threat", _r_spark_threat),
    Rule("hide_mantle", _r_hide_mantle),
]


def risk_prediction(world: World) -> dict:
    sim = clone_world(world)
    hero = sim.get("Hero")
    spill = sim.get("Spill")
    spark = sim.get("Spark")
    hero.meters["near_spill"] = 1
    spark.meters["lit"] = 1
    spill.meters["gasoline"] = 1
    propagate(sim, narrate=False)
    return {
        "danger": hero.memes.get("fear", 0) > 0 or hero.memes.get("worry", 0) > 0,
        "blaze": spark.meters.get("lit", 0) >= THRESHOLD and spill.meters.get("gasoline", 0) >= THRESHOLD,
    }


def setting_line(setting: Setting) -> str:
    return {
        "city_rooftop": "The city rooftop stood high above the street, with wind tugging at every cape.",
        "alley": "The alley below the neon signs was narrow and full of puddles and echoes.",
        "museum": "The museum hall was quiet, with polished floors and long shadows.",
    }.get(setting.place, f"{setting.place.capitalize()} waited under a bright sky.")


def hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a young {hero.type} superhero with a brave heart and a careful mind.")
    world.say(f"{hero.pronoun('possessive').capitalize()} mantle was the one thing {hero.pronoun('subject')} never forgot to wear.")


def foreshadow(world: World, hero: Entity, hazard: Hazard) -> None:
    world.say(f"Earlier, {hero.id} had noticed {hazard.omen}, and {hero.pronoun('subject')} remembered that warning now.")
    world.say(f"Again and again, {hero.id} told {hero.pronoun('object')}self, \"No sparks near gasoline.\"")


def scene_setup(world: World, hero: Entity, helper: Entity, prize: Entity, hazard: Hazard) -> None:
    world.say(setting_line(world.setting))
    world.say(f"{hero.id} had come with {helper.id} to keep the city safe.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, but {hazard.keyword} was the day’s trouble.")
    world.para()


def discover(world: World, hero: Entity, hazard: Hazard, prize: Entity) -> None:
    hero.meters["near_spill"] = 1
    world.zone = {"ground", "hands"}
    world.say(f"Then {hero.id} found {hazard.danger} near the broken crate.")
    world.say(f"It smelled like gasoline, and it was creeping close to {prize.phrase}.")
    propagate(world)


def warn_twice(world: World, hero: Entity, hazard: Hazard) -> None:
    world.say(f"\"No spark can touch that gasoline,\" {hero.id} said.")
    world.say(f"\"Not once, and not even by accident,\" {hero.id} said again.")
    world.say(f"The repeated warning made the danger feel even more real.")
    propagate(world)


def dextrous_plan(world: World, hero: Entity, helper: Entity, gear: Gear, hazard: Hazard) -> None:
    helper.meters["dextrous"] = 1
    world.say(f"{helper.id} was dextrous with small tools, so {helper.pronoun('subject')} knew just what to do.")
    world.say(f"\"Let's {gear.prep},\" {helper.id} said.")
    world.say(f"{hero.id} nodded, because {gear.label} would block the danger without slowing the rescue.")
    gear_ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.label,
        protective=True,
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id
    world.say(f"{hero.id} slipped on {gear.label} and moved more safely toward the spill.")
    world.para()


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, gear: Gear) -> None:
    hero.meters["near_spill"] = 0
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["worry"] = 0
    world.say(f"With {gear.label} on, {hero.id} could reach the crate without fear of the gasoline.")
    world.say(f"{helper.id} steadied the loose pipe while {hero.id} sealed the leak.")
    world.say(f"At last, the city was safe, {prize.phrase} was untouched, and {hero.pronoun('possessive')} mantle still swept proudly through the wind.")


def tell(setting: Setting, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type="hero", label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type="hero", label=helper_name))
    mantle = world.add(Entity(id="Mantle", kind="thing", type="mantle", label="mantle", phrase="the bright mantle", owner=hero.id, worn_by=hero.id))
    prize = world.add(Entity(id="Beacon", kind="thing", type="beacon", label="beacon", phrase="the city beacon", caretaker=helper.id))
    spill = world.add(Entity(id="Spill", kind="thing", type="spill", label="spill", phrase="the gasoline spill"))
    spark = world.add(Entity(id="Spark", kind="thing", type="spark", label="spark", phrase="a tiny spark"))
    spark.meters["lit"] = 1
    spill.meters["gasoline"] = 1
    hero.meters["near_spill"] = 0

    hazard = HAZARDS["gasoline"]

    hero_intro(world, hero)
    world.say(f"{hero.id} liked how the mantle made the hero look ready for any rescue.")
    world.say(f"{helper.id} was a dextrous sidekick who could twist wires and open locks with quick fingers.")
    world.say("That was important, because the city was never calm for long.")
    world.para()

    scene_setup(world, hero, helper, prize, hazard)
    foreshadow(world, hero, hazard)
    discover(world, hero, hazard, prize)
    warn_twice(world, hero, hazard)
    dextrous_plan(world, hero, helper, GEAR["rubber_gloves"], hazard)
    resolve(world, hero, helper, prize, GEAR["rubber_gloves"])

    world.facts.update(
        hero=hero,
        helper=helper,
        mantle=mantle,
        prize=prize,
        spill=spill,
        spark=spark,
        hazard=hazard,
        gear=GEAR["rubber_gloves"],
    )
    return world


SETTINGS = {
    "rooftop": Setting(place="city_rooftop", affords={"gasoline"}),
    "alley": Setting(place="alley", affords={"gasoline"}),
    "museum": Setting(place="museum", affords={"gasoline"}),
}

HAZARDS = {
    "gasoline": Hazard(
        id="gasoline",
        verb="deal with the gasoline spill",
        gerund="dealing with the gasoline spill",
        rush="dash toward the spill",
        danger="a dark puddle of gasoline",
        omen="the sharp smell of gasoline under the stairs",
        keyword="gasoline",
        tags={"gasoline", "fire", "warning"},
    )
}

GEAR = {
    "rubber_gloves": Gear(
        id="rubber_gloves",
        label="rubber gloves",
        covers={"hands"},
        guards={"gasoline"},
        prep="put on my rubber gloves first",
        tail="put on the rubber gloves and worked carefully",
        plural=True,
    )
}

PRIZES = {
    "beacon": Prize(
        id="beacon",
        label="beacon",
        phrase="the city beacon",
        region="torso",
    )
}

GIRL_NAMES = ["Nova", "Iris", "Mina", "Luna", "Zara", "Ada"]
BOY_NAMES = ["Jett", "Miles", "Theo", "Arlo", "Finn", "Noel"]
HELPER_NAMES = ["Spark", "Quill", "Pip", "Nico", "Vale", "Tess"]
TRAITS = ["bold", "curious", "brisk", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for hazard in setting.affords:
            if hazard in HAZARDS:
                combos.append((place, hazard, "beacon"))
    return combos


@dataclass
class StoryParams:
    place: str
    hazard: str
    prize: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes "mantle", "gasoline", and "dextrous".',
        f"Tell a brave rescue story where {f['hero'].label} and {f['helper'].label} handle a gasoline spill without losing the mantle.",
        f"Write a gentle action story with foreshadowing, repetition, and a careful fix for a gasoline danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    hazard: Hazard = f["hazard"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"Who wore the mantle in the story?",
            answer=f"{hero.id} wore the mantle and hurried into the rescue.",
        ),
        QAItem(
            question=f"What made the hero worry near the spill?",
            answer=f"The gasoline made the danger feel serious, because a spark could have made a blaze.",
        ),
        QAItem(
            question=f"How did the dextrous helper help?",
            answer=f"{helper.id} used careful, dextrous hands and rubber gloves to help seal the spill safely.",
        ),
        QAItem(
            question=f"What stayed safe at the end?",
            answer=f"The city beacon stayed untouched, and the mantle still swept proudly behind {hero.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gasoline?",
            answer="Gasoline is a fuel that can burn very easily, so it must be handled carefully.",
        ),
        QAItem(
            question="What does dextrous mean?",
            answer="Dextrous means skillful with your hands, especially when doing careful small tasks.",
        ),
        QAItem(
            question="What is a mantle?",
            answer="A mantle is a cape or long covering worn over the shoulders, like a superhero costume piece.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- affords(S,_).
prize(P) :- worn_on(P,_).
hazard(H) :- danger(H,_).

at_risk(H,P) :- hazard(H), worn_on(P,R), splashes(H,R).
compatible_fix(G,H,P) :- gear(G), at_risk(H,P), guards(G,M), danger_kind(H,M), covers(G,R), worn_on(P,R).
valid_story(S,H,P) :- affords(S,H), at_risk(H,P), compatible_fix(_,H,P).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("danger", hid, h.danger))
        lines.append(asp.fact("danger_kind", hid, "gasoline"))
        for t in sorted(h.tags):
            lines.append(asp.fact("tag", hid, t))
        lines.append(asp.fact("splashes", hid, "ground"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("worn_on", pid, p.region))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_ok(place: str, hazard: str, prize: str) -> bool:
    return (place, hazard, prize) in valid_combos()


def select_gear(hazard: Hazard, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if hazard.keyword in gear.guards and prize.region in gear.covers:
            return gear
    return None


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Story world: mantle, gasoline, and a dextrous rescue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.hazard and args.prize and not reasonableness_ok(args.place, args.hazard, args.prize):
        raise StoryError("No valid story matches those explicit choices.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, hazard, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hazard=hazard, prize=prize, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.helper)
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
    StoryParams(place="rooftop", hazard="gasoline", prize="beacon", name="Nova", helper="Pip", trait="bold"),
    StoryParams(place="alley", hazard="gasoline", prize="beacon", name="Jett", helper="Tess", trait="curious"),
    StoryParams(place="museum", hazard="gasoline", prize="beacon", name="Luna", helper="Quill", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
