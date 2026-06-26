#!/usr/bin/env python3
"""
A tiny ghost-story world about Shea and Mare, where a frightened haunting turns
into teamwork, transformation, and reconciliation.

The world is intentionally small and constraint-checked:
- a child and a ghost meet in a quiet setting,
- the ghost's shape can change when helped,
- the human and ghost must work together to solve the problem,
- the ending reconciles both sides so the final image proves what changed.
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
    kind: str = "thing"  # "character" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    forms: list[str] = field(default_factory=list)
    current_form: str = ""
    friendly: bool = False
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "shea"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "quiet"
    echoes: bool = True
    features: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _r_cold_spook(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "ghost":
            continue
        if ent.meters.get("cold", 0.0) < THRESHOLD:
            continue
        sig = ("spook", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
        out.append(f"The room shivered around {ent.label}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    shea = world.entities.get("Shea")
    mare = world.entities.get("Mare")
    if not shea or not mare:
        return out
    if shea.memes.get("helping", 0.0) < THRESHOLD:
        return out
    if mare.memes.get("trust", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shea.memes["teamwork"] = shea.memes.get("teamwork", 0.0) + 1
    mare.memes["teamwork"] = mare.memes.get("teamwork", 0.0) + 1
    out.append("They worked together instead of hiding from each other.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    mare = world.entities.get("Mare")
    if not mare:
        return out
    if mare.memes.get("trust", 0.0) < THRESHOLD:
        return out
    if mare.meters.get("cold", 0.0) < THRESHOLD:
        return out
    sig = ("transform", mare.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mare.current_form = "bright"
    mare.friendly = True
    mare.meters["cold"] = 0.0
    mare.meters["warm"] = mare.meters.get("warm", 0.0) + 1
    out.append("With a soft glow, Mare changed from a shivery ghost into a bright, kind shape.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    shea = world.entities.get("Shea")
    mare = world.entities.get("Mare")
    if not shea or not mare:
        return out
    if shea.memes.get("forgiveness", 0.0) < THRESHOLD:
        return out
    if mare.memes.get("apology", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shea.memes["peace"] = shea.memes.get("peace", 0.0) + 1
    mare.memes["peace"] = mare.memes.get("peace", 0.0) + 1
    out.append("The fear between them melted away, and the house felt less lonely.")
    return out


RULES = [_r_cold_spook, _r_teamwork, _r_transform, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, shea: Entity, mare: Entity) -> None:
    world.say(f"{shea.id} lived in {world.setting.place}, where the halls were quiet and the shadows looked long.")
    world.say(f"One chilly evening, {shea.id} heard a tiny voice in the dark, and that voice belonged to {mare.label}.")


def fright(world: World, shea: Entity, mare: Entity) -> None:
    shea.memes["fear"] = shea.memes.get("fear", 0.0) + 1
    mare.meters["cold"] = mare.meters.get("cold", 0.0) + 1
    world.say(f"{shea.id} wanted to run, because {mare.label} floated by the stairwell like a pale, shivering mist.")
    world.say(f"{mare.label} looked lost and cold, as if the house itself had forgotten how to welcome {mare.pronoun('object')}.")


def ask_help(world: World, shea: Entity, mare: Entity) -> None:
    shea.memes["helping"] = 1.0
    mare.memes["trust"] = mare.memes.get("trust", 0.0) + 1
    world.say(f"Instead of shouting, {shea.id} spoke gently and asked what was wrong.")
    world.say(f"{mare.label} whispered that the night made {mare.pronoun('object')} cold and lonely.")


def teamwork_plan(world: World, shea: Entity, mare: Entity) -> None:
    world.say(f"{shea.id} found a lantern, and {mare.label} pointed to a warm room under the roof.")
    world.say(f"Together they carried the light upstairs, one step at a time, like a small rescue team.")
    propagate(world)


def apology_and_change(world: World, shea: Entity, mare: Entity) -> None:
    mare.memes["apology"] = mare.memes.get("apology", 0.0) + 1
    shea.memes["forgiveness"] = shea.memes.get("forgiveness", 0.0) + 1
    propagate(world)
    world.say(f"{mare.label} apologized for scaring {shea.pronoun('object')}, and {shea.id} forgave {mare.pronoun('object')} right away.")
    world.say(f"After that, {mare.label} no longer drifted like a cold mist; {mare.pronoun('subject').capitalize()} shone softly, as if kindness had given {mare.pronoun('object')} a new shape.")


def ending(world: World, shea: Entity, mare: Entity) -> None:
    world.say(f"They finished the night together beside the lantern, with {shea.id} smiling and {mare.label} glowing bright and calm.")
    world.say(f"The old house still held its creaks, but now it sounded like a home with two friends inside.")


def tell(setting: Setting, shea_name: str = "Shea", mare_name: str = "Mare") -> World:
    world = World(setting)
    shea = world.add(Entity(id="Shea", kind="character", type="girl", label=shea_name, traits=["brave", "gentle"]))
    mare = world.add(Entity(id="Mare", kind="ghost", type="ghost", label=mare_name, traits=["cold", "lonely"], current_form="shivery"))

    introduce(world, shea, mare)
    world.para()
    fright(world, shea, mare)
    ask_help(world, shea, mare)
    world.para()
    teamwork_plan(world, shea, mare)
    world.para()
    apology_and_change(world, shea, mare)
    ending(world, shea, mare)

    world.facts.update(
        shea=shea,
        mare=mare,
        setting=setting,
        teamwork=bool(shea.memes.get("teamwork", 0.0) >= THRESHOLD and mare.memes.get("teamwork", 0.0) >= THRESHOLD),
        transformed=mare.current_form == "bright",
        reconciled=bool(shea.memes.get("peace", 0.0) >= THRESHOLD and mare.memes.get("peace", 0.0) >= THRESHOLD),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "house": Setting(place="the old house", mood="quiet", echoes=True, features={"stairs", "lantern"}),
    "attic": Setting(place="the attic", mood="dusty", echoes=True, features={"trunks", "moonlight"}),
    "hall": Setting(place="the long hall", mood="still", echoes=True, features={"doors", "whispers"}),
}

CURATED = [
    StoryParams(place="house", name="Shea", ghost_name="Mare"),
    StoryParams(place="attic", name="Shea", ghost_name="Mare"),
    StoryParams(place="hall", name="Shea", ghost_name="Mare"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for young children set in {f["setting"].place} with Shea and Mare.',
        "Tell a gentle haunted-house story where fear turns into teamwork and reconciliation.",
        "Write a child-friendly ghost story in which a ghost changes form after being helped by a brave child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shea: Entity = f["shea"]
    mare: Entity = f["mare"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who were the two main characters in the story?",
            answer=f"The story was about {shea.label}, a brave child, and {mare.label}, a lonely ghost in {setting.place}.",
        ),
        QAItem(
            question=f"What did {shea.label} do instead of running away?",
            answer=f"{shea.label} spoke gently, asked what was wrong, and stayed to help {mare.label} feel less cold.",
        ),
        QAItem(
            question=f"How did {mare.label} change by the end?",
            answer=f"{mare.label} changed from a shivery ghost into a bright, friendly shape after {shea.label} helped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is often a spooky character that can float, glow, or make a place feel haunted.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do something together.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and become friendly again.",
        ),
        QAItem(
            question="What can a transformation be in a story?",
            answer="A transformation is when something changes into a new form or becomes different in an important way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.kind == "ghost":
            bits.append(f"form={e.current_form}")
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_place/1.
#show valid_story/2.

valid_place(P) :- place(P), has_ghost(P), has_child(P), can_transform(P), can_reconcile(P).

valid_story(Child, Ghost) :- child(Child), ghost(Ghost), compatible(Child, Ghost).

can_transform(P) :- features(P, lantern), features(P, warm_room).
can_reconcile(P) :- features(P, lantern), features(P, safe_voice).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("has_ghost", pid))
        lines.append(asp.fact("has_child", pid))
        if "lantern" in setting.features:
            lines.append(asp.fact("features", pid, "lantern"))
        if "warm_room" in setting.features or pid == "house":
            lines.append(asp.fact("features", pid, "warm_room"))
        lines.append(asp.fact("features", pid, "safe_voice"))
    lines.append(asp.fact("child", "Shea"))
    lines.append(asp.fact("ghost", "Mare"))
    lines.append(asp.fact("compatible", "Shea", "Mare"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p,) for p in SETTINGS.keys())
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} places).")
        return 0
    print("MISMATCH:")
    print("  python only:", sorted(py - cl))
    print("  clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small ghost story world: Shea, Mare, transformation, teamwork, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", default="Shea")
    ap.add_argument("--ghost-name", default="Mare")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, name=args.name or "Shea", ghost_name=args.ghost_name or "Mare")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.ghost_name)
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

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible places:")
        for item in asp_valid_places():
            print(item)
        print("\nCompatible stories:")
        for item in asp_valid_stories():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            header = f"### {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
