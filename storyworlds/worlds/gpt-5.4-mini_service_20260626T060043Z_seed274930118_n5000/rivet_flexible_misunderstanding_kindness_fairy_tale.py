#!/usr/bin/env python3
"""
A standalone story world for a fairy-tale misunderstanding about kindness,
where a flexible helper and a stubborn rivet are part of the problem and the
solution.

The premise is simple: in a little fairy village, a gate hinge is held by a
tiny rivet, and the hero wants to help with a flexible willow bridge. A
misunderstanding makes the villagers worry the bridge will snap or the gate
will fall, but kindness, a careful explanation, and a gentle repair turn worry
into a happy ending.
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
    worn_by: Optional[str] = None
    protective: bool = False
    flexible: bool = False
    brittle: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy", "witch", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "boy-elf", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class StoryParams:
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    helper: Entity
    rivet: Entity
    bridge: Entity
    gate: Entity
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(
            hero=copy.deepcopy(self.hero),
            helper=copy.deepcopy(self.helper),
            rivet=copy.deepcopy(self.rivet),
            bridge=copy.deepcopy(self.bridge),
            gate=copy.deepcopy(self.gate),
        )
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if world.hero.memes.get("worry", 0) < THRESHOLD:
        return out
    if world.helper.flexible and world.bridge.meters.get("bend", 0) >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.gate.memes["fear"] = world.gate.memes.get("fear", 0) + 1
            out.append("The little village mistook the helper's flexibility for danger.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if world.helper.memes.get("kindness", 0) < THRESHOLD:
        return out
    if world.hero.memes.get("fear", 0) >= THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.hero.memes["calm"] = world.hero.memes.get("calm", 0) + 1
            world.hero.memes["fear"] = 0
            out.append("Kindness made the frightened heart feel safe enough to listen.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.rivet.meters.get("tightness", 0) < THRESHOLD:
        return out
    if world.bridge.meters.get("bend", 0) >= THRESHOLD:
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.gate.meters["stability"] = world.gate.meters.get("stability", 0) + 1
            world.bridge.meters["bend"] = max(0.0, world.bridge.meters.get("bend", 0) - 1)
            out.append("The rivet held fast, and the careful repair made the path steady again.")
    return out


RULES = [_r_misunderstanding, _r_kindness, _r_repair]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    sim.hero.memes["worry"] = sim.hero.memes.get("worry", 0) + 1
    sim.bridge.meters["bend"] = sim.bridge.meters.get("bend", 0) + 1
    propagate(sim, narrate=False)
    return {
        "misunderstanding": sim.gate.memes.get("fear", 0) > 0,
        "calmed": sim.hero.memes.get("calm", 0) > 0,
        "stable": sim.gate.meters.get("stability", 0) > 0,
    }


def tell(name: str, helper: str) -> World:
    hero = Entity(id=name, kind="character", type="girl", label=name, traits=["little", "brave"])
    helper_ent = Entity(
        id=helper,
        kind="character",
        type="fairy",
        label="the helper",
        traits=["kind", "patient"],
    )
    rivet = Entity(
        id="rivet",
        type="thing",
        label="rivet",
        phrase="a tiny silver rivet",
        brittle=False,
        protective=False,
    )
    bridge = Entity(
        id="bridge",
        type="thing",
        label="bridge",
        phrase="a flexible willow bridge",
        flexible=True,
        meters={"bend": 1.0},
    )
    gate = Entity(
        id="gate",
        type="thing",
        label="gate",
        phrase="the garden gate",
        meters={"stability": 0.0},
        memes={"fear": 0.0},
    )
    world = World(hero=hero, helper=helper_ent, rivet=rivet, bridge=bridge, gate=gate)

    world.say(
        f"Once upon a time, {hero.id} lived beside a lantern-lit garden where a "
        f"{bridge.phrase} led to {gate.phrase}."
    )
    world.say(
        f"Near the gate sat {rivet.phrase}, and {helper_ent.id} was known for "
        f"being flexible enough to help in any weather."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to cross the bridge and check on the roses, but the "
        f"bend in the bridge made {hero.pronoun('possessive')} heart flutter with worry."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"From the path, the villagers saw the flexible bridge and feared the "
        f"tiny rivet might fail."
    )
    propagate(world)

    world.para()
    world.say(
        f"Then {helper_ent.id} walked forward with a soft smile and showed the "
        f"shimmering rivet close up."
    )
    helper_ent.memes["kindness"] = helper_ent.memes.get("kindness", 0) + 1
    world.say(
        f'"It is not danger," {helper_ent.id} said gently. "It is care. A flexible '
        f"bridge can bend, and a good rivet can hold."' 
    )
    propagate(world)

    world.para()
    world.say(
        f"{hero.id} listened, and the misunderstanding grew small as a dew drop."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    helper_ent.memes["kindness"] += 1
    predict = predict_conflict(world)
    if predict["misunderstanding"]:
        world.say(
            f"To prove it, {helper_ent.id} pressed the rivet carefully into place "
            f"and steadied the bridge with both hands."
        )
    rivet.meters["tightness"] = 1.0
    propagate(world)

    world.para()
    if world.hero.memes.get("calm", 0) > 0:
        world.say(
            f"{hero.id} smiled, crossed the flexible bridge, and found the roses "
            f"sleeping safely behind the gate."
        )
        world.say(
            f"By sunset, the rivet was firm, the bridge was steady, and kindness "
            f"had turned fear into trust."
        )
    else:
        world.say(
            f"{hero.id} crossed anyway, while the village learned that a kind word "
            f"can be stronger than a frightened guess."
        )

    world.facts.update(
        hero=hero,
        helper=helper_ent,
        rivet=rivet,
        bridge=bridge,
        gate=gate,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fairy tale about a flexible bridge, a tiny rivet, and a misunderstanding that kindness fixes.',
        f"Tell a gentle story where {f['hero'].id} mistakes a flexible bridge for danger, but a kind helper explains the truth.",
        "Write a child-friendly fairy tale ending with a safe crossing and a steady, shining rivet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bridge = f["bridge"]
    rivet = f["rivet"]
    gate = f["gate"]
    return [
        QAItem(
            question=f"Who worried first when {hero.id} looked at the flexible bridge?",
            answer=f"{hero.id} worried first, because the bend in the bridge made {hero.pronoun('possessive')} heart flutter.",
        ),
        QAItem(
            question=f"What did the villagers misunderstand about the bridge near the gate?",
            answer=f"They misunderstood the flexible bridge and feared the tiny rivet might fail, even though it was only a sign that the bridge could bend safely.",
        ),
        QAItem(
            question=f"How did {helper.id} help fix the misunderstanding?",
            answer=f"{helper.id} used kindness, explained that the bridge was meant to be flexible, and showed that the rivet could hold it steady.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} felt calm, the rivet was firm, and the bridge led safely past the garden gate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rivet?",
            answer="A rivet is a small fastener that helps hold pieces of metal or wood together so they do not come apart.",
        ),
        QAItem(
            question="What does flexible mean?",
            answer="Flexible means something can bend a little without breaking.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.rivet, world.bridge, world.gate]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.flexible:
            bits.append("flexible=True")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n,) in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale world of misunderstanding and kindness.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", default=None)
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
    name = args.name or rng.choice(["Elin", "Mira", "Lina", "Nora", "Tessa"])
    helper = args.helper or rng.choice(["Aster", "Brindle", "Faye", "Lark"])
    return StoryParams(name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.helper)
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


def asp_facts() -> str:
    return "\n".join(
        [
            'hero(elin).',
            'helper(aster).',
            'thing(rivet).',
            'thing(bridge).',
            'thing(gate).',
            'flexible(bridge).',
            'kindness(aster).',
            'word(misunderstanding).',
            'word(kindness).',
        ]
    )


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- flexible(bridge), kindness(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import as required by contract.
    from storyworlds import asp  # type: ignore

    model = asp.one_model(asp_program("#show compatible/1."))
    atoms = asp.atoms(model, "compatible")
    if ("story",) in atoms:
        print("OK: ASP twin accepts the fairy tale premise.")
        return 0
    print("MISMATCH: ASP twin did not accept the fairy tale premise.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show compatible/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name=n, helper=h)) for n, h in [
            ("Elin", "Aster"),
            ("Mira", "Faye"),
            ("Lina", "Lark"),
        ]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
