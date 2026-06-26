#!/usr/bin/env python3
"""
orange_reconciliation_myth.py
==============================

A small mythic storyworld about an orange, a hurt pride, and reconciliation.
The world simulates a simple ceremonial domain where a prized orange can be
shared, split, forgiven, and made whole again through a ritual apology and a
gift of halves.

The premise is mythic rather than realistic: a child or small figure receives a
special orange, someone envies or mishandles it, and the story turns on a
reconciliation that restores both the fruit and the relationship.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    aura: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    value: str
    split_name: str
    seeds: int = 0


@dataclass
class Rite:
    id: str
    title: str
    action: str
    repair: str
    harmony: str
    needs: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.wounding: int = 0

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.wounding = self.wounding
        return clone


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    orange = world.entities.get("orange")
    if not orange or orange.meters.get("split", 0.0) < THRESHOLD:
        return out
    sig = ("break", orange.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    orange.meters["broken"] = 1
    out.append("The orange was no longer one sweet whole.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes.get("hurt", 0.0) < THRESHOLD or ch.memes.get("forgive", 0.0) < THRESHOLD:
            continue
        sig = ("reconcile", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["peace"] = 1
        ch.memes["hurt"] = 0
        out.append("The air softened, and anger left the chest of the one who forgave.")
    return out


CAUSAL_RULES = [_r_break, _r_reconcile]


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


def tell(setting: Setting, rite: Rite, relic: Relic, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="elder", label=helper_name))
    orange = world.add(Entity(id="orange", type="orange", label="orange", phrase=relic.phrase, owner=hero.id))
    rival = world.add(Entity(id="rival", kind="character", type="child", label="the jealous one"))

    hero.memes["love"] = 1
    helper.memes["wisdom"] = 1
    orange.meters["glow"] = 1

    world.say(f"Long ago, in {setting.place}, {hero.id} guarded {hero.pronoun('possessive')} {orange.label}, a {relic.phrase}.")
    world.say(f"The place itself had a {setting.aura} aura, and everyone knew the orange was for a sacred sharing.")
    world.para()
    world.say(f"One day, {rival.label} reached for the fruit while {hero.id} was away, and the moment turned sharp.")
    rival.memes["envy"] = 1
    hero.memes["hurt"] = 1
    world.say(f"{hero.id} returned and saw the orange touched and split, and {hero.pronoun()} felt the sting of insult.")
    orange.meters["split"] = 1
    world.wounding = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {helper.id} came like a patient moon and spoke the old law of {rite.title}.")
    world.say(f'"{rite.action}," {helper.id} said. "{rite.repair}."')
    hero.memes["forgive"] = 1
    rival.memes["shame"] = 1
    rival.memes["apology"] = 1
    orange.meters["offered"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.id} gave one half to the rival and kept one half for the shrine, and that was the way the hurt was mended."
    )
    world.say(
        f"{hero.id} and {rival.label} ate the sweet pieces together, and the orange's {relic.value} returned as harmony."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        rival=rival,
        orange=orange,
        setting=setting,
        rite=rite,
        relic=relic,
        reconciled=hero.memes.get("peace", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "grove": Setting(place="the moonlit grove", aura="silver", affords={"sharing"}),
    "temple": Setting(place="the old temple steps", aura="still", affords={"sharing"}),
    "harbor": Setting(place="the harbor wall", aura="salt", affords={"sharing"}),
}

RELICS = {
    "orange": Relic(
        label="orange",
        phrase="a bright orange with a sunlike skin",
        type="fruit",
        value="golden sweetness",
        split_name="halves",
        seeds=8,
    ),
    "citrine": Relic(
        label="orange",
        phrase="an orange orb that glimmered like a tiny dawn",
        type="fruit",
        value="clear sweetness",
        split_name="halves",
        seeds=9,
    ),
}

RITES = {
    "reconciliation": Rite(
        id="reconciliation",
        title="Reconciliation",
        action="Let the hurt be named so it can leave",
        repair="We shall split the orange, speak kindly, and share the sweetness fairly",
        harmony="reconciliation",
        needs={"orange"},
    )
}

HEROES = ["Ari", "Mina", "Taro", "Lina", "Sora", "Niko"]
HELPERS = ["Grandmother", "Old Sage", "River Priest", "Lantern Keeper"]


@dataclass
class StoryParams:
    place: str
    relic: str
    rite: str
    hero: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about an orange and the power of {f["rite"].title.lower()}.',
        f"Tell a gentle legend where {f['hero'].id} loses peace over a bright orange, then finds reconciliation with {f['helper'].id}.",
        f'Write a mythic story set at {f["setting"].place} that ends with an orange shared in forgiveness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    rival = f["rival"]
    orange = f["orange"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"What special fruit did {hero.id} guard in {setting.place}?",
            answer=f"{hero.id} guarded an orange, a {orange.phrase}. It was precious because it was meant to be shared as part of an old myth.",
        ),
        QAItem(
            question=f"Who helped {hero.id} after the orange was split?",
            answer=f"{helper.id} came to calm the trouble and taught the old way of reconciliation. {helper.id}'s words helped the anger begin to fade.",
        ),
        QAItem(
            question=f"What happened after {rival.label} reached for the orange?",
            answer=f"{hero.id} felt hurt, the orange was split, and then the story turned toward reconciliation. In the end, the fruit was shared instead of fought over.",
        ),
    ]
    if f["reconciled"]:
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.id} and {rival.label}?",
                answer=f"They shared the orange as halves and ate together. That ending proved the hurt had been healed by reconciliation.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orange?",
            answer="An orange is a round fruit with a peel that you can split into sweet segments inside.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a quarrel, so people can trust each other and share kindly.",
        ),
        QAItem(
            question="Why do people share fruit in stories?",
            answer="People share fruit in stories to show generosity, fairness, and a warm ending after conflict.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="grove", relic="orange", rite="reconciliation", hero="Ari", helper="Old Sage"),
    StoryParams(place="temple", relic="citrine", rite="reconciliation", hero="Mina", helper="Grandmother"),
    StoryParams(place="harbor", relic="orange", rite="reconciliation", hero="Taro", helper="Lantern Keeper"),
]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("aura", sid, setting.aura))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("fruit", rid))
        lines.append(asp.fact("value", rid, relic.value))
        lines.append(asp.fact("split_name", rid, relic.split_name))
    for ri, rite in RITES.items():
        lines.append(asp.fact("rite", ri))
        lines.append(asp.fact("needs", ri, "orange"))
    return "\n".join(lines)


ASP_RULES = r"""
risky(orange).
reconciles(R) :- rite(R), needs(R, orange).
valid_story(S, R) :- setting(S), reconciles(R), affords(S, sharing).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple[str, str]]:
    out = []
    for sid in SETTINGS:
        for rid in RITES:
            if "sharing" in SETTINGS[sid].affords and "orange" in RELICS and RITES[rid].id == "reconciliation":
                out.append((sid, rid))
    return out


def asp_verify() -> int:
    import asp

    a = set(asp_valid_stories())
    b = set(valid_stories())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic orange reconciliation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    rite = args.rite or "reconciliation"
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    if rite != "reconciliation":
        raise StoryError("Only reconciliation is available in this mythic world.")
    return StoryParams(place=place, relic=relic, rite=rite, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITES[params.rite], RELICS[params.relic], params.hero, params.helper)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid mythic story settings:")
        for setting, rite in stories:
            print(f"  {setting:8} {rite}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
