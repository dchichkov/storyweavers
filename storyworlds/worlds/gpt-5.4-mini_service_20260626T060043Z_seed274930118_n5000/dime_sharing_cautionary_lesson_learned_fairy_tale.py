#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dime_sharing_cautionary_lesson_learned_fairy_tale.py
===============================================================================================================================

A tiny fairy-tale story world about a dime, sharing, a cautionary mistake,
and a lesson learned.

The world is built from a short source-tale shape:

- a small fairy-tale child finds a dime
- the child is tempted to keep it all
- a cautious warning shows why selfishness can backfire
- the child learns to share, and the ending image proves the change

The simulation tracks physical meters and emotional memes so the prose is driven
by state, not by a fixed paragraph template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
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
    kind: str = "outdoor"
    affords: set[str] = field(default_factory=set)
    feature: str = ""


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    value: int = 1


@dataclass
class CompanionSpec:
    type: str
    label: str
    trait: str


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    child_trait: str
    companion: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_lost_chance(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    coin = world.get("dime")
    helper = world.get("companion")
    if child.memes.get("greedy", 0.0) < THRESHOLD:
        return out
    if child.meters.get("shares", 0.0) >= THRESHOLD:
        return out
    sig = ("lost_chance",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["regret"] = child.memes.get("regret", 0.0) + 1.0
    helper.memes["hurt"] = helper.memes.get("hurt", 0.0) + 1.0
    coin.meters["safe"] = 0.0
    out.append(f"The little promise of the dime slipped away from their hands.")
    return out


def _r_sharing_bloom(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("companion")
    if child.meters.get("shares", 0.0) < THRESHOLD:
        return out
    sig = ("sharing_bloom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1.0
    child.memes["greedy"] = 0.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    out.append("Sharing made the air feel warm and bright again.")
    return out


CAUSAL_RULES = [
    Rule(name="lost_chance", apply=_r_lost_chance),
    Rule(name="sharing_bloom", apply=_r_sharing_bloom),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return setting.feature or f"The {setting.place} looked bright and still."


def predict_outcome(world: World, child: Entity, action: str) -> dict:
    sim = world.copy()
    sim.get("child").memes[action] = sim.get("child").memes.get(action, 0.0) + 1.0
    propagate(sim, narrate=False)
    return {
        "regret": sim.get("child").memes.get("regret", 0.0),
        "joy": sim.get("companion").memes.get("joy", 0.0),
        "kindness": sim.get("child").memes.get("kindness", 0.0),
    }


def introduce(world: World, child: Entity, companion: Entity, coin: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "small")
    world.say(
        f"Once upon a time, there was a little {trait} {child.type} named {child.id}, "
        f"and {child.pronoun('possessive')} dear friend was {companion.label}."
    )
    world.say(
        f"One morning, {child.id} found a shiny dime tucked beside {setting_detail(world.setting)}"
    )
    world.say(
        f"{child.id} held the dime close, for {child.pronoun()} had never owned anything so bright."
    )
    coin.carried_by = child.id
    child.meters["found"] = 1.0
    child.memes["wonder"] = 1.0


def want_to_keep(world: World, child: Entity, coin: Entity) -> None:
    child.memes["greedy"] = 1.0
    world.say(
        f"{child.id} wanted to keep {coin.it()} all alone, because the little coin gleamed like a treasure."
    )


def caution(world: World, child: Entity, companion: Entity, coin: Entity) -> None:
    pred = predict_outcome(world, child, "greedy")
    world.facts["predicted_regret"] = pred["regret"]
    world.facts["predicted_joy"] = pred["joy"]
    world.say(
        f'"If you hide the dime and share nothing," said {companion.label}, '
        f'"your heart may grow heavy, and good friends may grow sad."'
    )
    child.memes["worry"] = 1.0


def mistaken_choice(world: World, child: Entity, coin: Entity) -> None:
    child.meters["hid"] = 1.0
    world.say(
        f"But {child.id} tucked the dime away under a leaf and tried to keep the secret."
    )
    propagate(world, narrate=True)


def lesson_turn(world: World, child: Entity, companion: Entity, coin: Entity) -> None:
    child.memes["regret"] = 1.0
    world.say(
        f"Then {child.id} saw {companion.label}'s face fall, and the little secret did not feel golden anymore."
    )
    child.meters["shares"] = 1.0
    world.say(
        f"{child.id} brought the dime back, opened {child.pronoun('possessive')} hand, and shared it at last."
    )
    propagate(world, narrate=True)


def ending(world: World, child: Entity, companion: Entity, coin: Entity) -> None:
    child.meters["shared_dime"] = 1.0
    world.say(
        f"{child.id} and {companion.label} used the dime together for a tiny treat, "
        f"and the treasure felt larger when it was shared."
    )
    world.say(
        f"From that day on, {child.id} remembered the lesson: a small kindness can shine brighter than a hidden coin."
    )


SETTINGS = {
    "cottage_gate": Setting(
        place="the cottage gate",
        kind="outdoor",
        affords={"find", "share"},
        feature="The cottage gate stood beside a little rose bush and a stone path.",
    ),
    "forest_path": Setting(
        place="the forest path",
        kind="outdoor",
        affords={"find", "share"},
        feature="The forest path was lined with fern leaves and sunbeams.",
    ),
    "market_square": Setting(
        place="the market square",
        kind="outdoor",
        affords={"find", "share"},
        feature="The market square hummed softly, with carts and bright cloth in the wind.",
    ),
}

COMPANIONS = {
    "rabbit": CompanionSpec(type="rabbit", label="a gentle rabbit", trait="gentle"),
    "sparrow": CompanionSpec(type="sparrow", label="a bright sparrow", trait="bright"),
    "mole": CompanionSpec(type="mole", label="a patient mole", trait="patient"),
}

OBJECTS = {
    "dime": ObjectSpec(label="dime", phrase="a shiny dime", type="dime", value=10),
}

CHILD_NAMES = ["Lina", "Milo", "Nora", "Toby", "Ivy", "Pia", "Rafi", "Mina"]
CHILD_TYPES = ["girl", "boy"]
TRAITS = ["curious", "earnest", "gentle", "stubborn", "hopeful", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, o) for s in SETTINGS for c in COMPANIONS for o in OBJECTS]


@dataclass
class StoryWorld:
    setting: Setting
    child: Entity
    companion: Entity
    coin: Entity


def make_world(params: StoryParams) -> StoryWorld:
    setting = SETTINGS[params.setting]
    child = Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        traits=["little", params.child_trait],
    )
    companion_spec = COMPANIONS[params.companion]
    companion = Entity(
        id="companion",
        kind="character",
        type=companion_spec.type,
        label=companion_spec.label,
        traits=[companion_spec.trait],
    )
    coin = Entity(
        id="dime",
        kind="thing",
        type="dime",
        label="dime",
        phrase="a shiny dime",
        owner="child",
    )
    return StoryWorld(setting=setting, child=child, companion=companion, coin=coin)


def tell(params: StoryParams) -> World:
    sw = make_world(params)
    world = World(sw.setting)
    world.add(sw.child)
    world.add(sw.companion)
    world.add(sw.coin)

    introduce(world, sw.child, sw.companion, sw.coin)
    world.para()
    want_to_keep(world, sw.child, sw.coin)
    caution(world, sw.child, sw.companion, sw.coin)
    mistaken_choice(world, sw.child, sw.coin)
    world.para()
    lesson_turn(world, sw.child, sw.companion, sw.coin)
    ending(world, sw.child, sw.companion, sw.coin)

    world.facts.update(
        child=sw.child,
        companion=sw.companion,
        coin=sw.coin,
        setting=sw.setting,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    setting = f["setting"]
    return [
        f'Write a short fairy tale about a child named {child.label} who finds a dime at {setting.place}.',
        f"Tell a cautionary story where {child.label} almost keeps a dime too selfishly, but {companion.label} helps them learn to share.",
        "Write a gentle fairy tale with a small treasure, a warning, and a lesson learned about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.label} find at {setting.place}?",
            answer=f"{child.label} found a shiny dime at {setting.place}.",
        ),
        QAItem(
            question=f"Who warned {child.label} about keeping the dime all alone?",
            answer=f"{companion.label} warned {child.label} that hiding the dime and sharing nothing would make the heart heavy.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn by the end?",
            answer=f"{child.label} learned that sharing can make a small treasure feel brighter and that kindness matters more than keeping everything.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dime?",
            answer="A dime is a small coin. In the United States, it is worth ten cents.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, enjoy, or have part of something with you.",
        ),
        QAItem(
            question="Why can being selfish cause trouble?",
            answer="Being selfish can hurt friendships because other people may feel left out or ignored.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_has_coin(C) :- owns(C, dime).
greedy(C) :- wants_keep(C, dime).
warning_needed(C) :- greedy(C), companion_warns(C).
regret(C) :- greedy(C), not shares(C).
lesson_learned(C) :- shares(C), warning_needed(C).
good_story(S) :- child_in(S, C), has_dime(S), lesson_learned(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = set((k,) for k in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a dime, sharing, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    companion = args.companion or rng.choice(list(COMPANIONS))
    object_ = args.object_ or "dime"
    if object_ != "dime":
        raise StoryError("This world only models a dime as the small treasure.")
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(
        setting=setting,
        child_name=name,
        child_type=child_type,
        child_trait=trait,
        companion=companion,
        object=object_,
    )


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
    StoryParams(setting="forest_path", child_name="Lina", child_type="girl", child_trait="curious", companion="rabbit", object="dime"),
    StoryParams(setting="cottage_gate", child_name="Milo", child_type="boy", child_trait="stubborn", companion="sparrow", object="dime"),
    StoryParams(setting="market_square", child_name="Nora", child_type="girl", child_trait="careful", companion="mole", object="dime"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible story settings:\n")
        for s in sorted(SETTINGS):
            print(f"  {s}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting} with {p.companion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
