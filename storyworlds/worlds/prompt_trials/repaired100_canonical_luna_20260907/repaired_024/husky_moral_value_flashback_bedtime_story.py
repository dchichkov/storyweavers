#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a husky, a remembered promise, and the moral
value of honesty.

The simulation follows a small husky who finds a warm mitten before bedtime.
A flashback to an earlier promise changes the choice he makes, and the ending
shows why telling the truth can bring peace.
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
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Setting:
    name: str
    landmark: str
    weather: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    name: str
    setting: str
    trait: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Arc:
    id: str
    object_label: str
    discovery: str
    owner_name: str
    owner_description: str
    promise: str
    temptation: str
    honest_action: str
    consequence: str
    final_image: str
    moral: str
    memory_image: str


SETTINGS = {
    "snowy porch": Setting("the snowy porch", "the blue front door", "soft snow"),
    "pine path": Setting("the pine path", "the old lantern post", "silver frost"),
    "quiet yard": Setting("the quiet yard", "the garden gate", "a pale winter wind"),
}

HUSKY_NAMES = ["Luna", "Koda", "Miska", "Niko", "Sable", "Tala"]
TRAITS = ["gentle", "playful", "thoughtful", "brave"]

ARCS = [
    Arc(
        "mitten",
        "a red wool mitten",
        "found a red wool mitten half-buried beside the path",
        "Mara",
        "a small child in a yellow coat",
        "to bring lost things to the basket by the door",
        "to carry the mitten into her warm sleeping corner",
        "carried the mitten to the basket and waited for its owner",
        "Mara soon came searching, and the mitten was warm and safe when she found it",
        "Mara hugged Luna while the red mitten rested beside the door",
        "Honesty means returning what belongs to someone else, even when keeping it would feel cozy.",
        "Mara once returned Luna's favorite blue ball after finding it under the porch",
    ),
    Arc(
        "bell",
        "a little brass bell",
        "noticed a little brass bell shining beneath the snow",
        "Mr. Rowan",
        "the old gardener who walked with a wooden cane",
        "to tell a grown-up whenever something important was found",
        "to hide the bell beneath the blanket and make it ring during dreams",
        "carried the bell to the lantern post and barked until Mr. Rowan heard",
        "Mr. Rowan found the bell and used it to call everyone safely home",
        "The brass bell chimed softly beside Luna's bed before the house grew quiet",
        "A truthful heart helps other people find their way home.",
        "Mr. Rowan once stopped to untangle Luna's leash from a thorn bush",
    ),
    Arc(
        "scarf",
        "a green knitted scarf",
        "spied a green knitted scarf caught on the garden gate",
        "Eli",
        "a sleepy boy who had come to feed the birds",
        "to tell the truth about anything she carried into the house",
        "to drag the scarf inside and curl up with it",
        "laid the scarf on the gate and called softly until Eli returned",
        "Eli wrapped the scarf around his neck and thanked her with a gentle pat",
        "The green scarf waved on the gate while Luna watched from the warm step",
        "Truth makes room for kindness to return.",
        "Eli once admitted that he had knocked over Luna's water bowl and filled it again",
    ),
    Arc(
        "key",
        "a small silver key",
        "found a small silver key under the porch rail",
        "Nora",
        "the baker who lived next door",
        "to speak plainly when she found something that was not hers",
        "to hide the key beneath a cushion and keep its bright secret",
        "placed the key on the doorstep and waited beside it",
        "Nora opened the bakery door and brought Luna a warm biscuit",
        "The silver key gleamed on the doorstep as the bakery lights glowed",
        "Honesty opens doors that hiding can never open.",
        "Nora once told the truth when she accidentally dropped Luna's treat",
    ),
]

OPENINGS = [
    "The moon was climbing over the rooftops",
    "Snowflakes whispered against the windows",
    "The evening sky turned the color of blueberry jam",
    "The last bird tucked its head beneath its wing",
]

MEMORY_LEADS = [
    "The memory came back as clearly as a lullaby.",
    "For one quiet moment, the past glowed inside her mind.",
    "Luna remembered before the tempting thought could grow.",
    "A small warm picture rose from yesterday.",
]

REQUESTS = [
    "What do you think I should do?",
    "Could you help me decide?",
    "Should I take this to the door?",
    "Will you listen to my plan?",
]

