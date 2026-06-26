#!/usr/bin/env python3
"""
A mythic storyworld about an inventor, a bottle of vinegar, and a sacred arch.

A small, state-driven simulation:
- The inventor carries a mood of wonder and worry.
- The arch can be stained by moss or soot.
- Vinegar can help only when it is the right kind of cleaner for the arch.
- Friendship and an inner monologue drive the turn from hesitation to a clever fix.

The story is meant to feel like a little myth: a human craftsperson, a worthy
stone arch, a remembered lesson, and a gentle ending image.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0, "stain": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "friend"}
        male = {"boy", "man", "father", "brother", "inventor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Arch:
    id: str
    label: str
    material: str
    stain: str
    region: str = "stone"


@dataclass
class Cleanser:
    id: str
    label: str
    phrase: str
    suited_for: set[str]
    careful: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_seen = False
        self.inner_monologue_seen = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.flashback_seen = self.flashback_seen
        c.inner_monologue_seen = self.inner_monologue_seen
        return c


@dataclass
class StoryParams:
    place: str
    arch: str
    cleanser: str
    name: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "temple_courtyard": Setting("the temple courtyard", "golden", {"clean"}),
    "old_road": Setting("the old road", "dusty", {"clean"}),
    "river_gate": Setting("the river gate", "misty", {"clean"}),
}

ARCHES = {
    "stone_arch": Arch("stone_arch", "stone arch", "stone", "moss"),
    "marble_arch": Arch("marble_arch", "marble arch", "marble", "soot"),
    "bronze_arch": Arch("bronze_arch", "bronze arch", "bronze", "verdigris"),
}

CLEANSERS = {
    "vinegar": Cleanser("vinegar", "vinegar", "a small bottle of vinegar", {"stone", "marble", "bronze"}),
    "salt_water": Cleanser("salt_water", "salt water", "a jar of salt water", {"bronze"}),
    "plain_water": Cleanser("plain_water", "plain water", "a cup of plain water", set()),
}

GIRL_NAMES = ["Ari", "Lina", "Mira", "Nia", "Sera", "Tala"]
BOY_NAMES = ["Orin", "Dara", "Kian", "Ravi", "Tovin", "Jaro"]
FRIENDS = ["companion", "apprentice", "neighbor", "friend"]
TRAITS = ["patient", "curious", "brave", "gentle", "steadfast"]


def choose_arch_cleanser(arch: Arch, cleanser: Cleanser) -> bool:
    return arch.material in cleanser.suited_for


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for arch_id, arch in ARCHES.items():
            for clean_id, c in CLEANSERS.items():
                if "clean" in setting.affords and choose_arch_cleanser(arch, c):
                    out.append((place, arch_id, clean_id))
    return out


def explain_rejection(arch: Arch, cleanser: Cleanser) -> str:
    return (
        f"(No story: {cleanser.label} would not be a sensible remedy for a "
        f"{arch.label}. The myth needs a cleaner that can truly help the stone.)"
    )


def explain_invalid_place(place: str) -> str:
    return f"(No story: unknown setting '{place}'.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic inventor storyworld with vinegar and an arch.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--arch", choices=ARCHES)
    ap.add_argument("--cleanser", choices=CLEANSERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(explain_invalid_place(args.place))
    if args.arch and args.cleanser:
        arch = ARCHES[args.arch]
        cleanser = CLEANSERS[args.cleanser]
        if not choose_arch_cleanser(arch, cleanser):
            raise StoryError(explain_rejection(arch, cleanser))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.arch is None or c[1] == args.arch)
        and (args.cleanser is None or c[2] == args.cleanser)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, arch, cleanser = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place, arch=arch, cleanser=cleanser, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="inventor"))
    pal = world.add(Entity(id="Friend", kind="character", type="friend", label=params.friend))
    arch = ARCHES[params.arch]
    cleanser = CLEANSERS[params.cleanser]
    arch_ent = world.add(Entity(id="Arch", type="stone", label=arch.label, phrase=f"the {arch.label}", caretaker=hero.id))
    bottle = world.add(Entity(id="Vinegar", type="thing", label="vinegar", phrase=cleanser.phrase, owner=hero.id, worn_by=None))

    hero.memes["love"] += 1
    world.say(
        f"In the days when the wind still sang over the stones, {hero.id} was an inventor who "
        f"loved making little useful wonders."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {pal.label} stood together in {world.setting.place}, "
        f"where a {arch.label} kept the old path like a gate of memory."
    )
    world.say(
        f"{hero.id} carried {bottle.phrase}, because {cleanser.label} could loosen the stain that clung to the arch."
    )
    world.para()

    hero.memes["worry"] += 1
    arch_ent.meters["stain"] += 1
    world.say(
        f"But the arch had gone dark with {arch.stain}, and {hero.id} paused."
    )
    world.say(
        f"{hero.id} looked at the stain and thought, 'If I scrub too hard, I may mar the old stone.'"
    )
    world.inner_monologue_seen = True
    world.say(
        f"{hero.id} remembered a bright afternoon long ago, when an older maker had whispered, "
        f"'A gentle hand can do what a proud hand cannot.'"
    )
    world.flashback_seen = True
    world.say(
        f"That memory returned like a small lantern, and {pal.label} stayed close, ready to help."
    )
    world.para()

    arch_ent.meters["stain"] -= 1
    arch_ent.meters["clean"] += 1
    hero.memes["resolve"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} poured a little {cleanser.label} into water, worked slowly, and the stain softened at once."
    )
    world.say(
        f"{pal.label} held the cloth, and together they wiped the {arch.label} until the stone shone pale again."
    )
    world.say(
        f"{hero.id} smiled at the arch and thought, 'The old world answers kindness better than force.'"
    )
    world.say(
        f"At sunset, the {arch.label} stood bright and still, and the two friends walked home with clean hands and light hearts."
    )

    world.facts.update(hero=hero, friend=pal, arch=arch_ent, arch_cfg=arch, cleanser=cleanser, bottle=bottle, setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth for children about an inventor, vinegar, and a sacred arch.',
        f"Tell a gentle story where {f['hero'].id} uses {f['cleanser'].label} to help the {f['arch_cfg'].label} with a friend nearby.",
        "Write a mythic little tale with a remembered lesson, a friendship, and a clean ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    arch = f["arch_cfg"]
    cleanser = f["cleanser"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the inventor in the story?",
            answer=f"The inventor was {hero.id}, who cared for the {arch.label} and tried to help it shine again.",
        ),
        QAItem(
            question=f"What did {hero.id} bring to clean the arch?",
            answer=f"{hero.id} brought {cleanser.phrase}, because it could loosen the stain on the {arch.label}.",
        ),
        QAItem(
            question=f"Who stayed beside {hero.id} while the arch was being cleaned?",
            answer=f"{friend.label} stayed beside {hero.id} in {place}, and the two of them worked together like good friends.",
        ),
    ] + (
        [
            QAItem(
                question=f"What old memory helped {hero.id} decide to be careful?",
                answer=(
                    f"{hero.id} remembered an older maker saying that a gentle hand can do what a proud hand cannot, "
                    f"and that flashback helped {hero.id} choose patience."
                ),
            )
        ]
        if world.flashback_seen
        else []
    ) + (
        [
            QAItem(
                question=f"What did {hero.id} think before scrubbing the stone?",
                answer=(
                    f"{hero.id} thought about not harming the old stone, and that inner thought made {hero.id} use a careful, soft touch."
                ),
            )
        ]
        if world.inner_monologue_seen
        else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is vinegar?",
            answer="Vinegar is a sour liquid made by changing alcohol with tiny living helpers called bacteria. People use it in cooking and for cleaning some things.",
        ),
        QAItem(
            question="What is an arch?",
            answer="An arch is a curved shape that can hold up stone or brick above a doorway or path.",
        ),
        QAItem(
            question="Why can cleaning help a stone arch?",
            answer="Cleaning can remove moss or grime so the stone looks brighter and the arch stays strong and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    lines.append(f"  inner_monologue_seen={world.inner_monologue_seen}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="temple_courtyard", arch="stone_arch", cleanser="vinegar", name="Ari", friend="friend"),
    StoryParams(place="old_road", arch="marble_arch", cleanser="vinegar", name="Orin", friend="companion"),
    StoryParams(place="river_gate", arch="bronze_arch", cleanser="vinegar", name="Mira", friend="neighbor"),
]


ASP_RULES = r"""
% A cleanser is suitable when it suits the arch material.
suitable(C, A) :- cleanser(C), arch(A), material(A, M), suits(C, M).

% A story is reasonable when the setting allows cleaning and the cleanser fits.
valid_story(P, A, C) :- setting(P), arch(A), cleanser(C), affords(P, clean), suitable(C, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ARCHES.items():
        lines.append(asp.fact("arch", aid))
        lines.append(asp.fact("material", aid, a.material))
    for cid, c in CLEANSERS.items():
        lines.append(asp.fact("cleanser", cid))
        for m in sorted(c.suited_for):
            lines.append(asp.fact("suits", cid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


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
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(set(asp.atoms(model, 'valid_story')))} compatible stories:")
        for t in sorted(set(asp.atoms(model, "valid_story"))):
            print("  ", t)
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
            header = f"### {p.name}: {p.arch} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
