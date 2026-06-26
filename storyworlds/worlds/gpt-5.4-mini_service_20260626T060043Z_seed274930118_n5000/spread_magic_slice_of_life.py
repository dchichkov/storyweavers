#!/usr/bin/env python3
"""
A small slice-of-life story world about a little bit of magic that spreads.

Seed premise:
- A child notices a small magical effect in an ordinary place.
- The magic spreads from one object/place to another in a harmless but surprising way.
- A helper suggests a gentle fix or playful redirect.
- The story ends with the world slightly changed and calmer.

This script models a tiny, child-facing domain where magic can spread between
nearby things in everyday life.
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
# Core world model
# ---------------------------------------------------------------------------

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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"magic": 0.0, "mess": 0.0, "shine": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "calm": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    spreadable: set[str] = field(default_factory=set)
    cozy_detail: str = ""


@dataclass
class Magic:
    id: str
    name: str
    verb: str
    gerund: str
    spread_to: set[str]
    rule: str
    sparkle: str
    mood: str
    tag: str


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    action: str
    result: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.magic_chain: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind != "character"]

    def say(self, text: str) -> None:
        if text:
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.story = [[]]
        c.fired = set(self.fired)
        c.magic_chain = list(self.magic_chain)
        return c

    def nearby_targets(self, source: str) -> list[Entity]:
        # In this tiny world, magic can spread to any spreadable thing in the scene,
        # but the reasonableness gate keeps only one compatible target at a time.
        return [e for e in self.things() if e.id != source]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        indoor=True,
        spreadable={"teacup", "table", "window"},
        cozy_detail="The kettle hummed on the stove, and sunlight leaned across the floor.",
    ),
    "porch": Setting(
        place="the porch",
        indoor=False,
        spreadable={"flowerpot", "bench", "mug"},
        cozy_detail="The porch boards were warm, and the afternoon breeze moved the curtains.",
    ),
    "garden": Setting(
        place="the garden",
        indoor=False,
        spreadable={"watering can", "stone", "petal"},
        cozy_detail="The garden was small and tidy, with little paths between the plants.",
    ),
}

MAGICS = {
    "glow": Magic(
        id="glow",
        name="a warm glow",
        verb="glow softly",
        gerund="glowing softly",
        spread_to={"lamp", "cup", "window"},
        rule="A glowing thing makes nearby ordinary things glow too.",
        sparkle="gold",
        mood="wonder",
        tag="light",
    ),
    "sparkle": Magic(
        id="sparkle",
        name="a bit of sparkle",
        verb="sparkle",
        gerund="sparkling",
        spread_to={"spoon", "jar", "flowerpot"},
        rule="A sparkling thing leaves tiny sparks on the next thing nearby.",
        sparkle="silver",
        mood="delight",
        tag="sparkle",
    ),
    "bloom": Magic(
        id="bloom",
        name="a little bloom of magic",
        verb="bloom",
        gerund="blooming",
        spread_to={"plant", "petal", "mug"},
        rule="Blooming magic can drift into things that like water or sun.",
        sparkle="pink",
        mood="gentle",
        tag="bloom",
    ),
}

CHARMS = {
    "cup": Charm("cup", "teacup", "a blue teacup with a small chip", "teacup", "hand", False),
    "jar": Charm("jar", "glass jar", "a glass jar with a round lid", "jar", "table", False),
    "mug": Charm("mug", "green mug", "a green mug with a tiny flower on it", "mug", "table", False),
    "lamp": Charm("lamp", "lamp", "a little lamp with a cloth shade", "lamp", "table", False),
    "pot": Charm("pot", "flowerpot", "a flowerpot with mint in it", "flowerpot", "ground", False),
    "window": Charm("window", "window", "a window with bright curtains", "window", "wall", False),
    "spoon": Charm("spoon", "spoon", "a silver spoon", "spoon", "table", False),
}

FIXES = {
    "tidy": Fix(
        id="tidy",
        label="wipe the table and set the glowing things together",
        action="wipe",
        result="the magic settled into one calm little shine instead of jumping around",
        covers={"table", "hand"},
    ),
    "shade": Fix(
        id="shade",
        label="pull the curtain halfway closed",
        action="shade",
        result="the glow stayed gentle, and nothing else got too bright",
        covers={"window"},
    ),
    "water": Fix(
        id="water",
        label="give the plant a little water",
        action="water",
        result="the bloom magic had a place to rest, and the whole room felt softer",
        covers={"plant", "petal", "flowerpot"},
    ),
}

NAMES = ["Maya", "Leo", "Nora", "Ben", "Ivy", "Ava", "Theo", "Mina"]
PARENTS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["quiet", "curious", "gentle", "cheerful", "small", "patient"]


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def valid_pair(setting: Setting, magic: Magic, charm: Charm) -> bool:
    return charm.type in setting.spreadable and charm.type in magic.spread_to


def choose_fix(magic: Magic, charm: Charm) -> Optional[Fix]:
    if magic.id == "glow" and charm.type in {"lamp", "window"}:
        return FIXES["shade"] if charm.type == "window" else FIXES["tidy"]
    if magic.id == "sparkle" and charm.type in {"spoon", "jar", "mug"}:
        return FIXES["tidy"]
    if magic.id == "bloom" and charm.type in {"plant", "petal", "flowerpot", "mug"}:
        return FIXES["water"]
    return None


def explain_rejection(setting: Setting, magic: Magic, charm: Charm) -> str:
    return (
        f"(No story: in {setting.place}, {magic.name} does not reasonably spread to a {charm.label}. "
        f"Try a charm that matches the magic's spread.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _narrate_intro(world: World, hero: Entity, parent: Entity, charm: Entity, magic: Magic) -> None:
    world.say(
        f"{hero.id} was a {next(t for t in hero.memes if t == 'curiosity' or True)} little {hero.type} who liked noticing small things."
    )
    world.say(
        f"One ordinary afternoon, {hero.id} found {charm.phrase} in {world.setting.place}."
    )
    world.say(world.setting.cozy_detail)
    world.say(
        f"When {hero.id} touched it, it began to {magic.verb}; the little {magic.name} felt like a secret in the room."
    )


def _spread_magic(world: World, source: Entity, magic: Magic) -> list[str]:
    out: list[str] = []
    for target in world.nearby_targets(source.id):
        if target.id in world.magic_chain:
            continue
        if target.type not in magic.spread_to and target.label not in magic.spread_to:
            continue
        sig = (magic.id, source.id, target.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.magic_chain.append(target.id)
        target.meters["shine"] = target.meters.get("shine", 0.0) + 1.0
        target.memes["curiosity"] = target.memes.get("curiosity", 0.0) + 1.0
        out.append(f"Then the magic drifted into the {target.label} too.")
        break
    return out


def _narrate_turn(world: World, hero: Entity, parent: Entity, source: Entity, magic: Magic, charm: Charm) -> None:
    if source.meters.get("shine", 0.0) >= 1.0:
        world.say(
            f"{hero.id} giggled, because the {charm.label} was not the only thing that looked different now."
        )
    world.say(
        f"{parent.id} noticed the spread and said, \"Let's keep it gentle before it gets too busy.\""
    )


def _apply_fix(world: World, hero: Entity, parent: Entity, charm: Entity, magic: Magic, fix: Optional[Fix]) -> None:
    if fix is None:
        return
    world.say(
        f"{parent.id} suggested to {fix.label}."
    )
    if fix.id == "tidy":
        charm.meters["shine"] = max(0.0, charm.meters.get("shine", 0.0) - 1.0)
    elif fix.id == "shade":
        world.setting.cozy_detail = "The room felt softer with the curtain half closed."
    elif fix.id == "water":
        charm.meters["shine"] = max(0.0, charm.meters.get("shine", 0.0) - 1.0)
        world.facts["bloom_settled"] = True
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    parent.memes["calm"] = parent.memes.get("calm", 0.0) + 1.0
    world.say(fix.result + ".")


def tell(setting: Setting, magic: Magic, charm: Charm, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["curiosity"] = 1.0
    parent = world.add(Entity(id=parent_type, kind="character", type=parent_type, label=parent_type))
    source = world.add(Entity(id=charm.id, type=charm.type, label=charm.label, phrase=charm.phrase, owner=hero.id))

    world.facts.update(hero=hero, parent=parent, source=source, magic=magic, charm=charm, setting=setting)

    # Setup
    world.say(f"{hero.id} was a {trait} little {hero_type} who liked quiet afternoons.")
    world.say(f"{hero.id} found {charm.phrase} in {setting.place}.")
    world.say(f"The room felt still until the {charm.label} began to {magic.verb}.")

    # Turn
    world.para()
    world.say(f"That was strange, and then it got stranger, because the magic started to spread.")
    spread = _spread_magic(world, source, magic)
    if spread:
        world.say(spread[0])
    else:
        world.say(f"It stayed on the {charm.label}, shining like a tiny lantern.")

    # More spread if sensible
    follow = _spread_magic(world, source, magic)
    if follow:
        world.say(follow[0])

    # Resolution
    world.para()
    _narrate_turn(world, hero, parent, source, magic, charm)
    fix = choose_fix(magic, charm)
    if fix is not None:
        _apply_fix(world, hero, parent, source, magic, fix)
        world.say(f"After that, the little magic stayed put and the afternoon felt peaceful again.")
    else:
        world.say(f"{parent.id} smiled and let the magic be, because it was only a small, friendly surprise.")
        world.say(f"Before long, the glow had settled into the {charm.label}, and everything felt calm.")

    world.facts["fix"] = fix
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle slice-of-life story about a child named {f['hero'].id} who finds {f['charm'].phrase} in {f['setting'].place} and sees magic spread.",
        f"Tell a short, child-friendly story where {f['magic'].name} starts on a {f['charm'].label} and spreads to another nearby thing.",
        f"Write a calm everyday story about {f['hero'].id}, a little bit of magic, and a simple fix that makes the room peaceful again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    charm = f["charm"]
    magic = f["magic"]
    fix = f.get("fix")
    qa = [
        QAItem(
            question=f"What did {hero.id} find in {f['setting'].place}?",
            answer=f"{hero.id} found {charm.phrase} in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} touched the {charm.label}?",
            answer=f"It began to {magic.verb}, and the little magic started to spread.",
        ),
        QAItem(
            question=f"Who helped keep the magic gentle?",
            answer=f"{parent.id} helped by suggesting a calm, simple way to handle the spreading magic.",
        ),
    ]
    if fix is not None:
        qa.append(
            QAItem(
                question=f"What did {parent.id} suggest to help?",
                answer=f"{parent.id} suggested to {fix.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did the story end after the fix?",
                answer=f"The magic settled down, and the afternoon felt peaceful again.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in this story world?",
            answer="Magic is a small unusual effect that can start on one thing and spread to nearby things.",
        ),
        QAItem(
            question="Can the magic spread forever?",
            answer="No. In this world it can be calmed with a gentle everyday fix, so it does not keep spreading forever.",
        ),
        QAItem(
            question="What kind of story is this?",
            answer="It is a slice-of-life story, so the magic happens in an ordinary place and stays gentle and close to home.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
spread(M, S, T) :- magic(M), source(S), target(T), can_spread(M, T), not blocked(S, T).
settled(M, S) :- source(S), magic(M), spread(M, S, _), fix_available(M).
valid_story(Place, M, C) :- setting(Place), magic(M), charm(C), allowed(Place, M, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for t in sorted(s.spreadable):
            lines.append(asp.fact("allowed", sid, "any", t))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        for t in sorted(m.spread_to):
            lines.append(asp.fact("can_spread", mid, t))
        lines.append(asp.fact("fix_available", mid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("source", cid))
        lines.append(asp.fact("target", cid))
        lines.append(asp.fact("can_be_source", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m, c) for p in SETTINGS for m in MAGICS for c in CHARMS if valid_pair(SETTINGS[p], MAGICS[m], CHARMS[c])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    magic: str
    charm: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a small magic that spreads.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--magic", choices=MAGICS.keys())
    ap.add_argument("--charm", choices=CHARMS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, m, c) for p in SETTINGS for m in MAGICS for c in CHARMS if valid_pair(SETTINGS[p], MAGICS[m], CHARMS[c])]
    if args.place:
        combos = [x for x in combos if x[0] == args.place]
    if args.magic:
        combos = [x for x in combos if x[1] == args.magic]
    if args.charm:
        combos = [x for x in combos if x[2] == args.charm]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, magic, charm = rng.choice(sorted(combos))
    chosen_charm = CHARMS[charm]
    gender = args.gender or rng.choice(sorted(chosen_charm.genders))
    if args.gender and args.gender not in chosen_charm.genders:
        raise StoryError(f"(No story: a {chosen_charm.label} does not fit that gender choice here.)")
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, charm=charm, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MAGICS[params.magic], CHARMS[params.charm], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in SETTINGS:
            for m in MAGICS:
                for c in CHARMS:
                    if valid_pair(SETTINGS[p], MAGICS[m], CHARMS[c]):
                        params = StoryParams(place=p, magic=m, charm=c, name="Maya", gender="girl", parent="mother", trait="curious")
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
