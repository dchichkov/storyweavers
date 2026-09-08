#!/usr/bin/env python3
"""A small adventure storyworld about a massive piglet and a brave repair."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("size", "strength", "risk", "distance", "damage"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "courage", "trust", "joy", "worry"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


@dataclass
class StoryParams:
    place: str
    hero: str
    piglet_name: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Conflict:
    title: str
    trouble: str
    first_guess: str
    clue: str
    discovery: str
    plan: str
    obstacle: str
    repair: str
    outcome: str
    lesson: str
    ending: str


CONFLICTS = [
    Conflict(
        "the fallen bridge",
        "a massive piglet had wandered onto a narrow wooden bridge, and one plank cracked beneath its muddy hoof",
        "the piglet was too heavy for anyone to move",
        "fresh hoofprints led to a berry patch on the far bank",
        "the piglet was frightened by a buzzing cart and had rushed onto the bridge",
        "guide the piglet back with apples while a helper steadied the bridge rope",
        "the piglet backed toward the broken plank whenever the cart buzzed",
        "covered the cart, spoke softly, and laid a wide mat over the soundest planks",
        "the piglet crossed safely and returned to its pen for a calm meal",
        "A large problem can become manageable when people learn what is causing the fear",
        "the repaired bridge shone over the creek while the piglet crunched an apple",
    ),
    Conflict(
        "the hilltop gate",
        "a massive piglet had pushed a farm gate off its hinges and blocked the trail to the hilltop bell",
        "the gate needed a strong adult to lift it",
        "the hinge pins were buried in soft mud rather than bent",
        "rain had loosened the ground while the piglet searched for a cool place",
        "dig around the pins, cool the piglet with water, and pull the gate with a rope",
        "the piglet kept nudging the gate whenever thunder rolled",
        "gave the piglet a shady stall and reset the gate after the storm passed",
        "the bell rang before sunset and the piglet rested safely away from the road",
        "Understanding a creature's need can solve a conflict better than pushing harder",
        "the hilltop bell rang as the massive piglet slept beneath a striped shade cloth",
    ),
    Conflict(
        "the orchard barrel",
        "a massive piglet had rolled an empty barrel into the orchard path and now stood guard beside it",
        "the piglet wanted to fight anyone who came near",
        "a torn sack of grain was trapped under the barrel",
        "the piglet was protecting food that had spilled where it could not reach",
        "slide a board beneath the barrel and move the grain sack into a clean trough",
        "the barrel rocked whenever the board touched a stone",
        "placed stones under the barrel, lifted it slowly, and cleared the grain",
        "the path opened and the piglet followed the grain to the trough",
        "A guarded thing may be a need asking for help",
        "sunlight returned to the orchard path as the piglet snuffled beside the full trough",
    ),
    Conflict(
        "the river raft",
        "a massive piglet had climbed onto a small raft and drifted away from the meadow bank",
        "the raft would tip if anyone stepped aboard",
        "a floating rope still connected the raft to a willow root",
        "the piglet had followed a bright red bucket into the shallow current",
        "pull the rope from shore and lure the piglet with a basket of pears",
        "the current tugged harder when a branch caught the rope",
        "free the branch with a long pole before drawing the raft to shore",
        "the piglet stepped onto dry grass and the raft was tied safely",
        "A calm plan can turn a drifting danger toward solid ground",
        "the massive piglet shook river drops from its ears beside the tied raft",
    ),
    Conflict(
        "the lantern tunnel",
        "a massive piglet had wedged itself inside a tunnel beneath the old trail",
        "the tunnel was too dark and narrow to enter",
        "the piglet's muddy nose pointed toward a warm lantern at the far opening",
        "it was trying to follow the smell of supper but had become stuck between roots",
        "clear loose stones from the outside and roll food toward the wider opening",
        "a sudden echo made the piglet shove deeper into the tunnel",
        "covered the lantern, quieted the voices, and widened the safe edge one stone at a time",
        "the piglet backed out and was led to supper without anyone crawling inside",
        "In an adventure, knowing when not to enter is part of bravery",
        "the lantern glowed on the trail as the piglet trotted home under the evening stars",
    ),
    Conflict(
        "the mountain bell",
        "a massive piglet had tangled its harness in the rope of a mountain warning bell",
        "pulling the bell rope would make the piglet panic",
        "the knot was loose enough to open if the rope stopped swinging",
        "wind had set the bell moving after the piglet brushed against it",
        "shield the bell from the wind and offer a quiet path toward the post",
        "the piglet tugged whenever the bell gave a sharp clang",
        "held the rope still with a padded hook and loosened the harness buckle",
        "the piglet walked free and the bell gave one gentle warning ring",
        "A brave helper protects both the frightened creature and the people nearby",
        "the massive piglet stood beneath the quiet bell while dawn lit the mountain path",
    ),
    Conflict(
        "the cave garden",
        "a massive piglet had knocked over the stone wall around a cave garden and blocked the spring",
        "the wall was too massive to rebuild before night",
        "water still trickled through a crack beneath the fallen stones",
        "the spring was blocked by one round stone, not the whole wall",
        "move the round stone with a lever and guide the water through a channel",
        "the piglet wanted to lie exactly where the channel needed to go",
        "lead the piglet to a bed of cool leaves before opening the spring",
        "water reached the garden and the wall could be rebuilt safely the next morning",
        "Look for the small cause of a large-looking problem",
        "moonlight touched the flowing spring while the piglet slept among cool leaves",
    ),
    Conflict(
        "the watchtower ladder",
        "a massive piglet had leaned against a watchtower ladder and left it crooked above the trail",
        "someone had to climb up and fix it quickly",
        "one lower brace had slipped, so climbing would make the ladder worse",
        "the piglet's weight had shifted the brace when it scratched its back",
        "keep everyone below the ladder, coax the piglet away, and replace the brace",
        "the piglet returned whenever it heard the rope scrape",
        "used a bell of grain to lead it to a fenced corner before repairing the brace",
        "the ladder stood firm and the lookout could safely signal the trail",
        "A shortcut is not brave if it adds danger",
        "the straight ladder pointed at the sunset as the piglet nibbled grain behind the fence",
    ),
]

ROUTES = [
    (
        "At dawn, the trail looked quiet enough for an easy journey.",
        "Then a conflict appeared where the path met the wild edge.",
        "By sunset, the travelers had earned a peaceful road instead of a victory over anyone.",
    ),
    (
        "The little expedition began with a map, a snack, and bright hopes.",
        "The map could not solve the problem; careful eyes and kind words had to do that.",
        "Their best treasure was the safe path they made for everyone.",
    ),
    (
        "Beyond the last fence, the adventure narrowed to one difficult choice.",
        "The heroes stopped rushing and studied the creature, the land, and the risk.",
        "The quiet ending felt stronger than a loud triumph.",
    ),
    (
        "A red morning sun followed the travelers toward an unknown corner of the valley.",
        "A massive shadow turned the ordinary walk into a test of courage and care.",
        "They carried the lesson home with the dust on their boots.",
    ),
]


HEROES = ["Luna", "Mara", "Pip", "Tavi", "Rin", "Kito"]
PIGLET_NAMES = ["Boulder", "Moss", "Thunder", "Button", "Bruno", "Pebble"]
TOOLS = ["a rope", "a wooden lever", "a padded hook", "a wide board", "a lantern"]


def _choose(params: StoryParams) -> tuple[Conflict, tuple[str, str, str]]:
    seed = params.seed if params.seed is not None else 0
    return CONFLICTS[seed % len(CONFLICTS)], ROUTES[(seed // len(CONFLICTS)) % len(ROUTES)]


def validate(params: StoryParams) -> None:
    if not params.place.strip():
        raise StoryError("place must not be empty")
    if params.hero == params.piglet_name:
        raise StoryError("hero and piglet must have different names")
    if not params.tool.strip():
        raise StoryError("tool must not be empty")


def tell_story(params: StoryParams) -> World:
    validate(params)
    conflict, route = _choose(params)
    world = World(params.place)
    hero = world.add(Entity(params.hero, "character", "young explorer", params.hero))
    piglet = world.add(Entity("piglet", "animal", "massive piglet", params.piglet_name))
    tool = world.add(Entity("tool", "object", "helping tool", params.tool))
    hero.memes.update(courage=1.0, worry=0.7)
    piglet.meters.update(size=3.0, strength=2.0, risk=1.0)
    piglet.memes.update(fear=0.8, trust=0.1)
    tool.meters["strength"] = 1.0

    world.say(route[0])
    world.say(
        f"In {params.place}, {params.hero} traveled with {params.tool} and found "
        f"{params.piglet_name}, a massive piglet, in trouble: {conflict.trouble}."
    )
    world.say(
        f'"We cannot rush in," {params.hero} said. "The piglet may be strong, but it may also be scared."'
    )
    world.say(
        f'"What should we watch for?" asked a trail keeper named {params.piglet_name}\'s keeper, Ivo.'
    )
    world.say(f'"Look at the ground first," {params.hero} replied. "The clue may tell us what it needs."')
    world.say(route[1])
    world.say(f"They noticed that {conflict.clue}.")
    world.say(f'"I think the trouble began because {conflict.discovery}," said Ivo.')
    world.say(
        f"{params.hero} lowered {params.tool} and explained the plan: {conflict.plan}. "
        f"The plan mattered because {conflict.obstacle}."
    )
    world.say(
        f"They worked slowly. {conflict.repair.capitalize()}. "
        f"{params.piglet_name} watched from the edge, then took one careful step."
    )
    world.say(f"The conflict changed when {conflict.outcome}.")
    world.say(f'"You are safe now," {params.hero} told the piglet. "We solved this together."')
    world.say(f'"And we learned that {conflict.lesson.lower()}', Ivo answered.')
    world.say(route[2])
    world.say(f"At the end of the adventure, {conflict.ending}.")

    piglet.meters["risk"] = 0.0
    piglet.memes.update(fear=0.0, trust=1.0, joy=0.8)
    hero.memes.update(worry=0.0, courage=1.0)
    world.facts.update(
        hero=hero,
        piglet=piglet,
        tool=tool,
        conflict=conflict,
        resolved=True,
        safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    conflict: Conflict = world.facts["conflict"]
    hero: Entity = world.facts["hero"]
    piglet: Entity = world.facts["piglet"]
    return [
        'Write an adventure story using the words "massive" and "piglet".',
        f"Tell a conflict adventure in which {hero.label} helps {piglet.label}, a massive piglet, without using force.",
        f"Build the story around this clue: {conflict.clue}. Include dialogue and a safe resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    piglet: Entity = world.facts["piglet"]
    conflict: Conflict = world.facts["conflict"]
    return [
        QAItem(
            f"What conflict did {hero.label} find?",
            f"{hero.label} found {piglet.label}, a massive piglet, in trouble because {conflict.trouble}.",
        ),
        QAItem(
            "What clue helped the explorers understand the problem?",
            f"They noticed that {conflict.clue}. This clue showed them how to help instead of rushing.",
        ),
        QAItem(
            "How did the characters solve the conflict?",
            f"They followed a careful plan: {conflict.plan.capitalize()}. Then they {conflict.repair}.",
        ),
        QAItem(
            f"How did {piglet.label} change by the end?",
            f"{piglet.label} became calm and safe. {conflict.outcome.capitalize()}.",
        ),
        QAItem(
            "What lesson did the adventure teach?",
            f"It taught that {conflict.lesson.lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a piglet?",
            "A piglet is a young pig. It can be strong and curious even when it is small, and a very large piglet still needs gentle, careful handling.",
        ),
        QAItem(
            "What does massive mean?",
            "Massive means very large or heavy. A massive animal may need extra space and a thoughtful plan.",
        ),
        QAItem(
            "What is a conflict?",
            "A conflict is a problem or disagreement that needs to be understood and resolved.",
        ),
        QAItem(
            "Why is calm communication useful during an adventure?",
            "Calm words can help frightened people or animals feel safer, reveal useful information, and prevent a problem from becoming more dangerous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    conflict: Conflict = world.facts["conflict"]
    lines.append(f"conflict: {conflict.title}; resolved={world.facts['resolved']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Massive piglet conflict adventure storyworld.")
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
    hero = rng.choice(HEROES)
    piglet = rng.choice([name for name in PIGLET_NAMES if name != hero])
    return StoryParams(
        place="the valley trail",
        hero=hero,
        piglet_name=piglet,
        tool=rng.choice(TOOLS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


ASP_RULES = """
place(valley_trail).
theme(massive).
theme(piglet).
feature(conflict).
style(adventure).
safe_plan :- feature(conflict), theme(piglet), theme(massive).
resolved_story :- safe_plan, style(adventure).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "valley_trail"),
            asp.fact("theme", "massive"),
            asp.fact("theme", "piglet"),
            asp.fact("feature", "conflict"),
            asp.fact("style", "adventure"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(asp_program("#show safe_plan/0.\n#show resolved_story/0."))
        names = {symbol.name for symbol in symbols}
        if not {"safe_plan", "resolved_story"} <= names:
            return 1
    except Exception:
        return 1

    try:
        for seed in range(len(CONFLICTS)):
            params = StoryParams(
                place="the valley trail",
                hero="Luna",
                piglet_name="Boulder",
                tool="a rope",
                seed=seed,
            )
            sample = generate(params)
            if not sample.world or not sample.world.facts.get("resolved"):
                return 1
            if "massive piglet" not in sample.story:
                return 1
            if "said" not in sample.story and "asked" not in sample.story:
                return 1
    except Exception:
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp or args.asp:
        print(asp_program("#show safe_plan/0.\n#show resolved_story/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.all:
        samples = [
            generate(
                StoryParams(
                    place="the valley trail",
                    hero="Luna",
                    piglet_name="Boulder",
                    tool="a rope",
                    seed=index,
                )
            )
            for index in range(len(CONFLICTS))
        ]
    else:
        samples = []
        for offset in range(args.n):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
