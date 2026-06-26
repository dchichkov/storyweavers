#!/usr/bin/env python3
"""
storyworlds/worlds/minimum_weapon_sharing_surprise_kindness_slice_of.py
========================================================================

A small slice-of-life story world about sharing a limited toy weapon:
a harmless pretend weapon that a child wants to keep, but kindness and
surprise turn the day into a better one when it is shared with someone who
needs it less, then everyone gets included.

The world is intentionally tiny and constraint-checked:
- one setting
- one shared toy weapon
- one surprise visit or moment
- one kindness turn
- one ending image that proves the sharing changed the day

The seed words "minimum" and "weapon" are included in the world vocabulary
and can appear in the generated story when appropriate.
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
# World data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    carried_by: Optional[str] = None
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


@dataclass
class Setting:
    place: str
    time_of_day: str
    mood: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Weapon:
    id: str
    label: str
    phrase: str
    kind: str
    safe: bool = True
    shareable: bool = True


@dataclass
class StoryParams:
    setting: str
    weapon: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    surprise: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "playground": Setting(
        place="the playground",
        time_of_day="late afternoon",
        mood="soft and busy",
        supports={"sharing", "surprise", "kindness"},
    ),
    "backyard": Setting(
        place="the backyard",
        time_of_day="after snack time",
        mood="quiet and warm",
        supports={"sharing", "surprise", "kindness"},
    ),
    "apartment_courtyard": Setting(
        place="the apartment courtyard",
        time_of_day="early evening",
        mood="calm and neighborly",
        supports={"sharing", "surprise", "kindness"},
    ),
}

WEAPONS = {
    "water_pistol": Weapon(
        id="water_pistol",
        label="water pistol",
        phrase="a tiny blue water pistol",
        kind="toy weapon",
        safe=True,
        shareable=True,
    ),
    "foam_sword": Weapon(
        id="foam_sword",
        label="foam sword",
        phrase="a light foam sword with a red handle",
        kind="toy weapon",
        safe=True,
        shareable=True,
    ),
    "popper_blaster": Weapon(
        id="popper_blaster",
        label="popper blaster",
        phrase="a little popper blaster that made funny puffs of air",
        kind="toy weapon",
        safe=True,
        shareable=True,
    ),
}

SURPRISES = {
    "cousin_visit": "a cousin stopped by with a paper bag of snacks",
    "new_neighbor": "a new neighbor came out to wave hello",
    "lost_friend": "a friend suddenly showed up after a long week away",
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Zoe", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah", "Finn", "Leo"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def pronoun_for(gender: str) -> dict[str, str]:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}
    return {"subject": "he", "object": "him", "possessive": "his"}


def valid_combo(setting: Setting, weapon: Weapon, surprise: str) -> bool:
    return (
        "sharing" in setting.supports
        and "kindness" in setting.supports
        and weapon.safe
        and weapon.shareable
        and surprise in SURPRISES
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for w_id, weapon in WEAPONS.items():
            for sur in SURPRISES:
                if valid_combo(setting, weapon, sur):
                    out.append((s_id, w_id, sur))
    return out


def introduce(world: World, hero: Entity, helper: Entity, weapon: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved quiet play at {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} especially loved {weapon.label}, "
        f"which felt exciting without being too big."
    )
    world.say(
        f"{helper.id} liked the same corner of the playground and smiled whenever the game stayed kind."
    )


def desire(world: World, hero: Entity, weapon: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted to keep {hero.pronoun('possessive')} {weapon.label} close because it was the minimum thing needed for the game."
    )


def surprise_turn(world: World, helper: Entity, surprise: str) -> None:
    world.say(
        f"Then, unexpectedly, {SURPRISES[surprise]}."
    )
    world.say(
        f"{helper.id} noticed that someone else looked a little left out and gently stepped closer."
    )


def share(world: World, hero: Entity, helper: Entity, weapon: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    weapon.held_by = helper.id
    world.say(
        f"{hero.id} held out {hero.pronoun('possessive')} {weapon.label} and said it was okay to take turns."
    )
    world.say(
        f"{helper.id} took {weapon.it()} carefully, and the two children made space for each other."
    )


def resolve(world: World, hero: Entity, helper: Entity, weapon: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"Soon they were both laughing, and the game became better because it was shared."
    )
    world.say(
        f"At the end, the {weapon.label} was still only one toy, but it had made room for two happy players."
    )


def tell(setting: Setting, weapon_cfg: Weapon, surprise_key: str, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={"attention": 1.0},
        memes={"joy": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        meters={"attention": 1.0},
        memes={"joy": 1.0},
    ))
    weapon = world.add(Entity(
        id=weapon_cfg.id,
        kind="thing",
        type="weapon",
        label=weapon_cfg.label,
        phrase=weapon_cfg.phrase,
        owner=hero.id,
        held_by=hero.id,
    ))

    introduce(world, hero, helper, weapon)
    world.para()
    desire(world, hero, weapon)
    surprise_turn(world, helper, surprise_key)
    share(world, hero, helper, weapon)
    world.para()
    resolve(world, hero, helper, weapon)

    world.facts.update(
        hero=hero,
        helper=helper,
        weapon=weapon,
        surprise=surprise_key,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the setting supports the slice-of-life values,
% the weapon is safe and shareable, and the surprise is one of the registered beats.
valid_story(S, W, R) :- setting(S), weapon(W), surprise(R),
                        supports(S, sharing), supports(S, kindness),
                        safe(W), shareable(W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(s.supports):
            lines.append(asp.fact("supports", sid, tag))
    for wid, w in WEAPONS.items():
        lines.append(asp.fact("weapon", wid))
        if w.safe:
            lines.append(asp.fact("safe", wid))
        if w.shareable:
            lines.append(asp.fact("shareable", wid))
    for rid in SURPRISES:
        lines.append(asp.fact("surprise", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child about sharing a "{f["weapon"].label}" at {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} wants to keep {f['hero'].pronoun('possessive')} {f['weapon'].label}, but a surprise makes kindness easier.",
        f'Write a simple story that includes the words "minimum", "weapon", "sharing", "surprise", and "kindness".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    weapon = f["weapon"]
    setting = f["setting"]
    surprise = f["surprise"]

    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=f"It is about {hero.id}, who plays there with {helper.id} and a {weapon.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want at first?",
            answer=f"{hero.id} wanted to keep {hero.pronoun('possessive')} {weapon.label} close and use it as the minimum toy needed for the game.",
        ),
        QAItem(
            question=f"What surprise happened during the story?",
            answer=f"{SURPRISES[surprise]}. That small surprise helped the children notice someone else and choose kindness.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {weapon.label} being shared, so both children could play together happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something or have a turn too.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect to happen.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What does minimum mean?",
            answer="Minimum means the smallest amount or the least that is needed.",
        ),
        QAItem(
            question="What is a toy weapon in this story?",
            answer="It is a pretend weapon, like a toy water pistol or foam sword, used for play instead of real fighting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "thing":
            bits.append(f"held_by={e.held_by}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about sharing a toy weapon kindly.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--weapon", choices=WEAPONS.keys())
    ap.add_argument("--surprise", choices=SURPRISES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    weapon = args.weapon or rng.choice(list(WEAPONS))
    surprise = args.surprise or rng.choice(list(SURPRISES))

    if not valid_combo(SETTINGS[setting], WEAPONS[weapon], surprise):
        raise StoryError("This setting/weapon/surprise combination does not make a gentle sharing story.")

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = BOY_NAMES if helper_gender == "boy" else GIRL_NAMES
    helper_name = args.helper_name or rng.choice([n for n in helper_pool if n != hero_name] or helper_pool)

    return StoryParams(
        setting=setting,
        weapon=weapon,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        surprise=surprise,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        WEAPONS[params.weapon],
        params.surprise,
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s_id, w_id, r_id in valid_combos():
            p = StoryParams(
                setting=s_id,
                weapon=w_id,
                surprise=r_id,
                hero_name="Mia",
                hero_gender="girl",
                helper_name="Owen",
                helper_gender="boy",
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
