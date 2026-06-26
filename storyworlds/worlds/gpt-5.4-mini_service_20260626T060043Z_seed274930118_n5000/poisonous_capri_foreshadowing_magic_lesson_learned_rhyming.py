#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/poisonous_capri_foreshadowing_magic_lesson_learned_rhyming.py
==================================================================================================

A small rhyming storyworld about a child on Capri, a hint of poisonous danger,
and a magical lesson learned in a gentle, child-facing tale.

Premise:
- A curious child visits Capri with a bright basket and a magic shell.
- A foreshadowed warning appears early: a shiny berry is poisonous.
- Magic helps reveal the safe path.
- The child learns a lesson about listening, looking, and asking before tasting.

The world is intentionally tiny and state-driven:
- physical meters track freshness, shine, and danger exposure
- emotional memes track worry, wonder, and wisdom
- the prose is assembled from simulation state, not from a frozen template

The style aims for a simple rhyming story with light repetition and an ending
that proves the world changed.
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
# Core data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched_by: Optional[str] = None
    carried_by: Optional[str] = None
    poisonous: bool = False
    safe: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("shine", "fresh", "danger", "taste"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "wonder", "joy", "wisdom", "fear"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "Capri"
    sunny: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    protagonist: str
    gender: str
    guide: str
    item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "capri": Setting(place="Capri", sunny=True, affords={"magic"}),
}

PROTAGONISTS = {
    "girl": ["Mina", "Lina", "Tia", "Nora"],
    "boy": ["Theo", "Milo", "Arlo", "Finn"],
}

GUIDES = {
    "grandma": ("grandma", "wise grandma"),
    "uncle": ("uncle", "cheerful uncle"),
}

ITEMS = {
    "berries": {
        "label": "berries",
        "phrase": "bright little berries",
        "poisonous": True,
        "safe_alt": "golden apricots",
    },
}

THRESHOLD = 1.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def foreshadow_warning(world: World, child: Entity, fruit: Entity) -> None:
    if fruit.poisonous and "warned" not in world.fired:
        world.fired.add(("warned", fruit.id))
        child.memes["worry"] += 1
        world.say(
            f"On Capri so bright, by the sea and the foam, "
            f"a shell gave a shimmer like light from home. "
            f"Then grandma said softly, with eyes kind and keen, "
            f'"That berry looks pretty, but don\'t taste the green."'
        )
        world.say(
            f"The warning was early, a whisper of care, "
            f"a little foreshadow of trouble in air."
        )


def magic_reveal(world: World, guide: Entity, child: Entity, fruit: Entity) -> None:
    if "revealed" in world.fired:
        return
    world.fired.add(("revealed", fruit.id))
    child.memes["wonder"] += 1
    fruit.meters["shine"] += 1
    world.say(
        f"Then magic did twinkle, like sparkles that sing; "
        f"{guide.label} waved a wand with a silver ring. "
        f"A glow on the berries grew brighter than dawn, "
        f"and a blue little warning-bell rang along."
    )
    world.say(
        f"The spell did not hurt them; it simply made plain "
        f"that danger can hide in a sweet-looking stain."
    )


def choose_safe_path(world: World, child: Entity, guide: Entity, fruit: Entity, snack: Entity) -> None:
    if "chosen" in world.fired:
        return
    world.fired.add(("chosen", fruit.id))
    child.memes["wisdom"] += 1
    child.memes["joy"] += 1
    fruit.meters["danger"] += 1
    snack.meters["fresh"] += 1
    world.say(
        f"{child.label} took a deep breath and looked once again, "
        f"and chose the safe snack instead of the bane. "
        f"{guide.label} smiled, and the lesson was clear: "
        f"first ask, then look, then taste without fear."
    )


