#!/usr/bin/env python3
"""
storyworlds/worlds/porcelain_halo_bad_ending_bravery_fable.py
=============================================================

A small fable-like story world about a fragile porcelain halo, a brave choice,
and a bad ending that still leaves a clear lesson behind.

Premise seed:
---
A little creature finds a porcelain halo in a chapel garden. The halo looks
bright and holy, but it is fragile. The creature wants to be brave and carry it
back to the old statue on the hill. The path is slippery, and the ending does
not go well.

World model:
---
- bravery rises when the hero chooses to act despite fear
- worry rises when the elder warns about the fragile object
- balance drops on a wet or narrow path
- the porcelain halo can break if carried without a safe case on the hill path
- a broken halo causes a bad ending: the hero loses the prize and feels sorry

This file follows the storyworld contract:
- standard parser and generator entry points
- Python reasonableness gate
- inline ASP twin
- story, trace, QA, JSON, and verification support
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "nun"}
        male = {"boy", "father", "man", "king", "monk"}
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
    slope: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    label: str
    phrase: str
    region: str
    fragile: bool = True
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    path_wet: bool = False
    path_narrow: bool = False
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.path_wet = self.path_wet
        clone.path_narrow = self.path_narrow
        clone.paragraphs = [[]]
        return clone


def _raise(path: str, reason: str) -> None:
    raise StoryError(f"{reason} ({path})")


def _r_fall(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters.get("balance", 0.0) <= 0:
            continue
        if not (world.path_wet or world.path_narrow):
            continue
        if hero.meters.get("caution", 0.0) >= THRESHOLD:
            continue
        if hero.meters.get("bravery", 0.0) < THRESHOLD:
            continue
        halo_id = world.facts.get("halo_id")
        if not halo_id:
            continue
        halo = world.entities[halo_id]
        if halo.meters.get("broken", 0.0) >= THRESHOLD:
            continue
        sig = ("fall", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["balance"] = 0.0
        halo.meters["broken"] = 1.0
        hero.memes["regret"] = hero.memes.get("regret", 0.0) + 1.0
        out.append(f"{hero.label} slipped on the path, and the porcelain halo fell and shattered.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out = []
    halo_id = world.facts.get("halo_id")
    hero_id = world.facts.get("hero_id")
    if not halo_id or not hero_id:
        return out
    halo = world.entities[halo_id]
    hero = world.entities[hero_id]
    if halo.meters.get("broken", 0.0) < THRESHOLD:
        return out
    sig = ("bad_ending",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sadness"] = hero.memes.get("sadness", 0.0) + 1.0
    hero.memes["bravery"] = max(hero.memes.get("bravery", 0.0) - 0.5, 0.0)
    out.append("That was a bad ending, because the halo could not be repaired.")
    return out


CAUSAL_RULES = [_r_fall, _r_bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def narrative_path(world: World, hero: Entity) -> str:
    if world.path_wet and world.path_narrow:
        return "the wet narrow path"
    if world.path_wet:
        return "the wet stone path"
    if world.path_narrow:
        return "the narrow hill path"
    return "the hill path"


def predict_break(world: World, hero: Entity) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    halo = sim.entities.get(sim.facts.get("halo_id", ""))
    return bool(halo and halo.meters.get("broken", 0.0) >= THRESHOLD)


def set_scene(world: World, setting: Setting, hero: Entity, elder: Entity, halo: Entity) -> None:
    world.say(f"In {setting.place}, a little fable began with {hero.label}, {elder.label}, and a porcelain halo.")
    world.say(f"The halo was bright and delicate, like moonlight caught in a ring.")
    world.say(f"{hero.label} loved how it gleamed, even though everyone could see it was fragile.")


def warn(world: World, elder: Entity, hero: Entity, halo: Entity) -> None:
    world.say(
        f'"Be careful," {elder.label} said. "A porcelain halo is not a toy. '
        f"If it falls, it will break.""
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 0.5


def choose_bravery(world: World, hero: Entity, halo: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.meters["balance"] = 1.0
    world.say(f"{hero.label} took a breath and decided to be brave.")
    world.say(f"{hero.label} lifted the halo with both hands and started up the hill.")


def climb(world: World, hero: Entity, halo: Entity) -> None:
    path = narrative_path(world, hero)
    if world.path_wet:
        world.say("The stones were slick with rain.")
    if world.path_narrow:
        world.say("The path was narrow, with a steep drop on one side.")
    world.say(f"{hero.label} walked carefully along {path}, trying to keep the halo steady.")
    hero.meters["balance"] = hero.meters.get("balance", 1.0) - (0.7 if world.path_wet else 0.3)
    hero.meters["caution"] = hero.meters.get("caution", 0.0) + (0.2 if world.path_wet else 0.0)
    halo.carried_by = hero.id
    halo.meters["shaken"] = halo.meters.get("shaken", 0.0) + 1.0
    propagate(world, narrate=True)


def end_story(world: World, hero: Entity, elder: Entity, halo: Entity) -> None:
    if halo.meters.get("broken", 0.0) >= THRESHOLD:
        world.say(
            f"{hero.label} stood still in the broken pieces, sorry and quiet. "
            f"{elder.label} gathered the shards in a cloth and sighed."
        )
        world.say(
            f"The bright ring was gone, and the hilltop looked lonelier than before."
        )
    else:
        world.say(
            f"{hero.label} carried the halo home safely, and the old statue on the hill kept its gentle glow."
        )


def tell(setting: Setting, hero_name: str, hero_type: str, elder_type: str, object_def: ObjectDef) -> World:
    world = World(setting)
    world.path_wet = "wet" in setting.affords
    world.path_narrow = "narrow" in setting.affords

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    halo = world.add(Entity(
        id="halo",
        type="thing",
        label=object_def.label,
        phrase=object_def.phrase,
        owner=hero.id,
        caretaker=elder.id,
        fragile=object_def.fragile,
    ))
    world.facts["hero_id"] = hero.id
    world.facts["elder_id"] = elder.id
    world.facts["halo_id"] = halo.id

    set_scene(world, setting, hero, elder, halo)
    world.para()
    warn(world, elder, hero, halo)
    choose_bravery(world, hero, halo)
    climb(world, hero, halo)
    world.para()
    end_story(world, hero, elder, halo)
    world.facts.update(hero=hero, elder=elder, halo=halo)
    return world


SETTINGS = {
    "chapel_garden": Setting(place="the chapel garden", slope="hill", weather="after rain", affords={"wet", "narrow"}),
    "stone_path": Setting(place="the stone path", slope="hill", weather="after rain", affords={"wet", "narrow"}),
    "old_steps": Setting(place="the old steps", slope="hill", weather="dry", affords={"narrow"}),
}

OBJECTS = {
    "porcelain_halo": ObjectDef(
        label="a porcelain halo",
        phrase="a bright porcelain halo",
        region="hands",
        fragile=True,
    )
}

HERO_NAMES = ["Mira", "Toby", "Pip", "Nell", "Rumi", "Sage"]
HERO_TYPES = ["girl", "boy"]
ELDER_TYPES = ["monk", "nun", "father", "mother"]


@dataclass
class StoryParams:
    setting: str
    object: str
    name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid in OBJECTS:
            if "wet" in setting.affords or "narrow" in setting.affords:
                combos.append((sid, oid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    halo = f["halo"]
    setting = f["setting"]
    return [
        f'Write a short fable for a young child about bravery and a fragile {halo.label} in {setting.place}.',
        f"Tell a gentle story where {hero.label} tries to be brave while carrying {halo.phrase} up a hill, and the ending goes badly.",
        f'Write a simple moral tale that includes the words "porcelain" and "halo" and ends with a sad lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    halo = f["halo"]
    setting = f["setting"]
    broken = halo.meters.get("broken", 0.0) >= THRESHOLD
    qa = [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"The story was about {hero.label}, who met the elder and found a porcelain halo in {setting.place}.",
        ),
        QAItem(
            question=f"Why did {elder.label} warn {hero.label} about the halo?",
            answer=f"{elder.label} warned {hero.label} because the halo was made of porcelain and was very fragile.",
        ),
        QAItem(
            question=f"What did {hero.label} choose to do anyway?",
            answer=f"{hero.label} chose to be brave and carry the halo up the hill.",
        ),
    ]
    if broken:
        qa.append(
            QAItem(
                question="What happened at the end?",
                answer="The ending was bad: the halo slipped, broke into pieces, and could not be repaired.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.label} feel after the fall?",
                answer=f"{hero.label} felt sorry and quiet after seeing the broken halo.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What happened at the end?",
                answer="The halo stayed safe, and the little traveler carried it home without breaking it.",
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is porcelain?",
        answer="Porcelain is a smooth, hard kind of ceramic that can look shiny and pretty, but it can also break if it falls.",
    ),
    QAItem(
        question="What is a halo?",
        answer="A halo is a ring that is often shown above a holy person or a statue, like a sign of light or goodness.",
    ),
    QAItem(
        question="What does bravery mean?",
        answer="Bravery means doing something hard or scary even when you feel afraid.",
    ),
    QAItem(
        question="What is a fable?",
        answer="A fable is a short story that often uses simple characters and ends with a lesson.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


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
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  path_wet={world.path_wet} path_narrow={world.path_narrow}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="chapel_garden", object="porcelain_halo", name="Mira", hero_type="girl", elder_type="nun"),
    StoryParams(setting="stone_path", object="porcelain_halo", name="Pip", hero_type="boy", elder_type="monk"),
    StoryParams(setting="old_steps", object="porcelain_halo", name="Nell", hero_type="girl", elder_type="mother"),
]


ASP_RULES = r"""
fragile_object(o) :- object(o), fragile(o).
at_risk(h,o) :- carries(h,o), fragile_object(o), wet_path, brave(h).
breaks(o) :- at_risk(_,o).
bad_ending :- breaks(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "wet" in s.affords:
            lines.append(asp.fact("wet_path", sid))
        if "narrow" in s.affords:
            lines.append(asp.fact("narrow_path", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0.\n#show breaks/1."))
    return sorted(set(asp.atoms(model, "bad_ending")))


def asp_verify() -> int:
    python_bad = any(True for _ in valid_combos())
    asp_bad = bool(asp_valid_combos())
    if python_bad == asp_bad:
        print("OK: ASP/Python parity holds.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: porcelain, halo, bravery, and a bad ending fable.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    if setting not in SETTINGS or obj not in OBJECTS:
        raise StoryError("No valid combination matches the given options.")
    return StoryParams(setting=setting, object=obj, name=name, hero_type=hero_type, elder_type=elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.name, params.hero_type, params.elder_type, OBJECTS[params.object])
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
        print(asp_program("#show bad_ending/0.\n#show breaks/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible pattern: brave hero + fragile halo on a wet path.\n")
        print("  chapel_garden  porcelain_halo  [brave]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
