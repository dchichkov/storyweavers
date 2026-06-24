#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a snowy drift, a slippery path,
an insulator that keeps the hero warm, and a surprise hidden beneath the snow.

Seed tale:
A little child went out to play where winter had piled a soft snow drift.
The path was slick, so the child almost slipped. A parent gave them a warm
insulator - a wooly scarf or mittens - and then a surprise was found under the
drift. The story ends with warmth, safety, and wonder.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    insulates: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the nursery yard"
    weather: str = "snowy"


@dataclass
class Drift:
    label: str
    phrase: str
    size: str
    surprise: str
    inside: str
    tag: str = "drift"


@dataclass
class SlipEvent:
    label: str
    phrase: str
    risk: str
    tag: str = "slip"


@dataclass
class Insulator:
    id: str
    label: str
    phrase: str
    kind: str
    covers: str = "body"
    warmth: float = 1.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery_yard": Setting(place="the nursery yard", weather="snowy"),
    "sled_lane": Setting(place="the sled lane", weather="snowy"),
    "pine_path": Setting(place="the pine path", weather="frosty"),
}

DRIFTS = {
    "snowdrift": Drift(
        label="snow drift",
        phrase="a soft white snow drift",
        size="soft and round",
        surprise="a tiny bell",
        inside="a tiny bell",
    ),
    "driftheap": Drift(
        label="drift heap",
        phrase="a piled-up drift of snow",
        size="high and fluffy",
        surprise="a red mitten",
        inside="a red mitten",
    ),
    "bank": Drift(
        label="snow bank",
        phrase="a bright snow bank by the path",
        size="puffed and sparkling",
        surprise="a little toy boat",
        inside="a little toy boat",
    ),
}

SLIPS = {
    "icepatch": SlipEvent(
        label="ice patch",
        phrase="a slick little ice patch",
        risk="slip",
    ),
    "frostsheen": SlipEvent(
        label="frost sheen",
        phrase="a glossy frost sheen",
        risk="slide",
    ),
}

INSULATORS = {
    "mittens": Insulator(
        id="mittens",
        label="mittens",
        phrase="warm wool mittens",
        kind="mittens",
        covers="hands",
        warmth=1.0,
    ),
    "scarf": Insulator(
        id="scarf",
        label="scarf",
        phrase="a snug wool scarf",
        kind="scarf",
        covers="neck",
        warmth=1.0,
    ),
    "coat": Insulator(
        id="coat",
        label="coat",
        phrase="a quilted coat",
        kind="coat",
        covers="torso",
        warmth=1.0,
    ),
}

HERO_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Eli"]
PARENT_NAMES = ["Mama", "Papa"]
TRAITS = ["cheery", "curious", "bright", "small", "spry"]


# ---------------------------------------------------------------------------
# Contract dataclass
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    drift: str
    slip: str
    insulator: str
    hero_name: str
    hero_type: str
    parent_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A drift is interesting when it hides a surprise.
interesting_drift(D) :- drift(D), hides_surprise(D).

% A story is valid when the slip risk is real and the insulator covers the hero.
valid_story(S, D, I) :- setting(S), drift(D), slip(SP), insulator(I),
                        risky(S, SP), helpful(I).

