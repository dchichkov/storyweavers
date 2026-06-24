#!/usr/bin/env python3
"""
storyworlds/worlds/gristle_whir_real_ist_dialogue_ghost_story.py
===============================================================

A small standalone story world in a ghost-story register: a child hears a
whir in the old house, finds a gristle-stiff mystery, and learns to be a
real-ist without flattening the wonder. The domain stays tiny on purpose:
one setting, one eerie sound, one misunderstood object, one helper, and a
dialogue-driven turn.

Seed words: gristle, whir, real-ist
Style: Ghost Story
Feature: Dialogue

The source-tale idea behind this world:
- A child hears a spooky whir in a quiet house.
- They think it is a ghost.
- A careful grown-up helps them find the real cause: a little fan, a loose toy,
  or another harmless machine making the sound.
- The child keeps the thrill, but learns a real-ist habit: look first, then
  wonder.

The simulation uses typed entities with physical meters and emotional memes.
The world state drives the prose: sound grows, fear rises, an investigation
happens, and a true explanation resolves the haunting.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: Optional[str] = None
    source: bool = False
    eerie: bool = False
    noisy: bool = False
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    detail: str
    dark_spot: str
    listener_spot: str
    time_word: str = "at night"


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    truth: str
    source_kind: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    method: str
    reveal: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    mystery: str
    guide: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(
        place="the attic",
        detail="Old trunks slept under the rafters, and the air smelled like dust and mothballs.",
        dark_spot="the dark corner by the trunk",
        listener_spot="at the top step",
    ),
    "hallway": Setting(
        place="the hallway",
        detail="The wallpaper peeled a little, and the floorboards whispered with every step.",
        dark_spot="the shadow under the stairs",
        listener_spot="by the lamp table",
    ),
    "basement": Setting(
        place="the basement",
        detail="The pipes ticked softly, and the concrete held a cold smell after the rain.",
        dark_spot="the space by the furnace",
        listener_spot="near the laundry door",
    ),
}

MYSTERIES = {
    "fan": Mystery(
        id="fan",
        label="little fan",
        phrase="a little fan with bent blades",
        sound="whir",
        clue="cool air tugged at the child's sleeve",
        truth="It was only a little fan turning on the shelf.",
        source_kind="fan",
        gentle=True,
        tags={"whir", "fan", "sound"},
    ),
    "toy": Mystery(
        id="toy",
        label="winding toy",
        phrase="an old winding toy with a stiff key",
        sound="whir",
        clue="a tinny click kept following the whir",
        truth="It was only an old winding toy turning itself around and around.",
        source_kind="toy",
        gentle=True,
        tags={"whir", "toy", "sound", "gristle"},
    ),
    "pipe": Mystery(
        id="pipe",
        label="pipe vent",
        phrase="a pipe vent with a loose grate",
        sound="whir",
        clue="the floor gave a tiny shiver under the sound",
        truth="It was only air hurrying through a loose pipe vent.",
        source_kind="pipe",
        gentle=True,
        tags={"whir", "pipe", "sound"},
    ),
}

GUIDES = {
    "realist": Guide(
        id="realist",
        label="real-ist",
        phrase="a real-ist",
        method="look first, then listen, then check the source",
        reveal="The world can still be wondrous when it is understood.",
        tags={"real-ist", "realist", "truth"},
    ),
    "lantern": Guide(
        id="lantern",
        label="lantern-bearer",
        phrase="a lantern-bearer",
        method="carry a lamp and peek carefully",
        reveal="A steady light makes a spooky room feel smaller.",
        tags={"lantern", "light", "truth"},
    ),
    "listener": Guide(
        id="listener",
        label="quiet listener",
        phrase="a quiet listener",
        method="pause, breathe, and ask what makes the sound",
        reveal="Not every strange sound is a ghostly one.",
        tags={"listen", "truth"},
    ),
}

GIRL_NAMES = ["Maya", "June", "Ella", "Lina", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Leo", "Eli", "Max", "Owen"]
TRAITS = ["curious", "brave", "careful", "quiet", "shivery", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for g in GUIDES:
                out.append((s, m, g))
    return out


def reasonableness_gate(mystery: Mystery, guide: Guide) -> bool:
    return mystery.gentle and "truth" in guide.tags


def explain_rejection(mystery: Mystery, guide: Guide) -> str:
    return (
        f"(No story: the chosen mystery is not gentle enough for this child-sized "
        f"ghost story, or the guide does not help reveal the truth. Try a gentle "
        f"whir and a real-ist guide.)"
    )


def _r_fear(world: World) -> list[str]:
    child = world.entities.get("child")
    mystery = world.entities.get("mystery")
    if not child or not mystery:
        return []
    if child.memes["fear"] < THRESHOLD:
        return []
    sig = ("fear", mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["shiver"] += 1
    return []


ASP_RULES = r"""
mystery_ok(M) :- mystery(M), gentle(M).
guide_ok(G) :- guide(G), truth_guide(G).
valid(S, M, G) :- setting(S), mystery_ok(M), guide_ok(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.gentle:
            lines.append(asp.fact("gentle", mid))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        if "truth" in g.tags:
            lines.append(asp.fact("truth_guide", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, t: str) -> None:
        if t:
            self.paragraphs[-1].append(t)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(setting: Setting, mystery: Mystery, guide: Guide, child_name: str, child_gender: str,
         adult_name: str, adult_gender: str, trait: str) -> StoryWorld:
    w = StoryWorld(setting)
    child = w.add(Entity(id=child_name, kind="character", type=child_gender, traits=["little", trait]))
    adult = w.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    mist = w.add(Entity(id="mystery", kind="thing", type=mystery.id, label=mystery.label, source=True, eerie=True))
    w.add(Entity(id="guide", kind="thing", type=guide.id, label=guide.label))
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    w.say(f"At night, {child.id} stood {setting.listener_spot} and heard a soft {mystery.sound}.")
    w.say(f'"What is that?" {child.id} whispered. "{mystery.sound}, {mystery.sound}..."')
    w.para()
    child.memes["fear"] += 1
    w.say(f"{setting.detail} {setting.dark_spot} seemed to breathe in the dark.")
    w.say(f'"It sounds like a ghost," {child.id} said.')
    w.say(f'"Maybe," said {adult.id}, "but let us be a {guide.label} and look first.')
    w.para()
    child.memes["fear"] = 0
    w.say(f'They followed {guide.method}. Under the dim light, {mystery.clue}.')
    w.say(f'"Oh," {child.id} said. "{mystery.truth}"')
    w.say(f'"See?" said {adult.id}. "{guide.reveal}"')
    w.para()
    child.memes["joy"] += 1
    child.memes["understanding"] += 1
    w.say(f"{child.id} smiled and called {mystery.label} a spooky thing that was not a ghost at all.")
    w.say(f'The house still felt haunted in the fun way, but now the whir had a name, and the name was real.')
    w.facts.update(child=child, adult=adult, mystery=mystery, guide=guide)
    return w


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child that includes the word "{f["mystery"].sound}" and ends with a true explanation.',
        f"Tell a dialogue-heavy story where {f['child'].id} hears a spooky sound in {world.setting.place} and learns to be a {f['guide'].label}.",
        f'Write a gentle story about a "ghost" that turns out to be {f["mystery"].phrase}.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    mystery = f["mystery"]
    guide = f["guide"]
    return [
        QAItem(
            question=f"What sound did {child.id} hear in {world.setting.place}?",
            answer=f"{child.id} heard a soft {mystery.sound} in {world.setting.place}."
        ),
        QAItem(
            question=f"What did {child.id} think the sound was at first?",
            answer=f"{child.id} thought it might be a ghost."
        ),
        QAItem(
            question=f"What was the real cause of the {mystery.sound}?",
            answer=mystery.truth
        ),
        QAItem(
            question=f"What did {adult.id} tell {child.id} to be?",
            answer=f"{adult.id} told {child.id} to be a {guide.label} and look first."
        ),
        QAItem(
            question=f"What did {child.id} learn by the end?",
            answer=f"{child.id} learned that a spooky sound can have a real cause, and wonder is still okay."
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word real-ist mean here?",
            answer="Here, a real-ist is someone who looks for the real cause of a strange thing before deciding what it is."
        ),
        QAItem(
            question="What does a whir sound like?",
            answer="A whir is a soft spinning sound, like a fan or a toy turning around."
        ),
        QAItem(
            question="Why can old houses sound spooky?",
            answer="Old houses can make little creaks, hums, and whirs that seem spooky in the dark."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid())
    if p == a:
        print(f"OK: ASP matches Python ({len(p)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(p - a))
    print("asp only:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with dialogue, whir, and real-ist wonder.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["girl", "boy"])
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
    if args.mystery and args.guide:
        if not reasonableness_gate(MYSTERIES[args.mystery], GUIDES[args.guide]):
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], GUIDES[args.guide]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, guide = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(GIRL_NAMES if adult_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mystery, guide, name, gender, adult, adult_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], GUIDES[params.guide],
                 params.child_name, params.child_gender, params.adult_name, params.adult_gender, params.trait)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for p in [StoryParams(s, m, g, "Maya", "girl", "Aunt June", "girl", "curious") for s, m, g in valid_combos()[:5]]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
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
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
