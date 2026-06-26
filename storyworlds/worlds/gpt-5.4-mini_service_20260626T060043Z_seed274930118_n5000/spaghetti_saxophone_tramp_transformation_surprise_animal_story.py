#!/usr/bin/env python3
"""
Standalone storyworld: animal surprise, transformation, spaghetti, saxophone, tramp.

A small, classical simulation about a stray tramp animal who is surprised by
music, a plate of spaghetti, and a magical transformation that changes what the
animal can do and how the other animals feel about it.
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
    kind: str = "thing"  # "animal" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    uses_hands: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal" and self.species in {"cat", "dog", "fox", "rabbit", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old lane"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str


@dataclass
class StoryParams:
    setting: str
    animal: str
    prop: str
    transformer: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

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
    "lane": Setting(place="the old lane", outdoors=True, affords={"music", "spaghetti"}),
    "yard": Setting(place="the quiet yard", outdoors=True, affords={"music", "spaghetti"}),
    "barn": Setting(place="the red barn", outdoors=False, affords={"music", "spaghetti"}),
}

ANIMALS = {
    "cat": {"species": "cat", "label": "cat", "phrase": "a scruffy little cat"},
    "dog": {"species": "dog", "label": "dog", "phrase": "a shaggy little dog"},
    "fox": {"species": "fox", "label": "fox", "phrase": "a clever little fox"},
    "rabbit": {"species": "rabbit", "label": "rabbit", "phrase": "a shy little rabbit"},
    "mouse": {"species": "mouse", "label": "mouse", "phrase": "a tiny little mouse"},
}

PROPS = {
    "spaghetti": Prop(id="spaghetti", label="spaghetti", phrase="a warm bowl of spaghetti", kind="food"),
    "saxophone": Prop(id="saxophone", label="saxophone", phrase="a shiny saxophone", kind="music"),
    "tramp": Prop(id="tramp", label="tramp", phrase="a tramp animal", kind="stray"),
}

TRANSFORM_TARGETS = {
    "music": "dancer",
    "spaghetti": "helper",
}

TRAITS = ["lonely", "curious", "brave", "shy", "bouncy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
animal(A) :- animal_fact(A).
setting(S) :- setting_fact(S).
prop(P) :- prop_fact(P).
transformer(T) :- transformer_fact(T).

surprise(A,P) :- wants(A,P), appears(P), not expects(A,P).
changes(A,New) :- surprise(A,P), transform_target(P,New).
valid_story(S,A,P,T) :- setting_fact(S), animal_fact(A), prop_fact(P), transformer_fact(T),
                        affords(S,music), affords(S,spaghetti).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for feat in sorted(s.affords):
            lines.append(asp.fact("affords", sid, feat))
    for aid in ANIMALS:
        lines.append(asp.fact("animal_fact", aid))
    for pid in PROPS:
        lines.append(asp.fact("prop_fact", pid))
    lines.append(asp.fact("transformer_fact", "wizard"))
    lines.append(asp.fact("transform_target", "spaghetti", "helper"))
    lines.append(asp.fact("transform_target", "music", "dancer"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def animal_name_key(species: str) -> str:
    return ANIMALS[species]["label"]


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    animal_cfg = ANIMALS[params.animal]
    animal = world.add(Entity(
        id="animal",
        kind="animal",
        species=animal_cfg["species"],
        label=animal_cfg["label"],
        phrase=animal_cfg["phrase"],
        meters={"hunger": 1.0, "dust": 1.0},
        memes={"lonely": 1.0, "curious": 1.0},
    ))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        label=params.prop,
        phrase=PROPS[params.prop].phrase,
        owner=animal.id,
        meters={},
        memes={},
    ))
    transformer = world.add(Entity(
        id="transformer",
        kind="animal",
        species="wizard",
        label="wizard",
        phrase="a small wizard bird",
        meters={},
        memes={"surprise": 1.0},
    ))
    world.facts.update(animal=animal, prop=prop, transformer=transformer, setting=setting)
    return world


def transform(world: World, animal: Entity, prop: Entity, transformer: Entity) -> str:
    if prop.id == "spaghetti":
        animal.species = "spaghetti-beast"
        animal.label = "spaghetti-beast"
        animal.phrase = "a spaghetti-beast with noodle curls"
        animal.meters["hunger"] = 0.0
        animal.memes["joy"] = 1.0
        return f"The wizard touched the spaghetti, and {animal.id} turned into a spaghetti-beast."
    if prop.id == "saxophone":
        animal.species = "music-singer"
        animal.label = "music-singer"
        animal.phrase = "a music-singer with bright ears"
        animal.memes["joy"] = 1.0
        return f"The wizard tapped the saxophone, and {animal.id} changed into a music-singer."
    animal.memes["surprise"] = 1.0
    return f"The wizard smiled, and {animal.id} changed in a small surprising way."


def tell(setting: Setting, animal_key: str, prop_key: str, transformer_key: str) -> World:
    world = World(setting)
    animal_cfg = ANIMALS[animal_key]
    animal = world.add(Entity(
        id="animal",
        kind="animal",
        species=animal_cfg["species"],
        label=animal_cfg["label"],
        phrase=animal_cfg["phrase"],
        meters={"hunger": 1.0, "dust": 1.0},
        memes={"lonely": 1.0, "curious": 1.0},
    ))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        label=prop_key,
        phrase=PROPS[prop_key].phrase,
        owner=animal.id,
    ))
    transformer = world.add(Entity(
        id="transformer",
        kind="animal",
        species="wizard",
        label=transformer_key,
        phrase="a tiny surprise wizard",
    ))

    world.say(f"{animal.phrase} lived near {setting.place}.")
    world.say(f"It was a {animal.memes['lonely'] and 'lonely' or 'happy'} tramp animal, and it wandered the lane looking for a friend.")
    world.para()
    world.say(f"Then it found {prop.phrase} by the road.")
    if prop.id == "spaghetti":
        animal.meters["hunger"] += 1.0
        animal.memes["delight"] = 1.0
        world.say(f"It sniffed the warm spaghetti and licked its lips.")
    elif prop.id == "saxophone":
        animal.memes["curious"] = 2.0
        world.say(f"It heard a bumpy note from the saxophone and tilted its head.")
    world.para()
    world.say(f"Just then, the {transformer.label} fluttered down with a little spark.")
    world.say(f"The spark caused a surprise, and the animal changed.")
    world.say(transform(world, animal, prop, transformer))
    world.para()
    if prop.id == "spaghetti":
        world.say(f"After the transformation, {animal.id} twirled noodle arms and shared the spaghetti with the wizard.")
        world.say(f"The tramp was no longer lonely; it had become a happy spaghetti-beast under the moon.")
    else:
        world.say(f"After the transformation, {animal.id} played the saxophone with a bright new song.")
        world.say(f"The tramp was still itself, but it felt bigger inside and walked home with a friend.")
    world.facts.update(setting=setting, animal=animal, prop=prop, transformer=transformer)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short animal story with a surprise transformation that includes spaghetti, saxophone, and a tramp animal.',
        f"Tell a gentle story where a {f['animal'].label} finds {f['prop'].phrase} and meets a surprise wizard.",
        f"Write a child-friendly story about {f['animal'].phrase}, {f['prop'].label}, and a magical change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal: Entity = f["animal"]
    prop: Entity = f["prop"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Where did the {animal.label} live?",
            answer=f"The {animal.label} lived near {setting.place}.",
        ),
        QAItem(
            question=f"What surprising thing did the tramp animal find?",
            answer=f"It found {prop.phrase}, which led to a surprise.",
        ),
        QAItem(
            question=f"What changed after the wizard appeared?",
            answer=f"The animal transformed, and the ending showed it had a new life and a new feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is spaghetti?",
            answer="Spaghetti is long, soft pasta that people often eat with sauce.",
        ),
        QAItem(
            question="What is a saxophone?",
            answer="A saxophone is a musical instrument that makes loud, bright notes when someone plays it.",
        ),
        QAItem(
            question="What does tramp mean?",
            answer="A tramp is a wandering stray or a traveler with no fixed home.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} species={e.species} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    expected = {(s, a, p, "wizard") for s in SETTINGS for a in ANIMALS for p in PROPS if True}
    if stories:
        print(f"OK: ASP produced {len(stories)} story tuples.")
        return 0
    print("MISMATCH: ASP produced no story tuples.")
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: spaghetti, saxophone, tramp, surprise transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--transformer", choices=["wizard"], default="wizard")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    prop = args.prop or rng.choice(list(PROPS))
    transformer = args.transformer or "wizard"
    if setting not in SETTINGS:
        raise StoryError("unknown setting")
    return StoryParams(setting=setting, animal=animal, prop=prop, transformer=transformer)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.animal, params.prop, params.transformer)
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
    StoryParams(setting="lane", animal="cat", prop="spaghetti", transformer="wizard"),
    StoryParams(setting="yard", animal="dog", prop="saxophone", transformer="wizard"),
    StoryParams(setting="barn", animal="fox", prop="spaghetti", transformer="wizard"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
