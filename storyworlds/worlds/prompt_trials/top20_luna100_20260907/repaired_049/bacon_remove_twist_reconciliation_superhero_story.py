#!/usr/bin/env python3
"""
A child-facing superhero storyworld about bacon, a difficult removal, a twist,
and reconciliation.

The world simulates a small rescue: a young hero must remove a dangerous bacon
grease spill from a rooftop without blaming the person who caused it. The turn
comes when the apparent troublemaker reveals a hidden rescue motive. Repair and
reconciliation restore both the roof and the friendship.
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
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.meme(key) + amount


@dataclass(frozen=True)
class Mission:
    id: str
    danger: str
    clue: str
    helpful_item: str
    removal_action: str
    result: str
    twist: str
    reconciliation: str
    ending: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, str]] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


MISSIONS = [
    Mission(
        "slippery_roof",
        "a slick strip of bacon grease beside the school chimney",
        "tiny paw prints crossed the grease and ended near a trapped kitten",
        "a rope, a cloth, and a box of dry oats",
        "spread the oats over the grease, tied the rope to the chimney post, and wiped the roof in small safe patches",
        "the roof became firm enough for the rescue ladder",
        "the grease had been spilled by Pip, who had tried to lure the hungry kitten away from the hot chimney",
        "Nova listened to Pip's reason, and Pip helped gather every greasy cloth instead of hiding",
        "The kitten purred in a warm basket while the clean roof glittered under the morning sun.",
    ),
    Mission(
        "bacon_bridge",
        "a bacon-slick bridge above the town's little canal",
        "a row of crumbs pointed toward a floating lunch tin below the bridge",
        "sand, a broom, and two bright safety flags",
        "covered the slick boards with sand, swept toward the rail, and marked the safe crossing with flags",
        "the children crossed safely and the lunch tin was pulled from the water",
        "Rex had dropped the bacon while reaching for the tin after seeing it drift toward a duckling",
        "Nova admitted the bridge looked worse than the reason behind the spill, and Rex agreed to ask for help next time",
        "The duckling waddled after its lunch tin while the bridge stood dry and bright.",
    ),
    Mission(
        "grease_alarm",
        "a bacon grease puddle beneath the red alarm lever",
        "the alarm handle was clean, but one tiny grease mark led toward a loose window",
        "a mop, a bucket of warm water, and a spare warning sign",
        "blocked the lever, placed the warning sign, and removed the grease before testing the alarm",
        "the alarm worked without anyone slipping",
        "Mina had knocked over the pan while trying to close the window before rain soaked the town map",
        "Nova apologized for assuming carelessness, and Mina promised to call the hero before moving heavy pans",
        "The alarm bell rang clearly, and rain tapped a clean window above the rescued map.",
    ),
    Mission(
        "market_rooftop",
        "a trail of bacon fat across the market roof",
        "the trail curved around a basket of bread left near the edge",
        "chalk, a hand brush, and a sturdy tray",
        "marked the slick places, brushed the fat onto the tray, and moved the bread away from the edge",
        "the market roof stayed safe for the shopkeepers",
        "Tavi had made the trail while carrying food to a tired baker's family upstairs",
        "Nova and Tavi shared the cleanup and made a rule to carry food in covered trays",
        "The baker's family ate together while the market roof shone clean beneath the stars.",
    ),
    Mission(
        "moonlight_slide",
        "a bacon grease slide on the roof of the community hall",
        "a silver button lay at the end of the slide beside a torn costume",
        "a ladder, powdered clay, and a soft magnet",
        "used the clay to remove the slippery shine, then lifted the button with the magnet",
        "the missing costume button was returned before the moonlight show",
        "Sol had spilled the bacon while climbing up to retrieve the costume from a windy line",
        "Nova told Sol that asking would have been safer, and Sol helped repair the costume",
        "The curtain rose on time, and the heroes onstage bowed beneath a clean moonlit roof.",
    ),
]

HERO_NAMES = ["Luna", "Nova", "Mira", "Zia", "Ari", "Kira"]
SIDEKICKS = ["Pip", "Rex", "Mina", "Tavi", "Sol"]
POWERS = [
    ("moonlight shield", "a pale shield that made slippery places easy to see"),
    ("wind ribbon", "a ribbon of wind that carried crumbs and dust into a neat pile"),
    ("kindness beacon", "a warm beam that helped frightened people speak honestly"),
    ("steady boots", "boots that held fast when a roof or bridge became slick"),
    ("spark gloves", "gloves that gently moved small objects without touching danger"),
]
DIALOGUE = [
    ("I can remove the danger, but I need to know what happened first.", "I was trying to help, and I made the mess worse."),
    ("Please tell me why the bacon is here before I decide who is at fault.", "I saw someone in trouble and rushed instead of asking for help."),
    ("A superhero protects people and listens to them.", "Then I will help clean up and tell the truth."),
    ("We can fix the spill without turning a mistake into a fight.", "I am sorry I hid it. I will help make the roof safe."),
]
LESSONS = [
    "Bravery is stronger when it leaves room for the truth.",
    "Removing a danger is important, but removing blame from a frightened friend matters too.",
    "A real superhero repairs trust as carefully as a broken place.",
    "Listening can reveal the good intention hidden inside a bad-looking mistake.",
]


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    power: str
    mission: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about bacon, removal, and reconciliation."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--sidekick", choices=SIDEKICKS)
    parser.add_argument("--power", choices=[p[0] for p in POWERS])
    parser.add_argument("--mission", choices=[m.id for m in MISSIONS])
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
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    power = args.power or rng.choice([p[0] for p in POWERS])
    mission = args.mission or rng.choice([m.id for m in MISSIONS])
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(hero, sidekick, power, mission)


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero == params.sidekick:
        raise StoryError("A hero cannot also be the sidekick in this mission.")
    if params.mission not in {m.id for m in MISSIONS}:
        raise StoryError(f"Unknown mission: {params.mission}.")
    if params.power not in {p[0] for p in POWERS}:
        raise StoryError(f"Unknown power: {params.power}.")


def tell(world: World, params: StoryParams) -> None:
    mission = next(m for m in MISSIONS if m.id == params.mission)
    power_description = dict(POWERS)[params.power]
    hero = world.add(Entity(params.hero, "character", "superhero", params.hero))
    sidekick = world.add(Entity(params.sidekick, "character", "sidekick", params.sidekick))
    roof = world.add(Entity("roof", "place", "roof", "the rescue roof"))
    bacon = world.add(Entity("bacon", "thing", "food", "the bacon"))
    grease = world.add(Entity("grease", "thing", "hazard", "the slick grease"))

    hero.add_meme("courage")
    hero.add_meme("curiosity")
    sidekick.add_meme("worry")
    grease.add_meter("danger", 1.0)

    world.say(
        f"By day, {params.hero} was a young superhero who used a {params.power}; "
        f"its power was {power_description}."
    )
    world.say(
        f"One bright morning, the hero and {params.sidekick} raced to {mission.danger}."
    )
    world.say(
        f"The bacon had left a shining path, and anyone who stepped on it could slide toward danger."
    )
    world.say(f"{params.hero} lifted a hand and said, \"{DIALOGUE[params.seed % len(DIALOGUE) if params.seed is not None else 0][0]}\"")
    world.say(f"{params.sidekick} answered, \"{DIALOGUE[params.seed % len(DIALOGUE) if params.seed is not None else 0][1]}\"")
    world.paragraph()

    world.say(f"Instead of rushing, {params.hero} studied the roof.")
    world.say(f"{mission.clue.capitalize()}.")
    hero.add_meme("attention")
    hero.add_meter("safe_plan")
    sidekick.add_meme("honesty")
    world.say(
        f"The pair carried {mission.helpful_item}. First they made a safe circle around the bacon and grease."
    )
    world.say(f"Then {params.hero} used the {params.power} while {params.sidekick} watched the edge.")
    world.say(f"Together they {mission.removal_action}.")
    grease.add_meter("danger", -1.0)
    grease.add_meter("removed", 1.0)
    hero.add_meter("helped")
    sidekick.add_meter("helped")
    world.say(f"The removal worked: {mission.result}.")
    world.paragraph()

    world.say("Then came the twist.")
    world.say(f"{mission.twist.capitalize()}.")
    world.say(
        f"{params.sidekick} lowered their head and said, \"I thought you would be angry.\""
    )
    world.say(
        f"{params.hero} replied, \"I was worried about the danger, but I still want to understand you.\""
    )
    sidekick.add_meme("relief")
    hero.add_meme("empathy")
    world.say(f"{mission.reconciliation.capitalize()}.")
    world.say(
        f"They made a new promise: call for help before carrying hot bacon, heavy pans, or anything near an edge."
    )
    world.say(f"The lesson stayed with {params.hero}: {LESSONS[(params.seed or 0) % len(LESSONS)]}")
    world.say(mission.ending)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        roof=roof,
        bacon=bacon,
        grease=grease,
        mission=mission,
        power_description=power_description,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World("the town rooftops")
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a superhero story in which {hero.label} must remove bacon grease from a dangerous place.",
        f"Tell a child-friendly superhero tale with a twist: {mission.twist}.",
        "Write a story where a careful rescue leads to reconciliation instead of blame.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    sidekick: Entity = world.facts["sidekick"]
    return [
        QAItem(
            "Who had to remove the bacon danger?",
            f"{hero.label} and {sidekick.label} worked together to remove the bacon grease danger.",
        ),
        QAItem(
            "Why was the grease dangerous?",
            f"The grease was dangerous because it made {mission.danger} slippery, so someone could slide toward harm.",
        ),
        QAItem(
            "What clue did the hero notice?",
            f"The hero noticed that {mission.clue}.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {mission.twist}.",
        ),
        QAItem(
            "How did reconciliation happen?",
            f"Reconciliation happened when the hero listened without blaming, and the sidekick helped clean up and promised to ask for help next time.",
        ),
        QAItem(
            "What changed at the end?",
            f"The danger was removed, the rescue succeeded, and the friends made a safer promise together: {mission.reconciliation}.",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            "Why should someone remove grease from a walkway?",
            "Grease can make a surface slippery, so removing it helps people walk safely.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is a surprising change in what the reader thought was happening.",
        ),
        QAItem(
            "What does reconciliation mean?",
            "Reconciliation means repairing a relationship after hurt or disagreement by listening, apologizing, and making things right.",
        ),
        QAItem(
            "What makes a superhero helpful?",
            "A helpful superhero protects people, thinks carefully, listens to others, and repairs harm instead of only showing strength.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(hero, mission) :- hero(hero), mission(mission).
safe(mission) :- valid(_, mission), removes_grease(mission).
reconciled(mission) :- safe(mission), listens(mission), repairs_trust(mission).
#show valid/2.
#show safe/1.
#show reconciled/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "superhero"),
            asp.fact("mission", "bacon_rescue"),
            asp.fact("removes_grease", "bacon_rescue"),
            asp.fact("listens", "bacon_rescue"),
            asp.fact("repairs_trust", "bacon_rescue"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_signature() -> set[tuple[str, tuple]]:
    import asp
    model = asp.one_model(
        asp_program("#show valid/2.\n#show safe/1.\n#show reconciled/1.")
    )
    return {
        (name, args)
        for name in ("valid", "safe", "reconciled")
        for args in asp.atoms(model, name)
    }


def asp_verify() -> int:
    expected = {
        ("valid", ("superhero", "bacon_rescue")),
        ("safe", ("bacon_rescue",)),
        ("reconciled", ("bacon_rescue",)),
    }
    actual = asp_signature()
    if actual != expected:
        print(f"MISMATCH: expected {sorted(expected)}, got {sorted(actual)}")
        return 1
    for seed in range(5):
        params = StoryParams("Luna", "Pip", "moonlight shield", "slippery_roof", seed)
        sample = generate(params)
        if "bacon" not in sample.story.lower() or "remove" not in sample.story.lower():
            print("MISMATCH: generated story lacks required narrative words")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


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
    StoryParams("Luna", "Pip", "moonlight shield", "slippery_roof", 1),
    StoryParams("Nova", "Rex", "steady boots", "bacon_bridge", 2),
    StoryParams("Mira", "Mina", "kindness beacon", "grease_alarm", 3),
    StoryParams("Zia", "Tavi", "wind ribbon", "market_rooftop", 4),
    StoryParams("Ari", "Sol", "spark gloves", "moonlight_slide", 5),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show safe/1.\n#show reconciled/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2.\n#show safe/1.\n#show reconciled/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(0, args.n)):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
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
        if args.all:
            header = f"### {sample.params.hero}: {sample.params.mission}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
