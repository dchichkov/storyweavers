#!/usr/bin/env python3
"""
storyworlds/worlds/slant_nostril_reconciliation_magic_detective_story.py
=======================================================================

A small detective-story world about a curious clue, a little bit of magic,
and a reconciliation that clears the air.

The seed tale premise:
- A detective notices a strange slant-shaped clue near a nostril.
- The clue seems magical, which makes the mystery feel bigger.
- The detective follows the trail, discovers a misunderstanding, and helps two
  characters reconcile.
- The ending proves what changed: the clue is explained, the worry fades, and
  the friends are kind again.

The world is designed to support a few tight, child-facing variations while
remaining state-driven: the physical world tracks clues, objects, and location,
and the emotional world tracks worry, blame, trust, and relief.
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
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    wearing: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["cleanliness", "mystery", "distance", "light", "magic"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "blame", "trust", "relief", "curiosity", "shame", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Place:
    id: str
    label: str
    mood: str
    light: str
    affords_magic: bool = False


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    slant: bool = False
    nostril: bool = False
    magic_trail: bool = False


@dataclass
class Mystery:
    id: str
    label: str
    explanation: str
    culprit: str
    misunderstanding: str


@dataclass
class StoryParams:
    place: str
    detective: str
    partner: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: list[str] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "library": Place("library", "the library", "quiet", "soft", affords_magic=False),
    "garden": Place("garden", "the garden", "bright", "sunlit", affords_magic=True),
    "station": Place("station", "the little train station", "busy", "clear", affords_magic=False),
    "attic": Place("attic", "the attic", "dusty", "thin", affords_magic=True),
}

DETECTIVES = {
    "milo": ("Milo", "boy", ["careful", "curious"]),
    "mina": ("Mina", "girl", ["careful", "curious"]),
    "pip": ("Pip", "thing", ["small", "curious"]),
}

PARTNERS = {
    "nina": ("Nina", "girl", ["nervous", "kind"]),
    "tom": ("Tom", "boy", ["quiet", "kind"]),
    "luna": ("Luna", "girl", ["sparkly", "gentle"]),
}

MYSTERIES = {
    "nosepaint": Mystery(
        id="nosepaint",
        label="the nose-paint mystery",
        explanation="a paintbrush had brushed a red slant near a nostril while someone was trying a magic trick",
        culprit="the little magician",
        misunderstanding="the detective thought someone had been teased, but it was only an accidental brush of paint",
    ),
    "flowerdust": Mystery(
        id="flowerdust",
        label="the flower-dust mystery",
        explanation="flower dust had blown into the air and left a slant on a nose from sneezing",
        culprit="the gardener",
        misunderstanding="the detective first thought the mark meant trouble, but it was just a sneeze and a flower pouch",
    ),
    "glitterwand": Mystery(
        id="glitterwand",
        label="the glitter-wand mystery",
        explanation="glitter from a wand made a bright slant across a nostril during a magic show",
        culprit="the magician",
        misunderstanding="the detective thought the glitter was a secret signal, but it was only stage magic",
    ),
}

CLUES = {
    "slant_mark": Clue("slant_mark", "a slant-shaped mark", "a slant-shaped mark", slant=True),
    "nostril_smudge": Clue("nostril_smudge", "a nostril smudge", "a smudge by a nostril", nostril=True),
    "glimmer_dust": Clue("glimmer_dust", "glimmer dust", "a trail of glimmer dust", magic_trail=True),
}

TITLE_ADJ = ["gentle", "tiny", "quiet", "clever"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(place: Place, mystery: Mystery) -> None:
    if not place.affords_magic and mystery.id in {"glitterwand", "nosepaint"}:
        # still possible because the magic happens as a small stage trick
        return
    if not place.label:
        raise StoryError("Invalid place for this detective story.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with slant, nostril, magic, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    detective = args.detective or rng.choice(list(DETECTIVES))
    partner = args.partner or rng.choice(list(PARTNERS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    reasonableness_gate(PLACES[place], MYSTERIES[mystery])
    return StoryParams(place=place, detective=detective, partner=partner, mystery=mystery)


def _entity_for(name_key: str, registry: dict[str, tuple[str, str, list[str]]], kind: str = "character") -> Entity:
    label, typ, traits = registry[name_key]
    return Entity(id=label, kind=kind, type=typ, label=label, traits=list(traits))


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    detective_label, detective_type, detective_traits = DETECTIVES[params.detective]
    partner_label, partner_type, partner_traits = PARTNERS[params.partner]

    world = World(place)
    detective = world.add(Entity(id=detective_label, kind="character", type=detective_type, label=detective_label, traits=list(detective_traits)))
    partner = world.add(Entity(id=partner_label, kind="character", type=partner_type, label=partner_label, traits=list(partner_traits)))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=CLUES["slant_mark"].label,
        phrase=CLUES["slant_mark"].phrase,
        location=place.id,
    ))

    # Beginning
    world.say(f"{detective.label} was a {random.choice(TITLE_ADJ)} detective who liked quiet places and small details.")
    world.say(f"On that day, {detective.label} met {partner.label} at {place.label}, where the light was {place.light} and the air felt {place.mood}.")
    world.say(f"Then {detective.label} spotted {CLUES['slant_mark'].phrase} near a nostril, and the little mark made the whole room feel mysterious.")

    # Middle
    world.para()
    detective.memes["curiosity"] += 1
    detective.meters["mystery"] += 1
    partner.memes["worry"] += 1
    world.say(f"{detective.label} leaned in and looked again, because the slant might have been a clue.")
    if mystery.id == "nosepaint":
        world.say(f"Nearby, a tiny paintbrush and a sparkly hat hinted at magic.")
        world.say(f"{partner.label} looked shy, because {mystery.misunderstanding}.")
    elif mystery.id == "flowerdust":
        world.say(f"A small pouch of flowers sat on a table, and a sneeze had left the odd mark.")
        world.say(f"{partner.label} looked shy, because {mystery.misunderstanding}.")
    else:
        world.say(f"A wand with glitter on its tip lay beside a velvet cloth.")
        world.say(f"{partner.label} looked shy, because {mystery.misunderstanding}.")

    detective.memes["blame"] += 1
    partner.memes["shame"] += 1
    world.say(f"At first, {detective.label} wondered if someone had done something wrong.")
    world.say(f"But the detective did not rush. Instead, {detective.label} followed the magic trail and asked one careful question after another.")

    # Resolution
    world.para()
    detective.memes["blame"] = 0.0
    detective.memes["trust"] += 1
    partner.memes["shame"] = 0.0
    partner.memes["relief"] += 1
    partner.memes["trust"] += 1

    world.say(f"That was when the truth came out: {mystery.explanation}.")
    world.say(f"{detective.label} smiled and said that a mystery can look scary before it is understood.")
    world.say(f"{partner.label} apologized for the confusion, and {detective.label} answered kindly, so they could reconcile.")
    world.say(f"By the end, the nostril mark was only a clue, the magic was only a trick, and {detective.label} and {partner.label} left together with lighter hearts.")

    world.facts.update(
        detective=detective,
        partner=partner,
        place=place,
        mystery=mystery,
        clue=clue,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"].label
    par = f["partner"].label
    place = f["place"].label
    mystery = f["mystery"].label
    return [
        f"Write a short detective story for a child set at {place} about {det} and {par}, with {mystery} and a kind ending.",
        f"Tell a gentle mystery where {det} notices a slant near a nostril, follows a magical clue, and helps everyone reconcile.",
        f"Write a tiny detective tale that includes the words slant, nostril, magic, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"].label
    par = f["partner"].label
    place = f["place"].label
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det}, who paid close attention to small clues at {place}.",
        ),
        QAItem(
            question=f"What odd clue did {det} notice?",
            answer="The detective noticed a slant-shaped mark near a nostril, which made the scene feel mysterious.",
        ),
        QAItem(
            question=f"What did the detective do instead of blaming {par} right away?",
            answer="The detective followed the magic trail, asked careful questions, and kept looking until the truth made sense.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because the misunderstanding was explained, {par} apologized, and the two characters reconciled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a misunderstanding or a disagreement.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is something surprising or special that seems impossible in real life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
detective(D) :- character(D), role(D, detective).
partner(P) :- character(P), role(P, partner).

mystery(M) :- mystery_kind(M).
magic(M) :- magic_kind(M).

reconciliation(D,P) :- apology(P), kindness(D), trust(D), trust(P).
resolved(P) :- reconciliation(_,P).

interesting_story(Place, Mystery) :- place(Place), mystery(Mystery).
interesting_story(Place, Mystery) :- place(Place), mystery(Mystery), magic(Mystery).

#show interesting_story/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.affords_magic:
            lines.append(asp.fact("magic_place", pid))
    for did in DETECTIVES:
        lines.append(asp.fact("character", DETECTIVES[did][0]))
        lines.append(asp.fact("role", DETECTIVES[did][0], "detective"))
        lines.append(asp.fact("kind", DETECTIVES[did][0], "character"))
        lines.append(asp.fact("kind_tag", DETECTIVES[did][0], "detective"))
    for pid in PARTNERS:
        lines.append(asp.fact("character", PARTNERS[pid][0]))
        lines.append(asp.fact("role", PARTNERS[pid][0], "partner"))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_kind", mid))
        if "glitter" in mid or "nosepaint" in mid:
            lines.append(asp.fact("magic_kind", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show interesting_story/2."))
    asp_pairs = set(asp.atoms(model, "interesting_story"))
    py_pairs = {(p, m) for p in PLACES for m in MYSTERIES}
    if asp_pairs != py_pairs:
        print("MISMATCH between ASP and Python story-space.")
        if asp_pairs - py_pairs:
            print("  only in ASP:", sorted(asp_pairs - py_pairs))
        if py_pairs - asp_pairs:
            print("  only in Python:", sorted(py_pairs - asp_pairs))
        return 1
    print(f"OK: ASP parity verified for {len(py_pairs)} story-space pairs.")
    return 0


# ---------------------------------------------------------------------------
# Generation and output
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="library", detective="milo", partner="nina", mystery="nosepaint"),
    StoryParams(place="garden", detective="mina", partner="tom", mystery="glitterwand"),
    StoryParams(place="attic", detective="pip", partner="luna", mystery="flowerdust"),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.label}")
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = [f"type={ent.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if ent.location:
            parts.append(f"location={ent.location}")
        lines.append(f"{ent.id}: " + ", ".join(parts))
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
        print(asp_program("#show interesting_story/2.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show interesting_story/2."))
        pairs = sorted(set(asp.atoms(model, "interesting_story")))
        for p, m in pairs:
            print(p, m)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.detective} / {p.partner} / {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
