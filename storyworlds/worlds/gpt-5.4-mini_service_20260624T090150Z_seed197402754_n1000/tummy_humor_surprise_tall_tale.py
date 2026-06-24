#!/usr/bin/env python3
"""
A tiny Storyweavers world: a tall-tale tummy story with humor and surprise.

A child gets a grumbly tummy, tries one absurd remedy, and then a surprise
turns the whole day into a laughing fit with a real fix at the end.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class TummyTrouble:
    id: str
    trigger: str
    sign: str
    noise: str
    outcome: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    verb: str
    surprise: str
    helps: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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

SETTINGS = {
    "barn": Setting(place="the old red barn", indoors=True),
    "kitchen": Setting(place="the kitchen", indoors=True),
    "porch": Setting(place="the wide front porch", indoors=False),
}

TROUBLES = {
    "rumbles": TummyTrouble(
        id="rumbles",
        trigger="had an empty tummy",
        sign="a loud rumbly tummy",
        noise="grumble-groan",
        outcome="started to chatter like a kettle",
        mood="hungry",
        tags={"tummy", "hungry", "loud"},
    ),
    "giggles": TummyTrouble(
        id="giggles",
        trigger="ate a too-sweet berry pie",
        sign="a bubbly tummy",
        noise="gluggle-giggle",
        outcome="wobbled like jelly",
        mood="ticklish",
        tags={"tummy", "funny", "sweet"},
    ),
    "surprise_soup": TummyTrouble(
        id="surprise_soup",
        trigger="drank a cold cup of soup by mistake",
        sign="a swishy tummy",
        noise="sloshy-swish",
        outcome="made the whole belly feel like a boat",
        mood="startled",
        tags={"tummy", "surprise", "soup"},
    ),
}

REMEDIES = {
    "supper": Remedy(
        id="supper",
        label="a big bowl of supper",
        verb="eat supper",
        surprise="a spoon that was bigger than a shovel",
        helps={"hungry"},
        tags={"food", "tummy"},
    ),
    "toast": Remedy(
        id="toast",
        label="warm toast with honey",
        verb="eat toast",
        surprise="a slice of toast that wore a tiny hat of butter",
        helps={"hungry", "ticklish"},
        tags={"food", "tummy", "sweet"},
    ),
    "music": Remedy(
        id="music",
        label="a silly marching tune",
        verb="listen to music",
        surprise="a goose on the fence joined in on a kazoo",
        helps={"startled", "ticklish"},
        tags={"music", "surprise"},
    ),
}

CHARACTER_NAMES = ["Nora", "Milo", "Pip", "Ruby", "Otis", "Willa"]
PARENT_NAMES = ["Mama", "Papa", "Granny", "Uncle Bert"]
TRAITS = ["brave", "cheerful", "busy", "curious", "sparkly"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    trouble: str
    remedy: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def tummy_at_risk(trouble: TummyTrouble, remedy: Remedy) -> bool:
    return bool(trouble.mood in remedy.helps)


def select_remedy(trouble: TummyTrouble) -> Optional[Remedy]:
    for rem in REMEDIES.values():
        if tummy_at_risk(trouble, rem):
            return rem
    return None


def reasonableness_gate(place: str, trouble: TummyTrouble, remedy: Remedy) -> bool:
    if place not in SETTINGS:
        return False
    return tummy_at_risk(trouble, remedy)


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Ruby", "Willa", "Nora"} else "boy",
        meters={"tummy": 0.0},
        memes={"worry": 0.0, "humor": 0.0, "surprise": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type="mother" if params.parent in {"Mama", "Granny"} else "father",
        label=params.parent,
        meters={},
        memes={"worry": 0.0, "humor": 0.0},
    ))

    world.say(f"{child.id} was a {params.trait} little child with a tummy that told tall tales.")
    world.say(f"One day {child.id} had {trouble.trigger}, and {child.id}'s tummy made a {trouble.noise} sound.")

    world.para()
    world.say(f"At {setting.place}, {child.id} tried to ignore it, but the belly {trouble.outcome}.")
    child.meters["tummy"] += 1.0
    child.memes["worry"] += 1.0
    parent.memes["worry"] += 1.0

    if trouble.id == "rumbles":
        world.say(f"{parent.label} listened close and said, \"That tummy sounds hungrier than a steer in a haystack.\"")
    elif trouble.id == "giggles":
        world.say(f"{parent.label} laughed and said, \"That is the zaniest tummy I ever heard squirm!\"")
    else:
        world.say(f"{parent.label} blinked and said, \"Well, butter my boots, that tummy sure surprised us.\"")

    world.para()
    surprise_event = REMEDIES[params.remedy].surprise
    world.say(f"Then came a surprise so mighty it could have wobbled a wagon: {surprise_event}.")
    child.memes["surprise"] += 1.0
    child.memes["humor"] += 1.0

    if remedy.id == "supper":
        world.say(f"That was the clue. {parent.label} brought {remedy.label}, and {child.id} ate {remedy.verb} right away.")
    elif remedy.id == "toast":
        world.say(f"That was the clue. {parent.label} brought {remedy.label}, and {child.id} munched {remedy.verb} with a grin.")
    else:
        world.say(f"That was the clue. {parent.label} tapped a spoon and told {child.id} to {remedy.verb} and sway like a scarecrow.")

    child.meters["tummy"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["humor"] += 1.0
    child.memes["relief"] += 1.0
    parent.memes["worry"] = 0.0

    world.para()
    world.say(f"At the end, {child.id}'s tummy was quiet as a mouse in a mitten.")
    world.say(f"{child.id} laughed, {parent.label} laughed, and even the barn felt like it was smiling.")
    world.say(f"The tall tale of the grumbly tummy ended with a full belly and a bigger grin.")

    world.facts.update(
        child=child,
        parent=parent,
        trouble=trouble,
        remedy=remedy,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    trouble = f["trouble"]
    remedy = f["remedy"]
    return [
        f'Write a tall-tale story for a young child about a tummy that gets "{trouble.sign}" and then meets a silly surprise.',
        f"Tell a funny bedtime-style story where {child.id} has a tummy problem, but a surprise helps the grown-up choose {remedy.label}.",
        f'Write a short humorous surprise story that includes the word "tummy" and ends with laughter and relief.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    trouble: TummyTrouble = f["trouble"]
    remedy: Remedy = f["remedy"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who had the tummy trouble at {setting.place}?",
            answer=f"{child.id} had the tummy trouble. {parent.label} was there too and helped choose what to do.",
        ),
        QAItem(
            question=f"What did {child.id}'s tummy sound like?",
            answer=f"{child.id}'s tummy made a {trouble.noise} sound, which was funny and a little startling.",
        ),
        QAItem(
            question=f"What surprise helped the story turn around?",
            answer=f"The surprise was {remedy.surprise}, and it helped make the moment funny instead of worrisome.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}'s tummy?",
            answer=f"It ended with {child.id}'s tummy quiet and the whole family laughing together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tummy?",
            answer="A tummy is another word for a belly, the part of the body where food is digested.",
        ),
        QAItem(
            question="Why can an empty tummy make noise?",
            answer="An empty tummy can make noises because the stomach and intestines keep moving even when there is not much food inside.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you do not know it is coming.",
        ),
        QAItem(
            question="Why can humor help when something feels bad?",
            answer="Humor can help because laughing can make a hard moment feel smaller and friendlier.",
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
trouble(T) :- tummy_trouble(T).
remedy(R) :- remedy_kind(R).
helps(T,R) :- matches(T,R).
valid_story(P,T,R) :- place(P), trouble(T), remedy(R), helps(T,R).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t, trouble in TROUBLES.items():
        lines.append(asp.fact("tummy_trouble", t))
        for tag in sorted(trouble.tags):
            lines.append(asp.fact("trouble_tag", t, tag))
    for r, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy_kind", r))
        for tag in sorted(remedy.tags):
            lines.append(asp.fact("remedy_tag", r, tag))
    for t, trouble in TROUBLES.items():
        for r, remedy in REMEDIES.items():
            if tummy_at_risk(trouble, remedy):
                lines.append(asp.fact("matches", t, r))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((p, t, r) for p in SETTINGS for t, trouble in TROUBLES.items() for r, remedy in REMEDIES.items() if reasonableness_gate(p, trouble, remedy))
    asp_set = asp_valid_stories()
    if set(py) == set(asp_set):
        print(f"OK: ASP parity matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(set(py) - set(asp_set)))
    print("asp only:", sorted(set(asp_set) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# Params, generation, CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale tummy storyworld with humor and surprise.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    tr = TROUBLES[trouble]
    remedy = args.remedy or rng.choice([r for r in REMEDIES if tummy_at_risk(tr, REMEDIES[r])])
    rem = REMEDIES[remedy]
    if not reasonableness_gate(place, tr, rem):
        raise StoryError("The chosen tummy problem and remedy do not fit together.")
    name = args.name or rng.choice(CHARACTER_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, remedy=remedy, name=name, parent=parent, trait=trait)


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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="barn", trouble="rumbles", remedy="supper", name="Milo", parent="Mama", trait="curious"),
        StoryParams(place="kitchen", trouble="giggles", remedy="toast", name="Ruby", parent="Papa", trait="sparkly"),
        StoryParams(place="porch", trouble="surprise_soup", remedy="music", name="Otis", parent="Granny", trait="brave"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        for row in stories:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
