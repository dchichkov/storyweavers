#!/usr/bin/env python3
"""
storyworlds/worlds/gefilte_able_conflict_tall_tale.py
======================================================

A small storyworld in the style of a tall tale: a person, a prideful problem,
and a comically large gefilte fix.

Premise:
- A child named Able lives in a windy riverside town.
- Able is proud of being able to do big things, especially on market day.
- A pot of gefilte fish is the prized food, and it must stay whole and neat.

Tension:
- A boastful helper and a stubborn plan lead to a conflict over who may carry
  the gefilte pot across a wobbling bridge.
- The bridge, the pot, and the pride are all at risk.

Turn:
- The world is forward-simulated: carrying the pot by hand over the bridge
  would spill it and trigger a messy, public conflict.
- The only reasonable fix is a cart with wide wheels and a lid strap.

Resolution:
- Able accepts help, the cart rolls safely, and the gefilte arrives intact.
- The ending image proves the change: no spill, no feud, and a proud story
  to tell at supper.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- lazy imports storyworlds/asp.py only in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
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
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectKind:
    label: str
    phrase: str
    region: str
    fragile: bool = False
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.path: str = ""
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
        clone.path = self.path
        clone.paragraphs = [[]]
        return clone


def path_risky(world: World, prize: Entity) -> bool:
    return world.setting.place == "wobbly bridge" and prize.owner is not None


def choose_gear(prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if prize.meters.get("need_cart", 0) >= THRESHOLD and "carry" in gear.guards:
            return gear
    return None


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("jostled", 0) < THRESHOLD:
            continue
        if ent.meters.get("wet", 0) >= THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["wet"] = ent.meters.get("wet", 0) + 1
        ent.memes["panic"] = ent.memes.get("panic", 0) + 1
        out.append(f"The {ent.label} sloshed and threatened to spill.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("boast", 0) < THRESHOLD:
            continue
        if ent.memes.get("warned", 0) < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] = ent.memes.get("conflict", 0) + 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if x != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, prize: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["jostled"] = 1
    propagate(sim, narrate=False)
    return {
        "spilled": sim.get(prize.id).meters.get("wet", 0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big grin and an even bigger way of saying "
        f"what {hero.pronoun('possessive')} hands could do."
    )


def loves_gefilte(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved the smell of gefilte on market day, and {hero.pronoun('possessive')} "
        f"{prize.label} sat ready for the town supper."
    )


def boast(world: World, hero: Entity) -> None:
    hero.memes["boast"] = hero.memes.get("boast", 0) + 1
    world.say(
        f"{hero.id} said {hero.pronoun('subject')} was able to carry anything, even a pot that "
        f"looked as heavy as a moonlit well bucket."
    )


def arrive(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"On market day, {hero.id} and {helper.id} came to the wobbly bridge where the river "
        f"below laughed and gulped at every gust."
    )


def warn(world: World, helper: Entity, hero: Entity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, prize)
    if not pred["spilled"]:
        return False
    helper.memes["warned"] = helper.memes.get("warned", 0) + 1
    world.say(
        f'"Careful now," {helper.id} said. "If you cross that bridge carrying the {prize.label} "
        f"by hand, it may spill before supper."'
    )
    return True


def argue(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(
        f"{hero.id} frowned and said {hero.pronoun('subject')} was able enough to do it alone, "
        f"which made the air feel as tight as a pulled drum."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} stepped toward the bridge while {helper.id} stood "
        f"firm as a fence post."
    )


def select_fix(world: World, prize: Entity) -> Optional[Gear]:
    return choose_gear(prize)


def offer_fix(world: World, helper: Entity, hero: Entity, prize: Entity) -> Optional[Gear]:
    gear = select_fix(world, prize)
    if gear is None:
        return None
    world.say(
        f'{helper.id} pointed to a little cart by the bridge and said, "{gear.prep}."'
    )
    return gear


def accept(world: World, hero: Entity, helper: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["conflict"] = 0
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"{hero.id} blinked, then nodded. {hero.pronoun('subject').capitalize()} let the cart take "
        f"the weight, and {helper.id} tied the lid down with a ribbon as blue as a robin's egg."
    )
    world.say(
        f"They {gear.tail}. The bridge stayed steady, the gefilte stayed neat, and {hero.id} was "
        f"able to carry the story instead of the pot."
    )


def tell(world: World, hero: Entity, helper: Entity, prize: Entity) -> World:
    introduce(world, hero)
    loves_gefilte(world, hero, prize)
    boast(world, hero)
    world.para()
    arrive(world, hero, helper)
    warn(world, helper, hero, prize)
    argue(world, hero, helper)
    world.para()
    gear = offer_fix(world, helper, hero, prize)
    if gear is not None:
        accept(world, hero, helper, prize, gear)
    world.facts.update(hero=hero, helper=helper, prize=prize, gear=gear)
    return world


SETTINGS = {
    "bridge": Setting(place="wobbly bridge", affords={"carry"}),
    "market": Setting(place="market square", affords={"carry"}),
    "kitchen": Setting(place="the warm kitchen", affords={"carry"}),
}

PRIZES = {
    "pot": ObjectKind(label="pot", phrase="a heavy pot of gefilte fish", region="hands"),
    "tray": ObjectKind(label="tray", phrase="a wide tray of gefilte patties", region="hands"),
}

GEAR = [
    Gear(
        id="cart",
        label="little cart",
        prep="Put the pot on the little cart and strap the lid tight",
        tail="rolled the cart across",
        guards={"carry"},
        covers={"hands"},
    ),
    Gear(
        id="sled",
        label="hand sled",
        prep="Set the pot on the hand sled and push it slowly",
        tail="shuffled the sled over",
        guards={"carry"},
        covers={"hands"},
    ),
]

HERO_NAMES = ["Able", "Miriam", "Toby", "Ruth", "Nate", "Sarah"]
HELPER_NAMES = ["Uncle Moses", "Aunt Dina", "Old Ben", "Grandma Tess", "Neighbor Eli"]
TRAITS = ["able", "brave", "cheerful", "sturdy", "quick-witted"]


@dataclass
class StoryParams:
    place: str
    prize: str
    hero_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prize_id in PRIZES:
            if "carry" in setting.affords:
                combos.append((place, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        f'Write a tall tale for a young child about "{hero.id}" and a {prize.label} of gefilte fish.',
        f"Tell a funny, high-spirited story where {hero.id} is able to help with gefilte but learns to listen.",
        f'Write a story that includes the words "gefilte" and "able" and ends with a safer way to carry supper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, gear = f["hero"], f["helper"], f["prize"], f["gear"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to carry?",
            answer=f"{hero.id} was trying to carry {prize.phrase} across the wobbly bridge."
        ),
        QAItem(
            question=f"Why did {helper.id} worry on the bridge?",
            answer=f"{helper.id} worried because carrying the {prize.label} by hand might spill the gefilte before supper."
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used the {gear.label} so the pot could cross safely and stay neat."
            if gear else
            "They found a safer way to carry the food."
        ),
    ]
    if hero.memes.get("conflict", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"What kind of feeling did the two get into before the fix?",
            answer=f"They got into a conflict because {hero.id} wanted to prove {hero.pronoun('subject')} was able to do it alone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gefilte fish?",
            answer="Geﬁlte fish is a traditional fish dish made from ground fish mixed with seasonings, often shaped into patties or balls and served at a family meal."
        ),
        QAItem(
            question="What does it mean to be able to do something?",
            answer="Being able to do something means you have the skill or strength to do it."
        ),
        QAItem(
            question="Why do people use a cart for heavy things?",
            answer="People use a cart for heavy things because wheels can carry the weight and make the job easier."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P), needs_carry(P).
has_fix(P) :- prize_at_risk(P), gear(G), fixes(G,P).
valid_story(Place, P) :- setting(Place), affords(Place, carry), prize(P), has_fix(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("needs_carry", pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for p in PRIZES:
            lines.append(asp.fact("fixes", gear.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale about gefilte, ability, and a bridge conflict.")
    ap.add_argument("--place", choices=SETTINGS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize, hero_name=hero_name, helper_name=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="boy" if params.hero_name == "Able" else "child", traits=[params.trait]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="adult"))
    prize = world.add(Entity(id="prize", type="thing", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    gear = world.add(Entity(id="cart", type="thing", label="little cart"))
    prize.meters["need_cart"] = 1
    hero.memes["pride"] = 1
    tell(world, hero, helper, prize)
    chosen_gear = Gear(
        id="cart",
        label="little cart",
        prep="Put the pot on the little cart and strap the lid tight",
        tail="rolled the cart across",
        guards={"carry"},
        covers={"hands"},
    )
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, prize in valid_combos():
            params = StoryParams(place=place, prize=prize, hero_name="Able", helper_name="Uncle Moses", trait="able", seed=base_seed)
            samples.append(generate(params))
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
