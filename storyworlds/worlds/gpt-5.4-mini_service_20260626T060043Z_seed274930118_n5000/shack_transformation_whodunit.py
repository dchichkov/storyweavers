#!/usr/bin/env python3
"""
shack_transformation_whodunit.py
================================

A small whodunit storyworld set around a shack where a surprising
transformation reveals who caused the trouble.

Premise:
- A small cast gathers at or near a shack.
- Something valuable or important goes missing, breaks, or changes.
- One character performs a transformation that creates a clue.
- The detective-like resolution explains the change and identifies the culprit.

The world model tracks:
- physical state in meters (location, disguise, evidence, transformation level)
- emotional state in memes (fear, suspicion, relief, pride)

The stories are designed to read like short child-facing whodunits:
a clue-heavy beginning, a tense middle, and a clear reveal at the end.
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
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    place: str
    detail: str
    clue_noun: str
    atmosphere: str


@dataclass(frozen=True)
class CharacterSpec:
    role: str
    name: str
    type: str
    trait: str


@dataclass(frozen=True)
class ObjectSpec:
    label: str
    clue: str
    owner_role: str
    value_word: str


@dataclass(frozen=True)
class TransformationSpec:
    id: str
    kind: str
    source_form: str
    result_form: str
    telltale: str
    effect: str
    clue_word: str


SETTINGS = {
    "shack": Setting(
        place="the old shack",
        detail="The shack stood at the edge of the lane, with a sagging roof and a squeaky door.",
        clue_noun="floorboards",
        atmosphere="quiet and creaky",
    ),
    "garden_shack": Setting(
        place="the garden shack",
        detail="The garden shack sat behind the hedges, and its little window was dusty and dark.",
        clue_noun="window",
        atmosphere="still and secret",
    ),
    "beach_shack": Setting(
        place="the beach shack",
        detail="The beach shack sat beside the dunes, where the wind could whisper under the door.",
        clue_noun="sand",
        atmosphere="windy and pale",
    ),
}

CHARACTER_POOL = [
    CharacterSpec("detective", "Mara", "girl", "curious"),
    CharacterSpec("detective", "Theo", "boy", "careful"),
    CharacterSpec("helper", "Pip", "fox", "quick"),
    CharacterSpec("helper", "Nina", "girl", "gentle"),
    CharacterSpec("suspect", "Uncle Ben", "man", "busy"),
    CharacterSpec("suspect", "Aunt Lila", "woman", "smiling"),
    CharacterSpec("suspect", "Jules", "boy", "shy"),
]

OBJECTS = {
    "lantern": ObjectSpec("lantern", "a bright lantern", "owner", "important"),
    "blue_scarf": ObjectSpec("blue scarf", "a soft blue scarf", "owner", "special"),
    "key": ObjectSpec("key", "a small brass key", "owner", "important"),
    "cookie_tin": ObjectSpec("cookie tin", "a round cookie tin", "owner", "precious"),
}

TRANSFORMATIONS = {
    "moth": TransformationSpec(
        id="moth",
        kind="moth",
        source_form="a dusty moth",
        result_form="a little girl in a gray cape",
        telltale="gray powder on the windowsill",
        effect="fluttered in through the crack and brushed the shelf with dusty wings",
        clue_word="moth",
    ),
    "cat": TransformationSpec(
        id="cat",
        kind="cat",
        source_form="a sleepy cat",
        result_form="a tall boy with a striped coat",
        telltale="a paw print in flour",
        effect="slipped past the chair and left a neat print near the crumbs",
        clue_word="cat",
    ),
    "bird": TransformationSpec(
        id="bird",
        kind="bird",
        source_form="a small brown bird",
        result_form="a tiny baby with a feather cap",
        telltale="a feather on the doormat",
        effect="hopped from beam to beam and dropped a feather beside the door",
        clue_word="bird",
    ),
}

MOTIVES = [
    "wanted the shiny thing for a game",
    "meant to hide a surprise",
    "was trying to fix a mistake",
    "did not want anyone to see the truth",
]

TRAITS = ["curious", "careful", "bright", "quiet", "brave", "gentle"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    disguise: str = ""
    transformed_from: str = ""
    transformed_to: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    characters: dict[str, Entity] = field(default_factory=dict)
    objects: dict[str, Entity] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)
    reveal: str = ""
    culprit: str = ""
    transformation: TransformationSpec = None  # type: ignore[assignment]
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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    detective: str
    helper: str
    suspect: str
    object: str
    transformation: str
    motive: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit storyworld set around a shack with a transformation clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--motive", choices=range(len(MOTIVES)), type=int)
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


def choose(rng: random.Random, items):
    return items[rng.randrange(len(items))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or choose(rng, list(SETTINGS))
    detective = args.detective or choose(rng, [c.name for c in CHARACTER_POOL if c.role == "detective"])
    helper = args.helper or choose(rng, [c.name for c in CHARACTER_POOL if c.role == "helper"])
    suspect = args.suspect or choose(rng, [c.name for c in CHARACTER_POOL if c.role == "suspect"])
    obj = args.object_ or choose(rng, list(OBJECTS))
    trans = args.transformation or choose(rng, list(TRANSFORMATIONS))
    motive = MOTIVES[args.motive] if args.motive is not None else choose(rng, MOTIVES)

    if detective == suspect or helper == suspect:
        raise StoryError("The detective, helper, and suspect must be different people.")
    if obj == "lantern" and trans == "cat":
        # Reasonableness gate: cat clue should not explain a lantern move by itself.
        raise StoryError("A cat transformation is not a good fit for a lantern mystery here.")

    return StoryParams(
        setting=setting,
        detective=detective,
        helper=helper,
        suspect=suspect,
        object=obj,
        transformation=trans,
        motive=motive,
    )


def _person_entity(name: str, role: str, trait: str) -> Entity:
    spec = next(c for c in CHARACTER_POOL if c.name == name and c.role == role)
    return Entity(
        id=name,
        kind="character",
        label=name,
        type=spec.type,
        location="",
        meters={"presence": 1.0},
        memes={"curious": 1.0 if role == "detective" else 0.2, "fear": 0.0},
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting=setting)
    detective_trait = next(c.trait for c in CHARACTER_POOL if c.name == params.detective and c.role == "detective")
    helper_trait = next(c.trait for c in CHARACTER_POOL if c.name == params.helper and c.role == "helper")
    suspect_trait = next(c.trait for c in CHARACTER_POOL if c.name == params.suspect and c.role == "suspect")
    world.characters[params.detective] = Entity(params.detective, "character", params.detective, "girl" if params.detective in {"Mara", "Nina"} else "boy", location=setting.place, meters={"presence": 1.0}, memes={"curious": 1.5, "suspicion": 0.0})
    world.characters[params.helper] = Entity(params.helper, "character", params.helper, "fox" if params.helper == "Pip" else "girl", location=setting.place, meters={"presence": 1.0}, memes={"helpfulness": 1.2})
    world.characters[params.suspect] = Entity(params.suspect, "character", params.suspect, "man" if "Ben" in params.suspect else ("woman" if "Lila" in params.suspect else "boy"), location=setting.place, meters={"presence": 1.0}, memes={"nervousness": 0.8, "secret": 1.0})

    obj = OBJECTS[params.object]
    world.objects[obj.label] = Entity(
        id=obj.label,
        kind="object",
        label=obj.label,
        owner=params.suspect,
        location=setting.place,
        meters={"whole": 1.0},
        memes={"value": 1.0},
    )

    trans = TRANSFORMATIONS[params.transformation]
    world.transformation = trans
    world.culprit = params.suspect

    world.facts = {
        "setting": setting,
        "detective": params.detective,
        "helper": params.helper,
        "suspect": params.suspect,
        "object": obj,
        "transformation": trans,
        "motive": params.motive,
        "detective_trait": detective_trait,
        "helper_trait": helper_trait,
        "suspect_trait": suspect_trait,
    }
    return world


def apply_transformation(world: World) -> None:
    t = world.transformation
    suspect = world.characters[world.culprit]
    suspect.meters["disguise"] = 1.0
    suspect.meters["transformation"] = 1.0
    suspect.disguise = t.result_form
    world.clues.append(t.telltale)
    world.say(
        f"In the dim light, someone near the shack had changed into {t.result_form}, "
        f"and {t.effect}."
    )


def story_intro(world: World) -> None:
    f = world.facts
    setting = f["setting"]
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    obj = f["object"]

    world.say(setting.detail)
    world.say(
        f"{detective} came to the shack with {helper}, because {obj.label} had gone missing."
    )
    world.say(
        f"Everyone wanted to know who had taken it, and {detective} noticed how quiet the place had become."
    )
    world.para()
    world.say(
        f"{suspect} stood nearby, looking worried, and said {f['motive']}."
    )


def story_middle(world: World) -> None:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    obj = f["object"]
    t = f["transformation"]

    world.say(
        f"{detective} bent down and studied the {world.setting.clue_noun}, while {helper} sniffed the air."
    )
    world.say(
        f"Then they found a clue: {t.telltale}."
    )
    world.say(
        f"That clue matched the strange change they had seen near the shack, where {t.source_form} had become {t.result_form}."
    )
    world.say(
        f"{detective} asked {suspect} a careful question about the {obj.label}, and {suspect} looked even more nervous."
    )


def story_reveal(world: World) -> None:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    obj = f["object"]
    t = f["transformation"]

    world.para()
    world.say(
        f"At last, {detective} put the pieces together: the transformation was the clue."
    )
    world.say(
        f"{suspect} had used the disguise to hide the truth, but the {t.clue_word} clue gave them away."
    )
    world.say(
        f"When {helper} opened the hiding spot, there was {obj.label} all along."
    )
    world.say(
        f"{suspect} confessed, and the shack felt less spooky at once."
    )
    world.say(
        f"By the end, {detective} had solved the mystery, {helper} was pleased, and {obj.label} was back where it belonged."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    apply_transformation(world)
    story_middle(world)
    story_reveal(world)
    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit story for young children set at {f['setting'].place} where a transformation helps solve a mystery.",
        f"Tell a gentle detective story in a shack with {f['object'].label} missing and a clue caused by {f['transformation'].kind}.",
        f"Write a simple mystery where {f['detective']} notices a clue, asks careful questions, and discovers who hid the {f['object'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What went missing near {f['setting'].place}?",
            answer=f"{f['object'].label.capitalize()} went missing near {f['setting'].place}, which is why {f['detective']} started looking for clues.",
        ),
        QAItem(
            question=f"What clue helped {f['detective']} solve the mystery?",
            answer=f"The clue was {f['transformation'].telltale}, and it matched the transformation seen near the shack.",
        ),
        QAItem(
            question=f"Who was the mystery solved by the end?",
            answer=f"{f['detective']} solved the mystery with help from {f['helper']}, and {f['suspect']} was the one hiding the truth.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shack?",
            answer="A shack is a small, simple building, often old and a little creaky.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a problem or mystery.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing from one form or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is valid when the suspect, detective, helper, object, and
% transformation are all distinct enough to make a clear whodunit.
valid_story(S, D, H, O, T) :- setting(S), detective(D), helper(H), object(O), transformation(T),
                              D != H, D != O, H != O.

% The transformation clue must be relevant to the shack setting.
clue_relevant(T) :- transformation(T), clue(T, _).

valid_world(S, D, H, O, T) :- valid_story(S, D, H, O, T), clue_relevant(T).
#show valid_story/5.
#show valid_world/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for name in {c.name for c in CHARACTER_POOL}:
        lines.append(asp.fact("person", name))
    for role in ("detective", "helper", "suspect"):
        for c in CHARACTER_POOL:
            if c.role == role:
                lines.append(asp.fact(role, c.name))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("clue", oid, o.clue))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("clue", tid, t.telltale))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_world/5."))
    return sorted(set(asp.atoms(model, "valid_world")))


def asp_verify() -> int:
    py = {
        (s, d, h, o, t)
        for s in SETTINGS
        for d in [c.name for c in CHARACTER_POOL if c.role == "detective"]
        for h in [c.name for c in CHARACTER_POOL if c.role == "helper"]
        for o in OBJECTS
        for t in TRANSFORMATIONS
        if d != h and d != o and h != o
    }
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP parity verified ({len(py)} combinations).")
        return 0
    print("MISMATCH between Python and ASP.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.characters.values():
        lines.append(
            f"{c.id}: kind={c.kind} type={c.type} location={c.location} meters={c.meters} memes={c.memes} disguise={c.disguise}"
        )
    for o in world.objects.values():
        lines.append(
            f"{o.id}: kind={o.kind} owner={o.owner} location={o.location} meters={o.meters} memes={o.memes}"
        )
    lines.append(f"clues={world.clues}")
    lines.append(f"culprit={world.culprit}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="shack", detective="Mara", helper="Pip", suspect="Uncle Ben", object="key", transformation="moth", motive=MOTIVES[0]),
    StoryParams(setting="garden_shack", detective="Theo", helper="Nina", suspect="Aunt Lila", object="cookie_tin", transformation="cat", motive=MOTIVES[1]),
    StoryParams(setting="beach_shack", detective="Mara", helper="Pip", suspect="Jules", object="lantern", transformation="bird", motive=MOTIVES[2]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid(), indent=2))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
