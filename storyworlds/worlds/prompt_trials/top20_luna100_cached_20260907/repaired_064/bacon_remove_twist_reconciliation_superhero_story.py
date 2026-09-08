#!/usr/bin/env python3
"""A child-facing superhero story about bacon, a careful removal, and reconciliation."""

from __future__ import annotations

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
    friend: str
    rival: str
    rescue: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class HeroCase:
    danger: str
    mistake: str
    first_plan: str
    failed: str
    twist: str
    truth: str
    remove: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    scene: Scene
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


PLACES = {
    "rooftop": Scene("the sunny rooftop", "bright", "a warm breeze"),
    "market": Scene("the corner market", "bustling", "a cool morning wind"),
    "firehouse": Scene("the neighborhood firehouse", "busy", "a soft spring rain"),
}

BACON = {
    "strip": "a long strip of sizzling bacon",
    "basket": "a basket of crisp bacon",
    "crumbs": "a box of bacon crumbs",
}

HEROES = {"Luna": "girl", "Milo": "boy", "Zara": "girl", "Toby": "boy"}
FRIENDS = {"Pip": "bird", "Nia": "girl", "Bo": "boy", "Remy": "robot"}
RIVALS = {"Blaze": "boy", "Skye": "girl", "Rocky": "boy", "Vera": "girl"}

CASES = {
    "sky_banner": HeroCase(
        "a storm had tangled the town banner around the lunch bell",
        "a bacon smell made everyone think the hungry rescue dog had caused the trouble",
        "flew straight toward the bell and pulled the banner free",
        "the tight knot grew worse when the cape caught the cloth",
        "the banner was holding a loose rooftop antenna against the bell rope",
        "the antenna, not the dog, had snagged the banner and made the bell ring",
        "the antenna from the rope with a padded hook",
        "folded the banner together and thanked the rescue dog for barking the warning",
        "a hero checks what is connected before choosing whom to blame",
        "the clean banner waved above a shared bacon breakfast",
    ),
    "flying_cart": HeroCase(
        "a food cart was rolling toward the fountain",
        "a missing bacon crumb trail pointed straight at Luna's rival",
        "raced beside the cart and tried to steer it",
        "the cart spun faster whenever someone grabbed its hot handle",
        "a loose wheel brace had caught on a bright superhero cape",
        "the cape had pulled the brace loose, sending the cart downhill",
        "the brace from the wheel with a cool metal tool",
        "admitted the cape caused the trouble and invited the rival to help repair it",
        "owning a mistake can turn a rival into a teammate",
        "the cart stood safely by the fountain as friends shared breakfast",
    ),
    "alarm_cloud": HeroCase(
        "a smoky alarm cloud filled the community kitchen",
        "bacon grease on the floor made everyone suspect the newest helper",
        "opened the windows and searched for the source",
        "the cloud spread when the big fan switched on",
        "a paper shield had covered the safety sensor",
        "the sensor had triggered because a practice shield blocked it",
        "the paper shield from the sensor and wipe the safe floor",
        "apologized to the helper and made a safety plan together",
        "good teamwork means fixing danger without hurting feelings",
        "fresh air filled the kitchen while bacon cooked safely on a new tray",
    ),
    "rope_rescue": HeroCase(
        "a little robot was stuck beneath a stage rope",
        "the rope was tied in a knot beside a fallen bacon basket",
        "pulled hard to free the robot",
        "the knot tightened and the stage curtain began to fall",
        "a hidden spring was pressing the rope against the basket handle",
        "the spring, not the robot, had locked the rope in place",
        "the spring from the handle before lifting the curtain",
        "let the rival hold the flashlight while Luna guided the rescue",
        "slowing down can reveal the small cause behind a big problem",
        "the robot rolled free and offered everyone one warm bacon crumb",
    ),
    "hero_badge": HeroCase(
        "the town's silver hero badge had vanished before the parade",
        "a greasy bacon mark appeared on the rival's glove",
        "followed the marks through the parade tent",
        "the marks ended at an empty table and explained nothing",
        "a magnet under the table had pulled the badge through the cloth",
        "the badge had slid beneath the table when the tent floor shook",
        "the badge from beneath the table with a wooden ruler",
        "shared the evidence and apologized before the parade began",
        "a suspicious mark is only a clue, not a verdict",
        "the badge shone on Luna's chest as every hero marched together",
    ),
}

