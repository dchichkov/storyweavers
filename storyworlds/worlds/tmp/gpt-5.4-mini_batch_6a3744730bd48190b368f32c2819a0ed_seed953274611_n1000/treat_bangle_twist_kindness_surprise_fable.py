#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/treat_bangle_twist_kindness_surprise_fable.py
=============================================================================

A small fable-style storyworld about a shared treat, a lost bangle, a twist,
kindness, and a surprise ending.

Premise:
- A child wants to keep a sweet treat.
- A bangle goes missing.
- A twist reveals that kindness matters more than winning.
- A surprise reward seals the lesson.

The world is built from typed entities with meters and memes, a small causal
engine, a Python reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "mother", "woman", "goat"}
        male = {"boy", "father", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class CharacterSpec:
    id: str
    type: str
    role: str
    trait: str
    mood: str
    age: int = 0
    label: str = ""


@dataclass
class TreatSpec:
    id: str
    label: str
    sweetness: int
    shareable: bool
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class BangleSpec:
    id: str
    label: str
    shine: str
    wearer: str
    lost: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistSpec:
    id: str
    reveal: str
    turn: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessSpec:
    id: str
    action: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseSpec:
    id: str
    gift: str
    ending: str
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
        clone.entities = {k: v for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    bangle = world.entities.get("bangle")
    if not child or not bangle:
        return out
    if child.memes["taking"] >= THRESHOLD and bangle.meters["kept"] < THRESHOLD:
        sig = ("lost",)
        if sig not in world.fired:
            world.fired.add(sig)
            bangle.meters["lost"] += 1
            out.append("__lost__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    bangle = world.entities.get("bangle")
    treat = world.entities.get("treat")
    if not helper or not child or not bangle or not treat:
        return out
    if helper.memes["kindness"] >= THRESHOLD and bangle.meters["lost"] >= THRESHOLD:
        sig = ("kind",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["peace"] += 1
            child.memes["shame"] += 0.5
            out.append("__kind__")
    return out


CAUSAL_RULES = [Rule("lost", _r_lost), Rule("kindness", _r_kindness)]


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


def reasonableness_gate(treat: TreatSpec, bangle: BangleSpec, twist: TwistSpec, kindness: KindnessSpec) -> bool:
    return bool(treat.shareable and bangle.lost is False and twist.reveal and kindness.action)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for tid in TREATS:
        for bid in BANGLES:
            for tw in TWISTS:
                for ki in KINDNESSES:
                    if reasonableness_gate(TREATS[tid], BANGLES[bid], TWISTS[tw], KINDNESSES[ki]):
                        combos.append((tid, bid, tw, ki))
    return combos


@dataclass
class StoryParams:
    treat: str
    bangle: str
    twist: str
    kindness: str
    surprise: str
    child_name: str = "Mira"
    helper_name: str = "Sana"
    seed: Optional[int] = None


TREATS = {
    "honey_cake": TreatSpec(id="honey_cake", label="honey cake treat", sweetness=9, shareable=True, fragile=True, tags={"treat"}),
    "apple_slice": TreatSpec(id="apple_slice", label="apple slice treat", sweetness=4, shareable=True, fragile=False, tags={"treat"}),
    "berry_cookie": TreatSpec(id="berry_cookie", label="berry cookie treat", sweetness=7, shareable=True, fragile=False, tags={"treat"}),
}

BANGLES = {
    "gold_bangle": BangleSpec(id="gold_bangle", label="gold bangle", shine="shone like a tiny sun", wearer="child", lost=False, tags={"bangle"}),
    "shell_bangle": BangleSpec(id="shell_bangle", label="shell bangle", shine="glimmered pale and soft", wearer="child", lost=False, tags={"bangle"}),
}

TWISTS = {
    "sister_twist": TwistSpec(id="sister_twist", reveal="the helper had not taken the bangle at all", turn="the bangle had slipped beneath the table", tags={"twist", "surprise"}),
    "wind_twist": TwistSpec(id="wind_twist", reveal="a sudden wind had rolled the bangle away", turn="it had hidden in a pile of leaves", tags={"twist"}),
}

KINDNESSES = {
    "share_treat": KindnessSpec(id="share_treat", action="share the treat without being asked", reward="calmer hearts", tags={"kindness"}),
    "return_bangle": KindnessSpec(id="return_bangle", action="return the bangle gently", reward="a warm smile", tags={"kindness"}),
}

SURPRISES = {
    "basket": SurpriseSpec(id="basket", gift="a basket of plums", ending="the day ended with a table of fruit and laughter", tags={"surprise"}),
    "ribbon": SurpriseSpec(id="ribbon", gift="a ribbon for the bangle", ending="the bangle rested in a ribbon nest beside the cake", tags={"surprise"}),
}

GIRL_NAMES = ["Mira", "Nina", "Lila", "Ivy", "Tara"]
BOY_NAMES = ["Oren", "Milo", "Ezra", "Jude", "Pax"]


def tell(treat: TreatSpec, bangle: BangleSpec, twist: TwistSpec, kindness: KindnessSpec, surprise: SurpriseSpec,
         child_name: str, helper_name: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper"))
    treat_ent = world.add(Entity(id="treat", kind="thing", type="food", label=treat.label))
    bangle_ent = world.add(Entity(id="bangle", kind="thing", type="jewel", label=bangle.label))
    helper.memes["kindness"] = 0.0

    world.say(f"{child.id} found {treat.label} on a bright morning, and {bangle.label} flashed at {her_or_child(child)} wrist.")
    world.say(f"{child.id} wanted to keep the treat all to {child.pronoun('object')}self, because sweet things felt precious.")
    world.say(f"Then a small twist came: {twist.reveal}. {twist.turn.capitalize()}, so the room grew quiet.")

    world.para()
    child.memes["taking"] += 1
    child.meters["worry"] += 1
    bangle_ent.meters["kept"] = 0.0
    propagate(world, narrate=False)
    world.say(f"{child.id} searched under the bench and beside the jars, but the {bangle.label} was gone.")
    world.say(f"{helper.id} did not blame {child.pronoun('object')}; instead, {helper.pronoun()} chose kindness and offered to {kindness.action}.")
    helper.memes["kindness"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"{child.id} looked up, surprised by the gentle answer.")
    world.say(f"Because {helper.id} was kind, the truth came out: the {bangle.label} had simply slipped away, and no one had meant harm.")
    world.say(f"{child.id} then chose to share the {treat.label}, and that made both children feel better at once.")
    child.memes["sharing"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.para()
    world.say(f"As a surprise, the elder in the house brought {surprise.gift}.")
    world.say(f"By the end, {surprise.ending}, and the {bangle.label} gleamed again beside the treat.")
    world.say(f"{child.id} learned that kindness can untie a knot faster than blame.")
    world.facts.update(
        treat=treat, bangle=bangle, twist=twist, kindness=kindness, surprise=surprise,
        child=child, helper=helper, outcome="kind",
    )
    return world


def her_or_child(child: Entity) -> str:
    return "her" if child.type == "girl" else "his"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treat: TreatSpec = f["treat"]
    bangle: BangleSpec = f["bangle"]
    return [
        f'Write a fable for a young child that includes the words "{treat.label}" and "{bangle.label}", and ends with kindness.',
        f"Tell a short story with a twist, kindness, and a surprise, where a child finds a {treat.label} and loses a {bangle.label}.",
        f"Write a gentle fable about a treat, a bangle, and a lesson that being kind matters more than being right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    treat = f["treat"]
    bangle = f["bangle"]
    twist = f["twist"]
    return [
        ("What did the child want at first?",
         f"{child.id} wanted to keep the {treat.label} and hold onto the happy feeling it brought. That wanting made the lost {bangle.label} feel bigger and more serious."),
        ("What was the twist in the story?",
         f"The twist was that {twist.reveal}. That changed the mood, because the loss was not a mean trick at all."),
        ("How did the helper answer the problem?",
         f"{helper.id} answered with kindness and chose to help instead of scold. That gentle choice made it easier for {child.id} to be honest and share."),
        ("What changed by the end?",
         f"At the end, the {bangle.label} was safe again and the children were calmer. The {treat.label} was shared, so the feeling in the room turned warm instead of tense."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bangle?",
         "A bangle is a round bracelet worn on the wrist. People like them because they can shine and jinggle softly."),
        ("What does kindness mean?",
         "Kindness means choosing gentle actions that help someone else feel safe. A kind choice can turn a hard moment into a better one."),
        ("What is a twist in a story?",
         "A twist is a surprise turn that changes what the reader expected. It can reveal new facts and make the ending feel fresher."),
        ("What is a fable?",
         "A fable is a short story that teaches a lesson. It often uses simple events to show how to be wise and good."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"  {e.id:8} meters={meters} memes={memes} role={e.role}")
    parts.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(parts)


CURATED = [
    StoryParams(treat="honey_cake", bangle="gold_bangle", twist="sister_twist", kindness="share_treat", surprise="basket", child_name="Mira", helper_name="Sana"),
    StoryParams(treat="berry_cookie", bangle="shell_bangle", twist="wind_twist", kindness="return_bangle", surprise="ribbon", child_name="Oren", helper_name="Nina"),
]


def explain_rejection() -> str:
    return "(No story: the requested combination does not form a reasonable fable.)"


def valid_outcome(params: StoryParams) -> str:
    return "kind"


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for bid in BANGLES:
        lines.append(asp.fact("bangle", bid))
    for tw in TWISTS:
        lines.append(asp.fact("twist", tw))
    for ki in KINDNESSES:
        lines.append(asp.fact("kindness", ki))
    for su in SURPRISES:
        lines.append(asp.fact("surprise", su))
    lines.append(asp.fact("shareable", "honey_cake"))
    lines.append(asp.fact("shareable", "apple_slice"))
    lines.append(asp.fact("shareable", "berry_cookie"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, B, Tw, K) :- treat(T), bangle(B), twist(Tw), kindness(K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"FAIL: generate smoke test crashed: {exc}")
    if ok:
        print(f"OK: ASP parity matches ({len(py)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld about treat, bangle, twist, kindness, and surprise.")
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--bangle", choices=BANGLES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.treat and args.bangle and args.twist and args.kindness and args.surprise:
        pass
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    tid, bid, tw, ki = rng.choice(combos)
    su = args.surprise or rng.choice(sorted(SURPRISES))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    if args.treat:
        tid = args.treat
    if args.bangle:
        bid = args.bangle
    if args.twist:
        tw = args.twist
    if args.kindness:
        ki = args.kindness
    if args.surprise:
        su = args.surprise
    return StoryParams(treat=tid, bangle=bid, twist=tw, kindness=ki, surprise=su, child_name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS or params.bangle not in BANGLES or params.twist not in TWISTS or params.kindness not in KINDNESSES or params.surprise not in SURPRISES:
        raise StoryError("invalid story parameters")
    world = tell(TREATS[params.treat], BANGLES[params.bangle], TWISTS[params.twist], KINDNESSES[params.kindness], SURPRISES[params.surprise], params.child_name, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
