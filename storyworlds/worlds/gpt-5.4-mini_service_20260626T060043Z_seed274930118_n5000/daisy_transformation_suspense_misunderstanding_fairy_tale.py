#!/usr/bin/env python3
"""
A small fairy-tale story world about Daisy, a misunderstanding, and a spell
that transforms the world just long enough to make the suspense matter.

Seed tale:
---
Daisy was a tiny daisy in a moonlit meadow. A silver fairy saw Daisy shaking
in the wind and misunderstood her as wishing to walk like a child. The fairy
cast a spell, and Daisy became a little girl so she could cross the dark path
to a ringing bell before midnight.

But the path was shadowed and strange, and Daisy worried she would never be a
flower again. In the end, she found the bell, the fairy learned Daisy had only
wanted shelter, and the spell turned gentle when the moon rose.

Causal shape:
- suspicion / misunderstanding raises confusion and fear
- spell transformation changes the body state and opens a risky path
- suspense is driven by a moon timer and the danger of the dark path
- truth spoken in time resolves the spell and returns Daisy safely
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed_from: str = ""
    transformed_to: str = ""
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    place: str
    enchanted: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    trigger: str
    effect: str
    form: str
    duration: str
    price: str
    keyword: str = "transformation"


@dataclass
class StoryParams:
    setting: str
    spell: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turn: int = 0

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.turn = self.turn
        return w


SETTINGS = {
    "meadow": Setting("meadow", "the moonlit meadow", True, {"transform", "hush"}),
    "cottage": Setting("cottage", "the cottage garden", True, {"transform", "hush"}),
    "bridge": Setting("bridge", "the whispering bridge", True, {"transform", "hush"}),
}

SPELLS = {
    "girlspell": Spell(
        id="girlspell",
        trigger="wanted to cross the dark path",
        effect="changed Daisy into a little girl",
        form="little girl",
        duration="until the moon rose high",
        price="the spell would fade when the truth was spoken",
        keyword="transformation",
    ),
    "lanternspell": Spell(
        id="lanternspell",
        trigger="needed light in the dark",
        effect="turned Daisy into a glowing lantern-flower",
        form="glowing lantern-flower",
        duration="until the first bell rang",
        price="the glow would sleep if Daisy grew too afraid",
        keyword="suspense",
    ),
}

GIRL_NAMES = ["Daisy", "Luna", "Mina", "Ivy"]
FAIRY_NAMES = ["Silverwing", "Mosspetal", "Starbell"]
TRAITS = ["gentle", "curious", "brave", "soft-hearted"]


def reasonableness(spell: Spell, setting: Setting) -> bool:
    return "transform" in setting.affords and "hush" in setting.affords and spell.id in SPELLS


ASP_RULES = r"""
setting(meadow). setting(cottage). setting(bridge).
affords(meadow, transform). affords(meadow, hush).
affords(cottage, transform). affords(cottage, hush).
affords(bridge, transform). affords(bridge, hush).

spell(girlspell). spell(lanternspell).

