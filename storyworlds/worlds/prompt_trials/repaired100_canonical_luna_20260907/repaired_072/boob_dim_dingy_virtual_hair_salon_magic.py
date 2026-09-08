#!/usr/bin/env python3
"""
A gentle ghost storyworld about a dingy hair salon, a virtual mirror,
boob-dim magic, conflict, and bravery.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    id: str
    occasion: str
    problem: str
    first_guess: str
    clue: str
    discovery: str
    repair: str
    lesson: str
    ending: str


NAMES = {
    "girl": ["Luna", "Maya", "Nina", "Zuri", "Ivy"],
    "boy": ["Owen", "Theo", "Eli", "Noah", "Jace"],
}
HELPERS = ["aunt", "mother", "father", "grandmother", "older cousin"]
GHOST_NAMES = ["Mica", "Bramble", "Pip", "Soot", "Dew"]


INCIDENTS = [
    Incident(
        "mirror_glitch",
        "the salon was preparing for its first haircut day after a long rainy week",
        "the virtual mirror showed every hairstyle with a dark, boob-dim shadow over the chest and shoulders",
        "that the mirror was simply being rude or broken",
        "the same shadow appeared only when the old blue dryer was plugged in",
        "the dryer had a loose cord that made the mirror's magic flicker",
        "unplugged the dryer, asked an adult to repair the cord, and tested the mirror with safe equipment",
        "bravery means speaking up about a danger even when a strange machine feels scary",
        "the repaired mirror filled with bright curls, silver braids, and smiling faces",
    ),
    Incident(
        "vanishing_ribbons",
        "customers were choosing colorful ribbons for a neighborhood celebration",
        "the virtual salon kept making ribbons vanish from its hairstyles",
        "that the ghost was stealing them for a secret costume",
        "the ribbons reappeared beside a dusty vent whenever the salon fan rattled",
        "a loose vent cover had been pulling the light virtual ribbons into its draft",
        "closed the fan, moved everyone away, and let the caretaker secure the cover",
        "conflict can be solved kindly when people check evidence instead of blaming a friend",
        "ribbons danced safely above the chairs like tiny rainbow flags",
    ),
    Incident(
        "dingy_spell",
        "Luna and her helper were giving the dingy salon a cheerful spring cleaning",
        "a magic shampoo spell made the virtual walls look even darker and gloomier",
        "that someone had cast a mean spell on purpose",
        "the spell card had a smudge over the word bright, making it read fright",
        "carefully cleaned the card, read it aloud with the salon owner, and tried the spell again",
        "a mistake can cause conflict, but patience and honesty can repair it",
        "the dingy walls shimmered into warm peach, lavender, and gold",
    ),
    Incident(
        "ghostly_bangs",
        "the salon was holding a playful virtual hairstyle contest",
        "a ghostly pair of bangs covered the screen whenever a child chose a brave new style",
        "that the ghost wanted everyone to keep the same haircut",
        "the bangs lifted whenever someone said what they truly liked",
        "the ghost was afraid that nobody would accept its old-fashioned style",
        "Luna invited the ghost to choose a style and promised that every customer could be different",
        "bravery includes making room for someone who feels left out",
        "the screen showed a whole parade of styles, including the ghost's bright silver pompadour",
    ),
    Incident(
        "sparkle_lock",
        "the salon was getting ready for a rainy-day story hour",
        "the magic cabinet locked itself while the virtual combs glowed inside",
        "that the cabinet was guarding a treasure from Luna",
        "the lock opened a little whenever Luna told the truth about feeling nervous",
        "the cabinet's spell needed a brave voice, not a secret password",
        "Luna admitted her fear, and the helper opened the cabinet after the spell softened",
        "naming a fear can make room for courage",
        "the glowing combs made starry patterns while everyone listened to a story",
    ),
]


OPENINGS = [
    "On a misty afternoon",
    "Just before the salon opened",
    "Under a sky full of rain clouds",
    "At the end of a quiet school day",
    "When the street lamps first blinked on",
]


@dataclass(frozen=True)
class ASPFacts:
    happy: bool
    brave: bool
    repaired: bool


def tell_story(params: StoryParams) -> World:
    if params.gender not in {"girl", "boy"}:
        raise StoryError("gender must be girl or boy")
    rng = random.Random(params.seed)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    world = World(place="the dingy Moonbeam Hair Salon")

    child = world.add(Entity(params.name, "character", params.gender))
    helper = world.add(Entity(params.helper.title(), "character", params.helper))
    ghost = world.add(Entity(params.ghost_name, "character", "ghost"))
    mirror = world.add(Entity("virtual_mirror", "thing", "virtual mirror"))
    magic = world.add(Entity("magic", "thing", "salon magic"))
    conflict = world.add(Entity("conflict", "thing", "conflict"))
    bravery = world.add(Entity("bravery", "thing", "bravery"))

    world.say(
        f"{opening}, {child.id} visited {world.place} with {helper.id}. "
        f"The salon was dingy, but its virtual mirror could show magical hairstyles."
    )
    world.say(
        f"Even the friendly ghost {ghost.id} liked to float between the chairs, "
        f"where bottles glittered like tiny moons."
    )
    world.say(f"They had come because {incident.occasion}.")
    world.say(f"Soon they discovered that {incident.problem}.")
    world.say(
        f"A dim shadow crossed the virtual screen. It looked boob-dim and peculiar, "
        f"so everyone stepped back instead of touching the magic."
    )

    world.para()
    world.say(
        f"At first, {child.id} guessed {incident.first_guess}. "
        f"{helper.id} shook their head gently. "
        f'"A guess is not proof," {helper.id} said. "Let us look carefully."'
    )
    world.say(
        f'"I am frightened, but I can still be brave," {child.id} said. '
        f'"Can you help me find a clue, {ghost.id}?"'
    )
    world.say(
        f'{ghost.id} nodded and whispered, "Look where the magic changes." '
        f"Then they noticed that {incident.clue}."
    )
    conflict.meters["noticed"] = 1.0
    ghost.memes["worried"] = 1.0

    world.para()
    world.say(
        f"With {helper.id} nearby, {child.id} checked the salon safely. "
        f"They discovered that {incident.discovery}."
    )
    world.say(
        f'"Now we know what caused the conflict," {child.id} said. '
        f'"We can fix the problem without blaming anyone."'
    )
    world.say(f"Together, they {incident.repair}.")
    mirror.meters["safe"] = 1.0
    magic.meters["working"] = 1.0
    bravery.memes["active"] = 1.0
    world.say(
        f"{ghost.id} smiled. \"You used magic carefully and courage kindly,\" "
        f"the ghost said."
    )

    world.para()
    ghost.memes["worried"] = 0.0
    ghost.memes["happy"] = 1.0
    world.say(
        f"{child.id} understood that {incident.lesson}. "
        f"The salon no longer felt only dingy; it felt ready for a fresh beginning."
    )
    world.say(f"At the end, {incident.ending}.")
    world.say(
        f"The ghost gave a tiny bow, and the virtual mirror glowed softly instead of dimly."
    )

    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        mirror=mirror,
        magic=magic,
        conflict=conflict,
        bravery=bravery,
        incident=incident,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]
    child: Entity = world.facts["child"]
    return [
        f"Write a gentle ghost story about {child.id} solving a magical hair-salon conflict.",
        f"Tell a child-safe story in which a virtual mirror, a dingy salon, and bravery reveal the truth.",
        f"Write a cozy salon mystery where careful evidence repairs a strange boob-dim magical problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    ghost: Entity = f["ghost"]
    incident: Incident = f["incident"]
    return [
        QAItem(
            f"What problem did {child.id} notice in the salon?",
            f"{child.id} noticed that {incident.problem}.",
        ),
        QAItem(
            f"What did {child.id} first guess?",
            f"{child.id} first guessed {incident.first_guess}, but {helper.id} reminded everyone to seek evidence.",
        ),
        QAItem(
            f"What clue helped {child.id} solve the conflict?",
            f"The clue was that {incident.clue}. It led to the discovery that {incident.discovery}.",
        ),
        QAItem(
            f"How did {child.id} show bravery?",
            f"{child.id} spoke honestly about being frightened, checked the magical salon safely, and helped {incident.repair}.",
        ),
        QAItem(
            f"What happened to the ghost at the end?",
            f"{ghost.id} became happy and thanked {child.id} for using magic carefully and courage kindly.",
        ),
        QAItem(
            "What changed in the ending image?",
            f"The ending showed that {incident.ending}. The salon's virtual mirror glowed softly instead of dimly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a virtual mirror?",
            "A virtual mirror is a screen or magical display that can show a person with imagined hairstyles or other changes.",
        ),
        QAItem(
            "What does bravery mean in this story?",
            "Bravery means acting carefully and honestly even when something feels frightening.",
        ),
        QAItem(
            "How can conflict be repaired?",
            "Conflict can be repaired by listening, checking evidence, avoiding blame, and working together on a safe solution.",
        ),
        QAItem(
            "What does dingy mean?",
            "Dingy means dull, dusty, or not very bright and clean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
safe_mirror :- repaired, virtual_mirror, magic_working.
happy_ending :- safe_mirror, brave.
#show safe_mirror/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("virtual_mirror"),
            asp.fact("repaired"),
            asp.fact("magic_working"),
            asp.fact("brave"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    if asp.atoms(model, "happy_ending"):
        print("OK: ASP reasoning confirms the repaired magical ending.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm the ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about a magical virtual hair salon."
    )
    parser.add_argument("--name", choices=sorted({n for values in NAMES.values() for n in values}))
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--ghost-name", choices=GHOST_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    inferred = next(
        (gender for gender, names in NAMES.items() if args.name in names),
        None,
    )
    gender = args.gender or inferred or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(name, gender, helper, ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:16} ({entity.type:12}) {' '.join(details)}"
        )
    return "\n".join(lines)


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


CURATED = [
    StoryParams("Luna", "girl", "aunt", "Mica", 7201),
    StoryParams("Owen", "boy", "mother", "Pip", 7202),
    StoryParams("Nina", "girl", "grandmother", "Dew", 7203),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_mirror/0. #show happy_ending/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show safe_mirror/0. #show happy_ending/0.")
        )
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
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
