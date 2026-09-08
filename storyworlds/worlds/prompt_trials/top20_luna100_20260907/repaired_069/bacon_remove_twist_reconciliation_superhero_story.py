#!/usr/bin/env python3
"""Child-friendly superhero stories about bacon, removal, a twist, and reconciliation."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    partner: str = "Bolt"
    helper: str = "Mira"
    place: str = "Skyline City"
    trial: int = 0
    opening: int = 0
    twist: int = 0
    reconciliation: int = 0
    ending: int = 0


HEROES = ["Luna", "Nova", "Comet", "Echo", "Stella", "Ray"]
PARTNERS = ["Bolt", "Dash", "Rocket", "Beacon", "Zip"]
HELPERS = ["Mira", "Pip", "Sunny", "June", "Kai"]
PLACES = ["Skyline City", "Harbor Heights", "Moonbeam Town", "Brightbridge"]

TRIALS = [
    {
        "title": "the bacon beacon",
        "problem": "A giant bacon-shaped beacon had jammed above the city kitchen, and its sizzling signal was drawing hungry pigeons into traffic.",
        "dismissal": "Your tiny magnet will never remove that heavy sign!",
        "clue": "Luna noticed that the beacon was held by one loose copper loop, not by the whole tower.",
        "action": "She used a gentle pull on the loop while Mira guided the falling sign onto a padded rescue net.",
        "result": "The beacon came down safely, and the pigeons flew toward a quiet rooftop.",
        "lesson": "A careful hero studies what really needs to move.",
        "object": "the bacon beacon",
    },
    {
        "title": "the bacon-bot parade",
        "problem": "A parade robot shaped like a strip of bacon rolled in circles and blocked the children’s route home.",
        "dismissal": "I will push it away myself. Your plan is too small!",
        "clue": "Luna saw that a red ribbon had wrapped around one wheel.",
        "action": "She asked Bolt to hold the robot steady while she removed the ribbon with a soft light beam.",
        "result": "The robot straightened up and played a cheerful tune for the parade.",
        "lesson": "Removing the true cause can be kinder than using more force.",
        "object": "the bacon-bot",
    },
    {
        "title": "the smoky supper signal",
        "problem": "A kitchen chimney sent bacon-scented smoke across the school field just before the night game.",
        "dismissal": "Only a powerful blast can remove this smoke!",
        "clue": "Luna found a crumpled paper wrapper covering the chimney’s air vent.",
        "action": "She lifted the wrapper away while Mira opened the windows on the calm side of the building.",
        "result": "The smoke cleared, and the supper cooks could breathe easily again.",
        "lesson": "The smallest hidden blockage can cause the biggest trouble.",
        "object": "the chimney vent",
    },
    {
        "title": "the bacon trophy switch",
        "problem": "A shiny bacon-shaped trophy had been stuck inside a museum’s locked display case.",
        "dismissal": "Break the case and remove the trophy now!",
        "clue": "Luna heard a tiny click beneath the velvet stand.",
        "action": "She pressed the hidden release while Bolt kept the glass from wobbling.",
        "result": "The trophy slid out without a crack, ready for the young inventors’ ceremony.",
        "lesson": "Patience can protect what rushing might damage.",
        "object": "the bacon trophy",
    },
]

OPENINGS = [
    "In {place}, {hero} wore a silver cape and watched over every busy street.",
    "The sunrise flashed across {place} as superhero {hero} answered the city alarm.",
    "At the hero station in {place}, {hero} was polishing a badge when trouble called.",
    "Above {place}, {hero} zoomed between rooftops with {partner} close behind.",
    "The people of {place} trusted {hero} to solve problems without making new ones.",
]

TWISTS = [
    "But then came the twist: the bacon object was not the danger at all.",
    "Then the alarm changed its tune. The real trouble was hidden underneath the bacon-shaped machine.",
    "Just as everyone expected a dramatic lift, Luna discovered a much smaller cause.",
    "The loudest part of the problem turned out to be a distraction.",
]

RECONCILIATIONS = [
    "{partner} lowered their head. 'I rushed to prove I was strong. I should have listened,' they said.",
    "'You were right to look closely,' said {partner}. 'I am sorry I dismissed your plan.'",
    "{partner} took a breath. 'Next time, let us test the gentle idea together.'",
    "'I wanted to be the fastest hero,' {partner} admitted. 'Will you forgive me and let me help?'",
]

ENDINGS = [
    "That evening, the city lights blinked softly while the rescued bacon sign rested safely in the kitchen garden.",
    "The children cheered, and the heroes shared warm sandwiches after checking every wheel and wire twice.",
    "By moonrise, the city was calm again, and the once-stuck bacon object shone beside a note that read: Look closely first.",
    "The team flew home beneath a clear sky, proud that courage had made room for careful listening.",
]

ASP_RULES = r"""
#show needs_remove/1.
#show reconciled/2.
needs_remove(O) :- bacon_object(O), blocked(O).
reconciled(A,B) :- apologized(A), forgave(B,A).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("bacon_object", "beacon"),
            asp.fact("blocked", "beacon"),
            asp.fact("apologized", "bolt"),
            asp.fact("forgave", "luna", "bolt"),
        ]
    )


