#!/usr/bin/env python3
"""A child-facing superhero story about bacon, a twist, and reconciliation."""

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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    bacon: str
    name: str
    partner: str
    rival: str
    power: str = ""
    twist: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mission:
    danger: str
    suspicion: str
    first_plan: str
    failure: str
    hidden_truth: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


PLACES = {
    "rooftop": Scene("the rooftop kitchen", "bright", "a warm breeze"),
    "market": Scene("the town market", "busy", "a fluttering wind"),
    "station": Scene("the rescue station", "hushed", "a silver rain"),
}

BACON = {
    "bacon": "a basket of sizzling bacon",
    "crispy_bacon": "a tray of crisp bacon",
    "maple_bacon": "a warm plate of maple bacon",
}

HEROES = {
    "Luna": ("girl", "moonlight"),
    "Max": ("boy", "super speed"),
    "Zara": ("girl", "light shields"),
    "Nico": ("boy", "sky leaps"),
}

PARTNERS = {"Pip": "robot", "Maya": "girl", "Ollie": "boy", "Bee": "girl"}
RIVALS = {"Vex": "masked hero", "Bolt": "young hero", "Crow": "night flyer", "Moss": "forest hero"}
TWISTS = ("secret_recipe", "windy_cape", "hungry_rescue", "false_alarm")
ROUTES = ("alarm_first", "bacon_first", "dialogue_first", "team_first", "quiet_first")

MISSIONS = {
    "secret_recipe": Mission(
        "the bacon basket disappeared before the town heroes' breakfast",
        "the rival was seen beside the empty counter",
        "followed the rival's footprints across the flour",
        "the footprints ended at a clean window, so they did not explain the missing food",
        "the rival had not stolen the bacon; they had removed it from a hot oven to stop a fire",
        "shared the rescued bacon and rebuilt the oven's loose handle together",
        "a hero must learn the whole story before choosing a target",
        "the heroes ate breakfast beneath a banner that read: Strong hearts listen first",
    ),
    "windy_cape": Mission(
        "the bacon basket rolled toward the edge of the rooftop",
        "the rival's cape flashed beside it just before it vanished",
        "chased the cape and tried to grab the basket",
        "the basket was already gone when the cape landed, leaving the chase empty-handed",
        "the rival had removed the basket because a gust was carrying it toward a frightened pigeon nest",
        "tied down the baskets and mended the rival's torn cape with bright thread",
        "quick eyes still need kind questions",
        "the bacon cooled safely while the pigeon family settled under the repaired cape",
    ),
    "hungry_rescue": Mission(
        "the rescue crew needed bacon sandwiches for a long night",
        "the rival carried a covered tray away from the station",
        "blocked the doorway and demanded that the tray be returned",
        "the tray held no sandwiches, only a blinking warning light",
        "the rival had removed the bacon because a hungry family was trapped behind a fallen cart",
        "freed the family, then made fresh sandwiches for every helper",
        "sharing a plan can turn rivals into teammates",
        "the rescue bell rang while every hero passed warm sandwiches around the station",
    ),
    "false_alarm": Mission(
        "the town's bacon trophy vanished from the market table",
        "a dark glove near the table seemed to belong to the rival",
        "announced that the rival must have taken it",
        "the glove was too small and belonged to a market puppet",
        "the rival had removed the trophy to keep it from falling on a baby goat",
        "apologized, lifted the trophy together, and placed it on a safer stand",
        "a dramatic clue can still tell the wrong story",
        "the trophy shone on its sturdy stand as the goat nibbled a carrot nearby",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story about bacon, a twist, and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--bacon", choices=sorted(BACON))
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=sorted(PARTNERS))
    ap.add_argument("--rival", choices=sorted(RIVALS))
    ap.add_argument("--power")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(p, b) for p in sorted(PLACES) for b in sorted(BACON)]


