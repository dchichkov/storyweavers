#!/usr/bin/env python3
"""
A tiny fable-like story world about a cautious small town, a boastful boozer,
an ounce of honesty, and a chitlin who notices the warning signs.

The domain is deliberately small and classical:
- One setting: a village lane by an old pantry garden
- One tension: a thirsty boozer ignores a foreshadowed warning
- One turn: a careful chitlin prepares an ounce of safe help
- One resolution: the bozer learns to slow down, and the village stays calm

The world model tracks both physical meters and emotional memes, and the story
is generated from simulated state rather than by swapping names in a template.
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
    companion: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"hare", "chitlin", "mouse", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boar", "fox", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the village lane"
    detail: str = "an old stone sign beside the pantry garden"


@dataclass
class Boast:
    id: str
    verb: str
    warning: str
    risk: str
    rush: str
    tag: str
    keyword: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    risk_area: str


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "clear"

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


def _do_booze(world: World, actor: Entity, boast: Boast, narrate: bool = True) -> None:
    actor.meters["buzz"] = actor.meters.get("buzz", 0.0) + 1.0
    actor.meters["stumble"] = actor.meters.get("stumble", 0.0) + 1.0
    actor.memes["restless"] = actor.memes.get("restless", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} took a long sip and wobbled a little more.")


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    boozer = world.get("Boozer")
    chitlin = world.get("Chitlin")
    if boozer.meters.get("buzz", 0.0) >= THRESHOLD and ("warn", "Boozer") not in world.fired:
        world.fired.add(("warn", "Boozer"))
        chitlin.memes["worry"] = chitlin.memes.get("worry", 0.0) + 1.0
        out.append("The old sign seemed to lean closer, as if it knew trouble was coming.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    boozer = world.get("Boozer")
    prize = world.get("Ounce")
    if boozer.meters.get("stumble", 0.0) < THRESHOLD:
        return out
    if ("spill", "Ounce") in world.fired:
        return out
    world.fired.add(("spill", "Ounce"))
    prize.meters["spilled"] = prize.meters.get("spilled", 0.0) + 1.0
    prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1.0
    boozer.memes["shame"] = boozer.memes.get("shame", 0.0) + 1.0
    out.append("A sudden stumble tipped the little cup, and the ounce splashed onto the stones.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    chitlin = world.get("Chitlin")
    prize = world.get("Ounce")
    if chitlin.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if prize.meters.get("spilled", 0.0) >= THRESHOLD and ("help", "Ounce") not in world.fired:
        world.fired.add(("help", "Ounce"))
        aid = world.get("Aid")
        prize.meters["clean"] = prize.meters.get("clean", 0.0) + 1.0
        chitlin.memes["hope"] = chitlin.memes.get("hope", 0.0) + 1.0
        out.append("Chitlin hurried in with a small towel and a steady hand.")
    return out


CAUSAL_RULES = [_r_warning, _r_spill, _r_help]


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


def foreshadow_line(boast: Boast) -> str:
    return f"At the edge of the lane, a sign creaked: {boast.warning}"


def setup_line(world: World, bozer: Entity, chitlin: Entity, prize: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived a boastful boozer named {bozer.id} "
        f"and a small careful chitlin named {chitlin.id}."
    )
    world.say(
        f"{bozer.id} liked to brag, but {chitlin.id} liked to notice what might happen next."
    )
    world.say(
        f"On the windowsill sat {prize.phrase}, neat and shiny, while {world.setting.detail} waited nearby."
    )


def desire_line(world: World, bozer: Entity, boast: Boast) -> None:
    bozer.memes["want"] = bozer.memes.get("want", 0.0) + 1.0
    world.say(
        f"{bozer.id} wanted to {boast.verb} right away, even though {boast.warning.lower()}."
    )


def suspense_line(world: World, bozer: Entity, boast: Boast) -> None:
    world.say(
        f"{bozer.id} took one more step toward the lane, and {boast.risk} felt ready to happen."
    )


def turn_line(world: World, chitlin: Entity, aid: Aid) -> None:
    world.say(
        f"Then {chitlin.id} remembered an ounce of kindness and brought {aid.label}."
    )
    world.say(
        f'"{aid.prep}," {chitlin.id} said, careful and calm.'
    )


def resolve_line(world: World, bozer: Entity, chitlin: Entity, prize: Prize, aid: Aid) -> None:
    bozer.memes["calm"] = bozer.memes.get("calm", 0.0) + 1.0
    bozer.memes["pride"] = max(0.0, bozer.memes.get("pride", 0.0) - 1.0)
    world.say(
        f"{bozer.id} stopped, looked at the spilled {prize.label}, and nodded."
    )
    world.say(
        f'"That was a near miss," {bozer.id} admitted. "Next time I will slow down first."'
    )
    world.say(
        f"So {chitlin.id} used {aid.label}, and soon the lane was tidy again."
    )
    world.say(
        f"By the end, the sign stood straight, the {prize.label} was safe, and {bozer.id} had learned that a small warning can save a big mess."
    )


def tell() -> World:
    world = World(Setting())
    bozer = world.add(Entity(id="Boozer", kind="character", type="boar", traits=["boastful", "stubborn"]))
    chitlin = world.add(Entity(id="Chitlin", kind="character", type="chitlin", traits=["careful", "small"]))
    prize = world.add(Entity(id="Ounce", kind="thing", type="cup", label="ounce", phrase="a tiny silver ounce cup", owner=bozer.id))
    aid = world.add(Entity(id="Aid", kind="thing", type="cloth", label="a clean little towel", phrase="a clean little towel"))

    boast = BOASTS["lane"]
    setup_line(world, bozer, chitlin, prize)
    world.para()
    world.say(foreshadow_line(boast))
    desire_line(world, bozer, boast)
    suspense_line(world, bozer, boast)
    propagate(world, narrate=True)
    world.para()
    turn_line(world, chitlin, AID)
    propagate(world, narrate=True)
    resolve_line(world, bozer, chitlin, prize, aid)

    world.facts.update(bozer=bozer, chitlin=chitlin, prize=prize, aid=aid, boast=boast)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable for a young child that uses the words "boozer", "ounce", and "chitlin".',
        'Tell a suspenseful little story where a boozer ignores a warning, and a chitlin helps with an ounce of kindness.',
        'Write a fable with foreshadowing, a near mishap, and a calm ending image on a village lane.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bozer: Entity = f["bozer"]
    chitlin: Entity = f["chitlin"]
    prize: Entity = f["prize"]
    boast: Boast = f["boast"]
    qa = [
        QAItem(
            question="Who was the story mostly about?",
            answer=f"It was about {bozer.id}, a boastful boozer, and {chitlin.id}, a small chitlin who noticed danger early.",
        ),
        QAItem(
            question="What warning was shown before the trouble?",
            answer=f"The warning was {boast.warning.lower()}. That was the foreshadowing that trouble might come if {bozer.id} kept going.",
        ),
        QAItem(
            question="What happened to the ounce before the story ended?",
            answer=f"The ounce spilled onto the stones when {bozer.id} stumbled, and then {chitlin.id} helped clean it up.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {bozer.id} slowing down, {chitlin.id} helping, and the lane becoming tidy and calm again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a little clue early on that something important or surprising may happen later.",
        ),
        QAItem(
            question="What does suspense do in a story?",
            answer="Suspense makes you wonder what will happen next, so you keep paying attention and feel a little worried or excited.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals or small characters to teach a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None


BOASTS = {
    "lane": Boast(
        id="lane",
        verb="dash down the lane",
        warning="The stones are slick after supper rain",
        risk="a spill",
        rush="dash",
        tag="suspense",
        keyword="foreshadowing",
    )
}

AID = Aid(
    id="aid",
    label="a clean little towel",
    prep="Hold still while I wipe the stones",
    effect="clean",
)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("boast", "lane"),
        asp.fact("warning", "lane", "The stones are slick after supper rain"),
        asp.fact("risk", "lane", "spill"),
        asp.fact("setting", "village_lane"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% A warning foreshadows trouble when the bozer keeps going.
foreshadows(lane) :- warning(lane,_), risk(lane,spill).

% Suspense exists when the bozer is at risk of a spill and there is a warning.
suspense(lane) :- foreshadows(lane).

#show foreshadows/1.
#show suspense/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show foreshadows/1. #show suspense/1."))
    foreshadows = set(asp.atoms(model, "foreshadows"))
    suspense = set(asp.atoms(model, "suspense"))
    py = {("lane",)}
    if foreshadows == py and suspense == py:
        print("OK: ASP and Python reasoning agree.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("foreshadows:", foreshadows)
    print("suspense:", suspense)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world with foreshadowing and suspense.")
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
    return StoryParams(seed=rng.randrange(2**31))


def generate(params: StoryParams) -> StorySample:
    world = tell()
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
        print(asp_program("#show foreshadows/1. #show suspense/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show foreshadows/1. #show suspense/1."))
        print("ASP facts:")
        print(asp_program("#show foreshadows/1. #show suspense/1."))
        print("Model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(seed=base_seed))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
