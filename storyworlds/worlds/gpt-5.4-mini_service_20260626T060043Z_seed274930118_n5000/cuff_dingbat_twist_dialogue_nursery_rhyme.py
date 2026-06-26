#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a little cuff, a dingbat, a twist, and a
bit of dialogue.

Premise:
- A child wears a neat cuff.
- A cheerful dingbat (a little bell-shaped toy) goes missing or gets stuck.
- A gentle twist reveals the cuff can help.

The prose aims for a sing-song, child-facing feel while still being driven by a
small simulation: objects have physical meters and emotional memes, state changes
cause the story beats, and the ending image proves what changed.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    role: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("tight", "stuck", "shiny", "lost", "tug", "joy", "worry", "surprise", "pride"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    plural: bool = False
    sound: str = ""
    mood: str = ""
    can_twist: bool = False


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    parent_type: str
    toy: str
    cuff: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affords={"twist"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"twist"}),
    "windowseat": Setting(place="the window seat", indoors=True, affords={"twist"}),
}

HEROES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Finn"]
PARENT_TYPES = ["mother", "father"]
HERO_TYPES = ["girl", "boy"]

CUFFS = {
    "redcuff": Toy(
        id="redcuff",
        label="red cuff",
        phrase="a neat red cuff",
        type="thing",
        sound="soft",
        mood="bright",
        can_twist=True,
    ),
    "bluecuff": Toy(
        id="bluecuff",
        label="blue cuff",
        phrase="a tiny blue cuff",
        type="thing",
        sound="tiny",
        mood="calm",
        can_twist=True,
    ),
    "goldcuff": Toy(
        id="goldcuff",
        label="gold cuff",
        phrase="a shiny gold cuff",
        type="thing",
        sound="bright",
        mood="proud",
        can_twist=True,
    ),
}

DINGBATS = {
    "dingbatbell": Toy(
        id="dingbatbell",
        label="dingbat",
        phrase="a little dingbat with a bell",
        type="thing",
        sound="ding-ding",
        mood="bouncy",
        can_twist=False,
    ),
    "dingbatspool": Toy(
        id="dingbatspool",
        label="dingbat",
        phrase="a round dingbat spool",
        type="thing",
        sound="zizz",
        mood="twirly",
        can_twist=False,
    ),
    "dingbatkite": Toy(
        id="dingbatkite",
        label="dingbat",
        phrase="a paper dingbat kite",
        type="thing",
        sound="flap",
        mood="airy",
        can_twist=False,
    ),
}

CURATED = [
    StoryParams(setting="nursery", hero_name="Mia", hero_type="girl", parent_type="mother", toy="dingbatbell", cuff="redcuff"),
    StoryParams(setting="playroom", hero_name="Noah", hero_type="boy", parent_type="father", toy="dingbatspool", cuff="bluecuff"),
    StoryParams(setting="windowseat", hero_name="Ava", hero_type="girl", parent_type="mother", toy="dingbatkite", cuff="goldcuff"),
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting: str, toy: str, cuff: str) -> bool:
    return setting in SETTINGS and toy in DINGBATS and cuff in CUFFS and CUFFS[cuff].can_twist


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, c) for s in SETTINGS for t in DINGBATS for c in CUFFS if valid_combo(s, t, c)]


