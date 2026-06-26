#!/usr/bin/env python3
"""
storyworlds/worlds/fortune_lesson_learned_slice_of_life.py
==========================================================

A small slice-of-life story world about a child, a little bit of fortune,
and a lesson learned.

Seed image:
- A child gets a cheerful fortune slip during an ordinary day.
- They think fortune should mean "getting what I want right away."
- A gentle grown-up shows that fortune is not a shortcut, and that a
  better day comes from patience, care, and sharing.
- The child ends the story having learned something useful.

This world is intentionally small and constraint-checked. It produces one
coherent story with a clear beginning, turn, and resolution.

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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Fortune:
    id: str
    label: str
    phrase: str
    kind: str
    outcome: str
    keyword: str = "fortune"
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    region: str
    kinds: set[str] = field(default_factory=set)
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class World:
    setting: Setting

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    fortune: str
    treat: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"fortune_cookie"}),
    "bakery": Setting(place="the bakery", indoor=True, affords={"fortune_cookie"}),
    "sidewalk": Setting(place="the sidewalk", indoor=False, affords={"fortune_cookie"}),
}

FORTUNES = {
    "cookie": Fortune(
        id="cookie",
        label="fortune cookie",
        phrase="a crisp fortune cookie with a tiny paper slip inside",
        kind="cookie",
        outcome="a sweet fortune",
        tags={"fortune", "cookie", "patience"},
    ),
    "slip": Fortune(
        id="slip",
        label="fortune slip",
        phrase="a folded paper fortune slip from a lucky snack",
        kind="slip",
        outcome="a thoughtful fortune",
        tags={"fortune", "slip", "kindness"},
    ),
}

TREATS = {
    "cookie": Treat(
        id="cookie",
        label="cookie",
        phrase="a warm cookie",
        region="mouth",
        kinds={"fortune_cookie"},
    ),
    "tea": Treat(
        id="tea",
        label="tea",
        phrase="a small cup of tea and a biscuit",
        region="hands",
        kinds={"fortune_cookie"},
    ),
}

GIRL_NAMES = ["Mia", "Nina", "Lila", "Ava", "Zoe", "Ruby", "Tessa", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo", "Milo", "Sam", "Owen"]
TRAITS = ["curious", "gentle", "playful", "quiet", "thoughtful", "cheerful"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_hungry(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    if child.meters.get("hungry", 0) >= THRESHOLD and not world.facts.get("noticed_hunger"):
        world.facts["noticed_hunger"] = True
        out.append(f"{child.id}'s tummy growled a little.")
    return out


def _r_lesson(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    guide = world.facts["parent"]
    if child.memes.get("impatient", 0) >= THRESHOLD and child.memes.get("calm", 0) >= THRESHOLD:
        sig = ("lesson", child.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["lesson_learned"] = 1
        out.append(f"{child.id} remembered what {guide.label_word} had said about waiting and sharing.")
    return out


CAUSAL_RULES = [Rule("hungry", _r_hungry), Rule("lesson", _r_lesson)]


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


def valid_combo(setting: Setting, fortune: Fortune, treat: Treat) -> bool:
    return "fortune_cookie" in setting.affords and treat.kinds and fortune.kind in {"cookie", "slip"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for f in FORTUNES.values():
            for t in TREATS.values():
                if valid_combo(setting, f, t):
                    out.append((place, f.id, t.id))
    return out


def choose_compromise(fortune: Fortune, treat: Treat):
    return fortune


def tell(setting: Setting, fortune: Fortune, treat: Treat, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    snack = world.add(
        Entity(
            id="snack",
            type=treat.id,
            label=treat.label,
            phrase=treat.phrase,
            owner=child.id,
            caretaker=parent.id,
            region=treat.region,
        )
    )
    fortune_item = world.add(
        Entity(
            id="fortune",
            type=fortune.kind,
            label=fortune.label,
            phrase=fortune.phrase,
            owner=child.id,
            caretaker=parent.id,
        )
    )

    world.facts.update(child=child, parent=parent, snack=snack, fortune_item=fortune_item, fortune=fortune, treat=treat)

    child.meters["hungry"] = 1
    child.memes["hope"] = 1

    world.say(
        f"{child.id} was a little {trait} {hero_type} who liked ordinary days and tiny surprises."
    )
    world.say(
        f"At {setting.place}, {child.id} found {fortune.phrase} beside {snack.phrase}."
    )
    world.say(
        f"{child.id} loved the little fortune and wanted it to mean something extra special."
    )

    world.para()
    world.say(
        f"Later, {child.id} and {child.pronoun('possessive')} {parent.label_word} sat down for a quiet snack."
    )
    world.say(
        f"{child.id} wanted to keep the whole treat for {child.pronoun('object')}self and not wait."
    )
    child.memes["impatient"] += 1
    child.meters["want"] = 1
    propagate(world)

    world.say(
        f'But {parent.label_word} smiled and said, "A fortune is not a shortcut. '
        f"It is a reminder to make good choices."'
    )
    child.memes["worry"] = 1
    world.say(
        f"{child.id} looked at the snack and the little paper slip and slowed down."
    )

    world.para()
    child.memes["calm"] += 1
    world.say(
        f"{child.id} broke the snack in half, offered {child.pronoun('object')} {parent.label_word} the bigger piece, and saved the paper slip in a pocket."
    )
    child.meters["hungry"] = 0
    child.memes["kind"] = child.memes.get("kind", 0) + 1
    child.memes["lesson_learned"] = 1
    world.say(
        f"{parent.label_word} laughed softly, and {child.id} felt proud because sharing made the day feel luckier than before."
    )
    world.say(
        f"By the end, {child.id} had learned that fortune was nicest when it helped everyone feel a little better."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    fortune = f["fortune"]
    treat = f["treat"]
    return [
        f'Write a short slice-of-life story for a child named {child.id} that includes the word "fortune".',
        f"Tell a gentle story where {child.id} gets {fortune.phrase} and learns a useful lesson about {treat.label}.",
        f"Write an everyday story about {child.id}, a small fortune, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    fortune = f["fortune"]
    treat = f["treat"]

    return [
        QAItem(
            question=f"What did {child.id} find at {world.setting.place}?",
            answer=f"{child.id} found {fortune.phrase}. It was a small fortune that felt exciting on an ordinary day.",
        ),
        QAItem(
            question=f"Why did {child.id} slow down before eating {treat.label}?",
            answer=f"{child.id} slowed down because {parent.label_word} reminded {child.id} that a fortune is not a shortcut and that good choices matter.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn by the end?",
            answer=f"{child.id} learned that fortune is nicest when it leads to patience, sharing, and a kinder day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fortune cookie?",
            answer="A fortune cookie is a crisp cookie with a little paper slip inside that often has a short message.",
        ),
        QAItem(
            question="What does it mean to be patient?",
            answer="Being patient means waiting calmly instead of rushing right away.",
        ),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it helps another person feel cared for and makes moments together feel warmer.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F,T) :- setting(P), fortune(F), treat(T), afford_cookie(P), fortune_kind(F,k), treat_kind(T,k2), k = k2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if "fortune_cookie" in s.affords:
            lines.append(asp.fact("afford_cookie", pid))
    for fid, f in FORTUNES.items():
        lines.append(asp.fact("fortune", fid))
        lines.append(asp.fact("fortune_kind", fid, f.kind))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("treat_kind", tid, "fortune_cookie"))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life fortune storyworld with a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--fortune", choices=FORTUNES)
    ap.add_argument("--treat", choices=TREATS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.fortune:
        combos = [c for c in combos if c[1] == args.fortune]
    if args.treat:
        combos = [c for c in combos if c[2] == args.treat]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, fortune_id, treat_id = rng.choice(sorted(combos))
    fortune = FORTUNES[fortune_id]
    treat = TREATS[treat_id]
    gender = args.gender or rng.choice(sorted(treat.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(place=place, fortune=fortune_id, treat=treat_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        FORTUNES[params.fortune],
        TREATS[params.treat],
        params.name,
        params.gender,
        params.parent,
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
    StoryParams(place="kitchen", fortune="cookie", treat="cookie", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bakery", fortune="slip", treat="cookie", name="Theo", gender="boy", parent="father", trait="thoughtful"),
    StoryParams(place="sidewalk", fortune="cookie", treat="tea", name="Lila", gender="girl", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
