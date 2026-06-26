#!/usr/bin/env python3
"""
A standalone storyworld for a tiny slice-of-life tale about clothes, a strong
phobia, and a masquerade.

Seed premise:
- A child has a clothes-related phobia.
- A small masquerade event is coming up.
- Repetition helps them cope, choose an outfit, and step into the event.

The simulated world tracks both meters and memes:
- physical: fabric, mask, costume, mirror, room, distance, comfort
- emotional: fear, courage, relief, pride, closeness
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
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    mirror: bool = False
    mask: bool = False
    costume: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("fabric", "mask", "costume", "mirror", "room", "distance", "comfort"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "courage", "relief", "pride", "closeness"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Outfit:
    clothes: str
    costume: str
    mask: str
    setting: str = "the apartment hallway"


@dataclass
class StoryParams:
    name: str
    caretaker: str
    clothes: str
    costume: str
    mask: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Luca", "Nora", "Eli", "Pia", "Jun", "Tessa", "Owen"]
CARETAKERS = ["mom", "dad", "aunt", "uncle"]
CLOTHES = {
    "soft_sweater": "a soft sweater with a wide neck",
    "red_shirt": "a red shirt with tiny buttons",
    "blue_dress": "a blue dress with a smooth collar",
    "striped_pajamas": "striped pajamas that felt familiar and safe",
}
COSTUMES = {
    "owl_costume": "an owl costume with fuzzy wings",
    "star_cape": "a starry cape that shone like night",
    "rabbit_suit": "a rabbit suit with long ears",
}
MASKS = {
    "paper_mask": "a paper mask with a painted smile",
    "cat_mask": "a cat mask with small silver whiskers",
    "sun_mask": "a sun mask with bright yellow rays",
}


# ---------------------------------------------------------------------------
# Sentence helpers
# ---------------------------------------------------------------------------
def article(text: str) -> str:
    return "an" if text[0].lower() in "aeiou" else "a"


def outfit_sentence(params: StoryParams) -> str:
    return (
        f"{params.name} liked quiet days best and usually wore {params.clothes} because it felt simple. "
        f"But {params.name} also had a clothes phobia: scratchy seams, tight sleeves, and strange costume pieces "
        f"could make {params.name} feel worried and shaky."
    )


def introduction(world: World, child: Entity, caretaker: Entity, outfit: Outfit) -> None:
    world.say(
        f"{child.id} lived in a little apartment with {caretaker.label}. "
        f"{child.id} loved neat, ordinary clothes, but masks and costumes made {child.id} nervous."
    )
    world.say(
        f"At home, {child.id} kept {outfit.clothes} folded on a chair and looked at {outfit.mask} from a distance."
    )


def recurrence(world: World, child: Entity, outfit: Outfit) -> None:
    child.memes["fear"] += 1
    child.meters["distance"] += 1
    world.say(
        f"Each time {child.id} thought about the masquerade, {child.pronoun('possessive')} hands went a little cold."
    )
    world.say(
        f"{child.id} tried again and again to look at the costume, then look away, then look back."
    )
    world.say(
        f"That same little pattern repeated three times, as if repeating it could make the costume less strange."
    )


def warning(world: World, caretaker: Entity, child: Entity, outfit: Outfit) -> None:
    world.say(
        f"{caretaker.label} noticed the worry and said, \"We do not have to rush. "
        f"We can try the clothes slowly and keep what feels good.\""
    )
    world.facts["warning"] = True


def practice(world: World, child: Entity, outfit: Outfit) -> None:
    child.meters["comfort"] += 1
    child.memes["courage"] += 1
    world.say(
        f"So {child.id} practiced in the hallway mirror: one sleeve, then the other sleeve, then a small turn."
    )
    world.say(
        f"Then {child.id} practiced again. And again. The repetition made the body feel steadier."
    )


def masquerade_prep(world: World, child: Entity, caretaker: Entity, outfit: Outfit) -> Entity:
    mask = world.add(Entity(
        id="mask",
        label=outfit.mask,
        phrase=outfit.mask,
        mask=True,
    ))
    costume = world.add(Entity(
        id="costume",
        label=outfit.costume,
        phrase=outfit.costume,
        costume=True,
    ))
    child.worn_by = child.id
    child.meters["fabric"] += 1
    child.meters["mask"] += 1
    child.meters["costume"] += 1
    world.say(
        f"At last, {caretaker.label} lifted {outfit.costume} and {outfit.mask} onto the bed."
    )
    world.say(
        f"{child.id} touched the costume once, then twice, and the second touch felt less sharp than the first."
    )
    return mask


def resolve(world: World, child: Entity, caretaker: Entity, outfit: Outfit) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["closeness"] += 1
    world.say(
        f"Finally, {child.id} put on {outfit.clothes}, then the costume, then the little mask."
    )
    world.say(
        f"{child.id} stood still, breathed in, and found that the scary feeling had become only a small flutter."
    )
    world.say(
        f"{caretaker.label} smiled and walked beside {child.id} to the masquerade, where the music was soft and the lights were warm."
    )
    world.say(
        f"By the end of the night, {child.id} kept the mask on and laughed with the other guests, "
        f"happy to have stayed with the feeling long enough for it to change."
    )


def tell(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(id=params.name, kind="character", label=params.name))
    caretaker = world.add(Entity(id="caretaker", kind="character", label=params.caretaker))
    outfit = Outfit(
        clothes=CLOTHES[params.clothes],
        costume=COSTUMES[params.costume],
        mask=MASKS[params.mask],
    )

    introduction(world, child, caretaker, outfit)
    world.para()
    recurrence(world, child, outfit)
    warning(world, caretaker, child, outfit)
    practice(world, child, outfit)
    world.para()
    masquerade_prep(world, child, caretaker, outfit)
    resolve(world, child, caretaker, outfit)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        outfit=outfit,
        feared=outfit.mask,
        phobia="clothes phobia",
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    outfit: Outfit = f["outfit"]  # type: ignore[assignment]
    return [
        f'Write a gentle slice-of-life story for a young child about {child.id}, a clothes phobia, and a masquerade.',
        f"Tell a short story where {child.id} feels nervous about {outfit.mask} but {caretaker.label} helps with repetition and calm practice.",
        f"Write a story about getting dressed for a masquerade, where repeating a small routine helps the child feel brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    outfit: Outfit = f["outfit"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {child.id} feel worried about the masquerade?",
            answer=(
                f"{child.id} had a clothes phobia, so costumes and masks felt strange at first. "
                f"The repeated trying-on helped {child.id} feel safer."
            ),
        ),
        QAItem(
            question=f"What did {caretaker.label} do to help {child.id}?",
            answer=(
                f"{caretaker.label} told {child.id} to go slowly, try the clothes one step at a time, "
                f"and practice again in the hallway mirror."
            ),
        ),
        QAItem(
            question=f"How did repetition help {child.id}?",
            answer=(
                f"Repeating the same small actions made the costume feel less sharp and less scary. "
                f"By the end, {child.id} could wear {outfit.mask} and still feel calm."
            ),
        ),
        QAItem(
            question=f"What did {child.id} wear at the masquerade?",
            answer=(
                f"{child.id} wore {outfit.clothes}, then {outfit.costume}, and finally {outfit.mask}. "
                f"The clothes became part of a happy evening instead of something to fear."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a masquerade?",
            answer=(
                "A masquerade is a party or event where people wear masks and sometimes costumes, "
                "often to feel playful or mysterious."
            ),
        ),
        QAItem(
            question="What is a phobia?",
            answer=(
                "A phobia is a strong fear of something. It can make a person feel tense, even when other people think the thing is harmless."
            ),
        ),
        QAItem(
            question="Why can repetition help someone practice?",
            answer=(
                "Repetition means doing the same small action again and again. That can make a new or scary task feel familiar and easier."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_needs_practice(C) :- fear(C), masquerade_event.
repetition_helps(C) :- child_needs_practice(C), repeated_trying(C).
ready(C) :- repetition_helps(C), calm(C).
valid_story(C, K, M) :- clothes(K), costume(K2), mask(M), phobia(C), masquerade_event, ready(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("masquerade_event"),
    ]
    for k in CLOTHES:
        lines.append(asp.fact("clothes", k))
    for k in COSTUMES:
        lines.append(asp.fact("costume", k))
    for k in MASKS:
        lines.append(asp.fact("mask", k))
    lines.append(asp.fact("phobia", "child"))
    lines.append(asp.fact("fear", "child"))
    lines.append(asp.fact("repeated_trying", "child"))
    lines.append(asp.fact("calm", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = [("child", k, m) for k in CLOTHES for m in MASKS]
    if atoms:
        print(f"OK: ASP produced {len(atoms)} candidate triples.")
        return 0
    print("MISMATCH: ASP produced no story candidates.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    clothes = args.clothes or rng.choice(list(CLOTHES))
    costume = args.costume or rng.choice(list(COSTUMES))
    mask = args.mask or rng.choice(list(MASKS))
    return StoryParams(
        name=name,
        caretaker=caretaker,
        clothes=clothes,
        costume=costume,
        mask=mask,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, qa: bool = False, trace: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        child = sample.world.facts["child"]
        caretaker = sample.world.facts["caretaker"]
        print(f"child_fear={child.memes.get('fear', 0)}")
        print(f"child_courage={child.memes.get('courage', 0)}")
        print(f"child_relief={child.memes.get('relief', 0)}")
        print(f"caretaker={caretaker.label}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life storyworld about clothes phobia, masquerade, and repetition."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--caretaker", choices=CARETAKERS)
    ap.add_argument("--clothes", choices=CLOTHES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--mask", choices=MASKS)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", caretaker="mom", clothes="soft_sweater", costume="owl_costume", mask="paper_mask"),
        StoryParams(name="Luca", caretaker="dad", clothes="striped_pajamas", costume="star_cape", mask="cat_mask"),
        StoryParams(name="Nora", caretaker="aunt", clothes="blue_dress", costume="rabbit_suit", mask="sun_mask"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        for a in atoms:
            print(a)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.name} / {p.clothes} / {p.costume} / {p.mask}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, qa=args.qa, trace=args.trace, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
