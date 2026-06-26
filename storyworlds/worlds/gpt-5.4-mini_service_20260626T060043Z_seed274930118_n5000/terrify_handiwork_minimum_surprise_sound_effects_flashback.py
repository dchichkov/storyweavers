#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/terrify_handiwork_minimum_surprise_sound_effects_flashback.py
====================================================================================================

A small mythic story world about a young craftsperson, a frightened village, and a
surprising repair whose sounds echo back a hidden memory.

Premise:
- A child learns a minimum, careful act of handiwork from an elder.
- A sudden surprise terrifies the child and the people nearby.
- Sound effects in the world reveal that the danger is not a monster, but a broken
  shrine needing a repair.
- A flashback explains why the child recognizes the pattern.
- The ending shows the repair complete, the fear gone, and the world changed.

The world is grounded in meters and memes:
- meters track tangible state: breakage, repair, noise, distance, light, and safety.
- memes track feelings: fear, courage, surprise, awe, relief, pride, memory.

The style aims for a short myth: concrete, child-facing, and ceremonial, with a
clear beginning, middle turn, and ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core registries
# ---------------------------------------------------------------------------

SETTING_NAMES = [
    "the stone valley",
    "the river shrine",
    "the hill village",
    "the moon forge",
    "the cinder temple",
]

ROLE_NAMES = [
    "apprentice",
    "child smith",
    "lantern keeper",
    "stone tender",
    "drum helper",
]

MATERIALS = [
    "bronze",
    "oak",
    "river clay",
    "black iron",
    "white stone",
]

DANGERS = [
    "a cracking pillar",
    "a loose idol",
    "a falling bell",
    "a split drum",
    "a broken gate chain",
]

SOUND_EFFECTS = [
    "CLANG",
    "THUMM",
    "KRAK",
    "HUMM",
    "TINK",
    "WHOOF",
]

SURPRISES = [
    "a hidden tremor",
    "a sudden echo",
    "a flare of sparks",
    "a moonlit shadow",
    "a burst of thunder",
]

FLASHBACK_TRIGGERS = [
    "the smell of hot stone",
    "the shape of the broken crack",
    "the old silver hammer",
    "the ringing in the air",
]

NAMES = [
    "Ari", "Mira", "Niko", "Sela", "Tavi", "Lena", "Oren", "Iva", "Kora", "Pavo"
]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    setting: str
    role: str
    material: str
    danger: str
    name: str
    seed: Optional[int] = None


@dataclass
class Setting:
    name: str
    sacred: bool = True
    noise_sensitive: bool = True
    affords_repair: bool = True


@dataclass
class Craft:
    label: str
    verb: str
    gerund: str
    tool: str
    sound: str
    requires: str
    minimum_step: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# World configuration
# ---------------------------------------------------------------------------

SETTINGS = {
    "valley": Setting("the stone valley"),
    "shrine": Setting("the river shrine"),
    "village": Setting("the hill village"),
    "forge": Setting("the moon forge"),
    "temple": Setting("the cinder temple"),
}

CRAFTS = {
    "mend": Craft(
        label="handiwork",
        verb="mend",
        gerund="mending",
        tool="a small chisel",
        sound="TINK",
        requires="a clean crack",
        minimum_step="only the minimum needed",
    ),
    "seal": Craft(
        label="handiwork",
        verb="seal",
        gerund="sealing",
        tool="a clay brush",
        sound="HUMM",
        requires="a wide seam",
        minimum_step="only the thin line needed",
    ),
    "retie": Craft(
        label="handiwork",
        verb="retie",
        gerund="tying",
        tool="a woven cord",
        sound="THUMM",
        requires="a loose gate chain",
        minimum_step="only the knot needed",
    ),
}

