#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/binocular_surprise_lesson_learned_cautionary_ghost_story.py
==========================================================================================================

A small storyworld for a child-facing ghost story with a binocular surprise,
a cautionary turn, and a lesson learned.

Premise seed:
- A curious child finds binoculars near an old, spooky place.
- The binoculars reveal an unexpected ghostly scene.
- The child learns a careful lesson about listening, staying with a helper,
  and not wandering off at night.

This world is intentionally tiny and constraint-checked:
- One child, one helper, one spooky setting, one eerie object, one surprise.
- The story turns on simulated state: curiosity, caution, fear, and relief.
- The ending image proves the lesson learned: the child is safer and wiser.

The prose style is close to a ghost story, but the ending stays gentle.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    spooky: bool = True
    afford_binoculars: bool = True
    afford_torch: bool = True


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    allows_surprise: bool = True


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    helper: str
    tone: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lighthouse": Setting(place="the old lighthouse"),
    "attic": Setting(place="the dusty attic"),
    "graveyard": Setting(place="the quiet graveyard"),
    "dock": Setting(place="the moonlit dock"),
}

OBJECTS = {
    "binoculars": ObjectCfg(
        label="binoculars",
        phrase="a heavy pair of binoculars",
        type="binoculars",
        allows_surprise=True,
    ),
    "lantern": ObjectCfg(
        label="lantern",
        phrase="a little lantern",
        type="lantern",
        allows_surprise=False,
    ),
    "key": ObjectCfg(
        label="key",
        phrase="an old brass key",
        type="key",
        allows_surprise=False,
    ),
}

HERO_NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Ivy", "Maya"],
    "boy": ["Finn", "Theo", "Eli", "Noah", "Ben"],
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandmother": "grandmother",
    "grandfather": "grandfather",
}

