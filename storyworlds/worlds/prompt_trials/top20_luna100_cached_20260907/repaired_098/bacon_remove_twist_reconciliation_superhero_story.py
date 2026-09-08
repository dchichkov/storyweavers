#!/usr/bin/env python3
"""A child-facing superhero story about bacon, removal, a twist, and reconciliation."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str = "hero headquarters"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Mission:
    trouble: str
    risk: str
    first_plan: str
    failed_reason: str
    twist: str
    truth: str
    brave_action: str
    repair: str
    reconciliation: str
    lesson: str
    ending: str


@dataclass
class World:
    tower: Place
    hero: Creature
    partner: Creature
    mission: Mission
    bacon: str
    removed: bool = False
    reconciled: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


TOWERS = {
    "the moonbeam tower": Place("the moonbeam tower", meters={"height": 8.0}),
    "the red-roof tower": Place("the red-roof tower", meters={"height": 6.0}),
    "the cloudstep tower": Place("the cloudstep tower", meters={"height": 10.0}),
}

HEROES = [
    ("Luna", "fox", "sky superhero"),
    ("Nova", "rabbit", "rescue superhero"),
    ("Comet", "cat", "neighborhood superhero"),
]

PARTNERS = [
    ("Pip", "mouse", "signal keeper"),
    ("Rae", "raccoon", "gadget maker"),
    ("Sol", "dog", "rescue planner"),
]

MISSIONS = {
    "banner": Mission(
        "the hero banner covered the emergency beacon",
        "a rescue signal might be hidden when neighbors needed it",
        "pulled the banner down quickly",
        "the beacon cord tightened and made the tower bell ring",
        "the banner had not slipped by accident; it was holding a loose roof tile in place",
        "wind had loosened the tile, and the banner was acting like a safety brace",
        "stopped pulling and asked the partner to hold the ladder while they inspected the roof from below",
        "removed the loose tile with a safety hook, then took down and folded the banner",
        "the partner apologized for hiding the danger, and the hero apologized for blaming the banner plan",
        "a teammate deserves the truth, especially when a quick fix is protecting someone",
        "the beacon shone above the folded banner while both heroes watched the safe roof",
    ),
    "bacon": Mission(
        "a strip of bacon hung across the robot door",
        "the hungry rescue robot could not roll out during an emergency",
        "tried to remove the bacon with a gloved paw",
        "the robot's warm wheel began turning whenever the strip tugged",
        "the bacon was not stuck in the door; it was tied to a hidden warning bell",
        "the partner had tied the bacon there to warn everyone that the robot's wheel was overheating",
        "kept paws away from the moving wheel and asked why the strange warning had been made",
        "removed the bacon only after cooling the wheel, then replaced it with a bright safe ribbon",
        "the hero listened to the partner's reason, and the partner admitted the warning should have been explained",
        "removing a problem safely may require understanding what job it was doing",
        "the robot rolled out beneath a bright ribbon while the bacon rested on a breakfast plate",
    ),
    "shadow": Mission(
        "a giant shadow covered the playground",
        "children might believe a monster was hiding near the swings",
        "shone the tower lamp straight at the shadow",
        "the shadow grew larger instead of smaller",
        "a new solar sail had folded over the lamp and cast the shape",
        "the sail was catching moonlight while its control rope was tangled",
        "called the partner before climbing near the sail",
        "lowered the sail with a pulley, removed the knot, and tested the lamp from the ground",
        "the partner explained the rushed shortcut, and the hero agreed to ask before changing equipment",
        "a frightening shape can have an ordinary cause, but feelings still deserve kind words",
        "the playground glowed again as the sail rested neatly beside the tower",
    ),
    "whistle": Mission(
        "the rescue whistle kept chirping by itself",
        "a false alarm could send heroes toward the wrong danger",
        "planned to remove its battery at once",
        "the chirping became louder when the battery cover moved",
        "a loose thread was pressing the whistle button against a spring",
        "the partner had sewn the thread into a signal flag during a hurried repair",
        "held the whistle still and asked the partner to explain the repair",
        "removed the thread, tightened the button, and tested the whistle three times",
        "both heroes admitted they had rushed because they were worried, then made a slower repair plan",
        "good teamwork makes room for both safety and honest explanations",
        "the whistle gave one clear chirp, and the signal flag waved without a sound",
    ),
}

MISSION_KEYS = list(MISSIONS)
ROUTES = ("alarm_first", "dialogue_first", "bacon_first", "twist_first", "quiet_first")


ASP_RULES = r"""
hero(luna).
hero(nova).
hero(comet).
mission(banner).
mission(bacon).
mission(shadow).
mission(whistle).
contains_bacon(bacon).
remove_action(bacon).
twist_required.
reconciliation_required.
valid_story(M) :- mission(M), contains_bacon(bacon), remove_action(bacon), twist_required, reconciliation_required.
"""


def mission_id(text: str) -> str:
    return "mission_" + "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("contains_bacon", "bacon"),
        asp.fact("remove_action", "bacon"),
        asp.fact("twist_required"),
        asp.fact("reconciliation_required"),
    ]
    for key in MISSION_KEYS:
        lines.append(asp.fact("mission", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {(key,) for key in MISSION_KEYS}
    if found == expected:
        print(f"OK: clingo gate matches python reasoning ({len(expected)} missions).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.tower_name, params.hero_name, params.hero_species,
        params.partner_name, params.partner_species, params.mission, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    tower_name: str = "the moonbeam tower"
    hero_name: str = "Luna"
    hero_species: str = "fox"
    partner_name: str = "Pip"
    partner_species: str = "mouse"
    mission: str = "bacon"
    route: str = "alarm_first"


def build_world(params: StoryParams) -> World:
    if params.tower_name not in TOWERS:
        raise StoryError(f"Unknown tower: {params.tower_name}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    template = TOWERS[params.tower_name]
    return World(
        tower=Place(template.name, template.kind, dict(template.meters)),
        hero=Creature(params.hero_name, params.hero_species, "superhero"),
        partner=Creature(params.partner_name, params.partner_species, "hero partner"),
        mission=MISSIONS[params.mission],
        bacon="a strip of bacon",
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    hero, partner, tower, mission = world.hero, world.partner, world.tower, world.mission
    hero.memes.update(courage=0.0, curiosity=1.0)
    partner.memes.update(care=1.0, trust=0.0)

    openings = {
        "alarm_first": f"The alarm flashed at {tower.name}. {mission.trouble.capitalize()}, and {hero.name} the {hero.species} superhero raced to help.",
        "dialogue_first": f'"We have a problem at {tower.name}," said {hero.name}, the {hero.species} superhero. {mission.trouble.capitalize()}, but nobody knew why.',
        "bacon_first": f"{hero.name} spotted {world.bacon} before seeing the danger at {tower.name}. It hung across the door, where {mission.trouble}.",
        "twist_first": f"Everyone thought {mission.trouble}, but the strangest clue was {world.bacon}. {hero.name}, the tower superhero, reached for it.",
        "quiet_first": f"The busy tower suddenly went quiet. {mission.trouble.capitalize()}, and {hero.name} noticed {world.bacon} nearby.",
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"It mattered because {mission.risk}.",
        f"The danger was small to look at, but {mission.risk}.",
        f"Even the bravest hero paused because {mission.risk}.",
    ]))
    world.say(rng.choice([
        f'"I will fix it fast," {hero.name} said. {partner.name} shook their head. "First, tell me what you see."',
        f'"Please wait," {partner.name} said. "{mission.risk.capitalize()}." {hero.name} listened, though the alarm still flashed.',
        f'{hero.name} asked, "Are you sure this is the cause?" {partner.name} answered, "No. That is why we should check together."',
    ]))

    world.para()
    world.say(f"At first, the heroes planned to {mission.first_plan}.")
    world.say(rng.choice([
        f"But the plan failed: {mission.failed_reason}.",
        f"The quick plan made things worse because {mission.failed_reason}.",
        f'{hero.name} stopped when {mission.failed_reason}.',
    ]))
    world.say(f"Then came the twist. {mission.twist.capitalize()}.")
    world.say(f"They learned that {mission.truth}.")
    world.say(f'"You should have told me," {hero.name} said. {partner.name} looked down. "I was trying to protect everyone."')

    world.para()
    world.say(f"Being a superhero did not mean rushing. {hero.name} {mission.brave_action}.")
    hero.memes["courage"] = 1.0
    hero.meters["safe_checks"] = 2.0
    world.say(f"Together, they {mission.repair}.")
    world.removed = True
    world.tower.meters["hazard_removed"] = 1.0
    world.say(f"Then reconciliation began: {mission.reconciliation}.")
    partner.memes["trust"] = 1.0
    world.reconciled = True

    world.para()
    world.say(rng.choice([
        f'{hero.name} wrote the lesson in the hero log: "{mission.lesson.capitalize()}."',
        f'"What will we remember?" asked {partner.name}. {hero.name} answered, "{mission.lesson.capitalize()}."',
        f"The rescue changed both heroes. They agreed that {mission.lesson}.",
    ]))
    world.say(rng.choice([
        f"At sunset, {mission.ending.capitalize()}.",
        f"By the time the stars appeared, {mission.ending.capitalize()}.",
        f"The safe ending was easy to see: {mission.ending.capitalize()}.",
    ]))
    world.facts.update(
        hero=hero,
        partner=partner,
        tower=tower,
        mission=mission,
        bacon=world.bacon,
        truth=mission.truth,
        repair=mission.repair,
        lesson=mission.lesson,
        ending=mission.ending,
        removed=world.removed,
        reconciled=world.reconciled,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    return [
        f"Write a superhero story about {f['hero'].name} and {f['partner'].name} handling {mission.trouble}.",
        f"Include {f['bacon']}, a safe removal, a twist revealing that {mission.truth}, and reconciliation.",
        f"End with this image: {f['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mission = f["mission"]
    hero, partner, tower = f["hero"], f["partner"], f["tower"]
    return [
        QAItem(
            question=f"What problem did {hero.name} find at {tower.name}?",
            answer=f"{hero.name} found that {mission.trouble}. It was dangerous because {mission.risk}.",
        ),
        QAItem(
            question=f"Why did the first plan to remove the problem fail?",
            answer=f"The heroes planned to {mission.first_plan}, but {mission.failed_reason}.",
        ),
        QAItem(
            question=f"What was the twist in the rescue?",
            answer=f"The twist was that {mission.twist}. They discovered that {mission.truth}.",
        ),
        QAItem(
            question=f"How did {hero.name} remove the danger safely?",
            answer=f"{hero.name} {mission.brave_action}, and together the heroes {mission.repair}.",
        ),
        QAItem(
            question=f"How did the heroes reconcile?",
            answer=f"{mission.reconciliation} They learned that {mission.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero uses courage, care, and useful skills to help people and solve danger safely.",
        ),
        QAItem(
            question="Why should someone understand a warning before removing it?",
            answer="A warning may be protecting people or equipment, so understanding its purpose helps prevent a new danger.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing trust after people disagree or hurt one another.",
        ),
        QAItem(
            question="Why is teamwork helpful during a rescue?",
            answer="Teamwork lets people share observations, check plans, and make safer choices together.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story with bacon, removal, twist, and reconciliation.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--tower", choices=sorted(TOWERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    tower = args.tower or rng.choice(sorted(TOWERS))
    hero_name, hero_species, _ = rng.choice(HEROES)
    partner_name, partner_species, _ = rng.choice(PARTNERS)
    return StoryParams(
        seed=args.seed,
        tower_name=tower,
        hero_name=args.hero_name or hero_name,
        hero_species=hero_species,
        partner_name=args.partner_name or partner_name,
        partner_species=partner_species,
        mission=rng.choice(MISSION_KEYS),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.tower, world.hero, world.partner):
        lines.append(f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}")
    lines.append(
        f"bacon={world.bacon!r} removed={world.removed} reconciled={world.reconciled} "
        f"truth={world.facts.get('truth', '')!r}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 4 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
