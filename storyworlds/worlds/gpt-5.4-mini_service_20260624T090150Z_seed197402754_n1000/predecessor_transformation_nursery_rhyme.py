#!/usr/bin/env python3
"""
storyworlds/worlds/predecessor_transformation_nursery_rhyme.py
==============================================================

A small storyworld about a little predecessor state that changes into a new
one. The prose leans toward nursery-rhyme cadence: concrete, gentle, and
repeatable, with a clear before/after turn.

Premise:
- A small child or creature begins in a predecessor form.
- A simple, safe change is possible only with the right help, place, and timing.
- The story celebrates the change without losing the memory of what came before.

The simulated world tracks:
- physical meters: small-state indicators like size, snugness, dampness, glow
- emotional memes: worry, hope, pride, delight

The story is driven by world state, not by a fixed paragraph template.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    form: str = ""
    target_form: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    title: str
    verb: str
    gerund: str
    cue: str
    result: str
    before_label: str
    after_label: str
    needed: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KeepSafe:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_transformed(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("ready", 0.0) < THRESHOLD:
            continue
        if ent.form != ent.target_form:
            continue
        sig = ("transformed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["changed"] = 1.0
        ent.memes["pride"] = ent.memes.get("pride", 0.0) + 1.0
        out.append(f"{ent.label or ent.id} changed at last.")
    return out


CAUSAL_RULES = [type("Rule", (), {"name": "transformed", "apply": staticmethod(_r_transformed)})]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def form_at_risk(trans: Transformation, prize_form: str) -> bool:
    return prize_form == trans.before_label


def select_keep(trans: Transformation, prize_form: str) -> Optional[KeepSafe]:
    for item in KEEPSAFE:
        if trans.needed in item.helps and prize_form in item.covers:
            return item
    return None


def predict_change(world: World, hero: Entity, trans: Transformation, helper_id: str) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["ready"] = 1.0
    h.form = trans.after_label
    propagate(sim, narrate=False)
    return {"changed": h.meters.get("changed", 0.0) >= THRESHOLD}


def introduce(world: World, hero: Entity, trans: Transformation) -> None:
    world.say(
        f"Little {hero.label} was once a {trans.before_label}, as small as a dew-drop in the morn."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the quiet of {world.setting.place} and listened to the soft old song."
    )


def long_for_change(world: World, hero: Entity, trans: Transformation) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"But {hero.label} longed to {trans.verb}, for every little thing must grow in its turn."
    )


def warn(world: World, parent: Entity, hero: Entity, trans: Transformation) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f'"Not yet," said {parent.label}. "First we need the {trans.needed}, '
        f"or the change may not take.""
    )


def offer_help(world: World, parent: Entity, hero: Entity, trans: Transformation, keep: KeepSafe) -> None:
    hero.memes["ready"] = 1.0
    world.say(
        f"{parent.label} brought {keep.phrase}, and the two of them made a little plan."
    )
    world.say(
        f"They would keep the {trans.before_label} safe while it learned the {trans.after_label} way."
    )


def bloom(world: World, hero: Entity, trans: Transformation) -> None:
    hero.form = trans.after_label
    hero.meters["changed"] = 1.0
    hero.meters["bright"] = 1.0
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then, like a pebble kissed by the sun, {hero.label} began to {trans.verb}."
    )
    world.say(
        f"At the end, {hero.label} was no longer a {trans.before_label}; {hero.pronoun()} was a {trans.after_label}, "
        f"glowing softly and ready to sing."
    )


def tell(setting: Setting, trans: Transformation, hero_name: str = "Mina", hero_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=hero_name,
            form=trans.before_label,
            target_form=trans.after_label,
            meters={"changed": 0.0, "bright": 0.0},
            memes={"hope": 0.0, "worry": 0.0, "ready": 0.0},
        )
    )
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="Mama"))
    helper = world.add(Entity(id="helper", kind="thing", type="thing", label="the warm light"))
    world.facts.update(hero=hero, parent=parent, helper=helper, trans=trans)

    introduce(world, hero, trans)
    long_for_change(world, hero, trans)
    world.para()
    warn(world, parent, hero, trans)
    keep = select_keep(trans, trans.before_label)
    if keep is None:
        raise StoryError("No safe helper exists for this transformation.")
    offer_help(world, parent, hero, trans, keep)
    world.para()
    bloom(world, hero, trans)
    world.facts["keep"] = keep
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"grow"}),
    "pond": Setting(place="the pond", indoors=False, affords={"grow"}),
    "windowsill": Setting(place="the sunny windowsill", indoors=True, affords={"grow"}),
}

TRANSFORMATIONS = {
    "seed_to_sunflower": Transformation(
        id="seed_to_sunflower",
        title="seed to sunflower",
        verb="open into a tall sunflower",
        gerund="opening into a tall sunflower",
        cue="sun",
        result="sunflower",
        before_label="seed",
        after_label="sunflower",
        needed="warm soil",
        risk="too cold to grow",
        tags={"grow", "sun", "seed"},
    ),
    "cocoon_to_butterfly": Transformation(
        id="cocoon_to_butterfly",
        title="cocoon to butterfly",
        verb="flutter out as a butterfly",
        gerund="fluttering out as a butterfly",
        cue="cocoon",
        result="butterfly",
        before_label="cocoon",
        after_label="butterfly",
        needed="quiet time",
        risk="too much poking",
        tags={"grow", "cocoon", "wing"},
    ),
    "tadpole_to_frog": Transformation(
        id="tadpole_to_frog",
        title="tadpole to frog",
        verb="hop out as a frog",
        gerund="hopping out as a frog",
        cue="pond",
        result="frog",
        before_label="tadpole",
        after_label="frog",
        needed="still water",
        risk="muddy splashing",
        tags={"grow", "pond", "water"},
    ),
}

KEEPSAFE = [
    KeepSafe(id="warm_soil", label="warm soil", phrase="a little nest of warm soil", helps={"warm soil"}, covers={"seed"}),
    KeepSafe(id="quiet_time", label="quiet time", phrase="a soft hush and a curtain of leaves", helps={"quiet time"}, covers={"cocoon"}),
    KeepSafe(id="still_water", label="still water", phrase="a calm, round pond", helps={"still water"}, covers={"tadpole"}),
]

NAMES = ["Mina", "Lily", "Pip", "Nora", "Toby", "Milo"]
BOY_NAMES = ["Pip", "Toby", "Milo", "Ben", "Theo"]
GIRL_NAMES = ["Mina", "Lily", "Nora", "Wren", "Ivy"]


@dataclass
class StoryParams:
    setting: str
    transformation: str
    name: str
    gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trans = f["trans"]
    return [
        f'Write a gentle nursery-rhyme story about a {trans.before_label} that becomes a {trans.after_label}.',
        f"Tell a child-friendly story where {hero.label} is the predecessor form before {trans.after_label} appears.",
        f'Write a short rhyme about "before" and "after" using the word "{trans.before_label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    trans = f["trans"]
    keep = f["keep"]
    return [
        QAItem(
            question=f"What was {hero.label} before the change?",
            answer=f"{hero.label} was a {trans.before_label} first. That was the predecessor form before the new {trans.after_label} way arrived.",
        ),
        QAItem(
            question=f"Why did Mama bring the {keep.label}?",
            answer=f"Mama brought the {keep.label} because {hero.label} needed {trans.needed} to change safely, and the old form could not risk {trans.risk}.",
        ),
        QAItem(
            question=f"What did {hero.label} become at the end?",
            answer=f"At the end, {hero.label} became a {trans.after_label}. The old predecessor form was left behind, and the new one shone bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does predecessor mean?",
            answer="A predecessor is something that came before another thing. In a story, it can be the first form before a change.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change from one form into another. A seed can become a flower, or a tadpole can become a frog.",
        ),
    ]


ASP_RULES = r"""
before(X) :- form(X, F), predecessor(F).
safe(X) :- needs(X, N), keep_safe(N).
can_change(X) :- before(X), safe(X).
after(X) :- can_change(X), target(X, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("predecessor", t.before_label))
        lines.append(asp.fact("target_form", t.after_label))
        lines.append(asp.fact("needs", tid, t.needed))
        lines.append(asp.fact("risk", tid, t.risk))
        lines.append(asp.fact("form", tid, t.before_label))
    for kid, k in [(k.id, k) for k in KEEPSAFE]:
        lines.append(asp.fact("keep_safe", k.label))
        for h in sorted(k.helps):
            lines.append(asp.fact("helps", kid, h))
        for c in sorted(k.covers):
            lines.append(asp.fact("covers", kid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in TRANSFORMATIONS.items():
            if s.indoors and t.needed == "still water":
                continue
            combos.append((sid, tid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show before/1. #show after/1."))
    return sorted(set((atom[0],) if len(atom) == 1 else atom for atom in asp.atoms(model, "before")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about predecessor forms and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    setting, transformation = rng.choice(combos)
    if args.setting:
        setting = args.setting
    if args.transformation:
        transformation = args.transformation
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, transformation=transformation, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TRANSFORMATIONS[params.transformation], params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.form:
            bits.append(f"form={e.form}")
        if e.target_form:
            bits.append(f"target={e.target_form}")
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
        print(asp_program("#show before/1. #show after/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world uses a compact parity check only.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="garden", transformation="seed_to_sunflower", name="Mina", gender="girl"),
            StoryParams(setting="pond", transformation="tadpole_to_frog", name="Toby", gender="boy"),
            StoryParams(setting="windowsill", transformation="cocoon_to_butterfly", name="Lily", gender="girl"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
