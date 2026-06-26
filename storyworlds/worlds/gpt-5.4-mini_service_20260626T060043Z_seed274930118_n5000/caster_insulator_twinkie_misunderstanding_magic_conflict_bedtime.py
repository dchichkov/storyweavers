#!/usr/bin/env python3
"""
Bedtime-story world: a little magical misunderstanding over a caster, an insulator,
and a twinkie.

A small child-friendly simulation with:
- physical meters: warmth, wobble, glow, crumb, calm
- emotional memes: confusion, fear, hope, trust, relief

The story is built from state changes, not a frozen paragraph.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the bedroom"
    bedtime: bool = True
    quiet: bool = True


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        clone = World(self.scene)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "the bedroom"
    caster: str = "candle caster"
    insulator: str = "blanket insulator"
    twinkie: str = "twinkie"
    name: str = "Mina"
    parent: str = "mother"
    seed: Optional[int] = None


PLACES = {
    "the bedroom": Scene(place="the bedroom", bedtime=True, quiet=True),
    "the hallway": Scene(place="the hallway", bedtime=True, quiet=True),
    "the pillow fort": Scene(place="the pillow fort", bedtime=True, quiet=True),
}

CASTERS = {
    "candle caster": {
        "label": "candle caster",
        "phrase": "a little candle caster",
        "gives": "a warm glow",
        "wobble": 1.0,
        "glow": 1.0,
    },
    "story caster": {
        "label": "story caster",
        "phrase": "a sleepy story caster",
        "gives": "soft story-light",
        "wobble": 0.2,
        "glow": 0.7,
    },
    "moon caster": {
        "label": "moon caster",
        "phrase": "a moon caster",
        "gives": "silver glow",
        "wobble": 0.1,
        "glow": 0.6,
    },
}

INSULATORS = {
    "blanket insulator": {
        "label": "blanket insulator",
        "phrase": "a fluffy blanket insulator",
        "catches": "warmth",
        "calms": 1.0,
        "holds": 1.0,
    },
    "pillow insulator": {
        "label": "pillow insulator",
        "phrase": "a soft pillow insulator",
        "catches": "worry",
        "calms": 0.8,
        "holds": 0.8,
    },
    "lamp insulator": {
        "label": "lamp insulator",
        "phrase": "a little lamp insulator",
        "catches": "glow",
        "calms": 0.5,
        "holds": 0.6,
    },
}

TWINKIES = {
    "twinkie": {
        "label": "twinkie",
        "phrase": "a shiny twinkie",
        "crumb": 1.0,
        "sweet": 1.0,
    },
    "mini twinkie": {
        "label": "mini twinkie",
        "phrase": "a tiny twinkie",
        "crumb": 0.6,
        "sweet": 0.8,
    },
}

GENTLE_NAMES = ["Mina", "Luna", "Nora", "Iris", "Mila", "Eva", "Rose", "June"]
PARENT_NAMES = ["mother", "father", "grandmother", "grandfather"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _bump(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _feel(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def _has(entity: Entity, key: str) -> bool:
    return entity.meters.get(key, 0.0) >= THRESHOLD or entity.memes.get(key, 0.0) >= THRESHOLD


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict_misunderstanding(world: World, caster: Entity, insulator: Entity, twinkie: Entity) -> bool:
    sim = world.copy()
    _do_magic(sim, sim.get(caster.id), sim.get(insulator.id), sim.get(twinkie.id), narrate=False)
    return sim.facts.get("conflict", False) is True


def _do_magic(world: World, caster: Entity, insulator: Entity, twinkie: Entity, narrate: bool = True) -> None:
    if "magic" in world.fired:
        return
    world.fired.add("magic")
    _bump(caster, "glow", CASTERS[caster.label]["glow"])
    _feel(caster, "hope", 1.0)
    _feel(twinkie, "sweetness", TWINKIES[twinkie.label]["sweet"])
    _bump(twinkie, "crumb", TWINKIES[twinkie.label]["crumb"])

    # A magical bedtime rule: the insulator softens the caster's wobble and can
    # hold warmth or glow, but if the twinkie is present too early, the child
    # may misunderstand the flicker as "something is wrong".
    wobble = CASTERS[caster.label]["wobble"]
    hold = INSULATORS[insulator.label]["holds"]
    _bump(caster, "wobble", max(0.0, wobble - hold))

    if twinkie.meters.get("crumb", 0.0) >= THRESHOLD and caster.meters.get("wobble", 0.0) > 0.2:
        world.facts["conflict"] = True
        _feel(caster, "confusion", 1.0)
        _feel(twinkie, "fear", 1.0)
    else:
        world.facts["conflict"] = False

    if narrate:
        world.say(
            f"The {caster.label} gave off a sleepy glow, and the {insulator.label} "
            f"tried to hold the warmth gentle and safe."
        )
        if world.facts["conflict"]:
            world.say(
                f"But when crumbs fell from the {twinkie.label}, the light looked funny "
                f"in the dark, and a misunderstanding began."
            )


def tell(params: StoryParams) -> World:
    scene = PLACES.get(params.place)
    if scene is None:
        raise StoryError(f"Unknown place: {params.place}")

    caster_cfg = CASTERS.get(params.caster)
    insulator_cfg = INSULATORS.get(params.insulator)
    twinkie_cfg = TWINKIES.get(params.twinkie)
    if caster_cfg is None:
        raise StoryError(f"Unknown caster: {params.caster}")
    if insulator_cfg is None:
        raise StoryError(f"Unknown insulator: {params.insulator}")
    if twinkie_cfg is None:
        raise StoryError(f"Unknown twinkie: {params.twinkie}")

    world = World(scene)
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent"))
    caster = world.add(Entity(id="caster", label=params.caster, phrase=caster_cfg["phrase"], type="caster"))
    insulator = world.add(Entity(id="insulator", label=params.insulator, phrase=insulator_cfg["phrase"], type="insulator"))
    twinkie = world.add(Entity(id="twinkie", label=params.twinkie, phrase=twinkie_cfg["phrase"], type="twinkie", plural=False))

    world.say(
        f"At bedtime in {scene.place}, {child.id} saw {caster_cfg['phrase']}, "
        f"{insulator_cfg['phrase']}, and {twinkie_cfg['phrase']} waiting on the quilt."
    )
    _feel(child, "curiosity", 1.0)
    _feel(parent, "calm", 1.0)

    world.para()
    world.say(
        f"{child.id} wanted the little magic to feel cozy, so {child.pronoun()} "
        f"brought the {insulator.label} closer and watched the glow."
    )
    _do_magic(world, caster, insulator, twinkie)

    world.para()
    if world.facts.get("conflict"):
        _feel(child, "confusion", 1.0)
        _feel(parent, "trust", 1.0)
        world.say(
            f"{child.id} thought the twinkie had spoiled the spell, but {parent.id} "
            f"smiled and said the crumbs were only making the light dance."
        )
        world.say(
            f"Together they tucked the {twinkie.label} onto a plate, and the "
            f"{insulator.label} kept the magic warm instead of wobbly."
        )
        _feel(child, "relief", 1.0)
        _feel(child, "trust", 1.0)
        _bump(insulator, "warmth", 1.0)
        world.facts["resolved"] = True
    else:
        world.say(
            f"There was no real trouble at all. The {insulator.label} held the glow, "
            f"and the {twinkie.label} stayed neatly on its napkin."
        )
        world.facts["resolved"] = True

    world.para()
    world.say(
        f"At the end, {child.id} was sleepy and safe, with the {caster.label} dimmed "
        f"to a tiny night-light and the {insulator.label} wrapped around the quiet room."
    )

    world.facts.update(
        child=child,
        parent=parent,
        caster=caster,
        insulator=insulator,
        twinkie=twinkie,
        place=params.place,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a bedtime story about a child, a {p.caster}, a {p.insulator}, and a {p.twinkie}.",
        f"Tell a gentle magic story in {p.place} where a misunderstanding gets soothed before sleep.",
        f"Make a child-friendly story with magic, conflict, and a soft ending image in the bedroom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    caster: Entity = f["caster"]
    insulator: Entity = f["insulator"]
    twinkie: Entity = f["twinkie"]

    out = [
        QAItem(
            question=f"What was {child.id} looking at at bedtime?",
            answer=f"{child.id} was looking at {caster.phrase}, {insulator.phrase}, and {twinkie.phrase} in {f['place']}."
        ),
        QAItem(
            question=f"What made the story feel like a misunderstanding?",
            answer=(
                f"The misunderstanding began when crumbs from the {twinkie.label} "
                f"made the magic light seem wobbly, so {child.id} thought something was wrong."
            ),
        ),
        QAItem(
            question=f"How did the {insulator.label} help?",
            answer=(
                f"The {insulator.label} held the warmth gentle, so the magic could stay cozy "
                f"and the room could calm down before sleep."
            ),
        ),
    ]
    if f.get("conflict"):
        out.append(
            QAItem(
                question=f"Why did {child.id} worry about the magic?",
                answer=(
                    f"{child.id} worried because the {caster.label} looked strange in the dark "
                    f"after the {twinkie.label} made crumbs, which felt like a problem until "
                    f"{parent.id} explained it was only a misunderstanding."
                ),
            )
        )
    if f.get("resolved"):
        out.append(
            QAItem(
                question=f"What changed by the end?",
                answer=(
                    f"By the end, the confusion turned into relief. The {twinkie.label} was put aside, "
                    f"the {insulator.label} kept the magic soft, and {child.id} fell asleep feeling safe."
                ),
            )
        )
    return out


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twinkie in this story world?",
            answer="A twinkie is a small sweet snack that can leave crumbs."
        ),
        QAItem(
            question="What does an insulator do?",
            answer="An insulator helps hold warmth or stop things from getting too strong or too cold."
        ),
        QAItem(
            question="What does a caster do in this story world?",
            answer="A caster makes a little magic glow or feeling, like a sleepy light."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The python reasonableness gate says:
% a story is valid when the selected caster, insulator, and twinkie exist.
valid_story(Caster, Insulator, Twinkie) :-
    caster(Caster), insulator(Insulator), twinkie(Twinkie).

% A misunderstanding is expected when the twinkie can crumb and the caster wobbles.
conflict(Caster, Twinkie) :-
    caster(Caster), twinkie(Twinkie),
    wobbles(Caster), crumbs(Twinkie).

% A soft resolution exists when the insulator can hold warmth.
resolution(Insulator) :- insulator(Insulator), holds_warmth(Insulator).

#show valid_story/3.
#show conflict/2.
#show resolution/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for cid in CASTERS:
        lines.append(asp.fact("caster", cid))
    for iid in INSULATORS:
        lines.append(asp.fact("insulator", iid))
    for tid in TWINKIES:
        lines.append(asp.fact("twinkie", tid))
    for cid, cfg in CASTERS.items():
        if cfg["wobble"] > 0.0:
            lines.append(asp.fact("wobbles", cid))
    for tid, cfg in TWINKIES.items():
        if cfg["crumb"] > 0.0:
            lines.append(asp.fact("crumbs", tid))
    for iid, cfg in INSULATORS.items():
        if cfg["holds"] > 0.0:
            lines.append(asp.fact("holds_warmth", iid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    asp_valid = set(asp.atoms(model, "valid_story"))
    py_valid = {(c, i, t) for c in CASTERS for i in INSULATORS for t in TWINKIES}
    if asp_valid != py_valid:
        print("MISMATCH between ASP and Python valid stories:")
        print("ASP:", sorted(asp_valid))
        print("PY :", sorted(py_valid))
        return 1
    print(f"OK: ASP matches Python valid stories ({len(py_valid)} triples).")
    return 0


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime magic story world.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--caster", choices=CASTERS.keys())
    ap.add_argument("--insulator", choices=INSULATORS.keys())
    ap.add_argument("--twinkie", choices=TWINKIES.keys())
    ap.add_argument("--name", choices=GENTLE_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    place = args.place or rng.choice(list(PLACES.keys()))
    caster = args.caster or rng.choice(list(CASTERS.keys()))
    insulator = args.insulator or rng.choice(list(INSULATORS.keys()))
    twinkie = args.twinkie or rng.choice(list(TWINKIES.keys()))
    name = args.name or rng.choice(GENTLE_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(
        place=place,
        caster=caster,
        insulator=insulator,
        twinkie=twinkie,
        name=name,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="the bedroom", caster="story caster", insulator="blanket insulator", twinkie="twinkie", name="Mina", parent="mother"),
    StoryParams(place="the pillow fort", caster="moon caster", insulator="pillow insulator", twinkie="mini twinkie", name="Luna", parent="father"),
    StoryParams(place="the hallway", caster="candle caster", insulator="blanket insulator", twinkie="twinkie", name="Nora", parent="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        triples = sorted(set(asp.atoms(model, "valid_story")))
        for triple in triples:
            print(triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        if len(samples) > 1:
            print(f"### story {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
