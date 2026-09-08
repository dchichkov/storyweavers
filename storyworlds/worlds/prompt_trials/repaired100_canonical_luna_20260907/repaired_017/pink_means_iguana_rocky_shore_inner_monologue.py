#!/usr/bin/env python3
"""
A tall-tale storyworld about pink clues, an iguana, and a rocky shore.

Luna learns that pink can mean more than a color when an iguana loses its way
among the rocks. Her inner monologue guides a brave choice, and a happy ending
returns the iguana to a warm sunlit ledge.
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
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ImportError:
    from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    location: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Shore:
    place: str = "the rocky shore"
    tide: str = "low tide"
    wind: str = "a roaring sea wind"
    landmark: str = "the tallest black rock"


@dataclass
class World:
    shore: Shore
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        if entity_id not in self.entities:
            raise StoryError(f"Unknown entity: {entity_id}")
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    tide: str
    child_name: str
    child_type: str
    iguana_name: str
    iguana_color: str
    clue_color: str
    seed: Optional[int] = None


PLACES = {
    "rocky_shore": Shore(
        place="the rocky shore",
        tide="low tide",
        wind="a roaring sea wind",
        landmark="the tallest black rock",
    ),
    "pink_cove": Shore(
        place="the rocky shore beside Pink Cove",
        tide="a falling tide",
        wind="a salty gust",
        landmark="a leaning red boulder",
    ),
    "moonlit_point": Shore(
        place="the rocky shore at Moonlit Point",
        tide="a silver low tide",
        wind="a whistling sea wind",
        landmark="the moon-shaped arch",
    ),
}

CHILD_NAMES = ["Luna", "Milo", "Pia", "Nico", "Tess", "Ravi"]
GIRL_NAMES = {"Luna", "Pia", "Tess"}
IGUANA_NAMES = ["Iggy", "Gale", "Pebble", "Ziggy", "Rocco"]
IGUANA_COLORS = ["green", "golden-green", "blue-green"]
PINK_MEANINGS = {
    "kindness": "pink means kindness when someone leaves a bright trail for a creature in trouble",
    "courage": "pink means courage when a small brave heart chooses to help",
    "home": "pink means home when a lost creature can follow it back",
}

THRESHOLD = 1.0


def propagate(world: World) -> None:
    iguana = world.get("iguana")
    child = world.get("child")
    if iguana.meters.get("safe", 0.0) >= THRESHOLD and not world.facts.get("ending_ready"):
        world.facts["ending_ready"] = True
        child.memes["relief"] = 1.0
        iguana.memes["trust"] = 1.0
        world.events.append("The iguana reached the safe ledge.")
        world.say(
            f"{iguana.label} settled beneath the warm ledge, and the rocks seemed to sigh with relief."
        )


def _tall_tale_name(child: Entity, shore: Shore) -> str:
    return (
        f"At {shore.place}, where waves could polish a pebble into a moon, "
        f"{child.id} was searching for a pink shell."
    )


def simulate(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown shore setting: {params.place}")
    if params.child_name == params.iguana_name:
        raise StoryError("The child and iguana must have different names.")
    if params.clue_color != "pink":
        raise StoryError("This story domain requires a pink clue.")
    if params.iguana_color not in IGUANA_COLORS:
        raise StoryError(f"Iguana color must be one of: {', '.join(IGUANA_COLORS)}")

    shore = PLACES[params.place]
    world = World(shore)
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_type,
            label=params.child_name,
            location=shore.place,
        )
    )
    iguana = world.add(
        Entity(
            id="iguana",
            kind="animal",
            type="iguana",
            label=f"{params.iguana_name}, the {params.iguana_color} iguana",
            location="between two slippery rocks",
        )
    )
    pink_ribbon = world.add(
        Entity(
            id="pink_ribbon",
            kind="thing",
            type="clue",
            label="a pink ribbon",
            location="beside a tide pool",
            owner=child.id,
        )
    )
    sunstone = world.add(
        Entity(
            id="sunstone",
            kind="thing",
            type="stone",
            label="a warm rose-colored stone",
            location=shore.landmark,
        )
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    meaning_key = rng.choice(list(PINK_MEANINGS))
    meaning = PINK_MEANINGS[meaning_key]
    world.facts.update(
        child=child,
        iguana=iguana,
        pink_ribbon=pink_ribbon,
        sunstone=sunstone,
        meaning_key=meaning_key,
        meaning=meaning,
        shore=shore,
        resolved=False,
    )

    world.say(_tall_tale_name(child, shore))
    world.say(
        f"The {shore.wind} blew so fiercely that it made the tide pools wobble "
        f"and sent {pink_ribbon.label} fluttering like a tiny flag."
    )
    world.say(
        f"Then {child.id} heard a scratch-scratch-scratch from {iguana.location}. "
        f"{iguana.label.capitalize()} had climbed into a narrow crack and could not find the sunny path out."
    )
    world.para()

    iguana.memes["fear"] = 1.0
    iguana.meters["trapped"] = 1.0
    child.memes["worry"] = 1.0
    world.say(
        f"{child.id} crouched beside the rocks. In {child.id}'s inner monologue came a worried thought: "
        f"\"I must not pull too hard. A frightened iguana needs a gentle way home.\""
    )
    world.say(
        f"\"Are you hurt, {iguana.label.split(',')[0]}?\" {child.id} asked. "
        f"\"Blink twice if you can hear me.\""
    )
    world.say(
        f"The iguana blinked twice. \"I hear you,\" {child.id} said, "
        f"\"so I will make a path instead of making a fuss.\""
    )
    world.para()

    child.memes["courage"] = 1.0
    world.say(
        f"{child.id} tied {pink_ribbon.label} to three low stones, then carried the "
        f"{sunstone.label} from {shore.landmark} to the edge of the crack."
    )
    pink_ribbon.meters["markers"] = 1.0
    sunstone.meters["warmth"] = 1.0
    iguana.meters["guided"] = 1.0
    world.say(
        f"\"Pink means {meaning_key},\" {child.id} told the iguana. "
        f"\"Follow the pink flutter and the warm stone. They will show you the safe way.\""
    )
    world.say(
        f"{iguana.label.capitalize()} stretched one claw, then another. "
        f"The pink markers turned a jumble of rocks into a road no taller than a spoon."
    )
    world.para()

    iguana.location = "the sunlit ledge"
    iguana.meters["safe"] = 1.0
    iguana.meters["trapped"] = 0.0
    child.memes["joy"] = 1.0
    world.say(
        f"At last, {iguana.label} scrambled free and climbed onto the sunlit ledge. "
        f"It lifted its chin so proudly that even the sea seemed to cheer."
    )
    world.say(
        f"\"You made it!\" {child.id} cried. The iguana answered with a slow golden blink, "
        f"as if it understood every word."
    )
    propagate(world)
    world.para()

    world.facts["resolved"] = True
    world.say(
        f"From that day on, children at {shore.place} said {meaning}. "
        f"{child.id} kept the pink ribbon tied to the first marker, where it danced safely above the waves."
    )
    world.say(
        f"And whenever {iguana.label.split(',')[0]} basked beside the rose-colored stone, "
        f"the rocky shore looked a little brighter, as though happiness had learned to shine pink."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    iguana: Entity = world.facts["iguana"]
    return [
        f"Write a tall tale set at {world.shore.place} where {child.id} helps {iguana.label}.",
        f"Use pink as a meaningful clue, include inner monologue, and give the iguana a happy ending.",
        "Build the middle around a dangerous rocky-shore problem that is solved through gentle observation rather than force.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    iguana: Entity = world.facts["iguana"]
    ribbon: Entity = world.facts["pink_ribbon"]
    meaning_key = world.facts["meaning_key"]
    return [
        QAItem(
            question=f"Why was {iguana.label} in trouble?",
            answer=f"{iguana.label.capitalize()} had climbed into a narrow crack between slippery rocks and could not find the sunny path out.",
        ),
        QAItem(
            question=f"How did {child.id} help the iguana?",
            answer=f"{child.id} tied {ribbon.label} to low stones and used a warm rose-colored stone to mark a gentle, safe route to the sunlit ledge.",
        ),
        QAItem(
            question="What did pink mean in the story?",
            answer=f"Pink meant {meaning_key}: {world.facts['meaning']}.",
        ),
        QAItem(
            question=f"How did the story end for {iguana.label}?",
            answer=f"{iguana.label.capitalize()} escaped to the sunlit ledge, trusted the child, and basked beside the rose-colored stone while the pink ribbon danced above the waves.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an iguana?",
            answer="An iguana is a sun-loving lizard with strong claws, a long tail, and a body that can use warmth to become active.",
        ),
        QAItem(
            question="Why should someone avoid pulling a trapped animal?",
            answer="Pulling can frighten or injure an animal, so a calm person should make space, guide it gently, and ask a trusted adult for help when needed.",
        ),
        QAItem(
            question="What is a rocky shore?",
            answer="A rocky shore is a coast where waves wash around stones, tide pools, cliffs, and ledges instead of a broad sandy beach.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C, I, R) :- child(C), iguana(I), pink_clue(R), notices(C, I), marks(R, I).
safe(I) :- iguana(I), guided(I), warm_path(I).
happy_ending(C, I) :- child(C), iguana(I), safe(I), helps(C, I).
#show reasonable/3.
#show safe/1.
#show happy_ending/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    lines.extend(
        [
            asp.fact("child", "child"),
            asp.fact("iguana", "iguana"),
            asp.fact("pink_clue", "pink_ribbon"),
            asp.fact("notices", "child", "iguana"),
            asp.fact("marks", "pink_ribbon", "iguana"),
            asp.fact("guided", "iguana"),
            asp.fact("warm_path", "iguana"),
            asp.fact("helps", "child", "iguana"),
        ]
    )
    for place_id in PLACES:
        lines.append(asp.fact("shore", place_id))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    extra = show if show else ""
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        from storyworlds.asp import atoms
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    safe = atoms(model, "safe")
    endings = atoms(model, "happy_ending")
    reasonable = atoms(model, "reasonable")
    if not safe or not endings or not reasonable:
        print("ASP verification failed: expected safety, reasonableness, and happy ending atoms.")
        return 1
    sample = generate(
        StoryParams(
            place="rocky_shore",
            tide="low tide",
            child_name="Luna",
            child_type="girl",
            iguana_name="Iggy",
            iguana_color="green",
            clue_color="pink",
            seed=17,
        )
    )
    required = ("pink", "iguana", "rocky shore")
    if any(word not in sample.story.lower() for word in required):
        print("Python verification failed: required story words are missing.")
        return 1
    if "inner monologue" in sample.story.lower():
        print("Python verification failed: scaffold phrase leaked into story.")
        return 1
    if not sample.world.facts.get("resolved"):
        print("Python verification failed: story did not resolve.")
        return 1
    print(
        f"OK: ASP parity passed with {len(reasonable)} reasonable atom(s), "
        f"{len(safe)} safe atom(s), and {len(endings)} happy ending atom(s)."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall-tale pink iguana storyworld on a rocky shore."
    )
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--tide", default=None)
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--iguana-name", choices=IGUANA_NAMES)
    parser.add_argument("--iguana-color", choices=IGUANA_COLORS)
    parser.add_argument("--clue-color", choices=["pink"], default="pink")
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
    place = args.place or rng.choice(list(PLACES))
    shore = PLACES[place]
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    iguana_name = args.iguana_name or rng.choice(IGUANA_NAMES)
    if child_name == iguana_name:
        raise StoryError("The child and iguana must have different names.")
    tide = args.tide or shore.tide
    iguana_color = args.iguana_color or rng.choice(IGUANA_COLORS)
    return StoryParams(
        place=place,
        tide=tide,
        child_name=child_name,
        child_type="girl" if child_name in GIRL_NAMES else "boy",
        iguana_name=iguana_name,
        iguana_color=iguana_color,
        clue_color=args.clue_color or "pink",
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: type={entity.type}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
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
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            print("\n".join(str(atom) for atom in model))
        except ImportError as exc:
            raise SystemExit(f"ASP mode requires clingo: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                place="rocky_shore",
                tide="low tide",
                child_name="Luna",
                child_type="girl",
                iguana_name="Iggy",
                iguana_color="green",
                clue_color="pink",
                seed=101,
            ),
            StoryParams(
                place="pink_cove",
                tide="a falling tide",
                child_name="Milo",
                child_type="boy",
                iguana_name="Pebble",
                iguana_color="golden-green",
                clue_color="pink",
                seed=202,
            ),
            StoryParams(
                place="moonlit_point",
                tide="a silver low tide",
                child_name="Pia",
                child_type="girl",
                iguana_name="Ziggy",
                iguana_color="blue-green",
                clue_color="pink",
                seed=303,
            ),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(base_seed + index))
            for index in range(max(0, args.n))
        ]

    samples = [generate(params) for params in params_list]
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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
