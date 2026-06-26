#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/destruction_inner_monologue_magic_ghost_story.py
================================================================================================

A small ghost-story world with inner monologue, magic, and a gentle
destruction-and-repair arc.

The simulated premise:
- A little ghost lives in a haunted place and treasures one fragile thing.
- A destructive force threatens it.
- The ghost thinks through the problem in an inner monologue.
- Magic can repair the damage, but only when it genuinely fits the thing at risk.

The story is built from world state rather than from a frozen template:
meters track physical damage and repair pressure; memes track fear, hope,
and resolve.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    fragile: bool = False
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["damage", "repair", "dust", "spark"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "hope", "resolve", "sadness", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    verb: str
    mess: str
    soil: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    cast: str
    effect: str
    covers: set[str]
    heals: set[str]
    tags: set[str] = field(default_factory=set)


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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_break(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    if ghost.meters["damage"] < THRESHOLD:
        return out
    treasure = world.get("treasure")
    sig = ("break", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["damage"] += 1
    ghost.memes["sadness"] += 1
    out.append(f"The {treasure.label} cracked a little more.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    wand = world.get("wand")
    treasure = world.get("treasure")
    if ghost.memes["resolve"] < THRESHOLD or wand.meters["spark"] < THRESHOLD:
        return out
    if treasure.meters["damage"] < THRESHOLD:
        return out
    sig = ("repair", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["damage"] = 0.0
    treasure.meters["repair"] += 1
    ghost.memes["hope"] += 1
    ghost.memes["sadness"] = max(0.0, ghost.memes["sadness"] - 1.0)
    out.append(f"The magic thread stitched the {treasure.label} back together.")
    return out


def _r_calm(world: World) -> list[str]:
    ghost = world.get("ghost")
    if ghost.memes["resolve"] < THRESHOLD or ghost.memes["fear"] < THRESHOLD:
        return []
    sig = ("calm", ghost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["calm"] += 1
    ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 1.0)
    return ["The ghost took a slow breath and listened to the quiet house."]


RULES = [_r_break, _r_repair, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "attic": Setting("the attic", "dusty", {"wind", "magic"}),
    "hall": Setting("the old hall", "echoing", {"wind", "magic"}),
    "garden": Setting("the moon garden", "silver", {"wind", "magic"}),
}

THREATS = {
    "wind": Threat(
        id="wind",
        label="the wind",
        verb="gust",
        mess="dust",
        soil="dusty and scattered",
        zone={"torso"},
        tags={"destruction", "wind"},
    ),
    "storm": Threat(
        id="storm",
        label="the storm",
        verb="howl",
        mess="rain",
        soil="wet and ruined",
        zone={"torso", "head"},
        tags={"destruction", "storm"},
    ),
    "bump": Threat(
        id="bump",
        label="a bump in the dark",
        verb="bump",
        mess="chips",
        soil="chipped and cracked",
        zone={"head", "torso"},
        tags={"destruction", "crack"},
    ),
}

TREASURES = {
    "lantern": Treasure(
        id="lantern",
        label="lantern",
        phrase="a tiny glass lantern",
        region="torso",
        tags={"light", "glass"},
    ),
    "doll": Treasure(
        id="doll",
        label="doll",
        phrase="a little cloth doll",
        region="torso",
        tags={"toy", "cloth"},
    ),
    "star": Treasure(
        id="star",
        label="paper star",
        phrase="a bright paper star",
        region="head",
        plural=False,
        tags={"paper", "light"},
    ),
}

MAGICS = {
    "stitch": Magic(
        id="stitch",
        label="silver stitch-magic",
        cast="whisper a silver stitch",
        effect="mended",
        covers={"torso", "head"},
        heals={"damage"},
        tags={"magic", "repair"},
    ),
    "glow": Magic(
        id="glow",
        label="moon glow magic",
        cast="lift a moon-glow charm",
        effect="smoothed",
        covers={"torso", "head"},
        heals={"damage"},
        tags={"magic", "light"},
    ),
}

GHOST_NAMES = ["Milo", "Mina", "Luna", "Pip", "Nell", "Ivo", "Wren"]
WITCH_NAMES = ["Sera", "Tess", "Nora"]


@dataclass
class StoryParams:
    place: str
    threat: str
    treasure: str
    magic: str
    ghost_name: str
    seed: Optional[int] = None


def is_reasonable(threat: Threat, treasure: Treasure, magic: Magic) -> bool:
    return treasure.region in threat.zone and treasure.region in magic.covers and "damage" in magic.heals


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tname, threat in THREATS.items():
            if tname not in setting.affords:
                continue
            for trname, treasure in TREASURES.items():
                for mname, magic in MAGICS.items():
                    if is_reasonable(threat, treasure, magic):
                        combos.append((place, tname, trname))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story world with destruction, inner monologue, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--magic", choices=MAGICS)
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
    if args.threat and args.treasure and args.magic:
        if not is_reasonable(THREATS[args.threat], TREASURES[args.treasure], MAGICS[args.magic]):
            raise StoryError("That ghostly problem has no matching magic fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.threat is None or c[1] == args.threat)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("No valid ghost story matches those choices.")
    place, threat, treasure = rng.choice(sorted(combos))
    magic = args.magic or rng.choice(sorted(MAGICS))
    name = args.name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, threat=threat, treasure=treasure, magic=magic, ghost_name=name)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    ghost = world.add(Entity("ghost", kind="character", type="ghost", label=params.ghost_name))
    wand = world.add(Entity("wand", kind="thing", type="wand", label=MAGICS[params.magic].label, magical=True))
    treasure = world.add(Entity("treasure", kind="thing", type=TREASURES[params.treasure].label,
                                label=TREASURES[params.treasure].label,
                                phrase=TREASURES[params.treasure].phrase, fragile=True))
    threat = THREATS[params.threat]
    magic = MAGICS[params.magic]

    ghost.memes["fear"] += 1
    ghost.memes["hope"] += 1
    world.say(f"{ghost.id.capitalize()} lived in {setting.place} where the air always felt {setting.mood}.")
    world.say(f"One night, {ghost.pronoun('possessive')} {treasure.label} was in danger from {threat.label}.")
    world.para()
    world.say(f"{ghost.id} looked at the {treasure.label} and thought, "
              f"“If I do nothing, it will end up {threat.soil}.”")
    ghost.memes["resolve"] += 1
    world.say(f"“I can still help,” {ghost.id} thought, “if I use {magic.label} the right way.”")
    ghost.meters["damage"] += 1
    propagate(world, narrate=True)
    world.para()
    wand.meters["spark"] += 1
    world.say(f"{ghost.id} lifted the wand and {magic.cast}.")
    world.say(f"The air answered with a soft blue shine.")
    propagate(world, narrate=True)
    if treasure.meters["damage"] < THRESHOLD:
        world.say(f"In the end, the {treasure.label} stayed whole, glowing like a little secret.")
    world.facts.update(ghost=ghost, wand=wand, treasure=treasure, threat=threat, magic=magic, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story about {f["ghost"].id} in {f["setting"].place} where {f["threat"].label} causes destruction.',
        f"Tell a child-friendly spooky story with inner monologue and magic where a {f['treasure'].label} is at risk.",
        f'Write a haunted-house tale where a ghost thinks, "I can fix this," and uses {f["magic"].label} to repair what was broken.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost = f["ghost"]
    treasure = f["treasure"]
    threat = f["threat"]
    magic = f["magic"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the ghost in the story?",
            answer=f"The ghost was {ghost.id}, and {ghost.id} lived in {setting.place}.",
        ),
        QAItem(
            question=f"What was in danger because of {threat.label}?",
            answer=f"The {treasure.label} was in danger, because {threat.label} could leave it {threat.soil}.",
        ),
        QAItem(
            question=f"What did the ghost think before using magic?",
            answer=f"The ghost thought, “If I do nothing, it will be destroyed,” and then decided to use {magic.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {treasure.label} repaired and safe, while {ghost.id} felt calmer and braver.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spooky spirit, a strange place, and something mysterious that happens there.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something special can happen that people cannot do in ordinary ways, like glowing, mending, or lifting a spell.",
        ),
        QAItem(
            question="What is destruction?",
            answer="Destruction means something gets broken, ruined, or torn apart.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for trid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", trid))
        lines.append(asp.fact("worn_on", trid, tr.region))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        for c in sorted(m.covers):
            lines.append(asp.fact("covers", mid, c))
        for h in sorted(m.heals):
            lines.append(asp.fact("heals", mid, h))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T, Th) :- treasure(T), threat(Th), worn_on(T, R), zone(Th, R).
fix(M, T, Th) :- magic(M), at_risk(T, Th), covers(M, R), worn_on(T, R), heals(M, damage).
valid(Place, Th, T) :- affords(Place, Th), at_risk(T, Th), fix(_, T, Th).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", threat="wind", treasure="lantern", magic="stitch", ghost_name="Mina"),
    StoryParams(place="hall", threat="bump", treasure="doll", magic="glow", ghost_name="Pip"),
    StoryParams(place="garden", threat="storm", treasure="star", magic="stitch", ghost_name="Luna"),
]


def explain_rejection(threat: Threat, treasure: Treasure, magic: Magic) -> str:
    return (
        f"(No story: {threat.label} would not reasonably destroy a {treasure.label} "
        f"with a magic fix of {magic.label} in this world.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.threat and args.treasure and args.magic:
        if not is_reasonable(THREATS[args.threat], TREASURES[args.treasure], MAGICS[args.magic]):
            raise StoryError(explain_rejection(THREATS[args.threat], TREASURES[args.treasure], MAGICS[args.magic]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.threat is None or c[1] == args.threat)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("No valid ghost-story combination matches those options.")
    place, threat, treasure = rng.choice(sorted(combos))
    magic = args.magic or rng.choice(sorted(MAGICS))
    name = args.name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, threat=threat, treasure=treasure, magic=magic, ghost_name=name)


def build_parser_full() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        vals = asp_valid_combos()
        print(f"{len(vals)} valid ghost-story combos:\n")
        for place, threat, treasure in vals:
            print(f"  {place:8} {threat:8} {treasure:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.ghost_name}: {p.threat} at {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
