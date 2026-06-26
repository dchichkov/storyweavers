#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a squash-dim mystery that ends kindly.

A child detective notices something important has been squashed and dimmed.
Instead of a mean culprit, the world usually reveals a helper who was trying
to do the right thing the wrong way. The story follows clues, suspicion,
kindness, and a happy ending where the damaged thing is fixed.

The domain is intentionally small and constraint-checked:
- a setting with a few places
- one mystery object that can be squashed and dimmed
- one helpful remedy that can restore it
- one of a few plausible helpers
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    region: str
    can_squash: bool = True
    can_dim: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    restores: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "hall": Setting(place="the hall", indoor=True, affords={"squash-dim"}),
    "library": Setting(place="the library", indoor=True, affords={"squash-dim"}),
    "attic": Setting(place="the attic", indoor=True, affords={"squash-dim"}),
    "garden_shed": Setting(place="the garden shed", indoor=False, affords={"squash-dim"}),
}

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        label="paper lantern",
        phrase="a bright paper lantern",
        region="ceiling",
    ),
    "sign": Mystery(
        id="sign",
        label="welcome sign",
        phrase="a cheerful welcome sign",
        region="wall",
    ),
    "cushion": Mystery(
        id="cushion",
        label="reading cushion",
        phrase="a soft reading cushion",
        region="floor",
    ),
}

REMEDIES = {
    "tape": Remedy(
        id="tape",
        label="tape",
        phrase="a roll of tape and a little string",
        restores={"squashed", "dimmed"},
        prep="fetch some tape and string",
        tail="patched it carefully back into shape",
    ),
    "lamp": Remedy(
        id="lamp",
        label="lamp oil",
        phrase="a little lamp oil and a clean cloth",
        restores={"dimmed"},
        prep="bring lamp oil and a clean cloth",
        tail="wiped the shade until it glowed again",
    ),
    "pillow": Remedy(
        id="pillow",
        label="pillow fluff",
        phrase="fresh pillow fluff and a stitched cover",
        restores={"squashed"},
        prep="get fresh fluff and a stitched cover",
        tail="fluffed it up until it looked round again",
    ),
}

