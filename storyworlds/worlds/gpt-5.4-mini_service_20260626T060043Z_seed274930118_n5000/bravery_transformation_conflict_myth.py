#!/usr/bin/env python3
"""
storyworlds/worlds/bravery_transformation_conflict_myth.py
===========================================================

A small mythic storyworld about bravery, conflict, and transformation.

Premise:
- A timid child or young hero faces a mythic challenge.
- A guide, elder, or spirit reveals a way to meet the conflict.
- The hero transforms from fear into bravery through action.
- The ending image proves the change in state.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- shared results imported eagerly
- ASP helper imported lazily
- StoryParams, registries, parser, resolver, generator, emitter, main
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen", "maiden"}
        male = {"boy", "man", "father", "brother", "king", "warrior"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    light: str
    danger: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    verb: str
    gerund: str
    risk: str
    danger_word: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transform:
    id: str
    charm: str
    offer: str
    effect: str
    ending: str
    tag: str


@dataclass
class World:
    setting: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _activity_conflict(world: World) -> list[str]:
    out = []
    hero = world.entities["hero"]
    if hero.meters.get("fear", 0) < THRESHOLD:
        return out
    if hero.memes.get("defiance", 0) >= THRESHOLD:
        sig = ("conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
            out.append("__conflict__")
    return out


def _transformation(world: World) -> list[str]:
    out = []
    hero = world.entities["hero"]
    if hero.meters.get("courage", 0) < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["fear"] = 0.0
    hero.meters["bravery"] = hero.meters.get("bravery", 0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    _activity_conflict,
    _transformation,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s not in {"__conflict__", "__transform__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "forest": Place(
        id="forest",
        label="the old forest",
        light="green light",
        danger="a shadowed path",
        affords={"bridge", "boar", "river"},
    ),
    "mountain": Place(
        id="mountain",
        label="the high mountain",
        light="silver light",
        danger="a narrow ledge",
        affords={"storm", "bridge"},
    ),
    "shore": Place(
        id="shore",
        label="the moonlit shore",
        light="blue light",
        danger="cold waves",
        affords={"river", "storm"},
    ),
}

CONFLICTS = {
    "bridge": Conflict(
        id="bridge",
        verb="cross the broken bridge",
        gerund="crossing the broken bridge",
        risk="fall into the dark water",
        danger_word="bridge",
        keyword="bridge",
        tags={"stone", "river"},
    ),
    "boar": Conflict(
        id="boar",
        verb="face the wild boar",
        gerund="facing the wild boar",
        risk="be driven back into the trees",
        danger_word="boar",
        keyword="boar",
        tags={"beast", "forest"},
    ),
    "river": Conflict(
        id="river",
        verb="walk through the river",
        gerund="walking through the river",
        risk="be carried by the current",
        danger_word="river",
        keyword="river",
        tags={"water", "current"},
    ),
    "storm": Conflict(
        id="storm",
        verb="climb into the storm",
        gerund="climbing into the storm",
        risk="be lost in thunder",
        danger_word="storm",
        keyword="storm",
        tags={"wind", "sky"},
    ),
}

TRANSFORMS = {
    "torch": Transform(
        id="torch",
        charm="a small torch of dawnfire",
        offer="lift the torch and step forward",
        effect="the flame warmed the hero's shaking hands",
        ending="the torch burned steady in the hero's fist",
        tag="fire",
    ),
    "mask": Transform(
        id="mask",
        charm="a mask of the river fox",
        offer="put on the fox mask and listen",
        effect="the fox mask taught the hero to breathe slowly",
        ending="the fox mask sat bright upon the hero's face",
        tag="fox",
    ),
    "cloak": Transform(
        id="cloak",
        charm="a cloak woven with star-thread",
        offer="wrap the cloak around the shoulders",
        effect="the star-thread gathered courage like moonlight",
        ending="the cloak shone softly on the hero's back",
        tag="star",
    ),
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Ari", "Mira", "Niko", "Lina", "Tavo", "Sera", "Ivo", "Kaia"]
GUIDE_TYPES = ["elder", "spirit", "mother", "father", "owl"]
GUIDE_LABELS = {"elder": "the elder", "spirit": "the spirit", "mother": "the mother", "father": "the father", "owl": "the owl"}

TRAITS = ["timid", "small", "quiet", "careful", "soft-spoken", "worried"]


@dataclass
class StoryParams:
    place: str
    conflict: str
    transform: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


def _hero_name(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in SETTINGS.items():
        for conflict_id in p.affords:
            for trans_id in TRANSFORMS:
                combos.append((place, conflict_id, trans_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic bravery storyworld with conflict and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--guide", choices=GUIDE_TYPES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.conflict is None or c[1] == args.conflict)
              and (args.transform is None or c[2] == args.transform)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, conflict, transform = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or _hero_name(rng, gender)
    guide = args.guide or rng.choice(GUIDE_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, conflict=conflict, transform=transform, name=name, gender=gender, guide=guide, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, traits=[params.trait, "brave-to-be"]))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide, label=GUIDE_LABELS[params.guide]))
    conflict = CONFLICTS[params.conflict]
    trans = TRANSFORMS[params.transform]

    hero.meters["fear"] = 1.0
    hero.memes["desire"] = 1.0

    world.say(f"Long ago, in {world.setting.label}, there lived a {params.trait} child named {params.name}.")
    world.say(f"{hero.label} loved the quiet edge of the world, where {world.setting.light} touched the stones, yet {hero.pronoun('possessive')} heart trembled when the path reached {conflict.verb}.")
    world.say(f"One evening, {world.setting.danger} waited ahead, and the people of the land whispered that only a true act of bravery could cross it.")

    world.para()
    world.say(f"At the meeting place, {guide.label} came near and spoke of {trans.charm}.")
    world.say(f'"To meet the trial," said {guide.label}, "you must {trans.offer}."')
    world.say(f"{params.name} looked at the dark way and wanted to turn back, but the story of {conflict.danger_word} would not leave {hero.pronoun('possessive')} mind.")
    hero.memes["defiance"] = 1.0
    hero.meters["courage"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{trans.effect}.")
    world.say(f"Then {params.name} stepped into the trial and did not run. {params.name} {conflict.gerund} was no longer the act of a frightened child, but the deed of someone becoming brave.")
    world.say(f"At last, {trans.ending}, and the old fear fell away like ash in the wind.")
    world.say(f"{params.name} stood in the end with {params.name}'s face calm, as if the dark path had changed into a road of light.")

    world.facts.update(
        hero=hero,
        guide=guide,
        conflict=conflict,
        transform=trans,
        place=world.setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    conflict = f["conflict"]
    trans = f["transform"]
    return [
        f'Write a short myth about bravery, conflict, and transformation in {f["place"].label}.',
        f"Tell a legend where {hero.label} must {conflict.verb} and receives {trans.charm}.",
        f'Write a child-friendly myth that begins with fear and ends with bravery after "{conflict.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    conflict = f["conflict"]
    trans = f["transform"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a {hero.type} child who begins afraid but grows brave."
        ),
        QAItem(
            question=f"What problem did {hero.label} face in the story?",
            answer=f"{hero.label} faced a conflict with {conflict.verb} in {f['place'].label}."
        ),
        QAItem(
            question=f"Who helped {hero.label} change?",
            answer=f"{guide.label} helped by offering {trans.charm} and showing {hero.label} how to meet the trial."
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"{hero.label} changed from fearful to brave, and the old fear gave way to courage."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the ability to act even when you feel scared."
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or struggle that a character has to face."
        ),
        QAItem(
            question="What is transformation in a myth?",
            answer="Transformation is a big change, like a fearful character becoming brave."
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
trial(P,C,T) :- setting(P), conflict(C), transform(T), affords(P,C).
valid_story(P,C,T) :- trial(P,C,T).

brave(H) :- hero(H), courage(H).
transformed(H) :- hero(H), brave(H), guidance(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for c in sorted(p.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="forest", conflict="boar", transform="torch", name="Ari", gender="boy", guide="elder", trait="timid"),
    StoryParams(place="forest", conflict="bridge", transform="cloak", name="Mira", gender="girl", guide="spirit", trait="quiet"),
    StoryParams(place="shore", conflict="river", transform="mask", name="Niko", gender="boy", guide="owl", trait="careful"),
    StoryParams(place="mountain", conflict="storm", transform="torch", name="Kaia", gender="girl", guide="mother", trait="worried"),
]


def resolve_restrictions(args: argparse.Namespace) -> None:
    return


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, conflict, transform) combos:\n")
        for row in combos:
            print("  ", row)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.conflict} at {p.place} (transform: {p.transform})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
