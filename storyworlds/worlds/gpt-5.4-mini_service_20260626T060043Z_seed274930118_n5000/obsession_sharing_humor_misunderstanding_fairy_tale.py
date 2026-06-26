#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/obsession_sharing_humor_misunderstanding_fairy_tale.py
===============================================================================================================================

A small fairy-tale storyworld about obsession, sharing, humor, and misunderstanding.

Premise:
- A character becomes fixated on a beloved object, phrase, or tiny wonder.
- A helper or friend tries to share it, but the obsession makes the hero misread the offer.
- A funny misunderstanding grows into trouble.
- A gentle turn restores sharing and ends with warmth, laughter, and a changed heart.

The world is simulated with meters and memes:
- meters track physical possession, scarcity, and distance
- memes track obsession, joy, confusion, embarrassment, and kindness

The story is authored from the evolving state, not from a frozen template.
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
# Core domain data
# ---------------------------------------------------------------------------

@dataclass
class CharacterSpec:
    name: str
    title: str
    trait: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str


@dataclass
class TreasureSpec:
    label: str
    phrase: str
    tiny_detail: str
    reason: str
    shareable: bool = True


@dataclass
class SceneSpec:
    place: str
    mood_detail: str
    threshold_detail: str


@dataclass
class StoryParams:
    character: str
    treasure: str
    scene: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    title: str = ""
    pronoun_subject: str = "it"
    pronoun_object: str = "it"
    pronoun_possessive: str = "its"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subj(self) -> str:
        return self.pronoun_subject

    def obj(self) -> str:
        return self.pronoun_object

    def pos(self) -> str:
        return self.pronoun_possessive


class World:
    def __init__(self, scene: SceneSpec) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CHARACTERS = {
    "mira": CharacterSpec("Mira", "little maiden", "curious", "she", "her", "her"),
    "robin": CharacterSpec("Robin", "little woodcutter", "cheerful", "he", "him", "his"),
    "elan": CharacterSpec("Elan", "little child", "dreamy", "they", "them", "their"),
    "sora": CharacterSpec("Sora", "little girl", "playful", "she", "her", "her"),
    "tomas": CharacterSpec("Tomas", "little boy", "gentle", "he", "him", "his"),
}

TREASURES = {
    "bell": TreasureSpec("silver bell", "a silver bell with a ribbon", "it shone like moonlight", "the sound kept everyone listening"),
    "spoon": TreasureSpec("gold spoon", "a gold spoon with a tiny handle", "it glimmered in the firelight", "the little one would not let it leave sight"),
    "berry": TreasureSpec("berry tart", "a berry tart on a little plate", "its berries were glossy and bright", "the smell made the hero think only of keeping it"),
    "riddle": TreasureSpec("riddle", "a funny riddle written on a scrap of bark", "the last line tickled the nose", "the answer seemed to live inside the hero's thoughts"),
    "pebble": TreasureSpec("pebble", "a smooth pebble with a spiral mark", "it felt cool as a well in winter", "the shape seemed too marvelous to share at once"),
}

SCENES = {
    "cottage": SceneSpec("the cottage kitchen", "The hearth gave off a sweet warm glow.", "A little table stood near the window."),
    "market": SceneSpec("the village market", "Lanterns swung softly over the stalls.", "A cloth-covered bench waited beside the bread cart."),
    "garden": SceneSpec("the rose garden", "The roses leaned close as if they were listening.", "A stone bench hid under the lavender."),
    "forest": SceneSpec("the pine forest", "The tall trees made a green hush.", "A fallen log lay beside a patch of moss."),
}