HELPERS = {
    "cat": "cat",
    "dog": "dog",
    "brother": "brother",
    "sister": "sister",
    "mom": "mother",
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Leo", "Theo", "Noah"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_squash_dim(world: World) -> list[str]:
    out = []
    for helper in world.entities.values():
        if helper.kind != "character":
            continue
        if helper.memes.get("helping", 0) < THRESHOLD:
            continue
        if helper.meters.get("clumsy_move", 0) < THRESHOLD:
            continue
        mystery = world.get(world.facts["mystery"].id)
        if mystery.meters.get("squashed", 0) >= THRESHOLD and mystery.meters.get("dimmed", 0) >= THRESHOLD:
            continue
        sig = ("squashdim", helper.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        mystery.meters["squashed"] = 1.0
        mystery.meters["dimmed"] = 1.0
        helper.memes["embarrassed"] = helper.memes.get("embarrassed", 0) + 1
        out.append(f"Something got squashed and dimmed.")
    return out


RULES = [Rule("squashdim", _r_squash_dim)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                lines.extend(got)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def mystery_at_risk(mystery: Mystery, setting: Setting) -> bool:
    return "squash-dim" in setting.affords and mystery.can_squash and mystery.can_dim


def select_remedy(mystery: Mystery) -> Optional[Remedy]:
    for remedy in REMEDIES.values():
        if "squashed" in remedy.restores and "dimmed" in remedy.restores and mystery.id == "lantern":
            return remedy
        if mystery.id == "sign" and {"squashed", "dimmed"} & remedy.restores:
            return remedy
        if mystery.id == "cushion" and "squashed" in remedy.restores:
            return remedy
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if not mystery_at_risk(mystery, setting):
                continue
            if not select_remedy(mystery):
                continue
            for helper in HELPERS:
                combos.append((place, mid, helper))
    return combos


def validate_explicit(args: argparse.Namespace) -> None:
    if args.mystery and args.place:
        mystery = MYSTERIES[args.mystery]
        setting = SETTINGS[args.place]
        if not mystery_at_risk(mystery, setting):
            raise StoryError("That place cannot host a squash-dim mystery.")
    if args.gender and args.mystery and args.gender not in MYSTERIES[args.mystery].genders:
        raise StoryError("That mystery object does not fit the requested gendered owner.")


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(setting: Setting, mystery: Mystery, helper_kind: str, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=HELPERS[helper_kind], label=f"the {helper_kind}"))
    object_ = world.add(Entity(
        id=mystery.id,
        type=mystery.label,
        label=mystery.label,
        phrase=mystery.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["mystery"] = object_

    world.say(f"{hero.id} loved solving little mysteries in {setting.place}.")
    world.say(f"One day, {hero.id} found {object_.phrase} in a funny state: a little squashed and dim.")
    world.say(f"{hero.pronoun('possessive').capitalize()} eyes narrowed kindly. \"Who did this?\" {hero.id} whispered.")

    world.para()
    helper.memes["helping"] = 1
    helper.meters["clumsy_move"] = 1
    world.say(f"There were clues: a tiny drag mark, a soft rustle, and a trail to {helper.label}.")
    world.say(f"{hero.id} did not shout. {hero.pronoun().capitalize()} just asked gentle questions and looked closely.")
    world.say(f"{helper.label} looked sorry and said {helper.pronoun('subject')} had tried to help.")

    propagate(world, narrate=False)
    if object_.meters.get("squashed", 0) < THRESHOLD or object_.meters.get("dimmed", 0) < THRESHOLD:
        object_.meters["squashed"] = 1.0
        object_.meters["dimmed"] = 1.0

    world.para()
    remedy = select_remedy(mystery)
    world.facts["remedy"] = remedy
    if remedy:
        world.say(f"The clue led to a simple fix: {remedy.prep}.")
        world.say(f"Together, they {remedy.tail}.")
        object_.meters["squashed"] = 0.0
        object_.meters["dimmed"] = 0.0
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
        helper.memes["relief"] = helper.memes.get("relief", 0) + 1
        world.say(f"{helper.label} was not a mean culprit at all, only a helper who made a mistake.")
        world.say(f"{hero.id} smiled, forgave {helper.label}, and the room ended bright and warm again.")
    else:
        world.say(f"There was no good fix, so the mystery stayed unsolved.")

    world.facts["resolved"] = bool(remedy)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        f"Write a child-friendly whodunit set in {world.setting.place} about {hero.id} and {mystery.label}.",
        f"Tell a gentle mystery where {helper.label} seems suspicious at first, but kindness wins in the end.",
        f"Make a short story with a squash-dim clue, a careful question, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    remedy = world.facts["remedy"]
    resolved = world.facts["resolved"]

    qs = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a kind little detective who noticed a mystery in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was wrong with the {mystery.label}?",
            answer=f"It had been squashed and dimmed.",
        ),
        QAItem(
            question=f"Who turned out to be the likely helper?",
            answer=f"It was {helper.label}, who had tried to help and made a clumsy mistake.",
        ),
    ]
    if resolved and remedy:
        qs.append(QAItem(
            question=f"How did they fix the {mystery.label}?",
            answer=f"They used {remedy.phrase} and carefully put the {mystery.label} back in good shape.",
        ))
        qs.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with forgiveness, a fixed {mystery.label}, and everyone feeling relieved.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="Why is kindness helpful in a mystery?",
            answer="Kindness helps because people tell the truth more easily when they feel safe and cared for.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_at_risk(M) :- mystery(M), can_squash(M), can_dim(M), setting_affords(S, squash_dim), chosen_place(S).
has_remedy(M) :- mystery(M), remedy(R), restores(R, squashed), restores(R, dimmed), supports(R, M).
valid_story(S, M, H) :- chosen_place(S), mystery_at_risk(M), has_remedy(M), helper_kind(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("chosen_place", s))
        lines.append(asp.fact("setting_affords", s, "squash_dim"))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.can_squash:
            lines.append(asp.fact("can_squash", mid))
        if m.can_dim:
            lines.append(asp.fact("can_dim", mid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for rest in sorted(r.restores):
            lines.append(asp.fact("restores", rid, rest))
        for mid in MYSTERIES:
            lines.append(asp.fact("supports", rid, mid))
    for hk in HELPERS:
        lines.append(asp.fact("helper_kind", hk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((p, m, h) for p, m, h in valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a squash-dim mystery and a kind happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    validate_explicit(args)
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("No valid squash-dim mystery matches those choices.")
    place, mystery, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    return StoryParams(place=place, mystery=mystery, helper=helper, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        params.helper,
        params.name,
        params.gender,
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


CURATED = [
    StoryParams(place="library", mystery="lantern", helper="cat", name="Mina", gender="girl"),
    StoryParams(place="hall", mystery="sign", helper="brother", name="Owen", gender="boy"),
    StoryParams(place="attic", mystery="cushion", helper="mom", name="Ivy", gender="girl"),
]


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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(c)
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
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