def asp_program(show: str = "#show needs_remove/1.\n#show reconciled/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about bacon, removal, a twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--trial", type=int, choices=range(len(TRIALS)))
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
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        partner=args.partner or rng.choice(PARTNERS),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        trial=args.trial if args.trial is not None else rng.randrange(len(TRIALS)),
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.partner:
        raise StoryError("hero and partner must be different characters")
    if not params.place:
        raise StoryError("place cannot be empty")
    if not 0 <= params.trial < len(TRIALS):
        raise StoryError("trial is outside the available story trials")

    world = World()
    hero = world.add(Entity(params.hero, "hero", params.hero))
    partner = world.add(Entity(params.partner, "hero", params.partner))
    helper = world.add(Entity(params.helper, "helper", params.helper))
    bacon = world.add(Entity("bacon_object", "object", "bacon object"))

    hero.meters.update(power=0.8, reach=0.6)
    hero.memes.update(care=1.0, courage=1.0)
    partner.meters.update(power=1.0, reach=0.9)
    partner.memes.update(pride=1.0, trust=0.2)
    helper.memes.update(attention=1.0)
    bacon.meters.update(weight=0.7, danger=0.2)
    bacon.memes.update(symbolic_value=1.0)

    trial = TRIALS[params.trial]

    def fmt(text: str) -> str:
        return text.format(
            hero=hero.label,
            partner=partner.label,
            helper=helper.label,
            place=params.place,
        )

    world.say(fmt(OPENINGS[params.opening]))
    world.say(f"{hero.label} saw {trial['problem']}")
    world.say(
        f"{partner.label} pointed at the trouble and said, '{trial['dismissal']}'"
    )
    world.say(
        f"{hero.label} answered, 'Wait. We can remove the cause without hurting anyone.' "
        f"{helper.label} nodded and checked the scene."
    )
    world.say(fmt(TWISTS[params.twist]))
    world.say(f"{hero.label} explained, '{trial['clue']}'")
    world.say(
        f"{partner.label} tried a strong pull, but the object shuddered. "
        f"{hero.label} called, 'Stop! Let us use the safer plan.'"
    )
    world.say(f"{hero.label} and {helper.label} worked together: {trial['action']}")
    world.say(trial["result"])

    partner.memes["pride"] = 0.2
    partner.memes["trust"] = 1.0
    bacon.meters["danger"] = 0.0
    world.say(fmt(RECONCILIATIONS[params.reconciliation]))
    world.say(
        f"{hero.label} smiled. 'Of course. A team is strongest when every hero can listen.'"
    )
    world.say(f"Lesson learned: {trial['lesson']}")
    world.say(ENDINGS[params.ending])

    world.facts.update(
        hero=hero,
        partner=partner,
        helper=helper,
        bacon=bacon,
        trial=trial,
        removed=True,
        twist=True,
        reconciliation=True,
        lesson=trial["lesson"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trial = f["trial"]
    hero = f["hero"].label
    partner = f["partner"].label
    return [
        f"Write a child-friendly superhero story in which {hero} must remove a bacon-related obstacle.",
        f"Tell a superhero story where {partner} doubts {hero}, a twist reveals the true cause, and the heroes reconcile.",
        f"Write a story about {trial['title']} with a gentle solution, spoken dialogue, and a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trial = f["trial"]
    hero = f["hero"].label
    partner = f["partner"].label
    helper = f["helper"].label
    return [
        QAItem(
            question=f"What problem did {hero} face?",
            answer=f"{hero} faced {trial['problem']}",
        ),
        QAItem(
            question=f"What twist changed {hero}'s plan?",
            answer=f"The twist was that the loud bacon-related object was not the true danger; {trial['clue']}",
        ),
        QAItem(
            question=f"How did {hero} and {helper} remove the trouble?",
            answer=trial["action"],
        ),
        QAItem(
            question=f"How did {partner} reconcile with {hero}?",
            answer=f"{partner} apologized for rushing and dismissing the careful plan, then promised to listen and help.",
        ),
        QAItem(
            question="What lesson did the heroes learn?",
            answer=f"The lesson was: {trial['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to remove something?",
            answer="To remove something means to take it away from a place or situation.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change that reveals new information or sends the story in a different direction.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, forgiving, or repairing trust.",
        ),
        QAItem(
            question="What makes a superhero helpful?",
            answer="A helpful superhero protects people, studies the problem, uses power carefully, and works with others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> tuple[set[tuple], set[tuple]]:
    import asp
    model = asp.one_model(asp_program())
    removals = set(asp.atoms(model, "needs_remove"))
    reconciliations = set(asp.atoms(model, "reconciled"))
    return removals, reconciliations


def asp_verify() -> int:
    removals, reconciliations = asp_valid()
    expected_removals = {("beacon",)}
    expected_reconciliations = {("luna", "bolt")}
    if removals != expected_removals or reconciliations != expected_reconciliations:
        print("MISMATCH between clingo and Python gate.")
        print("  clingo removals:", sorted(removals))
        print("  python removals:", sorted(expected_removals))
        print("  clingo reconciliation:", sorted(reconciliations))
        print("  python reconciliation:", sorted(expected_reconciliations))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "bacon" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print("OK: clingo parity and generated stories verified.")
    return 0


CURATED = [
    StoryParams(
        seed=1,
        hero="Luna",
        partner="Bolt",
        helper="Mira",
        place="Skyline City",
        trial=0,
        opening=0,
        twist=0,
        reconciliation=0,
        ending=0,
    ),
    StoryParams(
        seed=2,
        hero="Nova",
        partner="Dash",
        helper="Sunny",
        place="Harbor Heights",
        trial=1,
        opening=2,
        twist=1,
        reconciliation=1,
        ending=2,
    ),
    StoryParams(
        seed=3,
        hero="Comet",
        partner="Rocket",
        helper="June",
        place="Brightbridge",
        trial=3,
        opening=4,
        twist=3,
        reconciliation=3,
        ending=3,
    ),
]


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
        raise SystemExit(asp_verify())

    if args.asp:
        removals, reconciliations = asp_valid()
        print(f"{len(removals)} removable bacon objects")
        for item in sorted(removals):
            print("remove:", item)
        print(f"{len(reconciliations)} reconciliation facts")
        for item in sorted(reconciliations):
            print("reconciliation:", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if not samples:
        raise StoryError("no stories could be generated")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.hero}: superhero trial"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
