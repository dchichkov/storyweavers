#!/usr/bin/env python3
"""
storyworlds/worlds/yacht_snout_magic_fairy_tale.py
==================================================

A tiny fairy-tale storyworld about a magical yacht, a curious snout, and a
stolen sparkle that must be restored.

Premise:
- A small fairy-tale crew sails a yacht through a moonlit bay.
- A shy snout-sniffing helper finds a magical pearl that keeps the yacht singing.
- When a spell goes wrong, the yacht loses its glow and the bay turns still.
- A kind fairy fixes the spell with a gentle charm, and the yacht shines again.

This script follows the Storyweavers contract:
- standalone stdlib Python
- typed entities with physical meters and emotional memes
- state-driven prose with a forward-chaining world model
- QA grounded in simulation history
- optional ASP twin and verification
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
    role: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "queen", "mother", "woman"}
        male = {"boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Yacht:
    id: str
    label: str
    phrase: str
    glow: str
    harbor: str
    magic_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snout:
    id: str
    label: str
    phrase: str
    sniff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    mend: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    harbor: str
    yacht: str
    snout: str
    charm: str
    hero: str
    hero_kind: str
    fairy: str
    fairy_kind: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_bay": "the moonlit bay",
    "tidal_harbor": "the tidal harbor",
    "rose_inlet": "the rose-colored inlet",
}

YACHTS = {
    "silver_yacht": Yacht(
        id="silver_yacht",
        label="silver yacht",
        phrase="a silver yacht with a bell like a star",
        glow="gleamed like a ribbon of moonlight",
        harbor="the moonlit bay",
        magic_need="a warm sailing charm",
        tags={"yacht", "magic"},
    ),
    "small_yacht": Yacht(
        id="small_yacht",
        label="little yacht",
        phrase="a little yacht with round sails",
        glow="shone softly as it rocked",
        harbor="the tidal harbor",
        magic_need="a gentle keeping spell",
        tags={"yacht"},
    ),
}

SNOUTS = {
    "fox_snout": Snout(
        id="fox_snout",
        label="fox snout",
        phrase="a curious fox snout",
        sniff="sniffed out hidden things",
        tags={"snout"},
    ),
    "pig_snout": Snout(
        id="pig_snout",
        label="pig snout",
        phrase="a rosy pig snout",
        sniff="could smell magic in the air",
        tags={"snout"},
    ),
}

CHARMS = {
    "spark_charm": Charm(
        id="spark_charm",
        label="spark charm",
        phrase="a spark charm of blue glass",
        mend="made the yacht sing again",
        tags={"magic"},
    ),
    "golden_knot": Charm(
        id="golden_knot",
        label="golden knot",
        phrase="a golden knot of thread",
        mend="tied the spell back together",
        tags={"magic"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ava", "Sophie"]
BOY_NAMES = ["Tobin", "Finn", "Owen", "Theo", "Eli"]
FAIRY_NAMES = ["Merry", "Willow", "Pearl", "Lily", "Pippa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for yacht in YACHTS:
            for snout in SNOUTS:
                if "yacht" in YACHTS[yacht].tags and "snout" in SNOUTS[snout].tags:
                    combos.append((setting, yacht, snout))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for yid, y in YACHTS.items():
        lines.append(asp.fact("yacht", yid))
        for t in sorted(y.tags):
            lines.append(asp.fact("has_tag", yid, t))
    for sid, s in SNOUTS.items():
        lines.append(asp.fact("snout", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("has_tag", sid, t))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("has_tag", cid, t))
    return "\n".join(lines)


ASP_RULES = r"""
match(Y,S) :- yacht(Y), snout(S).
magic_story(Y,S) :- match(Y,S), has_tag(Y,magic).
#show match/2.
#show magic_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show match/2."))
    asp_pairs = sorted(set(asp.atoms(model, "match")))
    py_pairs = sorted((y, s) for _, y, s in valid_combos())
    if asp_pairs == py_pairs:
        print(f"OK: ASP matches Python ({len(py_pairs)} pairs).")
        return 0
    print("MISMATCH:")
    print("ASP:", asp_pairs)
    print("PY :", py_pairs)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld: a yacht, a snout, and a magic fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--yacht", choices=YACHTS)
    ap.add_argument("--snout", choices=SNOUTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--fairy")
    ap.add_argument("--fairy-kind", choices=["fairy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.yacht is None or c[1] == args.yacht)
              and (args.snout is None or c[2] == args.snout)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, yacht, snout = rng.choice(sorted(combos))
    charm = args.charm or rng.choice(sorted(CHARMS))
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_kind == "girl" else BOY_NAMES)
    fairy_kind = "fairy"
    fairy = args.fairy or rng.choice(FAIRY_NAMES)
    return StoryParams(setting, yacht, snout, charm, hero, hero_kind, fairy, fairy_kind)


def _story_setup(world: World, hero: Entity, fairy: Entity, setting: str, yacht: Yacht, snout: Snout) -> None:
    hero.memes["wonder"] = 1
    world.say(f"Once in {SETTINGS[setting]}, {hero.id} saw {yacht.phrase}.")
    world.say(f"{yacht.label.capitalize()} {yacht.glow}, and nearby {snout.phrase} {snout.sniff}.")
    world.say(f"{hero.id} and {fairy.id} both loved the little magic of the water.")


def _lose_magic(world: World, yacht: Entity) -> None:
    yacht.meters["glow"] = 0
    yacht.memes["sad"] = 1


def _detect_problem(world: World, hero: Entity, yacht: Entity, snout: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(f"But when the tide swirled, the yacht's singing spell went quiet.")
    world.say(f"{snout.id} snuffled by the rail and found the spell-knot missing.")


def _fix_spell(world: World, fairy: Entity, yacht: Entity, charm: Charm) -> None:
    fairy.memes["kindness"] += 1
    yacht.meters["glow"] = 1
    yacht.memes["joy"] = 1
    world.say(f"{fairy.id} lifted {charm.phrase} and whispered a soft rhyme.")
    world.say(f"At once, the charm {charm.mend}, and the yacht shone again.")


def tell(setting: str, yacht_id: str, snout_id: str, charm_id: str,
         hero_name: str = "Mina", hero_kind: str = "girl",
         fairy_name: str = "Merry", fairy_kind: str = "fairy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, role="hero"))
    fairy = world.add(Entity(id=fairy_name, kind="character", type=fairy_kind, role="fairy"))
    ycfg = YACHTS[yacht_id]
    scfg = SNOUTS[snout_id]
    ccfg = CHARMS[charm_id]
    yacht = world.add(Entity(id="yacht", kind="thing", type="yacht", label=ycfg.label, phrase=ycfg.phrase))
    snout = world.add(Entity(id="snout", kind="thing", type="snout", label=scfg.label, phrase=scfg.phrase))
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label=ccfg.label, phrase=ccfg.phrase))
    world.facts.update(setting=setting, yacht_cfg=ycfg, snout_cfg=scfg, charm_cfg=ccfg, hero=hero, fairy=fairy)
    _story_setup(world, hero, fairy, setting, ycfg, scfg)
    world.para()
    _detect_problem(world, hero, yacht, snout)
    _lose_magic(world, yacht)
    world.para()
    _fix_spell(world, fairy, yacht, ccfg)
    world.say(f"In the end, {yacht.label} floated bright again, and the bay felt kind.")
    world.facts.update(yacht=yacht, snout=snout, charm=charm)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a 3-to-5-year-old about a {f["yacht_cfg"].label}, a {f["snout_cfg"].label}, and a magic fix.',
        f"Tell a gentle story where {f['hero'].id} notices a magical yacht in {SETTINGS[f['setting']]} and asks a fairy for help.",
        f'Write a short fairy tale that includes the words "{f["yacht_cfg"].label}" and "{f["snout_cfg"].label}" and ends with a magic spell mended.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    fairy = f["fairy"]
    ycfg = f["yacht_cfg"]
    scfg = f["snout_cfg"]
    ccfg = f["charm_cfg"]
    return [
        QAItem(
            question=f"Who saw the magical yacht in {SETTINGS[f['setting']]}?",
            answer=f"{hero.id} saw {ycfg.phrase} in {SETTINGS[f['setting']]}, and {fairy.id} was there too.",
        ),
        QAItem(
            question=f"What did the snout find when the yacht's song went quiet?",
            answer=f"The {scfg.label} found the missing spell-knot, which had made the yacht's magic work.",
        ),
        QAItem(
            question=f"How did the fairy help the yacht shine again?",
            answer=f"{fairy.id} used {ccfg.phrase}, and that gentle charm made the yacht sing and glow again.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The yacht was bright again, the spell was mended, and the bay felt kind and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a yacht?", answer="A yacht is a boat people sail on water, often for a trip or a ride."),
        QAItem(question="What is a snout?", answer="A snout is the nose and mouth part of some animals, like a pig or a fox."),
        QAItem(question="What is magic in a fairy tale?", answer="Magic is a special power that can change things in stories, often with a spell or charm."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.yacht, params.snout, params.charm, params.hero, params.hero_kind, params.fairy, params.fairy_kind)
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
    StoryParams("moon_bay", "silver_yacht", "fox_snout", "spark_charm", "Mina", "girl", "Merry", "fairy"),
    StoryParams("tidal_harbor", "small_yacht", "pig_snout", "golden_knot", "Theo", "boy", "Pearl", "fairy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show match/2.\n#show magic_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show match/2.\n#show magic_story/2."))
        print("matches:", sorted(asp.atoms(model, "match")))
        print("magic_story:", sorted(asp.atoms(model, "magic_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