HELPERS = ["grandmother", "bard", "fox", "sister", "friend"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

def make_character(spec: CharacterSpec) -> Entity:
    return Entity(
        id=spec.name,
        kind="character",
        label=spec.name,
        title=spec.title,
        pronoun_subject=spec.pronoun_subject,
        pronoun_object=spec.pronoun_object,
        pronoun_possessive=spec.pronoun_possessive,
    )


def make_treasure(spec: TreasureSpec) -> Entity:
    return Entity(
        id=spec.label.replace(" ", "_"),
        kind="thing",
        label=spec.label,
        title=spec.phrase,
    )


def shares_possible(hero: Entity, treasure: Entity, helper: Entity) -> bool:
    return bool(treasure.meters.get("held", 0) >= 1 and treasure.memes.get("obsession", 0) < 3 and helper.kind == "character")


def could_misunderstand(hero: Entity) -> bool:
    return hero.memes.get("obsession", 0) >= 1 and hero.memes.get("confusion", 0) < 2


def predict_sharing(world: World) -> dict[str, bool]:
    sim = world.copy()
    hero = sim.get(sim.facts["hero_id"])
    treasure = sim.get(sim.facts["treasure_id"])
    helper = sim.get(sim.facts["helper_id"])
    # If shared while obsession is high, the hero may fear losing the treasure.
    return {
        "can_share": shares_possible(hero, treasure, helper),
        "likely_misunderstanding": could_misunderstand(hero),
    }


def begin_obsession(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["obsession"] = hero.memes.get("obsession", 0) + 2
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    treasure.meters["held"] = 1
    world.say(
        f"Once in {world.scene.place}, {hero.label} found {hero.pos()} {treasure.label} and loved it at once."
    )
    world.say(
        f"It was so special that {hero.subj()} kept looking at it as if the whole wide world had shrunk to one shining thing."
    )


def explain_fixation(world: World, hero: Entity, treasure: Entity) -> None:
    world.say(
        f"{hero.subj().capitalize()} would not set {treasure.obj()} down, for {hero.pos()} heart had become fixed on {treasure.obj()}."
    )
    world.say(
        f"That made the day feel full of wonder, but also a little too tight, like a ribbon tied in a hard knot."
    )


def helper_offers_sharing(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"Then {helper.label} came near and said, 'Let us share {treasure.obj()} for a while.'"
    )
    world.say(
        f"{helper.subj().capitalize()} smiled in a way that meant well, but {hero.label} did not hear only kindness."
    )


def misunderstand(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 2
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0) + 1
    world.say(
        f"{hero.label} thought {helper.obj()} meant to take {treasure.obj()} away forever, and that was not what was said at all."
    )
    world.say(
        f"Because of that misunderstanding, {hero.subj()} clutched {treasure.obj()} even tighter and made a face as sour as a green apple."
    )


def humor_turn(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["confusion"] = max(0, hero.memes.get("confusion", 0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["humor"] = helper.memes.get("humor", 0) + 1
    world.say(
        f"Then {helper.label} laughed softly and held up a tiny mirror, showing that the 'great theft' was only {helper.pos()} own shadow making a grin."
    )
    world.say(
        f"{hero.label} blinked, then laughed too, because the shadow had looked more dramatic than a dragon in a storybook."
    )


def share_resolution(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["obsession"] = 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 2
    treasure.meters["shared"] = 1
    treasure.meters["held"] = 0
    world.say(
        f"At last {hero.label} opened {hero.pos()} hand and shared {treasure.obj()} with {helper.obj()}."
    )
    world.say(
        f"They took turns with care, and what had felt like a secret treasure became a happy thing for two."
    )


def ending_image(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    world.say(
        f"In the end, {hero.label} still loved {treasure.obj()}, but now {hero.subj()} loved the sharing as well, and that was the finer magic."
    )
    world.say(
        f"The two of them walked on laughing, and the little treasure gleamed brighter because it was no longer alone."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    world = World(scene)
    hero = world.add(make_character(CHARACTERS[params.character]))
    treasure = world.add(make_treasure(TREASURES[params.treasure]))
    helper_spec = CHARACTERS[params.helper] if params.helper in CHARACTERS else CHARACTERS["elan"]
    helper = world.add(make_character(helper_spec))
    world.facts.update(hero_id=hero.id, treasure_id=treasure.id, helper_id=helper.id)

    begin_obsession(world, hero, treasure)
    explain_fixation(world, hero, treasure)

    world.para()
    world.say(scene.mood_detail)
    world.say(scene.threshold_detail)
    helper_offers_sharing(world, hero, helper, treasure)
    misunderstand(world, hero, helper, treasure)

    world.para()
    humor_turn(world, hero, helper, treasure)
    share_resolution(world, hero, helper, treasure)
    ending_image(world, hero, helper, treasure)

    world.facts.update(
        obsession=hero.memes.get("obsession", 0),
        confusion=hero.memes.get("confusion", 0),
        shared=treasure.meters.get("shared", 0) >= 1,
        humor=helper.memes.get("humor", 0) >= 1,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy-tale story about obsession, sharing, humor, and misunderstanding in {world.scene.place}.',
        f"Tell a gentle story where {f['hero_id']} cannot stop thinking about {f['treasure_id'].replace('_', ' ')} until a funny misunderstanding is cleared up.",
        f"Write a child-friendly fairy tale ending with two characters sharing a treasured thing and laughing together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get(f["hero_id"])
    treasure = world.get(f["treasure_id"])
    helper = world.get(f["helper_id"])
    return [
        QAItem(
            question=f"What did {hero.label} become obsessed with in the story?",
            answer=f"{hero.label} became obsessed with {treasure.obj()}, and that made {hero.subj()} hold on very tightly.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding when {helper.label} asked to share?",
            answer=f"{hero.label} thought {helper.obj()} wanted to take {treasure.obj()} away forever, even though {helper.subj()} only wanted to share it for a while.",
        ),
        QAItem(
            question=f"How did the humor help the problem get better?",
            answer=f"The humor helped because {helper.label} showed that the scary-looking moment was only a shadow joke, and then everyone could laugh instead of worry.",
        ),
        QAItem(
            question=f"What changed at the end of the tale?",
            answer=f"At the end, {hero.label} shared {treasure.obj()} with {helper.label}, and the treasure became a happy thing for two instead of one stubborn little secret.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, enjoy, or hold something for a while, so more than one person can take part in it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks words or actions mean one thing, but they really mean something else.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the funny part of a story or moment that makes people smile or laugh.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero_obsessed(H) :- obsession(H, O), O >= 2.
can_share(H, T) :- held(T, 1), hero_obsessed(H), shareable(T).
misunderstanding(H) :- confusion(H, C), C >= 2.
humor_turn(H) :- humor(H, U), U >= 1.
resolved(H, T) :- can_share(H, T), humor_turn(H), shared(T, 1).
valid_story(C, T, S, H) :- character(C), treasure(T), scene(S), helper(H),
                           shareable(T), compatible(C, T, H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("compatible", cid, "any", "any"))
    for tid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if tr.shareable:
            lines.append(asp.fact("shareable", tid))
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for hid in CHARACTERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_rows = sorted(set(asp.atoms(model, "valid_story")))
    python_rows = sorted(valid_triples())
    if clingo_rows == python_rows:
        print(f"OK: clingo gate matches python gate ({len(clingo_rows)} combinations).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_rows - python_rows:
        print("  only in clingo:", sorted(clingo_rows - python_rows))
    if python_rows - clingo_rows:
        print("  only in python:", sorted(python_rows - clingo_rows))
    return 1


def valid_triples() -> list[tuple]:
    out = []
    for c in CHARACTERS:
        for t, tr in TREASURES.items():
            for s in SCENES:
                for h in CHARACTERS:
                    if tr.shareable:
                        out.append((c, t, s, h))
    return out


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about obsession, sharing, humor, and misunderstanding.")
    ap.add_argument("--character", choices=CHARACTERS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--helper", choices=CHARACTERS)
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
    character = args.character or rng.choice(list(CHARACTERS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    scene = args.scene or rng.choice(list(SCENES))
    helper = args.helper or rng.choice([k for k in CHARACTERS if k != character])

    if args.character and args.helper and args.character == args.helper:
        raise StoryError("The helper should be a different character from the hero.")
    return StoryParams(character=character, treasure=treasure, scene=scene, helper=helper)


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:16} ({e.kind:9}) {' '.join(bits)}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(character="mira", treasure="bell", scene="cottage", helper="elan"),
        StoryParams(character="robin", treasure="pebble", scene="forest", helper="sora"),
        StoryParams(character="sora", treasure="berry", scene="garden", helper="tomas"),
        StoryParams(character="elan", treasure="riddle", scene="market", helper="mira"),
        StoryParams(character="tomas", treasure="spoon", scene="cottage", helper="robin"),
    ]


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
        rows = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(rows)} compatible story combinations:\n")
        for row in rows:
            print("  ", row)
        return

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.character} / {p.treasure} / {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
