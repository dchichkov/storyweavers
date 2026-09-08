#!/usr/bin/env python3
"""
A playful nursery-rhyme storyworld about sharp slacks, gentle teamwork, and humor.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RhymeCase:
    id: str
    place: str
    object_name: str
    trouble: str
    clue: str
    helper: str
    fix: str
    ending: str
    joke: str


@dataclass
class StoryParams:
    hero: str
    partner: str
    role: str
    case: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


CASES = {
    "button_bench": RhymeCase(
        "button_bench",
        "the village nursery",
        "a red button",
        "the sharp slacks snagged on a wooden bench",
        "the pointed seam was catching the cloth, not the bench itself",
        "the nursery keeper",
        "turn the slacks inside out, cover the sharp seam with a soft patch, and lift the cloth together",
        "The bench stood smooth, and the slacks danced free without one scratch.",
        "The button squeaked, “I meant to be shiny, not whiny!”",
    ),
    "tinsel_tunnel": RhymeCase(
        "tinsel_tunnel",
        "the moonlit playroom",
        "a silver tinsel tunnel",
        "the sharp slacks tore a tiny path through the sparkling tunnel",
        "the loose tinsel was brushing the pointed pocket edge",
        "the moon-mice",
        "hold the tunnel open, fold the sharp pocket flat, and guide the slacks through slowly",
        "The tunnel twinkled whole, and the slacks came out as neat as a song.",
        "A moon-mouse wore a thimble and called it a helmet.",
    ),
    "painted_pail": RhymeCase(
        "painted_pail",
        "the bright craft yard",
        "a blue painted pail",
        "the sharp slacks hooked the pail handle and sent paint wobbling",
        "the pointed belt loop was hooked around the handle",
        "the laughing art teacher",
        "set down the brush, unhook the loop, and carry the pail between two pairs of hands",
        "The paint stayed in the pail, and the blue pail shone like a bell.",
        "The pail declared, “I am a bucket, not a rocket!”",
    ),
    "picnic_ribbon": RhymeCase(
        "picnic_ribbon",
        "the daisy picnic hill",
        "a long yellow ribbon",
        "the sharp slacks caught the ribbon and wrapped it round a basket",
        "the stiff cuff had made the ribbon twist",
        "a team of ducklings",
        "pin the ribbon gently, soften the cuff with a napkin, and unwind it together",
        "The basket opened wide, and the ribbon waved like sunshine.",
        "One duckling saluted with a crumb and called it a grand parade.",
    ),
}

HEROES = ["Luna", "Pip", "Mara", "Toby", "Nell", "Rory"]
PARTNERS = ["Bram", "Kit", "Daisy", "Otto", "Wren", "Milo"]
ROLES = ["spry tailor", "cheerful helper", "little drummer", "curious dancer"]
OPENERS = [
    "Hush-a-bye, hum-a-hum",
    "By the moon's small silver drum",
    "One bright morn, with bells in tune",
    "Underneath the nursery moon",
]


def build_world(params: StoryParams) -> World:
    case = CASES[params.case]
    world = World()
    hero = world.add(Entity(params.hero, "character", params.hero))
    partner = world.add(Entity(params.partner, "character", params.partner))
    slacks = world.add(Entity("slacks", "garment", "sharp slacks"))
    seam = world.add(Entity("seam", "edge", "sharp seam"))
    hero.meters.update({"care": 0.0, "worry": 1.0, "laughter": 0.0})
    partner.meters.update({"care": 0.0, "worry": 0.0, "laughter": 0.0})
    slacks.meters.update({"sharpness": 1.0, "snag": 1.0, "safe": 0.0})
    seam.memes.update({"prickly": 1.0})
    world.facts.update(hero=hero, partner=partner, slacks=slacks, seam=seam, case=case)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    partner: Entity = f["partner"]  # type: ignore[assignment]
    slacks: Entity = f["slacks"]  # type: ignore[assignment]
    case: RhymeCase = f["case"]  # type: ignore[assignment]
    opener = OPENERS[(params.seed or 0) % len(OPENERS)]

    world.say(
        f"{opener}, {params.hero}, a {params.role}, came skipping to {case.place}. "
        f"{params.partner} skipped too, with a grin and a shoe."
    )
    world.say(
        f"{params.hero} wore sharp slacks with a pointy little seam, "
        f"and they shimmered and shimmied like trousers in a dream."
    )
    world.say(
        f"Near them waited {case.object_name}. {case.trouble.capitalize()} "
        f"with a tug and a tiny, “Oh dear!”"
    )
    world.para()

    world.say(
        f'"Stop, hop, do not pull!" cried {params.partner}. '
        f'"Let us look before we leap."'
    )
    world.say(
        f'"I thought my slacks were fancy," said {params.hero}. '
        f'"Now they are acting like a crab with too many feet!"'
    )
    hero.meters["worry"] = 1.0
    partner.meters["care"] = 1.0
    partner.meters["laughter"] = 0.5
    world.say(f"{case.joke} Even the sharp slacks seemed to giggle with a rustle.")
    world.say(f"They watched closely. {case.clue.capitalize()}.")
    world.para()

    world.say(
        f"{params.hero} took one breath. "
        f'"Teamwork?" asked {params.hero}. "Teamwork!" answered {params.partner}.'
    )
    world.say(
        f"Together they called for {case.helper}. The helper brought patience, "
        f"soft hands, and one very sensible plan."
    )
    world.say(f"They would {case.fix}.")
    slacks.meters["sharpness"] = 0.0
    slacks.meters["snag"] = 0.0
    slacks.meters["safe"] = 1.0
    hero.meters["care"] = 1.0
    hero.meters["worry"] = 0.0
    hero.meters["laughter"] = 1.0
    partner.meters["care"] = 1.0
    partner.meters["laughter"] = 1.0
    world.fired.update({"warning", "clue_found", "teamwork", "repair"})
    world.say(case.ending)
    world.say(
        f'"Sharp ideas need soft care," said {params.partner}. '
        f'"And funny troubles need helping hands."'
    )
    world.say(
        f"{params.hero} bowed to the nursery crowd. "
        f"Then the {params.hero} and {params.partner} danced a two-step jig: "
        f"tap, clap, turn, and laugh."
    )
    world.facts["resolved"] = True
    return world


def valid_cases() -> list[str]:
    return sorted(CASES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case = args.case or rng.choice(valid_cases())
    if case not in CASES:
        raise StoryError(f"Unknown rhyme case: {case}")
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        partner=args.partner or rng.choice(PARTNERS),
        role=args.role or rng.choice(ROLES),
        case=case,
    )


def generation_prompts(world: World) -> list[str]:
    case: RhymeCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a nursery rhyme about {hero.id} and sharp slacks near {case.object_name}.",
        f"Tell a humorous teamwork story in which {hero.id} solves this trouble: {case.trouble}.",
        "Use a gentle rhyme, spoken dialogue, a clue, and a happy repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: RhymeCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What caused trouble for {hero.id}?",
            answer=f"The sharp slacks caused trouble because {case.trouble.lower()}.",
        ),
        QAItem(
            question="What clue did the team discover?",
            answer=f"They discovered that {case.clue}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {partner.id} solve the problem?",
            answer=f"They used teamwork to {case.fix}.",
        ),
        QAItem(
            question="What humorous moment appeared in the rhyme?",
            answer=case.joke,
        ),
        QAItem(
            question="How did everyone know the problem was fixed?",
            answer=case.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a sharp edge be handled carefully?",
            answer="A sharp edge can scratch or poke, so people should slow down, keep fingers away, and ask for help when needed.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people cooperate, share ideas, and use their different strengths to solve a problem together.",
        ),
        QAItem(
            question="How can humor help during a small problem?",
            answer="Gentle humor can ease worry and help people stay calm, while careful actions still repair the problem safely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
sharp_slacks(X) :- slacks(X), sharp(X).
teamwork_story :- sharp_slacks(slacks), clue_found, repair_done.
valid_case(C) :- case(C), teamwork_story.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("slacks", "slacks"),
        asp.fact("sharp", "slacks"),
        asp.fact("clue_found"),
        asp.fact("repair_done"),
    ]
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show teamwork_story/0."))
    found = bool(asp.atoms(model, "teamwork_story"))
    if not found:
        print("ASP verification failed: teamwork story was not proved.")
        return 1
    print("OK: ASP proves sharp-slacks teamwork story.")
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
    parser = argparse.ArgumentParser(description="Sharp slacks nursery-rhyme storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--role", choices=ROLES)
    parser.add_argument("--case", choices=valid_cases())
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show teamwork_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show teamwork_story/0."))
        print(asp.atoms(model, "teamwork_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case_id in enumerate(valid_cases()):
            local_args = argparse.Namespace(
                hero=args.hero,
                partner=args.partner,
                role=args.role,
                case=case_id,
            )
            params = resolve_params(local_args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