ROUTES = ("bold_first", "question_first", "team_first", "quiet_first", "map_first")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story about bacon and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--bacon", choices=sorted(BACON))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--rival", choices=sorted(RIVALS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(place, bacon) for place in sorted(PLACES) for bacon in sorted(BACON)]


ASP_RULES = """
valid(Place, Bacon) :- place(Place), bacon(Bacon).
safe(Place, Bacon) :- valid(Place, Bacon).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", place) for place in PLACES),
            *(asp.fact("bacon", bacon) for bacon in BACON),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - clingo), sorted(clingo - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.bacon or combo[1] == args.bacon
    ]
    if not combos:
        raise StoryError("No valid superhero story fits those options.")
    place, bacon = rng.choice(combos)
    name = args.name or "Luna"
    friend = args.friend or rng.choice(sorted(FRIENDS))
    rival = args.rival or rng.choice(sorted(RIVALS))
    return StoryParams(
        place=place,
        bacon=bacon,
        name=name,
        friend=friend,
        rival=rival,
        rescue=rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.bacon,
            params.name,
            params.friend,
            params.rival,
            params.rescue,
            params.route,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = CASES[params.rescue]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=HEROES.get(params.name, "hero"),
            memes={"courage": 1.0, "kindness": 1.0},
        )
    )
    friend = world.add(
        Entity(id=params.friend, kind="character", type=FRIENDS[params.friend])
    )
    rival = world.add(
        Entity(
            id=params.rival,
            kind="character",
            type=RIVALS[params.rival],
            memes={"trust": 0.0},
        )
    )
    bacon = world.add(
        Entity(
            id=params.bacon,
            kind="food",
            type="bacon",
            label=BACON[params.bacon],
            meters={"warmth": 1.0},
        )
    )

    openings = {
        "bold_first": (
            f"{hero.id}, the small superhero of {scene.place}, swooped into action when "
            f"{case.danger}. Nearby, {bacon.label} cooled beside a bright red cape."
        ),
        "question_first": (
            f"At {scene.place}, {hero.id} heard a worried shout. {case.danger.capitalize()} "
            f"and {bacon.label} sat untouched on a table."
        ),
        "team_first": (
            f"{hero.id} and {friend.id} were sharing {bacon.label} at {scene.place} when "
            f"{case.danger}. Even a superhero needed a team."
        ),
        "quiet_first": (
            f"The morning at {scene.place} seemed peaceful until {friend.id} spotted trouble: "
            f"{case.danger}. A warm smell of bacon floated through the air."
        ),
        "map_first": (
            f"{hero.id} drew a quick map of {scene.place}, marking the bacon table, the bell, "
            f"and the danger: {case.danger}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{friend.id} pointed toward {rival.id}, who stood close to the trouble.",
                f"Everyone looked at {rival.id}, whose cape was tangled near the mess.",
                f"{rival.id} lifted both hands. '{hero.id}, I did not mean for this to happen!'",
                f"{friend.id} whispered, 'We need facts before we call anyone a villain.'",
            ]
        )
    )
    world.para()

    world.say(f"Somebody noticed that {case.mistake}.")
    world.say(
        rng.choice(
            [
                f'"It must be {rival.id}," a bystander cried. "They were right there!"',
                f"{rival.id} frowned as the crowd began to blame them.",
                f"{hero.id} felt the crowd's anger grow, but a true hero does not rush to punish.",
                f'"Being near trouble is not proof,' {friend.id} said. 'Let us look carefully.'",
            ]
        )
    )
    world.say(
        f'"I want to help, not hurt anyone," {hero.id} told {rival.id}. '
        f'"Will you tell me what you saw?"'
    )
    world.say(
        f'"I saw the {bacon.label} slide, then the rope jerk," {rival.id} answered. '
        f'"I tried to stop it, but my cape caught."'
    )
    rival.memes["blamed"] = 1.0
    hero.memes["fairness"] = 1.0
    world.para()

    world.say(f"{hero.id}'s first plan was to {case.first_plan}.")
    world.say(f"But {case.failed}.")
    world.say(
        rng.choice(
            [
                f"The failed plan taught {hero.id} to pause instead of pulling harder.",
                f"{friend.id} held the flashlight steady while {hero.id} studied every knot.",
                f'"A strong power needs a gentle plan," {friend.id} said.',
                f"{hero.id} lowered the cape and asked everyone to take one quiet step back.",
            ]
        )
    )
    world.say(f"Then came the twist: {case.twist}.")
    world.say(
        rng.choice(
            [
                f"The bacon trail had hidden the small detail that explained everything.",
                f"{friend.id} traced the movement from the table, and the whole puzzle changed.",
                f"{hero.id} realized that the loudest clue had pointed at the wrong person.",
                f"Even {rival.id} could see the new answer once the pieces were placed together.",
            ]
        )
    )
    world.para()

    world.say(f"The truth was that {case.truth}.")
    world.say(f"{hero.id} used a padded tool to {case.remove}.")
    hero.meters["danger_reduced"] = 1.0
    rival.memes["blamed"] = 0.0
    world.say(
        rng.choice(
            [
                f"Then {hero.id} turned to {rival.id}. 'I am sorry we blamed you. Will you help us finish?'",
                f'"Your warning helped us," {hero.id} said. "I should have listened sooner."',
                f"{rival.id} accepted the apology, and the two young heroes worked side by side.",
                f"The crowd grew quiet. Reconciliation began with honest words and a chance to help.",
            ]
        )
    )
    world.say(f"Together, they {case.repair}.")
    world.say(f"{hero.id} remembered the lesson: {case.lesson}.")
    world.say(
        rng.choice(
            [
                f"At last, {case.ending}.",
                f"When the danger was gone, {case.ending.capitalize()}.",
                f"The ending was brighter than a victory song: {case.ending}.",
                f"Before sunset, everyone could see what had changed: {case.ending}.",
            ]
        )
    )
    world.facts.update(
        hero=hero,
        friend=friend,
        rival=rival,
        bacon=bacon,
        scene=scene,
        case=case,
        twist=case.twist,
        remove=case.remove,
        truth=case.truth,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a child-friendly superhero story about {facts['hero'].id}, bacon, and a rescue at {facts['scene'].place}.",
        f"Include a twist revealing that {case.truth}, then show {facts['hero'].id} choosing to {case.remove}.",
        f"End with reconciliation between {facts['hero'].id} and {facts['rival'].id}, followed by {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    return [
        QAItem(
            question=f"What danger did {facts['hero'].id} find at {facts['scene'].place}?",
            answer=f"{case.danger.capitalize()}, while {facts['bacon'].label} was nearby.",
        ),
        QAItem(
            question=f"Why was {facts['rival'].id} blamed at first?",
            answer=f"{case.mistake.capitalize()} made the crowd suspect {facts['rival'].id}, but being nearby did not prove guilt.",
        ),
        QAItem(
            question=f"What was the twist in {facts['hero'].id}'s rescue?",
            answer=f"The twist was that {case.twist}. This showed that {case.truth}.",
        ),
        QAItem(
            question=f"How did {facts['hero'].id} remove the danger?",
            answer=f"{facts['hero'].id} used a padded tool to {case.remove}, then worked carefully with the team.",
        ),
        QAItem(
            question=f"How did reconciliation change the ending?",
            answer=f"{facts['hero'].id} apologized to {facts['rival'].id}, invited help, and together they {case.repair}. {case.ending.capitalize()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a superhero pause before blaming someone?",
            answer="A person can be near a problem without causing it. Checking clues helps a hero protect everyone fairly.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement through honest words, an apology when needed, and helpful action together.",
        ),
        QAItem(
            question="Why should bacon be handled carefully?",
            answer="Hot bacon and its grease can burn people or make a floor slippery, so an adult and safe tools should help manage it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1)),
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
    lines.append(f"  twist={world.facts['twist']}")
    lines.append(f"  remove={world.facts['remove']}")
    lines.append(f"  reconciliation={world.facts['repair']}")
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
        bacon="strip",
        name="Luna",
        friend="Pip",
        rival="Blaze",
        rescue="sky_banner",
        route="bold_first",
        seed=101,
    ),
    StoryParams(
        place="market",
        bacon="basket",
        name="Luna",
        friend="Nia",
        rival="Skye",
        rescue="flying_cart",
        route="team_first",
        seed=202,
    ),
    StoryParams(
        place="firehouse",
        bacon="crumbs",
        name="Luna",
        friend="Remy",
        rival="Vera",
        rescue="alarm_cloud",
        route="question_first",
        seed=303,
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
            print(f"  {place:10} {bacon}")
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
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=(
                "### curated story"
                if args.all
                else (
                    f"### variant {index + 1}"
                    if len(samples) > 1
                    else ""
                )
            ),
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
