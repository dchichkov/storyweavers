#!/usr/bin/env python3
"""
storyworlds/worlds/grape_millenium_humor_happy_ending_slice_of.py
==================================================================

A small slice-of-life storyworld about a child, a grape mess, and a funny
mix-up that still ends happily.

Seed image:
- A child at a little neighborhood market.
- A bright grape snack is about to become a problem.
- A parent notices the trouble early and suggests a playful fix.
- The ending should feel warm, ordinary, and gently funny.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the little market"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "market": Setting(place="the little market", indoors=False, affords={"grapes", "music", "grapes_and_music"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"grapes", "music"}),
    "porch": Setting(place="the front porch", indoors=False, affords={"grapes", "music"}),
}

TASTES = {
    "grapes": Treat(
        id="grapes",
        label="grapes",
        phrase="a small paper bowl of purple grapes",
        mess="purple",
        soil="squished and purple-stained",
        zone={"hands", "shirt"},
        keyword="grape",
        tags={"grape", "fruit"},
    ),
    "grapes_and_music": Treat(
        id="grapes_and_music",
        label="grapes",
        phrase="a small paper bowl of purple grapes",
        mess="purple",
        soil="squished and purple-stained",
        zone={"hands", "shirt"},
        keyword="grape",
        tags={"grape", "humor", "music"},
    ),
    "music": Treat(
        id="music",
        label="music",
        phrase="a tiny toy radio that played a cheerful tune",
        mess="none",
        soil="unchanged",
        zone=set(),
        keyword="tune",
        tags={"music", "humor"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="an old apron",
        covers={"shirt"},
        guards={"purple"},
        prep="put on an old apron first",
        tail="went back inside for the apron",
    ),
    Gear(
        id="napkins",
        label="a stack of napkins",
        covers={"hands"},
        guards={"purple"},
        prep="grab a stack of napkins first",
        tail="came back with a stack of napkins",
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Lina", "Tia", "June", "Nora", "Pia"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Ben", "Finn", "Eli"]
TRAITS = ["curious", "silly", "careful", "cheerful", "bouncy"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def treat_at_risk(treat: Treat) -> bool:
    return bool(treat.zone)


def select_gear(treat: Treat) -> Optional[Gear]:
    for gear in GEAR:
        if treat.mess in gear.guards and any(region in gear.covers for region in treat.zone):
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tid in setting.affords:
            tr = TASTES[tid]
            if treat_at_risk(tr) and select_gear(tr):
                combos.append((place, tid))
    return combos


def explain_rejection(treat: Treat) -> str:
    return (
        f"(No story: nothing in this world can reasonably protect the at-risk "
        f"grape snack from {treat.id}. The fix must actually cover the messy spot.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def prompt_name(params: StoryParams) -> str:
    return f"Write a short slice-of-life story for a young child about {params.name}, grapes, and a funny problem that ends happily."


def prompt_parent(params: StoryParams) -> str:
    return f"Tell a gentle story where {params.name} wants to enjoy grapes at {SETTINGS[params.place].place}, but {params.parent} notices a messy risk and helps with a playful solution."


def prompt_tone(params: StoryParams) -> str:
    return "Write an everyday, child-friendly story with humor and a happy ending, using the word grape."


def predict_mess(world: World, actor: Entity, treat: Treat, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), treat, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("purple", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, treat: Treat, narrate: bool = True) -> None:
    world.zone = set(treat.zone)
    if treat.mess != "none":
        actor.meters[treat.mess] = actor.meters.get(treat.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for item in world.entities.values():
        if item.worn_by == actor.id and item.label == "shirt":
            if item.kind == "thing" and treat.mess in {"purple"} and "shirt" in treat.zone:
                item.meters["purple"] = item.meters.get("purple", 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} reached for the grapes and looked very pleased.")


def apply_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("purple", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by == actor.id and item.label == "shirt" and item.meters.get("dirty", 0.0) < THRESHOLD:
                if ("spill", item.id) in world.fired:
                    continue
                world.fired.add(("spill", item.id))
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} shirt got a little purple.")
    return out


def apply_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.label == "shirt" and item.meters.get("dirty", 0.0) >= THRESHOLD and item.caretaker and ("worry", item.id) not in world.fired:
            world.fired.add(("worry", item.id))
            carer = world.get(item.caretaker)
            carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
            out.append(f"That would mean more laundry for {carer.label_word}.")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (apply_spill, apply_worry):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.meters.keys()), hero.type)} child who liked small everyday adventures.")


def setup_story(world: World, hero: Entity, parent: Entity, treat: Entity) -> None:
    world.say(f"{hero.id} loved {treat.label} and the tidy little moments that came with snack time.")
    world.say(f"One day, {parent.label_word} bought {hero.pronoun('object')} {treat.phrase}.")
    hero.worn = treat.id
    treat.worn_by = hero.id
    world.say(f"{hero.id} carried {treat.it()} as carefully as if it were a treasure.")


def offer(world: World, parent: Entity, hero: Entity, treat: Treat) -> Optional[Gear]:
    pred = predict_mess(world, hero, treat, "shirt")
    if not pred["soiled"]:
        return None
    gear = select_gear(treat)
    if gear is None:
        return None
    world.say(f'"{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. "How about we {gear.prep} and have our snack anyway?"')
    return gear


def accept(world: World, parent: Entity, hero: Entity, treat: Treat, gear: Gear, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(f"{hero.id} laughed, because the plan was almost too sensible to be funny.")
    world.say(f"They {gear.tail}. Soon {hero.id} was eating grapes without ruining {prize.label}, and {parent.label_word} was smiling too.")


def tell(setting: Setting, treat: Treat, hero_name: str, hero_type: str, parent_type: str, hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={hero_trait: 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="shirt", kind="thing", type="shirt", label="shirt", phrase="a clean shirt", caretaker=parent.id))
    treat_ent = world.add(Entity(id="treat", kind="thing", type=treat.id, label=treat.label, phrase=treat.phrase, owner=hero.id))
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a little {hero_trait} {hero.type} who noticed every snack and every puddle of trouble.")
    world.say(f"{hero.id} loved {treat.label}, especially on simple afternoons at {setting.place}.")
    world.say(f"One day, {parent.label_word} bought {hero.pronoun('object')} {treat.phrase}.")
    world.say(f"{hero.id} carried {treat.it()} with both hands and hoped the day would stay neat.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} wanted to enjoy the grapes right away.")
    world.say(f"Then {hero.pronoun('possessive')} smile turned a little mischievous, because the grapes were so juicy.")
    _do_activity(world, hero, treat, narrate=False)
    propagate(world, narrate=True)
    world.say(f"{hero.id} tried to balance the bowl, and one grape rolled like a tiny purple marble.")

    world.para()
    world.say(f"{parent.label_word.capitalize()} noticed the purple dot before it could become a bigger spot.")
    world.say(f'"If we keep going like this," {parent.label_word} said, "your shirt will look like it went to the grape parade."')
    gear = offer(world, parent, hero, treat)
    if gear:
        world.say(f"{hero.id} giggled, because that sounded very dramatic for such a small snack.")
        accept(world, parent, hero, treat, gear, prize)
    else:
        world.say(f"{hero.id} paused, then decided to hold the grapes more carefully.")
        world.say(f"That tiny change was enough to keep the shirt clean, and the afternoon stayed easy.")

    world.facts.update(hero=hero, parent=parent, prize=prize, treat=treat, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
at_risk(T) :- treat(T), zone(T,R), cloth_region(P,R).
need_fix(T) :- at_risk(T), has_gear(T).
valid(Place,T) :- affords(Place,T), need_fix(T).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, tr in TASTES.items():
        lines.append(asp.fact("treat", tid))
        for r in sorted(tr.zone):
            lines.append(asp.fact("zone", tid, r))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    lines.append(asp.fact("cloth_region", "shirt", "shirt"))
    for tid, tr in TASTES.items():
        if tr.zone and select_gear(tr):
            lines.append(asp.fact("has_gear", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
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


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, treat = f["hero"], f["parent"], f["treat"]
    return [
        prompt_name(world.facts["params"]),
        prompt_parent(world.facts["params"]),
        prompt_tone(world.facts["params"]),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, treat, gear = f["hero"], f["parent"], f["prize"], f["treat"], f["gear"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to enjoy at {world.setting.place}?",
            answer=f"{hero.id} wanted to enjoy grapes, and the snack was a small, cheerful part of the day.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the shirt?",
            answer=f"{parent.label_word.capitalize()} worried because the juicy grapes could leave the shirt purple and messy.",
        ),
        QAItem(
            question=f"What funny idea helped the family keep the snack time happy?",
            answer=f"They used {gear.label} before the snack, which was a silly little plan that worked well.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} enjoying grapes happily, while the shirt stayed clean enough for the rest of the day.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grape?",
            answer="A grape is a small round fruit that can be sweet and juicy.",
        ),
        QAItem(
            question="Why can grapes make a mess?",
            answer="Grapes can burst or drip juice, and that juice can stain clothes or hands purple.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling okay or glad.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: grapes, humor, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TASTES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.treat and args.place:
        if (args.place, args.treat) not in valid_combos():
            raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.treat is None or c[1] == args.treat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treat = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, treat=treat, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASTES[params.treat], params.name, params.gender, params.parent, params.trait)
    world.facts["params"] = params
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, treat in triples:
            print(f"  {place:10} {treat}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="market", treat="grapes", name="Mina", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="kitchen", treat="music", name="Theo", gender="boy", parent="father", trait="silly"),
            StoryParams(place="porch", treat="grapes_and_music", name="Lina", gender="girl", parent="mother", trait="careful"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.treat} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
