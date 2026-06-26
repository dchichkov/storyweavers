#!/usr/bin/env python3
"""
storyworlds/worlds/sanitary_monstrosity_ninety_sound_effects_myth.py
=====================================================================

A small mythic story world about a sanitary monstrosity, ninety echoes, and
sound effects that matter in the state of the world.

Premise:
- A child hero tends a holy bath-house and meets a fearsome but clean-loving
  monstrosity.
- The monstrosity grows harsh and noisy when soot or slime spreads.
- Careful washing, a ritual of ninety clear sound effects, and a brave helper
  turn the fright into a blessing.

The world is intentionally tiny and constraint-checked:
- Only a few places, tools, and creature variants exist.
- Each generated story is a full beginning/middle/end.
- Sound effects are not decorative: they are part of the causal setup and the
  ending image.
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


# ---------------------------------------------------------------------------
# Core model
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
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    sacred: bool = False


@dataclass
class Rite:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    sound: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    clears: set[str]
    covers: set[str]
    sound: str
    ritual: str


@dataclass
class Monster:
    id: str
    label: str
    phrase: str
    type: str
    temperament: str
    teeth: int
    sound: str
    loves: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.noise: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.noise = list(self.noise)
        return clone


# ---------------------------------------------------------------------------
# World registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "temple": Setting(place="the temple pool", affords={"wash", "chant", "polish"}, sacred=True),
    "well": Setting(place="the moon-well", affords={"wash", "chant"}, sacred=True),
    "courtyard": Setting(place="the stone courtyard", affords={"wash", "polish", "chant"}, sacred=False),
}

RITES = {
    "wash": Rite(
        id="wash",
        verb="wash the sacred stones",
        gerund="washing the sacred stones",
        risk="would stain the basin",
        mess="slime",
        zone={"hands", "feet"},
        sound="splish-splash",
        keyword="wash",
    ),
    "polish": Rite(
        id="polish",
        verb="polish the bronze altar",
        gerund="polishing the bronze altar",
        risk="would dull the shine",
        mess="soot",
        zone={"hands", "arms"},
        sound="scrape-scrape",
        keyword="polish",
    ),
    "chant": Rite(
        id="chant",
        verb="sing the cleansing hymn",
        gerund="singing the cleansing hymn",
        risk="would wake the gloom",
        mess="echo",
        zone={"mouth", "chest"},
        sound="hum-hum",
        keyword="chant",
    ),
}

TOOLS = {
    "soap": Tool(
        id="soap",
        label="river soap",
        phrase="a round cake of river soap",
        clears={"slime"},
        covers={"hands", "feet"},
        sound="slip",
        ritual="scrubbed the stones with river soap",
    ),
    "cloth": Tool(
        id="cloth",
        label="linen cloth",
        phrase="a clean linen cloth",
        clears={"soot"},
        covers={"hands", "arms"},
        sound="swish",
        ritual="wiped the bronze until it shone",
    ),
    "bell": Tool(
        id="bell",
        label="little bronze bells",
        phrase="ninety little bronze bells",
        clears={"echo"},
        covers={"mouth", "chest"},
        sound="ting",
        ritual="rang the bells in a steady circle",
    ),
}

MONSTROSITIES = {
    "guardian": Monster(
        id="guardian",
        label="sanitary monstrosity",
        phrase="a sanitary monstrosity with a moon-white mane",
        type="monstrosity",
        temperament="stern",
        teeth=90,
        sound="GRR-CHIME",
        loves={"slime", "soot", "echo"},
    ),
    "lakebeast": Monster(
        id="lakebeast",
        label="sanitary monstrosity",
        phrase="a sanitary monstrosity from the deep lake",
        type="monstrosity",
        temperament="watchful",
        teeth=90,
        sound="HMM-CLANG",
        loves={"slime", "echo"},
    ),
}

HERO_NAMES = ["Ari", "Nia", "Milo", "Tala", "Rin", "Sora", "Lio"]
TRAITS = ["brave", "curious", "gentle", "steadfast", "small", "bright"]


@dataclass
class StoryParams:
    setting: str
    rite: str
    tool: str
    monster: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def rite_is_risky(rite: Rite) -> bool:
    return bool(rite.mess)


def tool_fits(rite: Rite, tool: Tool) -> bool:
    return rite.mess in tool.clears and len(rite.zone & tool.covers) > 0


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for r in RITES.values():
            for t in TOOLS.values():
                if tool_fits(r, t):
                    out.append((s, r.id, t.id))
    return out


def explain_rejection(rite: Rite, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot honestly fix {rite.gerund}. "
        f"Try a tool that clears {rite.mess} and covers the same body region.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_ruin(world: World, hero: Entity, rite: Rite, tool: Tool, monster: Entity) -> dict:
    sim = world.copy()
    act(sim, hero.id, rite, tool, monster, narrate=False)
    return {
        "monster_upset": sim.get(monster.id).memes.get("alarm", 0.0) >= THRESHOLD,
        "cleared": sim.get(monster.id).memes.get("calm", 0.0) >= THRESHOLD,
    }


def act(world: World, hero_id: str, rite: Rite, tool: Tool, monster: Entity, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    if rite.id not in world.setting.affords:
        raise StoryError(f"The {world.setting.place} cannot host {rite.verb}.")
    hero.meters[rite.mess] = hero.meters.get(rite.mess, 0.0) + 1
    world.noise.append(rite.sound)
    sig = ("mess", hero.id, rite.id)
    if sig not in world.fired:
        world.fired.add(sig)
        monster.memes["alarm"] = monster.memes.get("alarm", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} began {rite.gerund}, and the air answered with {rite.sound}.")


def clean(world: World, hero: Entity, tool: Tool, monster: Entity, rite: Rite) -> None:
    hero.meters[tool.id] = hero.meters.get(tool.id, 0.0) + 1
    monster.memes["calm"] = monster.memes.get("calm", 0.0) + 1
    monster.memes["alarm"] = 0.0
    world.noise.append(tool.sound)
    world.say(
        f"{hero.id} used {tool.label}; {tool.sound}, {tool.sound}. "
        f"{tool.ritual.capitalize()}, and the {monster.label} stopped glaring."
    )


def tell(setting: Setting, rite: Rite, tool: Tool, monster_def: Monster,
         hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    monster = world.add(Entity(
        id="monster",
        kind="character",
        type=monster_def.type,
        label=monster_def.label,
        phrase=monster_def.phrase,
    ))
    world.facts["hero"] = hero
    world.facts["monster"] = monster
    world.facts["rite"] = rite
    world.facts["tool"] = tool
    world.facts["monster_def"] = monster_def
    world.facts["trait"] = trait

    world.say(
        f"In {setting.place}, {hero.id} was a {trait} child who served the old waters."
    )
    world.say(
        f"Under the altar lamps lived {monster_def.phrase}. "
        f"People called {monster_def.pronoun('object') if hasattr(monster_def, 'pronoun') else 'it'} "
        f"a sanitary monstrosity, for {monster_def.teeth} silver teeth clicked in its long jaw."
    )
    world.say(
        f"Whenever the stones were clean, the monster's great chest made a soft {monster_def.sound}."
    )

    world.para()
    world.say(
        f"One evening, {hero.id} wanted to {rite.verb}, but a dark smear crawled over the basin."
    )
    act(world, hero.id, rite, tool, monster)
    world.say(
        f"The smear made the holy place feel wrong, and the monstrosity answered with a harsh {monster_def.sound}."
    )

    world.para()
    if predict_ruin(world, hero, rite, tool, monster)["monster_upset"]:
        world.say(
            f"{hero.id} saw the trouble and fetched {tool.phrase}."
        )
        clean(world, hero, tool, monster, rite)
        world.say(
            f"Then {hero.id} whispered the old number: ninety, ninety, ninety."
        )
        world.say(
            f"At each count the bells rang, {('ting, ' * 3).strip(', ')}."
        )
        monster.memes["reverence"] = monster.memes.get("reverence", 0.0) + 1
        world.say(
            f"The {monster.label} bowed its head, and the pool shone sanitary again."
        )
    else:
        raise StoryError("(No story: the chosen rite and tool do not create a real turn.)")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for children about a {f["monster_def"].label} and the word "sanitary".',
        f'Write a story where {f["hero"].id} faces a monstrous guardian, uses {f["tool"].label}, and repeats "ninety".',
        f'Tell a small myth with clear sound effects like {f["rite"].sound} and {f["tool"].sound}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    monster = f["monster_def"]
    rite = f["rite"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {f['trait']} child serving the old waters.",
        ),
        QAItem(
            question=f"What problem did {hero.id} face?",
            answer=(
                f"{hero.id} wanted to {rite.verb}, but a smear of {rite.mess} made the "
                f"sanitary place feel wrong and woke the monstrosity."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} help the monstrosity calm down?",
            answer=(
                f"{hero.id} used {tool.label} and the cleansing ritual, then counted to ninety "
                f"while the bells said {tool.sound}. That made the monster bow and grow quiet."
            ),
        ),
        QAItem(
            question=f"What proved that the ending changed?",
            answer=(
                f"By the end, the pool was sanitary again, the monster had calmed, and the "
                f"last sound was a gentle echo of {tool.sound} and the ninety bells."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "sanitary": [
        QAItem(
            question="What does sanitary mean?",
            answer="Sanitary means clean and safe, especially where water, food, or people need to stay free from dirt and germs.",
        )
    ],
    "monstrosity": [
        QAItem(
            question="What is a monstrosity in a myth?",
            answer="A monstrosity is a huge strange creature. In myths it may look frightening, but it can still have a purpose or a heart.",
        )
    ],
    "ninety": [
        QAItem(
            question="What number comes after eighty-nine?",
            answer="Ninety comes after eighty-nine.",
        )
    ],
    "sound": [
        QAItem(
            question="Why do stories sometimes use sound effects?",
            answer="Sound effects help readers hear the action in their heads, so the story feels lively and easy to imagine.",
        )
    ],
    "myth": [
        QAItem(
            question="What makes a story feel like a myth?",
            answer="A myth often feels old, grand, and a little magical, with strong symbols, special places, and creatures that seem larger than ordinary life.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["sanitary"])
    out.extend(WORLD_KNOWLEDGE["monstrosity"])
    out.extend(WORLD_KNOWLEDGE["ninety"])
    out.extend(WORLD_KNOWLEDGE["sound"])
    out.extend(WORLD_KNOWLEDGE["myth"])
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
% A rite is compatible with a tool when the tool clears the rite's mess and
% covers at least one of the rite's at-risk body regions.
fits(R,T) :- rite(R), tool(T), mess_of(R,M), clears(T,M), affects(R,Z), covers(T,C), overlap(Z,C).

valid(Setting,R,T) :- setting(Setting), affords(Setting,R), fits(R,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("mess_of", rid, r.mess))
        for z in sorted(r.zone):
            lines.append(asp.fact("affects", rid, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.clears):
            lines.append(asp.fact("clears", tid, m))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic sanitary monstrosity story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--monster", choices=MONSTROSITIES)
    ap.add_argument("--name", choices=HERO_NAMES)
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
    if args.rite and args.tool and not tool_fits(RITES[args.rite], TOOLS[args.tool]):
        raise StoryError(explain_rejection(RITES[args.rite], TOOLS[args.tool]))
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.rite is None or c[1] == args.rite)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rite, tool = rng.choice(sorted(filtered))
    monster = args.monster or rng.choice(sorted(MONSTROSITIES))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, rite=rite, tool=tool, monster=monster, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        RITES[params.rite],
        TOOLS[params.tool],
        MONSTROSITIES[params.monster],
        params.name,
        params.trait,
    )
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
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"  sounds: {world.noise}")
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


CURATED = [
    StoryParams(setting="temple", rite="wash", tool="soap", monster="guardian", name="Nia", trait="brave"),
    StoryParams(setting="courtyard", rite="polish", tool="cloth", monster="lakebeast", name="Ari", trait="steadfast"),
    StoryParams(setting="well", rite="chant", tool="bell", monster="guardian", name="Tala", trait="curious"),
]


def asp_valid() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid()
        print(f"{len(models)} compatible combos:\n")
        for setting, rite, tool in models:
            print(f"  {setting:10} {rite:8} {tool:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