ASP_RULES = """
valid(Place,Bacon) :- place(Place), bacon(Bacon).
compatible(Place,Bacon) :- valid(Place,Bacon).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        *(asp.fact("place", p) for p in PLACES),
        *(asp.fact("bacon", b) for b in BACON),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.bacon or combo[1] == args.bacon
    ]
    if not combos:
        raise StoryError("No valid superhero mission fits those options.")
    place, bacon = rng.choice(combos)
    name = args.name or "Luna"
    if name not in HEROES:
        power = args.power or "brave teamwork"
        hero_type = "hero"
    else:
        power = args.power or HEROES[name][1]
        hero_type = HEROES[name][0]
    partners = [p for p in sorted(PARTNERS) if p != name] or sorted(PARTNERS)
    return StoryParams(
        place=place,
        bacon=bacon,
        name=name,
        partner=args.partner or rng.choice(partners),
        rival=args.rival or rng.choice(sorted(RIVALS)),
        power=power,
        twist=rng.choice(TWISTS),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (
        params.seed, params.place, params.bacon, params.name, params.partner,
        params.rival, params.power, params.twist, params.route,
    ))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    mission = MISSIONS[params.twist]
    rng = story_rng(params)
    world = World(scene)

    hero_type, _ = HEROES.get(params.name, ("hero", params.power))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        memes={"courage": 1.0, "patience": 0.0},
    ))
    partner = world.add(Entity(
        id=params.partner,
        kind="character",
        type=PARTNERS[params.partner],
        memes={"trust": 0.6},
    ))
    rival = world.add(Entity(
        id=params.rival,
        kind="character",
        type=RIVALS[params.rival],
        memes={"hurt": 0.0, "trust": 0.2},
    ))
    food = world.add(Entity(
        id=params.bacon,
        kind="object",
        type="food",
        label=BACON[params.bacon],
        meters={"warmth": 1.0},
    ))

    openings = {
        "alarm_first": (
            f"At {scene.place}, the hero alarm flashed red. {mission.danger.capitalize()}, "
            f"and {hero.id} raced in with {hero.id}'s {params.power}."
        ),
        "bacon_first": (
            f"The smell of {food.label} floated over {scene.place}, but the basket was suddenly gone. "
            f"{hero.id} promised to find it before the town breakfast began."
        ),
        "dialogue_first": (
            f'"Something is wrong," {params.partner} said at {scene.place}. '
            f"{mission.danger.capitalize()}, and {hero.id} listened before leaping."
        ),
        "team_first": (
            f"{hero.id} and {params.partner} trained together at {scene.place} when "
            f"{mission.danger}."
        ),
        "quiet_first": (
            f"For one quiet moment, {scene.place} smelled of warm food. Then "
            f"{mission.danger.capitalize()}."
        ),
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"{hero.id} checked the exits while {params.partner} protected the people nearby.",
        f"{params.partner} opened a notebook and recorded what had changed.",
        f"The two heroes agreed that rescue came before showing off.",
        f"{hero.id} tightened a bright cape and asked everyone to stay calm.",
    ]))
    world.para()

    world.say(f"Suspicion pointed at {rival.id} because {mission.suspicion}.")
    world.say(rng.choice([
        f'"It must be {rival.id}," a worried bystander cried.',
        f'{hero.id} saw {rival.id} near the empty place and felt ready to act.',
        f"Everyone looked toward {rival.id}, and the market grew quiet.",
        f"The clue seemed so clear that nobody asked {rival.id} a question.",
    ]))
    world.say(
        f'"Wait," {params.partner} said. "We know {rival.id} was nearby, but we do not know why."'
    )
    world.say(
        f'"Give me one minute to explain," {rival.id} replied. '
        f'"Then decide what kind of hero you want to be."'
    )
    hero.memes["patience"] = 0.5
    rival.memes["hurt"] = 0.7
    world.para()

    world.say(f"{hero.id} tried to {mission.first_plan}.")
    world.say(f"But {mission.failure}.")
    world.say(rng.choice([
        f"The failed plan made {hero.id} lower the hero's hands.",
        f"{params.partner} gently removed the old plan from the notebook.",
        f'"A rescue needs facts, not just speed," {params.partner} reminded them.',
        f"The crowd stopped cheering. Even {hero.id} could see that the first answer was too small.",
    ]))
    world.say(f"Then came the twist: {mission.hidden_truth}.")
    world.say(rng.choice([
        f"{hero.id} looked at {rival.id} with surprise instead of anger.",
        f"The new fact changed the shape of the whole mystery.",
        f"{params.partner} pointed to the danger that {rival.id} had noticed first.",
        f"The missing bacon was no longer the only thing that mattered; someone had been trying to help.",
    ]))
    world.para()

    world.say(
        f'"I am sorry I assumed the worst," {hero.id} told {rival.id}. '
        f'"Will you help us finish the rescue?"'
    )
    world.say(
        f'"Yes," {rival.id} said. "But next time, ask me before you chase me."'
    )
    hero.memes["patience"] = 1.0
    rival.memes["hurt"] = 0.0
    rival.memes["trust"] = 0.9
    world.say(f"Together they {mission.repair}.")
    world.say(
        f"{hero.id} wrote the lesson in the team's rescue book: {mission.lesson}."
    )
    world.say(rng.choice([
        f"At sunset, {mission.ending.capitalize()}.",
        f"When the danger passed, {mission.ending.capitalize()}.",
        f"Peace returned in a picture everyone could see: {mission.ending.capitalize()}.",
        f"Before the heroes left, {mission.ending.capitalize()}.",
    ]))

    world.facts.update(
        hero=hero,
        partner=partner,
        rival=rival,
        food=food,
        scene=scene,
        mission=mission,
        truth=mission.hidden_truth,
        repair=mission.repair,
        lesson=mission.lesson,
        ending=mission.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    mission = facts["mission"]
    return [
        f"Write a child-facing superhero story about {facts['hero'].id}, {facts['food'].label}, and a rescue at {facts['scene'].place}.",
        f"Tell a superhero story in which {facts['hero'].id} must remove a quick accusation, discover that {mission.hidden_truth}, and reconcile with {facts['rival'].id}.",
        f"Write a gentle story with a twist: {mission.hidden_truth} End with {mission.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    mission = facts["mission"]
    return [
        QAItem(
            question=f"What problem did {facts['hero'].id} find at {facts['scene'].place}?",
            answer=f"{mission.danger.capitalize()}. The problem began the superhero rescue.",
        ),
        QAItem(
            question=f"Why did people suspect {facts['rival'].id}?",
            answer=f"They suspected {facts['rival'].id} because {mission.suspicion}. That detail showed where the rival was, but not why.",
        ),
        QAItem(
            question=f"What failed about {facts['hero'].id}'s first plan?",
            answer=f"{mission.failure.capitalize()} The failure taught the heroes to look for more information.",
        ),
        QAItem(
            question=f"What twist changed {facts['hero'].id}'s understanding of the missing bacon?",
            answer=f"The twist was that {mission.hidden_truth}. The rival had been responding to danger rather than causing it.",
        ),
        QAItem(
            question=f"How did the heroes reconcile with {facts['rival'].id}?",
            answer=f"{facts['hero'].id} apologized for assuming the worst, and then they {mission.repair}. They rebuilt trust by working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a superhero ask questions before blaming someone?",
            answer="A nearby person may have been helping or may know an important fact. Questions can reveal the whole cause and prevent an unfair accusation.",
        ),
        QAItem(
            question="What does reconciliation mean in a team?",
            answer="Reconciliation means repairing trust after a disagreement. People can apologize, listen, and work together again.",
        ),
        QAItem(
            question="Why might someone remove bacon from a hot oven or table?",
            answer="Someone might remove bacon to prevent a fire, protect another person, save food from danger, or move it to a safer place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  truth={world.facts['truth']}")
    lines.append(f"  repair={world.facts['repair']}")
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="rooftop",
        bacon="bacon",
        name="Luna",
        partner="Pip",
        rival="Vex",
        power="moonlight",
        twist="secret_recipe",
        route="bacon_first",
        seed=11,
    ),
    StoryParams(
        place="market",
        bacon="crispy_bacon",
        name="Zara",
        partner="Maya",
        rival="Bolt",
        power="light shields",
        twist="windy_cape",
        route="alarm_first",
        seed=22,
    ),
    StoryParams(
        place="station",
        bacon="maple_bacon",
        name="Max",
        partner="Ollie",
        rival="Crow",
        power="super speed",
        twist="hungry_rescue",
        route="dialogue_first",
        seed=33,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, bacon in combos:
            print(f"  {place:8} {bacon}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = (
            "### curated story"
            if args.all
            else f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
