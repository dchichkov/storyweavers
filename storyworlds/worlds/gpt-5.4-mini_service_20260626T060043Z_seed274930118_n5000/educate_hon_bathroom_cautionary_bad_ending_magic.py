#!/usr/bin/env python3
"""
A small bathroom storyworld with a cautionary, magical turn and a bad-ending
variant that still lands in a warm, child-facing lesson.

Premise:
- A child named Hon wants to use a magic bath item in the bathroom.
- A careful parent tries to educate Hon about safe bathroom behavior.
- If Hon ignores the warning, the magic can make a slippery, messy, bad ending.
- If Hon listens, the story ends with a gentle, heartwarming lesson.

The simulated world tracks:
- Physical meters: slipperiness, wetness, mess, soap foam, brokenness
- Emotional memes: curiosity, worry, fear, relief, pride, care

The story is intentionally constrained so the cautionary turn is causal:
the parent warns because the world model predicts a real bathroom hazard.
"""

from __future__ import annotations

import argparse
import copy
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bathroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    hazard: str
    safe_use: str
    risky_use: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafetyGear:
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
        self.magic_on: bool = False
        self.spill_zone: set[str] = set()
        self.hazard_seen: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.paragraphs = [[]]
        clone.magic_on = self.magic_on
        clone.spill_zone = set(self.spill_zone)
        clone.hazard_seen = self.hazard_seen
        return clone

    def has_gear(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


def meter_get(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme_get(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _rule_magic_spill(world: World) -> list[str]:
    out: list[str] = []
    if not world.magic_on:
        return out
    for actor in world.characters():
        if meter_get(actor, "magic") < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.spill_zone = {"floor", "sink", "tub"}
        add_meter(actor, "wet", 1.0)
        add_meter(actor, "slippery", 1.0)
        add_meter(actor, "mess", 1.0)
        add_meme(actor, "curiosity", 0.5)
        world.hazard_seen = True
        out.append(f"The magic swirled fast and made the bathroom floor slippery.")
    return out


def _rule_slip_hazard(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if meter_get(actor, "slippery") < THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        add_meme(actor, "fear", 1.0)
        out.append(f"That was a dangerous moment for {actor.id}.")
    return out


def _rule_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if meter_get(item, "mess") < THRESHOLD or not item.caretaker:
            continue
        sig = ("cleanup", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        add_meme(carer, "worry", 1.0)
        out.append(f"Now there would be extra cleaning for {carer.label}.")
    return out


CAUSAL_RULES = [_rule_magic_spill, _rule_slip_hazard, _rule_cleanup]


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


def predict_hazard(world: World, actor: Entity) -> dict[str, bool]:
    sim = world.copy()
    sim.magic_on = True
    add_meter(sim.get(actor.id), "magic", 1.0)
    propagate(sim, narrate=False)
    hero = sim.get(actor.id)
    return {
        "slippery": meter_get(hero, "slippery") >= THRESHOLD,
        "mess": meter_get(hero, "mess") >= THRESHOLD,
        "fear": meme_get(hero, "fear") >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"Hon was a little curious {hero.type} who loved shiny surprises, and {parent.label} liked to educate {hero.pronoun('object')} about safe choices."
    )


def set_scene(world: World, item: MagicItem) -> None:
    world.say(
        f"In the bathroom, a tiny blue glow waited on the shelf: {item.phrase}."
    )
    world.say(
        f"It promised {item.glow}, but it also could cause {item.hazard} if used the wrong way."
    )


def want_magic(world: World, hero: Entity, item: MagicItem) -> None:
    add_meme(hero, "curiosity", 1.0)
    world.say(
        f"Hon wanted to try the magic item right away because {item.effect} sounded fun."
    )


def warn(world: World, parent: Entity, hero: Entity, item: MagicItem) -> bool:
    hazard = predict_hazard(world, hero)
    if not hazard["slippery"]:
        return False
    add_meme(parent, "worry", 1.0)
    world.facts["predicted_hazard"] = True
    world.say(
        f"\"Hon, this can make the floor slippery,\" {parent.label} said. \"I need to educate you before anyone gets hurt.\""
    )
    return True


def ignore_warn(world: World, hero: Entity) -> None:
    add_meme(hero, "defiance", 1.0)
    world.say(
        f"Hon still reached for it, even though {hero.pronoun('possessive')} heart thumped a little faster."
    )


def use_magic(world: World, hero: Entity, item: MagicItem) -> None:
    world.magic_on = True
    add_meter(hero, "magic", 1.0)
    world.say(f"Hon lifted {item.label}, and the room gave a soft sparkling hum.")
    propagate(world, narrate=True)


def safety_turn(world: World, parent: Entity, hero: Entity, item: MagicItem, gear: SafetyGear) -> None:
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id
    world.say(
        f"Then {parent.label} smiled and said, \"How about we {gear.prep} first?\""
    )
    world.say(
        f"Hon nodded, and together they {gear.tail} before touching the magic again."
    )


def resolve(world: World, hero: Entity, parent: Entity, item: MagicItem) -> None:
    add_meme(hero, "relief", 1.0)
    add_meme(parent, "pride", 1.0)
    world.say(
        f"After the warning, Hon looked at {parent.label} and took a slower breath."
    )
    world.say(
        f"That made the bathroom feel safe again, and the little glow stayed quiet on the shelf."
    )


def bad_end(world: World, hero: Entity, parent: Entity, item: MagicItem) -> None:
    add_meme(hero, "fear", 1.0)
    add_meter(hero, "wet", 1.0)
    world.say(
        f"The magic burst into bubbles, the floor turned slick, and Hon slid into a cold splash."
    )
    world.say(
        f"{parent.label} hurried over, picked {hero.pronoun('object')} up gently, and began the slow clean-up."
    )
    world.say(
        f"It was a bad ending for the sparkly trick, but a useful one: Hon had learned why bathroom rules mattered."
    )


def tell(world: World, hero: Entity, parent: Entity, item: MagicItem, gear: SafetyGear) -> World:
    introduce(world, hero, parent)
    world.para()
    set_scene(world, item)
    want_magic(world, hero, item)
    warn(world, parent, hero, item)
    ignore_warn(world, hero)
    world.para()
    use_magic(world, hero, item)
    if world.hazard_seen:
        bad_end(world, hero, parent, item)
    else:
        safety_turn(world, parent, hero, item, gear)
        resolve(world, hero, parent, item)
    world.facts.update(hero=hero, parent=parent, item=item, gear=gear, hazard=world.hazard_seen)
    return world


SETTINGS = {
    "bathroom": Setting(place="the bathroom", affords={"magic"}),
}

MAGIC_ITEMS = {
    "soap_star": MagicItem(
        id="soap_star",
        label="the soap star",
        phrase="a star-shaped soap bar with a blue shimmer",
        effect="make bubbles leap like tiny moons",
        hazard="slippery floor and messy splashes",
        safe_use="hold it carefully by the sink",
        risky_use="wave it over the wet floor",
        glow="sparkly bubbles and sweet clean smells",
        tags={"magic", "soap", "bathroom"},
    ),
    "bubble_wand": MagicItem(
        id="bubble_wand",
        label="the bubble wand",
        phrase="a wand with a silver handle and soap at the tip",
        effect="paint the air with floating bubbles",
        hazard="drips that turn the tiles slick",
        safe_use="blow one bubble at a time",
        risky_use="spin it above the tub",
        glow="round bubbles that drift and pop",
        tags={"magic", "soap", "bathroom"},
    ),
}

GEAR = {
    "slip_shoes": SafetyGear(
        id="slip_shoes",
        label="non-slip bathroom shoes",
        covers={"feet"},
        guards={"slippery"},
        prep="put on your non-slip bathroom shoes",
        tail="put on the non-slip shoes and walked carefully back to the sink",
        plural=True,
    ),
    "towel_apron": SafetyGear(
        id="towel_apron",
        label="a thick towel apron",
        covers={"torso"},
        guards={"mess"},
        prep="tie on a thick towel apron",
        tail="tied the towel apron and used the magic near the sink",
    ),
}

CHILD_NAMES = ["Hon", "Mina", "Theo", "Lia", "Pip", "Nia"]
PARENT_NAMES = ["Mom", "Dad", "Auntie", "Uncle"]
TRAITS = ["gentle", "curious", "small", "cheerful", "careful"]


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("bathroom", item_id) for item_id in MAGIC_ITEMS]


def explain_rejection(item: MagicItem) -> str:
    return f"(No story: {item.label} doesn't fit this cautionary bathroom setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bathroom cautionary magic storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=MAGIC_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["Mom", "Dad", "Auntie", "Uncle"])
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
    if args.item and args.item not in MAGIC_ITEMS:
        raise StoryError(explain_rejection(MAGIC_ITEMS[args.item]))
    choices = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.item is None or c[1] == args.item)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, item_id = rng.choice(choices)
    name = args.name or "Hon"
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item_id, name=name, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a heartwarming cautionary story set in the bathroom that includes the word "hon" and a little magic.',
        f"Tell a short story about Hon in {world.setting.place} who wants to use {item.label}, but a parent educates {f['hero'].pronoun('object')} about safety.",
        f"Write a magical bathroom story with a bad ending turn that teaches why slippery floors are dangerous.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: MagicItem = f["item"]
    qa = [
        QAItem(
            question=f"Who wanted to use the magic item in the bathroom?",
            answer=f"Hon wanted to use {item.label} in the bathroom.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn Hon about the magic?",
            answer=f"{parent.label} warned Hon because the magic could make the floor slippery and cause a bad fall.",
        ),
        QAItem(
            question=f"What did the story teach Hon at the end?",
            answer=f"It taught Hon to listen to bathroom safety advice and use magic carefully.",
        ),
    ]
    if f.get("hazard"):
        qa.append(QAItem(
            question="What went wrong when Hon used the magic carelessly?",
            answer="The magic made the bathroom floor slick, so Hon slipped and had to be helped.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should bathroom floors be kept dry?",
            answer="Bathroom floors should be kept dry because wet tiles can be slippery and dangerous.",
        ),
        QAItem(
            question="What does it mean to educate someone?",
            answer="To educate someone means to teach them something helpful so they can make a safer or better choice.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story shows a danger or mistake so the listener can learn a useful lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append("protective=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  magic_on={world.magic_on}")
    lines.append(f"  spill_zone={sorted(world.spill_zone)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S) :- setting(S), item(I), risky(I).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in MAGIC_ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risky", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hazard/1."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_verify() -> int:
    py = {("bathroom", iid) for _, iid in valid_combos()}
    asp_set = set(asp_valid_combos())
    asp_pairs = {("bathroom", t[0]) for t in asp_set}
    if py == asp_pairs:
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", sorted(py))
    print("asp:", sorted(asp_pairs))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label=params.parent))
    item = MAGIC_ITEMS[params.item]
    world.add(Entity(id=item.id, type="thing", label=item.label, phrase=item.phrase, caretaker=parent.id))
    gear = GEAR["slip_shoes"]

    tell(world, hero, parent, item, gear)
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
    StoryParams(place="bathroom", item="soap_star", name="Hon", parent="Mom", trait="curious"),
    StoryParams(place="bathroom", item="bubble_wand", name="Hon", parent="Dad", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show hazard/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program("#show hazard/1.")))
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