ASP_RULES = r"""
found_object(H) :- husky(H), carries_found(H).
remembered_promise(H) :- husky(H), flashback(H).
honest_choice(H) :- found_object(H), remembered_promise(H), returns_object(H).
peaceful_ending :- honest_choice(husky).
#show found_object/1.
#show remembered_promise/1.
#show honest_choice/1.
#show peaceful_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("husky", "husky"),
            asp.fact("carries_found", "husky"),
            asp.fact("flashback", "husky"),
            asp.fact("returns_object", "husky"),
        ]
    )


def asp_program(show: str = "#show peaceful_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if any(atom.name == "peaceful_ending" for atom in model):
        print("OK: ASP and Python agree on the peaceful honest ending.")
        return 0
    print("MISMATCH: ASP did not find the peaceful ending.")
    return 1


def validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")
    if not params.name.strip():
        raise StoryError("The husky needs a name.")


def tell(params: StoryParams) -> World:
    validate(params)
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name)
    cursor = seed
    arc = ARCS[cursor % len(ARCS)]
    cursor //= len(ARCS)
    opening = OPENINGS[cursor % len(OPENINGS)]
    cursor //= len(OPENINGS)
    memory_lead = MEMORY_LEADS[cursor % len(MEMORY_LEADS)]
    cursor //= len(MEMORY_LEADS)
    request = REQUESTS[cursor % len(REQUESTS)]

    setting = SETTINGS[params.setting]
    world = World(setting)
    husky = world.add(Entity("husky", "animal", params.name))
    found = world.add(Entity("found_object", "object", arc.object_label))
    child = world.add(Entity("owner", "person", arc.owner_name))
    door = world.add(Entity("door", "place", setting.landmark))
    husky.memes["kindness"] = 1
    husky.memes["truthfulness"] = 0
    world.facts.update(
        arc=arc,
        husky=husky,
        found=found,
        owner=child,
        door=door,
        opening=opening,
        memory_lead=memory_lead,
        request=request,
    )

    world.say(f"{opening}, and {params.name}, a {params.trait} husky, curled on the step outside {setting.name}.")
    world.say(f"The {setting.weather} made the world quiet, but near {setting.landmark}, {params.name} {arc.discovery}.")
    found.meters["found"] = 1

    world.para()
    world.say(f"The {arc.object_label} smelled like home, and {params.name} wanted to carry it to a soft place.")
    world.say(f"Just then, {arc.owner_name} called, \"{request}\"")
    world.say(f"\"I found something,\" said {params.name} with a small bark.")
    world.say(f"\"Then let us think before we choose,\" said {arc.owner_name}.")

    world.para()
    world.say(memory_lead)
    world.say(f"Luna remembered that {arc.memory_image}.")
    husky.memes["truthfulness"] = 1
    husky.meters["remembered_promise"] = 1
    world.say(f"The old promise was simple: {arc.promise}.")
    world.say(f"For a moment, {params.name} imagined this instead: {arc.temptation}.")
    world.say(f"Then {params.name} chose to be honest and {arc.honest_action}.")
    husky.meters["returned_object"] = 1
    world.fired.add("honest_choice")

    world.para()
    world.say(f"{arc.consequence}.")
    world.say(f"{arc.owner_name} smiled and said, \"Thank you for telling the truth, {params.name}.\"")
    world.say(f"{params.name} wagged her tail, and the evening became peaceful.")
    world.say(f"At bedtime, {arc.final_image}.")
    world.say(f"The moral value was clear: {arc.moral}")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    arc: Arc = f["arc"]  # type: ignore[assignment]
    return [
        f"Write a gentle bedtime story about a husky named {f['husky'].label} who finds {arc.object_label}.",
        f"Include a flashback in which {f['husky'].label} remembers that {arc.memory_image}.",
        f"End with the moral value that {arc.moral}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    arc: Arc = f["arc"]  # type: ignore[assignment]
    husky: Entity = f["husky"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who was the husky in the story?",
            f"The husky was {husky.label}, a {husky.memes and 'thoughtful' or 'kind'} husky who chose to be honest.",
        ),
        QAItem(
            f"What did {husky.label} find?",
            f"{husky.label} found {arc.object_label} near {f['door'].label}.",
        ),
        QAItem(
            "What did the flashback help the husky remember?",
            f"The flashback reminded the husky that {arc.memory_image}.",
        ),
        QAItem(
            f"Why did {husky.label} return the found object?",
            f"{husky.label} remembered the promise to {arc.promise}, so the husky {arc.honest_action}.",
        ),
        QAItem(
            "What moral value did the bedtime story teach?",
            f"It taught that {arc.moral}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a husky?",
            "A husky is a strong, fluffy dog often known for a thick coat, bright eyes, and a friendly, energetic nature.",
        ),
        QAItem(
            "What is a flashback in a story?",
            "A flashback is a part of a story that briefly returns to an earlier event or memory.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle about how to act well, such as honesty, kindness, or courage.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.kind} {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "snowy porch", "gentle", 101),
    StoryParams("Koda", "pine path", "playful", 202),
    StoryParams("Miska", "quiet yard", "thoughtful", 303),
]


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a bedtime story about a husky, a flashback, and honesty."
    )
    parser.add_argument("--name", choices=HUSKY_NAMES)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--trait", choices=TRAITS)
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
        name=args.name or rng.choice(HUSKY_NAMES),
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        trait=args.trait or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("peaceful ending:", any(atom.name == "peaceful_ending" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

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
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
