#!/usr/bin/env python3
"""
A standalone heartwarming equestrian challenge storyworld.

The domain models an issue that appears during a riding challenge and a brave,
kind choice that prevents the first bad ending from becoming the final one.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class StoryParams:
    rider_name: str
    horse_name: str
    helper_name: str
    scenario_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


RIDER_NAMES = ["Luna", "Maya", "Elsie", "Nora", "Tessa", "June"]
HORSE_NAMES = ["Clover", "Maple", "Bramble", "Pippin", "Sunny", "Willow"]
HELPER_NAMES = ["Aunt Rose", "Coach Ben", "Grandma Mae", "Mr. Rowan"]

SCENARIOS = [
    {
        "place": "the little meadow course",
        "challenge": "guide a horse over three low fences and carry a blue ribbon to the finish",
        "issue": "a loose stirrup strap slipped down just before the final fence",
        "bad_ending": "Luna nearly tried to jump on anyway, and the frightened horse stopped hard at the rail",
        "clue": "Clover's ears turned back whenever the dangling strap brushed his side",
        "bravery": "dismounted, held the reins gently, and asked for help instead of pretending everything was fine",
        "repair": "the strap was fastened, and the pair practiced the final approach at a walk",
        "result": "Clover stepped over the last fence calmly, and Luna carried the ribbon across the line beside him",
        "image": "The blue ribbon rested on Clover's bridle while Luna rubbed his warm neck.",
    },
    {
        "place": "the orchard riding ring",
        "challenge": "weave between six soft cones and halt beside the old apple tree",
        "issue": "a bright plastic cone toppled into the path after a gust of wind",
        "bad_ending": "the course became confusing, and Maple rushed toward the wrong marker",
        "clue": "Maple slowed whenever the fallen cone blocked the clear path",
        "bravery": "raised one hand, stopped the attempt, and told the judge that the course was no longer safe to follow",
        "repair": "the cone was moved, the route was explained again, and Maple received a quiet start",
        "result": "Maple threaded through the cones in a smooth golden curve and halted under the apple blossoms",
        "image": "A small apple dropped beside the finished pair like a congratulatory bell.",
    },
    {
        "place": "the covered arena",
        "challenge": "complete a gentle pattern of turns and salute at the center",
        "issue": "rain drummed so loudly on the roof that the rider could not hear the next instruction",
        "bad_ending": "the first pattern tangled into wrong turns, and Willow grew tense beneath the noise",
        "clue": "Willow relaxed when the signals became slower and clearer",
        "bravery": "asked the announcer to repeat the pattern and chose to ride the simpler safe version",
        "repair": "the arena grew quiet for a moment, and the pair practiced each turn with a visible hand signal",
        "result": "Willow followed the pattern with soft steps and stopped for a proud salute",
        "image": "Rain shone on the arena windows while horse and rider stood quietly together.",
    },
    {
        "place": "the creekside trail",
        "challenge": "cross a marked bridge and return with a yellow flower tucked in a saddle pouch",
        "issue": "the wooden bridge made a sharp creak beneath Bramble's first hoof",
        "bad_ending": "Bramble backed away, and the rider's hurried pull made both of them wobble",
        "clue": "Bramble trusted the bridge when he could inspect each board without being rushed",
        "bravery": "climbed down, walked beside Bramble, and admitted that courage could mean changing the plan",
        "repair": "the helper checked the bridge, and they crossed one careful step at a time",
        "result": "Bramble carried the flower home after choosing the bridge himself",
        "image": "The yellow flower bobbed beside Bramble's mane in the soft creek breeze.",
    },
    {
        "place": "the sunset paddock",
        "challenge": "lead a pony through a kindness course and finish with a quiet grooming stop",
        "issue": "a gate latch stuck while the pony was halfway through",
        "bad_ending": "the gate rattled, and the pony spun around before anyone knew what to do",
        "clue": "the pony settled when the rider loosened the rope and spoke in a low voice",
        "bravery": "stayed still, called for the barn keeper, and protected the pony from a hurried tug",
        "repair": "the latch was opened by hand, and the course was changed to include a wide safe turn",
        "result": "the pony finished the course and rested peacefully while the rider brushed dust from his coat",
        "image": "The paddock glowed orange, and every brush stroke made the pony's coat shine.",
    },
]

OPENINGS = [
    "The morning sun warmed the riding yard as Luna arrived for the equestrian challenge.",
    "At the edge of the green field, hoofprints made a path toward a day of brave choices.",
    "The stable smelled of hay and rain when the challenge began.",
    "Everyone at the riding yard had a ribbon, a helmet, and a reason to cheer.",
    "A quiet horse waited beside the mounting block while the first clouds moved over the course.",
]

DIALOGUES = [
    ('"Wait," Luna said. "Clover is telling us something."',
     '"Good noticing," said Aunt Rose. "Stopping safely is part of riding bravely."'),
    ('"I do not know how to fix this," Luna admitted.',
     '"You do not have to fix it alone," said Coach Ben.'),
    ('"Can we try a safer way?" Luna asked.',
     '"Yes," said the helper. "A kind plan is still a winning plan."'),
    ('"The challenge can wait," Luna said. "My horse needs us to listen."',
     '"That is the heart of horsemanship," said the helper.'),
]

ENDINGS = [
    "The ribbon mattered, but the trust between rider and horse mattered more.",
    "No one called the careful choice a failure; everyone called it wise.",
    "The challenge ended with warm smiles instead of a rushed finish.",
    "Luna learned that bravery has a quiet voice when it protects someone smaller or scared.",
    "The best part of the day was seeing horse and rider leave the ring together.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming equestrian challenge storyworld.")
    parser.add_argument("--rider", choices=RIDER_NAMES)
    parser.add_argument("--horse", choices=HORSE_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
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
    rider = args.rider or rng.choice(RIDER_NAMES)
    horse = args.horse or rng.choice(HORSE_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        rider_name=rider,
        horse_name=horse,
        helper_name=helper,
        scenario_id=rng.randrange(len(SCENARIOS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.rider_name or not params.horse_name or not params.helper_name:
        raise StoryError("A rider, horse, and helper are all required.")
    if params.rider_name == params.horse_name:
        raise StoryError("The rider and horse must have different names.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("scenario_id does not name a known equestrian challenge.")
    if not 0 <= params.dialogue_id < len(DIALOGUES):
        raise StoryError("dialogue_id does not name a known exchange.")
    if not 0 <= params.ending_id < len(ENDINGS):
        raise StoryError("ending_id does not name a known ending.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    world = World()
    rider = world.add(Entity("rider", "character", params.rider_name))
    horse = world.add(Entity("horse", "animal", params.horse_name))
    helper = world.add(Entity("helper", "character", params.helper_name))
    ribbon = world.add(Entity("ribbon", "object", "blue ribbon"))
    scenario = SCENARIOS[params.scenario_id]
    first_line, second_line = DIALOGUES[params.dialogue_id]

    world.facts.update(
        rider=rider,
        horse=horse,
        helper=helper,
        ribbon=ribbon,
        scenario=scenario,
        resolved=False,
    )

    rider.memes["hope"] += 1
    horse.memes["trust"] += 1
    horse.meters["calm"] += 1

    world.say(OPENINGS[params.scenario_id % len(OPENINGS)])
    world.say(
        f"{rider.label} rode {horse.label} toward {scenario['place']} to {scenario['challenge']}."
    )
    world.say(
        f"The challenge was not about being the fastest. It was about listening carefully and caring for the animal who carried the rider."
    )

    world.para()
    world.say(f"Then an issue appeared: {scenario['issue']}.")
    horse.memes["uneasy"] += 1
    rider.memes["worried"] += 1
    world.say(scenario["bad_ending"])
    world.say(f"{rider.label} noticed that {scenario['clue']}.")

    world.para()
    world.say(f'{first_line} {second_line}')
    rider.memes["bravery"] += 1
    rider.meters["safe_choice"] += 1
    horse.memes["trust"] += 1
    world.say(f"{rider.label} {scenario['bravery']}.")
    world.say(f"{params.helper_name} helped because {scenario['repair']}.")
    helper.memes["care"] += 1
    horse.memes["calm"] += 1
    horse.memes["uneasy"] = 0.0
    world.say(f"Together, they finished the challenge: {scenario['result']}.")
    ribbon.meters["earned_safely"] += 1
    world.facts["resolved"] = True

    world.para()
    world.say(ENDINGS[params.ending_id])
    world.say(scenario["image"])

    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    return [
        f"Write a heartwarming equestrian story about a challenge to {scenario['challenge']}.",
        f"Show how the issue that {scenario['issue']} creates a bad ending at first, then let the rider choose bravery.",
        f"Include a gentle spoken exchange in which the rider and helper change what they decide to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    scenario = facts["scenario"]
    rider = facts["rider"].label
    horse = facts["horse"].label
    helper = facts["helper"].label
    return [
        QAItem(
            question="What kind of challenge did the story describe?",
            answer=f"It described an equestrian challenge in which {rider} worked with {horse} to {scenario['challenge']}.",
        ),
        QAItem(
            question="What issue interrupted the challenge?",
            answer=f"The issue was that {scenario['issue']}. This made the original plan unsafe.",
        ),
        QAItem(
            question=f"How did {rider} show bravery?",
            answer=f"{rider} showed bravery by {scenario['bravery']}. The brave choice protected {horse} instead of hiding the problem.",
        ),
        QAItem(
            question="Why did the first attempt look like a bad ending?",
            answer=f"It looked like a bad ending because {scenario['bad_ending']}. The challenge could not be finished safely that way.",
        ),
        QAItem(
            question=f"How did {helper} help repair the situation?",
            answer=f"{helper} helped because {scenario['repair']}. This gave {rider} and {horse} a calmer way to finish together.",
        ),
        QAItem(
            question="What proved that the ending had changed?",
            answer=f"The ending changed when {scenario['result']}. The final image was that {scenario['image'][0].lower() + scenario['image'][1:]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does equestrian mean?",
            answer="Equestrian means related to horses, especially riding, caring for, or training them.",
        ),
        QAItem(
            question="What is a challenge?",
            answer="A challenge is a task that takes effort, attention, and sometimes courage to complete.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing what is right or necessary even when something feels frightening or difficult.",
        ),
        QAItem(
            question="Why should a rider listen to a horse?",
            answer="A rider should listen to a horse because the horse's movements and behavior can show comfort, worry, or danger.",
        ),
        QAItem(
            question="Why can stopping be a brave choice?",
            answer="Stopping can be brave because it gives people time to notice a problem and choose a safer, kinder action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.label} {' '.join(details)}")
    lines.append(f"resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(riding_yard).
seed_word(issue).
seed_word(equestrian).
seed_word(challenge).
feature(bad_ending).
feature(bravery).
valid_domain(riding_yard, issue, equestrian, challenge) :-
    setting(riding_yard),
    seed_word(issue),
    seed_word(equestrian),
    seed_word(challenge),
    feature(bad_ending),
    feature(bravery).
#show valid_domain/4.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "riding_yard"),
            asp.fact("seed_word", "issue"),
            asp.fact("seed_word", "equestrian"),
            asp.fact("seed_word", "challenge"),
            asp.fact("feature", "bad_ending"),
            asp.fact("feature", "bravery"),
        ]
    )


def asp_program(show: str = "#show valid_domain/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_domain"))
    expected = {("riding_yard", "issue", "equestrian", "challenge")}
    if found != expected:
        print("MISMATCH")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if not sample.story.strip() or "said" not in sample.story:
            print("MISMATCH: generated story lacks spoken dialogue.")
            return 1

    print("OK: ASP parity and generated-story checks match.")
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


CURATED = [
    StoryParams("Luna", "Clover", "Aunt Rose", 0, 0, 0),
    StoryParams("Maya", "Maple", "Coach Ben", 1, 1, 1),
    StoryParams("Elsie", "Bramble", "Grandma Mae", 2, 2, 2),
]


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        models = asp.solve(asp_program(), models=1)
        print(json.dumps([str(symbol) for symbol in models[0]] if models else []))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
