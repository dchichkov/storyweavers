#!/usr/bin/env python3
"""
storyworlds/worlds/tend_rough_misunderstanding_repetition_sharing_ghost_story.py
=================================================================================

A small ghost-story world: children tend a rough, old place, misunderstand a
ghostly noise, repeat the same brave check, and end by sharing the light.

Premise:
- A child tends a rough little yard or attic where a gentle ghost is making a
  soft sound.
- The sound is misunderstood at first.
- The child repeats a careful action instead of rushing away.
- Sharing a lantern, blanket, or snack helps the ghost and child settle into a
  friendly ending.

The world is intentionally tiny and state-driven. Physical meters and emotional
memes both matter: roughness, cold, glow, fear, relief, care, and sharing.

Story contract:
- Standalone stdlib script.
- Uses storyworlds/results.py eagerly.
- Imports storyworlds/asp.py lazily in ASP helpers.
- Provides StoryParams, valid_combos, build_parser, resolve_params, generate,
  emit, and main.
- Supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        for key in ("rough", "cold", "glow", "shared", "hidden", "settled"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "care", "relief", "wonder", "misunderstanding", "sharing", "patience"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    tends: str = ""


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    ghost: str
    tend_item: str
    share_item: str
    seed: Optional[int] = None


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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _rule_settle(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.meters["shared"] >= THRESHOLD and child.memes["sharing"] >= THRESHOLD:
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["settled"] += 1
            child.memes["relief"] += 1
            out.append("The room felt softer at once.")
    return out


def _rule_warm(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.meters["glow"] >= THRESHOLD and child.meters["cold"] >= THRESHOLD:
        sig = ("warm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["cold"] = max(0.0, child.meters["cold"] - 1)
            child.memes["relief"] += 1
            out.append("The little light chased away some of the chill.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_warm, _rule_settle):
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, tends="dusty beams"),
    "garden": Setting(place="the garden", indoor=False, tends="rough stones"),
    "shed": Setting(place="the shed", indoor=True, tends="old shelves"),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Eli", "Ava", "Finn", "Nora", "Theo"]
GHOST_NAMES = ["Pale Tom", "Misty May", "Quiet Gus", "Little Wren"]

TEND_ITEMS = {
    "lantern": Entity(id="lantern", type="thing", label="lantern", phrase="a little lantern", tags={"light", "sharing"}),
    "blanket": Entity(id="blanket", type="thing", label="blanket", phrase="a soft blanket", tags={"sharing", "warm"}),
    "basket": Entity(id="basket", type="thing", label="basket", phrase="a basket of treats", tags={"sharing"}),
}

SHARE_ITEMS = {
    "lantern": Entity(id="lantern", type="thing", label="lantern", phrase="a little lantern", tags={"light", "sharing"}),
    "cookies": Entity(id="cookies", type="thing", label="cookies", phrase="warm cookies", plural=True, tags={"sharing"}),
    "blanket": Entity(id="blanket", type="thing", label="blanket", phrase="a soft blanket", tags={"sharing", "warm"}),
}

CURATED = [
    StoryParams(setting="attic", child="Mia", child_gender="girl", ghost="Quiet Gus", tend_item="lantern", share_item="cookies"),
    StoryParams(setting="garden", child="Noah", child_gender="boy", ghost="Misty May", tend_item="blanket", share_item="lantern"),
    StoryParams(setting="shed", child="Lily", child_gender="girl", ghost="Little Wren", tend_item="basket", share_item="blanket"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for t_id in TEND_ITEMS:
            for sh_id in SHARE_ITEMS:
                if t_id == "basket" and sh_id == "basket":
                    continue
                combos.append((s_id, t_id, sh_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost story world about tending, misunderstanding, repetition, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--ghost", choices=GHOST_NAMES)
    ap.add_argument("--tend-item", choices=TEND_ITEMS)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
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
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.tend_item is None or c[1] == args.tend_item)
        and (args.share_item is None or c[2] == args.share_item)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, tend_item, share_item = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    ghost = args.ghost or rng.choice(GHOST_NAMES)
    return StoryParams(setting=setting, child=child, child_gender="girl" if child in {"Mia", "Lily", "Ava", "Nora"} else "boy", ghost=ghost, tend_item=tend_item, share_item=share_item)


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost))
    tend_item = world.add(Entity(id="tend_item", type="thing", label=params.tend_item, phrase=TEND_ITEMS[params.tend_item].phrase, tags=set(TEND_ITEMS[params.tend_item].tags), plural=TEND_ITEMS[params.tend_item].plural))
    share_item = world.add(Entity(id="share_item", type="thing", label=params.share_item, phrase=SHARE_ITEMS[params.share_item].phrase, tags=set(SHARE_ITEMS[params.share_item].tags), plural=SHARE_ITEMS[params.share_item].plural))
    world.facts.update(child=child, ghost=ghost, tend_item=tend_item, share_item=share_item, params=params)

    child.memes["care"] += 1
    child.memes["patience"] += 1
    child.meters["rough"] += 1
    ghost.meters["glow"] += 1
    if params.tend_item == "lantern":
        child.meters["cold"] += 1
    return world


def tell(world: World) -> None:
    child = world.get("child")
    ghost = world.get("ghost")
    tend_item = world.get("tend_item")
    share_item = world.get("share_item")
    place = world.setting.place

    world.say(f"{child.label} went to {place} where the stones and boards were rough and old.")
    world.say(f"{child.label} wanted to tend the place with {tend_item.phrase}, because {place} felt like it had been waiting for care.")
    world.say(f"Then a soft sound drifted out of the dark. {child.label} thought it might be a warning and felt a small shiver.")

    child.memes["misunderstanding"] += 1
    child.memes["fear"] += 1
    world.para()
    world.say(f"{child.label} listened again. The sound came a second time, and then a third time, so {child.label} repeated the same careful step instead of running away.")
    world.say(f"That was not a trick at all. {ghost.label} was only trying to ask for help, very gently.")

    ghost.meters["hidden"] += 1
    ghost.meters["shared"] += 1
    child.memes["sharing"] += 1
    world.say(f"{child.label} shared {share_item.phrase} with {ghost.label}, and the rough place suddenly felt less lonely.")
    if share_item.label == "lantern":
        ghost.meters["glow"] += 1
    elif share_item.label == "blanket":
        child.meters["cold"] = max(0.0, child.meters["cold"] - 1)
    else:
        child.memes["wonder"] += 1

    propagate(world, narrate=False)
    world.para()
    if ghost.meters["settled"] >= THRESHOLD:
        world.say(f"In the end, {ghost.label} drifted beside {child.label} like a friend, and {place} looked gentler in the lantern light.")
    else:
        world.say(f"In the end, {child.label} kept tending the rough little place, and {ghost.label} stayed near by, no longer scary at all.")

    world.facts["shared"] = ghost.meters["shared"] >= THRESHOLD
    world.facts["misunderstood"] = child.memes["misunderstanding"] >= THRESHOLD
    world.facts["repeated"] = True


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    tend_item = world.facts["tend_item"]
    share_item = world.facts["share_item"]
    params = world.facts["params"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"It is about {child.label} and {ghost.label}. {child.label} went there to tend the rough place and learn what the soft sound meant."
        ),
        QAItem(
            question=f"What did {child.label} first misunderstand?",
            answer=f"{child.label} misunderstood the soft sound and thought it might be something scary. It turned out to be {ghost.label} asking for help."
        ),
        QAItem(
            question=f"What did {child.label} repeat when the sound came again?",
            answer=f"{child.label} repeated the same careful step instead of rushing away. That repetition helped {child.label} stay calm long enough to understand the ghost."
        ),
        QAItem(
            question=f"How did {child.label} help {ghost.label} at the end?",
            answer=f"{child.label} shared {share_item.phrase} with {ghost.label}. Sharing made the place feel warm and friendly, so the ghost could settle down."
        ),
        QAItem(
            question=f"Why was {params.setting} rough at the start?",
            answer=f"It was rough because the place had old stones and worn boards that had not been tended yet. {child.label} took care of it with patience."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to tend something?", answer="To tend something means to take care of it gently, like cleaning, fixing, or watching over it so it gets better."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else."),
        QAItem(question="What is repetition?", answer="Repetition means doing or saying the same thing again. Sometimes repetition helps people notice a pattern."),
        QAItem(question="What is sharing?", answer="Sharing means giving or offering something to someone else so both people can enjoy it."),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a ghost story for a young child about {p.child} tending a rough place in {world.setting.place}.",
        f"Tell a gentle story where {p.child} misunderstands a soft ghost sound, repeats a careful action, and shares a light with {p.ghost}.",
        f"Write a simple ghost story with a calm ending that uses the words tend, rough, misunderstanding, repetition, and sharing.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, item in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {item}")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TEND_ITEMS:
        lines.append(asp.fact("tend_item", tid))
    for sid in SHARE_ITEMS:
        lines.append(asp.fact("share_item", sid))
    for c in CHILD_NAMES:
        lines.append(asp.fact("child_name", c))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost_name", g))
    lines.append(asp.fact("good_combo", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, H) :- setting(S), tend_item(T), share_item(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
