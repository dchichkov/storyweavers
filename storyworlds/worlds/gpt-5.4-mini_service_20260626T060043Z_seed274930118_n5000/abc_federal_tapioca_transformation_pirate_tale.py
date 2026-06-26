#!/usr/bin/env python3
"""
A standalone Storyweavers world: a small pirate-tale domain with a surprising
transformation, seeded by the words abc, federal, and tapioca.

The story premise:
- A young pirate on a small ship wants to keep a secret chart.
- A federal inspector arrives with an order.
- A bowl of tapioca is used in a clever plan that transforms the scene.
- The ending proves what changed.

The script keeps the world small and constraint-driven so every generated story
has a clear setup, a turn, and a resolution.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little pirate ship"
    on_water: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    topic: str
    fragile: bool = False


@dataclass
class Transform:
    id: str
    from_label: str
    to_label: str
    cue: str
    result: str
    method: str
    topic: str = "transformation"


@dataclass
class StoryParams:
    place: str
    artifact: str
    transform: str
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": Setting(place="the little pirate ship", on_water=True, affords={"sail", "hide", "stir"}),
    "dock": Setting(place="the dock by the harbor", on_water=False, affords={"hide", "stir"}),
    "cove": Setting(place="the quiet cove", on_water=True, affords={"sail", "hide", "stir"}),
}

ARTIFACTS = {
    "abc_chart": Artifact(
        id="abc_chart",
        label="ABC chart",
        phrase="a creaky ABC chart with painted letters",
        type="chart",
        topic="abc",
    ),
    "federal_seal": Artifact(
        id="federal_seal",
        label="federal seal",
        phrase="a shiny federal seal on a brass box",
        type="seal",
        topic="federal",
    ),
    "tapioca_bowl": Artifact(
        id="tapioca_bowl",
        label="bowl of tapioca",
        phrase="a warm bowl of tapioca pudding",
        type="bowl",
        topic="tapioca",
        fragile=False,
    ),
}

TRANSFORMS = {
    "ink_shift": Transform(
        id="ink_shift",
        from_label="letters",
        to_label="sea marks",
        cue="stirs the pudding over the page",
        result="the letters blur and become a secret treasure clue",
        method="a slow swirl of tapioca",
        topic="transformation",
    ),
    "badge_change": Transform(
        id="badge_change",
        from_label="seal",
        to_label="captain's token",
        cue="presses the pudding against the brass",
        result="the federal seal turns into a bright captain's token",
        method="a sticky tap of tapioca",
        topic="federal",
    ),
    "map_glow": Transform(
        id="map_glow",
        from_label="plain paper",
        to_label="golden map",
        cue="spills the pudding across the chart",
        result="the chart changes into a glowing map that points to safe water",
        method="a sweet slide of tapioca",
        topic="abc",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ruby", "Tess", "Ivy"]
BOY_NAMES = ["Finn", "Jory", "Milo", "Pax", "Rowan", "Tobin"]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for artifact_id, art in ARTIFACTS.items():
            if artifact_id == "tapioca_bowl" and "stir" in setting.affords:
                for tx in TRANSFORMS:
                    out.append((place, artifact_id, tx))
    return out


def explain_rejection(place: str, artifact_id: str, transform_id: str) -> str:
    return (
        f"(No story: {artifact_id} at {place} cannot reasonably support "
        f"{transform_id}. The pirate tale needs a tactile transformation on a small ship, dock, or cove.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def choose_artifact(rng: random.Random, artifact_id: Optional[str]) -> Artifact:
    if artifact_id is None:
        artifact_id = rng.choice(list(ARTIFACTS))
    return ARTIFACTS[artifact_id]


def choose_transform(rng: random.Random, transform_id: Optional[str]) -> Transform:
    if transform_id is None:
        transform_id = rng.choice(list(TRANSFORMS))
    return TRANSFORMS[transform_id]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="Captain Brine"))
    artifact = world.add(Entity(
        id=params.artifact,
        type=ARTIFACTS[params.artifact].type,
        label=ARTIFACTS[params.artifact].label,
        phrase=ARTIFACTS[params.artifact].phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, captain=captain, artifact=artifact)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero: Entity = world.facts["hero"]
    captain: Entity = world.facts["captain"]
    artifact: Entity = world.facts["artifact"]
    art = ARTIFACTS[params.artifact]
    tx = TRANSFORMS[params.transform]

    world.say(
        f"On {world.setting.place}, {hero.id} the little pirate loved the old {art.label}."
    )
    world.say(
        f"The chart had the seed word abc tucked in its corner, and {hero.id} could read the first three marks with a grin."
    )
    world.say(
        f"One gray morning, {captain.label} brought a federal notice and warned that the ship must be checked before sunset."
    )
    world.say(
        f"{hero.id} did not want the crew to lose the {art.label}, so {hero.pronoun('subject')} hid it beside {world.setting.place}."
    )
    world.say(
        f"Then {hero.id} found a bowl of tapioca and remembered a clever old trick."
    )
    world.say(
        f"{hero.id} {tx.cue}, and {tx.result}."
    )
    if params.transform == "map_glow":
        artifact.transformed = True
        artifact.label = "glowing map"
    elif params.transform == "badge_change":
        artifact.transformed = True
        artifact.label = "captain's token"
    else:
        artifact.transformed = True
        artifact.label = "secret treasure clue"
    world.say(
        f"In the end, the federal inspector smiled, because the new thing was useful, safe, and full of pirate sense."
    )
    world.say(
        f"{hero.id} sailed on with the transformed treasure tucked close, and the salty wind felt kind."
    )
    world.facts["transformed_label"] = artifact.label
    world.facts["transform"] = tx


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        'Write a short pirate tale for a child that includes the words "abc", "federal", and "tapioca".',
        f"Tell a story where {hero.id} and a federal inspector deal with a small ship problem by using tapioca.",
        "Write a gentle transformation story about a pirate, a secret chart, and a clever pudding trick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    artifact: Entity = f["artifact"]
    tx: Transform = f["transform"]
    return [
        QAItem(
            question=f"Who used the tapioca to change the {ARTIFACTS[artifact.id].label}?",
            answer=f"{hero.id} used the tapioca on the {ARTIFACTS[artifact.id].label}, and that changed the story's important object.",
        ),
        QAItem(
            question="Why did the federal inspector matter in the story?",
            answer="The federal inspector brought the warning that made the pirate find a safer and smarter plan.",
        ),
        QAItem(
            question=f"What did the transformation turn the {ARTIFACTS[artifact.id].label} into?",
            answer=f"It became {world.facts['transformed_label']}. The change was caused by {tx.method}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tapioca?",
            answer="Tapioca is a soft, pudding-like food made from starch, and it can be spooned or stirred.",
        ),
        QAItem(
            question="What does federal mean?",
            answer="Federal means it belongs to the national government, not just to one small town or ship.",
        ),
        QAItem(
            question="What does a transformation do in a story?",
            answer="A transformation changes one thing into another, so the world ends in a new state.",
        ),
        QAItem(
            question="What is an ABC chart for?",
            answer="An ABC chart can help someone learn letters in order, from A to B to C.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the setting supports the tapioca trick and the chosen
% transformation matches the small pirate tale domain.
valid_story(P, A, T) :- place(P), artifact(A), transform(T),
                        supports(P, A), supports_transform(A, T).

% The artifact must be something the hero can protect, and tapioca must be part
% of the method.
supports(P, abc_chart) :- place(P).
supports(P, federal_seal) :- place(P).
supports(P, tapioca_bowl) :- place(P).

supports_transform(abc_chart, map_glow).
supports_transform(abc_chart, ink_shift).
supports_transform(federal_seal, badge_change).
supports_transform(tapioca_bowl, ink_shift).
supports_transform(tapioca_bowl, map_glow).
supports_transform(tapioca_bowl, badge_change).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with a tapioca transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["pirate"], default="pirate")
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
    if args.place and args.artifact and args.transform:
        if (args.place, args.artifact, args.transform) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.artifact, args.transform))
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.artifact is None or c[1] == args.artifact)
        and (args.transform is None or c[2] == args.transform)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, artifact, transform = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        artifact=artifact,
        transform=transform,
        name=name,
        gender=gender,
        role=args.role,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="ship", artifact="abc_chart", transform="map_glow", name="Mina", gender="girl", role="pirate"),
    StoryParams(place="dock", artifact="federal_seal", transform="badge_change", name="Finn", gender="boy", role="pirate"),
    StoryParams(place="cove", artifact="tapioca_bowl", transform="ink_shift", name="Ruby", gender="girl", role="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            p = sample.params
            header = f"### {p.name}: {p.artifact} at {p.place} via {p.transform}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