def explain_rejection(setting: str, toy: str, cuff: str) -> str:
    return (
        f"(No story: this nursery-rhyme twist needs a cuff that can help turn the scene, "
        f"and {cuff} is not a fit with {toy} at {setting}.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, toy: Entity, cuff: Entity) -> dict:
    sim = world.copy()
    _twist(sim, sim.get(hero.id), sim.get(toy.id), sim.get(cuff.id), narrate=False)
    return {
        "freed": sim.get(toy.id).meters["stuck"] < THRESHOLD,
        "joy": sim.get(hero.id).memes["joy"],
    }


def _twist(world: World, hero: Entity, toy: Entity, cuff: Entity, narrate: bool = True) -> None:
    if ("twist", toy.id) in world.fired:
        return
    world.fired.add(("twist", toy.id))
    toy.meters["stuck"] = 0.0
    toy.meters["lost"] = 0.0
    hero.memes["surprise"] += 1
    hero.memes["joy"] += 1
    cuff.meters["shiny"] += 1
    cuff.memes["pride"] += 1
    if narrate:
        world.say(f"The cuff gave a little twist, and the dingbat came free with a bright little ring.")


def _make_stuck(world: World, hero: Entity, toy: Entity, cuff: Entity) -> None:
    hero.memes["worry"] += 1
    toy.meters["stuck"] = 1.0
    toy.meters["lost"] = 1.0
    cuff.meters["tight"] = 1.0
    world.say(f"The little dingbat had a snaggle, and the cuff sat tight as a button.")


def _dialogue(world: World, hero: Entity, parent: Entity, toy: Entity, cuff: Entity) -> None:
    world.say(f'"Oh dear," said {hero.id}, "my {toy.label} is caught!"')
    world.say(f'"Not dear," said {parent.label}, "just give the cuff a careful twist."')


def tell(setting: Setting, toy_cfg: Toy, cuff_cfg: Toy, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type, role="parent"))
    toy = world.add(Entity(id=toy_cfg.id, type=toy_cfg.type, label=toy_cfg.label, phrase=toy_cfg.phrase, owner=hero.id))
    cuff = world.add(Entity(id=cuff_cfg.id, type="thing", label=cuff_cfg.label, phrase=cuff_cfg.phrase, owner=hero.id))

    hero.memes["curious"] = 1.0
    cuff.worn_by = hero.id

    world.say(f"Little {hero.id} in {setting.place} wore {cuff.phrase}.")
    world.say(f"Near {hero.id} sat {toy.phrase}, all bouncy and bright.")
    world.para()
    world.say(f"{hero.id} hummed a nursery tune, nice and light.")
    world.say(f"Then the dingbat gave one tiny hop and slipped into a tricky place.")

    world.para()
    _make_stuck(world, hero, toy, cuff)
    _dialogue(world, hero, parent, toy, cuff)
    _twist(world, hero, toy, cuff)

    world.para()
    world.say(f'{hero.id} smiled and sang, "Twist and turn!"')
    world.say(f"The dingbat rang, the cuff gleamed, and both were ready for another playday.")

    world.facts.update(hero=hero, parent=parent, toy=toy, cuff=cuff, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, toy, cuff, setting = f["hero"], f["toy"], f["cuff"], f["setting"]
    return [
        f"Write a short nursery-rhyme story about {hero.id}, a {cuff.label}, and a {toy.label} in {setting.place}.",
        f"Tell a child-friendly twist story where {hero.id} speaks with a parent and saves {toy.label} using {cuff.label}.",
        f"Make a gentle rhyme about a dingbat getting stuck and a cuff helping it come loose.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, toy, cuff, setting = f["hero"], f["parent"], f["toy"], f["cuff"], f["setting"]
    return [
        QAItem(
            question=f"Who was the little story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and the parent who helped {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What got stuck in the story?",
            answer=f"The {toy.label} got stuck, and {hero.id} worried for a moment.",
        ),
        QAItem(
            question=f"What helped the dingbat come free?",
            answer=f"The {cuff.label} helped, because a careful twist made the little snaggle loosen.",
        ),
        QAItem(
            question=f"What did the parent tell {hero.id} to do?",
            answer=f"{parent.label.capitalize()} told {hero.id} to give the cuff a careful twist.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the dingbat ringing happily, the cuff shining, and {hero.id} smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a cuff?",
            answer="A cuff is the part at the end of a sleeve or a little band that can sit snugly and be turned or adjusted.",
        ),
        QAItem(
            question="What is a dingbat in this storyworld?",
            answer="A dingbat is a tiny playful thing that can bounce, ring, or spin, like a little toy with a funny sound.",
        ),
        QAItem(
            question="What does it mean to twist something?",
            answer="To twist something is to turn it gently around so it changes position.",
        ),
    ]
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(S, T, C) :- setting(S), toy(T), cuff(C), twisty(C), affords(S, twist).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in DINGBATS.items():
        lines.append(asp.fact("toy", tid))
        if t.can_twist:
            lines.append(asp.fact("twisty", tid))
    for cid, c in CUFFS.items():
        lines.append(asp.fact("cuff", cid))
        if c.can_twist:
            lines.append(asp.fact("twisty", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: cuff, dingbat, twist, dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=DINGBATS)
    ap.add_argument("--cuff", choices=CUFFS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.setting and args.toy and args.cuff and not valid_combo(args.setting, args.toy, args.cuff):
        raise StoryError(explain_rejection(args.setting, args.toy, args.cuff))
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.toy is None or c[1] == args.toy)
        and (args.cuff is None or c[2] == args.cuff)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, cuff = rng.choice(filtered)
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HEROES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(setting=setting, hero_name=name, hero_type=gender, parent_type=parent, toy=toy, cuff=cuff)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DINGBATS[params.toy], CUFFS[params.cuff], params.hero_name, params.hero_type, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, toy, cuff) combos:\n")
        for s, t, c in triples:
            print(f"  {s:10} {t:12} {c}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.toy} with {p.cuff} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
