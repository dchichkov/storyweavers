#!/usr/bin/env python3
"""
A small adventure storyworld about a curious child, a creaky house, and the
moral value of helping before judging someone by where they live.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


HERO_NAMES = ["Luna", "Milo", "Nia", "Toby", "Pia", "Sam"]
HELPER_NAMES = ["Aunt June", "Mr. Bell", "Mara", "Uncle Kit", "Ms. Rowan"]
HOUSE_NAMES = ["the old hill house", "the crooked house", "the red-roofed house", "the little hick house"]
TOOLS = ["a lantern", "a rope", "a basket", "a wooden plank"]
PLACES = ["the windy hill", "the blackberry lane", "the creek meadow", "the pine path"]


@dataclass
class StoryParams:
    hero: str
    helper: str
    house: str
    place: str
    tool: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
class Arc:
    task: str
    trouble: str
    first_guess: str
    clue: str
    discovery: str
    child_action: str
    helper_action: str
    repair: str
    result: str
    ending: str
    worried: str
    reply: str
    joke: str


ARCS = [
    Arc(
        task="carry warm bread to the hick house on the hill",
        trouble="a bright window went dark, and a small cry came from behind the house",
        first_guess="the old house was spooky and empty",
        clue="fresh footprints led from the porch toward the bramble shed",
        discovery="a little goat had caught its hoof in a loose fence",
        child_action="held the lantern low and spoke gently to the frightened goat",
        helper_action="used the rope to pull the fence board safely aside",
        repair="they tied the loose board back so no other hoof could get trapped",
        result="the goat trotted home, and the bread reached the hungry family",
        ending="the crooked house glowed with three warm windows while the goat bleated from its tidy pen",
        worried="Should we hurry away from this creaky place?",
        reply="Not yet. The footprints look like a clue, not a warning.",
        joke="The goat gave the fence a very serious head-butt inspection.",
    ),
    Arc(
        task="return a silver key found beside the hick house",
        trouble="the key slipped through a crack in the porch and vanished",
        first_guess="the house had swallowed it",
        clue="a thin whistle rose whenever the wind crossed the porch boards",
        discovery="the key had fallen into a hollow rain barrel under the porch",
        child_action="asked questions instead of blaming the strange old house",
        helper_action="lifted the barrel lid and lowered the basket on a rope",
        repair="they covered the crack with a smooth plank",
        result="the key came up shining and opened the garden gate",
        ending="moonlight flashed on the repaired porch while the gate swung open for the waiting dog",
        worried="That key is gone. Maybe this house keeps what it finds.",
        reply="Let's listen and look carefully before we decide what happened.",
        joke="The rain barrel held the key like a tiny silver soup spoon.",
    ),
    Arc(
        task="find a lost map near the red-roofed hick house",
        trouble="a sudden gust scattered the map pieces across the muddy yard",
        first_guess="the rough-looking house had torn the map",
        clue="one piece was caught on a thorn, but its trail pointed toward the creek",
        discovery="a curious magpie had carried the shiny pieces to its nest",
        child_action="left a bright button as a trade instead of reaching into the nest",
        helper_action="made a safe path with flat stones beside the creek",
        repair="they gathered the map pieces after the magpie flew to the nearby tree",
        result="the map showed a shorter trail around the flooded bank",
        ending="the repaired map rested on the porch, pointing to a sunny path beyond the hick house",
        worried="Those torn pieces make this place look guilty.",
        reply="A clue can point somewhere else. Let's follow it with care.",
        joke="The magpie had excellent taste in treasure and terrible taste in map storage.",
    ),
    Arc(
        task="deliver medicine to a family in the little hick house",
        trouble="the footbridge shook above the rushing creek",
        first_guess="the house stood too far away to help",
        clue="one bridge peg was missing, but a sturdy plank leaned beside the shed",
        discovery="the bridge could be mended without crossing the dangerous gap",
        child_action="counted the safe boards and warned everyone to stay back",
        helper_action="placed the plank across the broken section",
        repair="they tied the plank firmly and tested it with a rolling apple",
        result="the medicine crossed safely and the sick child received it before sunset",
        ending="a small hand waved from the house window beside a blue paper heart",
        worried="The creek is too wild. We may have to turn around.",
        reply="Curiosity helps us find a safe way, but it never means taking a foolish risk.",
        joke="The rolling apple became the bridge's first very round inspector.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curious hick-house adventure storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--house", choices=HOUSE_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        house=args.house or rng.choice(HOUSE_NAMES),
        place=args.place or rng.choice(PLACES),
        tool=args.tool or rng.choice(TOOLS),
    )


def validate(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("hero must not be empty")
    if params.hero == params.helper:
        raise StoryError("hero and helper must have different names")
    if params.tool not in TOOLS:
        raise StoryError(f"unknown tool: {params.tool}")
    if params.house not in HOUSE_NAMES:
        raise StoryError(f"unknown house: {params.house}")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World(params)
    world.add(Entity("hero", "character", params.hero, "child", memes={"curiosity": 1.0}))
    world.add(Entity("helper", "character", params.helper, "adult", memes={"care": 1.0}))
    world.add(Entity("house", "place", params.house, "house", meters={"distance": 1.0}, memes={"mystery": 1.0}))
    world.add(Entity("tool", "thing", params.tool, "tool", meters={"usefulness": 1.0}))
    return world


def choose_arc(params: StoryParams) -> Arc:
    text = "|".join((params.hero, params.helper, params.house, params.place, params.tool))
    value = params.seed if params.seed is not None else sum((i + 1) * ord(c) for i, c in enumerate(text))
    return ARCS[value % len(ARCS)]


def generate_story(world: World) -> None:
    p = world.params
    arc = choose_arc(p)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    house = world.entities["house"]

    world.say(
        f"At the edge of {p.place}, {p.hero} followed {p.helper} toward {p.house}, "
        f"a hick house with a crooked chimney and a bright blue door."
    )
    world.say(
        f"{p.hero} carried {p.tool} and felt a spark of curiosity. "
        f"Their adventure was to {arc.task}."
    )

    world.para()
    world.say(f"Before they reached the porch, {arc.trouble}.")
    world.say(f"{p.helper} whispered, '{arc.worried}'")
    world.say(f"{p.hero} answered, '{arc.reply}'")
    world.say(f"For a moment, {p.hero} guessed that {arc.first_guess}.")
    hero.memes["worry"] = 1.0
    house.memes["misjudged"] = 1.0
    world.facts["first_guess"] = arc.first_guess

    world.para()
    world.say(f"Then curiosity led {p.hero} to notice that {arc.clue}.")
    world.say(f"Together they discovered that {arc.discovery}.")
    world.say(f"{p.hero} {arc.child_action}, while {p.helper} {arc.helper_action}.")
    world.say(arc.joke)
    hero.memes["curiosity"] = 2.0
    house.memes["understood"] = 1.0
    world.facts.update({"clue": arc.clue, "discovery": arc.discovery})

    world.para()
    world.say(f"They repaired the trouble: {arc.repair}.")
    world.say(f"Because they chose kindness instead of judging the hick house, {arc.result}.")
    world.say(f"At sunset, {arc.ending}")
    hero.memes["courage"] = 1.0
    hero.memes["kindness"] = 1.0
    helper.memes["pride"] = 1.0
    world.facts.update(
        {
            "task": arc.task,
            "trouble": arc.trouble,
            "child_action": arc.child_action,
            "helper_action": arc.helper_action,
            "repair": arc.repair,
            "result": arc.result,
            "ending": arc.ending,
            "curiosity": True,
            "moral_value": "helping others instead of judging them",
            "resolved": True,
        }
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an adventure about {p.hero} exploring {p.house} in {p.place} with {p.helper}.",
        f"Show how curiosity helps {p.hero} solve a problem near a hick house without judging people by appearances.",
        "Create a child-facing adventure with a clear moral value: kindness is stronger than suspicion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What was {p.hero}'s adventure near {p.house}?",
            answer=f"{p.hero}'s adventure was to {f['task']}.",
        ),
        QAItem(
            question=f"What did {p.hero} first think about {p.house}'s trouble?",
            answer=f"At first, {p.hero} guessed that {f['first_guess']}, but that guess was wrong.",
        ),
        QAItem(
            question=f"How did curiosity help {p.hero}?",
            answer=f"Curiosity helped {p.hero} notice that {f['clue']} and discover that {f['discovery']}.",
        ),
        QAItem(
            question="What moral value did the adventure show?",
            answer=f"The adventure showed the moral value of {f['moral_value']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The problem was repaired because {f['repair']}. Then {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by asking questions, looking closely, and investigating safely.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good principle that helps guide choices, such as kindness, honesty, or fairness.",
        ),
        QAItem(
            question="Why should people avoid judging a house or person by appearances?",
            answer="Appearances do not tell the whole story, so it is fairer to learn the facts and treat people with respect.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:7} ({entity.kind:9}) {entity.label} {' '.join(parts)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"P{i}: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp

    lines = []
    for house in HOUSE_NAMES:
        lines.append(asp.fact("house", house))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    lines.extend(
        [
            asp.fact("feature", "curiosity"),
            asp.fact("feature", "moral_value"),
            asp.fact("style", "adventure"),
            asp.fact("seed_word", "house"),
            asp.fact("seed_word", "hick"),
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
curious_adventure(H,T) :- house(H), tool(T), feature(curiosity), style(adventure).
kind_choice(H) :- house(H), feature(moral_value).
complete_domain :- seed_word(house), seed_word(hick), feature(curiosity), feature(moral_value).
#show curious_adventure/2.
#show kind_choice/1.
#show complete_domain/0.
"""


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    curious = set(asp.atoms(model, "curious_adventure"))
    kind = set(asp.atoms(model, "kind_choice"))
    complete = set(asp.atoms(model, "complete_domain"))
    expected_curious = {(h, t) for h in HOUSE_NAMES for t in TOOLS}
    expected_kind = {(h,) for h in HOUSE_NAMES}
    if curious == expected_curious and kind == expected_kind and complete == {()}:
        for seed in range(5):
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story or "curiosity" not in sample.story.lower():
                print("Generated story verification failed.")
                return 1
        print("OK: ASP parity and generated stories verified.")
        return 0
    print("Mismatch between ASP and Python registries.")
    return 1


CURATED = [
    StoryParams("Luna", "Aunt June", "the old hill house", "the windy hill", "a lantern"),
    StoryParams("Milo", "Mr. Bell", "the crooked house", "the blackberry lane", "a rope"),
    StoryParams("Nia", "Mara", "the red-roofed house", "the creek meadow", "a basket"),
    StoryParams("Toby", "Uncle Kit", "the little hick house", "the pine path", "a wooden plank"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        model = asp.one_model(asp_program())
        print(f"curious_adventure={len(asp.atoms(model, 'curious_adventure'))}")
        print(f"kind_choice={len(asp.atoms(model, 'kind_choice'))}")
        print(f"complete_domain={len(asp.atoms(model, 'complete_domain'))}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.house}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
