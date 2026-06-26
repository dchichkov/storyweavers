#!/usr/bin/env python3
"""
storyworlds/worlds/pants_dim_ketchup_bravery_comedy.py
======================================================

A small storyworld about a brave child, a slippery ketchup bottle, and a pair
of light pants that end up dimmed with red spots in a comic little mishap.

Premise:
- A child loves a funny lunch-time ritual.
- Ketchup is present in the setting.
- The child is brave enough to try something new.
- A squeeze goes wrong and splashes the child's pants.

Turn:
- The child does not hide.
- They tell the truth, laugh, and clean up.

Resolution:
- The stain gets wiped down.
- The child keeps the brave feeling, and the room ends in laughter.

This world is deliberately tiny and constraint-checked: there is one main
problem/fix pattern, and every generated story is grounded in the simulated
state rather than a fixed paragraph shell.
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

# Physical and emotional thresholds.
THRESHOLD = 1.0

# -----------------------------------------------------------------------------
# Entities
# -----------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class CleanUp:
    id: str
    label: str
    tool: str
    prep: str
    tail: str
    fixes: set[str]
    covers: set[str]


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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"ketchup"}),
    "picnic": Setting(place="the picnic table", indoor=False, affords={"ketchup"}),
    "diner": Setting(place="the diner booth", indoor=True, affords={"ketchup"}),
}

ACTIVITIES = {
    "ketchup": Activity(
        id="ketchup",
        verb="help with the ketchup",
        gerund="squeezing ketchup",
        mess="red",
        soil="spotted red",
        zone={"legs"},
        keyword="ketchup",
        tags={"ketchup", "red", "messy"},
    )
}

PRIZES = {
    "pants": Prize(
        label="pants",
        phrase="a pair of pale pants",
        type="pants",
        region="legs",
        plural=True,
    )
}

CLEANUPS = [
    CleanUp(
        id="napkin",
        label="a napkin stack",
        tool="napkins",
        prep="grab a bunch of napkins first",
        tail="used the napkins and wiped the red spots away",
        fixes={"red"},
        covers={"legs"},
    ),
    CleanUp(
        id="apron",
        label="a big apron",
        tool="an apron",
        prep="tie on a big apron before trying again",
        tail="tied on the apron and kept the next squeeze tidy",
        fixes={"red"},
        covers={"legs"},
    ),
]

NAMES = ["Milo", "Nia", "Toby", "Lena", "Pia", "Arlo", "Ivy", "Ezra"]
TRAITS = ["brave", "cheerful", "curious", "comic", "lively"]


# -----------------------------------------------------------------------------
# Reasonableness gate
# -----------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_cleanup(activity: Activity, prize: Prize) -> Optional[CleanUp]:
    for clean in CLEANUPS:
        if activity.mess in clean.fixes and prize.region in clean.covers:
            return clean
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_cleanup(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} only splashes the {sorted(activity.zone)}, "
        f"but {prize.label} would not be at risk or there is no believable cleanup.)"
    )


# -----------------------------------------------------------------------------
# Narrative helpers
# -----------------------------------------------------------------------------
def _mess(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["surprise"] = actor.memes.get("surprise", 0.0) + 1
    if actor.meters[activity.mess] >= THRESHOLD:
        world.say(
            f"The ketchup made a tiny red splash, and {actor.pronoun('possessive')} "
            f"pants got spotted."
        )


def _soil_prize(world: World, actor: Entity, prize: Entity, activity: Activity) -> None:
    sig = ("soil", prize.id, activity.mess)
    if sig in world.fired:
        return
    world.fired.add(sig)
    prize.meters[activity.mess] = prize.meters.get(activity.mess, 0.0) + 1
    prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
    world.say(f"That left {actor.pronoun('possessive')} {prize.label} looking spotted red.")


def _cleanup(world: World, actor: Entity, prize: Entity, activity: Activity, clean: CleanUp) -> None:
    sig = ("clean", prize.id, clean.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if prize.meters.get(activity.mess, 0.0) >= THRESHOLD:
        prize.meters[activity.mess] = 0.0
        prize.meters["dirty"] = 0.0
    actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    world.say(f"They {clean.tail}, and the kitchen-table comedy got even funnier.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(actor.id)
    prize = sim.get(prize_id)
    _mess(sim, hero, activity)
    _soil_prize(sim, hero, prize, activity)
    return {
        "soiled": prize.meters.get(activity.mess, 0.0) >= THRESHOLD,
        "dirty": prize.meters.get("dirty", 0.0) >= THRESHOLD,
    }


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="boy" if name in {"Milo", "Toby", "Arlo", "Ezra"} else "girl",
        meters={},
        memes={"bravery": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type="mother",
        label="Mom",
        memes={},
    ))
    prize = world.add(Entity(
        id="pants",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.say(
        f"{hero.id} was a {trait} child who felt brave about lunch, especially when ketchup was on the table."
    )
    world.say(
        f"{hero.id} loved {activity.gerund}, because it made an ordinary meal feel like a joke waiting to happen."
    )
    world.say(
        f"One day at {setting.place}, {hero.id}'s {parent.label} had bought {hero.pronoun('object')} {prize.phrase}."
    )
    world.say(
        f"{hero.id} liked the light color of the {prize.label}, even if it made every little spill obvious."
    )

    world.para()
    world.say(
        f"At {setting.place}, {hero.id} tried to {activity.verb}, and the bottle gave a comic little hiccup."
    )
    _mess(world, hero, activity)
    _soil_prize(world, hero, prize, activity)
    pred = predict_mess(world, hero, activity, prize.id)
    world.facts["predicted"] = pred

    world.say(
        f"{hero.id} froze for a second, then smiled. {hero.pronoun().capitalize()} was brave enough to say, "
        f"\"Oops, that one went rogue.\""
    )
    world.say(
        f"That honesty made {parent.label} grin instead of scold."
    )

    world.para()
    clean = select_cleanup(activity, prize)
    if not clean:
        raise StoryError(explain_rejection(activity, prize))
    world.say(
        f"{parent.label} pointed to {clean.label} and said, \"Let's fix the spill before it becomes a parade.\""
    )
    world.say(
        f"{hero.id} nodded and helped {clean.prep}."
    )
    _cleanup(world, hero, prize, activity, clean)

    world.say(
        f"In the end, the {prize.label} were cleaner, the ketchup stayed on the plate, and {hero.id} laughed so hard they snorted."
    )
    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        cleanup=clean,
        resolved=True,
    )
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short comedy for a child who is brave, using the word "{act.keyword}" and a ketchup spill.',
        f"Tell a funny story where {hero.id} tries to {act.verb} and ends up helping clean {hero.pronoun('possessive')} pants.",
        f"Write a simple story about bravery, ketchup, and a silly accident at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    clean = f["cleanup"]
    qa = [
        QAItem(
            question=f"What was {hero.id} brave enough to do at {world.setting.place}?",
            answer=f"{hero.id} was brave enough to {act.verb}, even though ketchup was on the table.",
        ),
        QAItem(
            question=f"What got spotted red when the ketchup splashed?",
            answer=f"{hero.pronoun('possessive').capitalize()} {prize.label} got spotted red.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} fix the mess?",
            answer=f"They used {clean.tool} and then {clean.tail}.",
        ),
    ]
    if f["prize"].meters.get("dirty", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"Why did {hero.id} stop for a moment after the squeeze went wrong?",
                answer=(
                    f"{hero.id} stopped because the ketchup splash had made {hero.pronoun('possessive')} "
                    f"{prize.label} look messy, but {hero.id} stayed brave and told the truth."
                ),
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end after the cleanup?",
                answer=(
                    f"It ended happily, with the {prize.label} cleaner, the ketchup back on the plate, "
                    f"and everyone laughing at the silly mishap."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "ketchup": [
        QAItem(
            question="What is ketchup?",
            answer="Ketchup is a thick red sauce that people often put on fries, burgers, and hot dogs.",
        )
    ],
    "red": [
        QAItem(
            question="Why do red stains stand out on light clothes?",
            answer="Red stains stand out because they are easy to see on light cloth and make the fabric look spotted.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel shy, worried, or embarrassed.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story funny?",
            answer="A story can be funny when something goes a little wrong, but nobody gets hurt and everyone can laugh about it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("bravery")
    tags.add("comedy")
    out: list[QAItem] = []
    for tag in ["ketchup", "red", "bravery", "comedy"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
dirty(P, A) :- prize_at_risk(A, P), mess_of(A, M), makes_stain(M).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), cleanup_for(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        lines.append(asp.fact("makes_stain", act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for clean in CLEANUPS:
        lines.append(asp.fact("cleanup_for", "ketchup", "pants"))
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


# -----------------------------------------------------------------------------
# Params and generation
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="kitchen", activity="ketchup", prize="pants", name="Milo", trait="brave"),
    StoryParams(place="picnic", activity="ketchup", prize="pants", name="Nia", trait="cheerful"),
    StoryParams(place="diner", activity="ketchup", prize="pants", name="Toby", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A brave, comic ketchup-and-pants storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.trait)
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combo(s):")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
