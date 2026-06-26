#!/usr/bin/env python3
"""
Standalone storyworld: a superhero tale about a mysterious wad, a magical mishap,
and a reconciliation that saves the day.

The world is small and classical: a hero, a helper, a place, a problem, a magical
object, and a repair that changes the ending image. The story is driven by state,
not by template swapping.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    afford: set[str] = field(default_factory=set)
    magic_tone: str = "glowing"


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    danger: str
    mess: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    item: str
    magic: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SCENES = {
    "city": Scene(place="the city rooftops", afford={"float", "glow"}, magic_tone="shimmering"),
    "tower": Scene(place="the watch tower", afford={"float", "glow", "spark"}, magic_tone="bright"),
    "park": Scene(place="the moonlit park", afford={"float", "spark"}, magic_tone="silver"),
}

MAGIC_ITEMS = {
    "wand": MagicItem(
        id="wand",
        label="wand",
        phrase="a little silver wand",
        effect="sparkle into the air",
        danger="scatter the loose bits everywhere",
        mess="sparkly",
    ),
    "cape": MagicItem(
        id="cape",
        label="cape",
        phrase="a red cape with a gold star",
        effect="float above the ground",
        danger="blow the wad away",
        mess="windy",
    ),
    "orb": MagicItem(
        id="orb",
        label="orb",
        phrase="a round glass orb",
        effect="glow like a lantern",
        danger="make the wad twist and wobble",
        mess="glowing",
    ),
}

WADS = {
    "paper_wad": {
        "label": "wad",
        "phrase": "a crumpled wad of paper",
        "type": "wad",
        "kind": "thing",
    },
}

HERO_NAMES = ["Maya", "Nova", "Leo", "Zane", "Aria", "Finn", "Ivy", "Rex"]
HELPER_NAMES = ["Mina", "Jules", "Taro", "Pia", "Owen", "Luna", "Bo", "Skye"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def item_at_risk(magic: MagicItem, place: Scene) -> bool:
    return bool(place.afford & {"float", "glow", "spark"})


def magic_can_disrupt_wad(magic: MagicItem, item: dict) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, scene in SCENES.items():
        for magic_id, magic in MAGIC_ITEMS.items():
            for item_id in WADS:
                if item_at_risk(magic, scene) and magic_can_disrupt_wad(magic, WADS[item_id]):
                    combos.append((place_id, magic_id, item_id))
    return combos


# ---------------------------------------------------------------------------
# Prose engine
# ---------------------------------------------------------------------------

def predict_problem(world: World, magic: MagicItem, wad: Entity) -> dict[str, bool]:
    sim = world.copy()
    sim.get("hero").memes["curiosity"] = sim.get("hero").memes.get("curiosity", 0) + 1
    sim.get("wad").meters["mess"] = sim.get("wad").meters.get("mess", 0) + 1
    sim.get("wad").meters[magic.mess] = sim.get("wad").meters.get(magic.mess, 0) + 1
    return {"problem": True}


def setup_world(params: StoryParams) -> World:
    scene = SCENES[params.place]
    world = World(scene)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    wad_cfg = WADS[params.item]
    wad = world.add(Entity(id="wad", kind="thing", type="wad", label=wad_cfg["label"], phrase=wad_cfg["phrase"], owner=hero.id))
    magic = world.add(Entity(id="magic", kind="thing", type=params.magic, label=MAGIC_ITEMS[params.magic].label, phrase=MAGIC_ITEMS[params.magic].phrase, owner=helper.id))

    world.facts.update(hero=hero, helper=helper, wad=wad, magic=magic, scene=scene, magic_cfg=MAGIC_ITEMS[params.magic])
    return world


def narrate(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    wad: Entity = world.facts["wad"]  # type: ignore[assignment]
    magic: Entity = world.facts["magic"]  # type: ignore[assignment]
    magic_cfg: MagicItem = world.facts["magic_cfg"]  # type: ignore[assignment]
    scene: Scene = world.facts["scene"]  # type: ignore[assignment]

    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["love"] = hero.memes.get("love", 0) + 1

    world.say(
        f"{hero.label} was a little {hero.type} who loved flying over {scene.place} in a bright superhero way."
    )
    world.say(
        f"{hero.label} also noticed {wad.phrase}, and that strange {wad.label} made the day feel like a mystery."
    )
    world.para()

    world.say(
        f"One evening, {helper.label} brought {magic_cfg.phrase}. Its {magic_cfg.effect} made the air {scene.magic_tone}."
    )
    wad.meters["mess"] = wad.meters.get("mess", 0) + 1
    wad.meters[magic_cfg.mess] = wad.meters.get(magic_cfg.mess, 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"But the magic did something tricky: it started to {magic_cfg.danger}, and {wad.label} began to wobble in the wind."
    )

    world.para()
    helper.memes["guilt"] = helper.memes.get("guilt", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"{hero.label} frowned, because the wobbling wad had been meant for a school project, not a disaster."
    )
    world.say(
        f"{helper.label} lowered {helper.pronoun('possessive')} head and said sorry for making the trouble with the magic."
    )

    world.para()
    hero.memes["forgiveness"] = hero.memes.get("forgiveness", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    wad.meters["mess"] = 0
    wad.meters[magic_cfg.mess] = 0
    world.say(
        f"{hero.label} took a breath, forgave {helper.pronoun('object')}, and held the wad steady."
    )
    world.say(
        f"Then {helper.label} used the magic carefully, and this time it only made a soft glow around the wad instead of sending it flying."
    )
    world.say(
        f"By the end, {hero.label} and {helper.label} were smiling together beside the calm little wad, which now sat safe and ready for their project."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    magic: Entity = f["magic"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child about a wad, magic, and reconciliation at {scene.place}.',
        f"Tell a gentle story where {hero.label} and {helper.label} face trouble with {magic.label} and then make up.",
        'Write a small action story that includes the word "wad" and ends with friends working together again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    wad: Entity = f["wad"]  # type: ignore[assignment]
    magic: Entity = f["magic"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    magic_cfg: MagicItem = f["magic_cfg"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was the little hero watching at {scene.place}?",
            answer=f"{hero.label} was watching a crumpled wad of paper, because the wad looked important and a little mysterious.",
        ),
        QAItem(
            question=f"What went wrong when {helper.label} used the magic?",
            answer=f"The magic became tricky and started to {magic_cfg.danger}, so the wad began to wobble instead of staying calm.",
        ),
        QAItem(
            question="How did the two friends fix the problem?",
            answer=f"{hero.label} forgave {helper.label}, and then {helper.label} used the magic carefully so the wad could stay safe.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"At the end, the friends were smiling together, and the wad was calm and ready for their project.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "wad": [
        QAItem(
            question="What is a wad?",
            answer="A wad is a small clump or bundle of something, like crumpled paper or cloth pushed together tightly.",
        )
    ],
    "magic": [
        QAItem(
            question="What does magic usually mean in a story?",
            answer="In a story, magic is something special that can make surprising things happen, like glowing, floating, or transforming.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means two people stop fighting or feeling upset and become friendly again.",
        )
    ],
    "superhero": [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses courage, cleverness, and special powers to help others and solve problems.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("wad", "magic", "reconciliation", "superhero") for item in WORLD_KNOWLEDGE[key]]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- scene(P).
magic(M) :- magic_item(M).
wad(W) :- wad_item(W).

problem(P, M, W) :- scene(P), magic_item(M), wad_item(W), scene_affords(P, float).
reconcile(H, K) :- hero(H), helper(K).
valid_story(P, M, W) :- problem(P, M, W), reconcile(_, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for a in sorted(scene.afford):
            lines.append(asp.fact("scene_affords", sid, a))
    for mid, magic in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic_item", mid))
    for wid in WADS:
        lines.append(asp.fact("wad_item", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show problem/3.")), "problem"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SCENES:
        raise StoryError("Unknown place.")
    if args.item and args.item not in WADS:
        raise StoryError("Unknown item.")
    if args.magic and args.magic not in MAGIC_ITEMS:
        raise StoryError("Unknown magic item.")

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.magic:
        combos = [c for c in combos if c[1] == args.magic]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, magic, item = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        item=item,
        magic=magic,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with wad, magic, and reconciliation.")
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--item", choices=WADS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show problem/3."))
        print(f"{len(asp.atoms(model, 'problem'))} compatible problems")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, magic, item in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                hero_name=HERO_NAMES[0],
                hero_type="girl",
                helper_name=HELPER_NAMES[0],
                helper_type="boy",
                item=item,
                magic=magic,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
