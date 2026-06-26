#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sharp_plead_cautionary_conflict_misunderstanding_bedtime_story.py
================================================================================================

A small bedtime storyworld about a child, a sharp thing, and a gentle
misunderstanding that turns into a safer choice.

Seed tale used to shape the world model:
---
At bedtime, Mina found a sharp little moon charm tucked in her blanket.
She wanted to keep it under her pillow, because it felt like good luck.
Her mother gently said no, because the charm was sharp and could poke her.
Mina pleaded to keep it anyway, thinking her mother wanted to take it away.
Then her mother explained that the charm could sleep in a soft box on the
nightstand, and Mina could still have it nearby.
Mina agreed, hugged her mother, and fell asleep with the moon charm safe by
her bed.

World model:
---
    child desire for sharp keepsake -> eagerness + pleading
    parent caution about bedtime safety -> worry + warning
    misunderstanding about taking away treasure -> conflict
    safe compromise (soft box / nightstand) -> relief + calm

The prose is driven by simulated state rather than a fixed paragraph.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    stores: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["worry", "danger", "comfort", "joy", "plead", "conflict", "understanding", "sleepy"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    type: str
    dangerous_when: str
    safe_storage: str
    safe_label: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class SafePlace:
    id: str
    label: str
    phrase: str
    stores: set[str]
    comfort_bonus: float = 1.0


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _raise_conflict(world: World, child: Entity) -> None:
    child.memes["conflict"] += 1
    child.memes["plead"] += 1


def _resolve_conflict(world: World, child: Entity) -> None:
    child.memes["conflict"] = 0.0
    child.memes["understanding"] += 1
    child.memes["comfort"] += 1
    child.memes["plead"] = 0.0


def caution_about_sharp(world: World, parent: Entity, child: Entity, keepsake: Entity) -> None:
    child.memes["danger"] += 1
    parent.memes["worry"] += 1
    world.say(
        f'"That {keepsake.label} is sharp," {parent.pronoun("subject")} said softly. '
        f'"It could poke you in bed."'
    )


def plead_for_keepsake(world: World, child: Entity, keepsake: Entity) -> None:
    _raise_conflict(world, child)
    child.memes["joy"] += 0.2
    world.say(
        f"{child.id} clutched {child.pronoun('possessive')} {keepsake.label} and pleaded, "
        f'"Please let me keep it by my pillow."'
    )


def misunderstanding(world: World, child: Entity, parent: Entity, keepsake: Entity) -> None:
    if child.memes["conflict"] < THRESHOLD:
        return
    world.say(
        f"{child.id} thought {parent.pronoun('subject')} wanted to take the treasure away, "
        f"so the little voice in the room got tense."
    )
    world.say(
        f'"I am not trying to take it," {parent.id} said. "I only want it safe."'
    )


def safe_choice(world: World, parent: Entity, child: Entity, keepsake: Entity, safe: Entity) -> None:
    _resolve_conflict(world, child)
    safe.worn_by = None
    keepsake.worn_by = None
    keepsake.owner = child.id
    world.say(
        f"{parent.id} opened a {safe.label} and tucked the {keepsake.label} inside. "
        f"It rested on the nightstand, close enough for a good-night glance."
    )
    world.say(
        f"{child.id} nodded, hugged {parent.pronoun('object')}, and lay down feeling calm."
    )


def bedtime_settle(world: World, child: Entity, keepsake: Entity) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"The lamp glowed low, the blanket stayed smooth, and {child.id} fell asleep "
        f"knowing the {keepsake.label} was safe."
    )


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"bedtime"}),
}

KEEPSAKES = {
    "moon_charm": Keepsake(
        id="moon_charm",
        label="moon charm",
        phrase="a tiny silver moon charm",
        type="charm",
        dangerous_when="kept under a pillow",
        safe_storage="soft box",
        safe_label="soft box",
        genders={"girl", "boy"},
    ),
    "glass_star": Keepsake(
        id="glass_star",
        label="glass star",
        phrase="a small glass star",
        type="star",
        dangerous_when="kept in bed",
        safe_storage="cushioned box",
        safe_label="cushioned box",
        genders={"girl", "boy"},
    ),
    "metal_key": Keepsake(
        id="metal_key",
        label="tiny key",
        phrase="a tiny brass key",
        type="key",
        dangerous_when="kept under a blanket",
        safe_storage="drawer tray",
        safe_label="drawer tray",
        genders={"girl", "boy"},
    ),
}

SAFE_PLACES = {
    "soft_box": SafePlace(
        id="soft_box",
        label="soft box",
        phrase="a soft box with a padded lid",
        stores={"moon_charm"},
        comfort_bonus=1.0,
    ),
    "cushioned_box": SafePlace(
        id="cushioned_box",
        label="cushioned box",
        phrase="a cushioned box lined with cloth",
        stores={"glass_star"},
        comfort_bonus=1.0,
    ),
    "drawer_tray": SafePlace(
        id="drawer_tray",
        label="drawer tray",
        phrase="a little drawer tray lined with felt",
        stores={"metal_key"},
        comfort_bonus=1.0,
    ),
}


