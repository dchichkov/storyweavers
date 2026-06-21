#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/harden_textured_shod_misunderstanding_fairy_tale.py
===================================================================================

A tiny fairy-tale story world about a mistaken warning, a textured path, and a
small repair that lets the day end well. The seed words are woven in as living
story material: something can harden, a path can be textured, and someone can be
shod. The core feature is misunderstanding: a child or helper misreads a clue,
creates tension, and then the world resolves through a careful reveal.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py only inside ASP helpers
- typed entities with physical meters and emotional memes
- state-driven prose, Q&A, ASP twin, verify mode, JSON output, trace, and QA
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "prince", "knight", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Path:
    id: str
    label: str
    texture: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


@dataclass
class Shoe:
    id: str
    label: str
    description: str
    shod: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.path: Optional[Path] = None
        self.shoe: Optional[Shoe] = None
        self.remedy: Optional[Remedy] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.path = copy.deepcopy(self.path)
        c.shoe = copy.deepcopy(self.shoe)
        c.remedy = self.remedy
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["misunderstanding"] < THRESHOLD:
            continue
        sig = ("misunderstanding", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__warn__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["understanding"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, actor_id: str) -> dict:
    sim = world.copy()
    _make_mistake(sim, sim.get(actor_id), narrate=False)
    return {
        "worry": sim.get(actor_id).memes["worry"],
        "path_blocked": bool(sim.path and sim.path.meters["blocked"] >= THRESHOLD),
    }


def _make_mistake(world: World, actor: Entity, narrate: bool = True) -> None:
    if world.path:
        world.path.meters["blocked"] += 1
    actor.memes["misunderstanding"] += 1
    propagate(world, narrate=narrate)


def scene(world: World, hero: Entity, helper: Entity, path: Path, shoe: Shoe) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Once in a fair little kingdom, {hero.id} and {helper.id} walked beside "
        f"{path.label}, where the stones looked {path.texture} and old as a song."
    )
    world.say(
        f"{helper.id} was {shoe.description}, and the moon made {path.label} seem "
        f"like a ribbon laid for dancing."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, path: Path) -> None:
    hero.memes["misunderstanding"] += 1
    world.say(
        f"But {hero.id} frowned. {hero.id} thought the {path.texture} stones meant "
        f"the path was hardening into a trap."
    )
    world.say(
        f'"We must turn back," {hero.id} whispered, "or the road will harden under us."'
    )


def gentle_correction(world: World, helper: Entity, hero: Entity, path: Path, shoe: Shoe) -> None:
    helper.memes["understanding"] += 1
    world.say(
        f'{helper.id} smiled softly. "No, dear one. The stones are only {path.texture}; '
        f"they are made to be felt, not feared."
    )
    world.say(
        f'"And I am {shoe.description}, so my feet are safe on them."'
    )


def reveal(world: World, helper: Entity, hero: Entity, path: Path) -> None:
    hero.memes["understanding"] += 1
    hero.memes["worry"] = 0
    world.say(
        f"Then {helper.id} brushed the dust from one stone, and {hero.id} saw the "
        f"little marks carved into it like leaves and stars."
    )
    world.say(
        f"{hero.id} laughed, because the path was not a trap at all. It was a "
        f"storybook road, made {path.texture} by time."
    )


def repair(world: World, helper: Entity, hero: Entity, path: Path, remedy: Remedy) -> None:
    if path.meters["blocked"] >= THRESHOLD:
        world.say(
            f"{helper.id} took the {remedy.text}, and with a quick careful touch "
            f"the blocked place opened again."
        )
    else:
        world.say(
            f"{helper.id} did not need the {remedy.text}; the road was already open."
        )


def ending(world: World, hero: Entity, helper: Entity, path: Path) -> None:
    world.say(
        f"At last they crossed together, {hero.id} cheerful and {helper.id} calm, "
        f"while the {path.texture} stones shone silver in the fairy-tale light."
    )
    world.say(
        f"And from then on, whenever {hero.id} saw a rough path, {hero.id} remembered "
        f"that not every hard thing is a harm."
    )


def tell(hero: Entity, helper: Entity, path: Path, shoe: Shoe, remedy: Remedy) -> World:
    world = World()
    world.path = path
    world.shoe = shoe
    world.remedy = remedy
    world.add(hero)
    world.add(helper)

    scene(world, hero, helper, path, shoe)
    world.para()
    misunderstanding(world, hero, helper, path)
    gentle_correction(world, helper, hero, path, shoe)

    predicted = predict_outcome(world, hero.id)
    world.facts["predicted"] = predicted

    world.para()
    _make_mistake(world, hero)
    if world.path and world.path.meters["blocked"] >= THRESHOLD:
        world.say(f"The path did seem blocked for a breath, and the two travelers paused.")
    repair(world, helper, hero, path, remedy)
    reveal(world, helper, hero, path)
    ending(world, hero, helper, path)

    world.facts.update(hero=hero, helper=helper, path=path, shoe=shoe, remedy=remedy)
    world.facts["outcome"] = "repaired" if (world.path and world.path.meters["blocked"] >= THRESHOLD) else "clear"
    return world