def lesson_learned(world: World, child: Entity) -> None:
    if child.memes["wisdom"] >= THRESHOLD:
        world.say(
            f"So on Capri that evening, the child learned to say, "
            f"\"If it is unknown, I will ask first today.\" "
            f"The moon on the water was soft as a rhyme, "
            f"and safe little choices grew sweeter with time."
        )


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    child_name = params.protagonist
    child_type = params.gender
    guide_id, guide_label = GUIDES[params.guide]

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
    ))
    guide = world.add(Entity(
        id=guide_id,
        kind="character",
        type=guide_id,
        label=guide_label,
    ))
    fruit = world.add(Entity(
        id="berries",
        type="berries",
        label="berries",
        phrase=ITEMS["berries"]["phrase"],
        poisonous=True,
        safe=False,
        owner=None,
    ))
    snack = world.add(Entity(
        id="apricots",
        type="snack",
        label="apricots",
        phrase="golden apricots",
        poisonous=False,
        safe=True,
    ))

    world.say(
        f"On Capri, {child.label} went strolling by the sea, "
        f"with {guide.label} beside {child.pronoun('object')} in a songful spree."
    )
    world.say(
        f"The basket was little, the sky was blue, "
        f"and every bright wave said, \"Adventure for you!\""
    )

    world.para()
    foreshadow_warning(world, child, fruit)
    world.say(
        f"{child.label} spotted the berries, so shiny, so neat, "
        f"but remembered the warning before taking a treat."
    )

    world.para()
    magic_reveal(world, guide, child, fruit)
    choose_safe_path(world, guide, child, fruit, snack)

    world.para()
    lesson_learned(world, child)

    world.facts = {
        "child": child,
        "guide": guide,
        "fruit": fruit,
        "snack": snack,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    fruit = f["fruit"]
    return [
        "Write a short rhyming story for a young child about a warning, a magic glow, and a safe choice on Capri.",
        f"Tell a gentle poem-story where {child.label} is tempted by poisonous berries but listens to {guide.label}.",
        "Create a simple story with foreshadowing, magic, and a lesson learned about not tasting unknown fruit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    fruit = f["fruit"]
    snack = f["snack"]
    return [
        QAItem(
            question=f"Why did {child.label} decide not to eat the berries?",
            answer=f"{child.label} did not eat them because {guide.label} warned that the berries were poisonous, and the magic glow made the danger easy to notice.",
        ),
        QAItem(
            question=f"What did the magic help {child.label} understand?",
            answer=f"The magic helped {child.label} understand that something can look shiny and sweet but still be unsafe.",
        ),
        QAItem(
            question=f"What safe food did {child.label} choose instead?",
            answer=f"{child.label} chose the golden apricots instead of the poisonous berries.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does poisonous mean?",
            answer="Poisonous means something can make a person sick if they eat it or touch it the wrong way.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a little hint early in the story that helps readers guess something important will happen later.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone understands after something happens, so they can make a better choice next time.",
        ),
        QAItem(
            question="What is Capri?",
            answer="Capri is a sunny island place by the sea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
% A berry is dangerous if it is poisonous.
dangerous(F) :- fruit(F), poisonous(F).

% A warning should be shown when dangerous fruit is present.
warn(F) :- dangerous(F).

% Magic reveals the hidden danger.
revealed(F) :- dangerous(F), magic.
safe_choice(F) :- warned(F), revealed(F), not eaten(F).

#show warn/1.
#show revealed/1.
#show safe_choice/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        if SETTINGS[pid].sunny:
            lines.append(asp.fact("sunny", pid))
        for a in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("fruit", "berries"))
    lines.append(asp.fact("poisonous", "berries"))
    lines.append(asp.fact("magic"))
    lines.append(asp.fact("warned", "berries"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warn/1.\n#show revealed/1.\n#show safe_choice/1."))
    atoms = set(asp.atoms(model, "warn")) | set(asp.atoms(model, "revealed")) | set(asp.atoms(model, "safe_choice"))
    expected = {("berries",)}
    if atoms == expected:
        print("OK: ASP rules produce the expected warning/reveal/safe-choice structure.")
        return 0
    print("MISMATCH in ASP verification:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about Capri, poisonous berries, magic, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--protagonist")
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--item", choices=ITEMS)
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
    place = args.place or "capri"
    if place != "capri":
        raise StoryError("This storyworld only supports Capri.")
    gender = args.gender or rng.choice(["girl", "boy"])
    protagonist = args.protagonist or rng.choice(PROTAGONISTS[gender])
    guide = args.guide or rng.choice(list(GUIDES))
    item = args.item or "berries"
    return StoryParams(place=place, protagonist=protagonist, gender=gender, guide=guide, item=item)


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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show warn/1.\n#show revealed/1.\n#show safe_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show warn/1.\n#show revealed/1.\n#show safe_choice/1."))
        print("ASP atoms:")
        for pred in ("warn", "revealed", "safe_choice"):
            print(pred, asp.atoms(model, pred))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="capri", protagonist="Mina", gender="girl", guide="grandma", item="berries")
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