@dataclass
class StoryParams:
    place: str
    keepsake: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("bedroom", k) for k in KEEPSAKES]


def keep_is_risky(keepsake: Keepsake) -> bool:
    return True


def select_safe_place(keepsake: Keepsake) -> Optional[SafePlace]:
    for safe in SAFE_PLACES.values():
        if keepsake.id in safe.stores:
            return safe
    return None


def explain_rejection(keepsake: Keepsake) -> str:
    return f"(No story: the catalog has no safe bedside place for {keepsake.label}.)"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    keepsake_cfg = KEEPSAKES[params.keepsake]
    safe_cfg = select_safe_place(keepsake_cfg)
    if safe_cfg is None:
        raise StoryError(explain_rejection(keepsake_cfg))
    keepsake = world.add(Entity(
        id=keepsake_cfg.id,
        type=keepsake_cfg.type,
        label=keepsake_cfg.label,
        phrase=keepsake_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
    ))
    safe = world.add(Entity(
        id=safe_cfg.id,
        type="storage",
        label=safe_cfg.label,
        phrase=safe_cfg.phrase,
        protective=True,
        stores=set(safe_cfg.stores),
    ))
    child.memes["joy"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"At bedtime, {child.id} found {child.pronoun('possessive')} {keepsake.label} by the blanket."
    )
    world.say(
        f"{child.id} loved how special it looked and wanted to keep it close through the night."
    )
    world.para()
    caution_about_sharp(world, parent, child, keepsake)
    plead_for_keepsake(world, child, keepsake)
    misunderstanding(world, child, parent, keepsake)
    world.para()
    safe_choice(world, parent, child, keepsake, safe)
    bedtime_settle(world, child, keepsake)
    world.facts.update(child=child, parent=parent, keepsake=keepsake, safe=safe, keepsake_cfg=keepsake_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, ks = f["child"], f["parent"], f["keepsake_cfg"]
    return [
        f'Write a bedtime story for a young child about a sharp {ks.label} and a gentle compromise.',
        f"Tell a soft story where {child.id} pleads to keep a sharp treasure by the bed, but {parent.id} worries about safety.",
        f'Write a cozy bedtime tale that includes the word "sharp" and ends with a safe place for a special keepsake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, ks = f["child"], f["parent"], f["keepsake_cfg"]
    safe = f["safe"]
    return [
        QAItem(
            question=f"What did {child.id} want to keep near the pillow?",
            answer=f"{child.id} wanted to keep {child.pronoun('possessive')} {ks.label} near the pillow because it felt special.",
        ),
        QAItem(
            question=f"Why did {parent.id} say the {ks.label} should not stay in bed?",
            answer=f"{parent.id} was careful because the {ks.label} was sharp and could poke {child.pronoun('object')} during the night.",
        ),
        QAItem(
            question=f"How was the {ks.label} kept safe in the end?",
            answer=f"They put it in the {safe.label} on the nightstand, so it stayed close but not in the bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a sharp object not be left where someone sleeps?",
            answer="A sharp object can poke or scratch skin, so it is safer to put it somewhere soft and out of the bed.",
        ),
        QAItem(
            question="What does it mean to plead?",
            answer="To plead means to ask very hard and very earnestly for something.",
        ),
        QAItem(
            question="Why do parents often choose safe places for small treasures at bedtime?",
            answer="Parents try to keep children safe while still letting them keep special things nearby.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"stores={sorted(e.stores)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_wants(C,K) :- child(C), keepsake(K).
sharp(K) :- keepsake(K).
needs_safety(K) :- sharp(K).
risky_bedtime(K) :- needs_safety(K).
valid_fix(K,S) :- keepsake(K), safe_place(S), stores(S,K).
valid_story(C,K,S) :- child(C), keepsake(K), safe_place(S), valid_fix(K,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("child", "mina"))
    for kid in ["mina", "leo", "zoe"]:
        lines.append(asp.fact("child", kid))
    for ks in KEEPSAKES.values():
        lines.append(asp.fact("keepsake", ks.id))
        lines.append(asp.fact("sharp", ks.id))
    for safe in SAFE_PLACES.values():
        lines.append(asp.fact("safe_place", safe.id))
        for k in safe.stores:
            lines.append(asp.fact("stores", safe.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple[str, str, str]]:
    return [("mina", k, s) for k, s in [(k.id, select_safe_place(k).id) for k in KEEPSAKES.values()]]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a sharp keepsake and a gentle compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    choices = list(KEEPSAKES)
    ks = args.keepsake or rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = ["Mina", "Luna", "Noah", "Ivy", "Seth", "Ella"]
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=args.place or "bedroom", keepsake=ks, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    # lightweight parity check
    if not asp_program("#show valid_story/3."):
        print("MISMATCH: empty ASP program")
        return 1
    print("OK: ASP twin is present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = valid_story_triples()
        print(f"{len(triples)} compatible bedtime combinations:")
        for c, k, s in triples:
            print(f"  {c} / {k} / {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    if args.all:
        for k in KEEPSAKES:
            params = StoryParams(place="bedroom", keepsake=k, name="Mina", gender="girl", parent="mother")
            samples.append(generate(params))
    else:
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
