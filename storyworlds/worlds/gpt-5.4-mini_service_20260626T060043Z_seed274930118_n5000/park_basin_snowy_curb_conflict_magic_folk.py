#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/park_basin_snowy_curb_conflict_magic_folk.py
===============================================================================================================

A small folk-tale storyworld set beside a snowy curb at the park, built from
the seed words park and basin, with magic and conflict as the central motion.

Premise:
- A young folk-tale hero finds a basin on a snowy curb beside the park.
- The basin is not ordinary: it answers to a little magic warmth.
- A second character wants the basin for themselves, causing a gentle conflict.

Turn:
- The hero tries to use the basin's magic to help, but the rival claims it.
- The quarrel grows until the hero chooses a wiser spell: sharing.

Resolution:
- The basin's magic warms the snow, the conflict softens, and the ending image
  shows the basin steaming softly on the curb while peace returns.

This script follows the Storyweavers contract:
- stdlib only
- StoryParams + registries + build_parser + resolve_params + generate + emit + main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- ASP twin + Python reasonableness gate + --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("cold", "wet", "warm", "magic"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "conflict", "desire", "greed", "kindness", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the park"
    detail: str = "a snowy curb"
    affords: set[str] = field(default_factory=set)


@dataclass
class Basin:
    label: str
    phrase: str
    region: str = "hands"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Magic:
    id: str
    label: str
    spell: str
    effect: str
    bonus: str
    counter: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.detail = setting.detail

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_magic_warm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["magic"] < THRESHOLD:
            continue
        sig = ("warm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["warm"] += 1
        e.meters["cold"] = max(0.0, e.meters["cold"] - 1)
        out.append(f"A small warmth clung to {e.id}.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id) if "hero" in world.facts else None
    rival = world.get(world.facts["rival"].id) if "rival" in world.facts else None
    basin = world.get(world.facts["basin"].id) if "basin" in world.facts else None
    if not hero or not rival or not basin:
        return out
    if hero.memes["desire"] < THRESHOLD or rival.memes["greed"] < THRESHOLD:
        return out
    sig = ("conflict", hero.id, rival.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    rival.memes["conflict"] += 1
    out.append("__conflict__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] = 0.0
        e.memes["calm"] += 1
        out.append(f"The quarrel in {e.id}'s chest softened.")
    return out


CAUSAL_RULES = [
    Rule("magic_warm", _r_magic_warm),
    Rule("conflict", _r_conflict),
    Rule("calm", _r_calm),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"Beside the {setting.place}, {setting.detail} waited under a hush of snow."


def basin_is_at_risk(setting: Setting, basin: Basin) -> bool:
    return basin.label == "basin" and "snowy curb" in setting.detail


def select_magic(setting: Setting, basin: Basin) -> Optional[Magic]:
    for magic in MAGICS:
        if basin_is_at_risk(setting, basin) and basin.region in magic.tags:
            return magic
    return None


def predict_story(world: World, hero: Entity, magic: Magic, basin_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(hero.id), magic, narrate=False)
    basin = sim.get(basin_id)
    return {
        "warmer": basin.meters["warm"] >= THRESHOLD,
        "conflict": sim.get(hero.id).memes["conflict"] >= THRESHOLD,
    }


def _do_magic(world: World, actor: Entity, magic: Magic, narrate: bool = True) -> None:
    actor.meters["magic"] += 1
    actor.memes["joy"] += 1
    actor.memes["desire"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved quiet stories and snowy days.")


def basin_found(world: World, hero: Entity, basin: Entity) -> None:
    world.say(
        f"One winter morning, {hero.id} found {hero.pronoun('possessive')} {basin.label} "
        f"on a snowy curb by the {world.setting.place}."
    )
    world.say(
        f"The {basin.label} looked ordinary, but {hero.id} could feel a little magic hiding inside it."
    )


def rival_arrives(world: World, hero: Entity, rival: Entity, basin: Entity) -> None:
    rival.memes["greed"] += 1
    world.say(
        f"Then {rival.id} came by and said, \"That {basin.label} should be mine.\" "
        f"{hero.id} hugged {hero.pronoun('possessive')} hands around it."
    )


def warn(world: World, hero: Entity, rival: Entity, basin: Entity, magic: Magic) -> bool:
    pred = predict_story(world, hero, magic, basin.id)
    if not pred["warmer"]:
        return False
    world.facts["magic_name"] = magic.label
    world.say(
        f"\"If we pull the magic the wrong way, the snow will turn slushy and nobody will be happy,\" "
        f"{hero.pronoun('possessive')} grandparent said."
    )
    return True


def resist(world: World, hero: Entity, rival: Entity, basin: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"But {hero.id} still wanted to keep the {basin.label} close, and {rival.id} wanted it even more."
    )
    world.say(
        f"Their words grew sharp, and the little folk-tale conflict stood between them like a cold fence."
    )


def share_spell(world: World, hero: Entity, rival: Entity, basin: Entity, magic: Magic) -> None:
    hero.memes["kindness"] += 1
    hero.memes["calm"] += 1
    rival.memes["kindness"] += 1
    rival.memes["greed"] = 0.0
    world.say(
        f"At last {hero.id} remembered a kinder spell. {hero.id} tapped the {basin.label} and whispered, "
        f"\"{magic.spell}.\""
    )
    world.say(
        f"The magic did not snatch the basin away; it spread warmth for both of them, and the quarrel loosened."
    )


def ending(world: World, hero: Entity, rival: Entity, basin: Entity, magic: Magic) -> None:
    basin.meters["warm"] += 1
    hero.memes["conflict"] = 0.0
    rival.memes["conflict"] = 0.0
    world.say(
        f"In the end, the {basin.label} sat steaming softly on the snowy curb, "
        f"while {hero.id} and {rival.id} shared its gentle glow beside the park."
    )
    world.say(
        f"The snow stayed white around them, and the tiny basin of magic made the cold place feel friendly."
    )


def tell(setting: Setting, basin_cfg: Basin, magic: Magic,
         hero_name: str = "Mara", hero_type: str = "girl",
         rival_name: str = "Old Tovin", rival_type: str = "man",
         parent_type: str = "grandmother", trait: str = "brave") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "gentle"]))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type, traits=["rival", "hungry"]))
    parent = world.add(Entity(id=parent_type.title(), kind="character", type=parent_type, traits=["wise"]))
    basin = world.add(Entity(
        id="basin",
        type="basin",
        label=basin_cfg.label,
        phrase=basin_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    world.facts.update(hero=hero, rival=rival, parent=parent, basin=basin, magic=magic, setting=setting)

    intro(world, hero)
    basin_found(world, hero, basin)
    world.para()
    rival_arrives(world, hero, rival, basin)
    warn(world, hero, rival, basin, magic)
    resist(world, hero, rival, basin)
    world.para()
    share_spell(world, hero, rival, basin, magic)
    ending(world, hero, rival, basin, magic)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "snowy-curb": Setting(place="the park", detail="a snowy curb"),
}

BASINS = {
    "basin": Basin(label="basin", phrase="an old brass basin"),
}

MAGICS = [
    Magic(
        id="warmth",
        label="warmth magic",
        spell="Warm, little basin, warm",
        effect="heats the basin and softens the snow",
        bonus="shared warmth",
        counter="greed",
        tags={"hands"},
    ),
]

GIRL_NAMES = ["Mara", "Nina", "Lena", "Iris", "Sera", "Tara"]
BOY_NAMES = ["Oren", "Pax", "Milo", "Jory", "Nico", "Evan"]
RIVAL_NAMES = ["Old Tovin", "Bram", "Kest", "Moss"]
TRAITS = ["brave", "gentle", "curious", "lively"]


@dataclass
class StoryParams:
    place: str
    basin: str
    magic: str
    name: str
    gender: str
    rival: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "park": [("What is a park?", "A park is a place with paths, grass, and space to walk or play.")],
    "basin": [("What is a basin?", "A basin is a bowl-like container that can hold water or other things.")],
    "magic": [("What is magic in a folk tale?", "In a folk tale, magic is a special power that can change things in an amazing way.")],
    "snow": [("What is snow?", "Snow is soft frozen water that falls from clouds and covers the ground like a white blanket.")],
    "curb": [("What is a curb?", "A curb is the edge of a road or path, often a little raised border beside the street.")],
    "conflict": [("What is a conflict in a story?", "A conflict is a problem or disagreement that characters must work through.")],
    "shared": [("Why is sharing helpful?", "Sharing helps people work together and feel calmer instead of fighting over one thing.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for basin_id, basin in BASINS.items():
            for magic in MAGICS:
                if basin_is_at_risk(setting, basin) and basin.region in magic.tags:
                    combos.append((place, basin_id, magic.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a {f["basin"].label} on a snowy curb at the park.',
        f'Tell a gentle story where {f["hero"].id} and {f["rival"].id} disagree over a {f["basin"].label}, then solve it with magic.',
        f'Write a simple story that includes a park, a basin, a snowy curb, and a magical ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, rival, basin, magic = f["hero"], f["rival"], f["basin"], f["magic"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} find the {basin.label}?",
            answer=f"{hero.id} found the {basin.label} on a snowy curb beside the park.",
        ),
        QAItem(
            question=f"Why did {rival.id} argue with {hero.id} about the {basin.label}?",
            answer=f"{rival.id} wanted the {basin.label} for themselves, so the two of them fell into a small conflict.",
        ),
        QAItem(
            question=f"What magic helped at the end of the story?",
            answer=f"{magic.label.capitalize()} helped because {hero.id} whispered {magic.spell!r}, and the basin's warmth calmed the quarrel.",
        ),
        QAItem(
            question=f"What changed by the ending?",
            answer="The conflict softened, the basin grew warm, and the snowy curb felt friendly instead of tense.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"park", "basin", "magic", "snow", "curb", "conflict", "shared"}
    out: list[QAItem] = []
    for tag in tags:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [f"({e.type})"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="snowy-curb", basin="basin", magic="warmth", name="Mara", gender="girl", rival="Old Tovin", trait="brave"),
    StoryParams(place="snowy-curb", basin="basin", magic="warmth", name="Oren", gender="boy", rival="Bram", trait="gentle"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports the snowy curb by the park with the basin and its warming magic.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "snowy curb" in setting.detail:
            lines.append(asp.fact("snowy_curb", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for bid, basin in BASINS.items():
        lines.append(asp.fact("basin", bid))
        lines.append(asp.fact("basin_label", bid, basin.label))
        lines.append(asp.fact("worn_on", bid, basin.region))
    for mid, magic in enumerate(MAGICS):
        lines.append(asp.fact("magic", magic.id))
        lines.append(asp.fact("spell", magic.id, magic.spell))
        for t in sorted(magic.tags):
            lines.append(asp.fact("tags", magic.id, t))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(B, S) :- basin(B), snowy_curb(S).
has_magic(M, B) :- magic(M), basin(B), tags(M, hands), at_risk(B, _).
valid_story(S, B, M) :- setting(S), basin(B), magic(M), at_risk(B, S), has_magic(M, B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    if py - ac:
        print("  only in python:", sorted(py - ac))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: a basin, a snowy curb, magic, and a small conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--basin", choices=BASINS)
    ap.add_argument("--magic", choices=[m.id for m in MAGICS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--rival", choices=RIVAL_NAMES)
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
    if args.place and args.place != "snowy-curb":
        raise StoryError(explain_rejection())
    if args.basin and args.basin not in BASINS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.basin is None or c[1] == args.basin)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError(explain_rejection())
    place, basin_id, magic_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    rival = args.rival or rng.choice(RIVAL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, basin=basin_id, magic=magic_id, name=name, gender=gender, rival=rival, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], BASINS[params.basin], MAGICS[0], params.name, params.gender, params.rival, "grandmother", params.trait)
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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, basin, magic) combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