DANGERS_BY_SETTING = {
    "valley": "a cracking pillar",
    "shrine": "a loose idol",
    "village": "a falling bell",
    "forge": "a broken gate chain",
    "temple": "a split drum",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
craft(C) :- craft_name(C).
danger(D) :- danger_name(D).

compatible(S, C, D) :- setting(S), craft(C), danger(D),
                       fixes(C, D), occurs_in(D, S).
story(S, C, D) :- compatible(S, C, D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
    for key in CRAFTS:
        lines.append(asp.fact("craft_name", key))
    for setting, danger in DANGERS_BY_SETTING.items():
        lines.append(asp.fact("danger_name", danger.replace(" ", "_")))
        lines.append(asp.fact("occurs_in", danger.replace(" ", "_"), setting))
    for key, craft in CRAFTS.items():
        if key == "mend":
            lines.append(asp.fact("fixes", key, "a_cracking_pillar"))
        elif key == "seal":
            lines.append(asp.fact("fixes", key, "a_loose_idol"))
        elif key == "retie":
            lines.append(asp.fact("fixes", key, "a_broken_gate_chain"))
    # normalize danger symbols
    fixed = []
    for setting, danger in DANGERS_BY_SETTING.items():
        fixed.append(asp.fact("danger_name", danger.replace(" ", "_")))
        fixed.append(asp.fact("occurs_in", danger.replace(" ", "_"), setting))
    return "\n".join(lines + fixed)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_story_triples() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))

def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_story_triples())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------

def normalize_danger(d: str) -> str:
    return d.replace(" ", "_")

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for craft in CRAFTS:
            danger = DANGERS_BY_SETTING[setting]
            if craft == "mend" and danger == "a cracking pillar":
                combos.append((setting, craft, danger))
            if craft == "seal" and danger == "a loose idol":
                combos.append((setting, craft, danger))
            if craft == "retie" and danger == "a broken gate chain":
                combos.append((setting, craft, danger))
    return combos

def reasonableness_gate(setting: str, craft: str, danger: str) -> None:
    if (setting, craft, danger) not in valid_combos():
        raise StoryError(
            f"(No story: {craft} does not naturally solve {danger} in {setting}. "
            f"The repair would not feel like true handiwork at the minimum needed size.)"
        )

def predict_surprise(world: World, hero: Entity, craft: Craft, danger: Entity) -> bool:
    sim = world.copy()
    _attempt_repair(sim, sim.get(hero.id), craft, danger.id, narrate=False)
    return danger.meters.get("broken", 0) <= 0.0

