#!/usr/bin/env python3
"""
A tiny comedy world about a mosquito, an overconfident cremation plan, and
friendship that teaches a better meaning of "accustom."
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    alive: bool = True


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class ComicPlan:
    id: str
    mishap: str
    clue: str
    friend_move: str
    hero_move: str
    punchline: str
    ending: str


SETTING = Setting(
    place="the sunny backyard",
    affords={"friendship", "dialogue", "comedy", "mosquito", "cremate", "accustom"},
)

NAMES = ["Luna", "Milo", "Pip", "Nia", "Toby", "Rae"]
ANIMALS = ["rabbit", "duck", "hedgehog", "goat", "pigeon"]
TRAITS = ["dramatic", "curious", "earnest", "sleepy", "brave"]

PLANS = [
    ComicPlan(
        "tea_kettle",
        "a mosquito landed on the picnic teapot and announced itself as the new whistle",
        "the mosquito only buzzed loudly when someone waved a napkin",
        "held the napkin still and asked the mosquito what it actually wanted",
        "put away the tiny cremation ceremony and offered a saucer of sugar water instead",
        "The mosquito took one sip and declared the saucer a luxury swimming pool.",
        "The friends laughed beside the cool teapot while the mosquito practiced a much less alarming buzz.",
    ),
    ComicPlan(
        "hat_parade",
        "a mosquito marched into the hat parade and mistook a wool hat for a warm volcano",
        "the hat wobbled whenever anyone shouted, so whispering was the safest plan",
        "whispered a welcome instead of swatting at the unexpected parade guest",
        "replaced the plan to cremate the hat with a gentle lift toward a flower",
        "The mosquito saluted, flew three inches, and immediately forgot which direction was up.",
        "The hat parade continued, now with a tiny aerial drummer circling above it.",
    ),
    ComicPlan(
        "lemonade_alarm",
        "a mosquito fell into a lemonade cup and rang the straw like an alarm bell",
        "the bubbles pushed the mosquito toward the rim whenever the cup was tilted slowly",
        "tilted the cup while explaining each move in a calm voice",
        "stopped talking about cremating the sticky straw and used a leaf as a bridge",
        "The mosquito crossed the leaf, then asked whether the bridge came in a larger size.",
        "Everyone shared lemonade while the rescued mosquito learned to avoid cups with umbrellas.",
    ),
    ComicPlan(
        "lantern_mixup",
        "a mosquito mistook a paper lantern for the moon and tried to move into it",
        "the lantern's warm glow attracted the mosquito, but its open bottom offered an easy exit",
        "stood below the lantern and invited the visitor to follow a brighter flower",
        "gave up the idea of cremating the lantern and carried it away from the mosquito's path",
        "The mosquito followed the flower, then complained that the moon had become suspiciously portable.",
        "The lantern glowed over the friends as their new buzzing neighbor settled nearby.",
    ),
    ComicPlan(
        "birthday_candle",
        "a mosquito hovered over a birthday candle and became convinced it was a miniature sun",
        "the flame made the mosquito circle faster, but a shaded leaf gave it a safe resting place",
        "covered the flame with a plate while talking the mosquito through the landing",
        "forgot the dramatic cremation speech and guided the mosquito to the leaf",
        "The mosquito rested, then asked for a birthday cake with no fire and extra crumbs.",
        "The candle stayed safely covered while friendship turned a panic into a party joke.",
    ),
]


@dataclass
class StoryParams:
    name: str
    animal: str
    trait: str
    plan: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comedy story world about a mosquito, friendship, dialogue, and an absurd cremation plan."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--plan", choices=[p.id for p in PLANS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    trait = args.trait or rng.choice(TRAITS)
    plan = args.plan or rng.choice([p.id for p in PLANS])
    return StoryParams(name=name, animal=animal, trait=trait, plan=plan)


def tell(params: StoryParams) -> World:
    plan = next(p for p in PLANS if p.id == params.plan)
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        location=SETTING.place,
        meters={"courage": 0.0, "listening": 0.0},
        memes={"panic": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id="Pip" if params.name != "Pip" else "Nia",
        kind="character",
        type="squirrel",
        label="Pip" if params.name != "Pip" else "Nia",
        location=SETTING.place,
        meters={"helpfulness": 1.0},
        memes={"patience": 1.0},
    ))
    mosquito = world.add(Entity(
        id="mosquito",
        kind="character",
        type="mosquito",
        label="a mosquito",
        location=SETTING.place,
        meters={"safety": 0.0},
        memes={"confidence": 0.0},
    ))
    world.facts.update(hero=hero, friend=friend, mosquito=mosquito, plan=plan)

    world.say(
        f"{hero.id}, a {params.trait} {params.animal}, was arranging a picnic in {SETTING.place} "
        f"when a mosquito {plan.mishap}."
    )
    world.say(
        f"{hero.id} raised a spoon and announced, \"I shall cremate the nuisance before lunch!\""
    )
    world.say(
        f"{friend.id} blinked. \"That is a very large solution for a very small visitor,\" said {friend.id}."
    )
    world.para()

    world.say(f"Then {friend.id} noticed something important: {plan.clue}.")
    world.say(
        f"\"Let us accustom it to a safer place instead,\" said {friend.id}. "
        f"\"Can you help me listen before you act?\""
    )
    world.say(
        f"\"I can listen,\" replied {hero.id}, \"but if it asks for a tiny drum, I am leaving.\""
    )
    world.say(f"{friend.id} {plan.friend_move}.")
    hero.meters["listening"] += 1
    hero.memes["panic"] = 0
    world.say(f"That gave {hero.id} room to think. {hero.id} {plan.hero_move}.")
    hero.meters["courage"] += 1
    hero.memes["friendship"] += 1
    mosquito.meters["safety"] += 1
    mosquito.memes["confidence"] += 1
    world.fired.add("friendship_dialogue_changed_plan")
    world.say(plan.punchline)
    world.para()
    world.say(
        f"\"I suppose friendship is better than fire,\" said {hero.id}. "
        f"\"Much better for everyone, especially the mosquito,\" agreed {friend.id}."
    )
    world.say(plan.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    plan = world.facts["plan"]
    return [
        f"Write a short Comedy story about {hero.id} and a mosquito in {world.setting.place}.",
        f"Use Friendship and Dialogue to show why {hero.id} changes the plan after this clue: {plan.clue}",
        "Include the words cremate, mosquito, and accustom, but make the ending gentle and funny.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mosquito = world.facts["mosquito"]
    plan = world.facts["plan"]
    return [
        QAItem(
            question=f"What did the mosquito do in {world.setting.place}?",
            answer=f"The mosquito {plan.mishap}.",
        ),
        QAItem(
            question=f"What silly plan did {hero.id} announce?",
            answer=f"{hero.id} announced a plan to cremate the mosquito or the thing around it before lunch.",
        ),
        QAItem(
            question=f"What did {friend.id} notice?",
            answer=f"{friend.id} noticed that {plan.clue}.",
        ),
        QAItem(
            question=f"How did Friendship and Dialogue change {hero.id}'s decision?",
            answer=f"{friend.id} spoke calmly and helped {hero.id} listen, so {hero.id} stopped the cremation plan and chose a safer way to help the mosquito.",
        ),
        QAItem(
            question=f"How did {hero.id} accustom the mosquito to a safer place?",
            answer=f"{hero.id} followed the clue, worked with {friend.id}, and guided the mosquito toward a safe place instead of frightening it.",
        ),
        QAItem(
            question="What showed that the problem was over?",
            answer=plan.ending,
        ),
        QAItem(
            question="Why was the story funny?",
            answer=f"It was funny because {hero.id} treated a tiny mosquito problem like a grand fire emergency, then had to admit that listening and friendship worked better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mosquito?",
            answer="A mosquito is a small flying insect with thin legs and a buzzing sound.",
        ),
        QAItem(
            question="What does cremate mean?",
            answer="Cremate means to burn a dead body as part of a funeral practice; it is not a sensible way to solve a tiny living-animal problem.",
        ),
        QAItem(
            question="What does accustom mean?",
            answer="Accustom means to help someone or something become familiar with a new situation gradually and safely.",
        ),
        QAItem(
            question="What is Friendship?",
            answer="Friendship is caring about someone, listening to them, and helping them when a problem appears.",
        ),
        QAItem(
            question="Why is Dialogue useful?",
            answer="Dialogue lets characters share information, change a plan, and understand one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) location={entity.location!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return (
        params.name in NAMES
        and params.animal in ANIMALS
        and params.trait in TRAITS
        and params.plan in {p.id for p in PLANS}
    )


CURATED = [
    StoryParams("Luna", "rabbit", "dramatic", "tea_kettle", 0),
    StoryParams("Milo", "duck", "curious", "lemonade_alarm", 1),
    StoryParams("Nia", "hedgehog", "earnest", "birthday_candle", 2),
    StoryParams("Pip", "goat", "sleepy", "hat_parade", 3),
    StoryParams("Toby", "pigeon", "brave", "lantern_mixup", 4),
]


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The name, animal, trait, or comic plan is not registered in this world.")
    world = tell(params)
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


ASP_RULES = r"""
valid_story(N,A,T,P) :-
    name(N), animal(A), trait(T), plan(P),
    comedy_plan(P),
    friendship_dialogue(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for plan in PLANS:
        lines.append(asp.fact("plan", plan.id))
    for plan in PLANS:
        lines.append(asp.fact("comedy_plan", plan.id))
        lines.append(asp.fact("friendship_dialogue", plan.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {
        (name, animal, trait, plan.id)
        for name in NAMES
        for animal in ANIMALS
        for trait in TRAITS
        for plan in PLANS
    }
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} combinations).")
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "mosquito" not in sample.story:
                print("Generated-story exercise failed.")
                return 1
        print("OK: generated-story exercise passed.")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    seen = set()
    index = 0
    while len(samples) < args.n and index < max(50, args.n * 50):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combinations.")
        for combo in combos[:20]:
            print(combo)
        return

    samples = [generate(p) for p in CURATED] if args.all else build_story_from_args(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
