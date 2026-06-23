#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/respect_wafer_transformation_sharing_cautionary_animal_story.py
============================================================================================================

A small animal-story world about respect, a wafer, a surprising transformation,
sharing, and a cautionary turn that ends safely. The story space is intentionally
tiny and constraint-checked so every sample is a complete child-facing story with
a clear beginning, middle turn, and ending image.
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
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    caret: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "mouse", "cat", "fox", "otter", "hedgehog", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    safe_floor: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CharacterCfg:
    id: str
    type: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class WaferCfg:
    id: str
    label: str
    phrase: str
    crumbs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TransformationCfg:
    id: str
    label: str
    action: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingCfg:
    id: str
    label: str
    offer: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# Registries
PLACES = {
    "meadow": Place(id="meadow", label="the sunny meadow", tags={"outdoor"}),
    "barn": Place(id="barn", label="the warm barn", tags={"indoor"}),
    "riverbank": Place(id="riverbank", label="the quiet riverbank", tags={"outdoor"}),
}

ANIMALS = {
    "rabbit": CharacterCfg(id="rabbit", type="rabbit", label="rabbit", tags={"small"}),
    "mouse": CharacterCfg(id="mouse", type="mouse", label="mouse", tags={"small"}),
    "fox": CharacterCfg(id="fox", type="fox", label="fox", tags={"clever"}),
    "otter": CharacterCfg(id="otter", type="otter", label="otter", tags={"playful"}),
}

WAFERS = {
    "honey": WaferCfg(id="honey", label="a honey wafer", phrase="a crisp honey wafer", crumbs="honey crumbs", tags={"sweet"}),
    "oat": WaferCfg(id="oat", label="an oat wafer", phrase="a light oat wafer", crumbs="oat crumbs", tags={"plain"}),
    "berry": WaferCfg(id="berry", label="a berry wafer", phrase="a berry-sweet wafer", crumbs="purple crumbs", tags={"sweet"}),
}

TRANSFORMS = {
    "sparkle": TransformationCfg(id="sparkle", label="a sparkling change", action="took one bite and began to glow and grow", reveal="sparkled into a bigger, brighter shape", tags={"magic"}),
    "tiny": TransformationCfg(id="tiny", label="a tiny change", action="nibbled the edge and shrank to a little rounder shape", reveal="turned smaller and rounder", tags={"magic"}),
}

SHARINGS = {
    "split": SharingCfg(id="split", label="a careful sharing", offer="broke the wafer into neat pieces", result="every piece was fair", tags={"sharing"}),
    "slice": SharingCfg(id="slice", label="a kind sharing", offer="snapped the wafer in half", result="both friends got a fair share", tags={"sharing"}),
}

NAMES = ["Pip", "Milo", "Tia", "Nina", "Benny", "Luna", "Nora", "Ollie"]


@dataclass
class StoryParams:
    place: str
    animal1: str
    animal2: str
    wafer: str
    transform: str
    sharing: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    out = []
    for p in PLACES:
        for a in ANIMALS:
            for w in WAFERS:
                for t in TRANSFORMS:
                    for s in SHARINGS:
                        # all combos valid; story space stays small but rich
                        out.append((p, a, "friend", w, t, s))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: respect, wafer, sharing, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--wafer", choices=WAFERS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--sharing", choices=SHARINGS)
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
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.animal1 is None or c[1] == args.animal1)
                and (args.wafer is None or c[3] == args.wafer)
                and (args.transform is None or c[4] == args.transform)
                and (args.sharing is None or c[5] == args.sharing)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    p, a1, _, w, t, s = rng.choice(filtered)
    a2 = args.animal2 or rng.choice([k for k in ANIMALS if k != a1])
    return StoryParams(place=p, animal1=a1, animal2=a2, wafer=w, transform=t, sharing=s)


def world_from_params(params: StoryParams) -> World:
    place = PLACES.get(params.place)
    if place is None:
        raise StoryError("Unknown place.")
    if params.animal1 not in ANIMALS or params.animal2 not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.wafer not in WAFERS or params.transform not in TRANSFORMS or params.sharing not in SHARINGS:
        raise StoryError("Unknown story ingredient.")
    world = World(place)
    a1_cfg = ANIMALS[params.animal1]
    a2_cfg = ANIMALS[params.animal2]
    wcfg = WAFERS[params.wafer]
    tcfg = TRANSFORMS[params.transform]
    scfg = SHARINGS[params.sharing]

    a1 = world.add(Entity(id="a1", kind="character", type=a1_cfg.type, label=NAMES[0], tags=set(a1_cfg.tags), meters={}, memes={"curious": 1.0, "respect": 0.0}, attrs={"cfg": a1_cfg}))
    a2 = world.add(Entity(id="a2", kind="character", type=a2_cfg.type, label=NAMES[1], tags=set(a2_cfg.tags), meters={}, memes={"patient": 1.0, "respect": 0.0}, attrs={"cfg": a2_cfg}))
    wafer = world.add(Entity(id="wafer", kind="thing", type="wafer", label=wcfg.label, phrase=wcfg.phrase, tags=set(wcfg.tags), meters={"crumbs": 0.0}, memes={}, attrs={"cfg": wcfg}))
    world.facts.update(actor=a1, helper=a2, wafer=wafer, place=place, transform=tcfg, sharing=scfg, cfgs=(a1_cfg, a2_cfg, wcfg, tcfg, scfg), shared=False, transformed=False, warned=False)
    return world


