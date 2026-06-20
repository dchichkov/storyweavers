#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cherry_comfort_benefit_moral_value_friendship_conflict.py
=========================================================================================

A standalone story world for a tiny whodunit-like domestic mystery: a cherry
goes missing, friends disagree, someone hides behind "comfort," and the group
learns that honesty has a real benefit. The story stays child-facing and
state-driven: clues, tension, reveal, apology, and a ending image that proves
the conflict changed.

Seed words:
- cherry
- comfort
- benefit

Features:
- Moral Value
- Friendship
- Conflict

Style:
- Whodunit
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    props: str
    quiet_spot: str


@dataclass
class Mystery:
    id: str
    object_name: str
    plate_name: str
    clue: str
    hiding_place: str
    benefit: str
    moral: str
    conflict_line: str
    reveal_line: str


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.entities.values():
            if other.kind == "character" and other.id != e.id:
                other.memes["worry"] += 0.5
        out.append("__tension__")
    return out


def _r_confession(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["confession"] < THRESHOLD:
            continue
        sig = ("confess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["truth"] += 1
        out.append("__confession__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("tension", "social", _r_tension),
    Rule("confession", "social", _r_confession),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "a red table, a blue bowl, and a quiet chair", "the corner by the sink"),
    "garden": Setting("garden", "the garden", "a small bench, a fence, and a stone path", "the spot under the apple tree"),
    "playroom": Setting("playroom", "the playroom", "blocks, a rug, and a toy shelf", "the nook behind the curtain"),
}

MYSTERIES = {
    "missing_cherry": Mystery(
        "missing_cherry",
        "the cherry",
        "the cherry plate",
        "A single cherry was gone from the plate, and there was a sticky red dot nearby.",
        "under a napkin",
        "a child could tell the truth and fix the worry faster",
        "honesty can help friends trust each other",
        "No one wanted to be blamed, so the room got quiet and tense.",
        "When the truth came out, the friends could laugh again and share the cherries fairly.",
    ),
    "missing_basket": Mystery(
        "missing_basket",
        "the cherry",
        "the basket",
        "A cherry was missing from the basket, and the crumbs pointed toward the bench.",
        "in a pocket",
        "the group could stop guessing and solve the problem together",
        "friends help more when they are honest",
        "The friends started blaming each other, and their voices got sharp.",
        "Once the secret was spoken, everyone knew what happened and could make it right.",
    ),
}

COMFORTS = {
    "blanket": Comfort("blanket", "blanket", "a soft blanket", "helps a nervous child feel steady", {"comfort"}),
    "bear": Comfort("bear", "bear", "a stuffed bear", "helps a worried child tell the truth", {"comfort"}),
    "pillow": Comfort("pillow", "pillow", "a little pillow", "helps a child sit still and listen", {"comfort"}),
}

CHARACTER_NAMES = ["Lily", "Mia", "Nora", "Ava", "Ben", "Max", "Theo", "Eli"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero: str
    friend: str
    helper: str
    comfort: str
    seed: Optional[int] = None


def reasonableness_ok(params: StoryParams) -> bool:
    return params.hero != params.friend and params.hero != params.helper and params.friend != params.helper


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit story world about a missing cherry, a comfort object, and the benefit of honesty."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--helper")
    ap.add_argument("--comfort", choices=COMFORTS)
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
    if args.setting and args.mystery and (args.setting, args.mystery) not in combos:
        raise StoryError("That setting and mystery do not belong together.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    names = rng.sample(CHARACTER_NAMES, 3)
    hero = args.hero or names[0]
    friend = args.friend or names[1]
    helper = args.helper or names[2]
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    params = StoryParams(setting, mystery, hero, friend, helper, comfort)
    if not reasonableness_ok(params):
        raise StoryError("The characters need to be three different people.")
    return params


def _make_world(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    comfort = COMFORTS[params.comfort]
    hero = w.add(Entity(params.hero, kind="character", type="girl" if params.hero in {"Lily", "Mia", "Nora", "Ava"} else "boy", role="hero"))
    friend = w.add(Entity(params.friend, kind="character", type="girl" if params.friend in {"Lily", "Mia", "Nora", "Ava"} else "boy", role="friend"))
    helper = w.add(Entity(params.helper, kind="character", type="mother" if params.helper in {"Lily", "Mia", "Nora", "Ava"} else "father", role="helper"))
    plate = w.add(Entity("plate", type="thing", label=mystery.plate_name))
    cherry = w.add(Entity("cherry", type="thing", label=mystery.object_name))
    napkin = w.add(Entity("napkin", type="thing", label="napkin"))
    w.facts.update(setting=setting, mystery=mystery, comfort=comfort, hero=hero, friend=friend, helper=helper, plate=plate, cherry=cherry, napkin=napkin)
    return w


def tell(world: World) -> None:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    helper: Entity = f["helper"]
    comfort: Comfort = f["comfort"]
    cherry: Entity = f["cherry"]
    napkin: Entity = f["napkin"]

    hero.memes["curiosity"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"On a quiet afternoon, {hero.id} and {friend.id} were in {setting.place}. "
        f"{setting.props} sat nearby, and a plate of cherries waited on the table."
    )
    world.say(
        f"Then something strange happened. {mystery.clue}"
    )
    world.say(
        f'{friend.id} frowned. "{mystery.conflict_line}"'
    )

    world.para()
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} looked around like a little detective and pointed at the table, "
        f"the floor, and {setting.quiet_spot}. {hero.id} wanted to know who had moved the cherry."
    )
    world.say(
        f"But {friend.id} kept glancing at {comfort.phrase}. {friend.id} said it made {comfort.helps}."
    )
    world.say(
        f'{friend.id} whispered, "Maybe I know where it is." Then {friend.id} went very still.'
    )
    friend.memes["worry"] += 1
    propagate(world, narrate=False)

    world.para()
    helper.memes["patience"] += 1
    world.say(
        f"{helper.id} came in with a calm step and said, "
        f'"Let us look closely instead of guessing. The answer will help our friendship."'
    )
    world.say(
        f"{helper.id} noticed a sticky red smear leading to {mystery.hiding_place}."
    )
    world.say(
        f"At last, {friend.id} sighed and spoke up. {friend.id} had moved the cherry "
        f"there so nobody would take it before dessert."
    )
    friend.memes["confession"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f'{helper.id} nodded. "Thank you for telling the truth," {helper.pronoun()} said. '
        f'"That is the moral value here. Honesty brings a real benefit, because it helps '
        f'friends fix the problem faster."'
    )
    world.say(
        f"{friend.id} put the cherry back on the plate. Then {hero.id} and {friend.id} "
        f"shared the cherries fairly, and the room felt light again."
    )
    world.say(
        f"By the end, {mystery.reveal_line}"
    )

    world.facts.update(
        hero=hero, friend=friend, helper=helper, comfort=comfort, cherry=cherry,
        setting=setting, mystery=mystery, truth_spoken=friend.meters["truth"] >= THRESHOLD,
        resolved=True, conflict=True
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f'Write a whodunit-style story for a young child that includes the word "{mystery.object_name}" and ends with a moral lesson.',
        f"Tell a short friendship mystery where a cherry goes missing, someone feels comforted by {f['comfort'].phrase}, and honesty solves the conflict.",
        f"Write a gentle mystery story about {mystery.object_name}, friendship, and conflict, with a clear benefit to telling the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    qa = [
        QAItem(
            question="What was missing?",
            answer=f"{mystery.object_name} was missing, and that made everyone curious and a little tense."
        ),
        QAItem(
            question="Why did the room feel uncomfortable?",
            answer=f"{friend.id} was scared of being blamed, so {friend.id} stayed quiet instead of saying what happened. That silence made the friendship conflict grow."
        ),
        QAItem(
            question="What did the helper ask the children to do?",
            answer=f"{helper.id} asked them to look closely instead of guessing. That helped them find the real clue and stop blaming each other."
        ),
        QAItem(
            question="What was the moral value in the story?",
            answer=f"The moral value was honesty. When {friend.id} told the truth, the friends could fix the problem and trust each other again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a cherry?", "A cherry is a small round fruit. It can be sweet, and people often put it on desserts."),
        QAItem("What does comfort mean?", "Comfort means feeling safe, calm, and not worried. A comfort object can help someone relax."),
        QAItem("Why is honesty a benefit?", "Honesty is a benefit because it helps people solve problems sooner. It also helps friends trust each other."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "missing_cherry", "Lily", "Ben", "Mia", "bear"),
    StoryParams("garden", "missing_basket", "Nora", "Max", "Theo", "blanket"),
    StoryParams("playroom", "missing_cherry", "Ava", "Eli", "Mia", "pillow"),
]


def explain_rejection() -> str:
    return "(No story: the chosen characters must be three different people.)"


ASP_RULES = r"""
missing(C) :- cherry(C), not on_plate(C).
tension(H) :- character(H), worries(H).
conflict(F) :- friend(F), tension(F).
truth_benefit(F) :- friend(F), confession(F).
moral(honesty) :- confession(F), truth_benefit(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show moral/1."))
    _ = asp.atoms(model, "moral")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, hero=None, friend=None, helper=None, comfort=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: generate smoke test crashed: {exc}")
        return 1
    python_ok = all(reasonableness_ok(p) for p in CURATED)
    if not python_ok:
        print("FAIL: curated params invalid.")
        return 1
    print("OK: smoke test and basic checks passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    return sorted(valid_combos())


def asp_sensible() -> list[str]:
    return sorted(COMFORTS)


def build_sample(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("", "#show moral/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.hero} / {p.friend} / {p.helper}: {p.setting}, {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