TONES = ["surprise", "lesson learned", "cautionary"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _hero_desc(hero: Entity) -> str:
    return f"little {hero.type} {hero.id}"


def _night_opening(setting: Setting) -> str:
    if setting.place == "the old lighthouse":
        return "The night air hummed around the broken windows, and the lantern light trembled on the stairs."
    if setting.place == "the dusty attic":
        return "The attic was full of creaks and sleepy shadows, and the boards sighed with every step."
    if setting.place == "the quiet graveyard":
        return "The graveyard lay under a round moon, and the stones looked pale as bones."
    return "The dock was quiet under the moon, and the water kept whispering against the posts."


def _surprise_scene(setting: Setting) -> str:
    if setting.place == "the old lighthouse":
        return "When the child raised the binoculars, a bright face flashed in the tower window—then vanished."
    if setting.place == "the dusty attic":
        return "When the child peered through the binoculars, a pale glow seemed to bob between the trunks and boxes."
    if setting.place == "the quiet graveyard":
        return "When the child looked through the binoculars, a candle seemed to blink beside the tallest stone."
    return "When the child looked through the binoculars, a white shape seemed to drift above the dark water."


def _lesson_scene(setting: Setting) -> str:
    if setting.place == "the old lighthouse":
        return "It was only the caretaker's lantern reflected in a dusty pane, and the old building had fooled their eyes."
    if setting.place == "the dusty attic":
        return "It was only moonlight on a hanging sheet, and the attic had played a trick on the child's nerves."
    if setting.place == "the quiet graveyard":
        return "It was only the helper's lantern by a fresh flower, and the moon had made it seem ghostly."
    return "It was only the dock master's lantern on the water, and the waves had made it look like a drifting ghost."


def _safe_end(setting: Setting) -> str:
    if setting.place == "the old lighthouse":
        return "After that, the child stayed close to the mother, and the lanterns in the lighthouse looked friendly instead of frightful."
    if setting.place == "the dusty attic":
        return "After that, the child held the mother's hand, and even the attic shadows felt small and harmless."
    if setting.place == "the quiet graveyard":
        return "After that, the child walked beside the grandfather, and the graveyard seemed calm and respectful."
    return "After that, the child kept beside the father, and the dark water did not seem so strange anymore."


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    obj = OBJECTS[params.object]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "fear": 0.0, "caution": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"distance": 0.0},
        memes={"care": 1.0},
    ))
    item = world.add(Entity(
        id="object",
        kind="thing",
        type=obj.type,
        label=obj.label,
        phrase=obj.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    world.facts.update(hero=hero, helper=helper, item=item, setting=setting, object_cfg=obj)
    return world


def _look_through_binoculars(world: World) -> None:
    hero: Entity = world.facts["hero"]
    item: Entity = world.facts["item"]
    setting: Setting = world.facts["setting"]

    if item.type != "binoculars":
        raise StoryError("This story requires binoculars so the surprise can be seen from a distance.")

    hero.meters["distance"] += 1.0
    hero.memes["curiosity"] += 1.0
    world.say(f"{_hero_desc(hero)} found {item.phrase} near {setting.place}.")

    world.say(f"{hero.id} lifted the binoculars to {hero.pronoun('possessive')} eyes.")
    hero.memes["fear"] += 0.5
    world.say(_night_opening(setting))
    world.say(_surprise_scene(setting))
    hero.memes["fear"] += 1.0
    hero.memes["caution"] += 1.0


def _helper_explains(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    setting: Setting = world.facts["setting"]

    world.para()
    world.say(
        f"{helper.pronoun().capitalize()} came close and said, "
        f"\"Night can make ordinary things look like ghosts.\""
    )
    world.say(_lesson_scene(setting))
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["relief"] += 1.0
    hero.memes["caution"] += 1.0
    world.say(
        f"{hero.id} blinked, breathed out, and learned that a surprise is not always a danger."
    )


def _safe_choice(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    setting: Setting = world.facts["setting"]

    world.para()
    world.say(
        f"{hero.id} put the binoculars down and stayed beside {hero.pronoun('possessive')} {helper.type}."
    )
    world.say(_safe_end(setting))
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.75)
    hero.memes["relief"] += 1.0


def generate_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    item: Entity = world.facts["item"]
    setting: Setting = world.facts["setting"]

    world.say(
        f"{hero.id} was a curious little {hero.type} who liked listening to spooky stories."
    )
    world.say(
        f"One evening, {hero.id} and {helper.pronoun('possessive')} {helper.type} went to {setting.place}."
    )
    world.say(
        f"{hero.id} spotted {item.phrase} and reached for them at once."
    )
    _look_through_binoculars(world)
    _helper_explains(world)
    _safe_choice(world)

    world.facts["resolved"] = True
    world.facts["surprise"] = True
    world.facts["lesson_learned"] = True
    world.facts["cautionary"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    setting: Setting = f["setting"]
    return [
        f'Write a short ghost story for a child named {hero.id} that includes {item.label} and a spooky surprise.',
        f"Tell a cautionary story set at {setting.place} where {hero.id} learns a lesson from {helper.pronoun('possessive')} {helper.type}.",
        f'Write a gentle nighttime story with binoculars, a surprise, and a lesson learned at {setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"What did {hero.id} find near {setting.place}?",
            answer=f"{hero.id} found {item.phrase} near {setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} get startled when looking through the binoculars?",
            answer="The binoculars made an ordinary night scene look like a ghostly surprise before the helper explained it.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn from {helper.pronoun('possessive')} {helper.type}?",
            answer=f"{hero.id} learned that night can make harmless things look spooky, so it is wise to stay close to a helper and look carefully before worrying.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} put the binoculars down, stayed close to {helper.pronoun('possessive')} {helper.type}, and felt safer by the end.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "binoculars": [
        QAItem(
            question="What are binoculars for?",
            answer="Binoculars are for seeing things that are far away more clearly.",
        )
    ],
    "ghost": [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about something that seems mysterious or frightening, even if it turns out to be harmless.",
        )
    ],
    "caution": [
        QAItem(
            question="Why should you stay close to a trusted helper at night?",
            answer="Staying close helps you stay safe and makes it easier to tell whether something is really dangerous or only looks scary in the dark.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"binoculars", "ghost", "caution"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
is_binoculars(O) :- object(O), object_type(O, binoculars).
is_spooky_place(P) :- setting(P).
surprise_story(P, O) :- setting(P), object(O), object_type(O, binoculars).
lesson_learned(P) :- surprise_story(P, O), is_spooky_place(P).
cautionary(P) :- lesson_learned(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.spooky:
            lines.append(asp.fact("spooky", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_type", oid, o.type))
        if o.allows_surprise:
            lines.append(asp.fact("allows_surprise", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show lesson_learned/1. #show cautionary/1. #show surprise_story/2.")
    model = asp.one_model(program)
    pairs = set(asp.atoms(model, "surprise_story"))
    if ("the old lighthouse", "binoculars") in pairs or ("the dusty attic", "binoculars") in pairs or ("the quiet graveyard", "binoculars") in pairs or ("the moonlit dock", "binoculars") in pairs:
        print("OK: ASP twin emits a surprise story with binoculars.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected binocular story shape.")
    return 1


# ---------------------------------------------------------------------------
# Validation / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle cautionary ghost story about binoculars and a spooky surprise.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--object", dest="object_", choices=OBJECTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--name")
    ap.add_argument("--tone", choices=TONES)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    obj = args.object_ or "binoculars"
    if obj != "binoculars":
        raise StoryError("This storyworld only supports binoculars; the surprise depends on looking far away.")

    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(list(HELPERS.keys()))
    name = args.name or rng.choice(HERO_NAMES[gender])
    tone = args.tone or rng.choice(TONES)
    return StoryParams(place=place, object=obj, name=name, gender=gender, helper=helper, tone=tone)


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
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
        print(asp_program("#show surprise_story/2. #show lesson_learned/1. #show cautionary/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show surprise_story/2. #show lesson_learned/1. #show cautionary/1."))
        print("ASP model atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="lighthouse", object="binoculars", name="Mina", gender="girl", helper="mother", tone="surprise"),
            StoryParams(place="attic", object="binoculars", name="Finn", gender="boy", helper="father", tone="lesson learned"),
            StoryParams(place="graveyard", object="binoculars", name="Nora", gender="girl", helper="grandmother", tone="cautionary"),
            StoryParams(place="dock", object="binoculars", name="Theo", gender="boy", helper="grandfather", tone="surprise"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} with {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
