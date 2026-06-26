#!/usr/bin/env python3
"""
A small superhero-story world about a clutz, a cockatiel, a shared rescue plan,
and a finale that proves the lesson learned.

Seed inspiration:
- finale
- cockatiel
- clutz

Narrative instruments:
- Foreshadowing
- Sharing
- Lesson Learned
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Scene:
    place: str = "the skyline"
    crowd: str = "the plaza"


@dataclass
class HeroSpec:
    name: str
    gender: str
    trait: str
    cape_color: str


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    bird: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _sig(*parts) -> tuple:
    return tuple(parts)


def _rule_tumble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("clumsy", 0) < 1:
            continue
        if e.meters.get("gear_drop", 0) < 1:
            continue
        sig = _sig("tumble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["panic"] = e.memes.get("panic", 0) + 1
        out.append(f"{e.id} almost stumbled when the crowd gasped.")
    return out


def _rule_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    bird = world.entities.get("bird")
    if not hero or not bird:
        return out
    if hero.meters.get("share_cage", 0) < 1:
        return out
    sig = _sig("share", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["care"] = hero.memes.get("care", 0) + 1
    bird.meters["safe"] = bird.meters.get("safe", 0) + 1
    out.append("The shared cage kept the cockatiel safe and calm.")
    return out


def _rule_finale(world: World) -> list[str]:
    hero = world.entities.get("hero")
    bird = world.entities.get("bird")
    if not hero or not bird:
        return []
    if hero.meters.get("rescue_done", 0) < 1:
        return []
    sig = _sig("finale")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["lesson"] = hero.memes.get("lesson", 0) + 1
    return ["__finale__"]


RULES = [_rule_tumble, _rule_share, _rule_finale]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__finale__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["rescue_done"] = 1
    propagate(sim, narrate=False)
    return sim.get("bird").meters.get("safe", 0) >= 1


def build_story_world(params: StoryParams) -> World:
    scene = SCENE_REGISTRY[params.place]
    world = World(scene)
    hero_spec = HEROES[params.hero]
    side_spec = SIDEKICKS[params.sidekick]
    bird_spec = BIRDS[params.bird]

    hero = world.add(Entity(
        id="hero", kind="character", type=hero_spec.gender, label=hero_spec.name,
        phrase=f"young hero {hero_spec.name}",
        meters={"energy": 1.0}, memes={"brave": 1.0, "clumsy": 1.0},
    ))
    side = world.add(Entity(
        id="sidekick", kind="character", type=side_spec.gender, label=side_spec.name,
        phrase=f"bright sidekick {side_spec.name}",
        meters={"energy": 1.0}, memes={"helpful": 1.0},
    ))
    bird = world.add(Entity(
        id="bird", kind="character", type="bird", label=bird_spec.name,
        phrase=f"cockatiel {bird_spec.name}",
        meters={"wings": 1.0}, memes={"restless": 1.0},
    ))
    helmet = world.add(Entity(
        id="helmet", type="gear", label="signal helmet",
        phrase="a shiny signal helmet", owner=hero.id,
        meters={"shine": 1.0},
    ))
    cage = world.add(Entity(
        id="cage", type="gear", label="shared cage",
        phrase="a small shared cage with a soft latch", owner=bird.id,
        meters={"size": 1.0},
    ))

    world.say(f"At {scene.place}, {hero.label} the clutz kept checking the sky.")
    world.say(f"{hero.label} loved helping people, but {hero.pronoun().capitalize()} often dropped things when the wind picked up.")
    world.say(f"That was why {side.label} kept the signal helmet close and watched the cockatiel, {bird.label}.")
    world.say(f"The bird's bright feathers were a tiny clue that something big would happen before the finale.")

    world.para()
    world.say(f"One afternoon, the rescue show began at {scene.crowd}.")
    world.say(f"{hero.label} wanted to swing in with the helmet, but {hero.pronoun('possessive')} hands fumbled it.")
    world.say(f"It bounced once, then rolled toward the stage lights.")

    world.para()
    world.say(f"{side.label} called, \"Share the plan! I can hold the helmet while you save the bird.\"")
    hero.meters["share_cage"] = 1
    world.say(f"Together they shared the job: one steadied the cage, and the other guided {bird.label} away from the edge.")
    bird.carried_by = hero.id
    world.say(f"The cockatiel hopped into the safe cage instead of flapping into the crowd.")

    hero.meters["gear_drop"] = 1
    propagate(world, narrate=True)

    world.para()
    hero.meters["rescue_done"] = 1
    propagate(world, narrate=True)
    world.say(f"In the finale, {hero.label} lifted the helmet, {side.label} smiled, and {bird.label} chirped from the shared cage.")
    world.say("The clutz had not become perfect, but the hero had learned how sharing made brave work go better.")

    world.facts.update(
        hero=hero,
        sidekick=side,
        bird=bird,
        helmet=helmet,
        cage=cage,
        scene=scene,
        predicted_safe=predict_outcome(world),
        lesson="Sharing can turn a clumsy mistake into a team rescue.",
    )
    return world


SCENE_REGISTRY = {
    "plaza": Scene(place="the city plaza", crowd="the busy plaza"),
    "rooftop": Scene(place="the high rooftop", crowd="the windy rooftop"),
    "harbor": Scene(place="the harbor dock", crowd="the dockside stage"),
}

HEROES = {
    "nova": HeroSpec(name="Nova", gender="girl", trait="bold", cape_color="red"),
    "bolt": HeroSpec(name="Bolt", gender="boy", trait="quick", cape_color="blue"),
    "glow": HeroSpec(name="Glow", gender="girl", trait="bright", cape_color="gold"),
}

SIDEKICKS = {
    "mira": HeroSpec(name="Mira", gender="girl", trait="steady", cape_color="green"),
    "tate": HeroSpec(name="Tate", gender="boy", trait="smart", cape_color="orange"),
}

BIRDS = {
    "pearl": HeroSpec(name="Pearl", gender="bird", trait="curious", cape_color="white"),
    "coco": HeroSpec(name="Coco", gender="bird", trait="noisy", cape_color="yellow"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h, b) for p in SCENE_REGISTRY for h in HEROES for b in BIRDS]


@dataclass
class StoryState:
    world: World
    hero: Entity
    sidekick: Entity
    bird: Entity
    helmet: Entity
    cage: Entity


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short superhero story for a young child about a clutz, a cockatiel, and a rescue finale.",
        f"Tell a gentle action story where {f['hero'].label} must share the plan so the cockatiel stays safe.",
        "Write a story with foreshadowing, sharing, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    side: Entity = f["sidekick"]
    bird: Entity = f["bird"]
    return [
        QAItem(
            question=f"Why did {hero.label} need help during the rescue show?",
            answer=f"{hero.label} was a clutz and kept fumbling the signal helmet, so {side.label} had to help steady the plan.",
        ),
        QAItem(
            question=f"What did {hero.label} and {side.label} share?",
            answer=f"They shared the rescue job: one held the helmet while the other guided {bird.label}, the cockatiel, into the safe cage.",
        ),
        QAItem(
            question="What lesson was learned by the end?",
            answer=f"The lesson learned was that sharing can turn a clumsy mistake into a better team rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cockatiel?",
            answer="A cockatiel is a small pet parrot with a crest on its head. It can chirp, whistle, and flutter around when it gets excited.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives tiny hints early on about something important that will happen later, so the ending feels connected.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing is helpful because more than one person can do the job, and the work becomes easier and kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid_scene(P,H,B) :- scene(P), hero(H), bird(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SCENE_REGISTRY:
        lines.append(asp.fact("scene", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for b in BIRDS:
        lines.append(asp.fact("bird", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_scene/3."))
    return sorted(set(asp.atoms(model, "valid_scene")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(a - p))
    print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: a clutz, a cockatiel, and a shared rescue finale.")
    ap.add_argument("--place", choices=SCENE_REGISTRY)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--bird", choices=BIRDS)
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
    place = args.place or rng.choice(list(SCENE_REGISTRY))
    hero = args.hero or rng.choice(list(HEROES))
    side = args.sidekick or rng.choice(list(SIDEKICKS))
    bird = args.bird or rng.choice(list(BIRDS))
    return StoryParams(hero=hero, sidekick=side, bird=bird, place=place)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
    StoryParams(hero="nova", sidekick="mira", bird="pearl", place="plaza"),
    StoryParams(hero="bolt", sidekick="tate", bird="coco", place="rooftop"),
    StoryParams(hero="glow", sidekick="mira", bird="coco", place="harbor"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_scene/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
