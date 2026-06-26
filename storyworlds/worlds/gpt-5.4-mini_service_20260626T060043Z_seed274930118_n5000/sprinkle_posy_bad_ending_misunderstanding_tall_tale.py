#!/usr/bin/env python3
"""
storyworlds/worlds/sprinkle_posy_bad_ending_misunderstanding_tall_tale.py
==========================================================================

A tiny tall-tale storyworld about a child, a sprinkle, and a treasured posy.

Seed-tale premise:
---
A child named Nell carried a tiny posy to a county fair. A great sprinkler in
the garden was supposed to help the flowers. But the child and the grown-up
misunderstood each other: one meant "sprinkle the path," the other heard
"sprinkle the posy." The posy got soaked, the petals sagged, and the fair
ended with a bad feeling and a droopy bouquet.

This world keeps that premise small, concrete, and state-driven:
- meters track wetness, droop, and distance
- memes track worry, confidence, and misunderstanding
- the ending is intentionally a Bad Ending
- the style leans tall-tale: bold, rhythmic, a little exaggerated
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["wet", "droop", "dust", "distance"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "joy", "misunderstanding", "confidence", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_wet_posy(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    posy = world.entities.get("posy")
    sprinkler = world.entities.get("sprinkler")
    if not child or not posy or not sprinkler:
        return out
    if child.meters["wet"] < THRESHOLD:
        return out
    sig = ("wet_posy", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    posy.meters["wet"] += 1
    posy.meters["droop"] += 1
    out.append("The posy took the splash and began to droop like a tired flag.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    child = world.entities.get("child")
    grownup = world.entities.get("grownup")
    if not child or not grownup:
        return []
    if child.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("misunderstanding", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    grownup.memes["worry"] += 1
    return ["Nobody meant harm, but the words crossed in the air like two geese at dusk."]


CAUSAL_RULES = [_r_wet_posy, _r_misunderstanding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def maybe_apart(world: World, child: Entity) -> None:
    child.meters["distance"] += 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nell", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_type, label=hero_name))
    grownup = world.add(Entity(id="grownup", kind="character", type=parent_type, label="Ma"))
    sprinkler = world.add(Entity(id="sprinkler", type="machine", label="sprinkler"))
    posy = world.add(Entity(
        id="posy",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=grownup.id,
    ))

    world.say(
        f"Once, in {setting.place}, there was a little {hero_type} named {hero_name} "
        f"who carried a {prize_cfg.phrase} as carefully as a king carries his crown."
    )
    world.say(
        f"{hero_name} loved the bright little posy and kept it in sight, "
        f"for a tall-tale wind could snatch at anything with petals."
    )

    world.para()
    world.say(
        f"One day, the family went to {setting.place} where the great {activity.keyword} "
        f"was ready to {activity.verb} the path."
    )
    world.say(
        f"{hero_name} heard {grownup.label}'s words the wrong way and thought the order was to "
        f"{activity.verb} the posy itself."
    )
    child.memes["misunderstanding"] += 1
    grownup.memes["misunderstanding"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"With the confidence of a barn-cat on a fence rail, {hero_name} ran closer "
        f"and lifted the posy toward the spray."
    )

    world.para()
    child.meters["wet"] += 1
    maybe_apart(world, child)
    world.say(
        f"The sprinkler roared and sent silver beads everywhere. {hero_name} got wet, "
        f"the path shone like glass, and the posy stood right in the wrong place."
    )
    propagate(world)

    world.para()
    world.say(
        f"{grownup.label} cried out, but too late for the poor little posy. "
        f"Its petals bent down, one by one, like sleepy umbrellas after a storm."
    )
    posy.meters["wet"] += 1
    posy.meters["droop"] += 1
    child.memes["worry"] += 1
    grownup.memes["worry"] += 1

    world.para()
    world.say(
        f"When the spray finally stopped, {hero_name} held a soggy posy and stared "
        f"at the bent blooms. The fair music went on, but the flowers did not."
    )
    world.say(
        f"That was the bad ending of the tale: the misunderstanding had done its work, "
        f"and the proud little posy hung its head at last."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        sprinkler=sprinkler,
        posy=posy,
        setting=setting,
        activity=activity,
        prize_cfg=prize_cfg,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"sprinkle"}),
    "yard": Setting(place="the yard", indoors=False, affords={"sprinkle"}),
    "porch": Setting(place="the porch", indoors=False, affords={"sprinkle"}),
}

ACTIVITIES = {
    "sprinkle": Activity(
        id="sprinkle",
        verb="sprinkle",
        gerund="sprinkling",
        rush="dash into the spray",
        mess="wet",
        soil="soaked and droopy",
        keyword="sprinkle",
        tags={"water", "wet", "garden"},
    )
}

PRIZES = {
    "posy": Prize(
        label="posy",
        phrase="a tiny posy",
        type="posy",
        region="hands",
    )
}

GIRL_NAMES = ["Nell", "Poppy", "Mabel", "Sadie", "Lina", "Ruby"]
BOY_NAMES = ["Toby", "Benny", "Arlo", "Jesse", "Milo"]
TRAITS = ["bold", "merry", "curious", "wily", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                combos.append((place, act, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short tall-tale for a child named {child.label} that uses the word "{act.keyword}".',
        f"Tell a simple story where {child.label} misunderstands a grown-up and the {prize.label} ends badly.",
        f'Write a child-facing story about a {prize.phrase} near a {act.keyword} at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    prize = f["prize_cfg"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who was carrying the posy in the story?",
            answer=f"{child.label} was carrying the posy, and {grownup.label} was right there too.",
        ),
        QAItem(
            question=f"What did {child.label} misunderstand about the {act.keyword}?",
            answer=(
                f"{child.label} misunderstood the grown-up's words and thought the "
                f"spray was meant for the posy instead of the path."
            ),
        ),
        QAItem(
            question=f"What happened to the posy at the end?",
            answer=(
                f"The posy got wet and droopy. Its petals sagged, and the story ended badly "
                f"with the flowers looking tired and sad."
            ),
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"It was bad because the misunderstanding led to the posy getting soaked, "
                f"and nobody could make the bent petals stand up again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a posy?",
            answer="A posy is a small bunch of flowers, often held in one hand.",
        ),
        QAItem(
            question="What does sprinkle mean?",
            answer="To sprinkle is to scatter little drops or bits over something.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="sprinkle", prize="posy", name="Nell", gender="girl", parent="mother", trait="bold"),
    StoryParams(place="yard", activity="sprinkle", prize="posy", name="Poppy", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", activity="sprinkle", prize="posy", name="Toby", gender="boy", parent="father", trait="merry"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: a sprinkle, a posy, and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
prize(X) :- thing(X).

valid(P,A,X) :- setting(P), afford(P,A), prize(X), at_risk(A,X).

at_risk(A,X) :- splashes(A, hands), worn_on(X, hands).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact("tag", aid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("thing", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("splashes", "sprinkle", "hands"))
    return "\n".join(lines)


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
