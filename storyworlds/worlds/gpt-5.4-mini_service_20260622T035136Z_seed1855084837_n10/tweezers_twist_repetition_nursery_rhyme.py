#!/usr/bin/env python3
"""
storyworlds/worlds/tweezers_twist_repetition_nursery_rhyme.py
==============================================================

A tiny nursery-rhyme storyworld about a child, a tangle, a gentle twist, and
a repeated tug that only tweezers can solve. The domain stays small and
state-driven: a little helper notices a snag, tries twice, learns a better
twist, and ends with the toy or ribbon neat again.

The story style aims for a rhythmic, child-facing cadence with repetition and
one small twist in the middle.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
for parent in [_HERE] + list(_HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"stuck": 0.0, "tangle": 0.0, "glee": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "hope": 0.0, "joy": 0.0})

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
        return self.label or self.type


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    place: str
    item: str
    snag: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    detail: str
    can_hold_twist: bool = True


@dataclass(frozen=True)
class ItemCfg:
    id: str
    label: str
    phrase: str
    material: str
    wear: str
    snag_kind: str


@dataclass(frozen=True)
class TwistTool:
    id: str
    label: str
    phrase: str
    action: str
    finish: str
    helps: str


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", detail="A soft rug lay near the little chair."),
    "window": Place(id="window", label="the window nook", detail="The window nook shone with morning light."),
    "playroom": Place(id="playroom", label="the playroom", detail="The playroom held blocks, books, and a tiny basket."),
}

ITEMS = {
    "ribbon": ItemCfg(id="ribbon", label="ribbon", phrase="a bright ribbon", material="silk", wear="twisted", snag_kind="loop"),
    "teddy": ItemCfg(id="teddy", label="teddy", phrase="a fuzzy teddy bear", material="cloth", wear="snagged", snag_kind="thread"),
    "doll_hair": ItemCfg(id="doll_hair", label="doll hair", phrase="a doll with yarn hair", material="yarn", wear="tangled", snag_kind="knot"),
}

SNAGS = {
    "loop": "a loop was wrapped too tight",
    "thread": "a loose thread had caught on a button",
    "knot": "a knot had tied the strands in a knot",
}

TWISTS = {
    "tweezers": TwistTool(
        id="tweezers",
        label="tweezers",
        phrase="the tweezers",
        action="pinched the tiny snag again",
        finish="with a careful twist",
        helps="they can grip one tiny bit at a time",
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nina", "Ella", "Ruby", "Maya"]
BOY_NAMES = ["Finn", "Noah", "Ben", "Owen", "Theo", "Max"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.history = list(self.history)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _rise_repetition(world: World) -> list[str]:
    out = []
    child = world.get("child")
    item = world.get("item")
    if child.memes["hope"] < 1:
        return out
    if item.meters["stuck"] <= 0:
        return out
    sig = ("repetition", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("Again and again, the little snag would not budge.")
    return out


def _twist_turn(world: World) -> list[str]:
    out = []
    child = world.get("child")
    item = world.get("item")
    if child.memes["hope"] < 1 or item.meters["stuck"] <= 0:
        return out
    sig = ("twist", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["stuck"] = 0.0
    item.meters["glee"] += 1
    child.memes["joy"] += 1
    out.append("Then came a twist: the snag loosened at last.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_rise_repetition, _twist_turn):
            msgs = fn(world)
            if msgs:
                changed = True
                for m in msgs:
                    world.say(m)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if not place.can_hold_twist:
                continue
            combos.append((place_id, "tweezers", item_id))
    return combos


def explain_rejection(place: Place, item: ItemCfg) -> str:
    return f"(No story: {place.label} and {item.label} do not make a gentle, solvable snag.)"


def introduce(world: World, child: Entity, helper: Entity, place: Place, item: Entity, item_cfg: ItemCfg) -> None:
    child.memes["hope"] += 1
    child.memes["worry"] += 1
    world.say(f"{child.id} was a little {child.type} who liked neat things and tidy things too.")
    world.say(f"{helper.id} was there as well, with a soft smile and a patient heart.")
    world.say(f"At {place.label}, {item.phrase} had trouble: {SNAGS[item_cfg.snag_kind]}.")
    world.say(f"{child.id} wanted it fixed right away, right away, right away.")


def try_once(world: World, child: Entity, tool: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    child.memes["hope"] += 1
    item.meters["stuck"] += 1
    world.say(f"{child.id} tried the {tool.label} once, and once more, and once more.")
    world.say(f"But {item_cfg.label} still stayed {item_cfg.wear}.")


def twist_fix(world: World, child: Entity, helper: Entity, tool: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    child.memes["joy"] += 1
    item.meters["stuck"] = 0.0
    item.meters["glee"] += 1
    world.say(f"Then {helper.id} leaned in and showed how {tool.label} could grip one tiny bit at a time.")
    world.say(f"{child.id} used {tool.phrase}, {tool.action}, {tool.finish}.")
    world.say(f"At last, {item_cfg.phrase} was straight and sweet again.")


def end_image(world: World, child: Entity, helper: Entity, place: Place, item_cfg: ItemCfg) -> None:
    world.say(f"All was calm at {place.label}.")
    world.say(f"{child.id} and {helper.id} laughed softly, and the little thing looked neat and new.")
    world.say(f"What began as a twisty snag ended with a tidy shine.")


def tell(place: Place, item_cfg: ItemCfg, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase, owner=child.id))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="tweezers", phrase="the tweezers"))

    world.facts["place"] = place.id
    world.facts["item"] = item_cfg.id
    world.facts["tool"] = tool.id
    world.facts["snag_kind"] = item_cfg.snag_kind
    world.facts["item_phrase"] = item_cfg.phrase
    world.facts["place_label"] = place.label
    world.facts["helper_name"] = helper_name
    world.facts["child_name"] = child_name

    introduce(world, child, helper, place, item, item_cfg)
    world.para()
    try_once(world, child, tool, item, item_cfg)
    propagate(world)
    world.para()
    twist_fix(world, child, helper, tool, item, item_cfg)
    world.para()
    end_image(world, child, helper, place, item_cfg)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery rhyme story with the word "{f["tool"]}" where a child meets a tiny snag at {f["place_label"]}.',
        f"Tell a gentle story about {f['child_name']} and {f['helper_name']} using tweezers to fix {f['item_phrase']}.",
        f'Write a rhyme-like story that repeats a small problem twice, then turns on a twist and ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("item")
    place_label = f["place_label"]
    item_phrase = f["item_phrase"]
    return [
        QAItem(
            question=f"Who was the story about at {place_label}?",
            answer=f"It was about {child.label_word} {child.label} and {helper.label_word} {helper.label}. They worked together at {place_label} to help {item_phrase}.",
        ),
        QAItem(
            question=f"What happened when {child.label} tried to fix {item_phrase}?",
            answer=f"{child.label} tried once, and then again, and then again, but the little snag stayed stuck. That repetition showed the problem was too tiny for an ordinary tug.",
        ),
        QAItem(
            question="How did the story turn from trouble to success?",
            answer=f"The twist came when {helper.label} showed how tweezers could grip one tiny bit at a time. After that, the snag loosened and {item_phrase} looked neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are tweezers for?",
            answer="Tweezers are a small tool for picking up or moving tiny things. They help when fingers are too big for the job.",
        ),
        QAItem(
            question="Why can repeating the same pull fail?",
            answer="If a snag is tight, doing the same pull again and again may not change it. Sometimes you need a different angle or a gentler grip.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning motion. It can help loosen something that is wrapped, caught, or tangled.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={ {k: v for k, v in e.meters.items() if v} }")
        if e.memes:
            bits.append(f"memes={ {k: v for k, v in e.memes.items() if v} }")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,S) :- place(P), item(I), snag(S).
stuck_after_try(I) :- item(I).
fix_with_tweezers(I) :- tool(tweezers), item(I).
twist_event(I) :- fix_with_tweezers(I).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("tool", "tweezers")]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid in SNAGS:
        lines.append(asp.fact("snag", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    ok = 0
    if py == asps:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py - asps))
        print("  only in ASP:", sorted(asps - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about tweezers, twist, and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, _, item_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child_name])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        place=place_id,
        item=item_id,
        snag=ITEMS[item_id].snag_kind,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], ITEMS[params.item], params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
    StoryParams(child_name="Mia", child_gender="girl", helper_name="Nina", helper_gender="girl", place="nursery", item="ribbon", snag="loop"),
    StoryParams(child_name="Finn", child_gender="boy", helper_name="Maya", helper_gender="girl", place="window", item="teddy", snag="thread"),
    StoryParams(child_name="Lily", child_gender="girl", helper_name="Ben", helper_gender="boy", place="playroom", item="doll_hair", snag="knot"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
