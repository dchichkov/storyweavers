#!/usr/bin/env python3
"""
storyworlds/worlds/oppress_laryngitis_humor_bad_ending_heartwarming.py
======================================================================

A compact storyworld about a small voice, a too-tight feeling, and a warm,
funny attempt to help that does not fully succeed.

Seed-tale premise:
---
A child with a bright, silly voice loves telling jokes and singing little songs.
One windy morning, after shouting over a noisy game and wearing a scratchy scarf
too tight, the child's throat becomes sore and the voice turns raspy. A grown-up
worries that the throat is being oppressed by all the strain and says the child
needs quiet, honey, and rest. The child tries to talk anyway, but only a croaky
squeak comes out. Friends misunderstand the croak, laugh kindly, and then help
by playing a quiet game and bringing tea. The voice improves a little, but the
big talent-show song is missed, so the ending is gentle and sad instead of fixed.

World design:
---
- Physical meters: throat strain, dryness, warmth, noise, rest, steam, and scarf
  tightness.
- Emotional memes: cheer, worry, embarrassment, humor, tenderness, longing.
- Causal state drives prose: noisy jokes and a tight scarf worsen the throat;
  warm drinks and quiet help; laryngitis keeps the child from singing clearly.
- The story always contains a clear turn and a final image, but the final image
  is a bad ending: the performance is missed even though everyone is kind.
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
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

NAME_POOL = [
    "Milo", "Lena", "Pippa", "Jules", "Nina", "Owen", "Toby", "Ivy", "Rory",
    "Mira",
]

HELPERS = ["mother", "father", "grandma", "grandpa", "older sister", "older brother"]
SETTINGS = ["kitchen", "living room", "school hall", "bedroom", "porch"]
NOISE_SOURCES = ["a loud game", "a chant", "a buzzy crowd", "a toy trumpet"]
SOOTHERS = ["honey tea", "warm water", "quiet rest", "a soft blanket", "steam"]
JOKES = [
    "a squeaky duck joke",
    "a tiny frog joke",
    "a banana peel joke",
    "a wobbling hat joke",
]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["strain", "dryness", "warmth", "noise", "rest", "steam", "tightness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["cheer", "worry", "embarrassment", "humor", "tenderness", "longing"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandma", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandpa", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass(frozen=True)
class StoryParams:
    setting: str
    name: str
    helper: str
    noise: str
    soothe: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_params(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.helper in HELPERS


def explain_invalid(reason: str) -> str:
    return f"(No story: {reason})"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not valid_params(params):
        raise StoryError(explain_invalid("the chosen setting or helper is not available"))

    world = World(setting=params.setting)
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper))
    scarf = world.add(
        Entity(
            id="Scarf",
            type="scarf",
            label="scarf",
            phrase="a scratchy scarf",
            owner=child.id,
            worn_by=child.id,
        )
    )
    teacup = world.add(
        Entity(
            id="Tea",
            type="tea",
            label="tea",
            phrase=f"a mug of {params.soothe}",
            caretaker=helper.id,
        )
    )
    stage = world.add(Entity(id="Stage", type="stage", label="little stage"))

    # Setup
    child.memes["cheer"] += 1
    world.say(
        f"{child.id} loved telling jokes and singing in {world.setting}."
    )
    world.say(
        f"{child.pronoun().capitalize()} had a favorite {random.choice(JOKES)} that could make even a quiet room smile."
    )
    world.say(
        f"One morning, {child.id} wore {scarf.phrase} while the room buzzed with {params.noise}."
    )

    # Conflict: noisy strain and tight scarf cause laryngitis
    world.para()
    child.meters["noise"] += 1.0
    child.meters["tightness"] += 1.0
    child.memes["humor"] += 1.0
    world.say(
        f"{child.id} kept joking over the noise, and the scarf hugged {child.pronoun('possessive')} throat too hard."
    )
    world.say(
        f"The helper frowned kindly and said the throat was being oppressed by all that strain."
    )
    child.meters["strain"] += 2.0
    child.meters["dryness"] += 1.0
    child.memes["worry"] += 1.0
    child.memes["embarrassment"] += 1.0
    world.facts["laryngitis"] = True
    world.facts["oppress"] = True
    world.say(
        f"By afternoon, {child.id} had laryngitis, and every word came out as a tiny croak."
    )

    # Attempted fix
    world.para()
    helper.memes["tenderness"] += 1.0
    child.memes["longing"] += 1.0
    world.say(
        f"{helper.id} brought {params.soothe} and told {child.id} to rest, sip slowly, and keep the voice warm."
    )
    world.say(
        f"{child.id} tried to answer with a joke, but only a squeak hopped out."
    )

    # Bad ending: the performance is missed, though care remains.
    world.para()
    world.say(
        f"At the school hall, the little stage waited, but {child.id} could not sing the big song."
    )
    world.say(
        f"{helper.id} held {child.pronoun('possessive')} hand while friends listened to the croaky laugh and smiled anyway."
    )
    world.say(
        f"The evening ended with tea, a blanket, and a missed show; the throat was still sore, even if the room felt warm."
    )

    world.facts.update(
        child=child,
        helper=helper,
        scarf=scarf,
        tea=teacup,
        stage=stage,
        params=params,
        ending="bad",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.replace(" ", "_")))
    return "\n".join(lines)


ASP_RULES = r"""
setting_ok(S) :- setting(S).
helper_ok(H) :- helper(H).
valid_story(S,H) :- setting_ok(S), helper_ok(H).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a heartwarming but sad story for a young child about "{p.name}" getting laryngitis after too much noise.',
        f"Tell a gentle, funny story where a helper notices that {p.name}'s throat is oppressed by strain and brings {p.soothe}.",
        f"Write a short story in {p.setting} with a croaky voice, a kind helper, and a missed song at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]
    h: Entity = f["helper"]
    p: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Why did {c.id} start sounding croaky?",
            answer=(
                f"{c.id} kept joking through {p.noise}, and the scratchy scarf pressed too hard on the throat. "
                f"That strain gave {c.id} laryngitis, so the voice turned raspy."
            ),
        ),
        QAItem(
            question=f"What did {h.id} bring to help {c.id} feel better?",
            answer=f"{h.id} brought {p.soothe} and told {c.id} to rest and keep warm.",
        ),
        QAItem(
            question=f"What happened at the school hall in the end?",
            answer=(
                f"The big song was missed because {c.id} still had laryngitis. "
                f"Everyone stayed kind, but the ending was sad because the stage waited and the voice could not perform."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is laryngitis?",
            answer="Laryngitis is when the voice box gets sore or swollen, so a person may sound hoarse, whispery, or croaky.",
        ),
        QAItem(
            question="What does it mean when something is oppressed?",
            answer="If something is oppressed, it is pressed down or held under a hard weight or pressure, so it cannot feel free.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {q}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tracing
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(SETTINGS)
    helper = args.helper or rng.choice(HELPERS)
    name = args.name or rng.choice(NAME_POOL)
    noise = args.noise or rng.choice(NOISE_SOURCES)
    soothe = args.soothe or rng.choice(SOOTHERS)
    params = StoryParams(setting=setting, name=name, helper=helper, noise=noise, soothe=soothe)
    if not valid_params(params):
        raise StoryError(explain_invalid("the requested options do not make a reasonable story"))
    return params


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A warm, funny storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--noise", choices=NOISE_SOURCES)
    ap.add_argument("--soothe", choices=SOOTHERS)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    facts = set(asp.atoms(model, "valid_story"))
    python = {(s, h.replace(" ", "_")) for s in SETTINGS for h in HELPERS}
    if facts == python:
        print(f"OK: clingo gate matches python gate ({len(facts)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


CURATED = [
    StoryParams(setting="kitchen", name="Milo", helper="mother", noise="a loud game", soothe="honey tea"),
    StoryParams(setting="school hall", name="Lena", helper="grandma", noise="a buzzy crowd", soothe="quiet rest"),
    StoryParams(setting="living room", name="Pippa", helper="older sister", noise="a toy trumpet", soothe="warm water"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