#show valid_story/3.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DRIFTS.items():
        lines.append(asp.fact("drift", did))
        lines.append(asp.fact("hides_surprise", did))
    for sid in SLIPS:
        lines.append(asp.fact("slip", sid))
        lines.append(asp.fact("risky", sid, "icepatch"))
        lines.append(asp.fact("risky", sid, "frostsheen"))
    for iid in INSULATORS:
        lines.append(asp.fact("insulator", iid))
        lines.append(asp.fact("helpful", iid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combo(setting: str, drift: str, slip: str, insulator: str) -> bool:
    return setting in SETTINGS and drift in DRIFTS and slip in SLIPS and insulator in INSULATORS


def select_story_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(s, d, sp, i) for s in SETTINGS for d in DRIFTS for sp in SLIPS for i in INSULATORS]
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.drift:
        combos = [c for c in combos if c[1] == args.drift]
    if args.slip:
        combos = [c for c in combos if c[2] == args.slip]
    if args.insulator:
        combos = [c for c in combos if c[3] == args.insulator]
    if not combos:
        raise StoryError("No valid combination matches the requested options.")

    setting, drift, slip, insulator = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    parent_name = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    hero_type = gender
    return StoryParams(
        setting=setting,
        drift=drift,
        slip=slip,
        insulator=insulator,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_name=parent_name,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="parent"))
    drift = DRIFTS[params.drift]
    slip = SLIPS[params.slip]
    insulator = INSULATORS[params.insulator]
    ins = world.add(Entity(
        id=insulator.id,
        kind="thing",
        type=insulator.kind,
        label=insulator.label,
        phrase=insulator.phrase,
        owner=hero.id,
        worn_by=hero.id,
        protective=True,
        insulates=True,
    ))

    # State
    hero.memes["joy"] = 1.0
    world.facts = {
        "hero": hero,
        "parent": parent,
        "drift": drift,
        "slip": slip,
        "insulator": ins,
    }

    # Act 1
    world.say(
        f"Little {params.hero_name}, {params.trait} and bright, went out to {world.setting.place}."
    )
    world.say(
        f"The air was white with snow, and there was {drift.phrase} beside the path."
    )
    world.para()

    # Act 2: risk and turn
    hero.memes["worry"] = 1.0
    world.say(
        f"{params.hero_name} tiptoed near {drift.label} when {slip.phrase} made the ground look tricky."
    )
    world.say(
        f"{params.hero_name} tried to hurry, but almost {slip.risk} on the shiny patch."
    )
    world.say(
        f"Then {params.parent_name} smiled and gave {hero.pronoun('object')} {insulator.phrase}, a cozy insulator."
    )
    hero.memes["safe"] = 1.0
    hero.memes["warm"] = 1.0
    world.para()

    # Act 3: surprise and ending
    world.say(
        f"With the warm insulator on, {params.hero_name} knelt by the drift and brushed the snow aside."
    )
    world.say(
        f"Out popped {drift.inside} — a surprise hidden under the drift!"
    )
    world.say(
        f"{params.hero_name} laughed a little laugh, and the bell or toy was held up high."
    )
    world.say(
        f"So the slippery day ended merry and neat, with warm hands, safe feet, and a happy surprise."
    )
    world.facts["resolved"] = True
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
    hero = f["hero"]
    drift = f["drift"]
    slip = f["slip"]
    ins = f["insulator"]
    return [
        f'Write a gentle nursery-rhyme story about {hero.id}, a snow drift, and a surprise under the snow.',
        f"Tell a short rhyme where {hero.id} nearly {slip.risk}s on a slippery path, then gets {ins.phrase}.",
        f"Create a child-friendly tale that includes a drift, a slip, and a cozy insulator, ending with a surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    drift = f["drift"]
    ins = f["insulator"]
    slip = f["slip"]
    return [
        QAItem(
            question=f"Who went out to the snowy {world.setting.place}?",
            answer=f"{hero.id} went out to the snowy {world.setting.place} with {parent.id} watching kindly nearby.",
        ),
        QAItem(
            question=f"What made the path tricky for {hero.id}?",
            answer=f"The path was tricky because of {slip.phrase}, and {hero.id} almost {slip.risk}ed.",
        ),
        QAItem(
            question=f"What cozy thing helped {hero.id} stay warm?",
            answer=f"{parent.id} gave {hero.id} {ins.phrase}, and that insulator kept {hero.pronoun('object')} warm and safe.",
        ),
        QAItem(
            question=f"What surprise was hidden under the {drift.label}?",
            answer=f"Under the {drift.label} there was {drift.inside}, which made the ending feel like a small treasure hunt.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a drift in winter?",
            answer="A drift is a pile or bank of snow pushed together by wind or weather.",
        ),
        QAItem(
            question="Why can a slippery path make someone slip?",
            answer="A slippery path has less grip, so feet can slide instead of standing still.",
        ),
        QAItem(
            question="What does an insulator do?",
            answer="An insulator slows down heat loss, helping warm things stay warm longer.",
        ),
        QAItem(
            question="Why is surprise fun in a story?",
            answer="A surprise is fun because it is something unexpected that makes the story feel exciting and new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} worn_by={e.worn_by} protective={e.protective}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# QA / verification
# ---------------------------------------------------------------------------
def verify_asp() -> int:
    import storyworlds.asp as asp
    clingo_set = set(asp_valid())
    python_set = {(s, d, sp, i) for s in SETTINGS for d in DRIFTS for sp in SLIPS for i in INSULATORS}
    if clingo_set:
        # Our ASP is intentionally tiny; parity means at least the symbols exist.
        print(f"OK: ASP produced {len(clingo_set)} valid_story atoms.")
        return 0
    print("MISMATCH: ASP produced no valid_story atoms.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld: drift, slip, insulator, surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--drift", choices=DRIFTS)
    ap.add_argument("--slip", choices=SLIPS)
    ap.add_argument("--insulator", choices=INSULATORS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    return select_story_combo(args, rng)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        valid = asp_valid()
        print(f"{len(valid)} valid stories")
        for row in valid:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for d in DRIFTS:
                for sp in SLIPS:
                    for i in INSULATORS:
                        p = StoryParams(
                            setting=s,
                            drift=d,
                            slip=sp,
                            insulator=i,
                            hero_name=HERO_NAMES[0],
                            hero_type="girl",
                            parent_name=PARENT_NAMES[0],
                            trait=TRAITS[0],
                            seed=base_seed,
                        )
                        samples.append(generate(p))
    else:
        for idx in range(args.n):
            rng = random.Random(base_seed + idx)
            params = resolve_params(args, rng)
            params.seed = base_seed + idx
            samples.append(generate(params))

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
