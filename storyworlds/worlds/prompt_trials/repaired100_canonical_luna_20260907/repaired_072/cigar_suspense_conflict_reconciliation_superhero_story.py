#!/usr/bin/env python3
"""
A small superhero storyworld about a cigar-shaped signal, a misunderstanding,
and a careful reconciliation.
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
    owner: Optional[str] = None


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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    hero: str
    partner: str
    city: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mission:
    name: str
    danger: str
    clue: str
    misunderstanding: str
    truth: str
    repair: str
    ending: str


HEROES = ["Luna", "Nova", "Mira", "Sol", "Skye", "Aster"]
PARTNERS = ["Rex", "Pip", "Juno", "Kai", "Robin"]
CITIES = ["Bright Harbor", "Starbridge", "Moonrise City", "Copper Heights"]

MISSIONS = [
    Mission(
        "the dark rooftop",
        "the city beacon had gone dark during a thick midnight fog",
        "a silver cigar lay beside the silent control box",
        "that Luna's partner had touched the beacon without permission",
        "the cigar was a harmless signal tube left by the rescue crew, and its silver stripe pointed to a loose cable",
        "listened to both sides, tightened the cable together, and apologized for the quick accusation",
        "the beacon swept a golden path across the fog, and the two heroes stood beneath it as a team",
    ),
    Mission(
        "the museum alarm",
        "the superhero museum alarm began ringing just before closing time",
        "a wooden cigar-shaped case rested near the locked exhibit",
        "that the night guard had hidden a missing device",
        "the case held an old prop from a movie, while the real alarm had been triggered by a window latch",
        "checked the latch, thanked the guard, and returned the prop to its display",
        "the alarm became quiet, and the museum windows shone like friendly stars",
    ),
    Mission(
        "the tunnel message",
        "a whispering alarm echoed through the train tunnel",
        "a small cigar was drawn on a paper map beside a red arrow",
        "that a rival hero had planted a threatening message",
        "the drawing marked a maintenance signal, and the arrow led to a trapped repair worker",
        "followed the safe route, rescued the worker, and cleared up the misunderstanding",
        "the first train rolled through while grateful passengers waved from every window",
    ),
    Mission(
        "the storm tower",
        "lightning flashed around the city's weather tower",
        "a cigar-shaped cloud appeared above a blinking warning lamp",
        "that the storm was an attack caused by the new hero",
        "the cloud was only a weather pattern, and the lamp needed a fresh battery",
        "worked beside the new hero to replace the battery and spoke honestly about the mistake",
        "the warning lamp glowed steadily as rain softened into a shining curtain",
    ),
]


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    mission = rng.choice(MISSIONS)
    world = World(place=f"{params.city}'s {mission.name}")
    hero = world.add(Entity(params.hero, "character", "hero", params.hero))
    partner = world.add(Entity(params.partner, "character", "partner", params.partner))
    cigar = world.add(Entity("cigar", "thing", "cigar", "a cigar-shaped signal tube"))
    beacon = world.add(Entity("beacon", "thing", "beacon", "the city beacon"))

    hero.memes["brave"] = 1.0
    partner.memes["loyal"] = 1.0
    cigar.meters["near_clue"] = 1.0

    world.say(
        f"At dusk in {world.place}, {hero.id}, the city's bright-caped superhero, "
        f"patrolled with {partner.id}. They were ready to help anyone in trouble when "
        f"{mission.danger}."
    )
    world.say(
        f"Then {hero.id} spotted {mission.clue}. The little cigar-shaped object was not burning; "
        f"it was a clue with a silver button and a faint blue light."
    )
    world.say(
        f'"Stay back," {hero.id} said. "This could be dangerous." '
        f'"I can help inspect it," {partner.id} replied.'
    )

    world.para()
    hero.memes["worried"] = 1.0
    world.say(
        f"The suspense tightened like a knot. {hero.id} remembered that {partner.id} had worked "
        f"near the control box earlier, and guessed {mission.misunderstanding}."
    )
    world.say(
        f'"Did you leave this here?" {hero.id} asked. '
        f'"No," {partner.id} said, sounding hurt. "I came to warn you about the danger."'
    )
    world.say(
        f"Instead of arguing beside the clue, {hero.id} used a shield to block the sparks. "
        f"{partner.id} crouched low and followed the blue light. Together they discovered that "
        f"{mission.truth}."
    )

    world.para()
    hero.memes["worried"] = 0.0
    hero.memes["careful"] = 1.0
    cigar.meters["understood"] = 1.0
    beacon.meters["safe"] = 1.0
    world.say(
        f"{hero.id} lowered the shield. " 
        f'"I was wrong to blame you before checking," {hero.id} said. '
        f'"I should have explained sooner," {partner.id} answered.'
    )
    world.say(
        f"They {mission.repair}. The conflict faded because both heroes listened, shared the "
        f"evidence, and chose the safest next step."
    )
    world.say(
        f"At last, {mission.ending}. {hero.id} handed the harmless cigar-shaped signal tube to "
        f"{partner.id}, and they smiled at one another."
    )
    world.say(
        f"That night, the people of {params.city} learned that a true superhero is not only brave "
        f"against danger, but also brave enough to admit a mistake and make peace."
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        cigar=cigar,
        beacon=beacon,
        mission=mission,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a superhero story in which {hero.id} investigates {mission.name} after finding a cigar-shaped clue.",
        "Tell a suspenseful child-safe story with conflict, careful evidence, and reconciliation.",
        f"Write a superhero adventure where the truth is revealed: {mission.truth}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    mission: Mission = f["mission"]
    return [
        QAItem(
            f"What danger did {hero.id} discover?",
            f"{hero.id} discovered that {mission.danger}.",
        ),
        QAItem(
            f"What was the cigar-shaped clue?",
            f"It was {mission.clue}. It helped the heroes investigate the danger without rushing.",
        ),
        QAItem(
            f"What misunderstanding caused the conflict?",
            f"{hero.id} guessed {mission.misunderstanding}, but that guess was wrong.",
        ),
        QAItem(
            f"How did {hero.id} and {partner.id} learn the truth?",
            f"They protected the area, followed the blue light, and discovered that {mission.truth}.",
        ),
        QAItem(
            "How did the heroes reconcile?",
            f"They {mission.repair}. They also admitted their mistakes and listened to each other.",
        ),
        QAItem(
            "What made the ending safe and happy?",
            f"The danger was handled, and {mission.ending}. The heroes ended the night as friends and teammates.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is suspense?",
            "Suspense is the feeling of wondering what will happen next, especially when a character faces an uncertain danger.",
        ),
        QAItem(
            "What is conflict in a story?",
            "Conflict is a problem or disagreement that characters must face and try to solve.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by listening, apologizing, and repairing trust.",
        ),
        QAItem(
            "Why should an unknown object be checked carefully?",
            "Checking carefully helps people understand a possible danger before touching it, blaming someone, or making a rushed decision.",
        ),
        QAItem(
            "What is a cigar?",
            "A cigar is a tightly rolled bundle of dried tobacco made for smoking. In this story, the cigar-shaped object is a harmless signal tube and is not smoked.",
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
safe_signal :- clue(cigar), understood(cigar), protected(beacon).
reconciled :- apologized(hero), listened(partner), conflict_resolved.
happy_ending :- safe_signal, reconciled.

#show safe_signal/0.
#show reconciled/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue", "cigar"),
            asp.fact("understood", "cigar"),
            asp.fact("protected", "beacon"),
            asp.fact("apologized", "hero"),
            asp.fact("listened", "partner"),
            asp.fact("conflict_resolved"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    if asp.atoms(model, "happy_ending"):
        print("OK: ASP confirms safety, reconciliation, and a happy ending.")
        return 0
    print("MISMATCH: ASP did not confirm the happy ending.")
    return 1


def validate_params(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("hero must have a name")
    if not params.partner.strip():
        raise StoryError("partner must have a name")
    if params.hero == params.partner:
        raise StoryError("hero and partner must be different characters")
    if not params.city.strip():
        raise StoryError("city must not be empty")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
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
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about a cigar-shaped clue and reconciliation."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--city", choices=CITIES)
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
    hero = args.hero or rng.choice(HEROES)
    available = [name for name in PARTNERS if name != hero]
    partner = args.partner or rng.choice(available)
    city = args.city or rng.choice(CITIES)
    return StoryParams(hero=hero, partner=partner, city=city)


CURATED = [
    StoryParams("Luna", "Rex", "Bright Harbor", 8101),
    StoryParams("Nova", "Pip", "Starbridge", 8102),
    StoryParams("Mira", "Juno", "Moonrise City", 8103),
    StoryParams("Sol", "Kai", "Copper Heights", 8104),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_signal/0. #show reconciled/0. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show safe_signal/0. #show reconciled/0. #show happy_ending/0."
            )
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
