#!/usr/bin/env python3
"""
A self-contained storyworld: a tiny fable about an inning, a blip,
and a self that learns kindness and humor through sound effects.

The world is intentionally small and classical:
- one setting,
- one small cast of typed entities,
- a clear turn in the middle,
- and a resolution that changes the emotional state.

The seed words are woven into the domain:
- inning
- blip
- self

The story style aims for a child-facing fable tone.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "bird", "child", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"foxess", "hareess", "birdess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little green field"
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    kind: str
    text: str
    emoji: str = ""


@dataclass
class StoryParams:
    place: str
    hero: str
    neighbor: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the little green field", affords={"inning"}),
    "orchard": Setting(place="the apple orchard", affords={"inning"}),
    "yard": Setting(place="the sunny yard", affords={"inning"}),
}

HEROES = {
    "fox": Entity(id="Fox", kind="character", type="fox", label="Fox"),
    "hare": Entity(id="Hare", kind="character", type="hare", label="Hare"),
    "bird": Entity(id="Bird", kind="character", type="bird", label="Bird"),
}

NEIGHBORS = {
    "turtle": Entity(id="Turtle", kind="character", type="mouse", label="Turtle"),
    "mouse": Entity(id="Mouse", kind="character", type="mouse", label="Mouse"),
    "rabbit": Entity(id="Rabbit", kind="character", type="hare", label="Rabbit"),
}

OBJECTS = {
    "bell": Entity(id="Bell", kind="thing", type="thing", label="bell", phrase="a small brass bell"),
    "drum": Entity(id="Drum", kind="thing", type="thing", label="drum", phrase="a round little drum"),
    "bat": Entity(id="Bat", kind="thing", type="thing", label="bat", phrase="a smooth wooden bat"),
}

SOUND_EFFECTS = {
    "blip": SoundEffect(kind="blip", text="blip", emoji=""),
    "tap": SoundEffect(kind="tap", text="tap-tap", emoji=""),
    "bong": SoundEffect(kind="bong", text="bong", emoji=""),
    "giggle": SoundEffect(kind="giggle", text="hee-hee", emoji=""),
}


ASP_RULES = r"""
% A fable is reasonable when the inning has a sound, a small hurt,
% and a kindness-based repair.
sound_event(E) :- event(E), sound(E).
blip_turn(E) :- event(E), blip(E).
kindness_fix(E) :- event(E), kind(E).
humor_turn(E) :- event(E), humor(E).
valid_story(P, H, N, O) :- setting(P), hero(H), neighbor(N), object(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for nid in NEIGHBORS:
        lines.append(asp.fact("neighbor", nid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for sid, se in SOUND_EFFECTS.items():
        lines.append(asp.fact("event", sid))
        lines.append(asp.fact("sound", sid))
        if sid == "blip":
            lines.append(asp.fact("blip", sid))
        if sid in {"giggle", "bong"}:
            lines.append(asp.fact("humor", sid))
        if sid in {"tap", "bong"}:
            lines.append(asp.fact("kind", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(place, hero, neighbor, obj) for place in SETTINGS for hero in HEROES for neighbor in NEIGHBORS for obj in OBJECTS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python story space ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python story space.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_sound(rng: random.Random) -> SoundEffect:
    return rng.choice(list(SOUND_EFFECTS.values()))


def tell(setting: Setting, hero_id: str, neighbor_id: str, object_id: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_id, kind="character", type=hero_id.lower(), label=hero_id))
    neighbor = world.add(Entity(id=neighbor_id, kind="character", type=neighbor_id.lower(), label=neighbor_id))
    obj = world.add(Entity(id=object_id, kind="thing", type="thing", label=OBJECTS[object_id].label, phrase=OBJECTS[object_id].phrase))

    hero.memes["pride"] = 1.0
    hero.memes["humor"] = 0.0
    hero.memes["kindness"] = 0.0
    neighbor.memes["hope"] = 0.0
    neighbor.memes["hurt"] = 0.0

    world.say(f"In {setting.place}, {hero.id} loved the hush of the day and the neat little order of things.")
    world.say(f"{hero.id} carried {obj.phrase} as if it were a treasure for the next inning.")

    world.para()
    world.say(f"At the start of the inning, the air was still, and then came a tiny blip from the {obj.label}.")
    world.say(f"{hero.id} blinked. {hero.id} had not meant the blip, but it made {neighbor.id} pause and look sad.")

    neighbor.memes["hurt"] = 1.0
    hero.memes["pride"] += 1.0
    world.say(f"{neighbor.id} said nothing at first, only held {neighbor.pronoun('possessive')} eyes on the ground.")

    world.para()
    world.say(f"{hero.id} noticed the small hurt in {neighbor.id}'s face.")
    hero.memes["kindness"] += 1.0
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    world.say(f"Then {hero.id} laughed a gentle laugh, because the blip sounded more silly than sharp: blip, blip, blip.")

    hero.memes["humor"] += 1.0
    neighbor.memes["hurt"] = 0.0
    neighbor.memes["hope"] += 1.0
    world.say(f'{hero.id} said, "That was a clumsy blip, not a cruel one. Please forgive my self and share the joke."')

    world.para()
    world.say(f"{hero.id} set down {obj.phrase} and offered it to {neighbor.id}.")
    world.say(f"Together they made a happier sound, a warm bong of the {obj.label}, and the inning became a game again.")
    world.say(f"By the end, {hero.id}'s self felt lighter, because kindness had mended the little mistake.")

    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        obj=obj,
        sound="blip",
        place=setting.place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child about an inning, a blip, and a kind self in {f["place"]}.',
        f'Tell a gentle story where {f["hero"].id} makes a blip sound, then repairs the moment with kindness and humor.',
        f'Write a child-facing fable with sound effects that ends with friendship after a small mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    neighbor = world.facts["neighbor"]
    obj = world.facts["obj"]
    return [
        QAItem(
            question=f"Who made the blip sound in the story?",
            answer=f"{hero.id} made the blip sound with {obj.phrase}.",
        ),
        QAItem(
            question=f"Why did {neighbor.id} feel sad for a moment?",
            answer=f"{neighbor.id} felt sad because the blip startled {neighbor.pronoun('object')} and seemed like a mistake at first.",
        ),
        QAItem(
            question=f"What changed the story from a small problem into a happy ending?",
            answer=f"{hero.id} showed kindness, used humor, and shared {obj.phrase} so the two friends could smile together again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blip sound like?",
            answer="A blip is a tiny, quick sound, like something small tapping once.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about another creature and trying to help or comfort them.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the part of a story or joke that makes people smile or laugh gently.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson, often through animals or simple characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about inning, blip, self.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--neighbor", choices=NEIGHBORS)
    ap.add_argument("--object", choices=OBJECTS)
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    neighbor = args.neighbor or rng.choice(list(NEIGHBORS))
    obj = args.object or rng.choice(list(OBJECTS))
    if hero == neighbor:
        raise StoryError("The hero and neighbor must be different characters.")
    return StoryParams(place=place, hero=hero, neighbor=neighbor, object=obj, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero, params.neighbor, params.object)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for row in combos[:20]:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for hero in HEROES:
                for neighbor in NEIGHBORS:
                    if hero == neighbor:
                        continue
                    for obj in OBJECTS:
                        p = StoryParams(place=place, hero=hero, neighbor=neighbor, object=obj, seed=base_seed)
                        samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
