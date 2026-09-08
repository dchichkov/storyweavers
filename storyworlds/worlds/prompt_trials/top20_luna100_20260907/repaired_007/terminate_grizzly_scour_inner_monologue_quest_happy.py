#!/usr/bin/env python3
"""
A tiny superhero storyworld about a brave child who must scour a grizzly
mountain cave before a magical danger can terminate the town's festival.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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
class QuestArc:
    key: str
    danger: str
    object_name: str
    obstacle: str
    method: str
    ending_image: str


ARCS = (
    QuestArc(
        "crystal_bell",
        "a grizzly shadow-beast",
        "the sunrise bell",
        "a grizzly shadow-beast guarded the bell in a smoky cave",
        "scour the cave for the loose bell rope and ring it",
        "the bell rang over the valley, and the grizzly shadow curled into a friendly bear-shaped cloud",
    ),
    QuestArc(
        "moon_lantern",
        "a grizzly fog",
        "the moon lantern",
        "a grizzly fog swallowed the lantern beneath a rocky ledge",
        "scour the ledge with a silver cape and reflect moonlight onto the lantern",
        "the lantern shone again, and the grizzly fog became soft clouds above the happy town",
    ),
    QuestArc(
        "golden_map",
        "a grizzly mountain rumble",
        "the golden map",
        "a grizzly rumble buried the map under pebbles and pine needles",
        "scour the warm stones with a hero broom and follow the map's bright trail",
        "the map opened a safe path home, while golden arrows danced along the mountain",
    ),
    QuestArc(
        "rainbow_shield",
        "a grizzly storm",
        "the rainbow shield",
        "a grizzly storm pinned the shield inside a thorny ravine",
        "scour the ravine with careful hands and lift the shield with a wind-powered glove",
        "the shield spread rainbow light across the storm, and every raindrop sparkled",
    ),
)


PLACES = {
    "mountain": Place("mountain", "the Thunder Mountain trail", {"outdoors", "quest"}),
    "cave": Place("cave", "the Echoing Cave", {"underground", "quest"}),
    "valley": Place("valley", "the Sunbeam Valley", {"town", "quest"}),
}

NAMES = {
    "boy": ["Luna", "Milo", "Kai", "Theo"],
    "girl": ["Luna", "Maya", "Zoe", "Nia"],
}


@dataclass
class StoryParams:
    place: str = "mountain"
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    hero_gender: str = "girl"
    helper_gender: str = "animal"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}. Choose a listed quest place.")
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("The hero and helper both need names.")
    if params.hero_name.lower() == params.helper_name.lower():
        raise StoryError("The hero and helper need different names.")

    rng = random.Random(params.seed)
    arc = ARCS[rng.randrange(len(ARCS))]
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name))
    helper = world.add(Entity(params.helper_name, "helper", "bear", params.helper_name))
    danger = world.add(Entity("danger", "threat", "magic", arc.danger))
    treasure = world.add(Entity("quest_object", "object", "relic", arc.object_name))

    hero.memes["courage"] = 1
    hero.memes["doubt"] = 1
    helper.memes["loyalty"] = 1
    danger.meters["active"] = 1
    treasure.meters["hidden"] = 1
    place.meters["festival_safe"] = 0

    world.say(
        f"On {place.label}, {hero.label} wore a bright cape and watched the town's festival lights."
    )
    world.say(
        f"{helper.label}, a small grizzly bear with a red scarf, stood beside {hero.label}."
    )
    world.para()

    world.say(
        f"A warning boomed from the rocks: if {treasure.label} stayed hidden, the grizzly danger would terminate the festival before sunset."
    )
    world.say(
        f'"I feel worried," {hero.label} whispered inside, "but a hero can be worried and still begin a quest."'
    )
    world.say(
        f'"We will scour every corner together," said {helper.label}. "{hero.label}, you look high, and I will look low."'
    )
    world.para()

    hero.memes["courage"] += 2
    hero.memes["doubt"] = 0
    helper.memes["loyalty"] += 1
    treasure.meters["hidden"] = 0
    treasure.meters["found"] = 1
    danger.meters["active"] = 0
    place.meters["festival_safe"] = 1
    hero.meters["quest_complete"] = 1
    helper.meters["helped"] = 1

    world.say(
        f"They scoured {place.label}: {hero.label} lifted a flat stone while {helper.label} brushed away the dust with his scarf."
    )
    world.say(
        f"At last, they found {treasure.label}. {hero.label} used the hero gear, and {helper.label} held the path steady."
    )
    world.say(
        f'"You did not have to be fearless," said {helper.label}. "You only had to keep going."'
    )
    world.say(
        f'"Then let us save the festival!" said {hero.label}, and together they completed the quest.'
    )
    world.para()

    world.say(f"{arc.ending_image.capitalize()}.")
    world.say(
        f"The people cheered for {hero.label} and {helper.label}, and the festival glowed brighter because their brave hearts worked together."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        danger=danger,
        treasure=treasure,
        place=place,
        arc=arc,
        threat=arc.danger,
        method=arc.method,
        result=arc.ending_image,
        quest_complete=True,
        festival_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly superhero story using the words terminate, grizzly, and scour.",
        f"Tell a quest story in which {f['hero'].label} and {f['helper'].label} stop {f['threat']} and save a festival.",
        "Include a brief inner monologue, a spoken exchange, and a happy ending proving the danger has passed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    return [
        QAItem(
            "What danger threatened the festival?",
            f"{f['threat'].capitalize()} threatened to terminate the festival before sunset."
        ),
        QAItem(
            "How did the heroes complete their quest?",
            f"{hero} and {helper} scoured {f['place'].label}; {f['method']}. This uncovered the important object and made the festival safe."
        ),
        QAItem(
            "How did the story show a happy ending?",
            f"{f['result'].capitalize()}. The danger ended, and the festival glowed brighter as the people cheered."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey or challenge in which someone works toward an important goal."
        ),
        QAItem(
            "What does scour mean?",
            "To scour means to search a place very carefully, looking in every corner."
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is a character's private thoughts or feelings that the reader can hear."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id}: meters={meters} memes={memes}")
    lines.append(f"  place: festival_safe={world.place.meters['festival_safe']}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_ready :- hero(H), helper(K), different(H,K), scour_ready, object_found.
different(H,K) :- hero(H), helper(K), H != K.
object_found :- quest_object(O), found(O).
festival_safe :- quest_ready.
happy_ending :- festival_safe.
#show quest_ready/0.
#show festival_safe/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("hero", "hero"),
        asp.fact("helper", "helper"),
        asp.fact("quest_object", "relic"),
        asp.fact("found", "relic"),
        asp.fact("scour_ready"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        names = {str(symbol) for symbol in model}
        required = {"quest_ready", "festival_safe", "happy_ending"}
        if not required.issubset(names):
            print("ASP parity check failed.")
            return 1
        params = StoryParams(seed=3)
        sample = generate(params)
        if not sample.story.strip() or not sample.world.facts["festival_safe"]:
            print("Generation smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: Python and ASP quest checks passed.")
    return 0


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest with a grizzly danger.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-gender", choices=["boy", "girl"])
    parser.add_argument("--helper-gender", choices=["animal"])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(["Luna", "Maya", "Zoe", "Nia", "Milo"])
    helper = args.helper or rng.choice(["Pip", "Bramble", "Cocoa", "Bear"])
    if hero.lower() == helper.lower():
        helper = "Pip"
    return StoryParams(
        place=place,
        hero_name=hero,
        helper_name=helper,
        hero_gender=args.hero_gender or "girl",
        helper_gender=args.helper_gender or "animal",
    )


CURATED = [
    StoryParams("mountain", "Luna", "Pip", seed=11),
    StoryParams("cave", "Maya", "Bramble", seed=22),
    StoryParams("valley", "Zoe", "Cocoa", seed=33),
]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