def _attempt_repair(world: World, hero: Entity, craft: Craft, danger_id: str, narrate: bool = True) -> None:
    danger = world.get(danger_id)
    if danger.meters.get("broken", 0) <= 0:
        return
    danger.meters["broken"] = 0
    danger.meters["repair"] = 1
    hero.meters["skill"] = hero.meters.get("skill", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    if narrate:
        world.say(f"{hero.id} worked with {craft.minimum_step}, and {craft.sound} sounded in the still air.")

def flashback_line(trigger: str, hero: Entity, elder: Entity, craft: Craft) -> str:
    return (
        f"At {trigger}, {hero.id} remembered the elder's lesson: "
        f'"Use {craft.minimum_step}, because good handiwork does not fight the crack; it listens to it."'
    )

def tell(setting: Setting, craft: Craft, danger_label: str, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type="child",
        label="the young helper",
        meters={"distance": 0, "safety": 0},
        memes={"fear": 0, "surprise": 0, "courage": 0, "memory": 0, "relief": 0, "awe": 0},
    ))
    elder = world.add(Entity(
        id="Elder", kind="character", type="elder",
        label="the old maker",
        meters={"distance": 0},
        memes={"calm": 1, "patience": 1},
    ))
    danger = world.add(Entity(
        id="Danger", kind="thing", type="shrine-break",
        label=danger_label,
        meters={"broken": 1, "noise": 1, "risk": 1},
        memes={"fear": 0},
    ))
    shrine = world.add(Entity(
        id="Shrine", kind="place", type="place",
        label=setting.name,
        meters={"brightness": 1, "stillness": 1},
        memes={"awe": 0},
    ))

    world.say(
        f"{hero.id} lived by {setting.name}, where {elder.label} taught the old way of {craft.label}."
    )
    world.say(
        f"{hero.id} loved the craft and carried {craft.tool}, because the smallest careful work could keep a holy place standing."
    )
    world.para()
    surprise = random.choice(SURPRISES)
    world.say(
        f"One evening, {surprise} startled the valley, and the air went tight with a surprise so sharp it could terrify a child."
    )
    world.say(
        f"Then came the sound: {random.choice(SOUND_EFFECTS)}, {danger.sound if hasattr(danger, 'sound') else 'KRAK'}, {random.choice(SOUND_EFFECTS)}."
    )
    hero.memes["surprise"] += 1
    hero.memes["fear"] += 1
    danger.meters["noise"] += 1
    world.facts["surprise"] = surprise
    world.facts["craft"] = craft
    world.facts["danger"] = danger
    world.facts["elder"] = elder
    world.facts["hero"] = hero
    world.facts["setting"] = setting
    world.facts["shrine"] = shrine

    world.para()
    world.say(
        f"{hero.id} wanted to run, but {elder.label} pointed at {danger.label} and said the sound was not a monster at all."
    )
    world.say(
        f"It was only {danger.label}, waiting for {hero.id}'s handiwork and {craft.minimum_step}."
    )
    hero.memes["fear"] += 1
    hero.memes["courage"] += 1

    world.para()
    trigger = random.choice(FLASHBACK_TRIGGERS)
    world.say(flashback_line(trigger, hero, elder, craft))
    hero.memes["memory"] += 1
    elder.memes["memory"] = elder.memes.get("memory", 0) + 1

    world.para()
    _attempt_repair(world, hero, craft, danger.id, narrate=True)
    danger.meters["risk"] = 0
    shrine.meters["stillness"] += 1
    hero.memes["relief"] += 1
    hero.memes["awe"] += 1
    hero.memes["fear"] = 0
    world.say(
        f"At last, the crack was small and true, the minimum careful repair had done its work, and the shrine stood quiet again."
    )
    world.say(
        f"{hero.id} looked up at {setting.name}, hearing only soft wind now, and knew the valley had changed because one pair of hands had listened."
    )
    world.facts["resolved"] = True
    return world

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    craft = f["craft"]
    setting = f["setting"]
    danger = f["danger"]
    return [
        f'Write a short myth for children about a brave helper named {hero.id}, a surprise, and the word "terrify".',
        f"Tell a story where {hero.id} uses {craft.label} at {setting.name} to fix {danger.label} with only the minimum needed work.",
        f'Write a gentle myth with sound effects and a flashback, ending with calm after the danger is repaired.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    craft = f["craft"]
    danger = f["danger"]
    setting = f["setting"]
    surprise = f["surprise"]

    return [
        QAItem(
            question=f"What made {hero.id} afraid in {setting.name}?",
            answer=(
                f"{surprise} and the loud cracking sound made {hero.id} think something terrible had happened. "
                f"At first, it felt like enough to terrify a child."
            ),
        ),
        QAItem(
            question=f"What was the real problem behind the scary sound?",
            answer=(
                f"The real problem was {danger.label}. It needed {craft.label} done with the minimum careful step, "
                f"not panic."
            ),
        ),
        QAItem(
            question=f"What did the elder teach {hero.id} to do?",
            answer=(
                f"{elder.label} taught {hero.id} to use {craft.minimum_step} and listen to the crack before fixing it."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"{hero.id} finished the repair, felt relief and pride, and heard only the soft wind around {setting.name}."
            ),
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is handiwork?",
            answer="Handiwork is careful work made by hand, like fixing, shaping, or mending something gently.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens before you are ready for it.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you imagine noises, like CLANG, TINK, or KRAK.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What does minimum mean here?",
            answer="Minimum means the smallest amount needed to do the job well and safely.",
        ),
    ]

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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = list(SETTINGS.keys())
    if args.setting and args.craft and args.danger:
        reasonableness_gate(args.setting, args.craft, args.danger)
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.craft:
        combos = [c for c in combos if c[1] == args.craft]
    if args.danger:
        combos = [c for c in combos if c[2] == args.danger]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, craft_key, danger = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, role="apprentice", material="bronze", danger=danger, name=name)

def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    craft_key = "mend" if params.danger == "a cracking pillar" else "seal" if params.danger == "a loose idol" else "retie"
    craft = CRAFTS[craft_key]
    world = tell(setting, craft, params.danger, params.name)
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

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="valley", role="apprentice", material="bronze", danger="a cracking pillar", name="Ari"),
    StoryParams(setting="shrine", role="apprentice", material="river clay", danger="a loose idol", name="Mira"),
    StoryParams(setting="village", role="apprentice", material="oak", danger="a falling bell", name="Niko"),
    StoryParams(setting="forge", role="apprentice", material="black iron", danger="a broken gate chain", name="Sela"),
    StoryParams(setting="temple", role="apprentice", material="white stone", danger="a split drum", name="Tavi"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: terrify, handiwork, minimum, surprise, sound effects, flashback.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--craft", choices=CRAFTS.keys())
    ap.add_argument("--danger", choices=set(DANGERS_BY_SETTING.values()))
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

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, craft, danger) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
