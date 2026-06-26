#!/usr/bin/env python3
"""
A small animal-story world about a pixie, a nut, and a weed.

Premise:
- A small animal wants a shiny nut.
- A pixie uses a magical transformation on a stubborn weed.
- The animal and the pixie have a misunderstanding, then reconcile.
- They work together to make the garden kind and safe again.

The story engine is state-driven: characters have meters and memes, the
transformation changes the weed's form, and the ending image proves the repair.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "pixie" | "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    form: str = "normal"
    location: str = ""

    def pronoun(self) -> str:
        if self.kind == "pixie":
            return "she"
        return "it"

    def possessive(self) -> str:
        if self.kind == "pixie":
            return "her"
        return "its"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    animal: str
    pixie: str
    weed: str
    nut: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": "the garden",
    "orchard": "the orchard",
    "meadow": "the meadow",
    "hedge": "the hedge-row",
}

ANIMALS = {
    "squirrel": {
        "kind": "animal",
        "label": "squirrel",
        "phrase": "a quick little squirrel",
        "desire": "collect shiny things",
    },
    "rabbit": {
        "kind": "animal",
        "label": "rabbit",
        "phrase": "a curious rabbit",
        "desire": "gather snacks",
    },
    "mouse": {
        "kind": "animal",
        "label": "mouse",
        "phrase": "a tiny mouse",
        "desire": "find a cozy treasure",
    },
}

PIXIES = {
    "twig": {
        "label": "Twig",
        "phrase": "a bright pixie with leaf-green wings",
        "magic": "transformation",
    },
    "miri": {
        "label": "Miri",
        "phrase": "a gentle pixie with sparkly shoes",
        "magic": "transformation",
    },
    "luna": {
        "label": "Luna",
        "phrase": "a tiny pixie with a blue ribbon",
        "magic": "transformation",
    },
}

WEEDS = {
    "brambleweed": {
        "label": "weed",
        "phrase": "a stubborn weed with prickly leaves",
        "mess": "tangled",
    },
    "thistleweed": {
        "label": "weed",
        "phrase": "a thorny weed that pushed into every corner",
        "mess": "spiky",
    },
    "vineweed": {
        "label": "weed",
        "phrase": "a long weed that wrapped around everything",
        "mess": "twisty",
    },
}

NUTS = {
    "hazelnut": {
        "label": "nut",
        "phrase": "a smooth hazelnut",
    },
    "acorn": {
        "label": "nut",
        "phrase": "a small acorn",
    },
    "walnut": {
        "label": "nut",
        "phrase": "a round walnut",
    },
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _animal_name(animal_id: str) -> str:
    return ANIMALS[animal_id]["label"]


def _animal_phrase(animal_id: str) -> str:
    return ANIMALS[animal_id]["phrase"]


def _pixie_phrase(pixie_id: str) -> str:
    return PIXIES[pixie_id]["phrase"]


def _weed_phrase(weed_id: str) -> str:
    return WEEDS[weed_id]["phrase"]


def _nut_phrase(nut_id: str) -> str:
    return NUTS[nut_id]["phrase"]


def tell_story(params: StoryParams) -> World:
    world = World(place=SETTINGS[params.setting])

    animal_cfg = ANIMALS[params.animal]
    pixie_cfg = PIXIES[params.pixie]
    weed_cfg = WEEDS[params.weed]
    nut_cfg = NUTS[params.nut]

    animal = world.add(Entity(
        id="animal",
        kind="animal",
        label=animal_cfg["label"],
        phrase=animal_cfg["phrase"],
        meters={"hunger": 1.0, "hope": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "trust": 0.0, "teamwork": 0.0, "reconciliation": 0.0},
        location=world.place,
    ))
    pixie = world.add(Entity(
        id="pixie",
        kind="pixie",
        label=pixie_cfg["label"],
        phrase=pixie_cfg["phrase"],
        meters={"spark": 1.0},
        memes={"care": 1.0, "worry": 0.0, "joy": 0.0, "trust": 0.0, "teamwork": 0.0, "reconciliation": 0.0},
        location=world.place,
    ))
    weed = world.add(Entity(
        id="weed",
        kind="thing",
        label=weed_cfg["label"],
        phrase=weed_cfg["phrase"],
        meters={"mess": 1.0},
        memes={"stubbornness": 1.0, "trouble": 1.0},
        form="wild",
        location=world.place,
    ))
    nut = world.add(Entity(
        id="nut",
        kind="thing",
        label=nut_cfg["label"],
        phrase=nut_cfg["phrase"],
        meters={"shine": 1.0},
        memes={"value": 1.0},
        location=world.place,
    ))

    # Act 1: setup
    world.say(
        f"In {world.place}, {animal.phrase} sniffed the grass and found {nut.phrase} "
        f"near {weed.phrase}."
    )
    world.say(
        f"{animal.label.capitalize()} wanted the {nut.label}, but the weed blocked the path."
    )
    world.para()

    # Act 2: tension and transformation
    animal.memes["worry"] += 1.0
    pixie.memes["worry"] += 1.0
    weed.meters["mess"] += 0.5
    world.say(
        f"{animal.label.capitalize()} frowned and said, 'That weed is in my way.'"
    )
    world.say(
        f"{pixie.label} fluttered closer and whispered a transformation spell."
    )
    weed.form = "flower"
    weed.label = "flower"
    weed.phrase = "a soft flower with tiny petals"
    weed.meters["mess"] = 0.0
    pixie.memes["joy"] += 1.0
    world.say(
        f"With a twinkle, the stubborn weed changed into {weed.phrase}."
    )
    world.para()

    # Act 3: reconciliation and teamwork
    animal.memes["trust"] += 1.0
    pixie.memes["trust"] += 1.0
    animal.memes["reconciliation"] += 1.0
    pixie.memes["reconciliation"] += 1.0
    animal.memes["teamwork"] += 1.0
    pixie.memes["teamwork"] += 1.0
    animal.memes["joy"] += 1.0
    pixie.memes["joy"] += 1.0
    world.say(
        f"{animal.label.capitalize()} looked at {pixie.label}, and the two shared a small smile."
    )
    world.say(
        f"Together they nudged the flower aside, picked up the {nut.label}, and carried it to a sunny stone."
    )
    world.say(
        f"By the end, {animal.label} was calm, {pixie.label} was laughing, and the garden looked kind again."
    )

    world.facts.update(
        animal=animal,
        pixie=pixie,
        weed=weed,
        nut=nut,
        setting=params.setting,
        animal_id=params.animal,
        pixie_id=params.pixie,
        weed_id=params.weed,
        nut_id=params.nut,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short animal story about a {f['animal_id']} and a pixie in {world.place} with a nut and a weed.",
        f"Tell a gentle story where {f['animal'].label} and {f['pixie'].label} solve a problem by using transformation and teamwork.",
        f"Write a child-friendly story that begins with a small animal wanting a nut and ends with reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal = f["animal"]
    pixie = f["pixie"]
    weed = f["weed"]
    nut = f["nut"]
    return [
        QAItem(
            question=f"Who wanted the {nut.label} in {world.place}?",
            answer=f"{animal.label.capitalize()} wanted the {nut.label}."
        ),
        QAItem(
            question=f"What did the pixie do to the weed?",
            answer=f"{pixie.label} used a transformation spell and turned the weed into {weed.phrase}."
        ),
        QAItem(
            question="How did the animal and the pixie finish the story?",
            answer="They reconciled, worked together, and carried the nut away happily."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nut?",
            answer="A nut is a small hard seed or fruit with a shell, and many animals like to carry or eat them."
        ),
        QAItem(
            question="What is a weed?",
            answer="A weed is a plant that grows where people do not want it, so it can crowd out other plants."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when two friends stop being upset and make peace again."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together."
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a big change from one form into another."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(S). animal(A). pixie(P). weed(W). nut(N).
% transformed(W). reconciled(A,P). teamwork(A,P).
% at(S,A). at(S,P). at(S,W). at(S,N).

can_transform(P, W) :- pixie(P), weed(W), at(S, P), at(S, W), setting(S).
can_reconcile(A, P) :- animal(A), pixie(P), at(S, A), at(S, P), setting(S).
can_teamwork(A, P) :- can_reconcile(A, P).

valid_story(S, A, P, W, N) :-
    setting(S), animal(A), pixie(P), weed(W), nut(N),
    at(S, A), at(S, P), at(S, W), at(S, N),
    can_transform(P, W), can_reconcile(A, P), can_teamwork(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid in PIXIES:
        lines.append(asp.fact("pixie", pid))
    for wid in WEEDS:
        lines.append(asp.fact("weed", wid))
    for nid in NUTS:
        lines.append(asp.fact("nut", nid))
    for sid in SETTINGS:
        for aid in ANIMALS:
            lines.append(asp.fact("at", sid, aid))
        for pid in PIXIES:
            lines.append(asp.fact("at", sid, pid))
        for wid in WEEDS:
            lines.append(asp.fact("at", sid, wid))
        for nid in NUTS:
            lines.append(asp.fact("at", sid, nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Python gate is simply: everything in registries can make a valid story.
    py = {(s, a, p, w, n) for s in SETTINGS for a in ANIMALS for p in PIXIES for w in WEEDS for n in NUTS}
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:20])
    if py - cl:
        print("  only in python:", sorted(py - cl)[:20])
    return 1


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="garden", animal="squirrel", pixie="twig", weed="brambleweed", nut="hazelnut"),
    StoryParams(setting="orchard", animal="rabbit", pixie="miri", weed="thistleweed", nut="acorn"),
    StoryParams(setting="meadow", animal="mouse", pixie="luna", weed="vineweed", nut="walnut"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: nut, weed, pixie, transformation, reconciliation, teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--pixie", choices=PIXIES)
    ap.add_argument("--weed", choices=WEEDS)
    ap.add_argument("--nut", choices=NUTS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    pixie = args.pixie or rng.choice(list(PIXIES))
    weed = args.weed or rng.choice(list(WEEDS))
    nut = args.nut or rng.choice(list(NUTS))
    return StoryParams(setting=setting, animal=animal, pixie=pixie, weed=weed, nut=nut)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.form != "normal":
            bits.append(f"form={e.form}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories")
        for row in stories:
            print(row)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.animal} / {p.pixie} / {p.weed} / {p.nut}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
