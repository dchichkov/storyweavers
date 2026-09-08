#!/usr/bin/env python3
"""
A tall tale about a fantastic hyrax, a promise, and a warning hidden in plain sight.

The world models a small mountain domain:
- physical meters: bell weight, bridge distance, storm strength, stone warmth
- emotional memes: pride, worry, courage, kindness, relief

Moral value: true greatness means using strength to help others.
Foreshadowing: a humming red pebble warns Luna that the mountain bridge will fail.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Milo", "Nia", "Tavi", "Pip", "Zora"]
HELPER_POOL = ["Grandma", "Aunt Bea", "the shepherd", "Luna's friend Odo"]
VALLEY_POOL = ["Thunderstep Valley", "Blue Juniper Pass", "Cloudberry Ridge", "Whistling Stone Valley"]

TALES = [
    {
        "goal": "carry the enormous sunrise bell to the highest mountain peak",
        "problem": "the bell was so heavy that it made the path groan under every step",
        "foreshadow": "a warm red pebble hummed whenever Luna passed the old bridge",
        "warning": "the humming pebble showed a thin crack beneath the bridge stones",
        "turn": "the bridge would not hold the bell, but the bell rope could be tied to the bell tower on the safe ridge",
        "helper_action": "spread a wool blanket under the pebble and listened carefully",
        "child_action": "stopped, moved the bell away from the bridge, and rolled it along the safer ridge",
        "resolution": "the bell reached the peak without breaking a single bridge stone",
        "ending": "At dawn, one clear bell note rolled across the valley, and the red pebble glowed quietly beside the safe path.",
        "dialogue": '"A strong hero does not merely lift the biggest thing," Grandma said. "A strong hero knows when to set it down."',
        "object": "sunrise bell",
    },
    {
        "goal": "rescue a cloud trapped in a pine tree before the valley lost its rain",
        "problem": "the cloud tugged at the branches like a gigantic wool blanket",
        "foreshadow": "three blue leaves spun backward whenever the wind was about to change",
        "warning": "the backward-spinning leaves pointed away from the narrow cliff trail",
        "turn": "the cloud could be freed by pulling from the broad meadow instead of the dangerous cliff",
        "helper_action": "held the cloud rope and counted the backward-spinning leaves",
        "child_action": "led the rope around the meadow and pulled with the wind",
        "resolution": "the cloud floated free and sprinkled rain over every thirsty garden",
        "ending": "The next morning, silver drops shone on the leaves, while the three blue leaves rested in a neat row.",
        "dialogue": '"Why take the cliff path?" the shepherd asked. "Because it is shorter," Luna said. "And why choose it?" "I should not, if the leaves disagree."',
        "object": "trapped cloud",
    },
    {
        "goal": "prove that a small hyrax could outrun the king's thunder wagon",
        "problem": "the thunder wagon raced downhill so loudly that nobody heard the warning drums",
        "foreshadow": "a tiny yellow flower bent uphill even though the wind blew downhill",
        "warning": "the flower showed that a warm gust was rising from the ravine",
        "turn": "the safest race was not downhill but around the broad mountain meadow",
        "helper_action": "pointed toward the bent flower and checked the wagon's loose wheel",
        "child_action": "changed the course to the meadow and helped fasten the wheel",
        "resolution": "the hyrax finished first, and the wagon arrived safely with all its riders",
        "ending": "The fantastic hyrax wore the winner's ribbon, but it shared the ribbon with the repaired wagon team.",
        "dialogue": '"You can win and still help," Odo said. "That sounds like two victories," Luna replied.',
        "object": "thunder wagon",
    },
    {
        "goal": "fill the village well with one heroic bucket of moonlight",
        "problem": "the moonlight bucket became heavier each time someone bragged about it",
        "foreshadow": "a silver moth landed only on the quietest hands",
        "warning": "the moth avoided the steep boastful path and flew toward a shaded spring",
        "turn": "the bucket had to be carried gently by many quiet helpers",
        "helper_action": "covered the bucket and invited everyone to walk without boasting",
        "child_action": "asked the villagers to carry the moonlight together toward the spring",
        "resolution": "the bucket grew light, and the spring filled the village well",
        "ending": "That night, the well reflected a round moon and many small faces smiling beside it.",
        "dialogue": '"Can I be the greatest helper?" Luna asked. "You can be the first helper," Aunt Bea said. "That is better."',
        "object": "moonlight bucket",
    },
]


THOUGHTS = [
    {
        "role": "a mountain captain",
        "opening": "A true captain notices what the mountain is saying.",
        "mistake": "I am enormous enough to solve this by force. Probably. Maybe.",
        "turn": "The mountain has given me a warning, so I must choose the safer path.",
        "victory": "A captain's finest tool is not muscle. It is attention.",
    },
    {
        "role": "a royal explorer",
        "opening": "Today I shall discover the highest place and make a very impressive entrance.",
        "mistake": "If I keep marching grandly, perhaps the trouble will become smaller.",
        "turn": "That clue is too clear to ignore. A wise explorer changes direction.",
        "victory": "The best discoveries are sometimes the dangers we avoid.",
    },
    {
        "role": "a careful inventor",
        "opening": "Every mountain problem has a solution, but not every solution needs a hammer.",
        "mistake": "My first idea is enormous. My second idea should be sensible.",
        "turn": "The warning reveals a better design: help first, boast later.",
        "victory": "A useful invention is one that leaves everyone safe.",
    },
    {
        "role": "a legendary storyteller",
        "opening": "This adventure will be so grand that even the peaks may lean closer.",
        "mistake": "I have made one very large mistake, which is traditional in legendary adventures.",
        "turn": "The little sign was telling a big truth. I should listen before the tale turns tragic.",
        "victory": "A tall tale grows tallest when kindness stands at its center.",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Grandma"
    valley: str = "Thunderstep Valley"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("weight", "distance", "storm", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("pride", "worry", "courage", "kindness", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    valley: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return int.from_bytes(
        f"{params.name}|{params.helper}|{params.valley}".encode("utf-8"),
        "little",
    )


def tell_world(params: StoryParams) -> World:
    rng = random.Random(seed_number(params))
    tale = TALES[seed_number(params) % len(TALES)]
    thought = THOUGHTS[(seed_number(params) // len(TALES)) % len(THOUGHTS)]

    world = World(params.valley)
    child = world.add(Entity(params.name, "character", params.name))
    hyrax = world.add(Entity("hyrax", "fantastic animal", "a fantastic hyrax"))
    helper = world.add(Entity("helper", "character", params.helper))
    treasure = world.add(Entity("treasure", "important object", tale["object"]))
    pebble = world.add(Entity("foreshadowing", "warning sign", "the warning sign"))

    child.meters["distance"] = 12
    child.memes["pride"] = 1
    hyrax.meters["weight"] = 3
    hyrax.memes["courage"] = 2
    treasure.meters["weight"] = 8
    pebble.meters["warmth"] = 2

    world.facts.update(
        params=params,
        tale=tale,
        thought=thought,
        child=child,
        hyrax=hyrax,
        helper=helper,
        treasure=treasure,
        pebble=pebble,
        resolved=False,
    )

    world.say(
        f"In {params.valley}, {params.name} lived with a {thought['role']} "
        f"and a fantastic hyrax who was small enough to nap in a teacup but strong enough "
        f"to push a boulder uphill."
    )
    world.say(f"One bright morning, {params.name} decided to {tale['goal']}.")
    world.say(
        f"The plan sounded so grand that {params.helper} packed three sandwiches, "
        f"and the fantastic hyrax carried the sandwiches, the rope, and one very serious hat."
    )
    world.say(f'{params.name} thought, "{thought["opening"]}"')
    world.para()

    child.memes["worry"] += 1
    child.memes["pride"] += 1
    treasure.meters["weight"] += 2
    world.say(f"But {tale['problem'].capitalize()}.")
    world.say(f'{params.name} thought, "{thought["mistake"]}"')
    world.say(
        f"Still, {params.name} marched on, while the fantastic hyrax puffed out its chest "
        f"and tried to look taller than the mountain."
    )
    world.say(f"Then came the first warning: {tale['foreshadow'].capitalize()}.")
    world.say(
        f"The warning was easy to miss, but the fantastic hyrax stopped so suddenly "
        f"that the serious hat fell into a bush."
    )
    world.facts["foreshadowing"] = tale["foreshadow"]
    world.para()

    helper_name = params.helper
    world.say(f"{helper_name} crouched beside the sign and {tale['helper_action']}.")
    world.say(f'"Look closely," {helper_name} said. "{tale["warning"].capitalize()}."')
    world.say(
        f'"Then the mountain is telling us to turn back," {params.name} said. '
        f'"Not back," {helper_name} replied. "A wiser way forward."'
    )
    world.say(f'{params.name} thought, "{thought["turn"]}"')
    world.say(f"The fantastic hyrax nodded. {tale['turn'].capitalize()}.")
    world.say(f"So {params.name} {tale['child_action']}.")
    child.memes["pride"] = 0
    child.memes["worry"] = 0
    child.memes["courage"] += 2
    child.memes["kindness"] += 2
    child.memes["relief"] += 1
    treasure.meters["weight"] -= 3
    child.meters["distance"] = 4
    world.say(tale["resolution"].capitalize() + ".")
    world.say(f'{params.name} thought, "{thought["victory"]}"')
    world.facts["resolved"] = True
    world.facts["moral"] = (
        "True greatness means using strength and courage to keep others safe."
    )
    world.para()
    world.say(tale["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    tale = world.facts["tale"]
    return [
        f"Write a Tall Tale about {params.name} and a fantastic hyrax in {params.valley}.",
        f"Include foreshadowing through this clue: {tale['foreshadow']}.",
        "Show the moral value that true strength is used to help others, not merely to boast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    tale = world.facts["tale"]
    return [
        QAItem(
            question=f"What did {params.name} want to do in {params.valley}?",
            answer=f"{params.name} wanted to {tale['goal']}.",
        ),
        QAItem(
            question="What foreshadowed the danger?",
            answer=f"The warning was that {tale['foreshadow']}.",
        ),
        QAItem(
            question="How did the conversation change the plan?",
            answer=(
                f"{params.helper} explained that {tale['warning']}. "
                f"Because of that warning, {params.name} chose to {tale['child_action']}."
            ),
        ),
        QAItem(
            question="What moral value does the tale show?",
            answer="It shows that true greatness means using strength and courage to keep others safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue placed earlier in a story that hints at something important later.",
        ),
        QAItem(
            question="What is a hyrax?",
            answer="A hyrax is a small, sturdy mammal that lives among rocks, though this story imagines a fantastic hyrax with enormous courage.",
        ),
        QAItem(
            question="Why is listening a moral value?",
            answer="Listening helps people notice danger, understand others, and choose actions that protect the whole group.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts=resolved:{world.facts.get('resolved')} moral:{world.facts.get('moral')}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_choice :- listens, warning_seen, helps_others.
moral_value :- safe_choice.
foreshadowing :- warning_seen.
valid_tall_tale :- fantastic_hyrax, moral_value, foreshadowing.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("fantastic_hyrax"),
            asp.fact("warning_seen"),
            asp.fact("listens"),
            asp.fact("helps_others"),
        ]
    )


def asp_program(show: str = "#show valid_tall_tale/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program())
    valid = asp.atoms(model, "valid_tall_tale")
    if valid == [()]:
        print("OK: ASP parity matches the Python moral and foreshadowing gate.")
        return 0
    print("MISMATCH: ASP did not find the valid tall tale.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Tall Tale storyworld about a fantastic hyrax."
    )
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
    parser.add_argument("--valley", choices=VALLEY_POOL)
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
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        valley=args.valley or rng.choice(VALLEY_POOL),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as err:
            raise StoryError(f"ASP mode requires clingo: {err}") from err
        model = asp.one_model(asp_program())
        print(sorted(asp.atoms(model, "valid_tall_tale")))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, valley in enumerate(VALLEY_POOL):
            params = StoryParams(
                name=NAME_POOL[index % len(NAME_POOL)],
                helper=HELPER_POOL[index % len(HELPER_POOL)],
                valley=valley,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not generate the requested number of distinct stories")

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