def _apply_transformation(world: World) -> list[str]:
    out = []
    if world.facts["transformed"]:
        return out
    wafer: Entity = world.facts["wafer"]  # type: ignore[assignment]
    tcfg: TransformationCfg = world.facts["transform"]  # type: ignore[assignment]
    if wafer.meters.get("crumbs", 0.0) < THRESHOLD:
        return out
    world.facts["transformed"] = True
    actor: Entity = world.facts["actor"]  # type: ignore[assignment]
    actor.memes["wonder"] = actor.memes.get("wonder", 0.0) + 1.0
    out.append(f"{actor.label} {tcfg.action}. Soon {actor.pronoun().capitalize()} {tcfg.reveal}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _apply_transformation(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = world_from_params(params)
    actor: Entity = world.facts["actor"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    wafer: Entity = world.facts["wafer"]  # type: ignore[assignment]
    tcfg: TransformationCfg = world.facts["transform"]  # type: ignore[assignment]
    scfg: SharingCfg = world.facts["sharing"]  # type: ignore[assignment]

    world.say(f"At {world.place.label}, {actor.label} found {wafer.label} beside a stone.")
    world.say(f"{helper.label} looked at it and said, \"Let's show respect and share it fairly.\"")
    world.para()
    world.say(f"{actor.label} wanted to keep it all, but {helper.label} waited calmly.")
    actor.memes["respect"] += 1.0
    helper.memes["respect"] += 1.0
    world.facts["warned"] = True
    world.say(f"Then {helper.label} {scfg.offer}, and {scfg.result}.")
    wafer.meters["crumbs"] += 1.0
    world.say(f"The {params.wafer} wafer broke open with {wafer.attrs['cfg'].crumbs}.")
    propagate(world)
    if world.facts["transformed"]:
        world.para()
        world.say(f"After the change, {actor.label} and {helper.label} smiled and shared the last crumb.")
        world.say(f"They sat together at {world.place.label}, with the wafer gone and the new shape resting in the grass.")
    else:
        world.para()
        world.say(f"The wafer stayed still, and the friends still shared it with care.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    actor: Entity = f["actor"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    wafer: Entity = f["wafer"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short animal story for a 3-to-5-year-old about {actor.label} and {helper.label} at {place.label}, using the word "respect".',
        f"Tell a gentle cautionary story where {actor.label} finds {wafer.label}, learns to share it, and something changes in a surprising way.",
        f'Write a small story about sharing a wafer fairly, with a calm warning and a magical transformation at {place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor: Entity = f["actor"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    wafer: Entity = f["wafer"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    tcfg: TransformationCfg = f["transform"]  # type: ignore[assignment]
    scfg: SharingCfg = f["sharing"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {actor.label} find at {place.label}?",
            answer=f"{actor.label} found {wafer.label} at {place.label}. It was a small treat, but the story was really about how {actor.label} treated {helper.label} with respect.",
        ),
        QAItem(
            question=f"How did {helper.label} help with the wafer?",
            answer=f"{helper.label} showed a calm, careful way to share it. {scfg.offer.capitalize()}, and that made the moment fair for both animals.",
        ),
        QAItem(
            question=f"What changed after the wafer was shared?",
            answer=f"The wafer's crumbs began the transformation, and {actor.label} {tcfg.action}. After that, {actor.pronoun().capitalize()} {tcfg.reveal}, which proved the sharing had changed the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is respect?", "Respect means treating someone kindly, listening to them, and caring about what they need too."),
        QAItem("What is a wafer?", "A wafer is a thin, crisp snack that can break into little pieces."),
        QAItem("Why should animals share?", "Sharing helps everyone get enough and keeps friends from feeling left out."),
        QAItem("What is a transformation?", "A transformation is a change from one shape or state into another."),
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
        lines.append(f"  {e.id}: type={e.type} label={e.label!r} meters={e.meters} memes={e.memes} attrs={list(e.attrs.keys())}")
    lines.append(f"  facts={sorted(world.fired)}")
    lines.append(f"  transformed={world.facts.get('transformed')} warned={world.facts.get('warned')}")
    return "\n".join(lines)


ASP_RULES = r"""
share_ok(A,W) :- actor(A), wafer(W).
transform_occurs(A,W,T) :- share_ok(A,W), crumbs(W,1), transform(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for wid in WAFERS:
        lines.append(asp.fact("wafer", wid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    for sid in SHARINGS:
        lines.append(asp.fact("sharing", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    if not model:
        print("ASP produced no model.")
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, animal1=None, animal2=None, wafer=None, transform=None, sharing=None), random.Random(7)))
    try:
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    print("OK: ASP and Python hooks are reachable.")
    return 0


def valid_combo_rows() -> list[tuple[str, str, str, str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


CURATED = [
    StoryParams(place="meadow", animal1="rabbit", animal2="mouse", wafer="honey", transform="sparkle", sharing="split"),
    StoryParams(place="barn", animal1="fox", animal2="rabbit", wafer="oat", transform="tiny", sharing="slice"),
    StoryParams(place="riverbank", animal1="otter", animal2="mouse", wafer="berry", transform="sparkle", sharing="split"),
    StoryParams(place="meadow", animal1="mouse", animal2="rabbit", wafer="berry", transform="tiny", sharing="slice"),
]


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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.asp:
        print(f"{len(valid_combos())} valid combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
