#!/usr/bin/env python3
"""
A standalone superhero quest storyworld about a grizzly's dangerous den.
Seed words: terminate, grizzly, scour.
Features: inner monologue, quest, happy ending.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
setting(ember_valley).
has_quest(ember_valley).
has_happy_ending(ember_valley).
has_inner_monologue(ember_valley).
hero_ready(ember_valley) :- has_quest(ember_valley), has_happy_ending(ember_valley).
safe_plan(ember_valley) :- scour_needed(ember_valley), helper_present(ember_valley).
victory(ember_valley) :- hero_ready(ember_valley), safe_plan(ember_valley), threat_ended(ember_valley).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    hero: str
    helper: str
    token: str
    power: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    threat: str
    first_try: str
    clue: str
    dialogue: str
    plan: str
    repair: str
    result: str
    ending: str
    lesson: str


@dataclass
class World:
    place: str = "Ember Valley"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for ent in self.entities.values():
            details = []
            if ent.meters:
                details.append(f"meters={dict(ent.meters)}")
            if ent.memes:
                details.append(f"memes={dict(ent.memes)}")
            if ent.label:
                details.append(f"label={ent.label!r}")
            lines.append(f"  {ent.id:10} ({ent.kind:9}) {' '.join(details)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


HEROES = ["Nova", "Bolt", "Skylark", "Comet", "Beacon", "Vega"]
HELPERS = ["Mira", "Taro", "Pip", "Sol", "Rin", "Juno"]
TOKENS = ["silver whistle", "blue compass", "sunstone badge", "rescue lantern"]
POWERS = ["a bright shield", "swift wind", "a thunder call", "a beam of warm light"]

SCENARIOS = [
    Scenario(
        key="smoke_trail",
        opening="A dark smoke trail curled above the old pine ridge.",
        threat="A frightened grizzly had stumbled into a cave where a cracked beacon was filling the den with hot smoke.",
        first_try="Nova rushed toward the entrance, but the smoke made every step uncertain.",
        clue="the grizzly kept pawing at a cool patch of stone beneath the beacon",
        dialogue='"Do not charge in," Mira called. "The bear is showing us where the safe air is."',
        plan="Nova listened, mapped the cool stones, and decided to guide the grizzly toward the creek instead of trapping it.",
        repair="used the bright shield to block falling sparks while Mira opened a clear path to the creek",
        result="Fresh air swept through the den, and the grizzly padded safely into the moonlit trees.",
        ending="The repaired beacon shone softly over the valley while the grizzly watched from a peaceful meadow.",
        lesson="a true hero studies danger before trying to defeat it",
    ),
    Scenario(
        key="lost_cubs",
        opening="A deep rumble rolled across the valley like a drum.",
        threat="A mother grizzly had wandered from her cubs after a landslide covered the trail to their den.",
        first_try="Bolt tried to scour the whole hillside at once, but loose stones slid underfoot.",
        clue="tiny claw marks pointed toward a narrow tunnel beside the fallen cedar",
        dialogue='"I hear small voices there," Pip said. "Can we clear only the safe stones first?"',
        plan="Bolt marked the unstable ground, then chose a careful route that would not frighten the mother bear.",
        repair="used swift wind to lift dust away while Pip moved the light stones from the tunnel mouth",
        result="The cubs called out, and the mother grizzly led them into the warm evening grass.",
        ending="The family curled together beneath a cedar as the heroes watched the valley grow quiet.",
        lesson="a patient quest can rescue more than speed ever could",
    ),
    Scenario(
        key="storm_gate",
        opening="Lightning flashed behind the mountain gate.",
        threat="A storm had knocked a metal gate across the path, trapping a grizzly between the gate and a flooded ravine.",
        first_try="Skylark pulled at the gate, but its sharp edge scraped the bear's shelter.",
        clue="the hinges were loose on one side and the ground rose gently behind the gate",
        dialogue='"Lift the hinge side," Taro said. "Then the bear can walk toward higher ground."',
        plan="Skylark waited for the safest pause in the rain and asked Taro to signal when the grizzly was ready.",
        repair="used a thunder call to warn the bear, then raised the loose hinge while Taro cleared the high path",
        result="The grizzly crossed to dry ground before the ravine filled any higher.",
        ending="Rain glittered on the open gate, and the rescued bear disappeared into a ferny hillside.",
        lesson="careful teamwork can turn a barrier into a doorway",
    ),
    Scenario(
        key="honey_trap",
        opening="A sweet smell drifted through the ranger meadow.",
        threat="A grizzly had become stuck near a broken honey cart, and the spilled honey drew it toward a busy road.",
        first_try="Comet tried to pull the cart away, but the wheels were wedged under a signpost.",
        clue="the grizzly backed away whenever the lantern cast a wide circle of light",
        dialogue='"Give the bear room," Sol said. "We can scour the road for another safe route."',
        plan="Comet kept the road quiet while Sol checked the meadow and marked a wide trail toward the forest.",
        repair="used warm light to make a calm boundary, then freed the cart and guided the grizzly away from traffic",
        result="The bear followed the forest trail, and the road became safe for travelers again.",
        ending="The empty cart stood beside the meadow as the grizzly's footprints faded among the pines.",
        lesson="protecting a wild neighbor also protects everyone nearby",
    ),
    Scenario(
        key="frozen_stream",
        opening="Winter stars trembled above a frozen stream.",
        threat="A young grizzly had slipped onto thin ice while trying to reach the far bank.",
        first_try="Beacon stepped onto the ice, but a sharp crack warned that the shortcut was unsafe.",
        clue="a line of flat stones led from the bank to a sturdy fallen log",
        dialogue='"The safest path is not always the shortest," Rin said.',
        plan="Beacon studied the stones, tied a rescue line around the log, and waited until the cub looked toward the bank.",
        repair="used the rescue lantern to guide the cub while Rin secured the line and Beacon called softly",
        result="The cub crossed the log and scrambled onto solid snow.",
        ending="The young grizzly shook snow from its fur, then vanished beneath the star-bright trees.",
        lesson="bravery means choosing a safe way to help",
    ),
    Scenario(
        key="echoing_cave",
        opening="An unusual roar echoed from the canyon wall.",
        threat="A grizzly was trapped behind a fallen sign that made the cave echo and frightened every creature nearby.",
        first_try="Vega shouted a warning, but the echo made the grizzly growl louder.",
        clue="the bear relaxed whenever the heroes spoke in low, steady voices",
        dialogue='"Let the cave hear calm words," Juno whispered. "Then we can work."',
        plan="Vega quieted the valley, and Juno helped scour the cave edge for a stable place to move the sign.",
        repair="used a beam of warm light to reveal the sign's safe corner, then shifted it inch by inch",
        result="The grizzly stepped out, sniffed the open air, and lumbered toward the berry field.",
        ending="The canyon held only gentle voices as the heroes left the open cave behind.",
        lesson="calm courage can end a frightening echo",
    ),
]

OPENINGS = [
    "{hero} was patrolling Ember Valley when the emergency beacon blinked red.",
    "At sunset, {hero} heard a warning bell beyond the ranger station.",
    "The people of Ember Valley looked up when {hero} streaked across the golden sky.",
    "A quiet evening changed when {hero} spotted a trail of giant paw prints.",
    "The valley's watchtower flashed three times, calling {hero} to a new quest.",
]

INNER_THOUGHTS = [
    'Inside, {hero} thought, "A power is useful only when it protects someone weaker."',
    'For one heartbeat, {hero} wondered, "Can I be brave without being reckless?"',
    '{hero} reminded themself, "The fastest answer is not always the safest rescue."',
    'A careful thought steadied {hero}: "Listen first. Then act."',
    '{hero} felt fear rise, but thought, "Fear can be a warning, not a command to run."',
]

REWARDS = [
    "The helpers cheered, but {hero} pointed to the rescued animal and smiled.",
    "Everyone celebrated the safe ending with warm cocoa at the ranger station.",
    "The valley children made a new trail marker shaped like a grizzly paw.",
    "The rescue team recorded the safe route so no traveler would forget it.",
    "The heroes shared a quiet high-five beneath the returning stars.",
]


def valid_power_choices() -> list[str]:
    return list(POWERS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("The superhero needs a name.")
    if not params.helper.strip():
        raise StoryError("The quest needs a helpful partner.")
    if params.power not in POWERS:
        raise StoryError("The power must be a gentle rescue power.")
    if params.token not in TOKENS:
        raise StoryError("The quest token must be a safe tool for a rescue.")
    if params.hero.lower() == params.helper.lower():
        raise StoryError("The hero and helper need different names.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "ember_valley"),
            asp.fact("has_quest", "ember_valley"),
            asp.fact("has_happy_ending", "ember_valley"),
            asp.fact("has_inner_monologue", "ember_valley"),
            asp.fact("scour_needed", "ember_valley"),
            asp.fact("helper_present", "ember_valley"),
            asp.fact("threat_ended", "ember_valley"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero grizzly rescue storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--token", choices=TOKENS)
    parser.add_argument("--power", choices=POWERS)
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


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=rng.choice(HEROES),
        helper=rng.choice(HELPERS),
        token=rng.choice(TOKENS),
        power=rng.choice(POWERS),
        seed=rng.randrange(2**31),
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    if args.hero:
        params.hero = args.hero
    if args.helper:
        params.helper = args.helper
    if args.token:
        params.token = args.token
    if args.power:
        params.power = args.power
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity("hero", "character", params.hero))
    world.add(Entity("helper", "character", params.helper))
    world.add(Entity("grizzly", "animal", "grizzly"))
    world.add(Entity("token", "tool", params.token, owner=params.hero))
    world.add(Entity("power", "power", params.power, owner=params.hero))
    world.facts.update(
        place="Ember Valley",
        hero=params.hero,
        helper=params.helper,
        grizzly="grizzly",
        token=params.token,
        power=params.power,
        quest=True,
        inner_monologue=True,
        happy_ending=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    helper = world.get("helper")
    grizzly = world.get("grizzly")
    token = world.get("token")
    power = world.get("power")

    hero.bump_meme("courage")
    helper.bump_meme("trust")
    grizzly.bump_meme("fear")

    world.say(rng.choice(OPENINGS).format(hero=hero.label))
    world.say(scenario.opening)
    world.say(f"{hero.label} carried the {token.label}, and {helper.label} followed with a rescue map.")
    world.say(scenario.threat)
    world.para()

    world.say(scenario.first_try)
    world.say(rng.choice(INNER_THOUGHTS).format(hero=hero.label))
    world.say(f"{hero.label} knew the quest was not to defeat the {grizzly.label}, but to protect it.")
    world.para()

    hero.bump_meter("risk", 1)
    helper.bump_meter("scouting", 1)
    world.say(f"Together they began to scour the area for a safe answer: {scenario.clue}.")
    world.say(scenario.dialogue)
    world.say(scenario.plan)
    world.para()

    power.bump_meter("used", 1)
    grizzly.bump_meme("trust", 1)
    world.say(f"{hero.label} raised {power.label}.")
    world.say(f"{hero.label} and {helper.label} {scenario.repair}.")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("relief")
    helper.bump_meme("joy")
    grizzly.bump_meme("safety")
    world.say(rng.choice(REWARDS).format(hero=hero.label))
    world.say(f"The rescue taught them that {scenario.lesson}.")
    world.say(f"To terminate the danger for good, they marked the safe route with the {token.label}.")
    world.say(scenario.ending)

    world.facts.update(
        scenario=scenario.key,
        threat=scenario.threat,
        first_try=scenario.first_try,
        clue=scenario.clue,
        dialogue=scenario.dialogue,
        plan=scenario.plan,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        lesson=scenario.lesson,
        resolved=True,
        terminated=True,
        scoured=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero quest in Ember Valley where {f['hero']} rescues a grizzly with help from {f['helper']}.",
        f"Include the words terminate, grizzly, and scour, plus an inner monologue and a happy ending.",
        f"Tell how {f['hero']} used {f['power']} and a {f['token']} to solve a dangerous animal rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What danger did the grizzly face?",
            f"The grizzly faced this danger: {f['threat']}",
        ),
        QAItem(
            f"What did {f['hero']} think during the quest?",
            f"{f['hero']} thought that the fastest answer was not always the safest rescue and chose to listen before acting.",
        ),
        QAItem(
            "What clue helped the heroes make a safe plan?",
            f"They noticed that {f['clue']}.",
        ),
        QAItem(
            f"How did {f['hero']} and {f['helper']} help the grizzly?",
            f"They {f['repair']}.",
        ),
        QAItem(
            "How did the story end happily?",
            f"{f['result']} {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey in which someone works through challenges to reach an important goal.",
        ),
        QAItem(
            "What does terminate mean?",
            "Terminate means to bring something to an end, such as ending a danger so it cannot continue.",
        ),
        QAItem(
            "What does scour mean?",
            "Scour means to search an area carefully and thoroughly.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is a character's private thought expressed in the story.",
        ),
        QAItem(
            "What makes a happy ending?",
            "A happy ending shows that the main worry has been solved and the characters or creatures are safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp

    expected = {
        ("hero_ready", ("ember_valley",)),
        ("safe_plan", ("ember_valley",)),
        ("victory", ("ember_valley",)),
    }
    model = asp.one_model(
        asp_program("#show hero_ready/1.\n#show safe_plan/1.\n#show victory/1.")
    )
    actual = set()
    for name in ("hero_ready", "safe_plan", "victory"):
        actual.update((name, args) for args in asp.atoms(model, name))
    if actual == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        for seed in (3, 17, 41):
            sample = generate(
                StoryParams("Nova", "Mira", "blue compass", "a bright shield", seed)
            )
            if not sample.story or "grizzly" not in sample.story:
                print("Generated-story verification failed.")
                return 1
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show victory/1."))
    return sorted(asp.atoms(model, "victory"))


CURATED = [
    StoryParams("Nova", "Mira", "blue compass", "a bright shield", 11),
    StoryParams("Bolt", "Pip", "rescue lantern", "swift wind", 29),
    StoryParams("Beacon", "Rin", "sunstone badge", "a beam of warm light", 47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero_ready/1.\n#show safe_plan/1.\n#show victory/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP-compatible Ember Valley stories:")
        for item in asp_list():
            print(item)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n:
            if attempts > max(100, args.n * 100):
                raise StoryError("Could not produce enough distinct stories.")
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
