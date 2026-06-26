#!/usr/bin/env python3
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Animal:
    kind: str
    type: str
    label: str
    name: str
    trait: str
    species_sound: str


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    growth_goal: float = 3.0


@dataclass
class Setting:
    place: str
    light: str
    water_source: str


@dataclass
class StoryParams:
    setting: str = "garden"
    hero: str = "bunny"
    friend: str = "turtle"
    plant: str = "seed"
    name: str = "Pip"
    friend_name: str = "Milo"
    seed: Optional[int] = None


ANIMALS = {
    "bunny": Animal(kind="animal", type="bunny", label="bunny", name="Pip", trait="small and quick", species_sound="hop"),
    "turtle": Animal(kind="animal", type="turtle", label="turtle", name="Milo", trait="slow and careful", species_sound="plod"),
    "fox": Animal(kind="animal", type="fox", label="fox", name="Fenn", trait="bright and clever", species_sound="dash"),
    "mouse": Animal(kind="animal", type="mouse", label="mouse", name="Mimi", trait="tiny and brave", species_sound="scurry"),
    "bear": Animal(kind="animal", type="bear", label="bear", name="Bram", trait="gentle and strong", species_sound="stomp"),
}

PLANTS = {
    "seed": Plant(id="seed", label="seed", phrase="a tiny seed", growth_goal=3.0),
    "sprout": Plant(id="sprout", label="sprout", phrase="a tender sprout", growth_goal=2.0),
    "flower": Plant(id="flower", label="flower", phrase="a bright flower", growth_goal=4.0),
}

SETTINGS = {
    "garden": Setting(place="the garden", light="sunny", water_source="watering can"),
    "meadow": Setting(place="the meadow", light="bright", water_source="pond"),
    "yard": Setting(place="the yard", light="warm", water_source="bucket"),
}

NAME_POOL = ["Pip", "Mia", "Toby", "Luna", "Coco", "Penny", "Nori", "Ollie"]
FRIEND_NAMES = ["Milo", "Dora", "Tess", "Puck", "Kiki", "Bram", "Finn", "Mina"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship growth story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    hero = args.hero or rng.choice(list(ANIMALS))
    friend = args.friend or rng.choice([k for k in ANIMALS if k != hero])
    plant = args.plant or rng.choice(list(PLANTS))
    if hero == friend:
        raise StoryError("Hero and friend must be different animals.")
    return StoryParams(
        setting=setting,
        hero=hero,
        friend=friend,
        plant=plant,
        name=args.name or rng.choice(NAME_POOL),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
    )


def _inc(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def predict_growth(world: World, hero: Entity, friend: Entity, plant: Entity) -> float:
    sim = world.copy()
    _care_for_seed(sim, sim.entities[hero.id], sim.entities[friend.id], sim.entities[plant.id], narrate=False)
    return sim.entities[plant.id].meters.get("growth", 0.0)


def _care_for_seed(world: World, hero: Entity, friend: Entity, plant: Entity, narrate: bool = True) -> None:
    if "care" in world.fired:
        return
    world.fired.add("care")
    _inc(plant, "growth", 1.0)
    _inc(hero, "joy", 0.5)
    _inc(friend, "joy", 0.5)
    if narrate:
        world.say(f"They watered the seed together, and the little plant got a bit taller.")


def tell(setting: Setting, hero_cfg: Animal, friend_cfg: Animal, plant_cfg: Plant,
         hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="animal", type=hero_cfg.type, label=hero_cfg.label))
    friend = world.add(Entity(id=friend_name, kind="animal", type=friend_cfg.type, label=friend_cfg.label))
    seed = world.add(Entity(id=plant_cfg.id, kind="plant", type=plant_cfg.id, label=plant_cfg.label))

    _inc(hero, "hope", 1.0)
    _inc(friend, "hope", 1.0)
    _inc(seed, "growth", 0.0)

    world.say(
        f"{hero.name if hasattr(hero, 'name') else hero.id} was a {hero_cfg.trait} {hero_cfg.label} who loved to watch little things grow."
    )
    world.say(
        f"{friend_name} was a {friend_cfg.trait} {friend_cfg.label}, and the two friends liked doing things side by side."
    )
    world.say(
        f"One morning in {setting.place}, they found {plant_cfg.phrase} tucked in the soft dirt."
    )

    world.para()
    world.say(
        f"They planted the seed and waited, but at first it stayed very small."
    )
    _inc(hero, "worry", 1.0)
    _inc(friend, "worry", 1.0)
    if predict_growth(world, hero, friend, seed) < plant_cfg.growth_goal:
        world.say(
            f"{friend_name} looked down and wondered if it would ever become something great."
        )
        world.say(
            f"{hero_name} gave a tiny smile and said they could help it grow by caring for it every day."
        )

    world.para()
    world.say(
        f"Each day they brought water from the {setting.water_source}, and they sat in the {setting.light} light together."
    )
    _care_for_seed(world, hero, friend, seed, narrate=False)
    _inc(seed, "growth", 1.5)
    _inc(hero, "friendship", 1.0)
    _inc(friend, "friendship", 1.0)
    world.say(
        f"The seed drank the water, and its stem stood up straighter."
    )

    world.para()
    _inc(seed, "growth", 2.0)
    _inc(hero, "pride", 1.0)
    _inc(friend, "pride", 1.0)
    world.say(
        f"By the end, the plant had grown into something great: a bright little bloom swaying in the breeze."
    )
    world.say(
        f"{hero_name} and {friend_name} smiled at their happy ending, because their friendship had helped the garden grow too."
    )

    world.facts.update(hero=hero, friend=friend, plant=seed, setting=setting, hero_cfg=hero_cfg, friend_cfg=friend_cfg, plant_cfg=plant_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a child about growth and friendship in {f["setting"].place}.',
        f"Tell a happy ending story where a {f['hero_cfg'].label} and a {f['friend_cfg'].label} help {f['plant_cfg'].phrase} grow into something great.",
        f"Write a gentle story about two animal friends caring for a seed until it becomes a plant.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    plant = f["plant"]
    return [
        QAItem(
            question=f"Who helped the seed grow in {f['setting'].place}?",
            answer=f"{hero.id} and {friend.id} helped the seed grow by watering it and caring for it every day.",
        ),
        QAItem(
            question=f"What did the friends find in the dirt?",
            answer=f"They found {f['plant_cfg'].phrase} tucked in the soft dirt.",
        ),
        QAItem(
            question="What was the ending like?",
            answer="It was a happy ending, because the seed grew into something great and the friends felt proud together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a seed need to grow?",
            answer="A seed usually needs water, light, and care to grow into a plant.",
        ),
        QAItem(
            question="Why do friends help each other?",
            answer="Friends help each other because working together makes hard things easier and more fun.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
    for pid, p in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("growth_goal", pid, int(p.growth_goal)))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,H,F,P) :- setting(S), animal(H), animal(F), H != F, plant(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((s, h, f, p) for s in SETTINGS for h in ANIMALS for f in ANIMALS if h != f for p in PLANTS)
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH")
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.hero], ANIMALS[params.friend], PLANTS[params.plant], params.name, params.friend_name)
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="garden", hero="bunny", friend="turtle", plant="seed", name="Pip", friend_name="Milo"),
            StoryParams(setting="meadow", hero="mouse", friend="fox", plant="sprout", name="Mimi", friend_name="Fenn"),
            StoryParams(setting="yard", hero="bear", friend="bunny", plant="flower", name="Bram", friend_name="Luna"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