PATHS = {
    "moss": Path(id="moss", label="the mossy lane", texture="textured with moss", tags={"textured"}),
    "pebbles": Path(id="pebbles", label="the pebble road", texture="textured with pebbles", tags={"textured"}),
    "runes": Path(id="runes", label="the rune path", texture="textured with old carvings", tags={"textured"}),
}

SHOES = {
    "shod_boots": Shoe(id="shod_boots", label="shod boots", description="shod in sturdy boots", tags={"shod"}),
    "shod_slippers": Shoe(id="shod_slippers", label="shod slippers", description="shod in soft slippers", tags={"shod"}),
}

REMEDIES = {
    "brush": Remedy(
        id="brush",
        sense=3,
        power=3,
        text="little brush",
        fail="tugged at the blocked stone but could not free it",
        qa_text="used a little brush to clear the stones",
        tags={"brush"},
    ),
    "water": Remedy(
        id="water",
        sense=2,
        power=2,
        text="cup of water",
        fail="poured water on the stones, but the jam stayed stuck",
        qa_text="used a cup of water to loosen the jam",
        tags={"water"},
    ),
}

HEROES = ["Ari", "Mina", "Nell", "Pip", "Rowan", "Sera"]
HELPERS = ["the old queen", "the kindly knight", "the lantern bearer", "the fairy guide"]


@dataclass
class StoryParams:
    path: str
    shoe: str
    remedy: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PATHS:
        for s in SHOES:
            for r in REMEDIES:
                combos.append((p, s, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale misunderstanding story world.")
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--shoe", choices=SHOES)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    combos = [c for c in valid_combos()
              if (args.path is None or c[0] == args.path)
              and (args.shoe is None or c[1] == args.shoe)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    p, s, r = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(path=p, shoe=s, remedy=r, hero=hero, helper=helper)


def asp_facts() -> str:
    import asp
    lines = []
    for p in PATHS:
        lines.append(asp.fact("path", p))
        lines.append(asp.fact("textured", p))
    for s in SHOES:
        lines.append(asp.fact("shoe", s))
        lines.append(asp.fact("shod", s))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,R) :- path(P), shoe(S), remedy(R), textured(P), shod(S).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a child that includes the words "harden", "textured", and "shod".',
        f"Tell a gentle misunderstanding story where {f['hero'].id} worries about {f['path'].label}, "
        f"but {f['helper'].id} explains the truth and the day ends safely.",
        f"Write a small kingdom story with a mistaken warning, a wise correction, and a bright ending on {f['path'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    path: Path = f["path"]
    shoe: Shoe = f["shoe"]
    remedy: Remedy = f["remedy"]
    return [
        QAItem(
            question=f"What did {hero.id} misunderstand?",
            answer=(
                f"{hero.id} misunderstood the {path.texture} stones and thought the road was hardening into a trap. "
                f"{helper.id} gently showed that the texture was only the look of the path, not a danger."
            ),
        ),
        QAItem(
            question=f"Why was {helper.id} not afraid of the road?",
            answer=(
                f"{helper.id} was {shoe.description}, so the rough stones were comfortable instead of scary. "
                f"That let {helper.id} see the path as a safe place to walk."
            ),
        ),
        QAItem(
            question="How was the blocked place fixed?",
            answer=(
                f"{helper.id} used the {remedy.text} to clear the jam and open the road again. "
                f"The little repair matched the problem, so the travelers could continue."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does textured mean?",
            answer="Textured means something has a rough or patterned surface that you can feel with your fingers or feet.",
        ),
        QAItem(
            question="What does shod mean?",
            answer="Shod means wearing shoes or boots. A person can be shod in sturdy boots for walking safely.",
        ),
        QAItem(
            question="What does harden mean?",
            answer="Harden means to become firm or less soft. Things can harden when they dry, cool, or settle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    if world.path:
        lines.append(f"  path meters={dict(world.path.meters)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS or params.shoe not in SHOES or params.remedy not in REMEDIES:
        raise StoryError("Invalid params for this world.")
    hero = Entity(id=params.hero, kind="character", type="girl" if params.hero[0] in "AEIOU" else "boy")
    helper = Entity(id=params.helper, kind="character", type="woman", role="helper")
    world = tell(hero, helper, PATHS[params.path], SHOES[params.shoe], REMEDIES[params.remedy])
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
    StoryParams(path="moss", shoe="shod_boots", remedy="brush", hero="Ari", helper="the lantern bearer"),
    StoryParams(path="pebbles", shoe="shod_slippers", remedy="water", hero="Mina", helper="the kindly knight"),
    StoryParams(path="runes", shoe="shod_boots", remedy="brush", hero="Nell", helper="the fairy guide"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
