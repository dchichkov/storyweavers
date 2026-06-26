#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/moment_semantic_mild_kindness_fairy_tale.py
=========================================================================================================================

A small fairy-tale storyworld about kindness at the right moment.

Premise:
- A gentle fairy or child-like helper notices a tiny problem in a village, wood,
  or garden.
- A mild, kind response at the right moment turns a worry into comfort.
- The world keeps track of both physical state ("meters") and feelings
  ("memes"), so the ending is driven by causal changes rather than swapped nouns.

This world is intentionally compact and constraint-checked: only plausible
stories are generated, and invalid explicit choices raise ``StoryError``.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "fairy", "mother"}
        male = {"boy", "king", "boy-fairy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    kind: str  # village, forest, cottage, garden
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    source: str
    damage: str
    concern: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    action: str
    effect: str
    fits: set[str]
    tags: set[str] = field(default_factory=set)


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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for aid in list(world.entities.values()):
        if aid.kind != "character":
            continue
        if aid.memes.get("comfort", 0.0) < THRESHOLD:
            continue
        if aid.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("relief", aid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        aid.memes["worry"] = 0.0
        aid.memes["peace"] = aid.memes.get("peace", 0.0) + 1
        out.append(f"{aid.id} felt lighter inside.")
    return out


CAUSAL_RULES = [
    _r_relief,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(setting: Setting, trouble: Trouble, aid: Aid, hero_name: str, hero_type: str,
                helper_name: str, helper_type: str) -> World:
    if trouble.id not in setting.affords:
        raise StoryError("That trouble does not fit this setting.")
    if trouble.id not in aid.fits:
        raise StoryError("No kind enough aid matches that trouble.")

    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "gentle"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["kind", "mild"],
    ))
    problem = world.add(Entity(
        id="trouble",
        type=trouble.id,
        label=trouble.label,
        phrase=trouble.source,
        caretaker=helper.id,
    ))
    help_item = world.add(Entity(
        id="aid",
        type=aid.id,
        label=aid.label,
        phrase=aid.action,
        owner=helper.id,
    ))

    world.say(
        f"Once, in {setting.place}, there lived a little {hero.type} named {hero.id} "
        f"who loved a quiet, happy day."
    )
    world.say(
        f"Nearby, {helper.id} noticed a {problem.label} from {problem.phrase}, and it was enough to make the day feel uneasy."
    )

    world.para()
    hero.memes["worry"] = 1.0
    world.say(
        f"{hero.id} saw the trouble and felt a small worry in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"Then {helper.id} came at just the right moment and chose a mild, kind way to help: {help_item.phrase}."
    )
    world.say(
        f"It did not make a big fuss; it only {aid.effect}."
    )
    helper.memes["comfort"] = 1.0
    problem.meters["damage"] = 0.0
    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    world.say(
        f"After that, {hero.id} smiled at {helper.id}, because the kind answer had arrived in the right moment."
    )
    world.say(
        f"The little place felt soft and safe again, and the day ended with gentle peace."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=problem,
        aid=help_item,
        setting=setting,
        trouble=trouble,
        helper_tool=aid,
    )
    return world


SETTINGS = {
    "village": Setting(place="the village green", kind="village", affords={"lost", "tear", "snag"}),
    "forest": Setting(place="the forest path", kind="forest", affords={"lost", "tear"}),
    "cottage": Setting(place="the cottage door", kind="cottage", affords={"snag", "lost"}),
    "garden": Setting(place="the garden gate", kind="garden", affords={"tear", "snag"}),
}

TROUBLES = {
    "lost": Trouble(
        id="lost",
        label="lost ribbon",
        source="a ribbon that had slipped under a bench",
        damage="gone missing",
        concern="worried someone",
        zone="hands",
        tags={"lost", "ribbon"},
    ),
    "tear": Trouble(
        id="tear",
        label="torn sleeve",
        source="a sleeve caught on a thorn",
        damage="torn",
        concern="hurt the cloth",
        zone="arm",
        tags={"tear", "cloth"},
    ),
    "snag": Trouble(
        id="snag",
        label="snagged basket handle",
        source="a basket handle stuck on a nail",
        damage="stuck",
        concern="would not let it carry well",
        zone="hands",
        tags={"snag", "basket"},
    ),
}

AIDS = {
    "ribbon": Aid(
        id="ribbon",
        label="a soft ribbon",
        action="smooth it into place",
        effect="made the ribbon easy to tie again",
        fits={"lost"},
        tags={"ribbon", "kindness"},
    ),
    "needle": Aid(
        id="needle",
        label="a tiny needle and thread",
        action="mend it with tiny stitches",
        effect="closed the tear with careful little stitches",
        fits={"tear"},
        tags={"cloth", "mend"},
    ),
    "oil": Aid(
        id="oil",
        label="a drop of oil",
        action="loosen the catch",
        effect="helped the snag slide free without a yank",
        fits={"snag"},
        tags={"basket", "kindness"},
    ),
}

GIRL_NAMES = ["Mira", "Luna", "Ivy", "Rose", "Nina", "Elsa"]
BOY_NAMES = ["Finn", "Theo", "Robin", "Pip", "Noel", "Jasper"]
HELPER_NAMES = ["Nora", "Cedric", "Mabel", "Oren", "Elowen", "Rowan"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    aid: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


ASP_RULES = r"""
setting(village). setting(forest). setting(cottage). setting(garden).

affords(village,lost). affords(village,tear). affords(village,snag).
affords(forest,lost). affords(forest,tear).
affords(cottage,snag). affords(cottage,lost).
affords(garden,tear). affords(garden,snag).

trouble(lost). trouble(tear). trouble(snag).
aid(ribbon). aid(needle). aid(oil).

fits(ribbon,lost).
fits(needle,tear).
fits(oil,snag).

compatible(S,T,A) :- affords(S,T), fits(A,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for t in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
        for t in sorted(AIDS[aid].fits):
            lines.append(asp.fact("fits", aid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in setting.affords:
            for aid in AIDS:
                if tid in AIDS[aid].fits:
                    combos.append((sid, tid, aid))
    return sorted(set(combos))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("only in clingo:", sorted(a - p))
    if p - a:
        print("only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale kindness storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.trouble:
        combos = [c for c in combos if c[1] == args.trouble]
    if args.aid:
        combos = [c for c in combos if c[2] == args.aid]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, trouble, aid = rng.choice(combos)
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    if args.gender and args.name:
        hero_name = args.name
    else:
        hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        trouble=trouble,
        aid=aid,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trouble = f["trouble"]
    aid = f["helper_tool"]
    return [
        f'Write a short fairy tale about kindness, a {trouble.label}, and a mild solution in {world.setting.place}.',
        f"Tell a gentle story where {hero.id} learns that {helper.id} can help at just the right moment with {aid.label}.",
        f'Write a child-friendly fairy tale that includes the words "moment", "semantic", and "mild" and ends in peace.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trouble = f["trouble"]
    aid = f["helper_tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did the little story happen?",
            answer=f"It happened at {setting.place}, a place that could hold a small trouble and a kind answer.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the trouble appeared?",
            answer=f"{helper.id} helped {hero.id} with a mild, kind action at just the right moment.",
        ),
        QAItem(
            question=f"What was the trouble in the story?",
            answer=f"The trouble was {trouble.label}, which came from {trouble.source}.",
        ),
        QAItem(
            question=f"How did the helper make things better?",
            answer=f"{helper.id} used {aid.label} to {aid.action}, and that made the trouble feel safe and small again.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"{hero.id} felt happy instead of worried, and the place ended in gentle peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle actions that help someone feel safe, seen, or cared for.",
        ),
        QAItem(
            question="What is a moment?",
            answer="A moment is a very short time, like the tiny instant when someone decides to help.",
        ),
        QAItem(
            question="What does mild mean?",
            answer="Mild means gentle or not too strong, like a soft answer instead of a rough one.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a make-believe story with a magical feeling, often about hopes, lessons, and happy endings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        SETTINGS[params.setting],
        TROUBLES[params.trouble],
        AIDS[params.aid],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
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
    StoryParams(setting="village", trouble="lost", aid="ribbon", hero_name="Mira", hero_type="girl", helper_name="Nora", helper_type="girl"),
    StoryParams(setting="forest", trouble="tear", aid="needle", hero_name="Finn", hero_type="boy", helper_name="Elowen", helper_type="girl"),
    StoryParams(setting="garden", trouble="snag", aid="oil", hero_name="Ivy", hero_type="girl", helper_name="Cedric", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, t, a in combos:
            print(f"  {s:8} {t:6} {a:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
