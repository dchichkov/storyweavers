#!/usr/bin/env python3
"""
storyworlds/worlds/winter_kindness.py
=====================================

A standalone story world from the seed:

    Words: scarf, mitten, sleepy
    Features: Kindness, Cautionary, Humor
    Style: Myth

The world models a child-like woodland helper who sees a sleepy creature in the
cold. A mentor predicts what will happen if the creature is left exposed. The
story is only valid when the shared warm item covers the creature's actual need.

Run it
------
    python storyworlds/worlds/winter_kindness.py
    python storyworlds/worlds/winter_kindness.py --all --trace --qa
    python storyworlds/worlds/winter_kindness.py --creature mouse --garment mittens
    python storyworlds/worlds/winter_kindness.py --creature robin --garment mittens  # rejected
    python storyworlds/worlds/winter_kindness.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REGIONS = {"neck", "paws", "body", "ears"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    need: str = ""
    covers: set[str] = field(default_factory=set)
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    phrase: str
    affords: set[str]


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    need: str
    sleepy_sound: str
    thanks: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    covers: set[str]
    share: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


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
        return clone


def _r_cold_makes_sleepy(world: World) -> list[str]:
    creature = world.get("Creature")
    if creature.meters["exposed"] < THRESHOLD:
        return []
    sig = ("sleepy", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["cold"] += 1
    creature.meters["sleepy"] += 1
    creature.memes["worried"] += 1
    return [f"{creature.label.capitalize()} grew sleepier in the cold."]


def _r_shared_warmth_helps(world: World) -> list[str]:
    creature = world.get("Creature")
    garment = world.get("Garment")
    if garment.worn_by != creature.id or creature.need not in garment.covers:
        return []
    sig = ("warm", creature.id, garment.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["cold"] = 0.0
    creature.meters["sleepy"] = 0.0
    creature.memes["warm"] += 1
    creature.memes["gratitude"] += 1
    return [f"{creature.label.capitalize()} warmed up and blinked wide awake."]


CAUSAL_RULES = [
    Rule("cold_makes_sleepy", _r_cold_makes_sleepy),
    Rule("shared_warmth_helps", _r_shared_warmth_helps),
]


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
        for sent in produced:
            world.say(sent)
    return produced


def garment_fits(creature: Creature, garment: Garment) -> bool:
    return creature.need in garment.covers


def valid_story(setting: Setting, creature: Creature, garment: Garment) -> bool:
    return creature.id in setting.affords and garment_fits(creature, garment)


def leave_exposed(world: World, creature: Entity, narrate: bool = True) -> None:
    creature.meters["exposed"] += 1
    propagate(world, narrate=narrate)


def predict_sleepiness(world: World, creature: Entity) -> dict:
    sim = world.copy()
    leave_exposed(sim, sim.get(creature.id), narrate=False)
    predicted = sim.get(creature.id)
    return {
        "sleepy": predicted.meters["sleepy"] >= THRESHOLD,
        "cold": predicted.meters["cold"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, mentor: Entity, garment: Entity) -> None:
    proud_ref = "them" if garment.type == "mittens" else "it"
    world.say(
        f"Long ago, when frost still told tiny myths, {hero.label} walked through "
        f"{world.setting.phrase} with {hero.pronoun('possessive')} {mentor.label}."
    )
    world.say(f"{hero.label} wore {garment.phrase} and felt proud of {proud_ref}.")


def notice(world: World, hero: Entity, creature_cfg: Creature) -> None:
    world.say(
        f"Under a snowy bush, {hero.label} found {creature_cfg.phrase}. "
        f'"{creature_cfg.sleepy_sound}," went {creature_cfg.label}.'
    )


def warn(world: World, hero: Entity, mentor: Entity, creature: Entity) -> bool:
    prediction = predict_sleepiness(world, creature)
    if not prediction["sleepy"]:
        return False
    world.facts["predicted_sleepy"] = True
    world.say(
        f'"If we leave {creature.label} exposed, the cold will make them too sleepy '
        f'to get home," {hero.pronoun("possessive")} {mentor.label} said.'
    )
    return True


def hesitate(world: World, hero: Entity, garment: Entity) -> None:
    hero.memes["selfish_pull"] += 1
    favorite = "they are my favorites" if garment.type == "mittens" else "it is my favorite"
    world.say(
        f"{hero.label} hugged {garment.label} close. "
        f'"But {favorite}," {hero.pronoun()} thought.'
    )


def share(world: World, hero: Entity, creature: Entity, garment: Entity,
          garment_cfg: Garment) -> None:
    hero.memes["kindness"] += 1
    garment.worn_by = creature.id
    world.say(garment_cfg.share.format(hero=hero.label, creature=creature.label))
    propagate(world, narrate=True)


def thanks(world: World, hero: Entity, creature_cfg: Creature) -> None:
    world.say(
        f'"{creature_cfg.thanks}," said {creature_cfg.label}, and {hero.label} laughed so hard '
        "the frost shook like sugar."
    )


def moral(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.label} learned that warmth grows bigger when it is shared."
    )


def tell(setting: Setting, creature_cfg: Creature, garment_cfg: Garment,
         hero_name: str, gender: str, mentor_type: str) -> World:
    if not valid_story(setting, creature_cfg, garment_cfg):
        raise StoryError(explain_rejection(setting, creature_cfg, garment_cfg))
    world = World(setting)
    hero = world.add(Entity("Hero", kind="character", type=gender, label=hero_name))
    mentor = world.add(Entity("Mentor", kind="character", type=mentor_type, label=mentor_type))
    creature = world.add(Entity("Creature", kind="character", type=creature_cfg.id,
                                label=creature_cfg.label, phrase=creature_cfg.phrase,
                                need=creature_cfg.need))
    garment = world.add(Entity("Garment", type=garment_cfg.id, label=garment_cfg.label,
                               phrase=garment_cfg.phrase, covers=set(garment_cfg.covers),
                               worn_by=hero.id))

    introduce(world, hero, mentor, garment)
    world.para()
    notice(world, hero, creature_cfg)
    warn(world, hero, mentor, creature)
    hesitate(world, hero, garment)
    world.para()
    share(world, hero, creature, garment, garment_cfg)
    thanks(world, hero, creature_cfg)
    moral(world, hero)
    world.facts.update(hero=hero, mentor=mentor, creature=creature,
                       creature_cfg=creature_cfg, garment=garment,
                       garment_cfg=garment_cfg, setting=setting)
    return world


SETTINGS = {
    "snowfield": Setting("the moonlit snowfield", {"robin", "mouse", "foxkit"}),
    "frost_wood": Setting("the frost wood", {"owl", "mouse", "hare"}),
    "icy_bridge": Setting("the icy bridge pass", {"robin", "hare", "foxkit"}),
    "winter_gate": Setting("the old winter gate", {"owl", "mouse", "robin"}),
}

CREATURES = {
    "robin": Creature("robin", "the robin", "a sleepy robin with a bare neck",
                      "neck", "Peep-snore", "My neck feels like spring now",
                      {"bird", "sleepy"}),
    "mouse": Creature("mouse", "the mouse", "a sleepy mouse with cold paws",
                      "paws", "Squeak-yawn", "My paws remember dancing",
                      {"mouse", "sleepy"}),
    "owl": Creature("owl", "the owl", "a sleepy owl with chilly ears",
                    "ears", "Hoo-hoo-honk", "My ears heard kindness",
                    {"owl", "sleepy"}),
    "hare": Creature("hare", "the hare", "a sleepy hare curled in the snow",
                     "body", "Hop-snrrk", "My whole self feels warm",
                     {"hare", "sleepy"}),
    "foxkit": Creature("foxkit", "the fox kit", "a sleepy fox kit shivering all over",
                       "body", "Yip-yawn", "My tail can stop pretending to be a blanket",
                       {"fox", "sleepy"}),
}

GARMENTS = {
    "scarf": Garment("scarf", "the scarf", "a long red scarf", {"neck", "ears"},
                     "{hero} wrapped the scarf around {creature} with a careful knot.",
                     {"scarf", "warmth"}),
    "mittens": Garment("mittens", "the mittens", "soft blue mittens", {"paws"},
                       "{hero} slipped the mittens onto {creature}'s paws.",
                       {"mitten", "warmth"}),
    "cloak": Garment("cloak", "the cloak", "a little wool cloak", {"body"},
                     "{hero} spread the cloak over {creature} like a tiny tent.",
                     {"cloak", "warmth"}),
    "cap": Garment("cap", "the cap", "a fuzzy cap", {"ears"},
                   "{hero} tucked the cap over {creature}'s chilly ears.",
                   {"cap", "warmth"}),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Rose"]
BOY_NAMES = ["Ben", "Eli", "Theo", "Max", "Sam", "Finn"]
MENTORS = ["mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for creature_id in setting.affords:
            creature = CREATURES[creature_id]
            for garment_id, garment in GARMENTS.items():
                if valid_story(setting, creature, garment):
                    combos.append((place, creature_id, garment_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    creature: str
    garment: str
    hero: str
    gender: str
    mentor: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "scarf": [("What is a scarf for?",
               "A scarf wraps around the neck to help keep warm air close.")],
    "mitten": [("What are mittens for?",
                "Mittens keep fingers together so hands can stay warmer in cold weather.")],
    "warmth": [("Why does sharing warm clothing help?",
                "Warm clothing slows heat loss, so a cold body can warm up again.")],
    "sleepy": [("Can cold make someone sleepy?",
                "Yes. Being too cold can make a body tired and slow, which is a sign to warm up safely.")],
    "bird": [("How do small birds stay warm?",
              "Small birds fluff their feathers and find shelter from wind and snow.")],
    "mouse": [("Where do mice keep warm?",
               "Mice often hide in nests, burrows, or sheltered corners to stay warm.")],
    "owl": [("Why do ears need warmth?",
             "Ears can lose heat quickly because they are small and exposed.")],
}
KNOWLEDGE_ORDER = ["scarf", "mitten", "warmth", "sleepy", "bird", "mouse", "owl"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, creature, garment = f["hero"], f["creature_cfg"], f["garment_cfg"]
    return [
        'Write a funny cautionary myth for children using the words "scarf", "mitten", and "sleepy".',
        f"Tell a kindness story where {hero.label} helps {creature.phrase} by sharing {garment.phrase}.",
        "Write a gentle winter tale where sharing warm clothing solves the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mentor, creature, garment = (
        f["hero"], f["mentor"], f["creature_cfg"], f["garment_cfg"]
    )
    return [
        ("Who is the story about?",
         f"It is about {hero.label}, {hero.pronoun('possessive')} {mentor.label}, and {creature.phrase}."),
        ("Why was the creature sleepy?",
         f"The creature was exposed to the cold, and the world model predicted the cold would make them too sleepy to get home."),
        ("What did the mentor warn?",
         f"{mentor.label.capitalize()} warned that leaving {creature.label} exposed would make them too sleepy to get home."),
        ("How did kindness solve the problem?",
         f"{hero.label} shared {garment.phrase}, which covered {creature.label}'s {creature.need}. That warmed the creature up."),
        (f"What did {hero.label} learn?",
         f"{hero.label} learned that warmth grows bigger when it is shared."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["creature_cfg"].tags) | set(f["garment_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.need:
            bits.append(f"need={ent.need}")
        if ent.covers:
            bits.append(f"covers={sorted(ent.covers)}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("snowfield", "robin", "scarf", "Lina", "girl", "mother"),
    StoryParams("frost_wood", "mouse", "mittens", "Theo", "boy", "aunt"),
    StoryParams("icy_bridge", "hare", "cloak", "Nora", "girl", "father"),
    StoryParams("winter_gate", "owl", "cap", "Finn", "boy", "uncle"),
]


def explain_rejection(setting: Setting, creature: Creature, garment: Garment) -> str:
    if creature.id not in setting.affords:
        return (f"(No story: {setting.phrase} does not contain {creature.phrase}, "
                "so the winter problem cannot be staged there.)")
    return (f"(No story: {garment.phrase} covers {sorted(garment.covers)}, but "
            f"{creature.label} needs warmth on the {creature.need}.)")


ASP_RULES = r"""
fits(C, G) :- need(C, R), covers(G, R).
valid(P, C, G) :- affords(P, C), fits(C, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for region in sorted(REGIONS):
        lines.append(asp.fact("region", region))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for creature in sorted(setting.affords):
            lines.append(asp.fact("affords", place, creature))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("need", creature_id, creature.need))
    for garment_id, garment in GARMENTS.items():
        lines.append(asp.fact("garment", garment_id))
        for region in sorted(garment.covers):
            lines.append(asp.fact("covers", garment_id, region))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: scarf, mitten, sleepy. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and args.creature not in SETTINGS[args.place].affords:
        raise StoryError(explain_rejection(SETTINGS[args.place], CREATURES[args.creature],
                                           GARMENTS[args.garment or "scarf"]))
    if args.creature and args.garment and not garment_fits(CREATURES[args.creature],
                                                           GARMENTS[args.garment]):
        setting = SETTINGS[args.place] if args.place else next(
            s for s in SETTINGS.values() if args.creature in s.affords
        )
        raise StoryError(explain_rejection(setting, CREATURES[args.creature],
                                           GARMENTS[args.garment]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.creature is None or c[1] == args.creature)
              and (args.garment is None or c[2] == args.garment)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, creature, garment = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(names)
    mentor = args.mentor or rng.choice(MENTORS)
    return StoryParams(place, creature, garment, hero, gender, mentor)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CREATURES[params.creature],
                 GARMENTS[params.garment], params.hero, params.gender,
                 params.mentor)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(combos)} compatible (place, creature, garment) combos:\n")
        for place, creature, garment in combos:
            print(f"  {place:12} {creature:8} {garment}")
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
            header = f"### {p.hero}: {p.creature} with {p.garment} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