reasonable(S, P) :- setting(S), spell(P), affords(S, transform), affords(S, hush).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for pid in SPELLS:
        lines.append(asp.fact("spell", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for p in SPELLS:
            if reasonableness(SPELLS[p], SETTINGS[s]):
                combos.append((s, p))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


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
    ap = argparse.ArgumentParser(description="A fairy-tale story world of Daisy, transformation, suspense, and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
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
    combos = valid_combos()
    if args.setting and args.spell:
        if (args.setting, args.spell) not in combos:
            raise StoryError("That setting and spell do not make a reasonable fairy-tale transformation.")
        return StoryParams(setting=args.setting, spell=args.spell)
    filtered = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.spell is None or c[1] == args.spell)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    s, p = rng.choice(filtered)
    return StoryParams(setting=s, spell=p)


def _narrate_setup(world: World, daisy: Entity, fairy: Entity, spell: Spell) -> None:
    world.say(f"Long ago, in {world.setting.place}, there lived a tiny daisy named {daisy.id}.")
    world.say(f"{daisy.id} loved the warm hush of the meadow, but {daisy.pronoun()} trembled whenever the wind bent the grass.")
    world.say(f"Near the moonlit path lived {fairy.id}, a {fairy.label} who listened to every whisper in the night.")
    world.say(f"One evening, {fairy.id} saw {daisy.id} shaking and thought {daisy.pronoun('subject')} was asking for {spell.keyword}.")


def _do_transformation(world: World, daisy: Entity, spell: Spell) -> None:
    sig = ("transform", spell.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    daisy.meters["fear"] += 1
    daisy.meters["body"] = 1
    daisy.memes["confusion"] += 1
    daisy.transformed_from = "daisy"
    daisy.transformed_to = spell.form
    world.say(f"{fairy.id} lifted a silver wand and whispered a spell.")
    world.say(f"In a blink, {spell.effect}.")
    world.say(f"Now {daisy.id} wore the shape of a {spell.form}, and the dark path seemed much farther away.")


def _do_suspense(world: World, daisy: Entity, spell: Spell) -> None:
    if ("suspense", spell.id) in world.fired:
        return
    world.fired.add(("suspense", spell.id))
    daisy.meters["danger"] += 1
    daisy.memes["worry"] += 1
    world.say(f"But the moon was still low, and the first bell had not yet rung.")
    world.say(f"Through the trees, the path to the little bell looked shadowy and long, and {daisy.id} wondered if the spell would last too long.")


def _do_misunderstanding(world: World, daisy: Entity, fairy: Entity, spell: Spell) -> None:
    if ("misunderstanding", spell.id) in world.fired:
        return
    world.fired.add(("misunderstanding", spell.id))
    fairy.memes["certainty"] += 1
    fairy.memes["blindness"] += 1
    daisy.memes["silence"] += 1
    world.say(f"{fairy.id} smiled, thinking the magic was a kindness.")
    world.say(f"But {daisy.id} was not wishing to change; {daisy.pronoun('subject')} only wanted shelter and a kinder path through the night.")


def _do_truth(world: World, daisy: Entity, fairy: Entity, spell: Spell) -> None:
    if ("truth", spell.id) in world.fired:
        return
    world.fired.add(("truth", spell.id))
    daisy.memes["courage"] += 1
    fairy.memes["shame"] += 1
    fairy.memes["love"] += 1
    daisy.memes["confusion"] = 0
    world.say(f"At last, {daisy.id} found her voice and told the truth beneath the silver branches.")
    world.say(f'"I did not ask to change," {daisy.id} said. "I only wanted to be safe."')
    world.say(f"Then {fairy.id} understood the mistake, and the spell softened like dew on petals.")


def _do_resolution(world: World, daisy: Entity, fairy: Entity, spell: Spell) -> None:
    if ("resolve", spell.id) in world.fired:
        return
    world.fired.add(("resolve", spell.id))
    daisy.transformed_to = "daisy"
    daisy.meters["danger"] = 0
    daisy.meters["fear"] = 0
    world.say(f"The moon climbed high, and the magic unwound gently.")
    world.say(f"Before the bell could echo again, {daisy.id} was a daisy once more, standing safely in the glow.")
    world.say(f"{fairy.id} bowed her head, and the meadow kept its quiet secret in the grass.")


def generate_world(setting: Setting, spell: Spell, name: str = "Daisy", fairy_name: str = "Silverwing", trait: str = "gentle") -> World:
    world = World(setting)
    daisy = world.add(Entity(id=name, kind="character", type="daisy", label="little daisy", location=setting.place))
    fairy = world.add(Entity(id=fairy_name, kind="character", type="fairy", label="silver fairy", location=setting.place))
    daisy.meters.update({"fear": 0, "danger": 0, "body": 0})
    daisy.memes.update({"confusion": 0, "worry": 0, "courage": 0, "silence": 0})
    fairy.meters.update({"magic": 1})
    fairy.memes.update({"certainty": 0, "blindness": 0, "love": 0, "shame": 0})

    world.facts.update(daisy=daisy, fairy=fairy, spell=spell, trait=trait)
    _narrate_setup(world, daisy, fairy, spell)
    world.para()
    _do_transformation(world, daisy, spell)
    _do_suspense(world, daisy, spell)
    _do_misunderstanding(world, daisy, fairy, spell)
    world.para()
    _do_truth(world, daisy, fairy, spell)
    _do_resolution(world, daisy, fairy, spell)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a young child about {f["daisy"].id}, a daisy, and a spell of {f["spell"].keyword}.',
        f"Tell a gentle story where a silver fairy misunderstands {f['daisy'].id} and magic changes the shape of the night.",
        f"Write a suspenseful fairy tale with a misunderstanding, a transformation, and a happy ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    daisy, fairy, spell = f["daisy"], f["fairy"], f["spell"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {daisy.id}, a tiny daisy who had to face a strange spell and a dark path.",
        ),
        QAItem(
            question=f"What did the fairy misunderstand about {daisy.id}?",
            answer=f"The fairy misunderstood {daisy.id}'s trembling and thought the daisy wanted {spell.keyword}, when really {daisy.id} only wanted safety.",
        ),
        QAItem(
            question=f"What changed {daisy.id} during the middle of the story?",
            answer=f"A silver spell changed {daisy.id} from a daisy into {spell.form}, which made the night feel full of suspense.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=f"{daisy.id} spoke the truth, and {fairy.id} understood the mistake. Then the spell softened and {daisy.id} became a daisy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a daisy?",
            answer="A daisy is a small flower with bright petals and a cheerful face that often grows in meadows and gardens.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing and acts on it before the truth is clear.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form, like a flower becoming something else in a spell.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of worry or waiting when something important might happen soon.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.transformed_from or e.transformed_to:
            bits.append(f"transform={e.transformed_from}->{e.transformed_to}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


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
    StoryParams(setting="meadow", spell="girlspell"),
    StoryParams(setting="cottage", spell="lanternspell"),
    StoryParams(setting="bridge", spell="girlspell"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(SETTINGS[params.setting], SPELLS[params.spell])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/spell combos:\n")
        for s, p in combos:
            print(f"  {s:8} {p}")
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
            header = f"### {p.setting} / {p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
